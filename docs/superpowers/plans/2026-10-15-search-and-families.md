# Touchstone plan 2A: identities, D2, search, reference selection, bank, calibration, tuning, manifest

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the core engine with identities and identity replacement (H3), add the D2 adaptive family with its knob transforms, implement the pre-registered CMA-ES search with twin search, last-step reference selection, gain decomposition and the search checks, the candidate bank, calibration of S_hat and alpha, baseline tuning on the locked grid, and the cell manifest with a parallel sweep runner, so that every pre-lock simulator run the spec names can be executed from one locked configuration file.

**Architecture:** Plan 1's engine stays the authority on money and admissibility; this plan adds a layer above it. Identities become separate from entities inside `run_episode` (ledger columns and bans are per identity, profit is per entity). Families are objects that map an unbounded CMA-ES vector to a policy through a logistic transform and can project any point to its truthful twin. A `SeedCache` holds draws and S* per seed so every cell shares them. Search, reference selection, bank, tuning, and the manifest are pure functions over cells that read one `experiments/locked.yaml`.

**Tech Stack:** Python 3.12+, numpy, scipy, `cma` (pycma) for CMA-ES, `pyyaml` for the locked config, `multiprocessing` for the sweep, pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5 plus the plan 1 implementation note). This plan implements sections 3 (identity replacement and entry cost), 4.2 (baseline tuning), 5.1 to 5.3 (families, twins, containment, search, positions, search checks, candidate bank, workload manifest), 6.2 (H3), 7 (reference run, gain, clipped-attack run, efficiency quadruple), the calibration constants of section 3 (S_hat, m, rho, B), and the seed namespaces of section 6. Plan 2B covers the interval algorithms, the coverage study, `check_claim.py`, the lock tooling and hash checks, the LLM and Jev actor harness with the `describe()` renderer and comprehension fixture, the custodian instructions for the sealed bundle, the token pilot, and `plot.py`.

**Scope split, stated once:** Plan 2A ends when `scripts/sweep.py` can run the development sweep, the twin runs, the rho sweep, the all-deviators table, and the tuning grid from `locked.yaml`, and `scripts/manifest.py` reports the run counts. Nothing in this plan designs or runs a proposed rule, touches held-out families, or computes a confidence bound.

## Global Constraints

- All of plan 1's constraints remain (unit jobs, unclipped noise, truthful iff claim <= effort, read-only inputs to rules, admissible consequences, integer audits, action-independent draws, conservation each round).
- An entity may drop its identity and re-enter under a fresh one at entry cost `e >= 0`, default `e = 0`; entry cost is a destroyed resource that enters surplus and the entity's profit (spec 3).
- A fresh identity has no history, no ban, and no bond; bond of an exited identity settles as if it had stayed and its releases go to the entity (spec 4.0, 7).
- Profit is per entity across all its identities (spec 7).
- D1 knobs: `u, m in [0,1]`, `s in [0,0.3]`, `w in [0,2]`, `clip in {0,1}`. D2 knobs: `u0, m0 in [0,1]`, `s in [0,0.3]`, `d in [0,1]`, `r in [0,0.2]`, `w in [0,2]`, `clip in {0,1}`; D2 markup recurrence `m_{t+1} = m_t (1-d)` after a failed audit, else `min(m0, m_t + r m0)`, unchanged during a ban; D2 contains D1 at `d = r = 0` (spec 5.3).
- Knobs are mapped from the unbounded search space by a logistic transform; `clip` is a logistic coordinate thresholded at 0.5 (spec 5.3).
- Search: CMA-ES, population 8, initial step 0.3, 5 restarts from registered points (near-honest at logit 0.02 on every knob with clip at logit 0.98, near-full-cheat at logit 0.98 with `s` and `clip` at logit 0.02, three Sobol points), 300 evaluations per restart including incumbent re-evaluation every 10 iterations; exact corners evaluated once as controls outside the budget (spec 5.3).
- The search objective is the mean over 5 dev-train seeds of per-seed normalized profit `pi / (S* / N)`; the reference is subtracted after reference selection, which is the last step (spec 5.2, 5.3).
- Reference candidates are admitted only in projected (`clip = 1`) form: the twin search's best point, honest-max, abstention, the projection of the selected attack, and projected compatible bank members; `clip = 0` points that never inflated on dev-train need no new run (spec 5.2).
- Three pre-registered positions by `b_i q_max_i` (lowest, median, highest); all three at `beta = 0.05`, median elsewhere; headline position selected per cell on dev-train seeds by gain (spec 5.3).
- Seed namespaces: dev-train, dev-val, final-eval are disjoint; final-eval seeds are generated and held by the separate session and are never present in this repo before the unseal (spec 6).
- Calibration: `S_hat` is the expected honest-max first-best surplus over T rounds; `m = S_hat / n_FB`; `rho = alpha / m`, default 0.2; `B = beta S_hat` (spec 3).
- Tuning grid: 27 ordered price triples (P3 geometric between `c_min` and `0.9 q90(v)`, `P2 = f2 P3`, `P1 = f1 P2`, `f in {0.5, 0.7, 0.9}`), `tol_R in {0.08, 0.12, 0.16}`, `L in {10, 20, 50}`; inner search D2 at the median position, 1 restart x 100 evaluations x 3 dev-train seeds, with the twin searched at the same budget and the reference selected last; objective `min((eff - 0.90)/0.90, (0.30 - gain)/0.30)`; top 3 re-checked at the full budget (spec 4.2).
- Manifest: every cell with its run count, pre-lock and post-lock separated, simulator work separated from interval work (spec 5.3).

## Review Focus

1. An entity exits in the last round: no re-entry, no entry cost charged, its bond is released at terminal settlement to the entity. Task 2.
2. A banned identity's entity decides to exit: the exit is honored even though the identity cannot offer, and the fresh identity is not banned. Task 2.
3. A D2 policy whose markup state must persist across rounds is instantiated fresh per episode, so two seeds never share state. Task 3.
4. A search whose objective is flat (every candidate scores the same, as on a rule that never serves the focal provider) terminates within its budget and returns a finite best value. Task 5.
5. Reference selection where every candidate has non-positive profit: abstention wins with profit exactly 0 and gain can be negative. Task 6.
6. A tuning grid point whose prices make tier 3 unaffordable for every job: the inner search still terminates and the point simply scores badly. Task 10.

---

### Task 1: Dependencies and the locked configuration file

**Files:**
- Modify: `pyproject.toml` (add `cma>=4.0`, `pyyaml>=6.0`)
- Create: `experiments/locked.yaml`, `sim/locked.py`
- Test: `tests/test_locked.py`

**Interfaces:**
- Produces: `load_locked(path="experiments/locked.yaml") -> dict`; `seeds(locked, namespace) -> list[int]` for `"dev_train"`, `"dev_val"`; `sha256_file(path) -> str`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_locked.py
import pytest
from sim.locked import load_locked, seeds, sha256_file


def test_locked_loads_and_namespaces_are_disjoint():
    lk = load_locked()
    tr, va = seeds(lk, "dev_train"), seeds(lk, "dev_val")
    assert len(tr) == 5 and len(va) == 20
    assert not set(tr) & set(va)
    assert lk["seeds"]["final_eval"] is None     # custodian-held until the unseal
    assert lk["beta_grid"] == [0.0, 0.01, 0.02, 0.05, 0.10, 0.20]
    assert lk["rho"]["default"] == 0.2 and lk["rho"]["sweep"] == [0.05, 0.2, 1.0]
    assert lk["search"]["popsize"] == 8 and lk["search"]["restarts"] == 5 and lk["search"]["evals_per_restart"] == 300


def test_sha256_is_stable(tmp_path):
    p = tmp_path / "x.txt"; p.write_text("abc")
    assert sha256_file(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_locked.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.locked'`

- [ ] **Step 3: Add dependencies, the config, and the loader**

In `pyproject.toml` change the dependency list to:

```toml
dependencies = ["numpy>=2.0", "scipy>=1.13", "cma>=4.0", "pyyaml>=6.0"]
```

```yaml
# experiments/locked.yaml
# Draft until the lock on 2026-10-28. At the lock this file is frozen by the
# lock tag and check_claim.py refuses any run whose config hash differs.
version: draft
seeds:
  dev_train: [1000, 1001, 1002, 1003, 1004]
  dev_val: [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
            2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019]
  final_eval: null          # generated and held by the separate session
  calibration: [4000, 4001, 4002, 4003, 4004, 4005, 4006, 4007, 4008, 4009,
                4010, 4011, 4012, 4013, 4014, 4015, 4016, 4017, 4018, 4019]
market:
  N: 10
  J: 50
  T: 200
  sigma: 0.05
  e: 0.0
beta_grid: [0.0, 0.01, 0.02, 0.05, 0.10, 0.20]
beta_headline: 0.05
rho:
  default: 0.2
  sweep: [0.05, 0.2, 1.0]
search:
  popsize: 8
  sigma0: 0.3
  restarts: 5
  evals_per_restart: 300
  reeval_every: 10
  sobol_seed: 20261028
  near_corner: 0.02
tuning:
  price_f: [0.5, 0.7, 0.9]
  tol: [0.08, 0.12, 0.16]
  L: [10, 20, 50]
  inner_restarts: 1
  inner_evals: 100
  inner_seeds: 3
  recheck_top: 3
positions: [low, median, high]
all_deviators:
  sweeps: 3
  restarts: 1
  evals: 100
  seeds: 3
```

```python
# sim/locked.py
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "experiments" / "locked.yaml"


def load_locked(path: str | Path = DEFAULT_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def seeds(locked: dict, namespace: str) -> list[int]:
    s = locked["seeds"][namespace]
    if s is None:
        raise ValueError(f"seed namespace {namespace!r} is not available in this repo")
    return [int(x) for x in s]


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv sync && uv run pytest tests/test_locked.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock experiments/locked.yaml sim/locked.py tests/test_locked.py
git commit -m "feat: locked configuration draft with seed namespaces; cma and pyyaml dependencies"
```

---

### Task 2: Identities, exit and re-entry, entry cost, and the H3 policy wrapper

**Files:**
- Modify: `sim/ledger.py` (add `grow`), `sim/policies/base.py` (`ProviderView.identity`, exit allowed), `sim/market.py` (identity bookkeeping), `sim/rng.py` (no change), `sim/checks.py` (no change)
- Create: `sim/policies/identity.py`
- Test: `tests/test_identity.py`; update `tests/test_policies.py::test_validate_action`

**Interfaces:**
- Consumes: plan 1 engine.
- Produces:
  - `Ledger.grow(m: int)` extends every per-identity array to `m` columns.
  - `ProviderView.identity: int` (current identity id of the entity).
  - `validate_action` no longer raises on `exit`.
  - `run_episode` keeps `entity_of: list[int]` (identity to entity) and `identity_of: list[int]` (entity to identity); an `Action.exit` is honored at the end of the round: the identity dies (capacity 0, never active again), a fresh identity is created for the next round, and `cfg.e` is charged to it as entry cost at that round. No re-entry after the last round.
  - `EpisodeResult.profit` stays per entity; new fields `n_identities: int`, `entity_of: tuple[int, ...]`, `identity_profit: np.ndarray`.
  - `IdentityReplacement(policy)` wrapper (H3): acts like `policy` and sets `exit=True` in the round after a failed audit.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_identity.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.base import Consequences
from sim.policies.base import Action, ProviderView, ProviderHistory
from sim.policies.honest import HonestMax
from sim.policies.identity import IdentityReplacement
from sim.ledger import Ledger


def cfgb(budget, e=0.0, T=40):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


class ExitAt:
    """Exits in round `when`, otherwise honest-max."""
    name = "exit_at"
    def __init__(self, when): self.when = when
    def act(self, view):
        a = HonestMax().act(view)
        return Action(effort=a.effort, offer=a.offer, exit=(view.t == self.when))


def test_ledger_grow_keeps_totals():
    led = Ledger(N=2, T=3)
    esc, own = {}, {}
    led.fund(0, 0, 1, 0.5, esc, own); led.settle(0, esc, own, Consequences(), {})
    led.grow(4)
    assert led.funding.shape == (3, 4) and led.bond.shape == (4,)
    assert led.funding.sum() == pytest.approx(0.5)
    led.check_conservation(0.0)


def test_exit_creates_fresh_identity_and_charges_entry_cost():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=3)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N + 1
    assert res.entity_of[-1] == 2
    assert res.ledger.entry.sum() == pytest.approx(0.3)
    assert res.ledger.entry[4, cfg.N] == pytest.approx(0.3)        # charged in the re-entry round
    # the old identity never offers again; the new one does
    old_served = [rec.assignment for rec in res.history[4:]]
    assert all(2 not in asg.values() for asg in old_served)
    assert any(cfg.N in asg.values() for asg in old_served)
    assert res.profit.shape == (cfg.N,)


