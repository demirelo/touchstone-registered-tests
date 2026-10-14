# Touchstone plan 2A (version 2): identities, D2, search, reference selection, bank, calibration, tuning, manifest and sweep

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the core engine with identities and identity replacement (H3), the enforcement-ablation adapter, the D2 adaptive family, the pre-registered CMA-ES search with an evaluation archive, twin search, last-step reference selection from the bounded projected set, gain decomposition, the candidate bank pass, calibration, baseline tuning with dev-val rechecks, the all-deviators table, the search checks, and one schedule that both the manifest counts and the sweep executes, so that every pre-lock simulator run the spec names can be run from one locked configuration file and counted.

**Architecture:** Plan 1's engine stays the authority on money and admissibility. Identities are separate from entities inside `run_episode`: ledger columns, bans, capacity, and tie-break keys are per identity; profit is per entity; a retired identity is never marked in a rule's view. Families map an unbounded CMA-ES vector to a policy through a logistic transform and project any point to its truthful twin. An `Objective` evaluates exact knob dictionaries and keeps an archive of every evaluated point with its per-seed values and an inflation flag; the reference set and the incumbent rules of spec 5.2 are built from that archive. A `SeedCache` holds draws and S* per (market, seed) and counts runs. `sim/schedule.py` is the one place that says which runs a cell needs; `manifest.py` sums it and `sweep.py` executes it stage by stage (search, bank, reference, evaluate, checks, all-deviators), writing one JSON record per cell and stage.

**Tech Stack:** Python 3.12+, numpy, scipy, `cma` (pycma) for CMA-ES, `pyyaml` for the locked config, `concurrent.futures` for the sweep, pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5 plus the plan 1 implementation note). This plan implements sections 3 (identity replacement, entry cost, calibration constants), 4.0 (identity opacity), 4.1 (no-ban diagnostic), 4.2 (baseline tuning), 5.1 to 5.3 (families, twins, containment tests, search with incumbents and projection replacement, positions and headline selection, search checks, all-deviators, candidate bank, workload manifest and the full-path gate), 6 (seed namespaces, `locked.yaml` contents, `families.md`), 6.2 (H3), 7 (reference run, gain, clipped-attack run, efficiency quadruple, per-seed output schema), and the enforcement-ablation adapter of section 8. Plan 2B covers the interval algorithms, the coverage study, `check_claim.py`, the lock tooling and hash checks, the LLM and Jev actor harness with the `describe()` renderer and comprehension fixture, the custodian instructions for the sealed bundle, the token pilot, and `plot.py`. Nothing else is deferred.

**Scope split, stated once:** Plan 2A ends when `scripts/sweep.py --stage all` runs the development cells, the rho sweep, the H3 cells, the no-ban cells, the controls, the bank pass, reference selection, dev-val evaluation, headline selection, the search checks, and the all-deviators table from `locked.yaml` and a calibration file; `scripts/tune_baselines.py` runs the tuning grid; `scripts/manifest.py` reports run counts derived from the same schedule; and `scripts/bench_sweep.py` measures the full path. Nothing in this plan designs or runs a proposed rule, touches held-out families, or computes a confidence bound.

**Changes from version 1 (two reviews, both reject):** retired identities are no longer marked in the rule's view and fresh identities get their own tie-break keys (identity opacity); an exit takes effect in the round the policy makes it, so H3 re-enters in the round after a failure (ruling, recorded in Task 14); exits do not change bans or bond schedules; the search keeps an archive and the attack search carries the twin best and the honest-max point as incumbents and replaces its best by its projection when that scores higher; reference candidates come from the archive and the bank, in registered order with abstention first; `evaluate_gain` subtracts the reference profit on the seeds it is given; corner controls use exact knobs; the doubling check reports gain, attack objective, and reference objective; tuning rechecks score on dev-val; calibration validates its input and binds to the market; `locked.yaml` carries the provider table, the value distribution, the admissible-class constants, and the candidate order; the sweep has stages and calls the bank, the controls, and headline selection; the manifest derives counts from the schedule the sweep executes; the per-seed row schema carries every section 7 metric; the all-deviators runner, the H3 cells, the no-ban diagnostic, the enforcement-ablation adapter, `families.md`, and the full-path benchmark are in this plan; the four test defects of version 1 are fixed.

## Global Constraints

