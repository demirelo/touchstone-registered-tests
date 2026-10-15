# Touchstone plan 2A (version 9): identities, D2, search, reference selection, bank, calibration, tuning, manifest and sweep

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the core engine with identities and identity replacement (H3), the enforcement-ablation adapter, the D2 adaptive family, the pre-registered CMA-ES search with an evaluation archive, twin search, last-step reference selection from the bounded projected set, gain decomposition, the candidate bank pass, calibration, baseline tuning with dev-val rechecks, the all-deviators table, the search checks, and one schedule that both the manifest counts and the sweep executes, so that every pre-lock simulator run the spec names can be run from one locked configuration file and counted.

**Architecture:** Plan 1's engine stays the authority on money and admissibility. Identities are separate from entities inside `run_episode`: ledger columns, bans, capacity, and tie-break keys are per identity; profit is per entity; a retired identity is never marked in a rule's view. Families map an unbounded CMA-ES vector to a policy through a logistic transform and project any point to its truthful twin. An `Objective` evaluates exact knob dictionaries and keeps an archive of every evaluated point with its per-seed values and an inflation flag; the reference set and the incumbent rules of spec 5.2 are built from that archive. A `SeedCache` holds draws and S* per (market, seed) and counts runs. `sim/schedule.py` is the one place that says which runs a cell needs; `manifest.py` sums it and `sweep.py` executes it stage by stage (search, bank, reference, evaluate, checks, all-deviators), writing one JSON record per cell and stage.

**Tech Stack:** Python 3.12+, numpy, scipy, `cma` (pycma) for CMA-ES, `pyyaml` for the locked config, `concurrent.futures` for the sweep, pytest.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5 plus the plan 1 implementation note). This plan implements sections 3 (identity replacement, entry cost, calibration constants), 4.0 (identity opacity), 4.1 (no-ban diagnostic), 4.2 (baseline tuning), 5.1 to 5.3 (families, twins, containment tests, search with incumbents and projection replacement, positions and headline selection, search checks, all-deviators, candidate bank, workload manifest and the full-path gate), 6 (seed namespaces, `locked.yaml` contents, `families.md`), 6.2 (H3), 7 (reference run, gain, clipped-attack run, efficiency quadruple, per-seed output schema), and the enforcement-ablation adapter of section 8. Plan 2B covers the interval algorithms, the coverage study, `check_claim.py`, the lock tooling and hash checks, the LLM and Jev actor harness with the `describe()` renderer and comprehension fixture, the custodian instructions for the sealed bundle, the token pilot, and `plot.py`. Nothing else is deferred.

**Scope split, stated once:** Plan 2A ends when `scripts/sweep.py --stage all` runs the development cells, the rho sweep, the H3 cells, the no-ban cells, the controls, the bank pass, reference selection, dev-val evaluation, headline selection, the search checks, and the all-deviators table from `locked.yaml` and a calibration file; `scripts/tune_baselines.py` runs the tuning grid; `scripts/manifest.py` reports run counts derived from the same schedule; and `scripts/bench_sweep.py` measures the full path. Nothing in this plan designs or runs a proposed rule, touches held-out families, or computes a confidence bound.

