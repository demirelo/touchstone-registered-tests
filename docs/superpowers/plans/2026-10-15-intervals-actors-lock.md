# Touchstone plan 2B (version 3): intervals, coverage study, model actors, describe renderer, claim check, lock tooling, plots, custodian instructions

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete every pre-lock deliverable the spec names after plan 2A: the locked interval algorithms, the coverage study with its joint fixture test and power check, the model-actor harness (LLM and the Jev decision model) with the `describe()` renderer, vocabulary, comprehension fixture, and the H1 five-episode procedure, the token pilot, `check_claim.py` with the predicate and the lock and freeze hash checks, the lock script, the figures, and the custodian instructions for the separate session, so that the lock on 2026-10-28 can be cut from a repo in which every tool the post-lock weeks need already exists and is frozen.

**Architecture:** Statistics live in pure functions over numpy arrays (`sim/intervals.py`, `sim/coverage.py`) with the market work behind them produced by the plan 2A cell runners and recorded by the schedule. The model actor is a `Policy` whose decisions come from a `Backend` behind a prompt-hash cache: an Anthropic backend (structured JSON output), a Jev backend (typed Choice questions over a discretized action menu), and a fake backend for tests; the H1 procedure, fallback accounting, invalidity rule, and the closed-loop clipped re-run live in `sim/llm_actor.py` and never touch the market loop. The `describe()` record is validated against `experiments/vocabulary.yaml` and rendered by one frozen template. `scripts/check_claim.py` is the only reader of final results: it verifies hashes against the lock and freeze tags, admits bounds the coverage study admitted, and evaluates the predicate. `scripts/lock.py` writes the lock-time blocks into `locked.yaml` and prints the tag command for the author to sign.

**Tech Stack:** Python 3.12+, numpy, scipy (stats: t, nct, skew, bootstrap helpers written here), pandas and matplotlib for figures, `anthropic` SDK (`claude-opus-5-5` by default, pinned snapshot id recorded in `locked.yaml`), `typesafe-sdk` for Jev (`jev-1.14.0`), pyyaml, pytest. No network in tests: both real backends are exercised only through the fake backend and recorded fixtures.

**Spec:** `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (version 7.5 plus the plan 1 and plan 2A implementation notes). This plan implements sections 5.4 (LLM actor, describe renderer, comprehension fixture, H1 procedure, token pilot), 6 (lock contents, allow-list, hash checks, freeze, repairs), 6.1 (what the sealed bundle must contain, as instructions to the separate session), 8 (interval algorithms, coverage study, joint fixture test, power, pre-registered consequences, claim predicate, decision rule, figures), 11 (layout: `llm_actor.py`, `policies/llm.py`, `vocabulary.yaml`, `coverage_study.py`, `plot.py`, `check_claim.py`, `sealed/`), 12 (the remaining tests), and 13 (the gate for 10-18 to 10-28). It also folds the deferred minors of the plan 2A final review that touch frozen files.

**Scope split, stated once:** Plan 2B ends when `scripts/check_claim.py --verify-lock` passes on a lock-candidate tree, `scripts/coverage_study.py` runs end to end at a smoke size and at the registered size from the manifest, the model actor runs the H1 procedure against B1 to B3 with the fake backend and with cached real responses, the token pilot script exists and has been run once per backend by the user, `scripts/plot.py` draws figures 1 and 2 from the sweep CSVs, and `docs/custodian.md` tells the separate session exactly what to produce. The proposed rule, the sealed H1 prompt and H2 definition, and every post-lock run are outside this plan.

**Changes from version 2 (both seats rejected v2):** the frozen post-lock paths now run end to end (the manifest drops `proposed` from the pre-lock entries and lists it once in `heldout`; the schedule counts corners of a registered family through the registry; the sweep loads H2 through `available_families(locked)`, writes the bundle hash into every record, computes headline positions for `heldout`, and evaluates `4 x final_eval_n` runs under `final_eval`); a test runs `--sections heldout --rules B2,proposed` through every stage with a synthetic H2 whose corner count differs from D2's; the conditional n = 40 run triggers when both n = 20 procedures fail; the pool is observed once per cell and reused across n; `nct.cdf` NaN tails are filled by the sign of the noncentrality; the threshold check uses the between-pool standard error, runs at every M used, and a failure withholds admission at that n; `manifest_weights` ignores coverage rows when it collects rule names; the vocabulary uses block lists, carries B1's acceptance condition and tier rule and B3's eligibility and runner-up rule in words, and refuses non-finite figures; the budgeted backend reserves the cost of the next request and keeps a cumulative ledger across runs; the patch log entries name the file they replace and `effective_path` applies them to the prompt, the family, and the seeds without touching the original bundle; `check_proposed_module` snapshots every loaded `sim.*` module including function code and defaults and re-checks after `make(params)`; confirmatory `check_claim.py` rebuilds every held-out job and runs the sweep's own record check, requires the exact first `final_eval_n` sealed seeds in order, the LLM model, the locked T = 100 calibration hash, complete comprehension scores, and the frozen description record; the lock script requires both commitments, a finite positive cap, a complete pilot of the registered size, complete fixture, power, and threshold-check evidence, and re-validates under `--check`; tree checks use `git diff --name-status -z`; H1 figures use the t bound in every mode; the custodian and run-book commands were executed as written; the H1 cache directory is allow-listed (D3 amended); the coverage study runs one cell per process or per machine (`--cell`) with a `--merge` step, so the six cells can run on six CPU pods.

**Changes from version 1 (both seats rejected v1):** registries for the proposed rule and the sealed H2 family, the `heldout` section, and the final-eval sample size from the coverage consequences, so no frozen file needs a post-lock edit (new Task 1b); the import and attribute check for `proposed.py` written now against synthetic modules; `budget` in the CSV schema; the evaluation namespace checked before any record; `settings_hash` ignores `h1.cost_cap_usd` and `coverage_consequences`; vocabulary values that carry the baselines' selection rules and payment formulas, numeric frames, and numeric fixture questions; the backend protocol carries `instructions`, the cache stores the canonical request, and every wrapper forwards the prompt; a budgeted backend enforces the calls and cost caps and the pilot target before each uncached request; invalid repetitions counted once per repetition and applied to baseline H1 cells; H1 reference selection on dev-train (D10); the coverage study rewritten for memory (chunked scalar observations, serializable worker payloads), scipy's Hermite rule, the registered selection rule (D12), the registered threshold simulation saved in the report, independent statistics in the joint fixture, one coherent (M, R) per n, conditional n = 40, input validation through the sweep's own record check, and the manifest's trajectory graph outside the search gate (D8); required families from the lock, mandatory provenance in confirmatory mode, `--verify-only`, headline position for H2, patch demotions, caches outside `sealed/`, `-z` git parsing; the lock script's hash invariance and input validation with `--salt-hash`; figures read the admitted method and the per-budget position and take H1 rows; corrected run-book commands.

**Design decisions in this plan (rulings for the executor's ledger and the spec note):** (D1) Jev is a second model backend behind the same actor interface as the LLM, with the action space discretized into a registered menu (effort levels and claim offsets as Choice questions); it is a development-side actor for the model-actor table, not a held-out family, because H1 is defined as the sealed LLM. (D2) The coverage study draws its reference pools and replications from a dedicated contiguous seed range `seeds.coverage` (start 3,000,000), disjoint from dev-train, dev-val, calibration, and the custodian's final-eval range, because the 20-element dev-val list cannot supply 35,000 seeds per cell; the spec note records this as the dev-val namespace's coverage sub-range. (D3) The prompt cache is a content-addressed directory of JSON files keyed by the SHA-256 of the canonical request (which includes the system prompt), under `experiments/cache/<backend>/` for development runs and `experiments/cache/h1/<backend>/` for the H1 runs after the unseal, never under `sealed/`; `experiments/cache/h1/` is on the allow-list so the post-lock cache can be committed as the replay evidence; replay is byte-identical without the network. (D4) Fallback rounds are counted per repetition and the invalidity rule (more than 5% fallback rounds) marks the repetition; the statistic always includes all 10 repetitions. (D5) `check_claim.py` reads the admitted-sides table from the coverage report by (statistic, side, level, n) and refuses a clause whose needed side is absent. (D6) The lock script writes `tuned`, `calibration`, `coverage_report_sha256`, `sealed_bundle_sha256`, `h1` (budget, cost cap, model ids), and `intervals` into `locked.yaml`, and prints the `git tag -s` command; the salt commitment is written by the separate session. (D7) T = 100 for every H1 run with its own calibration (`scripts/calibrate.py --T 100`), as the spec says S_hat, B, and the twin are calibrated at T = 100. (D8) The coverage study's workload follows spec 5.3 lines 450 to 463: `manifest.py` enumerates unique trajectory keys per cell seed (the cell rule's attack, clipped attack, and reference unless abstain; the B2 and B3 attacks and clipped attacks for the loss-difference endpoint; a key is reused when the cell rule is B2 or B3), the base entry is the pools plus the replications at n = 10 and n = 20, and n = 40, the M doubling, and the R doubling are conditional entries run only when the registered remedy order reaches them; the study runs n = 10 and n = 20 first. The base entry is about 6 x 95,000 seeds x 4 to 7 keys, 2.3 to 4.0 million episodes, 19 to 33 core-hours at 29 ms (the spec's planning figure is 2.3 to 2.9 million), outside the search gate and excluded from `manifest_weights`; the observations are reduced to scalars per seed in chunks so memory stays flat. (D9) Baseline parameters for the H1 market are the T = 200 tuned parameters: `scripts/h1.py` verifies the tuned files against the T = 200 calibration's market key and settings hash, and builds the H1 market from the T = 100 calibration; both calibrations are inputs and both are hashed into `locked.yaml`. (D10) H1 reference selection (spec 5.2 and 5.4) runs the twin procedure with the evaluation episode on each of the 5 dev-train seeds (episodes 1 to 4 on `dev_train[:4]` as always), compares the mean normalized profit of the twin, honest-max, and abstention on those seeds in the registered order (abstain, honest_max, twin; ties to the earlier), and evaluates the chosen reference on the evaluation seeds; the H1 gain is attack minus that reference, and the twin difference is reported next to it. The 10 repetitions share the dev-train episodes, so with a deterministic cached actor they differ only in episode 5; the spec note and README say so. (D11) The comprehension rule compares the proposed rule's score with the minimum of B2's and B3's scores (B1 is not in the predicate): H1 is INCONCLUSIVE when `score(R*) < min(score(B2), score(B3)) - 1`. (D12) The coverage selection rule, registered exactly: take the top 3 by gain skewness and the top 3 by the Sarle coefficient of ban counts (finite values only, descending, cell name as the tie-break); their union, in the order skewness picks then Sarle picks, is the selection; while fewer than 6, add the next unused entry of the ranking that has contributed fewer distinct cells (ties go to skewness), and when a ranking is exhausted take from the other; `--smoke` selects the first 6 cells by name and marks the report `unranked`.

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
  - `locked.yaml` gains `seeds.coverage: {start: 3000000, block: 600000, pool: 35000, replications: {"10": 2000, "20": 2000, "40": 4000}, n_grid: [10, 20, 40]}` (one block of 600,000 seeds per selected cell: room for the pool and the replications with both doublings), `intervals: {bootstrap_resamples: 10000, bootstrap_seed: 20261111, h1_repetitions: 10, reference_level: 0.95, margins: {"0.95": 2.0, "0.9875": 1.0}, deficits: {"0.95": 3.0, "0.9875": 1.5}, joint_trials: 200, joint_min_admitted: 190, quadrature_nodes: 200, remedy_order: [percentile, studentized, studentized_n40]}`, `h1: {model: claude-opus-5-5, jev_model: jev-1.14.0, T: 100, episodes: 5, repetitions: 10, betas: [0.02, 0.05, 0.10], fallback_limit: 0.05, invalid_limit: 2, cost_cap_usd: null, calls_cap: 192000}`, `claim: {beta: 0.05, eff_min: 0.90, gain_max: 0.30, loss_diff_min: 0.05, baseline_gain_min: 1.0, rule_level: 0.95, baseline_level: 0.9875}`, `allow_list: [sim/mechanisms/proposed.py, experiments/proposed.yaml, experiments/proposed_describe.yaml, experiments/cache/h1/, scripts/plot.py, docs/, sealed/, sealed/patches/]`, `calibration: null`, `sealed_bundle_sha256: null`, `coverage_report_sha256: null`, `comprehension_fixture_sha256: null`.
  - `sweep.py` reference records carry `attack_per_seed_normalized` and `reference_per_seed_normalized` (dev-train) and `reference_per_seed_profit`; `--eval-namespace {dev_val,final_eval}` selects the evaluation seeds of the `evaluate` stage (default `dev_val`; `final_eval` refuses to run, before any record is read, unless the namespace is available: `locked.yaml` or the verified sealed bundle, Task 7); under `final_eval` the number of evaluation seeds is `locked["coverage_consequences"]["final_eval_n"]` (20 or 40) instead of the budget's `n_val`; `META_FIELDS` gains `budget` and `meta_of` writes `float(job["cfg"]["budget"])` into every per-seed row; a record whose rule is not in the current `--rules` raises `SystemExit` naming the rule.
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
    filled["h1"] = dict(lk["h1"], cost_cap_usd=120.0)
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
    from scripts.sweep import train_val
    from sim.schedule import Budget, stage_runs
    job = {"budget": [1, 16, 1, 2], "locked": dict(lk, coverage_consequences={"final_eval_n": 3}, seeds=dict(lk["seeds"], final_eval=[9, 8, 7, 6])), "eval_namespace": "final_eval"}
    _, val, b = train_val(job)
    assert val == (9, 8, 7) and b == Budget(1, 16, 1, 3) and stage_runs("D1", "evaluate", b) == 12      # the evaluate count follows final_eval_n
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

In `sim/locked.py`, extend the exclusion list of `settings_hash` to `("version", "tuned", "calibration", "identity_salt_sha256", "sealed_bundle_sha256", "coverage_report_sha256", "comprehension_fixture_sha256", "coverage_consequences")`, and inside the bound dict replace `h1` by `{k: v for k, v in locked["h1"].items() if k != "cost_cap_usd"}` (the cost cap is measured by the pilot and written at the lock); change the docstring to name them as the blocks written at the lock. Add to the Task 1 test: `filled["h1"] = dict(lk["h1"], cost_cap_usd=120.0)` before the final equality.

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
- in `train_val`, take the evaluation namespace from `job["eval_namespace"]` (default `"dev_val"`); under `final_eval` use `n_eval = int((lk.get("coverage_consequences") or {}).get("final_eval_n") or b.n_val)` seeds and return `Budget(b.restarts, b.evals, b.n_train, n_eval)` as the budget, so `stage_runs(family, "evaluate", b)` in `stage_evaluate` counts `4 x n_eval` (the 40-seed remedy then passes the exact run check); in `run_stages`, before `load_params` and before any record is read, `try: locked_seeds(lk, ns) except ValueError as e: raise SystemExit(f"evaluation namespace {ns} is not available: {e}")`;
- in the evaluate stage's headline computation, include every section whose cells run all three positions at the headline beta (`development` and `heldout`), so `headline.json` carries `"<rule>/H2"` keys after the unseal;
- `--shard K/N` (search stage only): the selected cells are sorted by name and cell `i` runs when `i % N == K`; each shard writes its own records into `--out`, and the later stages run once over the union of the shard outputs (copy the `search/` directories together); a test runs `--shard 0/2` and `--shard 1/2` into one directory and checks the record set equals the unsharded run's;
- `META_FIELDS = ["cell", "section", "rule", "family", "beta", "rho", "position", "smoke", "reference", "budget"]` and `meta_of` adds `"budget": float(job["cfg"]["budget"])`; update the header assertion in `tests/test_sweep.py::test_smoke_sweep_runs_every_stage_with_counted_runs` to the new `META_FIELDS + ROW_FIELDS`;
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

### Task 1b: Registries for the proposed rule and the sealed family, and the `heldout` section

**Files:**
- Create: `sim/registry.py`
- Modify: `sim/tuning.py` (`rule_from_params` delegates `proposed`), `scripts/sweep.py` (`family_of`, `load_params` for `proposed`, `ALL_FAMILIES` from the registry), `sim/manifest.py` (`heldout` section)
- Test: `tests/test_registry.py`

**Why before the lock:** `sim/tuning.py`, `scripts/sweep.py`, `sim/manifest.py`, and `tests/` are frozen at the lock (spec 6). The proposed rule and H2 enter only through allow-listed files (`sim/mechanisms/proposed.py`, `experiments/proposed.yaml`, `sealed/`), so the frozen code must already know how to load them when they appear.

**Interfaces:**
- Consumes: `rule_from_params` (`sim/tuning.py`), `FAMILIES`, `Family` (`sim/policies/families.py`), `h3_family`, `verify_bundle` and `load_bundle` (Task 7; until Task 7 exists, `available_families` imports them lazily and a missing `sim.sealed` means no H2).
- Produces (`sim/registry.py`):
  - `PROPOSED_MODULE`, `PROPOSED_PARAMS`, `SEALED_DIR`: `Path`s from the environment variables `TOUCHSTONE_PROPOSED_MODULE`, `TOUCHSTONE_PROPOSED_PARAMS`, `TOUCHSTONE_SEALED_DIR` (tests) or the repository defaults `sim/mechanisms/proposed.py`, `experiments/proposed.yaml`, `sealed/`.
  - `proposed_available() -> bool`; `load_proposed_module()` (imports the module from its path; it must define `make(params: dict)` returning a `Mechanism` whose `describe()` is a vocabulary record; a module without `make` raises `ValueError`); `proposed_params() -> dict` (the YAML's `best_params`, with `market_key`, `settings_hash`, `calibration_seeds` for `load_params`' checks).
  - `make_rule(rule_name: str, params: dict)`: B1 to B3 as `rule_from_params`, `"proposed"` through the module.
  - `available_families(locked: dict | None = None) -> dict[str, Family]`: `FAMILIES` plus `"D2+H3"`, plus `"H2"` (from `sealed/h2/family.py`, attribute `H2`) when `SEALED_DIR / "h2/family.py"` exists and, if `locked` is given, the bundle verifies; `"H2+H3"` is not registered (H2 never exits, spec 6.1).
  - `available_rules() -> list[str]`: `["B1", "B2", "B3"]` plus `"proposed"` when available.
- Produces (`sim/manifest.py`): `_full_cells` takes `families: tuple[str, ...]`; `enumerate_manifest(locked, rules, budget=None)` separates `baselines = [r for r in rules if r != "proposed"]` (the pre-lock entries, tuning grids, and bank are built from the baselines only, so `rules` may contain `proposed` without a `KeyError`) and lists, when `"H2"` is in the registry, a `heldout` section: for every rule in `baselines + (["proposed"] if proposed_available() else [])` (once each) and every beta in the grid, positions at the headline beta, `kind = "full_cell"`, `post_lock = True`, family `"H2"`, `runs = sum(cell_runs("H2", b_eval).values())` where `b_eval` replaces `n_val` by `coverage_consequences.final_eval_n` when set.
- Produces (`sim/schedule.py`): `cell_runs(family_name, b)` counts corners as `N_CORNERS[family_name]` when known, else `len(available_families()[family_name].corners()) * b.n_train` (the custodian's family declares its own knobs), so a registered H2 schedules without an edit.
- Produces (`scripts/sweep.py`): `family_of(name)` reads `available_families(locked)` (the bundle is verified against the lock commitment before H2 is used; before the lock, with no commitment, `available_families(None)`); every record of an H2 cell carries `"bundle_hash": bundle_hash(SEALED_DIR)`; `load_params("proposed", ...)` reads `proposed_params()` and applies the same four checks as a tuned file; `rule_from_params` is replaced by `make_rule` everywhere in the script; the `heldout` section is accepted by `--sections`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_registry.py
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from sim.config import MarketConfig
from sim.locked import load_locked, settings_hash

ROOT = Path(__file__).resolve().parents[1]
PROPOSED_SRC = '''
from sim.mechanisms.posted_audit import PostedRandomAudit

def make(params):
    return PostedRandomAudit(params["P1"], params["P2"], params["P3"], tol=params["tol"], L=params["L"])
'''
H2_SRC = '''
from sim.policies.families import D2, Family
# A synthetic family named H2 with its own knob set so the corner count differs from D2's (schedule test).
H2 = Family("H2", D2.knob_names[:-1] + ("clip",), D2.make, D2.project, D2.registered_starts_fn, D2.exact_key_fn, D2.knob_key_fn)
CONTAINMENT = "H2 is D2 with one fewer knob (synthetic test family)"
'''


def synthetic_env(tmp_path, monkeypatch, with_sealed=True):
    (tmp_path / "proposed.py").write_text(PROPOSED_SRC)
    lk = load_locked()
    (tmp_path / "proposed.yaml").write_text(yaml.safe_dump({"rule": "proposed", "best_params": {"P1": 0.25, "P2": 0.4, "P3": 0.55, "tol": 0.1, "L": 5},
                                                             "market_key": "k", "settings_hash": settings_hash(lk), "calibration_seeds": [1]}))
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_MODULE", str(tmp_path / "proposed.py"))
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_PARAMS", str(tmp_path / "proposed.yaml"))
    if with_sealed:
        s = tmp_path / "sealed"; (s / "h2").mkdir(parents=True); (s / "h2" / "family.py").write_text(H2_SRC)
        monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(s))
    return tmp_path


def test_registry_loads_the_proposed_rule_and_the_sealed_family(tmp_path, monkeypatch):
    import importlib
    synthetic_env(tmp_path, monkeypatch)
    import sim.registry as reg; importlib.reload(reg)
    assert reg.proposed_available() and reg.available_rules() == ["B1", "B2", "B3", "proposed"]
    rule = reg.make_rule("proposed", reg.proposed_params()["best_params"])
    assert rule.tol == 0.1 and rule.L == 5                       # the describe() record is checked in Task 3's tests
    fams = reg.available_families()
    assert set(fams) == {"D1", "D2", "D2+H3", "H2"} and fams["H2"].name == "H2" and len(fams["H2"].corners()) != len(fams["D2"].corners())
    from sim.schedule import cell_runs, budget_from_locked
    b = budget_from_locked(lk); assert cell_runs("H2", b)["corners"] == len(fams["H2"].corners()) * b.n_train
    from sim.tuning import rule_from_params
    assert rule_from_params("proposed", {"P1": 0.25, "P2": 0.4, "P3": 0.55, "tol": 0.1, "L": 5}).name == rule.name


def test_registry_without_the_files_has_only_baselines(tmp_path, monkeypatch):
    import importlib
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_MODULE", str(tmp_path / "nope.py")); monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(tmp_path / "nosealed"))
    import sim.registry as reg; importlib.reload(reg)
    assert not reg.proposed_available() and reg.available_rules() == ["B1", "B2", "B3"] and "H2" not in reg.available_families()
    with pytest.raises(ValueError):
        reg.make_rule("proposed", {})


def test_manifest_lists_heldout_cells_only_when_h2_is_registered(tmp_path, monkeypatch):
    import importlib
    from sim.manifest import enumerate_manifest, totals
    lk = load_locked()
    monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(tmp_path / "nosealed")); import sim.registry as reg; importlib.reload(reg)
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    assert not any(c.section == "heldout" for c in cells)
    synthetic_env(tmp_path, monkeypatch); importlib.reload(reg)
    cells = enumerate_manifest(lk, ["B1", "B2", "B3", "proposed"])            # proposed in --rules never reaches the tuning grids or the bank
    held = [c for c in cells if c.section == "heldout"]
    n_betas = len(lk["beta_grid"]); n_pos = len(lk["positions"])
    assert len(held) == 4 * (n_betas - 1 + n_pos) and all(c.post_lock and c.family == "H2" for c in held) and {c.rule for c in held} == {"B1", "B2", "B3", "proposed"}
    assert len({c.name for c in held}) == len(held) and not any(c.rule == "proposed" and c.section != "heldout" for c in cells if not c.post_lock)
    t = totals(cells)
    assert t["heldout"] > 0 and t["pre_lock"] == totals([c for c in cells if c.section != "heldout"])["pre_lock"]
    from sim.schedule import budget_from_locked
    lk40 = dict(lk, coverage_consequences={"final_eval_n": 40, "h1": "confirmatory", "parametrized": "studentized_n40"})
    held40 = [c for c in enumerate_manifest(lk40, ["B2"]) if c.section == "heldout"]
    assert held40[0].runs - held[0].runs == 4 * (40 - budget_from_locked(lk).n_val)


def test_sweep_smoke_runs_the_proposed_rule_and_h2_through_every_stage(tmp_path, monkeypatch):
    # The documented post-lock command on the locked market with a smoke budget: every stage, a baseline and the proposed
    # rule, the synthetic H2 whose corner count differs from D2's, the bundle hash in the records, and the H2 headline.
    import os
    from sim.calibrate import calibrate, save_calibration
    from sim.locked import market_config_from_locked
    synthetic_env(tmp_path, monkeypatch)
    lk = load_locked(); save_calibration(calibrate(market_config_from_locked(lk), [4000, 4001]), tmp_path / "cal.json")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "sweep.py"), "--stage", "all", "--sections", "heldout", "--rules", "B2,proposed",
                        "--calibration", str(tmp_path / "cal.json"), "--smoke", "--select", "beta0.05", "--out", str(tmp_path / "out")],
                       capture_output=True, text=True, cwd=ROOT, env=dict(os.environ))
    assert r.returncode == 0, r.stderr
    evals = {p.stem: json.loads(p.read_text()) for p in (tmp_path / "out" / "evaluate").glob("*.json")}
    assert {v["spec"]["rule"] for v in evals.values()} == {"B2", "proposed"} and all(v["spec"]["family"] == "H2" and v.get("bundle_hash") for v in evals.values())
    head = json.loads((tmp_path / "out" / "headline.json").read_text())
    assert "B2/H2" in head and "proposed/H2" in head and head["B2/H2"]["headline"] in ("low", "median", "high")
```