- All of plan 1's constraints remain (unit jobs, unclipped noise, truthful iff claim <= effort, read-only inputs to rules, admissible consequences, integer audits, action-independent draws, conservation each round).
- A rule may read only offers, values, its purchased audit results, its own memory, and the locked config; identity ids are opaque tokens, and a rule's decisions must be invariant to relabeling them (spec 4.0). A retired identity is indistinguishable in the view from an identity that stopped offering.
- An entity may drop its identity and re-enter under a fresh one at entry cost `e >= 0`, default `e = 0`; entry cost is a destroyed resource that enters surplus and the entity's profit (spec 3). An exit decision made in the action of round t takes effect in round t: the old identity is retired before offers, and the fresh identity makes round t's offer and pays `e` in round t (ruling: this is the "takes effect next round" of spec 3 step 8 read from the round whose outcome caused the decision; it matches Proposition B's immediate re-entry).
- A fresh identity has no history, no ban, and no bond; the exited identity's bans and bond keep their schedule as if it had stayed and had stopped serving, and its releases go to the entity (spec 4.0, 7).
- Profit is per entity across all its identities (spec 7).
- D1 knobs: `u, m in [0,1]`, `s in [0,0.3]`, `w in [0,2]`, `clip in {0,1}`. D2 knobs: `u0, m0 in [0,1]`, `s in [0,0.3]`, `d in [0,1]`, `r in [0,0.2]`, `w in [0,2]`, `clip in {0,1}`; D2 markup recurrence `m_{t+1} = m_t (1-d)` after a failed audit, else `min(m0, m_t + r m0)`, unchanged during a ban; D2 contains D1 at `d = r = 0` (spec 5.3).
- Knobs are mapped from the unbounded search space by a logistic transform; `clip` is a logistic coordinate thresholded at 0.5 (spec 5.3). Exact corners and registered incumbents are evaluated from knob dictionaries, never through the inverse transform.
- Search: CMA-ES, population 8, initial step 0.3, 5 restarts from registered points (near-honest at logit 0.02 on every knob with clip at logit 0.98, near-full-cheat at logit 0.98 with `s` and `clip` at logit 0.02, three Sobol points), 300 evaluations per restart including incumbent re-evaluation every 10 iterations; exact corners evaluated once each as controls outside the budget; the twin best and the honest-max point are registered incumbents of the attack search; the clip = 1 projection of the selected attack is evaluated and replaces the incumbent when it scores higher (spec 5.3, 5.2).
- The search objective is the mean over 5 dev-train seeds of per-seed normalized profit `pi / (S* / N)`; the reference is subtracted after reference selection, which is the last step before evaluation, after the attack search and the bank pass (spec 5.2, 5.3).
- Reference candidates, all in projected (`clip = 1`) form, in registered tie order: abstention, honest-max, the twin search's best point, the projection of the selected attack, the best archived clip = 1 point of the attack search, the best archived clip = 0 point that never inflated on dev-train (its observed value is its projected value, no new run), and the projection of every compatible bank member. Clip = 0 points that inflated are not admitted (spec 5.2).
- Three pre-registered positions by `b_i q_max_i` (lowest, median, highest); all three at `beta = 0.05`, median elsewhere; headline position selected per (rule, family) on dev-train gain (spec 5.3).
- Seed namespaces: dev-train (search objectives), dev-val (all pre-lock reporting and tuning rechecks), final-eval (custodian-held, never in this repo before the unseal), plus a calibration namespace disjoint from the three (spec 6; the calibration namespace is recorded in Task 14).
- Calibration: `S_hat` is the expected honest-max first-best surplus over T rounds on calibration seeds; `m = S_hat / n_FB`; `rho = alpha / m`, default 0.2; `B = beta S_hat`; every cell derives `alpha` and `B` from its own `(rho, beta)` and the one calibration (spec 3). `calibrate` refuses an invalid configuration.
- Tuning grid: 27 ordered price triples (P3 geometric between `c_min` and `0.9 q90(v)`, `P2 = f2 P3`, `P1 = f1 P2`, `f in {0.5, 0.7, 0.9}`), `tol_R in {0.08, 0.12, 0.16}`, `L in {10, 20, 50}`; inner search D2 at the median position, 1 restart x 100 evaluations x 3 dev-train seeds, twin at the same budget, reference selected last; objective `min((eff - 0.90)/0.90, (0.30 - gain)/0.30)` on the inner seeds; top 3 re-searched at the full budget on dev-train and scored on dev-val; the dev-val margin picks the locked winner (spec 4.2, 6).
- Manifest: every cell with its run count derived from `sim/schedule.py`, pre-lock and post-lock separated, simulator work separated from interval work; the gate is a benchmark of the full path through `sweep.py` (spec 5.3).
- Admissible class constants: `L_max = 50`, `H_max = 3` (spec 4.0), recorded in `locked.yaml`.

## Review Focus

1. A rule that records the view every round cannot tell, from `capacity`, `banned_until`, `bond`, or the tie-break keys, that an identity retired, nor which fresh identity belongs to the same entity. Task 2, `test_rule_view_does_not_reveal_exit_or_successor`.
2. A banned identity's entity decides to exit: the exit is honored, the fresh identity is not banned, and the old identity's ban and bond keep their schedule. Task 2, `test_banned_identity_can_still_exit_and_fresh_identity_is_not_banned`, `test_exit_does_not_change_ban_or_bond_schedule`.
3. A D2 policy whose markup state must persist across rounds is instantiated fresh per episode, so two seeds never share state. Task 4, `test_make_returns_fresh_instances`.
4. A search whose objective is flat terminates within its budget and returns a finite best value; a cell in which the twin serves nothing ties abstention at profit 0, and abstention wins by registered order. Task 6, `test_flat_objective_terminates`; Task 7, `test_abstention_wins_when_everything_loses_money`.
5. A corner whose claim sits exactly on a tier boundary (q_max = 0.8 honest corner) is evaluated at that claim, not at a value one ulp below it. Task 6, `test_corner_controls_use_exact_knobs_at_tier_boundaries`.
6. `evaluate_gain` on dev-val seeds with a reference chosen on dev-train subtracts the reference's dev-val profit, so an honest attack against an honest reference has gain exactly 0 on every seed. Task 7, `test_gain_on_other_seeds_subtracts_reference_on_those_seeds`.
7. A calibration file produced for one market is refused by a cell of another market, and the sweep refuses to run without tuned parameters unless told it is a smoke run. Task 9, `test_cell_config_refuses_foreign_calibration`; Task 13, `test_sweep_refuses_untuned_run_without_smoke_flag`.

---

### Task 1: Dependencies and the locked configuration file

**Files:**
- Modify: `pyproject.toml` (add `cma>=4.0`, `pyyaml>=6.0`)
- Create: `experiments/locked.yaml`, `sim/locked.py`
- Test: `tests/test_locked.py`

**Interfaces:**
- Produces: `load_locked(path="experiments/locked.yaml") -> dict`; `seeds(locked, namespace) -> list[int]` for `"dev_train"`, `"dev_val"`, `"calibration"`; `sha256_file(path) -> str`; `market_config_from_locked(locked) -> MarketConfig` (every market primitive from the YAML; `alpha` and `budget` zero until a cell derives them).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_locked.py
import pytest
from sim.locked import load_locked, seeds, sha256_file, market_config_from_locked
from sim.mechanisms.base import L_MAX, H_MAX


def test_locked_loads_and_namespaces_are_disjoint():
    lk = load_locked()
    tr, va, ca = seeds(lk, "dev_train"), seeds(lk, "dev_val"), seeds(lk, "calibration")
    assert len(tr) == 5 and len(va) == 20 and len(ca) == 20
    assert not (set(tr) & set(va)) and not (set(tr) & set(ca)) and not (set(va) & set(ca))
    assert lk["seeds"]["final_eval"] is None     # custodian-held until the unseal
    with pytest.raises(ValueError):
        seeds(lk, "final_eval")
    assert lk["beta_grid"] == [0.0, 0.01, 0.02, 0.05, 0.10, 0.20]
    assert lk["rho"]["default"] == 0.2 and lk["rho"]["sweep"] == [0.05, 0.2, 1.0]
    assert lk["search"]["popsize"] == 8 and lk["search"]["restarts"] == 5 and lk["search"]["evals_per_restart"] == 300
    assert lk["admissible"]["L_max"] == L_MAX and lk["admissible"]["H_max"] == H_MAX
    assert lk["reference_order"][0] == "abstain"
    assert lk["tuning"]["recheck_namespace"] == "dev_val"


def test_market_config_comes_from_the_yaml_alone():
    lk = load_locked()
    cfg = market_config_from_locked(lk)
    cfg.validate()
    assert cfg.N == 10 and cfg.J == 50 and cfg.T == 200 and cfg.alpha == 0.0 and cfg.budget == 0.0
    assert [p.q_max for p in cfg.providers] == lk["market"]["providers"]["q_max"]
    assert cfg.v_min == lk["market"]["v_min"]


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
  v_min: 0.6
  v_max: 1.4
  providers:                # spec 3 provider table; k = 6 for every provider
    q_max: [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.00]
    a:     [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02]
    b:     [0.40, 0.38, 0.36, 0.34, 0.32, 0.30, 0.28, 0.26, 0.24, 0.22]
    k:     [6, 6, 6, 6, 6, 6, 6, 6, 6, 6]
admissible:
  L_max: 50
  H_max: 3
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
reference_order: [abstain, honest_max, twin_search, attack_projection, archive_clip1, archive_truthful_clip0, bank]
tuning:
  price_f: [0.5, 0.7, 0.9]
  tol: [0.08, 0.12, 0.16]
  L: [10, 20, 50]
  inner_restarts: 1
  inner_evals: 100
  inner_seeds: 3
  recheck_top: 3
  recheck_namespace: dev_val
tuned: null                 # written by scripts/tune_baselines.py --write-locked before the lock
positions: [low, median, high]
doubling_cells: [[D1, median], [D2, median]]     # per rule, at beta_headline and rho default
no_ban_rules: [B2, B3]
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

from .config import MarketConfig, ProviderParams

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


def market_config_from_locked(locked: dict) -> MarketConfig:
    mk = locked["market"]; pt = mk["providers"]
    providers = tuple(ProviderParams(q_max=float(q), a=float(a), b=float(b), k=int(k))
                      for q, a, b, k in zip(pt["q_max"], pt["a"], pt["b"], pt["k"]))
    return MarketConfig(N=int(mk["N"]), J=int(mk["J"]), T=int(mk["T"]), sigma=float(mk["sigma"]), e=float(mk["e"]),
                        v_min=float(mk["v_min"]), v_max=float(mk["v_max"]), providers=providers, alpha=0.0, budget=0.0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv sync && uv run pytest tests/test_locked.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock experiments/locked.yaml sim/locked.py tests/test_locked.py
git commit -m "feat: locked configuration draft with the market table, seed namespaces, candidate order; cma and pyyaml dependencies"
```

---

### Task 2: Identities, exit and re-entry, entry cost, identity opacity, and the H3 policy wrapper

**Files:**
- Modify: `sim/ledger.py` (add `grow`), `sim/policies/base.py` (`ProviderView.identity`, exit allowed), `sim/rng.py` (add `fresh_tie_keys`), `sim/market.py` (identity bookkeeping)
- Create: `sim/policies/identity.py`
- Test: `tests/test_identity.py`; update `tests/test_policies.py::test_validate_action`

**Interfaces:**
- Consumes: plan 1 engine.
- Produces:
  - `Ledger.grow(m: int)` extends every per-identity array to `m` columns.
  - `ProviderView.identity: int` (current identity id of the entity).
  - `validate_action` no longer raises on `exit`.
  - `fresh_tie_keys(seed, t, count, J) -> np.ndarray` of shape `(J, count)`, read-only, a pure function of `(seed, t)` and the column index: column `g` is the same for every `count > g`.
  - `run_episode` keeps `entity_of: list[int]` (identity to entity) and `identity_of: list[int]` (entity to identity) and a harness-private `alive` list. An `Action.exit` is honored at the start of the acting entity's turn in that round: the current identity retires (never offers again; its `capacity`, `banned_until`, and `bond` entries in the view are left as they are), a fresh identity is created with capacity `k_i`, `banned_until 0`, no bond, and `cfg.e` charged in that round; the action's offer, if any, is submitted under the fresh identity. Identity `g >= N` uses tie-break column `g - N` of `fresh_tie_keys`.
  - `EpisodeResult.profit` stays per entity; new fields `n_identities: int`, `entity_of: tuple[int, ...]`, `identity_round: tuple[int, ...]` (creation round, 0 for initial identities), `identity_profit: np.ndarray`.
  - `IdentityReplacement(policy)` wrapper (H3): acts like `policy` and sets `exit=True` in the round after a failed audit. `h3_family(family) -> Family` wraps a family's factory in `IdentityReplacement` (used by Task 4's `Family`; defined here, imported there).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_identity.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.base import Consequences
from sim.policies.base import Action, ProviderView, ProviderHistory
from sim.policies.honest import HonestMax
from sim.policies.identity import IdentityReplacement
from sim.ledger import Ledger
from sim.rng import fresh_tie_keys, make_draws, Draws


def cfgb(budget, e=0.0, T=40, N=None):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


class ExitAt:
    """Exits in round `when` (the fresh identity offers in that round), otherwise honest-max."""
    name = "exit_at"
    def __init__(self, when): self.when = when
    def act(self, view):
        a = HonestMax().act(view)
        return Action(effort=a.effort, offer=a.offer, exit=(view.t == self.when))


class Spy(PostedRandomAudit):
    """Records what a rule can see each round."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.seen = []
    def allocate(self, values_t, offers, view):
        self.seen.append({"t": view.t, "N": view.N, "cap": view.capacity.copy(), "ban": view.banned_until.copy(),
                          "bond": view.bond.copy(), "tie": np.array(view.memory["tie_key"], copy=True),
                          "offers": set(offers)})
        return super().allocate(values_t, offers, view)


def test_ledger_grow_keeps_totals():
    led = Ledger(N=2, T=3)
    esc, own = {}, {}
    led.fund(0, 0, 1, 0.5, esc, own); led.settle(0, esc, own, Consequences(), {})
    led.grow(4)
    assert led.funding.shape == (3, 4) and led.bond.shape == (4,)
    assert led.funding.sum() == pytest.approx(0.5)
    led.check_conservation(0.0)


def test_fresh_tie_keys_are_prefix_stable_and_distinct():
    a = fresh_tie_keys(7, 3, 2, 50); b = fresh_tie_keys(7, 3, 5, 50)
    assert a.shape == (50, 2) and np.array_equal(a, b[:, :2])
    assert not np.array_equal(b[:, 0], b[:, 1]) and not a.flags.writeable
    assert not np.array_equal(fresh_tie_keys(7, 4, 1, 50), fresh_tie_keys(7, 3, 1, 50))


def test_exit_creates_fresh_identity_and_charges_entry_cost_in_that_round():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=3)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N + 1 and res.entity_of[-1] == 2 and res.identity_round[-1] == 3
    assert res.ledger.entry.sum() == pytest.approx(0.3) and res.ledger.entry[3, cfg.N] == pytest.approx(0.3)
    assert all(2 not in rec.assignment.values() for rec in res.history[3:])     # old identity never offers again
    assert any(cfg.N in rec.assignment.values() for rec in res.history[3:])     # fresh one serves
    assert cfg.N in res.history[3].offers and 2 not in res.history[3].offers    # offer of round 3 is under the fresh identity
    assert res.profit.shape == (cfg.N,)
    assert res.profit[2] == pytest.approx(res.identity_profit[2] + res.identity_profit[cfg.N])


def test_exit_in_last_round_creates_identity_and_releases_its_bond_at_terminal_settlement():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=9)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N + 1 and res.ledger.entry[9, cfg.N] == pytest.approx(0.3)
    assert res.ledger.bond.sum() == 0.0


def test_banned_identity_can_still_exit_and_fresh_identity_is_not_banned():
    cfg = cfgb(budget=50.0, e=0.0, T=12)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=50)   # every audit fails, long bans
    pols = [HonestMax() for _ in range(cfg.N)]; pols[0] = IdentityReplacement(HonestMax())
    res = run_episode(cfg, rule, pols, 0)
    assert res.n_identities > cfg.N
    # after a failure in round t the entity serves again in round t + 1 under a fresh identity
    fails = np.flatnonzero(res.failures[:, 0] > 0)
    assert len(fails) >= 1 and res.served[fails[0] + 1, 0] > 0


def test_identity_replacement_exits_in_the_round_after_failure():
    cfg = cfgb(budget=50.0, T=6)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=2)
    pols = [IdentityReplacement(HonestMax()) for _ in range(cfg.N)]
    res = run_episode(cfg, rule, pols, 0)
    first_fail = int(np.argmax(res.failures[:, 0] > 0))
    assert res.failures[first_fail, 0] > 0
    created = [r for r, e in zip(res.identity_round, res.entity_of) if e == 0 and r > 0]
    assert created[0] == first_fail + 1
    assert res.identity_profit.shape == (res.n_identities,)
    assert res.profit[0] == pytest.approx(sum(res.identity_profit[k] for k, e in enumerate(res.entity_of) if e == 0))


def test_rule_view_does_not_reveal_exit_or_successor():
    cfg = cfgb(budget=5.0, T=8)
    rule = Spy(0.25, 0.40, 0.55, tol=0.12, L=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=3)
    run_episode(cfg, rule, pols, 0)
    before, after = rule.seen[2], rule.seen[3]
    assert after["N"] == before["N"] + 1
    assert after["cap"][2] == before["cap"][2] and after["ban"][2] == before["ban"][2]    # old identity not marked
    assert after["cap"][cfg.N] == cfg.providers[2].k and after["ban"][cfg.N] == 0
    assert not np.array_equal(after["tie"][:, 2], after["tie"][:, cfg.N])                  # no shared randomness
    assert 2 not in after["offers"] and cfg.N in after["offers"]


def test_relabeling_with_reentry_relabels_decisions():
    c = cfgb(budget=1.0, T=12)
    perm = np.array([3, 0, 9, 1, 7, 2, 8, 5, 4, 6])   # new index -> old index
    cfg_p = MarketConfig(N=c.N, J=c.J, T=c.T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                         providers=tuple(c.providers[o] for o in perm), alpha=c.alpha, budget=c.budget)
    d = make_draws(c, 5)
    d_p = Draws(values=d.values, noise=d.noise[:, perm, :], tie_key=d.tie_key[:, :, perm], audit_u=d.audit_u,
                audit_key=d.audit_key, policy_seed=d.policy_seed[:, perm])
    inv = np.argsort(perm)
    pols = [HonestMax() for _ in range(c.N)]; pols[2] = ExitAt(when=3); pols[5] = ExitAt(when=3)
    pols_p = [pols[o] for o in perm]
    r = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    a = run_episode(c, r, pols, 5, draws=d); b = run_episode(cfg_p, r, pols_p, 5, draws=d_p)
    # key an identity by (entity, generation) so fresh identities compare across runs
    def keys(res, to_new):
        gen, out = {}, {}
        for ident, e in enumerate(res.entity_of):
            g = gen.get(e, 0); gen[e] = g + 1; out[ident] = (int(to_new[e]), g)
        return out
    ka, kb = keys(a, inv), keys(b, np.arange(c.N))
    for ra, rb in zip(a.history, b.history):
        assert {j: ka[i] for j, i in ra.assignment.items()} == {j: kb[i] for j, i in rb.assignment.items()}
    assert np.allclose(a.profit[perm], b.profit)


def _hold_rule_factory(exit_round):
    class HoldAndExit(HonestMax):
        name = "hold_and_exit"
        def act(self, view):
            a = super().act(view)
            return Action(effort=a.effort, offer=a.offer, exit=(view.t == exit_round))
    class HoldRule(PostedRandomAudit):
        """Holds back 10% of each release and releases every bond one round later."""
        def enforce(self, records, view):
            cons = super().enforce(records, view)
            for j, amt in view.escrow.items():
                i = view.memory["owner"][j]
                cons.holdbacks[i] = cons.holdbacks.get(i, 0.0) + 0.1 * amt
            for i in range(view.N):
                if view.bond[i] > 0:
                    cons.releases[i] = float(view.bond[i])
            return cons
        def allocate(self, values_t, offers, view):
            out = super().allocate(values_t, offers, view)
            view.memory["owner"] = dict(out)
            return out
    return HoldAndExit, HoldRule


def test_exit_does_not_change_ban_or_bond_schedule():
    cfg = cfgb(budget=0.0, T=8)
    HoldAndExit, HoldRule = _hold_rule_factory(exit_round=3)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[5] = HoldAndExit()
    with_exit = run_episode(cfg, HoldRule(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    pols2 = [HonestMax() for _ in range(cfg.N)]; pols2[5] = HonestMax()
    no_exit = run_episode(cfg, HoldRule(0.25, 0.40, 0.55, tol=0.12, L=10), pols2, 0)
    # the bond held back in round 2 is released in round 3 in both runs, to identity 5
    assert with_exit.ledger.holdback_in[2, 5] > 0
    assert with_exit.ledger.holdback_out[3, 5] == pytest.approx(no_exit.ledger.holdback_out[3, 5])
    assert with_exit.ledger.holdback_out[3, 5] == pytest.approx(with_exit.ledger.holdback_in[2, 5])
    assert with_exit.ledger.bond.sum() == pytest.approx(0.0)
    assert with_exit.ledger.holdback_out[:, 5].sum() == pytest.approx(with_exit.ledger.holdback_in[:, 5].sum())
    with_exit.ledger.check_conservation(0.0)
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
Expected: FAIL on `ImportError: cannot import name 'fresh_tie_keys'`, then on `sim.policies.identity`, `Ledger.grow`, `n_identities`, and `NotImplementedError`.

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

Add to `sim/rng.py` after `make_draws`:

```python
def fresh_tie_keys(seed: int, t: int, count: int, J: int) -> np.ndarray:
    """Tie-break keys for identities created by re-entry, (J, count). Column g is a
    pure function of (seed, t, g): rows are drawn one identity at a time, so the
    first g columns are identical for every count > g. Keyed apart from the
    round's main child so initial identities' draws are unchanged."""
    g = np.random.default_rng(np.random.SeedSequence([int(seed), int(t), 1]))
    out = g.random(size=(max(int(count), 0), J)).T.copy()
    out.setflags(write=False)
    return out
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

from dataclasses import replace

from .base import Action, ProviderView


class IdentityReplacement:
    """H3 (spec 6.2): behave like the wrapped policy, and exit in the round
    after a failed audit so the entity re-enters under a fresh identity in that
    round (exits take effect when made, Task 2)."""

    def __init__(self, policy) -> None:
        self.policy = policy
        self.name = f"h3({getattr(policy, 'name', 'policy')})"

    def act(self, view: ProviderView) -> Action:
        a = self.policy.act(view)
        failed_last = bool(view.history.failed) and view.history.failed[-1] > 0
        return Action(effort=a.effort, offer=a.offer, exit=a.exit or failed_last)


def h3_family(family):
    """A family whose policies are wrapped in IdentityReplacement; same knobs, same transforms."""
    base_factory = family.factory
    return replace(family, name=f"{family.name}+H3", factory=lambda **k: IdentityReplacement(base_factory(**k)))
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
from .rng import Draws, fresh_tie_keys, make_draws


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
    claims: np.ndarray            # (T, N) per entity, nan when no offer
    efforts: np.ndarray           # (T, N) per entity
    buyer_surplus: float
    W: float
    history: tuple[RoundRecord, ...]
    ledger: Ledger
    n_identities: int
    entity_of: tuple[int, ...]    # identity -> entity
    identity_round: tuple[int, ...]   # identity -> creation round (0 for initial identities)
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
    N, T, J, alpha = cfg.N, cfg.T, cfg.J, cfg.alpha
    allowance = int(np.floor(cfg.budget / alpha + 1e-12)) if alpha > 0 else 0
    ledger = Ledger(N, T)
    caps_entity = np.array([p.k for p in cfg.providers], dtype=np.int64)
    a_arr = np.array([p.a for p in cfg.providers]); b_arr = np.array([p.b for p in cfg.providers])
    # identity bookkeeping; the arrays below are per identity. `alive` is harness-private and never reaches a rule.
    entity_of: list[int] = list(range(N))
    identity_of: list[int] = list(range(N))
    identity_round: list[int] = [0] * N
    alive: list[bool] = [True] * N
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
        values_t = d.values[t].copy()
        offers: dict[int, Offer] = {}
        effort_e = np.zeros(N)
        for e in range(N):
            ident = identity_of[e]
            act = policies[e].act(ProviderView(i=e, params=cfg.providers[e], t=t, posted_prices=posted,
                                               history=histories[e], policy_seed=int(d.policy_seed[t, e]), identity=ident))
            validate_action(act, cfg.providers[e])
            if act.exit:
                # retire the current identity now; the fresh identity makes this round's offer and pays e now
                alive[ident] = False
                new = len(entity_of)
                entity_of.append(e); identity_of[e] = new; identity_round.append(t); alive.append(True)
                caps_id = np.append(caps_id, caps_entity[e]); banned_until = np.append(banned_until, 0)
                ledger.grow(new + 1)
                ledger.charge_entry(t, new, cfg.e)
                ident = new
            effort_e[e] = float(act.effort); efforts[t, e] = effort_e[e]
            if t < banned_until[ident]:
                continue
            if act.offer is not None:
                offers[ident] = Offer(claim=float(act.offer.claim), bid=float(act.offer.bid))
                claims[t, e] = offers[ident].claim
        M = len(entity_of)
        ent_arr = np.array(entity_of, dtype=np.int64)
        tie_key = d.tie_key[t] if M == N else np.concatenate([d.tie_key[t], fresh_tie_keys(seed, t, M - N, J)], axis=1)
        tie_key = np.array(tie_key, copy=True); tie_key.setflags(write=False)
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
                         n_identities=len(entity_of), entity_of=tuple(entity_of), identity_round=tuple(identity_round),
                         identity_profit=identity_profit)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_identity.py tests/test_policies.py -v && uv run pytest -q`
Expected: PASS (10 new tests; whole suite green, 101 tests). The plan 1 relabeling test still passes because initial identity ids equal entity indices. `scripts/bench.py` stays under the gate (the identity loop adds about 2 ms on an M4 Max).

- [ ] **Step 5: Commit**

```bash
git add sim/ledger.py sim/rng.py sim/policies/base.py sim/policies/identity.py sim/market.py tests/test_identity.py tests/test_policies.py
git commit -m "feat: identities separate from entities with opaque retirement, fresh tie keys, same-round exit and entry cost; H3 wrapper"
```

---

### Task 3: Enforcement-ablation adapter and exclusion-by-allocation count

**Files:**
- Create: `sim/mechanisms/ablation.py`
- Test: `tests/test_ablation.py`

**Interfaces:**
- Consumes: `Mechanism`, `EpisodeResult` (Task 2).
- Produces:
  - `EnforcementAblation(rule: Mechanism, enforcer: Mechanism)`: a `Mechanism` whose `allocate`, `price`, `audit`, `tol`, and `describe` (non-enforcement fields) come from `rule`, and whose `enforce` output comes from `enforcer.enforce(records, view)`; `bind` binds both. The harness recomputes every economic state from the consequences actually applied (plan 1), so only the rule's policy memory survives the swap (spec 8).
  - `exclusion_by_allocation(res: EpisodeResult) -> dict[int, int]`: for each identity, the number of rounds after its first failed audit in which it offered, was not banned, and received no job.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ablation.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.ablation import EnforcementAblation, exclusion_by_allocation
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax


def cfgb(budget, T=20):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


class HoldAndLongBan(PostedRandomAudit):
    """A rule with hold-backs and 40-round bans; the ablation must strip both to B2's enforcement."""
    def enforce(self, records, view):
        cons = super().enforce(records, view)
        for j, amt in view.escrow.items():
            i = view.memory["owner"][j]
            cons.holdbacks[i] = cons.holdbacks.get(i, 0.0) + 0.2 * amt
        for i in list(cons.bans):
            cons.bans[i] = 40
        return cons
    def allocate(self, values_t, offers, view):
        out = super().allocate(values_t, offers, view)
        view.memory["owner"] = dict(out)
        return out


class Shunner(PostedRandomAudit):
    """Never allocates to an identity after it failed an audit; no bans."""
    def allocate(self, values_t, offers, view):
        shunned = view.memory.setdefault("shunned", set())
        out = super().allocate(values_t, {i: o for i, o in offers.items() if i not in shunned}, view)
        return out
    def enforce(self, records, view):
        cons = super().enforce(records, view)
        cons.bans.clear()
        for r in records:
            if r.failed:
                view.memory.setdefault("shunned", set()).add(r.provider)
        return cons


def test_ablation_uses_enforcer_consequences_and_rule_allocation():
    cfg = cfgb(budget=5.0)
    rule = HoldAndLongBan(0.25, 0.40, 0.55, tol=-10.0, L=40)        # every audit fails
    enforcer = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=3)
    abl = EnforcementAblation(rule, enforcer)
    assert abl.tol == rule.tol and abl.name.startswith("ablation(")
    res = run_episode(cfg, abl, [HonestMax() for _ in range(cfg.N)], 0)
    assert res.ledger.holdback_in.sum() == 0.0 and res.ledger.bond.sum() == 0.0
    bans = [c for rec in res.history for c in rec.consequences.bans.values()]
    assert bans and set(bans) == {3}
    res.ledger.check_conservation(0.0)
    d = abl.describe()
    assert d["ban_length"] == "3" and d["holdback"] == "none" and d["pricing"] == rule.describe()["pricing"]


def test_exclusion_by_allocation_counts_shunned_rounds():
    cfg = cfgb(budget=5.0, T=12)
    res = run_episode(cfg, Shunner(0.25, 0.40, 0.55, tol=-10.0, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    ex = exclusion_by_allocation(res)
    assert any(v > 0 for v in ex.values())
    assert all(not rec.consequences.bans for rec in res.history)
    res2 = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    ex2 = exclusion_by_allocation(res2)
    assert set(ex2) == set(range(res2.n_identities)) and all(v >= 0 for v in ex2.values())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ablation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.mechanisms.ablation'`

- [ ] **Step 3: Write the implementation**

```python
# sim/mechanisms/ablation.py
from __future__ import annotations

import numpy as np

from .base import AuditRecord, Consequences, Mechanism, Offers, StateView

ENFORCEMENT_FIELDS = ("failed_audit", "ban_length", "holdback")


class EnforcementAblation(Mechanism):
    """Spec 8: the rule's allocation, pricing, audit selection and tolerance with
    another rule's enforcement. The harness applies only the consequences
    returned here, so the economic state is the ablated one by construction."""

    def __init__(self, rule: Mechanism, enforcer: Mechanism) -> None:
        self.rule, self.enforcer = rule, enforcer
        self.name = f"ablation({rule.name}|{enforcer.name})"
        self.tol = rule.tol
        self.prices = getattr(rule, "prices", None)

    def bind(self, cfg) -> None:
        self.rule.bind(cfg); self.enforcer.bind(cfg)

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        return self.rule.allocate(values_t, offers, view)

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return self.rule.price(assignment, values_t, offers, view)

    def audit(self, assignment, view) -> list[int]:
        return self.rule.audit(assignment, view)

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        return self.enforcer.enforce(records, view)

    def describe(self) -> dict[str, str]:
        d = dict(self.rule.describe())
        e = self.enforcer.describe()
        for k in ENFORCEMENT_FIELDS:
            d[k] = e[k]
        return d


def exclusion_by_allocation(res) -> dict[int, int]:
    """Rounds after an identity's first failed audit in which it offered, was not
    banned, and got no job (spec 8: exclusion through allocation priority)."""
    first_fail: dict[int, int] = {}
    for rec in res.history:
        for r in rec.audits:
            if r.failed and r.provider not in first_fail:
                first_fail[r.provider] = rec.t
    counts = {i: 0 for i in range(res.n_identities)}
    banned_until: dict[int, int] = {}
    for rec in res.history:
        served = set(rec.assignment.values())
        for i in rec.offers:
            if i in first_fail and rec.t > first_fail[i] and rec.t >= banned_until.get(i, 0) and i not in served:
                counts[i] += 1
        for i, rounds in rec.consequences.bans.items():
            banned_until[i] = max(banned_until.get(i, 0), rec.t + int(rounds) + 1)
    return counts
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ablation.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/mechanisms/ablation.py tests/test_ablation.py
git commit -m "feat: enforcement-ablation adapter and exclusion-by-allocation count"
```

---

### Task 4: Families, knob transforms, projection, containment tests, and the D2 adaptive policy

**Files:**
- Create: `sim/policies/families.py`, `sim/policies/adaptive.py`
- Test: `tests/test_families.py`

**Interfaces:**
- Produces:
  - `Family` frozen dataclass: `name`, `knobs: tuple[str, ...]`, `bounds: dict[str, tuple[float, float]]`, `factory`, `dim`; methods `transform(x) -> dict`, `inverse(knobs, near) -> np.ndarray`, `project(knobs) -> dict` (clip forced to 1), `make(knobs) -> Policy` (fresh instance), `corners() -> list[dict]` (all bound corners times clip in {0,1}, de-duplicated), `registered_starts(settings) -> list[np.ndarray]` (near-honest, near-full-cheat, three Sobol), `honest_point() -> dict` (every knob at its lower bound, clip 1: reproduces honest-max).
  - `knob_key(knobs) -> tuple` (knobs rounded to 9 decimals, sorted; the de-duplication key used by the archive and the bank).
  - `D1`, `D2`, `FAMILIES = {"D1": D1, "D2": D2}`, `embed_d1_in_d2(knobs) -> dict`.
  - `AdaptiveCheat(u0, m0, s, d, r, w, clip)` policy with per-instance markup state.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_families.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.policies.families import D1, D2, FAMILIES, embed_d1_in_d2, knob_key
from sim.policies.adaptive import AdaptiveCheat
from sim.policies.base import ProviderView, ProviderHistory
from sim.policies.honest import HonestMax
from sim.policies.identity import h3_family, IdentityReplacement


def view(i=0, t=0, failed=None, banned=None):
    cfg = MarketConfig.default()
    h = ProviderHistory()
    for k, f in enumerate(failed or []):
        h.append(1, 0.5, 1, f, 0.0, (banned or [0] * len(failed))[k])
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


def test_project_corners_keys_and_honest_point():
    assert D1.project({"u": 0.2, "m": 0.9, "s": 0.0, "w": 0.0, "clip": 0})["clip"] == 1
    corners = D1.corners()
    assert len(corners) == 2 ** 5 and len({knob_key(c) for c in corners}) == len(corners)
    assert len(D2.corners()) == 2 ** 7
    assert knob_key({"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}) == knob_key({"u": 0.5000000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0})
    assert D1.honest_point() == {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}
    assert D2.honest_point() == {"u0": 0.0, "m0": 0.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "clip": 1}


def test_honest_point_of_each_family_reproduces_honest_max():
    for fam in (D1, D2):
        p = fam.make(fam.honest_point())
        for i in range(10):
            for t, failed in enumerate(([], [1], [1, 0])):
                assert p.act(view(i=i, t=t, failed=failed)) == HonestMax().act(view(i=i, t=t, failed=failed))


def test_d2_recurrence_and_containment_of_d1():
    p = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.0, w=0.0, clip=0)
    a0 = p.act(view(i=0, failed=[]))                    # m_1 = 0.6 -> claim min(1, 0.3 + 0.6 - 0.2) = 0.7
    assert a0.offer.claim == pytest.approx(0.7)
    a1 = p.act(view(i=0, t=1, failed=[1]))              # failed last round -> m = 0.3 -> claim 0.4
    assert a1.offer.claim == pytest.approx(0.4)
    a2 = p.act(view(i=0, t=2, failed=[1, 0]))           # no failure, r = 0 -> stays 0.3
    assert a2.offer.claim == pytest.approx(0.4)
    q = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.2, w=0.0, clip=0)
    q.act(view(i=0, failed=[])); q.act(view(i=0, t=1, failed=[1]))
    a = q.act(view(i=0, t=2, failed=[1, 0]))            # recovery: min(0.6, 0.3 + 0.2 * 0.6) = 0.42 -> claim 0.52
    assert a.offer.claim == pytest.approx(0.52)
    with pytest.raises(ValueError):
        AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.5, w=0.0, clip=0)   # r outside [0, 0.2]
    # ban branch: banned last round and not audited -> state unchanged
    b = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.2, w=0.0, clip=0)
    b.act(view(i=0, failed=[])); b.act(view(i=0, t=1, failed=[1]))          # m = 0.3
    a_b = b.act(view(i=0, t=2, failed=[1, 0], banned=[0, 5]))              # banned in round 1 -> m stays 0.3
    assert a_b.offer.claim == pytest.approx(0.4)
    # containment: D1 point embedded at d = r = 0 behaves like D1 every round
    k1 = {"u": 0.4, "m": 0.5, "s": 0.1, "w": 0.3, "clip": 0}
    d2 = D2.make(embed_d1_in_d2(k1)); d1 = D1.make(k1)
    for t, failed in enumerate(([], [1], [1, 1], [1, 1, 0])):
        assert d2.act(view(i=1, t=t, failed=failed)) == d1.act(view(i=1, t=t, failed=failed))


