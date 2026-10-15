# Touchstone plan 2B (version 1): intervals, coverage study, model actors, describe renderer, claim check, lock tooling, plots, custodian instructions

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete every pre-lock deliverable the spec names after plan 2A: the locked interval algorithms, the coverage study with its joint fixture test and power check, the model-actor harness (LLM and the Jev decision model) with the `describe()` renderer, vocabulary, comprehension fixture, and the H1 five-episode procedure, the token pilot, `check_claim.py` with the predicate and the lock and freeze hash checks, the lock script, the figures, and the custodian instructions for the separate session, so that the lock on 2026-10-28 can be cut from a repo in which every tool the post-lock weeks need already exists and is frozen.

**Architecture:** Statistics live in pure functions over numpy arrays (`sim/intervals.py`, `sim/coverage.py`) with the market work behind them produced by the plan 2A cell runners and recorded by the schedule. The model actor is a `Policy` whose decisions come from a `Backend` behind a prompt-hash cache: an Anthropic backend (structured JSON output), a Jev backend (typed Choice questions over a discretized action menu), and a fake backend for tests; the H1 procedure, fallback accounting, invalidity rule, and the closed-loop clipped re-run live in `sim/llm_actor.py` and never touch the market loop. The `describe()` record is validated against `experiments/vocabulary.yaml` and rendered by one frozen template. `scripts/check_claim.py` is the only reader of final results: it verifies hashes against the lock and freeze tags, admits bounds the coverage study admitted, and evaluates the predicate. `scripts/lock.py` writes the lock-time blocks into `locked.yaml` and prints the tag command for the author to sign.

**Tech Stack:** Python 3.12+, numpy, scipy (stats: t, nct, skew, bootstrap helpers written here), pandas and matplotlib for figures, `anthropic` SDK (`claude-opus-5-5` by default, pinned snapshot id recorded in `locked.yaml`), `typesafe-sdk` for Jev (`jev-1.14.0`), pyyaml, pytest. No network in tests: both real backends are exercised only through the fake backend and recorded fixtures.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5 plus the plan 1 and plan 2A implementation notes). This plan implements sections 5.4 (LLM actor, describe renderer, comprehension fixture, H1 procedure, token pilot), 6 (lock contents, allow-list, hash checks, freeze, repairs), 6.1 (what the sealed bundle must contain, as instructions to the separate session), 8 (interval algorithms, coverage study, joint fixture test, power, pre-registered consequences, claim predicate, decision rule, figures), 11 (layout: `llm_actor.py`, `policies/llm.py`, `vocabulary.yaml`, `coverage_study.py`, `plot.py`, `check_claim.py`, `sealed/`), 12 (the remaining tests), and 13 (the gate for 10-18 to 10-28). It also folds the deferred minors of the plan 2A final review that touch frozen files.

**Scope split, stated once:** Plan 2B ends when `scripts/check_claim.py --verify-lock` passes on a lock-candidate tree, `scripts/coverage_study.py` runs end to end at a smoke size and at the registered size from the manifest, the model actor runs the H1 procedure against B1 to B3 with the fake backend and with cached real responses, the token pilot script exists and has been run once per backend by the user, `scripts/plot.py` draws figures 1 and 2 from the sweep CSVs, and `docs/custodian.md` tells the separate session exactly what to produce. The proposed rule, the sealed H1 prompt and H2 definition, and every post-lock run are outside this plan.