def test_exit_in_last_round_has_no_reentry_and_no_entry_cost():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=9)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N and res.ledger.entry.sum() == 0.0


def test_banned_identity_can_still_exit_and_fresh_identity_is_not_banned():
    cfg = cfgb(budget=50.0, e=0.0, T=12)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=50)   # every audit fails, long bans
    pols = [HonestMax() for _ in range(cfg.N)]; pols[0] = IdentityReplacement(HonestMax())
    res = run_episode(cfg, rule, pols, 0)
    assert res.n_identities > cfg.N
    # after each re-entry the fresh identity serves at least once before its own first failed audit
    served_by_entity0 = res.served[:, 0]
    assert served_by_entity0.sum() > served_by_entity0[0]


def test_identity_replacement_exits_round_after_failure():
    cfg = cfgb(budget=50.0, T=6)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=2)
    pols = [IdentityReplacement(HonestMax()) for _ in range(cfg.N)]
    res = run_episode(cfg, rule, pols, 0)
    first_fail = int(np.argmax(res.failures[:, 0] > 0))
    assert res.n_identities > cfg.N
    assert res.entity_of.count(0) >= 2
    # bans do not follow the entity: the fresh identity has banned_until 0 at creation
    assert res.identity_profit.shape == (res.n_identities,)
    assert res.profit[0] == pytest.approx(sum(res.identity_profit[k] for k, e in enumerate(res.entity_of) if e == 0))