(`--smoke` with `--rules proposed` uses `DEFAULT_PARAMS`; add `"proposed": dict(DEFAULT_PARAMS["B2"])` to `DEFAULT_PARAMS` so the smoke path has parameters for the synthetic module, which wraps B2. The `Family` constructor's positional argument order and the attribute names `knob_names`, `registered_starts_fn`, `exact_key_fn`, `knob_key_fn` used by `H2_SRC` must match `sim/policies/families.py`; read the class before writing the fixture and adapt the fixture, not the class. The `--select beta0.05` substring keeps the smoke run to the headline-beta cells of both rules, which is where the headline position is computed. Before the lock `sealed_bundle_sha256` is null, so `family_of` loads the synthetic H2 without a bundle check; after the lock the check is mandatory.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.registry'`.

- [ ] **Step 3: Write the implementation**

```python
# sim/registry.py
"""Where frozen code finds the two things that arrive after the lock: the proposed rule (allow-listed module and
parameter file) and the sealed H2 family (spec 6). Environment variables point tests at synthetic copies."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import yaml

from .policies.families import FAMILIES, Family
from .policies.identity import h3_family

ROOT = Path(__file__).resolve().parents[1]


def _path(env: str, default: str) -> Path:
    return Path(os.environ.get(env) or (ROOT / default))


PROPOSED_MODULE = _path("TOUCHSTONE_PROPOSED_MODULE", "sim/mechanisms/proposed.py")
PROPOSED_PARAMS = _path("TOUCHSTONE_PROPOSED_PARAMS", "experiments/proposed.yaml")
SEALED_DIR = _path("TOUCHSTONE_SEALED_DIR", "sealed")


def _import(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def proposed_available() -> bool:
    return PROPOSED_MODULE.exists()


def load_proposed_module():
    if not proposed_available():
        raise ValueError(f"no proposed rule module at {PROPOSED_MODULE}")
    mod = _import(PROPOSED_MODULE, "touchstone_proposed")
    if not callable(getattr(mod, "make", None)):
        raise ValueError("the proposed rule module must define make(params) -> Mechanism")
    return mod


def proposed_params() -> dict:
    return yaml.safe_load(PROPOSED_PARAMS.read_text())


def make_rule(rule_name: str, params: dict):
    from .tuning import rule_from_params
    if rule_name == "proposed":
        return load_proposed_module().make(dict(params))
    return rule_from_params(rule_name, params)


def available_families(locked: dict | None = None) -> dict:
    fams: dict = dict(FAMILIES); fams["D2+H3"] = h3_family(FAMILIES["D2"])
    h2 = SEALED_DIR / "h2" / "family.py"
    if h2.exists():
        if locked is not None:
            from .sealed import verify_bundle
            verify_bundle(SEALED_DIR, locked)
        mod = _import(h2, "sealed_h2_family")
        fam = getattr(mod, "H2", None)
        if not isinstance(fam, Family):
            raise ValueError("sealed/h2/family.py must define H2, a Family")
        fams["H2"] = fam
    return fams


def available_rules() -> list:
    return ["B1", "B2", "B3"] + (["proposed"] if proposed_available() else [])
```

In `sim/tuning.py::rule_from_params`, before `raise ValueError(rule_name)`: `if rule_name == "proposed": from .registry import load_proposed_module; return load_proposed_module().make(dict(params))`.

In `scripts/sweep.py`: `ALL_FAMILIES` is replaced by `def family_of(name): return available_families()[name]` (the registry re-reads the sealed path each call so a bundle unsealed later is seen without a restart); every `rule_from_params(rule, params)` call becomes `make_rule(rule, params)`; in `load_params`, when `rule == "proposed"` and `tuned_dir` is not `None` or not smoke, read `proposed_params()` instead of `tuned_dir / "tuned_proposed.json"` and apply the same `rule`, `market_key`, `settings_hash`, `calibration_seeds` checks; `DEFAULT_PARAMS["proposed"] = dict(DEFAULT_PARAMS["B2"])`; the `--sections` help lists `heldout`.

In `sim/manifest.py`: `_full_cells(locked, rules, b, post_lock, families=("D1", "D2"), section="development")` loops over `families`; `enumerate_manifest(locked, rules, budget=None)` sets `baselines = [r for r in rules if r != "proposed"]` and builds every existing entry from `baselines`; then, when `"H2" in available_families()` (imported lazily from `sim.registry`), it appends `_full_cells(locked, baselines + (["proposed"] if proposed_available() else []), b_eval, post_lock=True, families=("H2",), section="heldout")` with `b_eval = Budget(b.restarts, b.evals, b.n_train, final_eval_n or b.n_val)`; `totals` already keys by section and `post_lock`; `manifest_weights` already skips `post_lock` rows. In `sim/schedule.py::cell_runs`: `corners = N_CORNERS[family_name] if family_name in N_CORNERS else len(available_families()[family_name].corners())` (lazy import of `sim.registry`). In `scripts/sweep.py`, `family_of` calls `available_families(lk if lk.get("sealed_bundle_sha256") else None)`, and `base_record` adds `"bundle_hash": bundle_hash(SEALED_DIR) if job["spec"]["family"] == "H2" else None`; the headline loop in the evaluate stage includes `s["section"] in ("development", "heldout")`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_registry.py tests/test_manifest.py tests/test_sweep.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add sim/registry.py sim/tuning.py scripts/sweep.py sim/manifest.py tests/test_registry.py
git commit -m "feat: registries for the proposed rule and the sealed H2 family; heldout manifest section; sweep runs any registered rule and family"
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
  - The baselines' `describe()` records use vocabulary values whose text carries the operational rule: B1 `allocation_order: "descending job value, each job to the highest posted tier its claim reaches, at random within a tier"`, `eligibility: "active offers with capacity"`, `payment: "the posted price of the highest tier the claim reaches"`, the audit and enforcement fields `"none"`; B2 as B1 with `audit_selection: "uniform random among served jobs, spread evenly over rounds"`, `audit_tolerance: "number"` plus a `parameters` sub-record `{"audit_tolerance": tol, "ban_length": L}`, `failed_audit: "full refund of the audited job"`, `ban_length: "number"`; B3 with `allocation_order: "descending score, where score = job value times claim minus bid, capacity respected"`, `payment: "second score, equal to job value times claim minus the runner-up score"`, audits and enforcement as B2. The vocabulary's `numeric` map names the values that need a figure in `parameters` (validated as a number); `NUMBER_FRAMES` renders them; `correct_value(record, answer_from)` resolves `parameters.<field>` questions.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_describe.py
import pytest
from sim.describe import (DESCRIBE_FIELDS, NOT_EXPRESSIBLE, load_vocabulary, validate_record, render, uses_not_expressible,
                          describe_record, comprehension_questions, score_comprehension, correct_value)
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
    assert "0.12" in text and "banned for 10 rounds" in text and "uniform random" in text and "PostedRandomAudit" not in text
    assert "claim times the job value reaches the tier price" in text and "0.5 to below 0.8" in text and "tier the job was allocated in" in text   # the acceptance condition, the tiers, the payment
    b3 = render(describe_record(SecondScore(tol=0.12, L=10)), voc)
    assert "score = job value times claim minus bid" in b3 and "negative score are not eligible" in b3 and "zero when there is none" in b3
    for bad in ("twelve", float("nan"), float("inf"), True):
        with pytest.raises(ValueError, match="numeric"):
            validate_record(dict(rec, parameters=dict(rec["parameters"], audit_tolerance=bad)), voc)
    assert len(voc["numeric"]["holdback"]) == 2 and all("," in v for v in voc["numeric"]["holdback"])             # YAML kept the two values whole
    hb = dict(rec, holdback=voc["numeric"]["holdback"][0])
    with pytest.raises(ValueError, match="holdback"):
        validate_record(hb, voc)                                                                                   # a hold-back value needs its figure
    hb["parameters"] = dict(rec["parameters"], holdback=7)
    assert "last 7 rounds are held back" in render(hb, voc)
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
    perfect = {q["id"]: next(o for o in q["options"] if o["value"] == correct_value(rec, q["answer_from"]))["label"] for q in qs}
    assert score_comprehension(perfect, rec, qs) == len(qs)
    assert correct_value(rec, "parameters.audit_tolerance") == "0.12" and correct_value(rec, "parameters.ban_length") == "10"
    assert correct_value(describe_record(PostedPrices(0.25, 0.40, 0.55)), "parameters.ban_length") == "none"
    assert len([q for q in qs if q["answer_from"].startswith("parameters.")]) == 2
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
# Values carry the operational rule in words (selection order, payment formula), so the actor reads what the mechanism does.
# `numeric` lists the values that need a figure in the record's `parameters` map under the field's name.
numeric:
  audit_tolerance:
    - number
  ban_length:
    - number
  holdback:
    - "a number of rounds of receipts, released after the next passed audit"
    - "a number of rounds of receipts, released on a fixed schedule"
fields:
  allocation_order:
    - "jobs in descending value; each job goes to the highest posted tier that has an offer with capacity whose claim times the job value reaches the tier price, at random among those offers; tiers by claim: below 0.5, 0.5 to below 0.8, 0.8 and above"
    - "jobs in descending value; each job goes to the offer with capacity and the highest score, score = job value times claim minus bid, offers with a negative score are not eligible, at random among equal scores"
    - ascending bid
    - round robin
    - not expressible
  eligibility:
    - active offers with capacity
    - active offers with capacity and no failed audit in the last rounds
    - active offers with capacity above a reputation threshold
    - not expressible
  payment:
    - the posted price of the tier the job was allocated in
    - "second score: job value times claim minus the highest score among the other eligible offers for that job, zero when there is none"
    - the bid
    - job value times claim
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
    - "a number of rounds of receipts, released after the next passed audit"
    - "a number of rounds of receipts, released on a fixed schedule"
    - not expressible
```

(Every value that contains a comma is quoted so YAML keeps it as one string; a test checks that `numeric.holdback` has exactly two entries.)

```yaml
# experiments/comprehension_fixture.yaml
# Locked factual questions about a rule, answered by the actor from the rendered description alone (spec 5.4).
# `answer_from` names the describe() field whose value is the correct answer; options map vocabulary values to labels.
questions:
  - id: q_allocation
    question: "In what order are jobs allocated?"
    answer_from: allocation_order
    options:
      - {label: "A", value: "jobs in descending value; each job goes to the highest posted tier that has an offer with capacity whose claim times the job value reaches the tier price, at random among those offers; tiers by claim: below 0.5, 0.5 to below 0.8, 0.8 and above"}
      - {label: "B", value: "jobs in descending value; each job goes to the offer with capacity and the highest score, score = job value times claim minus bid, offers with a negative score are not eligible, at random among equal scores"}
      - {label: "C", value: "ascending bid"}
      - {label: "D", value: "round robin"}
      - {label: "E", value: "not expressible"}
  - id: q_payment
    question: "How is the payment for a served job set?"
    answer_from: payment
    options:
      - {label: "A", value: "the posted price of the tier the job was allocated in"}
      - {label: "B", value: "second score: job value times claim minus the highest score among the other eligible offers for that job, zero when there is none"}
      - {label: "C", value: "the bid"}
      - {label: "D", value: "job value times claim"}
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
      - {label: "B", value: "a number of rounds of receipts, released after the next passed audit"}
      - {label: "C", value: "a number of rounds of receipts, released on a fixed schedule"}
      - {label: "D", value: "not expressible"}
  - id: q_eligibility
    question: "Which offers are eligible for allocation?"
    answer_from: eligibility
    options:
      - {label: "A", value: "active offers with capacity"}
      - {label: "B", value: "active offers with capacity and no failed audit in the last rounds"}
      - {label: "C", value: "active offers with capacity above a reputation threshold"}
      - {label: "D", value: "not expressible"}
  # Numeric questions: `answer_from: parameters.<field>`; the correct value is the figure formatted with `{:g}`, or the field's
  # non-numeric vocabulary value ("none", "until the next passed audit", "not expressible") when the field is not numeric.
  - id: q_tolerance
    question: "By how much may a delivery fall below its claim before the audit fails?"
    answer_from: parameters.audit_tolerance
    options:
      - {label: "A", value: "none"}
      - {label: "B", value: "0.05"}
      - {label: "C", value: "0.12"}
      - {label: "D", value: "0.2"}
      - {label: "E", value: "not expressible"}
  - id: q_ban_rounds
    question: "For how many rounds is an identity banned after a failed audit?"
    answer_from: parameters.ban_length
    options:
      - {label: "A", value: "none"}
      - {label: "B", value: "3"}
      - {label: "C", value: "10"}
      - {label: "D", value: "20"}
      - {label: "E", value: "until the next passed audit"}
      - {label: "F", value: "not expressible"}
```

The numeric options list the tuned figures of the baselines after tuning (replace 0.05, 0.12, 0.2 and 3, 10, 20 with the tuned `tol` and `L` values plus two distractors each before the lock; the fixture is hashed into `locked.yaml` by `scripts/lock.py`).

```python
# sim/describe.py
"""describe() records: vocabulary validation, the frozen prose renderer, and the comprehension fixture (spec 5.4)."""
from __future__ import annotations

import math
from pathlib import Path

import yaml

DESCRIBE_FIELDS = ("allocation_order", "eligibility", "payment", "audit_selection", "audit_tolerance", "failed_audit", "ban_length", "holdback")
NOT_EXPRESSIBLE = "not expressible"
ROOT = Path(__file__).resolve().parents[1]
VOCABULARY_PATH = ROOT / "experiments" / "vocabulary.yaml"
FIXTURE_PATH = ROOT / "experiments" / "comprehension_fixture.yaml"

# Sentence frames, fixed at the lock. {value} is the vocabulary value (which carries the selection rule or the
# payment formula in words); numeric values use NUMBER_FRAMES with {number}, the figure from `parameters`.
FRAMES = {
    "allocation_order": "Jobs are allocated in this order: {value}.",
    "eligibility": "Offers eligible for allocation: {value}.",
    "payment": "A served job pays its provider {value}.",
    "audit_selection": "Audits are selected as follows: {value}.",
    "audit_tolerance": "Audit tolerance: {value}.",
    "failed_audit": "After a failed audit, the consequence for the payment is: {value}.",
    "ban_length": "After a failed audit, the ban lasts: {value}.",
    "holdback": "Hold-back of receipts: {value}.",
}
NUMBER_FRAMES = {
    "audit_tolerance": {"number": "A delivery fails its audit when it falls below the claim by more than {number}."},
    "ban_length": {"number": "After a failed audit, the identity is banned for {number} rounds."},
    "holdback": {"a number of rounds of receipts, released after the next passed audit": "The receipts of the last {number} rounds are held back and released after the next passed audit.",
                 "a number of rounds of receipts, released on a fixed schedule": "The receipts of the last {number} rounds are held back and released on a fixed schedule."},
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
        if value in vocabulary.get("numeric", {}).get(name, []):
            figure = record.get("parameters", {}).get(name)
            if not isinstance(figure, (int, float)) or isinstance(figure, bool) or not math.isfinite(float(figure)):
                raise ValueError(f"describe() field {name!r} is numeric ({value!r}) but parameters has no finite number for {name!r}")


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
        elif value in vocabulary.get("numeric", {}).get(name, []):
            lines.append(NUMBER_FRAMES[name][value].format(number=f"{params[name]:g}"))
        else:
            lines.append(FRAMES[name].format(value=value))
    return "\n".join(lines) + "\n"


def comprehension_questions(path: str | Path | None = None) -> list[dict]:
    with open(path or FIXTURE_PATH) as f:
        return yaml.safe_load(f)["questions"]


def correct_value(record: dict, answer_from: str) -> str:
    """The option value that is correct for this record: a field's vocabulary value, or for `parameters.<field>` the
    figure formatted with {:g} when the field is numeric, else the field's non-numeric value."""
    if answer_from.startswith("parameters."):
        field = answer_from.split(".", 1)[1]; figure = record.get("parameters", {}).get(field)
        return f"{figure:g}" if isinstance(figure, (int, float)) and not isinstance(figure, bool) else str(record[field])
    return str(record[answer_from])


def score_comprehension(answers: dict, record: dict, questions: list[dict]) -> int:
    correct = 0
    for q in questions:
        truth = correct_value(record, q["answer_from"])
        label = next((o["label"] for o in q["options"] if o["value"] == truth), None)
        if label is not None and answers.get(q["id"]) == label:
            correct += 1
    return correct
```

Change the baselines' `describe()` methods to return vocabulary values with a `parameters` map:

```python
# sim/mechanisms/posted.py (B1)
    def describe(self) -> dict:
        return {"allocation_order": "jobs in descending value; each job goes to the highest posted tier that has an offer with capacity whose claim times the job value reaches the tier price, at random among those offers; tiers by claim: below 0.5, 0.5 to below 0.8, 0.8 and above",
                "eligibility": "active offers with capacity", "payment": "the posted price of the tier the job was allocated in",
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
        return {"allocation_order": "jobs in descending value; each job goes to the offer with capacity and the highest score, score = job value times claim minus bid, offers with a negative score are not eligible, at random among equal scores",
                "eligibility": "active offers with capacity", "payment": "second score: job value times claim minus the highest score among the other eligible offers for that job, zero when there is none",
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

### Task 4: Model actor (LLM and Jev backends behind a prompt-hash cache), the budgeted backend, the H1 procedure with reference selection, and the closed-loop clipped re-run

**Files:**
- Create: `sim/llm_actor.py`, `sim/policies/llm.py`
- Test: `tests/test_llm_actor.py`

**Interfaces:**
- Consumes: `Twin` (plan 1), `run_episode`, `Abstain` (`sim/cell.py`), `HonestMax`, `cell_config`, `render`/`describe_record`/`correct_value` (Task 3), `locked["h1"]`.
- Produces (`sim/llm_actor.py`):
  - `ACTION_SCHEMA`; `parse_action(data, params) -> Action | None` (None when malformed: missing keys, non-finite, effort outside `[0, q_max]`, claim outside `[0, 1]`, bid negative).
  - `ACTOR_INSTRUCTIONS` (the development system prompt; the sealed H1 prompt replaces it through `make_backend(..., instructions=...)`).
  - `Backend` protocol: attributes `name`, `model`, `instructions`; `complete(kind, payload) -> {"data": parsed | None, "raw": dict, "usage": {"input_tokens", "output_tokens"}}`, `kind in {"action", "comprehension"}`. Every wrapper forwards all three attributes.
  - `build_payload(backend, kind, rendered_rule, state=None, questions=None) -> dict`: `{"instructions": backend.instructions, "rule": rendered_rule, "state"|"questions": ...}`; the prompt is part of every cache key through this payload (attribute access, never `getattr` with a default).
  - `canonical_request(backend_name, model, kind, payload) -> str`, `request_hash(...) -> str` (SHA-256).
  - `PromptCache(directory)`: `get(key) -> response | None`, `put(key, request: str, response)` (one JSON file `{"request": ..., "response": ...}` per key), `entry(key) -> dict | None`, counters `hits`, `misses`.
  - `AnthropicBackend(model, instructions)`, `JevBackend(model, instructions)` (menu `EFFORT_LEVELS`, `CLAIM_OFFSETS`, `MARKUPS`, serve/abstain; usage fields `or 0`), `FakeBackend(fn, model="fake-1", instructions=ACTOR_INSTRUCTIONS)`, `make_backend(name, locked, instructions=None)`.
  - `CapExceeded(Exception)` with `.reason`; `PilotTargetReached(Exception)`; `BudgetedBackend(inner, max_calls=None, max_cost_usd=None, prices=None, stop_at=None, ledger=None, max_request_tokens=(8000, 512))`: forwards `name`, `model`, `instructions`; `ledger` is a JSON path holding the cumulative `calls`, `usage`, and `cost_usd` of every earlier run with this backend (loaded at construction, written after every call), so a restarted run continues the same allowance; before every call raises `CapExceeded("calls cap N ...")` when `calls + 1 > max_calls`, `CapExceeded("cost cap X USD ...")` when `cost_usd + reserve > max_cost_usd` where `reserve` is the price of one request of `max_request_tokens` (input, output) at `prices[model]` (so the cap is never crossed), and `PilotTargetReached` when `calls >= stop_at`; after every call records `calls`, `usage`, `latencies` (seconds, this run only), `cost_usd`; `calls_this_run` counts this run only.
  - `build_state(view, feedback, T) -> dict`.
  - `ProcedureResult(profits (5), fallback_rounds, total_rounds, invalid, calls, cache_hits, usage, episode5)`; `run_procedure(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds (4), eval_seed, locked, clip_episode5=False, twin=False)`.
  - `H1Reference(name, scores: dict[str, float], twin_results: list[ProcedureResult])`; `select_h1_reference(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, selection_seeds, locked) -> H1Reference` (ruling D10: twin procedures whose episode 5 runs on each selection seed; honest-max and abstention without calls; the chosen name is the maximizer of the mean normalized profit `profit / (S* / N)` in the order `REFERENCE_ORDER = ("abstain", "honest_max", "twin")`, ties to the earlier).
  - `reference_on_seed(name, cfg, rule_factory, focal, seed, twin_result) -> tuple[float, float]` = `(profit, eff)` of the chosen reference on an evaluation seed (`twin` reads `twin_result.episode5`; `honest_max` and `abstain` run one episode without the actor).
  - `H1CellResult(attack, twin, clipped, reference: H1Reference, ref_profit: list, ref_eff: list, eval_seeds, invalid_flags: list[bool], invalid_count, inconclusive, calls, new_calls_clipped, usage)`; `run_h1_cell(cfg, rule_factory, focal, backend, cache, rendered_rule, train_seeds, eval_seeds, locked, selection_seeds) -> H1CellResult` (`invalid_flags[k]` is True when the attack, twin, or clipped procedure of repetition k is invalid; `invalid_count = sum(invalid_flags)`; `inconclusive = invalid_count > locked["h1"]["invalid_limit"]`).
  - `H1_ROW_FIELDS = ["rep", "eval_seed", "sstar", "reference", "profit_attack", "profit_twin", "profit_clip", "profit_ref", "gain", "gain_vs_twin", "eff_attack", "eff_twin", "eff_clip", "eff_ref", "audit_cost_attack", "fallback_rounds", "invalid"]`; `h1_rows(result, meta) -> list[dict]` (`gain = (profit_attack - profit_ref) / (S* / N)`, `gain_vs_twin = (profit_attack - profit_twin) / (S* / N)`).
  - `ask_comprehension(backend, cache, rendered_rule, questions) -> dict[str, str]`, `comprehension_check(backend, cache, rules, questions) -> dict[str, int]`.
  - `estimate_cost_usd(usage, model, locked) -> float` from `locked["h1"]["prices"]`.
- Produces (`sim/policies/llm.py`): `LLMProvider(backend, cache, rendered_rule, params, feedback, T, counters)`, `ActorCounters(calls, cache_hits, fallbacks, rounds, usage)`; `act(view)` never exits; a `CapExceeded` or `PilotTargetReached` raised by the backend propagates out of `run_episode` (the caller decides what to keep).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_llm_actor.py
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
    assert b.calls == 4                                             # the fifth call never happened
    b2 = BudgetedBackend(FakeBackend(honest_fn), stop_at=3)
    prov = LLMProvider(b2, PromptCache(tmp_path / "d"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(PilotTargetReached):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b2.calls == 3 and len(b2.latencies) == 3 and b2.usage["input_tokens"] > 0
    prices = {"fake-1": {"input": 1e6, "output": 0.0}}                 # one USD per input token: every request costs more than a dollar
    b3 = BudgetedBackend(FakeBackend(honest_fn), max_cost_usd=1.0, prices=prices, max_request_tokens=(1, 0))
    prov = LLMProvider(b3, PromptCache(tmp_path / "e"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded, match="cost cap"):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    assert b3.calls == 0 and b3.cost_usd == 0.0                       # the reserve stops the first request that would cross the cap
    ledger = tmp_path / "ledger.json"
    b4 = BudgetedBackend(FakeBackend(honest_fn), max_calls=5, ledger=ledger)
    prov = LLMProvider(b4, PromptCache(tmp_path / "f"), rendered, cfg.providers[3], feedback=[], T=cfg.T, counters=ActorCounters()); pols[3] = prov
    with pytest.raises(CapExceeded):
        run_episode(cfg, PostedPrices(0.2, 0.35, 0.5), pols, 1)
    b5 = BudgetedBackend(FakeBackend(honest_fn), max_calls=5, ledger=ledger)                # a restart continues the same allowance
    assert b5.calls == 5 and b5.calls_this_run == 0
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

from ..llm_actor import PromptCache, build_payload, build_state, canonical_request, parse_action, request_hash
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
    honest-max for that round and is counted. A cap raised by the backend propagates."""
    name = "llm_provider"

    def __init__(self, backend, cache: PromptCache, rendered_rule: str, params, feedback: list, T: int, counters: ActorCounters) -> None:
        self.backend, self.cache, self.rendered_rule, self.params, self.feedback, self.T, self.counters = backend, cache, rendered_rule, params, list(feedback), int(T), counters

    def act(self, view: ProviderView) -> Action:
        self.counters.rounds += 1
        payload = build_payload(self.backend, "action", self.rendered_rule, state=build_state(view, self.feedback, self.T))
        key = request_hash(self.backend.name, self.backend.model, "action", payload)
        resp = self.cache.get(key)
        if resp is None:
            resp = self.backend.complete("action", payload)
            self.cache.put(key, canonical_request(self.backend.name, self.backend.model, "action", payload), resp)
            self.counters.calls += 1
            for k in ("input_tokens", "output_tokens"):
                self.counters.usage[k] += int(resp.get("usage", {}).get(k) or 0)
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
        return {"data": data, "raw": response.to_dict(),
                "usage": {"input_tokens": int(response.usage.input_tokens or 0), "output_tokens": int(response.usage.output_tokens or 0)}}


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
    def __init__(self, reason: str) -> None:
        super().__init__(reason); self.reason = reason


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
        self.calls = 0; self.usage = {"input_tokens": 0, "output_tokens": 0}; self.cost_usd = 0.0
        if self.ledger is not None and self.ledger.exists():
            led = json.loads(self.ledger.read_text()); self.calls = int(led["calls"]); self.usage = dict(led["usage"]); self.cost_usd = float(led["cost_usd"])
        self.calls_this_run = 0; self.latencies: list = []

    def _price(self, input_tokens: int, output_tokens: int) -> float:
        p = self.prices.get(self.model)
        return 0.0 if p is None else input_tokens / 1e6 * float(p["input"]) + output_tokens / 1e6 * float(p["output"])

    def complete(self, kind: str, payload: dict) -> dict:
        if self.stop_at is not None and self.calls_this_run >= self.stop_at:
            raise PilotTargetReached()
        if self.max_calls is not None and self.calls + 1 > self.max_calls:
            raise CapExceeded(f"calls cap {self.max_calls} reached after {self.calls} calls (cumulative)")
        reserve = self._price(*self.max_request_tokens)
        if self.max_cost_usd is not None and self.cost_usd + reserve > float(self.max_cost_usd):
            raise CapExceeded(f"cost cap {self.max_cost_usd} USD would be crossed ({self.cost_usd:.4f} USD spent after {self.calls} calls, next request up to {reserve:.4f} USD)")
        t0 = time.perf_counter(); out = self.inner.complete(kind, payload); self.latencies.append(time.perf_counter() - t0)
        self.calls += 1; self.calls_this_run += 1
        for k in self.usage:
            self.usage[k] += int(out.get("usage", {}).get(k) or 0)
        self.cost_usd = self._price(self.usage["input_tokens"], self.usage["output_tokens"])
        if self.ledger is not None:
            self.ledger.parent.mkdir(parents=True, exist_ok=True)
            self.ledger.write_text(json.dumps({"calls": self.calls, "usage": self.usage, "cost_usd": self.cost_usd, "model": self.model}))
        return out


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_llm_actor.py -v`
Expected: PASS (10 tests). No network is touched. If `test_reference_selection_follows_the_registered_order` finds that the clipped cheat earns more than honest-max under the small B1 fixture, replace the equality on `ref.name` with the registered-order expression that precedes it and record the observed winner in the ledger; the second assertion (ties go to the earlier name) must hold as written.

Call accounting (ruling D10, for the spec note): per (rule, beta) cell at T = 100, the uncached calls are at most 5 x 500 (selection twins) + 10 x (500 + 500 + 100) (attack, twin, clipped) = 13,500, but the 10 repetitions share the four dev-train episodes, so with a deterministic cached actor the real count is about 4 x 100 + 10 x 100 (attack) + 4 x 100 + 10 x 100 (twin) + up to 10 x 100 (clipped) + up to 5 x 100 (selection) about 4,300 per cell and about 39,000 for 3 rules x 3 betas, well under the 192,000 cap.

- [ ] **Step 5: Commit**

```bash
git add experiments/locked.yaml sim/llm_actor.py sim/policies/llm.py tests/test_llm_actor.py
git commit -m "feat: model actor with Anthropic, Jev, and fake backends behind a prompt-hash cache that stores the request; budgeted backend; H1 procedure with reference selection, per-repetition invalidity, clipped re-run, comprehension check"
```

---

### Task 5: Coverage study (cell selection, thresholds with their simulation check, joint fixture test, power, chunked pools and replications, admission, report, manifest entries)

**Files:**
- Create: `sim/coverage.py`, `scripts/coverage_study.py`
- Modify: `sim/manifest.py` (`coverage` entries, base and conditional, outside the gate and the weights), `scripts/manifest.py` (print them)
- Test: `tests/test_coverage.py`, `tests/test_manifest.py` (one test)

**Interfaces:**
- Consumes: `bound`, `t_bound`, `t_interval`, `Bound` (Task 2); `run_focal`, `Cell`, `SeedCache` (`sim/cell.py`); `make_rule`, `available_families` (Task 1b); `job_for`, `check_record`, `load_params`, `train_val`, `read_dir`, `settings_for` (`scripts/sweep.py`); `candidate_from_record` (`sim/records.py`); `participant_diagnostics` (`sim/reference.py`); `locked["seeds"]["coverage"]`, `locked["intervals"]` (Task 1).
- Produces (`sim/coverage.py`):
  - `STATISTICS`, `ENDPOINTS` (eight, spec order), `LEVELS`, `PROCEDURES_AT_N = {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)}`, `BASE_N = (10, 20)`, `CONDITIONAL_N = (40,)`, `endpoint_key(stat, side, level, n) -> str`.
  - `skewness(x)`, `sarle_bimodality(x)` (nan on fewer than 3 or 4 values or zero variance).
  - `select_cells(stats_by_cell, k=3) -> list[str]`: ruling D12 exactly.
  - `seed_blocks(locked, cell_index, pool_factor=1, rep_factor=1, n_list=None) -> tuple[np.ndarray, dict[int, np.ndarray]]`: the pool, then per `n` in `n_list` (default `n_grid`) an `(R_n * rep_factor, n)` array of fresh consecutive seeds; the layout is fixed by `n_grid` order and both factors so a later conditional run at n = 40 uses the same seeds it would have used in one run; `ValueError` when the block is exceeded.
  - `CoverageCellSpec(name, cfg: dict, focal, rule, family, params_by_rule: dict[str, dict], attack_knobs_by_rule: dict[str, dict], ref_candidate: dict | None, pair=("B2", "B3"))` (a plain dataclass of JSON values: it is what a worker process receives); `trajectory_keys(spec) -> list[tuple[str, str]]` (unique `(rule, kind)` keys: `(rule, "attack")`, `(rule, "clip")`, `(rule, "ref")` unless `ref_candidate` is `None` (abstain), plus `(p, "attack")` and `(p, "clip")` for each pair rule `p != rule`); `runs_per_seed(spec) = len(trajectory_keys(spec))`.
  - `observe_chunk(spec, seeds, families) -> dict[str, np.ndarray]` (one `SeedCache`, every run reduced to scalars: `profit[focal]`, `W`, `audit_cost`, `S*`; episode results are dropped before return); `observe(spec, seeds, chunk=500) -> dict[str, np.ndarray]` (loops `observe_chunk` over disjoint chunks; peak memory is one chunk).
  - `reference_interval`, `covered`, `measure` as in version 1.
  - `analytic_conservative_coverage(n, critical, M, ref_level=0.95)`: the known-variance expression (noncentral t); the docstring says it is exact for known sigma and a normal-quantile reference interval, and that the t-interval and pool-variance terms are O(1/M) (below 1e-6 at M = 35,000).
  - `simulated_conservative_coverage(n, level, M, pools, reps, rng)`; `threshold_check(locked, M, pools, reps, rng) -> dict[key, {"analytic", "simulated", "gap", "se"}]` (the registered cross-check: 200 pools of size M, 20,000 replications each, for every n and level; `pass_` when `|gap| <= 3 se + 1e-4`).
  - `thresholds(locked, M)`; `clopper_pearson_lower`; `joint_fixture(locked, n, M, R, thr, trials, rng, cells=6)` (an independent pool and sample per statistic and cell, so each trial scores 6 x 8 endpoints; sides and levels of one statistic share its samples); `control_power(...)` with `scipy.special.roots_hermite` and an assertion that nodes, weights, probabilities, and the total are finite; `power_check(locked, M, R_by_n, thr)`.
  - `fixture_and_power(locked, smoke, rng, n_list) -> dict`: per `n` in `n_list`, attempts `(pool_factor, rep_factor)` in `((1, 1), (2, 1), (2, 2))` each with its own thresholds at `M = base_M * pool_factor` and `R = R_n * rep_factor`, stopping at the first attempt whose fixture and power both pass; returns `per_n`, `remedies` (the passing factors per n, or the last attempt's factors with `admissible = False`), `admissible_n`, `base_M`, `base_R`, and `threshold_check` at the base M.
  - `admission(measured, thr_by_n: dict[int, dict], locked, admissible_n: dict[str, bool] | None = None) -> dict` (`procedure_admitted`, `method_at_n`, `admitted_sides`, `consequences`; a procedure at an `n` whose fixture or power failed is not admitted; an `n` with no measurements is not admitted).
  - `write_report`, `load_report`.
- Produces (`sim/manifest.py`): `manifest_weights` collects its rule names and its rows from cells with `section != "coverage"` (the estimate rows carry rule `"?"`); `coverage_cells(locked, selection: list | None) -> list[CellSpec]`: per selected cell (or six estimated cells at 5 runs per seed), a `coverage_base` entry (`runs_per_seed * (pool + sum over BASE_N of R_n * n)`) and three `coverage_conditional` entries (`n40`: `runs_per_seed * R_40 * 40`; `double_M`: `runs_per_seed * pool`; `double_R`: `runs_per_seed * sum over all n of R_n * n`), `section = "coverage"`, `post_lock = False`, `exact = True`; `totals` reports `coverage_base` and `coverage_conditional` and excludes `section == "coverage"` from `pre_lock`, `pre_lock_exact`, and `pre_lock_upper_bound`; `manifest_weights` skips `section == "coverage"`.
- Produces (`scripts/coverage_study.py`): CLI `--sweep-out DIR --calibration PATH [--tuned-dir DIR] --out DIR [--smoke] [--workers K] [--select-only] [--cell INDEX] [--merge] [--force-n40] [--register]`; validates every reference record with the sweep's own `check_record` against jobs rebuilt from the calibration and tuned parameters, and in registered mode also requires the full calibration namespace, the full dev-train vector in every record (`len(attack_per_seed_normalized) == n_train`), the bank document the records cite (`load_bank_doc` + `check_bank_record`), and no smoke record; writes `<out>/coverage_report.json` and `<out>/coverage_cells.json`; `--register` copies the selection to `experiments/coverage_cells.json` for the manifest. The pool of a cell is observed once per `pool_factor` and saved to `<out>/pool_<cell>_<factor>.npz`, and every n (and the conditional n = 40 later) reads it back. **Per-cell mode for separate machines:** `--cell INDEX` runs the selection step (deterministic, the same on every machine) and then only cell `INDEX`'s pools and replications, writing `<out>/cell_<INDEX>.json`; `--merge` reads the six `cell_*.json` files, runs the fixture and power step, admits, and writes the report, so the six cells can run on six CPU pods and be merged on one. Without `--cell`, one process runs every cell (with `--workers` in parallel) and merges at the end. n = 10 and n = 20 run first; n = 40 runs (per cell, in the same mode) only when `method_at_n["20"]` is `None` after the base admission and n = 40 has not run (or `--force-n40`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_coverage.py
import numpy as np
import pytest
from scipy import stats

from sim.coverage import (ENDPOINTS, PROCEDURES_AT_N, BASE_N, endpoint_key, skewness, sarle_bimodality, select_cells, seed_blocks, CoverageCellSpec,
                          trajectory_keys, runs_per_seed, observe, observe_chunk, reference_interval, covered, measure, analytic_conservative_coverage,
                          simulated_conservative_coverage, threshold_check, thresholds, clopper_pearson_lower, joint_fixture, control_power, power_check,
                          fixture_and_power, admission, write_report, load_report)
from sim.config import MarketConfig
from sim.intervals import Bound
from sim.locked import load_locked
from sim.records import cfg_to_dict
from sim.registry import available_families


def test_endpoints_and_moments():
    assert len(ENDPOINTS) == 8 and ENDPOINTS[0] == ("gain", "upper", 0.95) and ENDPOINTS[4] == ("loss_diff", "lower", 0.9875)
    assert PROCEDURES_AT_N == {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)} and BASE_N == (10, 20)
    assert endpoint_key("gain", "upper", 0.95, 20) == "gain|upper|0.95|20"
    x = np.array([1.0, 2.0, 3.0, 10.0])
    assert skewness(x) == pytest.approx(stats.skew(x, bias=False))
    g, k, n = stats.skew(x, bias=False), stats.kurtosis(x, bias=False), 4
    assert sarle_bimodality(x) == pytest.approx((g * g + 1) / (k + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))))
    assert np.isnan(skewness(np.array([1.0, 1.0, 1.0]))) and np.isnan(sarle_bimodality(np.array([1.0, 2.0, 3.0])))


def test_cell_selection_handles_degenerate_rankings():
    nan = float("nan")
    st = {"a": {"skew_gain": 3.0, "sarle_bans": 0.9}, "b": {"skew_gain": 2.0, "sarle_bans": 0.1}, "c": {"skew_gain": 1.0, "sarle_bans": 0.5},
          "d": {"skew_gain": 0.5, "sarle_bans": 0.8}, "e": {"skew_gain": 0.1, "sarle_bans": nan}, "f": {"skew_gain": nan, "sarle_bans": 0.7},
          "g": {"skew_gain": -1.0, "sarle_bans": 0.0}}
    # skew ranking a b c d e g; sarle ranking a d f c b g; union of the top threes = a b c d f (5); skew contributed 3 distinct,
    # sarle 2 new (a overlapped) -> fill from sarle: c (used), b (used), g -> a b c d f g
    assert select_cells(st, k=3) == ["a", "b", "c", "d", "f", "g"]
    st2 = {"a": {"skew_gain": 1.0, "sarle_bans": 1.0}, "b": {"skew_gain": 0.0, "sarle_bans": nan}, "c": {"skew_gain": nan, "sarle_bans": nan}}
    assert select_cells(st2, k=3) == ["a", "b"]                   # both rankings exhausted: fewer than 6
    st3 = {n: {"skew_gain": v, "sarle_bans": nan} for n, v in zip("abcdefg", range(7, 0, -1))}
    assert select_cells(st3, k=3) == ["a", "b", "c", "d", "e", "f"]   # the Sarle ranking is empty: skewness fills


def test_seed_blocks_are_fresh_disjoint_and_bounded():
    lk = load_locked(); cov = lk["seeds"]["coverage"]
    pool, reps = seed_blocks(lk, 0)
    assert pool[0] == cov["start"] and len(pool) == cov["pool"]
    assert reps[10].shape == (2000, 10) and reps[20].shape == (2000, 20) and reps[40].shape == (4000, 40)
    allseeds = np.concatenate([pool] + [r.ravel() for r in reps.values()])
    assert len(np.unique(allseeds)) == len(allseeds) and allseeds.max() < cov["start"] + cov["block"]
    pool1, _ = seed_blocks(lk, 1); assert pool1[0] == cov["start"] + cov["block"]
    _, base = seed_blocks(lk, 0, n_list=BASE_N)
    assert set(base) == {10, 20} and np.array_equal(base[20], reps[20])       # a base-only run uses the same seeds as the full layout
    pool2, reps2 = seed_blocks(lk, 2, pool_factor=2, rep_factor=2)
    assert len(pool2) == 2 * cov["pool"] and reps2[40].shape == (8000, 40)
    with pytest.raises(ValueError):
        seed_blocks(dict(lk, seeds=dict(lk["seeds"], coverage=dict(cov, block=1000))), 0)


def small_spec(rule="B1", ref=True):
    c = MarketConfig.default()
    cfg = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=c.alpha, budget=0.3)
    params = {"B1": {"P1": 0.2, "P2": 0.35, "P3": 0.5}, "B2": {"P1": 0.2, "P2": 0.35, "P3": 0.5, "tol": 0.12, "L": 3}, "B3": {"tol": 0.12, "L": 3}}
    cheat = {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0.0}
    return CoverageCellSpec(name=f"x_{rule}", cfg=cfg_to_dict(cfg), focal=3, rule=rule, family="D1", params_by_rule=params,
                            attack_knobs_by_rule={r: dict(cheat) for r in params}, ref_candidate={"name": "honest_max", "knobs": None} if ref else None)


def test_observe_is_chunked_scalar_and_pair_invariant():
    fams = available_families()
    s1 = small_spec("B1"); s2 = small_spec("B2", ref=False)
    assert runs_per_seed(s1) == 7 and runs_per_seed(s2) == 4 and ("B2", "clip") in trajectory_keys(s2) and ("B2", "ref") not in trajectory_keys(s2)
    seeds = np.arange(6)
    obs = observe(s1, seeds, chunk=2); whole = observe_chunk(s1, seeds, fams)
    assert set(obs) == {"gain", "eff", "loss_diff"} and all(v.shape == (6,) and np.all(np.isfinite(v)) for v in obs.values())
    for k in obs:
        assert np.array_equal(obs[k], whole[k])                                # chunking does not change the observations
    obs2 = observe(s2, seeds, chunk=4)
    assert np.array_equal(obs["loss_diff"], obs2["loss_diff"])                # the pair statistic does not depend on the cell's rule


def test_reference_interval_and_conservative_scoring():
    rng = np.random.default_rng(1); pool = rng.normal(0.0, 1.0, size=5000)
    lo, hi, se = reference_interval(pool, 0.95)
    assert lo < pool.mean() < hi and se == pytest.approx(pool.std(ddof=1) / np.sqrt(5000)) and hi - lo == pytest.approx(2 * stats.t.ppf(0.975, 4999) * se)
    assert covered(Bound(hi + 0.01, "upper", 0.95, "t", False, 10), lo, hi) and not covered(Bound(hi - 0.01, "upper", 0.95, "t", False, 10), lo, hi)
    assert covered(Bound(lo - 0.01, "lower", 0.95, "t", False, 10), lo, hi) and not covered(Bound(lo + 0.01, "lower", 0.95, "t", False, 10), lo, hi)


def test_measure_runs_every_endpoint_and_procedure():
    rng = np.random.default_rng(2)
    samples = {s: rng.normal(size=(50, 20)) for s in ("gain", "eff", "loss_diff")}
    out = measure(samples, {s: (-0.05, 0.05) for s in samples}, 20, ("percentile", "studentized"), {"bootstrap_resamples": 200, "bootstrap_seed": 3})
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
    chk = threshold_check(lk, 2000, pools=20, reps=2000, rng=np.random.default_rng(5))
    assert set(chk) == set(thr) and all(abs(v["gap"]) < 0.02 and v["se"] > 0 for v in chk.values())


def test_clopper_pearson_and_joint_fixture_small():
    assert clopper_pearson_lower(190, 200, 1 - 0.05 / 3) == pytest.approx(0.9063, abs=5e-4)
    assert clopper_pearson_lower(189, 200, 1 - 0.05 / 3) < 0.9 and clopper_pearson_lower(0, 10, 0.95) == 0.0
    lk = load_locked(); thr = thresholds(lk, 500)
    res = joint_fixture(lk, 20, 500, 60, thr, trials=8, rng=np.random.default_rng(5), cells=2)
    assert res["trials"] == 8 and 0 <= res["admitted"] <= 8 and 0.0 <= res["lower_limit"] <= 1.0 and isinstance(res["pass_"], bool) and res["endpoints_per_cell"] == 8


def test_control_power_is_high_for_a_3_point_deficit_and_quadrature_converges():
    lk = load_locked(); thr = thresholds(lk, 35000)
    p200 = control_power(20, 0.95, 3.0, 35000, 2000, thr["20|0.95"]["threshold"], nodes=200)
    p400 = control_power(20, 0.95, 3.0, 35000, 2000, thr["20|0.95"]["threshold"], nodes=400)
    assert np.isfinite(p200) and np.isfinite(p400) and p200 > 0.8 and abs(p200 - p400) <= 0.001
    pc = power_check(lk, 35000, {10: 2000, 20: 2000, 40: 4000}, thr)
    assert set(pc) == set(thr) and all(v["converged"] and np.isfinite(v["power_400"]) for v in pc.values())
    assert min(v["power_200"] for v in pc.values()) > 0.9                     # spec 8 reports a minimum of about 0.938


def test_fixture_and_power_smoke_shape():
    lk = load_locked()
    fp = fixture_and_power(lk, smoke=True, rng=np.random.default_rng(6), n_list=(10, 20))
    assert set(fp["per_n"]) == {"10", "20"} and set(fp["remedies"]) == {"10", "20"} and str(fp["base_M"]) in fp["threshold_check"]
    assert all(a["fixture"]["M"] == fp["base_M"] * a["pool_factor"] and a["fixture"]["R"] == int(fp["base_R"][n]) * a["rep_factor"]
               and str(a["M"]) in fp["threshold_check"] for n, atts in fp["per_n"].items() for a in atts)   # one coherent (M, R) per attempt, each M cross-checked
    assert np.isfinite(control_power(20, 0.9875, 1.5, 200, 20, 0.9, nodes=400))                     # the smoke M: NaN tails are filled, no FloatingPointError
    chk = threshold_check(lk, 2000, pools=6, reps=500, rng=np.random.default_rng(7))
    assert all(v["se"] > 0 for v in chk.values())


def test_admission_follows_the_remedy_order_and_sets_consequences():
    lk = load_locked(); thr = {n: {f"{n}|{lv}": {"threshold": 0.9} for lv in (0.95, 0.9875)} for n in (10, 20, 40)}
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
    b = admission({"c1": cellcov({("percentile", 20)}), "c2": cellcov(set())}, thr, lk)
    assert b["method_at_n"]["20"] == "studentized" and b["consequences"]["parametrized"] == "studentized_n20"
    c = admission({"c1": cellcov({("percentile", 20), ("studentized", 20)})}, thr, lk)
    assert c["method_at_n"]["20"] is None and c["consequences"] == {"h1": "confirmatory", "parametrized": "studentized_n40", "final_eval_n": 40}
    d = admission({"c1": cellcov({("t", 10), ("percentile", 20), ("studentized", 20), ("studentized", 40)})}, thr, lk)
    assert d["consequences"] == {"h1": "exploratory", "parametrized": "inconclusive", "final_eval_n": None} and d["admitted_sides"]["gain|upper|0.95|20"] is None
    e = admission({"c1": cellcov(set())}, thr, lk, admissible_n={"10": False, "20": True, "40": True})
    assert e["consequences"]["h1"] == "exploratory" and e["method_at_n"]["20"] == "percentile"           # a failed fixture at n strikes every procedure at n
    base_only = {k: v for k, v in cellcov(set()).items() if "|40|" not in k}
    f = admission({"c1": base_only}, thr, lk)
    assert f["method_at_n"]["40"] is None and f["consequences"]["parametrized"] == "percentile_n20"       # no n = 40 measurements: not admitted, not needed


def test_report_roundtrip_and_hash(tmp_path):
    rep = {"selection": ["a"], "admitted_sides": {"gain|upper|0.95|20": "percentile"}}
    h = write_report(tmp_path / "r.json", rep)
    assert len(h) == 64 and load_report(tmp_path / "r.json") == rep
```

Append to `tests/test_manifest.py`:

```python
def test_manifest_lists_the_coverage_study_outside_the_search_gate_and_the_weights():
    from sim.manifest import coverage_cells, enumerate_manifest, manifest_weights, totals
    lk = load_locked(); cov = lk["seeds"]["coverage"]
    base_seeds = cov["pool"] + sum(int(cov["replications"][str(n)]) * n for n in (10, 20))
    est = coverage_cells(lk, None)
    assert len(est) == 24 and all(c.section == "coverage" for c in est)
    assert sum(c.runs for c in est if c.kind == "coverage_base") == 6 * 5 * base_seeds
    sel = [{"name": "B2_D1_beta0.05_rho0.5_median_development", "rule": "B2", "family": "D1", "position": "median", "runs_per_seed": 4}]
    real = coverage_cells(lk, sel)
    kinds = {c.kind: c.runs for c in real}
    assert kinds["coverage_base"] == 4 * base_seeds and kinds["coverage_conditional"] > 0 and len(real) == 4
    assert [c for c in real if c.name.endswith("n40")][0].runs == 4 * int(cov["replications"]["40"]) * 40
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"]); t = totals(cells)
    no_cov = [c for c in cells if c.section != "coverage"]
    assert t["coverage_base"] > 0 and t["coverage_conditional"] > 0
    assert t["pre_lock"] == totals(no_cov)["pre_lock"] and t["pre_lock_exact"] == totals(no_cov)["pre_lock_exact"]
    assert manifest_weights(cells) == manifest_weights(no_cov)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_coverage.py tests/test_manifest.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.coverage'` and `ImportError: cannot import name 'coverage_cells'`.

- [ ] **Step 3: Write the implementation**

```python
# sim/coverage.py
"""Coverage study (spec 8): the registered cell selection (ruling D12), fresh seed blocks, per-seed scalar observations
for the eight endpoints computed in chunks, conservative scoring against the reference-mean interval, the analytic
threshold with its registered simulation check, the joint fixture test and control power (scipy Hermite rule),
admission in the remedy order, and the report."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.special import roots_hermite

from .cell import Cell, SeedCache, run_focal
from .intervals import Bound, bound, t_interval
from .records import cfg_from_dict

STATISTICS = ("gain", "eff", "loss_diff")
ENDPOINTS = (("gain", "upper", 0.95), ("gain", "lower", 0.95), ("eff", "lower", 0.95), ("eff", "upper", 0.95),
             ("loss_diff", "lower", 0.9875), ("loss_diff", "upper", 0.9875), ("gain", "lower", 0.9875), ("gain", "upper", 0.9875))
LEVELS = (0.95, 0.9875)
PROCEDURES_AT_N = {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)}
BASE_N = (10, 20)
CONDITIONAL_N = (40,)


def endpoint_key(stat: str, side: str, level: float, n: int) -> str:
    return f"{stat}|{side}|{level}|{n}"


# ---- selection (ruling D12) -------------------------------------------------------------------------------------------

def skewness(x) -> float:
    x = np.asarray(x, dtype=float)
    return float("nan") if x.size < 3 or np.std(x) == 0.0 else float(stats.skew(x, bias=False))


def sarle_bimodality(x) -> float:
    x = np.asarray(x, dtype=float); n = x.size
    if n < 4 or np.std(x) == 0.0:
        return float("nan")
    g = float(stats.skew(x, bias=False)); k = float(stats.kurtosis(x, bias=False))
    return (g * g + 1.0) / (k + 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3)))


def select_cells(stats_by_cell: dict, k: int = 3) -> list:
    """Top k by gain skewness and top k by the Sarle coefficient of ban counts (finite values, descending, name as the
    tie-break); their union in order (skewness picks, then Sarle picks); while fewer than 2k, the next unused entry of
    the ranking that has contributed fewer distinct cells (ties to skewness); an exhausted ranking yields to the other."""
    def ranking(key):
        valid = [(float(v[key]), name) for name, v in stats_by_cell.items() if math.isfinite(float(v[key]))]
        return [name for _, name in sorted(valid, key=lambda p: (-p[0], p[1]))]
    ranks = [ranking("skew_gain"), ranking("sarle_bans")]
    chosen: list = []; contributed = [0, 0]; cursor = [0, 0]

    def take(i) -> bool:
        while cursor[i] < len(ranks[i]):
            name = ranks[i][cursor[i]]; cursor[i] += 1
            if name not in chosen:
                chosen.append(name); contributed[i] += 1
                return True
        return False

    for i in (0, 1):
        for _ in range(k):
            take(i)
    while len(chosen) < 2 * k:
        first = 1 if contributed[1] < contributed[0] else 0
        if not take(first) and not take(1 - first):
            break
    return chosen


# ---- seeds and observations ------------------------------------------------------------------------------------------

def seed_blocks(locked: dict, cell_index: int, pool_factor: int = 1, rep_factor: int = 1, n_list=None):
    cov = locked["seeds"]["coverage"]
    start = int(cov["start"]) + int(cell_index) * int(cov["block"])
    pool_n = int(cov["pool"]) * int(pool_factor)
    pool = np.arange(start, start + pool_n, dtype=np.int64)
    nxt = start + pool_n; reps = {}
    wanted = {int(n) for n in (n_list if n_list is not None else cov["n_grid"])}
    for n in cov["n_grid"]:                                   # fixed layout: every n reserves its range even when not run now
        R = int(cov["replications"][str(n)]) * int(rep_factor)
        if int(n) in wanted:
            reps[int(n)] = np.arange(nxt, nxt + R * int(n), dtype=np.int64).reshape(R, int(n))
        nxt += R * int(n)
    if nxt > start + int(cov["block"]):
        raise ValueError(f"coverage block of {cov['block']} seeds is too small for pool {pool_n} and the replication layout ({nxt - start} seeds)")
    return pool, reps


@dataclass
class CoverageCellSpec:
    name: str
    cfg: dict
    focal: int
    rule: str
    family: str
    params_by_rule: dict
    attack_knobs_by_rule: dict
    ref_candidate: dict | None
    pair: tuple = ("B2", "B3")


def trajectory_keys(spec: CoverageCellSpec) -> list:
    keys = [(spec.rule, "attack"), (spec.rule, "clip")] + ([(spec.rule, "ref")] if spec.ref_candidate is not None else [])
    for p in spec.pair:
        if p != spec.rule:
            keys += [(p, "attack"), (p, "clip")]
    return keys


def runs_per_seed(spec: CoverageCellSpec) -> int:
    return len(trajectory_keys(spec))


def _factory(spec: CoverageCellSpec, rule: str, kind: str, families: dict):
    from .records import candidate_from_record
    fam = families[spec.family]; knobs = spec.attack_knobs_by_rule[rule]
    if kind == "attack":
        return lambda: fam.make(dict(knobs))
    if kind == "clip":
        return lambda: fam.make(fam.project(dict(knobs)))
    return candidate_from_record(fam, spec.ref_candidate).policy_factory


def observe_chunk(spec: CoverageCellSpec, seeds, families: dict) -> dict:
    """Scalars per seed for one chunk: profit of the focal entity, gross efficiency, S*; episode results are dropped."""
    from .registry import make_rule
    seeds = tuple(int(s) for s in seeds); cfg = cfg_from_dict(spec.cfg); N = cfg.N; f = spec.focal; cache = SeedCache()
    scal: dict = {}
    for rule, kind in trajectory_keys(spec):
        cell = Cell(cfg=cfg, rule_factory=(lambda r=rule: make_rule(r, spec.params_by_rule[r])), focal=f, seeds=seeds, name=f"{spec.name}/{rule}/{kind}")
        res = run_focal(cell, _factory(spec, rule, kind, families), cache).results
        scal[(rule, kind)] = {"profit": np.array([r.profit[f] for r in res]), "eff": np.array([(r.W + r.audit_cost) / r.sstar for r in res]),
                              "sstar": np.array([r.sstar for r in res])}
        del res
    own = scal[(spec.rule, "attack")]; scale = own["sstar"] / N
    p_ref = scal[(spec.rule, "ref")]["profit"] if (spec.rule, "ref") in scal else np.zeros_like(own["profit"])
    a, b = spec.pair
    return {"gain": (own["profit"] - p_ref) / scale, "eff": own["eff"],
            "loss_diff": (scal[(a, "clip")]["eff"] - scal[(a, "attack")]["eff"]) - (scal[(b, "clip")]["eff"] - scal[(b, "attack")]["eff"])}


def observe(spec: CoverageCellSpec, seeds, chunk: int = 500, families: dict | None = None) -> dict:
    from .registry import available_families
    families = families or available_families()
    seeds = np.asarray(seeds, dtype=np.int64).ravel(); parts = [observe_chunk(spec, seeds[i:i + chunk], families) for i in range(0, len(seeds), chunk)]
    return {s: np.concatenate([p[s] for p in parts]) if parts else np.zeros(0) for s in STATISTICS}


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
    """Expected conservative coverage of x_bar + c s / sqrt(n) scored against pool_mean + z sigma / sqrt(M) for normal data
    with known sigma: the pool-mean error and the sample mean combine into one normal, so the statistic is noncentral t
    with df n - 1. The reference interval's t quantile and the pool's sample variance add O(1/M) terms (below 1e-6 at
    M = 35,000); the registered cross-check is `threshold_check` (spec 8)."""
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


def _pool_coverages(n: int, level: float, M: int, pools: int, reps: int, rng) -> np.ndarray:
    crit = stats.t.ppf(level, n - 1); out = np.empty(pools)
    for k in range(pools):
        pool = rng.normal(size=M); _, hi = t_interval(pool, 0.95)
        X = rng.normal(size=(reps, n)); U = X.mean(axis=1) + crit * X.std(axis=1, ddof=1) / math.sqrt(n)
        out[k] = float((U >= hi).mean())
    return out


def threshold_check(locked: dict, M: int, pools: int, reps: int, rng) -> dict:
    """The registered cross-check of the analytic threshold: 200 pools of size M, 20,000 replications each (spec 8). The
    replications in one pool share its mean error, so the standard error is the between-pool one: sd(per-pool coverage) / sqrt(pools)."""
    out = {}
    for key, t in thresholds(locked, M).items():
        cov = _pool_coverages(t["n"], t["level"], M, pools, reps, rng); sim = float(cov.mean())
        se = float(cov.std(ddof=1) / math.sqrt(pools)) if pools > 1 else float("inf")
        out[key] = {"analytic": t["exact"], "simulated": sim, "gap": t["exact"] - sim, "se": se, "pools": pools, "reps": reps, "pass_": bool(abs(t["exact"] - sim) <= 3 * se + 1e-4)}
    return out


def clopper_pearson_lower(k: int, n: int, conf: float) -> float:
    return 0.0 if k == 0 else float(stats.beta.ppf(1.0 - conf, k, n - k + 1))


def joint_fixture(locked: dict, n: int, M: int, R: int, thr: dict, trials: int, rng, cells: int = 6) -> dict:
    """One trial: for each cell and each statistic an independent normal pool and (R, n) sample; the sides and levels of
    one statistic share its sample; admitted when all 6 x 8 endpoints are at or above threshold."""
    iv = locked["intervals"]; conf = 1.0 - 0.05 / 3.0; admitted = 0
    crit = {lv: float(stats.t.ppf(lv, n - 1)) for lv in LEVELS}
    for _ in range(trials):
        ok = True
        for _c in range(cells):
            for stat in STATISTICS:
                pool = rng.normal(size=M); lo, hi = t_interval(pool, float(iv["reference_level"]))
                X = rng.normal(size=(R, n)); m = X.mean(axis=1); se = X.std(axis=1, ddof=1) / math.sqrt(n)
                for s, side, lv in ENDPOINTS:
                    if s != stat:
                        continue
                    cov = float(((m + crit[lv] * se) >= hi).mean()) if side == "upper" else float(((m - crit[lv] * se) <= lo).mean())
                    if cov < thr[f"{n}|{lv}"]["threshold"]:
                        ok = False; break
                if not ok:
                    break
            if not ok:
                break
        admitted += int(ok)
    ll = clopper_pearson_lower(admitted, trials, conf)
    return {"n": n, "M": M, "R": R, "trials": trials, "cells": cells, "endpoints_per_cell": len(ENDPOINTS), "admitted": admitted, "conf": conf,
            "lower_limit": ll, "pass_": bool(ll >= 0.9)}


def control_power(n: int, level: float, deficit_points: float, M: int, R: int, threshold: float, nodes: int, ref_level: float = 0.95) -> float:
    """Expected binomial rejection probability of the negative control (a t bound whose true coverage is the nominal level
    minus the deficit), integrated over the pool-mean error with the Gauss-Hermite rule (spec 8, power)."""
    c = float(stats.t.ppf(level - deficit_points / 100.0, n - 1))
    z = stats.norm.ppf(0.5 + ref_level / 2.0); delta = z / math.sqrt(M)
    x, w = roots_hermite(int(nodes))
    eps = math.sqrt(2.0) / math.sqrt(M) * x                       # pool-mean error in units of sigma
    nc = -(eps + delta) * math.sqrt(n)
    p = 1.0 - stats.nct.cdf(-c, n - 1, nc)
    p = np.where(np.isfinite(p), p, (nc < 0).astype(float))      # scipy's nct.cdf returns NaN for |nc| above about 9: coverage is 1 when the pool mean is far below, 0 when far above
    need = int(math.ceil(R * threshold))                         # admitted iff hits >= need; rejected iff hits <= need - 1
    rej = stats.binom.cdf(need - 1, R, p)
    total = float((w * rej).sum() / math.sqrt(math.pi))
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(w)) and math.isfinite(total)):
        raise FloatingPointError("non-finite quadrature in control_power")
    return total


def power_check(locked: dict, M: int, R_by_n: dict, thr: dict) -> dict:
    iv = locked["intervals"]; out = {}
    for key, t in thr.items():
        n, lv = t["n"], t["level"]
        if int(n) not in R_by_n:
            continue
        d = float(iv["deficits"][str(lv)]); R = int(R_by_n[int(n)])
        p200 = control_power(n, lv, d, M, R, t["threshold"], int(iv["quadrature_nodes"]), float(iv["reference_level"]))
        p400 = control_power(n, lv, d, M, R, t["threshold"], 2 * int(iv["quadrature_nodes"]), float(iv["reference_level"]))
        conv = abs(p200 - p400) <= 0.001
        out[key] = {"deficit": d, "power_200": p200, "power_400": p400, "converged": bool(conv), "pass_": bool(conv and p200 >= 0.8)}
    return out


def fixture_and_power(locked: dict, smoke: bool, rng, n_list) -> dict:
    cov = locked["seeds"]["coverage"]; iv = locked["intervals"]
    base_M = 200 if smoke else int(cov["pool"]); trials = 10 if smoke else int(iv["joint_trials"])
    base_R = {int(n): (20 if smoke else int(cov["replications"][str(n)])) for n in cov["n_grid"]}
    per_n = {}; admissible = {}; remedies = {}; checks = {}
    pools_c, reps_c = (5, 500) if smoke else (int(iv.get("threshold_check_pools", 200)), int(iv.get("threshold_check_reps", 20000)))
    for n in n_list:
        n = int(n); attempts = []
        for pf, rf in ((1, 1), (2, 1), (2, 2)):
            M = base_M * pf; R = base_R[n] * rf; thr = thresholds(locked, M)
            if str(M) not in checks:                                  # the analytic threshold is cross-checked at every M actually used
                checks[str(M)] = threshold_check(locked, M, pools_c, reps_c, rng)
            chk_ok = all(v["pass_"] for k, v in checks[str(M)].items() if v and int(k.split("|")[0]) == n)
            fx = joint_fixture(locked, n, M, R, thr, trials, rng)
            pw = power_check(locked, M, {n: R}, {k: v for k, v in thr.items() if v["n"] == n})
            ok = fx["pass_"] and all(v["pass_"] for v in pw.values()) and chk_ok
            attempts.append({"pool_factor": pf, "rep_factor": rf, "M": M, "R": R, "fixture": fx, "power": pw, "threshold_check_pass": bool(chk_ok), "pass_": bool(ok)})
            if ok:
                break
        per_n[str(n)] = attempts; admissible[str(n)] = bool(attempts[-1]["pass_"])
        remedies[str(n)] = {"pool_factor": attempts[-1]["pool_factor"], "rep_factor": attempts[-1]["rep_factor"], "admissible": admissible[str(n)]}
    return {"per_n": per_n, "admissible_n": admissible, "remedies": remedies, "base_M": base_M, "base_R": {str(k): v for k, v in base_R.items()},
            "threshold_check": checks, "smoke": bool(smoke)}


# ---- admission -------------------------------------------------------------------------------------------------------

def admission(measured: dict, thr_by_n: dict, locked: dict, admissible_n: dict | None = None) -> dict:
    admissible_n = admissible_n or {}
    procedure_admitted = {}
    for n, procs in PROCEDURES_AT_N.items():
        thr = thr_by_n.get(n) or thr_by_n.get(str(n)) or {}
        for proc in procs:
            ok = len(measured) > 0 and admissible_n.get(str(n), True) and bool(thr)
            for cell, cov in measured.items():
                for stat, side, lv in ENDPOINTS:
                    key = f"{endpoint_key(stat, side, lv, n)}|{proc}"
                    if key not in cov or cov[key] < thr[f"{n}|{lv}"]["threshold"]:
                        ok = False
            procedure_admitted[f"{proc}|{n}"] = bool(ok)
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
    """The coverage study (spec 8 and spec 5.3 lines 450 to 463): per selected cell a base entry (the pool plus the
    replications at n = 10 and n = 20) and three conditional entries (n = 40, one M doubling, one R doubling), with the
    run count derived from the cell's trajectory keys (runs_per_seed). Outside the search gate and the weights. Before
    the study has run, six cells are estimated at five runs per seed."""
    from .coverage import BASE_N
    cov = locked["seeds"]["coverage"]; bh = float(locked["beta_headline"]); rho0 = float(locked["rho"]["default"])
    R = {int(n): int(r) for n, r in cov["replications"].items()}; pool = int(cov["pool"])
    base_seeds = pool + sum(R[n] * n for n in BASE_N)
    cond = {"n40": R[40] * 40, "double_M": pool, "double_R": sum(R[n] * n for n in R)}
    sel = selection if selection is not None else [{"name": f"estimate_{i}", "rule": "?", "family": "?", "position": "?", "runs_per_seed": 5} for i in range(6)]
    out = []
    for s in sel:
        k = int(s["runs_per_seed"]); kind_est = selection is None
        out.append(CellSpec("coverage", s["rule"], s["family"], bh, rho0, s["position"], "coverage_base", k * base_seeds, True, False, f"coverage_{s['name']}_base"))
        for name, seeds in cond.items():
            out.append(CellSpec("coverage", s["rule"], s["family"], bh, rho0, s["position"], "coverage_conditional", k * seeds, True, False, f"coverage_{s['name']}_{name}"))
    return out
```

(the `kind_est` variable is unused; drop it.) In `enumerate_manifest`, after the existing cells are built, append `coverage_cells(locked, _load_selection())` where `_load_selection()` returns the parsed `experiments/coverage_cells.json` if it exists, else `None`. In `totals`: `if c.section == "coverage": t[c.kind] = t.get(c.kind, 0) + c.runs; continue` before the `pre_lock` accounting (so `coverage_base` and `coverage_conditional` are reported and nothing from the study enters `pre_lock*`). In `manifest_weights`: build `rules` from `c for c in cells if not c.post_lock and c.section != "coverage" and c.rule not in ("all", "proposed")`, and in the loop `if c.post_lock or c.section == "coverage": continue`. In `scripts/manifest.py`, print `coverage base (outside the search gate): <runs> runs, <hours> core-hours at the benchmark rate; conditional: <runs> runs`.

```python
# scripts/coverage_study.py
"""Run the coverage study (spec 8) on the sweep's reference records: validate the 18-cell universe against the current
calibration and tuned parameters, select 6 cells (ruling D12), compute thresholds with their simulation check, run the
joint fixture test and the power check with the registered remedies per n, run the pools and replications in chunks
(n = 10 and n = 20 first; n = 40 only when the remedy order reaches it), admit the procedures, and write the report."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import SMOKE_BUDGET, check_bank_record, check_record, job_for, load_bank_doc, load_params, make_cell, read_dir, train_val  # noqa: E402
from sim.calibrate import load_calibration  # noqa: E402
from sim.cell import SeedCache, run_focal  # noqa: E402
from sim.coverage import (BASE_N, CONDITIONAL_N, CoverageCellSpec, STATISTICS, PROCEDURES_AT_N, admission, fixture_and_power, measure, observe,  # noqa: E402
                          reference_interval, runs_per_seed, sarle_bimodality, seed_blocks, select_cells, skewness, thresholds, write_report)
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash  # noqa: E402
from sim.manifest import enumerate_manifest  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.records import cfg_from_dict  # noqa: E402
from sim.reference import participant_diagnostics  # noqa: E402
from sim.registry import available_families  # noqa: E402
from sim.rng import load_identity_salt  # noqa: E402
from sim.schedule import budget_from_locked  # noqa: E402


def validated_universe(sweep_out: Path, locked: dict, cal, tuned_dir: Path | None, smoke: bool) -> dict:
    """The 18 development cells at beta_headline with their reference records, each checked by the sweep's own
    check_record against a job rebuilt from the current calibration and tuned parameters (stale, foreign, or smoke
    records are refused in registered mode)."""
    budget = SMOKE_BUDGET if smoke else budget_from_locked(locked); base = market_config_from_locked(locked)
    rules = ["B1", "B2", "B3"]
    params = {r: load_params(r, tuned_dir, smoke, cal.market_key, settings_hash(locked), cal.seeds) for r in rules}
    specs = [c for c in enumerate_manifest(locked, rules, budget=budget) if c.section == "development" and float(c.beta) == float(locked["beta_headline"])]
    refs = read_dir(sweep_out / "reference"); out = {}
    for spec in specs:
        job = job_for(spec, locked, cal, base, params[spec.rule], budget, smoke)
        rec = refs.get(spec.name)
        if rec is None:
            raise SystemExit(f"{spec.name}: no reference record in {sweep_out}/reference")
        check_record(job, rec)
        if rec.get("smoke") and not smoke:
            raise SystemExit(f"{spec.name}: smoke record in a registered run")
        out[spec.name] = (job, rec)
    if len(out) != 18:
        raise SystemExit(f"expected 18 development cells at beta_headline, found {len(out)}")
    return out


def cell_statistics(job: dict, rec: dict) -> dict:
    gain = np.array(rec["attack_per_seed_normalized"]) - np.array(rec["reference_per_seed_normalized"])
    train, _, _ = train_val(job); fam = available_families()[job["spec"]["family"]]
    cell = make_cell(job, train); res = run_focal(cell, lambda: fam.make(dict(rec["attack_knobs"])), SeedCache()).results
    bans = np.array([participant_diagnostics(r, cell.cfg, cell.focal)["focal_bans"] for r in res], dtype=float)
    return {"skew_gain": skewness(gain), "sarle_bans": sarle_bimodality(bans), "n_train": int(len(gain))}


def build_spec(name: str, universe: dict) -> CoverageCellSpec:
    job, rec = universe[name]; spec = job["spec"]
    params, knobs = {}, {}
    for rule in ("B1", "B2", "B3"):
        pj, pr = next(v for v in universe.values() if v[0]["spec"]["rule"] == rule and v[0]["spec"]["family"] == spec["family"] and v[0]["spec"]["position"] == spec["position"])
        params[rule] = pj["params"]; knobs[rule] = pr["attack_knobs"]
    cand = rec["candidate"]
    return CoverageCellSpec(name=name, cfg=job["cfg"], focal=positions(cfg_from_dict(job["cfg"]))[spec["position"]], rule=spec["rule"], family=spec["family"],
                            params_by_rule=params, attack_knobs_by_rule=knobs, ref_candidate=None if cand["name"] == "abstain" else cand)


def pool_observations(spec: CoverageCellSpec, pool: np.ndarray, out: Path, tag: str) -> dict:
    """The pool is observed once per (cell, pool_factor) and saved; every n reads it back (the manifest's base entry)."""
    path = out / f"pool_{tag}.npz"
    if path.exists():
        d = np.load(path)
        if np.array_equal(d["seeds"], pool):
            return {s: d[s] for s in STATISTICS}
    pobs = observe(spec, pool)
    np.savez(path, seeds=pool, **pobs)
    return pobs


def run_cell(args) -> tuple:
    name, spec, locked, index, pool_factor, rep_factor, n_list, smoke, out = args
    out = Path(out); settings = dict(locked["intervals"])
    if smoke:
        settings["bootstrap_resamples"] = 200
    pool, reps = seed_blocks(locked, index, pool_factor, rep_factor, n_list=n_list)
    if smoke:
        pool = pool[:200]; reps = {n: r[:20] for n, r in reps.items()}
    pobs = pool_observations(spec, pool, out, f"{index}_{pool_factor}")
    refs = {s: reference_interval(pobs[s], float(locked["intervals"]["reference_level"])) for s in STATISTICS}
    measured = {}; degenerate = {}
    for n, S in reps.items():
        flat = observe(spec, S.ravel())
        samples = {s: flat[s].reshape(S.shape) for s in STATISTICS}
        measured.update(measure(samples, {s: refs[s][:2] for s in STATISTICS}, int(n), PROCEDURES_AT_N[int(n)], settings))
        degenerate[str(n)] = {s: float(np.mean(samples[s].std(axis=1) == 0.0)) for s in STATISTICS}     # share of replications with identical values
    return name, {"measured": measured, "pool_mean": {s: float(pobs[s].mean()) for s in STATISTICS}, "pool_se": {s: refs[s][2] for s in STATISTICS},
                  "pool_size": int(len(pool)), "replications": {str(n): int(S.shape[0]) for n, S in reps.items()},
                  "replication_se": {str(n): float(np.sqrt(0.95 * 0.05 / S.shape[0])) for n, S in reps.items()}, "degenerate_share": degenerate,
                  "runs": runs_per_seed(spec) * sum(S.size for S in reps.values()), "pool_runs": runs_per_seed(spec) * len(pool)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-out", dest="sweep_out", required=True); ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--select-only", dest="select_only", action="store_true"); ap.add_argument("--force-n40", dest="force_n40", action="store_true")
    ap.add_argument("--cell", type=int, default=None, help="run only this selected cell (0 to 5) and write cell_<i>.json; merge later with --merge")
    ap.add_argument("--merge", action="store_true", help="read cell_*.json from --out, run the fixture and power step, admit, and write the report")
    ap.add_argument("--register", action="store_true", help="copy the selection to experiments/coverage_cells.json for the manifest")
    a = ap.parse_args()
    lk = load_locked(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True); cal = load_calibration(a.calibration)
    tuned = Path(a.tuned_dir) if a.tuned_dir else None
    universe = validated_universe(Path(a.sweep_out), lk, cal, tuned, a.smoke)
    if not a.smoke:
        if list(cal.seeds) != list(locked_seeds(lk, "calibration")):
            raise SystemExit("the calibration must use the full calibration namespace")
        bank = load_bank_doc(Path(a.sweep_out))
        for name, (job, rec) in universe.items():
            check_bank_record(rec, bank, "coverage")
            if len(rec["attack_per_seed_normalized"]) != job["budget"][2] or len(rec["reference_per_seed_normalized"]) != job["budget"][2]:
                raise SystemExit(f"{name}: the record's dev-train vectors are not the full n_train = {job['budget'][2]}")
    stats_by_cell = {name: cell_statistics(job, rec) for name, (job, rec) in universe.items()}
    if a.smoke:
        chosen = sorted(universe)[:6]; unranked = True
    else:
        if any(v["n_train"] < 4 for v in stats_by_cell.values()):
            raise SystemExit("the ranking statistics need at least 4 dev-train seeds per cell")
        chosen = select_cells(stats_by_cell, k=3); unranked = False
        if len(chosen) != 6:
            raise SystemExit(f"the selection rule produced {len(chosen)} cells, not 6")
    specs = {name: build_spec(name, universe) for name in chosen}
    selection = [{"name": n, "rule": universe[n][0]["spec"]["rule"], "family": universe[n][0]["spec"]["family"], "position": universe[n][0]["spec"]["position"],
                  "runs_per_seed": runs_per_seed(specs[n]), **stats_by_cell[n]} for n in chosen]
    (out / "coverage_cells.json").write_text(json.dumps(selection, indent=1))
    if a.register:
        shutil.copy(out / "coverage_cells.json", "experiments/coverage_cells.json")
    print("selected: " + ", ".join(chosen) + (" (SMOKE, unranked)" if unranked else ""))
    if a.select_only:
        return
    rng = np.random.default_rng(int(lk["intervals"]["bootstrap_seed"]))
    n_list = list(BASE_N) + (list(CONDITIONAL_N) if a.force_n40 else [])
    fp = fixture_and_power(lk, a.smoke, rng, n_list)            # cheap and deterministic: every machine computes the same remedies
    results: dict = {}; thr_by_n: dict = {}
    my_cells = [chosen[a.cell]] if a.cell is not None else list(chosen)

    def run_ns(ns):
        for n in ns:
            rem = fp["remedies"][str(n)]; M = fp["base_M"] * rem["pool_factor"]; thr_by_n[int(n)] = thresholds(lk, M)
            jobs = [(name, specs[name], lk, chosen.index(name), rem["pool_factor"], rem["rep_factor"], (int(n),), a.smoke, out) for name in my_cells]
            got = dict(ProcessPoolExecutor(a.workers).map(run_cell, jobs)) if a.workers > 1 else dict(map(run_cell, jobs))
            for name, r in got.items():
                results.setdefault(name, {"measured": {}, "runs": 0, "pool_runs": 0, "per_n": {}})
                results[name]["measured"].update(r["measured"]); results[name]["runs"] += r["runs"]; results[name]["pool_runs"] = max(results[name]["pool_runs"], r["pool_runs"])
                results[name]["per_n"][str(n)] = {k: v for k, v in r.items() if k != "measured"}

    def needs_n40(adm):
        return adm["method_at_n"]["20"] is None and 40 not in thr_by_n and not a.smoke

    if a.merge:
        for pth in sorted(out.glob("cell_*.json")):
            results.update(json.loads(pth.read_text())["results"]); thr_by_n.update({int(k): v for k, v in json.loads(pth.read_text())["thr_by_n"].items()})
        missing = [c for c in chosen if c not in results]
        if missing:
            raise SystemExit(f"--merge: no cell_*.json for {missing}")
    else:
        run_ns(n_list)
        adm0 = admission({n: r["measured"] for n, r in results.items()}, thr_by_n, lk, fp["admissible_n"]) if a.cell is None else None
        if a.cell is None and needs_n40(adm0):
            fp40 = fixture_and_power(lk, a.smoke, rng, [40]); fp["per_n"].update(fp40["per_n"]); fp["remedies"].update(fp40["remedies"]); fp["admissible_n"].update(fp40["admissible_n"])
            run_ns([40])
        if a.cell is not None:
            (out / f"cell_{a.cell}.json").write_text(json.dumps({"results": results, "thr_by_n": {str(k): v for k, v in thr_by_n.items()}, "cell": chosen[a.cell]}, default=float))
            print(f"wrote {out / f'cell_{a.cell}.json'}; after all six cells exist run --merge (if the merge reports inconclusive at n = 20, rerun each cell with --force-n40, then --merge again)")
            return
    adm = admission({n: r["measured"] for n, r in results.items()}, thr_by_n, lk, fp["admissible_n"])
    if a.merge and needs_n40(adm):
        print("the n = 20 procedures are not admitted: rerun every cell with --cell i --force-n40, then --merge again", file=sys.stderr)
    provenance = {"settings_hash": settings_hash(lk), "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest(), "calibration_sha256": hashlib.sha256(Path(a.calibration).read_bytes()).hexdigest(),
                  "tuned_sha256": {r: hashlib.sha256((tuned / f"tuned_{r}.json").read_bytes()).hexdigest() for r in ("B1", "B2", "B3")} if tuned else None, "sweep_out": str(a.sweep_out)}
    report = {"smoke": bool(a.smoke), "unranked": unranked, "admission_basis": "smoke (not an admission)" if a.smoke else "registered", "selection": selection,
              "statistics": stats_by_cell, "thresholds": {str(n): t for n, t in thr_by_n.items()}, "fixture_and_power": fp, "cells": results, **adm,
              "provenance": provenance, "manifest_runs": sum(r["runs"] + r["pool_runs"] for r in results.values())}
    h = write_report(out / "coverage_report.json", report)
    print(json.dumps({"sha256": h, "method_at_n": adm["method_at_n"], "consequences": adm["consequences"], "runs": report["manifest_runs"]}))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_coverage.py tests/test_manifest.py -v`
Expected: PASS (13 new tests, under a minute).

- [ ] **Step 5: Smoke the script end to end and measure memory**

```bash
uv run python scripts/calibrate.py --seeds 2 --out /tmp/calibration_smoke.json
uv run python scripts/sweep.py --stage all --sections development --rules B1,B2,B3 --calibration /tmp/calibration_smoke.json --smoke --out /tmp/sweep_smoke
uv run python scripts/coverage_study.py --sweep-out /tmp/sweep_smoke --calibration /tmp/calibration_smoke.json --smoke --out /tmp/coverage_smoke
/usr/bin/time -l uv run python -c "import numpy as np, sys; sys.path.insert(0, '.'); from tests.test_coverage import small_spec; from sim.coverage import observe; observe(small_spec('B1'), np.arange(2000), chunk=500)" 2>&1 | grep "maximum resident"
uv run python scripts/manifest.py
```
Expected: the study prints six selected cells marked `(SMOKE, unranked)`, then a JSON line with `method_at_n`, `consequences`, and `runs`; the smoke report's `manifest_runs` equals the manifest formula for the smoke sizes (the pool is counted once per cell); the memory probe's maximum resident set stays under 1 GB for 2,000 seeds on the small market (the chunk, not the seed count, sets the peak; on the locked market a worker peaks near 1.3 GB per chunk of 500, so 16 workers need about 24 GB); the manifest prints the coverage base and conditional totals on their own lines. Then exercise the per-cell path: `--cell 0 --smoke` and `--cell 1 --smoke` into the same `--out`, then `--merge --smoke`, and compare the merged report's `cells` for those two cells with the single-process report (equal). Record the manifest's base total and core-hours in the ledger (expected 2.3 to 4.0 million episodes).

- [ ] **Step 6: Commit**

```bash
git add sim/coverage.py scripts/coverage_study.py sim/manifest.py scripts/manifest.py tests/test_coverage.py tests/test_manifest.py
git commit -m "feat: coverage study with the registered selection rule, chunked scalar observations, analytic thresholds with the simulation check, joint fixture and power checks per n, remedies, conditional n = 40, admission, report; manifest entries outside the gate"
```

---

### Task 6: The H1 runner with the budgeted backend and the token pilot, and T = 100 calibration

**Files:**
- Create: `scripts/h1.py`
- Modify: `scripts/calibrate.py` (`--T`)
- Test: `tests/test_h1_script.py`, `tests/test_calibrate.py` (one test)

**Interfaces:**
- Consumes: `run_h1_cell`, `h1_rows`, `H1_ROW_FIELDS`, `comprehension_check`, `make_backend`, `BudgetedBackend`, `CapExceeded`, `PilotTargetReached`, `PromptCache`, `FakeBackend` (Task 4); `render`, `describe_record`, `load_vocabulary`, `comprehension_questions` (Task 3); `cell_config`, `load_calibration`, `calibrate` (`sim/calibrate.py`); `positions`; `make_rule`, `available_rules` (Task 1b); `load_params` (`scripts/sweep.py`); `locked["h1"]`.
- Produces (`scripts/h1.py`):
  - CLI `--backend {fake-honest,fake-cheat,anthropic,jev} --rules B1,B2,B3[,proposed] --calibration PATH --calibration-t100 PATH [--tuned-dir DIR] [--cache DIR] --out DIR [--eval-namespace dev_val|final_eval] [--smoke] [--pilot] [--pilot-calls 200] [--max-calls N] [--max-cost-usd X] [--prompt PATH]`.
  - Ruling D9: `--calibration` is the T = 200 calibration whose market key and seeds verify the tuned files through `load_params`; `--calibration-t100` is the calibration the H1 market is built from (`cell_config` on the locked market with `T = locked["h1"]["T"]`). In `--smoke` both may be the same smoke calibration.
  - `run_h1(o: dict) -> dict`: the backend is wrapped in `BudgetedBackend(max_calls, max_cost_usd, prices, stop_at = pilot_calls if pilot else None)`, so every uncached request (comprehension included) is counted and the caps and the pilot target are enforced before the request that would exceed them; for every rule: the comprehension check once, then for every beta: `run_h1_cell` at the median position with `train_seeds = dev_train[:4]`, `selection_seeds = dev_train[:5]`, `eval_seeds = <namespace>[:repetitions]`; a `CapExceeded` or `PilotTargetReached` inside a cell leaves that cell out of the rows and records it in the summary as `partial`; `h1_rows.csv` is rewritten from the rows of this run (never appended); `h1_summary.json` holds `backend, model, instructions_sha256, T, eval_namespace, calibration_t100_sha256, calls_cap, cost_cap_usd, calls, cache_hits, usage, cost_usd, comprehension, cells, partial, stopped_by`; a cap stop exits with status 3 after writing, naming the cap.
  - `--pilot`: stops at exactly `--pilot-calls` uncached calls (`PilotTargetReached`), writes `<out>/pilot_<backend>.json` with `calls, mean_input_tokens, mean_output_tokens, mean_latency_s, cost_per_call_usd, projected_cost_usd = cost_per_call * calls_cap`, `complete = calls >= pilot_calls`, and exits 0; an incomplete pilot (the cells ended before the target) is written with `complete = false` and exits 4.
  - `--smoke`: `repetitions = 2`, `betas = [0.05]`, the cache under `<out>/cache`, `smoke_config` (N = 4, J = 30) with the T of `--calibration-t100` as the market; a `--tuned-dir` given under `--smoke` is still verified against `--calibration` (the D9 test).
- Produces (`scripts/calibrate.py`): `--T N` replaces the horizon of the locked market before calibration.

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
    p = tmp_path / "cal.json"; save_calibration(calibrate(cfg, [4000, 4001]), p)
    return p


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "h1.py"), *args], capture_output=True, text=True, cwd=ROOT)


def base_args(cal, out):
    return ["--calibration", str(cal), "--calibration-t100", str(cal), "--smoke", "--out", str(out)]


def test_h1_smoke_writes_rows_and_summary_and_replays(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-cheat", "--rules", "B1,B2", *base_args(cal, out))
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader((out / "h1_rows.csv").open()))
    assert len(rows) == 2 * 1 * 2 and {"rule", "beta", "budget", "rep", "eval_seed", "reference", "profit_attack", "profit_ref", "gain", "gain_vs_twin", "invalid", "backend"} <= set(rows[0])
    s = json.loads((out / "h1_summary.json").read_text())
    assert set(s["cells"]) == {"B1|0.05", "B2|0.05"} and all(c["inconclusive"] is False for c in s["cells"].values()) and s["partial"] == []
    assert s["comprehension"]["B1"] >= 0 and s["calls_cap"] == load_locked()["h1"]["calls_cap"] and s["calls"] > 0 and len(s["instructions_sha256"]) == 64
    r2 = run("--backend", "fake-cheat", "--rules", "B1,B2", *base_args(cal, out))
    assert r2.returncode == 0 and json.loads((out / "h1_summary.json").read_text())["calls"] == 0
    assert len(list(csv.DictReader((out / "h1_rows.csv").open()))) == 4                      # rewritten, not appended


def test_h1_stops_before_the_call_that_exceeds_the_cap(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--max-calls", "10")
    assert r.returncode == 3 and "calls cap" in (r.stderr + r.stdout)
    s = json.loads((out / "h1_summary.json").read_text())
    assert s["calls"] == 10 and s["partial"] == ["B1|0.05"] and s["stopped_by"].startswith("calls cap")
    assert not (out / "h1_rows.csv").exists() or list(csv.DictReader((out / "h1_rows.csv").open())) == []    # the partial cell is not written as rows


def test_h1_pilot_stops_at_the_target_and_reports_cost_per_call(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--pilot", "--pilot-calls", "17")
    assert r.returncode == 0, r.stderr
    p = json.loads((out / "pilot_fake.json").read_text())
    assert p["calls"] == 17 and p["complete"] is True and p["mean_input_tokens"] > 0 and p["mean_latency_s"] >= 0
    assert p["projected_cost_usd"] == pytest.approx(p["cost_per_call_usd"] * load_locked()["h1"]["calls_cap"])
    r2 = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, tmp_path / "out2"), "--pilot", "--pilot-calls", "100000")
    assert r2.returncode == 4 and json.loads((tmp_path / "out2" / "pilot_fake.json").read_text())["complete"] is False


def test_h1_final_eval_namespace_refused_before_the_unseal(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--eval-namespace", "final_eval")
    assert r.returncode != 0 and "final_eval" in (r.stderr + r.stdout)


def test_h1_verifies_tuned_files_against_the_t200_calibration(tmp_path):
    """Ruling D9: a non-smoke run takes the T = 200 calibration for the tuned-file check and the T = 100 one for the market."""
    import hashlib
    from sim.locked import market_config_from_locked, settings_hash
    from sim.cell import market_key
    import dataclasses
    lk = load_locked(); base = market_config_from_locked(lk)
    c = MarketConfig.default()
    small = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)
    save_calibration(calibrate(small, [4000]), tmp_path / "cal200.json")            # stands in for the T = 200 calibration
    save_calibration(calibrate(dataclasses.replace(small, T=5), [4000]), tmp_path / "cal100.json")
    tuned = tmp_path / "tuned"; tuned.mkdir()
    (tuned / "tuned_B1.json").write_text(json.dumps({"rule": "B1", "best_params": {"P1": 0.2, "P2": 0.35, "P3": 0.5}, "market_key": market_key(small),
                                                     "settings_hash": settings_hash(lk), "calibration_seeds": [4000], "quick": False}))
    out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", "--calibration", str(tmp_path / "cal200.json"), "--calibration-t100", str(tmp_path / "cal100.json"),
            "--tuned-dir", str(tuned), "--out", str(out), "--max-calls", "5", "--smoke")      # --smoke keeps the small market; the tuned file is still verified
    assert "tuned on another market" not in (r.stderr + r.stdout)                 # the T = 200 key verified the tuned file
    assert r.returncode == 3 and json.loads((out / "h1_summary.json").read_text())["T"] == 5    # the market came from the T100 calibration; the cap stopped it
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
Expected: FAIL: the five `h1.py` tests with a non-zero return code (no such script), the calibrate test with `unrecognized arguments: --T`.

- [ ] **Step 3: Write the implementation**

Replace `scripts/calibrate.py::main` with:

```python
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20, help="how many calibration seeds to use")
    ap.add_argument("--T", type=int, default=None, help="horizon override (the H1 market is calibrated at T = 100)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lk = load_locked()
    base = market_config_from_locked(lk)
    if args.T is not None:
        base = dataclasses.replace(base, T=int(args.T))
    cal = calibrate(base, seeds(lk, "calibration")[: args.seeds])
    save_calibration(cal, args.out)
    print(json.dumps(cal.as_dict(), sort_keys=True))
```

with `import dataclasses` added at the top of the script.

```python
# scripts/h1.py
"""Run the H1 five-episode procedure (spec 5.4) against registered rules with a model backend: the comprehension check
first, every uncached request counted and capped by the budgeted backend, replay from the prompt cache, and the
token pilot that sets the cost cap. Ruling D9: the T = 200 calibration verifies the tuned files; the T = 100
calibration builds the market."""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import load_params  # noqa: E402
from sim.calibrate import cell_config, load_calibration  # noqa: E402
from sim.config import MarketConfig  # noqa: E402
from sim.describe import comprehension_questions, describe_record, load_vocabulary, render  # noqa: E402
from sim.llm_actor import (ACTOR_INSTRUCTIONS, BudgetedBackend, CapExceeded, FakeBackend, H1_ROW_FIELDS, PilotTargetReached, PromptCache,  # noqa: E402
                           comprehension_check, h1_rows, make_backend, run_h1_cell)
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.registry import available_rules, make_rule  # noqa: E402

META = ["backend", "model", "rule", "beta", "eval_namespace", "T", "budget"]
FIELDS = META + H1_ROW_FIELDS


def smoke_config() -> MarketConfig:
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)


def h1_config(locked: dict, cal, beta: float, base: MarketConfig) -> MarketConfig:
    return cell_config(base, cal, rho=float(locked["rho"]["default"]), beta=float(beta))


def make_fake_cheat(instructions: str):
    def fn(kind, payload):
        if kind == "comprehension":
            return {"answers": {q["id"]: q["options"][0]["label"] for q in payload["questions"]}}
        p = payload["state"]["provider"]
        return {"effort": 0.0, "offer": {"claim": 1.0, "bid": p["a"]}}
    return FakeBackend(fn, instructions=instructions)


def run_h1(o: dict) -> tuple[dict, int]:
    lk = load_locked(); h = dict(lk["h1"]); smoke = bool(o["smoke"])
    reps = 2 if smoke else int(h["repetitions"]); betas = [0.05] if smoke else [float(b) for b in h["betas"]]
    lk_run = dict(lk, h1=dict(h, repetitions=reps))
    out = Path(o["out"]); out.mkdir(parents=True, exist_ok=True)
    cache = PromptCache(o["cache"] or (out / "cache" if smoke else Path("experiments/cache/h1") / o["backend"]))
    instructions = Path(o["prompt"]).read_text() if o.get("prompt") else ACTOR_INSTRUCTIONS
    raw = make_fake_cheat(instructions) if o["backend"] == "fake-cheat" else make_backend(o["backend"], lk, instructions)
    calls_cap = int(o["max_calls"] if o["max_calls"] is not None else h["calls_cap"])
    cost_cap = o["max_cost_usd"] if o["max_cost_usd"] is not None else h.get("cost_cap_usd")
    backend = BudgetedBackend(raw, max_calls=calls_cap, max_cost_usd=cost_cap, prices=h.get("prices", {}), stop_at=int(o["pilot_calls"]) if o["pilot"] else None,
                              ledger=None if (smoke or o["pilot"]) else cache.directory / "ledger.json")      # the caps are cumulative across restarts of a real run
    cal200 = load_calibration(o["calibration"]); cal100 = load_calibration(o["calibration_t100"])
    base = dataclasses.replace(smoke_config(), T=int(cal100.T)) if smoke else dataclasses.replace(market_config_from_locked(lk), T=int(h["T"]))
    if not smoke and int(cal100.T) != int(h["T"]):
        raise SystemExit(f"--calibration-t100 has T = {cal100.T}, locked h1.T is {h['T']}")
    from sim.cell import market_key
    if cal100.market_key != market_key(base):
        raise SystemExit("--calibration-t100 belongs to a different market than the H1 market built from locked.yaml (or the smoke market)")
    try:
        eval_seeds = tuple(locked_seeds(lk, o["eval_namespace"]))
    except ValueError as e:
        raise SystemExit(f"evaluation namespace {o['eval_namespace']} is not available: {e}")
    train = tuple(locked_seeds(lk, "dev_train")[:4]); selection = tuple(locked_seeds(lk, "dev_train")[:5])
    voc = load_vocabulary(); qs = comprehension_questions()
    rules = [r.strip() for r in o["rules"].split(",") if r.strip()]
    unknown = [r for r in rules if r not in available_rules()]
    if unknown:
        raise SystemExit(f"unknown rules {unknown}; available: {available_rules()}")
    tuned = Path(o["tuned_dir"]) if o["tuned_dir"] else None
    params = {r: load_params(r, tuned, smoke, cal200.market_key, settings_hash(lk), cal200.seeds) for r in rules}
    summary = {"backend": backend.name, "model": backend.model, "instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(), "T": int(base.T),
               "calls_cumulative": backend.calls,
               "eval_namespace": o["eval_namespace"], "calibration_t100_sha256": hashlib.sha256(Path(o["calibration_t100"]).read_bytes()).hexdigest(),
               "calls_cap": calls_cap, "cost_cap_usd": cost_cap, "calls": 0, "cache_hits": 0, "usage": backend.usage, "cost_usd": 0.0,
               "comprehension": {}, "cells": {}, "partial": [], "stopped_by": None, "smoke": smoke}
    rows: list = []; status = 0

    def flush():
        summary["calls"] = backend.calls_this_run; summary["calls_cumulative"] = backend.calls; summary["cost_usd"] = backend.cost_usd
        (out / "h1_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True, default=float))
        with (out / "h1_rows.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

    try:
        summary["comprehension"] = comprehension_check(backend, cache, {r: make_rule(r, params[r]) for r in rules}, qs)
        for rule in rules:
            for beta in betas:
                key = f"{rule}|{beta}"; summary["partial"].append(key)
                cfg = h1_config(lk, cal100, beta, base)
                rule_factory = (lambda r=rule: make_rule(r, params[r]))
                rendered = render(describe_record(rule_factory()), voc)
                res = run_h1_cell(cfg, rule_factory, positions(cfg)["median"], backend, cache, rendered, train, eval_seeds[:reps], lk_run, selection)
                meta = {"backend": backend.name, "model": backend.model, "rule": rule, "beta": beta, "eval_namespace": o["eval_namespace"], "T": int(cfg.T), "budget": float(cfg.budget)}
                rows += h1_rows(res, meta)
                summary["cache_hits"] += sum(r.cache_hits for r in res.attack + res.twin + res.clipped + res.reference.twin_results)
                summary["cells"][key] = {"calls": res.calls, "new_calls_clipped": res.new_calls_clipped, "invalid_count": res.invalid_count,
                                         "inconclusive": res.inconclusive, "reference": res.reference.name, "reference_scores": res.reference.scores, "usage": res.usage}
                summary["partial"].remove(key)
                flush()
    except CapExceeded as e:
        summary["stopped_by"] = e.reason; status = 3
    except PilotTargetReached:
        summary["stopped_by"] = "pilot target"
    finally:
        flush()
    if o["pilot"]:
        n = max(backend.calls_this_run, 1); target = int(o["pilot_calls"])
        pilot = {"backend": backend.name, "model": backend.model, "calls": backend.calls_this_run, "target": target, "complete": backend.calls_this_run >= target,
                 "mean_input_tokens": backend.usage["input_tokens"] / n, "mean_output_tokens": backend.usage["output_tokens"] / n,
                 "mean_latency_s": (sum(backend.latencies) / len(backend.latencies)) if backend.latencies else 0.0,
                 "cost_per_call_usd": backend.cost_usd / n, "projected_cost_usd": backend.cost_usd / n * int(h["calls_cap"])}
        (out / f"pilot_{backend.name}.json").write_text(json.dumps(pilot, indent=1)); print(json.dumps(pilot))
        status = 0 if pilot["complete"] else 4
    if status == 3:
        print(f"stopped: {summary['stopped_by']}; partial cells {summary['partial']} are not in h1_rows.csv; results so far are in {out}", file=sys.stderr)
    return summary, status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True, choices=["fake-honest", "fake-cheat", "anthropic", "jev"])
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", required=True, help="the T = 200 calibration (verifies the tuned files, ruling D9)")
    ap.add_argument("--calibration-t100", dest="calibration_t100", required=True, help="the T = 100 calibration the H1 market is built from")
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--cache", default=None); ap.add_argument("--out", required=True)
    ap.add_argument("--eval-namespace", dest="eval_namespace", default="dev_val", choices=["dev_val", "final_eval"])
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--pilot-calls", dest="pilot_calls", type=int, default=200)
    ap.add_argument("--max-calls", dest="max_calls", type=int, default=None); ap.add_argument("--max-cost-usd", dest="max_cost_usd", type=float, default=None)
    ap.add_argument("--prompt", default=None, help="path of the sealed H1 prompt (sealed/h1_prompt.txt); replaces the development instructions")
    s, status = run_h1(vars(ap.parse_args()))
    print(json.dumps({"calls": s["calls"], "cost_usd": s["cost_usd"], "cells": {k: v["inconclusive"] for k, v in s["cells"].items()}, "partial": s["partial"]}))
    sys.exit(status)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_h1_script.py tests/test_calibrate.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Produce the T = 100 calibration and the fake run; the user runs the two real pilots**

```bash
uv run python scripts/calibrate.py --T 100 --out experiments/calibration_T100.json
uv run python scripts/h1.py --backend fake-cheat --rules B1,B2,B3 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/h1_fake
```
Expected: `results/h1_fake/h1_rows.csv` with 3 rules x 3 betas x 10 rows; the summary's `calls` is about 4,300 per cell on the first run (ruling D10's accounting) and 0 on a re-run. Then the user, with `ANTHROPIC_API_KEY` and `TYPESAFE_API_KEY` set, runs the two pilots and passes the Anthropic pilot file to `scripts/lock.py --pilot`:
```bash
uv run python scripts/h1.py --backend anthropic --rules B2 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_anthropic --pilot
uv run python scripts/h1.py --backend jev --rules B2 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_jev --pilot
```
The executor does not run the real pilots (they spend money); the ledger records that they are the user's step.

- [ ] **Step 6: Commit**

```bash
git add scripts/h1.py scripts/calibrate.py tests/test_h1_script.py tests/test_calibrate.py experiments/calibration_T100.json
git commit -m "feat: H1 runner with the budgeted backend (caps and pilot target before each request), comprehension check, cache replay, rewritten rows; calibrate --T"
```

---

### Task 7: The claim predicate, the lock, freeze, record, and module checks, the lock script, and the sealed bundle

**Files:**
- Create: `sim/claimcheck.py`, `sim/sealed.py`, `scripts/check_claim.py`, `scripts/lock.py`
- Modify: `sim/locked.py` (`seeds` falls back to the sealed final-eval seeds)
- Test: `tests/test_claimcheck.py`, `tests/test_sealed.py`, `tests/test_lock_script.py`

**Interfaces:**
- Consumes: `bound` (Task 2), `endpoint_key`, the coverage report (`admitted_sides`, `consequences`, `smoke`, `admission_basis`, `selection`, `fixture_and_power`) (Task 5), `uses_not_expressible` (Task 3), `settings_hash`, `load_locked` (`sim/locked.py`), the sweep's evaluate records (`rows` with `META_FIELDS + ROW_FIELDS`, `budget` included), `<sweep_out>/headline.json`, `h1_rows.csv` and `h1_summary.json` (Task 6), `SEALED_DIR` (Task 1b).
- Produces (`sim/claimcheck.py`):
  - `PASS, FAIL, INCONCLUSIVE`; `Verdict(status, bound, side, method, threshold, n, note)`; `decide(x, stat, pass_side, level, threshold, coverage, settings, n=None) -> Verdict`; `combine_all`, `combine_any`.
  - `h1_frame(h1_rows) -> DataFrame` (adds `family = "H1"`, renames `eval_seed -> seed`; `gain` is already the reference gain of Task 4).
  - `h1_cell_reason(rule, h1_summary, beta) -> str | None` (`"invalid repetitions"` when `cells[f"{rule}|{beta}"]["inconclusive"]`, `"missing"` when the cell is absent); `h1_proposed_reason(proposed, h1_summary, describe_record, beta) -> str | None` (`"not expressible"`, `"comprehension"` by ruling D11, or the cell reason).
  - `required_families(coverage) -> list[str]`: `["H2"]` plus `"H1"` when `coverage["consequences"]["h1"] == "confirmatory"`; H2's sample size is `consequences["final_eval_n"]` (an `inconclusive` parametrized consequence makes every H2 bound INCONCLUSIVE).
  - `evaluate_claim(h2, h1, coverage, locked, proposed, h1_summary=None, describe_record=None, h2_headline: dict[str, str] | None = None, demoted: set[str] = frozenset()) -> dict`: families come from `required_families`, never from which inputs are present (missing rows are INCONCLUSIVE with the note `"no rows"`); H2 rows of a rule are those at that rule's headline position (`h2_headline[rule]`, default `"median"`); a demoted cell `"<rule>|<family>"` (from the patch log) is INCONCLUSIVE; baseline H1 cells with invalid repetitions make their pairs INCONCLUSIVE; the audit sub-clause is `audit_cost_attack <= budget` on every seed (the harness clips audit spend to the budget, so this is a consistency check; a violation means corrupt rows); returns `claim`, `confirmatory`, `rule_clause`, `baseline_clause`, `h1_note`, `n`, `demoted`, `proposed`, `beta`.
  - `verdict_json(result) -> dict`.
  - Git and file checks: `tree_changes(repo, ref, paths=None) -> dict[path, status]` (`git diff --name-status -z --no-renames <ref> -- [paths]` between the tag and the working tree: `M`, `A`, `D`; git handles quoting and symlinks), `allowed(path, allow_list)`, `verify_lock(repo, lock_tag, allow_list) -> list[str]` (any change outside the allow-list: changed, new (added to the index), or deleted), `verify_freeze(repo, freeze_tag, locked, allow_list) -> list[str]` (the three `FROZEN_AT_FREEZE` files must exist in the tag (`git ls-tree`) and show no change against it; `sealed/` must exist and match the bundle hash; `verify_patches`), `verify_records(records, locked, jobs: dict[str, dict], expected_seeds: list[int]) -> list[str]` (for every record: the sweep's own `check_record(jobs[name], rec)` (params, cfg, settings hash, budget, smoke, salt), `eval_namespace == "final_eval"`, `bundle_hash` equals the lock commitment for H2 records, and the row seeds are exactly `expected_seeds[:final_eval_n]` in order), `verify_h1_summary(summary, rows, locked, prompt_path, expected_seeds) -> list[str]` (model is `h1.model` (the sealed LLM; Jev is a development actor, ruling D1), `T == h1.T`, `eval_namespace == "final_eval"`, `instructions_sha256` equals the sealed prompt's hash, `calibration_t100_sha256 == locked["calibration"]["T100"]["sha256"]`, not smoke, no partial cells, comprehension scores present for the proposed rule and B2 and B3, and per (rule, beta) the rows' `eval_seed` equal `expected_seeds[:h1_repetitions]` in order with `rep` 0..9 and `sum(invalid) == cells[...]["invalid_count"]`), `verify_coverage_report(path, locked) -> list[str]` (its hash equals `coverage_report_sha256`, `admission_basis == "registered"`, 6 selected cells with distinct names, `consequences` equal `locked["coverage_consequences"]`).
  - `check_proposed_module(path, repo, params=None) -> list[str]` (spec 12): the module's imports are only `sim.mechanisms.base` (absolute form; a relative import is reported, and `docs/custodian.md` and the run book say absolute imports only), `numpy`, `scipy`, `math`, `dataclasses`, `typing`, `__future__`, `itertools`, `functools`; importing it, and when `params` is given calling `make(params)`, changes no attribute of any loaded `sim.*` module (after importing `FROZEN_MODULES`, the snapshot covers every `sys.modules` entry whose name starts with `sim.`: module attributes, class attributes, and for functions and methods the identity of `__code__`, `__defaults__`, `__kwdefaults__`, and `__dict__`; plain values by `repr`); a detected change is reported and restored where the original is known.
- Produces (`sim/sealed.py`): `BUNDLE_FILES`, `bundle_hash(sealed_dir)` (ignores `patches/`, `__pycache__/`, `*.pyc`), `verify_bundle(sealed_dir, locked)`, `patch_log(sealed_dir) -> dict[path, {"sha256", "replaces": "<bundle file>", "demotes": [...]}]`, `verify_patches(sealed_dir) -> list[str]` (every patch file is logged with its hash, every logged file exists, and `replaces` names a file in `BUNDLE_FILES`), `demoted_cells(sealed_dir) -> set[str]`, `effective_path(sealed_dir, rel) -> Path` (the logged, hash-verified patch that replaces `rel`, else the original: the overlay by which a repair takes effect while the original bundle and its hash stay untouched), `SealedBundle`, `load_bundle(sealed_dir, locked)` (reads `h1_prompt.txt`, `h2/family.py`, `final_eval_seeds.json` through `effective_path`), `final_eval_seeds(sealed_dir)` (through `effective_path`). `sim/registry.py::available_families` and `scripts/h1.py --prompt` read through `effective_path` too.
- Produces (`sim/locked.py`): `seeds(locked, "final_eval")` falls back to the verified sealed bundle at `sim.registry.SEALED_DIR`.
- Produces (`scripts/check_claim.py`): two modes. **Synthetic** (`--synthetic --h2-rows CSV [--h1-rows CSV] --coverage-report PATH --proposed NAME`): the predicate only, no tree or hash checks, output marked `SYNTHETIC`. **Confirmatory** (the default): requires `--verify-lock TAG --verify-freeze TAG --sweep-out DIR --proposed NAME`, optional `--h1-dir DIR --tuned-dir DIR --proposed-describe PATH`; runs the tree checks, `check_proposed_module`, `verify_coverage_report`, `verify_records` against the sealed seed list, `verify_h1_summary`, and refuses (exit 2) on any problem; `--verify-only` stops after the tree, module, and coverage-report checks (exit 0 when clean, 2 otherwise) and needs no results; a verdict exits 0.
- Produces (`scripts/lock.py`): `--locked PATH --tuned-dir DIR --calibration PATH --calibration-t100 PATH --coverage-report PATH [--fixture PATH] --bundle-hash HEX --salt-hash HEX (--pilot PATH | --cost-cap-usd X) [--date 2026-10-28] [--check]`; validates before writing: the calibration's `T` equals the locked market `T` and the T100 calibration's `T` equals `h1.T`; the coverage report is registered (not smoke), has 6 distinct named cells, complete consequences, fixture and power results for n = 10 and n = 20 with `joint_trials` trials, every threshold cross-check passed, and no partial cell; a finite positive cost cap comes from `--pilot` (a complete Anthropic pilot of at least 200 calls; `ceil(projected_cost_usd)`) or `--cost-cap-usd`; both commitments are required and must be 64 hex characters; `--check` runs the same validation (reading the commitments and the cap from the file when not passed) and then compares every written value; writes `version`, `tuned`, `calibration` (with `T100`), `coverage_report_sha256`, `coverage_consequences`, `comprehension_fixture_sha256`, `sealed_bundle_sha256`, `identity_salt_sha256`, `h1.cost_cap_usd`; refuses if the settings hash changes; `--check` verifies every written value against its file and exits 1 on a mismatch; prints the commit, tag, push, and timestamp commands.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_claimcheck.py
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sim.claimcheck import (PASS, FAIL, INCONCLUSIVE, decide, combine_all, combine_any, h1_frame, h1_proposed_reason, required_families, evaluate_claim,
                            tracked_blobs, allowed, verify_lock, verify_freeze, verify_records, verify_h1_summary, verify_coverage_report, check_proposed_module)
from sim.coverage import ENDPOINTS, endpoint_key
from sim.locked import load_locked, settings_hash

ROOT = Path(__file__).resolve().parents[1]
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
    assert decide(hi[:5], "eff", "lower", 0.95, 0.90, cov, SETTINGS, n=20).status == INCONCLUSIVE
    assert combine_all([PASS, PASS]) == PASS and combine_all([PASS, INCONCLUSIVE]) == INCONCLUSIVE and combine_all([FAIL, INCONCLUSIVE]) == FAIL
    assert combine_any([FAIL, PASS]) == PASS and combine_any([FAIL, FAIL]) == FAIL and combine_any([FAIL, INCONCLUSIVE]) == INCONCLUSIVE


def frame(rule, family, gain, eff, eff_clip, audit, budget=1.0, n=20, position="median"):
    rng = np.random.default_rng(abs(hash((rule, family))) % 2**32)
    return pd.DataFrame({"rule": rule, "family": family, "position": position, "seed": np.arange(n), "beta": 0.05, "sstar": 10.0,
                         "gain": gain + rng.normal(0, 0.01, n), "eff_attack": eff + rng.normal(0, 0.005, n), "eff_clip": eff_clip + rng.normal(0, 0.005, n),
                         "audit_cost_attack": audit, "budget": budget})


def good_h2():
    return pd.concat([frame("R", "H2", 0.05, 0.97, 0.98, 0.5), frame("B2", "H2", 1.5, 0.80, 0.95, 0.5), frame("B3", "H2", 0.2, 0.85, 0.97, 0.5)], ignore_index=True)


def good_h1():
    return pd.concat([pd.DataFrame({"rule": r, "beta": 0.05, "rep": range(10), "eval_seed": range(10), "sstar": 5.0, "reference": "honest_max", "gain": g,
                                    "eff_attack": e, "eff_clip": e + 0.01, "audit_cost_attack": 0.1, "budget": 0.25, "invalid": 0})
                      for r, g, e in (("R", 0.02, 0.96), ("B2", 1.4, 0.8), ("B3", 1.3, 0.8))], ignore_index=True)


def summary(inconclusive=(), comp=None):
    return {"cells": {f"{r}|0.05": {"inconclusive": r in inconclusive} for r in ("R", "B2", "B3")}, "comprehension": comp or {"R": 7, "B2": 7, "B3": 6}}


def test_required_families_come_from_the_lock_not_the_inputs():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    assert required_families(coverage()) == ["H2", "H1"] and required_families(coverage(h1="exploratory")) == ["H2"]
    r = evaluate_claim(good_h2(), None, coverage(), lk, "R")                      # H1 required but absent
    assert r["confirmatory"] == ["H2", "H1"] and r["rule_clause"]["H1"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE
    r = evaluate_claim(None, good_h1(), coverage(), lk, "R", h1_summary=summary())  # H2 absent
    assert r["rule_clause"]["H2"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE
    r = evaluate_claim(good_h2(), good_h1(), coverage(h1="exploratory"), lk, "R")
    assert r["confirmatory"] == ["H2"] and r["claim"] == PASS and "exploratory" in r["h1_note"]
    r = evaluate_claim(good_h2(), good_h1(), coverage(method20=None, par="inconclusive", n_final=None), lk, "R", h1_summary=summary())
    assert r["rule_clause"]["H2"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE   # a failed parametrized remedy never drops H2


def test_claim_pass_fail_and_baseline_alternatives():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary())
    assert r["claim"] == PASS and r["baseline_clause"]["B2"]["status"] == PASS and r["baseline_clause"]["B3"]["status"] == PASS and r["n"] == {"H2": 20, "H1": 10}
    bad = good_h2(); bad.loc[bad.rule == "R", "gain"] += 1.0
    assert evaluate_claim(bad, good_h1(), coverage(), lk, "R", h1_summary=summary())["claim"] == FAIL
    over = good_h2(); over.loc[(over.rule == "R") & (over.seed == 3), "audit_cost_attack"] = 2.0
    assert evaluate_claim(over, good_h1(), coverage(), lk, "R", h1_summary=summary())["rule_clause"]["H2"]["audit"] == FAIL
    weak = good_h2(); weak.loc[weak.rule == "B2", "gain"] = 0.2; weak.loc[weak.rule == "B2", "eff_clip"] = weak.loc[weak.rule == "B2", "eff_attack"] + 0.005
    weak_h1 = good_h1(); weak_h1.loc[weak_h1.rule == "B2", "gain"] = 0.1; weak_h1.loc[weak_h1.rule == "B2", "eff_clip"] = weak_h1.loc[weak_h1.rule == "B2", "eff_attack"]
    assert evaluate_claim(weak, weak_h1, coverage(), lk, "R", h1_summary=summary())["baseline_clause"]["B2"]["status"] == FAIL
    # headline position: only rows at the rule's headline position enter
    two = pd.concat([good_h2(), frame("R", "H2", 5.0, 0.5, 0.5, 0.5, position="high")], ignore_index=True)
    assert evaluate_claim(two, good_h1(), coverage(), lk, "R", h1_summary=summary(), h2_headline={"R": "median"})["claim"] == PASS
    assert evaluate_claim(two, good_h1(), coverage(), lk, "R", h1_summary=summary(), h2_headline={"R": "high"})["claim"] == FAIL


def test_h1_invalidity_demotion_and_not_expressible():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary(inconclusive=("R",)))
    assert r["rule_clause"]["H1"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary(inconclusive=("B2",)))
    assert r["baseline_clause"]["B2"]["pairs"]["H1|gain"].status == INCONCLUSIVE and r["baseline_clause"]["B2"]["status"] == PASS   # B2 still passes through H2
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary(), demoted={"R|H2"})
    assert r["rule_clause"]["H2"]["status"] == INCONCLUSIVE and "demoted" in r["rule_clause"]["H2"]["eff"].note
    rec = {"allocation_order": "ascending bid", "eligibility": "not expressible", "payment": "the bid", "audit_selection": "none",
           "audit_tolerance": "none", "failed_audit": "none", "ban_length": "none", "holdback": "none"}
    assert h1_proposed_reason("R", summary(), rec, 0.05) == "not expressible"
    assert h1_proposed_reason("R", summary(comp={"R": 5, "B2": 7, "B3": 7, "B1": 3}), None, 0.05) == "comprehension"     # ruling D11: min of B2 and B3
    assert h1_proposed_reason("R", summary(comp={"R": 6, "B2": 7, "B3": 7}), None, 0.05) is None
    assert h1_proposed_reason("R", summary(inconclusive=("R",)), None, 0.05) == "invalid repetitions"
    assert h1_proposed_reason("R", {"cells": {}, "comprehension": {}}, None, 0.05) == "missing"
    f = h1_frame(good_h1()); assert set(f.family) == {"H1"} and "seed" in f


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout


def make_repo(tmp_path):
    repo = tmp_path / "repo"; (repo / "sim" / "mechanisms").mkdir(parents=True); (repo / "experiments").mkdir(); (repo / "docs").mkdir()
    git(repo, "init", "-q")
    (repo / "sim" / "market.py").write_text("frozen = 1\n"); (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 0\n")
    (repo / "experiments" / "proposed.yaml").write_text("a: 1\n"); (repo / "experiments" / "proposed_describe.yaml").write_text("b: 1\n")
    (repo / "docs" / "note.md").write_text("hi\n"); (repo / "docs" / "odd name.md").write_text("quoted path\n")
    git(repo, "add", "."); git(repo, "commit", "-q", "-m", "lock"); git(repo, "tag", "lock-test")
    return repo


ALLOW = ["sim/mechanisms/proposed.py", "experiments/proposed.yaml", "experiments/proposed_describe.yaml", "scripts/plot.py", "docs/", "sealed/", "sealed/patches/"]


def test_check_claim_refuses_modified_frozen_file(tmp_path):
    repo = make_repo(tmp_path)
    assert verify_lock(repo, "lock-test", ALLOW) == []
    assert "docs/odd name.md" in tracked_blobs(repo, None) and tracked_blobs(repo, None)["docs/odd name.md"] == tracked_blobs(repo, "lock-test")["docs/odd name.md"]
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
    assert verify_lock(repo, "lock-test", ALLOW) == []
    lk = {"sealed_bundle_sha256": bundle_hash(sealed), "allow_list": ALLOW}
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 2\n")
    assert any("proposed.py" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 1\n")
    (sealed / "__pycache__").mkdir(); (sealed / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []                              # import artifacts never change the bundle hash
    (sealed / "h1_prompt.txt").write_text("tampered\n")
    assert any("bundle" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))
    (sealed / "h1_prompt.txt").write_text("prompt\n")
    (sealed / "patches" / "fix.diff").write_text("--- a\n+++ b\n")
    assert any("patches" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))        # unlogged patch
    (sealed / "patches" / "log.json").write_text(json.dumps({"fix.diff": {"sha256": hashlib.sha256(b"--- a\n+++ b\n").hexdigest(), "demotes": ["R|H2"]},
                                                              "gone.diff": {"sha256": "00" * 32, "demotes": []}}))
    assert any("gone.diff" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))      # a logged patch must exist
    (sealed / "patches" / "log.json").write_text(json.dumps({"fix.diff": {"sha256": hashlib.sha256(b"--- a\n+++ b\n").hexdigest(), "demotes": ["R|H2"]}}))
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []
    from sim.sealed import demoted_cells
    assert demoted_cells(sealed) == {"R|H2"}
    (repo / "experiments" / "proposed_describe.yaml").unlink()
    assert any("proposed_describe.yaml" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))   # frozen files must exist


def test_verify_records_summary_and_coverage_report(tmp_path):
    from scripts.sweep import check_record
    lk = load_locked(); lk = dict(lk, identity_salt_sha256="ab" * 32, sealed_bundle_sha256="ee" * 32,
                                  calibration={"T100": {"sha256": "cc" * 32}}, coverage_consequences={"final_eval_n": 3, "h1": "confirmatory", "parametrized": "percentile_n20"})
    job = {"spec": {"name": "c", "rule": "B2", "family": "H2"}, "params": {"tol": 0.1}, "cfg": {"T": 200}, "settings_hash": settings_hash(lk), "budget": [1, 2, 3, 4], "smoke": False, "salt_hash": "ab" * 32}
    good = {**{k: job[k] for k in ("spec", "params", "cfg", "settings_hash", "budget", "smoke", "salt_hash")}, "eval_namespace": "final_eval", "bundle_hash": "ee" * 32,
            "rows": [{"seed": s} for s in (7, 8, 9)]}
    seeds = [7, 8, 9, 10]
    assert verify_records([good], lk, {"c": job}, seeds) == []
    for bad in (dict(good, settings_hash="x"), dict(good, salt_hash="y"), dict(good, params={"tol": 0.2}), dict(good, cfg={"T": 100}), dict(good, eval_namespace="dev_val"),
                dict(good, smoke=True), dict(good, bundle_hash="00" * 32), dict(good, rows=[{"seed": 8}, {"seed": 7}, {"seed": 9}]), dict(good, rows=[{"seed": 7}, {"seed": 8}]),
                dict(good, rows=[{"seed": 7}, {"seed": 8}, {"seed": 10}])):
        assert verify_records([bad], lk, {"c": job}, seeds) != []
    assert any("no job" in p for p in verify_records([dict(good, spec=dict(job["spec"], name="zz"))], lk, {"c": job}, seeds))
    prompt = tmp_path / "h1_prompt.txt"; prompt.write_text("sealed prompt")
    summ = {"model": lk["h1"]["model"], "T": lk["h1"]["T"], "eval_namespace": "final_eval", "instructions_sha256": hashlib.sha256(b"sealed prompt").hexdigest(),
            "calibration_t100_sha256": "cc" * 32, "smoke": False, "partial": [], "comprehension": {"R": 7, "B2": 7, "B3": 7},
            "cells": {f"{r}|0.05": {"inconclusive": False, "invalid_count": 0} for r in ("R", "B2", "B3")}}
    rows = pd.concat([pd.DataFrame({"rule": r, "beta": 0.05, "rep": range(10), "eval_seed": list(range(100, 110)), "invalid": 0}) for r in ("R", "B2", "B3")], ignore_index=True)
    sealed_seeds = list(range(100, 140))
    assert verify_h1_summary(summ, rows, lk, prompt, sealed_seeds) == []
    for bad in (dict(summ, model=lk["h1"]["jev_model"]), dict(summ, T=5), dict(summ, eval_namespace="dev_val"), dict(summ, instructions_sha256="00" * 32),
                dict(summ, calibration_t100_sha256="dd" * 32), dict(summ, smoke=True), dict(summ, partial=["B2|0.05"]), dict(summ, comprehension={"R": 7, "B2": 7})):
        assert verify_h1_summary(bad, rows, lk, prompt, sealed_seeds) != []
    wrong_seeds = rows.copy(); wrong_seeds.loc[wrong_seeds.rule == "R", "eval_seed"] = 0
    assert verify_h1_summary(summ, wrong_seeds, lk, prompt, sealed_seeds) != []
    wrong_invalid = rows.copy(); wrong_invalid.loc[wrong_invalid.rule == "B2", "invalid"] = 1
    assert verify_h1_summary(summ, wrong_invalid, lk, prompt, sealed_seeds) != []
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{"name": f"c{i}"} for i in range(6)], "consequences": lk["coverage_consequences"]}
    data = json.dumps(rep, sort_keys=True, indent=1).encode(); (tmp_path / "cov.json").write_bytes(data)
    lk2 = dict(lk, coverage_report_sha256=hashlib.sha256(data).hexdigest())
    assert verify_coverage_report(tmp_path / "cov.json", lk2) == []
    assert verify_coverage_report(tmp_path / "cov.json", dict(lk2, coverage_report_sha256="00" * 32)) != []
    for bad in (dict(rep, admission_basis="smoke (not an admission)"), dict(rep, selection=[{"name": "c0"}] * 6)):
        (tmp_path / "bad.json").write_text(json.dumps(bad, sort_keys=True, indent=1))
        assert verify_coverage_report(tmp_path / "bad.json", dict(lk2, coverage_report_sha256=hashlib.sha256((tmp_path / "bad.json").read_bytes()).hexdigest())) != []