**Design decisions in this plan (rulings for the executor's ledger and the spec note):** (D1) Jev is a second model backend behind the same actor interface as the LLM, with the action space discretized into a registered menu (effort levels and claim offsets as Choice questions); it is a development-side actor for the model-actor table, not a held-out family, because H1 is defined as the sealed LLM. (D2) The coverage study draws its reference pools and replications from a dedicated contiguous seed range `seeds.coverage` (start 3,000,000), disjoint from dev-train, dev-val, calibration, and the custodian's final-eval range, because the 20-element dev-val list cannot supply 35,000 seeds per cell; the spec note records this as the dev-val namespace's coverage sub-range. (D3) The prompt cache is a content-addressed directory of JSON files keyed by the SHA-256 of the canonical request, committed under `experiments/cache/` for the development runs and under `sealed/` for H1, so replay is byte-identical without the network. (D4) Fallback rounds are counted per repetition and the invalidity rule (more than 5% fallback rounds) marks the repetition; the statistic always includes all 10 repetitions. (D5) `check_claim.py` reads the admitted-sides table from the coverage report by (statistic, side, level, n) and refuses a clause whose needed side is absent. (D6) The lock script writes `tuned`, `calibration`, `coverage_report_sha256`, `sealed_bundle_sha256`, `h1` (budget, cost cap, model ids), and `intervals` into `locked.yaml`, and prints the `git tag -s` command; the salt commitment is written by the separate session. (D7) T = 100 for every H1 run with its own calibration (`scripts/calibrate.py --T 100`), as the spec says S_hat, B, and the twin are calibrated at T = 100. (D8) The coverage study's run count is the real one: every pool seed and every replication seed needs the attack, the clipped attack, and the reference run under the cell's rule plus the attack and clipped runs under the B2/B3 pair for the loss-difference endpoint (4 to 7 episodes per seed), and the replications draw fresh seeds as the spec requires (220,000 per cell), so the study is about 6 x 255,000 x (4 to 7) = 6 to 11 million episodes, 50 to 90 core-hours at the benchmark rate, listed in the manifest outside the search gate; the spec's figure of about 210,000 runs counted one episode per pool seed and no replication seeds and is superseded by the manifest. The registered design (M, R, endpoints, thresholds) is unchanged; a cheaper variant (replications resampled from the pool) is not used because it would make the replications dependent on the reference mean. The study runs once, in the background, over a day on 8 cores; `--smoke` exists for development.

## Global Constraints

- Every plan 1 and plan 2A constraint remains; frozen modules are not changed except where this plan names the file and the reason (`scripts/sweep.py` gains an evaluation-namespace option and per-seed reference values in its records; `sim/calibrate.py` gains a zero-division guard; `sim/market.py` gains one comment).
- Interval algorithms (spec 8): percentile bootstrap on the per-seed paired statistic, 10,000 resamples, seed as the resampling unit, one-sided; identical per-seed values give the bound equal to that value and a `degenerate` flag; studentized bootstrap-t with each resample studentized by its own standard error, a zero-standard-error resample using the full-sample standard error; H1 bound: one-sided t on 10 repetitions; reference-mean interval: two-sided t at 95%. All resampling is seeded from `locked.yaml` (`intervals.bootstrap_seed`).
- Coverage study (spec 8): 6 cells by the mechanical rule (top 3 skewness of per-seed gain, top 3 Sarle bimodality of per-seed ban counts, dev-train seeds, degenerate inputs excluded, ties and overlaps filled from the other ranking); M = 35,000 reference seeds per cell; R = 2,000 replications per (cell, endpoint, n) and 4,000 at n = 40, each from a fresh disjoint sub-range; eight endpoints; conservative scoring against the 95% reference interval; analytic thresholds from the noncentral t with margins 2.0 points at 95% and 1.0 point at 98.75%; joint fixture test of 200 trials with the Clopper-Pearson lower limit at level 1 - 0.05/3 of at least 0.9 (190 of 200); power against the negative control (deficit 3 points at 95%, 1.5 at 98.75%) by Gauss-Hermite quadrature with 200 nodes checked against 400 to within 0.001, rejection probability at least 0.8; remedy order double M, then double R; procedure remedy order percentile, studentized, then 40 seeds studentized.
- Claim predicate (spec 8): rule clause at 95% (gross efficiency lower bound >= 0.90, gain upper bound <= 0.30, total audit cost <= B on every seed); baseline clause at 98.75% (for each of B2 and B3, some confirmatory family with inflation-caused loss difference lower bound >= 0.05 or gain lower bound >= 1.0); PASS, FAIL, INCONCLUSIVE per clause and overall; thresholds read from `locked.yaml`.
- H1 procedure (spec 5.4): provider role only; JSON schema with effort in [0, q_max] and an offer (claim, bid) or abstain; no exit; twin is the same actor with the claim clipped by the harness; temperature 0 (`output_config.effort` low and no sampling parameters on the Anthropic side, which rejects `temperature`; the request is pinned and cached, so replay is deterministic); every request and response cached by prompt hash; malformed response falls back to honest-max for that round and is counted; more than 5% fallback rounds in a repetition marks it invalid; more than 2 of 10 invalid makes the cell INCONCLUSIVE; 5 episodes of T = 100 with profit feedback between episodes; episodes 1 to 4 on dev-train seeds, episode 5 on one evaluation seed; 10 repetitions with 10 evaluation seeds; the closed-loop clipped re-run applies the clip in episode 5 only, replays matching prompts from cache, and counts new calls; scope beta in {0.02, 0.05, 0.10}, median position, one rho.
- Describe renderer (spec 5.4): every `describe()` field value in the vocabulary or `"not expressible"`; one frozen template renders the record to prose; the renderer receives only the record (renderer spy test); changing source comments and identifiers leaves the rendered bytes unchanged.
- Lock (spec 6): `locked.yaml` with every listed block; `families.md`; `check_claim.py` refuses a run if any tracked file differs from the lock tag except the allow-list (`sim/mechanisms/proposed.py`, its config, its `describe()` record, `scripts/plot.py`, `docs/`, `sealed/`, `sealed/patches/`); after the freeze, allow-listed files compared to the freeze tag, `sealed/` to the bundle hash, patches to their logged hashes, new tracked files outside the allow-list refused; `proposed.py` imports only `sim/mechanisms/base.py` and standard numerical libraries and leaves frozen modules' attributes unchanged.
- Model ids are pinned in `locked.yaml` (`h1.model: claude-opus-5-5`, `h1.jev_model: jev-1.14.0`); the Anthropic client is the official SDK; the Jev client is `typesafe-sdk`; neither is imported at module load by any frozen module except behind the backend factory.

## Review Focus

1. A per-seed statistic with all values identical gives a bootstrap bound equal to that value and a degenerate flag, and never a NaN. Task 2, `test_percentile_bootstrap_degenerate_when_all_values_equal`.
2. A studentized resample with zero standard error uses the full-sample standard error and the bound stays finite. Task 2, `test_studentized_bootstrap_zero_se_resample_uses_full_sample_se`.
3. A cell whose ban counts have zero variance is excluded from the bimodality ranking, and an exhausted ranking is filled from the other, so exactly 6 distinct cells are always selected. Task 5, `test_cell_selection_handles_degenerate_rankings`.
4. A malformed model response (invalid JSON, out-of-range effort, claim above 1) falls back to honest-max for that round, is counted, and the episode continues with the same seeds. Task 4, `test_malformed_response_falls_back_and_is_counted`.
5. Clipping in episode 5 changes a later prompt, so the clipped re-run makes a new call for that prompt and replays every unchanged prompt from cache. Task 4, `test_clipped_rerun_replays_cache_and_counts_new_calls`.
6. A `describe()` record with a field outside the vocabulary is refused at load, and a record using "not expressible" marks H1 INCONCLUSIVE for that rule. Task 3, `test_vocabulary_refuses_unknown_values`, Task 7, `test_not_expressible_record_makes_h1_inconclusive`.
7. `check_claim.py` refuses a result file whose settings hash, salt hash, or tuned-file hashes differ from the lock, and refuses a tracked file changed since the lock tag unless it is on the allow-list. Task 7, `test_check_claim_refuses_modified_frozen_file`, `test_check_claim_accepts_allow_listed_changes_after_freeze`.

---

### Task 1: Dependencies, the coverage seed range, lock-time blocks in `locked.yaml`, sweep record additions, and the deferred plan 2A minors

**Files:**
- Modify: `pyproject.toml` (add `pandas>=2.2`, `matplotlib>=3.9`, `anthropic>=1.0`, `typesafe-sdk>=0.3`), `experiments/locked.yaml` (new blocks), `scripts/sweep.py` (per-seed reference values in records; `--eval-namespace`; clear error on a foreign record), `sim/calibrate.py` (zero-division guard), `sim/market.py` (one comment), `sim/search.py` (silence the cma import warning), `tests/test_locked.py`, `tests/test_sweep.py`, `tests/test_calibrate.py`
- Test: the updated tests

**Interfaces:**
- Produces:
  - `locked.yaml` gains `seeds.coverage: {start: 3000000, block: 600000, pool: 35000, replications: {"10": 2000, "20": 2000, "40": 4000}, n_grid: [10, 20, 40]}` (one block of 600,000 seeds per selected cell: room for the pool and the replications with both doublings), `intervals: {bootstrap_resamples: 10000, bootstrap_seed: 20261111, h1_repetitions: 10, reference_level: 0.95, margins: {"0.95": 2.0, "0.9875": 1.0}, deficits: {"0.95": 3.0, "0.9875": 1.5}, joint_trials: 200, joint_min_admitted: 190, quadrature_nodes: 200, remedy_order: [percentile, studentized, studentized_n40]}`, `h1: {model: claude-opus-5-5, jev_model: jev-1.14.0, T: 100, episodes: 5, repetitions: 10, betas: [0.02, 0.05, 0.10], fallback_limit: 0.05, invalid_limit: 2, cost_cap_usd: null, calls_cap: 192000}`, `claim: {beta: 0.05, eff_min: 0.90, gain_max: 0.30, loss_diff_min: 0.05, baseline_gain_min: 1.0, rule_level: 0.95, baseline_level: 0.9875}`, `allow_list: [sim/mechanisms/proposed.py, experiments/proposed.yaml, experiments/proposed_describe.yaml, scripts/plot.py, docs/, sealed/, sealed/patches/]`, `calibration: null`, `sealed_bundle_sha256: null`, `coverage_report_sha256: null`, `comprehension_fixture_sha256: null`.
  - `sweep.py` reference records carry `attack_per_seed_normalized` and `reference_per_seed_normalized` (dev-train) and `reference_per_seed_profit`; `--eval-namespace {dev_val,final_eval}` selects the evaluation seeds of the `evaluate` stage (default `dev_val`; `final_eval` refuses to run unless the namespace is present in `locked.yaml`, which happens only after the unseal); a record whose rule is not in the current `--rules` raises `SystemExit` naming the rule.
  - `calibrate` raises `ValueError("no job has positive first-best surplus")` when `n_FB == 0`.
  - `EpisodeResult.efforts` comment states that efforts are recorded in banned rounds too.
  - `sim/search.py` imports `cma` inside `warnings.catch_warnings()` filtering the matplotlib `UserWarning`, so scripts print nothing from cma.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_locked.py`:

```python
def test_locked_has_plan_2b_blocks_and_coverage_range_is_disjoint():
    lk = load_locked()
    cov = lk["seeds"]["coverage"]
    assert cov["start"] == 3_000_000 and cov["pool"] == 35_000 and cov["replications"] == {"10": 2000, "20": 2000, "40": 4000} and cov["n_grid"] == [10, 20, 40]
    assert cov["block"] >= 2 * cov["pool"] + 2 * sum(int(r) * int(n) for n, r in cov["replications"].items())   # room for both doublings
    lo, hi = cov["start"], cov["start"] + 6 * cov["block"]
    for ns in ("dev_train", "dev_val", "calibration"):
        assert all(not (lo <= s < hi) for s in seeds(lk, ns))
    assert lk["intervals"]["bootstrap_resamples"] == 10_000 and lk["intervals"]["margins"] == {"0.95": 2.0, "0.9875": 1.0}
    assert lk["h1"]["model"] == "claude-opus-5-5" and lk["h1"]["jev_model"] == "jev-1.14.0" and lk["h1"]["T"] == 100
    assert lk["claim"]["eff_min"] == 0.90 and lk["claim"]["gain_max"] == 0.30 and lk["claim"]["baseline_level"] == 0.9875
    assert "sim/mechanisms/proposed.py" in lk["allow_list"] and "sealed/" in lk["allow_list"]
    assert lk["calibration"] is None and lk["sealed_bundle_sha256"] is None
    h = settings_hash(lk)
    filled = dict(lk); filled["calibration"] = {"S_hat": 1.0}; filled["sealed_bundle_sha256"] = "ab" * 32
    filled["coverage_report_sha256"] = "cd" * 32; filled["comprehension_fixture_sha256"] = "ef" * 32; filled["coverage_consequences"] = {"final_eval_n": 20}
    assert settings_hash(filled) == h          # lock-time blocks never invalidate pre-lock artifacts
```

Append to `tests/test_calibrate.py`:

```python
def test_calibrate_refuses_a_market_with_no_served_job(monkeypatch):
    import sim.calibrate as cal
    monkeypatch.setattr(cal, "first_best_served", lambda cfg, values_t: 0)       # a valid market always serves; force the edge
    with pytest.raises(ValueError, match="positive first-best surplus"):
        cal.calibrate(MarketConfig.default(), seeds=[4000])
```

Append to `tests/test_sweep.py`:

```python
def test_reference_records_carry_per_seed_values_and_foreign_rules_are_refused(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development", "--rules", "B1",
                  "--select", "B1_D1_beta0.05_rho0.2_median", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    rec = json.loads(next((out / "reference").glob("*.json")).read_text())
    assert len(rec["attack_per_seed_normalized"]) == 1 and len(rec["reference_per_seed_normalized"]) == 1
    assert rec["gain_train"] == pytest.approx(rec["attack_per_seed_normalized"][0] - rec["reference_per_seed_normalized"][0])
    r = run_sweep(cal_path, out, "--stage", "reference", "--rules", "B2", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "B1" in (r.stderr + r.stdout)
    r = run_sweep(cal_path, out, "--stage", "evaluate", "--rules", "B1", "--smoke", "--workers", "1", "--eval-namespace", "final_eval")
    assert r.returncode != 0 and "final_eval" in (r.stderr + r.stdout)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_locked.py tests/test_calibrate.py tests/test_sweep.py -q -k "plan_2b or no_served or per_seed_values"`
Expected: FAIL: `KeyError: 'coverage'`; `ZeroDivisionError` instead of `ValueError`; `KeyError: 'attack_per_seed_normalized'`.

- [ ] **Step 3: Apply the changes**

In `pyproject.toml`:

```toml
dependencies = ["numpy>=2.0", "scipy>=1.13", "cma>=4.0", "pyyaml>=6.0", "pandas>=2.2", "matplotlib>=3.9", "anthropic>=1.0", "typesafe-sdk>=0.3"]
```

Append to `experiments/locked.yaml` (after `all_deviators:`), and add `coverage` under `seeds:`:

```yaml
seeds:
  # ... existing namespaces ...
  coverage:                 # dev-val sub-range for the coverage study: pools and replications, disjoint from every other range
    start: 3000000
    block: 600000           # seeds reserved per selected cell: pool + replications, with room for both doublings
    pool: 35000
    replications: {"10": 2000, "20": 2000, "40": 4000}
    n_grid: [10, 20, 40]
intervals:
  bootstrap_resamples: 10000
  bootstrap_seed: 20261111
  h1_repetitions: 10
  reference_level: 0.95
  margins: {"0.95": 2.0, "0.9875": 1.0}       # coverage points below the analytic threshold, per level
  deficits: {"0.95": 3.0, "0.9875": 1.5}      # negative-control coverage deficit the gate must detect, per level
  joint_trials: 200
  joint_min_admitted: 190
  joint_level: 0.9833333333                    # 1 - 0.05 / 3: at most three attempts
  quadrature_nodes: 200
  remedy_order: [percentile, studentized, studentized_n40]
h1:
  model: claude-opus-5-5                       # pinned snapshot id; the sealed prompt is the custodian's
  jev_model: jev-1.14.0
  T: 100
  episodes: 5
  repetitions: 10
  betas: [0.02, 0.05, 0.10]
  fallback_limit: 0.05
  invalid_limit: 2
  calls_cap: 192000
  cost_cap_usd: null                           # set at the lock from the token pilot
claim:
  beta: 0.05
  eff_min: 0.90
  gain_max: 0.30
  loss_diff_min: 0.05
  baseline_gain_min: 1.0
  rule_level: 0.95
  baseline_level: 0.9875
allow_list: [sim/mechanisms/proposed.py, experiments/proposed.yaml, experiments/proposed_describe.yaml, scripts/plot.py, docs/, sealed/, sealed/patches/]
calibration: null                              # written by scripts/lock.py from experiments/calibration.json
sealed_bundle_sha256: null                     # written by scripts/lock.py from the custodian's hash
coverage_report_sha256: null                   # written by scripts/lock.py
comprehension_fixture_sha256: null             # written by scripts/lock.py
```

In `sim/locked.py`, extend the exclusion list of `settings_hash` to `("version", "tuned", "calibration", "identity_salt_sha256", "sealed_bundle_sha256", "coverage_report_sha256", "comprehension_fixture_sha256", "coverage_consequences")` and change the docstring to name them as the blocks written at the lock.

In `sim/calibrate.py`, after computing `n_FB`, insert:

```python
    if n_FB <= 0:
        raise ValueError("no job has positive first-best surplus: calibration is undefined for this market")
```

In `sim/market.py`, change the `efforts` field comment to `# (T, N) per entity: the effort chosen each round, recorded in banned rounds too (no job is served then)`.

In `sim/search.py`, replace `import cma` with:

```python
import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message="Could not import matplotlib.pyplot", category=UserWarning)
    import cma
```

In `scripts/sweep.py`:
- in `stage_reference`, add to the record: `"attack_per_seed_normalized": [float(v) for v in attack.archive[exact_key(attack.best_knobs)].per_seed_normalized]`, `"reference_per_seed_normalized": [float(v) for v in ref.per_seed_normalized]`, `"reference_per_seed_profit": [float(v) for v in ref.per_seed_profit]`;
- in `train_val`, take the evaluation namespace from `job["eval_namespace"]` (default `"dev_val"`) and raise `SystemExit(f"evaluation namespace {ns} is not available in locked.yaml")` when `locked_seeds` raises `ValueError`;
- in `job_for`, add `"eval_namespace": eval_namespace` (a new parameter, default `"dev_val"`), and in `run_stages` pass `o.get("eval_namespace", "dev_val")`; add `ap.add_argument("--eval-namespace", dest="eval_namespace", default="dev_val", choices=["dev_val", "final_eval"])`;
- in `run_stages`, when building `jobs` from the search records, raise `SystemExit(f"record {name} belongs to rule {rule}, which is not in --rules; pass it or use another output directory")` instead of a `KeyError`;
- in `base_record`, add `"eval_namespace": job["eval_namespace"]` and in `check_record` compare it too.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv sync && uv run pytest tests/test_locked.py tests/test_calibrate.py tests/test_sweep.py -q && uv run pytest -q`
Expected: PASS; whole suite green (165 tests: 162 plus the three new ones). The smoke sweep test still passes with the per-seed fields present.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock experiments/locked.yaml sim/locked.py sim/calibrate.py sim/market.py sim/search.py scripts/sweep.py tests/test_locked.py tests/test_calibrate.py tests/test_sweep.py
git commit -m "feat: plan 2B configuration blocks, coverage seed range, per-seed reference values in sweep records, evaluation namespace option; plan 2A deferred minors"
```

---

### Task 2: Interval algorithms

**Files:**
- Create: `sim/intervals.py`
- Test: `tests/test_intervals.py`

**Interfaces:**
- Produces:
  - `Bound(value: float, side: str, level: float, method: str, degenerate: bool, n: int)`.
  - `percentile_bootstrap(x, side, level, resamples, seed) -> Bound`: one-sided percentile bootstrap of the mean of per-seed values `x` (seed is the resampling unit); `side` is `"upper"` or `"lower"`; identical values give `value = x[0]`, `degenerate = True`.
  - `studentized_bootstrap(x, side, level, resamples, seed) -> Bound`: bootstrap-t with each resample studentized by its own standard error; a resample with zero standard error uses the full-sample standard error; degenerate when the full sample has zero standard error.
  - `t_bound(x, side, level) -> Bound`: one-sided Student t bound on the mean (H1's 10 repetitions).
  - `t_interval(x, level=0.95) -> tuple[float, float]`: two-sided t interval (the coverage study's reference-mean interval).
  - `bound(method, x, side, level, settings) -> Bound` dispatch with `method in {"percentile", "studentized", "t"}` and `settings` from `locked["intervals"]`.
  - `exact_t_bound_with_critical(x, side, critical) -> float`: the negative control's bound at an arbitrary critical value (used by the coverage study's power check).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_intervals.py
import numpy as np
import pytest
from scipy import stats
from sim.intervals import percentile_bootstrap, studentized_bootstrap, t_bound, t_interval, bound, exact_t_bound_with_critical


def test_percentile_bootstrap_degenerate_when_all_values_equal():
    b = percentile_bootstrap(np.full(20, 0.37), "upper", 0.95, resamples=1000, seed=1)
    assert b.value == 0.37 and b.degenerate is True and np.isfinite(b.value)
    b2 = percentile_bootstrap(np.full(20, 0.37), "lower", 0.9875, resamples=1000, seed=1)
    assert b2.value == 0.37 and b2.degenerate is True


def test_percentile_bootstrap_is_one_sided_seeded_and_brackets_the_mean():
    rng = np.random.default_rng(0); x = rng.normal(1.0, 0.5, size=20)
    up = percentile_bootstrap(x, "upper", 0.95, resamples=2000, seed=7)
    lo = percentile_bootstrap(x, "lower", 0.95, resamples=2000, seed=7)
    assert lo.value < x.mean() < up.value and up.side == "upper" and up.level == 0.95 and up.n == 20 and up.degenerate is False
    assert percentile_bootstrap(x, "upper", 0.95, resamples=2000, seed=7).value == up.value       # seeded: byte-identical
    assert percentile_bootstrap(x, "upper", 0.95, resamples=2000, seed=8).value != up.value
    tighter = percentile_bootstrap(x, "upper", 0.9875, resamples=2000, seed=7)
    assert tighter.value > up.value


def test_studentized_bootstrap_zero_se_resample_uses_full_sample_se():
    x = np.array([0.0] * 9 + [1.0])          # a resample of ten zeros has zero standard error
    b = studentized_bootstrap(x, "upper", 0.95, resamples=500, seed=3)
    assert np.isfinite(b.value) and b.degenerate is False and b.value >= x.mean()
    d = studentized_bootstrap(np.full(10, 2.0), "lower", 0.95, resamples=500, seed=3)
    assert d.degenerate is True and d.value == 2.0


def test_t_bound_and_interval_match_scipy():
    x = np.array([0.2, 0.5, 0.1, 0.9, 0.4, 0.6, 0.3, 0.8, 0.7, 0.35])
    n = len(x); se = x.std(ddof=1) / np.sqrt(n)
    assert t_bound(x, "upper", 0.95).value == pytest.approx(x.mean() + stats.t.ppf(0.95, n - 1) * se)
    assert t_bound(x, "lower", 0.9875).value == pytest.approx(x.mean() - stats.t.ppf(0.9875, n - 1) * se)
    lo, hi = t_interval(x, 0.95)
    assert (lo, hi) == pytest.approx((x.mean() - stats.t.ppf(0.975, n - 1) * se, x.mean() + stats.t.ppf(0.975, n - 1) * se))
    assert exact_t_bound_with_critical(x, "upper", 1.0) == pytest.approx(x.mean() + se)


def test_dispatch_reads_settings():
    settings = {"bootstrap_resamples": 300, "bootstrap_seed": 5}
    x = np.linspace(0, 1, 20)
    assert bound("percentile", x, "upper", 0.95, settings).method == "percentile"
    assert bound("studentized", x, "lower", 0.95, settings).method == "studentized"
    assert bound("t", x, "upper", 0.95, settings).method == "t"
    with pytest.raises(ValueError):
        bound("other", x, "upper", 0.95, settings)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_intervals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.intervals'`

- [ ] **Step 3: Write the implementation**

```python
# sim/intervals.py
"""The locked interval algorithms of spec 8. Every function is a pure function of its inputs and the seed."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class Bound:
    value: float
    side: str
    level: float
    method: str
    degenerate: bool
    n: int


def _check(x: np.ndarray, side: str, level: float) -> np.ndarray:
    x = np.asarray(x, dtype=float).ravel()
    if x.size < 2 or not np.all(np.isfinite(x)):
        raise ValueError("need at least two finite per-seed values")
    if side not in ("upper", "lower"):
        raise ValueError("side must be 'upper' or 'lower'")
    if not (0.5 < level < 1.0):
        raise ValueError("level must be in (0.5, 1)")
    return x


def percentile_bootstrap(x, side: str, level: float, resamples: int, seed: int) -> Bound:
    """One-sided percentile bootstrap of the mean; the seed is the resampling unit (spec 8)."""
    x = _check(x, side, level); n = x.size
    if np.all(x == x[0]):
        return Bound(float(x[0]), side, level, "percentile", True, n)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, n, size=(int(resamples), n))
    means = x[idx].mean(axis=1)
    q = level if side == "upper" else 1.0 - level
    return Bound(float(np.quantile(means, q)), side, level, "percentile", False, n)


def studentized_bootstrap(x, side: str, level: float, resamples: int, seed: int) -> Bound:
    """Bootstrap-t: each resample studentized by its own standard error; a zero-standard-error resample
    uses the full-sample standard error (spec 8)."""
    x = _check(x, side, level); n = x.size
    mean = x.mean(); se = x.std(ddof=1) / np.sqrt(n)
    if se == 0.0:
        return Bound(float(mean), side, level, "studentized", True, n)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, n, size=(int(resamples), n))
    samples = x[idx]
    m = samples.mean(axis=1); s = samples.std(axis=1, ddof=1) / np.sqrt(n)
    s = np.where(s > 0, s, se)
    tstat = (m - mean) / s
    if side == "upper":
        return Bound(float(mean - np.quantile(tstat, 1.0 - level) * se), side, level, "studentized", False, n)
    return Bound(float(mean - np.quantile(tstat, level) * se), side, level, "studentized", False, n)


def t_bound(x, side: str, level: float) -> Bound:
    """One-sided Student t bound on the mean (H1's 10 repetitions, spec 8)."""
    x = _check(x, side, level); n = x.size
    se = x.std(ddof=1) / np.sqrt(n)
    crit = stats.t.ppf(level, n - 1)
    degenerate = bool(se == 0.0)
    value = x.mean() + crit * se if side == "upper" else x.mean() - crit * se
    return Bound(float(value), side, level, "t", degenerate, n)


def exact_t_bound_with_critical(x, side: str, critical: float) -> float:
    """A one-sided t-type bound at an arbitrary critical value (the coverage study's negative control)."""
    x = np.asarray(x, dtype=float).ravel(); n = x.size
    se = x.std(ddof=1) / np.sqrt(n)
    return float(x.mean() + critical * se if side == "upper" else x.mean() - critical * se)


def t_interval(x, level: float = 0.95) -> tuple[float, float]:
    """Two-sided t interval on the mean (the reference-mean interval of the coverage study)."""
    x = np.asarray(x, dtype=float).ravel(); n = x.size
    se = x.std(ddof=1) / np.sqrt(n)
    h = stats.t.ppf(0.5 + level / 2.0, n - 1) * se
    return float(x.mean() - h), float(x.mean() + h)


def bound(method: str, x, side: str, level: float, settings: dict) -> Bound:
    if method == "percentile":
        return percentile_bootstrap(x, side, level, int(settings["bootstrap_resamples"]), int(settings["bootstrap_seed"]))
    if method == "studentized":
        return studentized_bootstrap(x, side, level, int(settings["bootstrap_resamples"]), int(settings["bootstrap_seed"]))
    if method == "t":
        return t_bound(x, side, level)
    raise ValueError(f"unknown interval method {method!r}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_intervals.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add sim/intervals.py tests/test_intervals.py
git commit -m "feat: locked interval algorithms (percentile and studentized bootstrap, t bound, t interval)"
```

---

### Task 3: Vocabulary, `describe()` validation, the frozen renderer, and the comprehension fixture

**Files:**
- Create: `experiments/vocabulary.yaml`, `experiments/comprehension_fixture.yaml`, `sim/describe.py`
- Modify: `sim/mechanisms/posted.py`, `sim/mechanisms/posted_audit.py`, `sim/mechanisms/second_score.py`, `sim/mechanisms/ablation.py` (`describe()` values drawn from the vocabulary)
- Test: `tests/test_describe.py`

**Interfaces:**
- Produces:
  - `experiments/vocabulary.yaml`: for each of the eight fields `allocation_order, eligibility, payment, audit_selection, audit_tolerance, failed_audit, ban_length, holdback` the list of admissible values (strings; numeric fields admit the pattern `number` and `none`), plus `not_expressible: "not expressible"`.
  - `DESCRIBE_FIELDS` (the eight), `NOT_EXPRESSIBLE`.
  - `validate_record(record: dict, vocabulary: dict) -> None` (raises `ValueError` naming the field and value); `load_vocabulary(path=None) -> dict`.
  - `render(record: dict, vocabulary: dict) -> str`: the frozen template; prose assembled only from the record's values through fixed sentence frames; `uses_not_expressible(record) -> bool`.
  - `describe_record(rule) -> dict`: calls `rule.describe()` and validates.
  - `comprehension_questions(path=None) -> list[dict]` (`id`, `question`, `answer_from: field`, `options`), `score_comprehension(answers: dict[str, str], record: dict, questions) -> int` (number of correct answers, correct meaning the option that the record's field value maps to).
  - The baselines' `describe()` records use vocabulary values: B1 `{"allocation_order": "descending value", "eligibility": "active offers with capacity", "payment": "posted tier price", "audit_selection": "none", "audit_tolerance": "none", "failed_audit": "none", "ban_length": "none", "holdback": "none"}`; B2 as B1 with `audit_selection: "uniform random among served jobs, spread evenly over rounds"`, `audit_tolerance: "number"` plus a `parameters` sub-record `{"audit_tolerance": tol, "ban_length": L}`, `failed_audit: "full refund of the audited job"`, `ban_length: "number"`; B3 with `allocation_order: "descending value by score"`, `payment: "second score"`, audits and enforcement as B2. The record keeps a separate `parameters` map for numeric values, which the renderer prints with the field's sentence frame.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_describe.py
import pytest
from sim.describe import (DESCRIBE_FIELDS, NOT_EXPRESSIBLE, load_vocabulary, validate_record, render, uses_not_expressible,
                          describe_record, comprehension_questions, score_comprehension)
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.mechanisms.ablation import EnforcementAblation


def rules():
    return [PostedPrices(0.25, 0.40, 0.55), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), SecondScore(tol=0.12, L=10),
            EnforcementAblation(SecondScore(tol=0.12, L=10), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=20))]


def test_every_rule_record_uses_only_vocabulary_values():
    voc = load_vocabulary()
    for r in rules():
        rec = describe_record(r)
        assert set(rec) >= set(DESCRIBE_FIELDS)
        validate_record(rec, voc)
        assert not uses_not_expressible(rec)


def test_vocabulary_refuses_unknown_values():
    voc = load_vocabulary()
    rec = describe_record(PostedPrices(0.25, 0.40, 0.55))
    bad = dict(rec, failed_audit="we think about it")
    with pytest.raises(ValueError, match="failed_audit"):
        validate_record(bad, voc)
    missing = {k: v for k, v in rec.items() if k != "holdback"}
    with pytest.raises(ValueError, match="holdback"):
        validate_record(missing, voc)
    ne = dict(rec, holdback=NOT_EXPRESSIBLE)
    validate_record(ne, voc)
    assert uses_not_expressible(ne)


def test_renderer_receives_only_the_record_and_is_noninterfering(monkeypatch):
    voc = load_vocabulary()
    rec = describe_record(PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10))
    text = render(rec, voc)
    assert "0.12" in text and "10" in text and "uniform random" in text and "PostedRandomAudit" not in text
    # the renderer sees the record only: a spy record with a changed numeric parameter changes the bytes; nothing else can
    spy = dict(rec, parameters=dict(rec["parameters"], audit_tolerance=0.16))
    assert render(spy, voc) != text
    # noninterference: renaming the class and changing its source comments does not change the rendered bytes
    class RenamedRuleWithDifferentComments(PostedRandomAudit):
        """A docstring that mentions tolerance 0.99 and bans forever."""
    assert render(describe_record(RenamedRuleWithDifferentComments(0.25, 0.40, 0.55, tol=0.12, L=10)), voc) == text
    assert render(rec, voc) == text                                              # deterministic


def test_comprehension_fixture_scores_answers_from_the_record():
    qs = comprehension_questions()
    assert len(qs) >= 6 and all({"id", "question", "answer_from", "options"} <= set(q) for q in qs)
    rec = describe_record(PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10))
    perfect = {q["id"]: next(o for o in q["options"] if o["value"] == rec[q["answer_from"]])["label"] for q in qs}
    assert score_comprehension(perfect, rec, qs) == len(qs)
    wrong = dict(perfect); first = qs[0]; wrong[first["id"]] = next(o["label"] for o in first["options"] if o["label"] != perfect[first["id"]])
    assert score_comprehension(wrong, rec, qs) == len(qs) - 1
    assert score_comprehension({}, rec, qs) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_describe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.describe'`

- [ ] **Step 3: Write the implementation**

```yaml
# experiments/vocabulary.yaml
# Locked vocabulary for describe() records (spec 5.4). Frozen at the lock, before any proposed rule exists.
# A numeric field takes the value "number" and puts its figure in the record's `parameters` map.
not_expressible: "not expressible"
fields:
  allocation_order:
    - descending value
    - descending value by score
    - ascending bid
    - round robin
    - not expressible
  eligibility:
    - active offers with capacity
    - active offers with capacity and no failed audit in the last rounds
    - active offers with capacity above a reputation threshold
    - not expressible
  payment:
    - posted tier price
    - second score
    - bid
    - value times claim
    - not expressible
  audit_selection:
    - none
    - uniform random among served jobs, spread evenly over rounds
    - highest claim first
    - newest identities first
    - lowest recent audit count first
    - weighted by claim above history
    - not expressible
  audit_tolerance:
    - none
    - number
    - not expressible
  failed_audit:
    - none
    - full refund of the audited job
    - partial refund of the audited job
    - full refund and forfeit of the held-back bond
    - not expressible
  ban_length:
    - none
    - number
    - until the next passed audit
    - not expressible
  holdback:
    - none
    - number of rounds of receipts, released after the next passed audit
    - number of rounds of receipts, released on a fixed schedule
    - not expressible
```

```yaml
# experiments/comprehension_fixture.yaml
# Locked factual questions about a rule, answered by the actor from the rendered description alone (spec 5.4).
# `answer_from` names the describe() field whose value is the correct answer; options map vocabulary values to labels.
questions:
  - id: q_allocation
    question: "In what order are jobs allocated?"
    answer_from: allocation_order
    options:
      - {label: "A", value: "descending value"}
      - {label: "B", value: "descending value by score"}
      - {label: "C", value: "ascending bid"}
      - {label: "D", value: "round robin"}
      - {label: "E", value: "not expressible"}
  - id: q_payment
    question: "How is the payment for a served job set?"
    answer_from: payment
    options:
      - {label: "A", value: "posted tier price"}
      - {label: "B", value: "second score"}
      - {label: "C", value: "bid"}
      - {label: "D", value: "value times claim"}
      - {label: "E", value: "not expressible"}
  - id: q_audit_selection
    question: "How does the operator choose which jobs to audit?"
    answer_from: audit_selection
    options:
      - {label: "A", value: "none"}
      - {label: "B", value: "uniform random among served jobs, spread evenly over rounds"}
      - {label: "C", value: "highest claim first"}
      - {label: "D", value: "newest identities first"}
      - {label: "E", value: "lowest recent audit count first"}
      - {label: "F", value: "weighted by claim above history"}
      - {label: "G", value: "not expressible"}
  - id: q_failed_audit
    question: "What happens to the payment of a job that fails its audit?"
    answer_from: failed_audit
    options:
      - {label: "A", value: "none"}
      - {label: "B", value: "full refund of the audited job"}
      - {label: "C", value: "partial refund of the audited job"}
      - {label: "D", value: "full refund and forfeit of the held-back bond"}
      - {label: "E", value: "not expressible"}
  - id: q_ban
    question: "After a failed audit, for how long is the identity banned?"
    answer_from: ban_length
    options:
      - {label: "A", value: "none"}
      - {label: "B", value: "number"}
      - {label: "C", value: "until the next passed audit"}
      - {label: "D", value: "not expressible"}
  - id: q_holdback
    question: "Does the operator hold back part of the receipts as a bond?"
    answer_from: holdback
    options:
      - {label: "A", value: "none"}
      - {label: "B", value: "number of rounds of receipts, released after the next passed audit"}
      - {label: "C", value: "number of rounds of receipts, released on a fixed schedule"}
      - {label: "D", value: "not expressible"}
  - id: q_eligibility
    question: "Which offers are eligible for allocation?"
    answer_from: eligibility
    options:
      - {label: "A", value: "active offers with capacity"}
      - {label: "B", value: "active offers with capacity and no failed audit in the last rounds"}
      - {label: "C", value: "active offers with capacity above a reputation threshold"}
      - {label: "D", value: "not expressible"}
```

```python
# sim/describe.py
"""describe() records: vocabulary validation, the frozen prose renderer, and the comprehension fixture (spec 5.4)."""
from __future__ import annotations

from pathlib import Path

import yaml

DESCRIBE_FIELDS = ("allocation_order", "eligibility", "payment", "audit_selection", "audit_tolerance", "failed_audit", "ban_length", "holdback")
NOT_EXPRESSIBLE = "not expressible"
ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = ROOT / "experiments" / "vocabulary.yaml"
FIXTURE_PATH = ROOT / "experiments" / "comprehension_fixture.yaml"

# Sentence frames: one per field, fixed at the lock. {value} is the vocabulary value; {number} the figure from `parameters`.
FRAMES = {
    "allocation_order": "Jobs are allocated in {value} order.",
    "eligibility": "An offer is eligible when it comes from {value}.",
    "payment": "A served job pays its provider the {value}.",
    "audit_selection": "Audits are selected as follows: {value}.",
    "audit_tolerance": "A delivery fails its audit when it falls below the claim by more than {number}.",
    "failed_audit": "After a failed audit, the consequence for the payment is: {value}.",
    "ban_length": "After a failed audit, the identity is banned for {number} rounds.",
    "holdback": "Hold-back of receipts: {value}.",
}
NONE_FRAMES = {
    "audit_selection": "No audits are performed.",
    "audit_tolerance": "There is no audit tolerance because there are no audits.",
    "failed_audit": "A failed audit has no consequence for the payment.",
    "ban_length": "Failed audits never lead to a ban.",
    "holdback": "No receipts are held back.",
}


def load_vocabulary(path: str | Path | None = None) -> dict:
    with open(path or VOCABULARY_PATH) as f:
        return yaml.safe_load(f)


def validate_record(record: dict, vocabulary: dict) -> None:
    fields = vocabulary["fields"]
    for name in DESCRIBE_FIELDS:
        if name not in record:
            raise ValueError(f"describe() record lacks the field {name!r}")
        value = record[name]
        if value not in fields[name]:
            raise ValueError(f"describe() field {name!r} has the value {value!r}, which is not in the vocabulary")
        if value == "number" and name not in record.get("parameters", {}):
            raise ValueError(f"describe() field {name!r} is 'number' but parameters has no {name!r}")


def uses_not_expressible(record: dict) -> bool:
    return any(record[name] == NOT_EXPRESSIBLE for name in DESCRIBE_FIELDS)


def describe_record(rule) -> dict:
    rec = dict(rule.describe())
    validate_record(rec, load_vocabulary())
    return rec


def render(record: dict, vocabulary: dict) -> str:
    """The frozen template: prose assembled only from the record through fixed sentence frames."""
    validate_record(record, vocabulary)
    params = record.get("parameters", {})
    lines = ["Market rule."]
    for name in DESCRIBE_FIELDS:
        value = record[name]
        if value == "none" and name in NONE_FRAMES:
            lines.append(NONE_FRAMES[name])
        elif value == NOT_EXPRESSIBLE:
            lines.append(f"The {name.replace('_', ' ')} of this rule is not expressible in the locked vocabulary.")
        elif value == "number":
            lines.append(FRAMES[name].format(value=value, number=f"{params[name]:g}"))
        else:
            lines.append(FRAMES[name].format(value=value, number=""))
    return "\n".join(lines) + "\n"


def comprehension_questions(path: str | Path | None = None) -> list[dict]:
    with open(path or FIXTURE_PATH) as f:
        return yaml.safe_load(f)["questions"]


def score_comprehension(answers: dict, record: dict, questions: list[dict]) -> int:
    correct = 0
    for q in questions:
        truth = record[q["answer_from"]]
        label = next((o["label"] for o in q["options"] if o["value"] == truth), None)
        if label is not None and answers.get(q["id"]) == label:
            correct += 1
    return correct
```

Change the baselines' `describe()` methods to return vocabulary values with a `parameters` map:

```python
# sim/mechanisms/posted.py (B1)
    def describe(self) -> dict:
        return {"allocation_order": "descending value", "eligibility": "active offers with capacity", "payment": "posted tier price",
                "audit_selection": "none", "audit_tolerance": "none", "failed_audit": "none", "ban_length": "none", "holdback": "none",
                "parameters": {}}
```

```python
# sim/mechanisms/posted_audit.py (B2)
    def describe(self) -> dict:
        d = PostedPrices.describe(self)
        d.update({"audit_selection": "uniform random among served jobs, spread evenly over rounds", "audit_tolerance": "number",
                  "failed_audit": "full refund of the audited job", "ban_length": "number" if self.L > 0 else "none", "holdback": "none",
                  "parameters": {"audit_tolerance": float(self.tol), **({"ban_length": int(self.L)} if self.L > 0 else {})}})
        return d
```

```python
# sim/mechanisms/second_score.py (B3)
    def describe(self) -> dict:
        return {"allocation_order": "descending value by score", "eligibility": "active offers with capacity", "payment": "second score",
                "audit_selection": "uniform random among served jobs, spread evenly over rounds", "audit_tolerance": "number",
                "failed_audit": "full refund of the audited job", "ban_length": "number" if self.L > 0 else "none", "holdback": "none",
                "parameters": {"audit_tolerance": float(self.tol), **({"ban_length": int(self.L)} if self.L > 0 else {})}}
```

In `sim/mechanisms/ablation.py`, `ENFORCEMENT_FIELDS = ("failed_audit", "ban_length", "holdback")` stays; `describe()` also merges the enforcer's `parameters` entries for those fields into the rule's `parameters` (the rule's `audit_tolerance` parameter stays). Update two plan 1 assertions: in `tests/test_ablation.py` replace `assert d["ban_length"] == "3" and d["holdback"] == "none" and d["pricing"] == rule.describe()["pricing"]` with `assert d["ban_length"] == "number" and d["parameters"]["ban_length"] == 3 and d["holdback"] == "none" and d["payment"] == rule.describe()["payment"]`; in `tests/test_posted.py::test_describe_fields` replace the field set with `{"allocation_order", "eligibility", "payment", "audit_selection", "audit_tolerance", "failed_audit", "ban_length", "holdback", "parameters"}`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_describe.py tests/test_ablation.py tests/test_posted.py tests/test_posted_audit.py tests/test_second_score.py -v`
Expected: PASS (4 new tests; the plan 1 describe assertions, if any compare literal strings, are updated to the vocabulary values in the same commit).

- [ ] **Step 5: Commit**

```bash
git add experiments/vocabulary.yaml experiments/comprehension_fixture.yaml sim/describe.py sim/mechanisms/posted.py sim/mechanisms/posted_audit.py sim/mechanisms/second_score.py sim/mechanisms/ablation.py tests/test_describe.py tests/test_ablation.py tests/test_posted.py
git commit -m "feat: locked describe() vocabulary, validation, frozen renderer, comprehension fixture; baselines describe in vocabulary values"
```

---

### Task 4: Model actor (LLM and Jev backends behind a prompt-hash cache), the H1 procedure, and the closed-loop clipped re-run

**Files:**
- Create: `sim/llm_actor.py`, `sim/policies/llm.py`
- Test: `tests/test_llm_actor.py`

**Interfaces:**
- Consumes: `Twin` (plan 1), `run_episode`, `SeedCache`, `cell_config`, `render`/`describe_record` (Task 3), `t_bound` (Task 2).
- Produces (`sim/llm_actor.py`):
  - `ACTION_SCHEMA`: JSON schema `{"effort": number, "offer": {"claim": number, "bid": number} | null}`; `parse_action(data: dict, params: ProviderParams) -> Action | None` (None when malformed: missing keys, non-finite, effort outside `[0, q_max]`, claim outside `[0, 1]`, bid negative).
  - `canonical_request(backend_name, model, kind, payload) -> str` (sorted-key JSON) and `request_hash(...) -> str` (SHA-256).
  - `PromptCache(directory)`: `get(key) -> dict | None`, `put(key, response: dict)`, counters `hits`, `misses`; one JSON file per key under `directory`.
  - `Backend` protocol: `name: str`, `model: str`, `complete(kind: str, payload: dict) -> dict` returning `{"data": <parsed answer or None>, "raw": <provider response as dict>, "usage": {"input_tokens": int, "output_tokens": int}}`; `kind in {"action", "comprehension"}`.
  - `AnthropicBackend(model)`: `anthropic.Anthropic()` client, `messages.create` with `output_config={"format": {"type": "json_schema", "schema": ACTION_SCHEMA}}` for actions and a schema of `{"answers": {<question id>: label}}` for comprehension, `output_config.effort = "low"`, `max_tokens = 512`, `system` = the frozen actor instructions plus the rendered rule, one user message with the state; no sampling parameters (Opus 5.5 rejects `temperature`; determinism comes from the cache and the pinned snapshot).
  - `JevBackend(model)`: `typesafe_sdk.TypeSafeClient(model=model)`, `client.system_one(state=<state dict>, questions=<Choice menu>)`; the action menu is three Choice questions: `effort` over `EFFORT_LEVELS = (0.0, 0.25, 0.5, 0.75, 1.0)` (fractions of q_max), `claim_offset` over `CLAIM_OFFSETS = (-0.10, 0.0, 0.10, 0.20, 0.40)` (claim = clip(effort + offset, 0, 1)), `markup` over `MARKUPS = (0.0, 0.25, 0.5, 1.0)` (bid = (1 + markup) cost), and `serve` over `{serve, abstain}`; comprehension is one Choice per fixture question over its labels; `data` carries the chosen values and every answer's `confidence`.
  - `FakeBackend(fn)`: `fn(kind, payload) -> dict | None` for tests; `usage` counts the canonical request's characters as tokens.
  - `make_backend(name, locked, instructions=None) -> Backend` for `"anthropic"`, `"jev"`, `"fake-honest"`; `instructions` replaces `ACTOR_INSTRUCTIONS` (the sealed H1 prompt after the unseal). The prompt text is part of the cache key only through the request payload, so a different prompt never replays a cached development response: `canonical_request` includes `instructions` in the payload (see `LLMProvider.act`).
  - `ACTOR_INSTRUCTIONS`: the frozen system prompt frame for the development runs (the sealed H1 prompt is the custodian's and replaces it at the unseal through the same field).
  - `build_state(view, rendered_rule, feedback: list[float], T) -> dict`: round, horizon, provider parameters, posted prices if any, own history (served, payments, audits, failures, refunds, ban), profits of previous episodes.
  - `ProcedureResult(profits: list[float] (5), fallback_rounds: int, total_rounds: int, invalid: bool, calls: int, cache_hits: int, usage: dict, episode5: EpisodeResult)`; `run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds: tuple[int, int, int, int], eval_seed: int, locked, clip_episode5: bool = False, twin: bool = False) -> ProcedureResult`: 5 episodes of `cfg.T` rounds; episodes 1 to 4 on the train seeds, episode 5 on the evaluation seed; the actor sees its profits of earlier episodes in the state; `twin=True` wraps the actor in `Twin` for every episode; `clip_episode5=True` wraps it in `Twin` in episode 5 only (the closed-loop clipped-attack run), replaying matching prompts from the cache and counting new calls; `invalid = fallback_rounds / total_rounds > locked["h1"]["fallback_limit"]`.
  - `H1CellResult(attack: list[ProcedureResult], twin: list[ProcedureResult], clipped: list[ProcedureResult], eval_seeds, invalid_count, inconclusive: bool, calls, new_calls_clipped, usage)`; `run_h1_cell(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, eval_seeds: tuple[int, ...], locked) -> H1CellResult` (10 repetitions; the actor learns within a procedure, never across repetitions; `inconclusive = invalid_count > locked["h1"]["invalid_limit"]`); `h1_rows(result, cell_meta) -> list[dict]` with `rep, eval_seed, profit_attack, profit_twin, profit_clip, sstar, gain_vs_twin, eff_attack, eff_twin, eff_clip, audit_cost_attack, fallback_rounds, invalid`.
  - `ask_comprehension(backend, cache, rendered_rule, questions) -> dict[str, str]` and `comprehension_check(backend, cache, rules: dict[str, rule], questions) -> dict[str, int]` (score per rule).
  - `estimate_cost_usd(usage, model, locked) -> float` from `locked["h1"]["prices"]` (added in this task: `{"claude-opus-5-5": {"input": 4.0, "output": 20.0}, "jev-1.14.0": {"input": 0.042, "output": 0.0}}` per million tokens).
- Produces (`sim/policies/llm.py`): `LLMProvider(backend, cache, rendered_rule, params, feedback, T, counters: ActorCounters)` with `act(view) -> Action` (never exits), `ActorCounters(calls, cache_hits, fallbacks, rounds, usage)`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llm_actor.py
import json
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.describe import describe_record, load_vocabulary, render, comprehension_questions
from sim.llm_actor import (ACTION_SCHEMA, parse_action, request_hash, PromptCache, FakeBackend, make_backend, build_state,
                           run_procedure, run_h1_cell, h1_rows, ask_comprehension, comprehension_check, estimate_cost_usd,
                           EFFORT_LEVELS, CLAIM_OFFSETS, MARKUPS)
from sim.locked import load_locked
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.llm import LLMProvider, ActorCounters


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


def test_schema_and_parse_action():
    p = MarketConfig.default().providers[9]
    assert ACTION_SCHEMA["required"] == ["effort", "offer"]
    a = parse_action({"effort": 0.5, "offer": {"claim": 0.9, "bid": 0.3}}, p)
    assert a.effort == 0.5 and a.offer.claim == 0.9 and a.exit is False
    assert parse_action({"effort": 0.5, "offer": None}, p).offer is None
    for bad in ({"effort": 1.5, "offer": None}, {"effort": 0.5}, {"effort": float("nan"), "offer": None},
                {"effort": 0.5, "offer": {"claim": 1.2, "bid": 0.1}}, {"effort": 0.5, "offer": {"claim": 0.5, "bid": -1}}, "nonsense"):
        assert parse_action(bad, p) is None


def test_cache_is_content_addressed_and_backend_usage_is_recorded(tmp_path):
    cache = PromptCache(tmp_path / "cache")
    k = request_hash("fake", "m", "action", {"state": {"t": 0}})
    assert k == request_hash("fake", "m", "action", {"state": {"t": 0}}) and k != request_hash("fake", "m", "action", {"state": {"t": 1}})
    assert cache.get(k) is None and cache.misses == 1
    cache.put(k, {"data": {"x": 1}, "raw": {}, "usage": {"input_tokens": 3, "output_tokens": 1}})
    assert cache.get(k)["data"] == {"x": 1} and cache.hits == 1
    assert (tmp_path / "cache" / f"{k}.json").exists()


def test_llm_provider_acts_through_the_cache_and_never_exits(tmp_path):
    cfg = small_cfg(); voc = load_vocabulary()
    rendered = render(describe_record(PostedPrices(0.2, 0.35, 0.5)), voc)
    cache = PromptCache(tmp_path / "c"); counters = ActorCounters()
    prov = LLMProvider(FakeBackend(honest_fn), cache, rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=counters)
    from sim.market import run_episode
    from sim.policies.honest import HonestMax
    pols = [HonestMax() for _ in range(4)]; pols[3] = prov
    res = run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert res.n_identities == 4 and counters.calls == cfg.T and counters.fallbacks == 0 and counters.cache_hits == 0
    prov2 = LLMProvider(FakeBackend(honest_fn), cache, rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters())
    pols[3] = prov2
    res2 = run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert prov2.counters.cache_hits == cfg.T and prov2.counters.calls == 0 and np.array_equal(res.profit, res2.profit)   # replay is byte-identical


def test_malformed_response_falls_back_and_is_counted(tmp_path):
    cfg = small_cfg(); voc = load_vocabulary()
    rendered = render(describe_record(PostedPrices(0.2, 0.35, 0.5)), voc)
    def flaky(kind, payload):
        return None if payload["state"]["round"] == 2 else honest_fn(kind, payload)
    counters = ActorCounters()
    prov = LLMProvider(FakeBackend(flaky), PromptCache(tmp_path / "c"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=counters)
    from sim.market import run_episode
    from sim.policies.honest import HonestMax
    pols = [HonestMax() for _ in range(4)]; pols[3] = prov
    res = run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert counters.fallbacks == 1 and counters.rounds == cfg.T
    assert res.efforts[2, 3] == cfg.providers[3].q_max and res.claims[2, 3] == cfg.providers[3].q_max   # honest-max for that round


def test_procedure_runs_five_episodes_with_feedback_and_invalidity_rule(tmp_path):
    lk = load_locked(); cfg = small_cfg(); voc = load_vocabulary()
    rendered = render(describe_record(PostedPrices(0.2, 0.35, 0.5)), voc)
    seen_feedback = []
    def fn(kind, payload):
        seen_feedback.append(tuple(payload["state"]["previous_episode_profits"]))
        return honest_fn(kind, payload)
    pr = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(fn), PromptCache(tmp_path / "c"), rendered,
                       train_seeds=(1000, 1001, 1002, 1003), eval_seed=2000, locked=lk)
    assert len(pr.profits) == 5 and pr.total_rounds == 5 * cfg.T and pr.fallback_rounds == 0 and pr.invalid is False
    assert max(len(f) for f in seen_feedback) == 4 and seen_feedback[0] == ()         # profit feedback grows by one per episode
    assert pr.episode5.sstar > 0 and pr.calls == 5 * cfg.T
    def mostly_bad(kind, payload):
        return None if payload["state"]["round"] % 2 == 0 else honest_fn(kind, payload)
    bad = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(mostly_bad), PromptCache(tmp_path / "d"), rendered,
                        train_seeds=(1000, 1001, 1002, 1003), eval_seed=2000, locked=lk)
    assert bad.invalid is True and bad.fallback_rounds == 5 * (cfg.T // 2)


def test_clipped_rerun_replays_cache_and_counts_new_calls(tmp_path):
    lk = load_locked(); cfg = small_cfg(); voc = load_vocabulary()
    rendered = render(describe_record(PostedPrices(0.2, 0.35, 0.5)), voc)
    cache = PromptCache(tmp_path / "c")
    attack = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered,
                           train_seeds=(1000, 1001, 1002, 1003), eval_seed=2000, locked=lk)
    clipped = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered,
                            train_seeds=(1000, 1001, 1002, 1003), eval_seed=2000, locked=lk, clip_episode5=True)
    assert clipped.cache_hits >= 4 * cfg.T                        # episodes 1 to 4 replay from cache
    assert clipped.calls >= 1                                     # clipping changed the history, so a later prompt is new
    assert clipped.profits[4] < attack.profits[4]                 # the cheat loses its tier under the clip
    assert np.all(clipped.episode5.claims[:, 3][~np.isnan(clipped.episode5.claims[:, 3])] <= clipped.episode5.efforts[:, 3][~np.isnan(clipped.episode5.claims[:, 3])] + 1e-12)
    twin = run_procedure(cfg, lambda: PostedPrices(0.2, 0.35, 0.5), 3, FakeBackend(cheat_fn), cache, rendered,
                         train_seeds=(1000, 1001, 1002, 1003), eval_seed=2000, locked=lk, twin=True)
    assert twin.profits[4] == pytest.approx(clipped.profits[4])   # with a memoryless actor the twin and the clipped run agree in episode 5


def test_h1_cell_rows_and_inconclusive(tmp_path):
    lk = dict(load_locked()); lk["h1"] = dict(lk["h1"], repetitions=3, invalid_limit=0)
    cfg = small_cfg(budget=0.3); voc = load_vocabulary()
    rendered = render(describe_record(PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3)), voc)
    res = run_h1_cell(cfg, lambda: PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3), 3, FakeBackend(cheat_fn), PromptCache(tmp_path / "c"),
                      rendered, train_seeds=(1000, 1001, 1002, 1003), eval_seeds=(2000, 2001, 2002), locked=lk)
    assert len(res.attack) == 3 and len(res.twin) == 3 and len(res.clipped) == 3 and res.inconclusive is False
    rows = h1_rows(res, {"rule": "B2"})
    assert len(rows) == 3 and {"rep", "eval_seed", "profit_attack", "profit_twin", "profit_clip", "gain_vs_twin", "invalid"} <= set(rows[0])
    def bad(kind, payload):
        return None if payload["state"]["round"] % 2 == 0 else cheat_fn(kind, payload)
    res2 = run_h1_cell(cfg, lambda: PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3), 3, FakeBackend(bad), PromptCache(tmp_path / "d"),
                       rendered, train_seeds=(1000, 1001, 1002, 1003), eval_seeds=(2000, 2001, 2002), locked=lk)
    assert res2.invalid_count == 3 and res2.inconclusive is True and len(res2.attack) == 3        # nothing dropped