def test_bond_of_exited_identity_is_released_to_entity():
    class HoldAndExit(HonestMax):
        name = "hold_and_exit"
        def act(self, view):
            a = super().act(view)
            return Action(effort=a.effort, offer=a.offer, exit=(view.t == 2))
    class HoldRule(PostedRandomAudit):
        def enforce(self, records, view):
            cons = super().enforce(records, view)
            for j, amt in view.escrow.items():
                i = view.memory["owner"][j]
                cons.holdbacks[i] = cons.holdbacks.get(i, 0.0) + 0.1 * amt
            return cons
        def allocate(self, values_t, offers, view):
            out = super().allocate(values_t, offers, view)
            view.memory["owner"] = dict(out)
            return out
    cfg = cfgb(budget=0.0, T=8)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[5] = HoldAndExit()
    res = run_episode(cfg, HoldRule(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.ledger.bond.sum() == pytest.approx(0.0)
    assert res.ledger.holdback_in[:, 5].sum() > 0
    assert res.ledger.holdback_out[:, 5].sum() == pytest.approx(res.ledger.holdback_in[:, 5].sum())
    res.ledger.check_conservation(0.0)
```

Also change `tests/test_policies.py::test_validate_action`: replace the two lines

```python
    with pytest.raises(NotImplementedError):
        validate_action(Action(effort=0.5, offer=None, exit=True), p)
```

with

```python
    validate_action(Action(effort=0.5, offer=None, exit=True), p)   # exit is a legal decision
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_identity.py tests/test_policies.py -v`
Expected: FAIL on `ModuleNotFoundError: No module named 'sim.policies.identity'`, then on `Ledger.grow`, `n_identities`, and `NotImplementedError`.

- [ ] **Step 3: Write the implementation**

Add to `sim/ledger.py` inside `class Ledger` after `__init__`:

```python
    def grow(self, m: int) -> None:
        """Extend every per-identity array to m columns (new identities on re-entry)."""
        cur = self.bond.shape[0]
        if m <= cur:
            return
        pad = m - cur
        for name in ("funding", "refunds", "released", "holdback_in", "holdback_out", "forfeits", "cost", "entry"):
            setattr(self, name, np.pad(getattr(self, name), ((0, 0), (0, pad))))
        self.bond = np.pad(self.bond, (0, pad))
        self.N = m
```

In `sim/policies/base.py`: add the field `identity: int = -1` as the last field of `ProviderView`, and replace the body of `validate_action` so that `exit` is accepted:

```python
def validate_action(action: Action, params: ProviderParams) -> None:
    e = action.effort
    if not (isinstance(e, (int, float, np.floating)) and math.isfinite(float(e))):
        raise ValueError("effort must be finite")
    if not (0.0 <= float(e) <= params.q_max + 1e-12):
        raise ValueError(f"effort {e} outside [0, q_max={params.q_max}]")
```

```python
# sim/policies/identity.py
from __future__ import annotations

from .base import Action, ProviderView


class IdentityReplacement:
    """H3 (spec 6.2): behave like the wrapped policy, and exit in the round
    after a failed audit so the entity re-enters under a fresh identity."""

    def __init__(self, policy) -> None:
        self.policy = policy
        self.name = f"h3({getattr(policy, 'name', 'policy')})"

    def act(self, view: ProviderView) -> Action:
        a = self.policy.act(view)
        failed_last = bool(view.history.failed) and view.history.failed[-1] > 0
        return Action(effort=a.effort, offer=a.offer, exit=a.exit or failed_last)
```

Replace `sim/market.py` entirely with the identity-aware loop:

```python
# sim/market.py
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import numpy as np

from .checks import validate_assignment, validate_audits, validate_consequences, validate_payments
from .config import MarketConfig
from .firstbest import first_best_episode
from .ledger import Ledger
from .mechanisms.base import AuditRecord, Consequences, Offer, RoundRecord, StateView
from .policies.base import ProviderHistory, ProviderView, validate_action
from .rng import Draws, make_draws


@dataclass
class EpisodeResult:
    sstar: float
    profit: np.ndarray            # per entity, summed over its identities
    value: float
    cost: float
    entry: float
    audit_cost: float
    served: np.ndarray            # (T, N) per entity
    audits: np.ndarray
    failures: np.ndarray          # (T, N) per entity
    claims: np.ndarray            # (T, N) per entity
    efforts: np.ndarray           # (T, N) per entity
    buyer_surplus: float
    W: float
    history: tuple[RoundRecord, ...]
    ledger: Ledger
    n_identities: int
    entity_of: tuple[int, ...]    # identity -> entity
    identity_profit: np.ndarray   # per identity


def _frozen(cons: Consequences) -> Consequences:
    return Consequences(refunds=MappingProxyType(dict(cons.refunds)), bans=MappingProxyType(dict(cons.bans)),
                        holdbacks=MappingProxyType(dict(cons.holdbacks)), forfeits=MappingProxyType(dict(cons.forfeits)),
                        releases=MappingProxyType(dict(cons.releases)))


def run_episode(cfg: MarketConfig, rule, policies, seed: int, draws: Draws | None = None, sstar: float | None = None) -> EpisodeResult:
    cfg.validate()
    if len(policies) != cfg.N:
        raise ValueError("one policy per entity")
    d = draws if draws is not None else make_draws(cfg, seed)
    sstar_v = first_best_episode(cfg, d) if sstar is None else float(sstar)
    rule.bind(cfg)
    N, T, alpha = cfg.N, cfg.T, cfg.alpha
    allowance = int(np.floor(cfg.budget / alpha + 1e-12)) if alpha > 0 else 0
    ledger = Ledger(N, T)
    caps_entity = np.array([p.k for p in cfg.providers], dtype=np.int64)
    a_arr = np.array([p.a for p in cfg.providers]); b_arr = np.array([p.b for p in cfg.providers])
    # identity bookkeeping: identity ids are slots; arrays below are per identity
    entity_of: list[int] = list(range(N))
    identity_of: list[int] = list(range(N))
    banned_until = np.zeros(N, dtype=np.int64)
    caps_id = caps_entity.copy()
    histories = [ProviderHistory() for _ in range(N)]
    posted = getattr(rule, "prices", None)
    memory: dict = {}
    records_all: list[RoundRecord] = []
    served = np.zeros((T, N), dtype=np.int64); audits = np.zeros(T, dtype=np.int64)
    failures = np.zeros((T, N), dtype=np.int64); claims = np.full((T, N), np.nan); efforts = np.zeros((T, N))
    value_total = 0.0
    tol = rule.tol

    for t in range(T):
        M = len(entity_of)
        ent_arr = np.array(entity_of, dtype=np.int64)
        values_t = d.values[t].copy()
        offers: dict[int, Offer] = {}
        effort_e = np.zeros(N)
        exits: list[int] = []
        for e in range(N):
            ident = identity_of[e]
            act = policies[e].act(ProviderView(i=e, params=cfg.providers[e], t=t, posted_prices=posted,
                                               history=histories[e], policy_seed=int(d.policy_seed[t, e]), identity=ident))
            validate_action(act, cfg.providers[e])
            effort_e[e] = float(act.effort); efforts[t, e] = effort_e[e]
            if act.exit:
                exits.append(e)
            if t < banned_until[ident]:
                continue
            if act.offer is not None:
                offers[ident] = Offer(claim=float(act.offer.claim), bid=float(act.offer.bid))
                claims[t, e] = offers[ident].claim
        tie_key = np.array(d.tie_key[t][:, ent_arr], copy=True); tie_key.setflags(write=False)
        memory["tie_key"] = tie_key
        values_ro = values_t.copy(); values_ro.setflags(write=False)
        hist = tuple(records_all)
        view = StateView(t=t, T=T, N=M, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                         banned_until=banned_until, bond=ledger.bond, capacity=caps_id, escrow={}, history=hist, memory=memory)
        try:
            assignment = dict(rule.allocate(values_ro, dict(offers), view))
            payments = dict(rule.price(dict(assignment), values_ro, dict(offers), view))
        except ValueError as exc:
            if "read-only" in str(exc):
                raise ValueError("rule attempted to write read-only state") from exc
            raise
        validate_assignment(assignment, values_t, offers, view)
        validate_payments(payments, assignment, values_t, offers)
        escrow: dict[int, float] = {}; owner: dict[int, int] = {}
        delivered: dict[int, float] = {}
        if assignment:
            jobs = np.fromiter(assignment.keys(), dtype=np.int64, count=len(assignment))
            ids = np.fromiter(assignment.values(), dtype=np.int64, count=len(assignment))
            ents = ent_arr[ids]
            pay = np.array([payments[j] for j in assignment], dtype=float)
            ledger.funding[t] += np.bincount(ids, weights=pay, minlength=M)
            escrow = dict(zip(jobs.tolist(), pay.tolist()))
            owner = dict(assignment)
            slots = np.zeros(len(ents), dtype=np.int64); seen = np.zeros(N, dtype=np.int64)
            for n, e in enumerate(ents.tolist()):
                slots[n] = seen[e]; seen[e] += 1
            y = effort_e[ents] + d.noise[t, ents, slots]
            value_total += float((values_t[jobs] * y).sum())
            counts_e = np.bincount(ents, minlength=N)
            counts_id = np.bincount(ids, minlength=M)
            ledger.cost[t] += counts_id * (a_arr[ent_arr] + b_arr[ent_arr] * effort_e[ent_arr])
            served[t] = counts_e
            delivered = dict(zip(jobs.tolist(), y.tolist()))
        view_a = StateView(t=t, T=T, N=M, audits_left=allowance, audit_u=float(d.audit_u[t]), audit_key=d.audit_key[t],
                           banned_until=banned_until, bond=ledger.bond, capacity=caps_id, escrow=escrow, history=hist, memory=memory)
        to_audit = list(rule.audit(dict(assignment), view_a))
        validate_audits(to_audit, assignment, view_a)
        records = tuple(AuditRecord(job=j, provider=assignment[j], delivered=delivered[j], claim=offers[assignment[j]].claim,
                                    failed=(tol is not None and delivered[j] < offers[assignment[j]].claim - tol))
                        for j in to_audit)
        allowance -= len(records)
        ledger.charge_audit(t, alpha * len(records))
        audits[t] = len(records)
        cons = rule.enforce(records, view_a)
        if not isinstance(cons, Consequences):
            raise TypeError("enforce must return a Consequences object")
        validate_consequences(cons, records, escrow, owner, ledger.bond, ledger.recent_receipts(), set(offers.keys()))
        failed_jobs_of: dict[int, list[int]] = {}
        failed_e = np.zeros(N, dtype=np.int64)
        for r in records:
            if r.failed:
                failed_e[entity_of[r.provider]] += 1
                failed_jobs_of.setdefault(r.provider, []).append(r.job)
        failures[t] = failed_e
        for ident, rounds in cons.bans.items():
            banned_until[ident] = max(int(banned_until[ident]), t + int(rounds) + 1)
        refunded_e = np.zeros(N)
        for j, amt in cons.refunds.items():
            refunded_e[entity_of[owner[j]]] += amt
        ledger.settle(t, escrow, owner, cons, failed_jobs_of)
        ledger.check_conservation(escrow_outstanding=0.0)
        records_all.append(RoundRecord(t=t, offers=MappingProxyType(dict(offers)), assignment=MappingProxyType(dict(assignment)),
                                       payments=MappingProxyType(dict(payments)), audits=records, consequences=_frozen(cons)))
        audited_e = np.zeros(N, dtype=np.int64)
        for r in records:
            audited_e[entity_of[r.provider]] += 1
        funding_e = np.bincount(ent_arr, weights=ledger.funding[t], minlength=N)
        for e in range(N):
            histories[e].append(int(served[t, e]), float(funding_e[e]), int(audited_e[e]), int(failed_e[e]),
                                float(refunded_e[e]), int(banned_until[identity_of[e]]))
        # 8. exits take effect now; re-entry next round with a fresh identity
        for e in exits:
            old = identity_of[e]
            caps_id[old] = 0
            banned_until[old] = T
            if t + 1 < T:
                new = len(entity_of)
                entity_of.append(e); identity_of[e] = new
                caps_id = np.append(caps_id, caps_entity[e])
                banned_until = np.append(banned_until, 0)
                ledger.grow(new + 1)
                ledger.charge_entry(t + 1, new, cfg.e)

    ledger.terminal_settlement()
    ledger.check_conservation(escrow_outstanding=0.0)
    ent_final = np.array(entity_of, dtype=np.int64)
    identity_profit = ledger.profit()
    profit = np.bincount(ent_final, weights=identity_profit, minlength=N)
    cost = float(ledger.cost.sum()); entry = float(ledger.entry.sum())
    audit_cost = min(float(ledger.audit_cost.sum()), float(cfg.budget))
    W = value_total - cost - entry - audit_cost
    buyer_surplus = value_total - float(ledger.funding.sum()) + ledger.buyer_credit()
    return EpisodeResult(sstar=sstar_v, profit=profit, value=value_total, cost=cost, entry=entry, audit_cost=audit_cost,
                         served=served, audits=audits, failures=failures, claims=claims, efforts=efforts,
                         buyer_surplus=buyer_surplus, W=W, history=tuple(records_all), ledger=ledger,
                         n_identities=len(entity_of), entity_of=tuple(entity_of), identity_profit=identity_profit)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_identity.py tests/test_policies.py -v && uv run pytest -q`
Expected: PASS (6 new tests; whole suite green, 97 tests). The relabeling test in `tests/test_boundary.py` still passes because initial identity ids equal entity indices.

- [ ] **Step 5: Commit**

```bash
git add sim/ledger.py sim/policies/base.py sim/policies/identity.py sim/market.py tests/test_identity.py tests/test_policies.py
git commit -m "feat: identities separate from entities; exit and re-entry with entry cost; H3 identity replacement"
```

---

### Task 3: Families, knob transforms, projection, and the D2 adaptive policy

**Files:**
- Create: `sim/policies/families.py`, `sim/policies/adaptive.py`
- Test: `tests/test_families.py`

**Interfaces:**
- Produces:
  - `Family` dataclass: `name`, `knobs: tuple[str, ...]`, `bounds: dict[str, tuple[float, float]]`, `dim`; methods `transform(x: np.ndarray) -> dict`, `inverse(knobs: dict, near: float) -> np.ndarray` (logit of knob positions; `clip` uses `near`/`1-near`), `project(knobs) -> dict` (clip forced to 1), `make(knobs) -> Policy` (fresh instance), `corners() -> list[dict]` (all bound corners times clip in {0,1}, de-duplicated), `registered_starts(settings: dict) -> list[np.ndarray]` (near-honest, near-full-cheat, three Sobol).
  - `D1 = Family("D1", ...)`, `D2 = Family("D2", ...)`, `FAMILIES = {"D1": D1, "D2": D2}`, `embed_d1_in_d2(knobs) -> dict`.
  - `AdaptiveCheat(u0, m0, s, d, r, w, clip)` policy with per-instance markup state.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_families.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.policies.families import D1, D2, FAMILIES, embed_d1_in_d2
from sim.policies.adaptive import AdaptiveCheat
from sim.policies.base import ProviderView, ProviderHistory


def view(i=0, t=0, failed=None):
    cfg = MarketConfig.default()
    h = ProviderHistory()
    for f in (failed or []):
        h.append(1, 0.5, 1, f, 0.0, 0)
    return ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=None, history=h, policy_seed=0, identity=i)


def test_transform_maps_into_bounds_and_clip_thresholds():
    x = np.zeros(D2.dim)
    k = D2.transform(x)
    assert k["u0"] == pytest.approx(0.5) and k["s"] == pytest.approx(0.15) and k["w"] == pytest.approx(1.0)
    assert k["clip"] == 1          # sigmoid(0) = 0.5 >= 0.5
    k2 = D2.transform(np.full(D2.dim, -0.1))
    assert k2["clip"] == 0
    big = D2.transform(np.full(D2.dim, 50.0))
    assert big["u0"] == pytest.approx(1.0) and big["r"] == pytest.approx(0.2)


def test_inverse_round_trips_and_registered_starts():
    k = {"u0": 0.3, "m0": 0.7, "s": 0.1, "d": 0.2, "r": 0.05, "w": 1.5, "clip": 1}
    x = D2.inverse(k, near=0.02)
    back = D2.transform(x)
    for name in ("u0", "m0", "s", "d", "r", "w"):
        assert back[name] == pytest.approx(k[name], abs=1e-9)
    assert back["clip"] == 1
    settings = {"near_corner": 0.02, "sobol_seed": 7}
    starts = D2.registered_starts(settings)
    assert len(starts) == 5
    honest = D2.transform(starts[0]); cheat = D2.transform(starts[1])
    assert honest["u0"] == pytest.approx(0.02) and honest["clip"] == 1
    assert cheat["u0"] == pytest.approx(0.98) and cheat["s"] == pytest.approx(0.3 * 0.02) and cheat["clip"] == 0


def test_project_forces_clip_and_corners_are_deduplicated():
    assert D1.project({"u": 0.2, "m": 0.9, "s": 0.0, "w": 0.0, "clip": 0})["clip"] == 1
    corners = D1.corners()
    assert len(corners) == 2 ** 5
    assert len({tuple(sorted(c.items())) for c in corners}) == len(corners)


def test_d2_recurrence_and_containment_of_d1():
    p = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.0, w=0.0, clip=0)
    a0 = p.act(view(i=0, failed=[]))                    # m_1 = 0.6 -> claim min(1, 0.3 + 0.6 - 0.2) = 0.7
    assert a0.offer.claim == pytest.approx(0.7)
    a1 = p.act(view(i=0, t=1, failed=[1]))              # failed last round -> m = 0.3 -> claim 0.4
    assert a1.offer.claim == pytest.approx(0.4)
    a2 = p.act(view(i=0, t=2, failed=[1, 0]))           # no failure, r = 0 -> stays 0.3
    assert a2.offer.claim == pytest.approx(0.4)
    q = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.5, w=0.0, clip=0)
    q.act(view(i=0, failed=[])); q.act(view(i=0, t=1, failed=[1]))
    a = q.act(view(i=0, t=2, failed=[1, 0]))            # recovery: min(0.6, 0.3 + 0.3) = 0.6 -> claim 0.7
    assert a.offer.claim == pytest.approx(0.7)
    # containment: D1 point embedded at d = r = 0 behaves like D1 every round
    k1 = {"u": 0.4, "m": 0.5, "s": 0.1, "w": 0.3, "clip": 0}
    d2 = D2.make(embed_d1_in_d2(k1)); d1 = D1.make(k1)
    for t, failed in enumerate(([], [1], [1, 1], [1, 1, 0])):
        assert d2.act(view(i=1, t=t, failed=failed)) == d1.act(view(i=1, t=t, failed=failed))


def test_make_returns_fresh_instances():
    k = {"u0": 0.5, "m0": 0.6, "s": 0.2, "d": 0.5, "r": 0.0, "w": 0.0, "clip": 0}
    a, b = D2.make(k), D2.make(k)
    a.act(view(i=0)); a.act(view(i=0, t=1, failed=[1]))
    assert b.act(view(i=0)).offer.claim == pytest.approx(0.7)    # b's state untouched
    assert set(FAMILIES) == {"D1", "D2"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_families.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.policies.families'`

- [ ] **Step 3: Write the implementation**

```python
# sim/policies/adaptive.py
from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class AdaptiveCheat:
    """D2 (spec 5.3). Markup state m_t: m_1 = m0; after a failed audit
    m <- m (1 - d); otherwise m <- min(m0, m + r m0); unchanged during a ban.
    One instance per entity per episode."""
    name = "adaptive_cheat"

    def __init__(self, u0: float, m0: float, s: float, d: float, r: float, w: float, clip: int) -> None:
        if not (0.0 <= u0 <= 1.0 and 0.0 <= m0 <= 1.0 and 0.0 <= s <= 0.3 and 0.0 <= d <= 1.0
                and 0.0 <= r <= 0.2 and 0.0 <= w <= 2.0):
            raise ValueError("D2 knob outside its domain")
        if isinstance(clip, bool) or clip not in (0, 1) or int(clip) != clip:
            raise ValueError("clip must be exactly 0 or 1")
        self.u0, self.m0, self.s, self.d, self.r, self.w, self.clip = float(u0), float(m0), float(s), float(d), float(r), float(w), int(clip)
        self.m = float(m0)
        self._last_t: int | None = None

    def _update_state(self, view: ProviderView) -> None:
        # Apply the recurrence once per round, using what happened last round.
        if self._last_t is not None and view.t > self._last_t and view.history.failed:
            if view.history.banned_until and view.history.banned_until[-1] > view.t - 1 and view.history.failed[-1] == 0:
                pass   # banned last round and not audited: state unchanged
            elif view.history.failed[-1] > 0:
                self.m *= (1.0 - self.d)
            else:
                self.m = min(self.m0, self.m + self.r * self.m0)
        self._last_t = view.t

    def act(self, view: ProviderView) -> Action:
        self._update_state(view)
        p = view.params
        effort = p.q_max * (1.0 - self.u0)
        claim = min(1.0, max(0.0, effort + self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + self.w) * (p.a + p.b * effort)))
```

```python
# sim/policies/families.py
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np
from scipy.stats import qmc

from .adaptive import AdaptiveCheat
from .fixed_cheat import FixedCheat


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _logit(p: float) -> float:
    p = min(max(p, 1e-12), 1 - 1e-12)
    return float(np.log(p / (1 - p)))


@dataclass(frozen=True)
class Family:
    name: str
    knobs: tuple[str, ...]            # continuous knobs in order, then "clip" last
    bounds: dict
    factory: object

    @property
    def dim(self) -> int:
        return len(self.knobs)

    def transform(self, x: np.ndarray) -> dict:
        s = _sigmoid(np.asarray(x, dtype=float))
        out = {}
        for k, v in zip(self.knobs, s):
            if k == "clip":
                out[k] = 1 if v >= 0.5 else 0
            else:
                lo, hi = self.bounds[k]
                out[k] = float(lo + (hi - lo) * v)
        return out

    def inverse(self, knobs: dict, near: float = 0.02) -> np.ndarray:
        x = []
        for k in self.knobs:
            if k == "clip":
                x.append(_logit(1 - near if knobs[k] else near))
            else:
                lo, hi = self.bounds[k]
                x.append(_logit((knobs[k] - lo) / (hi - lo)))
        return np.array(x)

    def project(self, knobs: dict) -> dict:
        out = dict(knobs); out["clip"] = 1
        return out

    def make(self, knobs: dict):
        return self.factory(**knobs)

    def corners(self) -> list[dict]:
        seen, out = set(), []
        for bits in product((0, 1), repeat=self.dim):
            k = {}
            for name, b in zip(self.knobs, bits):
                k[name] = b if name == "clip" else self.bounds[name][b]
            key = tuple(sorted(k.items()))
            if key not in seen:
                seen.add(key); out.append(k)
        return out

    def registered_starts(self, settings: dict) -> list[np.ndarray]:
        near = float(settings["near_corner"])
        lo_x, hi_x = _logit(near), _logit(1 - near)
        honest = np.full(self.dim, lo_x); honest[self.knobs.index("clip")] = hi_x
        cheat = np.full(self.dim, hi_x)
        for name in ("s", "clip"):
            if name in self.knobs:
                cheat[self.knobs.index(name)] = lo_x
        sob = qmc.Sobol(d=self.dim, scramble=True, seed=int(settings["sobol_seed"])).random(4)[1:4]
        sobol = [np.array([_logit(float(v)) for v in row]) for row in sob]
        return [honest, cheat] + sobol


D1 = Family("D1", ("u", "m", "s", "w", "clip"),
            {"u": (0.0, 1.0), "m": (0.0, 1.0), "s": (0.0, 0.3), "w": (0.0, 2.0)}, FixedCheat)
D2 = Family("D2", ("u0", "m0", "s", "d", "r", "w", "clip"),
            {"u0": (0.0, 1.0), "m0": (0.0, 1.0), "s": (0.0, 0.3), "d": (0.0, 1.0), "r": (0.0, 0.2), "w": (0.0, 2.0)},
            AdaptiveCheat)
FAMILIES = {"D1": D1, "D2": D2}


def embed_d1_in_d2(k: dict) -> dict:
    return {"u0": k["u"], "m0": k["m"], "s": k["s"], "d": 0.0, "r": 0.0, "w": k["w"], "clip": k["clip"]}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_families.py -v`
Expected: PASS (5 tests). If `test_d2_recurrence_and_containment_of_d1` fails on the ban branch, note that the test histories carry `banned_until=0`, so the ban branch is never taken there; the branch is exercised by Task 5's cell runs.

- [ ] **Step 5: Commit**

```bash
git add sim/policies/families.py sim/policies/adaptive.py tests/test_families.py
git commit -m "feat: D1/D2 families with logistic knob transforms, projection, corners, registered starts; D2 adaptive policy"
```

---

### Task 4: Seed cache and the cell runner

**Files:**
- Create: `sim/cell.py`
- Test: `tests/test_cell.py`

**Interfaces:**
- Produces:
  - `SeedCache()` with `get(cfg, seed) -> tuple[Draws, float]` (draws and S*, computed once per `(config_key(cfg), seed)`); `config_key(cfg) -> str` (sha256 of the config's fields).
  - `Cell(cfg, rule_factory: Callable[[], Mechanism], focal: int, seeds: tuple[int, ...], name: str)`.
  - `run_focal(cell, policy_factory: Callable[[], Policy], cache) -> FocalRun` with `profit[len(seeds)]`, `normalized[len(seeds)]` (`profit / (S*/N)`), `results: list[EpisodeResult]`; every other entity plays `HonestMax`.
  - `Abstain()` policy: effort 0, no offer.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cell.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell, run_focal, Abstain, config_key
from sim.config import MarketConfig, ProviderParams
from sim.mechanisms.posted import PostedPrices
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat


def tiny(budget=0.0, T=10):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=T, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers[6:10], alpha=c.alpha, budget=budget)


def test_cache_computes_once_per_config_and_seed():
    cache = SeedCache()
    cfg = tiny()
    d1, s1 = cache.get(cfg, 1); d2, s2 = cache.get(cfg, 1)
    assert d1 is d2 and s1 == s2 and cache.hits == 1
    other = tiny(T=11)
    assert config_key(other) != config_key(cfg)
    cache.get(other, 1)
    assert cache.misses == 2


def test_run_focal_normalizes_by_sstar_over_n():
    cache = SeedCache()
    cell = Cell(cfg=tiny(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=3, seeds=(1, 2, 3), name="t")
    fr = run_focal(cell, lambda: HonestMax(), cache)
    assert fr.profit.shape == (3,) and fr.normalized.shape == (3,)
    for k, res in enumerate(fr.results):
        assert fr.normalized[k] == pytest.approx(fr.profit[k] / (res.sstar / 4))


def test_abstain_has_zero_profit():
    cache = SeedCache()
    cell = Cell(cfg=tiny(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=0, seeds=(1,), name="t")
    fr = run_focal(cell, Abstain, cache)
    assert fr.profit[0] == 0.0 and fr.results[0].served[:, 0].sum() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cell.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.cell'`

- [ ] **Step 3: Write the implementation**

```python
# sim/cell.py
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from .config import MarketConfig
from .firstbest import first_best_episode
from .market import EpisodeResult, run_episode
from .policies.base import Action, ProviderView
from .policies.honest import HonestMax
from .rng import Draws, make_draws


def config_key(cfg: MarketConfig) -> str:
    return hashlib.sha256(repr(cfg).encode()).hexdigest()[:16]


class SeedCache:
    """Draws and S* per (config, seed): computed once, shared by every cell."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, int], tuple[Draws, float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, cfg: MarketConfig, seed: int) -> tuple[Draws, float]:
        key = (config_key(cfg), int(seed))
        if key in self._store:
            self.hits += 1
            return self._store[key]
        self.misses += 1
        d = make_draws(cfg, seed)
        self._store[key] = (d, first_best_episode(cfg, d))
        return self._store[key]


class Abstain:
    name = "abstain"

    def act(self, view: ProviderView) -> Action:
        return Action(effort=0.0, offer=None)


@dataclass(frozen=True)
class Cell:
    cfg: MarketConfig
    rule_factory: Callable
    focal: int
    seeds: tuple[int, ...]
    name: str


@dataclass
class FocalRun:
    profit: np.ndarray
    normalized: np.ndarray
    results: list = field(default_factory=list)


def run_focal(cell: Cell, policy_factory: Callable, cache: SeedCache) -> FocalRun:
    profits, norms, results = [], [], []
    for seed in cell.seeds:
        d, sstar = cache.get(cell.cfg, seed)
        pols = [HonestMax() for _ in range(cell.cfg.N)]
        pols[cell.focal] = policy_factory()
        res = run_episode(cell.cfg, cell.rule_factory(), pols, seed, draws=d, sstar=sstar)
        profits.append(float(res.profit[cell.focal]))
        norms.append(float(res.profit[cell.focal] / (sstar / cell.cfg.N)))
        results.append(res)
    return FocalRun(profit=np.array(profits), normalized=np.array(norms), results=results)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cell.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/cell.py tests/test_cell.py
git commit -m "feat: seed cache and focal cell runner"
```

---

### Task 5: CMA-ES search with registered settings

**Files:**
- Create: `sim/search.py`
- Test: `tests/test_search.py`

**Interfaces:**
- Consumes: `Family`, `Cell`, `run_focal`, `SeedCache`.
- Produces:
  - `SearchSettings(popsize, sigma0, restarts, evals_per_restart, reeval_every, near_corner, sobol_seed)` and `settings_from_locked(locked) -> SearchSettings`.
  - `Objective`: `make_objective(cell, family, cache, force_clip: bool = False) -> Callable[[np.ndarray], float]` returning mean normalized profit over the cell's seeds; with `force_clip` the knobs are projected before `make`.
  - `cma_search(objective, family, settings, seed) -> SearchResult(best_x, best_knobs, best_f, restart_bests: list[float], evals: int, trace: list[tuple[int, float]])`.
  - `corner_controls(objective, family) -> list[tuple[dict, float]]` evaluated once each, outside the budget.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_search.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2
from sim.search import SearchSettings, make_objective, cma_search, corner_controls


def fixture_cfg():
    # every job accepts tier 3 at P3 = 0.5 (v_min 0.6 >= 0.5), P3 > a, focal has positive allocation
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=60, reeval_every=10,
                       near_corner=0.02, sobol_seed=3)


def test_search_recovers_b1_analytic_best_response_within_one_percent():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1, 2), name="b1fix")
    obj = make_objective(cell, D1, cache)
    analytic = obj(D1.inverse({"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, near=1e-9))
    full = SearchSettings(popsize=8, sigma0=0.3, restarts=5, evals_per_restart=300, reeval_every=10, near_corner=0.02, sobol_seed=3)
    res = cma_search(obj, D1, full, seed=0)
    assert res.best_f >= analytic * 0.99
    assert res.best_knobs["clip"] == 0 and res.best_knobs["u"] > 0.9 and res.best_knobs["m"] > 0.9
    assert res.evals == 5 * 300 and len(res.restart_bests) == 5


def test_search_respects_budget_and_is_deterministic():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="b1fix")
    obj = make_objective(cell, D2, cache)
    a = cma_search(obj, D2, SMALL, seed=1); b = cma_search(obj, D2, SMALL, seed=1)
    assert a.evals == 2 * 60 and a.best_f == b.best_f and np.array_equal(a.best_x, b.best_x)
    assert np.isfinite(a.best_f)


def test_flat_objective_terminates():
    res = cma_search(lambda x: 0.0, D1, SMALL, seed=0)
    assert res.evals == 120 and res.best_f == 0.0


def test_force_clip_objective_never_inflates_and_corner_controls():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="b1fix")
    obj_t = make_objective(cell, D1, cache, force_clip=True)
    x = D1.inverse({"u": 0.5, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, near=1e-9)
    obj_t(x)
    res = cache.get(cell.cfg, 1)
    ctrl = corner_controls(make_objective(cell, D1, cache), D1)
    assert len(ctrl) == 32 and all(np.isfinite(f) for _, f in ctrl)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_search.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.search'`

- [ ] **Step 3: Write the implementation**

```python
# sim/search.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import cma
import numpy as np

from .cell import Cell, SeedCache, run_focal
from .policies.families import Family


@dataclass(frozen=True)
class SearchSettings:
    popsize: int
    sigma0: float
    restarts: int
    evals_per_restart: int
    reeval_every: int
    near_corner: float
    sobol_seed: int


def settings_from_locked(locked: dict) -> SearchSettings:
    s = locked["search"]
    return SearchSettings(popsize=int(s["popsize"]), sigma0=float(s["sigma0"]), restarts=int(s["restarts"]),
                          evals_per_restart=int(s["evals_per_restart"]), reeval_every=int(s["reeval_every"]),
                          near_corner=float(s["near_corner"]), sobol_seed=int(s["sobol_seed"]))


@dataclass
class SearchResult:
    best_x: np.ndarray
    best_knobs: dict
    best_f: float
    restart_bests: list
    evals: int
    trace: list


def make_objective(cell: Cell, family: Family, cache: SeedCache, force_clip: bool = False) -> Callable[[np.ndarray], float]:
    """Mean over the cell's seeds of per-seed normalized profit pi / (S* / N).
    The reference is subtracted after reference selection, never here."""
    def objective(x: np.ndarray) -> float:
        knobs = family.transform(x)
        if force_clip:
            knobs = family.project(knobs)
        fr = run_focal(cell, lambda: family.make(knobs), cache)
        return float(fr.normalized.mean())
    return objective


def cma_search(objective: Callable[[np.ndarray], float], family: Family, settings: SearchSettings, seed: int) -> SearchResult:
    """CMA-ES maximization with registered restarts and a fixed evaluation budget
    per restart (incumbent re-evaluations count)."""
    starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed})
    best_x, best_f = None, -np.inf
    restart_bests, trace, evals = [], [], 0
    for r in range(settings.restarts):
        x0 = starts[r % len(starts)]
        es = cma.CMAEvolutionStrategy(x0, settings.sigma0,
                                      {"popsize": settings.popsize, "seed": int(seed) + 1 + r, "verbose": -9, "verb_log": 0})
        used, it = 0, 0
        r_best_x, r_best_f = x0.copy(), objective(x0)
        used += 1; evals += 1
        if r_best_f > best_f:
            best_x, best_f = r_best_x.copy(), r_best_f
        while used < settings.evals_per_restart:
            X = es.ask()
            n = min(len(X), settings.evals_per_restart - used)
            X = X[:n]
            F = [objective(np.asarray(x)) for x in X]
            used += n; evals += n
            if n == settings.popsize:
                es.tell(X, [-f for f in F])
            for x, f in zip(X, F):
                if f > r_best_f:
                    r_best_x, r_best_f = np.asarray(x).copy(), f
            it += 1
            if it % settings.reeval_every == 0 and used < settings.evals_per_restart:
                f_re = objective(r_best_x)
                used += 1; evals += 1
                r_best_f = min(r_best_f, f_re)   # a deterministic objective returns the same value
            trace.append((evals, r_best_f))
            if r_best_f > best_f:
                best_x, best_f = r_best_x.copy(), r_best_f
        restart_bests.append(r_best_f)
    return SearchResult(best_x=best_x, best_knobs=family.transform(best_x), best_f=float(best_f),
                        restart_bests=restart_bests, evals=evals, trace=trace)


def corner_controls(objective: Callable[[np.ndarray], float], family: Family) -> list[tuple[dict, float]]:
    out = []
    for k in family.corners():
        out.append((k, float(objective(family.inverse(k, near=1e-9)))))
    return out
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_search.py -v`
Expected: PASS (4 tests). The analytic check runs 1,500 evaluations on two 20-round episodes; expect under a minute.

- [ ] **Step 5: Commit**

```bash
git add sim/search.py tests/test_search.py
git commit -m "feat: CMA-ES best-response search with registered starts, evaluation budget, and corner controls"
```

---

### Task 6: Twin search, last-step reference selection, gain decomposition, clipped-attack run

**Files:**
- Create: `sim/reference.py`
- Test: `tests/test_reference.py`

**Interfaces:**
- Consumes: Tasks 4 and 5.
- Produces:
  - `Candidate(name, policy_factory, knobs: dict | None)`.
  - `twin_search(cell, family, cache, settings, seed) -> SearchResult` (search with `force_clip=True`).
  - `reference_candidates(cell, family, attack_knobs, twin_result, bank_members: list[dict]) -> list[Candidate]`: twin best (projected), honest-max, abstain, projection of the selected attack, projected bank members, and every projected point from `extra_points` the caller passes (Task 7's bank handles its own projections).
  - `select_reference(cell, candidates, cache) -> ReferenceChoice(candidate, per_seed_profit, per_seed_normalized)` choosing the highest mean normalized profit on the cell's seeds, ties by candidate order.
  - `evaluate_gain(cell, family, attack_knobs, reference: ReferenceChoice, cache) -> GainResult` with per-seed `gain`, `inflation_term`, `selection_term`, and `eff_attack, eff_clip, eff_ref, eff_honest` (gross efficiencies), where the clipped-attack run is the same knobs with `clip = 1`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reference.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.families import D1
from sim.reference import twin_search, reference_candidates, select_reference, evaluate_gain
from sim.search import SearchSettings


def fixture_cfg(budget=0.0):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=budget)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=1, evals_per_restart=40, reeval_every=10, near_corner=0.02, sobol_seed=3)


def test_reference_is_chosen_last_and_honest_max_gain_is_zero():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=2, seeds=(1, 2), name="c")
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    honest_knobs = {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}
    cands = reference_candidates(cell, D1, honest_knobs, tw, bank_members=[])
    names = [c.name for c in cands]
    assert names[:3] == ["twin_search", "honest_max", "abstain"] and "attack_projection" in names
    ref = select_reference(cell, cands, cache)
    g = evaluate_gain(cell, D1, honest_knobs, ref, cache)
    assert np.all(g.inflation_term == 0.0)
    assert g.gain.mean() <= 1e-12


def test_full_cheat_has_positive_gain_and_decomposition_adds_up():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1, 2), name="c")
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    attack = {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}
    ref = select_reference(cell, reference_candidates(cell, D1, attack, tw, []), cache)
    g = evaluate_gain(cell, D1, attack, ref, cache)
    assert g.gain.mean() > 0
    assert np.allclose(g.gain, g.inflation_term + g.selection_term)
    assert g.eff_attack.shape == (2,) and np.all(np.isfinite(g.eff_honest))