def test_make_returns_fresh_instances_and_h3_family_wraps():
    k = {"u0": 0.5, "m0": 0.6, "s": 0.2, "d": 0.5, "r": 0.0, "w": 0.0, "clip": 0}
    a, b = D2.make(k), D2.make(k)
    a.act(view(i=0)); a.act(view(i=0, t=1, failed=[1]))
    assert b.act(view(i=0)).offer.claim == pytest.approx(0.7)    # b's state untouched
    assert set(FAMILIES) == {"D1", "D2"}
    h3 = h3_family(D2)
    assert h3.name == "D2+H3" and h3.knobs == D2.knobs and isinstance(h3.make(k), IdentityReplacement)
    assert h3.make(k).act(view(i=0, t=1, failed=[1])).exit is True
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
            banned_last = bool(view.history.banned_until) and view.history.banned_until[-1] > view.t - 1
            if view.history.failed[-1] > 0:
                self.m *= (1.0 - self.d)
            elif banned_last:
                pass   # banned and not audited last round: state unchanged
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


def knob_key(knobs: dict) -> tuple:
    """De-duplication key: knobs rounded to 9 decimals, sorted by name."""
    return tuple(sorted((k, round(float(v), 9)) for k, v in knobs.items()))


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
        """Approximate inverse for search starts only; never use it to evaluate an exact point."""
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
                k[name] = b if name == "clip" else float(self.bounds[name][b])
            key = knob_key(k)
            if key not in seen:
                seen.add(key); out.append(k)
        return out

    def honest_point(self) -> dict:
        return {k: (1 if k == "clip" else float(self.bounds[k][0])) for k in self.knobs}

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
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/policies/families.py sim/policies/adaptive.py tests/test_families.py
git commit -m "feat: D1/D2 families with logistic knob transforms, projection, corners, honest point, registered starts; D2 adaptive policy"
```

---

### Task 5: Seed cache, profile runner, and the focal cell runner with inflation flag

**Files:**
- Create: `sim/cell.py`
- Test: `tests/test_cell.py`

**Interfaces:**
- Produces:
  - `market_key(cfg) -> str` (sha256 prefix of the market primitives `N, J, T, sigma, e, v_min, v_max, providers`; `alpha` and `budget` excluded so draws and S* are shared across betas and rhos).
  - `SeedCache()` with `get(cfg, seed) -> tuple[Draws, float]` (computed once per `(market_key, seed)`), counters `hits`, `misses`, and `runs` (episodes executed through this cache).
  - `Cell(cfg, rule_factory, focal, seeds, name, others=())`: `others` is a tuple of `(entity, policy_factory)` pairs for non-focal entities that do not play honest-max.
  - `run_profile(cfg, rule_factory, factories: list[Callable], seeds, cache) -> list[EpisodeResult]` (one policy factory per entity).
  - `run_focal(cell, policy_factory, cache) -> FocalRun` with `profit[len(seeds)]`, `normalized[len(seeds)]` (`profit / (S*/N)`), `inflated_per_seed: np.ndarray[bool]` (any round where the focal claim exceeds its effort by more than 1e-12), `inflated: bool` (any seed), `results: list[EpisodeResult]`; every other entity plays `HonestMax` unless named in `others`.
  - `Abstain()` policy: effort 0, no offer.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cell.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell, run_focal, run_profile, Abstain, market_key
from sim.config import MarketConfig, ProviderParams
from sim.mechanisms.posted import PostedPrices
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat


def tiny(budget=0.0, T=10, alpha=None):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=T, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers[6:10], alpha=c.alpha if alpha is None else alpha, budget=budget)


def test_cache_keys_on_market_not_on_budget():
    cache = SeedCache()
    cfg = tiny()
    d1, s1 = cache.get(cfg, 1); d2, s2 = cache.get(tiny(budget=3.0, alpha=0.1), 1)
    assert d1 is d2 and s1 == s2 and cache.hits == 1 and cache.misses == 1
    assert market_key(tiny(T=11)) != market_key(cfg)
    cache.get(tiny(T=11), 1)
    assert cache.misses == 2


def test_run_focal_normalizes_by_sstar_over_n_and_counts_runs():
    cache = SeedCache()
    cell = Cell(cfg=tiny(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=3, seeds=(1, 2, 3), name="t")
    fr = run_focal(cell, lambda: HonestMax(), cache)
    assert fr.profit.shape == (3,) and fr.normalized.shape == (3,) and cache.runs == 3
    for k, res in enumerate(fr.results):
        assert fr.normalized[k] == pytest.approx(fr.profit[k] / (res.sstar / 4))
    assert fr.inflated is False and not fr.inflated_per_seed.any()


def test_inflation_flag_and_others():
    cache = SeedCache()
    cell = Cell(cfg=tiny(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=3, seeds=(1,), name="t",
                others=((0, lambda: FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)),))
    fr = run_focal(cell, lambda: FixedCheat(u=0.5, m=1.0, s=0.0, w=0.0, clip=0), cache)
    assert fr.inflated is True
    assert fr.results[0].efforts[0, 0] == 0.0                 # entity 0 played the cheat named in `others`
    fr2 = run_focal(cell, lambda: FixedCheat(u=0.5, m=1.0, s=0.0, w=0.0, clip=1), cache)
    assert fr2.inflated is False


def test_run_profile_and_abstain():
    cache = SeedCache()
    cfg = tiny()
    res = run_profile(cfg, lambda: PostedPrices(0.25, 0.40, 0.55), [Abstain, HonestMax, HonestMax, HonestMax], (1,), cache)
    assert res[0].profit[0] == 0.0 and res[0].served[:, 0].sum() == 0 and cache.runs == 1
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


def market_key(cfg: MarketConfig) -> str:
    """Hash of the market primitives; alpha and budget excluded (draws and S* do not depend on them)."""
    parts = (cfg.N, cfg.J, cfg.T, cfg.sigma, cfg.e, cfg.v_min, cfg.v_max,
             tuple((p.q_max, p.a, p.b, p.k) for p in cfg.providers))
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


class SeedCache:
    """Draws and S* per (market, seed): computed once, shared by every cell. Counts episodes run."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, int], tuple[Draws, float]] = {}
        self.hits = 0
        self.misses = 0
        self.runs = 0

    def get(self, cfg: MarketConfig, seed: int) -> tuple[Draws, float]:
        key = (market_key(cfg), int(seed))
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
    others: tuple = ()      # ((entity, policy_factory), ...) for non-focal entities not on honest-max


@dataclass
class FocalRun:
    profit: np.ndarray
    normalized: np.ndarray
    inflated_per_seed: np.ndarray
    inflated: bool
    results: list = field(default_factory=list)


def run_profile(cfg: MarketConfig, rule_factory: Callable, factories: list, seeds, cache: SeedCache) -> list[EpisodeResult]:
    out = []
    for seed in seeds:
        d, sstar = cache.get(cfg, seed)
        pols = [f() for f in factories]
        out.append(run_episode(cfg, rule_factory(), pols, int(seed), draws=d, sstar=sstar))
        cache.runs += 1
    return out


def run_focal(cell: Cell, policy_factory: Callable, cache: SeedCache) -> FocalRun:
    factories: list = [HonestMax for _ in range(cell.cfg.N)]
    for e, f in cell.others:
        factories[e] = f
    factories[cell.focal] = policy_factory
    results = run_profile(cell.cfg, cell.rule_factory, factories, cell.seeds, cache)
    profits = np.array([float(r.profit[cell.focal]) for r in results])
    norms = np.array([float(r.profit[cell.focal] / (r.sstar / cell.cfg.N)) for r in results])
    infl = np.array([bool(np.any(r.claims[:, cell.focal] > r.efforts[:, cell.focal] + 1e-12)) for r in results])
    return FocalRun(profit=profits, normalized=norms, inflated_per_seed=infl, inflated=bool(infl.any()), results=results)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cell.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/cell.py tests/test_cell.py
git commit -m "feat: seed cache keyed on the market, profile runner, focal cell runner with inflation flag and run counter"
```

---

### Task 6: Objective with archive, CMA-ES search with incumbents and projection replacement, exact corner controls

**Files:**
- Create: `sim/search.py`
- Test: `tests/test_search.py`

**Interfaces:**
- Consumes: `Family`, `knob_key`, `Cell`, `run_focal`, `SeedCache`.
- Produces:
  - `SearchSettings(popsize, sigma0, restarts, evals_per_restart, reeval_every, near_corner, sobol_seed)` and `settings_from_locked(locked) -> SearchSettings`.
  - `ArchiveEntry(knobs, f, per_seed_profit, per_seed_normalized, inflated: bool, source: str)`.
  - `Objective(cell, family, cache, force_clip=False)`: `knobs_of(x) -> dict` (transform, projected when `force_clip`), `eval_knobs(knobs, source="search") -> float` (exact knobs; projected when `force_clip`; records an archive entry; counts `evals`), `__call__(x) -> float`, `archive: dict[tuple, ArchiveEntry]`, `evals: int`.
  - `best_archived(archive, clip: int, truthful_only: bool = False) -> ArchiveEntry | None` (highest `f`; first inserted wins ties).
  - `cma_search(objective, family, settings, seed, incumbents: dict[str, dict] | None = None) -> SearchResult(best_x, best_knobs, best_f, best_source, restart_bests, evals, trace, incumbent_scores: dict[str, float], projection_f: float, replaced_by_projection: bool, archive: dict)`. After the restarts, every incumbent is evaluated exactly (outside the budget) and replaces the best when higher; then the clip = 1 projection of the best is evaluated exactly (always one evaluation, so the run count is exact) and replaces the best when higher. `objective` must provide `knobs_of`, `eval_knobs`, and `__call__`.
  - `corner_controls(objective, family) -> list[tuple[dict, float]]` through `eval_knobs`, outside the budget.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_search.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig, ProviderParams
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2, knob_key
from sim.search import SearchSettings, Objective, cma_search, corner_controls, best_archived


def fixture_cfg(J=30):
    # every job accepts tier 3 at P3 = 0.5 (v_min 0.6 >= 0.5), P3 > a; 30 jobs so the focal serves at every tier
    c = MarketConfig.default()
    return MarketConfig(N=4, J=J, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=60, reeval_every=10,
                       near_corner=0.02, sobol_seed=3)
FULL = SearchSettings(popsize=8, sigma0=0.3, restarts=5, evals_per_restart=300, reeval_every=10, near_corner=0.02, sobol_seed=3)


class Flat:
    """Objective protocol stub: every point scores the same."""
    def __init__(self, family, value=0.0): self.family, self.value, self.evals, self.archive = family, value, 0, {}
    def knobs_of(self, x): return self.family.transform(x)
    def eval_knobs(self, knobs, source="search"): self.evals += 1; return self.value
    def __call__(self, x): return self.eval_knobs(self.knobs_of(x))


class PrefersIncumbent:
    """Stub: only the exact honest point (unreachable through the sigmoid) scores 2.0."""
    def __init__(self, family): self.family, self.evals, self.archive = family, 0, {}
    def knobs_of(self, x): return self.family.transform(x)
    def eval_knobs(self, knobs, source="search"):
        self.evals += 1
        return 2.0 if knobs == self.family.honest_point() else 1.0 - knobs["u"] * 0.1
    def __call__(self, x): return self.eval_knobs(self.knobs_of(x))


class PrefersProjection:
    """Stub: the evaluation made at the projection step scores highest."""
    def __init__(self, family): self.family, self.evals, self.archive = family, 0, {}
    def knobs_of(self, x): return self.family.transform(x)
    def eval_knobs(self, knobs, source="search"):
        self.evals += 1
        return 3.0 if source == "projection" else 1.0 - knobs["u"] * 0.1
    def __call__(self, x): return self.eval_knobs(self.knobs_of(x))


def test_search_recovers_b1_analytic_best_response_within_one_percent():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1, 2), name="b1fix")
    obj = Objective(cell, D1, cache)
    analytic = obj.eval_knobs({"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, source="analytic")
    res = cma_search(obj, D1, FULL, seed=0)
    assert res.best_f >= analytic * 0.99
    k = res.best_knobs
    assert k["clip"] == 0 and k["u"] > 0.99 and k["m"] - k["s"] >= 0.8
    assert res.evals == 5 * 300 and len(res.restart_bests) == 5
    # the optimizer, not only the registered near-full-cheat start, reaches the optimum: a Sobol restart gets there
    assert max(res.restart_bests[2:]) >= analytic * 0.99
    assert res.replaced_by_projection is False and res.projection_f < res.best_f


def test_search_respects_budget_and_is_deterministic():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="b1fix")
    a = cma_search(Objective(cell, D2, cache), D2, SMALL, seed=1); b = cma_search(Objective(cell, D2, cache), D2, SMALL, seed=1)
    assert a.evals == 2 * 60 and a.best_f == b.best_f and np.array_equal(a.best_x, b.best_x)
    assert np.isfinite(a.best_f)
    assert len(a.archive) >= 100 and all(e.per_seed_profit.shape == (1,) for e in a.archive.values())


def test_flat_objective_terminates_and_counts():
    obj = Flat(D1)
    res = cma_search(obj, D1, SMALL, seed=0)
    assert res.evals == 120 and res.best_f == 0.0 and obj.evals == 120 + 1   # + the projection evaluation


def test_incumbents_and_projection_replace_the_best_when_higher():
    obj = PrefersIncumbent(D1)
    res = cma_search(obj, D1, SMALL, seed=0, incumbents={"honest_point": D1.honest_point()})
    assert res.incumbent_scores == {"honest_point": 2.0}
    assert res.best_f == 2.0 and res.best_knobs == D1.honest_point() and res.best_source == "incumbent:honest_point"
    assert res.projection_f == 2.0 and res.replaced_by_projection is False     # projection of a clip = 1 point is itself; not strictly higher
    res2 = cma_search(PrefersProjection(D1), D1, SMALL, seed=0)
    assert res2.replaced_by_projection is True and res2.best_knobs["clip"] == 1 and res2.best_source == "projection" and res2.best_f == 3.0


def test_force_clip_objective_never_inflates_and_archive_flags_inflation():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="b1fix")
    obj_t = Objective(cell, D1, cache, force_clip=True)
    k = {"u": 0.5, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}
    obj_t.eval_knobs(k)
    entry = next(iter(obj_t.archive.values()))
    assert entry.knobs["clip"] == 1 and entry.inflated is False
    obj = Objective(cell, D1, cache)
    obj.eval_knobs(k)
    e2 = next(iter(obj.archive.values()))
    assert e2.inflated is True and e2.knobs["clip"] == 0
    assert best_archived(obj.archive, clip=0, truthful_only=True) is None
    assert best_archived(obj.archive, clip=0) is e2


def test_corner_controls_use_exact_knobs_at_tier_boundaries():
    c = MarketConfig.default()
    providers = (ProviderParams(q_max=0.8, a=0.02, b=0.32, k=6),) + c.providers[6:9]
    cfg = MarketConfig(N=4, J=30, T=5, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=providers, alpha=c.alpha, budget=0.0)
    cache = SeedCache()
    cell = Cell(cfg=cfg, rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=0, seeds=(1,), name="tier")
    obj = Objective(cell, D1, cache)
    ctrl = dict((knob_key(k), f) for k, f in corner_controls(obj, D1))
    honest = D1.honest_point()
    exact = ctrl[knob_key(honest)]
    via_inverse = obj(D1.inverse(honest, near=1e-9))
    assert exact > via_inverse            # claim 0.8 is tier 3 at P3; one ulp below is tier 2 at P2
    assert len(ctrl) == 32 and all(np.isfinite(f) for f in ctrl.values())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_search.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.search'`

- [ ] **Step 3: Write the implementation**

```python
# sim/search.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import cma
import numpy as np

from .cell import Cell, SeedCache, run_focal
from .policies.families import Family, knob_key


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
class ArchiveEntry:
    knobs: dict
    f: float
    per_seed_profit: np.ndarray
    per_seed_normalized: np.ndarray
    inflated: bool
    source: str


class Objective:
    """Mean over the cell's seeds of per-seed normalized profit pi / (S* / N).
    The reference is subtracted after reference selection, never here. Every
    evaluated point goes to the archive with its per-seed values and whether
    the focal provider ever claimed above its effort (spec 5.2)."""

    def __init__(self, cell: Cell, family: Family, cache: SeedCache, force_clip: bool = False) -> None:
        self.cell, self.family, self.cache, self.force_clip = cell, family, cache, force_clip
        self.archive: dict[tuple, ArchiveEntry] = {}
        self.evals = 0

    def knobs_of(self, x: np.ndarray) -> dict:
        k = self.family.transform(x)
        return self.family.project(k) if self.force_clip else k

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        knobs = self.family.project(knobs) if self.force_clip else dict(knobs)
        fr = run_focal(self.cell, lambda: self.family.make(knobs), self.cache)
        f = float(fr.normalized.mean())
        key = knob_key(knobs)
        if key not in self.archive:
            self.archive[key] = ArchiveEntry(knobs=dict(knobs), f=f, per_seed_profit=fr.profit, per_seed_normalized=fr.normalized,
                                             inflated=fr.inflated, source=source)
        self.evals += 1
        return f

    def __call__(self, x: np.ndarray) -> float:
        return self.eval_knobs(self.knobs_of(x))


def best_archived(archive: dict, clip: int, truthful_only: bool = False) -> ArchiveEntry | None:
    best = None
    for e in archive.values():
        if e.knobs["clip"] != clip or (truthful_only and e.inflated):
            continue
        if best is None or e.f > best.f:
            best = e
    return best


@dataclass
class SearchResult:
    best_x: np.ndarray
    best_knobs: dict
    best_f: float
    best_source: str
    restart_bests: list
    evals: int
    trace: list
    incumbent_scores: dict
    projection_f: float
    replaced_by_projection: bool
    archive: dict = field(default_factory=dict)


def cma_search(objective, family: Family, settings: SearchSettings, seed: int,
               incumbents: dict[str, dict] | None = None) -> SearchResult:
    """CMA-ES maximization with registered restarts and a fixed evaluation budget
    per restart (incumbent re-evaluations count). Registered incumbents and the
    projection of the best point are evaluated exactly, outside the budget."""
    starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed})
    best_x, best_knobs, best_f, best_source = None, None, -np.inf, ""
    restart_bests, trace, evals = [], [], 0
    for r in range(settings.restarts):
        x0 = starts[r % len(starts)]
        es = cma.CMAEvolutionStrategy(x0, settings.sigma0,
                                      {"popsize": settings.popsize, "seed": int(seed) + 1 + r, "verbose": -9, "verb_log": 0})
        used, it = 0, 0
        r_best_x, r_best_f = x0.copy(), objective(x0)
        used += 1; evals += 1
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
        restart_bests.append(r_best_f)
        if r_best_f > best_f:
            best_x, best_knobs, best_f, best_source = r_best_x.copy(), objective.knobs_of(r_best_x), r_best_f, f"restart_{r}"
    incumbent_scores: dict[str, float] = {}
    for name, k in (incumbents or {}).items():
        f = objective.eval_knobs(k, source=f"incumbent:{name}")
        incumbent_scores[name] = float(f)
        if f > best_f:
            best_x, best_knobs, best_f, best_source = family.inverse(k, settings.near_corner), dict(k), float(f), f"incumbent:{name}"
    proj = family.project(best_knobs)
    projection_f = float(objective.eval_knobs(proj, source="projection"))
    replaced = projection_f > best_f
    if replaced:
        best_x, best_knobs, best_f, best_source = family.inverse(proj, settings.near_corner), proj, projection_f, "projection"
    return SearchResult(best_x=best_x, best_knobs=best_knobs, best_f=float(best_f), best_source=best_source,
                        restart_bests=restart_bests, evals=evals, trace=trace, incumbent_scores=incumbent_scores,
                        projection_f=projection_f, replaced_by_projection=replaced, archive=objective.archive)


def corner_controls(objective, family: Family) -> list[tuple[dict, float]]:
    """Exact corners (knobs at 0 or 1), one evaluation each, outside the search budget (spec 5.3)."""
    return [(k, float(objective.eval_knobs(k, source="corner"))) for k in family.corners()]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_search.py -v`