def test_patch_overlay_applies_logged_repairs_without_touching_the_bundle(tmp_path):
    from sim.sealed import bundle_hash, effective_path, verify_patches
    s = tmp_path / "sealed"; (s / "h2").mkdir(parents=True); (s / "patches").mkdir()
    (s / "h1_prompt.txt").write_text("original\n"); (s / "h2" / "family.py").write_text("ORIG = 1\n"); h = bundle_hash(s)
    assert effective_path(s, "h1_prompt.txt") == s / "h1_prompt.txt"
    (s / "patches" / "h1_prompt.txt").write_text("repaired\n")
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": hashlib.sha256(b"repaired\n").hexdigest(), "replaces": "h1_prompt.txt", "demotes": []}}))
    assert verify_patches(s) == [] and effective_path(s, "h1_prompt.txt") == s / "patches" / "h1_prompt.txt" and bundle_hash(s) == h
    assert effective_path(s, "h1_prompt.txt").read_text() == "repaired\n" and (s / "h1_prompt.txt").read_text() == "original\n"
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": "00" * 32, "replaces": "h1_prompt.txt", "demotes": []}}))
    assert verify_patches(s) != [] and effective_path(s, "h1_prompt.txt") == s / "h1_prompt.txt"            # an unverified patch is not applied
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": hashlib.sha256(b"repaired\n").hexdigest(), "replaces": "nope.txt", "demotes": []}}))
    assert any("replaces" in p for p in verify_patches(s))