def test_abstention_wins_when_everything_loses_money():
    cache = SeedCache()
    # tier prices below cost for everyone: any truthful service loses money
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.05, 0.10, 0.15), focal=3, seeds=(1,), name="c")
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    attack = {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}
    ref = select_reference(cell, reference_candidates(cell, D1, attack, tw, []), cache)
    assert ref.candidate.name == "abstain" and ref.per_seed_profit[0] == 0.0
    g = evaluate_gain(cell, D1, attack, ref, cache)
    assert g.gain[0] < 0.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_reference.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.reference'`

- [ ] **Step 3: Write the implementation**

```python
# sim/reference.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .cell import Abstain, Cell, SeedCache, run_focal
from .policies.families import Family
from .policies.honest import HonestMax
from .search import SearchResult, SearchSettings, cma_search, make_objective


@dataclass(frozen=True)
class Candidate:
    name: str
    policy_factory: Callable
    knobs: dict | None


@dataclass
class ReferenceChoice:
    candidate: Candidate
    per_seed_profit: np.ndarray
    per_seed_normalized: np.ndarray


@dataclass
class GainResult:
    gain: np.ndarray
    inflation_term: np.ndarray
    selection_term: np.ndarray
    eff_attack: np.ndarray
    eff_clip: np.ndarray
    eff_ref: np.ndarray
    eff_honest: np.ndarray
    profit_attack: np.ndarray
    profit_clip: np.ndarray


def twin_search(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int) -> SearchResult:
    return cma_search(make_objective(cell, family, cache, force_clip=True), family, settings, seed)


def reference_candidates(cell: Cell, family: Family, attack_knobs: dict, twin_result: SearchResult,
                         bank_members: list[dict]) -> list[Candidate]:
    """Every reference candidate in projected form (spec 5.2). Order is the tie-break."""
    tw = family.project(twin_result.best_knobs)
    cands = [Candidate("twin_search", lambda tw=tw: family.make(tw), tw),
             Candidate("honest_max", HonestMax, None),
             Candidate("abstain", Abstain, None)]
    proj = family.project(attack_knobs)
    cands.append(Candidate("attack_projection", lambda proj=proj: family.make(proj), proj))
    for n, k in enumerate(bank_members):
        pk = family.project(k)
        cands.append(Candidate(f"bank_{n}", lambda pk=pk: family.make(pk), pk))
    return cands


def select_reference(cell: Cell, candidates: list[Candidate], cache: SeedCache) -> ReferenceChoice:
    best = None
    for c in candidates:
        fr = run_focal(cell, c.policy_factory, cache)
        score = float(fr.normalized.mean())
        if best is None or score > best[0] + 1e-15:
            best = (score, c, fr.profit, fr.normalized)
    _, c, profit, norm = best
    return ReferenceChoice(candidate=c, per_seed_profit=profit, per_seed_normalized=norm)


def _gross_eff(results) -> np.ndarray:
    return np.array([(r.W + r.audit_cost) / r.sstar for r in results])


def evaluate_gain(cell: Cell, family: Family, attack_knobs: dict, reference: ReferenceChoice, cache: SeedCache) -> GainResult:
    attack = run_focal(cell, lambda: family.make(attack_knobs), cache)
    clipped = run_focal(cell, lambda: family.make(family.project(attack_knobs)), cache)
    ref = run_focal(cell, reference.candidate.policy_factory, cache)
    honest = run_focal(cell, HonestMax, cache)
    scale = np.array([r.sstar / cell.cfg.N for r in attack.results])
    inflation = (attack.profit - clipped.profit) / scale
    selection = (clipped.profit - reference.per_seed_profit) / scale
    return GainResult(gain=inflation + selection, inflation_term=inflation, selection_term=selection,
                      eff_attack=_gross_eff(attack.results), eff_clip=_gross_eff(clipped.results),
                      eff_ref=_gross_eff(ref.results), eff_honest=_gross_eff(honest.results),
                      profit_attack=attack.profit, profit_clip=clipped.profit)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_reference.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/reference.py tests/test_reference.py
git commit -m "feat: twin search, last-step reference selection, gain decomposition with clipped-attack run"
```