Expected: PASS (6 tests). The analytic check runs 1,500 evaluations on two 20-round episodes with 30 jobs; expect under a minute. If `max(res.restart_bests[2:])` falls short of `0.99 * analytic` on this machine, record the restart values in the ledger and rule: the registered near-full-cheat start is allowed to be the recovering restart only if the executor also shows that a Sobol restart reaches 0.95 of the analytic profit; otherwise the search settings are suspect and the task stops.

- [ ] **Step 5: Commit**

```bash
git add sim/search.py tests/test_search.py
git commit -m "feat: objective with evaluation archive, CMA-ES search with registered incumbents and projection replacement, exact corner controls"
```

---

### Task 7: Twin and attack searches, reference selection from the bounded projected set, gain decomposition, per-seed output rows

**Files:**
- Create: `sim/reference.py`
- Test: `tests/test_reference.py`

**Interfaces:**
- Consumes: Tasks 5 and 6, `sim.metrics.harm`.
- Produces:
  - `REFERENCE_ORDER = ("abstain", "honest_max", "twin_search", "attack_projection", "archive_clip1", "archive_truthful_clip0", "bank")`.
  - `Candidate(name, policy_factory, knobs: dict | None, known_profit: np.ndarray | None = None, known_normalized: np.ndarray | None = None)`: a known value is a dev-train observation the archive already holds, so selection needs no new run for it.
  - `twin_search(cell, family, cache, settings, seed) -> SearchResult` (forced clip; `best_knobs` is the projected point).
  - `attack_search(cell, family, cache, settings, seed, twin: SearchResult) -> SearchResult` with incumbents `twin_best` and `honest_point`.
  - `reference_candidates(cell, family, attack: SearchResult, twin: SearchResult, bank_members: list[dict], order=REFERENCE_ORDER) -> list[Candidate]`: abstention (known 0), honest-max, the twin best (known), the projection of the selected attack (known from the search's projection evaluation), the best archived clip = 1 point (known), the best archived clip = 0 point that never inflated (admitted as its projection with its observed values), and the projection of every bank member; de-duplicated by `knob_key`, first in order wins.
  - `select_reference(cell, candidates, cache) -> ReferenceChoice(candidate, per_seed_profit, per_seed_normalized, scores: dict[str, float])`: highest mean normalized profit on the cell's seeds, ties to the earlier candidate.
  - `evaluate_gain(cell, family, attack_knobs, reference: Candidate, cache) -> GainResult`: runs the attack, the clipped attack, the reference, and honest-max on the cell's seeds; `gain = (profit_attack - profit_ref) / (S*/N)` per seed, `inflation_term = (profit_attack - profit_clip) / (S*/N)`, `selection_term = (profit_clip - profit_ref) / (S*/N)`; gross and net efficiencies; audit cost, audit spend, audited fraction (attack run); harm (accounting and direct); focal served, failures, entry cost, identities; others' profit.
  - `seed_rows(cell, g: GainResult, meta: dict) -> list[dict]` and `ROW_FIELDS` (the CSV schema: `meta` keys first, then the metrics).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reference.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell, run_focal
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, knob_key
from sim.policies.honest import HonestMax
from sim.reference import (REFERENCE_ORDER, Candidate, twin_search, attack_search, reference_candidates,
                           select_reference, evaluate_gain, seed_rows, ROW_FIELDS)
from sim.search import SearchSettings, Objective


def fixture_cfg(budget=0.0):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=budget)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=1, evals_per_restart=40, reeval_every=10, near_corner=0.02, sobol_seed=3)


def cell_on(prices, seeds=(1, 2), focal=3):
    return Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(*prices), focal=focal, seeds=seeds, name="c")


def test_candidates_come_from_archive_in_registered_order_and_known_values_skip_runs():
    cache = SeedCache()
    cell = cell_on((0.20, 0.35, 0.50))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    assert set(at.incumbent_scores) == {"twin_best", "honest_point"}
    cands = reference_candidates(cell, D1, at, tw, bank_members=[])
    names = [c.name for c in cands]
    assert names[:3] == ["abstain", "honest_max", "twin_search"] and "attack_projection" in names
    assert all(c.knobs is None or c.knobs["clip"] == 1 for c in cands)
    assert len({knob_key(c.knobs) for c in cands if c.knobs}) == len([c for c in cands if c.knobs])
    runs_before = cache.runs
    ref = select_reference(cell, cands, cache)
    assert cache.runs - runs_before == len(cell.seeds)          # only honest_max needed a run
    assert set(ref.scores) == set(names) and ref.candidate.name in names
    assert ref.scores["abstain"] == 0.0


def test_twin_point_as_attacker_reproduces_trajectory():
    cache = SeedCache()
    cell = cell_on((0.20, 0.35, 0.50), seeds=(1,))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    att = Objective(cell, D1, cache)
    for entry in list(tw.archive.values())[:5]:
        # the twin candidate re-run as an attacker with clip = 1 reproduces its value and never inflates (spec 5.2 pre-lock test)
        att.eval_knobs(entry.knobs)
        a = att.archive[knob_key(entry.knobs)]
        assert a.knobs["clip"] == 1 and a.f == entry.f and np.array_equal(a.per_seed_profit, entry.per_seed_profit) and a.inflated is False
    # the clipped-attack run of section 7 is the same policy with the clip knob set: efforts unchanged, claims = min(claim, effort)
    k = {"u": 0.4, "m": 0.9, "s": 0.05, "w": 0.2, "clip": 0}
    raw = run_focal(cell, lambda: D1.make(k), cache).results[0]
    clp = run_focal(cell, lambda: D1.make(D1.project(k)), cache).results[0]
    assert np.array_equal(raw.efforts[:, 3], clp.efforts[:, 3])
    assert np.allclose(clp.claims[:, 3], np.minimum(raw.claims[:, 3], raw.efforts[:, 3]))


def test_honest_attack_against_honest_reference_has_gain_exactly_zero():
    cache = SeedCache()
    cell = cell_on((0.25, 0.40, 0.55))
    ref = select_reference(cell, [Candidate("honest_max", HonestMax, None)], cache)
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    assert np.all(g.gain == 0.0) and np.all(g.inflation_term == 0.0) and np.all(g.selection_term == 0.0)
    assert np.all(g.eff_attack == g.eff_ref) and np.all(g.eff_attack == g.eff_honest)


def test_gain_on_other_seeds_subtracts_reference_on_those_seeds():
    cache = SeedCache()
    train = cell_on((0.25, 0.40, 0.55), seeds=(1, 2))
    ref = select_reference(train, [Candidate("honest_max", HonestMax, None)], cache)
    val = Cell(cfg=train.cfg, rule_factory=train.rule_factory, focal=train.focal, seeds=(3, 4, 5), name="val")
    g = evaluate_gain(val, D1, D1.honest_point(), ref.candidate, cache)
    assert g.gain.shape == (3,) and np.all(g.gain == 0.0)
    assert g.profit_ref.shape == (3,) and np.array_equal(g.profit_ref, g.profit_attack)


def test_full_cheat_has_positive_gain_and_decomposition_adds_up():
    cache = SeedCache()
    cell = cell_on((0.20, 0.35, 0.50))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    attack = {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}
    ref = select_reference(cell, reference_candidates(cell, D1, at, tw, []), cache)
    g = evaluate_gain(cell, D1, attack, ref.candidate, cache)
    assert g.gain.mean() > 0
    assert np.allclose(g.gain, g.inflation_term + g.selection_term)
    assert g.eff_attack.shape == (2,) and np.all(np.isfinite(g.eff_honest)) and np.all(g.audit_spend_attack == 0.0)
    assert np.allclose(g.harm_accounting, g.harm_direct, atol=1e-9)


def test_abstention_wins_when_everything_loses_money():
    cache = SeedCache()
    # every tier price is below the fixed cost a = 0.02: any service loses money; a twin that serves nothing ties abstention at 0
    cell = cell_on((0.005, 0.010, 0.015), seeds=(1,))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    ref = select_reference(cell, reference_candidates(cell, D1, at, tw, []), cache)
    assert ref.candidate.name == "abstain" and ref.per_seed_profit[0] == 0.0
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    assert g.gain[0] < 0.0


def test_seed_rows_follow_the_schema():
    cache = SeedCache()
    cell = cell_on((0.25, 0.40, 0.55))
    ref = select_reference(cell, [Candidate("honest_max", HonestMax, None)], cache)
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    rows = seed_rows(cell, g, {"cell": "c", "rule": "B1"})
    assert len(rows) == 2 and list(rows[0]) == ["cell", "rule"] + ROW_FIELDS
    assert rows[0]["seed"] == 1 and rows[0]["sstar"] > 0 and rows[0]["n_identities_attack"] == 4
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
from .metrics import harm
from .policies.families import Family, knob_key
from .policies.honest import HonestMax
from .search import Objective, SearchResult, SearchSettings, best_archived, cma_search

REFERENCE_ORDER = ("abstain", "honest_max", "twin_search", "attack_projection", "archive_clip1", "archive_truthful_clip0", "bank")


@dataclass(frozen=True)
class Candidate:
    name: str
    policy_factory: Callable
    knobs: dict | None
    known_profit: np.ndarray | None = None
    known_normalized: np.ndarray | None = None


@dataclass
class ReferenceChoice:
    candidate: Candidate
    per_seed_profit: np.ndarray
    per_seed_normalized: np.ndarray
    scores: dict


def twin_search(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int) -> SearchResult:
    return cma_search(Objective(cell, family, cache, force_clip=True), family, settings, seed)


def attack_search(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int, twin: SearchResult) -> SearchResult:
    """Attack search with the twin best and the honest-max point as registered incumbents (spec 5.2)."""
    return cma_search(Objective(cell, family, cache), family, settings, seed,
                      incumbents={"twin_best": twin.best_knobs, "honest_point": family.honest_point()})


def _factory(family: Family, knobs: dict) -> Callable:
    return lambda: family.make(knobs)


def _known(entry) -> dict:
    return {} if entry is None else {"known_profit": entry.per_seed_profit, "known_normalized": entry.per_seed_normalized}


def reference_candidates(cell: Cell, family: Family, attack: SearchResult, twin: SearchResult,
                         bank_members: list[dict], order=REFERENCE_ORDER) -> list[Candidate]:
    """Every reference candidate in projected form, in registered tie order (spec 5.2)."""
    n = len(cell.seeds)
    groups: dict[str, list[Candidate]] = {}
    groups["abstain"] = [Candidate("abstain", Abstain, None, np.zeros(n), np.zeros(n))]
    groups["honest_max"] = [Candidate("honest_max", HonestMax, None)]
    tw = family.project(twin.best_knobs)
    groups["twin_search"] = [Candidate("twin_search", _factory(family, tw), tw, **_known(twin.archive.get(knob_key(tw))))]
    proj = family.project(attack.best_knobs)
    groups["attack_projection"] = [Candidate("attack_projection", _factory(family, proj), proj, **_known(attack.archive.get(knob_key(proj))))]
    e1 = best_archived(attack.archive, clip=1)
    groups["archive_clip1"] = [] if e1 is None else [Candidate("archive_clip1", _factory(family, e1.knobs), dict(e1.knobs), **_known(e1))]
    e0 = best_archived(attack.archive, clip=0, truthful_only=True)
    if e0 is None:
        groups["archive_truthful_clip0"] = []
    else:   # never inflated on dev-train: its projection has the same trajectory, so its observed values are its projected values
        p0 = family.project(e0.knobs)
        groups["archive_truthful_clip0"] = [Candidate("archive_truthful_clip0", _factory(family, p0), p0, **_known(e0))]
    groups["bank"] = [Candidate(f"bank_{i}", _factory(family, family.project(m)), family.project(m)) for i, m in enumerate(bank_members)]
    out, seen = [], set()
    for g in order:
        for c in groups.get(g, []):
            key = knob_key(c.knobs) if c.knobs is not None else ("name", c.name)
            if key in seen:
                continue
            seen.add(key); out.append(c)
    return out


def select_reference(cell: Cell, candidates: list[Candidate], cache: SeedCache) -> ReferenceChoice:
    """Highest mean normalized profit on the cell's seeds; ties to the earlier candidate; known values need no run."""
    best, scores = None, {}
    for c in candidates:
        if c.known_normalized is not None and len(c.known_normalized) == len(cell.seeds):
            profit, norm = c.known_profit, c.known_normalized
        else:
            fr = run_focal(cell, c.policy_factory, cache)
            profit, norm = fr.profit, fr.normalized
        score = float(norm.mean())
        scores[c.name] = score
        if best is None or score > best[0]:
            best = (score, c, profit, norm)
    _, c, profit, norm = best
    return ReferenceChoice(candidate=c, per_seed_profit=np.asarray(profit, dtype=float), per_seed_normalized=np.asarray(norm, dtype=float), scores=scores)


@dataclass
class GainResult:
    gain: np.ndarray
    inflation_term: np.ndarray
    selection_term: np.ndarray
    profit_attack: np.ndarray
    profit_clip: np.ndarray
    profit_ref: np.ndarray
    profit_honest: np.ndarray
    sstar: np.ndarray
    eff_attack: np.ndarray
    eff_clip: np.ndarray
    eff_ref: np.ndarray
    eff_honest: np.ndarray
    net_eff_attack: np.ndarray
    net_eff_ref: np.ndarray
    audit_cost_attack: np.ndarray
    audit_spend_attack: np.ndarray
    audited_fraction_attack: np.ndarray
    harm_accounting: np.ndarray
    harm_direct: np.ndarray
    served_focal_attack: np.ndarray
    failures_focal_attack: np.ndarray
    entry_attack: np.ndarray
    n_identities_attack: np.ndarray
    others_profit_attack: np.ndarray
    seeds: tuple


METRIC_FIELDS = ["seed", "sstar", "gain", "inflation_term", "selection_term", "profit_attack", "profit_clip", "profit_ref",
                 "profit_honest", "eff_attack", "eff_clip", "eff_ref", "eff_honest", "net_eff_attack", "net_eff_ref",
                 "audit_cost_attack", "audit_spend_attack", "audited_fraction_attack", "harm_accounting", "harm_direct",
                 "served_focal_attack", "failures_focal_attack", "entry_attack", "n_identities_attack", "others_profit_attack"]
ROW_FIELDS = METRIC_FIELDS


def _gross(results) -> np.ndarray:
    return np.array([(r.W + r.audit_cost) / r.sstar for r in results])


def _net(results) -> np.ndarray:
    return np.array([r.W / r.sstar for r in results])


def evaluate_gain(cell: Cell, family: Family, attack_knobs: dict, reference: Candidate, cache: SeedCache) -> GainResult:
    attack = run_focal(cell, _factory(family, dict(attack_knobs)), cache)
    clipped = run_focal(cell, _factory(family, family.project(attack_knobs)), cache)
    ref = run_focal(cell, reference.policy_factory, cache)
    honest = run_focal(cell, HonestMax, cache)
    N, f = cell.cfg.N, cell.focal
    sstar = np.array([r.sstar for r in attack.results])
    scale = sstar / N
    inflation = (attack.profit - clipped.profit) / scale
    selection = (clipped.profit - ref.profit) / scale
    hm = np.array([harm(a, r, f) for a, r in zip(attack.results, ref.results)])
    served = np.array([int(r.served[:, f].sum()) for r in attack.results])
    audited = np.array([int(r.audits.sum()) for r in attack.results])
    total_served = np.array([int(r.served.sum()) for r in attack.results])
    return GainResult(
        gain=inflation + selection, inflation_term=inflation, selection_term=selection,
        profit_attack=attack.profit, profit_clip=clipped.profit, profit_ref=ref.profit, profit_honest=honest.profit, sstar=sstar,
        eff_attack=_gross(attack.results), eff_clip=_gross(clipped.results), eff_ref=_gross(ref.results), eff_honest=_gross(honest.results),
        net_eff_attack=_net(attack.results), net_eff_ref=_net(ref.results),
        audit_cost_attack=np.array([r.audit_cost for r in attack.results]),
        audit_spend_attack=np.array([r.audit_cost / r.sstar for r in attack.results]),
        audited_fraction_attack=np.where(total_served > 0, audited / np.maximum(total_served, 1), 0.0),
        harm_accounting=hm[:, 0], harm_direct=hm[:, 1],
        served_focal_attack=served, failures_focal_attack=np.array([int(r.failures[:, f].sum()) for r in attack.results]),
        entry_attack=np.array([r.entry for r in attack.results]),
        n_identities_attack=np.array([r.n_identities for r in attack.results]),
        others_profit_attack=np.array([float(r.profit.sum() - r.profit[f]) for r in attack.results]),
        seeds=tuple(cell.seeds))


def seed_rows(cell: Cell, g: GainResult, meta: dict) -> list[dict]:
    rows = []
    for k, seed in enumerate(cell.seeds):
        row = dict(meta)
        for name in METRIC_FIELDS:
            if name == "seed":
                row["seed"] = int(seed)
            else:
                v = getattr(g, name)[k]
                row[name] = int(v) if isinstance(v, (np.integer, int)) else float(v)
        rows.append(row)
    return rows
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_reference.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/reference.py tests/test_reference.py
git commit -m "feat: twin and attack searches with incumbents, reference selection from the archive-bounded projected set, gain decomposition, per-seed row schema"
```

---

### Task 8: Candidate bank and the bank pass

**Files:**
- Create: `sim/bank.py`
- Test: `tests/test_bank.py`

**Interfaces:**
- Consumes: Tasks 4 to 6.
- Produces: `Bank()` with `add(family_name, knobs, origin)`, `members_for(family_name) -> list[dict]` (typed filter: D1 members enter D2 cells through `embed_d1_in_d2`; D2 members never enter D1; the 128 D2 corners are members of every D2 cell with origin `corner`; duplicates removed by `knob_key`), `projected_members_for(family_name) -> list[dict]` (the projection of every compatible member, de-duplicated; what reference selection admits), `evaluate(cell, family, cache) -> list[tuple[dict, float, str]]` sorted by mean normalized profit (members as attacks, unprojected), `bank_pass(cell, family, cache, incumbent_f: float) -> BankPass(ranked, best_knobs, best_f, best_origin, improved)` (the incumbent is replaced when a member scores higher, spec 8), `transfer_rows(cell_name, incumbent_f, bp) -> dict`, `to_json() / from_json(text)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_bank.py
import pytest
from sim.bank import Bank
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2, knob_key


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