def test_check_proposed_module_import_and_attribute_rules(tmp_path):
    good = tmp_path / "good.py"; good.write_text("from sim.mechanisms.base import Mechanism\nimport numpy as np\nimport math\n\ndef make(params):\n    return None\n")
    assert check_proposed_module(good, ROOT) == []
    bad = tmp_path / "bad.py"; bad.write_text("from sim.market import run_episode\nimport sim.search\n\ndef make(params):\n    return None\n")
    probs = check_proposed_module(bad, ROOT)
    assert any("sim.market" in p for p in probs) and any("sim.search" in p for p in probs)
    mut = tmp_path / "mut.py"; mut.write_text("import sim.policies.honest as h\nh.HonestMax.name = 'hacked'\n\ndef make(params):\n    return None\n")
    probs = check_proposed_module(mut, ROOT)
    assert any("sim.policies.honest" in p for p in probs)
    import sim.policies.honest as hm
    assert hm.HonestMax.name != "hacked"                                                  # the check restores what it can and reports
    code = tmp_path / "code.py"; code.write_text("from sim.mechanisms.base import Mechanism\n\ndef _nop(self, *a, **k):\n    return {}\n\nMechanism.allocate.__code__ = _nop.__code__\n\ndef make(params):\n    return None\n")
    assert any("Mechanism.allocate" in p for p in check_proposed_module(code, ROOT))      # function code counts as an attribute
    late = tmp_path / "late.py"; late.write_text("import sim.metrics as m\n\ndef make(params):\n    m.LATE = 1\n    return None\n")
    assert check_proposed_module(late, ROOT) == [] and any("sim.metrics" in p for p in check_proposed_module(late, ROOT, params={}))   # mutation at factory time
    rel = tmp_path / "rel.py"; rel.write_text("from .base import Mechanism\n\ndef make(params):\n    return None\n")
    assert any("relative" in p.lower() or "not allowed" in p for p in check_proposed_module(rel, ROOT))


