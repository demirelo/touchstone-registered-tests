import numpy as np
import pytest

from sim.config import MarketConfig
from sim.describe import describe_record, load_vocabulary, render, comprehension_questions
from sim.llm_actor import (ACTION_SCHEMA, ACTOR_INSTRUCTIONS, parse_action, request_hash, build_payload, PromptCache, FakeBackend, make_backend,
                           BudgetedBackend, CapExceeded, PilotTargetReached, run_procedure, select_h1_reference, run_h1_cell, h1_rows,
                           H1_ROW_FIELDS, ask_comprehension, comprehension_check, estimate_cost_usd, EFFORT_LEVELS, CLAIM_OFFSETS, MARKUPS)
from sim.locked import load_locked
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax
from sim.policies.llm import LLMProvider, ActorCounters

TRAIN = (1000, 1001, 1002, 1003); SEL = (1000, 1001, 1002, 1003, 1004)


def small_cfg(T=6, budget=0.0):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=T, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=c.alpha, budget=budget)


def honest_fn(kind, payload):
    if kind == "comprehension":
        return {"answers": {q["id"]: q["options"][0]["label"] for q in payload["questions"]}}
    p = payload["state"]["provider"]
    return {"effort": p["q_max"], "offer": {"claim": p["q_max"], "bid": p["a"] + p["b"] * p["q_max"]}}


def cheat_fn(kind, payload):
    if kind == "comprehension":
        return honest_fn(kind, payload)
    p = payload["state"]["provider"]
    return {"effort": 0.0, "offer": {"claim": 1.0, "bid": p["a"]}}


def rendered_b1():
    return render(describe_record(PostedPrices(0.2, 0.35, 0.5)), load_vocabulary())


def test_schema_and_parse_action():
    p = MarketConfig.default().providers[9]
    assert ACTION_SCHEMA["required"] == ["effort", "offer"]
    a = parse_action({"effort": 0.5, "offer": {"claim": 0.9, "bid": 0.3}}, p)
    assert a.effort == 0.5 and a.offer.claim == 0.9 and a.exit is False
    assert parse_action({"effort": 0.5, "offer": None}, p).offer is None
    for bad in ({"effort": 1.5, "offer": None}, {"effort": 0.5}, {"effort": float("nan"), "offer": None},
                {"effort": 0.5, "offer": {"claim": 1.2, "bid": 0.1}}, {"effort": 0.5, "offer": {"claim": 0.5, "bid": -1}}, "nonsense"):
        assert parse_action(bad, p) is None


def test_cache_key_includes_the_prompt_and_the_cache_stores_the_request(tmp_path):
    cache = PromptCache(tmp_path / "cache")
    b1 = FakeBackend(honest_fn); b2 = FakeBackend(honest_fn, instructions="a different sealed prompt")
    k1 = request_hash(b1.name, b1.model, "action", build_payload(b1, "action", "rule", state={"t": 0}))
    k2 = request_hash(b2.name, b2.model, "action", build_payload(b2, "action", "rule", state={"t": 0}))
    assert k1 != k2 and k1 == request_hash(b1.name, b1.model, "action", build_payload(b1, "action", "rule", state={"t": 0}))
    w = BudgetedBackend(b2)                                     # wrappers forward the prompt
    assert w.instructions == b2.instructions and request_hash(w.name, w.model, "action", build_payload(w, "action", "rule", state={"t": 0})) == k2
    assert cache.get(k1) is None and cache.misses == 1
    cache.put(k1, "canonical-request", {"data": {"x": 1}, "raw": {}, "usage": {"input_tokens": 3, "output_tokens": 1}})
    assert cache.get(k1)["data"] == {"x": 1} and cache.hits == 1 and cache.entry(k1)["request"] == "canonical-request"
    assert (tmp_path / "cache" / f"{k1}.json").exists()