def test_typed_filter_corners_projection_and_dedupe():
    b = Bank()
    b.add("D1", {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="B1/D1/0.05")
    b.add("D1", {"u": 0.5000000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="dup")
    b.add("D2", {"u0": 0.1, "m0": 0.2, "s": 0.0, "d": 0.5, "r": 0.1, "w": 0.0, "clip": 1}, origin="B2/D2/0.05")
    d1 = b.members_for("D1"); d2 = b.members_for("D2")
    assert len(d1) == 1                                   # the D2 member never enters D1; duplicate removed
    assert len(d2) == 2 + 128                             # both members (D1 embedded) plus the D2 corners
    assert any(m["d"] == 0.0 and m["u0"] == 0.5 for m in d2)
    p2 = b.projected_members_for("D2")
    assert len(p2) == 2 + 64 and all(m["clip"] == 1 for m in p2)
    assert len({knob_key(m) for m in p2}) == len(p2)
    b2 = Bank.from_json(b.to_json())
    assert len(b2.members_for("D2")) == len(d2)


def test_bank_pass_replaces_incumbent_when_a_member_scores_higher():
    b = Bank()
    b.add("D1", {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, origin="cheat")
    b.add("D1", {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}, origin="honest")
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    cache = SeedCache()
    ranked = b.evaluate(cell, D1, cache)
    assert ranked[0][2] == "cheat" and ranked[0][1] > ranked[-1][1]
    bp = b.bank_pass(cell, D1, cache, incumbent_f=ranked[-1][1])
    assert bp.improved is True and bp.best_origin == "cheat" and bp.best_f == ranked[0][1]
    bp2 = b.bank_pass(cell, D1, cache, incumbent_f=ranked[0][1] + 1.0)
    assert bp2.improved is False
    row = Bank.transfer_rows("c", ranked[-1][1], bp)
    assert row["improved"] is True and row["best_origin"] == "cheat"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_bank.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.bank'`

- [ ] **Step 3: Write the implementation**

```python
# sim/bank.py
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .cell import Cell, SeedCache, run_focal
from .policies.families import D2, FAMILIES, Family, embed_d1_in_d2, knob_key


@dataclass
class BankPass:
    ranked: list            # (knobs, f, origin) descending
    best_knobs: dict | None
    best_f: float
    best_origin: str | None
    improved: bool


@dataclass
class Bank:
    entries: list = field(default_factory=list)   # (family_name, knobs, origin)

    def add(self, family_name: str, knobs: dict, origin: str) -> None:
        if family_name not in FAMILIES:
            raise ValueError(f"unknown family {family_name}")
        if not any(f == family_name and knob_key(k) == knob_key(knobs) for f, k, _ in self.entries):
            self.entries.append((family_name, dict(knobs), origin))

    def _compatible(self, target: str) -> list[tuple[dict, str]]:
        out, seen = [], set()
        for f, k, origin in self.entries:
            if f == target:
                m = dict(k)
            elif f == "D1" and target == "D2":
                m = embed_d1_in_d2(k)
            else:
                continue
            key = knob_key(m)
            if key not in seen:
                seen.add(key); out.append((m, origin))
        if target == "D2":
            for c in D2.corners():
                key = knob_key(c)
                if key not in seen:
                    seen.add(key); out.append((c, "corner"))
        return out

    def members_for(self, family_name: str) -> list[dict]:
        return [m for m, _ in self._compatible(family_name)]

    def projected_members_for(self, family_name: str) -> list[dict]:
        fam = FAMILIES[family_name]
        out, seen = [], set()
        for m, _ in self._compatible(family_name):
            p = fam.project(m); key = knob_key(p)
            if key not in seen:
                seen.add(key); out.append(p)
        return out

    def evaluate(self, cell: Cell, family: Family, cache: SeedCache) -> list[tuple[dict, float, str]]:
        scored = []
        for m, origin in self._compatible(family.name):
            fr = run_focal(cell, lambda m=m: family.make(m), cache)
            scored.append((m, float(fr.normalized.mean()), origin))
        scored.sort(key=lambda t: -t[1])
        return scored

    def bank_pass(self, cell: Cell, family: Family, cache: SeedCache, incumbent_f: float) -> BankPass:
        ranked = self.evaluate(cell, family, cache)
        if not ranked:
            return BankPass(ranked=[], best_knobs=None, best_f=float(incumbent_f), best_origin=None, improved=False)
        m, f, origin = ranked[0]
        improved = f > incumbent_f
        return BankPass(ranked=ranked, best_knobs=m if improved else None, best_f=f if improved else float(incumbent_f),
                        best_origin=origin if improved else None, improved=improved)

    @staticmethod
    def transfer_rows(cell_name: str, incumbent_f: float, bp: BankPass) -> dict:
        return {"cell": cell_name, "incumbent": float(incumbent_f), "best_bank": float(bp.ranked[0][1]) if bp.ranked else None,
                "best_origin": bp.ranked[0][2] if bp.ranked else None, "improved": bool(bp.improved)}

    def to_json(self) -> str:
        return json.dumps([{"family": f, "knobs": k, "origin": o} for f, k, o in self.entries], indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Bank":
        b = cls()
        for e in json.loads(text):
            b.add(e["family"], e["knobs"], e["origin"])
        return b
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_bank.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/bank.py tests/test_bank.py
git commit -m "feat: candidate bank with typed filter, projected members, bank pass, transfer rows, JSON round trip"
```

---

### Task 9: Calibration of S_hat, n_FB, and m, bound to the market

**Files:**
- Create: `sim/calibrate.py`, `scripts/calibrate.py`
- Test: `tests/test_calibrate.py`

**Interfaces:**
- Consumes: `market_config_from_locked` (Task 1), `market_key` (Task 5).
- Produces:
  - `first_best_served(cfg, values_t) -> int` (jobs served in the first-best assignment, pairs with positive weight).
  - `Calibration(S_hat, n_FB, m, market_key, T, seeds)` with `as_dict()`; `calibrate(cfg_base, seeds) -> Calibration` (validates the configuration first; refuses an empty seed list).
  - `cell_config(cfg_base, cal, rho, beta) -> MarketConfig` with `alpha = rho * m` and `budget = beta * S_hat`; refuses a calibration whose `market_key` differs from the base configuration's.
  - `load_calibration(path) -> Calibration`, `save_calibration(cal, path)`.
  - `scripts/calibrate.py --seeds 20 --out experiments/calibration.json`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_calibrate.py
import json, subprocess, sys
import numpy as np
import pytest
from sim.calibrate import calibrate, cell_config, first_best_served, load_calibration, save_calibration
from sim.cell import market_key
from sim.config import MarketConfig, ProviderParams
from sim.locked import load_locked, market_config_from_locked


def test_first_best_served_counts_positive_pairs():
    cfg = MarketConfig(N=1, J=3, T=1, sigma=0.0, e=0.0, v_min=0.6, v_max=2.0,
                       providers=(ProviderParams(q_max=1.0, a=0.0, b=0.5, k=2),), alpha=0.0, budget=0.0)
    assert first_best_served(cfg, np.array([2.0, 1.0, 0.6])) == 2


def test_calibration_binds_to_the_market_and_cells_derive_alpha_and_budget():
    cfg = market_config_from_locked(load_locked())
    cal = calibrate(cfg, seeds=[4000, 4001])
    assert cal.S_hat > 0 and cal.n_FB > 0 and cal.m == pytest.approx(cal.S_hat / cal.n_FB)
    assert cal.market_key == market_key(cfg) and cal.T == cfg.T
    c = cell_config(cfg, cal, rho=0.2, beta=0.05)
    c.validate()
    assert c.alpha == pytest.approx(0.2 * cal.m) and c.budget == pytest.approx(0.05 * cal.S_hat)
    assert cell_config(cfg, cal, rho=1.0, beta=0.0).budget == 0.0


def test_calibrate_refuses_invalid_config_and_empty_seeds():
    c = MarketConfig.default()
    bad = MarketConfig(N=c.N, J=c.J, T=c.T, sigma=c.sigma, e=c.e, v_min=0.1, v_max=c.v_max, providers=c.providers, alpha=0.0, budget=0.0)
    with pytest.raises(ValueError):
        calibrate(bad, seeds=[4000])
    with pytest.raises(ValueError):
        calibrate(c, seeds=[])


def test_cell_config_refuses_foreign_calibration(tmp_path):
    cfg = market_config_from_locked(load_locked())
    cal = calibrate(cfg, seeds=[4000])
    other = MarketConfig(N=cfg.N, J=cfg.J, T=cfg.T + 1, sigma=cfg.sigma, e=cfg.e, v_min=cfg.v_min, v_max=cfg.v_max,
                         providers=cfg.providers, alpha=0.0, budget=0.0)
    with pytest.raises(ValueError, match="calibration"):
        cell_config(other, cal, rho=0.2, beta=0.05)
    p = tmp_path / "cal.json"; save_calibration(cal, p)
    assert load_calibration(p) == cal


def test_calibrate_script_writes_json(tmp_path):
    out = tmp_path / "cal.json"
    subprocess.run([sys.executable, "scripts/calibrate.py", "--seeds", "2", "--out", str(out)], check=True)
    cal = json.loads(out.read_text())
    assert set(cal) == {"S_hat", "n_FB", "m", "market_key", "T", "seeds"} and cal["seeds"] == [4000, 4001]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_calibrate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.calibrate'`

- [ ] **Step 3: Write the implementation**

```python
# sim/calibrate.py
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from .cell import market_key
from .config import MarketConfig
from .firstbest import first_best_episode
from .rng import make_draws


@dataclass(frozen=True)
class Calibration:
    S_hat: float
    n_FB: float
    m: float
    market_key: str
    T: int
    seeds: tuple

    def as_dict(self) -> dict:
        d = asdict(self); d["seeds"] = list(self.seeds); return d


def first_best_served(cfg: MarketConfig, values_t: np.ndarray) -> int:
    q_full = np.array([p.q_max for p in cfg.providers]); cost_full = cfg.cost_full
    owner = np.repeat(np.arange(cfg.N), [p.k for p in cfg.providers])
    w = np.maximum(values_t[None, :] * q_full[owner][:, None] - cost_full[owner][:, None], 0.0)
    rows, cols = linear_sum_assignment(w, maximize=True)
    return int((w[rows, cols] > 0).sum())


def calibrate(cfg_base: MarketConfig, seeds) -> Calibration:
    """S_hat and n_FB on the calibration seeds (spec 3). Refuses an invalid market or no seeds."""
    cfg_base.validate()
    seeds = [int(s) for s in seeds]
    if not seeds:
        raise ValueError("calibration needs at least one seed")
    totals, served = [], []
    for s in seeds:
        d = make_draws(cfg_base, s)
        totals.append(first_best_episode(cfg_base, d))
        served.append(sum(first_best_served(cfg_base, d.values[t]) for t in range(cfg_base.T)))
    S_hat = float(np.mean(totals)); n_FB = float(np.mean(served))
    return Calibration(S_hat=S_hat, n_FB=n_FB, m=S_hat / n_FB, market_key=market_key(cfg_base), T=int(cfg_base.T), seeds=tuple(seeds))


def cell_config(cfg_base: MarketConfig, cal: Calibration, rho: float, beta: float) -> MarketConfig:
    """alpha = rho * m and B = beta * S_hat for one cell; the calibration must belong to this market."""
    if cal.market_key != market_key(cfg_base):
        raise ValueError("calibration belongs to a different market configuration")
    cfg = MarketConfig(N=cfg_base.N, J=cfg_base.J, T=cfg_base.T, sigma=cfg_base.sigma, e=cfg_base.e, v_min=cfg_base.v_min,
                       v_max=cfg_base.v_max, providers=cfg_base.providers, alpha=float(rho) * cal.m, budget=float(beta) * cal.S_hat)
    cfg.validate()
    return cfg


def save_calibration(cal: Calibration, path: str | Path) -> None:
    Path(path).write_text(json.dumps(cal.as_dict(), indent=2, sort_keys=True) + "\n")


def load_calibration(path: str | Path) -> Calibration:
    d = json.loads(Path(path).read_text())
    return Calibration(S_hat=float(d["S_hat"]), n_FB=float(d["n_FB"]), m=float(d["m"]), market_key=str(d["market_key"]),
                       T=int(d["T"]), seeds=tuple(int(s) for s in d["seeds"]))
```

```python
# scripts/calibrate.py
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked, seeds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20, help="how many calibration seeds to use")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lk = load_locked()
    cal = calibrate(market_config_from_locked(lk), seeds(lk, "calibration")[: args.seeds])
    save_calibration(cal, args.out)
    print(json.dumps(cal.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_calibrate.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/calibrate.py scripts/calibrate.py tests/test_calibrate.py
git commit -m "feat: calibration of S_hat, n_FB, m bound to the market; cells derive alpha and budget"
```

---

### Task 10: Positions, headline selection, and the search checks

**Files:**
- Create: `sim/positions.py`, `sim/search_checks.py`
- Test: `tests/test_positions_checks.py`

**Interfaces:**
- Consumes: Tasks 6 and 7.
- Produces:
  - `positions(cfg) -> dict[str, int]` with keys `low, median, high` by `b_i q_max_i` (ties by index); `median` is the middle element of the sorted order.
  - `headline_position(gain_by_position: dict[str, float]) -> str` (highest mean dev-train gain, tie order `low, median, high`).
  - `restart_spread(attack: SearchResult, twin: SearchResult) -> dict` with `attack_bests`, `reference_bests` (the twin's restart bests), `attack_spread`, `reference_spread` (check (c): both objectives reported separately).
  - `FixedClipObjective(objective: Objective, clip: int)`: the same protocol with the clip coordinate fixed.
  - `doubling_check(cell, family, cache, settings, seed, base_attack, base_twin, bank_members, order) -> DoublingCheck(attack_base_f, attack_doubled_f, clip0_f, clip1_f, ref_base_f, ref_doubled_f, ref_base_name, ref_doubled_name, gain_base, gain_doubled, delta_gain, passed)`: the extra budget equal to the base search is split half and half between a search with clip fixed at 0 and a search with clip fixed at 1 on the same seeds; the doubled attack is the best of the base and the two fixed-clip searches (each already projection-finalized); the reference is selected by the full section 5.2 rule for both the base archive and the merged archive; `passed` when `|delta_gain| < 0.005` (check (b)).
  - `twin_vs_honest(twin: SearchResult, honest_f: float) -> TwinCheck(twin_f, honest_f, passed)` with `passed = twin_f >= honest_f - 0.01 * abs(honest_f)` (check (d), relative 1%).

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
from sim.search import SearchSettings, Objective
from sim.search_checks import restart_spread, doubling_check, twin_vs_honest, FixedClipObjective
from sim.reference import twin_search, attack_search, REFERENCE_ORDER


def test_positions_by_b_times_qmax_and_headline():
    cfg = MarketConfig.default()
    pos = positions(cfg)
    score = [p.b * p.q_max for p in cfg.providers]
    order = sorted(range(cfg.N), key=lambda i: (score[i], i))
    assert pos == {"low": order[0], "median": order[cfg.N // 2], "high": order[-1]}
    assert headline_position({"low": 0.1, "median": 0.3, "high": 0.3}) == "median"
    assert headline_position({"low": 0.5, "median": 0.3, "high": 0.3}) == "low"


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=24, reeval_every=10, near_corner=0.02, sobol_seed=3)


def test_fixed_clip_objective_fixes_the_clip():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    f0 = FixedClipObjective(Objective(cell, D1, cache), clip=0); f1 = FixedClipObjective(Objective(cell, D1, cache), clip=1)
    x = np.full(D1.dim, 3.0)
    assert f0.knobs_of(x)["clip"] == 0 and f1.knobs_of(x)["clip"] == 1
    f0(x); f1(x)
    assert all(e.knobs["clip"] == 0 for e in f0.archive.values()) and all(e.knobs["clip"] == 1 for e in f1.archive.values())


def test_doubling_spread_and_twin_vs_honest():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    runs_before = cache.runs
    dc = doubling_check(cell, D1, cache, SMALL, seed=0, base_attack=at, base_twin=tw, bank_members=[], order=REFERENCE_ORDER)
    # two fixed-clip searches at half the budget each, plus two projections and one honest-max run for each reference selection
    assert cache.runs - runs_before == 2 * (2 * 12) + 2 * 1 + 2 * 1
    assert dc.attack_doubled_f >= dc.attack_base_f - 1e-12 and np.isfinite(dc.clip0_f) and np.isfinite(dc.clip1_f)
    assert dc.delta_gain == pytest.approx(dc.gain_doubled - dc.gain_base) and isinstance(dc.passed, bool)
    assert dc.ref_base_name in REFERENCE_ORDER or dc.ref_base_name.startswith("bank_")
    sp = restart_spread(at, tw)
    assert sp["attack_spread"] >= 0.0 and sp["reference_spread"] >= 0.0 and len(sp["attack_bests"]) == 2
    chk = twin_vs_honest(tw, honest_f=at.incumbent_scores["honest_point"])
    assert chk.passed is (chk.twin_f >= chk.honest_f - 0.01 * abs(chk.honest_f))
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

from .cell import Cell, SeedCache
from .policies.families import Family
from .reference import reference_candidates, select_reference
from .search import Objective, SearchResult, SearchSettings, cma_search


def restart_spread(attack: SearchResult, twin: SearchResult) -> dict:
    """Check (c): attack and reference objectives per restart, reported separately."""
    return {"attack_bests": list(attack.restart_bests), "reference_bests": list(twin.restart_bests),
            "attack_spread": float(max(attack.restart_bests) - min(attack.restart_bests)),
            "reference_spread": float(max(twin.restart_bests) - min(twin.restart_bests))}


class FixedClipObjective:
    """The wrapped objective with the clip coordinate fixed; exact-knob evaluations keep their own clip."""

    def __init__(self, objective: Objective, clip: int) -> None:
        self.inner, self.clip = objective, int(clip)
        self.family = objective.family

    @property
    def archive(self):
        return self.inner.archive

    @property
    def evals(self):
        return self.inner.evals

    def knobs_of(self, x: np.ndarray) -> dict:
        k = self.inner.knobs_of(x); k["clip"] = self.clip
        return k

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        return self.inner.eval_knobs(knobs, source)

    def __call__(self, x: np.ndarray) -> float:
        return self.eval_knobs(self.knobs_of(x))


@dataclass
class DoublingCheck:
    attack_base_f: float
    attack_doubled_f: float
    clip0_f: float
    clip1_f: float
    ref_base_f: float
    ref_doubled_f: float
    ref_base_name: str
    ref_doubled_name: str
    gain_base: float
    gain_doubled: float
    delta_gain: float
    passed: bool


def doubling_check(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int,
                   base_attack: SearchResult, base_twin: SearchResult, bank_members: list[dict], order) -> DoublingCheck:
    """Check (b): the extra budget (equal to the base search) is split between a clip = 0 and a clip = 1 search;
    the reference is re-selected from the merged archive; the change in finalized dev-train gain must be under 0.5 points."""
    half = replace(settings, evals_per_restart=max(1, settings.evals_per_restart // 2))
    c0 = cma_search(FixedClipObjective(Objective(cell, family, cache), 0), family, half, seed + 100)
    c1 = cma_search(FixedClipObjective(Objective(cell, family, cache), 1), family, half, seed + 200)
    doubled = max((base_attack, c0, c1), key=lambda r: r.best_f)
    merged = replace(doubled, archive={**base_attack.archive, **c0.archive, **c1.archive})
    ref_base = select_reference(cell, reference_candidates(cell, family, base_attack, base_twin, bank_members, order), cache)
    ref_doubled = select_reference(cell, reference_candidates(cell, family, merged, base_twin, bank_members, order), cache)
    rb, rd = ref_base.scores[ref_base.candidate.name], ref_doubled.scores[ref_doubled.candidate.name]
    gain_base = base_attack.best_f - rb; gain_doubled = merged.best_f - rd
    delta = gain_doubled - gain_base
    return DoublingCheck(attack_base_f=base_attack.best_f, attack_doubled_f=merged.best_f, clip0_f=c0.best_f, clip1_f=c1.best_f,
                         ref_base_f=rb, ref_doubled_f=rd, ref_base_name=ref_base.candidate.name, ref_doubled_name=ref_doubled.candidate.name,
                         gain_base=gain_base, gain_doubled=gain_doubled, delta_gain=delta, passed=bool(abs(delta) < 0.005))


@dataclass
class TwinCheck:
    twin_f: float
    honest_f: float
    passed: bool


def twin_vs_honest(twin: SearchResult, honest_f: float) -> TwinCheck:
    """Check (d): the twin's objective is never below honest-max's by more than 1% (relative)."""
    return TwinCheck(twin_f=float(twin.best_f), honest_f=float(honest_f), passed=bool(twin.best_f >= honest_f - 0.01 * abs(honest_f)))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_positions_checks.py -v`
Expected: PASS (3 tests). The run-count assertion in the doubling test counts: each fixed-clip search uses 2 restarts x 12 evaluations on one seed (24 runs) plus one projection run; each reference selection runs honest-max once (the other candidates are known from the archives).

- [ ] **Step 5: Commit**

```bash
git add sim/positions.py sim/search_checks.py tests/test_positions_checks.py
git commit -m "feat: adversary positions, headline selection, restart spread with both objectives, clip-split doubling check on finalized gain, relative twin-vs-honest check"
```

---

### Task 11: All-deviators iterated best response

**Files:**
- Create: `sim/all_deviators.py`
- Test: `tests/test_all_deviators.py`

**Interfaces:**
- Consumes: `Cell.others`, `Objective`, `cma_search`, `run_profile`.
- Produces: `iterated_best_response(cfg, rule_factory, family, cache, settings, seeds, sweeps, seed=0) -> AllDeviatorsResult(profiles: list[list[dict]], values: list[list[float]], final_profile: list[dict], final_gross_eff: float, final_normalized_profit: list[float])`: every provider starts at the family's honest point; in each sweep, each provider in index order searches its best response to the current profile of the others and adopts the result when it scores strictly higher than its current policy on the same seeds (spec 5.3: 3 sweeps, 1 restart x 100 evaluations x 3 dev-train seeds per sweep and provider). `profiles[s][i]` is provider i's knobs after sweep s.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_all_deviators.py
import numpy as np
import pytest
from sim.all_deviators import iterated_best_response
from sim.cell import SeedCache
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D2
from sim.search import SearchSettings


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=8, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


def test_iterated_best_response_terminates_and_records_profiles():
    cache = SeedCache()
    settings = SearchSettings(popsize=8, sigma0=0.3, restarts=1, evals_per_restart=16, reeval_every=10, near_corner=0.02, sobol_seed=3)
    res = iterated_best_response(fixture_cfg(), lambda: PostedPrices(0.20, 0.35, 0.50), D2, cache, settings, seeds=(1,), sweeps=2)
    assert len(res.profiles) == 2 and all(len(p) == 4 for p in res.profiles)
    assert all(set(k) == set(D2.knobs) for p in res.profiles for k in p)
    assert len(res.values) == 2 and all(np.isfinite(v) for row in res.values for v in row)
    assert res.final_profile == res.profiles[-1] and np.isfinite(res.final_gross_eff)
    # under B1 without audits every provider gains from cheating: no one stays at the honest point after sweep 1
    assert all(k != D2.honest_point() for k in res.profiles[0])
    assert cache.runs == 2 * 4 * (16 + 1 + 1) + 1     # per provider and sweep: search, projection, current-value evaluation; one final profile run
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_all_deviators.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.all_deviators'`

- [ ] **Step 3: Write the implementation**

```python
# sim/all_deviators.py
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cell import Cell, SeedCache, run_profile
from .policies.families import Family
from .search import Objective, SearchSettings, cma_search


@dataclass
class AllDeviatorsResult:
    profiles: list
    values: list
    final_profile: list
    final_gross_eff: float
    final_normalized_profit: list


def iterated_best_response(cfg, rule_factory, family: Family, cache: SeedCache, settings: SearchSettings, seeds,
                           sweeps: int, seed: int = 0) -> AllDeviatorsResult:
    """Spec 5.3 all-deviators table: iterated best response, every provider on `family`."""
    N = cfg.N
    profile: list[dict] = [family.honest_point() for _ in range(N)]
    profiles, values = [], []
    for s in range(sweeps):
        row = []
        for i in range(N):
            others = tuple((j, (lambda k=profile[j]: family.make(k))) for j in range(N) if j != i)
            cell = Cell(cfg=cfg, rule_factory=rule_factory, focal=i, seeds=tuple(seeds), name=f"all_deviators/{i}", others=others)
            obj = Objective(cell, family, cache)
            current = obj.eval_knobs(profile[i], source="current")
            res = cma_search(obj, family, settings, seed=seed + s * N + i)
            if res.best_f > current:
                profile[i] = dict(res.best_knobs); row.append(float(res.best_f))
            else:
                row.append(float(current))
        profiles.append([dict(k) for k in profile]); values.append(row)
    results = run_profile(cfg, rule_factory, [(lambda k=k: family.make(k)) for k in profile], tuple(seeds), cache)
    eff = float(np.mean([(r.W + r.audit_cost) / r.sstar for r in results]))
    norm = [float(np.mean([r.profit[i] / (r.sstar / N) for r in results])) for i in range(N)]
    return AllDeviatorsResult(profiles=profiles, values=values, final_profile=[dict(k) for k in profile],
                              final_gross_eff=eff, final_normalized_profit=norm)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_all_deviators.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add sim/all_deviators.py tests/test_all_deviators.py
git commit -m "feat: all-deviators iterated best response"
```

---

### Task 12: Baseline tuning on the locked grid with dev-val rechecks

**Files:**
- Create: `sim/tuning.py`, `scripts/tune_baselines.py`
- Test: `tests/test_tuning.py`

**Interfaces:**
- Consumes: Tasks 5 to 10.
- Produces:
  - `price_grid(cfg, f_values) -> list[tuple[float, float, float]]` (27 ordered triples).
  - `tuning_grid(rule_name, cfg, locked) -> list[dict]`: B1 has price triples only; B2 has price triples x tol x L; B3 has tol x L.
  - `rule_from_params(rule_name, params) -> Mechanism`.
  - `TuningScore(eff, gain, margin, namespace)`; `margin = min((eff - 0.90)/0.90, (0.30 - gain)/0.30)`.
  - `score_point(rule_name, params, cfg, locked, cache, family=D2, inner_override=None, recheck=False) -> TuningScore`: inner scoring searches twin and attack at the inner budget on the first `inner_seeds` dev-train seeds, selects the reference last, and scores gain and efficiency on those seeds (`namespace = "dev_train"`); the recheck searches at the full budget on all dev-train seeds, selects the reference there, and scores on the seeds of `locked["tuning"]["recheck_namespace"]` (`namespace = "dev_val"`).
  - `tune(rule_name, cfg, locked, cache, inner_override=None, grid_limit=None) -> TuningResult(best_params, scores, rechecked)`; the locked winner is the rechecked point with the highest dev-val margin.
  - `scripts/tune_baselines.py --calibration experiments/calibration.json --rule B2 --out experiments/tuned/tuned_B2.json [--quick]`. Tuning runs at `beta_headline` and the default rho.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_tuning.py
import json, subprocess, sys
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


def small_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers[6:10], alpha=0.05, budget=0.3)


QUICK = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16, "recheck_restarts": 1, "recheck_val_seeds": 2}


def test_inner_score_is_in_sample_and_recheck_scores_on_dev_val():
    lk = load_locked(); cfg = small_cfg(); cache = SeedCache()
    params = {"P1": 0.9, "P2": 1.0, "P3": 1.2, "tol": 0.12, "L": 10}   # tier 3 unaffordable for most jobs
    sc = score_point("B2", params, cfg, lk, cache, inner_override=QUICK)
    assert sc.namespace == "dev_train" and sc.margin <= 0.0 and sc.eff < 0.9
    rc = score_point("B2", params, cfg, lk, cache, inner_override=QUICK, recheck=True)
    assert rc.namespace == "dev_val" and rc.margin == pytest.approx(min((rc.eff - 0.90) / 0.90, (0.30 - rc.gain) / 0.30))


def test_quick_tune_terminates_and_picks_by_recheck():
    lk = load_locked(); cache = SeedCache()
    res = tune("B2", small_cfg(), lk, cache, inner_override=QUICK, grid_limit=3)
    assert res.best_params in [s["params"] for s in res.scores] and len(res.rechecked) == 1
    assert res.rechecked[0]["namespace"] == "dev_val" and res.best_params == res.rechecked[0]["params"]


def test_tune_script_quick(tmp_path):
    cal = {"S_hat": 1.0, "n_FB": 1.0, "m": 1.0, "market_key": "x", "T": 200, "seeds": [4000]}
    # a foreign calibration must be refused
    calp = tmp_path / "cal.json"; calp.write_text(json.dumps(cal))
    r = subprocess.run([sys.executable, "scripts/tune_baselines.py", "--calibration", str(calp), "--rule", "B3",
                        "--out", str(tmp_path / "t.json"), "--quick"], capture_output=True, text=True)
    assert r.returncode != 0 and "calibration" in (r.stderr + r.stdout)
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
from .reference import attack_search, evaluate_gain, reference_candidates, select_reference, twin_search
from .search import SearchSettings, settings_from_locked


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
    namespace: str


def _margin(eff: float, gain: float) -> float:
    return min((eff - 0.90) / 0.90, (0.30 - gain) / 0.30)


def _settings_and_seeds(locked: dict, override: dict | None, recheck: bool) -> tuple[SearchSettings, list[int], list[int] | None]:
    tg = dict(locked["tuning"]); tg.update(override or {})
    base = settings_from_locked(locked)
    tr = locked_seeds(locked, "dev_train")
    if recheck:
        evals = int(tg.get("recheck_evals", base.evals_per_restart)); restarts = int(tg.get("recheck_restarts", base.restarts))
        val = locked_seeds(locked, tg["recheck_namespace"])[: int(tg.get("recheck_val_seeds", 10**9))]
        return replace(base, evals_per_restart=evals, restarts=restarts), tr, val
    return replace(base, restarts=int(tg["inner_restarts"]), evals_per_restart=int(tg["inner_evals"])), tr[: int(tg["inner_seeds"])], None


def score_point(rule_name: str, params: dict, cfg: MarketConfig, locked: dict, cache: SeedCache,
                family: Family = D2, inner_override: dict | None = None, recheck: bool = False) -> TuningScore:
    """Inner scoring is in-sample on the inner dev-train seeds (spec 4.2); the recheck searches on all dev-train
    seeds at the full budget and scores on the recheck namespace (dev-val, spec 6)."""
    settings, train, val = _settings_and_seeds(locked, inner_override, recheck)
    focal = positions(cfg)["median"]
    cell = Cell(cfg=cfg, rule_factory=lambda: rule_from_params(rule_name, params), focal=focal, seeds=tuple(train), name=f"tune/{rule_name}")
    tw = twin_search(cell, family, cache, settings, seed=0)
    at = attack_search(cell, family, cache, settings, seed=1, twin=tw)
    ref = select_reference(cell, reference_candidates(cell, family, at, tw, [], tuple(locked["reference_order"])), cache)
    score_cell = cell if val is None else Cell(cfg=cfg, rule_factory=cell.rule_factory, focal=focal, seeds=tuple(val), name=cell.name + "/val")
    g = evaluate_gain(score_cell, family, at.best_knobs, ref.candidate, cache)
    eff, gain = float(g.eff_attack.mean()), float(g.gain.mean())
    return TuningScore(eff=eff, gain=gain, margin=_margin(eff, gain), namespace="dev_train" if val is None else str(locked["tuning"]["recheck_namespace"]))


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
        scores.append({"params": params, "eff": sc.eff, "gain": sc.gain, "margin": sc.margin, "namespace": sc.namespace})
    scores.sort(key=lambda s: -s["margin"])
    top = int((inner_override or {}).get("recheck_top", locked["tuning"]["recheck_top"]))
    rechecked = []
    for s in scores[:top]:
        sc = score_point(rule_name, s["params"], cfg, locked, cache, inner_override=inner_override, recheck=True)
        rechecked.append({"params": s["params"], "eff": sc.eff, "gain": sc.gain, "margin": sc.margin, "namespace": sc.namespace})
    rechecked.sort(key=lambda s: -s["margin"])
    return TuningResult(best_params=rechecked[0]["params"], scores=scores, rechecked=rechecked)
```

```python
# scripts/tune_baselines.py
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import cell_config, load_calibration
from sim.cell import SeedCache
from sim.locked import load_locked, market_config_from_locked
from sim.tuning import tune


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--rule", required=True, choices=["B1", "B2", "B3"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true", help="tiny budgets for a smoke run; never for the lock")
    args = ap.parse_args()
    lk = load_locked()
    cal = load_calibration(args.calibration)
    cfg = cell_config(market_config_from_locked(lk), cal, rho=float(lk["rho"]["default"]), beta=float(lk["beta_headline"]))
    override = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16, "recheck_restarts": 1, "recheck_val_seeds": 2} if args.quick else None
    res = tune(args.rule, cfg, lk, SeedCache(), inner_override=override, grid_limit=3 if args.quick else None)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"rule": args.rule, "quick": bool(args.quick), "best_params": res.best_params,
                                          "rechecked": res.rechecked, "scores": res.scores}, indent=2) + "\n")
    print(json.dumps(res.best_params))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_tuning.py -v`
Expected: PASS (5 tests). The script test exercises the calibration refusal only; a successful quick tune is covered by `test_quick_tune_terminates_and_picks_by_recheck`.

- [ ] **Step 5: Commit**

```bash
git add sim/tuning.py scripts/tune_baselines.py tests/test_tuning.py
git commit -m "feat: baseline tuning on the locked grid with in-sample inner scoring and dev-val rechecks"
```

---

### Task 13: One schedule for the manifest and the staged sweep, records, and the full-path benchmark

**Files:**
- Create: `sim/schedule.py`, `sim/manifest.py`, `sim/records.py`, `scripts/manifest.py`, `scripts/sweep.py`, `scripts/bench_sweep.py`
- Test: `tests/test_manifest.py`, `tests/test_sweep.py`

**Interfaces:**
- Consumes: every earlier task.
- Produces:
  - `sim/schedule.py`: `Budget(restarts, evals, n_train, n_val)`, `budget_from_locked(locked) -> Budget`, `SMOKE_BUDGET = Budget(1, 16, 1, 2)`, `search_runs(b) -> int`, `cell_runs(family_name, b) -> dict[str, int]` with keys `twin, twin_projection, attack, incumbents, attack_projection, reference, corners, evaluation` (every entry exact: the sweep always makes these runs), `h3_cell_runs(b)` (same as `cell_runs("D2", b)`: the H3 cell is a full cell over the wrapped family), `doubling_runs(b)`, `all_deviators_runs(locked, N, b)`, `tuning_point_runs(locked)`, `tuning_recheck_runs(b)`, `bank_runs(n_rules, b) -> int` (upper bound, labeled), `stage_runs(section, family_name, stage, b) -> int` (what one cell's stage must execute; used by the sweep to assert its own run counter).
  - `sim/manifest.py`: `CellSpec(section, rule, family, beta, rho, position, kind, runs, exact: bool, post_lock: bool, name, params_override: dict | None)`, `enumerate_manifest(locked, rules, budget=None) -> list[CellSpec]`, `totals(cells) -> dict[str, int]` by section plus `pre_lock`, `post_lock`, `pre_lock_exact`, `pre_lock_upper_bound`.
  - `sim/records.py`: `cfg_to_dict / cfg_from_dict`, `search_to_json(res) -> dict / search_from_json(d) -> SearchResult` (archive included, `per_seed_*` as lists), `candidate_from_record(family, d) -> Candidate`.
  - `scripts/manifest.py --ms-per-run 45 [--smoke]` prints the table and totals with core-hours.
  - `scripts/sweep.py --stage {search,bank,reference,evaluate,checks,all_deviators,all} --sections development,rho_sweep,no_ban,h3 --rules B1,B2,B3 --calibration FILE --tuned-dir DIR | --smoke --workers K [--limit N] --out DIR`. Stages read and write JSON under `DIR/<stage>/<cell>.json`; `evaluate` also writes `DIR/<section>.csv` with `ROW_FIELDS` and `DIR/headline.json`; `bank` writes `DIR/transfer.csv`; `checks` writes `DIR/checks.json`; `all_deviators` writes `DIR/all_deviators.json`. Without `--tuned-dir` the script refuses to run unless `--smoke` is given; a smoke run uses `DEFAULT_PARAMS`, `SMOKE_BUDGET`, and writes `DIR/SMOKE`.
  - `scripts/bench_sweep.py`: runs the `search` stage in-process for one smoke cell of each baseline, checks that the run counter equals the schedule, reports ms per run and the pre-lock manifest in core-hours at that rate, exits 1 above 20 core-hours.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_manifest.py
import subprocess, sys
import pytest
from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals
from sim.schedule import Budget, SMOKE_BUDGET, budget_from_locked, cell_runs, search_runs, doubling_runs, tuning_point_runs, tuning_recheck_runs, all_deviators_runs, bank_runs


def test_schedule_arithmetic_is_explicit():
    b = budget_from_locked(load_locked())
    assert b == Budget(restarts=5, evals=300, n_train=5, n_val=20) and search_runs(b) == 7500
    d1, d2 = cell_runs("D1", b), cell_runs("D2", b)
    assert d1 == {"twin": 7500, "twin_projection": 5, "attack": 7500, "incumbents": 10, "attack_projection": 5,
                  "reference": 5, "corners": 32 * 5, "evaluation": 4 * 20}
    assert sum(d1.values()) == 15265 and sum(d2.values()) == 15265 - 160 + 640
    assert doubling_runs(b) == 2 * (5 * 150 * 5 + 5) + 2 * 5
    lk = load_locked()
    assert tuning_point_runs(lk) == 2 * (1 * 100 * 3) + 3 + 6 + 3 + 3 + 4 * 3
    assert tuning_recheck_runs(b) == 2 * 7500 + 5 + 10 + 5 + 5 + 4 * 20
    assert all_deviators_runs(lk, 10, b) == 3 * 10 * (100 + 2) * 3 + 3
    assert bank_runs(3, b) == 24 * (24 * 5 * 2 + 85) + 24 * ((48 + 128) * 5 + (48 + 64) * 5 + 85)


def test_manifest_totals_follow_the_schedule():
    lk = load_locked()
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    t = totals(cells)
    b = budget_from_locked(lk)
    c1, c2 = sum(cell_runs("D1", b).values()), sum(cell_runs("D2", b).values())
    assert t["development"] == 24 * c1 + 24 * c2                   # 3 rules x 2 families x (5 + 3) cells
    assert t["rho_sweep"] == 2 * 3 * c2 and t["no_ban"] == 2 * c2 and t["h3"] == 3 * c2
    assert t["controls"] == 3 * 2 * doubling_runs(b)
    assert t["all_deviators"] == 3 * all_deviators_runs(lk, 10, b)
    assert t["tuning"] == (27 + 243 + 9) * tuning_point_runs(lk) + 9 * tuning_recheck_runs(b)
    assert t["bank"] == bank_runs(3, b) and t["bank_post_lock"] == bank_runs(4, b) - bank_runs(3, b)
    assert t["ablation"] == 3 * c1 + 3 * c2
    assert t["pre_lock"] == t["development"] + t["rho_sweep"] + t["no_ban"] + t["h3"] + t["controls"] + t["all_deviators"] + t["tuning"] + t["bank"]
    assert t["pre_lock"] * 45.0 / 3.6e6 < 20.0                     # the gate at 45 ms per run
    assert all(c.post_lock for c in cells if c.section in ("bank_post_lock", "ablation"))
    assert all(not c.exact for c in cells if c.section.startswith("bank"))
    names = [c.name for c in cells]
    assert len(names) == len(set(names))


def test_manifest_script_prints_totals():
    out = subprocess.run([sys.executable, "scripts/manifest.py", "--ms-per-run", "45"], check=True, capture_output=True, text=True).stdout
    assert "pre_lock" in out and "core-hours" in out and "upper bound" in out
```