def test_check_claim_cli_synthetic_and_verify_only(tmp_path):
    good_h2().to_csv(tmp_path / "h2.csv", index=False); good_h1().to_csv(tmp_path / "h1.csv", index=False)
    (tmp_path / "cov.json").write_text(json.dumps(coverage())); (tmp_path / "s.json").write_text(json.dumps(summary()))
    cmd = [sys.executable, str(ROOT / "scripts" / "check_claim.py")]
    r = subprocess.run(cmd + ["--synthetic", "--h2-rows", str(tmp_path / "h2.csv"), "--h1-rows", str(tmp_path / "h1.csv"), "--h1-summary", str(tmp_path / "s.json"),
                              "--coverage-report", str(tmp_path / "cov.json"), "--proposed", "R", "--out", str(tmp_path / "verdict.json")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert json.loads((tmp_path / "verdict.json").read_text())["claim"] == "PASS" and "SYNTHETIC" in r.stdout
    r2 = subprocess.run(cmd + ["--h2-rows", str(tmp_path / "h2.csv"), "--coverage-report", str(tmp_path / "cov.json"), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r2.returncode == 2 and "synthetic" in (r2.stderr + r2.stdout).lower()           # CSV inputs without --synthetic are refused
    r3 = subprocess.run(cmd + ["--sweep-out", str(tmp_path), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r3.returncode == 2 and "verify-lock" in (r3.stderr + r3.stdout)                 # confirmatory mode needs both tags, the calibrations, the tuned dir, and the description
    repo = make_repo(tmp_path)
    r4 = subprocess.run(cmd + ["--verify-only", "--verify-lock", "lock-test", "--repo", str(repo), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r4.returncode == 0, r4.stderr
    (repo / "sim" / "market.py").write_text("frozen = 2\n")
    r5 = subprocess.run(cmd + ["--verify-only", "--verify-lock", "lock-test", "--repo", str(repo), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r5.returncode == 2 and "sim/market.py" in r5.stderr
```

```python
# tests/test_sealed.py
import json
import pytest
from sim.sealed import BUNDLE_FILES, bundle_hash, verify_bundle, patch_log, verify_patches, demoted_cells, load_bundle, final_eval_seeds
from sim.locked import load_locked, seeds


def make_bundle(root):
    s = root / "sealed"; (s / "h2").mkdir(parents=True); (s / "patches").mkdir()
    (s / "README.md").write_text("bundle\n"); (s / "h1_prompt.txt").write_text("You are a provider.\n")
    (s / "h2" / "family.py").write_text("from sim.policies.families import D2 as H2\nCONTAINMENT = 'contains D2 through an embedding'\n")
    (s / "h2" / "containment.md").write_text("H2 contains D2.\n")
    (s / "final_eval_seeds.json").write_text(json.dumps(list(range(5000, 5040))))
    (s / "identity_salt.hex").write_text("00" * 32 + "\n"); (s / "b1_check.json").write_text(json.dumps({"B1": "pass"}))
    return s


def test_bundle_hash_is_content_addressed_and_ignores_patches_and_bytecode(tmp_path):
    s = make_bundle(tmp_path); h = bundle_hash(s)
    assert len(h) == 64 and set(BUNDLE_FILES) <= {str(p.relative_to(s)) for p in s.rglob("*") if p.is_file()}
    (s / "patches" / "x.diff").write_text("d\n"); assert bundle_hash(s) == h
    (s / "h2" / "__pycache__").mkdir(); (s / "h2" / "__pycache__" / "family.cpython-312.pyc").write_bytes(b"\x00"); assert bundle_hash(s) == h
    (s / "h1_prompt.txt").write_text("changed\n"); assert bundle_hash(s) != h


def test_verify_and_load_bundle_and_seed_fallback(tmp_path, monkeypatch):
    import importlib
    s = make_bundle(tmp_path); lk = dict(load_locked(), sealed_bundle_sha256=bundle_hash(s))
    verify_bundle(s, lk)
    with pytest.raises(ValueError):
        verify_bundle(s, dict(lk, sealed_bundle_sha256="00" * 32))
    b = load_bundle(s, lk)
    assert b.h1_prompt.startswith("You are") and b.final_eval_seeds == list(range(5000, 5040)) and b.h2_module.H2.name == "D2" and b.salt_hex == "00" * 32
    assert final_eval_seeds(s) == list(range(5000, 5040))
    monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(s)); import sim.registry as reg; importlib.reload(reg)
    assert seeds(lk, "final_eval") == list(range(5000, 5040))
    with pytest.raises(ValueError):
        seeds(dict(lk, sealed_bundle_sha256="11" * 32), "final_eval")
    assert patch_log(s) == {} and verify_patches(s) == [] and demoted_cells(s) == set()
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


def setup(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir(); shutil.copy(ROOT / "experiments" / "locked.yaml", exp / "locked.yaml")
    shutil.copy(ROOT / "experiments" / "comprehension_fixture.yaml", exp / "comprehension_fixture.yaml")
    tuned = tmp_path / "tuned"; tuned.mkdir()
    for r in ("B1", "B2", "B3"):
        (tuned / f"tuned_{r}.json").write_text(json.dumps({"rule": r}))
    lk = load_locked(); T = lk["market"]["T"]; T100 = lk["h1"]["T"]
    cal = {"S_hat": 1.0, "n_FB": 2.0, "m": 0.5, "market_key": "k", "T": T, "seeds": [1]}
    (tmp_path / "cal.json").write_text(json.dumps(cal)); (tmp_path / "cal100.json").write_text(json.dumps(dict(cal, T=T100))); (tmp_path / "calbad.json").write_text(json.dumps(dict(cal, T=7)))
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{} for _ in range(6)],
           "fixture_and_power": {"per_n": {"10": [{"fixture": {"trials": lk["intervals"]["joint_trials"]}}], "20": [{"fixture": {"trials": lk["intervals"]["joint_trials"]}}]}},
           "consequences": {"h1": "confirmatory", "parametrized": "percentile_n20", "final_eval_n": 20}}
    rep["fixture_and_power"]["threshold_check"] = {"35000": {"10|0.95": {"pass_": True}}}; rep["cells"] = {f"c{i}": {"per_n": {"10": {}, "20": {}}} for i in range(6)}
    rep["selection"] = [{"name": f"c{i}"} for i in range(6)]
    (tmp_path / "cov.json").write_text(json.dumps(rep)); (tmp_path / "pilot.json").write_text(json.dumps({"projected_cost_usd": 118.4, "complete": True, "calls": 200, "backend": "anthropic"}))
    return exp, tuned


def cmd(tmp_path, exp, tuned, *extra):
    return [sys.executable, str(ROOT / "scripts" / "lock.py"), "--locked", str(exp / "locked.yaml"), "--tuned-dir", str(tuned), "--calibration", str(tmp_path / "cal.json"),
            "--calibration-t100", str(tmp_path / "cal100.json"), "--coverage-report", str(tmp_path / "cov.json"), "--fixture", str(exp / "comprehension_fixture.yaml"), *extra]


def test_lock_script_writes_lock_time_blocks_validates_inputs_and_check_passes(tmp_path):
    exp, tuned = setup(tmp_path); before = settings_hash(load_locked(exp / "locked.yaml"))
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32, "--pilot", str(tmp_path / "pilot.json")), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    lk = yaml.safe_load((exp / "locked.yaml").read_text())
    assert lk["version"] == "locked-2026-10-28" and set(lk["tuned"]) == {"B1", "B2", "B3"} and lk["calibration"]["T100"]["T"] == lk["h1"]["T"]
    assert lk["sealed_bundle_sha256"] == "ab" * 32 and lk["identity_salt_sha256"] == "cd" * 32 and lk["h1"]["cost_cap_usd"] == 119 and lk["coverage_consequences"]["final_eval_n"] == 20
    assert len(lk["coverage_report_sha256"]) == 64 and len(lk["comprehension_fixture_sha256"]) == 64
    assert settings_hash(lk) == before and "git tag -s lock-2026-10-28" in r.stdout
    chk = subprocess.run(cmd(tmp_path, exp, tuned, "--check", "--pilot", str(tmp_path / "pilot.json")), capture_output=True, text=True, cwd=ROOT)
    assert chk.returncode == 0, chk.stderr
    (tuned / "tuned_B2.json").write_text("{}")
    chk2 = subprocess.run(cmd(tmp_path, exp, tuned, "--check", "--pilot", str(tmp_path / "pilot.json")), capture_output=True, text=True, cwd=ROOT)
    assert chk2.returncode == 1 and "tuned_B2" in (chk2.stdout + chk2.stderr)


def test_lock_script_refuses_bad_inputs(tmp_path):
    exp, tuned = setup(tmp_path)
    base = cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32, "--cost-cap-usd", "120")
    bad_t = [a if a != str(tmp_path / "cal100.json") else str(tmp_path / "calbad.json") for a in base]
    r = subprocess.run(bad_t, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "T" in (r.stderr + r.stdout)
    smoke = json.loads((tmp_path / "cov.json").read_text()); smoke["admission_basis"] = "smoke (not an admission)"; (tmp_path / "cov_smoke.json").write_text(json.dumps(smoke))
    bad_c = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_smoke.json") for a in base]
    r = subprocess.run(bad_c, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "coverage" in (r.stderr + r.stdout).lower()
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "zz", "--salt-hash", "cd" * 32, "--cost-cap-usd", "1"), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "hex" in (r.stderr + r.stdout).lower()
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "cost cap" in (r.stderr + r.stdout).lower()                 # a cost cap is required (pilot or explicit)
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--salt-hash", "cd" * 32, "--cost-cap-usd", "120"), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "bundle-hash" in (r.stderr + r.stdout)                      # both commitments are required
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32, "--cost-cap-usd", "-1"), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "positive" in (r.stderr + r.stdout)
    short = json.loads((tmp_path / "cov.json").read_text()); short["fixture_and_power"]["threshold_check"]["35000"]["10|0.95"]["pass_"] = False
    (tmp_path / "cov_chk.json").write_text(json.dumps(short))
    bad_k = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_chk.json") for a in base]
    r = subprocess.run(bad_k, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "cross-check" in (r.stderr + r.stdout)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_claimcheck.py tests/test_sealed.py tests/test_lock_script.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sim.claimcheck'`, `... 'sim.sealed'`, and the lock-script tests with a non-zero return code.

- [ ] **Step 3: Write the implementation**

```python
# sim/sealed.py
"""The sealed held-out bundle (spec 6.1): layout, content hash, patch log with demotions, and loader."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

BUNDLE_FILES = ("README.md", "h1_prompt.txt", "h2/family.py", "h2/containment.md", "final_eval_seeds.json", "identity_salt.hex", "b1_check.json")
IGNORED_DIRS = ("patches", "__pycache__")


def _bundle_files(root: Path):
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        rel = p.relative_to(root)
        if any(part in IGNORED_DIRS for part in rel.parts) or p.suffix == ".pyc":
            continue
        yield rel.as_posix(), p


def bundle_hash(sealed_dir) -> str:
    h = hashlib.sha256()
    for rel, p in _bundle_files(Path(sealed_dir)):
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
    present = {q.relative_to(d).as_posix(): q for q in d.rglob("*") if q.is_file() and q.name != "log.json"} if d.exists() else {}
    for rel, p in present.items():
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if rel not in log:
            problems.append(f"sealed/patches/{rel}: not in the patch log")
        elif log[rel].get("sha256") != h:
            problems.append(f"sealed/patches/{rel}: hash {h} differs from the logged {log[rel].get('sha256')}")
        elif log[rel].get("replaces") not in BUNDLE_FILES:
            problems.append(f"sealed/patches/{rel}: 'replaces' must name a bundle file, got {log[rel].get('replaces')!r}")
    for rel in log:
        if rel not in present:
            problems.append(f"sealed/patches/{rel}: logged but missing")
    return problems


def effective_path(sealed_dir, rel: str) -> Path:
    """The overlay: the logged, hash-verified patch that replaces `rel`, else the original bundle file. The original is
    never edited, so the bundle hash stays what the lock committed to."""
    root = Path(sealed_dir); log = patch_log(root)
    for prel, entry in log.items():
        p = root / "patches" / prel
        if entry.get("replaces") == rel and p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == entry.get("sha256"):
            return p
    return root / rel


def demoted_cells(sealed_dir) -> set:
    return {c for entry in patch_log(sealed_dir).values() for c in entry.get("demotes", [])}


def final_eval_seeds(sealed_dir) -> list:
    return [int(s) for s in json.loads(effective_path(sealed_dir, "final_eval_seeds.json").read_text())]


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
    spec = importlib.util.spec_from_file_location("sealed_h2_family", effective_path(root, "h2/family.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    salt = root / "identity_salt.hex"
    return SealedBundle(h1_prompt=effective_path(root, "h1_prompt.txt").read_text(), h2_module=mod, containment=(root / "h2" / "containment.md").read_text(),
                        final_eval_seeds=final_eval_seeds(root), salt_hex=salt.read_text().strip() if salt.exists() else None,
                        b1_check=json.loads((root / "b1_check.json").read_text()) if (root / "b1_check.json").exists() else {})
```

In `sim/locked.py`, change `seeds`:

```python
def seeds(locked: dict, namespace: str) -> list[int]:
    v = locked["seeds"].get(namespace)
    if v is None and namespace == "final_eval":
        from .registry import SEALED_DIR
        if (SEALED_DIR / "final_eval_seeds.json").exists():
            from .sealed import final_eval_seeds, verify_bundle
            verify_bundle(SEALED_DIR, locked)                 # the seeds count only from a bundle that matches the lock commitment
            return final_eval_seeds(SEALED_DIR)
    if v is None:
        raise ValueError(f"seed namespace {namespace!r} is not available (final-eval seeds are released with the sealed bundle)")
    return [int(s) for s in v]
```

(`sim.registry` imports `sim.locked` nowhere, so the lazy import has no cycle; keep `ValueError` so `train_val` in `scripts/sweep.py` still maps it to `SystemExit`.)

```python
# sim/claimcheck.py
"""The claim predicate and decision rule (spec 8) and the lock, freeze, record, summary, coverage-report, and
proposed-module checks (spec 6 and 12)."""
from __future__ import annotations

import ast
import hashlib
import importlib
import importlib.util
import json
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
ALLOWED_IMPORTS = ("sim.mechanisms.base", "numpy", "scipy", "math", "dataclasses", "typing", "__future__", "itertools", "functools")
FROZEN_MODULES = ("sim.market", "sim.mechanisms.base", "sim.policies.base", "sim.policies.honest", "sim.policies.twin", "sim.metrics", "sim.rng")


@dataclass
class Verdict:
    status: str
    bound: float | None
    side: str | None
    method: str | None
    threshold: float
    n: int
    note: str = ""


def _inc(n: int, note: str, threshold: float = 0.0) -> Verdict:
    return Verdict(INCONCLUSIVE, None, None, None, threshold, n, note)


def _admitted(coverage: dict, stat: str, side: str, level: float, n: int):
    return coverage["admitted_sides"].get(endpoint_key(stat, side, level, n))


def decide(x, stat: str, pass_side: str, level: float, threshold: float, coverage: dict, settings: dict, n: int | None = None) -> Verdict:
    x = np.asarray(x, dtype=float); n = int(x.size if n is None else n)
    if x.size != n or x.size < 2:
        return _inc(n, f"{x.size} observations, expected {n}", threshold)
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
    f = h1_rows.rename(columns={"eval_seed": "seed"}).copy(); f["family"] = "H1"
    return f


def h1_cell_reason(rule: str, h1_summary: dict | None, beta: float) -> str | None:
    if h1_summary is None:
        return "missing"
    cell = h1_summary.get("cells", {}).get(f"{rule}|{beta}")
    if cell is None:
        return "missing"
    return "invalid repetitions" if cell.get("inconclusive") else None


def h1_proposed_reason(proposed: str, h1_summary: dict | None, describe_record: dict | None, beta: float) -> str | None:
    """Ruling D11: comprehension is compared with the minimum of B2's and B3's scores."""
    if describe_record is not None and uses_not_expressible(describe_record):
        return "not expressible"
    if h1_summary is not None:
        comp = h1_summary.get("comprehension", {}); others = [comp[b] for b in BASELINES if b in comp]
        if proposed in comp and others and comp[proposed] < min(others) - 1:
            return "comprehension"
    return h1_cell_reason(proposed, h1_summary, beta)


def required_families(coverage: dict) -> list:
    return ["H2"] + (["H1"] if coverage["consequences"].get("h1") == "confirmatory" else [])


def _rows(df: pd.DataFrame | None, rule: str, beta: float, position: str | None) -> pd.DataFrame:
    if df is None or len(df) == 0:
        return pd.DataFrame()
    d = df[df["rule"] == rule]
    if "beta" in d:
        d = d[np.isclose(d["beta"].astype(float), beta)]
    if position is not None and "position" in d:
        d = d[d["position"] == position]
    return d.sort_values("seed").reset_index(drop=True)


def evaluate_claim(h2: pd.DataFrame | None, h1: pd.DataFrame | None, coverage: dict, locked: dict, proposed: str, h1_summary: dict | None = None,
                   describe_record: dict | None = None, h2_headline: dict | None = None, demoted=frozenset()) -> dict:
    c = locked["claim"]; beta = float(c["beta"]); settings = locked["intervals"]; cons = coverage["consequences"]; headline = h2_headline or {}
    confirmatory = required_families(coverage)
    frames = {"H2": h2, "H1": h1_frame(h1) if h1 is not None else None}
    n_of = {"H2": int(cons["final_eval_n"]) if cons.get("final_eval_n") else None, "H1": int(locked["intervals"]["h1_repetitions"])}
    h1_note = h1_proposed_reason(proposed, h1_summary, describe_record, beta) if "H1" in confirmatory else ("exploratory (proxy bound not admitted)" if h1 is not None else None)
    rl, bl = float(c["rule_level"]), float(c["baseline_level"])

    def blocked(fam: str, rule: str) -> str | None:
        if f"{rule}|{fam}" in demoted:
            return "demoted by a logged repair"
        if fam == "H2" and n_of["H2"] is None:
            return "parametrized bound not admitted at any n"
        if fam == "H1":
            return h1_note if rule == proposed else h1_cell_reason(rule, h1_summary, beta)
        return None

    def rows_for(fam: str, rule: str) -> pd.DataFrame:
        return _rows(frames[fam], rule, beta, headline.get(rule, "median") if fam == "H2" else None)

    rule_clause = {}
    for fam in confirmatory:
        n = n_of[fam] or 0; why = blocked(fam, proposed); d = rows_for(fam, proposed)
        if why is None and len(d) == 0:
            why = "no rows"
        if why is not None:
            v = _inc(n, f"{fam} inconclusive: {why}")
            rule_clause[fam] = {"eff": v, "gain": v, "audit": INCONCLUSIVE, "status": INCONCLUSIVE, "audit_over_sstar_mean": None}
            continue
        eff = decide(d["eff_attack"], "eff", "lower", rl, float(c["eff_min"]), coverage, settings, n)
        gain = decide(d["gain"], "gain", "upper", rl, float(c["gain_max"]), coverage, settings, n)
        audit = PASS if len(d) == n and bool((d["audit_cost_attack"] <= d["budget"] + 1e-9).all()) else FAIL if len(d) == n else INCONCLUSIVE
        rule_clause[fam] = {"eff": eff, "gain": gain, "audit": audit, "status": combine_all([eff.status, gain.status, audit]),
                            "audit_over_sstar_mean": float((d["audit_cost_attack"] / d["sstar"]).mean())}
    baseline_clause = {}
    for B in BASELINES:
        pairs = {}
        for fam in confirmatory:
            n = n_of[fam] or 0; why = blocked(fam, B) or blocked(fam, proposed)
            dB = rows_for(fam, B); dR = rows_for(fam, proposed)
            if why is None and (len(dB) == 0 or len(dR) == 0):
                why = "no rows"
            if why is not None:
                pairs[f"{fam}|loss_diff"] = pairs[f"{fam}|gain"] = _inc(n, f"{fam} inconclusive: {why}")
                continue
            m = dB.merge(dR, on="seed", suffixes=("_B", "_R"))
            ld = (m["eff_clip_B"] - m["eff_attack_B"]) - (m["eff_clip_R"] - m["eff_attack_R"])
            pairs[f"{fam}|loss_diff"] = decide(ld, "loss_diff", "lower", bl, float(c["loss_diff_min"]), coverage, settings, n)
            pairs[f"{fam}|gain"] = decide(dB["gain"], "gain", "lower", bl, float(c["baseline_gain_min"]), coverage, settings, n)
        baseline_clause[B] = {"pairs": pairs, "status": combine_any([v.status for v in pairs.values()])}
    statuses = [v["status"] for v in rule_clause.values()] + [v["status"] for v in baseline_clause.values()]
    return {"claim": combine_all(statuses), "confirmatory": confirmatory, "rule_clause": rule_clause, "baseline_clause": baseline_clause, "h1_note": h1_note,
            "n": {k: v for k, v in n_of.items() if k in confirmatory}, "demoted": sorted(demoted), "proposed": proposed, "beta": beta}


def verdict_json(result: dict) -> dict:
    def conv(v):
        if isinstance(v, Verdict):
            return asdict(v)
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        return v
    return conv(result)


# ---- lock, freeze, record, summary, report, and module checks -----------------------------------------------------------

def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def tree_changes(repo: Path, ref: str, paths=None) -> dict:
    """Working tree against `ref`: {path: 'M' | 'A' | 'D'} (git handles quoting, symlinks, and the index)."""
    out = _git(repo, "diff", "--name-status", "-z", "--no-renames", ref, "--", *(paths or [])).split("\0")
    changes = {}
    for status, path in zip(out[0::2], out[1::2]):
        if status:
            changes[path] = status[0]
    return changes


def allowed(path: str, allow_list) -> bool:
    return any(path == e or (e.endswith("/") and path.startswith(e)) for e in allow_list)


def verify_lock(repo, lock_tag: str, allow_list) -> list:
    words = {"M": "changed", "A": "new tracked file", "D": "deleted"}
    return [f"{path}: {words.get(st, st)} since {lock_tag} and outside the allow-list" for path, st in sorted(tree_changes(Path(repo), lock_tag).items()) if not allowed(path, allow_list)]


def verify_freeze(repo, freeze_tag: str, locked: dict, allow_list) -> list:
    repo = Path(repo); problems = []
    in_tag = {e.split("\t", 1)[1] for e in _git(repo, "ls-tree", "-r", "-z", freeze_tag).split("\0") if e}
    for path in FROZEN_AT_FREEZE:
        if path not in in_tag:
            problems.append(f"{path}: missing from the freeze tag {freeze_tag}")
    changed = tree_changes(repo, freeze_tag, list(FROZEN_AT_FREEZE))
    for path, st in changed.items():
        problems.append(f"{path}: {'deleted' if st == 'D' else 'differs'} since the freeze tag {freeze_tag}")
    sealed = repo / "sealed"
    if not sealed.exists():
        problems.append("sealed/: missing")
    else:
        want = locked.get("sealed_bundle_sha256"); got = bundle_hash(sealed)
        if want != got:
            problems.append(f"sealed/: bundle hash {got} differs from the lock commitment {want}")
        problems += verify_patches(sealed)
    return problems


def verify_records(records, locked: dict, jobs: dict, expected_seeds) -> list:
    """Every held-out record is checked by the sweep's own check_record against the job rebuilt from the lock (params,
    cfg, settings hash, budget, smoke, salt), then for the namespace, the bundle hash, and the exact seed sequence."""
    from scripts.sweep import check_record
    problems = []; n_final = int((locked.get("coverage_consequences") or {}).get("final_eval_n") or 0)
    want_seeds = [int(x) for x in expected_seeds][:n_final]
    for rec in records:
        name = rec.get("spec", {}).get("name", "?")
        job = jobs.get(name)
        if job is None:
            problems.append(f"{name}: no job for this record in the locked manifest"); continue
        try:
            check_record(job, rec)
        except SystemExit as e:
            problems.append(f"{name}: {e}")
        if rec.get("eval_namespace") != "final_eval":
            problems.append(f"{name}: evaluation namespace is {rec.get('eval_namespace')!r}, not final_eval")
        if rec.get("spec", {}).get("family") == "H2" and rec.get("bundle_hash") != locked.get("sealed_bundle_sha256"):
            problems.append(f"{name}: bundle hash differs from the lock commitment")
        seeds = [int(r.get("seed")) for r in rec.get("rows", [])]
        if seeds != want_seeds:
            problems.append(f"{name}: row seeds are not the first {n_final} sealed final-eval seeds in order")
    return problems


def verify_h1_summary(summary: dict, rows: pd.DataFrame, locked: dict, prompt_path, expected_seeds) -> list:
    h = locked["h1"]; problems = []; reps = int(locked["intervals"]["h1_repetitions"]); want = [int(x) for x in expected_seeds][:reps]
    if summary.get("model") != h["model"]:
        problems.append(f"h1 summary: model {summary.get('model')!r} is not the sealed LLM {h['model']!r}")
    if int(summary.get("T", -1)) != int(h["T"]):
        problems.append(f"h1 summary: T = {summary.get('T')}, locked h1.T = {h['T']}")
    if summary.get("eval_namespace") != "final_eval":
        problems.append("h1 summary: evaluation namespace is not final_eval")
    want_prompt = hashlib.sha256(Path(prompt_path).read_bytes()).hexdigest() if Path(prompt_path).exists() else None
    if summary.get("instructions_sha256") != want_prompt:
        problems.append("h1 summary: the instructions hash is not the sealed prompt's hash")
    if summary.get("calibration_t100_sha256") != (locked.get("calibration") or {}).get("T100", {}).get("sha256"):
        problems.append("h1 summary: the T = 100 calibration hash differs from the lock")
    if summary.get("smoke"):
        problems.append("h1 summary: smoke run")
    if summary.get("partial"):
        problems.append(f"h1 summary: partial cells {summary['partial']}")
    comp = summary.get("comprehension", {})
    if not all(k in comp for k in list(BASELINES) + [r for r in rows["rule"].unique() if r not in BASELINES]):
        problems.append("h1 summary: comprehension scores missing for a rule in the rows")
    for (rule, beta), d in rows.groupby(["rule", "beta"]):
        d = d.sort_values("rep")
        if list(d["rep"]) != list(range(reps)) or [int(x) for x in d["eval_seed"]] != want:
            problems.append(f"h1 rows {rule}|{beta}: repetitions or evaluation seeds are not the first {reps} sealed seeds in order")
        cell = summary.get("cells", {}).get(f"{rule}|{beta}")
        if cell is None or int(d["invalid"].sum()) != int(cell.get("invalid_count", -1)):
            problems.append(f"h1 rows {rule}|{beta}: invalid flags do not match the summary")
    return problems


def verify_coverage_report(path, locked: dict) -> list:
    data = Path(path).read_bytes(); problems = []
    if hashlib.sha256(data).hexdigest() != locked.get("coverage_report_sha256"):
        problems.append("coverage report: hash differs from the lock")
    rep = json.loads(data)
    if rep.get("admission_basis") != "registered" or rep.get("smoke"):
        problems.append("coverage report: not a registered admission")
    names = [c.get("name") for c in rep.get("selection", [])]
    if len(names) != 6 or len(set(names)) != 6 or not all(names):
        problems.append("coverage report: selection is not 6 distinct named cells")
    if rep.get("consequences") != locked.get("coverage_consequences"):
        problems.append("coverage report: consequences differ from the lock")
    return problems


def _snapshot() -> dict:
    """Every loaded sim.* module: module attributes, class attributes, and function internals (code, defaults, dict)."""
    import sys as _sys, types
    out = {}
    def fn_sig(f):
        return (id(getattr(f, "__code__", None)), id(getattr(f, "__defaults__", None)), id(getattr(f, "__kwdefaults__", None)), repr(sorted(getattr(f, "__dict__", {}).keys())))
    def val(v):
        if isinstance(v, (types.FunctionType, types.MethodType, staticmethod, classmethod)):
            return ("fn", fn_sig(getattr(v, "__func__", v)))
        if isinstance(v, (int, float, str, tuple, bool, type(None), frozenset)):
            return ("val", repr(v))
        return ("id", id(v))
    for m, mod in list(_sys.modules.items()):
        if not (m == "sim" or m.startswith("sim.")) or mod is None:
            continue
        for k, v in list(vars(mod).items()):
            if k.startswith("__"):
                continue
            out[(m, k)] = val(v)
            if isinstance(v, type) and getattr(v, "__module__", None) == m:
                for ak, av in list(vars(v).items()):
                    if not ak.startswith("__"):
                        out[(m, f"{k}.{ak}")] = val(av)
    return out


def check_proposed_module(path, repo, params: dict | None = None) -> list:
    """Spec 12: proposed.py imports only sim/mechanisms/base.py (absolute form) and standard numerical libraries, and
    neither importing it nor calling make(params) changes any attribute of a loaded sim.* module (functions compared by
    code, defaults, and dict). A detected change is reported and restored where the original is known."""
    import sys as _sys
    problems = []; src = Path(path).read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and node.level:
            problems.append(f"{Path(path).name}: relative import is not allowed (use absolute imports)"); continue
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        for name in names:
            if not any(name == ok or name.startswith(ok + ".") for ok in ALLOWED_IMPORTS):
                problems.append(f"{Path(path).name}: import of {name!r} is not allowed (only {', '.join(ALLOWED_IMPORTS)})")
    for m in FROZEN_MODULES + ("sim.mechanisms.posted", "sim.mechanisms.posted_audit", "sim.mechanisms.second_score"):
        importlib.import_module(m)
    originals = {(m, k): v for m, mod in list(_sys.modules.items()) if (m == "sim" or m.startswith("sim.")) and mod is not None for k, v in list(vars(mod).items())}
    class_originals = {(m, f"{k}.{ak}"): av for (m, k), v in originals.items() if isinstance(v, type) and getattr(v, "__module__", None) == m for ak, av in list(vars(v).items())}
    before = _snapshot()
    spec = importlib.util.spec_from_file_location("proposed_under_check", path); mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        if params is not None and callable(getattr(mod, "make", None)):
            mod.make(dict(params))
    except Exception as e:                                        # an import or factory error is a problem, not a crash of the checker
        problems.append(f"{Path(path).name}: import or make() failed: {e!r}")
    after = _snapshot()
    for key in sorted(set(before) | set(after), key=str):
        if before.get(key) != after.get(key):
            m, k = key; problems.append(f"{m}.{k}: changed by {Path(path).name}")
            if "." in k and (m, k) in class_originals:
                cls, attr = k.split(".", 1); setattr(originals[(m, cls)], attr, class_originals[(m, k)])   # a replaced class attribute is restored
            elif "." not in k and (m, k) in originals:
                setattr(_sys.modules[m], k, originals[(m, k)])    # a replaced module attribute is restored
            elif "." not in k and k in vars(_sys.modules[m]):
                delattr(_sys.modules[m], k)                       # an attribute added by the module is removed
            # a changed class attribute or function internal cannot be restored from a snapshot of ids: the report is the
            # guarantee, and check_claim.py refuses the run
    return problems
```

```python
# scripts/check_claim.py
"""Evaluate the claim predicate (spec 8). Confirmatory mode verifies the lock and freeze tags, the proposed module, the
coverage report, every record, and the H1 summary before reading a number (spec 6); --verify-only stops after the
tree, module, and report checks. Synthetic mode (--synthetic, CSV inputs) runs the predicate alone for tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import read_dir  # noqa: E402
from sim.claimcheck import (check_proposed_module, evaluate_claim, verdict_json, verify_coverage_report, verify_freeze, verify_h1_summary, verify_lock,  # noqa: E402
                            verify_records)
from sim.coverage import load_report  # noqa: E402
from sim.locked import load_locked, settings_hash  # noqa: E402
from sim.registry import PROPOSED_MODULE, SEALED_DIR, proposed_params  # noqa: E402
from sim.sealed import demoted_cells, effective_path, final_eval_seeds  # noqa: E402


def h2_from_sweep(sweep_out: Path) -> tuple[pd.DataFrame, list, dict]:
    recs = read_dir(sweep_out / "evaluate"); rows = []; records = []
    for rec in recs.values():
        if rec["spec"]["section"] == "heldout" and rec["spec"]["family"] == "H2":
            records.append(rec); rows += rec["rows"]
    head = json.loads((sweep_out / "headline.json").read_text()) if (sweep_out / "headline.json").exists() else {}
    headline = {k.split("/")[0]: v["headline"] for k, v in head.items() if k.endswith("/H2")}
    return pd.DataFrame(rows), records, headline


def refuse(problems: list) -> None:
    for p in problems:
        print("REFUSED: " + p, file=sys.stderr)
    sys.exit(2)


def heldout_jobs(locked: dict, calibration: str, tuned_dir: Path) -> dict:
    """The jobs of every held-out cell, rebuilt from the lock exactly as the sweep builds them (the record check compares
    params, cfg, settings hash, budget, smoke flag, and salt hash against these)."""
    from scripts.sweep import job_for, load_params
    from sim.calibrate import load_calibration
    from sim.locked import market_config_from_locked
    from sim.manifest import enumerate_manifest
    from sim.registry import available_rules
    from sim.schedule import budget_from_locked
    cal = load_calibration(calibration); base = market_config_from_locked(locked); b = budget_from_locked(locked); rules = available_rules()
    params = {r: load_params(r, tuned_dir, False, cal.market_key, settings_hash(locked), cal.seeds) for r in rules}
    jobs = {}
    for spec in enumerate_manifest(locked, rules, budget=b):
        if spec.section == "heldout":
            jobs[spec.name] = dict(job_for(spec, locked, cal, base, params[spec.rule], b, False), eval_namespace="final_eval")
    return jobs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true"); ap.add_argument("--verify-only", dest="verify_only", action="store_true")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--sweep-out", dest="sweep_out", default=None); ap.add_argument("--h2-rows", dest="h2_rows", default=None)
    ap.add_argument("--h1-dir", dest="h1_dir", default=None); ap.add_argument("--h1-rows", dest="h1_rows", default=None); ap.add_argument("--h1-summary", dest="h1_summary", default=None)
    ap.add_argument("--coverage-report", dest="coverage_report", default="experiments/coverage_report.json")
    ap.add_argument("--proposed", required=True); ap.add_argument("--proposed-describe", dest="proposed_describe", default=None)
    ap.add_argument("--verify-lock", dest="verify_lock", default=None); ap.add_argument("--verify-freeze", dest="verify_freeze", default=None)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--calibration", default=None)
    ap.add_argument("--out", default="results/verdict.json")
    a = ap.parse_args()
    lk = load_locked(); repo = Path(a.repo); problems = []
    if not a.synthetic:
        if not a.verify_lock or (not a.verify_only and not a.verify_freeze):
            refuse(["confirmatory mode needs --verify-lock TAG and --verify-freeze TAG (or --verify-only with --verify-lock); pass --synthetic for CSV inputs"])
        problems += verify_lock(repo, a.verify_lock, lk["allow_list"])
        if a.verify_freeze:
            problems += verify_freeze(repo, a.verify_freeze, lk, lk["allow_list"])
        if PROPOSED_MODULE.exists():
            problems += check_proposed_module(PROPOSED_MODULE, repo, params=proposed_params().get("best_params") if a.verify_freeze else None)
        if Path(a.coverage_report).exists():
            problems += verify_coverage_report(a.coverage_report, lk)
        elif not a.verify_only:
            problems.append(f"coverage report {a.coverage_report} not found")
        if problems:
            refuse(problems)
        if a.verify_only:
            print("verified: tree, proposed module, coverage report"); return
        if a.h2_rows or a.h1_rows:
            refuse(["CSV inputs are for synthetic tests; pass --synthetic"])
        if not (a.sweep_out and a.calibration and a.tuned_dir and a.proposed_describe):
            refuse(["confirmatory mode needs --sweep-out DIR --calibration PATH --tuned-dir DIR --proposed-describe PATH"])
    h2 = h1 = None; h1_summary = None; headline = {}; demoted = set()
    if a.sweep_out:
        h2, records, headline = h2_from_sweep(Path(a.sweep_out))
        expected = final_eval_seeds(SEALED_DIR)
        jobs = heldout_jobs(lk, a.calibration, Path(a.tuned_dir))
        problems += verify_records(records, lk, jobs, expected)
        demoted = demoted_cells(SEALED_DIR)
    elif a.h2_rows:
        h2 = pd.read_csv(a.h2_rows)
    if a.h1_dir:
        d = Path(a.h1_dir); h1 = pd.read_csv(d / "h1_rows.csv"); h1_summary = json.loads((d / "h1_summary.json").read_text())
        problems += verify_h1_summary(h1_summary, h1, lk, effective_path(SEALED_DIR, "h1_prompt.txt"), final_eval_seeds(SEALED_DIR))
    elif a.h1_rows:
        h1 = pd.read_csv(a.h1_rows); h1_summary = json.loads(Path(a.h1_summary).read_text()) if a.h1_summary else None
    if problems:
        refuse(problems)
    cov = load_report(a.coverage_report)
    rec = yaml.safe_load(Path(a.proposed_describe).read_text()) if a.proposed_describe else None
    res = evaluate_claim(h2, h1, cov, lk, a.proposed, h1_summary=h1_summary, describe_record=rec, h2_headline=headline, demoted=demoted)
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

```python
# scripts/lock.py
"""Write the lock-time blocks into experiments/locked.yaml (spec 6) after validating their inputs, and print the tag
commands; --check verifies every written value against its file."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sim.locked import settings_hash  # noqa: E402

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(a, lk: dict, cal: dict, cal100: dict, cov: dict) -> list:
    problems = []
    if int(cal.get("T", -1)) != int(lk["market"]["T"]):
        problems.append(f"--calibration has T = {cal.get('T')}, the locked market T is {lk['market']['T']}")
    if int(cal100.get("T", -1)) != int(lk["h1"]["T"]):
        problems.append(f"--calibration-t100 has T = {cal100.get('T')}, locked h1.T is {lk['h1']['T']}")
    if cov.get("admission_basis") != "registered" or cov.get("smoke"):
        problems.append("coverage report: not a registered admission (smoke run?)")
    if len(cov.get("selection", [])) != 6:
        problems.append("coverage report: selection is not 6 cells")
    trials = int(lk["intervals"]["joint_trials"])
    for n, attempts in (cov.get("fixture_and_power", {}).get("per_n") or {}).items():
        if any(int(att.get("fixture", {}).get("trials", 0)) != trials for att in attempts):
            problems.append(f"coverage report: the joint fixture at n = {n} did not run {trials} trials")
    if "consequences" not in cov:
        problems.append("coverage report: no consequences")
    for name, v in (("--bundle-hash", a.bundle_hash), ("--salt-hash", a.salt_hash)):
        if v is None or not HEX64.match(v):
            problems.append(f"{name} is required and must be 64 hex characters")
    names = [c.get("name") for c in cov.get("selection", [])]
    if len(set(names)) != len(names) or not all(names):
        problems.append("coverage report: selection names must be present and distinct")
    cons = cov.get("consequences") or {}
    if not {"h1", "parametrized", "final_eval_n"} <= set(cons):
        problems.append("coverage report: consequences incomplete")
    per_n = (cov.get("fixture_and_power") or {}).get("per_n") or {}
    if not {"10", "20"} <= set(per_n) or any(not attempts for attempts in per_n.values()):
        problems.append("coverage report: fixture and power results missing for n = 10 or n = 20")
    for M, chk in ((cov.get("fixture_and_power") or {}).get("threshold_check") or {}).items():
        if not chk or any(not v.get("pass_") for v in chk.values()):
            problems.append(f"coverage report: the threshold cross-check at M = {M} did not pass")
    if cov.get("partial") or any(not r.get("per_n") for r in (cov.get("cells") or {}).values()):
        problems.append("coverage report: partial run")
    if a.pilot is None and a.cost_cap_usd is None:
        problems.append("a cost cap is required: --pilot PILOT.json (ceil of projected_cost_usd) or --cost-cap-usd X")
    if a.cost_cap_usd is not None and not (math.isfinite(a.cost_cap_usd) and a.cost_cap_usd > 0):
        problems.append("--cost-cap-usd must be a finite positive number")
    if a.pilot is not None:
        pilot = json.loads(Path(a.pilot).read_text())
        if not pilot.get("complete") or int(pilot.get("calls", 0)) < 200 or pilot.get("backend") != "anthropic":
            problems.append("--pilot must be a complete Anthropic pilot of at least 200 calls")
        if not (isinstance(pilot.get("projected_cost_usd"), (int, float)) and math.isfinite(pilot["projected_cost_usd"]) and pilot["projected_cost_usd"] > 0):
            problems.append("--pilot has no finite positive projected cost")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", default="experiments/locked.yaml"); ap.add_argument("--tuned-dir", dest="tuned_dir", required=True)
    ap.add_argument("--calibration", required=True); ap.add_argument("--calibration-t100", dest="calibration_t100", required=True)
    ap.add_argument("--coverage-report", dest="coverage_report", required=True); ap.add_argument("--fixture", default="experiments/comprehension_fixture.yaml")
    ap.add_argument("--bundle-hash", dest="bundle_hash", default=None); ap.add_argument("--salt-hash", dest="salt_hash", default=None)
    ap.add_argument("--pilot", default=None); ap.add_argument("--cost-cap-usd", dest="cost_cap_usd", type=float, default=None)
    ap.add_argument("--date", default="2026-10-28"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    path = Path(a.locked); lk = yaml.safe_load(path.read_text()); before = settings_hash(lk)
    tuned = {r: sha(Path(a.tuned_dir) / f"tuned_{r}.json") for r in ("B1", "B2", "B3")}
    cal = json.loads(Path(a.calibration).read_text()); cal100 = json.loads(Path(a.calibration_t100).read_text()); cov = json.loads(Path(a.coverage_report).read_text())
    new = {"version": f"locked-{a.date}", "tuned": tuned,
           "calibration": {**cal, "sha256": sha(a.calibration), "T100": {**cal100, "sha256": sha(a.calibration_t100)}},
           "coverage_report_sha256": sha(a.coverage_report), "coverage_consequences": cov.get("consequences"), "comprehension_fixture_sha256": sha(a.fixture)}
    if a.check:
        a.bundle_hash = a.bundle_hash or lk.get("sealed_bundle_sha256"); a.salt_hash = a.salt_hash or lk.get("identity_salt_sha256")
        a.cost_cap_usd = a.cost_cap_usd if (a.cost_cap_usd is not None or a.pilot) else lk.get("h1", {}).get("cost_cap_usd")
        problems = validate(a, lk, cal, cal100, cov)                   # the same validation as at write time
        problems += [f"{k}: {lk.get(k)!r} != {v!r}" for k, v in new.items() if k != "version" and lk.get(k) != v]
        problems += [f"tuned_{r}.json hash differs from the lock" for r in tuned if (lk.get("tuned") or {}).get(r) != tuned[r]]
        if lk.get("h1", {}).get("cost_cap_usd") is None:
            problems.append("h1.cost_cap_usd is not set")
        if problems:
            print("\n".join(problems)); sys.exit(1)
        print("lock-time blocks match their files"); return
    problems = validate(a, lk, cal, cal100, cov)
    if problems:
        sys.exit("\n".join("REFUSED: " + p for p in problems))
    cap = a.cost_cap_usd
    if a.pilot is not None:
        pilot = json.loads(Path(a.pilot).read_text())
        cap = float(math.ceil(float(pilot["projected_cost_usd"])))
    lk.update(new); lk["h1"]["cost_cap_usd"] = cap; lk["sealed_bundle_sha256"] = a.bundle_hash; lk["identity_salt_sha256"] = a.salt_hash
    if settings_hash(lk) != before:
        sys.exit("REFUSED: the lock-time blocks changed the settings hash; nothing written")
    path.write_text(yaml.safe_dump(lk, sort_keys=False, default_flow_style=None, width=120))
    print(f"wrote {path}\n")
    print(f"git add {path} && git commit -S -m 'lock: {a.date}' && git tag -s lock-{a.date} -m 'Touchstone lock {a.date}' && git push origin main lock-{a.date}")
    print("then post the tag hash to the public timestamp (OSF or AsPredicted) the same day")


if __name__ == "__main__":
    main()
```

`yaml.safe_dump` drops the comments in `locked.yaml`; that is acceptable at the lock (the tag fixes the bytes) and the ledger records it.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_claimcheck.py tests/test_sealed.py tests/test_lock_script.py -v`
Expected: PASS (13 tests).

- [ ] **Step 5: Run the verify-only check on the current tree against a throwaway tag**

```bash
git tag lock-candidate && uv run python scripts/check_claim.py --verify-only --verify-lock lock-candidate --proposed R; git tag -d lock-candidate
```
Expected: `verified: tree, proposed module, coverage report` and exit 0 (no proposed module and no coverage report exist yet, so those two checks are skipped by the verify-only path; the tree check passes).

- [ ] **Step 6: Commit**

```bash
git add sim/claimcheck.py sim/sealed.py sim/locked.py scripts/check_claim.py scripts/lock.py tests/test_claimcheck.py tests/test_sealed.py tests/test_lock_script.py
git commit -m "feat: claim predicate with required families, headline positions, demotions, and the decision rule; lock, freeze, record, summary, report, and proposed-module checks; lock script with input validation; sealed bundle loader and final-eval seed fallback"
```

---

### Task 8: Figures 1 and 2

**Files:**
- Create: `scripts/plot.py`
- Test: `tests/test_plot.py`

**Interfaces:**
- Consumes: the sweep's evaluate records (`<out>/evaluate/<cell>.json`, each with `rows` carrying `ROW_FIELDS` plus `meta_of` fields and `params` with `tol`), `percentile_bootstrap` (Task 2), `locked["intervals"]`, `locked["market"]["sigma"]`.
- Produces: `figure_frames(sweep_out: Path, locked: dict, coverage: dict | None = None, h1_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]`: `fig1` with columns `rule, family, beta, position, audit_spend, gain_mean, gain_upper, bound_method, n_seeds, honest_failure_rate` (one row per (rule, family, beta): at the headline beta the position named in `<out>/headline.json` for that rule and family, else `median`, which is the schedule's position for every other beta; `audit_spend = mean(audit_spend_attack)`; `gain_upper` the one-sided upper 95% bound by the method the coverage report admitted at this sample size (`coverage["method_at_n"][str(n_seeds)]`; `percentile` when no report is given; `NaN` with `bound_method = "none"` when the report admits nothing at that n); `honest_failure_rate = Phi(-tol / sigma)` from the record's `params["tol"]`, `0.0` for a rule without `tol`), plus one row per H1 cell from `<h1_dir>/h1_rows.csv` when given (`family = "H1"`, `gain` from the rows, `audit_spend = mean(audit_cost_attack / sstar)`), and `fig2` with columns `rule, family, beta, audit_spend, eff_honest, eff_ref, eff_clip, eff_attack` (means over seeds; for H1 rows `eff_honest` is `NaN` and `eff_ref` is the rows' `eff_ref`); `draw(fig1, fig2, out_dir) -> list[Path]` writing `figure1_gain_vs_audit.png` (one panel per family, one line per rule, mean with the bound as a lighter line, the honest failure rate in each rule's legend label) and `figure2_efficiency_quadruple.png` (one panel per rule, four lines per family); the CLI `--sweep-out DIR --out DIR [--coverage-report PATH] [--h1-dir DIR]` writes both PNGs and `figure_data.csv`.

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
    from sim.coverage import ENDPOINTS, endpoint_key
    out = fake_sweep(tmp_path); lk = load_locked()
    f1, f2 = figure_frames(out, lk)
    assert len(f1) == 8 and set(f1.rule) == {"B1", "B2"} and (f1.gain_upper >= f1.gain_mean).all() and (f1.n_seeds == 20).all() and (f1.bound_method == "percentile (nominal)").all()
    cov = {"method_at_n": {"10": "t", "20": "studentized", "40": None}, "admitted_sides": {endpoint_key(s, side, lv, 20): "studentized" for s, side, lv in ENDPOINTS}}
    g1, _ = figure_frames(out, lk, coverage=cov)
    assert (g1.bound_method == "studentized").all() and not np.allclose(g1.gain_upper, f1.gain_upper)
    none, _ = figure_frames(out, lk, coverage={"method_at_n": {"20": None}, "admitted_sides": {}})
    assert (none.bound_method == "none").all() and none.gain_upper.isna().all()
    (out / "headline.json").write_text(json.dumps({"B2/D1": {"gain_train": {}, "headline": "high"}}))
    (out / "evaluate" / "B2_D1_beta0.05_rho0.5_high_development.json").write_text(
        (out / "evaluate" / "B2_D1_beta0.05_rho0.5_median_development.json").read_text().replace('"position": "median"', '"position": "high"').replace("_median_", "_high_"))
    h1, _ = figure_frames(out, lk)
    row = h1[(h1.rule == "B2") & (h1.family == "D1")]
    assert set(row[row.beta == 0.05].position) == {"high"} and set(row[row.beta == 0.02].position) == {"median"}    # headline position only at the headline beta
    h1dir = tmp_path / "h1"; h1dir.mkdir()
    pd.DataFrame({"rule": ["B2"] * 10, "beta": 0.05, "rep": range(10), "eval_seed": range(10), "sstar": 5.0, "gain": 0.3, "eff_attack": 0.9, "eff_clip": 0.92,
                  "eff_ref": 0.95, "audit_cost_attack": 0.1, "budget": 0.25, "invalid": 0}).to_csv(h1dir / "h1_rows.csv", index=False)
    with_h1, f2h = figure_frames(out, lk, h1_dir=h1dir)
    h1row = with_h1[with_h1.family == "H1"].iloc[0]
    assert (with_h1.family == "H1").sum() == 1 and h1row.n_seeds == 10 and h1row.bound_method == "t (nominal)" and f2h[f2h.family == "H1"].eff_honest.isna().all()
    from sim.intervals import t_bound
    assert h1row.gain_upper == pytest_approx(t_bound(np.full(10, 0.3), "upper", 0.95).value)
    b2 = f1[f1.rule == "B2"].iloc[0]; assert b2.honest_failure_rate == pytest_approx(stats.norm.cdf(-0.12 / lk["market"]["sigma"]))
    assert f1[f1.rule == "B1"].honest_failure_rate.eq(0.0).all()
    assert len(f2) == 8 and {"eff_honest", "eff_ref", "eff_clip", "eff_attack", "audit_spend"} <= set(f2.columns)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "plot.py"), "--sweep-out", str(out), "--out", str(tmp_path / "figs"), "--h1-dir", str(h1dir)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "figs" / "figure1_gain_vs_audit.png").stat().st_size > 1000 and (tmp_path / "figs" / "figure2_efficiency_quadruple.png").exists()
    assert len(pd.read_csv(tmp_path / "figs" / "figure_data.csv")) == 9


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
from sim.coverage import load_report  # noqa: E402
from sim.intervals import bound  # noqa: E402
from sim.locked import load_locked  # noqa: E402


def _upper(g: np.ndarray, iv: dict, coverage: dict | None, family: str) -> tuple[float, str]:
    """The upper 95% bound by the admitted method at this sample size; without a coverage report the nominal method of
    spec 8 (the t bound for H1, the percentile bootstrap for parametrized families), labeled 'nominal'."""
    n = int(len(g))
    if coverage is None:
        method = "t" if family == "H1" else "percentile"; label = f"{method} (nominal)"
    else:
        method = coverage.get("method_at_n", {}).get(str(n)); label = method
    if method is None or n < 2:
        return float("nan"), "none"
    return float(bound(method, g, "upper", 0.95, iv).value), label


def figure_frames(sweep_out: Path, locked: dict, coverage: dict | None = None, h1_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    sweep_out = Path(sweep_out); iv = locked["intervals"]; sigma = float(locked["market"]["sigma"]); bh = float(locked["beta_headline"])
    headline = json.loads((sweep_out / "headline.json").read_text()) if (sweep_out / "headline.json").exists() else {}
    f1, f2 = [], []
    for p in sorted((sweep_out / "evaluate").glob("*.json")):
        rec = json.loads(p.read_text()); spec = rec["spec"]
        if spec["section"] not in ("development", "heldout"):
            continue
        want = headline.get(f"{spec['rule']}/{spec['family']}", {}).get("headline", "median") if float(spec["beta"]) == bh else "median"
        if spec["position"] != want:
            continue
        df = pd.DataFrame(rec["rows"]); tol = rec.get("params", {}).get("tol"); g = df["gain"].to_numpy(dtype=float)
        upper, method = _upper(g, iv, coverage, spec["family"])
        base = {"rule": spec["rule"], "family": spec["family"], "beta": float(spec["beta"]), "position": spec["position"], "audit_spend": float(df["audit_spend_attack"].mean())}
        f1.append({**base, "gain_mean": float(g.mean()), "gain_upper": upper, "bound_method": method, "n_seeds": int(len(g)),
                   "honest_failure_rate": float(stats.norm.cdf(-float(tol) / sigma)) if tol is not None else 0.0})
        f2.append({**base, **{k: float(df[k].mean()) for k in ("eff_honest", "eff_ref", "eff_clip", "eff_attack")}})
    if h1_dir is not None and (Path(h1_dir) / "h1_rows.csv").exists():
        h1 = pd.read_csv(Path(h1_dir) / "h1_rows.csv")
        for (rule, beta), df in h1.groupby(["rule", "beta"]):
            g = df["gain"].to_numpy(dtype=float); upper, method = _upper(g, iv, coverage, "H1")
            base = {"rule": rule, "family": "H1", "beta": float(beta), "position": "median", "audit_spend": float((df["audit_cost_attack"] / df["sstar"]).mean())}
            f1.append({**base, "gain_mean": float(g.mean()), "gain_upper": upper, "bound_method": method, "n_seeds": int(len(g)), "honest_failure_rate": float("nan")})
            f2.append({**base, "eff_honest": float("nan"), "eff_ref": float(df["eff_ref"].mean()), "eff_clip": float(df["eff_clip"].mean()), "eff_attack": float(df["eff_attack"].mean())})
    return pd.DataFrame(f1), pd.DataFrame(f2)


def draw(fig1: pd.DataFrame, fig2: pd.DataFrame, out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True); paths = []
    fams = sorted(fig1.family.unique()); fig, axes = plt.subplots(1, max(len(fams), 1), figsize=(5 * max(len(fams), 1), 4), squeeze=False)
    for ax, fam in zip(axes[0], fams):
        d = fig1[fig1.family == fam]
        for rule, g in d.groupby("rule"):
            g = g.sort_values("audit_spend")
            label = f"{rule} (honest failure rate {g.honest_failure_rate.iloc[0]:.3f})" if np.isfinite(g.honest_failure_rate.iloc[0]) else rule
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
    ap.add_argument("--coverage-report", dest="coverage_report", default=None); ap.add_argument("--h1-dir", dest="h1_dir", default=None)
    a = ap.parse_args(); lk = load_locked()
    f1, f2 = figure_frames(Path(a.sweep_out), lk, coverage=load_report(a.coverage_report) if a.coverage_report else None, h1_dir=Path(a.h1_dir) if a.h1_dir else None)
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
- Create: `docs/custodian.md`, `docs/lock-runbook.md`, `scripts/pod_setup.sh`
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
2. **What to produce**, the bundle layout, exactly the files `sim/sealed.py::BUNDLE_FILES` expects: `sealed/README.md` (what the bundle contains and the access log), `sealed/h1_prompt.txt` (the H1 system prompt: it replaces the development `ACTOR_INSTRUCTIONS` in `sim/llm_actor.py` through `scripts/h1.py --prompt`, and because the prompt is part of every cache key, H1 runs with it never replay a development response; its H1 cache lives under `experiments/cache/h1/<backend>/`, never under `sealed/`; it must describe the provider role, the schema, and the goal, and must not name any rule), `sealed/h2/family.py` (a module defining `H2`, an instance of `sim.policies.families.Family` with knob domains, a claim map that permits claims below effort, the binary `clip` knob so that H2 contains its twin by construction, `registered_starts`, `exact_key`, and `knob_key` as in `experiments/families.md`; and `CONTAINMENT`, a string), `sealed/h2/containment.md` (whether H2 contains D2, is contained by it, or is non-nested, and which observation or memory it uses that D2 cannot; if H2 contains D2, the embedding function `embed_d2(knobs) -> knobs` in `family.py`), `sealed/final_eval_seeds.json` (a JSON list of at least 40 distinct integers in `[10_000_000, 20_000_000)`, so disjoint from dev-train, dev-val, calibration, and the coverage block `3,000,000` to `6,600,000`; the first 20 or 40 are used, as `coverage_consequences.final_eval_n` says, and the first 10 for H1), `sealed/identity_salt.hex` (32 random bytes as 64 hex characters; its SHA-256 goes into `experiments/locked.yaml` as `identity_salt_sha256` before the lock commit; the file itself stays sealed until the evaluation freeze, when the author exports it as `TOUCHSTONE_IDENTITY_SALT` for the final-eval runs), `sealed/b1_check.json` (the result of running H2 and the H1 harness with the fake backend against B1 only, recorded as pass or fail per check, with the commands used).
3. **The commitment.** Compute `python -c "from sim.sealed import bundle_hash; print(bundle_hash('sealed'))"` on the finished bundle, send the hash and the salt hash to the author for `locked.yaml` (`sealed_bundle_sha256`, `identity_salt_sha256`), keep the bundle outside the repository until the unseal, and keep an access log in `sealed/README.md`.
4. **Checks you run before the lock** (B1 only), each command as written, with your bundle directory exported as `TOUCHSTONE_SEALED_DIR=/path/to/your/sealed` so the frozen registry loads your family without any edit: `uv run pytest tests/test_registry.py` (your family must load as `H2`); `uv run python scripts/calibrate.py --seeds 2 --out /tmp/cal_smoke.json` then `uv run python scripts/h1.py --backend fake-honest --rules B1 --calibration /tmp/cal_smoke.json --calibration-t100 /tmp/cal_smoke.json --smoke --out /tmp/b1 --prompt $TOUCHSTONE_SEALED_DIR/h1_prompt.txt` (the smoke market is built from the T of the T100 calibration; a non-smoke run needs `experiments/calibration.json`, `experiments/calibration_T100.json`, `--tuned-dir experiments/tuned`, and `--max-calls 2000`); one H2 cell against B1 through every stage: `uv run python scripts/sweep.py --stage all --sections heldout --rules B1 --select B1_H2 --calibration /tmp/cal_locked.json --smoke --out /tmp/b1_sweep` where `/tmp/cal_locked.json` is `scripts/calibrate.py --seeds 2` on the locked market (the smoke budget on the locked market is what the plan's own test runs). Use absolute imports in `h2/family.py` (`from sim.policies.families import Family`), never relative ones. Record pass or fail and the commands in `b1_check.json`.
5. **At the unseal (week 5).** The bundle enters the repository under `sealed/`; `scripts/check_claim.py --verify-only --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11 --proposed proposed` checks the tree and the bundle hash; no registration step exists: the frozen registry (`sim/registry.py`) finds `sealed/h2/family.py`, the final-eval seeds, and the prompt by itself. The author then runs the comprehension fixture, H1, H2, and the twins on the frozen rule and the baselines on the final-eval namespace (the run book lists the commands), then `scripts/check_claim.py`.
6. **Repairs.** A repair after the unseal is a complete replacement file under `sealed/patches/` with an entry `{"<patch file>": {"sha256": "<hex>", "replaces": "<bundle file, for example h2/family.py>", "demotes": ["<rule>|<family>", ...]}}` in `sealed/patches/log.json`, written by you, limited to interface errors, logged, and reported; the original bundle is never edited (`bundle_hash` ignores `patches/` and import artifacts), and the frozen code reads the replaced file through `sim.sealed.effective_path`, which applies a patch only when its hash matches the log. A repair that changes any H1 or H2 decision on a dev-val seed demotes the affected cells to exploratory: list them in `demotes`; `scripts/check_claim.py` reads the log and marks them INCONCLUSIVE.
7. **Timeline.** Bundle complete by 2026-10-27; commitment hashes to the author by 2026-10-27 so the lock commit on 2026-10-28 carries them; unseal on 2026-11-12.

`docs/lock-runbook.md`: the ordered commands for the lock day, each exactly as its script's CLI reads them (every command in the run book is executed once in a smoke form by the executor before the commit; the ledger records it). Compute notes at the top: the simulator is branchy single-thread Python, so a GPU does not help and core count does; set `OMP_NUM_THREADS=1` before any multi-worker run; the search manifest splits across machines with `scripts/sweep.py --stage search --shard K/N` (copy the shards' `search/` directories together before the later stages) and the coverage study with `scripts/coverage_study.py --cell i` (six machines, one cell each, about 20 to 40 minutes on a 16-vCPU pod) followed by `--merge` on one; a `scripts/pod_setup.sh` (created in this task: `git clone`, `pip install uv`, `uv sync`, `export OMP_NUM_THREADS=1`) prepares a fresh CPU pod. The commands: `scripts/calibrate.py --out experiments/calibration.json` and `--T 100 --out experiments/calibration_T100.json`; `scripts/tune_baselines.py`; the full `scripts/sweep.py --stage all`; `scripts/coverage_study.py --sweep-out ... --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --register --workers 8` (about a day on 8 cores for the base entry; the conditional n = 40 run starts by itself only when the remedy order reaches it); the two pilots (`scripts/h1.py ... --pilot`); `scripts/lock.py --tuned-dir experiments/tuned --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --coverage-report results/coverage/coverage_report.json --bundle-hash <from the custodian> --salt-hash <from the custodian> --pilot results/pilot_anthropic/pilot_anthropic.json`; `scripts/lock.py ... --check`; `git tag lock-candidate && uv run python scripts/check_claim.py --verify-only --verify-lock lock-candidate --proposed none; git tag -d lock-candidate`; the signed tag; the push; the public timestamp. The freeze day: `git tag -s freeze-2026-11-11`; `uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11 --proposed proposed`. The evaluation: `scripts/sweep.py --stage all --sections heldout --rules B1,B2,B3,proposed --eval-namespace final_eval ...`, `scripts/h1.py --backend anthropic --rules B2,B3,proposed --eval-namespace final_eval --prompt sealed/h1_prompt.txt ...`, then `scripts/check_claim.py --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11 --sweep-out results/final --h1-dir results/h1_final --tuned-dir experiments/tuned --proposed proposed --proposed-describe experiments/proposed_describe.yaml`. The post-lock test that `proposed.py` imports only the base module and mutates nothing runs inside `check_claim.py` (`check_proposed_module`), so no new test file is needed after the lock.

Spec section 14: append an implementation note "Plan 2B" listing rulings D1 to D12 with one sentence each, the coverage manifest figures (base and conditional), the H1 call accounting of ruling D10 (the ten repetitions share the dev-train episodes with a deterministic cached actor), the renderer's location (`sim/describe.py`, not `sim/llm_actor.py` as section 11 says), the known-variance label of the analytic threshold, and the statement that `scripts/plot.py` and `docs/` are outside the predicate.

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

1. **Spec coverage.** 5.4 actor, schema, cache, fallback, invalidity, five-episode procedure, twin, clipped re-run, describe renderer, vocabulary, comprehension fixture, token pilot: Tasks 3, 4, 6. 6 lock contents, allow-list, hash checks after the freeze, repairs, final-eval seeds released with the bundle: Tasks 1, 7, 9. 6.1 bundle contents and the custodian's B1-only check: Task 9 (`docs/custodian.md`) and Task 7 (`sim/sealed.py`). 8 interval algorithms, coverage study (selection, pools, replications, endpoints, thresholds, joint fixture, power, remedies, consequences), claim predicate, decision rule, figures, units: Tasks 2, 5, 7, 8. 11 layout: `llm_actor.py`, `policies/llm.py`, `vocabulary.yaml`, `coverage_study.py`, `plot.py`, `check_claim.py`, `sealed/`: present; `scripts/run.py` is plan 1. 12 tests: LLM replay byte-identical (Task 4), describe-record vocabulary and renderer spy and noninterference (Task 3), lock and freeze hash checks and the new-file refusal (Task 7), `proposed.py` import restriction and frozen-module attribute check (`check_proposed_module`, Task 7, tested on synthetic modules and run by `check_claim.py` on the real one), sealed bundle hash check (Task 7). 13 gate for 10-18 to 10-28: Task 9 step 5. Gaps: the enforcement-matched ablation runs and the bank's post-lock application are plan 2A code paths run post-lock; the held-out family registration in the sweep's table at the unseal is described in `docs/custodian.md` and is a post-lock, allow-listed step.
2. **Placeholders.** None: every step has its code or its exact command; the two documents in Task 9 have their required sections and commands listed; the pilots are the user's step by design. Test names in the Review Focus section exist in their tasks.
3. **Type consistency.** `Bound` fields (Task 2) are read by `covered` (Task 5), `decide` (Task 7), and `_upper` (Task 8) as `value`, `side`, `degenerate`; `endpoint_key` (Task 5) is the key format `check_claim.py` reads from `admitted_sides` (Task 7); `H1_ROW_FIELDS` (Task 4) are the columns `scripts/h1.py` writes (Task 6), `h1_frame` reads (Task 7), and the H1 adapter in `plot.py` reads (Task 8); `H1CellResult.reference.twin_results`, `new_calls_clipped`, `invalid_count`, `inconclusive` are read by `scripts/h1.py`; `BudgetedBackend` forwards `name`, `model`, `instructions`, which `build_payload` reads by attribute; `make_backend(name, locked, instructions)` is called by `scripts/h1.py` with three arguments; `coverage_cells` reads `runs_per_seed` from the selection file that `scripts/coverage_study.py` writes with `--register`; `CoverageCellSpec` is JSON-valued so `ProcessPoolExecutor` can pickle it; `validated_universe` rebuilds jobs with the sweep's own `job_for` and checks records with its `check_record`; `make_rule` and `available_families` (Task 1b) replace `rule_from_params` and `ALL_FAMILIES` in `scripts/sweep.py`, and `scripts/h1.py` and `scripts/coverage_study.py` import them from `sim.registry`; `coverage_consequences` is written by `scripts/lock.py`, read by `train_val` (Task 1) for the final-eval sample size, and compared by `verify_coverage_report` (Task 7); `demoted_cells` (Task 7, `sim/sealed.py`) feeds `evaluate_claim(..., demoted=...)`.
4. **Review Focus.** Every line names its test: 1 and 2 in Task 2; 3 in Task 5 (`test_cell_selection_handles_degenerate_rankings`); 4 and 5 in Task 4; 6 in Tasks 3 and 7; 7 in Task 7.