**Changes from version 8 (round 8: both seats reject on the settings hash):** the H3 reading note and the common-random-numbers amendment are made precise (timing alone identifies the newcomer in registered H3 cells; only the exiting entity's draws diverge); the `Draws` docstring and the `fresh_seed` comment are updated; the settings hash excludes `identity_salt_sha256`, which the lock tooling writes, so installing the commitment at the lock does not invalidate the tuned files the lock lists (regression in `test_settings_hash_covers_every_experimental_setting`); the untracked-salt test is placed after the complete secret test.

**Changes from version 7 (round 7: Astra reject on the salt timeline, Opus accept-with-caveat):** replacement noise is computed once per identity per round; Task 14 amends the spec's common-random-numbers sentence (replacement streams are fixed and action-independent; H3 attack and reference share draws until the first exit); `families.md` carries the H3 reading note; the salt lifecycle is made consistent with the freeze dates (development salt tracked; final salt generated and committed by hash at the lock, released with the sealed bundle after the rule freeze, loaded from an untracked path through `TOUCHSTONE_IDENTITY_SALT`, checked by `check_claim.py`); the spec note's opacity claim is limited to the repaired channels; refusal messages name the stages to rerun.

**Changes from version 6 (round 6: Astra reject on the offer order, Opus accept-with-caveat):** replacement identities deliver with salted noise, so an audited delivery no longer matches the entity's public noise stream; the salt lifecycle is stated (placeholder before the lock, final salt by the separate session after the proposed rule is frozen); the inherent link through a newcomer's offer type is stated; the offers dictionary a rule receives, and the history record, are in identity-id order instead of entity order, which closed the last way a rule could link a same-round newcomer to its predecessor; the entrant-order regression test also checks the offer order, and a misplaced test block is restored; D1 and D2 records without a bank hash are refused; the spec note's version label is corrected.

**Changes from version 5 (round 5: Astra reject with one material finding, Opus accept-with-caveat):** same-round exits are ordered by a salted per-entity rank (`entrant_rank`), with a test that the order depends on the salt and is not the seed-only permutation; reference records carry the bank hash and the evaluate stage checks the bank too; records carry a salt fingerprint; the one-restart inner search is stated as a lower bound; the benchmark margin and the B3 optimization fallback are stated; the heading and stale call examples are fixed.

**Changes from version 4 (round 4: Astra reject with two material findings, Opus accept-with-caveat):** replacement identities' secrets are keyed with a 32-byte identity salt stored in `experiments/identity_salt.hex`, a harness secret outside the config a rule may read, because the episode seed itself can be recovered from public job values; the bank stage validates every source record before building the bank, `bank.json` records its sources with hashes and a bank hash, bank records carry it, and the reference and checks stages refuse a stale bank, a missing bank record, or a bank whose sources changed; twin searches start near-honest first (R14 amended) so a one-restart twin search keeps positive truthful profit; the focal entity's current identity breaks creation-round ties by generation; search coordinates follow a corner or bank replacement.

**Changes from version 3 (round 3: both seats reject):** replacement identities' tie keys come from one-way BLAKE2b secrets (a reversible hash let a rule link successors to predecessors); archive lookups in reference selection use exact keys (rounded keys caused re-runs that broke the H3 reference bound); exact keys also de-duplicate bank members and candidates; the registered start order puts near-full-cheat first so one-restart searches (inner tuning, all-deviators) can cheat (R14, with tests that B1 inner gain is positive and all-deviators attack profiles inflate); the best exact corner replaces a cell's attack incumbent in every cell including H3 (R15) and the bank pass reuses corner values; the bank total counts full cells only; records bind budget, mode, and cell name, and every consumed record is checked; the settings hash covers the whole locked configuration; tuned files bind their calibration seeds and non-quick tuning requires the full calibration namespace; focal banned rounds count only the entity's current identity; the ablation enforcer's memory contract is stated and enforced; the all-deviators stage honors `--sections`; test counts corrected.

**Changes from version 2 (round 2: Astra reject, Opus accept-with-caveat):** replacement identities draw tie keys from their entity's per-round `fresh_seed` and their generation, and same-round entrants get ids in a keyed random order (relabeling invariance with re-entry, both reversed-order and unequal-history tests); the archive keys points by exact value and the inflation flag is strict; the ablation adapter runs the rule's own `enforce` for its memory and gives the enforcer a separate memory; the bank holds each target family's corners; the doubling check starts from the bank-finalized attack and reports pre-projection clip values; the H3 family carries an exit knob `x` so its honest point is honest-max; all-deviators runs the attack and the twin procedure and evaluates both on dev-val; the schedule has exact entries and bounds, the sweep records its counter after all work and asserts every stage, and the benchmark times every stage; per-seed rows carry the refund and forfeit split, the participant diagnostics, the focal ban count, and the reference name; tuned files and the calibration are bound to the market key and the settings hash; `restart_spread` reports the gain differences; the two test defects of version 2 are fixed.

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
- Produces: `load_locked(path="experiments/locked.yaml") -> dict`; `seeds(locked, namespace) -> list[int]` for `"dev_train"`, `"dev_val"`, `"calibration"`; `sha256_file(path) -> str`; `settings_hash(locked) -> str` (sha256 of the whole locked configuration except the blocks written at the lock, `version`, `tuned`, `calibration`, and `identity_salt_sha256`, sorted keys; artifacts record it so a stale tuning or search record is refused, and installing the lock-time blocks does not invalidate the pre-lock artifacts they list); `market_config_from_locked(locked) -> MarketConfig` (every market primitive from the YAML; `alpha` and `budget` zero until a cell derives them).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_locked.py
import pytest
from sim.locked import load_locked, seeds, sha256_file, settings_hash, market_config_from_locked
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


def test_settings_hash_covers_every_experimental_setting():
    lk = load_locked()
    h = settings_hash(lk)
    assert len(h) == 64
    for key, value in (("tuning", dict(lk["tuning"], inner_evals=101)), ("beta_headline", 0.1), ("rho", dict(lk["rho"], default=0.5)),
                       ("seeds", dict(lk["seeds"], calibration=[4000]))):
        other = dict(lk); other[key] = value
        assert settings_hash(other) != h
    same = dict(lk); same["version"] = "something-else"; same["tuned"] = {"B1": "x"}; same["identity_salt_sha256"] = "ab" * 32
    assert settings_hash(same) == h          # the blocks written at the lock do not invalidate the artifacts the lock lists
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
tuned: null                 # at the lock, the lock tooling (plan 2B) lists experiments/tuned/tuned_<rule>.json with sha256 here
identity_salt_sha256: null  # at the lock, the separate session commits the SHA-256 of the final salt here; the salt itself is released with the sealed bundle
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
import json
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


def settings_hash(locked: dict) -> str:
    """Hash of every experimental setting: the whole file except the version label and the blocks the lock tooling fills
    (tuned, calibration, identity_salt_sha256), so installing them at the lock keeps the pre-lock artifacts valid."""
    bound = {k: v for k, v in locked.items() if k not in ("version", "tuned", "calibration", "identity_salt_sha256")}
    return hashlib.sha256(json.dumps(bound, sort_keys=True).encode()).hexdigest()


def market_config_from_locked(locked: dict) -> MarketConfig:
    mk = locked["market"]; pt = mk["providers"]
    providers = tuple(ProviderParams(q_max=float(q), a=float(a), b=float(b), k=int(k))
                      for q, a, b, k in zip(pt["q_max"], pt["a"], pt["b"], pt["k"]))
    return MarketConfig(N=int(mk["N"]), J=int(mk["J"]), T=int(mk["T"]), sigma=float(mk["sigma"]), e=float(mk["e"]),
                        v_min=float(mk["v_min"]), v_max=float(mk["v_max"]), providers=providers, alpha=0.0, budget=0.0)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv sync && uv run pytest tests/test_locked.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock experiments/locked.yaml sim/locked.py tests/test_locked.py
git commit -m "feat: locked configuration draft with the market table, seed namespaces, candidate order; cma and pyyaml dependencies"
```

---

### Task 2: Identities, exit and re-entry, entry cost, identity opacity, and the H3 policy wrapper

**Files:**
- Modify: `sim/ledger.py` (add `grow`), `sim/policies/base.py` (`ProviderView.identity`, exit allowed), `sim/rng.py` (add `fresh_seed`, the identity salt, the secrets, `fresh_tie_keys`), `sim/market.py` (identity bookkeeping)
- Create: `experiments/identity_salt.hex` (64 hex characters: run `python -c "import secrets; print(secrets.token_hex(32))"` once and commit the output; this is the development salt, used for every pre-lock and post-lock development run). Lifecycle of the final salt: at the lock (2026-10-28, before any proposed rule exists) the separate session generates a second 32-byte salt, publishes only its SHA-256 in `locked.yaml` under `identity_salt_sha256`, and holds the salt with the final-eval seeds; it is released with the sealed bundle at the evaluation freeze, after the proposed rule is frozen; final-eval runs load it from an untracked path named by the environment variable `TOUCHSTONE_IDENTITY_SALT` (so no frozen tracked file changes), and `check_claim.py` (plan 2B) requires the loaded salt's hash to equal the committed one for final-eval runs and the development salt's hash for every other run. Records carry the salt fingerprint either way.
- Create: `sim/policies/identity.py`
- Test: `tests/test_identity.py`; update `tests/test_policies.py::test_validate_action`

**Interfaces:**
- Consumes: plan 1 engine.
- Produces:
  - `Ledger.grow(m: int)` extends every per-identity array to `m` columns.
  - `ProviderView.identity: int` (current identity id of the entity).
  - `validate_action` no longer raises on `exit`.
  - `Draws.fresh_seed: np.ndarray` of shape `(T, N)`, int64, drawn in `draws_for_round` after `policy_seed` (every earlier draw keeps its value); `draws_for_round` returns seven arrays.
  - `load_identity_salt(path=None) -> bytes` (32 bytes, cached, from `path`, else from the file named by the environment variable `TOUCHSTONE_IDENTITY_SALT`, else from `experiments/identity_salt.hex`): a harness secret that is not part of the locked config a rule may read (spec 4.0) and never reaches a rule. `identity_secret(salt, seed, t, fresh_seed_e, generation) -> int` and `retired_secret(salt, seed, t, identity) -> int`: 64-bit keyed BLAKE2b digests. Every public stream (values, keys) is a function of the small episode seed, so a rule could recover the seed by brute force from the job values; the keyed digest makes that useless, because the salt is high-entropy and unavailable to the rule. `fresh_tie_keys(secrets, J) -> np.ndarray` of shape `(J, len(secrets))`, read-only: column `c` is `default_rng(SeedSequence(secrets[c])).random(J)`. A live replacement identity's column comes from `identity_secret(salt, seed, t, fresh_seed[t, entity], generation)`, so it depends only on the entity and the generation, never on creation order, and permutes with the entity under relabeling; a retired replacement identity's column comes from `retired_secret(salt, seed, t, identity)` (fresh each round, no entity information, never used for an allocation because a retired identity never offers).
  - `run_episode` keeps `entity_of: list[int]` (identity to entity), `identity_of: list[int]` (entity to identity), `generation: list[int]` (0 for an initial identity, 1 for the first replacement, and so on), and a harness-private `alive` list. Each round has three passes: every entity acts; exits are applied in the order of `entrant_rank(salt, seed, t, fresh_seed[t, entity])` (a keyed secret per exiting entity, so the ids of same-round entrants carry no entity information even to a rule that recovered the episode seed, and the order permutes with the entity under relabeling); offers are then recorded under each entity's current identity, and the offers dictionary a rule receives (and the history record) is in identity-id order, never in entity order, so neither the ids nor the order of offers links a newcomer to its predecessor. An exit retires the current identity (never offers again; its `capacity`, `banned_until`, and `bond` entries in the view are left as they are), creates a fresh identity with capacity `k_i`, `banned_until 0`, no bond, and charges `cfg.e` in that round; the action's offer, if any, is submitted under the fresh identity. An initial identity uses its entity's column of `Draws.tie_key`; a replacement identity uses `fresh_tie_keys([identity_secret(salt, seed, t, fresh_seed[t, entity], generation)], J)`, and its deliveries use `replacement_noise(salt, seed, t, fresh_seed[t, entity], generation, kmax, sigma)` (computed once per replacement identity per round) instead of the entity's public noise stream (an audited delivery would otherwise match that stream). These streams are fixed functions of entity, generation, round, and salt, so no action changes a draw; in H3 cells the attack and the reference runs share every draw except the exiting entity's tie keys and delivery noise after its first exit (Task 14 amends the spec's common-random-numbers sentence). What remains linkable is inherent: in a registered H3 cell only the focal entity exits, so timing alone identifies every newcomer, and a newcomer's offer reflects its provider type, which with ten distinct types identifies the entity; the salted channels matter for rules that would exploit more than timing and type (several simultaneous exits, or identical types); `families.md` and the spec note say so for the reader of the H3 table.
  - `EpisodeResult.profit` stays per entity; new fields `n_identities: int`, `entity_of: tuple[int, ...]`, `identity_round: tuple[int, ...]` (creation round, 0 for initial identities), `identity_generation: tuple[int, ...]`, `identity_profit: np.ndarray`.
  - `IdentityReplacement(policy)` wrapper (H3): acts like `policy` and sets `exit=True` in the round after a failed audit. `h3_family(family) -> Family`: the family `<name>+H3` with one more binary knob `x` (placed before `clip`): with `x = 1` the policy is wrapped in `IdentityReplacement`, with `x = 0` it is the base policy. Its honest point (`x = 0`, `clip = 1`) therefore reproduces honest-max, so reference containment holds for the H3 cells (spec 5.2). Defined here on top of Task 4's `Family` fields by `dataclasses.replace`; Task 4 tests it.

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
from sim.rng import fresh_tie_keys, identity_secret, retired_secret, entrant_rank, replacement_noise, load_identity_salt, DEFAULT_SALT_PATH, make_draws, Draws


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
                          "offers": set(offers), "offer_order": list(offers)})
        return super().allocate(values_t, offers, view)


def test_ledger_grow_keeps_totals():
    led = Ledger(N=2, T=3)
    esc, own = {}, {}
    led.fund(0, 0, 1, 0.5, esc, own); led.settle(0, esc, own, Consequences(), {})
    led.grow(4)
    assert led.funding.shape == (3, 4) and led.bond.shape == (4,)
    assert led.funding.sum() == pytest.approx(0.5)
    led.check_conservation(0.0)


def test_fresh_tie_keys_depend_only_on_the_secret():
    salt = bytes(range(32))
    s1, s2, s3 = identity_secret(salt, 7, 3, 11, 1), identity_secret(salt, 7, 3, 22, 1), identity_secret(salt, 7, 3, 11, 2)
    assert len({s1, s2, s3, retired_secret(salt, 7, 3, 10), identity_secret(salt, 7, 4, 11, 1)}) == 5     # entity, generation, round, retirement all matter
    assert identity_secret(bytes(32), 7, 3, 11, 1) != s1          # without the salt, knowing seed, round, fresh_seed and generation gives nothing
    assert entrant_rank(salt, 7, 3, 11) != entrant_rank(bytes(32), 7, 3, 11) and entrant_rank(salt, 7, 3, 11) != s1
    assert len(load_identity_salt()) == 32
    a = fresh_tie_keys([s1, s2], 50); b = fresh_tie_keys([s2, s1, s3], 50)
    assert a.shape == (50, 2) and np.array_equal(a[:, 0], b[:, 1]) and np.array_equal(a[:, 1], b[:, 0])
    assert not np.array_equal(b[:, 2], a[:, 0])
    assert not a.flags.writeable and a.min() >= 0.0 and a.max() < 1.0 and len(np.unique(a[:, 0])) == 50
    d = make_draws(MarketConfig.default(), 3)
    assert d.fresh_seed.shape == (200, 10) and d.fresh_seed.dtype == np.int64


def test_identity_salt_can_be_loaded_from_an_untracked_path(tmp_path, monkeypatch):
    other = tmp_path / "final_salt.hex"; other.write_text("ab" * 32 + "\n")
    monkeypatch.setenv("TOUCHSTONE_IDENTITY_SALT", str(other))
    assert load_identity_salt() == bytes([0xAB] * 32) and load_identity_salt() != load_identity_salt(DEFAULT_SALT_PATH)
    bad = tmp_path / "short.hex"; bad.write_text("abcd\n")
    with pytest.raises(ValueError):
        load_identity_salt(bad)


def test_same_round_entrant_order_is_not_a_function_of_the_seed_alone():
    """A rule that recovers the episode seed must not be able to map same-round entrants to their predecessors,
    neither through the ids nor through the order of the offers it receives."""
    cfg = cfgb(budget=0.0, T=5)
    orders = {}
    for salt in (bytes(range(32)), bytes(range(1, 33))):
        pols = [ExitAt(when=2) for _ in range(cfg.N)]                       # every entity exits in round 2
        spy = Spy(0.25, 0.40, 0.55, tol=0.12, L=10)
        res = run_episode(cfg, spy, pols, 0, identity_salt=salt)
        orders[salt] = tuple(res.entity_of[cfg.N:])                          # entity of identity N, N + 1, ... in creation order
        assert all(rec["offer_order"] == sorted(rec["offer_order"]) for rec in spy.seen)   # offers arrive in id order, never in entity order
        assert all(list(h.offers) == sorted(h.offers) for h in res.history)
    assert len(set(orders.values())) == 2                                   # the order depends on the salt, not on the seed alone
    public = tuple(int(x) for x in np.random.default_rng(np.random.SeedSequence([0, 2, 2])).permutation(cfg.N))
    assert all(o != public for o in orders.values())


def test_replacement_identities_deliver_with_salted_noise():
    """An audited delivery of a replacement identity never matches the entity's public noise stream."""
    cfg = cfgb(budget=50.0, T=6)                                            # every served job is audited
    d = make_draws(cfg, 0); salt = bytes(range(32))
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=1)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0, draws=d, identity_salt=salt)
    audits = [(rec.t, r) for rec in res.history for r in rec.audits if r.provider == cfg.N]
    assert audits
    q = cfg.providers[2].q_max
    for t, r in audits:
        public = q + d.noise[t, 2, :]                                         # what a seed-recovering rule predicts from the entity's stream
        salted = q + replacement_noise(salt, 0, t, int(d.fresh_seed[t, 2]), 1, cfg.kmax, cfg.sigma)
        assert not np.any(np.isclose(r.delivered, public)) and np.any(np.isclose(r.delivered, salted))


def test_exit_creates_fresh_identity_and_charges_entry_cost_in_that_round():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=3)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N + 1 and res.entity_of[-1] == 2 and res.identity_round[-1] == 3 and res.identity_generation[-1] == 1
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


class ExitAtRounds:
    """Exits in each round of `when`, otherwise honest-max."""
    name = "exit_at_rounds"
    def __init__(self, when): self.when = set(when)
    def act(self, view):
        a = HonestMax().act(view)
        return Action(effort=a.effort, offer=a.offer, exit=(view.t in self.when))


@pytest.mark.parametrize("perm,exits", [
    (np.array([3, 0, 9, 1, 7, 5, 8, 2, 4, 6]), {2: (3,), 5: (3,)}),        # simultaneous exits whose creation order reverses under the permutation
    (np.array([3, 0, 9, 1, 7, 2, 8, 5, 4, 6]), {2: (3, 6), 5: (3,)}),     # unequal replacement histories
])
def test_relabeling_with_reentry_relabels_decisions(perm, exits):
    c = cfgb(budget=1.0, T=12)
    cfg_p = MarketConfig(N=c.N, J=c.J, T=c.T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                         providers=tuple(c.providers[o] for o in perm), alpha=c.alpha, budget=c.budget)
    d = make_draws(c, 5)
    d_p = Draws(values=d.values, noise=d.noise[:, perm, :], tie_key=d.tie_key[:, :, perm], audit_u=d.audit_u,
                audit_key=d.audit_key, policy_seed=d.policy_seed[:, perm], fresh_seed=d.fresh_seed[:, perm])
    inv = np.argsort(perm)
    pols = [HonestMax() for _ in range(c.N)]
    for e, when in exits.items():
        pols[e] = ExitAtRounds(when)
    pols_p = [pols[o] for o in perm]
    r = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    a = run_episode(c, r, pols, 5, draws=d); b = run_episode(cfg_p, r, pols_p, 5, draws=d_p)
    # key an identity by (entity, generation) so fresh identities compare across runs whatever their creation order
    ka = {i: (int(inv[e]), g) for i, (e, g) in enumerate(zip(a.entity_of, a.identity_generation))}
    kb = {i: (int(e), g) for i, (e, g) in enumerate(zip(b.entity_of, b.identity_generation))}
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

Also change two plan 1 tests for the new draw. In `tests/test_rng.py::test_round_draws_are_pure_function_of_seed_and_round` replace `v, n, tk, au, ak, ps = draws_for_round(cfg, seed=11, t=t)` with `v, n, tk, au, ak, ps, fs = draws_for_round(cfg, seed=11, t=t)` and add `assert np.array_equal(fs, full.fresh_seed[t])` after the `policy_seed` assertion. In `tests/test_boundary.py::test_relabeling_identities_relabels_decisions` add `fresh_seed=d.fresh_seed[:, perm]` to the `Draws(...)` call.

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
Expected: FAIL on `ImportError: cannot import name 'fresh_tie_keys'` (and `identity_secret`, `retired_secret`, `entrant_rank`, `replacement_noise`), then on `sim.policies.identity`, `Ledger.grow`, `n_identities`, `fresh_seed`, and `NotImplementedError`.

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

Change `sim/rng.py`: change the `Draws` docstring to `Every random input of an episode, a pure function of (seed, round); replacement identities add fixed streams keyed by entity, generation, round, and the identity salt.`; add the field `fresh_seed: np.ndarray   # (T, N) per-entity base for replacement identities' secrets (tie keys, entrant order, delivery noise)` as the last field of `Draws`; in `draws_for_round` add `fresh_seed = g.integers(0, 2**62, size=cfg.N)` after the `policy_seed` draw and return it as the seventh value; in `make_draws` allocate `fresh_seed = np.empty((cfg.T, cfg.N), dtype=np.int64)`, fill it from the seventh value, include it in the read-only loop, and pass it to `Draws`. Then add after `make_draws`:

```python
DEFAULT_SALT_PATH = Path(__file__).resolve().parents[1] / "experiments" / "identity_salt.hex"
SALT_ENV = "TOUCHSTONE_IDENTITY_SALT"
_SALT_CACHE: dict[str, bytes] = {}


def load_identity_salt(path: str | Path | None = None) -> bytes:
    """Harness secret for replacement identities' keys: 32 bytes, outside the config a rule may read.
    Resolution: the given path, else the file named by TOUCHSTONE_IDENTITY_SALT (the final salt, released
    after the freeze, lives at an untracked path), else the development salt in experiments/."""
    if path is None:
        path = os.environ.get(SALT_ENV) or DEFAULT_SALT_PATH
    key = str(path)
    if key not in _SALT_CACHE:
        salt = bytes.fromhex(Path(path).read_text().strip())
        if len(salt) != 32:
            raise ValueError("identity salt must be 32 bytes")
        _SALT_CACHE[key] = salt
    return _SALT_CACHE[key]


def _secret(salt: bytes, *parts) -> int:
    """Keyed one-way 64-bit digest; without the salt, the public streams (all functions of the episode seed) reveal nothing."""
    data = ":".join(str(int(x)) for x in parts).encode()
    return int.from_bytes(hashlib.blake2b(data, key=salt, digest_size=8).digest(), "little")


def identity_secret(salt: bytes, seed: int, t: int, fresh_seed_e: int, generation: int) -> int:
    return _secret(salt, 1, seed, t, fresh_seed_e, generation)


def retired_secret(salt: bytes, seed: int, t: int, identity: int) -> int:
    return _secret(salt, 2, seed, t, identity)


def entrant_rank(salt: bytes, seed: int, t: int, fresh_seed_e: int) -> int:
    """Order in which same-round exits are processed: a keyed secret per entity, so the ids of
    same-round entrants reveal nothing to a rule, even one that recovered the episode seed."""
    return _secret(salt, 3, seed, t, fresh_seed_e)


def replacement_noise(salt: bytes, seed: int, t: int, fresh_seed_e: int, generation: int, kmax: int, sigma: float) -> np.ndarray:
    """Delivery noise of a replacement identity's slots in round t: a salted stream, so an audited delivery
    cannot be matched to the entity's public noise stream by a rule that recovered the episode seed."""
    g = np.random.default_rng(np.random.SeedSequence(_secret(salt, 4, seed, t, fresh_seed_e, generation)))
    return g.normal(0.0, sigma, size=int(kmax))


def fresh_tie_keys(secrets, J: int) -> np.ndarray:
    """Tie-break keys for identities created by re-entry, (J, len(secrets)): column c is the
    uniform stream seeded by secrets[c]. A live replacement identity's secret depends on its
    entity's per-round fresh_seed and its generation only, so relabeling entities permutes
    the columns and creation order is irrelevant; the secret never reaches a rule."""
    out = np.empty((int(J), len(secrets)))
    for c, sec in enumerate(secrets):
        out[:, c] = np.random.default_rng(np.random.SeedSequence(int(sec))).random(int(J))
    out.setflags(write=False)
    return out
```

and add `import hashlib`, `import os`, and `from pathlib import Path` at the top of `sim/rng.py`.

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
    """The family with one more binary knob x: x = 1 wraps the policy in IdentityReplacement,
    x = 0 leaves it unwrapped, so the honest point (x = 0, clip = 1) is honest-max."""
    base_factory = family.factory

    def factory(**k):
        k = dict(k); x = int(k.pop("x"))
        p = base_factory(**k)
        return IdentityReplacement(p) if x else p
    knobs = tuple(n for n in family.knobs if n != "clip") + ("x", "clip")
    return replace(family, name=f"{family.name}+H3", knobs=knobs, factory=factory)
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
from .rng import Draws, entrant_rank, fresh_tie_keys, identity_secret, load_identity_salt, make_draws, replacement_noise, retired_secret


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
    identity_generation: tuple[int, ...]   # identity -> 0 for initial, 1 for the first replacement, ...
    identity_profit: np.ndarray   # per identity


def _frozen(cons: Consequences) -> Consequences:
    return Consequences(refunds=MappingProxyType(dict(cons.refunds)), bans=MappingProxyType(dict(cons.bans)),
                        holdbacks=MappingProxyType(dict(cons.holdbacks)), forfeits=MappingProxyType(dict(cons.forfeits)),
                        releases=MappingProxyType(dict(cons.releases)))


def run_episode(cfg: MarketConfig, rule, policies, seed: int, draws: Draws | None = None, sstar: float | None = None,
                identity_salt: bytes | None = None) -> EpisodeResult:
    cfg.validate()
    salt = load_identity_salt() if identity_salt is None else identity_salt
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
    generation: list[int] = [0] * N
    gen_of_entity = [0] * N
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
        actions = []
        for e in range(N):   # pass 1: every entity acts under its current identity
            act = policies[e].act(ProviderView(i=e, params=cfg.providers[e], t=t, posted_prices=posted,
                                               history=histories[e], policy_seed=int(d.policy_seed[t, e]), identity=identity_of[e]))
            validate_action(act, cfg.providers[e])
            actions.append(act)
            effort_e[e] = float(act.effort); efforts[t, e] = effort_e[e]
        exiting = [e for e in range(N) if actions[e].exit]
        if exiting:   # pass 2: exits in the order of a salted per-entity rank, so same-round entrants' ids carry no entity information
            for e in sorted(exiting, key=lambda e: entrant_rank(salt, seed, t, int(d.fresh_seed[t, e]))):
                # retire the current identity now; the fresh identity makes this round's offer and pays e now
                alive[identity_of[e]] = False
                new = len(entity_of)
                gen_of_entity[e] += 1
                entity_of.append(e); identity_of[e] = new; identity_round.append(t); generation.append(gen_of_entity[e]); alive.append(True)
                caps_id = np.append(caps_id, caps_entity[e]); banned_until = np.append(banned_until, 0)
                ledger.grow(new + 1)
                ledger.charge_entry(t, new, cfg.e)
        for e in range(N):   # pass 3: offers under the current identity
            ident = identity_of[e]; act = actions[e]
            if t < banned_until[ident] or act.offer is None:
                continue
            offers[ident] = Offer(claim=float(act.offer.claim), bid=float(act.offer.bid))
            claims[t, e] = offers[ident].claim
        offers = dict(sorted(offers.items()))    # id order, never entity order: a rule must not learn which entity a new id belongs to
        M = len(entity_of)
        ent_arr = np.array(entity_of, dtype=np.int64)
        if M == N:
            tie_key = np.array(d.tie_key[t], copy=True)
        else:   # replacement identities: one-way keyed streams; live ones by (entity secret, generation), retired ones by identity
            secrets = [identity_secret(salt, seed, t, int(d.fresh_seed[t, entity_of[i]]), generation[i]) if alive[i] else retired_secret(salt, seed, t, i)
                       for i in range(N, M)]
            tie_key = np.concatenate([d.tie_key[t], fresh_tie_keys(secrets, J)], axis=1)
        tie_key.setflags(write=False)
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
            noise = d.noise[t, ents, slots].copy()
            rnoise = {i: replacement_noise(salt, seed, t, int(d.fresh_seed[t, entity_of[i]]), generation[i], cfg.kmax, cfg.sigma)
                      for i in set(ids.tolist()) if i >= N}          # one stream per replacement identity per round
            for n, i in enumerate(ids.tolist()):      # replacement identities deliver with salted noise, never the entity's public stream
                if i >= N:
                    noise[n] = rnoise[i][slots[n]]
            y = effort_e[ents] + noise
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
                         identity_generation=tuple(generation), identity_profit=identity_profit)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_identity.py tests/test_policies.py tests/test_rng.py tests/test_boundary.py -v && uv run pytest -q`
Expected: PASS (12 new test functions, 13 test items with the parametrized relabeling test; whole suite green, 108 items after Task 1's four). The plan 1 relabeling test still passes because initial identity ids equal entity indices. `scripts/bench.py` stays under the gate (the identity loop adds about 2 ms on an M4 Max).

- [ ] **Step 5: Commit**

```bash
git add experiments/identity_salt.hex sim/ledger.py sim/rng.py sim/policies/base.py sim/policies/identity.py sim/market.py tests/test_identity.py tests/test_policies.py tests/test_rng.py tests/test_boundary.py
git commit -m "feat: identities separate from entities with opaque retirement, per-entity fresh tie keys, same-round exit and entry cost; H3 wrapper"
```

---

### Task 3: Enforcement-ablation adapter and exclusion-by-allocation count

**Files:**
- Create: `sim/mechanisms/ablation.py`
- Test: `tests/test_ablation.py`

**Interfaces:**
- Consumes: `Mechanism`, `EpisodeResult` (Task 2).
- Produces:
  - `EnforcementAblation(rule: Mechanism, enforcer: Mechanism)`: a `Mechanism` whose `allocate`, `price`, `audit`, `tol`, and `describe` (non-enforcement fields) come from `rule`, and whose `enforce` calls `rule.enforce(records, view)` first for its policy-memory side effects, discards that result, and returns `enforcer.enforce(records, view_e)` where `view_e` is the same view with the enforcer's own memory dict (so the two memories never collide); `bind` binds both and resets the enforcer memory. The harness recomputes every economic state from the consequences actually applied (plan 1), so the rule keeps its own non-economic memory on the counterfactual history and nothing else (spec 8).
  - `exclusion_by_allocation(res: EpisodeResult, after_failure: bool = True) -> dict[int, int]`: for each identity, the number of rounds in which it offered, was not banned, and received no job; with `after_failure` only rounds after its first failed audit count (identities without a failure count 0), and with `after_failure=False` every such round counts for every identity (the baseline under competition, reported next to the first in the ablation table).

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


def test_ablation_keeps_the_rules_enforce_time_memory():
    cfg = cfgb(budget=5.0, T=12)
    abl = EnforcementAblation(Shunner(0.25, 0.40, 0.55, tol=-10.0, L=10), PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=3))
    res = run_episode(cfg, abl, [HonestMax() for _ in range(cfg.N)], 0)
    assert any(v > 0 for v in exclusion_by_allocation(res).values())        # the shun list, written in enforce, still drives allocation
    bans = [c for rec in res.history for c in rec.consequences.bans.values()]
    assert bans and set(bans) == {3}                                        # consequences come from the enforcer


def test_exclusion_by_allocation_counts_shunned_rounds():
    cfg = cfgb(budget=5.0, T=12)
    res = run_episode(cfg, Shunner(0.25, 0.40, 0.55, tol=-10.0, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    ex = exclusion_by_allocation(res)
    assert any(v > 0 for v in ex.values())
    assert all(not rec.consequences.bans for rec in res.history)
    res2 = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    ex2 = exclusion_by_allocation(res2)
    assert set(ex2) == set(range(res2.n_identities)) and all(v >= 0 for v in ex2.values())
    base = exclusion_by_allocation(res, after_failure=False)
    assert all(base[i] >= ex[i] for i in ex)            # the competition baseline counts at least the post-failure rounds
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ablation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.mechanisms.ablation'`

