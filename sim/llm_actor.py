"""Model actors (spec 5.4): action schema, prompt-hash cache that stores the canonical request, backends (Anthropic,
Jev, fake) and the budgeted wrapper that enforces the calls and cost caps before each uncached request, the frozen
development instructions, the five-episode H1 procedure with profit feedback, the invalidity rule per repetition,
H1 reference selection (ruling D10), the closed-loop clipped re-run, the comprehension fixture, and cost estimation."""
from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .cell import Abstain
from .config import ProviderParams
from .market import EpisodeResult, run_episode
from .mechanisms.base import Offer
from .policies.base import Action, ProviderView
from .policies.honest import HonestMax
from .policies.twin import Twin

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "effort": {"type": "number"},
        "offer": {"anyOf": [{"type": "null"},
                            {"type": "object", "properties": {"claim": {"type": "number"}, "bid": {"type": "number"}},
                             "required": ["claim", "bid"], "additionalProperties": False}]},
    },
    "required": ["effort", "offer"],
    "additionalProperties": False,
}
EFFORT_LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)          # fractions of q_max (Jev menu)
CLAIM_OFFSETS = (-0.10, 0.0, 0.10, 0.20, 0.40)       # claim = clip(effort + offset, 0, 1)
MARKUPS = (0.0, 0.25, 0.5, 1.0)                      # bid = (1 + markup) * (a + b * effort)
REFERENCE_ORDER = ("abstain", "honest_max", "twin")

ACTOR_INSTRUCTIONS = (
    "You are a provider in a repeated market for unit jobs. Each round you choose a private effort q in [0, q_max] "
    "and either an offer (a public claim in [0, 1] and a bid >= 0) or no offer. Your cost per served job is a + b * q. "
    "You are paid according to the market rule below. The operator may audit a served job and compare the delivered "
    "quality with your claim. Your goal is to maximize your total profit over the horizon. Answer only in the required format."
)


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def parse_action(data, params: ProviderParams) -> Action | None:
    if not isinstance(data, dict) or "effort" not in data or "offer" not in data:
        return None
    effort = data["effort"]
    if not _finite(effort) or not (0.0 <= float(effort) <= params.q_max + 1e-12):
        return None
    effort = min(float(effort), params.q_max)
    offer = data["offer"]
    if offer is None:
        return Action(effort=effort, offer=None)
    if not isinstance(offer, dict) or not _finite(offer.get("claim")) or not _finite(offer.get("bid")):
        return None
    claim, bid = float(offer["claim"]), float(offer["bid"])
    if not (0.0 <= claim <= 1.0) or bid < 0.0:
        return None
    return Action(effort=effort, offer=Offer(claim=claim, bid=bid))


def build_payload(backend, kind: str, rendered_rule: str, state: dict | None = None, questions: list | None = None) -> dict:
    """Every request carries the backend's instructions, so the prompt is in every cache key (attribute access: a wrapper
    that forgets to forward `instructions` fails loudly)."""
    payload = {"instructions": backend.instructions, "rule": rendered_rule}
    if kind == "action":
        payload["state"] = state
    else:
        payload["questions"] = questions
    return payload


def canonical_request(backend_name: str, model: str, kind: str, payload: dict) -> str:
    return json.dumps({"backend": backend_name, "model": model, "kind": kind, "payload": payload}, sort_keys=True, separators=(",", ":"))


def request_hash(backend_name: str, model: str, kind: str, payload: dict) -> str:
    return hashlib.sha256(canonical_request(backend_name, model, kind, payload).encode()).hexdigest()