```python
# tests/test_sweep.py
import json, subprocess, sys
from pathlib import Path
import pytest
from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked
from sim.manifest import enumerate_manifest
from sim.reference import ROW_FIELDS
from sim.schedule import SMOKE_BUDGET, stage_runs


@pytest.fixture(scope="module")
def cal_path(tmp_path_factory):
    p = tmp_path_factory.mktemp("cal") / "cal.json"
    save_calibration(calibrate(market_config_from_locked(load_locked()), seeds=[4000]), p)
    return p


def run_sweep(cal_path, out, *extra):
    return subprocess.run([sys.executable, "scripts/sweep.py", "--calibration", str(cal_path), "--out", str(out), *extra],
                          capture_output=True, text=True)


def test_sweep_refuses_untuned_run_without_smoke_flag(cal_path, tmp_path):
    r = run_sweep(cal_path, tmp_path / "res", "--stage", "search", "--rules", "B1", "--limit", "1")
    assert r.returncode != 0 and "tuned" in (r.stderr + r.stdout)


def test_smoke_sweep_runs_every_stage_and_counts_runs(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development,h3", "--rules", "B1,B2", "--limit", "2", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    assert (out / "SMOKE").exists()
    search = {p.stem: json.loads(p.read_text()) for p in (out / "search").glob("*.json")}
    assert len(search) >= 2
    for rec in search.values():
        assert rec["runs"] == stage_runs(rec["spec"]["section"], rec["spec"]["family"], "search", SMOKE_BUDGET)
        assert rec["attack"]["best_f"] >= rec["attack"]["incumbent_scores"]["honest_point"] - 1e-12
    assert (out / "transfer.csv").exists() and (out / "headline.json").exists() and (out / "checks.json").exists()
    rows = (out / "development.csv").read_text().splitlines()
    assert rows[0] == "cell,section,rule,family,beta,rho,position,smoke," + ",".join(ROW_FIELDS)
    assert len(rows) >= 1 + 2       # two dev-val seeds for at least one development cell
    ref = {p.stem: json.loads(p.read_text()) for p in (out / "reference").glob("*.json")}
    assert all(rec["candidate"]["name"] in rec["scores"] for rec in ref.values())
    assert any(p.stem.startswith("B1_D2+H3") or "H3" in p.stem for p in (out / "search").glob("*.json"))
    assert (out / "all_deviators.json").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_manifest.py tests/test_sweep.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.schedule'`

- [ ] **Step 3: Write the implementation**