---

### Task 7: Candidate bank

**Files:**
- Create: `sim/bank.py`
- Test: `tests/test_bank.py`

**Interfaces:**
- Produces: `Bank()` with `add(family_name, knobs, origin: str)`, `members_for(family_name) -> list[dict]` (typed filter: D1 members enter D2 cells through `embed_d1_in_d2`; D2 members never enter D1; corners of D2 included once; duplicates removed by rounding knobs to 6 decimals), `evaluate(cell, family, cache) -> list[tuple[dict, float, str]]` sorted by mean normalized profit, `truthful_members_for(family_name)` (members with `clip == 1`, for reference selection), `transfer_table(cells_results) -> list[dict]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_bank.py
import pytest
from sim.bank import Bank
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


def test_typed_filter_and_dedupe():
    b = Bank()
    b.add("D1", {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="B1/D1/0.05")
    b.add("D1", {"u": 0.5000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="dup")
    b.add("D2", {"u0": 0.1, "m0": 0.2, "s": 0.0, "d": 0.5, "r": 0.1, "w": 0.0, "clip": 1}, origin="B2/D2/0.05")
    d1 = b.members_for("D1"); d2 = b.members_for("D2")
    assert len(d1) == 1                      # the D2 member never enters D1, duplicate removed
    assert any(m.get("d") == 0.0 and m["u0"] == 0.5 for m in d2)   # D1 member embedded
    assert len(b.truthful_members_for("D2")) == 1


def test_evaluate_ranks_members():
    b = Bank()
    b.add("D1", {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, origin="cheat")
    b.add("D1", {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}, origin="honest")
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    ranked = b.evaluate(cell, D1, SeedCache())
    assert ranked[0][2] == "cheat" and ranked[0][1] > ranked[-1][1]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_bank.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.bank'`

- [ ] **Step 3: Write the implementation**

```python
# sim/bank.py
from __future__ import annotations

from dataclasses import dataclass, field

from .cell import Cell, SeedCache, run_focal
from .policies.families import D2, FAMILIES, Family, embed_d1_in_d2


def _key(knobs: dict) -> tuple:
    return tuple(sorted((k, round(float(v), 6)) for k, v in knobs.items()))


@dataclass
class Bank:
    entries: list = field(default_factory=list)   # (family_name, knobs, origin)

    def add(self, family_name: str, knobs: dict, origin: str) -> None:
        if family_name not in FAMILIES:
            raise ValueError(f"unknown family {family_name}")
        if not any(f == family_name and _key(k) == _key(knobs) for f, k, _ in self.entries):
            self.entries.append((family_name, dict(knobs), origin))

    def _compatible(self, target: str):
        out, seen = [], set()
        for f, k, origin in self.entries:
            if f == target:
                m = dict(k)
            elif f == "D1" and target == "D2":
                m = embed_d1_in_d2(k)
            else:
                continue
            key = _key(m)
            if key not in seen:
                seen.add(key); out.append((m, origin))
        if target == "D2":
            for c in D2.corners():
                key = _key(c)
                if key not in seen:
                    seen.add(key); out.append((c, "corner"))
        return out

    def members_for(self, family_name: str) -> list[dict]:
        return [m for m, _ in self._compatible(family_name)]

    def truthful_members_for(self, family_name: str) -> list[dict]:
        return [m for m, _ in self._compatible(family_name) if m.get("clip") == 1]

    def evaluate(self, cell: Cell, family: Family, cache: SeedCache) -> list[tuple[dict, float, str]]:
        scored = []
        for m, origin in self._compatible(family.name):
            fr = run_focal(cell, lambda m=m: family.make(m), cache)
            scored.append((m, float(fr.normalized.mean()), origin))
        scored.sort(key=lambda t: -t[1])
        return scored

    @staticmethod
    def transfer_table(cells_results: dict) -> list[dict]:
        """cells_results: cell name -> (incumbent value, best bank value, best bank origin)."""
        return [{"cell": name, "incumbent": inc, "best_bank": best, "origin": origin, "improved": best > inc + 1e-12}
                for name, (inc, best, origin) in cells_results.items()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_bank.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/bank.py tests/test_bank.py
git commit -m "feat: candidate bank with typed compatibility filter and transfer table"
```

---

### Task 8: Calibration of S_hat, n_FB, m, alpha, and B

**Files:**
- Create: `sim/calibrate.py`, `scripts/calibrate.py`
- Test: `tests/test_calibrate.py`