def test_comprehension_and_cost(tmp_path):
    lk = load_locked(); voc = load_vocabulary()
    qs = comprehension_questions()
    rules = {"B1": PostedPrices(0.2, 0.35, 0.5), "B2": PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3)}
    scores = comprehension_check(FakeBackend(honest_fn), PromptCache(tmp_path / "c"), rules, qs)
    assert set(scores) == {"B1", "B2"} and all(0 <= v <= len(qs) for v in scores.values())
    assert estimate_cost_usd({"input_tokens": 1_000_000, "output_tokens": 100_000}, "claude-opus-5-5", lk) == pytest.approx(4.0 + 2.0)
    assert estimate_cost_usd({"input_tokens": 1_000_000, "output_tokens": 100_000}, "jev-1.14.0", lk) == pytest.approx(0.042)
    assert make_backend("fake-honest", lk).name == "fake"
    assert len(EFFORT_LEVELS) == 5 and len(CLAIM_OFFSETS) == 5 and len(MARKUPS) == 4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_llm_actor.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.llm_actor'`

- [ ] **Step 3: Write the implementation**

Add to `experiments/locked.yaml` under `h1:`:

```yaml
  prices:                                      # USD per million tokens, used by the token pilot and the cost cap
    claude-opus-5-5: {input: 4.0, output: 20.0}
    jev-1.14.0: {input: 0.042, output: 0.0}
```

```python
# sim/policies/llm.py
"""A provider whose decisions come from a model backend through a prompt-hash cache (spec 5.4)."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..llm_actor import PromptCache, build_state, parse_action, request_hash
from ..mechanisms.base import Offer
from .base import Action, ProviderView
from .honest import HonestMax


@dataclass
class ActorCounters:
    calls: int = 0
    cache_hits: int = 0
    fallbacks: int = 0
    rounds: int = 0
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})


class LLMProvider:
    """Provider role only: effort plus an offer or abstain, never an exit. A malformed response falls back to
    honest-max for that round and is counted."""
    name = "llm_provider"

    def __init__(self, backend, cache: PromptCache, rendered_rule: str, params, feedback: list, T: int, counters: ActorCounters) -> None:
        self.backend, self.cache, self.rendered_rule, self.params, self.feedback, self.T, self.counters = backend, cache, rendered_rule, params, list(feedback), int(T), counters

    def act(self, view: ProviderView) -> Action:
        self.counters.rounds += 1
        state = build_state(view, self.rendered_rule, self.feedback, self.T)
        payload = {"instructions": getattr(self.backend, "instructions", ""), "rule": self.rendered_rule, "state": state}
        key = request_hash(self.backend.name, self.backend.model, "action", payload)
        resp = self.cache.get(key)
        if resp is None:
            resp = self.backend.complete("action", payload)
            self.cache.put(key, resp)
            self.counters.calls += 1
            for k in ("input_tokens", "output_tokens"):
                self.counters.usage[k] += int(resp.get("usage", {}).get(k, 0))
        else:
            self.counters.cache_hits += 1
        action = parse_action(resp.get("data"), self.params)
        if action is None:
            self.counters.fallbacks += 1
            return HonestMax().act(view)
        return action
```

```python
# sim/llm_actor.py
"""Model actors (spec 5.4): action schema, prompt-hash cache, backends (Anthropic, Jev, fake), the frozen actor
instructions, the five-episode H1 procedure with profit feedback, the invalidity rule, the closed-loop clipped
re-run, the comprehension fixture, and cost estimation."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .config import ProviderParams
from .describe import comprehension_questions
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


def canonical_request(backend_name: str, model: str, kind: str, payload: dict) -> str:
    return json.dumps({"backend": backend_name, "model": model, "kind": kind, "payload": payload}, sort_keys=True, separators=(",", ":"))


def request_hash(backend_name: str, model: str, kind: str, payload: dict) -> str:
    return hashlib.sha256(canonical_request(backend_name, model, kind, payload).encode()).hexdigest()


class PromptCache:
    """Content-addressed cache: one JSON file per request hash. Replay never touches the network."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.hits = 0; self.misses = 0

    def get(self, key: str) -> dict | None:
        p = self.directory / f"{key}.json"
        if p.exists():
            self.hits += 1
            return json.loads(p.read_text())
        self.misses += 1
        return None

    def put(self, key: str, response: dict) -> None:
        (self.directory / f"{key}.json").write_text(json.dumps(response, sort_keys=True, indent=1, default=float))


class FakeBackend:
    """Test backend: fn(kind, payload) -> parsed data or None (malformed)."""
    name = "fake"

    def __init__(self, fn, model: str = "fake-1") -> None:
        self.fn, self.model = fn, model

    def complete(self, kind: str, payload: dict) -> dict:
        data = self.fn(kind, payload)
        n = len(canonical_request(self.name, self.model, kind, payload))
        return {"data": data, "raw": {"fake": True}, "usage": {"input_tokens": n, "output_tokens": 16}}


class AnthropicBackend:
    name = "anthropic"

    def __init__(self, model: str, instructions: str = ACTOR_INSTRUCTIONS) -> None:
        import anthropic
        self.model = model; self.instructions = instructions
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
        return {"data": data, "raw": response.to_dict(),
                "usage": {"input_tokens": int(response.usage.input_tokens), "output_tokens": int(response.usage.output_tokens)}}


class JevBackend:
    """Typed decisions: Choice questions over a registered menu; the state is the same dict the LLM sees."""
    name = "jev"

    def __init__(self, model: str, instructions: str = ACTOR_INSTRUCTIONS) -> None:
        from typesafe_sdk import TypeSafeClient
        self.model = model; self.instructions = instructions
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
        answers = {k: {"choice": a.choice, "confidence": float(a.confidence), "probabilities": dict(a.probabilities)} for k, a in response.answers.items()}
        usage = {"input_tokens": int(getattr(response.usage, "input_tokens", 0)), "output_tokens": int(getattr(response.usage, "output_tokens", 0))}
        if kind == "comprehension":
            return {"data": {"answers": {k: v["choice"] for k, v in answers.items()}, "confidence": {k: v["confidence"] for k, v in answers.items()}},
                    "raw": answers, "usage": usage}
        p = payload["state"]["provider"]
        effort = float(answers["effort"]["choice"]) * p["q_max"]
        if answers["serve"]["choice"] == "abstain":
            data = {"effort": effort, "offer": None}
        else:
            claim = min(1.0, max(0.0, effort + float(answers["claim_offset"]["choice"])))
            bid = (1.0 + float(answers["markup"]["choice"])) * (p["a"] + p["b"] * effort)
            data = {"effort": effort, "offer": {"claim": claim, "bid": bid}}
        data["confidence"] = {k: v["confidence"] for k, v in answers.items()}
        return {"data": {k: data[k] for k in ("effort", "offer")} | {"confidence": data["confidence"]}, "raw": answers, "usage": usage}


def make_backend(name: str, locked: dict, instructions: str | None = None):
    """`instructions` replaces the development ACTOR_INSTRUCTIONS with the sealed H1 prompt after the unseal."""
    if name == "anthropic":
        return AnthropicBackend(str(locked["h1"]["model"]), instructions or ACTOR_INSTRUCTIONS)
    if name == "jev":
        return JevBackend(str(locked["h1"]["jev_model"]), instructions or ACTOR_INSTRUCTIONS)
    if name == "fake-honest":
        def fn(kind, payload):
            if kind == "comprehension":
                return {"answers": {q["id"]: q["options"][0]["label"] for q in payload["questions"]}}
            p = payload["state"]["provider"]
            return {"effort": p["q_max"], "offer": {"claim": p["q_max"], "bid": p["a"] + p["b"] * p["q_max"]}}
        return FakeBackend(fn)
    raise ValueError(f"unknown backend {name!r}")


def build_state(view: ProviderView, rendered_rule: str, feedback: list, T: int) -> dict:
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


def run_procedure(cfg, rule_factory, focal: int, backend, cache: PromptCache, rendered_rule: str, train_seeds, eval_seed: int, locked: dict,
                  clip_episode5: bool = False, twin: bool = False) -> ProcedureResult:
    """Spec 5.4: five episodes with profit feedback; episodes 1 to 4 on dev-train seeds, episode 5 on the evaluation seed.
    `twin` clips the claim in every episode (the matched truthful twin); `clip_episode5` clips in episode 5 only (the
    closed-loop clipped-attack run), replaying unchanged prompts from the cache."""
    from .policies.llm import ActorCounters, LLMProvider
    assert len(train_seeds) == 4
    feedback: list[float] = []
    counters = ActorCounters()
    profits, last = [], None
    for ep, seed in enumerate((*train_seeds, eval_seed)):
        actor = LLMProvider(backend, cache, rendered_rule, cfg.providers[focal], feedback, cfg.T, counters)
        policy = Twin(actor) if (twin or (clip_episode5 and ep == 4)) else actor
        pols = [HonestMax() for _ in range(cfg.N)]; pols[focal] = policy
        res = run_episode(cfg, rule_factory(), pols, int(seed))
        profits.append(float(res.profit[focal])); feedback.append(float(res.profit[focal])); last = res
    limit = float(locked["h1"]["fallback_limit"])
    invalid = counters.fallbacks / max(counters.rounds, 1) > limit
    return ProcedureResult(profits=profits, fallback_rounds=counters.fallbacks, total_rounds=counters.rounds, invalid=invalid,
                           calls=counters.calls, cache_hits=counters.cache_hits, usage=dict(counters.usage), episode5=last)


@dataclass
class H1CellResult:
    attack: list
    twin: list
    clipped: list
    eval_seeds: tuple
    invalid_count: int
    inconclusive: bool
    calls: int
    new_calls_clipped: int
    usage: dict


def run_h1_cell(cfg, rule_factory, focal: int, backend, cache: PromptCache, rendered_rule: str, train_seeds, eval_seeds, locked: dict) -> H1CellResult:
    reps = int(locked["h1"]["repetitions"])
    eval_seeds = tuple(eval_seeds)[:reps]
    attack, twin, clipped = [], [], []
    usage = {"input_tokens": 0, "output_tokens": 0}; calls = 0; new_clipped = 0
    for s in eval_seeds:
        a = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, s, locked)
        t = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, s, locked, twin=True)
        c = run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, s, locked, clip_episode5=True)
        attack.append(a); twin.append(t); clipped.append(c)
        for r in (a, t, c):
            calls += r.calls
            for k in usage:
                usage[k] += r.usage[k]
        new_clipped += c.calls
    invalid_count = sum(1 for r in attack + twin + clipped if r.invalid)
    return H1CellResult(attack=attack, twin=twin, clipped=clipped, eval_seeds=eval_seeds, invalid_count=invalid_count,
                        inconclusive=invalid_count > int(locked["h1"]["invalid_limit"]), calls=calls, new_calls_clipped=new_clipped, usage=usage)


def _gross(res: EpisodeResult) -> float:
    return (res.W + res.audit_cost) / res.sstar


def h1_rows(result: H1CellResult, meta: dict) -> list[dict]:
    rows = []
    for k, s in enumerate(result.eval_seeds):
        a, t, c = result.attack[k], result.twin[k], result.clipped[k]
        N = len(a.episode5.profit); scale = a.episode5.sstar / N
        rows.append(dict(meta, rep=k, eval_seed=int(s), profit_attack=a.profits[4], profit_twin=t.profits[4], profit_clip=c.profits[4],
                         sstar=a.episode5.sstar, gain_vs_twin=(a.profits[4] - t.profits[4]) / scale,
                         eff_attack=_gross(a.episode5), eff_twin=_gross(t.episode5), eff_clip=_gross(c.episode5),
                         audit_cost_attack=a.episode5.audit_cost, fallback_rounds=a.fallback_rounds + t.fallback_rounds + c.fallback_rounds,
                         invalid=int(a.invalid or t.invalid or c.invalid)))
    return rows


def ask_comprehension(backend, cache: PromptCache, rendered_rule: str, questions: list) -> dict:
    payload = {"instructions": getattr(backend, "instructions", ""), "rule": rendered_rule, "questions": questions}
    key = request_hash(backend.name, backend.model, "comprehension", payload)
    resp = cache.get(key)
    if resp is None:
        resp = backend.complete("comprehension", payload); cache.put(key, resp)
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_llm_actor.py -v`
Expected: PASS (8 tests). No network is touched: only `FakeBackend` runs; `AnthropicBackend` and `JevBackend` import their SDKs lazily in `__init__`.

- [ ] **Step 5: Commit**

```bash
git add experiments/locked.yaml sim/llm_actor.py sim/policies/llm.py tests/test_llm_actor.py
git commit -m "feat: model actor with Anthropic, Jev, and fake backends behind a prompt-hash cache; H1 five-episode procedure, invalidity rule, clipped re-run, comprehension check"
```

---

### Task 5: Coverage study (cell selection, thresholds, joint fixture test, power, pools, replications, admission, report)

**Files:**
- Create: `sim/coverage.py`, `scripts/coverage_study.py`
- Modify: `sim/manifest.py` (a `coverage` section), `scripts/manifest.py` (print it)
- Test: `tests/test_coverage.py`, `tests/test_manifest.py` (one test)