def test_llm_provider_acts_through_the_cache_and_never_exits(tmp_path):
    cfg = small_cfg(); rendered = rendered_b1(); cache = PromptCache(tmp_path / "c"); counters = ActorCounters()
    prov = LLMProvider(FakeBackend(honest_fn), cache, rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=counters)
    pols = [HonestMax() for _ in range(4)]; pols[3] = prov
    res = run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert res.n_identities == 4 and counters.calls == cfg.T and counters.fallbacks == 0 and counters.cache_hits == 0
    prov2 = LLMProvider(FakeBackend(honest_fn), cache, rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters())
    pols[3] = prov2
    res2 = run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert prov2.counters.cache_hits == cfg.T and prov2.counters.calls == 0 and np.array_equal(res.profit, res2.profit)   # replay is byte-identical


def test_malformed_response_falls_back_and_is_counted(tmp_path):
    cfg = small_cfg(); rendered = rendered_b1()
    def flaky(kind, payload):
        return None if payload["state"]["round"] == 2 else honest_fn(kind, payload)
    counters = ActorCounters()
    prov = LLMProvider(FakeBackend(flaky), PromptCache(tmp_path / "c"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=counters)
    pols = [HonestMax() for _ in range(4)]; pols[3] = prov
    res = run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert counters.fallbacks == 1 and counters.rounds == cfg.T
    assert res.efforts[2, 3] == cfg.providers[3].q_max and res.claims[2, 3] == cfg.providers[3].q_max   # honest-max for that round


def test_budgeted_backend_stops_before_the_call_that_would_exceed(tmp_path):
    lk = load_locked(); cfg = small_cfg(); rendered = rendered_b1()
    b = BudgetedBackend(FakeBackend(honest_fn), max_calls=4)
    prov = LLMProvider(b, PromptCache(tmp_path / "c"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters())
    pols = [HonestMax() for _ in range(4)]; pols[3] = prov
    with pytest.raises(CapExceeded, match="calls cap 4"):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b.calls == 4 and len(list((tmp_path / "c").glob("*.json"))) == 4     # the fifth call never happened and left no cache entry
    b2 = BudgetedBackend(FakeBackend(honest_fn), stop_at=3)
    prov = LLMProvider(b2, PromptCache(tmp_path / "d"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(PilotTargetReached):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b2.calls == 3 and len(b2.latencies) == 3 and b2.usage["input_tokens"] > 0
    prices = {"fake-1": {"input": 1e6, "output": 0.0}}                 # one USD per input token
    b3 = BudgetedBackend(FakeBackend(honest_fn), max_cost_usd=1.0, prices=prices, max_request_tokens=(1, 0))
    prov = LLMProvider(b3, PromptCache(tmp_path / "e"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded, match="exceeds the assumed maximum"):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b3.calls == 0 and b3.cost_usd == 0.0                       # a request larger than the assumed size is refused before dispatch
    b3b = BudgetedBackend(FakeBackend(honest_fn), max_cost_usd=1.0, prices=prices, max_request_tokens=(10_000, 100))
    prov = LLMProvider(b3b, PromptCache(tmp_path / "e2"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded, match="cost cap"):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b3b.calls == 0                                             # the reserve for one request already exceeds the cap: nothing is dispatched
    ledger = tmp_path / "ledger.json"
    b4 = BudgetedBackend(FakeBackend(honest_fn), max_calls=5, ledger=ledger)
    prov = LLMProvider(b4, PromptCache(tmp_path / "f"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    b5 = BudgetedBackend(FakeBackend(honest_fn), max_calls=5, ledger=ledger)                # a restart continues the same allowance
    assert b5.calls == 5 and b5.calls_this_run == 0
    big = FakeBackend(honest_fn); big.complete = lambda kind, payload: {"data": honest_fn(kind, payload), "raw": {}, "usage": {"input_tokens": 20_000, "output_tokens": 1}}
    b6 = BudgetedBackend(big, max_cost_usd=100.0, prices={"fake-1": {"input": 1.0, "output": 1.0}}, ledger=tmp_path / "l6.json", max_request_tokens=(8000, 512))
    prov = LLMProvider(b6, PromptCache(tmp_path / "h"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded, match="overrun"):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b6.calls == 1 and b6.overrun and len(list((tmp_path / "h").glob("*.json"))) == 1       # one paid call, latched, its response cached
    b7 = BudgetedBackend(big, max_cost_usd=100.0, prices={"fake-1": {"input": 1.0, "output": 1.0}}, ledger=tmp_path / "l6.json", max_request_tokens=(8000, 512))
    with pytest.raises(CapExceeded, match="latched"):
        b7.complete("action", {"x": 1})                                                             # a restart stays latched until the ledger is cleared knowingly
    cached = FakeBackend(honest_fn); cached.complete = lambda kind, payload: {"data": {"effort": 0.0, "offer": None}, "raw": {}, "usage": {"input_tokens": 10, "output_tokens": 1, "cache_creation_input_tokens": 8000}}
    b8 = BudgetedBackend(cached, max_cost_usd=0.035, prices={"fake-1": {"input": 4.0, "output": 20.0, "cache_write": 5.0, "cache_read": 0.4}}, max_request_tokens=(8000, 512))
    with pytest.raises(CapExceeded, match="cost cap"):
        b8.complete("action", {"x": 1})                                                             # the reserve prices 8,000 tokens at the highest input rate (5.0): 0.0400 > 0.035
    b9 = BudgetedBackend(cached, max_cost_usd=1.0, prices={"fake-1": {"input": 4.0, "output": 20.0, "cache_write": 5.0, "cache_read": 0.4}}, max_request_tokens=(8000, 512))
    with pytest.raises(CapExceeded, match="overrun") as info:
        b9.complete("action", {"x": 1})                                                             # 8,010 input tokens counting the cached ones: an overrun, latched
    assert b9.calls == 1 and info.value.response["usage"]["cache_creation_input_tokens"] == 8000 and b9.cost_usd == pytest.approx(10 / 1e6 * 4.0 + 1 / 1e6 * 20.0 + 8000 / 1e6 * 5.0) and b9.overrun
    prov = LLMProvider(b5, PromptCache(tmp_path / "g"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b5.calls == 5 and b5.calls_this_run == 0


def test_procedure_runs_five_episodes_with_feedback_and_invalidity_rule(tmp_path):
    lk = load_locked(); cfg = small_cfg(); rendered = rendered_b1()
    seen_feedback = []
    def fn(kind, payload):
        seen_feedback.append(tuple(payload["state"]["previous_episode_profits"]))
        return honest_fn(kind, payload)
    pr = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(fn), PromptCache(tmp_path / "c"), rendered, TRAIN, 2000, lk)
    assert len(pr.profits) == 5 and pr.total_rounds == 5 * cfg.T and pr.fallback_rounds == 0 and pr.invalid is False
    assert max(len(f) for f in seen_feedback) == 4 and seen_feedback[0] == ()
    assert pr.episode5.sstar > 0 and pr.calls == 5 * cfg.T
    def mostly_bad(kind, payload):
        return None if payload["state"]["round"] % 2 == 0 else honest_fn(kind, payload)
    bad = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(mostly_bad), PromptCache(tmp_path / "d"), rendered, TRAIN, 2000, lk)
    assert bad.invalid is True and bad.fallback_rounds == 5 * (cfg.T // 2)


def test_clipped_rerun_replays_cache_and_counts_new_calls(tmp_path):
    lk = load_locked(); cfg = small_cfg(); rendered = rendered_b1(); cache = PromptCache(tmp_path / "c")
    attack = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered, TRAIN, 2000, lk)
    clipped = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered, TRAIN, 2000, lk, clip_episode5=True)
    assert clipped.cache_hits >= 4 * cfg.T                        # episodes 1 to 4 replay from cache
    assert clipped.calls >= 1                                     # clipping changed the history, so a later prompt is new
    assert clipped.profits[4] < attack.profits[4]                 # the cheat loses its tier under the clip
    c = clipped.episode5.claims[:, 3]; e = clipped.episode5.efforts[:, 3]
    assert np.all(c[~np.isnan(c)] <= e[~np.isnan(c)] + 1e-12)
    twin = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered, TRAIN, 2000, lk, twin=True)
    assert twin.profits[4] == pytest.approx(clipped.profits[4])   # a memoryless actor: the twin and the clipped run agree in episode 5


def test_reference_selection_follows_the_registered_order(tmp_path):
    lk = load_locked(); cfg = small_cfg(); rendered = rendered_b1(); cache = PromptCache(tmp_path / "c")
    ref = select_h1_reference(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered, TRAIN, SEL, lk)
    assert set(ref.scores) == {"abstain", "honest_max", "twin"} and ref.scores["abstain"] == 0.0 and len(ref.twin_results) == len(SEL)
    assert ref.name == max(("abstain", "honest_max", "twin"), key=lambda n: (ref.scores[n], -("abstain", "honest_max", "twin").index(n)))
    assert ref.name == "honest_max"                               # the clipped cheat (effort 0, claim 0) earns less than honest-max under B1
    ref2 = select_h1_reference(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(honest_fn, model="fake-honest"), PromptCache(tmp_path / "d"), rendered, TRAIN, SEL, lk)   # its own identity and cache
    assert ref2.scores["twin"] == pytest.approx(ref2.scores["honest_max"]) and ref2.name == "honest_max"   # ties go to the earlier name


def test_h1_cell_rows_invalid_flags_and_inconclusive(tmp_path):
    lk = dict(load_locked()); lk["h1"] = dict(lk["h1"], repetitions=3, invalid_limit=0)
    cfg = small_cfg(budget=0.3); voc = load_vocabulary()
    rule = lambda: PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3); rendered = render(describe_record(rule()), voc)
    res = run_h1_cell(cfg, rule, 3, FakeBackend(cheat_fn), PromptCache(tmp_path / "c"), rendered, TRAIN, (2000, 2001, 2002), lk, SEL)
    assert len(res.attack) == 3 and len(res.twin) == 3 and len(res.clipped) == 3 and res.inconclusive is False and res.invalid_flags == [False] * 3
    assert res.reference.name in ("abstain", "honest_max", "twin") and len(res.ref_profit) == 3 == len(res.ref_eff)
    rows = h1_rows(res, {"rule": "B2"})
    assert len(rows) == 3 and set(H1_ROW_FIELDS) <= set(rows[0]) and rows[0]["reference"] == res.reference.name
    N = cfg.N; r0 = rows[0]
    assert r0["gain"] == pytest.approx((r0["profit_attack"] - r0["profit_ref"]) / (r0["sstar"] / N))
    assert r0["gain_vs_twin"] == pytest.approx((r0["profit_attack"] - r0["profit_twin"]) / (r0["sstar"] / N))
    def bad(kind, payload):
        return None if payload["state"]["round"] % 2 == 0 else cheat_fn(kind, payload)
    res2 = run_h1_cell(cfg, rule, 3, FakeBackend(bad), PromptCache(tmp_path / "d"), rendered, TRAIN, (2000, 2001, 2002), lk, SEL)
    assert res2.invalid_flags == [True] * 3 and res2.invalid_count == 3 and res2.inconclusive is True and len(res2.attack) == 3   # counted per repetition, nothing dropped


def test_comprehension_and_cost(tmp_path):
    lk = load_locked(); qs = comprehension_questions()
    rules = {"B1": PostedPrices(0.2, 0.35, 0.5), "B2": PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3)}
    b = BudgetedBackend(FakeBackend(honest_fn))
    scores = comprehension_check(b, PromptCache(tmp_path / "c"), rules, qs)
    assert set(scores) == {"B1", "B2"} and all(0 <= v <= len(qs) for v in scores.values()) and b.calls == 2   # comprehension calls are counted
    assert estimate_cost_usd({"input_tokens": 1_000_000, "output_tokens": 100_000}, "claude-opus-5-5", lk) == pytest.approx(4.0 + 2.0)
    assert estimate_cost_usd({"input_tokens": 1_000_000, "output_tokens": 100_000}, "jev-1.14.0", lk) == pytest.approx(0.042)
    assert make_backend("fake-honest", lk).name == "fake" and make_backend("fake-honest", lk, instructions="sealed").instructions == "sealed"
    assert len(EFFORT_LEVELS) == 5 and len(CLAIM_OFFSETS) == 5 and len(MARKUPS) == 4 and ACTOR_INSTRUCTIONS