**Interfaces:**
- Produces:
  - `first_best_served(cfg, values_t) -> int` (jobs served in the first-best assignment, pairs with positive weight).
  - `calibrate(cfg_base, seeds, rho, beta) -> Calibration(S_hat, n_FB, m, alpha, budget)`.
  - `apply_calibration(cfg_base, cal) -> MarketConfig` with `alpha` and `budget` set.
  - `market_config_from_locked(locked) -> MarketConfig` (the locked market block with the default provider table; `alpha` and `budget` zero until calibrated).
  - `scripts/calibrate.py --rho 0.2 --beta 0.05 --out experiments/calibration.json`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_calibrate.py
import json, subprocess, sys
import numpy as np
import pytest
from sim.calibrate import calibrate, apply_calibration, first_best_served, market_config_from_locked
from sim.config import MarketConfig, ProviderParams
from sim.locked import load_locked


def test_first_best_served_counts_positive_pairs():
    cfg = MarketConfig(N=1, J=3, T=1, sigma=0.0, e=0.0, v_min=0.6, v_max=2.0,
                       providers=(ProviderParams(q_max=1.0, a=0.0, b=0.5, k=2),), alpha=0.0, budget=0.0)
    assert first_best_served(cfg, np.array([2.0, 1.0, 0.6])) == 2


def test_calibration_defines_alpha_and_budget():
    cfg = market_config_from_locked(load_locked())
    cal = calibrate(cfg, seeds=[4000, 4001], rho=0.2, beta=0.05)
    assert cal.S_hat > 0 and cal.n_FB > 0
    assert cal.m == pytest.approx(cal.S_hat / cal.n_FB)
    assert cal.alpha == pytest.approx(0.2 * cal.m) and cal.budget == pytest.approx(0.05 * cal.S_hat)
    cfg2 = apply_calibration(cfg, cal)
    cfg2.validate()
    assert cfg2.alpha == cal.alpha and cfg2.budget == cal.budget