**Interfaces:**
- Consumes: `bound`, `t_bound`, `t_interval`, `exact_t_bound_with_critical`, `Bound` (Task 2); `run_focal`, `Cell`, `SeedCache` (plan 2A `sim/cell.py`); `rule_from_params` (`sim/tuning.py`); `family_of`, `job_for`, `load_params`, `train_val` (`scripts/sweep.py`); `candidate_from_record`, `participant_diagnostics` (`sim/reference.py`); `locked["seeds"]["coverage"]`, `locked["intervals"]` (Task 1).
- Produces (`sim/coverage.py`):
  - `ENDPOINTS`: the eight `(statistic, side, level)` triples in spec order: `("gain","upper",0.95), ("gain","lower",0.95), ("eff","lower",0.95), ("eff","upper",0.95), ("loss_diff","lower",0.9875), ("loss_diff","upper",0.9875), ("gain","lower",0.9875), ("gain","upper",0.9875)`; `STATISTICS = ("gain", "eff", "loss_diff")`; `PROCEDURES_AT_N = {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)}`; `endpoint_key(stat, side, level, n) -> str` = `f"{stat}|{side}|{level}|{n}"`.
  - `skewness(x) -> float` (unbiased sample skewness; `nan` when `len(x) < 3` or zero variance), `sarle_bimodality(x) -> float` (`(g^2 + 1) / (k + 3 (n-1)^2 / ((n-2)(n-3)))` with unbiased `g`, excess kurtosis `k`; `nan` when `n < 4` or zero variance).
  - `select_cells(stats_by_cell: dict[str, dict], k: int = 3) -> list[str]`: `stats_by_cell[name] = {"skew_gain": float, "sarle_bans": float}`; each ranking sorts valid (finite) values descending with the cell name as the tie-break and drops `nan`; the selection interleaves the two rankings (`skew` first) skipping names already chosen until `2k` distinct names or both rankings are exhausted.
  - `seed_blocks(locked, cell_index: int, pool_factor: int = 1, rep_factor: int = 1) -> tuple[np.ndarray, dict[int, np.ndarray]]`: the pool seeds (`pool * pool_factor` consecutive integers from `start + cell_index * block`) and, per `n` in `n_grid`, an array of shape `(R_n * rep_factor, n)` of the following consecutive seeds; raises `ValueError` if the block is exceeded.
  - `CoverageCell(name, cfg, focal, rule, rule_factories: dict[str, Callable], attack_factories: dict[str, Callable], clip_factories: dict[str, Callable], ref_factory: Callable | None, pair: tuple[str, str] = ("B2", "B3"))`; `runs_per_seed(cell) -> int`; `observe(cell, seeds, cache) -> dict[str, np.ndarray]` with keys `gain`, `eff`, `loss_diff` (per seed: `gain = (profit_attack - profit_ref) / (S* / N)` under `cell.rule`, with `profit_ref = 0` when `ref_factory is None` (abstain); `eff = (W + audit_cost) / S*` of the attack run under `cell.rule`; `loss_diff = [eff(pair[0], clip) - eff(pair[0], attack)] - [eff(pair[1], clip) - eff(pair[1], attack)]`), reusing a run when `cell.rule` is in the pair.
  - `reference_interval(obs: np.ndarray, level: float) -> tuple[float, float, float]` = `(lo, hi, pool_se)`.
  - `covered(b: Bound, lo: float, hi: float) -> bool`: `b.value >= hi` for an upper bound, `b.value <= lo` for a lower bound.
  - `measure(samples: dict[str, np.ndarray], refs: dict[str, tuple[float, float]], n: int, procedures: tuple[str, ...], settings: dict) -> dict[str, float]`: `samples[stat]` has shape `(R, n)`; returns measured conservative coverage keyed by `f"{endpoint_key(stat, side, level, n)}|{procedure}"`.
  - `analytic_conservative_coverage(n: int, critical: float, M: int, ref_level: float = 0.95) -> float`: `1 - nct.cdf(-critical / sqrt(1 + n / M); df = n - 1, nc = -z_ref * sqrt(n / (M + n)))` with `z_ref = norm.ppf(0.5 + ref_level / 2)`.
  - `simulated_conservative_coverage(n, level, M, pools, reps, rng) -> float`: average over `pools` simulated normal pools of size `M` of the fraction of `reps` exact one-sided t bounds (upper side, by symmetry) that cover conservatively.
  - `thresholds(locked, M: int) -> dict[str, dict]` keyed by `f"{n}|{level}"` with `exact`, `margin`, `threshold` (= `exact - margin / 100`) for every `n` in `n_grid` and both levels.
  - `clopper_pearson_lower(k: int, n: int, conf: float) -> float`.
  - `joint_fixture(locked, n: int, M: int, R: int, thr: dict, trials: int, rng, cells: int = 6) -> dict` with `admitted`, `trials`, `lower_limit`, `conf`, `pass_`; one trial = `cells` fresh normal pools and `(R, n)` normal samples, the `t` procedure on all eight endpoints (the three statistics share one sample set), admitted when every endpoint at every cell is at least its threshold.
  - `control_power(n, level, deficit_points, M, R, threshold, nodes, ref_level=0.95) -> float`: Gauss-Hermite expectation over the pool-mean error of the binomial rejection probability of a one-sided t bound at critical `t.ppf(level - deficit_points / 100, n - 1)`.
  - `power_check(locked, M, R_by_n: dict[int, int], thr: dict) -> dict` keyed by `f"{n}|{level}"` with `power_200`, `power_400`, `converged` (`|diff| <= 0.001`), `pass_` (`converged and power_200 >= 0.8`).
  - `fixture_and_power(locked, smoke: bool, rng) -> dict`: runs the fixture and the power check at the base `(M, R)`, then with `pool_factor = 2`, then `rep_factor = 2` as remedies, per `n`; returns `remedies`, `per_n` results, and `admissible_n: dict[int, bool]`.
  - `admission(measured: dict[str, dict[str, float]], thr: dict, locked) -> dict`: `measured[cell][key]` as returned by `measure`; returns `procedure_admitted: {f"{proc}|{n}": bool}` (every endpoint at every cell at or above threshold), `method_at_n: {str(n): proc | None}` (the first admitted procedure in `PROCEDURES_AT_N[n]`), `admitted_sides: {endpoint_key: proc | None}`, and `consequences: {"h1": "confirmatory" | "exploratory", "parametrized": "percentile_n20" | "studentized_n20" | "studentized_n40" | "inconclusive", "final_eval_n": 20 | 40 | None}`.
  - `write_report(path, report: dict) -> str` (sha256 of the written bytes), `load_report(path) -> dict`.
- Produces (`sim/manifest.py`): `coverage_cells(locked, selection: list[dict] | None) -> list[CellSpec]` with `section = "coverage"`, `kind = "coverage_pool"`, `runs = runs_per_seed * (pool + sum_n R_n * n)` per selected cell; without a selection file the six cells are listed as `coverage_estimate` with 5 runs per seed; `enumerate_manifest` appends them and `totals` reports `coverage` separately from the search gate.
- Produces (`scripts/coverage_study.py`): CLI `--sweep-out DIR --calibration PATH --tuned-dir DIR --out PATH [--smoke] [--workers K] [--select-only]`; writes the report and `experiments/coverage_cells.json` (the selection with ranking statistics and `runs_per_seed`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_coverage.py
import json
import numpy as np
import pytest
from scipy import stats
from sim.coverage import (ENDPOINTS, PROCEDURES_AT_N, endpoint_key, skewness, sarle_bimodality, select_cells, seed_blocks, CoverageCell,
                          runs_per_seed, observe, reference_interval, covered, measure, analytic_conservative_coverage,
                          simulated_conservative_coverage, thresholds, clopper_pearson_lower, joint_fixture, control_power, power_check,
                          admission, write_report, load_report)
from sim.cell import SeedCache
from sim.config import MarketConfig
from sim.intervals import Bound
from sim.locked import load_locked
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.policies.families import D1
from sim.policies.honest import HonestMax


def test_endpoints_and_moments():
    assert len(ENDPOINTS) == 8 and ENDPOINTS[0] == ("gain", "upper", 0.95) and ENDPOINTS[4] == ("loss_diff", "lower", 0.9875)
    assert PROCEDURES_AT_N == {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)}
    assert endpoint_key("gain", "upper", 0.95, 20) == "gain|upper|0.95|20"
    x = np.array([1.0, 2.0, 3.0, 10.0])
    assert skewness(x) == pytest.approx(stats.skew(x, bias=False))
    g, k, n = stats.skew(x, bias=False), stats.kurtosis(x, bias=False), 4
    assert sarle_bimodality(x) == pytest.approx((g * g + 1) / (k + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))))
    assert np.isnan(skewness(np.array([1.0, 1.0, 1.0]))) and np.isnan(sarle_bimodality(np.array([1.0, 2.0, 3.0])))


def test_cell_selection_handles_degenerate_rankings():
    st = {"a": {"skew_gain": 3.0, "sarle_bans": 0.9}, "b": {"skew_gain": 2.0, "sarle_bans": 0.1}, "c": {"skew_gain": 1.0, "sarle_bans": 0.5},
          "d": {"skew_gain": 0.5, "sarle_bans": 0.8}, "e": {"skew_gain": 0.1, "sarle_bans": float("nan")}, "f": {"skew_gain": float("nan"), "sarle_bans": 0.7},
          "g": {"skew_gain": -1.0, "sarle_bans": 0.0}}
    assert select_cells(st, k=3) == ["a", "d", "b", "f", "c", "e"]     # skew: a b c d e; sarle: a d f c b g; interleaved, no repeats
    assert select_cells({"a": {"skew_gain": 1.0, "sarle_bans": 1.0}, "b": {"skew_gain": 0.0, "sarle_bans": float("nan")}}, k=3) == ["a", "b"]


def test_seed_blocks_are_fresh_disjoint_and_bounded():
    lk = load_locked(); cov = lk["seeds"]["coverage"]
    pool, reps = seed_blocks(lk, 0)
    assert pool[0] == cov["start"] and len(pool) == cov["pool"]
    assert reps[10].shape == (2000, 10) and reps[20].shape == (2000, 20) and reps[40].shape == (4000, 40)
    allseeds = np.concatenate([pool] + [r.ravel() for r in reps.values()])
    assert len(np.unique(allseeds)) == len(allseeds) and allseeds.max() < cov["start"] + cov["block"]
    pool1, _ = seed_blocks(lk, 1)
    assert pool1[0] == cov["start"] + cov["block"]
    pool2, reps2 = seed_blocks(lk, 2, pool_factor=2, rep_factor=2)
    assert len(pool2) == 2 * cov["pool"] and reps2[40].shape == (8000, 40)
    with pytest.raises(ValueError):
        seed_blocks(dict(lk, seeds=dict(lk["seeds"], coverage=dict(cov, block=1000))), 0)


def small_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=c.alpha, budget=0.3)


def test_observe_runs_per_seed_and_statistics_are_finite():
    cfg = small_cfg()
    rules = {"B1": lambda: PostedPrices(0.2, 0.35, 0.5), "B2": lambda: PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3),
             "B3": lambda: SecondScore(0.2, 0.35, 0.5, tol=0.12, L=3)}
    cheat = {"u": 1.0, "m": 1.0, "clip": 0.0}
    att = {r: (lambda: D1.make(cheat)) for r in rules}; clip = {r: (lambda: D1.make(D1.project(cheat))) for r in rules}
    cell = CoverageCell("x", cfg, 3, "B1", rules, att, clip, ref_factory=HonestMax)
    assert runs_per_seed(cell) == 3 + 4
    cell2 = CoverageCell("y", cfg, 3, "B2", rules, att, clip, ref_factory=None)
    assert runs_per_seed(cell2) == 2 + 2
    obs = observe(cell, np.arange(5), SeedCache())
    assert set(obs) == {"gain", "eff", "loss_diff"} and all(v.shape == (5,) and np.all(np.isfinite(v)) for v in obs.values())
    obs2 = observe(cell2, np.arange(5), SeedCache())
    assert np.array_equal(obs["loss_diff"], obs2["loss_diff"])       # the pair statistic does not depend on the cell's rule


def test_reference_interval_and_conservative_scoring():
    rng = np.random.default_rng(1); pool = rng.normal(0.0, 1.0, size=5000)
    lo, hi, se = reference_interval(pool, 0.95)
    assert lo < pool.mean() < hi and se == pytest.approx(pool.std(ddof=1) / np.sqrt(5000)) and hi - lo == pytest.approx(2 * stats.t.ppf(0.975, 4999) * se)
    assert covered(Bound(hi + 0.01, "upper", 0.95, "t", False, 10), lo, hi) and not covered(Bound(hi - 0.01, "upper", 0.95, "t", False, 10), lo, hi)
    assert covered(Bound(lo - 0.01, "lower", 0.95, "t", False, 10), lo, hi) and not covered(Bound(lo + 0.01, "lower", 0.95, "t", False, 10), lo, hi)


def test_measure_runs_every_endpoint_and_procedure():
    rng = np.random.default_rng(2)
    samples = {s: rng.normal(size=(50, 20)) for s in ("gain", "eff", "loss_diff")}
    refs = {s: (-0.05, 0.05) for s in samples}
    out = measure(samples, refs, 20, ("percentile", "studentized"), {"bootstrap_resamples": 200, "bootstrap_seed": 3})
    assert len(out) == 16 and all(0.0 <= v <= 1.0 for v in out.values())
    assert "gain|upper|0.95|20|percentile" in out and "loss_diff|lower|0.9875|20|studentized" in out


def test_analytic_threshold_matches_simulation_and_nominal_limit():
    assert analytic_conservative_coverage(20, stats.t.ppf(0.95, 19), 10**9) == pytest.approx(0.95, abs=1e-4)
    a = analytic_conservative_coverage(20, stats.t.ppf(0.95, 19), 2000)
    s = simulated_conservative_coverage(20, 0.95, 2000, pools=40, reps=4000, rng=np.random.default_rng(4))
    assert a < 0.95 and abs(a - s) < 0.01
    lk = load_locked(); thr = thresholds(lk, 35000)
    assert set(thr) == {f"{n}|{lv}" for n in (10, 20, 40) for lv in (0.95, 0.9875)}
    assert thr["20|0.95"]["threshold"] == pytest.approx(thr["20|0.95"]["exact"] - 0.02) and thr["40|0.9875"]["margin"] == 1.0


def test_clopper_pearson_and_joint_fixture_small():
    assert clopper_pearson_lower(190, 200, 1 - 0.05 / 3) == pytest.approx(0.9063, abs=5e-4)
    assert clopper_pearson_lower(189, 200, 1 - 0.05 / 3) < 0.9 and clopper_pearson_lower(0, 10, 0.95) == 0.0
    lk = load_locked(); thr = thresholds(lk, 500)
    res = joint_fixture(lk, 20, 500, 60, thr, trials=8, rng=np.random.default_rng(5), cells=2)
    assert res["trials"] == 8 and 0 <= res["admitted"] <= 8 and 0.0 <= res["lower_limit"] <= 1.0 and isinstance(res["pass_"], bool)


def test_control_power_is_high_for_a_3_point_deficit_and_quadrature_converges():
    lk = load_locked(); thr = thresholds(lk, 35000)
    p200 = control_power(20, 0.95, 3.0, 35000, 2000, thr["20|0.95"]["threshold"], nodes=200)
    p400 = control_power(20, 0.95, 3.0, 35000, 2000, thr["20|0.95"]["threshold"], nodes=400)
    assert p200 > 0.8 and abs(p200 - p400) <= 0.001
    pc = power_check(lk, 35000, {10: 2000, 20: 2000, 40: 4000}, thr)
    assert set(pc) == set(thr) and all(v["converged"] for v in pc.values())


def test_admission_follows_the_remedy_order_and_sets_consequences():
    lk = load_locked(); thr = {f"{n}|{lv}": {"threshold": 0.9} for n in (10, 20, 40) for lv in (0.95, 0.9875)}
    def cellcov(fail: set):
        out = {}
        for n, procs in PROCEDURES_AT_N.items():
            for proc in procs:
                for st, side, lv in ENDPOINTS:
                    out[f"{endpoint_key(st, side, lv, n)}|{proc}"] = 0.5 if (proc, n) in fail else 0.95
        return out
    a = admission({"c1": cellcov(set()), "c2": cellcov(set())}, thr, lk)
    assert a["method_at_n"] == {"10": "t", "20": "percentile", "40": "studentized"}
    assert a["consequences"] == {"h1": "confirmatory", "parametrized": "percentile_n20", "final_eval_n": 20}
    assert a["admitted_sides"]["gain|upper|0.95|20"] == "percentile" and a["admitted_sides"]["eff|lower|0.95|10"] == "t"
    b = admission({"c1": cellcov({("percentile", 20)}), "c2": cellcov(set())}, thr, lk)     # one cell fails percentile: remedy 1
    assert b["method_at_n"]["20"] == "studentized" and b["consequences"]["parametrized"] == "studentized_n20"
    c = admission({"c1": cellcov({("percentile", 20), ("studentized", 20)})}, thr, lk)
    assert c["method_at_n"]["20"] is None and c["consequences"] == {"h1": "confirmatory", "parametrized": "studentized_n40", "final_eval_n": 40}
    d = admission({"c1": cellcov({("t", 10), ("percentile", 20), ("studentized", 20), ("studentized", 40)})}, thr, lk)
    assert d["consequences"] == {"h1": "exploratory", "parametrized": "inconclusive", "final_eval_n": None}
    assert d["admitted_sides"]["gain|upper|0.95|20"] is None


def test_report_roundtrip_and_hash(tmp_path):
    rep = {"selection": ["a"], "admitted_sides": {"gain|upper|0.95|20": "percentile"}}
    h = write_report(tmp_path / "r.json", rep)
    assert len(h) == 64 and load_report(tmp_path / "r.json") == rep
```

Append to `tests/test_manifest.py`:

```python
def test_manifest_lists_the_coverage_study_outside_the_search_gate():
    from sim.manifest import coverage_cells, enumerate_manifest, totals
    lk = load_locked()
    est = coverage_cells(lk, None)
    assert len(est) == 6 and all(c.section == "coverage" and c.kind == "coverage_estimate" for c in est)
    cov = lk["seeds"]["coverage"]; seeds_per_cell = cov["pool"] + sum(int(r) * int(n) for n, r in cov["replications"].items())
    assert est[0].runs == 5 * seeds_per_cell
    sel = [{"name": "B2_D1_beta0.05_rho0.5_median_development", "rule": "B2", "family": "D1", "position": "median", "runs_per_seed": 4}]
    real = coverage_cells(lk, sel)
    assert len(real) == 1 and real[0].kind == "coverage_pool" and real[0].runs == 4 * seeds_per_cell
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    t = totals(cells)
    assert t["coverage"] == 6 * 5 * seeds_per_cell and t["search_gate"] == totals([c for c in cells if c.section != "coverage"])["search_gate"]
```

(Read `totals` in `sim/manifest.py` before writing the test's last line: the key that holds the search-gate total may have another name there; use that name.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_coverage.py tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.coverage'` and `ImportError: cannot import name 'coverage_cells'`.

- [ ] **Step 3: Write the implementation**

```python
# sim/coverage.py
"""Coverage study (spec 8): mechanical cell selection, fresh seed blocks, per-seed observations for the eight endpoints,
conservative scoring against the reference-mean interval, analytic thresholds with their simulation check, the
pre-registered joint fixture test and control power, admission in the remedy order, and the report."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from scipy import stats

from .cell import Cell, SeedCache, run_focal
from .intervals import Bound, bound, t_interval

STATISTICS = ("gain", "eff", "loss_diff")
ENDPOINTS = (("gain", "upper", 0.95), ("gain", "lower", 0.95), ("eff", "lower", 0.95), ("eff", "upper", 0.95),
             ("loss_diff", "lower", 0.9875), ("loss_diff", "upper", 0.9875), ("gain", "lower", 0.9875), ("gain", "upper", 0.9875))
PROCEDURES_AT_N = {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)}
LEVELS = (0.95, 0.9875)


def endpoint_key(stat: str, side: str, level: float, n: int) -> str:
    return f"{stat}|{side}|{level}|{n}"


# ---- selection -------------------------------------------------------------------------------------------------------

def skewness(x) -> float:
    x = np.asarray(x, dtype=float)
    if x.size < 3 or np.std(x) == 0.0:
        return float("nan")
    return float(stats.skew(x, bias=False))


def sarle_bimodality(x) -> float:
    x = np.asarray(x, dtype=float); n = x.size
    if n < 4 or np.std(x) == 0.0:
        return float("nan")
    g = float(stats.skew(x, bias=False)); k = float(stats.kurtosis(x, bias=False))
    return (g * g + 1.0) / (k + 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3)))


def select_cells(stats_by_cell: dict, k: int = 3) -> list:
    """Top k by gain skewness and top k by the Sarle coefficient of ban counts, interleaved (skewness first), overlaps
    filled from the next unused entry of either ranking; nan ranks last by exclusion (spec 8)."""
    def ranking(key):
        valid = [(float(v[key]), name) for name, v in stats_by_cell.items() if math.isfinite(float(v[key]))]
        return [name for _, name in sorted(valid, key=lambda p: (-p[0], p[1]))]
    r = [ranking("skew_gain"), ranking("sarle_bans")]; cur = [0, 0]; chosen: list = []
    turn = 0; stalled = 0
    while len(chosen) < 2 * k and stalled < 2:
        lst = r[turn]
        while cur[turn] < len(lst) and lst[cur[turn]] in chosen:
            cur[turn] += 1
        if cur[turn] < len(lst):
            chosen.append(lst[cur[turn]]); cur[turn] += 1; stalled = 0
        else:
            stalled += 1
        turn = 1 - turn
    return chosen


# ---- seeds and observations ------------------------------------------------------------------------------------------

def seed_blocks(locked: dict, cell_index: int, pool_factor: int = 1, rep_factor: int = 1):
    cov = locked["seeds"]["coverage"]
    start = int(cov["start"]) + int(cell_index) * int(cov["block"])
    pool_n = int(cov["pool"]) * int(pool_factor)
    pool = np.arange(start, start + pool_n, dtype=np.int64)
    nxt = start + pool_n; reps = {}
    for n in cov["n_grid"]:
        R = int(cov["replications"][str(n)]) * int(rep_factor)
        reps[int(n)] = np.arange(nxt, nxt + R * int(n), dtype=np.int64).reshape(R, int(n)); nxt += R * int(n)
    if nxt > start + int(cov["block"]):
        raise ValueError(f"coverage block of {cov['block']} seeds is too small for pool {pool_n} and replications {sum(r.size for r in reps.values())}")
    return pool, reps


@dataclass
class CoverageCell:
    name: str
    cfg: object
    focal: int
    rule: str
    rule_factories: dict
    attack_factories: dict
    clip_factories: dict
    ref_factory: Callable | None
    pair: tuple = ("B2", "B3")


def runs_per_seed(cell: CoverageCell) -> int:
    own = 2 + (0 if cell.ref_factory is None else 1)                       # attack, clip, reference (abstain needs no run)
    pair = sum(2 for r in cell.pair if r != cell.rule)                     # attack and clip under each partner rule not already run
    return own + pair


def _run(cell: CoverageCell, rule: str, factory: Callable, seeds, cache: SeedCache):
    c = Cell(cfg=cell.cfg, rule_factory=cell.rule_factories[rule], focal=cell.focal, seeds=tuple(int(s) for s in seeds), name=f"{cell.name}/{rule}")
    return run_focal(c, factory, cache).results


def observe(cell: CoverageCell, seeds, cache: SeedCache) -> dict:
    seeds = [int(s) for s in seeds]; N = cell.cfg.N; f = cell.focal
    att: dict = {}; clp: dict = {}
    for rule in {cell.rule, *cell.pair}:
        att[rule] = _run(cell, rule, cell.attack_factories[rule], seeds, cache)
        clp[rule] = _run(cell, rule, cell.clip_factories[rule], seeds, cache)
    ref = _run(cell, cell.rule, cell.ref_factory, seeds, cache) if cell.ref_factory is not None else None
    sstar = np.array([r.sstar for r in att[cell.rule]]); scale = sstar / N
    p_att = np.array([r.profit[f] for r in att[cell.rule]]); p_ref = np.array([r.profit[f] for r in ref]) if ref is not None else np.zeros_like(p_att)
    eff = lambda rs: np.array([(r.W + r.audit_cost) / r.sstar for r in rs])
    a, b = cell.pair
    return {"gain": (p_att - p_ref) / scale, "eff": eff(att[cell.rule]),
            "loss_diff": (eff(clp[a]) - eff(att[a])) - (eff(clp[b]) - eff(att[b]))}


# ---- scoring ---------------------------------------------------------------------------------------------------------

def reference_interval(obs, level: float):
    obs = np.asarray(obs, dtype=float); lo, hi = t_interval(obs, level)
    return lo, hi, float(obs.std(ddof=1) / np.sqrt(obs.size))


def covered(b: Bound, lo: float, hi: float) -> bool:
    return bool(b.value >= hi) if b.side == "upper" else bool(b.value <= lo)


def measure(samples: dict, refs: dict, n: int, procedures, settings: dict) -> dict:
    out = {}
    for stat in STATISTICS:
        X = np.asarray(samples[stat], dtype=float); lo, hi = refs[stat]
        eps = [(side, lv) for s, side, lv in ENDPOINTS if s == stat]
        for proc in procedures:
            hits = {e: 0 for e in eps}
            for row in X:
                for side, lv in eps:
                    if covered(bound(proc, row, side, lv, settings), lo, hi):
                        hits[(side, lv)] += 1
            for (side, lv), h in hits.items():
                out[f"{endpoint_key(stat, side, lv, n)}|{proc}"] = h / X.shape[0]
    return out


# ---- thresholds, fixture, power --------------------------------------------------------------------------------------

def analytic_conservative_coverage(n: int, critical: float, M: int, ref_level: float = 0.95) -> float:
    """P(x_bar + c s / sqrt(n) >= pool_mean + z sigma / sqrt(M)) for normal data: the pool mean error and the sample mean
    combine into one normal, so the statistic is noncentral t with df n - 1 (spec 8 threshold)."""
    z = stats.norm.ppf(0.5 + ref_level / 2.0)
    nc = -z * math.sqrt(n / (M + n))
    return float(1.0 - stats.nct.cdf(-critical / math.sqrt(1.0 + n / M), n - 1, nc))


def simulated_conservative_coverage(n: int, level: float, M: int, pools: int, reps: int, rng) -> float:
    crit = stats.t.ppf(level, n - 1); hits = 0; total = 0
    for _ in range(pools):
        pool = rng.normal(size=M); _, hi = t_interval(pool, 0.95)
        X = rng.normal(size=(reps, n)); U = X.mean(axis=1) + crit * X.std(axis=1, ddof=1) / math.sqrt(n)
        hits += int((U >= hi).sum()); total += reps
    return hits / total


def thresholds(locked: dict, M: int) -> dict:
    iv = locked["intervals"]; out = {}
    for n in locked["seeds"]["coverage"]["n_grid"]:
        for lv in LEVELS:
            exact = analytic_conservative_coverage(int(n), float(stats.t.ppf(lv, int(n) - 1)), int(M), float(iv["reference_level"]))
            margin = float(iv["margins"][str(lv)])
            out[f"{n}|{lv}"] = {"n": int(n), "level": lv, "exact": exact, "margin": margin, "threshold": exact - margin / 100.0}
    return out


def clopper_pearson_lower(k: int, n: int, conf: float) -> float:
    return 0.0 if k == 0 else float(stats.beta.ppf(1.0 - conf, k, n - k + 1))


def joint_fixture(locked: dict, n: int, M: int, R: int, thr: dict, trials: int, rng, cells: int = 6) -> dict:
    iv = locked["intervals"]; conf = 1.0 - 0.05 / 3.0; admitted = 0
    crit = {lv: float(stats.t.ppf(lv, n - 1)) for lv in LEVELS}
    for _ in range(trials):
        ok = True
        for _c in range(cells):
            pool = rng.normal(size=M); lo, hi = t_interval(pool, float(iv["reference_level"]))
            X = rng.normal(size=(R, n)); m = X.mean(axis=1); se = X.std(axis=1, ddof=1) / math.sqrt(n)
            for stat, side, lv in ENDPOINTS:
                cov = float(((m + crit[lv] * se) >= hi).mean()) if side == "upper" else float(((m - crit[lv] * se) <= lo).mean())
                if cov < thr[f"{n}|{lv}"]["threshold"]:
                    ok = False; break
            if not ok:
                break
        admitted += int(ok)
    ll = clopper_pearson_lower(admitted, trials, conf)
    return {"n": n, "M": M, "R": R, "trials": trials, "admitted": admitted, "conf": conf, "lower_limit": ll, "pass_": bool(ll >= 0.9)}


def control_power(n: int, level: float, deficit_points: float, M: int, R: int, threshold: float, nodes: int, ref_level: float = 0.95) -> float:
    """Expected binomial rejection probability of the negative control (a t bound whose true coverage is the nominal level
    minus the deficit), integrated over the pool-mean error with Gauss-Hermite quadrature (spec 8, power)."""
    c = float(stats.t.ppf(level - deficit_points / 100.0, n - 1))
    z = stats.norm.ppf(0.5 + ref_level / 2.0); delta = z / math.sqrt(M)
    x, w = np.polynomial.hermite.hermgauss(int(nodes))
    eps = math.sqrt(2.0) / math.sqrt(M) * x                       # pool-mean error in units of sigma
    p = 1.0 - stats.nct.cdf(-c, n - 1, -(eps + delta) * math.sqrt(n))
    need = int(math.ceil(R * threshold))                         # admitted iff hits >= need; rejected iff hits <= need - 1
    rej = stats.binom.cdf(need - 1, R, p)
    return float((w * rej).sum() / math.sqrt(math.pi))


def power_check(locked: dict, M: int, R_by_n: dict, thr: dict) -> dict:
    iv = locked["intervals"]; out = {}
    for key, t in thr.items():
        n, lv = t["n"], t["level"]; d = float(iv["deficits"][str(lv)]); R = int(R_by_n[int(n)])
        p200 = control_power(n, lv, d, M, R, t["threshold"], int(iv["quadrature_nodes"]), float(iv["reference_level"]))
        p400 = control_power(n, lv, d, M, R, t["threshold"], 2 * int(iv["quadrature_nodes"]), float(iv["reference_level"]))
        conv = abs(p200 - p400) <= 0.001
        out[key] = {"deficit": d, "power_200": p200, "power_400": p400, "converged": bool(conv), "pass_": bool(conv and p200 >= 0.8)}
    return out


def fixture_and_power(locked: dict, smoke: bool, rng) -> dict:
    cov = locked["seeds"]["coverage"]; iv = locked["intervals"]
    base_M = 200 if smoke else int(cov["pool"]); trials = 10 if smoke else int(iv["joint_trials"])
    base_R = {int(n): (20 if smoke else int(r)) for n, r in cov["replications"].items()}
    per_n = {}; admissible = {}; remedies = {}
    for n in cov["n_grid"]:
        n = int(n); attempts = []
        for pf, rf, label in ((1, 1, "base"), (2, 1, "double_M"), (2, 2, "double_R")):
            M = base_M * pf; R = base_R[n] * rf; thr = thresholds(locked, M)
            fx = joint_fixture(locked, n, M, R, thr, trials, rng)
            pw = {k: v for k, v in power_check(locked, M, {n: R}, {k: v for k, v in thr.items() if v["n"] == n}).items()}
            ok = fx["pass_"] and all(v["pass_"] for v in pw.values())
            attempts.append({"attempt": label, "pool_factor": pf, "rep_factor": rf, "fixture": fx, "power": pw, "pass_": bool(ok)})
            if ok:
                remedies[str(n)] = {"pool_factor": pf, "rep_factor": rf}; break
        per_n[str(n)] = attempts; admissible[str(n)] = bool(attempts[-1]["pass_"])
        remedies.setdefault(str(n), {"pool_factor": 2, "rep_factor": 2})
    return {"per_n": per_n, "admissible_n": admissible, "remedies": remedies, "base_M": base_M, "base_R": {str(k): v for k, v in base_R.items()}}


# ---- admission -------------------------------------------------------------------------------------------------------

def admission(measured: dict, thr: dict, locked: dict) -> dict:
    procedure_admitted = {}
    for n, procs in PROCEDURES_AT_N.items():
        for proc in procs:
            ok = True
            for cell, cov in measured.items():
                for stat, side, lv in ENDPOINTS:
                    key = f"{endpoint_key(stat, side, lv, n)}|{proc}"
                    if key not in cov or cov[key] < thr[f"{n}|{lv}"]["threshold"]:
                        ok = False
            procedure_admitted[f"{proc}|{n}"] = bool(ok and len(measured) > 0)
    method_at_n = {str(n): next((p for p in procs if procedure_admitted[f"{p}|{n}"]), None) for n, procs in PROCEDURES_AT_N.items()}
    admitted_sides = {endpoint_key(s, side, lv, n): method_at_n[str(n)] for n in PROCEDURES_AT_N for s, side, lv in ENDPOINTS}
    h1 = "confirmatory" if method_at_n["10"] == "t" else "exploratory"
    if method_at_n["20"] == "percentile":
        par, fe = "percentile_n20", 20
    elif method_at_n["20"] == "studentized":
        par, fe = "studentized_n20", 20
    elif method_at_n["40"] == "studentized":
        par, fe = "studentized_n40", 40
    else:
        par, fe = "inconclusive", None
    return {"procedure_admitted": procedure_admitted, "method_at_n": method_at_n, "admitted_sides": admitted_sides,
            "consequences": {"h1": h1, "parametrized": par, "final_eval_n": fe}}


def write_report(path, report: dict) -> str:
    data = json.dumps(report, sort_keys=True, indent=1, default=float).encode()
    Path(path).parent.mkdir(parents=True, exist_ok=True); Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def load_report(path) -> dict:
    return json.loads(Path(path).read_text())
```