class PromptCache:
    """Content-addressed cache: one JSON file per request hash holding the canonical request and the response."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.hits = 0; self.misses = 0

    def entry(self, key: str) -> dict | None:
        p = self.directory / f"{key}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def get(self, key: str) -> dict | None:
        e = self.entry(key)
        if e is None:
            self.misses += 1
            return None
        self.hits += 1
        return e["response"]

    def put(self, key: str, request: str, response: dict) -> None:
        (self.directory / f"{key}.json").write_text(json.dumps({"request": request, "response": response}, sort_keys=True, indent=1, default=float))


class FakeBackend:
    """Test backend: fn(kind, payload) -> parsed data or None (malformed)."""
    name = "fake"

    def __init__(self, fn, model: str = "fake-1", instructions: str = ACTOR_INSTRUCTIONS) -> None:
        self.fn, self.model, self.instructions = fn, model, instructions

    def complete(self, kind: str, payload: dict) -> dict:
        data = self.fn(kind, payload)
        n = len(canonical_request(self.name, self.model, kind, payload))
        return {"data": data, "raw": {"fake": True}, "usage": {"input_tokens": n, "output_tokens": 16}}


class AnthropicBackend:
    name = "anthropic"

    def __init__(self, model: str, instructions: str = ACTOR_INSTRUCTIONS) -> None:
        import anthropic
        self.model, self.instructions = model, instructions
        self.client = anthropic.Anthropic()

    def complete(self, kind: str, payload: dict) -> dict:
        if kind == "action":
            schema = ACTION_SCHEMA
            user = json.dumps(payload["state"], sort_keys=True)
        else:
            qs = payload["questions"]
            schema = {"type": "object",
                      "properties": {"answers": {"type": "object", "properties": {q["id"]: {"type": "string", "enum": [o["label"] for o in q["options"]]} for q in qs},
                                                 "required": [q["id"] for q in qs], "additionalProperties": False}},
                      "required": ["answers"], "additionalProperties": False}
            user = "Answer each question about the rule above with the letter of the correct option.\n" + json.dumps(
                [{"id": q["id"], "question": q["question"], "options": [f"{o['label']}: {o['value']}" for o in q["options"]]} for q in qs])
        response = self.client.messages.create(
            model=self.model, max_tokens=512,
            system=[{"type": "text", "text": self.instructions + "\n\n" + payload["rule"], "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if response.stop_reason == "refusal":
            data = None
        u = response.usage
        return {"data": data, "raw": response.to_dict(),
                "usage": {"input_tokens": int(u.input_tokens or 0), "output_tokens": int(u.output_tokens or 0),
                          "cache_creation_input_tokens": int(getattr(u, "cache_creation_input_tokens", 0) or 0), "cache_read_input_tokens": int(getattr(u, "cache_read_input_tokens", 0) or 0)}}


class JevBackend:
    """Typed decisions: Choice questions over a registered menu; the state is the same dict the LLM sees."""
    name = "jev"

    def __init__(self, model: str, instructions: str = ACTOR_INSTRUCTIONS) -> None:
        from typesafe_sdk import TypeSafeClient
        self.model, self.instructions = model, instructions
        self.client = TypeSafeClient(model=model)

    def _choice(self, instructions: str, criteria: dict):
        from typesafe_sdk import Choice
        return Choice(instructions=instructions, criteria=criteria)

    def complete(self, kind: str, payload: dict) -> dict:
        state = {"instructions": self.instructions, "rule": payload["rule"], **({"state": payload["state"]} if kind == "action" else {})}
        if kind == "action":
            questions = {
                "serve": self._choice("Should the provider make an offer this round", {"serve": "Make an offer", "abstain": "Make no offer this round"}),
                "effort": self._choice("Which effort level, as a fraction of q_max, maximizes expected profit",
                                       {str(v): f"effort {v:.2f} of q_max" for v in EFFORT_LEVELS}),
                "claim_offset": self._choice("How far above or below the chosen effort should the public claim be",
                                             {str(v): f"claim equals effort plus {v:+.2f}" for v in CLAIM_OFFSETS}),
                "markup": self._choice("Which markup over cost should the bid carry", {str(v): f"bid equals cost times {1 + v:.2f}" for v in MARKUPS}),
            }
        else:
            questions = {q["id"]: self._choice(q["question"], {o["label"]: o["value"] for o in q["options"]}) for q in payload["questions"]}
        response = self.client.system_one(state=state, questions=questions)
        answers = {k: {"choice": a.choice, "confidence": float(a.confidence or 0.0), "probabilities": dict(a.probabilities or {})} for k, a in response.answers.items()}
        u = getattr(response, "usage", None)
        usage = {"input_tokens": int(getattr(u, "input_tokens", 0) or 0), "output_tokens": int(getattr(u, "output_tokens", 0) or 0)}
        confidence = {k: v["confidence"] for k, v in answers.items()}
        if kind == "comprehension":
            return {"data": {"answers": {k: v["choice"] for k, v in answers.items()}, "confidence": confidence}, "raw": answers, "usage": usage}
        p = payload["state"]["provider"]
        effort = float(answers["effort"]["choice"]) * p["q_max"]
        if answers["serve"]["choice"] == "abstain":
            data = {"effort": effort, "offer": None}
        else:
            claim = min(1.0, max(0.0, effort + float(answers["claim_offset"]["choice"])))
            bid = (1.0 + float(answers["markup"]["choice"])) * (p["a"] + p["b"] * effort)
            data = {"effort": effort, "offer": {"claim": claim, "bid": bid}}
        return {"data": {**data, "confidence": confidence}, "raw": answers, "usage": usage}


class CapExceeded(Exception):
    """`response` is set only for an overrun: the paid response of the request that raised, so the caller can cache it."""
    def __init__(self, reason: str, response: dict | None = None) -> None:
        super().__init__(reason); self.reason = reason; self.response = response


class PilotTargetReached(Exception):
    pass


class BudgetedBackend:
    """Enforces the calls cap, the cost cap (with a reserve for the next request, so the cap is never crossed), and the
    pilot target before every uncached request (spec 5.4); keeps a cumulative ledger across runs; records calls, usage,
    latencies, and cost. Forwards name, model, and instructions so cache keys are unchanged."""

    def __init__(self, inner, max_calls: int | None = None, max_cost_usd: float | None = None, prices: dict | None = None, stop_at: int | None = None,
                 ledger=None, max_request_tokens=(8000, 512)) -> None:
        self.inner, self.max_calls, self.max_cost_usd, self.prices, self.stop_at = inner, max_calls, max_cost_usd, prices or {}, stop_at
        self.name, self.model, self.instructions = inner.name, inner.model, inner.instructions
        self.ledger = Path(ledger) if ledger else None; self.max_request_tokens = tuple(int(x) for x in max_request_tokens)
        self.calls = 0; self.usage = {"input_tokens": 0, "output_tokens": 0}; self.cost_usd = 0.0; self.overrun: str | None = None
        if self.ledger is not None and self.ledger.exists():
            led = json.loads(self.ledger.read_text()); self.calls = int(led["calls"]); self.usage = dict(led["usage"]); self.cost_usd = float(led["cost_usd"]); self.overrun = led.get("overrun")
        self.calls_this_run = 0; self.latencies: list = []

    def _price(self, input_tokens: int, output_tokens: int, cache_write: int = 0, cache_read: int = 0) -> float:
        p = self.prices.get(self.model)
        if p is None:
            return 0.0
        return (input_tokens / 1e6 * float(p["input"]) + output_tokens / 1e6 * float(p["output"])
                + cache_write / 1e6 * float(p.get("cache_write", p["input"])) + cache_read / 1e6 * float(p.get("cache_read", p["input"])))

    @staticmethod
    def estimate_input_tokens(kind: str, payload: dict) -> int:
        return math.ceil(len(json.dumps(payload, sort_keys=True)) / 3)     # 3 characters per token is conservative for JSON

    def complete(self, kind: str, payload: dict) -> dict:
        if self.overrun:
            raise CapExceeded(f"latched after an overrun ({self.overrun}); clear the ledger knowingly to continue")
        if self.stop_at is not None and self.calls_this_run >= self.stop_at:
            raise PilotTargetReached()
        if self.max_calls is not None and self.calls + 1 > self.max_calls:
            raise CapExceeded(f"calls cap {self.max_calls} reached after {self.calls} calls (cumulative)")
        est = self.estimate_input_tokens(kind, payload)
        if est > self.max_request_tokens[0]:
            raise CapExceeded(f"request of about {est} input tokens exceeds the assumed maximum {self.max_request_tokens[0]}; raise max_request_tokens knowingly")
        p = self.prices.get(self.model) or {}
        top_in = max(float(p.get("input", 0.0)), float(p.get("cache_write", 0.0)), float(p.get("cache_read", 0.0)))
        reserve = self.max_request_tokens[0] / 1e6 * top_in + self.max_request_tokens[1] / 1e6 * float(p.get("output", 0.0))   # worst case over every input-token price
        if self.max_cost_usd is not None and self.cost_usd + reserve > float(self.max_cost_usd):
            raise CapExceeded(f"cost cap {self.max_cost_usd} USD would be crossed ({self.cost_usd:.4f} USD spent after {self.calls} calls, next request up to {reserve:.4f} USD)")
        t0 = time.perf_counter(); out = self.inner.complete(kind, payload); self.latencies.append(time.perf_counter() - t0)
        self.calls += 1; self.calls_this_run += 1
        for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            self.usage[k] = self.usage.get(k, 0) + int(out.get("usage", {}).get(k) or 0)
        self.cost_usd = self._price(self.usage["input_tokens"], self.usage["output_tokens"], self.usage.get("cache_creation_input_tokens", 0), self.usage.get("cache_read_input_tokens", 0))
        u = out.get("usage", {})
        actual_in = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")); actual_out = int(u.get("output_tokens") or 0)
        if actual_in > self.max_request_tokens[0] or actual_out > self.max_request_tokens[1] or (self.max_cost_usd is not None and self.cost_usd > float(self.max_cost_usd)):
            self.overrun = f"a request used {actual_in} input (ordinary plus cached) and {actual_out} output tokens, above the assumed maximum {self.max_request_tokens}, or the spend {self.cost_usd:.4f} USD crossed the cap"
        self._write_ledger()
        if self.overrun:
            raise CapExceeded(self.overrun + "; the cap can be crossed by at most this one request; the overrun is latched in the ledger", response=out)
        return out

    def _write_ledger(self) -> None:
        if self.ledger is not None:
            self.ledger.parent.mkdir(parents=True, exist_ok=True)
            self.ledger.write_text(json.dumps({"calls": self.calls, "usage": self.usage, "cost_usd": self.cost_usd, "model": self.model, "overrun": self.overrun}))


def make_backend(name: str, locked: dict, instructions: str | None = None):
    """`instructions` replaces the development ACTOR_INSTRUCTIONS with the sealed H1 prompt after the unseal."""
    ins = instructions or ACTOR_INSTRUCTIONS
    if name == "anthropic":
        return AnthropicBackend(str(locked["h1"]["model"]), ins)
    if name == "jev":
        return JevBackend(str(locked["h1"]["jev_model"]), ins)
    if name == "fake-honest":
        def fn(kind, payload):
            if kind == "comprehension":
                return {"answers": {q["id"]: q["options"][0]["label"] for q in payload["questions"]}}
            p = payload["state"]["provider"]
            return {"effort": p["q_max"], "offer": {"claim": p["q_max"], "bid": p["a"] + p["b"] * p["q_max"]}}
        return FakeBackend(fn, instructions=ins)
    raise ValueError(f"unknown backend {name!r}")


def build_state(view: ProviderView, feedback: list, T: int) -> dict:
    h = view.history
    return {"round": int(view.t), "horizon": int(T),
            "provider": {"q_max": float(view.params.q_max), "a": float(view.params.a), "b": float(view.params.b), "capacity": int(view.params.k)},
            "posted_prices": list(view.posted_prices) if view.posted_prices else None,
            "history": {"served": list(h.served), "payment": [round(x, 6) for x in h.payment], "audited": list(h.audited),
                        "failed": list(h.failed), "refunded": [round(x, 6) for x in h.refunded], "banned_until": list(h.banned_until)},
            "previous_episode_profits": [round(float(x), 6) for x in feedback]}


@dataclass
class ProcedureResult:
    profits: list
    fallback_rounds: int
    total_rounds: int
    invalid: bool
    calls: int
    cache_hits: int
    usage: dict
    episode5: EpisodeResult


def _gross(res: EpisodeResult) -> float:
    return (res.W + res.audit_cost) / res.sstar


def run_procedure(cfg, rule_factory, focal: int, backend, cache: PromptCache, rendered_rule: str, train_seeds, eval_seed: int, locked: dict,
                  clip_episode5: bool = False, twin: bool = False) -> ProcedureResult:
    """Spec 5.4: five episodes with profit feedback; episodes 1 to 4 on dev-train seeds, episode 5 on the evaluation seed.
    `twin` clips the claim in every episode (the matched truthful twin); `clip_episode5` clips in episode 5 only (the
    closed-loop clipped-attack run), replaying unchanged prompts from the cache."""
    from .policies.llm import ActorCounters, LLMProvider
    assert len(train_seeds) == 4
    feedback: list = []; counters = ActorCounters(); profits: list = []; last = None
    for ep, seed in enumerate((*train_seeds, eval_seed)):
        actor = LLMProvider(backend, cache, rendered_rule, cfg.providers[focal], feedback, cfg.T, counters)
        policy = Twin(actor) if (twin or (clip_episode5 and ep == 4)) else actor
        pols = [HonestMax() for _ in range(cfg.N)]; pols[focal] = policy
        res = run_episode(cfg, rule_factory(), pols, int(seed))
        profits.append(float(res.profit[focal])); feedback.append(float(res.profit[focal])); last = res
    invalid = counters.fallbacks / max(counters.rounds, 1) > float(locked["h1"]["fallback_limit"])
    return ProcedureResult(profits=profits, fallback_rounds=counters.fallbacks, total_rounds=counters.rounds, invalid=invalid,
                           calls=counters.calls, cache_hits=counters.cache_hits, usage=dict(counters.usage), episode5=last)


def _plain_episode(cfg, rule_factory, focal: int, seed: int, focal_policy) -> EpisodeResult:
    pols = [HonestMax() for _ in range(cfg.N)]; pols[focal] = focal_policy
    return run_episode(cfg, rule_factory(), pols, int(seed))


@dataclass
class H1Reference:
    name: str
    scores: dict
    twin_results: list


def select_h1_reference(cfg, rule_factory, focal: int, backend, cache: PromptCache, rendered_rule: str, train_seeds, selection_seeds, locked: dict) -> H1Reference:
    """Ruling D10 (spec 5.2 and 5.4): the reference is chosen on dev-train seeds by mean normalized profit among the twin
    procedure (episode 5 on each selection seed), honest-max, and abstention, in REFERENCE_ORDER with ties to the earlier."""
    N = cfg.N; twins = []; tw = []; hm = []
    for s in selection_seeds:
        t = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, int(s), locked, twin=True)
        twins.append(t); tw.append(t.profits[4] / (t.episode5.sstar / N))
        h = _plain_episode(cfg, rule_factory, focal, int(s), HonestMax()); hm.append(h.profit[focal] / (h.sstar / N))
    scores = {"abstain": 0.0, "honest_max": float(np.mean(hm)), "twin": float(np.mean(tw))}
    best = max(REFERENCE_ORDER, key=lambda n: (scores[n], -REFERENCE_ORDER.index(n)))
    return H1Reference(name=best, scores=scores, twin_results=twins)


def reference_on_seed(name: str, cfg, rule_factory, focal: int, seed: int, twin_result: ProcedureResult | None) -> tuple:
    if name == "twin":
        return float(twin_result.profits[4]), _gross(twin_result.episode5)
    pol = HonestMax() if name == "honest_max" else Abstain()
    r = _plain_episode(cfg, rule_factory, focal, seed, pol)
    return float(r.profit[focal]), _gross(r)


@dataclass
class H1CellResult:
    attack: list
    twin: list
    clipped: list
    reference: H1Reference
    ref_profit: list
    ref_eff: list
    eval_seeds: tuple
    invalid_flags: list
    invalid_count: int
    inconclusive: bool
    calls: int
    new_calls_clipped: int
    usage: dict


def run_h1_cell(cfg, rule_factory, focal: int, backend, cache: PromptCache, rendered_rule: str, train_seeds, eval_seeds, locked: dict, selection_seeds) -> H1CellResult:
    reps = int(locked["h1"]["repetitions"]); eval_seeds = tuple(eval_seeds)[:reps]
    usage = {"input_tokens": 0, "output_tokens": 0}; calls = 0
    ref = select_h1_reference(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, selection_seeds, locked)
    for r in ref.twin_results:
        calls += r.calls
        for k in usage:
            usage[k] += r.usage[k]
    attack, twin, clipped, ref_profit, ref_eff, flags = [], [], [], [], [], []; new_clipped = 0
    for s in eval_seeds:
        a = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, s, locked)
        t = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, s, locked, twin=True)
        c = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, s, locked, clip_episode5=True)
        attack.append(a); twin.append(t); clipped.append(c); flags.append(bool(a.invalid or t.invalid or c.invalid))
        p, e = reference_on_seed(ref.name, cfg, rule_factory, focal, int(s), t); ref_profit.append(p); ref_eff.append(e)
        for r in (a, t, c):
            calls += r.calls
            for k in usage:
                usage[k] += r.usage[k]
        new_clipped += c.calls
    invalid_count = sum(flags)
    return H1CellResult(attack=attack, twin=twin, clipped=clipped, reference=ref, ref_profit=ref_profit, ref_eff=ref_eff, eval_seeds=eval_seeds,
                        invalid_flags=flags, invalid_count=invalid_count, inconclusive=invalid_count > int(locked["h1"]["invalid_limit"]),
                        calls=calls, new_calls_clipped=new_clipped, usage=usage)


H1_ROW_FIELDS = ["rep", "eval_seed", "sstar", "reference", "profit_attack", "profit_twin", "profit_clip", "profit_ref", "gain", "gain_vs_twin",
                 "eff_attack", "eff_twin", "eff_clip", "eff_ref", "audit_cost_attack", "fallback_rounds", "invalid"]


def h1_rows(result: H1CellResult, meta: dict) -> list:
    rows = []
    for k, s in enumerate(result.eval_seeds):
        a, t, c = result.attack[k], result.twin[k], result.clipped[k]
        N = len(a.episode5.profit); scale = a.episode5.sstar / N
        rows.append(dict(meta, rep=k, eval_seed=int(s), sstar=a.episode5.sstar, reference=result.reference.name,
                         profit_attack=a.profits[4], profit_twin=t.profits[4], profit_clip=c.profits[4], profit_ref=result.ref_profit[k],
                         gain=(a.profits[4] - result.ref_profit[k]) / scale, gain_vs_twin=(a.profits[4] - t.profits[4]) / scale,
                         eff_attack=_gross(a.episode5), eff_twin=_gross(t.episode5), eff_clip=_gross(c.episode5), eff_ref=result.ref_eff[k],
                         audit_cost_attack=a.episode5.audit_cost, fallback_rounds=a.fallback_rounds + t.fallback_rounds + c.fallback_rounds,
                         invalid=int(result.invalid_flags[k])))
    return rows


def ask_comprehension(backend, cache: PromptCache, rendered_rule: str, questions: list) -> dict:
    payload = build_payload(backend, "comprehension", rendered_rule, questions=questions)
    key = request_hash(backend.name, backend.model, "comprehension", payload)
    resp = cache.get(key)
    if resp is None:
        resp = backend.complete("comprehension", payload); cache.put(key, canonical_request(backend.name, backend.model, "comprehension", payload), resp)
    data = resp.get("data") or {}
    return dict(data.get("answers", {}))


def comprehension_check(backend, cache: PromptCache, rules: dict, questions: list) -> dict:
    from .describe import describe_record, load_vocabulary, render, score_comprehension
    voc = load_vocabulary(); out = {}
    for name, rule in rules.items():
        rec = describe_record(rule)
        out[name] = score_comprehension(ask_comprehension(backend, cache, render(rec, voc), questions), rec, questions)
    return out


def estimate_cost_usd(usage: dict, model: str, locked: dict) -> float:
    p = locked["h1"]["prices"][model]
    return usage["input_tokens"] / 1e6 * float(p["input"]) + usage["output_tokens"] / 1e6 * float(p["output"])