def test_calibrate_script_writes_json(tmp_path):
    out = tmp_path / "cal.json"
    subprocess.run([sys.executable, "scripts/calibrate.py", "--rho", "0.2", "--beta", "0.05", "--seeds", "2",
                    "--out", str(out)], check=True)
    cal = json.loads(out.read_text())
    assert set(cal) >= {"S_hat", "n_FB", "m", "alpha", "budget", "rho", "beta", "seeds"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_calibrate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.calibrate'`

- [ ] **Step 3: Write the implementation**

```python
# sim/calibrate.py
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from scipy.optimize import linear_sum_assignment

from .config import MarketConfig
from .firstbest import first_best_episode
from .rng import make_draws


@dataclass(frozen=True)
class Calibration:
    S_hat: float
    n_FB: float
    m: float
    alpha: float
    budget: float
    rho: float
    beta: float
    seeds: tuple

    def as_dict(self) -> dict:
        d = asdict(self); d["seeds"] = list(self.seeds); return d


def first_best_served(cfg: MarketConfig, values_t: np.ndarray) -> int:
    q_full = np.array([p.q_max for p in cfg.providers]); cost_full = cfg.cost_full
    owner = np.repeat(np.arange(cfg.N), [p.k for p in cfg.providers])
    w = np.maximum(values_t[None, :] * q_full[owner][:, None] - cost_full[owner][:, None], 0.0)
    rows, cols = linear_sum_assignment(w, maximize=True)
    return int((w[rows, cols] > 0).sum())


def calibrate(cfg_base: MarketConfig, seeds, rho: float, beta: float) -> Calibration:
    totals, served = [], []
    for s in seeds:
        d = make_draws(cfg_base, int(s))
        totals.append(first_best_episode(cfg_base, d))
        served.append(sum(first_best_served(cfg_base, d.values[t]) for t in range(cfg_base.T)))
    S_hat = float(np.mean(totals)); n_FB = float(np.mean(served))
    m = S_hat / n_FB
    return Calibration(S_hat=S_hat, n_FB=n_FB, m=m, alpha=rho * m, budget=beta * S_hat, rho=float(rho), beta=float(beta),
                       seeds=tuple(int(s) for s in seeds))


def apply_calibration(cfg: MarketConfig, cal: Calibration) -> MarketConfig:
    return MarketConfig(N=cfg.N, J=cfg.J, T=cfg.T, sigma=cfg.sigma, e=cfg.e, v_min=cfg.v_min, v_max=cfg.v_max,
                        providers=cfg.providers, alpha=cal.alpha, budget=cal.budget)


def market_config_from_locked(locked: dict) -> MarketConfig:
    base = MarketConfig.default()
    mk = locked["market"]
    return MarketConfig(N=int(mk["N"]), J=int(mk["J"]), T=int(mk["T"]), sigma=float(mk["sigma"]), e=float(mk["e"]),
                        v_min=base.v_min, v_max=base.v_max, providers=base.providers, alpha=0.0, budget=0.0)
```

```python
# scripts/calibrate.py
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import calibrate, market_config_from_locked
from sim.locked import load_locked, seeds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rho", type=float, required=True)
    ap.add_argument("--beta", type=float, required=True)
    ap.add_argument("--seeds", type=int, default=20, help="how many calibration seeds to use")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lk = load_locked()
    cfg = market_config_from_locked(lk)
    cal = calibrate(cfg, seeds(lk, "calibration")[: args.seeds], args.rho, args.beta)
    Path(args.out).write_text(json.dumps(cal.as_dict(), indent=2, sort_keys=True) + "\n")
    print(json.dumps(cal.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_calibrate.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/calibrate.py scripts/calibrate.py tests/test_calibrate.py
git commit -m "feat: calibration of S_hat, n_FB, m, alpha, and budget from the locked market"
```

---

### Task 9: Positions, headline selection, and the search checks

**Files:**
- Create: `sim/positions.py`, `sim/search_checks.py`
- Test: `tests/test_positions_checks.py`

**Interfaces:**
- Produces:
  - `positions(cfg) -> dict[str, int]` with keys `low, median, high` by `b_i q_max_i` (ties by index); `median` is the middle element of the sorted order.
  - `headline_position(gain_by_position: dict[str, float]) -> str` (highest mean dev-train gain, tie order `low, median, high`).
  - `restart_spread(result: SearchResult) -> float` (max minus min of restart bests).
  - `doubling_check(cell, family, cache, settings, seed) -> DoublingCheck(base_f, doubled_f, clip0_f, clip1_f, mixed_f, delta)`: base search; doubled budget split half between a `clip` fixed at 0 search and a `clip` fixed at 1 search; `delta = doubled_f - base_f` where `doubled_f = max(clip0_f, clip1_f, base_f)`.
  - `twin_vs_honest(cell, family, cache, twin_result) -> float` (twin objective minus honest-max objective; the check passes when `>= -0.01`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_positions_checks.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1
from sim.positions import positions, headline_position
from sim.search import SearchSettings
from sim.search_checks import restart_spread, doubling_check, twin_vs_honest
from sim.reference import twin_search


def test_positions_by_b_times_qmax():
    cfg = MarketConfig.default()
    pos = positions(cfg)
    score = [p.b * p.q_max for p in cfg.providers]
    order = sorted(range(cfg.N), key=lambda i: (score[i], i))
    assert pos == {"low": order[0], "median": order[cfg.N // 2], "high": order[-1]}
    assert headline_position({"low": 0.1, "median": 0.3, "high": 0.3}) == "median"


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=24, reeval_every=10, near_corner=0.02, sobol_seed=3)


def test_doubling_check_and_spread_and_twin_vs_honest():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    dc = doubling_check(cell, D1, cache, SMALL, seed=0)
    assert dc.doubled_f >= dc.base_f - 1e-12 and np.isfinite(dc.clip0_f) and np.isfinite(dc.clip1_f)
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    assert restart_spread(tw) >= 0.0
    assert twin_vs_honest(cell, D1, cache, tw) >= -0.01
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_positions_checks.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.positions'`

- [ ] **Step 3: Write the implementation**

```python
# sim/positions.py
from __future__ import annotations

from .config import MarketConfig

ORDER = ("low", "median", "high")


def positions(cfg: MarketConfig) -> dict[str, int]:
    score = [p.b * p.q_max for p in cfg.providers]
    order = sorted(range(cfg.N), key=lambda i: (score[i], i))
    return {"low": order[0], "median": order[cfg.N // 2], "high": order[-1]}


def headline_position(gain_by_position: dict[str, float]) -> str:
    best, best_v = None, None
    for name in ORDER:
        if name in gain_by_position and (best_v is None or gain_by_position[name] > best_v):
            best, best_v = name, gain_by_position[name]
    return best
```

```python
# sim/search_checks.py
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .cell import Cell, SeedCache, run_focal
from .policies.families import Family
from .policies.honest import HonestMax
from .search import SearchResult, SearchSettings, cma_search, make_objective


def restart_spread(result: SearchResult) -> float:
    return float(max(result.restart_bests) - min(result.restart_bests))


@dataclass
class DoublingCheck:
    base_f: float
    doubled_f: float
    clip0_f: float
    clip1_f: float
    mixed_f: float
    delta: float


def _fixed_clip_objective(cell: Cell, family: Family, cache: SeedCache, clip: int):
    base = make_objective(cell, family, cache)
    idx = family.knobs.index("clip")
    big = 30.0 if clip == 1 else -30.0

    def obj(x: np.ndarray) -> float:
        y = np.array(x, dtype=float); y[idx] = big
        return base(y)
    return obj


def doubling_check(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int) -> DoublingCheck:
    base = cma_search(make_objective(cell, family, cache), family, settings, seed)
    half = replace(settings, evals_per_restart=settings.evals_per_restart)   # same budget per branch = doubled in total
    c0 = cma_search(_fixed_clip_objective(cell, family, cache, 0), family, half, seed + 100)
    c1 = cma_search(_fixed_clip_objective(cell, family, cache, 1), family, half, seed + 200)
    doubled = max(base.best_f, c0.best_f, c1.best_f)
    return DoublingCheck(base_f=base.best_f, doubled_f=doubled, clip0_f=c0.best_f, clip1_f=c1.best_f,
                         mixed_f=base.best_f, delta=doubled - base.best_f)


def twin_vs_honest(cell: Cell, family: Family, cache: SeedCache, twin_result: SearchResult) -> float:
    honest = run_focal(cell, HonestMax, cache)
    return float(twin_result.best_f - honest.normalized.mean())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_positions_checks.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/positions.py sim/search_checks.py tests/test_positions_checks.py
git commit -m "feat: adversary positions, headline selection, restart spread, clip-split doubling check, twin-vs-honest check"
```

---

### Task 10: Baseline tuning on the locked grid

**Files:**
- Create: `sim/tuning.py`, `scripts/tune_baselines.py`
- Test: `tests/test_tuning.py`

**Interfaces:**
- Produces:
  - `price_grid(cfg, f_values) -> list[tuple[float, float, float]]` (27 ordered triples).
  - `tuning_grid(rule_name, cfg, locked) -> list[dict]`: B1 has price triples only; B2 has price triples x tol x L; B3 has tol x L.
  - `rule_from_params(rule_name, params) -> Mechanism`.
  - `score_point(rule_name, params, cfg, locked, cache, family=D2) -> TuningScore(eff, gain, margin)` using the inner search at the median position with the twin and last-step reference; `margin = min((eff - 0.90)/0.90, (0.30 - gain)/0.30)`.
  - `tune(rule_name, cfg, locked, cache, inner_override: dict | None = None) -> TuningResult(best_params, scores: list, rechecked: list)`.
  - `scripts/tune_baselines.py --calibration experiments/calibration.json --rule B2 --out experiments/tuned_B2.json [--quick]`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tuning.py
import pytest
from sim.cell import SeedCache
from sim.config import MarketConfig
from sim.locked import load_locked
from sim.tuning import price_grid, tuning_grid, rule_from_params, score_point, tune


def test_price_grid_is_27_ordered_positive_triples():
    cfg = MarketConfig.default()
    g = price_grid(cfg, [0.5, 0.7, 0.9])
    assert len(g) == 27
    for p1, p2, p3 in g:
        assert 0 < p1 < p2 < p3
    assert max(t[2] for t in g) == pytest.approx(0.9 * cfg.q90)
    assert min(t[2] for t in g) == pytest.approx(float(cfg.cost_full.min()))


def test_tuning_grids_sizes_and_rule_construction():
    lk = load_locked(); cfg = MarketConfig.default()
    assert len(tuning_grid("B1", cfg, lk)) == 27
    assert len(tuning_grid("B2", cfg, lk)) == 27 * 3 * 3
    assert len(tuning_grid("B3", cfg, lk)) == 9
    r = rule_from_params("B2", tuning_grid("B2", cfg, lk)[0])
    assert r.name == "B2_posted_random_audit" and r.L in (10, 20, 50)


def test_score_point_and_quick_tune_terminate():
    lk = load_locked()
    c = MarketConfig.default()
    cfg = MarketConfig(N=4, J=12, T=10, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers[6:10], alpha=0.05, budget=0.3)
    cache = SeedCache()
    quick = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16}
    params = {"P1": 0.9, "P2": 1.0, "P3": 1.2, "tol": 0.12, "L": 10}   # tier 3 unaffordable for most jobs
    sc = score_point("B2", params, cfg, lk, cache, inner_override=quick)
    assert sc.margin <= 0.0 and sc.eff < 0.9
    res = tune("B2", cfg, lk, cache, inner_override=quick, grid_limit=3)
    assert res.best_params in [s["params"] for s in res.scores] and len(res.rechecked) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_tuning.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.tuning'`

- [ ] **Step 3: Write the implementation**

```python
# sim/tuning.py
from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product

import numpy as np

from .cell import Cell, SeedCache
from .config import MarketConfig
from .locked import seeds as locked_seeds
from .mechanisms.posted import PostedPrices
from .mechanisms.posted_audit import PostedRandomAudit
from .mechanisms.second_score import SecondScore
from .policies.families import D2, Family
from .positions import positions
from .reference import evaluate_gain, reference_candidates, select_reference, twin_search
from .search import SearchSettings, cma_search, make_objective, settings_from_locked


def price_grid(cfg: MarketConfig, f_values) -> list[tuple[float, float, float]]:
    c_min = float(cfg.cost_full.min()); p_top = 0.9 * cfg.q90
    p3s = np.geomspace(c_min, p_top, 3)
    out = []
    for p3 in p3s:
        for f2 in f_values:
            for f1 in f_values:
                p2 = f2 * p3; p1 = f1 * p2
                out.append((float(p1), float(p2), float(p3)))
    return out


def tuning_grid(rule_name: str, cfg: MarketConfig, locked: dict) -> list[dict]:
    tg = locked["tuning"]
    prices = price_grid(cfg, tg["price_f"])
    if rule_name == "B1":
        return [{"P1": a, "P2": b, "P3": c} for a, b, c in prices]
    if rule_name == "B2":
        return [{"P1": a, "P2": b, "P3": c, "tol": float(t), "L": int(L)}
                for (a, b, c), t, L in product(prices, tg["tol"], tg["L"])]
    if rule_name == "B3":
        return [{"tol": float(t), "L": int(L)} for t, L in product(tg["tol"], tg["L"])]
    raise ValueError(rule_name)


def rule_from_params(rule_name: str, params: dict):
    if rule_name == "B1":
        return PostedPrices(params["P1"], params["P2"], params["P3"])
    if rule_name == "B2":
        return PostedRandomAudit(params["P1"], params["P2"], params["P3"], tol=params["tol"], L=params["L"])
    if rule_name == "B3":
        return SecondScore(tol=params["tol"], L=params["L"])
    raise ValueError(rule_name)


@dataclass
class TuningScore:
    eff: float
    gain: float
    margin: float


def _inner_settings(locked: dict, override: dict | None, recheck: bool) -> tuple[SearchSettings, list[int]]:
    tg = dict(locked["tuning"]); tg.update(override or {})
    base = settings_from_locked(locked)
    tr = locked_seeds(locked, "dev_train")
    if recheck:
        evals = int(tg.get("recheck_evals", base.evals_per_restart)); restarts = int(tg.get("recheck_restarts", base.restarts))
        return replace(base, evals_per_restart=evals, restarts=restarts), tr[: int(tg.get("recheck_seeds", len(tr)))]
    return replace(base, restarts=int(tg["inner_restarts"]), evals_per_restart=int(tg["inner_evals"])), tr[: int(tg["inner_seeds"])]


def score_point(rule_name: str, params: dict, cfg: MarketConfig, locked: dict, cache: SeedCache,
                family: Family = D2, inner_override: dict | None = None, recheck: bool = False) -> TuningScore:
    settings, seeds = _inner_settings(locked, inner_override, recheck)
    focal = positions(cfg)["median"]
    cell = Cell(cfg=cfg, rule_factory=lambda: rule_from_params(rule_name, params), focal=focal, seeds=tuple(seeds),
                name=f"tune/{rule_name}")
    tw = twin_search(cell, family, cache, settings, seed=0)
    attack = cma_search(make_objective(cell, family, cache), family, settings, seed=1)
    ref = select_reference(cell, reference_candidates(cell, family, attack.best_knobs, tw, []), cache)
    g = evaluate_gain(cell, family, attack.best_knobs, ref, cache)
    eff, gain = float(g.eff_attack.mean()), float(g.gain.mean())
    return TuningScore(eff=eff, gain=gain, margin=min((eff - 0.90) / 0.90, (0.30 - gain) / 0.30))


@dataclass
class TuningResult:
    best_params: dict
    scores: list
    rechecked: list


def tune(rule_name: str, cfg: MarketConfig, locked: dict, cache: SeedCache, inner_override: dict | None = None,
         grid_limit: int | None = None) -> TuningResult:
    grid = tuning_grid(rule_name, cfg, locked)
    if grid_limit is not None:
        grid = grid[:grid_limit]
    scores = []
    for params in grid:
        sc = score_point(rule_name, params, cfg, locked, cache, inner_override=inner_override)
        scores.append({"params": params, "eff": sc.eff, "gain": sc.gain, "margin": sc.margin})
    scores.sort(key=lambda s: -s["margin"])
    top = int((inner_override or {}).get("recheck_top", locked["tuning"]["recheck_top"]))
    rechecked = []
    for s in scores[:top]:
        sc = score_point(rule_name, s["params"], cfg, locked, cache, inner_override=inner_override, recheck=True)
        rechecked.append({"params": s["params"], "eff": sc.eff, "gain": sc.gain, "margin": sc.margin})
    rechecked.sort(key=lambda s: -s["margin"])
    return TuningResult(best_params=rechecked[0]["params"], scores=scores, rechecked=rechecked)
```

```python
# scripts/tune_baselines.py
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import Calibration, apply_calibration, market_config_from_locked
from sim.cell import SeedCache
from sim.locked import load_locked
from sim.tuning import tune


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--rule", required=True, choices=["B1", "B2", "B3"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true", help="tiny budgets for a smoke run")
    args = ap.parse_args()
    lk = load_locked()
    cal_d = json.loads(Path(args.calibration).read_text())
    cal = Calibration(**{k: (tuple(v) if k == "seeds" else v) for k, v in cal_d.items()})
    cfg = apply_calibration(market_config_from_locked(lk), cal)
    override = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16} if args.quick else None
    res = tune(args.rule, cfg, lk, SeedCache(), inner_override=override, grid_limit=3 if args.quick else None)
    Path(args.out).write_text(json.dumps({"rule": args.rule, "best_params": res.best_params, "rechecked": res.rechecked,
                                          "scores": res.scores}, indent=2) + "\n")
    print(json.dumps(res.best_params))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tuning.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/tuning.py scripts/tune_baselines.py tests/test_tuning.py
git commit -m "feat: baseline tuning on the locked grid with inner search, min-margin objective, and top-k recheck"
```

---

### Task 11: Cell manifest and the parallel sweep runner

**Files:**
- Create: `sim/manifest.py`, `scripts/manifest.py`, `scripts/sweep.py`
- Test: `tests/test_manifest.py`

**Interfaces:**
- Produces:
  - `CellSpec(section, rule, family, beta, rho, position, kind, runs: int, post_lock: bool)`.
  - `enumerate_manifest(locked, rules: list[str]) -> list[CellSpec]` covering: `development` (rules x {D1, D2} x beta grid x positions as per spec, attack search runs), `twins` (same cells, twin search runs), `references` (reference candidate evaluations, upper bound), `controls` (corner controls, doubling checks on two cells per rule, restart spread), `rho_sweep` (beta headline only, D2 and twin, median position, rho in sweep minus default), `all_deviators`, `tuning` (grid size x inner runs plus rechecks), `bank` (post-lock estimate), `ablation` (post-lock estimate).
  - `totals(cells) -> dict[str, int]` by section and `pre_lock`/`post_lock`.
  - `scripts/manifest.py` prints the table and the totals, with the core-hour estimate at a given ms per run.
  - `scripts/sweep.py --section development --rules B1,B2,B3 --calibration experiments/calibration.json --workers 8 --out results/` runs each cell (search, twin, reference, gain on dev-val seeds) in a process pool and writes one CSV row per (cell, seed) plus a JSON of best knobs; `--limit N` and `--quick` for smoke runs.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_manifest.py
import subprocess, sys, json
from pathlib import Path
import pytest
from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals


def test_manifest_counts_match_spec_arithmetic():
    lk = load_locked()
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    t = totals(cells)
    # development: 3 rules x 2 families x (5 budgets x 1 position + 1 budget x 3 positions) x 5 restarts x 300 evals x 5 seeds
    assert t["development"] == 3 * 2 * (5 + 3) * 5 * 300 * 5
    assert t["twins"] == t["development"]
    assert t["rho_sweep"] == 2 * 2 * 3 * 7500
    assert t["all_deviators"] == 3 * 10 * 300 * 3 * 2
    assert t["tuning"] > 400_000 and t["pre_lock"] > 1_000_000
    assert all(c.post_lock for c in cells if c.section in ("bank", "ablation"))


def test_manifest_script_prints_totals():
    out = subprocess.run([sys.executable, "scripts/manifest.py", "--ms-per-run", "45"], check=True, capture_output=True, text=True).stdout
    assert "pre_lock" in out and "core-hours" in out


def test_sweep_quick_run_writes_outputs(tmp_path):
    cal = {"S_hat": 1.0, "n_FB": 1.0, "m": 1.0, "alpha": 0.05, "budget": 0.3, "rho": 0.05, "beta": 0.05, "seeds": [4000]}
    calp = tmp_path / "cal.json"; calp.write_text(json.dumps(cal))
    subprocess.run([sys.executable, "scripts/sweep.py", "--section", "development", "--rules", "B1", "--calibration", str(calp),
                    "--workers", "1", "--limit", "1", "--quick", "--out", str(tmp_path / "res")], check=True)
    rows = (tmp_path / "res" / "development.csv").read_text().splitlines()
    assert rows[0].startswith("cell,rule,family,beta,rho,position,seed,")
    assert len(rows) >= 2
    assert (tmp_path / "res" / "development_best.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.manifest'`

- [ ] **Step 3: Write the implementation**

```python
# sim/manifest.py
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class CellSpec:
    section: str
    rule: str
    family: str
    beta: float
    rho: float
    position: str
    kind: str
    runs: int
    post_lock: bool


def enumerate_manifest(locked: dict, rules: list[str]) -> list[CellSpec]:
    s = locked["search"]; tg = locked["tuning"]; ad = locked["all_deviators"]
    per_search = s["restarts"] * s["evals_per_restart"]
    n_train = len(locked["seeds"]["dev_train"])
    betas = [float(b) for b in locked["beta_grid"]]; bh = float(locked["beta_headline"])
    rho0 = float(locked["rho"]["default"])
    cells: list[CellSpec] = []
    for rule in rules:
        for fam in ("D1", "D2"):
            for beta in betas:
                for pos in (locked["positions"] if beta == bh else ["median"]):
                    runs = per_search * n_train
                    cells.append(CellSpec("development", rule, fam, beta, rho0, pos, "attack_search", runs, False))
                    cells.append(CellSpec("twins", rule, fam, beta, rho0, pos, "twin_search", runs, False))
                    cells.append(CellSpec("references", rule, fam, beta, rho0, pos, "reference_eval", 8 * n_train, False))
        # controls: corners (D1 32, D2 128) on every cell is counted once per rule and family at the headline budget
        for fam, ncorner in (("D1", 32), ("D2", 128)):
            cells.append(CellSpec("controls", rule, fam, bh, rho0, "median", "corner_controls", ncorner * n_train, False))
            cells.append(CellSpec("controls", rule, fam, bh, rho0, "median", "doubling_check_x2", 2 * 2 * per_search * n_train, False))
        for rho in [float(r) for r in locked["rho"]["sweep"] if float(r) != rho0]:
            for kind in ("attack_search", "twin_search"):
                cells.append(CellSpec("rho_sweep", rule, "D2", bh, rho, "median", kind, per_search * n_train, False))
        cells.append(CellSpec("all_deviators", rule, "D2", bh, rho0, "all", "iterated_br",
                              ad["sweeps"] * locked["market"]["N"] * ad["restarts"] * ad["evals"] * ad["seeds"] * 2, False))
        grid = {"B1": 27, "B2": 27 * len(tg["tol"]) * len(tg["L"]), "B3": len(tg["tol"]) * len(tg["L"])}[rule]
        inner = tg["inner_restarts"] * tg["inner_evals"] * tg["inner_seeds"] * 2
        recheck = tg["recheck_top"] * per_search * n_train * 2
        cells.append(CellSpec("tuning", rule, "D2", bh, rho0, "median", "grid_inner_search", grid * inner + recheck, False))
    cells.append(CellSpec("bank", "all", "D1+D2", bh, rho0, "median", "bank_eval", 4 * 2 * 6 * 192 * n_train + 64 * n_train, True))
    cells.append(CellSpec("ablation", "proposed", "D1+D2", bh, rho0, "all", "ablation_search", 2 * 3 * 2 * per_search * n_train, True))
    return cells


def totals(cells: list[CellSpec]) -> dict[str, int]:
    t: dict[str, int] = {}
    for c in cells:
        t[c.section] = t.get(c.section, 0) + c.runs
        key = "post_lock" if c.post_lock else "pre_lock"
        t[key] = t.get(key, 0) + c.runs
    return t


def rows(cells: list[CellSpec]) -> list[dict]:
    return [asdict(c) for c in cells]
```

```python
# scripts/manifest.py
from __future__ import annotations

import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--ms-per-run", type=float, default=45.0)
    args = ap.parse_args()
    cells = enumerate_manifest(load_locked(), args.rules.split(","))
    t = totals(cells)
    for k in sorted(t):
        hours = t[k] * args.ms_per_run / 3.6e6
        print(f"{k:14s} {t[k]:>12,d} runs  {hours:8.1f} core-hours at {args.ms_per_run:.0f} ms/run")


if __name__ == "__main__":
    main()
```

```python
# scripts/sweep.py
from __future__ import annotations

import argparse, csv, json, sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.bank import Bank
from sim.calibrate import Calibration, apply_calibration, market_config_from_locked
from sim.cell import Cell, SeedCache
from sim.config import MarketConfig
from sim.locked import load_locked, seeds as locked_seeds
from sim.manifest import enumerate_manifest
from sim.policies.families import FAMILIES
from sim.positions import positions
from sim.reference import evaluate_gain, reference_candidates, select_reference, twin_search
from sim.search import cma_search, make_objective, settings_from_locked
from sim.tuning import rule_from_params

DEFAULT_PARAMS = {"B1": {"P1": 0.25, "P2": 0.40, "P3": 0.55},
                  "B2": {"P1": 0.25, "P2": 0.40, "P3": 0.55, "tol": 0.12, "L": 10},
                  "B3": {"tol": 0.12, "L": 10}}


def load_params(rule: str, tuned_dir: Path | None) -> dict:
    if tuned_dir is not None and (tuned_dir / f"tuned_{rule}.json").exists():
        return json.loads((tuned_dir / f"tuned_{rule}.json").read_text())["best_params"]
    return DEFAULT_PARAMS[rule]


def run_cell_job(args: tuple) -> dict:
    spec, cfg_dict, locked, params, quick = args
    cfg = MarketConfig(**{**cfg_dict, "providers": tuple(__import__("sim.config", fromlist=["ProviderParams"]).ProviderParams(*p)
                                                           for p in cfg_dict["providers"])})
    settings = settings_from_locked(locked)
    if quick:
        settings = replace(settings, restarts=1, evals_per_restart=16)
    train = tuple(locked_seeds(locked, "dev_train")[: (1 if quick else None)])
    val = tuple(locked_seeds(locked, "dev_val")[: (2 if quick else None)])
    fam = FAMILIES[spec["family"]]
    focal = positions(cfg)[spec["position"]]
    cache = SeedCache()
    cell = Cell(cfg=cfg, rule_factory=lambda: rule_from_params(spec["rule"], params), focal=focal, seeds=train, name=spec["name"])
    tw = twin_search(cell, fam, cache, settings, seed=0)
    attack = cma_search(make_objective(cell, fam, cache), fam, settings, seed=1)
    ref = select_reference(cell, reference_candidates(cell, fam, attack.best_knobs, tw, []), cache)
    cell_val = Cell(cfg=cfg, rule_factory=cell.rule_factory, focal=focal, seeds=val, name=spec["name"])
    ref_val = select_reference(cell_val, [ref.candidate], cache)
    g = evaluate_gain(cell_val, fam, attack.best_knobs, ref_val, cache)
    rows = []
    for k, seed in enumerate(val):
        rows.append({"cell": spec["name"], "rule": spec["rule"], "family": spec["family"], "beta": spec["beta"], "rho": spec["rho"],
                     "position": spec["position"], "seed": seed, "gain": g.gain[k], "inflation_term": g.inflation_term[k],
                     "selection_term": g.selection_term[k], "eff_attack": g.eff_attack[k], "eff_clip": g.eff_clip[k],
                     "eff_ref": g.eff_ref[k], "eff_honest": g.eff_honest[k]})
    return {"rows": rows, "best": {"cell": spec["name"], "attack_knobs": attack.best_knobs, "attack_f": attack.best_f,
                                   "twin_knobs": tw.best_knobs, "twin_f": tw.best_f, "reference": ref.candidate.name,
                                   "restart_bests": attack.restart_bests}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--section", required=True, choices=["development", "rho_sweep"])
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", default=None)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lk = load_locked()
    cal_d = json.loads(Path(args.calibration).read_text())
    cal = Calibration(**{k: (tuple(v) if k == "seeds" else v) for k, v in cal_d.items()})
    base = market_config_from_locked(lk)
    specs = [c for c in enumerate_manifest(lk, args.rules.split(",")) if c.section == args.section and c.kind == "attack_search"]
    if args.limit:
        specs = specs[: args.limit]
    jobs = []
    for c in specs:
        cal_b = replace(cal, budget=c.beta * cal.S_hat, alpha=c.rho * cal.m) if args.section == "rho_sweep" else replace(cal, budget=c.beta * cal.S_hat)
        cfg = apply_calibration(base, cal_b)
        cfg_dict = {"N": cfg.N, "J": cfg.J, "T": cfg.T, "sigma": cfg.sigma, "e": cfg.e, "v_min": cfg.v_min, "v_max": cfg.v_max,
                    "providers": [(p.q_max, p.a, p.b, p.k) for p in cfg.providers], "alpha": cfg.alpha, "budget": cfg.budget}
        name = f"{c.rule}/{c.family}/beta{c.beta}/rho{c.rho}/{c.position}"
        jobs.append(({"name": name, "rule": c.rule, "family": c.family, "beta": c.beta, "rho": c.rho, "position": c.position},
                     cfg_dict, lk, load_params(c.rule, Path(args.tuned_dir) if args.tuned_dir else None), args.quick))
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(run_cell_job, jobs))
    rows = [r for res in results for r in res["rows"]]
    with open(out / f"{args.section}.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    (out / f"{args.section}_best.json").write_text(json.dumps([r["best"] for r in results], indent=2) + "\n")
    print(f"wrote {len(rows)} rows for {len(results)} cells to {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_manifest.py -v`
Expected: PASS (3 tests). The quick sweep runs one B1 cell at 16 evaluations on one training seed and two validation seeds.

- [ ] **Step 5: Commit**

```bash
git add sim/manifest.py scripts/manifest.py scripts/sweep.py tests/test_manifest.py
git commit -m "feat: cell manifest with run counts and a parallel sweep runner"
```

---

### Task 12: Spec implementation note and README status

**Files:**
- Modify: `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (section 14), `README.md` (Status)

- [ ] **Step 1: Append to section 14**

```
Implementation (plan 2A, search and families): identities separate from
entities with exit and re-entry at entry cost e; bans and bonds per identity,
profit per entity; H3 as a policy wrapper that exits after a failed audit;
D1 and D2 as families with logistic knob transforms and clip thresholded at
0.5; CMA-ES search with registered starts, a fixed evaluation budget per
restart, and corner controls outside the budget; twin search with the clip
forced; reference selected last among projected candidates; gain reported
as inflation term plus selection term with the clipped-attack run;
candidate bank with a typed compatibility filter; calibration of S_hat,
n_FB, m, alpha, and B from the locked market on calibration seeds; baseline
tuning on the locked grid with the min-margin objective and top-3 recheck;
cell manifest with run counts; parallel sweep runner. Seed namespaces
dev-train 1000-1004, dev-val 2000-2019, calibration 4000-4019; final-eval
held by the separate session.
```

- [ ] **Step 2: Update the README status**

Replace the README's `## Status` body with:

```
Week 2. Identities and H3, D1/D2 families, CMA-ES search with twins and
last-step reference selection, candidate bank, calibration, baseline tuning,
manifest, and sweep runner implemented. Plan 2B (intervals, coverage study,
claim script, lock tooling, model actors, custodian instructions) next.
```

- [ ] **Step 3: Run the whole suite**

Run: `uv run pytest -q`
Expected: all tests PASS

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md README.md
git commit -m "docs: record plan 2A implementation in the spec; README status"
```

---

## Self-review

**Spec coverage for this plan's scope.** Section 3 identity replacement and entry cost: Task 2. Section 4.2 tuning grid, inner search, objective, recheck: Task 10. Section 5.1 views with identity: Task 2. Section 5.2 honest-max, twin search, projected reference candidates selected last, decomposition: Task 6. Section 5.3 D1/D2 with recurrence and domains, transforms, registered starts, search budget, incumbent re-evaluation, corners, positions, headline selection, search checks (B1 fixture, doubling with clip split, restart spread, twin vs honest), workload manifest: Tasks 3, 5, 9, 11. Section 5.3 all-deviators: counted in the manifest (Task 11); its runner is deferred to plan 2B with the rho sweep already runnable here. Section 5.2/8 candidate bank with scope and typed filter: Task 7. Section 3 calibration constants: Task 8. Section 6 seed namespaces: Task 1. Section 6.2 H3: Task 2. Section 7 reference run, gain per entity, clipped-attack run, efficiency quadruple: Tasks 2 and 6. Not in this plan, by the stated split: interval algorithms, coverage study, `check_claim.py`, hashes and lock tooling, the model-actor harness, `describe()` rendering, the custodian bundle, `plot.py`, and the all-deviators runner.

**Placeholder scan.** None.

**Type consistency.** `Family.transform/inverse/project/make/corners/registered_starts`; `Cell(cfg, rule_factory, focal, seeds, name)`; `run_focal(cell, policy_factory, cache) -> FocalRun(profit, normalized, results)`; `cma_search(objective, family, settings, seed) -> SearchResult(best_x, best_knobs, best_f, restart_bests, evals, trace)`; `twin_search(cell, family, cache, settings, seed)`; `reference_candidates(cell, family, attack_knobs, twin_result, bank_members)`; `select_reference(cell, candidates, cache) -> ReferenceChoice(candidate, per_seed_profit, per_seed_normalized)`; `evaluate_gain(cell, family, attack_knobs, reference, cache) -> GainResult`; `Bank.add/members_for/truthful_members_for/evaluate`; `calibrate(cfg, seeds, rho, beta) -> Calibration`; `score_point/tune`; `enumerate_manifest/totals`. `EpisodeResult` gains `n_identities, entity_of, identity_profit` and keeps every plan 1 field.

**Review Focus.** Items 1 and 2: Task 2 tests. Item 3: Task 3 `test_make_returns_fresh_instances`. Item 4: Task 5 `test_flat_objective_terminates`. Item 5: Task 6 `test_abstention_wins_when_everything_loses_money`. Item 6: Task 10 `test_score_point_and_quick_tune_terminate`.