Add to `sim/manifest.py` (after `_bank_total`):

```python
def coverage_cells(locked: dict, selection: list | None) -> list[CellSpec]:
    """The coverage study's pools and replications (spec 8), listed outside the search gate. Without the selection
    file (before the study has run), six cells are estimated at five runs per seed."""
    cov = locked["seeds"]["coverage"]; bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"])
    seeds_per_cell = int(cov["pool"]) + sum(int(r) * int(n) for n, r in cov["replications"].items())
    if selection is None:
        return [CellSpec("coverage", "?", "?", bh, rho0, "?", "coverage_estimate", 5 * seeds_per_cell, True, False, f"coverage_estimate_{i}") for i in range(6)]
    return [CellSpec("coverage", s["rule"], s["family"], bh, rho0, s["position"], "coverage_pool", int(s["runs_per_seed"]) * seeds_per_cell, True, False,
                     "coverage_" + s["name"]) for s in selection]
```

and in `enumerate_manifest`, after the existing cells are built, append `coverage_cells(locked, _load_selection())` where `_load_selection()` returns the parsed `experiments/coverage_cells.json` if it exists, else `None`; in `totals`, add `"coverage": sum(c.runs for c in cells if c.section == "coverage")` and exclude `section == "coverage"` from the search-gate total (read the function to find the key it uses). In `scripts/manifest.py`, print the coverage total on its own line as `coverage (outside the search gate): <runs> runs, <hours> core-hours at the benchmark rate`.

```python
# scripts/coverage_study.py
"""Run the coverage study (spec 8) on the sweep's reference records: select 6 cells, compute thresholds, run the joint
fixture test and the power check with the registered remedies, then the real pools and replications, admit the
procedures in the remedy order, and write experiments/coverage_report.json and experiments/coverage_cells.json."""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import family_of, job_for, load_params, make_cell, read_dir, settings_for, train_val  # noqa: E402
from sim.calibrate import load_calibration  # noqa: E402
from sim.cell import SeedCache, run_focal  # noqa: E402
from sim.coverage import (CoverageCell, STATISTICS, admission, fixture_and_power, load_report, measure, observe, reference_interval,  # noqa: E402
                          runs_per_seed, sarle_bimodality, seed_blocks, select_cells, skewness, thresholds, write_report, PROCEDURES_AT_N)
from sim.locked import load_locked  # noqa: E402
from sim.manifest import enumerate_manifest  # noqa: E402
from sim.records import cfg_from_dict  # noqa: E402
from sim.reference import candidate_from_record, participant_diagnostics  # noqa: E402
from sim.schedule import budget_from_locked  # noqa: E402
from sim.tuning import rule_from_params  # noqa: E402


def universe(sweep_out: Path, locked: dict) -> dict:
    """The 18 development cells at beta_headline: their reference records keyed by cell name."""
    refs = read_dir(sweep_out / "reference"); bh = float(locked["beta_headline"])
    return {name: rec for name, rec in refs.items() if rec["spec"]["section"] == "development" and float(rec["spec"]["beta"]) == bh}


def job_from_record(rec: dict, locked: dict) -> dict:
    """The sweep's job dict rebuilt from a stage record (records store every job field except `locked`)."""
    return {**{k: rec[k] for k in ("spec", "cfg", "params", "budget", "smoke", "settings_hash", "salt_hash")}, "locked": locked}


def cell_statistics(name: str, rec: dict, locked: dict) -> dict:
    """Per-seed gain on dev-train from the record; per-seed focal bans from re-running the attack on dev-train seeds."""
    gain = np.array(rec["attack_per_seed_normalized"]) - np.array(rec["reference_per_seed_normalized"])
    job = job_from_record(rec, locked); train, _, _ = train_val(job); fam = family_of(job["spec"]["family"])
    cell = make_cell(job, train); res = run_focal(cell, lambda: fam.make(rec["attack_knobs"]), SeedCache()).results
    bans = np.array([participant_diagnostics(r, cell.cfg, cell.focal)["focal_bans"] for r in res], dtype=float)
    return {"skew_gain": skewness(gain), "sarle_bans": sarle_bimodality(bans), "n_train": int(len(gain))}


def build_cell(name: str, recs: dict, rec: dict, locked: dict) -> CoverageCell:
    job = job_from_record(rec, locked); cfg = cfg_from_dict(job["cfg"]); fam = family_of(job["spec"]["family"]); spec = job["spec"]
    rule_f, att_f, clip_f = {}, {}, {}
    for rule in ("B1", "B2", "B3"):
        partner = next(r for n, r in recs.items() if r["spec"]["rule"] == rule and r["spec"]["family"] == spec["family"] and r["spec"]["position"] == spec["position"])
        params = partner["params"]; knobs = partner["attack_knobs"]
        rule_f[rule] = (lambda p=params, r=rule: rule_from_params(r, p))
        att_f[rule] = (lambda k=knobs, f=fam: f.make(k)); clip_f[rule] = (lambda k=knobs, f=fam: f.make(f.project(k)))
    cand = candidate_from_record(fam, rec["candidate"])
    ref_factory = None if rec["candidate"]["name"] == "abstain" else cand.policy_factory
    return CoverageCell(name, cfg, make_cell(job, (0,)).focal, spec["rule"], rule_f, att_f, clip_f, ref_factory)


def run_cell(args) -> tuple:
    name, cell, locked, index, pool_factor, rep_factor, smoke = args
    cov = locked["seeds"]["coverage"]; settings = dict(locked["intervals"])
    if smoke:
        settings["bootstrap_resamples"] = 200
    pool, reps = seed_blocks(locked, index, pool_factor, rep_factor)
    if smoke:
        pool = pool[:200]; reps = {n: r[:20] for n, r in reps.items()}
    cache = SeedCache()
    pobs = observe(cell, pool, cache)
    refs = {s: reference_interval(pobs[s], float(locked["intervals"]["reference_level"])) for s in STATISTICS}
    measured = {}
    for n, S in reps.items():
        flat = observe(cell, S.ravel(), cache)
        samples = {s: flat[s].reshape(S.shape) for s in STATISTICS}
        measured.update(measure(samples, {s: refs[s][:2] for s in STATISTICS}, int(n), PROCEDURES_AT_N[int(n)], settings))
    return name, {"measured": measured, "pool_mean": {s: float(pobs[s].mean()) for s in STATISTICS},
                  "pool_se": {s: refs[s][2] for s in STATISTICS}, "pool_size": int(len(pool)),
                  "replications": {str(n): int(S.shape[0]) for n, S in reps.items()},
                  "replication_se": {str(n): float(np.sqrt(0.95 * 0.05 / S.shape[0])) for n, S in reps.items()}, "runs": runs_per_seed(cell) * (len(pool) + sum(S.size for S in reps.values()))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-out", dest="sweep_out", required=True)
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None)
    ap.add_argument("--out", default="experiments/coverage_report.json")
    ap.add_argument("--cells-out", dest="cells_out", default="experiments/coverage_cells.json")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--select-only", dest="select_only", action="store_true")
    a = ap.parse_args()
    lk = load_locked(); sweep_out = Path(a.sweep_out)
    recs = universe(sweep_out, lk)
    if len(recs) != 18 and not a.smoke:
        raise SystemExit(f"expected the 18 development cells at beta_headline in {sweep_out}/reference, found {len(recs)}")
    stats_by_cell = {name: cell_statistics(name, rec, lk) for name, rec in recs.items()}
    chosen = select_cells(stats_by_cell, k=3)
    cells = {name: build_cell(name, recs, recs[name], lk) for name in chosen}
    selection = [{"name": n, "rule": recs[n]["spec"]["rule"], "family": recs[n]["spec"]["family"], "position": recs[n]["spec"]["position"],
                  "runs_per_seed": runs_per_seed(cells[n]), **stats_by_cell[n]} for n in chosen]
    Path(a.cells_out).write_text(json.dumps(selection, indent=1))
    print("selected: " + ", ".join(chosen))
    if a.select_only:
        return
    rng = np.random.default_rng(int(lk["intervals"]["bootstrap_seed"]))
    fp = fixture_and_power(lk, a.smoke, rng)
    remedies = fp["remedies"]
    per_n_factor = {int(n): (r["pool_factor"], r["rep_factor"]) for n, r in remedies.items()}
    pool_factor = max(pf for pf, _ in per_n_factor.values()); rep_factor = max(rf for _, rf in per_n_factor.values())
    M = fp["base_M"] * pool_factor
    thr = thresholds(lk, M)
    jobs = [(name, cells[name], lk, i, pool_factor, rep_factor, a.smoke) for i, name in enumerate(chosen)]
    if a.workers > 1:
        with ProcessPoolExecutor(a.workers) as ex:
            results = dict(ex.map(run_cell, jobs))
    else:
        results = dict(map(run_cell, jobs))
    adm = admission({n: r["measured"] for n, r in results.items()}, thr, lk)
    for n, ok in fp["admissible_n"].items():                        # a failed fixture or power check makes every procedure at that n inadmissible
        if not ok:
            for proc in PROCEDURES_AT_N[int(n)]:
                adm["procedure_admitted"][f"{proc}|{n}"] = False
    adm = _recompute(adm)                                           # idempotent when nothing was struck
    report = {"smoke": bool(a.smoke), "selection": selection, "statistics": stats_by_cell, "M": M, "thresholds": thr,
              "fixture_and_power": fp, "cells": results, **adm, "manifest_runs": sum(r["runs"] for r in results.values())}
    h = write_report(a.out, report)
    print(json.dumps({"sha256": h, "method_at_n": adm["method_at_n"], "consequences": adm["consequences"], "runs": report["manifest_runs"]}))


def _recompute(adm: dict) -> dict:
    """Re-derive method_at_n, admitted_sides, and consequences after inadmissible n's were struck."""
    from sim.coverage import ENDPOINTS, endpoint_key
    method = {str(n): next((p for p in procs if adm["procedure_admitted"].get(f"{p}|{n}")), None) for n, procs in PROCEDURES_AT_N.items()}
    sides = {endpoint_key(s, side, lv, n): method[str(n)] for n in PROCEDURES_AT_N for s, side, lv in ENDPOINTS}
    h1 = "confirmatory" if method["10"] == "t" else "exploratory"
    par, fe = ("percentile_n20", 20) if method["20"] == "percentile" else ("studentized_n20", 20) if method["20"] == "studentized" \
        else ("studentized_n40", 40) if method["40"] == "studentized" else ("inconclusive", None)
    return {"procedure_admitted": adm["procedure_admitted"], "method_at_n": method, "admitted_sides": sides,
            "consequences": {"h1": h1, "parametrized": par, "final_eval_n": fe}}


if __name__ == "__main__":
    main()
```

The stage records store every job field except `locked` (see `base_record` in `scripts/sweep.py`); `job_from_record` rebuilds the job for `make_cell` and `train_val`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_coverage.py tests/test_manifest.py -v`
Expected: PASS (11 new tests). The analytic-versus-simulation test takes a few seconds (40 pools of 2,000 and 4,000 replications).

- [ ] **Step 5: Smoke the script end to end**

Run (after a smoke sweep exists, see plan 2A `scripts/sweep.py --smoke`):
```bash
uv run python scripts/sweep.py --stage all --rules B1,B2,B3 --calibration experiments/calibration_smoke.json --smoke --out /tmp/sweep_smoke
uv run python scripts/coverage_study.py --sweep-out /tmp/sweep_smoke --calibration experiments/calibration_smoke.json --smoke --out /tmp/coverage_smoke.json --cells-out /tmp/coverage_cells_smoke.json
uv run python scripts/manifest.py
```
Expected: the study prints six selected cell names, then a JSON line with `method_at_n`, `consequences`, and `runs`; the manifest prints the coverage total on its own line. Record in the ledger the manifest's coverage total and core-hours at the benchmark rate (expected about 6 cells x 255,000 seeds x 4 to 7 runs per seed, 6 to 11 million episodes, 50 to 90 core-hours at 29 ms; this replaces the spec's 210,000 estimate, see ruling D8).

- [ ] **Step 6: Commit**

```bash
git add sim/coverage.py scripts/coverage_study.py sim/manifest.py scripts/manifest.py tests/test_coverage.py tests/test_manifest.py
git commit -m "feat: coverage study with mechanical cell selection, analytic thresholds, joint fixture and power checks, remedies, admission, and report; coverage runs in the manifest outside the search gate"
```

---

### Task 6: The H1 runner with the token pilot, and T = 100 calibration

**Files:**
- Create: `scripts/h1.py`
- Modify: `scripts/calibrate.py` (`--T`)
- Test: `tests/test_h1_script.py`, `tests/test_calibrate.py` (one test)

**Interfaces:**
- Consumes: `run_h1_cell`, `h1_rows`, `comprehension_check`, `make_backend`, `PromptCache`, `estimate_cost_usd` (Task 4); `render`, `describe_record`, `load_vocabulary`, `comprehension_questions` (Task 3); `cell_config`, `load_calibration`, `calibrate` (`sim/calibrate.py`); `positions` (`sim/positions.py`); `rule_from_params` (`sim/tuning.py`); `load_params` (`scripts/sweep.py`); `locked["h1"]`.
- Produces (`scripts/h1.py`):
  - CLI `--backend {fake-honest,fake-cheat,anthropic,jev} --rules B1,B2,B3 --calibration PATH [--tuned-dir DIR] [--cache DIR] --out DIR [--eval-namespace dev_val|final_eval] [--smoke] [--pilot] [--pilot-calls 200] [--max-calls N] [--max-cost-usd X] [--prompt sealed/h1_prompt.txt]`.
  - `run_h1(o: dict) -> dict`: for every rule and every `beta` in `locked["h1"]["betas"]`: the comprehension check once per rule, then `run_h1_cell` at the median position with `train_seeds = dev_train[:4]` and `eval_seeds = <namespace>[:repetitions]`; appends `h1_rows` to `<out>/h1_rows.csv` with `backend, model, beta, eval_namespace, T` added to the meta; writes `<out>/h1_summary.json` with per-(rule, beta) `calls`, `cache_hits`, `usage`, `cost_usd`, `invalid_count`, `inconclusive`, `comprehension` scores, and the caps; stops with `SystemExit` naming the cap when `calls` exceeds `--max-calls` (default `locked["h1"]["calls_cap"]`) or the estimated cost exceeds `--max-cost-usd` (default `locked["h1"]["cost_cap_usd"]`, unlimited when null), after writing what has been completed.
  - `--pilot`: runs procedures on the first (rule, beta) until `--pilot-calls` new backend calls have been made, then writes `<out>/pilot_<backend>.json` with `calls, mean_input_tokens, mean_output_tokens, mean_latency_s, cost_per_call_usd, projected_cost_usd = cost_per_call * calls_cap` and exits 0; the user copies `projected_cost_usd` (rounded up) into `h1.cost_cap_usd` before the lock (ruling D6).
  - `--smoke`: `T = 6`, `repetitions = 2`, `betas = [0.05]`, the cache under `<out>/cache`.
  - `smoke_config(locked) -> MarketConfig` (N = 4, J = 30, T = 6 as in the tests) and `h1_config(locked, cal, beta, T) -> MarketConfig` (`cell_config` on the T = 100 base).
- Produces (`scripts/calibrate.py`): `--T N` replaces the horizon of the locked market before calibration; the written calibration carries `T` (already a `Calibration` field), and `cell_config` refuses a calibration whose `market_key` differs, which includes `T`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_h1_script.py
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sim.calibrate import calibrate, save_calibration
from sim.config import MarketConfig
from sim.locked import load_locked

ROOT = Path(__file__).resolve().parents[1]


def smoke_cal(tmp_path):
    c = MarketConfig.default()
    cfg = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)
    cal = calibrate(cfg, [4000, 4001]); p = tmp_path / "cal.json"; save_calibration(cal, p)
    return p


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "h1.py"), *args], capture_output=True, text=True, cwd=ROOT)


def test_h1_smoke_writes_rows_and_summary(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-cheat", "--rules", "B1,B2", "--calibration", str(cal), "--smoke", "--out", str(out))
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader((out / "h1_rows.csv").open()))
    assert len(rows) == 2 * 1 * 2 and {"rule", "beta", "rep", "eval_seed", "profit_attack", "profit_twin", "profit_clip", "gain_vs_twin", "invalid", "backend"} <= set(rows[0])
    s = json.loads((out / "h1_summary.json").read_text())
    assert set(s["cells"]) == {"B1|0.05", "B2|0.05"} and all(c["inconclusive"] is False for c in s["cells"].values())
    assert s["comprehension"]["B1"] >= 0 and s["calls_cap"] == load_locked()["h1"]["calls_cap"]
    r2 = run("--backend", "fake-cheat", "--rules", "B1,B2", "--calibration", str(cal), "--smoke", "--out", str(out))     # replay from cache
    assert r2.returncode == 0 and json.loads((out / "h1_summary.json").read_text())["calls"] == 0


def test_h1_refuses_when_the_calls_cap_is_exceeded(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", "--calibration", str(cal), "--smoke", "--out", str(out), "--max-calls", "10")
    assert r.returncode != 0 and "calls cap" in (r.stderr + r.stdout)
    assert (out / "h1_summary.json").exists()                     # what was completed is written


def test_h1_pilot_reports_cost_per_call(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", "--calibration", str(cal), "--smoke", "--out", str(out), "--pilot", "--pilot-calls", "30")
    assert r.returncode == 0, r.stderr
    p = json.loads((out / "pilot_fake.json").read_text())
    assert p["calls"] >= 30 and p["mean_input_tokens"] > 0 and p["projected_cost_usd"] == pytest.approx(p["cost_per_call_usd"] * load_locked()["h1"]["calls_cap"])


def test_h1_final_eval_namespace_refused_before_the_unseal(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", "--calibration", str(cal), "--smoke", "--out", str(out), "--eval-namespace", "final_eval")
    assert r.returncode != 0 and "final_eval" in (r.stderr + r.stdout)
```

Append to `tests/test_calibrate.py`:

```python
def test_calibrate_script_accepts_T_override(tmp_path):
    import json, subprocess, sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, str(root / "scripts" / "calibrate.py"), "--T", "7", "--seeds", "1", "--out", str(tmp_path / "c.json")],
                       capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stderr
    assert json.loads((tmp_path / "c.json").read_text())["T"] == 7
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_h1_script.py tests/test_calibrate.py -v`
Expected: FAIL: the four `h1.py` tests with `returncode != 0` (no such script), the calibrate test with `unrecognized arguments: --T`.

- [ ] **Step 3: Write the implementation**

In `scripts/calibrate.py`, add `ap.add_argument("--T", type=int, default=None, help="horizon override (H1 runs at T = 100)")` and, after building the base config, `if args.T is not None: base = dataclasses.replace(base, T=int(args.T))`.