- [ ] **Step 3: Write the implementation**

```python
# sim/mechanisms/ablation.py
from __future__ import annotations

from dataclasses import replace

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

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        return self.rule.allocate(values_t, offers, view)

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return self.rule.price(assignment, values_t, offers, view)

    def audit(self, assignment, view) -> list[int]:
        return self.rule.audit(assignment, view)

    def bind(self, cfg) -> None:
        self.rule.bind(cfg); self.enforcer.bind(cfg)
        self._enforcer_memory: dict = {}

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        self.rule.enforce(records, view)          # side effects on the rule's memory only; its consequences are discarded
        try:
            return self.enforcer.enforce(records, replace(view, memory=self._enforcer_memory))
        except KeyError as exc:                   # the enforcer's allocate never runs, so its memory holds only what its own enforce wrote
            raise ValueError("an ablation enforcer must not depend on allocation-time memory") from exc

    def describe(self) -> dict[str, str]:
        d = dict(self.rule.describe())
        e = self.enforcer.describe()
        for k in ENFORCEMENT_FIELDS:
            d[k] = e[k]
        return d


def exclusion_by_allocation(res, after_failure: bool = True) -> dict[int, int]:
    """Rounds in which an identity offered, was not banned, and got no job; by default only
    after its first failed audit (spec 8: exclusion through allocation priority). With
    after_failure=False every identity's unserved eligible offers count: the competition baseline."""
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
            eligible = rec.t >= banned_until.get(i, 0) and i not in served
            if eligible and (not after_failure or (i in first_fail and rec.t > first_fail[i])):
                counts[i] += 1
        for i, rounds in rec.consequences.bans.items():
            banned_until[i] = max(banned_until.get(i, 0), rec.t + int(rounds) + 1)
    return counts
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ablation.py -v`
Expected: PASS (3 tests)

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
  - `Family` frozen dataclass: `name`, `knobs: tuple[str, ...]`, `bounds: dict[str, tuple[float, float]]`, `factory`, `dim`; a knob absent from `bounds` is binary (`clip`, and `x` for H3) and is a logistic coordinate thresholded at 0.5; methods `transform(x) -> dict`, `inverse(knobs, near) -> np.ndarray`, `project(knobs) -> dict` (clip forced to 1, every other knob unchanged), `make(knobs) -> Policy` (fresh instance), `corners() -> list[dict]` (all bound corners times every binary knob in {0,1}, de-duplicated), `registered_starts(settings, twin=False) -> list[np.ndarray]` in the registered order near-full-cheat (every coordinate at logit 0.98 except `s` and clip at 0.02), near-honest (every coordinate at logit 0.02 except clip at 0.98), three Sobol; with `twin=True` the first two are swapped. The order matters for searches with fewer than five restarts (the inner tuning search and all-deviators use one): an attack search must start where cheating is reachable, a twin search where truthful profit is positive (a near-zero-effort truthful start scores about 0) (ruling R14), `honest_point() -> dict` (every bounded knob at its lower bound, every binary knob 0 except clip 1: reproduces honest-max).
  - `exact_key(knobs) -> tuple` (exact floats, sorted: the key for the archive, for bank membership, and for candidate de-duplication, so two distinct policies never share an entry or drop each other) and `knob_key(knobs) -> tuple` (rounded to 9 decimals, sorted: for grouping in reports only).
  - `D1`, `D2`, `FAMILIES = {"D1": D1, "D2": D2}`, `embed_d1_in_d2(knobs) -> dict`.
  - `AdaptiveCheat(u0, m0, s, d, r, w, clip)` policy with per-instance markup state.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_families.py
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.policies.families import D1, D2, FAMILIES, embed_d1_in_d2, knob_key, exact_key
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
    cheat = D2.transform(starts[0]); honest = D2.transform(starts[1])      # near-full-cheat first: a one-restart attack search can cheat
    tw = D2.registered_starts(settings, twin=True)
    assert np.array_equal(tw[0], starts[1]) and np.array_equal(tw[1], starts[0]) and all(np.array_equal(a, b) for a, b in zip(tw[2:], starts[2:]))
    assert honest["u0"] == pytest.approx(0.02) and honest["clip"] == 1
    assert cheat["u0"] == pytest.approx(0.98) and cheat["s"] == pytest.approx(0.3 * 0.02) and cheat["clip"] == 0


def test_project_corners_keys_and_honest_point():
    assert D1.project({"u": 0.2, "m": 0.9, "s": 0.0, "w": 0.0, "clip": 0})["clip"] == 1
    corners = D1.corners()
    assert len(corners) == 2 ** 5 and len({knob_key(c) for c in corners}) == len(corners)
    assert len(D2.corners()) == 2 ** 7
    assert knob_key({"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}) == knob_key({"u": 0.5000000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0})
    assert exact_key({"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}) != exact_key({"u": 0.5000000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0})
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


def test_make_returns_fresh_instances():
    k = {"u0": 0.5, "m0": 0.6, "s": 0.2, "d": 0.5, "r": 0.0, "w": 0.0, "clip": 0}
    a, b = D2.make(k), D2.make(k)
    a.act(view(i=0)); a.act(view(i=0, t=1, failed=[1]))
    assert b.act(view(i=0)).offer.claim == pytest.approx(0.7)    # b's state untouched
    assert set(FAMILIES) == {"D1", "D2"}


def test_h3_family_adds_the_exit_knob_and_keeps_honest_max_inside():
    h3 = h3_family(D2)
    assert h3.name == "D2+H3" and h3.knobs == D2.knobs[:-1] + ("x", "clip") and h3.dim == D2.dim + 1
    assert h3.honest_point() == dict(D2.honest_point(), x=0) and len(h3.corners()) == 2 ** 8
    k = {"u0": 0.5, "m0": 0.6, "s": 0.2, "d": 0.5, "r": 0.0, "w": 0.0, "clip": 0}
    wrapped = h3.make(dict(k, x=1)); plain = h3.make(dict(k, x=0))
    assert isinstance(wrapped, IdentityReplacement) and isinstance(plain, AdaptiveCheat)
    assert wrapped.act(view(i=0, t=1, failed=[1])).exit is True and plain.act(view(i=0, t=1, failed=[1])).exit is False
    honest = h3.make(h3.honest_point())
    for t, failed in enumerate(([], [1], [1, 0])):
        assert honest.act(view(i=0, t=t, failed=failed)) == HonestMax().act(view(i=0, t=t, failed=failed))
    starts = h3.registered_starts({"near_corner": 0.02, "sobol_seed": 7})
    assert h3.transform(starts[0])["x"] == 1 and h3.transform(starts[0])["clip"] == 0 and h3.transform(starts[1])["x"] == 0
    assert h3.project(dict(k, x=1))["x"] == 1 and h3.project(dict(k, x=1))["clip"] == 1
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


def exact_key(knobs: dict) -> tuple:
    """Identity of a policy: exact values, sorted by name. Used by the archive, the bank, and candidate
    de-duplication, so two distinct policies never share an entry or drop each other."""
    return tuple(sorted((k, float(v)) for k, v in knobs.items()))


def knob_key(knobs: dict) -> tuple:
    """Rounded key (9 decimals) for grouping in reports only; never for de-duplication."""
    return tuple(sorted((k, round(float(v), 9)) for k, v in knobs.items()))


@dataclass(frozen=True)
class Family:
    name: str
    knobs: tuple[str, ...]            # bounded knobs in order, then the binary knobs, "clip" last
    bounds: dict                      # a knob absent here is binary: a logistic coordinate thresholded at 0.5
    factory: object

    @property
    def dim(self) -> int:
        return len(self.knobs)

    def is_binary(self, k: str) -> bool:
        return k not in self.bounds

    def transform(self, x: np.ndarray) -> dict:
        s = _sigmoid(np.asarray(x, dtype=float))
        out = {}
        for k, v in zip(self.knobs, s):
            if self.is_binary(k):
                out[k] = 1 if v >= 0.5 else 0
            else:
                lo, hi = self.bounds[k]
                out[k] = float(lo + (hi - lo) * v)
        return out

    def inverse(self, knobs: dict, near: float = 0.02) -> np.ndarray:
        """Approximate inverse for search starts only; never use it to evaluate an exact point."""
        x = []
        for k in self.knobs:
            if self.is_binary(k):
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
                k[name] = b if self.is_binary(name) else float(self.bounds[name][b])
            key = exact_key(k)
            if key not in seen:
                seen.add(key); out.append(k)
        return out

    def honest_point(self) -> dict:
        return {k: ((1 if k == "clip" else 0) if self.is_binary(k) else float(self.bounds[k][0])) for k in self.knobs}

    def registered_starts(self, settings: dict, twin: bool = False) -> list[np.ndarray]:
        near = float(settings["near_corner"])
        lo_x, hi_x = _logit(near), _logit(1 - near)
        honest = np.full(self.dim, lo_x); honest[self.knobs.index("clip")] = hi_x
        cheat = np.full(self.dim, hi_x)
        for name in ("s", "clip"):
            if name in self.knobs:
                cheat[self.knobs.index(name)] = lo_x
        sob = qmc.Sobol(d=self.dim, scramble=True, seed=int(settings["sobol_seed"])).random(4)[1:4]
        sobol = [np.array([_logit(float(v)) for v in row]) for row in sob]
        return ([honest, cheat] if twin else [cheat, honest]) + sobol      # a one-restart attack search starts where cheating is reachable; a twin search where truthful profit is positive


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
Expected: PASS (7 tests)

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
  - `run_focal(cell, policy_factory, cache) -> FocalRun` with `profit[len(seeds)]`, `normalized[len(seeds)]` (`profit / (S*/N)`), `inflated_per_seed: np.ndarray[bool]` (any round where the focal claim is strictly greater than its effort; no tolerance, because a projection changes the trajectory for any positive excess), `inflated: bool` (any seed), `results: list[EpisodeResult]`; every other entity plays `HonestMax` unless named in `others`.
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
    fr3 = run_focal(cell, lambda: FixedCheat(u=0.5, m=0.2, s=0.2, w=0.0, clip=0), cache)   # claim == effort exactly: truthful
    assert fr3.inflated is False
    fr4 = run_focal(cell, lambda: FixedCheat(u=0.5, m=0.2 + 1e-13, s=0.2, w=0.0, clip=0), cache)   # any positive excess inflates
    assert fr4.inflated is True


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
    infl = np.array([bool(np.any(r.claims[:, cell.focal] > r.efforts[:, cell.focal])) for r in results])   # nan claims (no offer) compare False
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
- Consumes: `Family`, `exact_key`, `Cell`, `run_focal`, `SeedCache`.
- Produces:
  - `SearchSettings(popsize, sigma0, restarts, evals_per_restart, reeval_every, near_corner, sobol_seed)` and `settings_from_locked(locked) -> SearchSettings`.
  - `ArchiveEntry(knobs, f, per_seed_profit, per_seed_normalized, inflated: bool, source: str)`.
  - `Objective(cell, family, cache, force_clip=False)`: `knobs_of(x) -> dict` (transform, projected when `force_clip`), `eval_knobs(knobs, source="search") -> float` (exact knobs; projected when `force_clip`; records an archive entry keyed by `exact_key`; counts `evals`), `__call__(x) -> float`, `archive: dict[tuple, ArchiveEntry]`, `evals: int`.
  - `best_archived(archive, clip: int, truthful_only: bool = False) -> ArchiveEntry | None` (highest `f`; first inserted wins ties).
  - `cma_search(objective, family, settings, seed, incumbents: dict[str, dict] | None = None, starts: list | None = None) -> SearchResult(best_x, best_knobs, best_f, best_source, restart_bests, evals, trace, incumbent_scores: dict[str, float], projection_f: float, replaced_by_projection: bool, archive: dict)`. After the restarts, every incumbent is evaluated exactly (outside the budget) and replaces the best when higher; then the clip = 1 projection of the best is evaluated exactly (always one evaluation, so the run count is exact) and replaces the best when higher. `objective` must provide `knobs_of`, `eval_knobs`, and `__call__`.
  - `corner_controls(objective, family) -> list[tuple[dict, float]]` through `eval_knobs`, outside the budget.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_search.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig, ProviderParams
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2, knob_key, exact_key
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
    # the optimizer, not only the registered near-full-cheat start (restart 0), reaches the optimum: a Sobol restart gets there
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
    # the archive never merges distinct policies: one ulp of u is a different entry with its own value
    obj.eval_knobs(dict(k, u=0.5 + 1e-12))
    assert len(obj.archive) == 2 and exact_key(dict(k, u=0.5 + 1e-12)) in obj.archive


def test_corner_controls_use_exact_knobs_at_tier_boundaries():
    c = MarketConfig.default()
    providers = (ProviderParams(q_max=0.8, a=0.02, b=0.32, k=6),) + c.providers[6:9]
    cfg = MarketConfig(N=4, J=30, T=5, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=providers, alpha=c.alpha, budget=0.0)
    cache = SeedCache()
    cell = Cell(cfg=cfg, rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=0, seeds=(1,), name="tier")
    obj = Objective(cell, D1, cache)
    ctrl = dict((exact_key(k), f) for k, f in corner_controls(obj, D1))
    honest = D1.honest_point()
    exact = ctrl[exact_key(honest)]
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
from .policies.families import Family, exact_key


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
        key = exact_key(knobs)
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
               incumbents: dict[str, dict] | None = None, starts: list | None = None) -> SearchResult:
    """CMA-ES maximization with registered restarts and a fixed evaluation budget
    per restart (incumbent re-evaluations count). Registered incumbents and the
    projection of the best point are evaluated exactly, outside the budget."""
    if starts is None:
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
  - `twin_search(cell, family, cache, settings, seed) -> SearchResult` (forced clip; near-honest start first; `best_knobs` is the projected point).
  - `attack_search(cell, family, cache, settings, seed, twin: SearchResult) -> SearchResult` with incumbents `twin_best` and `honest_point`.
  - `reference_candidates(cell, family, attack: SearchResult, twin: SearchResult, bank_members: list[dict], order=REFERENCE_ORDER) -> list[Candidate]`: abstention (known 0), honest-max, the twin best (known), the projection of the selected attack (known from the search's projection evaluation), the best archived clip = 1 point (known), the best archived clip = 0 point that never inflated (admitted as its projection with its observed values), and the projection of every bank member; de-duplicated by `exact_key`, first in order wins.
  - `select_reference(cell, candidates, cache) -> ReferenceChoice(candidate, per_seed_profit, per_seed_normalized, scores: dict[str, float])`: highest mean normalized profit on the cell's seeds, ties to the earlier candidate.
  - `evaluate_gain(cell, family, attack_knobs, reference: Candidate, cache) -> GainResult`: runs the attack, the clipped attack, the reference, and honest-max on the cell's seeds; `gain = (profit_attack - profit_ref) / (S*/N)` per seed, `inflation_term = (profit_attack - profit_clip) / (S*/N)`, `selection_term = (profit_clip - profit_ref) / (S*/N)`; gross and net efficiencies; audit cost, audit spend, audited fraction (attack run); harm (accounting and direct); focal served, failures, entry cost, identities; others' profit; enforcement totals of the attack run (refunds, forfeits, hold-backs, spec 4.0 reports refund and forfeit separately); participant diagnostics of the attack run (spec 7): focal audited count and banned rounds, non-focal audited count, non-focal bans (false bans, since non-focal providers are honest-max), non-focal lost capacity (sum over rounds of the capacity of banned non-focal identities).
  - `participant_diagnostics(res, cfg, focal) -> dict`; `seed_rows(cell, g: GainResult, meta: dict) -> list[dict]` and `ROW_FIELDS` (the CSV schema: `meta` keys first, then the metrics).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_reference.py
import numpy as np
import pytest
from sim.cell import SeedCache, Cell, run_focal
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, exact_key
from sim.policies.honest import HonestMax
from sim.reference import (REFERENCE_ORDER, Candidate, twin_search, attack_search, reference_candidates,
                           select_reference, evaluate_gain, seed_rows, ROW_FIELDS)
from sim.search import SearchSettings, Objective


def fixture_cfg(budget=0.0):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=budget)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=40, reeval_every=10, near_corner=0.02, sobol_seed=3)   # two restarts: the near-full-cheat start reaches a cheating attack


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
    assert names[:3] == ["abstain", "honest_max", "twin_search"]          # the attack projection may de-duplicate against the twin
    assert set(names) <= set(REFERENCE_ORDER) | {n for n in names if n.startswith("bank_")}
    assert all(c.knobs is None or c.knobs["clip"] == 1 for c in cands)
    assert len({exact_key(c.knobs) for c in cands if c.knobs}) == len([c for c in cands if c.knobs])
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
        a = att.archive[exact_key(entry.knobs)]
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
    for name in ("refunds_attack", "forfeits_attack", "holdback_in_attack", "refunds_focal_attack", "forfeits_focal_attack", "focal_bans_attack",
                 "focal_audited_attack", "focal_banned_rounds_attack", "others_audited_attack", "others_bans_attack", "others_lost_capacity_attack"):
        assert name in ROW_FIELDS and rows[0][name] == 0       # B1 audits nothing


def test_participant_diagnostics_count_audits_bans_and_lost_capacity():
    from sim.mechanisms.posted_audit import PostedRandomAudit
    c = fixture_cfg(budget=5.0)
    cache = SeedCache()
    cell = Cell(cfg=c, rule_factory=lambda: PostedRandomAudit(0.20, 0.35, 0.50, tol=-10.0, L=2), focal=3, seeds=(1,), name="a")   # every audit fails
    ref = select_reference(cell, [Candidate("honest_max", HonestMax, None)], cache)
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    res = run_focal(cell, HonestMax, cache).results[0]                   # the attack run is honest-max here
    total_audits = int(res.audits.sum())
    assert total_audits > 0 and g.focal_audited_attack[0] + g.others_audited_attack[0] == total_audits
    assert g.others_bans_attack[0] > 0 and g.others_lost_capacity_attack[0] > 0
    assert g.refunds_attack[0] > 0 and g.forfeits_attack[0] == 0 and g.holdback_in_attack[0] == 0
    assert g.refunds_focal_attack[0] <= g.refunds_attack[0] and (g.focal_bans_attack[0] > 0) == (g.focal_banned_rounds_attack[0] > 0)


def test_focal_banned_rounds_ignore_retired_identities():
    from sim.mechanisms.posted_audit import PostedRandomAudit
    from sim.policies.identity import h3_family
    from sim.reference import participant_diagnostics
    c = fixture_cfg(budget=5.0)
    cache = SeedCache()
    cell = Cell(cfg=c, rule_factory=lambda: PostedRandomAudit(0.20, 0.35, 0.50, tol=-10.0, L=50), focal=3, seeds=(1,), name="h3")
    h3 = h3_family(D1)
    res = run_focal(cell, lambda: h3.make(dict(D1.honest_point(), x=1)), cache).results[0]      # exits after every failure
    d = participant_diagnostics(res, c, 3)
    assert res.n_identities > 4 and d["focal_banned_rounds"] <= c.T and d["focal_bans"] >= 1
    # a round-zero exit: the initial and the replacement identity share creation round 0; the replacement is current
    from sim.policies.base import Action
    class ExitFirst:
        name = "exit_first"
        def act(self, view):
            a = HonestMax().act(view)
            return Action(effort=a.effort, offer=a.offer, exit=(view.t == 0))
    c_all = fixture_cfg(budget=50.0)                                                         # every served job is audited and fails
    cell_all = Cell(cfg=c_all, rule_factory=lambda: PostedRandomAudit(0.20, 0.35, 0.50, tol=-10.0, L=50), focal=3, seeds=(1,), name="x0")
    res0 = run_focal(cell_all, ExitFirst, cache).results[0]
    d0 = participant_diagnostics(res0, c_all, 3)
    assert res0.n_identities == 5 and res0.served[0, 3] > 0 and d0["focal_banned_rounds"] == c_all.T - 1   # the replacement is current and banned from round 1
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
from .policies.families import Family, exact_key
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
    starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed}, twin=True)
    return cma_search(Objective(cell, family, cache, force_clip=True), family, settings, seed, starts=starts)


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
    """Every reference candidate in projected form, in registered tie order (spec 5.2); de-duplicated by exact key."""
    n = len(cell.seeds)
    groups: dict[str, list[Candidate]] = {}
    groups["abstain"] = [Candidate("abstain", Abstain, None, np.zeros(n), np.zeros(n))]
    groups["honest_max"] = [Candidate("honest_max", HonestMax, None)]
    tw = family.project(twin.best_knobs)
    groups["twin_search"] = [Candidate("twin_search", _factory(family, tw), tw, **_known(twin.archive.get(exact_key(tw))))]
    proj = family.project(attack.best_knobs)
    groups["attack_projection"] = [Candidate("attack_projection", _factory(family, proj), proj, **_known(attack.archive.get(exact_key(proj))))]
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
            key = exact_key(c.knobs) if c.knobs is not None else ("name", c.name)
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
    refunds_attack: np.ndarray
    forfeits_attack: np.ndarray
    holdback_in_attack: np.ndarray
    refunds_focal_attack: np.ndarray
    forfeits_focal_attack: np.ndarray
    focal_bans_attack: np.ndarray
    focal_audited_attack: np.ndarray
    focal_banned_rounds_attack: np.ndarray
    others_audited_attack: np.ndarray
    others_bans_attack: np.ndarray
    others_lost_capacity_attack: np.ndarray
    seeds: tuple