```python
# sim/schedule.py
"""The one place that says how many runs a cell needs. manifest.py sums it; sweep.py executes it
and asserts its run counter against it (spec 5.3: the manifest is authoritative)."""
from __future__ import annotations

from dataclasses import dataclass

from .policies.families import FAMILIES

N_CORNERS = {"D1": 32, "D2": 128, "D2+H3": 128}


@dataclass(frozen=True)
class Budget:
    restarts: int
    evals: int
    n_train: int
    n_val: int


SMOKE_BUDGET = Budget(restarts=1, evals=16, n_train=1, n_val=2)


def budget_from_locked(locked: dict) -> Budget:
    s = locked["search"]
    return Budget(restarts=int(s["restarts"]), evals=int(s["evals_per_restart"]),
                  n_train=len(locked["seeds"]["dev_train"]), n_val=len(locked["seeds"]["dev_val"]))


def search_runs(b: Budget) -> int:
    return b.restarts * b.evals * b.n_train


def cell_runs(family_name: str, b: Budget) -> dict[str, int]:
    """Exact runs of one full cell: twin search and its projection, attack search with two incumbents and its
    projection, reference selection (honest-max is the only candidate without a known value), corner controls,
    and the dev-val evaluation of attack, clipped attack, reference, and honest-max."""
    s = search_runs(b)
    return {"twin": s, "twin_projection": b.n_train, "attack": s, "incumbents": 2 * b.n_train, "attack_projection": b.n_train,
            "reference": b.n_train, "corners": N_CORNERS[family_name] * b.n_train, "evaluation": 4 * b.n_val}


def h3_cell_runs(b: Budget) -> dict[str, int]:
    return cell_runs("D2+H3", b)


def doubling_runs(b: Budget) -> int:
    """Two fixed-clip searches at half the budget, each with a projection, plus honest-max in two reference selections."""
    half = b.restarts * (b.evals // 2) * b.n_train
    return 2 * (half + b.n_train) + 2 * b.n_train


def all_deviators_runs(locked: dict, N: int, b: Budget) -> int:
    ad = locked["all_deviators"]
    per = ad["restarts"] * ad["evals"] + 2        # search, projection, current-value evaluation
    return ad["sweeps"] * N * per * ad["seeds"] + ad["seeds"]


def tuning_point_runs(locked: dict) -> int:
    tg = locked["tuning"]
    s = tg["inner_restarts"] * tg["inner_evals"] * tg["inner_seeds"]; n = tg["inner_seeds"]
    return 2 * s + n + 2 * n + n + n + 4 * n     # twin, attack, twin projection, incumbents, attack projection, honest, in-sample evaluation


def tuning_recheck_runs(b: Budget) -> int:
    s = search_runs(b); n = b.n_train
    return 2 * s + n + 2 * n + n + n + 4 * b.n_val


def tuning_grid_sizes(locked: dict) -> dict[str, int]:
    tg = locked["tuning"]
    return {"B1": 27, "B2": 27 * len(tg["tol"]) * len(tg["L"]), "B3": len(tg["tol"]) * len(tg["L"])}


def bank_runs(n_rules: int, b: Budget) -> int:
    """Upper bound: every compatible member evaluated as an attack, every projected member evaluated as a
    reference candidate, and one re-finalization (projection plus evaluation) per cell."""
    cells_per_family = n_rules * 8
    members = cells_per_family           # best-found attacks of one family
    d1 = cells_per_family * (members * b.n_train * 2 + b.n_train + 4 * b.n_val)
    d2 = cells_per_family * ((2 * members + 128) * b.n_train + (2 * members + 64) * b.n_train + b.n_train + 4 * b.n_val)
    return d1 + d2


STAGE_KEYS = {"search": ("twin", "twin_projection", "attack", "incumbents", "attack_projection", "corners"),
              "reference": ("reference",), "evaluate": ("evaluation",)}


def stage_runs(section: str, family_name: str, stage: str, b: Budget) -> int:
    runs = cell_runs(family_name, b)
    return sum(runs[k] for k in STAGE_KEYS[stage])
```

```python
# sim/manifest.py
from __future__ import annotations

from dataclasses import dataclass, asdict

from .schedule import (Budget, all_deviators_runs, bank_runs, budget_from_locked, cell_runs, doubling_runs,
                       tuning_grid_sizes, tuning_point_runs, tuning_recheck_runs)


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
    exact: bool
    post_lock: bool
    name: str
    params_override: dict | None = None


def cell_name(section: str, rule: str, family: str, beta: float, rho: float, position: str) -> str:
    return f"{rule}_{family}_beta{beta}_rho{rho}_{position}_{section}"


def enumerate_manifest(locked: dict, rules: list[str], budget: Budget | None = None) -> list[CellSpec]:
    b = budget or budget_from_locked(locked)
    betas = [float(x) for x in locked["beta_grid"]]; bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"])
    cells: list[CellSpec] = []
    for rule in rules:
        for fam in ("D1", "D2"):
            for beta in betas:
                for pos in (locked["positions"] if beta == bh else ["median"]):
                    cells.append(CellSpec("development", rule, fam, beta, rho0, pos, "full_cell", sum(cell_runs(fam, b).values()), True, False,
                                          cell_name("development", rule, fam, beta, rho0, pos)))
        for rho in [float(r) for r in locked["rho"]["sweep"] if float(r) != rho0]:
            cells.append(CellSpec("rho_sweep", rule, "D2", bh, rho, "median", "full_cell", sum(cell_runs("D2", b).values()), True, False,
                                  cell_name("rho_sweep", rule, "D2", bh, rho, "median")))
        if rule in locked["no_ban_rules"]:
            cells.append(CellSpec("no_ban", rule, "D2", bh, rho0, "median", "full_cell", sum(cell_runs("D2", b).values()), True, False,
                                  cell_name("no_ban", rule, "D2", bh, rho0, "median"), params_override={"L": 0}))
        cells.append(CellSpec("h3", rule, "D2+H3", bh, rho0, "median", "full_cell", sum(cell_runs("D2+H3", b).values()), True, False,
                              cell_name("h3", rule, "D2+H3", bh, rho0, "median")))
        for fam, pos in locked["doubling_cells"]:
            cells.append(CellSpec("controls", rule, fam, bh, rho0, pos, "doubling_check", doubling_runs(b), True, False,
                                  cell_name("controls", rule, fam, bh, rho0, pos)))
        cells.append(CellSpec("all_deviators", rule, "D2", bh, rho0, "all", "iterated_br",
                              all_deviators_runs(locked, int(locked["market"]["N"]), b), True, False,
                              cell_name("all_deviators", rule, "D2", bh, rho0, "all")))
        grid = tuning_grid_sizes(locked)[rule]
        cells.append(CellSpec("tuning", rule, "D2", bh, rho0, "median", "grid_and_recheck",
                              grid * tuning_point_runs(locked) + int(locked["tuning"]["recheck_top"]) * tuning_recheck_runs(b), True, False,
                              cell_name("tuning", rule, "D2", bh, rho0, "median")))
    n_rules = len(rules)
    cells.append(CellSpec("bank", "all", "D1+D2", bh, rho0, "all", "bank_pass", bank_runs(n_rules, b), False, False, "bank_pre_lock"))
    cells.append(CellSpec("bank_post_lock", "proposed", "D1+D2", bh, rho0, "all", "bank_pass",
                          bank_runs(n_rules + 1, b) - bank_runs(n_rules, b), False, True, "bank_post_lock"))
    for fam in ("D1", "D2"):
        for pos in locked["positions"]:
            cells.append(CellSpec("ablation", "proposed", fam, bh, rho0, pos, "full_cell", sum(cell_runs(fam, b).values()), True, True,
                                  cell_name("ablation", "proposed", fam, bh, rho0, pos)))
    return cells


def totals(cells: list[CellSpec]) -> dict[str, int]:
    t: dict[str, int] = {}
    for c in cells:
        t[c.section] = t.get(c.section, 0) + c.runs
        key = "post_lock" if c.post_lock else "pre_lock"
        t[key] = t.get(key, 0) + c.runs
        if not c.post_lock:
            k2 = "pre_lock_exact" if c.exact else "pre_lock_upper_bound"
            t[k2] = t.get(k2, 0) + c.runs
    return t


def rows(cells: list[CellSpec]) -> list[dict]:
    return [asdict(c) for c in cells]
```

```python
# sim/records.py
"""JSON records for the sweep stages: configs, search results with archives, candidates."""
from __future__ import annotations

import numpy as np

from .cell import Abstain
from .config import MarketConfig, ProviderParams
from .policies.families import Family
from .policies.honest import HonestMax
from .reference import Candidate
from .search import ArchiveEntry, SearchResult


def cfg_to_dict(cfg: MarketConfig) -> dict:
    return {"N": cfg.N, "J": cfg.J, "T": cfg.T, "sigma": cfg.sigma, "e": cfg.e, "v_min": cfg.v_min, "v_max": cfg.v_max,
            "providers": [[p.q_max, p.a, p.b, p.k] for p in cfg.providers], "alpha": cfg.alpha, "budget": cfg.budget}


def cfg_from_dict(d: dict) -> MarketConfig:
    return MarketConfig(N=int(d["N"]), J=int(d["J"]), T=int(d["T"]), sigma=float(d["sigma"]), e=float(d["e"]), v_min=float(d["v_min"]),
                        v_max=float(d["v_max"]), providers=tuple(ProviderParams(float(q), float(a), float(b), int(k)) for q, a, b, k in d["providers"]),
                        alpha=float(d["alpha"]), budget=float(d["budget"]))


def search_to_json(res: SearchResult) -> dict:
    return {"best_x": [float(v) for v in np.asarray(res.best_x)], "best_knobs": res.best_knobs, "best_f": res.best_f, "best_source": res.best_source,
            "restart_bests": [float(v) for v in res.restart_bests], "evals": res.evals, "incumbent_scores": res.incumbent_scores,
            "projection_f": res.projection_f, "replaced_by_projection": res.replaced_by_projection,
            "archive": [{"knobs": e.knobs, "f": e.f, "per_seed_profit": [float(v) for v in e.per_seed_profit],
                         "per_seed_normalized": [float(v) for v in e.per_seed_normalized], "inflated": bool(e.inflated), "source": e.source}
                        for e in res.archive.values()]}


def search_from_json(d: dict) -> SearchResult:
    from .policies.families import knob_key
    archive = {knob_key(e["knobs"]): ArchiveEntry(knobs=e["knobs"], f=float(e["f"]), per_seed_profit=np.array(e["per_seed_profit"]),
                                                  per_seed_normalized=np.array(e["per_seed_normalized"]), inflated=bool(e["inflated"]), source=e["source"])
               for e in d["archive"]}
    return SearchResult(best_x=np.array(d["best_x"]), best_knobs=d["best_knobs"], best_f=float(d["best_f"]), best_source=d["best_source"],
                        restart_bests=list(d["restart_bests"]), evals=int(d["evals"]), trace=[], incumbent_scores=dict(d["incumbent_scores"]),
                        projection_f=float(d["projection_f"]), replaced_by_projection=bool(d["replaced_by_projection"]), archive=archive)


def candidate_to_json(c: Candidate) -> dict:
    return {"name": c.name, "knobs": c.knobs}


def candidate_from_record(family: Family, d: dict) -> Candidate:
    if d["knobs"] is None:
        return Candidate(d["name"], Abstain if d["name"] == "abstain" else HonestMax, None)
    knobs = dict(d["knobs"])
    return Candidate(d["name"], lambda: family.make(knobs), knobs)
```

```python
# scripts/manifest.py
from __future__ import annotations

import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals
from sim.schedule import SMOKE_BUDGET


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--ms-per-run", type=float, default=45.0)
    ap.add_argument("--smoke", action="store_true", help="counts at the smoke budget")
    args = ap.parse_args()
    cells = enumerate_manifest(load_locked(), args.rules.split(","), budget=SMOKE_BUDGET if args.smoke else None)
    for c in cells:
        tag = "exact" if c.exact else "upper bound"
        print(f"{c.name:60s} {c.runs:>10,d}  {tag}{'  post-lock' if c.post_lock else ''}")
    t = totals(cells)
    for k in sorted(t):
        hours = t[k] * args.ms_per_run / 3.6e6
        print(f"{k:22s} {t[k]:>12,d} runs  {hours:8.1f} core-hours at {args.ms_per_run:.0f} ms/run")


if __name__ == "__main__":
    main()
```

```python
# scripts/sweep.py
from __future__ import annotations

import argparse, csv, json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.all_deviators import iterated_best_response
from sim.bank import Bank
from sim.calibrate import cell_config, load_calibration
from sim.cell import Cell, SeedCache
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds
from sim.manifest import CellSpec, enumerate_manifest
from sim.policies.families import D2, FAMILIES
from sim.policies.identity import h3_family
from sim.positions import headline_position, positions
from sim.records import candidate_from_record, candidate_to_json, cfg_from_dict, cfg_to_dict, search_from_json, search_to_json
from sim.reference import ROW_FIELDS, attack_search, evaluate_gain, reference_candidates, seed_rows, select_reference, twin_search
from sim.schedule import SMOKE_BUDGET, Budget, budget_from_locked, stage_runs
from sim.search import Objective, SearchSettings, corner_controls, settings_from_locked
from sim.search_checks import doubling_check, restart_spread, twin_vs_honest
from sim.tuning import rule_from_params

DEFAULT_PARAMS = {"B1": {"P1": 0.25, "P2": 0.40, "P3": 0.55},
                  "B2": {"P1": 0.25, "P2": 0.40, "P3": 0.55, "tol": 0.12, "L": 10},
                  "B3": {"tol": 0.12, "L": 10}}
STAGES = ("search", "bank", "reference", "evaluate", "checks", "all_deviators")
ALL_FAMILIES = dict(FAMILIES, **{"D2+H3": h3_family(D2)})
META_FIELDS = ["cell", "section", "rule", "family", "beta", "rho", "position", "smoke"]


def family_of(name: str):
    return ALL_FAMILIES[name]


def load_params(rule: str, tuned_dir: Path | None, smoke: bool) -> dict:
    if tuned_dir is None:
        if not smoke:
            raise SystemExit("refusing to run without tuned parameters: pass --tuned-dir, or --smoke for a smoke run")
        return dict(DEFAULT_PARAMS[rule])
    p = tuned_dir / f"tuned_{rule}.json"
    if not p.exists():
        raise SystemExit(f"tuned parameters for {rule} not found at {p}")
    d = json.loads(p.read_text())
    if d.get("quick"):
        raise SystemExit(f"{p} is a quick tuning result and cannot be used for a real run")
    return dict(d["best_params"])


def settings_for(locked: dict, budget: Budget) -> SearchSettings:
    s = settings_from_locked(locked)
    return SearchSettings(popsize=s.popsize, sigma0=s.sigma0, restarts=budget.restarts, evals_per_restart=budget.evals,
                          reeval_every=s.reeval_every, near_corner=s.near_corner, sobol_seed=s.sobol_seed)


def job_for(spec: CellSpec, locked: dict, cal, base, params: dict, budget: Budget, smoke: bool) -> dict:
    cfg = cell_config(base, cal, rho=spec.rho, beta=spec.beta)
    p = dict(params); p.update(spec.params_override or {})
    return {"spec": {"name": spec.name, "section": spec.section, "rule": spec.rule, "family": spec.family, "beta": spec.beta,
                     "rho": spec.rho, "position": spec.position}, "cfg": cfg_to_dict(cfg), "params": p, "locked": locked,
            "budget": [budget.restarts, budget.evals, budget.n_train, budget.n_val], "smoke": smoke}


def make_cell(job: dict, seeds: tuple[int, ...], suffix: str = "") -> Cell:
    cfg = cfg_from_dict(job["cfg"]); params = job["params"]; rule = job["spec"]["rule"]
    return Cell(cfg=cfg, rule_factory=lambda: rule_from_params(rule, params), focal=positions(cfg)[job["spec"]["position"]],
                seeds=seeds, name=job["spec"]["name"] + suffix)


def train_val(job: dict) -> tuple[tuple[int, ...], tuple[int, ...], Budget]:
    b = Budget(*job["budget"]); lk = job["locked"]
    return tuple(locked_seeds(lk, "dev_train")[: b.n_train]), tuple(locked_seeds(lk, "dev_val")[: b.n_val]), b


def meta_of(job: dict) -> dict:
    s = job["spec"]
    return {"cell": s["name"], "section": s["section"], "rule": s["rule"], "family": s["family"], "beta": s["beta"], "rho": s["rho"],
            "position": s["position"], "smoke": bool(job["smoke"])}


def stage_search(job: dict) -> dict:
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    settings = settings_for(job["locked"], b)
    tw = twin_search(cell, fam, cache, settings, seed=0)
    at = attack_search(cell, fam, cache, settings, seed=1, twin=tw)
    corners = [(k, f) for k, f in corner_controls(Objective(cell, fam, cache), fam)]
    expected = stage_runs(job["spec"]["section"], job["spec"]["family"], "search", b)
    if cache.runs != expected:
        raise AssertionError(f"{cell.name}: search stage ran {cache.runs} episodes, schedule says {expected}")
    return {"spec": job["spec"], "cfg": job["cfg"], "params": job["params"], "smoke": job["smoke"], "runs": cache.runs,
            "twin": search_to_json(tw), "attack": search_to_json(at), "corners": [{"knobs": k, "f": f} for k, f in corners],
            "restart_spread": restart_spread(at, tw), "twin_vs_honest": twin_vs_honest(tw, at.incumbent_scores["honest_point"]).__dict__}


def stage_bank(job: dict, rec: dict, bank_json: str) -> dict:
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    bank = Bank.from_json(bank_json)
    attack = search_from_json(rec["attack"])
    bp = bank.bank_pass(cell, fam, cache, incumbent_f=attack.best_f)
    out = {"spec": job["spec"], "transfer": Bank.transfer_rows(cell.name, attack.best_f, bp), "ranked_top": bp.ranked[:10], "runs": cache.runs}
    if bp.improved:
        obj = Objective(cell, fam, cache); obj.archive.update(attack.archive)
        f = obj.eval_knobs(bp.best_knobs, source=f"bank:{bp.best_origin}")
        proj = fam.project(bp.best_knobs); pf = obj.eval_knobs(proj, source="projection")
        best, best_f, src = (proj, pf, "projection") if pf > f else (bp.best_knobs, f, f"bank:{bp.best_origin}")
        attack.best_knobs, attack.best_f, attack.best_source, attack.archive = best, best_f, src, obj.archive
        attack.projection_f, attack.replaced_by_projection = pf, pf > f
    out["attack"] = search_to_json(attack)
    out["projected_members"] = bank.projected_members_for(fam.name) if fam.name in FAMILIES else []
    return out


def stage_reference(job: dict, rec: dict, bank_rec: dict | None) -> dict:
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); twin = search_from_json(rec["twin"])
    members = bank_rec["projected_members"] if bank_rec else []
    cands = reference_candidates(cell, fam, attack, twin, members, tuple(job["locked"]["reference_order"]))
    ref = select_reference(cell, cands, cache)
    return {"spec": job["spec"], "candidate": candidate_to_json(ref.candidate), "scores": ref.scores, "runs": cache.runs,
            "attack_knobs": attack.best_knobs, "attack_f": attack.best_f, "attack_source": attack.best_source,
            "gain_train": attack.best_f - ref.scores[ref.candidate.name]}


def stage_evaluate(job: dict, ref_rec: dict) -> dict:
    _, val, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, val, suffix="/val")
    cand = candidate_from_record(fam, ref_rec["candidate"])
    g = evaluate_gain(cell, fam, ref_rec["attack_knobs"], cand, cache)
    expected = stage_runs(job["spec"]["section"], job["spec"]["family"], "evaluate", b)
    if cache.runs != expected:
        raise AssertionError(f"{cell.name}: evaluate stage ran {cache.runs} episodes, schedule says {expected}")
    return {"spec": job["spec"], "rows": seed_rows(cell, g, meta_of(job)), "runs": cache.runs}


def stage_checks(job: dict, rec: dict, bank_rec: dict | None) -> dict:
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    attack = search_from_json(rec["attack"]); twin = search_from_json(rec["twin"])
    members = bank_rec["projected_members"] if bank_rec else []
    dc = doubling_check(cell, fam, cache, settings_for(job["locked"], b), seed=0, base_attack=attack, base_twin=twin,
                        bank_members=members, order=tuple(job["locked"]["reference_order"]))
    return {"spec": job["spec"], "doubling": dc.__dict__, "restart_spread": rec["restart_spread"], "twin_vs_honest": rec["twin_vs_honest"], "runs": cache.runs}


def stage_all_deviators(job: dict) -> dict:
    train, _, b = train_val(job)
    lk = job["locked"]; ad = lk["all_deviators"]; cfg = cfg_from_dict(job["cfg"]); params = job["params"]; rule = job["spec"]["rule"]
    s = settings_from_locked(lk)
    settings = SearchSettings(popsize=s.popsize, sigma0=s.sigma0, restarts=int(ad["restarts"]), evals_per_restart=min(int(ad["evals"]), b.evals),
                              reeval_every=s.reeval_every, near_corner=s.near_corner, sobol_seed=s.sobol_seed)
    seeds = tuple(locked_seeds(lk, "dev_train")[: min(int(ad["seeds"]), b.n_train)])
    cache = SeedCache()
    res = iterated_best_response(cfg, lambda: rule_from_params(rule, params), D2, cache, settings, seeds, sweeps=int(ad["sweeps"]))
    return {"spec": job["spec"], "profiles": res.profiles, "values": res.values, "final_profile": res.final_profile,
            "final_gross_eff": res.final_gross_eff, "final_normalized_profit": res.final_normalized_profit, "runs": cache.runs}


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float) + "\n")


def read_dir(path: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(path.glob("*.json"))} if path.exists() else {}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES + ("all",))
    ap.add_argument("--sections", default="development,rho_sweep,no_ban,h3")
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", default=None)
    ap.add_argument("--smoke", action="store_true", help="DEFAULT_PARAMS and the smoke budget; output marked SMOKE")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None, help="at most this many cells per section (search stage)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lk = load_locked(); cal = load_calibration(args.calibration); base = market_config_from_locked(lk)
    budget = SMOKE_BUDGET if args.smoke else budget_from_locked(lk)
    rules = args.rules.split(","); sections = args.sections.split(",")
    tuned = Path(args.tuned_dir) if args.tuned_dir else None
    params = {r: load_params(r, tuned, args.smoke) for r in rules}
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    if args.smoke:
        (out / "SMOKE").write_text("smoke run: DEFAULT_PARAMS and SMOKE_BUDGET; not a result\n")
    manifest = enumerate_manifest(lk, rules, budget=budget)
    stages = STAGES if args.stage == "all" else (args.stage,)
    pool = ProcessPoolExecutor(max_workers=args.workers)
    for stage in stages:
        if stage == "search":
            jobs = []
            for sec in sections:
                specs = [c for c in manifest if c.section == sec and c.kind == "full_cell" and c.rule in rules]
                jobs += [job_for(c, lk, cal, base, params[c.rule], budget, args.smoke) for c in specs[: args.limit]]
            for rec in pool.map(stage_search, jobs):
                write_json(out / "search" / f"{rec['spec']['name']}.json", rec)
        search = read_dir(out / "search")
        jobs = {name: job_for(next(c for c in manifest if c.name == name), lk, cal, base, params[rec["spec"]["rule"]], budget, args.smoke)
                for name, rec in search.items()}
        if stage == "bank":
            bank = Bank()
            for name, rec in search.items():
                if rec["spec"]["section"] == "development":
                    bank.add(rec["spec"]["family"], rec["attack"]["best_knobs"], origin=name)
            bj = bank.to_json(); (out / "bank.json").write_text(bj)
            targets = [n for n, r in search.items() if r["spec"]["family"] in FAMILIES]
            for rec in pool.map(stage_bank, [jobs[n] for n in targets], [search[n] for n in targets], [bj] * len(targets)):
                write_json(out / "bank" / f"{rec['spec']['name']}.json", rec)
            trows = [json.loads((out / "bank" / f"{n}.json").read_text())["transfer"] for n in targets]
            with open(out / "transfer.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["cell", "incumbent", "best_bank", "best_origin", "improved"]); w.writeheader(); w.writerows(trows)
        bank_recs = read_dir(out / "bank")
        if stage == "reference":
            names = list(search)
            for rec in pool.map(stage_reference, [jobs[n] for n in names], [search[n] for n in names], [bank_recs.get(n) for n in names]):
                write_json(out / "reference" / f"{rec['spec']['name']}.json", rec)
        refs = read_dir(out / "reference")
        if stage == "evaluate":
            names = list(refs)
            by_section: dict[str, list] = {}
            for rec in pool.map(stage_evaluate, [jobs[n] for n in names], [refs[n] for n in names]):
                write_json(out / "evaluate" / f"{rec['spec']['name']}.json", rec)
                by_section.setdefault(rec["spec"]["section"], []).extend(rec["rows"])
            for sec, rws in by_section.items():
                with open(out / f"{sec}.csv", "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=META_FIELDS + ROW_FIELDS); w.writeheader(); w.writerows(rws)
            headline = {}
            for name, r in refs.items():
                s = r["spec"]
                if s["section"] == "development" and float(s["beta"]) == float(lk["beta_headline"]):
                    headline.setdefault(f"{s['rule']}/{s['family']}", {})[s["position"]] = float(r["gain_train"])
            write_json(out / "headline.json", {k: {"gain_train": v, "headline": headline_position(v)} for k, v in headline.items()})
        if stage == "checks":
            cells = [c for c in manifest if c.section == "controls" and c.rule in rules]
            names, recs = [], []
            for c in cells:
                n = next((n for n, r in search.items() if r["spec"]["section"] == "development" and r["spec"]["rule"] == c.rule
                          and r["spec"]["family"] == c.family and r["spec"]["position"] == c.position
                          and float(r["spec"]["beta"]) == c.beta and float(r["spec"]["rho"]) == c.rho), None)
                if n is not None:
                    names.append(n)
            results = list(pool.map(stage_checks, [jobs[n] for n in names], [search[n] for n in names], [bank_recs.get(n) for n in names]))
            write_json(out / "checks.json", results)
        if stage == "all_deviators":
            specs = [c for c in manifest if c.section == "all_deviators" and c.rule in rules]
            adj = [job_for(c, lk, cal, base, params[c.rule], budget, args.smoke) for c in specs]
            write_json(out / "all_deviators.json", list(pool.map(stage_all_deviators, adj)))
    pool.shutdown()
    print(f"done: stages {stages} in {out}")


if __name__ == "__main__":
    main()
```