```python
# scripts/h1.py
"""Run the H1 five-episode procedure (spec 5.4) against the baselines with a model backend, with the comprehension
check first, the calls and cost caps, replay from the prompt cache, and a token pilot that sets the cost cap."""
from __future__ import annotations

import argparse
import csv
import dataclasses
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import load_params  # noqa: E402
from sim.calibrate import cell_config, load_calibration  # noqa: E402
from sim.config import MarketConfig  # noqa: E402
from sim.describe import comprehension_questions, describe_record, load_vocabulary, render  # noqa: E402
from sim.llm_actor import PromptCache, comprehension_check, estimate_cost_usd, h1_rows, make_backend, run_h1_cell  # noqa: E402
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.tuning import rule_from_params  # noqa: E402

FIELDS = ["backend", "model", "rule", "beta", "eval_namespace", "T", "budget", "rep", "eval_seed", "profit_attack", "profit_twin", "profit_clip", "sstar",
          "gain_vs_twin", "eff_attack", "eff_twin", "eff_clip", "audit_cost_attack", "fallback_rounds", "invalid"]


def smoke_config(locked: dict) -> MarketConfig:
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)


def h1_config(locked: dict, cal, beta: float, T: int, base: MarketConfig | None = None) -> MarketConfig:
    base = base or dataclasses.replace(market_config_from_locked(locked), T=int(T))
    return cell_config(base, cal, rho=float(locked["rho"]["default"]), beta=float(beta))


class TimedBackend:
    """Wraps a backend to record wall-clock latency per call (the pilot's latency figure)."""

    def __init__(self, inner) -> None:
        self.inner, self.name, self.model, self.latencies = inner, inner.name, inner.model, []

    def complete(self, kind: str, payload: dict) -> dict:
        t0 = time.perf_counter(); out = self.inner.complete(kind, payload); self.latencies.append(time.perf_counter() - t0)
        return out


def make_fake_cheat():
    from sim.llm_actor import FakeBackend
    def fn(kind, payload):
        if kind == "comprehension":
            return {"answers": {q["id"]: q["options"][0]["label"] for q in payload["questions"]}}
        p = payload["state"]["provider"]
        return {"effort": 0.0, "offer": {"claim": 1.0, "bid": p["a"]}}
    return FakeBackend(fn)


def run_h1(o: dict) -> dict:
    lk = load_locked(); h = dict(lk["h1"]); smoke = bool(o["smoke"])
    T = 6 if smoke else int(h["T"]); reps = 2 if smoke else int(h["repetitions"]); betas = [0.05] if smoke else [float(b) for b in h["betas"]]
    lk_run = dict(lk, h1=dict(h, repetitions=reps))
    out = Path(o["out"]); out.mkdir(parents=True, exist_ok=True)
    cache = PromptCache(o["cache"] or (out / "cache" if smoke else Path("experiments/cache") / o["backend"]))
    instructions = Path(o["prompt"]).read_text() if o.get("prompt") else None
    backend = TimedBackend(make_fake_cheat() if o["backend"] == "fake-cheat" else make_backend(o["backend"], lk, instructions))
    cal = load_calibration(o["calibration"])
    try:
        eval_seeds = tuple(locked_seeds(lk, o["eval_namespace"]))
    except ValueError:
        raise SystemExit(f"evaluation namespace {o['eval_namespace']} is not available in locked.yaml (final_eval is released at the unseal)")
    train = tuple(locked_seeds(lk, "dev_train")[:4])
    calls_cap = int(o["max_calls"] if o["max_calls"] is not None else h["calls_cap"])
    cost_cap = o["max_cost_usd"] if o["max_cost_usd"] is not None else h.get("cost_cap_usd")
    voc = load_vocabulary(); qs = comprehension_questions()
    rules = [r.strip() for r in o["rules"].split(",") if r.strip()]
    params = {r: load_params(r, Path(o["tuned_dir"]) if o["tuned_dir"] else None, smoke, cal.market_key, settings_hash(lk), cal.seeds) for r in rules}
    summary = {"backend": backend.name, "model": backend.model, "T": T, "eval_namespace": o["eval_namespace"], "calls_cap": calls_cap, "cost_cap_usd": cost_cap,
               "calls": 0, "cache_hits": 0, "usage": {"input_tokens": 0, "output_tokens": 0}, "cost_usd": 0.0, "comprehension": {}, "cells": {}}
    summary["comprehension"] = comprehension_check(backend, cache, {r: rule_from_params(r, params[r]) for r in rules}, qs)
    rows_path = out / "h1_rows.csv"; new_file = not rows_path.exists() or smoke
    writer_f = rows_path.open("w" if new_file else "a", newline=""); w = csv.DictWriter(writer_f, fieldnames=FIELDS, extrasaction="ignore")
    if new_file:
        w.writeheader()

    def flush():
        writer_f.flush(); (out / "h1_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=float))

    def check_caps():
        summary["cost_usd"] = estimate_cost_usd(summary["usage"], backend.model, lk) if backend.model in h.get("prices", {}) else 0.0
        if summary["calls"] > calls_cap:
            flush(); raise SystemExit(f"calls cap {calls_cap} exceeded ({summary['calls']} calls); results so far are in {out}")
        if cost_cap is not None and summary["cost_usd"] > float(cost_cap):
            flush(); raise SystemExit(f"cost cap {cost_cap} USD exceeded ({summary['cost_usd']:.2f} USD); results so far are in {out}")

    try:
        for rule in rules:
            for beta in betas:
                cfg = h1_config(lk, cal, beta, T, base=smoke_config(lk) if smoke else None)
                rule_factory = (lambda r=rule: rule_from_params(r, params[r]))
                rendered = render(describe_record(rule_factory()), voc)
                res = run_h1_cell(cfg, rule_factory, positions(cfg)["median"], backend, cache, rendered, train, eval_seeds[:reps], lk_run)
                meta = {"backend": backend.name, "model": backend.model, "rule": rule, "beta": beta, "eval_namespace": o["eval_namespace"], "T": T, "budget": cfg.budget}
                for row in h1_rows(res, meta):
                    w.writerow(row)
                summary["calls"] += res.calls; summary["cache_hits"] += sum(r.cache_hits for r in res.attack + res.twin + res.clipped)
                for k in summary["usage"]:
                    summary["usage"][k] += res.usage[k]
                summary["cells"][f"{rule}|{beta}"] = {"calls": res.calls, "new_calls_clipped": res.new_calls_clipped, "invalid_count": res.invalid_count,
                                                      "inconclusive": res.inconclusive, "usage": res.usage}
                check_caps(); flush()
                if o["pilot"] and summary["calls"] >= int(o["pilot_calls"]):
                    raise StopIteration
    except StopIteration:
        pass
    finally:
        flush(); writer_f.close()
    if o["pilot"]:
        n = max(summary["calls"], 1)
        cost_per_call = (estimate_cost_usd(summary["usage"], backend.model, lk) / n) if backend.model in h.get("prices", {}) else 0.0
        pilot = {"backend": backend.name, "model": backend.model, "calls": summary["calls"], "mean_input_tokens": summary["usage"]["input_tokens"] / n,
                 "mean_output_tokens": summary["usage"]["output_tokens"] / n, "mean_latency_s": (sum(backend.latencies) / len(backend.latencies)) if backend.latencies else 0.0,
                 "cost_per_call_usd": cost_per_call, "projected_cost_usd": cost_per_call * int(h["calls_cap"])}
        (out / f"pilot_{backend.name}.json").write_text(json.dumps(pilot, indent=1))
        print(json.dumps(pilot))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["fake-honest", "fake-cheat", "anthropic", "jev"])
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", required=True, help="a T = 100 calibration (scripts/calibrate.py --T 100), or the smoke one")
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--eval-namespace", dest="eval_namespace", default="dev_val", choices=["dev_val", "final_eval"])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--pilot-calls", dest="pilot_calls", type=int, default=200)
    ap.add_argument("--max-calls", dest="max_calls", type=int, default=None)
    ap.add_argument("--max-cost-usd", dest="max_cost_usd", type=float, default=None)
    ap.add_argument("--prompt", default=None, help="path of the sealed H1 prompt (sealed/h1_prompt.txt); replaces the development instructions")
    s = run_h1(vars(ap.parse_args()))
    print(json.dumps({"calls": s["calls"], "cost_usd": s["cost_usd"], "cells": {k: v["inconclusive"] for k, v in s["cells"].items()}}))


if __name__ == "__main__":
    main()
```

`load_params` in `scripts/sweep.py` takes `(rule, tuned_dir, smoke, market_key, shash, cal_seeds)`; read it before calling: with `--smoke` it returns `DEFAULT_PARAMS[rule]`, and with a tuned directory it checks the tuned file's market key and settings hash. The T = 100 tuned parameters are the T = 200 tuned parameters (the spec tunes once; the H1 market differs only in T, so the tuned-file check must compare the market key without T, or the script must pass the T = 200 market key: read `load_params` and pass `cal.market_key` of the T = 200 calibration when the check would otherwise refuse; record the choice as a ruling).

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_h1_script.py tests/test_calibrate.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Produce the T = 100 calibration and run the pilots (the user runs the two real ones)**

```bash
uv run python scripts/calibrate.py --T 100 --out experiments/calibration_T100.json
uv run python scripts/h1.py --backend fake-cheat --rules B1,B2,B3 --calibration experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/h1_fake
```
Expected: `results/h1_fake/h1_rows.csv` with 3 rules x 3 betas x 10 rows; the summary reports about 3 x 3 x 10 x (500 + 500 + up to 100) = up to 99,000 calls on the first run (the clipped run replays episodes 1 to 4) and 0 on a re-run. Then the user, with `ANTHROPIC_API_KEY` and `TYPESAFE_API_KEY` set, runs the two pilots and records `projected_cost_usd` in `h1.cost_cap_usd`:
```bash
uv run python scripts/h1.py --backend anthropic --rules B2 --calibration experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_anthropic --pilot
uv run python scripts/h1.py --backend jev --rules B2 --calibration experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_jev --pilot
```
The executor does not run the real pilots (they spend money); the ledger records that they are the user's step.

- [ ] **Step 6: Commit**

```bash
git add scripts/h1.py scripts/calibrate.py tests/test_h1_script.py tests/test_calibrate.py experiments/calibration_T100.json
git commit -m "feat: H1 runner with comprehension check, caps, cache replay, and the token pilot; calibrate --T for the T = 100 market"
```

---

### Task 7: The claim predicate, the lock and freeze checks, the lock script, and the sealed bundle

**Files:**
- Create: `sim/claimcheck.py`, `sim/sealed.py`, `scripts/check_claim.py`, `scripts/lock.py`
- Modify: `sim/locked.py` (`seeds` falls back to the sealed final-eval seeds), `scripts/sweep.py` (`meta_of` adds `budget`)
- Test: `tests/test_claimcheck.py`, `tests/test_sealed.py`, `tests/test_lock_script.py`