METRIC_FIELDS = ["seed", "sstar", "gain", "inflation_term", "selection_term", "profit_attack", "profit_clip", "profit_ref",
                 "profit_honest", "eff_attack", "eff_clip", "eff_ref", "eff_honest", "net_eff_attack", "net_eff_ref",
                 "audit_cost_attack", "audit_spend_attack", "audited_fraction_attack", "harm_accounting", "harm_direct",
                 "served_focal_attack", "failures_focal_attack", "entry_attack", "n_identities_attack", "others_profit_attack",
                 "refunds_attack", "forfeits_attack", "holdback_in_attack", "refunds_focal_attack", "forfeits_focal_attack",
                 "focal_bans_attack", "focal_audited_attack", "focal_banned_rounds_attack",
                 "others_audited_attack", "others_bans_attack", "others_lost_capacity_attack"]
ROW_FIELDS = METRIC_FIELDS


def participant_diagnostics(res, cfg, focal: int) -> dict:
    """Spec 7 scripted-participant diagnostics from one episode: audits on the focal entity's identities and on
    the others, bans on the others (false bans: the others are honest-max), rounds the focal entity spent banned,
    and the capacity the others lost while banned (sum over banned identity-rounds of k_i). A ban on a retired
    focal identity does not count: the entity acts through its current identity."""
    ids_f = {i for i, e in enumerate(res.entity_of) if e == focal}
    k_of = [cfg.providers[e].k for e in res.entity_of]
    created = sorted((r, i) for i, (e, r) in enumerate(zip(res.entity_of, res.identity_round)) if e == focal)
    banned_until: dict[int, int] = {}
    out = {"focal_audited": 0, "others_audited": 0, "others_bans": 0, "focal_bans": 0, "focal_banned_rounds": 0, "others_lost_capacity": 0,
           "refunds_focal": float(sum(res.ledger.refunds[:, i].sum() for i in ids_f)),
           "forfeits_focal": float(sum(res.ledger.forfeits[:, i].sum() for i in ids_f))}
    for rec in res.history:
        current = max((i for r, i in created if r <= rec.t), key=lambda i: (res.identity_round[i], res.identity_generation[i]))   # the entity's identity this round
        for i, until in banned_until.items():
            if rec.t < until:
                if i == current:
                    out["focal_banned_rounds"] += 1      # a ban on a retired identity excludes nothing
                elif i not in ids_f:
                    out["others_lost_capacity"] += k_of[i]
        for r in rec.audits:
            out["focal_audited" if r.provider in ids_f else "others_audited"] += 1
        for i, rounds in rec.consequences.bans.items():
            out["focal_bans" if i in ids_f else "others_bans"] += 1
            banned_until[i] = max(banned_until.get(i, 0), rec.t + int(rounds) + 1)
    return out


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
    diag = [participant_diagnostics(r, cell.cfg, f) for r in attack.results]
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
        refunds_attack=np.array([float(r.ledger.refunds.sum()) for r in attack.results]),
        forfeits_attack=np.array([float(r.ledger.forfeits.sum()) for r in attack.results]),
        holdback_in_attack=np.array([float(r.ledger.holdback_in.sum()) for r in attack.results]),
        refunds_focal_attack=np.array([d["refunds_focal"] for d in diag]),
        forfeits_focal_attack=np.array([d["forfeits_focal"] for d in diag]),
        focal_bans_attack=np.array([d["focal_bans"] for d in diag]),
        focal_audited_attack=np.array([d["focal_audited"] for d in diag]),
        focal_banned_rounds_attack=np.array([d["focal_banned_rounds"] for d in diag]),
        others_audited_attack=np.array([d["others_audited"] for d in diag]),
        others_bans_attack=np.array([d["others_bans"] for d in diag]),
        others_lost_capacity_attack=np.array([d["others_lost_capacity"] for d in diag]),
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
Expected: PASS (9 tests)

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
- Produces: `Bank()` with `add(family_name, knobs, origin)`, `members_for(family_name) -> list[dict]` (typed filter: D1 members enter D2 cells through `embed_d1_in_d2`; D2 members never enter D1; the target family's exact corners are members of every cell of that family with origin `corner`, so the 32 D1 corners enter D1 cells and the 128 D2 corners enter D2 cells, spec 8; duplicates removed by `exact_key`), `projected_members_for(family_name) -> list[dict]` (the projection of every compatible member, de-duplicated; what reference selection admits), `evaluate(cell, family, cache, known: dict | None = None) -> list[tuple[dict, float, str]]` sorted by mean normalized profit (members as attacks, unprojected; a member whose exact key is in `known` takes that value without a run, which is how the search stage's corner values are reused), `bank_pass(cell, family, cache, incumbent_f: float, known=None) -> BankPass(ranked, best_knobs, best_f, best_origin, improved)` (the incumbent is replaced when a member scores higher, spec 8), `transfer_rows(cell_name, incumbent_f, bp) -> dict`, `to_json() / from_json(text)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_bank.py
import pytest
from sim.bank import Bank
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2, exact_key


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


def test_typed_filter_corners_projection_and_dedupe():
    b = Bank()
    b.add("D1", {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="B1/D1/0.05")
    b.add("D1", {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="same-again")
    b.add("D1", {"u": 0.5 + 1e-12, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="one-ulp-away")      # a distinct policy, kept
    b.add("D1", {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, origin="is-a-corner")                 # equals a D1 corner: one entry, member origin kept
    b.add("D2", {"u0": 0.1, "m0": 0.2, "s": 0.0, "d": 0.5, "r": 0.1, "w": 0.0, "clip": 1}, origin="B2/D2/0.05")
    d1 = b.members_for("D1"); d2 = b.members_for("D2")
    assert len(d1) == 3 + 32 - 1                          # three distinct D1 members plus the 32 D1 corners, one of them already a member
    assert len(d2) == 3 + 1 + 128 - 1                     # three D1 members embedded, the D2 member, 128 D2 corners; the embedded full cheat is a D2 corner
    assert any(m["d"] == 0.0 and m["u0"] == 0.5 for m in d2)
    p1 = b.projected_members_for("D1"); p2 = b.projected_members_for("D2")
    assert len(p1) == 3 + 16 - 1 and all(m["clip"] == 1 for m in p1)
    assert len({exact_key(m) for m in p2}) == len(p2) and all(m["clip"] == 1 for m in p2)
    b2 = Bank.from_json(b.to_json())
    assert len(b2.members_for("D2")) == len(d2)


def test_bank_pass_replaces_incumbent_when_a_member_or_corner_scores_higher():
    b = Bank()
    b.add("D1", {"u": 0.9, "m": 0.9, "s": 0.0, "w": 0.0, "clip": 0}, origin="cheat")
    b.add("D1", {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}, origin="honest")
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    cache = SeedCache()
    ranked = b.evaluate(cell, D1, cache)
    assert len(ranked) == 1 + 32 and ranked[0][2] == "corner"          # the honest member is itself a corner (de-duplicated, keeps its origin); the full-cheat corner (u = m = 1) wins
    assert sum(1 for _, _, o in ranked if o == "honest") == 1
    runs = cache.runs
    known = {exact_key(m): f for m, f, _ in ranked}
    assert b.evaluate(cell, D1, cache, known=known) == ranked and cache.runs == runs      # known values need no run
    assert ranked[0][1] > ranked[-1][1]
    bp = b.bank_pass(cell, D1, cache, incumbent_f=ranked[-1][1])
    assert bp.improved is True and bp.best_origin == "corner" and bp.best_f == ranked[0][1] and bp.best_knobs["u"] == 1.0
    bp2 = b.bank_pass(cell, D1, cache, incumbent_f=ranked[0][1] + 1.0)
    assert bp2.improved is False
    row = Bank.transfer_rows("c", ranked[-1][1], bp)
    assert row["improved"] is True and row["best_origin"] == "corner"
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
from .policies.families import FAMILIES, Family, embed_d1_in_d2, exact_key


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
        if not any(f == family_name and exact_key(k) == exact_key(knobs) for f, k, _ in self.entries):
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
            key = exact_key(m)
            if key not in seen:
                seen.add(key); out.append((m, origin))
        for c in FAMILIES[target].corners():      # the target family's exact-corner controls are members too (spec 8)
            key = exact_key(c)
            if key not in seen:
                seen.add(key); out.append((c, "corner"))
        return out

    def members_for(self, family_name: str) -> list[dict]:
        return [m for m, _ in self._compatible(family_name)]

    def projected_members_for(self, family_name: str) -> list[dict]:
        fam = FAMILIES[family_name]
        out, seen = [], set()
        for m, _ in self._compatible(family_name):
            p = fam.project(m); key = exact_key(p)
            if key not in seen:
                seen.add(key); out.append(p)
        return out

    def evaluate(self, cell: Cell, family: Family, cache: SeedCache, known: dict | None = None) -> list[tuple[dict, float, str]]:
        """Members as attacks on the cell's seeds; a member whose exact key is in `known` takes that value without a run."""
        known = known or {}
        scored = []
        for m, origin in self._compatible(family.name):
            key = exact_key(m)
            f = known[key] if key in known else float(run_focal(cell, lambda m=m: family.make(m), cache).normalized.mean())
            scored.append((m, f, origin))
        scored.sort(key=lambda t: -t[1])
        return scored

    def bank_pass(self, cell: Cell, family: Family, cache: SeedCache, incumbent_f: float, known: dict | None = None) -> BankPass:
        ranked = self.evaluate(cell, family, cache, known)
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
  - `restart_spread(attack: SearchResult, twin: SearchResult) -> dict` with `attack_bests`, `reference_bests` (the twin's restart bests), `gain_bests` (restart r of the attack minus restart r of the twin: the registered pairing convention), `attack_spread`, `reference_spread`, `gain_spread` (check (c): both objectives and their difference).
  - `FixedClipObjective(objective: Objective, clip: int)`: the same protocol with the clip coordinate fixed.
  - `doubling_check(cell, family, cache, settings, seed, base_attack, base_twin, bank_members, order) -> DoublingCheck(attack_base_f, attack_doubled_f, clip0_f, clip1_f, clip0_search_f, clip1_search_f, ref_base_f, ref_doubled_f, ref_base_name, ref_doubled_name, gain_base, gain_doubled, delta_gain, passed)` (`clip0_search_f` and `clip1_search_f` are the best values the fixed-clip searches found before projection replacement, so the clip diagnostic reads directly): the extra budget equal to the base search is split half and half between a search with clip fixed at 0 and a search with clip fixed at 1 on the same seeds; the doubled attack is the best of the base and the two fixed-clip searches (each already projection-finalized); the reference is selected by the full section 5.2 rule for both the base archive and the merged archive; `passed` when `|delta_gain| < 0.005` (check (b)).
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
    assert dc.clip0_f >= dc.clip0_search_f and dc.clip1_f >= dc.clip1_search_f
    assert dc.delta_gain == pytest.approx(dc.gain_doubled - dc.gain_base) and isinstance(dc.passed, bool)
    assert dc.ref_base_name in REFERENCE_ORDER or dc.ref_base_name.startswith("bank_")
    sp = restart_spread(at, tw)
    assert sp["attack_spread"] >= 0.0 and sp["reference_spread"] >= 0.0 and len(sp["attack_bests"]) == 2
    assert sp["gain_bests"] == [a - r for a, r in zip(sp["attack_bests"], sp["reference_bests"])] and sp["gain_spread"] >= 0.0
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
    """Check (c): attack and reference objectives per restart, reported separately, and their difference
    (restart r of the attack paired with restart r of the twin search: the registered convention)."""
    a, r = list(attack.restart_bests), list(twin.restart_bests)
    g = [x - y for x, y in zip(a, r)]
    return {"attack_bests": a, "reference_bests": r, "gain_bests": g,
            "attack_spread": float(max(a) - min(a)), "reference_spread": float(max(r) - min(r)), "gain_spread": float(max(g) - min(g))}


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
    clip0_search_f: float
    clip1_search_f: float
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
                         clip0_search_f=float(max(c0.restart_bests)), clip1_search_f=float(max(c1.restart_bests)), ref_base_f=rb, ref_doubled_f=rd, ref_base_name=ref_base.candidate.name, ref_doubled_name=ref_doubled.candidate.name,
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
- Produces: `iterated_best_response(cfg, rule_factory, family, cache, settings, seeds, sweeps, seed=0, force_clip=False, eval_seeds=None) -> AllDeviatorsResult(profiles: list[list[dict]], values: list[list[float]], final_profile: list[dict], final_gross_eff: float, final_normalized_profit: list[float], eval_seeds: tuple)`: every provider starts at the family's honest point; in each sweep, each provider in index order searches its best response to the current profile of the others and adopts the result when it scores strictly higher than its current policy on the same seeds (spec 5.3: 3 sweeps, 1 restart x 100 evaluations x 3 dev-train seeds per sweep and provider). With `force_clip` every search is a twin search (the matched truthful procedure, spec 5.3 counts attack and twin). The frozen final profile is evaluated once on `eval_seeds` (dev-val in the sweep, spec 6), which gives `final_gross_eff` and `final_normalized_profit`. `profiles[s][i]` is provider i's knobs after sweep s.

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
    res = iterated_best_response(fixture_cfg(), lambda: PostedPrices(0.20, 0.35, 0.50), D2, cache, settings, seeds=(1,), sweeps=2, eval_seeds=(2, 3))
    assert len(res.profiles) == 2 and all(len(p) == 4 for p in res.profiles)
    assert all(set(k) == set(D2.knobs) for p in res.profiles for k in p)
    assert len(res.values) == 2 and all(np.isfinite(v) for row in res.values for v in row)
    assert res.final_profile == res.profiles[-1] and np.isfinite(res.final_gross_eff) and res.eval_seeds == (2, 3)
    # under B1 without audits every provider gains from cheating: every provider's policy inflates (clip = 0) after sweep 1
    assert all(k["clip"] == 0 for k in res.profiles[0])
    assert cache.runs == 2 * 4 * (16 + 1 + 1) + 2     # per provider and sweep: search, projection, current-value evaluation; final profile on two evaluation seeds


def test_twin_procedure_keeps_every_provider_truthful():
    cache = SeedCache()
    settings = SearchSettings(popsize=8, sigma0=0.3, restarts=1, evals_per_restart=16, reeval_every=10, near_corner=0.02, sobol_seed=3)
    res = iterated_best_response(fixture_cfg(), lambda: PostedPrices(0.20, 0.35, 0.50), D2, cache, settings, seeds=(1,), sweeps=1, force_clip=True)
    assert all(k["clip"] == 1 for k in res.final_profile) and res.eval_seeds == (1,)
    assert all(v > 0.0 for v in res.final_normalized_profit)          # the twin procedure starts near honest, so truthful profit stays positive
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
    eval_seeds: tuple


def iterated_best_response(cfg, rule_factory, family: Family, cache: SeedCache, settings: SearchSettings, seeds,
                           sweeps: int, seed: int = 0, force_clip: bool = False, eval_seeds=None) -> AllDeviatorsResult:
    """Spec 5.3 all-deviators table: iterated best response, every provider on `family`;
    with force_clip the matched truthful (twin) procedure. The frozen final profile is
    evaluated on eval_seeds (dev-val in the sweep)."""
    N = cfg.N
    profile: list[dict] = [family.honest_point() for _ in range(N)]
    profiles, values = [], []
    for s in range(sweeps):
        row = []
        for i in range(N):
            others = tuple((j, (lambda k=profile[j]: family.make(k))) for j in range(N) if j != i)
            cell = Cell(cfg=cfg, rule_factory=rule_factory, focal=i, seeds=tuple(seeds), name=f"all_deviators/{i}", others=others)
            obj = Objective(cell, family, cache, force_clip=force_clip)
            current = obj.eval_knobs(profile[i], source="current")
            starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed}, twin=force_clip)
            res = cma_search(obj, family, settings, seed=seed + s * N + i, starts=starts)
            if res.best_f > current:
                profile[i] = dict(res.best_knobs); row.append(float(res.best_f))
            else:
                row.append(float(current))
        profiles.append([dict(k) for k in profile]); values.append(row)
    ev = tuple(seeds) if eval_seeds is None else tuple(eval_seeds)
    results = run_profile(cfg, rule_factory, [(lambda k=k: family.make(k)) for k in profile], ev, cache)
    eff = float(np.mean([(r.W + r.audit_cost) / r.sstar for r in results]))
    norm = [float(np.mean([r.profit[i] / (r.sstar / N) for r in results])) for i in range(N)]
    return AllDeviatorsResult(profiles=profiles, values=values, final_profile=[dict(k) for k in profile],
                              final_gross_eff=eff, final_normalized_profit=norm, eval_seeds=ev)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_all_deviators.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/all_deviators.py tests/test_all_deviators.py
git commit -m "feat: all-deviators iterated best response with the matched twin procedure and dev-val evaluation"
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
  - `score_point(rule_name, params, cfg, locked, cache, family=D2, inner_override=None, recheck=False) -> TuningScore`: inner scoring searches twin and attack at the inner budget (one restart from the near-full-cheat start: a lower bound on manipulability that can miss small within-tolerance cheats under audited rules; the recheck at the full budget is the measurement that picks the locked winner) on the first `inner_seeds` dev-train seeds, selects the reference last, and scores gain and efficiency on those seeds (`namespace = "dev_train"`); the recheck searches at the full budget on all dev-train seeds, selects the reference there, and scores on the seeds of `locked["tuning"]["recheck_namespace"]` (`namespace = "dev_val"`).
  - `tune(rule_name, cfg, locked, cache, inner_override=None, grid_limit=None) -> TuningResult(best_params, scores, rechecked)`; the locked winner is the rechecked point with the highest dev-val margin.
  - `scripts/tune_baselines.py --calibration experiments/calibration.json --rule B2 --out experiments/tuned/tuned_B2.json [--quick]`. Tuning runs at `beta_headline` and the default rho. The output JSON binds the result: `rule`, `market_key` (from the calibration), `calibration_seeds`, `settings_hash` (Task 1, which covers `beta_headline` and the rho default the tuning ran at), `quick`, `best_params`, `rechecked`, `scores`. A non-quick tuning run refuses a calibration that is not the full calibration namespace. The sweep (Task 13) refuses a tuned file whose `rule`, `market_key`, `settings_hash`, or `calibration_seeds` does not match, or whose `quick` is true.

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
    b1 = score_point("B1", {"P1": 0.20, "P2": 0.35, "P3": 0.50}, cfg, lk, cache, inner_override=QUICK)
    assert b1.gain > 0.0                       # a one-restart inner search starts near full cheat, so B1's manipulability is measured


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
from sim.locked import load_locked, market_config_from_locked, seeds, settings_hash
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
    if not args.quick and list(cal.seeds) != seeds(lk, "calibration"):
        raise SystemExit("tuning for the lock needs the full calibration namespace (pass --quick for a smoke run)")
    cfg = cell_config(market_config_from_locked(lk), cal, rho=float(lk["rho"]["default"]), beta=float(lk["beta_headline"]))
    override = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16, "recheck_restarts": 1, "recheck_val_seeds": 2} if args.quick else None
    res = tune(args.rule, cfg, lk, SeedCache(), inner_override=override, grid_limit=3 if args.quick else None)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"rule": args.rule, "market_key": cal.market_key, "calibration_seeds": list(cal.seeds),
                                          "settings_hash": settings_hash(lk), "quick": bool(args.quick), "best_params": res.best_params,
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

### Task 13: One schedule for the manifest and the staged sweep, records, artifact binding, and the full-path benchmark

**Files:**
- Create: `sim/schedule.py`, `sim/manifest.py`, `sim/records.py`, `scripts/__init__.py` (empty), `scripts/manifest.py`, `scripts/sweep.py`, `scripts/bench_sweep.py`
- Test: `tests/test_manifest.py`, `tests/test_sweep.py`

**Interfaces:**
- Consumes: every earlier task.
- Produces:
  - `sim/schedule.py`: `Budget(restarts, evals, n_train, n_val)`, `budget_from_locked(locked) -> Budget`, `SMOKE_BUDGET = Budget(1, 16, 1, 2)`, `search_runs(b)`, `cell_runs(family_name, b) -> dict[str, int]` with keys `twin, twin_projection, attack, incumbents, attack_projection, reference, corners, evaluation` (exact), `stage_runs(family_name, stage, b)` for the exact stages `search` and `evaluate`, `bank_stage_bound(n_unknown, b) = (n_unknown + 2) * n_train` (members without a known value; the target family's corners are known from the search stage), `reference_bound(n_projected, b) = (1 + n_projected) * n_train`, `doubling_bound(n_projected, b) = 2 * (restarts * (evals // 2) * n_train + n_train) + 2 * reference_bound(n_projected, b)`, `all_deviators_runs(locked, N, b)` (attack and twin procedures, plus both final profiles on dev-val), `tuning_point_runs(locked)`, `tuning_recheck_runs(b)`, `tuning_grid_sizes(locked)`, `bank_members(n_dev_cells_per_family) -> dict` giving per target family `n_unknown` (members without a known value: D1 target the D1 members, D2 target the D1 and D2 members; corners are known) and `n_projected` (D1: D1 members plus 16 projected corners; D2: both member sets plus 64).
  - `sim/manifest.py`: `CellSpec(section, rule, family, beta, rho, position, kind, runs, exact, post_lock, name, params_override)`, `enumerate_manifest(locked, rules, budget=None) -> list[CellSpec]` (sections `development`, `rho_sweep`, `no_ban`, `h3`, `controls`, `all_deviators`, `tuning`, `bank`, and post-lock `bank_post_lock`, `all_deviators_post_lock`, `ablation`), `totals(cells)` by section plus `pre_lock`, `post_lock`, `pre_lock_exact`, `pre_lock_upper_bound`, `cell_name(...)`.
  - `sim/records.py`: `cfg_to_dict / cfg_from_dict`, `search_to_json / search_from_json`, `candidate_to_json / candidate_from_record(family, d)`.
  - `scripts/manifest.py --ms-per-run 45 [--smoke]`.
  - `scripts/sweep.py --stage {search,bank,reference,evaluate,checks,all_deviators,all} --sections ... --rules ... --calibration FILE (--tuned-dir DIR | --smoke) --workers K [--select SUBSTRING] [--limit N] --out DIR`, with `run_stages(opts: dict) -> dict` as the in-process entry point. Every stage writes `DIR/<stage>/<cell>.json` with `runs` (counted after all of the stage's work) and `scheduled` (the exact count or the bound); exact stages (`search`, `evaluate`, `all_deviators`) raise when `runs != scheduled`, bounded stages (`bank`, `reference`, `checks`) raise when `runs > scheduled`. Records carry `params`, `cfg`, `settings_hash`, `budget`, `smoke`, `salt_hash` (sha256 of the identity salt: results with replacement identities depend on it, so a regenerated salt invalidates the records), and the cell name; every record a later stage consumes (search, bank, reference) is checked against the current run, so a smoke record never feeds a real run. The bank stage validates every source record before any member enters the bank; `bank.json` lists its sources with their file hashes and a `bank_hash` over members and sources; every bank record carries that hash; the reference and checks stages refuse a bank record whose hash is not the current bank's, and refuse a bank whose source records changed or disappeared. `load_params` refuses a tuned file whose `rule`, `market_key`, `settings_hash`, or `calibration_seeds` mismatches or whose `quick` is true; without `--smoke` the calibration must use the full calibration namespace. `evaluate` writes `DIR/<section>.csv` with `META_FIELDS + ROW_FIELDS` (`META_FIELDS` ends with `reference`, the selected candidate's name) and `DIR/headline.json`; `bank` writes `DIR/bank.json` and `DIR/transfer.csv`; `checks` writes `DIR/checks.json`; `all_deviators` writes `DIR/all_deviators.json` with the attack and twin procedures and per-provider gain on dev-val.
  - `scripts/bench_sweep.py`: runs every stage in-process (`run_stages` with `--smoke`) for the `beta_headline` median D1 and D2 development cells and the H3 cell of each baseline, sums the recorded `runs`, reports ms per run and the pre-lock manifest in core-hours at that rate, and exits 1 above 20 core-hours.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_manifest.py
import subprocess, sys
import pytest
from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals
from sim.schedule import (Budget, SMOKE_BUDGET, budget_from_locked, cell_runs, search_runs, stage_runs, bank_stage_bound,
                          reference_bound, doubling_bound, tuning_point_runs, tuning_recheck_runs, all_deviators_runs, bank_members)


def test_schedule_arithmetic_is_explicit():
    lk = load_locked(); b = budget_from_locked(lk)
    assert b == Budget(restarts=5, evals=300, n_train=5, n_val=20) and search_runs(b) == 7500
    d1, d2, h3 = cell_runs("D1", b), cell_runs("D2", b), cell_runs("D2+H3", b)
    assert d1 == {"twin": 7500, "twin_projection": 5, "attack": 7500, "incumbents": 10, "attack_projection": 5,
                  "reference": 5, "corners": 32 * 5, "evaluation": 4 * 20}
    assert sum(d1.values()) == 15265 and sum(d2.values()) == 15265 - 160 + 640 and sum(h3.values()) == 15265 - 160 + 1280
    assert stage_runs("D1", "search", b) == 7500 + 5 + 7500 + 10 + 5 + 160 and stage_runs("D1", "evaluate", b) == 80
    assert bank_stage_bound(24, b) == (24 + 2) * 5 and reference_bound(40, b) == 41 * 5
    assert doubling_bound(40, b) == 2 * (5 * 150 * 5 + 5) + 2 * 41 * 5
    assert tuning_point_runs(lk) == 2 * (1 * 100 * 3) + 3 + 6 + 3 + 3 + 4 * 3
    assert tuning_recheck_runs(b) == 2 * 7500 + 5 + 10 + 5 + 5 + 4 * 20
    assert all_deviators_runs(lk, 10, b) == 2 * (3 * 10 * (100 + 2) * 3) + 2 * 20
    m = bank_members(24)
    assert m == {"D1": {"n_unknown": 24, "n_projected": 24 + 16}, "D2": {"n_unknown": 48, "n_projected": 48 + 64}}
    assert all_deviators_runs(lk, 10, SMOKE_BUDGET) == 2 * (3 * 10 * (16 + 2) * 1) + 2 * 2     # the smoke budget caps evaluations and seeds


def test_manifest_totals_follow_the_schedule():
    lk = load_locked()
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    t = totals(cells)
    b = budget_from_locked(lk)
    c1, c2, c3 = (sum(cell_runs(f, b).values()) for f in ("D1", "D2", "D2+H3"))
    assert t["development"] == 24 * c1 + 24 * c2                   # 3 rules x 2 families x (5 + 3) cells
    assert t["rho_sweep"] == 2 * 3 * c2 and t["no_ban"] == 2 * c2 and t["h3"] == 3 * c3
    m = bank_members(24)
    assert t["controls"] == 3 * (doubling_bound(m["D1"]["n_projected"], b) + doubling_bound(m["D2"]["n_projected"], b))
    assert t["all_deviators"] == 3 * all_deviators_runs(lk, 10, b)
    assert t["tuning"] == (27 + 243 + 9) * tuning_point_runs(lk) + 9 * tuning_recheck_runs(b)
    # bank: every pre-lock D1 and D2 full cell is a target (24 D1; 24 + 6 + 2 = 32 D2); bank stage plus the extra reference candidates
    per_d1 = bank_stage_bound(m["D1"]["n_unknown"], b) + m["D1"]["n_projected"] * 5
    per_d2 = bank_stage_bound(m["D2"]["n_unknown"], b) + m["D2"]["n_projected"] * 5
    assert t["bank"] == 24 * per_d1 + 32 * per_d2 == 24 * 330 + 32 * 810
    assert t["ablation"] == 3 * c1 + 3 * c2 and t["all_deviators_post_lock"] == all_deviators_runs(lk, 10, b)
    assert t["bank_post_lock"] > 0
    assert t["pre_lock"] == sum(t[k] for k in ("development", "rho_sweep", "no_ban", "h3", "controls", "all_deviators", "tuning", "bank"))
    assert t["pre_lock"] * 45.0 / 3.6e6 < 20.0                     # the gate at 45 ms per run
    assert t["pre_lock_exact"] + t["pre_lock_upper_bound"] == t["pre_lock"]
    assert {c.section for c in cells if c.post_lock} == {"bank_post_lock", "all_deviators_post_lock", "ablation"}
    assert all(not c.exact for c in cells if c.section in ("bank", "bank_post_lock", "controls"))
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
from sim.locked import load_locked, market_config_from_locked, seeds, settings_hash
from sim.reference import ROW_FIELDS


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


def test_sweep_refuses_unbound_tuned_file_and_partial_calibration(cal_path, tmp_path):
    td = tmp_path / "tuned"; td.mkdir()
    lk = load_locked()
    good = {"rule": "B1", "market_key": json.loads(cal_path.read_text())["market_key"], "settings_hash": settings_hash(lk), "quick": False,
            "calibration_seeds": [4000], "best_params": {"P1": 0.25, "P2": 0.40, "P3": 0.55}}
    (td / "tuned_B1.json").write_text(json.dumps(dict(good, rule="B3")))
    r = run_sweep(cal_path, tmp_path / "r1", "--stage", "search", "--rules", "B1", "--limit", "1", "--tuned-dir", str(td))
    assert r.returncode != 0 and "rule" in (r.stderr + r.stdout)
    (td / "tuned_B1.json").write_text(json.dumps(dict(good, calibration_seeds=[4000, 4001])))
    r = run_sweep(cal_path, tmp_path / "r2", "--stage", "search", "--rules", "B1", "--limit", "1", "--tuned-dir", str(td))
    assert r.returncode != 0 and "calibration seeds" in (r.stderr + r.stdout)   # tuned with another calibration
    (td / "tuned_B1.json").write_text(json.dumps(good))
    r = run_sweep(cal_path, tmp_path / "r3", "--stage", "search", "--rules", "B1", "--limit", "1", "--tuned-dir", str(td))
    assert r.returncode != 0 and "calibration namespace" in (r.stderr + r.stdout)     # one calibration seed is not the full namespace


def test_smoke_sweep_runs_every_stage_with_counted_runs(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development,h3,all_deviators", "--rules", "B1",
                  "--select", "beta0.05_rho0.2_median", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    assert (out / "SMOKE").exists()
    search = {p.stem: json.loads(p.read_text()) for p in (out / "search").glob("*.json")}
    assert {rec["spec"]["family"] for rec in search.values()} == {"D1", "D2", "D2+H3"}
    for stage in ("search", "bank", "reference", "evaluate", "checks"):
        for p in (out / stage).glob("*.json"):
            rec = json.loads(p.read_text())
            assert rec["runs"] == rec["scheduled"] if stage in ("search", "evaluate") else rec["runs"] <= rec["scheduled"]
    assert len(json.loads((out / "checks.json").read_text())) == 2        # D1 and D2 doubling cells at beta_headline, median
    headline = json.loads((out / "headline.json").read_text())
    assert set(headline) == {"B1/D1", "B1/D2"} and all(h["headline"] == "median" for h in headline.values())
    rows = (out / "development.csv").read_text().splitlines()
    assert rows[0] == "cell,section,rule,family,beta,rho,position,smoke,reference," + ",".join(ROW_FIELDS)
    assert len(rows) == 1 + 2 * 2 and (out / "h3.csv").exists()
    ad = json.loads((out / "all_deviators.json").read_text())
    assert len(ad) == 1 and ad[0]["runs"] == ad[0]["scheduled"] and len(ad[0]["gain_dev_val"]) == 10
    assert set(ad[0]) >= {"attack", "twin", "gain_dev_val"}
    # provenance: a changed source record stops the bank stage; a changed bank stops the reference stage
    src = next((out / "search").glob("*D1*.json"))
    rec = json.loads(src.read_text()); rec["params"]["P3"] = 0.99; src.write_text(json.dumps(rec))
    r = run_sweep(cal_path, out, "--stage", "bank", "--rules", "B1", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "differs" in (r.stderr + r.stdout)
    r = run_sweep(cal_path, out, "--stage", "reference", "--rules", "B1", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "bank source" in (r.stderr + r.stdout)
    r = run_sweep(cal_path, out, "--stage", "evaluate", "--rules", "B1", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "bank" in (r.stderr + r.stdout)           # the evaluate stage checks the bank too
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_manifest.py tests/test_sweep.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.schedule'`

- [ ] **Step 3: Write the implementation**

```python
# sim/schedule.py
"""The one place that says how many runs a cell needs. manifest.py sums it; sweep.py executes it
and checks its run counter against it (spec 5.3: the manifest is authoritative). Exact entries are
what the sweep always runs; bounds cover data-dependent work (bank candidates with unknown values)."""
from __future__ import annotations

from dataclasses import dataclass

N_CORNERS = {"D1": 32, "D2": 128, "D2+H3": 256}
N_PROJECTED_CORNERS = {"D1": 16, "D2": 64}


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
    projection, reference selection (honest-max is the only registered candidate without a known value),
    corner controls, and the dev-val evaluation of attack, clipped attack, reference, and honest-max."""
    s = search_runs(b)
    return {"twin": s, "twin_projection": b.n_train, "attack": s, "incumbents": 2 * b.n_train, "attack_projection": b.n_train,
            "reference": b.n_train, "corners": N_CORNERS[family_name] * b.n_train, "evaluation": 4 * b.n_val}


STAGE_KEYS = {"search": ("twin", "twin_projection", "attack", "incumbents", "attack_projection", "corners"),
              "evaluate": ("evaluation",)}


def stage_runs(family_name: str, stage: str, b: Budget) -> int:
    runs = cell_runs(family_name, b)
    return sum(runs[k] for k in STAGE_KEYS[stage])


def bank_stage_bound(n_unknown: int, b: Budget) -> int:
    """Every member without a known value as an attack (corners are known from the search stage),
    plus a re-evaluation and a projection when the incumbent is replaced."""
    return (n_unknown + 2) * b.n_train


def reference_bound(n_projected: int, b: Budget) -> int:
    """Honest-max plus every projected bank member with an unknown value."""
    return (1 + n_projected) * b.n_train


def doubling_bound(n_projected: int, b: Budget) -> int:
    """Two fixed-clip searches at half the budget, each with a projection, plus two reference selections."""
    half = b.restarts * (b.evals // 2) * b.n_train
    return 2 * (half + b.n_train) + 2 * reference_bound(n_projected, b)


def all_deviators_runs(locked: dict, N: int, b: Budget) -> int:
    """Attack and twin procedures (spec 5.3 counts both), each: sweeps x N x (search + projection + current value) x seeds;
    plus both final profiles evaluated on dev-val. The smoke budget caps evaluations and seeds the way sweep.py does."""
    ad = locked["all_deviators"]
    evals = min(int(ad["evals"]), b.evals) * int(ad["restarts"]); seeds = min(int(ad["seeds"]), b.n_train)
    return 2 * (int(ad["sweeps"]) * N * (evals + 2) * seeds) + 2 * b.n_val


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


def bank_members(n_dev_cells_per_family: int) -> dict:
    """Bank composition per target family: members are the best-found attacks of the development cells of each
    family plus the target family's exact corners (known from the search stage, so they cost no bank run);
    D1 members enter D2 through the embedding."""
    m = n_dev_cells_per_family
    return {"D1": {"n_unknown": m, "n_projected": m + N_PROJECTED_CORNERS["D1"]},
            "D2": {"n_unknown": 2 * m, "n_projected": 2 * m + N_PROJECTED_CORNERS["D2"]}}
```

```python
# sim/manifest.py
from __future__ import annotations

from dataclasses import dataclass, asdict

from .schedule import (Budget, all_deviators_runs, bank_members, bank_stage_bound, budget_from_locked, cell_runs,
                       doubling_bound, tuning_grid_sizes, tuning_point_runs, tuning_recheck_runs)


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


def _full_cells(locked: dict, rules: list[str], b: Budget, post_lock: bool) -> list[CellSpec]:
    betas = [float(x) for x in locked["beta_grid"]]; bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"])
    cells: list[CellSpec] = []
    for rule in rules:
        for fam in ("D1", "D2"):
            for beta in betas:
                for pos in (locked["positions"] if beta == bh else ["median"]):
                    cells.append(CellSpec("development", rule, fam, beta, rho0, pos, "full_cell", sum(cell_runs(fam, b).values()), True, post_lock,
                                          cell_name("development", rule, fam, beta, rho0, pos)))
        for rho in [float(r) for r in locked["rho"]["sweep"] if float(r) != rho0]:
            cells.append(CellSpec("rho_sweep", rule, "D2", bh, rho, "median", "full_cell", sum(cell_runs("D2", b).values()), True, post_lock,
                                  cell_name("rho_sweep", rule, "D2", bh, rho, "median")))
        if rule in locked["no_ban_rules"]:
            cells.append(CellSpec("no_ban", rule, "D2", bh, rho0, "median", "full_cell", sum(cell_runs("D2", b).values()), True, post_lock,
                                  cell_name("no_ban", rule, "D2", bh, rho0, "median"), params_override={"L": 0}))
        cells.append(CellSpec("h3", rule, "D2+H3", bh, rho0, "median", "full_cell", sum(cell_runs("D2+H3", b).values()), True, post_lock,
                              cell_name("h3", rule, "D2+H3", bh, rho0, "median")))
    return cells


def _bank_total(cells: list[CellSpec], b: Budget) -> int:
    n_dev = len([c for c in cells if c.section == "development" and c.family == "D1"])
    m = bank_members(n_dev)
    total = 0
    for c in cells:
        if c.kind == "full_cell" and c.family in m:      # targets: every D1 and D2 full cell; controls, tuning, all-deviators rows are not cells
            total += bank_stage_bound(m[c.family]["n_unknown"], b) + m[c.family]["n_projected"] * b.n_train
    return total


def enumerate_manifest(locked: dict, rules: list[str], budget: Budget | None = None) -> list[CellSpec]:
    b = budget or budget_from_locked(locked)
    bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"]); N = int(locked["market"]["N"])
    cells = _full_cells(locked, rules, b, post_lock=False)
    m = bank_members(len([c for c in cells if c.section == "development" and c.family == "D1"]))
    for rule in rules:
        for fam, pos in locked["doubling_cells"]:
            cells.append(CellSpec("controls", rule, fam, bh, rho0, pos, "doubling_check", doubling_bound(m[fam]["n_projected"], b), False, False,
                                  cell_name("controls", rule, fam, bh, rho0, pos)))
        cells.append(CellSpec("all_deviators", rule, "D2", bh, rho0, "all", "iterated_br_attack_and_twin", all_deviators_runs(locked, N, b), True, False,
                              cell_name("all_deviators", rule, "D2", bh, rho0, "all")))
        grid = tuning_grid_sizes(locked)[rule]
        cells.append(CellSpec("tuning", rule, "D2", bh, rho0, "median", "grid_and_recheck",
                              grid * tuning_point_runs(locked) + int(locked["tuning"]["recheck_top"]) * tuning_recheck_runs(b), True, False,
                              cell_name("tuning", rule, "D2", bh, rho0, "median")))
    pre_bank = _bank_total(cells, b)
    cells.append(CellSpec("bank", "all", "D1+D2", bh, rho0, "all", "bank_pass_and_candidates", pre_bank, False, False, "bank_pre_lock"))
    with_proposed = _full_cells(locked, rules + ["proposed"], b, post_lock=True)
    cells.append(CellSpec("bank_post_lock", "proposed", "D1+D2", bh, rho0, "all", "bank_pass_and_candidates",
                          _bank_total(with_proposed, b) - pre_bank, False, True, "bank_post_lock"))
    cells.append(CellSpec("all_deviators_post_lock", "proposed", "D2", bh, rho0, "all", "iterated_br_attack_and_twin",
                          all_deviators_runs(locked, N, b), True, True, cell_name("all_deviators", "proposed", "D2", bh, rho0, "all")))
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
from .policies.families import Family, exact_key
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
    archive = {exact_key(e["knobs"]): ArchiveEntry(knobs=e["knobs"], f=float(e["f"]), per_seed_profit=np.array(e["per_seed_profit"]),
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
        print(f"{k:24s} {t[k]:>12,d} runs  {hours:8.1f} core-hours at {args.ms_per_run:.0f} ms/run")


if __name__ == "__main__":
    main()
```

```python
# scripts/sweep.py
from __future__ import annotations

import argparse, csv, hashlib, json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.all_deviators import iterated_best_response
from sim.bank import Bank
from sim.calibrate import cell_config, load_calibration
from sim.cell import Cell, SeedCache
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash
from sim.manifest import CellSpec, enumerate_manifest
from sim.rng import load_identity_salt
from sim.policies.families import D2, FAMILIES, exact_key
from sim.policies.identity import h3_family
from sim.positions import headline_position, positions
from sim.records import candidate_from_record, candidate_to_json, cfg_from_dict, cfg_to_dict, search_from_json, search_to_json
from sim.reference import ROW_FIELDS, attack_search, evaluate_gain, reference_candidates, seed_rows, select_reference, twin_search
from sim.schedule import SMOKE_BUDGET, Budget, all_deviators_runs, bank_stage_bound, budget_from_locked, doubling_bound, reference_bound, stage_runs
from sim.search import Objective, SearchSettings, corner_controls, settings_from_locked
from sim.search_checks import doubling_check, restart_spread, twin_vs_honest
from sim.tuning import rule_from_params

DEFAULT_PARAMS = {"B1": {"P1": 0.25, "P2": 0.40, "P3": 0.55},
                  "B2": {"P1": 0.25, "P2": 0.40, "P3": 0.55, "tol": 0.12, "L": 10},
                  "B3": {"tol": 0.12, "L": 10}}
STAGES = ("search", "bank", "reference", "evaluate", "checks", "all_deviators")
ALL_FAMILIES = dict(FAMILIES, **{"D2+H3": h3_family(D2)})
META_FIELDS = ["cell", "section", "rule", "family", "beta", "rho", "position", "smoke", "reference"]


def family_of(name: str):
    return ALL_FAMILIES[name]


def load_params(rule: str, tuned_dir: Path | None, smoke: bool, market_key: str, shash: str, cal_seeds) -> dict:
    if tuned_dir is None:
        if not smoke:
            raise SystemExit("refusing to run without tuned parameters: pass --tuned-dir, or --smoke for a smoke run")
        return dict(DEFAULT_PARAMS[rule])
    p = tuned_dir / f"tuned_{rule}.json"
    if not p.exists():
        raise SystemExit(f"tuned parameters for {rule} not found at {p}")
    d = json.loads(p.read_text())
    if d.get("rule") != rule:
        raise SystemExit(f"{p} is a tuning result for rule {d.get('rule')!r}, not {rule}")
    if d.get("market_key") != market_key:
        raise SystemExit(f"{p} was tuned on another market (market_key mismatch)")
    if d.get("settings_hash") != shash:
        raise SystemExit(f"{p} was tuned under other locked settings (settings_hash mismatch)")
    if d.get("quick"):
        raise SystemExit(f"{p} is a quick tuning result and cannot be used for a real run")
    if list(d.get("calibration_seeds", [])) != list(cal_seeds):
        raise SystemExit(f"{p} was tuned with another calibration (calibration seeds differ)")
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
            "budget": [budget.restarts, budget.evals, budget.n_train, budget.n_val], "smoke": smoke, "settings_hash": settings_hash(locked),
            "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest()}


def check_record(job: dict, rec: dict) -> None:
    """A later stage refuses a record from another configuration or mode (stale tuned parameters, calibration,
    settings, budget, or a smoke record under a real run)."""
    for key in ("params", "cfg", "settings_hash", "budget", "smoke", "salt_hash"):
        if rec.get(key) != job[key]:
            raise SystemExit(f"{job['spec']['name']}: stored {key} differs from the current run; rerun from the search stage")
    if rec.get("spec", {}).get("name") != job["spec"]["name"]:
        raise SystemExit(f"{job['spec']['name']}: record belongs to another cell")


def make_cell(job: dict, seeds: tuple[int, ...], suffix: str = "") -> Cell:
    cfg = cfg_from_dict(job["cfg"]); params = job["params"]; rule = job["spec"]["rule"]
    return Cell(cfg=cfg, rule_factory=lambda: rule_from_params(rule, params), focal=positions(cfg)[job["spec"]["position"]],
                seeds=seeds, name=job["spec"]["name"] + suffix)


def train_val(job: dict) -> tuple[tuple[int, ...], tuple[int, ...], Budget]:
    b = Budget(*job["budget"]); lk = job["locked"]
    return tuple(locked_seeds(lk, "dev_train")[: b.n_train]), tuple(locked_seeds(lk, "dev_val")[: b.n_val]), b


def base_record(job: dict, cache: SeedCache, scheduled: int, exact: bool) -> dict:
    if exact and cache.runs != scheduled:
        raise AssertionError(f"{job['spec']['name']}: ran {cache.runs} episodes, schedule says {scheduled}")
    if not exact and cache.runs > scheduled:
        raise AssertionError(f"{job['spec']['name']}: ran {cache.runs} episodes, schedule bound is {scheduled}")
    return {"spec": job["spec"], "cfg": job["cfg"], "params": job["params"], "settings_hash": job["settings_hash"], "smoke": job["smoke"],
            "budget": job["budget"], "salt_hash": job["salt_hash"], "runs": cache.runs, "scheduled": scheduled}


def stage_search(job: dict) -> dict:
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    settings = settings_for(job["locked"], b)
    tw = twin_search(cell, fam, cache, settings, seed=0)
    at = attack_search(cell, fam, cache, settings, seed=1, twin=tw)
    obj = Objective(cell, fam, cache); obj.archive.update(at.archive)
    corners = corner_controls(obj, fam)
    best_corner, best_corner_f = max(corners, key=lambda kf: kf[1])
    if best_corner_f > at.best_f:     # an exact corner control replaces the incumbent when it scores higher (spec 8); its projection is a corner, already evaluated
        proj = fam.project(best_corner); pf = obj.archive[exact_key(proj)].f
        at.best_knobs, at.best_f, at.best_source = (proj, pf, "projection") if pf > best_corner_f else (best_corner, best_corner_f, "corner")
        at.projection_f, at.replaced_by_projection = pf, pf > best_corner_f
        at.best_x = fam.inverse(at.best_knobs, settings.near_corner)      # coordinates follow the selected point (approximate, as for incumbents)
    at.archive = obj.archive
    rec = base_record(job, cache, stage_runs(job["spec"]["family"], "search", b), exact=True)
    rec.update({"twin": search_to_json(tw), "attack": search_to_json(at), "corners": [{"knobs": k, "f": f} for k, f in corners],
                "restart_spread": restart_spread(at, tw), "twin_vs_honest": twin_vs_honest(tw, at.incumbent_scores["honest_point"]).__dict__})
    return rec


def record_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bank(out: Path, search: dict, jobs: dict) -> dict:
    """Every source record is validated before any member enters the bank; the bank document lists its sources with
    their hashes and carries a hash of members and sources, which every bank record and every later stage checks."""
    for name, rec in search.items():
        check_record(jobs[name], rec)
    bank = Bank(); sources = {}
    for name, rec in search.items():
        if rec["spec"]["section"] == "development":
            bank.add(rec["spec"]["family"], rec["attack"]["best_knobs"], origin=name)
            sources[name] = record_hash(out / "search" / f"{name}.json")
    members = json.loads(bank.to_json())
    bank_hash = hashlib.sha256(json.dumps({"members": members, "sources": sources}, sort_keys=True).encode()).hexdigest()
    return {"members": members, "sources": sources, "bank_hash": bank_hash}


def load_bank_doc(out: Path) -> dict:
    """The current bank document, refused when a source record changed or disappeared since the bank was built."""
    doc = json.loads((out / "bank.json").read_text())
    for name, h in doc["sources"].items():
        path = out / "search" / f"{name}.json"
        if not path.exists() or record_hash(path) != h:
            raise SystemExit(f"bank source {name} changed or disappeared since the bank was built; rerun the bank stage")
    expect = hashlib.sha256(json.dumps({"members": doc["members"], "sources": doc["sources"]}, sort_keys=True).encode()).hexdigest()
    if doc["bank_hash"] != expect:
        raise SystemExit("bank.json does not match its hash; rerun the bank stage")
    return doc


def check_bank_record(rec: dict | None, doc: dict | None, stage: str) -> None:
    """A bank or reference record of a D1 or D2 cell must come from the current bank (its hash); H3 records carry no bank."""
    if rec is None:
        return
    needs_bank = rec["spec"]["family"] in FAMILIES
    if rec.get("bank_hash") is None:
        if needs_bank:
            raise SystemExit(f"{rec['spec']['name']}: record carries no bank hash; rerun the bank and reference stages before {stage}")
        return
    if doc is None or rec["bank_hash"] != doc["bank_hash"]:
        raise SystemExit(f"{rec['spec']['name']}: record belongs to another bank; rerun the bank and reference stages before {stage}")


def stage_bank(job: dict, rec: dict, bank_doc: dict) -> dict:
    check_record(job, rec)
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    bank = Bank.from_json(json.dumps(bank_doc["members"]))
    attack = search_from_json(rec["attack"])
    known = {exact_key(c["knobs"]): float(c["f"]) for c in rec["corners"]}          # corner controls were evaluated in the search stage
    n_unknown = sum(1 for m in bank.members_for(fam.name) if exact_key(m) not in known)
    bp = bank.bank_pass(cell, fam, cache, incumbent_f=attack.best_f, known=known)
    if bp.improved:
        obj = Objective(cell, fam, cache); obj.archive.update(attack.archive)
        f = obj.eval_knobs(bp.best_knobs, source=f"bank:{bp.best_origin}")
        proj = fam.project(bp.best_knobs); pf = obj.eval_knobs(proj, source="projection")
        best, best_f, src = (proj, pf, "projection") if pf > f else (bp.best_knobs, f, f"bank:{bp.best_origin}")
        attack.best_knobs, attack.best_f, attack.best_source, attack.archive = best, best_f, src, obj.archive
        attack.projection_f, attack.replaced_by_projection = pf, pf > f
        attack.best_x = fam.inverse(best, settings_for(job["locked"], b).near_corner)
    out = base_record(job, cache, bank_stage_bound(n_unknown, b), exact=False)
    out.update({"bank_hash": bank_doc["bank_hash"], "transfer": Bank.transfer_rows(cell.name, float(rec["attack"]["best_f"]), bp),
                "ranked_top": bp.ranked[:10], "attack": search_to_json(attack), "projected_members": bank.projected_members_for(fam.name)})
    return out


def stage_reference(job: dict, rec: dict, bank_rec: dict | None) -> dict:
    check_record(job, rec)
    if bank_rec is not None:
        check_record(job, bank_rec)
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); twin = search_from_json(rec["twin"])
    members = bank_rec["projected_members"] if bank_rec else []
    cands = reference_candidates(cell, fam, attack, twin, members, tuple(job["locked"]["reference_order"]))
    ref = select_reference(cell, cands, cache)
    out = base_record(job, cache, reference_bound(len(members), b), exact=False)
    out.update({"candidate": candidate_to_json(ref.candidate), "scores": ref.scores, "attack_knobs": attack.best_knobs,
                "attack_f": attack.best_f, "attack_source": attack.best_source, "gain_train": attack.best_f - ref.scores[ref.candidate.name],
                "bank_hash": bank_rec["bank_hash"] if bank_rec else None})
    return out


def meta_of(job: dict, reference_name: str) -> dict:
    s = job["spec"]
    return {"cell": s["name"], "section": s["section"], "rule": s["rule"], "family": s["family"], "beta": s["beta"], "rho": s["rho"],
            "position": s["position"], "smoke": bool(job["smoke"]), "reference": reference_name}


def stage_evaluate(job: dict, ref_rec: dict) -> dict:
    check_record(job, ref_rec)
    _, val, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, val, suffix="/val")
    cand = candidate_from_record(fam, ref_rec["candidate"])
    g = evaluate_gain(cell, fam, ref_rec["attack_knobs"], cand, cache)
    out = base_record(job, cache, stage_runs(job["spec"]["family"], "evaluate", b), exact=True)
    out["rows"] = seed_rows(cell, g, meta_of(job, ref_rec["candidate"]["name"]))
    return out


def stage_checks(job: dict, rec: dict, bank_rec: dict | None, ref_rec: dict) -> dict:
    check_record(job, rec); check_record(job, ref_rec)
    if bank_rec is not None:
        check_record(job, bank_rec)
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); twin = search_from_json(rec["twin"])   # bank-finalized base
    members = bank_rec["projected_members"] if bank_rec else []
    dc = doubling_check(cell, fam, cache, settings_for(job["locked"], b), seed=0, base_attack=attack, base_twin=twin,
                        bank_members=members, order=tuple(job["locked"]["reference_order"]))
    if abs(dc.gain_base - ref_rec["gain_train"]) > 1e-9 or dc.ref_base_name != ref_rec["candidate"]["name"]:
        raise AssertionError(f"{cell.name}: the doubling check's base does not reproduce the reference-stage record")
    out = base_record(job, cache, doubling_bound(len(members), b), exact=False)
    out.update({"doubling": dc.__dict__, "restart_spread": rec["restart_spread"], "twin_vs_honest": rec["twin_vs_honest"]})
    return out


def stage_all_deviators(job: dict) -> dict:
    _, val, b = train_val(job)
    lk = job["locked"]; ad = lk["all_deviators"]; cfg = cfg_from_dict(job["cfg"]); params = job["params"]; rule = job["spec"]["rule"]
    s = settings_from_locked(lk)
    settings = SearchSettings(popsize=s.popsize, sigma0=s.sigma0, restarts=int(ad["restarts"]), evals_per_restart=min(int(ad["evals"]), b.evals),
                              reeval_every=s.reeval_every, near_corner=s.near_corner, sobol_seed=s.sobol_seed)
    seeds = tuple(locked_seeds(lk, "dev_train")[: min(int(ad["seeds"]), b.n_train)])
    cache = SeedCache()
    att = iterated_best_response(cfg, lambda: rule_from_params(rule, params), D2, cache, settings, seeds, sweeps=int(ad["sweeps"]), eval_seeds=val)
    tw = iterated_best_response(cfg, lambda: rule_from_params(rule, params), D2, cache, settings, seeds, sweeps=int(ad["sweeps"]), force_clip=True, eval_seeds=val)
    out = base_record(job, cache, all_deviators_runs(lk, cfg.N, b), exact=True)
    out.update({"attack": att.__dict__, "twin": tw.__dict__,
                "gain_dev_val": [a - t for a, t in zip(att.final_normalized_profit, tw.final_normalized_profit)]})
    return out


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float) + "\n")


def read_dir(path: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(path.glob("*.json"))} if path.exists() else {}


def run_stages(o: dict) -> dict:
    """o: stage, sections, rules, calibration, tuned_dir, smoke, workers, select, limit, out. Returns the totals of recorded runs per stage."""
    lk = load_locked(); cal = load_calibration(o["calibration"]); base = market_config_from_locked(lk)
    budget = SMOKE_BUDGET if o["smoke"] else budget_from_locked(lk)
    rules = o["rules"].split(","); sections = o["sections"].split(",")
    tuned = Path(o["tuned_dir"]) if o.get("tuned_dir") else None
    params = {r: load_params(r, tuned, o["smoke"], cal.market_key, settings_hash(lk), cal.seeds) for r in rules}
    if not o["smoke"] and list(cal.seeds) != locked_seeds(lk, "calibration"):
        raise SystemExit("calibration must use the full calibration namespace for a real run (pass --smoke for a smoke run)")
    out = Path(o["out"]); out.mkdir(parents=True, exist_ok=True)
    if o["smoke"]:
        (out / "SMOKE").write_text("smoke run: DEFAULT_PARAMS and SMOKE_BUDGET; not a result\n")
    manifest = enumerate_manifest(lk, rules, budget=budget)
    stages = STAGES if o["stage"] == "all" else (o["stage"],)
    counted: dict[str, int] = {}
    pool = ProcessPoolExecutor(max_workers=int(o.get("workers", 1)))

    def record(stage: str, rec: dict) -> None:
        counted[stage] = counted.get(stage, 0) + int(rec["runs"])
        write_json(out / stage / f"{rec['spec']['name']}.json", rec)

    for stage in stages:
        if stage == "search":
            jobs = []
            for sec in sections:
                specs = [c for c in manifest if c.section == sec and c.kind == "full_cell" and c.rule in rules
                         and (not o.get("select") or o["select"] in c.name)]
                jobs += [job_for(c, lk, cal, base, params[c.rule], budget, o["smoke"]) for c in specs[: o.get("limit")]]
            for rec in pool.map(stage_search, jobs):
                record("search", rec)
        search = read_dir(out / "search")
        jobs = {name: job_for(next(c for c in manifest if c.name == name), lk, cal, base, params[rec["spec"]["rule"]], budget, o["smoke"])
                for name, rec in search.items()}
        if stage == "bank":
            doc = build_bank(out, search, jobs)
            write_json(out / "bank.json", doc)
            targets = [n for n, r in search.items() if r["spec"]["family"] in FAMILIES]
            for rec in pool.map(stage_bank, [jobs[n] for n in targets], [search[n] for n in targets], [doc] * len(targets)):
                record("bank", rec)
            trows = [json.loads((out / "bank" / f"{n}.json").read_text())["transfer"] for n in targets]
            with open(out / "transfer.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["cell", "incumbent", "best_bank", "best_origin", "improved"]); w.writeheader(); w.writerows(trows)
        bank_recs = read_dir(out / "bank")
        bank_doc = None
        if stage in ("reference", "evaluate", "checks"):
            bank_doc = load_bank_doc(out) if (out / "bank.json").exists() else None
            for n, r in search.items():
                if r["spec"]["family"] in FAMILIES and n not in bank_recs:
                    raise SystemExit(f"{n}: no bank record; run the bank stage before {stage}")
                check_bank_record(bank_recs.get(n), bank_doc, stage)
        refs = read_dir(out / "reference")
        if stage in ("evaluate", "checks"):
            for n, r in refs.items():
                check_bank_record(r, bank_doc, stage)
        if stage == "reference":
            names = list(search)
            for rec in pool.map(stage_reference, [jobs[n] for n in names], [search[n] for n in names], [bank_recs.get(n) for n in names]):
                record("reference", rec)
            refs = read_dir(out / "reference")
        if stage == "evaluate":
            names = list(refs)
            by_section: dict[str, list] = {}
            for rec in pool.map(stage_evaluate, [jobs[n] for n in names], [refs[n] for n in names]):
                record("evaluate", rec)
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
            names = []
            for c in [c for c in manifest if c.section == "controls" and c.rule in rules]:
                n = next((n for n, r in search.items() if r["spec"]["section"] == "development" and r["spec"]["rule"] == c.rule
                          and r["spec"]["family"] == c.family and r["spec"]["position"] == c.position
                          and float(r["spec"]["beta"]) == c.beta and float(r["spec"]["rho"]) == c.rho and n in refs), None)
                if n is not None:
                    names.append(n)
            results = list(pool.map(stage_checks, [jobs[n] for n in names], [search[n] for n in names], [bank_recs.get(n) for n in names], [refs[n] for n in names]))
            for rec in results:
                counted["checks"] = counted.get("checks", 0) + int(rec["runs"])
                write_json(out / "checks" / f"{rec['spec']['name']}.json", rec)
            write_json(out / "checks.json", results)
        if stage == "all_deviators" and (o["stage"] == "all_deviators" or "all_deviators" in sections):
            specs = [c for c in manifest if c.section == "all_deviators" and c.rule in rules]
            adj = [job_for(c, lk, cal, base, params[c.rule], budget, o["smoke"]) for c in specs]
            results = list(pool.map(stage_all_deviators, adj))
            for rec in results:
                counted["all_deviators"] = counted.get("all_deviators", 0) + int(rec["runs"])
            write_json(out / "all_deviators.json", results)
    pool.shutdown()
    return counted


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES + ("all",))
    ap.add_argument("--sections", default="development,rho_sweep,no_ban,h3,all_deviators",
                    help="cell sections for the search stage; the all_deviators stage runs under --stage all only when listed here")
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None)
    ap.add_argument("--smoke", action="store_true", help="DEFAULT_PARAMS and the smoke budget; output marked SMOKE")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--select", default=None, help="only cells whose name contains this substring (search stage)")
    ap.add_argument("--limit", type=int, default=None, help="at most this many cells per section (search stage)")
    ap.add_argument("--out", required=True)
    counted = run_stages(vars(ap.parse_args()))
    print("done: " + ", ".join(f"{k} {v} runs" for k, v in counted.items()))


if __name__ == "__main__":
    main()
```

```python
# scripts/bench_sweep.py
"""The spec 5.3 gate: time every cell stage of sweep.py (search, bank, reference, evaluate, checks) for the
headline median D1, D2, and H3 cells of each baseline at the smoke budget, and extrapolate the pre-lock
manifest. All-deviators is left out so the benchmark mix matches the manifest mix (it is 4% of the manifest
and would be half of the benchmark). Exits 1 above 20 core-hours."""
from __future__ import annotations

import argparse, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bench import cpu_model
from scripts.sweep import run_stages
from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked, seeds
from sim.manifest import enumerate_manifest, totals

GATE_HOURS = 20.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    lk = load_locked(); base = market_config_from_locked(lk)
    with tempfile.TemporaryDirectory() as tmp:
        calp = Path(tmp) / "cal.json"; save_calibration(calibrate(base, seeds(lk, "calibration")[:2]), calp)
        per_rule = {}
        for r in args.rules.split(","):
            t0 = time.perf_counter()
            counted = run_stages({"stage": "all", "sections": "development,h3", "rules": r, "calibration": str(calp), "tuned_dir": None,
                                  "smoke": True, "workers": args.workers, "select": f"beta{lk['beta_headline']}_rho{lk['rho']['default']}_median",
                                  "limit": None, "out": str(Path(tmp) / r)})
            per_rule[r] = (sum(counted.values()), time.perf_counter() - t0)
    runs = sum(n for n, _ in per_rule.values()); secs = sum(s for _, s in per_rule.values())
    ms = 1000.0 * secs / runs
    pre = totals(enumerate_manifest(lk, args.rules.split(",")))["pre_lock"]
    hours = pre * ms / 3.6e6
    for r, (n, s) in per_rule.items():
        print(f"{r}: {n} runs in {s:.1f} s = {1000.0 * s / n:.1f} ms/run")
    print(f"full staged path: {runs} runs in {secs:.1f} s = {ms:.1f} ms/run on {cpu_model()}; pre-lock manifest {pre:,} runs = {hours:.1f} core-hours (gate {GATE_HOURS})")
    sys.exit(0 if hours <= GATE_HOURS else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_manifest.py tests/test_sweep.py -v && uv run python scripts/bench_sweep.py`
Expected: PASS (6 tests). The smoke sweep test runs the B1 headline median D1, D2, and H3 cells through every stage (about 2,500 runs at T = 200), under three minutes with one worker. `bench_sweep.py` prints the ms per run and the extrapolated core-hours, under 20 on an idle machine (rounds 4 and 5 measured 48.6 to 49.6 ms per run blended on an Apple M4 Max, 18.5 to 18.9 core-hours, and 20.1 under load; B3 costs about 86 ms per run because its allocation loop is NumPy-heavy). Run the benchmark on an idle machine and record the figure in Task 14. If the production machine misses the gate, the first optimization is B3's allocation loop in plain Python like B1's; that change is a plan 2B item and does not touch results.

- [ ] **Step 5: Commit**

```bash
git add sim/schedule.py sim/manifest.py sim/records.py scripts/__init__.py scripts/manifest.py scripts/sweep.py scripts/bench_sweep.py tests/test_manifest.py tests/test_sweep.py
git commit -m "feat: one schedule for the manifest and the staged sweep with counted runs, bound artifacts, and a full-path benchmark"
```

---

### Task 14: Spec implementation note, rulings, `families.md`, and README status

**Files:**
- Create: `experiments/families.md`
- Modify: `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (section 3 one sentence; section 7 one insertion; section 14), `README.md` (Status)

- [ ] **Step 1: Write `experiments/families.md`**

```markdown
# Development families D1 and D2 (executable definitions)

Code: `sim/policies/fixed_cheat.py` (D1), `sim/policies/adaptive.py` (D2),
`sim/policies/families.py` (knobs, bounds, transforms, projection, corners,
registered starts), `sim/policies/identity.py` (H3 wrapper and the D2+H3
family).

D1 fixed cheat. Knobs u, m in [0, 1], s in [0, 0.3], w in [0, 2], clip in
{0, 1}. Effort q = q_max (1 - u); claim c = min(1, max(0, q + m - s)); with
clip = 1 the claim is min(c, q); bid = (1 + w)(a + b q). Never abstains or
exits.

D2 adaptive cheat. Knobs u0, m0 in [0, 1], s in [0, 0.3], d in [0, 1], r in
[0, 0.2], w in [0, 2], clip in {0, 1}. State m_t with m_1 = m0; effort
q = q_max (1 - u0); claim as D1 with m_t; after a round with a failed audit
m_{t+1} = m_t (1 - d), otherwise m_{t+1} = min(m0, m_t + r m0); unchanged
during a ban. D2 contains D1 at d = r = 0 (`embed_d1_in_d2`).

D2+H3 (stress test, spec 6.2). D2 plus a binary knob x: with x = 1 the
policy exits in the round after a failed audit and re-enters under a fresh
identity in that round at cost e; with x = 0 it never exits. Its honest
point (x = 0, clip = 1) is honest-max, so the reference is contained.
Reading the H3 table: a rule cannot link a fresh identity to its
predecessor through ids, offer order, tie-break keys, or audited
deliveries (all salted or ordered by id). Two links remain and are
inherent: in a registered H3 cell only the focal entity exits, so the
timing of one identity going silent and one appearing identifies the
newcomer; and the newcomer's offer reflects its provider type, which
with ten distinct provider types identifies the entity. Gains in the H3
table are therefore against rules that could, in principle, treat a
newcomer by timing or by type; the salted channels matter for rules that
would exploit more (several simultaneous exits, identical types).

Transform. Search coordinate in R^dim; bounded knob = lo + (hi - lo)
sigmoid(x); a binary knob (clip, x) is 1 iff sigmoid(x) >= 0.5. Exact
points (corners, the honest point, registered incumbents) are evaluated
from knob dictionaries, never through the inverse transform; the archive
keys points by their exact values.

Registered starts (spec 5.3), in this order for attack searches:
near-full-cheat (logit 0.98 on every coordinate, s and clip at logit
0.02); near-honest (logit 0.02 on every coordinate, clip at logit 0.98);
three scrambled Sobol points with seed `search.sobol_seed` from
`locked.yaml`. Twin searches swap the first two. A search with one
restart (inner tuning, all-deviators) uses the first start only. Honest point: every bounded knob at
its lower bound, every binary knob 0 except clip = 1; it reproduces
honest-max (`tests/test_families.py`).

Projection: clip set to 1, every other knob unchanged. Twins are the
families with clip fixed at 1. Containment tests: `tests/test_families.py`,
`tests/test_reference.py`.
```

- [ ] **Step 2: Edit section 3 and append to section 14 of the spec**

In section 3, step 8, replace the sentence `Exit and re-entry decisions take effect next round.` with: `An exit decision is made in the action of a round in response to the previous round's outcome and takes effect in that round, before offers: the old identity retires, and the fresh identity makes the round's offer and pays e.`

In section 7, Common random numbers, after `No action can change any draw;` insert: `a replacement identity draws its tie-break keys and its delivery noise from its own fixed stream, keyed by its entity's per-round fresh seed, its generation, and the identity salt, so those draws are also action-independent; in H3 cells the attack and the reference runs share every draw except the exiting entity's tie keys and delivery noise after its first exit;`.

Append to section 14:

```
Implementation (plan 2A, version 9 after eight review rounds): identities
separate from entities; a retired identity is not marked in the rule's
view; replacement identities draw tie-break keys from a keyed one-way
BLAKE2b secret of their entity's per-round fresh_seed and their generation
(`identity_secret`, `fresh_tie_keys`), retired ones from a secret of the
round and identity, and same-round entrants are ordered by a salted
per-entity rank; the key is the identity salt in
`experiments/identity_salt.hex` (the development salt) or, for final-eval
runs, an untracked file named by `TOUCHSTONE_IDENTITY_SALT` holding the
final salt, which the separate session generates at the lock, commits by
hash in `locked.yaml` (`identity_salt_sha256`), holds with the final-eval
seeds, and releases with the sealed bundle after the proposed rule is
frozen; `check_claim.py` checks the loaded salt against the commitment.
The salt is a harness secret outside the config a rule may read, so
recovering the episode seed from public values (which is feasible, the
seeds are small) yields no link between a newcomer and its predecessor
through ids, order, tie keys, or audited deliveries. What remains
linkable is the newcomer's offer, which reflects its provider type, and
with ten distinct types that identifies the entity; this is inherent to
the market and is stated here and in `experiments/families.md` for the
reader of the H3 table. Decisions are invariant to relabeling with
re-entry; an exit made in the action of round t takes
effect in round t (section 3 wording updated), which matches Proposition
B; an exited identity's bans and bond keep their schedule as if it had
stayed and stopped serving. Enforcement-ablation adapter
(`sim/mechanisms/ablation.py`): the rule's own enforce runs for its policy
memory and its consequences are discarded, the enforcer has a separate
memory; exclusion-by-allocation count with its competition baseline. D1 and
D2 as families with logistic knob transforms; binary knobs clip and x;
exact points evaluated from knob dictionaries; the archive keys points by
exact value. H3 cells run the family D2+H3 (D2 plus the exit knob x), whose
honest point is honest-max. CMA-ES search with an evaluation archive
(knobs, per-seed values, strict inflation flag); the twin best and the
honest point are registered incumbents of the attack search; the projection
of the best point is always evaluated and replaces it when higher.
Reference candidates in the registered tie order abstention, honest-max,
twin best, attack projection, best archived clip = 1 point, best archived
never-inflated clip = 0 point (as its projection, no new run), projected
bank members; abstention first so a tie at zero profit is labeled
abstention. The bank holds every development cell's best-found attack and
each target family's exact corners. Calibration of S_hat, n_FB, m bound to
the market; every cell derives alpha = rho m and B = beta S_hat; the
calibration seed namespace 4000-4019 is disjoint from dev-train 1000-1004
and dev-val 2000-2019; a real sweep and a non-quick tuning run require the
full calibration namespace. Tuned parameters are bound by rule, market
key, calibration seeds, and a hash of every locked setting; sweep records
are bound by configuration, budget, mode, and cell, and every consumed
record is checked; the lock tooling (plan 2B) copies the tuned files and
the calibration into `locked.yaml` at the lock. Tuning rechecks search on
dev-train and score on dev-val. All-deviators runs the attack and the
matched twin procedure and evaluates both frozen profiles on dev-val.
Doubling check on the bank-finalized attack: the extra budget is split
half and half between clip-fixed searches and the finalized gain is
compared; twin-vs-honest at relative 1%; restart spread reported for the
attack and the reference objectives and their difference. `sim/schedule.py`
is the single source of run counts: exact entries are asserted equal by
`sweep.py`, bounds (bank, reference candidates, controls) are asserted as
upper limits. Manifest at this version, pre-lock: development 744,240;
rho sweep 94,470; no-ban 31,490; H3 49,155; controls 49,680 (bound);
all-deviators 55,200; tuning 310,878; bank 33,840 (bound); total 1,368,953
[the executor replaces these figures with the output of
`scripts/manifest.py` and adds the measured ms per run and core-hours from
`scripts/bench_sweep.py`; rounds 4 to 6 measured 48 to 50 ms per run
blended over every stage on an idle Apple M4 Max, B3 about 86 ms]; these figures supersede the prose totals in
section 5.3 (tuning is 279 grid points, not 3 x 243; corners are counted
per cell and their values are reused in the bank pass; bank and controls
are bounds). Registered start order is near-full-cheat, near-honest,
Sobol for attack searches (twin searches swap the first two), so
one-restart searches (inner tuning, all-deviators) start where cheating,
or truthful profit, is reachable; a one-restart search is a lower bound on
manipulability (it can miss small within-tolerance cheats under audited
rules), which is why the tuning winner is picked by the full-budget
recheck and the all-deviators table is labeled a robustness table; the best exact corner replaces a cell's attack
incumbent when it scores higher, in every cell including H3. Per-seed output rows carry the
section 7 metrics and the section 4.0 refund and forfeit split
(`sim/reference.py::ROW_FIELDS`), and the selected reference's name.
```

- [ ] **Step 3: Update the README status**

Replace the README's `## Status` body with:

```
Week 2. Identities and H3, enforcement-ablation adapter, D1/D2 families,
CMA-ES search with an archive, incumbents and projection replacement, twin
search, reference selection from the bounded projected set, candidate bank
pass, calibration, baseline tuning with dev-val rechecks, all-deviators
with its twin procedure, search checks, schedule-driven manifest, staged
sweep runner with counted runs, and the full-path benchmark implemented.
Plan 2B (intervals, coverage study, claim script, lock tooling, model
actors, custodian instructions) next.
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

**Spec coverage for this plan's scope.** Section 3 identity replacement, entry cost, exit timing (sentence updated in Task 14): Task 2. Section 3 calibration constants and configuration validity: Task 9. Section 4.0 identity opacity and relabeling invariance with re-entry: Task 2 (`test_rule_view_does_not_reveal_exit_or_successor`, parametrized `test_relabeling_with_reentry_relabels_decisions`); refund and forfeit split: Task 7. Section 4.1 no-ban diagnostic: Task 13 (`no_ban` section). Section 4.2 tuning grid, inner search, objective, dev-val recheck: Task 12. Section 5.1 views with identity: Task 2. Section 5.2 honest-max, twin, abstention, every discovered admissible truthful candidate in projected form from the archive and the bank, reference selected last after the bank pass, incumbent replacement by the projection, twin and honest-max incumbents, containment (including the H3 family's honest point): Tasks 4, 6, 7, 8, 13. Section 5.3 D1/D2 with recurrence and domains, transforms, registered starts, search budget, incumbent re-evaluation, exact corners, positions, headline selection, search checks (a) to (d) with both objectives and their difference, all-deviators with attack and twin, workload manifest with exact entries and bounds, full-path gate: Tasks 4, 6, 10, 11, 13. Section 6 `locked.yaml` contents, `families.md`, seed namespaces, artifact binding: Tasks 1, 12, 13, 14. Section 6.2 H3: Tasks 2, 4, 13 (`h3` section over D2+H3). Section 7 reference run, gain per entity, clipped-attack run, efficiency quadruple, audit spend, harm, participant diagnostics, per-seed rows: Tasks 2, 7, 13. Section 8 enforcement-ablation adapter with retained policy memory and exclusion count, candidate bank with corners: Tasks 3, 8, 13. Section 12 pre-lock tests (honest-max equals its twin; honest-max gain exactly 0 under an honest-max reference; twin candidate as attacker reproduces its trajectory): Tasks 4, 7. Not in this plan, by the stated split: interval algorithms, coverage study, `check_claim.py`, hashes and lock tooling (which also writes `tuned` and `calibration` into `locked.yaml`), the model-actor harness, `describe()` rendering, the custodian bundle, `plot.py`, and the post-lock runs against a proposed rule.

**Placeholder scan.** One deliberate placeholder: the manifest and benchmark figures in Task 14 Step 2 are copied from the scripts' output at execution time, and the sentence says so.

**Type consistency.** `Family.transform/inverse/project/make/corners/honest_point/registered_starts/is_binary`, `knob_key`, `exact_key`; `h3_family(family)`; `load_identity_salt`, `identity_secret(salt, seed, t, fresh_seed_e, generation)`, `retired_secret(salt, seed, t, identity)`, `entrant_rank(salt, seed, t, fresh_seed_e)`, `replacement_noise(salt, seed, t, fresh_seed_e, generation, kmax, sigma)`, `fresh_tie_keys(secrets, J)`; `Draws.fresh_seed`; `run_episode(..., identity_salt=None)`; `EpisodeResult.identity_generation`; `EnforcementAblation`, `exclusion_by_allocation(res, after_failure)`; `Cell(cfg, rule_factory, focal, seeds, name, others=())`; `run_profile`; `run_focal -> FocalRun(profit, normalized, inflated_per_seed, inflated, results)`; `Objective` with `knobs_of/eval_knobs/__call__/archive/evals`; `best_archived(archive, clip, truthful_only)`; `cma_search(objective, family, settings, seed, incumbents, starts) -> SearchResult(best_x, best_knobs, best_f, best_source, restart_bests, evals, trace, incumbent_scores, projection_f, replaced_by_projection, archive)`; `corner_controls`; `twin_search`, `attack_search(..., twin)`; `reference_candidates(cell, family, attack, twin, bank_members, order)`; `select_reference -> ReferenceChoice(candidate, per_seed_profit, per_seed_normalized, scores)`; `evaluate_gain(cell, family, attack_knobs, reference: Candidate, cache) -> GainResult`; `participant_diagnostics`, `seed_rows`, `ROW_FIELDS`; `Bank.add/members_for/projected_members_for/evaluate/bank_pass/transfer_rows/to_json/from_json`; `calibrate(cfg_base, seeds) -> Calibration(S_hat, n_FB, m, market_key, T, seeds)`, `cell_config`, `load_calibration`, `save_calibration`; `settings_hash(locked)`; `positions`, `headline_position`; `restart_spread(attack, twin)` with `gain_bests`, `FixedClipObjective`, `doubling_check(...) -> DoublingCheck(... clip0_search_f, clip1_search_f ...)`, `twin_vs_honest(twin, honest_f)`; `iterated_best_response(cfg, rule_factory, family, cache, settings, seeds, sweeps, seed, force_clip, eval_seeds) -> AllDeviatorsResult(..., eval_seeds)`; `score_point`, `tune`; `Budget`, `cell_runs`, `stage_runs`, `bank_stage_bound`, `reference_bound`, `doubling_bound`, `bank_members`, `all_deviators_runs`; `enumerate_manifest(locked, rules, budget)`, `totals`; `search_to_json/search_from_json`, `candidate_from_record`; `run_stages(opts)`.

**Review Focus.** Item 1: Task 2 `test_rule_view_does_not_reveal_exit_or_successor`, `test_relabeling_with_reentry_relabels_decisions`. Item 2: Task 2 `test_banned_identity_can_still_exit_and_fresh_identity_is_not_banned`, `test_exit_does_not_change_ban_or_bond_schedule`. Item 3: Task 4 `test_make_returns_fresh_instances`. Item 4: Task 6 `test_flat_objective_terminates_and_counts`, Task 7 `test_abstention_wins_when_everything_loses_money`. Item 5: Task 6 `test_corner_controls_use_exact_knobs_at_tier_boundaries`. Item 6: Task 7 `test_gain_on_other_seeds_subtracts_reference_on_those_seeds`. Item 7: Task 9 `test_cell_config_refuses_foreign_calibration`, Task 13 `test_sweep_refuses_untuned_run_without_smoke_flag`, `test_sweep_refuses_unbound_tuned_file_and_partial_calibration`.

**Rulings carried in this plan (for the executor's ledger and the spec note):** (R1) exits take effect in the round the policy makes them, and the section 3 sentence is updated; (R2) retired identities are not marked in the view; (R3) abstention is first in the registered candidate order; (R4) the twin search has no incumbents so that check (d) stays a diagnostic; (R5) the projection of the best point is always evaluated so the exact schedule entries stay exact; (R6) the H3 cell is a full cell over D2+H3 (D2 plus the exit knob x), whose honest point is honest-max; (R7) bank members come from development cells plus each target family's corners, and the bank pass targets every D1 and D2 cell including rho-sweep and no-ban cells; (R8) tuning runs at `beta_headline` and the default rho; (R9) the doubling check gives each clip-fixed search half of one extra base budget and starts from the bank-finalized attack; (R10) a calibration seed namespace exists next to the three of section 6; (R11) before the lock, tuned files and the calibration are bound to the market key and the settings hash, and the lock tooling of plan 2B writes them into `locked.yaml`; (R12) the all-deviators gain is the per-provider difference between the attack profile and the twin profile on dev-val; (R13) same-round entrants get ids in the order of a salted per-entity secret rank, so the order is unavailable to a rule even with the episode seed; (R14) the registered start order is near-full-cheat, near-honest, three Sobol for attack searches and near-honest, near-full-cheat, three Sobol for twin searches, so a one-restart attack search can reach a cheating point and a one-restart twin search starts where truthful profit is positive; (R15) the best exact corner control replaces a cell's attack incumbent when it scores higher, in every cell including H3, and the bank pass reuses the corner values of the search stage.