```python
# scripts/bench_sweep.py
"""The spec 5.3 gate: time the full search path through sweep.py for one smoke cell per baseline
and extrapolate the pre-lock manifest. Exits 1 above 20 core-hours."""
from __future__ import annotations

import argparse, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bench import cpu_model
from scripts.sweep import DEFAULT_PARAMS, job_for, stage_search
from sim.calibrate import calibrate
from sim.locked import load_locked, market_config_from_locked, seeds
from sim.manifest import enumerate_manifest, totals
from sim.schedule import SMOKE_BUDGET

GATE_HOURS = 20.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    args = ap.parse_args()
    lk = load_locked(); base = market_config_from_locked(lk)
    cal = calibrate(base, seeds(lk, "calibration")[:2])
    rules = args.rules.split(",")
    manifest = enumerate_manifest(lk, rules, budget=SMOKE_BUDGET)
    runs, secs = 0, 0.0
    for r in rules:
        spec = next(c for c in manifest if c.section == "development" and c.rule == r and c.family == "D2" and c.position == "median"
                    and c.beta == float(lk["beta_headline"]))
        job = job_for(spec, lk, cal, base, DEFAULT_PARAMS[r], SMOKE_BUDGET, smoke=True)
        t0 = time.perf_counter(); rec = stage_search(job); secs += time.perf_counter() - t0
        runs += rec["runs"]      # stage_search asserts rec["runs"] == schedule
    ms = 1000.0 * secs / runs
    pre = totals(enumerate_manifest(lk, rules))["pre_lock"]
    hours = pre * ms / 3.6e6
    print(f"full search path: {runs} runs in {secs:.1f} s = {ms:.1f} ms/run on {cpu_model()}; pre-lock manifest {pre:,} runs = {hours:.1f} core-hours (gate {GATE_HOURS})")
    sys.exit(0 if hours <= GATE_HOURS else 1)


if __name__ == "__main__":
    main()
```

Also add an empty `scripts/__init__.py` so `scripts.bench` and `scripts.sweep` import from `bench_sweep.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_manifest.py tests/test_sweep.py -v && uv run python scripts/bench_sweep.py`
Expected: PASS (5 tests); the smoke sweep test runs two development cells and one H3 cell per rule for B1 and B2 at the smoke budget (about 200 runs per cell at T = 200) and every stage, under two minutes. `bench_sweep.py` prints the ms per run and the extrapolated core-hours, under 20.

- [ ] **Step 5: Commit**

```bash
git add sim/schedule.py sim/manifest.py sim/records.py scripts/__init__.py scripts/manifest.py scripts/sweep.py scripts/bench_sweep.py tests/test_manifest.py tests/test_sweep.py
git commit -m "feat: one schedule for the manifest and the staged sweep (search, bank, reference, evaluate, checks, all-deviators); full-path benchmark"
```

---

### Task 14: Spec implementation note, rulings, `families.md`, and README status

**Files:**
- Create: `experiments/families.md`
- Modify: `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (section 14), `README.md` (Status)

- [ ] **Step 1: Write `experiments/families.md`**

```markdown
# Development families D1 and D2 (executable definitions)

Code: `sim/policies/fixed_cheat.py` (D1), `sim/policies/adaptive.py` (D2),
`sim/policies/families.py` (knobs, bounds, transforms, projection, corners,
registered starts), `sim/policies/identity.py` (H3 wrapper).

D1 fixed cheat. Knobs u, m in [0, 1], s in [0, 0.3], w in [0, 2], clip in
{0, 1}. Effort q = q_max (1 - u); claim c = min(1, max(0, q + m - s)); with
clip = 1 the claim is min(c, q); bid = (1 + w)(a + b q). Never abstains or
exits.

D2 adaptive cheat. Knobs u0, m0 in [0, 1], s in [0, 0.3], d in [0, 1], r in
[0, 0.2], w in [0, 2], clip in {0, 1}. State m_t with m_1 = m0; effort
q = q_max (1 - u0); claim as D1 with m_t; after a round with a failed audit
m_{t+1} = m_t (1 - d), otherwise m_{t+1} = min(m0, m_t + r m0); unchanged
during a ban. D2 contains D1 at d = r = 0 (`embed_d1_in_d2`).

Transform. Search coordinate x in R^dim; knob = lo + (hi - lo) sigmoid(x);
clip = 1 iff sigmoid(x_clip) >= 0.5. Exact points (corners, the honest
point, registered incumbents) are evaluated from knob dictionaries, never
through the inverse transform.

Registered starts (spec 5.3): near-honest (logit 0.02 on every knob, clip at
logit 0.98); near-full-cheat (logit 0.98 on every knob, s and clip at logit
0.02); three scrambled Sobol points with seed `search.sobol_seed` from
`locked.yaml`. Honest point: every knob at its lower bound, clip = 1; it
reproduces honest-max (`tests/test_families.py`).

Projection: clip set to 1. Twins are the families with clip fixed at 1.
Containment tests: `tests/test_families.py`, `tests/test_reference.py`.

H3: `IdentityReplacement(policy)` exits in the round after a failed audit;
the exit takes effect in that round and the fresh identity offers in it.
```

- [ ] **Step 2: Append to spec section 14**

```
Implementation (plan 2A, version 2 after two reviews): identities separate
from entities; a retired identity is not marked in the rule's view and
fresh identities draw their own tie-break keys (`fresh_tie_keys`), so a
rule cannot link a successor to its predecessor beyond the timing of one
identity going silent and one appearing (N is fixed); an exit made in the
action of round t takes effect in round t (the identity retires before
offers, the fresh identity offers in round t and pays e in round t), which
is the "takes effect next round" of section 3 read from the round whose
outcome caused the decision and matches Proposition B; an exited identity's
bans and bond keep their schedule as if it had stayed and stopped serving.
Enforcement-ablation adapter (`sim/mechanisms/ablation.py`) and
exclusion-by-allocation count. D1 and D2 as families with logistic knob
transforms; exact points evaluated from knob dictionaries. CMA-ES search
with an evaluation archive (knobs, per-seed values, inflation flag); the
twin best and the honest point are registered incumbents of the attack
search; the projection of the best point is always evaluated and replaces
it when higher. Reference candidates in the registered tie order
abstention, honest-max, twin best, attack projection, best archived
clip = 1 point, best archived never-inflated clip = 0 point (as its
projection, no new run), projected bank members; abstention first so a tie
at zero profit is labeled abstention. Calibration of S_hat, n_FB, m bound to
the market; every cell derives alpha = rho m and B = beta S_hat; the
calibration seed namespace 4000-4019 is disjoint from dev-train 1000-1004 and
dev-val 2000-2019. Tuning rechecks search on dev-train and score on dev-val.
Doubling check: the extra budget is split half and half between clip-fixed
searches and the finalized gain is compared; twin-vs-honest at relative 1%;
restart spread reported for the attack and the reference objectives.
`sim/schedule.py` is the single source of run counts; `manifest.py` sums it
and `sweep.py` asserts its run counter against it. Manifest at this
version, pre-lock, exact unless stated: development 744,240 (48 cells);
rho sweep 94,470; no-ban 31,490; H3 47,235... [the executor replaces this
sentence with the figures `scripts/manifest.py` prints at the end of the
task, section by section, and with the measured ms per run and core-hours
from `scripts/bench_sweep.py`]; these figures supersede the prose totals in
section 5.3 (tuning is 279 grid points, not 3 x 243; corners are counted
per cell; bank figures are upper bounds). Per-seed output rows carry the
section 7 metrics (`sim/reference.py::ROW_FIELDS`).
```

- [ ] **Step 3: Update the README status**

Replace the README's `## Status` body with:

```
Week 2. Identities and H3, enforcement-ablation adapter, D1/D2 families,
CMA-ES search with an archive, incumbents and projection replacement, twin
search, reference selection from the bounded projected set, candidate bank
pass, calibration, baseline tuning with dev-val rechecks, all-deviators,
search checks, schedule-driven manifest, staged sweep runner, and the
full-path benchmark implemented. Plan 2B (intervals, coverage study, claim
script, lock tooling, model actors, custodian instructions) next.
```

- [ ] **Step 4: Run the whole suite and the benchmarks**

Run: `uv run pytest -q && uv run python scripts/bench.py && uv run python scripts/bench_sweep.py && uv run python scripts/manifest.py`
Expected: all tests PASS; both benchmarks under their gates; the manifest totals printed (copy them into the spec note of Step 2).

- [ ] **Step 5: Commit**

```bash
git add experiments/families.md docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md README.md
git commit -m "docs: plan 2A implementation note with rulings and manifest figures; families.md; README status"
```

---

## Self-review

**Spec coverage for this plan's scope.** Section 3 identity replacement, entry cost, exit timing: Task 2. Section 3 calibration constants and configuration validity: Task 9. Section 4.0 identity opacity: Task 2 (`test_rule_view_does_not_reveal_exit_or_successor`, `test_relabeling_with_reentry_relabels_decisions`). Section 4.1 no-ban diagnostic: Task 13 (`no_ban` section). Section 4.2 tuning grid, inner search, objective, dev-val recheck: Task 12. Section 5.1 views with identity: Task 2. Section 5.2 honest-max, twin, abstention, every discovered admissible truthful candidate in projected form from the archive and the bank, reference selected last after the bank pass, incumbent replacement by the projection, twin and honest-max incumbents, containment tests: Tasks 6, 7, 8, 13. Section 5.3 D1/D2 with recurrence and domains, transforms, registered starts, search budget, incumbent re-evaluation, exact corners, positions, headline selection, search checks (a) to (d), all-deviators, workload manifest and full-path gate: Tasks 4, 6, 10, 11, 13. Section 6 `locked.yaml` contents, `families.md`, seed namespaces: Tasks 1, 14. Section 6.2 H3: Tasks 2, 13 (`h3` section). Section 7 reference run, gain per entity, clipped-attack run, efficiency quadruple, audit spend, harm, participant diagnostics, per-seed rows: Tasks 2, 7, 13. Section 8 enforcement-ablation adapter and candidate bank: Tasks 3, 8, 13. Section 12 pre-lock tests (honest-max equals its twin; honest-max gain exactly 0 under an honest-max reference; twin candidate as attacker reproduces its trajectory): Tasks 4, 7. Not in this plan, by the stated split: interval algorithms, coverage study, `check_claim.py`, hashes and lock tooling, the model-actor harness, `describe()` rendering, the custodian bundle, `plot.py`, and the ablation runs against a proposed rule (post-lock by definition; the adapter and its tests exist).

**Placeholder scan.** One deliberate placeholder: the manifest figures in Task 14 Step 2 are copied from `scripts/manifest.py` output at execution time, and the sentence says so.

**Type consistency.** `Family.transform/inverse/project/make/corners/honest_point/registered_starts`, `knob_key`; `h3_family(family)`; `Cell(cfg, rule_factory, focal, seeds, name, others=())`; `run_profile(cfg, rule_factory, factories, seeds, cache)`; `run_focal(cell, policy_factory, cache) -> FocalRun(profit, normalized, inflated_per_seed, inflated, results)`; `Objective(cell, family, cache, force_clip)` with `knobs_of/eval_knobs/__call__/archive/evals`; `best_archived(archive, clip, truthful_only)`; `cma_search(objective, family, settings, seed, incumbents) -> SearchResult(best_x, best_knobs, best_f, best_source, restart_bests, evals, trace, incumbent_scores, projection_f, replaced_by_projection, archive)`; `corner_controls(objective, family)`; `twin_search(cell, family, cache, settings, seed)`; `attack_search(cell, family, cache, settings, seed, twin)`; `reference_candidates(cell, family, attack, twin, bank_members, order)`; `select_reference(cell, candidates, cache) -> ReferenceChoice(candidate, per_seed_profit, per_seed_normalized, scores)`; `evaluate_gain(cell, family, attack_knobs, reference: Candidate, cache) -> GainResult`; `seed_rows(cell, g, meta)`, `ROW_FIELDS`; `Bank.add/members_for/projected_members_for/evaluate/bank_pass/transfer_rows/to_json/from_json`; `calibrate(cfg_base, seeds) -> Calibration(S_hat, n_FB, m, market_key, T, seeds)`, `cell_config(cfg_base, cal, rho, beta)`; `positions`, `headline_position`; `restart_spread(attack, twin)`, `FixedClipObjective`, `doubling_check(cell, family, cache, settings, seed, base_attack, base_twin, bank_members, order)`, `twin_vs_honest(twin, honest_f)`; `iterated_best_response(cfg, rule_factory, family, cache, settings, seeds, sweeps, seed)`; `score_point(rule_name, params, cfg, locked, cache, family, inner_override, recheck)`, `tune(...)`; `Budget`, `cell_runs`, `stage_runs`, `enumerate_manifest(locked, rules, budget)`, `totals`; `search_to_json/search_from_json`, `candidate_from_record`. `EpisodeResult` gains `n_identities, entity_of, identity_round, identity_profit` and keeps every plan 1 field.

**Review Focus.** Item 1: Task 2 `test_rule_view_does_not_reveal_exit_or_successor`. Item 2: Task 2 `test_banned_identity_can_still_exit_and_fresh_identity_is_not_banned`, `test_exit_does_not_change_ban_or_bond_schedule`. Item 3: Task 4 `test_make_returns_fresh_instances_and_h3_family_wraps`. Item 4: Task 6 `test_flat_objective_terminates_and_counts`, Task 7 `test_abstention_wins_when_everything_loses_money`. Item 5: Task 6 `test_corner_controls_use_exact_knobs_at_tier_boundaries`. Item 6: Task 7 `test_gain_on_other_seeds_subtracts_reference_on_those_seeds`. Item 7: Task 9 `test_cell_config_refuses_foreign_calibration`, Task 13 `test_sweep_refuses_untuned_run_without_smoke_flag`.

**Rulings carried in this plan (for the executor's ledger and the spec note):** (1) exits take effect in the round the policy makes them; (2) retired identities are not marked in the view; (3) abstention is first in the registered candidate order; (4) the twin search has no incumbents so that check (d) stays a diagnostic; (5) the projection of the best point is always evaluated so the schedule stays exact; (6) the H3 cell is a full cell over the wrapped family `D2+H3` with its own twin and reference; (7) bank members come from development cells only and the bank pass targets every D1 and D2 cell including rho-sweep and no-ban cells; (8) tuning runs at `beta_headline` and the default rho; (9) the doubling check gives each clip-fixed search half of one extra base budget; (10) a calibration namespace exists next to the three of section 6.