**Interfaces:**
- Consumes: `bound` (Task 2), `endpoint_key` and the coverage report's `admitted_sides` and `consequences` (Task 5), `uses_not_expressible` and `DESCRIBE_FIELDS` (Task 3), `settings_hash`, `load_locked`, `sha256_file` (`sim/locked.py`), the sweep's evaluate records (`rows` with `METRIC_FIELDS` plus `meta_of`), `h1_rows.csv` and `h1_summary.json` (Task 6).
- Produces (`sim/claimcheck.py`):
  - `PASS, FAIL, INCONCLUSIVE` strings; `Verdict(status, bound, side, method, threshold, n, note)`.
  - `decide(x, stat, pass_side, level, threshold, coverage, settings, n=None) -> Verdict`: the decision rule of spec 8 for one bound (`pass_side = "lower"` means PASS needs the lower bound at or above the threshold; `"upper"` means PASS needs the upper bound at or below it).
  - `combine_all(statuses) -> str` (PASS if all PASS, FAIL if any FAIL, else INCONCLUSIVE), `combine_any(statuses) -> str` (PASS if any PASS, FAIL if all FAIL, else INCONCLUSIVE).
  - `h1_frame(h1_rows: pd.DataFrame) -> pd.DataFrame` (renames `eval_seed -> seed`, `gain_vs_twin -> gain`, adds `family = "H1"`).
  - `h1_inconclusive_reason(proposed, h1_summary: dict | None, describe_record: dict | None, beta) -> str | None`: `"not expressible"` when the record uses it, `"comprehension"` when `score(proposed) < min(baseline scores) - 1`, `"invalid repetitions"` when `cells[f"{proposed}|{beta}"]["inconclusive"]`, else `None`.
  - `evaluate_claim(h2: pd.DataFrame | None, h1: pd.DataFrame | None, coverage: dict, locked: dict, proposed: str, h1_summary: dict | None = None, describe_record: dict | None = None) -> dict` with `claim`, `confirmatory` (families), `rule_clause: {family: {eff, gain, audit, status, audit_over_sstar_mean}}`, `baseline_clause: {B: {pairs: {f"{family}|{alt}": Verdict}, status}}`, `h1_note`, `n: {family: n}`.
  - `tracked_blobs(repo: Path, ref: str | None) -> dict[str, str]` (path to blob sha; `ref=None` hashes the working tree with `git hash-object --stdin-paths` over `git ls-files`), `allowed(path, allow_list) -> bool` (exact match, or prefix match for entries ending in `/`), `verify_lock(repo, lock_tag, allow_list) -> list[str]` (problems: changed, new, or deleted tracked files outside the allow-list), `verify_freeze(repo, freeze_tag, locked, allow_list) -> list[str]` (the three proposed-rule files must equal the freeze tag's blobs; `sealed/` must match the bundle hash; every file under `sealed/patches/` must be in the patch log with its hash; `scripts/plot.py` and `docs/` are not checked), `verify_records(records: list[dict], locked: dict, tuned_dir: Path | None) -> list[str]` (settings hash, salt hash, `eval_namespace == "final_eval"`, `smoke` false, tuned-file hashes against `locked["tuned"]`).
- Produces (`sim/sealed.py`): `BUNDLE_FILES`, `bundle_hash(sealed_dir, exclude=("patches",)) -> str`, `verify_bundle(sealed_dir, locked) -> None` (raises `ValueError`), `patch_log(sealed_dir) -> dict`, `verify_patches(sealed_dir) -> list[str]`, `SealedBundle(h1_prompt, h2_module, containment, final_eval_seeds, salt_hex, b1_check)`, `load_bundle(sealed_dir, locked) -> SealedBundle`, `final_eval_seeds(sealed_dir) -> list[int]`.
- Produces (`sim/locked.py`): `seeds(locked, "final_eval")` returns `locked["seeds"]["final_eval"]` when set, else the sealed seeds when `sealed/final_eval_seeds.json` exists and the bundle verifies, else raises `ValueError`.
- Produces (`scripts/check_claim.py`): CLI `[--sweep-out DIR | --h2-rows CSV] [--h1-dir DIR | --h1-rows CSV] [--coverage-report PATH] --proposed NAME [--proposed-describe PATH] [--verify-lock TAG] [--verify-freeze TAG] [--tuned-dir DIR] [--synthetic] [--out PATH]`; refuses (exit 2) on any hash or tree problem unless `--synthetic` with CSV inputs; prints the clause table and writes the verdict JSON; exit 0 after a verdict (PASS, FAIL, and INCONCLUSIVE are all exit 0).
- Produces (`scripts/lock.py`): CLI `--tuned-dir DIR --calibration PATH --calibration-t100 PATH --coverage-report PATH [--bundle-hash HEX] [--cost-cap-usd X] [--date 2026-10-28] [--check]`; writes `version`, `tuned`, `calibration`, `coverage_report_sha256`, `coverage_consequences`, `comprehension_fixture_sha256`, `sealed_bundle_sha256`, `h1.cost_cap_usd` into `experiments/locked.yaml` (keys only, every other byte unchanged, through a YAML round trip with sorted keys preserved by `ruamel`-free editing: load, update, dump with `sort_keys=False`), and prints the commit and tag commands; `--check` verifies every written hash against its file and exits non-zero on a mismatch.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_claimcheck.py
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sim.claimcheck import (PASS, FAIL, INCONCLUSIVE, decide, combine_all, combine_any, h1_frame, h1_inconclusive_reason, evaluate_claim,
                            tracked_blobs, allowed, verify_lock, verify_freeze, verify_records)
from sim.coverage import ENDPOINTS, endpoint_key
from sim.locked import load_locked, settings_hash

SETTINGS = {"bootstrap_resamples": 500, "bootstrap_seed": 1}


def coverage(method20="percentile", method10="t", h1="confirmatory", par="percentile_n20", n_final=20, drop=()):
    sides = {endpoint_key(s, side, lv, n): m for n, m in ((10, method10), (20, method20), (40, None)) for s, side, lv in ENDPOINTS}
    for k in drop:
        sides[k] = None
    return {"admitted_sides": sides, "consequences": {"h1": h1, "parametrized": par, "final_eval_n": n_final}}


def test_decide_pass_fail_inconclusive():
    rng = np.random.default_rng(0); cov = coverage()
    hi = rng.normal(0.97, 0.01, size=20); lo = rng.normal(0.5, 0.01, size=20); mid = rng.normal(0.90, 0.05, size=20)
    assert decide(hi, "eff", "lower", 0.95, 0.90, cov, SETTINGS).status == PASS
    assert decide(lo, "eff", "lower", 0.95, 0.90, cov, SETTINGS).status == FAIL
    assert decide(mid, "eff", "lower", 0.95, 0.90, cov, SETTINGS).status == INCONCLUSIVE
    assert decide(lo, "gain", "upper", 0.95, 0.30, cov, SETTINGS).status == FAIL and decide(lo * 0.1, "gain", "upper", 0.95, 0.30, cov, SETTINGS).status == PASS
    cov2 = coverage(drop=(endpoint_key("eff", "lower", 0.95, 20),))
    v = decide(hi, "eff", "lower", 0.95, 0.90, cov2, SETTINGS)
    assert v.status == INCONCLUSIVE and "not admitted" in v.note
    assert decide(lo, "eff", "lower", 0.95, 0.90, cov2, SETTINGS).status == FAIL          # the opposite side is still admitted
    assert decide(hi[:5], "eff", "lower", 0.95, 0.90, cov, SETTINGS, n=20).status == INCONCLUSIVE   # wrong n
    assert combine_all([PASS, PASS]) == PASS and combine_all([PASS, INCONCLUSIVE]) == INCONCLUSIVE and combine_all([FAIL, INCONCLUSIVE]) == FAIL
    assert combine_any([FAIL, PASS]) == PASS and combine_any([FAIL, FAIL]) == FAIL and combine_any([FAIL, INCONCLUSIVE]) == INCONCLUSIVE


def frame(rule, family, gain, eff, eff_clip, audit, budget=1.0, n=20, seed0=0):
    rng = np.random.default_rng(hash((rule, family)) % 2**32)
    return pd.DataFrame({"rule": rule, "family": family, "seed": np.arange(seed0, seed0 + n), "beta": 0.05, "sstar": 10.0,
                         "gain": gain + rng.normal(0, 0.01, n), "eff_attack": eff + rng.normal(0, 0.005, n), "eff_clip": eff_clip + rng.normal(0, 0.005, n),
                         "audit_cost_attack": audit, "budget": budget})


def good_h2():
    return pd.concat([frame("R", "H2", 0.05, 0.97, 0.98, 0.5), frame("B2", "H2", 1.5, 0.80, 0.95, 0.5), frame("B3", "H2", 0.2, 0.85, 0.97, 0.5)], ignore_index=True)


def test_claim_pass_fail_inconclusive_end_to_end():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    r = evaluate_claim(good_h2(), None, coverage(), lk, "R")
    assert r["confirmatory"] == ["H2"] and r["claim"] == PASS and r["rule_clause"]["H2"]["status"] == PASS
    assert r["baseline_clause"]["B2"]["status"] == PASS and r["baseline_clause"]["B3"]["status"] == PASS   # B2 by gain, B3 by loss difference
    bad = good_h2(); bad.loc[bad.rule == "R", "gain"] += 1.0
    assert evaluate_claim(bad, None, coverage(), lk, "R")["claim"] == FAIL
    over = good_h2(); over.loc[(over.rule == "R") & (over.seed == 3), "audit_cost_attack"] = 2.0
    assert evaluate_claim(over, None, coverage(), lk, "R")["rule_clause"]["H2"]["audit"] == FAIL
    assert evaluate_claim(good_h2(), None, coverage(method20=None, par="inconclusive", n_final=None), lk, "R")["claim"] == INCONCLUSIVE
    weak = good_h2(); weak.loc[weak.rule == "B2", "gain"] = 0.2; weak.loc[weak.rule == "B2", "eff_clip"] = weak.loc[weak.rule == "B2", "eff_attack"] + 0.005
    assert evaluate_claim(weak, None, coverage(), lk, "R")["baseline_clause"]["B2"]["status"] == FAIL


def test_h1_enters_only_when_admitted_and_not_inconclusive():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    h1 = pd.concat([pd.DataFrame({"rule": r, "beta": 0.05, "rep": range(10), "eval_seed": range(10), "sstar": 5.0, "gain_vs_twin": g, "eff_attack": e,
                                  "eff_clip": e + 0.01, "audit_cost_attack": 0.1, "budget": 0.25, "invalid": 0})
                    for r, g, e in (("R", 0.02, 0.96), ("B2", 1.4, 0.8), ("B3", 1.3, 0.8))], ignore_index=True)
    f = h1_frame(h1); assert set(f.family) == {"H1"} and "gain" in f and "seed" in f
    r = evaluate_claim(good_h2(), h1, coverage(), lk, "R", h1_summary={"cells": {"R|0.05": {"inconclusive": False}}, "comprehension": {"R": 7, "B2": 7, "B3": 6}})
    assert r["confirmatory"] == ["H2", "H1"] and r["claim"] == PASS and r["n"]["H1"] == 10
    r2 = evaluate_claim(good_h2(), h1, coverage(h1="exploratory"), lk, "R")
    assert r2["confirmatory"] == ["H2"] and r2["claim"] == PASS
    r3 = evaluate_claim(good_h2(), h1, coverage(), lk, "R", h1_summary={"cells": {"R|0.05": {"inconclusive": True}}, "comprehension": {"R": 7, "B2": 7, "B3": 6}})
    assert r3["confirmatory"] == ["H2", "H1"] and r3["rule_clause"]["H1"]["status"] == INCONCLUSIVE and r3["claim"] == INCONCLUSIVE


def test_not_expressible_record_makes_h1_inconclusive():
    rec = {"allocation_order": "descending value", "eligibility": "not expressible", "payment": "posted tier price", "audit_selection": "none",
           "audit_tolerance": "none", "failed_audit": "none", "ban_length": "none", "holdback": "none"}
    assert h1_inconclusive_reason("R", {"cells": {"R|0.05": {"inconclusive": False}}, "comprehension": {"R": 7, "B2": 7}}, rec, 0.05) == "not expressible"
    assert h1_inconclusive_reason("R", {"cells": {"R|0.05": {"inconclusive": False}}, "comprehension": {"R": 5, "B2": 7, "B3": 7}}, None, 0.05) == "comprehension"
    assert h1_inconclusive_reason("R", {"cells": {"R|0.05": {"inconclusive": False}}, "comprehension": {"R": 6, "B2": 7, "B3": 7}}, None, 0.05) is None


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def make_repo(tmp_path):
    repo = tmp_path / "repo"; (repo / "sim" / "mechanisms").mkdir(parents=True); (repo / "experiments").mkdir(); (repo / "docs").mkdir()
    git(repo, "init", "-q")
    (repo / "sim" / "market.py").write_text("frozen = 1\n"); (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 0\n")
    (repo / "experiments" / "proposed.yaml").write_text("a: 1\n"); (repo / "docs" / "note.md").write_text("hi\n")
    git(repo, "add", "."); git(repo, "commit", "-q", "-m", "lock"); git(repo, "tag", "lock-test")
    return repo


ALLOW = ["sim/mechanisms/proposed.py", "experiments/proposed.yaml", "experiments/proposed_describe.yaml", "scripts/plot.py", "docs/", "sealed/", "sealed/patches/"]


def test_check_claim_refuses_modified_frozen_file(tmp_path):
    repo = make_repo(tmp_path)
    assert verify_lock(repo, "lock-test", ALLOW) == []
    assert allowed("docs/x/y.md", ALLOW) and allowed("sim/mechanisms/proposed.py", ALLOW) and not allowed("sim/market.py", ALLOW)
    (repo / "sim" / "market.py").write_text("frozen = 2\n")
    probs = verify_lock(repo, "lock-test", ALLOW)
    assert len(probs) == 1 and "sim/market.py" in probs[0] and "changed" in probs[0]
    (repo / "sim" / "market.py").write_text("frozen = 1\n")
    (repo / "sim" / "new.py").write_text("n = 1\n"); git(repo, "add", "sim/new.py")
    assert any("sim/new.py" in p and "new" in p for p in verify_lock(repo, "lock-test", ALLOW))
    git(repo, "rm", "-q", "--cached", "sim/new.py"); (repo / "sim" / "new.py").unlink()
    (repo / "sim" / "market.py").unlink()
    assert any("sim/market.py" in p and "deleted" in p for p in verify_lock(repo, "lock-test", ALLOW))


def test_check_claim_accepts_allow_listed_changes_after_freeze(tmp_path):
    from sim.sealed import bundle_hash
    repo = make_repo(tmp_path)
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 1\n"); (repo / "docs" / "note.md").write_text("changed\n")
    (repo / "scripts").mkdir(); (repo / "scripts" / "plot.py").write_text("p = 1\n")
    sealed = repo / "sealed"; sealed.mkdir(); (sealed / "h1_prompt.txt").write_text("prompt\n"); (sealed / "patches").mkdir()
    git(repo, "add", "."); git(repo, "commit", "-q", "-m", "freeze"); git(repo, "tag", "freeze-test")
    assert verify_lock(repo, "lock-test", ALLOW) == []                                    # every change is allow-listed
    lk = {"sealed_bundle_sha256": bundle_hash(sealed), "allow_list": ALLOW}
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 2\n")
    assert any("proposed.py" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 1\n")
    (sealed / "h1_prompt.txt").write_text("tampered\n")
    assert any("bundle" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))
    (sealed / "h1_prompt.txt").write_text("prompt\n")
    (sealed / "patches" / "fix.diff").write_text("--- a\n+++ b\n")
    assert any("patches" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))     # unlogged patch
    import hashlib, json
    (sealed / "patches" / "log.json").write_text(json.dumps({"fix.diff": hashlib.sha256(b"--- a\n+++ b\n").hexdigest()}))
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []


def test_verify_records_checks_hashes_and_namespace(tmp_path):
    lk = load_locked(); lk = dict(lk, identity_salt_sha256="ab" * 32, tuned={"B2": "cd" * 32})
    good = {"settings_hash": settings_hash(lk), "salt_hash": "ab" * 32, "eval_namespace": "final_eval", "smoke": False, "spec": {"rule": "B2"}}
    (tmp_path / "tuned_B2.json").write_text("{}")
    probs = verify_records([good], lk, tmp_path)
    assert len(probs) == 1 and "tuned" in probs[0]                                          # the tuned file hash differs
    import hashlib
    lk2 = dict(lk, tuned={"B2": hashlib.sha256(b"{}").hexdigest()})
    good2 = dict(good, settings_hash=settings_hash(lk2))
    assert verify_records([good2], lk2, tmp_path) == []
    for bad in (dict(good2, settings_hash="x"), dict(good2, salt_hash="y"), dict(good2, eval_namespace="dev_val"), dict(good2, smoke=True)):
        assert verify_records([bad], lk2, tmp_path) != []
```

```python
# tests/test_sealed.py
import json
import pytest
from sim.sealed import BUNDLE_FILES, bundle_hash, verify_bundle, patch_log, verify_patches, load_bundle, final_eval_seeds
from sim.locked import load_locked, seeds


def make_bundle(root):
    s = root / "sealed"; (s / "h2").mkdir(parents=True); (s / "patches").mkdir()
    (s / "README.md").write_text("bundle\n"); (s / "h1_prompt.txt").write_text("You are a provider.\n")
    (s / "h2" / "family.py").write_text("from sim.policies.families import D2 as H2\nCONTAINMENT = 'contains D2 through an embedding'\n")
    (s / "h2" / "containment.md").write_text("H2 contains D2.\n")
    (s / "final_eval_seeds.json").write_text(json.dumps(list(range(5000, 5040))))
    (s / "identity_salt.hex").write_text("00" * 32 + "\n"); (s / "b1_check.json").write_text(json.dumps({"B1": "pass"}))
    return s


def test_bundle_hash_is_content_addressed_and_ignores_patches(tmp_path):
    s = make_bundle(tmp_path); h = bundle_hash(s)
    assert len(h) == 64 and set(BUNDLE_FILES) <= {str(p.relative_to(s)) for p in s.rglob("*") if p.is_file()}
    (s / "patches" / "x.diff").write_text("d\n"); assert bundle_hash(s) == h
    (s / "h1_prompt.txt").write_text("changed\n"); assert bundle_hash(s) != h


def test_verify_and_load_bundle_and_seed_fallback(tmp_path, monkeypatch):
    s = make_bundle(tmp_path); lk = dict(load_locked(), sealed_bundle_sha256=bundle_hash(s))
    verify_bundle(s, lk)
    with pytest.raises(ValueError):
        verify_bundle(s, dict(lk, sealed_bundle_sha256="00" * 32))
    b = load_bundle(s, lk)
    assert b.h1_prompt.startswith("You are") and b.final_eval_seeds == list(range(5000, 5040)) and b.h2_module.H2.name == "D2" and b.salt_hex == "00" * 32
    assert final_eval_seeds(s) == list(range(5000, 5040))
    monkeypatch.chdir(tmp_path)                                    # sim.locked looks for ./sealed relative to the cwd
    assert seeds(lk, "final_eval") == list(range(5000, 5040))
    with pytest.raises(ValueError):
        seeds(dict(lk, sealed_bundle_sha256="11" * 32), "final_eval")
    assert patch_log(s) == {} and verify_patches(s) == []
    (s / "patches" / "a.diff").write_text("a\n")
    assert verify_patches(s) != []
```

```python
# tests/test_lock_script.py
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from sim.locked import load_locked, settings_hash

ROOT = Path(__file__).resolve().parents[1]


def test_lock_script_writes_lock_time_blocks_and_check_passes(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir(); shutil.copy(ROOT / "experiments" / "locked.yaml", exp / "locked.yaml")
    shutil.copy(ROOT / "experiments" / "comprehension_fixture.yaml", exp / "comprehension_fixture.yaml")
    tuned = tmp_path / "tuned"; tuned.mkdir()
    for r in ("B1", "B2", "B3"):
        (tuned / f"tuned_{r}.json").write_text(json.dumps({"rule": r}))
    cal = {"S_hat": 1.0, "n_FB": 2.0, "m": 0.5, "market_key": "k", "T": 200, "seeds": [1]}
    (tmp_path / "cal.json").write_text(json.dumps(cal)); (tmp_path / "cal100.json").write_text(json.dumps(dict(cal, T=100)))
    (tmp_path / "cov.json").write_text(json.dumps({"consequences": {"h1": "confirmatory", "parametrized": "percentile_n20", "final_eval_n": 20}}))
    before = settings_hash(load_locked(exp / "locked.yaml"))
    cmd = [sys.executable, str(ROOT / "scripts" / "lock.py"), "--locked", str(exp / "locked.yaml"), "--tuned-dir", str(tuned), "--calibration", str(tmp_path / "cal.json"),
           "--calibration-t100", str(tmp_path / "cal100.json"), "--coverage-report", str(tmp_path / "cov.json"), "--bundle-hash", "ab" * 32, "--cost-cap-usd", "120"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    lk = yaml.safe_load((exp / "locked.yaml").read_text())
    assert lk["version"] == "locked-2026-10-28" and set(lk["tuned"]) == {"B1", "B2", "B3"} and lk["calibration"]["T100"]["T"] == 100
    assert lk["sealed_bundle_sha256"] == "ab" * 32 and lk["h1"]["cost_cap_usd"] == 120 and lk["coverage_consequences"]["final_eval_n"] == 20
    assert len(lk["coverage_report_sha256"]) == 64 and len(lk["comprehension_fixture_sha256"]) == 64
    assert settings_hash(lk) == before and "git tag -s lock-2026-10-28" in r.stdout
    chk = subprocess.run(cmd[:4] + ["--tuned-dir", str(tuned), "--calibration", str(tmp_path / "cal.json"), "--calibration-t100", str(tmp_path / "cal100.json"),
                                     "--coverage-report", str(tmp_path / "cov.json"), "--check"], capture_output=True, text=True, cwd=ROOT)
    assert chk.returncode == 0, chk.stderr
    (tuned / "tuned_B2.json").write_text("{}")
    chk2 = subprocess.run(cmd[:4] + ["--tuned-dir", str(tuned), "--calibration", str(tmp_path / "cal.json"), "--calibration-t100", str(tmp_path / "cal100.json"),
                                      "--coverage-report", str(tmp_path / "cov.json"), "--check"], capture_output=True, text=True, cwd=ROOT)
    assert chk2.returncode != 0 and "tuned_B2" in (chk2.stdout + chk2.stderr)
```

Also append to `tests/test_claimcheck.py` an end-to-end run of the CLI on synthetic CSVs:

```python
def test_check_claim_cli_on_synthetic_csvs(tmp_path):
    import json, subprocess, sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    good_h2().to_csv(tmp_path / "h2.csv", index=False)
    cov = coverage(); (tmp_path / "cov.json").write_text(json.dumps(cov))
    r = subprocess.run([sys.executable, str(root / "scripts" / "check_claim.py"), "--h2-rows", str(tmp_path / "h2.csv"), "--coverage-report", str(tmp_path / "cov.json"),
                        "--proposed", "R", "--synthetic", "--out", str(tmp_path / "verdict.json")], capture_output=True, text=True, cwd=root)
    assert r.returncode == 0, r.stderr
    v = json.loads((tmp_path / "verdict.json").read_text())
    assert v["claim"] == "PASS" and "SYNTHETIC" in r.stdout
    r2 = subprocess.run([sys.executable, str(root / "scripts" / "check_claim.py"), "--h2-rows", str(tmp_path / "h2.csv"), "--coverage-report", str(tmp_path / "cov.json"),
                         "--proposed", "R"], capture_output=True, text=True, cwd=root)
    assert r2.returncode == 2 and "synthetic" in (r2.stderr + r2.stdout).lower()           # CSV inputs without --synthetic are refused
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_claimcheck.py tests/test_sealed.py tests/test_lock_script.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.claimcheck'`, `... 'sim.sealed'`, and the lock-script test with a non-zero return code.

- [ ] **Step 3: Write the implementation**

```python
# sim/sealed.py
"""The sealed held-out bundle (spec 6.1): layout, content hash, patch log, and loader."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

BUNDLE_FILES = ("README.md", "h1_prompt.txt", "h2/family.py", "h2/containment.md", "final_eval_seeds.json", "identity_salt.hex", "b1_check.json")


def bundle_hash(sealed_dir, exclude=("patches",)) -> str:
    root = Path(sealed_dir); h = hashlib.sha256()
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = p.relative_to(root).as_posix()
        if rel.split("/")[0] in exclude:
            continue
        h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).hexdigest().encode()); h.update(b"\n")
    return h.hexdigest()


def verify_bundle(sealed_dir, locked: dict) -> None:
    want = locked.get("sealed_bundle_sha256")
    if not want:
        raise ValueError("locked.yaml has no sealed_bundle_sha256")
    got = bundle_hash(sealed_dir)
    if got != want:
        raise ValueError(f"sealed bundle hash {got} differs from the lock commitment {want}")


def patch_log(sealed_dir) -> dict:
    p = Path(sealed_dir) / "patches" / "log.json"
    return json.loads(p.read_text()) if p.exists() else {}


def verify_patches(sealed_dir) -> list:
    d = Path(sealed_dir) / "patches"; log = patch_log(sealed_dir); problems = []
    if not d.exists():
        return problems
    for p in sorted(q for q in d.rglob("*") if q.is_file() and q.name != "log.json"):
        rel = p.relative_to(d).as_posix(); h = hashlib.sha256(p.read_bytes()).hexdigest()
        if rel not in log:
            problems.append(f"sealed/patches/{rel}: not in the patch log")
        elif log[rel] != h:
            problems.append(f"sealed/patches/{rel}: hash {h} differs from the logged {log[rel]}")
    return problems


def final_eval_seeds(sealed_dir) -> list:
    return [int(s) for s in json.loads((Path(sealed_dir) / "final_eval_seeds.json").read_text())]


@dataclass
class SealedBundle:
    h1_prompt: str
    h2_module: object
    containment: str
    final_eval_seeds: list
    salt_hex: str | None
    b1_check: dict


def load_bundle(sealed_dir, locked: dict) -> SealedBundle:
    root = Path(sealed_dir); verify_bundle(root, locked)
    spec = importlib.util.spec_from_file_location("sealed_h2_family", root / "h2" / "family.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    salt = (root / "identity_salt.hex")
    return SealedBundle(h1_prompt=(root / "h1_prompt.txt").read_text(), h2_module=mod, containment=(root / "h2" / "containment.md").read_text(),
                        final_eval_seeds=final_eval_seeds(root), salt_hex=salt.read_text().strip() if salt.exists() else None,
                        b1_check=json.loads((root / "b1_check.json").read_text()) if (root / "b1_check.json").exists() else {})
```

In `sim/locked.py`, change `seeds`:

```python
def seeds(locked: dict, namespace: str) -> list[int]:
    v = locked["seeds"].get(namespace)
    if v is None and namespace == "final_eval":
        sealed = Path("sealed")
        if (sealed / "final_eval_seeds.json").exists():
            from .sealed import final_eval_seeds, verify_bundle
            verify_bundle(sealed, locked)                     # the seeds count only from a bundle that matches the lock commitment
            return final_eval_seeds(sealed)
    if v is None:
        raise ValueError(f"seed namespace {namespace!r} is not available (final-eval seeds are released with the sealed bundle)")
    return [int(s) for s in v]
```

(Keep the existing error type `ValueError` so `train_val` in `scripts/sweep.py` still maps it to `SystemExit`.)

```python
# sim/claimcheck.py
"""The claim predicate and decision rule (spec 8) and the lock, freeze, and record checks (spec 6)."""
from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .coverage import endpoint_key
from .describe import uses_not_expressible
from .intervals import bound
from .locked import settings_hash
from .sealed import bundle_hash, verify_patches

PASS, FAIL, INCONCLUSIVE = "PASS", "FAIL", "INCONCLUSIVE"
BASELINES = ("B2", "B3")
FROZEN_AT_FREEZE = ("sim/mechanisms/proposed.py", "experiments/proposed.yaml", "experiments/proposed_describe.yaml")


@dataclass
class Verdict:
    status: str
    bound: float | None
    side: str | None
    method: str | None
    threshold: float
    n: int
    note: str = ""


def _admitted(coverage: dict, stat: str, side: str, level: float, n: int):
    return coverage["admitted_sides"].get(endpoint_key(stat, side, level, n))


def decide(x, stat: str, pass_side: str, level: float, threshold: float, coverage: dict, settings: dict, n: int | None = None) -> Verdict:
    x = np.asarray(x, dtype=float); n = int(x.size if n is None else n)
    if x.size != n or x.size < 2:
        return Verdict(INCONCLUSIVE, None, None, None, threshold, n, f"{x.size} observations, expected {n}")
    opp = "upper" if pass_side == "lower" else "lower"
    m_pass = _admitted(coverage, stat, pass_side, level, n)
    if m_pass is not None:
        b = bound(m_pass, x, pass_side, level, settings)
        if (b.value >= threshold) if pass_side == "lower" else (b.value <= threshold):
            return Verdict(PASS, b.value, pass_side, m_pass, threshold, n, "degenerate" if b.degenerate else "")
    m_opp = _admitted(coverage, stat, opp, level, n)
    if m_opp is not None:
        b2 = bound(m_opp, x, opp, level, settings)
        if (b2.value < threshold) if pass_side == "lower" else (b2.value > threshold):
            return Verdict(FAIL, b2.value, opp, m_opp, threshold, n, "degenerate" if b2.degenerate else "")
    note = f"{pass_side} side not admitted at n = {n}" if m_pass is None else "the pass side did not clear and the opposite side did not miss"
    return Verdict(INCONCLUSIVE, None, None, m_pass, threshold, n, note)


def combine_all(statuses) -> str:
    s = list(statuses)
    return PASS if s and all(v == PASS for v in s) else FAIL if any(v == FAIL for v in s) else INCONCLUSIVE


def combine_any(statuses) -> str:
    s = list(statuses)
    return PASS if any(v == PASS for v in s) else FAIL if s and all(v == FAIL for v in s) else INCONCLUSIVE


def h1_frame(h1_rows: pd.DataFrame) -> pd.DataFrame:
    f = h1_rows.rename(columns={"eval_seed": "seed", "gain_vs_twin": "gain"}).copy(); f["family"] = "H1"
    return f


def h1_inconclusive_reason(proposed: str, h1_summary: dict | None, describe_record: dict | None, beta: float) -> str | None:
    if describe_record is not None and uses_not_expressible(describe_record):
        return "not expressible"
    if h1_summary is None:
        return None
    comp = h1_summary.get("comprehension", {})
    others = [v for k, v in comp.items() if k != proposed]
    if proposed in comp and others and comp[proposed] < min(others) - 1:
        return "comprehension"
    if h1_summary.get("cells", {}).get(f"{proposed}|{beta}", {}).get("inconclusive"):
        return "invalid repetitions"
    return None


def _rows(df: pd.DataFrame | None, rule: str, beta: float) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    d = df[(df["rule"] == rule) & (np.isclose(df["beta"].astype(float), beta))] if "beta" in df else df[df["rule"] == rule]
    return d.sort_values("seed").reset_index(drop=True)


def evaluate_claim(h2: pd.DataFrame | None, h1: pd.DataFrame | None, coverage: dict, locked: dict, proposed: str,
                   h1_summary: dict | None = None, describe_record: dict | None = None) -> dict:
    c = locked["claim"]; beta = float(c["beta"]); settings = locked["intervals"]; cons = coverage["consequences"]
    frames: dict = {}; n_of: dict = {}; confirmatory = []
    if h2 is not None and cons.get("parametrized") != "inconclusive" and cons.get("final_eval_n"):
        frames["H2"] = h2; n_of["H2"] = int(cons["final_eval_n"]); confirmatory.append("H2")
    h1_note = None
    if h1 is not None and cons.get("h1") == "confirmatory":
        frames["H1"] = h1_frame(h1) if "gain_vs_twin" in h1 else h1; n_of["H1"] = int(locked["intervals"]["h1_repetitions"]); confirmatory.append("H1")
        h1_note = h1_inconclusive_reason(proposed, h1_summary, describe_record, beta)
    elif h1 is not None:
        h1_note = "exploratory (proxy bound not admitted)"
    rl, bl = float(c["rule_level"]), float(c["baseline_level"])
    rule_clause = {}
    for fam in confirmatory:
        d = _rows(frames[fam], proposed, beta); n = n_of[fam]
        if fam == "H1" and h1_note:
            v = Verdict(INCONCLUSIVE, None, None, None, 0.0, n, f"H1 inconclusive: {h1_note}")
            rule_clause[fam] = {"eff": v, "gain": v, "audit": INCONCLUSIVE, "status": INCONCLUSIVE, "audit_over_sstar_mean": None}
            continue
        eff = decide(d["eff_attack"], "eff", "lower", rl, float(c["eff_min"]), coverage, settings, n)
        gain = decide(d["gain"], "gain", "upper", rl, float(c["gain_max"]), coverage, settings, n)
        audit = PASS if len(d) == n and bool((d["audit_cost_attack"] <= d["budget"] + 1e-9).all()) else FAIL if len(d) == n else INCONCLUSIVE
        rule_clause[fam] = {"eff": eff, "gain": gain, "audit": audit, "status": combine_all([eff.status, gain.status, audit]),
                            "audit_over_sstar_mean": float((d["audit_cost_attack"] / d["sstar"]).mean()) if len(d) else None}
    baseline_clause = {}
    for B in BASELINES:
        pairs = {}
        for fam in confirmatory:
            n = n_of[fam]
            if fam == "H1" and h1_note:
                pairs[f"{fam}|loss_diff"] = pairs[f"{fam}|gain"] = Verdict(INCONCLUSIVE, None, None, None, 0.0, n, f"H1 inconclusive: {h1_note}")
                continue
            dB = _rows(frames[fam], B, beta); dR = _rows(frames[fam], proposed, beta)
            m = dB.merge(dR, on="seed", suffixes=("_B", "_R"))
            ld = (m["eff_clip_B"] - m["eff_attack_B"]) - (m["eff_clip_R"] - m["eff_attack_R"])
            pairs[f"{fam}|loss_diff"] = decide(ld, "loss_diff", "lower", bl, float(c["loss_diff_min"]), coverage, settings, n)
            pairs[f"{fam}|gain"] = decide(dB["gain"], "gain", "lower", bl, float(c["baseline_gain_min"]), coverage, settings, n)
        baseline_clause[B] = {"pairs": pairs, "status": combine_any([v.status for v in pairs.values()])}
    statuses = [v["status"] for v in rule_clause.values()] + [v["status"] for v in baseline_clause.values()]
    claim = combine_all(statuses) if confirmatory else INCONCLUSIVE
    return {"claim": claim, "confirmatory": confirmatory, "rule_clause": rule_clause, "baseline_clause": baseline_clause, "h1_note": h1_note, "n": n_of,
            "proposed": proposed, "beta": beta}


def verdict_json(result: dict) -> dict:
    def conv(v):
        if isinstance(v, Verdict):
            return asdict(v)
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        return v
    return conv(result)


# ---- lock, freeze, and record checks ---------------------------------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def tracked_blobs(repo: Path, ref: str | None) -> dict:
    if ref is not None:
        out = {}
        for line in _git(repo, "ls-tree", "-r", ref).splitlines():
            meta, path = line.split("\t", 1); out[path] = meta.split()[2]
        return out
    paths = [p for p in _git(repo, "ls-files").splitlines() if p]
    present = [p for p in paths if (repo / p).is_file()]
    hashes = subprocess.run(["git", "hash-object", "--stdin-paths"], cwd=repo, input="\n".join(present) + "\n", check=True, capture_output=True, text=True).stdout.split()
    out = dict(zip(present, hashes))
    for p in paths:
        if p not in out:
            out[p] = None                                        # tracked but missing from the working tree
    return out


def allowed(path: str, allow_list) -> bool:
    return any(path == e or (e.endswith("/") and path.startswith(e)) for e in allow_list)


def verify_lock(repo, lock_tag: str, allow_list) -> list:
    repo = Path(repo); locked_tree = tracked_blobs(repo, lock_tag); tree = tracked_blobs(repo, None); problems = []
    for path, sha in tree.items():
        if allowed(path, allow_list):
            continue
        if path not in locked_tree:
            problems.append(f"{path}: new tracked file since {lock_tag} and outside the allow-list")
        elif sha is None:
            problems.append(f"{path}: deleted since {lock_tag}")
        elif sha != locked_tree[path]:
            problems.append(f"{path}: changed since {lock_tag}")
    for path in locked_tree:
        if path not in tree and not allowed(path, allow_list):
            problems.append(f"{path}: deleted since {lock_tag}")
    return problems


def verify_freeze(repo, freeze_tag: str, locked: dict, allow_list) -> list:
    repo = Path(repo); frozen = tracked_blobs(repo, freeze_tag); tree = tracked_blobs(repo, None); problems = []
    for path in FROZEN_AT_FREEZE:
        if path in frozen and tree.get(path) != frozen[path]:
            problems.append(f"{path}: differs from the freeze tag {freeze_tag}")
    sealed = repo / "sealed"
    if sealed.exists():
        want = locked.get("sealed_bundle_sha256"); got = bundle_hash(sealed)
        if want != got:
            problems.append(f"sealed/: bundle hash {got} differs from the lock commitment {want}")
        problems += verify_patches(sealed)
    return problems


def verify_records(records, locked: dict, tuned_dir) -> list:
    problems = []; want_settings = settings_hash(locked); want_salt = locked.get("identity_salt_sha256"); tuned = locked.get("tuned") or {}
    for rec in records:
        name = rec.get("spec", {}).get("name", rec.get("spec", {}).get("rule", "?"))
        if rec.get("settings_hash") != want_settings:
            problems.append(f"{name}: settings hash differs from the lock")
        if rec.get("salt_hash") != want_salt:
            problems.append(f"{name}: salt hash differs from the lock")
        if rec.get("eval_namespace") != "final_eval":
            problems.append(f"{name}: evaluation namespace is {rec.get('eval_namespace')!r}, not final_eval")
        if rec.get("smoke"):
            problems.append(f"{name}: smoke record")
        rule = rec.get("spec", {}).get("rule")
        if rule in tuned and tuned_dir is not None:
            p = Path(tuned_dir) / f"tuned_{rule}.json"
            got = hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
            if got != tuned[rule]:
                problems.append(f"{name}: tuned file {p.name} hash {got} differs from the lock {tuned[rule]}")
    return problems
```

In `scripts/sweep.py`, `meta_of` adds `"budget": float(job["cfg"]["budget"])` (the per-seed rows then carry the cell's audit budget for the audit clause).

```python
# scripts/check_claim.py
"""Evaluate the claim predicate (spec 8) on final-eval results after verifying the lock, the freeze, and every record
hash (spec 6). CSV inputs are for synthetic tests only and require --synthetic."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import read_dir  # noqa: E402
from sim.claimcheck import PASS, evaluate_claim, verdict_json, verify_freeze, verify_lock, verify_records  # noqa: E402
from sim.coverage import load_report  # noqa: E402
from sim.locked import load_locked  # noqa: E402


def h2_from_sweep(sweep_out: Path, locked: dict) -> tuple[pd.DataFrame, list]:
    recs = read_dir(sweep_out / "evaluate"); rows = []; records = []
    for rec in recs.values():
        if rec["spec"]["section"] != "heldout" or rec["spec"]["family"] != "H2":
            continue
        records.append(rec); rows += rec["rows"]
    return pd.DataFrame(rows), records


def refuse(problems: list) -> None:
    for p in problems:
        print("REFUSED: " + p, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-out", dest="sweep_out", default=None); ap.add_argument("--h2-rows", dest="h2_rows", default=None)
    ap.add_argument("--h1-dir", dest="h1_dir", default=None); ap.add_argument("--h1-rows", dest="h1_rows", default=None)
    ap.add_argument("--coverage-report", dest="coverage_report", default="experiments/coverage_report.json")
    ap.add_argument("--proposed", required=True); ap.add_argument("--proposed-describe", dest="proposed_describe", default=None)
    ap.add_argument("--verify-lock", dest="verify_lock", default=None); ap.add_argument("--verify-freeze", dest="verify_freeze", default=None)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--synthetic", action="store_true"); ap.add_argument("--out", default="results/verdict.json")
    a = ap.parse_args()
    lk = load_locked(); repo = Path(__file__).resolve().parents[1]; problems = []
    if a.verify_lock:
        problems += verify_lock(repo, a.verify_lock, lk["allow_list"])
    if a.verify_freeze:
        problems += verify_freeze(repo, a.verify_freeze, lk, lk["allow_list"])
    if problems:
        refuse(problems)
    if (a.h2_rows or a.h1_rows) and not a.synthetic:
        refuse(["CSV inputs are for synthetic tests; pass --synthetic (no hash checks are run on CSV inputs)"])
    h2 = h1 = None; h1_summary = None
    if a.sweep_out:
        h2, records = h2_from_sweep(Path(a.sweep_out), lk); problems += verify_records(records, lk, a.tuned_dir)
    elif a.h2_rows:
        h2 = pd.read_csv(a.h2_rows)
    if a.h1_dir:
        d = Path(a.h1_dir); h1 = pd.read_csv(d / "h1_rows.csv"); h1_summary = json.loads((d / "h1_summary.json").read_text())
        if h1_summary.get("eval_namespace") != "final_eval":
            problems.append("h1 summary: evaluation namespace is not final_eval")
    elif a.h1_rows:
        h1 = pd.read_csv(a.h1_rows)
    if problems:
        refuse(problems)
    cov = load_report(a.coverage_report)
    rec = yaml.safe_load(Path(a.proposed_describe).read_text()) if a.proposed_describe else None
    res = evaluate_claim(h2, h1, cov, lk, a.proposed, h1_summary=h1_summary, describe_record=rec)
    out = verdict_json(res); out["synthetic"] = bool(a.synthetic)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(json.dumps(out, indent=1, default=float))
    print(("SYNTHETIC " if a.synthetic else "") + f"claim: {res['claim']}   confirmatory families: {res['confirmatory']}")
    for fam, r in res["rule_clause"].items():
        print(f"  rule clause {fam}: {r['status']}  eff {r['eff'].status} ({r['eff'].bound})  gain {r['gain'].status} ({r['gain'].bound})  audit {r['audit']}")
    for B, r in res["baseline_clause"].items():
        print(f"  baseline clause {B}: {r['status']}  " + "  ".join(f"{k} {v.status} ({v.bound})" for k, v in r["pairs"].items()))
    if res["h1_note"]:
        print(f"  H1 note: {res['h1_note']}")


if __name__ == "__main__":
    main()
```

(`h2_from_sweep` filters `section == "heldout"`: the post-lock sweep of H2 against the frozen rule and the baselines must write its evaluate records with that section name and `family == "H2"`; `scripts/sweep.py` is extended for held-out families after the unseal by the custodian-provided family module, outside this plan; record this as a plan note for the post-lock weeks in `docs/custodian.md`.)

```python
# scripts/lock.py
"""Write the lock-time blocks into experiments/locked.yaml (spec 6) and print the tag commands; --check verifies them."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sim.locked import settings_hash  # noqa: E402


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", default="experiments/locked.yaml")
    ap.add_argument("--tuned-dir", dest="tuned_dir", required=True)
    ap.add_argument("--calibration", required=True); ap.add_argument("--calibration-t100", dest="calibration_t100", required=True)
    ap.add_argument("--coverage-report", dest="coverage_report", required=True)
    ap.add_argument("--fixture", default="experiments/comprehension_fixture.yaml")
    ap.add_argument("--bundle-hash", dest="bundle_hash", default=None); ap.add_argument("--cost-cap-usd", dest="cost_cap_usd", type=float, default=None)
    ap.add_argument("--date", default="2026-10-28"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    path = Path(a.locked); lk = yaml.safe_load(path.read_text()); before = settings_hash(lk)
    tuned = {r: sha(Path(a.tuned_dir) / f"tuned_{r}.json") for r in ("B1", "B2", "B3")}
    cal = json.loads(Path(a.calibration).read_text()); cal100 = json.loads(Path(a.calibration_t100).read_text())
    cov = json.loads(Path(a.coverage_report).read_text())
    fixture = Path(a.locked).parent / Path(a.fixture).name if not Path(a.fixture).exists() else Path(a.fixture)
    new = {"version": f"locked-{a.date}", "tuned": tuned,
           "calibration": {**cal, "sha256": sha(a.calibration), "T100": {**cal100, "sha256": sha(a.calibration_t100)}},
           "coverage_report_sha256": sha(a.coverage_report), "coverage_consequences": cov["consequences"],
           "comprehension_fixture_sha256": sha(fixture)}
    if a.check:
        problems = [f"{k}: {lk.get(k)!r} != {v!r}" for k, v in new.items() if k != "version" and lk.get(k) != v]
        bad_tuned = [r for r in tuned if (lk.get("tuned") or {}).get(r) != tuned[r]]
        problems += [f"tuned_{r}.json hash differs from the lock" for r in bad_tuned]
        if problems:
            print("\n".join(problems)); sys.exit(1)
        print("lock-time blocks match their files"); return
    lk.update(new)
    if a.bundle_hash:
        lk["sealed_bundle_sha256"] = a.bundle_hash
    if a.cost_cap_usd is not None:
        lk["h1"]["cost_cap_usd"] = a.cost_cap_usd
    if settings_hash(lk) != before:
        sys.exit("the lock-time blocks changed the settings hash; refusing to write")
    path.write_text(yaml.safe_dump(lk, sort_keys=False, default_flow_style=None, width=120))
    print(f"wrote {path}\n")
    print(f"git add {path} && git commit -S -m 'lock: {a.date}' && git tag -s lock-{a.date} -m 'Touchstone lock {a.date}' && git push origin main lock-{a.date}")
    print("then post the tag hash to the public timestamp (OSF or AsPredicted) the same day")


if __name__ == "__main__":
    main()
```

`yaml.safe_dump` drops the comments in `locked.yaml`; that is acceptable at the lock (the tag fixes the bytes), and the ledger records it. If the executor prefers to keep the comments, replace the dump with a line-level edit that appends the new blocks under a `# ---- written at the lock ----` marker; either way the `--check` round trip and the settings-hash equality are the tests.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_claimcheck.py tests/test_sealed.py tests/test_lock_script.py -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Run the lock check on the current tree against a throwaway tag**

```bash
git tag lock-candidate && uv run python scripts/check_claim.py --proposed R --verify-lock lock-candidate --synthetic --h2-rows /dev/null; git tag -d lock-candidate
```
Expected: the tree check passes (no `REFUSED` lines), then the predicate refuses the empty CSV with a pandas error; that is fine for this step (the point is the tree check). Alternatively run `uv run python -c "from sim.claimcheck import verify_lock; print(verify_lock('.', 'lock-candidate', __import__('sim.locked').locked.load_locked()['allow_list']))"` and expect `[]`.

- [ ] **Step 6: Commit**

```bash
git add sim/claimcheck.py sim/sealed.py sim/locked.py scripts/check_claim.py scripts/lock.py scripts/sweep.py tests/test_claimcheck.py tests/test_sealed.py tests/test_lock_script.py
git commit -m "feat: claim predicate with the decision rule and admitted sides; lock, freeze, bundle, patch, and record hash checks; lock script; sealed bundle loader and final-eval seed fallback"
```

---

### Task 8: Figures 1 and 2

**Files:**
- Create: `scripts/plot.py`
- Test: `tests/test_plot.py`

**Interfaces:**
- Consumes: the sweep's evaluate records (`<out>/evaluate/<cell>.json`, each with `rows` carrying `ROW_FIELDS` plus `meta_of` fields and `params` with `tol`), `percentile_bootstrap` (Task 2), `locked["intervals"]`, `locked["market"]["sigma"]`.
- Produces: `figure_frames(sweep_out: Path, locked: dict) -> tuple[pd.DataFrame, pd.DataFrame]`: `fig1` with columns `rule, family, beta, position, audit_spend, gain_mean, gain_upper, n_seeds, honest_failure_rate` (one row per cell at the headline position of each (rule, family, beta): the position named in `<out>/headline.json` when present, else `median`; `audit_spend = mean(audit_spend_attack)`; `gain_upper` the one-sided upper 95% percentile bootstrap with the locked resamples and seed; `honest_failure_rate = Phi(-tol / sigma)` from the record's `params["tol"]`, `0.0` for a rule without `tol`), and `fig2` with columns `rule, family, beta, audit_spend, eff_honest, eff_ref, eff_clip, eff_attack` (means over seeds); `draw(fig1, fig2, out_dir) -> list[Path]` writing `figure1_gain_vs_audit.png` (one panel per family, one line per rule, mean with the bound as a lighter line, the honest failure rate in each rule's legend label) and `figure2_efficiency_quadruple.png` (one panel per rule, four lines per family); the CLI `--sweep-out DIR --out DIR` writes both PNGs and `figure_data.csv`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_plot.py
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from sim.locked import load_locked
from sim.reference import ROW_FIELDS

ROOT = Path(__file__).resolve().parents[1]


def fake_sweep(tmp_path):
    out = tmp_path / "sweep"; (out / "evaluate").mkdir(parents=True); rng = np.random.default_rng(0)
    for rule, tol in (("B1", None), ("B2", 0.12)):
        for fam in ("D1", "D2"):
            for beta in (0.02, 0.05):
                rows = []
                for k, seed in enumerate(range(2000, 2020)):
                    r = {f: float(rng.uniform(0, 1)) for f in ROW_FIELDS}
                    r.update({"seed": seed, "sstar": 10.0, "gain": 0.2 + beta + rng.normal(0, 0.05), "audit_spend_attack": beta * 0.9,
                              "eff_honest": 0.99, "eff_ref": 0.97, "eff_clip": 0.95, "eff_attack": 0.90,
                              "cell": f"{rule}_{fam}_{beta}", "section": "development", "rule": rule, "family": fam, "beta": beta, "rho": 0.5,
                              "position": "median", "smoke": False, "reference": "honest_max", "budget": beta * 10})
                    rows.append(r)
                params = {"P1": 0.25, "P2": 0.4, "P3": 0.55} | ({"tol": tol, "L": 10} if tol else {})
                (out / "evaluate" / f"{rule}_{fam}_beta{beta}_rho0.5_median_development.json").write_text(json.dumps(
                    {"spec": {"name": f"{rule}_{fam}_beta{beta}_rho0.5_median_development", "section": "development", "rule": rule, "family": fam,
                              "beta": beta, "rho": 0.5, "position": "median"}, "params": params, "rows": rows}))
    return out


def test_plot_writes_figures_and_data(tmp_path):
    from scripts.plot import figure_frames
    out = fake_sweep(tmp_path); lk = load_locked()
    f1, f2 = figure_frames(out, lk)
    assert len(f1) == 8 and set(f1.rule) == {"B1", "B2"} and (f1.gain_upper >= f1.gain_mean).all() and (f1.n_seeds == 20).all()
    b2 = f1[f1.rule == "B2"].iloc[0]; assert b2.honest_failure_rate == pytest_approx(stats.norm.cdf(-0.12 / lk["market"]["sigma"]))
    assert f1[f1.rule == "B1"].honest_failure_rate.eq(0.0).all()
    assert len(f2) == 8 and {"eff_honest", "eff_ref", "eff_clip", "eff_attack", "audit_spend"} <= set(f2.columns)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "plot.py"), "--sweep-out", str(out), "--out", str(tmp_path / "figs")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "figs" / "figure1_gain_vs_audit.png").stat().st_size > 1000 and (tmp_path / "figs" / "figure2_efficiency_quadruple.png").exists()
    assert len(pd.read_csv(tmp_path / "figs" / "figure_data.csv")) == 8


def pytest_approx(x):
    import pytest
    return pytest.approx(x)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_plot.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.plot'`.

- [ ] **Step 3: Write the implementation**

```python
# scripts/plot.py
"""Figures 1 and 2 (spec 8) from the sweep's per-seed evaluate records."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sim.intervals import percentile_bootstrap  # noqa: E402
from sim.locked import load_locked  # noqa: E402


def figure_frames(sweep_out: Path, locked: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    sweep_out = Path(sweep_out); iv = locked["intervals"]; sigma = float(locked["market"]["sigma"])
    headline = json.loads((sweep_out / "headline.json").read_text()) if (sweep_out / "headline.json").exists() else {}
    f1, f2 = [], []
    for p in sorted((sweep_out / "evaluate").glob("*.json")):
        rec = json.loads(p.read_text()); spec = rec["spec"]
        if spec["section"] not in ("development", "heldout"):
            continue
        want = headline.get(f"{spec['rule']}/{spec['family']}", {}).get("headline", "median")
        if spec["position"] != want:
            continue
        df = pd.DataFrame(rec["rows"]); tol = rec.get("params", {}).get("tol")
        g = df["gain"].to_numpy(dtype=float)
        upper = percentile_bootstrap(g, "upper", 0.95, int(iv["bootstrap_resamples"]), int(iv["bootstrap_seed"])).value if len(g) > 1 else float(g.mean())
        base = {"rule": spec["rule"], "family": spec["family"], "beta": float(spec["beta"]), "position": spec["position"], "audit_spend": float(df["audit_spend_attack"].mean())}
        f1.append({**base, "gain_mean": float(g.mean()), "gain_upper": float(upper), "n_seeds": int(len(g)),
                   "honest_failure_rate": float(stats.norm.cdf(-float(tol) / sigma)) if tol is not None else 0.0})
        f2.append({**base, **{k: float(df[k].mean()) for k in ("eff_honest", "eff_ref", "eff_clip", "eff_attack")}})
    return pd.DataFrame(f1), pd.DataFrame(f2)


def draw(fig1: pd.DataFrame, fig2: pd.DataFrame, out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); paths = []
    fams = sorted(fig1.family.unique()); fig, axes = plt.subplots(1, max(len(fams), 1), figsize=(5 * max(len(fams), 1), 4), squeeze=False)
    for ax, fam in zip(axes[0], fams):
        d = fig1[fig1.family == fam]
        for rule, g in d.groupby("rule"):
            g = g.sort_values("audit_spend"); label = f"{rule} (honest failure rate {g.honest_failure_rate.iloc[0]:.3f})"
            line, = ax.plot(g.audit_spend, g.gain_mean, marker="o", label=label)
            ax.plot(g.audit_spend, g.gain_upper, linestyle="--", alpha=0.5, color=line.get_color())
        ax.set_title(f"family {fam}"); ax.set_xlabel("audit spend / S*"); ax.set_ylabel("gain (S* / N units): mean, upper 95% bound dashed"); ax.legend(fontsize=7)
    p1 = out_dir / "figure1_gain_vs_audit.png"; fig.tight_layout(); fig.savefig(p1, dpi=150); plt.close(fig); paths.append(p1)
    rules = sorted(fig2.rule.unique()); fig, axes = plt.subplots(1, max(len(rules), 1), figsize=(5 * max(len(rules), 1), 4), squeeze=False)
    for ax, rule in zip(axes[0], rules):
        d = fig2[fig2.rule == rule]
        for fam, g in d.groupby("family"):
            g = g.sort_values("audit_spend")
            for k, ls in (("eff_honest", "-"), ("eff_ref", "--"), ("eff_clip", "-."), ("eff_attack", ":")):
                ax.plot(g.audit_spend, g[k], linestyle=ls, marker=".", label=f"{fam} {k[4:]}")
        ax.set_title(f"rule {rule}"); ax.set_xlabel("audit spend / S*"); ax.set_ylabel("gross efficiency"); ax.legend(fontsize=6, ncol=2)
    p2 = out_dir / "figure2_efficiency_quadruple.png"; fig.tight_layout(); fig.savefig(p2, dpi=150); plt.close(fig); paths.append(p2)
    return paths


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--sweep-out", dest="sweep_out", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); lk = load_locked()
    f1, f2 = figure_frames(Path(a.sweep_out), lk)
    paths = draw(f1, f2, Path(a.out))
    f1.merge(f2, on=["rule", "family", "beta", "position", "audit_spend"]).to_csv(Path(a.out) / "figure_data.csv", index=False)
    print("wrote " + ", ".join(str(p) for p in paths))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_plot.py -v`
Expected: PASS. Then draw the real smoke figures: `uv run python scripts/plot.py --sweep-out /tmp/sweep_smoke --out results/figures_smoke` and look at both PNGs once (the executor opens them with the Read tool and records in the ledger that the axes, legend labels, and bound lines are present).

- [ ] **Step 5: Commit**

```bash
git add scripts/plot.py tests/test_plot.py
git commit -m "feat: figures 1 and 2 from the evaluate records with the bootstrap upper bound and the honest failure rate"
```

---

### Task 9: Custodian instructions, spec note, README, and the run book for the lock

**Files:**
- Create: `docs/custodian.md`, `docs/lock-runbook.md`
- Modify: `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (section 14: plan 2B implementation note), `README.md` (status, the H1 exception sentence, the sealed-bundle hash line)
- Test: `tests/test_docs.py` (one test: every path named in `docs/custodian.md` under `sealed/` is in `sim.sealed.BUNDLE_FILES` or under `sealed/patches/`; every script named in `docs/lock-runbook.md` exists)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_docs.py
import re
from pathlib import Path

from sim.sealed import BUNDLE_FILES

ROOT = Path(__file__).resolve().parents[1]


def test_custodian_bundle_paths_match_the_loader_and_runbook_scripts_exist():
    text = (ROOT / "docs" / "custodian.md").read_text()
    paths = set(re.findall(r"`sealed/([A-Za-z0-9_./-]+)`", text))
    assert {p for p in paths if not p.startswith("patches/") and not p.endswith("/")} == set(BUNDLE_FILES)
    rb = (ROOT / "docs" / "lock-runbook.md").read_text()
    for script in set(re.findall(r"scripts/([a-z_]+\.py)", rb)):
        assert (ROOT / "scripts" / script).exists(), script
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_docs.py -v`
Expected: FAIL with `FileNotFoundError` for `docs/custodian.md`.

- [ ] **Step 3: Write the documents**

`docs/custodian.md` (write it in full; the outline below is the required content, each heading a section):

1. **Who you are and what you must not see.** The separate session (the custodian) writes the sealed bundle before the lock and never reads any rule-design work. It works from a clone of the repository at the lock-candidate commit, which contains no proposed rule. The author does not read the bundle until the unseal.
2. **What to produce**, the bundle layout, exactly the files `sim/sealed.py::BUNDLE_FILES` expects: `sealed/README.md` (what the bundle contains and the access log), `sealed/h1_prompt.txt` (the H1 system prompt: it replaces the development `ACTOR_INSTRUCTIONS` in `sim/llm_actor.py` through `scripts/h1.py --prompt`; it must describe the provider role, the schema, and the goal, and must not name any rule), `sealed/h2/family.py` (a module defining `H2`, an instance of `sim.policies.families.Family` with knob domains, a claim map that permits claims below effort, the binary `clip` knob so that H2 contains its twin by construction, `registered_starts`, `exact_key`, and `knob_key` as in `experiments/families.md`; and `CONTAINMENT`, a string), `sealed/h2/containment.md` (whether H2 contains D2, is contained by it, or is non-nested, and which observation or memory it uses that D2 cannot; if H2 contains D2, the embedding function `embed_d2(knobs) -> knobs` in `family.py`), `sealed/final_eval_seeds.json` (a JSON list of at least 40 distinct integers in `[10_000_000, 20_000_000)`, so disjoint from dev-train, dev-val, calibration, and the coverage block `3,000,000` to `6,600,000`; the first 20 or 40 are used, as `coverage_consequences.final_eval_n` says, and the first 10 for H1), `sealed/identity_salt.hex` (32 random bytes as 64 hex characters; its SHA-256 goes into `experiments/locked.yaml` as `identity_salt_sha256` before the lock commit; the file itself stays sealed until the evaluation freeze, when the author exports it as `TOUCHSTONE_IDENTITY_SALT` for the final-eval runs), `sealed/b1_check.json` (the result of running H2 and the H1 harness with the fake backend against B1 only, recorded as pass or fail per check, with the commands used).
3. **The commitment.** Compute `python -c "from sim.sealed import bundle_hash; print(bundle_hash('sealed'))"` on the finished bundle, send the hash and the salt hash to the author for `locked.yaml` (`sealed_bundle_sha256`, `identity_salt_sha256`), keep the bundle outside the repository until the unseal, and keep an access log in `sealed/README.md`.
4. **Checks you run before the lock** (B1 only): `uv run pytest tests/test_families.py -k H2` after adding your family to a scratch copy of the test's family list; `uv run python scripts/h1.py --backend fake-honest --rules B1 --calibration experiments/calibration_T100.json --smoke --out /tmp/b1 --prompt sealed/h1_prompt.txt`; one search cell of H2 against B1 with `scripts/sweep.py --smoke --select B1_H2` after registering H2 in a scratch copy of `scripts/sweep.py`'s family table. Record pass or fail in `b1_check.json`.
5. **At the unseal (week 5).** The bundle enters the repository under `sealed/`; CI runs `scripts/check_claim.py --verify-freeze <freeze tag>` which checks the bundle hash; the author then registers H2 in the sweep's family table through the allow-listed mechanism (a `sealed/` module is allow-listed; the sweep's table reads `sealed/h2/family.py` when present, the only post-lock code path that imports from `sealed/`), runs the comprehension fixture, then H1, H2, and the twins on the frozen rule and the baselines on the final-eval namespace, then `scripts/check_claim.py`.
6. **Repairs.** A repair after the unseal is a separately hashed patch under `sealed/patches/` with its SHA-256 in `sealed/patches/log.json`, written by you, limited to interface errors, logged, and reported; the original bundle is never edited. A repair that changes any H1 or H2 decision on a dev-val seed demotes the affected cell to exploratory; say so in the patch log.
7. **Timeline.** Bundle complete by 2026-10-27; commitment hashes to the author by 2026-10-27 so the lock commit on 2026-10-28 carries them; unseal on 2026-11-12.

`docs/lock-runbook.md`: the ordered commands for the lock day (calibrate at T = 200 and T = 100; tune; the full sweep; `scripts/coverage_study.py`; the two pilots; `scripts/lock.py` with the custodian's hashes and the cost cap; `scripts/lock.py --check`; `scripts/check_claim.py --verify-lock <tag>` on a throwaway tag; the signed tag; the push; the public timestamp), and the freeze day (`git tag -s freeze-2026-11-11`; `scripts/check_claim.py --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11`).

Spec section 14: append an implementation note "Plan 2B" listing rulings D1 to D8 with one sentence each, the coverage manifest figure, the H1 call count, and the statement that `scripts/plot.py` and `docs/` are outside the predicate.

README: in Status, replace the last sentence with the plan 2B summary (intervals, coverage study, model actors with Anthropic and Jev backends, the describe renderer and vocabulary, the comprehension fixture, the H1 runner with the pilot, `check_claim.py`, `lock.py`, figures, custodian instructions); add under the pre-registration section the sentence that H1 is a five-episode adaptive procedure with profit feedback, not the normalized-gain search, and the line `sealed bundle SHA-256: (written at the lock)`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_docs.py -v`
Expected: PASS.

- [ ] **Step 5: Run the whole suite and the benchmarks**

Run: `uv run pytest -q` and `uv run python scripts/bench.py` and `uv run python scripts/bench_sweep.py`.
Expected: every test passes (162 from plan 2A plus about 48 new); the benchmarks stay under their gates (45 ms per episode, 20 core-hours for the search manifest); the manifest's coverage line is printed separately. Record the three figures in the ledger.

- [ ] **Step 6: Commit**

```bash
git add docs/custodian.md docs/lock-runbook.md docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md README.md tests/test_docs.py
git commit -m "docs: custodian instructions for the sealed bundle, lock run book, plan 2B spec note, README status"
```

---

## Self-review (done while writing; the executor re-checks against the spec)

1. **Spec coverage.** 5.4 actor, schema, cache, fallback, invalidity, five-episode procedure, twin, clipped re-run, describe renderer, vocabulary, comprehension fixture, token pilot: Tasks 3, 4, 6. 6 lock contents, allow-list, hash checks after the freeze, repairs, final-eval seeds released with the bundle: Tasks 1, 7, 9. 6.1 bundle contents and the custodian's B1-only check: Task 9 (`docs/custodian.md`) and Task 7 (`sim/sealed.py`). 8 interval algorithms, coverage study (selection, pools, replications, endpoints, thresholds, joint fixture, power, remedies, consequences), claim predicate, decision rule, figures, units: Tasks 2, 5, 7, 8. 11 layout: `llm_actor.py`, `policies/llm.py`, `vocabulary.yaml`, `coverage_study.py`, `plot.py`, `check_claim.py`, `sealed/`: present; `scripts/run.py` is plan 1. 12 tests: LLM replay byte-identical (Task 4), describe-record vocabulary and renderer spy and noninterference (Task 3), lock and freeze hash checks and the new-file refusal (Task 7), `proposed.py` import restriction and frozen-module attribute check (not in this plan: `proposed.py` does not exist before the lock; the test is written at the freeze and is listed in `docs/lock-runbook.md` as a post-lock item), sealed bundle hash check (Task 7). 13 gate for 10-18 to 10-28: Task 9 step 5. Gaps: the enforcement-matched ablation runs and the bank's post-lock application are plan 2A code paths run post-lock; the held-out family registration in the sweep's table at the unseal is described in `docs/custodian.md` and is a post-lock, allow-listed step.
2. **Placeholders.** None: every step has its code or its exact command; the two documents in Task 9 have their required sections listed; the pilots are the user's step by design.
3. **Type consistency.** `Bound` fields (Task 2) are read by `covered` (Task 5) and `decide` (Task 7) as `value`, `side`, `degenerate`; `endpoint_key` (Task 5) is the key format `check_claim.py` reads from `admitted_sides` (Task 7); `h1_rows` columns (Task 4) are the columns `scripts/h1.py` writes (Task 6, `FIELDS`) and `h1_frame` renames (Task 7); `ProcedureResult.cache_hits` and `H1CellResult.new_calls_clipped` are read by `scripts/h1.py`; `make_backend(name, locked, instructions)` is called by `scripts/h1.py` with three arguments; `coverage_cells` reads `runs_per_seed` from the selection file that `scripts/coverage_study.py` writes; `job_from_record` rebuilds the fields `base_record` stores.
4. **Review Focus.** Every line names its test: 1 and 2 in Task 2; 3 in Task 5 (`test_cell_selection_handles_degenerate_rankings`); 4 and 5 in Task 4; 6 in Tasks 3 and 7; 7 in Task 7.
