# Revision program, operations phase: Implementation Plan (version 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the built and reviewed revision code (main `8569e07`) through design 11 steps 2 to 9 (sealed H4, paid benchmark, comparator selection and tuning, coverage, protocol v2 and lock, block draw, evaluation, report, artifact), with the code those steps still lack.

**Architecture:** Part A builds ten pieces test-first on development data and ends with a whole-branch review; its reviewed head is `code_commit`. Part B is the run book in design order; each operation names its actor (author or executor), commands, entry check, exit check, and stop rule. Every paid run goes through the existing capped pod launcher `results/pods/explore_pod.sh` (local, untracked: USD cap from allocation time, `SCRIPT` and `ROUT` overrides, pull then verified delete). Version 2 answers round 1 (`docs/revision/roster/sol-ops-plan-r1.md`, `astra-ops-plan-r1.md`); the disposition is at the end.

**Tech Stack:** Python 3 with uv, numpy, scipy 1.18.1 (pinned in `uv.lock`), cma, pytest; OpenTimestamps client (`uvx --from opentimestamps-client ots`); Runpod CPU pods via `results/pods/runpod.py`.

**Spec:** `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 6, accepted; "design"). Build plan `docs/superpowers/plans/2026-10-22-revision-build.md` and its ledger `docs/revision/build-ledger-2026-10-22.md` hold the rulings this plan inherits.

## Global Constraints

- No paid API calls of any kind (design 1 non-goals). Paid compute is Runpod CPU pods only, each started through `explore_pod.sh` with a USD cap taken from the budget ledger (Task 4); every pod is deleted, and the deletion verified, once its outputs are pulled.
- Caps (design 8.2): development 12 USD, evaluation 40 USD, benchmark spend counted in development; **the author's approval is required for any recomputed total above 40 USD**. Cut order and stop rules as design 8.2. No paid step after the benchmark runs before the cost decision (Operation 2's exit).
- Development data only until the draw: seeds dev-train 1000-1004, dev-val 2000-2019, calibration 4000-4019, coverage pools in [40,000,000, 60,000,000); root "dev-20261022". Evaluation seeds [30,000,000, 40,000,000) exist only after the draw.
- Frozen files stay byte-identical to `2a288f5` (`tests/test_frozen_files.py`). Registered files of the first evaluation (`experiments/locked.yaml`, `sealed/`, its records) are never changed; `sealed/` is never read.
- **H4 custody.** The sealed Codex session (fresh `gpt-6.1-sol`, high effort, its own clone at `code_commit`, design 5.3) writes, checks, and commits `sealed2/h4/` in that clone; the author keeps the clone outside this repository until the report. No person or agent in this program reads its contents before the report. Permitted access before then is automated only: `scripts/h4_check.py` (inside the sealed session), hashing and copying, and `sim/h4_loader.load` called by `scripts/draw_v2.py --h4-decision` and by `scripts/revision_v2.py` on pods.
- **Two commits and one checkout.** `code_commit` is the frozen code. The protocol commits add only `experiments/v2/`, `experiments/protocol-v2.yaml`, its `.ots` proof, and `docs/`; the signed tag `protocol-v2` points at the commit that holds the upgraded proof (Operation 5). Every evaluation pod, the verification, the report, and the reproduction run from a clean checkout of `protocol-v2`; later commits (ledger, paper) happen elsewhere.
- After the lock, design 9.6: no change to rules, families, seeds, manifest, cuts, or decision rules; orchestration changes go to `docs/revision/operations-ledger.md`.
- Commits unsigned (`git -c commit.gpgsign=false`), ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the author signs commits and every tag. Whole suite: `uv run pytest -q`. Code style as the surrounding code.

## Review Focus

1. **A pod dies, is replaced, or runs another commit.** Rerunning a stage on the same `--out` reuses valid records, recomputes stale ones, and refuses foreign ones (the resume rule); a pod whose checkout is not the protocol tag stops before any episode. Pinned by Task 6 `test_check_commit_refuses_other_head_or_unsigned_tag` and Task 8 `test_verify_stage_runs_no_episode`.
2. **The publication deadline.** Tag, protocol, and upgraded proof public before block H = A + 144; else the draw is kept and every claim is labelled nonconfirmatory (design 7.3). Pinned by Task 7 `test_late_publication_is_nonconfirmatory` and Task 9 `test_nonconfirmatory_draw_has_no_confirmatory_claim`.
3. **H4 fails or differs between pods.** One recorded decision; every pod enforces it; a failure excludes H4 for all and the independently authored part of Q3 is unanswered. Pinned by Task 7 `test_h4_decision_records_exclusion`, Task 8 `test_pods_enforce_the_h4_decision`, Task 9 `test_q3_unanswered_without_h4`.
4. **A cap is hit.** Missing cells are reported, nothing is replaced, and each question whose required cells are missing is unanswered. Pinned by Task 9 `test_missing_cells_make_dependent_questions_unanswered`.
5. **A family's multiplier fails validation.** Only an admitted kappa reaches the protocol; otherwise "no confirmatory decision" with estimates and descriptive intervals. Pinned by Task 3 `test_failed_validation_exports_null` and Task 9 `test_no_kappa_no_decision_but_estimates`.

---

## Part A: missing code (test first, development data, no pods)

### Task 1: H4 session kit

**Files:** Create `docs/revision/h4-brief.md`, `scripts/h4_check.py`, `tests/fixtures/h4_toy/h4/{family.py,containment.md}`, `tests/test_h4_check.py`.

**Interfaces:**
- Consumes: `sim.h4_loader.load`, `bundle_sha`, `_check`, `CHECK_CONSTANTS`; `scripts.revision_v2.market`, `job`, `train_cell`, `eval_cell`, `settings`; `sim.reference.twin_search`, `evaluate_gain`.
- Produces: `load_check(bundle: Path) -> dict` (`{"ok", "problem", "constants": [[200, 10], [100, 20]]}`); `smoke(bundle: Path, rules=("F000", "F111"), markets=("dev0", "dev1"), budget=SMOKE) -> dict` (twin and attack search, gain on dev-val seeds); CLI `h4_check.py --bundle DIR [--smoke]` writes `DIR/h4/check.json` (`{"load", "smoke", "scipy", "commit"}`) last and prints `bundle_sha(DIR)`. Without `--smoke` the smoke evaluation runs at the registered inner budget (design 5.3 "smoke evaluation").
- The brief gives the session only the `Family` interface, `ProviderView`, spec 4.0, the public constants T and L (design 5.1), the exports `make_family(T: int, L: int) -> Family` (name "H4", `clip` last and binary) and `BINARY`, the containment note, the `h4_check.py` command, and the final step: `git add sealed2 && git commit` in its clone and print the commit hash and bundle hash.

- [ ] **Step 1: Failing tests:** `test_toy_bundle_passes_load_and_hash_round_trip` (`main(["--bundle", d, "--smoke"])`; `load(d, bundle_sha(d))` is an `H4Source`; `check.json["load"]["ok"]`), `test_missing_binary_or_wrong_name_fails_load_check`, `test_smoke_touches_development_seeds_only` (`sim.instances.eval_seeds` patched to raise; every seed in `range(1000, 1005)` or `range(2000, 2020)`), `test_check_json_is_inside_the_hash`.
- [ ] **Step 2:** `uv run pytest tests/test_h4_check.py -q` FAILS (no module).
- [ ] **Step 3:** implement (the smoke builds the family from `make_family`, since the loader's hash covers `check.json`).
- [ ] **Step 4:** `uv run pytest tests/test_h4_check.py tests/test_h4_loader.py -q` PASSES.
- [ ] **Step 5:** commit `ops: H4 session kit`.

### Task 2: Tuning on many cores, fixture provenance

**Files:** Modify `scripts/tune_v2.py`, `tests/test_tune_v2.py`.

**Interfaces:**
- Produces: `_tune(rule, specs, markets, out, smoke, workers=1)` scores configurations with `ProcessPoolExecutor(workers)` (inner scores, then the top 2 rechecks), results ordered by grid index so `rank` and ties are unchanged; `fixture_searches(markets, out, cred, smoke, workers=1)` runs markets in parallel and writes `smoke`, `budget`, `markets`, and `commit` into `fixture_cstar_s2.json`; `main` passes `--workers`. `select_comparator` and `tune_system` write `budget_inner`, `budget_full`, `commit` (they already write `smoke`, `markets`).
- [ ] **Step 1: Failing tests:** `test_parallel_tuning_equals_serial` (smoke, `grid_limit=2`, `workers=2` vs 1: identical `scores`, `rechecked`, chosen spec), `test_fixture_file_carries_provenance`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_tune_v2.py -q --runslow` PASSES. **Step 5:** commit `ops: tuning and fixtures use --workers; fixture provenance`.

### Task 3: Coverage on many cores, admitted kappa only

**Files:** Modify `scripts/coverage_v2.py`, `sim/calibration_v2.py` (`build_pool` chunking only), `tests/test_calibration_v2.py`.

**Interfaces:**
- Produces: `coverage_v2.py --pools --market LABEL --workers N` builds one market's pool, its seed range split into `N` chunks run in a process pool and concatenated in seed order (identical bytes to `workers=1`); `--select` and `--validate` read all pools of `--branch`. `coverage.json` per family gains `kappa_effective` = `kappa` when `admitted` is true, else `null`, and `resamples`, `validation_replications`, `endpoints`.
- [ ] **Step 1: Failing tests:** `test_failed_validation_exports_null` (validate patched to `admitted: False`: `kappa_effective is None`, `kappa` kept), `test_pool_by_market_and_workers_equals_serial` (two-market synthetic inputs, 40-seed pools), `test_select_needs_every_branch_market`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_calibration_v2.py -q` PASSES. **Step 5:** commit `ops: coverage pools per market on many cores; kappa_effective from admission only`.

### Task 4: Cost model for cuts and branches, and the budget ledger

**Files:** Modify `scripts/benchmark_v2.py`, `tests/test_benchmark_v2.py`; create `scripts/budget_v2.py`, `tests/test_budget_v2.py`.

**Interfaces:**
- Produces: `cost_table(timings, usd_per_core_hour, cuts=0, h4_excluded=False, markets=("headline", "dev0", "dev1"), branch="three20k", utilisation=0.8)`: cell, reference-menu, doubling, and cross counts come from `manifest_v2.effective(cuts, h4_excluded)`, `doublings()`, and `cross_evaluations()` instead of constants (the defaults reproduce today's 374 / 118 / 132 / 14); configuration-markets scale with `len(markets)`; coverage episodes from `calibration_v2.BRANCHES[branch]`; USD = core-hours / utilisation x rate. `choose(timings, rate) -> dict` returns the design 8.2 decision: development branch (three markets / two markets 20k / two markets 10k / stop) and the smallest `cuts` in 0..4 under the evaluation cap (or stop), with `approval_required`.
- `budget_v2.py`: `docs/revision/budget-ledger.json` holds `{caps, spent: [{op, pod, usd}], planned}`; `cap_for(op: str, estimate_usd: float) -> float` returns `min(estimate x 1.25, remaining in the op's cap)` and refuses when the remainder is below the estimate; CLI `--record OP POD USD`, `--cap OP ESTIMATE`, `--show`.
- [ ] **Step 1: Failing tests:** `test_defaults_reproduce_the_current_table`, `test_cuts_and_branches_change_counts` (cuts 1..4 reduce cells by the manifest's numbers; branch `two10k` halves coverage episodes and scales configuration-markets by 2/3), `test_choose_follows_design_order` (synthetic timings: over the development cap → `two20k`, then `two10k`, then stop; over the evaluation cap → smallest sufficient cut, else stop), `test_cap_for_never_exceeds_the_remainder`, `test_benchmark_spend_counts_in_development`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_benchmark_v2.py tests/test_budget_v2.py -q` PASSES. **Step 5:** commit `ops: cost model aware of cuts, branches, and utilisation; budget ledger with capped pod allocation`.

### Task 5: Staged promotion

**Files:** Create `scripts/promote_v2.py`, `tests/test_promote_v2.py`.

**Interfaces:**
- Produces: `promote_v2.py --kind comparator|system|fixtures|coverage|benchmark --from DIR --to experiments/v2 --markets M [--final]`; each kind is validated and copied on its own, appending `{path: sha256}` to `experiments/v2/promotion.json`; `--final` checks completeness (comparator, four systems, fixtures, coverage, benchmark) and writes `params.json` (`{"cred", "tuned": {name: {"tol", "L"}}}`, the `--params` of `revision_v2.py`).
- Checks: `smoke` false, `commit` equals `code_commit`, markets equal `--markets`; comparator 12 scored and 2 rechecked; each system 16 and 2, ties by grid index, C*-t's `cred` equal to the promoted comparator's; inner budget `(1, 100, 3, 20)` and the locked full budget; fixtures cover every market; coverage `kappa_effective` present per family (null allowed) and, when non-null, `admitted` true with 20,000 validation replications, 9,999 resamples, and the branch's endpoint count; benchmark `smoke` false and its table recomputed equal by `cost_table`.
- [ ] **Step 1: Failing tests** built from the producers' own smoke outputs (`tune_v2.main([... "--smoke"])`, `coverage_v2.main` on synthetic pools) with the flags edited: `test_staged_kinds_promote_independently`, `test_each_refusal` (parametrised over every check), `test_final_needs_all_kinds_and_writes_params`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** commit `ops: staged promotion with validation and a final completeness check`.

### Task 6: Protocol v2 writer and checker

**Files:** Create `scripts/lock_v2.py`, `tests/test_lock_v2.py`, `docs/revision/predictions-v2.md` (template with design 9.7 headings).

**Interfaces:**
- Produces: `build(repo, code_commit, cuts, h4: dict | None, approval: str | None, branch: str, markets: list) -> dict`; `check(repo, protocol) -> list[str]` (every hash re-derived from its file; `cuts` and `branch` equal Task 4's `choose` on the promoted benchmark; `approval` present when `total_usd > 40`); `check_commit(repo) -> None` (clean tree; `git tag -v protocol-v2` succeeds; `HEAD` is the tag's commit; `git diff --name-only code_commit HEAD` lists only the allowed paths; `check` passes). CLI `--write --code-commit SHA --cuts N --branch B --markets M (--h4-commit SHA --h4-sha HEX | --no-h4) --approval TEXT`, `--check`, `--check-commit`.
- Fields: `version: 2`, `code_commit`, `manifest_sha256`, `cuts`, `branch`, `development_markets`, `h4: {commit, bundle_sha256} | null`, `params_sha256`, `promotion_sha256`, `kappa: {Q1, Q4}` (from `kappa_effective`), `coverage_sha256`, `cost: {development_usd, evaluation_usd, total_usd, spent_usd}`, `approval`, `predictions_sha256`, `block: {rule: "H = A + 144", depth: 6, explorers: [blockstream.info, mempool.space]}`, `seeds: {eval_range: [30000000, 40000000], per_market: 200}`, `markets: [headline, fresh0, ..., fresh5]`, `caps: {development: 12, evaluation: 40}`.
- [ ] **Step 1: Failing tests:** `test_build_and_check_round_trip`, `test_check_reports_each_changed_input` (params, coverage, manifest, predictions, promotion, benchmark, each mutated in turn; an expected-hash table written independently in the test), `test_total_above_40_needs_approval`, `test_kappa_comes_from_kappa_effective`, `test_check_commit_refuses_other_head_or_unsigned_tag` (temporary repo with a test signing key: untagged HEAD, lightweight tag, code change after `code_commit`, and dirty tree each refuse; a signed tag on a data-only commit passes).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** commit `ops: protocol v2 writer and checker`.

### Task 7: Draw to instances, and the single H4 decision

**Files:** Create `scripts/draw_v2.py`, `tests/test_draw_v2.py`.

**Interfaces:**
- Consumes: the `block_draw.py` final record (`status`, `height`, `hash`, `anchor`, `headers`, `tips`, `protocol_sha256`) and its verifiers (`check_protocol`, the header-chain and depth checks of `read_final`, re-run offline on the stored headers); `sim.instances.markets`, `eval_seeds`, `identity_salt_hex`, `calibrated`; `sim.records.cfg_to_dict`; `sim.h4_loader.load`.
- Produces: `instances(draw, protocol_bytes, published_height) -> dict` (`root`, `height`, `markets: {label: {stream_index, rejections, cfg, calibrated_cfg}}`, `seeds: {label: [200]}`, `salt_sha256`, `confirmatory`); `h4_decision(bundle: Path | None, protocol) -> dict` (`{loaded, reason, bundle_sha256, h4_excluded}`); CLI `--instances --draw FILE --protocol FILE --published-height N --out DIR` and `--h4-decision --protocol FILE [--bundle DIR] --out DIR` (creates `--out`).
- Checks: `draw["protocol_sha256"]` equals SHA-256 of the protocol bytes; `height` equals anchor height + 144; the stored headers link from A to H + 6 with valid proof of work and A's Merkle root equals the anchor's; `hash` equals the header hash at H and is 64 lowercase hex; both `tips` at least H + 6. `confirmatory` is false when `published_height` is missing or at least H.
- [ ] **Step 1: Failing tests** (synthetic headers from `tests/test_block_draw.py`'s fixtures): `test_instances_follow_generator_and_streams` (a fixed root; labels fresh0..fresh5; a monkeypatched stream limit keeps label order), `test_substituted_draw_is_refused` (another protocol's digest; H != A + 144; a broken header link; a hash mismatch; tips below H + 6: each refuses), `test_late_publication_is_nonconfirmatory`, `test_seeds_equal_an_independent_derivation` (re-derive v_n from the design 7.2 formula in the test; exact equality, disjoint from every reserved range), `test_h4_decision_records_exclusion` (toy bundle with a wrong hash: `loaded` false, `h4_excluded` true).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_draw_v2.py tests/test_block_draw.py tests/test_instances.py -q` PASSES. **Step 5:** commit `ops: draw to instances bound to the protocol; one H4 decision`.

### Task 8: Runner: priority dispatch, read-only verification, H4 decision

**Files:** Modify `scripts/revision_v2.py`, `tests/test_revision_v2.py`.

**Interfaces:**
- Consumes: `sim.manifest_v2.priority(cell)` (needs the cell's `block`); Task 7's `h4.json`.
- Produces: `job()` carries `block` and `priority`; `run(stage, ...)` dispatches in priority tiers 0 to 3, and within a tier keeps the dependency waves (non-X7 searches before the same tier's X7-SC searches; W1 non-X7 before X7; coalition prerequisites before objectives), so no tier-k job runs before every tier-(k-1) job of the stage. New `--stage verify`: for each context, `accept`, then every evaluate, cross, and doubling record checked against its expected stage, provenance, dependency set and hashes, seeds (equal to the instance's), array lengths, and finiteness; it reports missing, stale, and foreign records and never calls a stage body. New `--h4-decision FILE` (required with `--root`): an excluded decision sets `h4_excluded`; a loaded decision requires `--h4`, the same bundle hash, and a successful load, else the run stops before any episode.
- Ruling (accepted by both seats in round 1): priority cannot waive the complete freeze (design 6.4); a context evaluates only after its freeze. Fresh-market pods start before the headline pods, and the headline pods run priority 2 work last.
- [ ] **Step 1: Failing tests:** `test_dispatch_follows_priority_tiers` (`_pool` patched to record order; full params: `cred` and tuned `B3-t`, `R3-t`, `R4-t`, `C*-t`; every tier-0 job, X7-SC included, precedes any tier-1 job), `test_verify_stage_runs_no_episode` (every stage body patched to raise; a complete context verifies; a deleted evaluate record, a stale freeze, and a foreign record are each reported), `test_pods_enforce_the_h4_decision` (excluded decision → manifest without H4 even with `--h4`; loaded decision with a different hash → `SystemExit` before any episode).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_revision_v2.py -q` PASSES. **Step 5:** commit `ops: runner priority tiers, read-only verify stage, enforced H4 decision`.

### Task 9: The report

**Files:** Create `scripts/report_v2.py`, `tests/test_report_v2.py`.

**Interfaces:**
- Consumes: records verified by Task 8's verify stage (the report calls it first and refuses on any problem other than missing cells); `sim.decisions_v2`; `sim.intervals`; the protocol (`kappa`), `instances.json` (`confirmatory`), `h4.json`.
- Produces: `build(out, protocol, instances, h4) -> dict` with `q1`, `q2`, `q3`, `q4`, `secondary`, `doubling`, `missing`, `unanswered`, `confirmatory`; CLI `--out DIR --protocol FILE --instances FILE --h4 FILE --report DIR [--check]` (writes `report.json`, `report.md`; `--check` rebuilds and compares).
- **Question dependencies** (a missing record of any listed cell makes the question unanswered; other questions stay answered): Q1 needs F111, C*, R4, C*/S2 x {D2+H3, X7-SC} on the six fresh markets; Q4 needs F000 and F111 under D2+H3 on each fresh market (a market with a missing cell is "not decided"); Q2 needs the eight factorial cells per market and family and their cross records; Q3 needs each core rule's envelope families, welfare, and coalition cells (H4's part unanswered when `h4.loaded` is false). Search-incomplete labels from doubling checks are reported beside the estimates and do not change decisions (design 6.4 "Doubling results never enter the frozen candidates"; ruling for the reviewers).
- **Q1:** per pair (F111 vs C*, R4 vs C*/S2) and family, six strata = per fresh market the per-seed difference of the two rules' gains; `q1_family(tests, kappa_Q1)`; estimate and the calibrated simultaneous interval at one-sided tails `kappa_Q1 x 0.05/8`; per-market and headline differences with nominal 95 percent intervals, labelled descriptive. **Q4:** per fresh market `p_a = bootstrap_pvalue(g_F000 - g_F111, 0.10, "lower")` under D2+H3 and `p_b = bootstrap_pvalue(eff_F111, 0.90, "lower")`; `q4_markets(pa, pb, kappa_Q4)`; calibrated one-sided lower bounds at `kappa_Q4 x 0.05/6`; wording "replicated on k of 6 sampled markets", failing markets named, "generalisation not established" when any market is not decided. **Q2:** per seed the effect-coded contrasts (P, G, S, PG, PS, GS, PGS, G at P=0 and 1, P at S=0 and 1) over the eight cells' per-seed gains, on the diagonal and on the fixed-attack matrix (per-seed contrast within each attack row, then the mean over the 8 rows), then stratified nominal 95 percent intervals pooled over the six fresh markets; the per-rule bank envelope. **Q3:** per core rule the envelope family (its `envelope` record's choice) with the evaluation gain and interval; W0 and W1 lowest efficiency (winners selected on training seeds), its interval, the attacker's gain (W0: `normalized - profit_ref / (sstar / N)` from the rule's D2+H3 evaluation on the same seeds; W1: the stored constraint) and the W1 constraint interval, or "no feasible candidate found"; coalition G_tot and G_min with `gmin_bounds(member_rows, 0.05)`. **Secondary:** whole systems (B3-t, R3-t, R4-t, C*-t) and the rho = 1 repair cells, descriptive. **Doubling:** every scheduled check's measured changes and label. **Nonconfirmatory draw:** Q1 categories and Q4 passes are printed as descriptive results under the heading "nonconfirmatory (late publication)".
- [ ] **Step 1: Failing tests** with producer-shaped records (written through `revision_v2`'s own record writers on tiny contexts) and independent oracles computed in the test from the per-seed arrays: `test_q1_strata_tails_and_kappa` (a wrong tail or an unused kappa changes the asserted interval), `test_q2_per_seed_contrasts_against_an_oracle`, `test_q3_welfare_gain_and_no_feasible_case`, `test_q4_wording_bounds_and_named_failures`, `test_no_kappa_no_decision_but_estimates`, `test_missing_cells_make_dependent_questions_unanswered` (a missing F111 D2+H3 record leaves Q1, Q2, Q4 for that market and Q3 unanswered as listed, and the rest answered), `test_q3_unanswered_without_h4`, `test_nonconfirmatory_draw_has_no_confirmatory_claim`, `test_report_refuses_foreign_or_stale_records`, `test_check_mode_detects_a_changed_record`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_report_v2.py tests/test_decisions_v2.py -q` PASSES. **Step 5:** commit `ops: report with question dependencies, calibrated and descriptive intervals`.

### Task 10: Artifact assembly, reproduction, check

**Files:** Create `scripts/artifact_v2.py`, `scripts/reproduce.py`, `tests/test_artifact.py`.

**Interfaces:**
- Produces: `artifact_v2.py --assemble --eval DIR --draw DIR --report DIR --h4 DIR --out release/` builds `release/touchstone-v2.tar.gz` (records, draw record with headers, instances, report, the released H4 bundle, promoted inputs, protocol and upgraded proof, paper sources, `uv.lock`, a manifest of SHA-256s) because `results/` is ignored by git; `--check TARBALL` verifies every manifest hash, the tag signature (`git tag -v protocol-v2`), and the freeze records' hashes; `reproduce.py --artifact TARBALL` unpacks into a temporary directory, checks out `protocol-v2` in a fresh clone, runs `report_v2.py --check`, and exits non-zero on any difference.
- [ ] **Step 1: Failing tests:** `test_assemble_and_check_a_synthetic_release`, `test_check_reports_missing_and_changed_files`, `test_reproduce_detects_a_changed_record` (synthetic tiny release with a temporary repo and tag).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_artifact.py -q && uv run pytest -q` PASSES (whole suite). **Step 5:** commit `ops: artifact assembly, reproduction, and check`.

**End of Part A:** Sol high and Astra high review Tasks 1 to 10 to consensus. The reviewed head is `code_commit`.

---

## Part B: operations (design 11 steps 2 to 9)

Each operation is logged in `docs/revision/operations-ledger.md` (date, commit, command, pod ids, USD, outputs and hashes, deviations); every paid pod's spend is recorded with `budget_v2.py --record`.

### Operation 1: H4 sealed session (author)
- [ ] Executor: tag `code_commit` as `h4-base` (author signs); hand over `docs/revision/h4-brief.md`.
- [ ] Author: in a fresh clone at `h4-base`, run the fresh Codex `gpt-6.1-sol` session (high) with the brief; it writes `sealed2/h4/`, runs `scripts/h4_check.py --bundle sealed2`, commits in that clone, and prints the commit and bundle hashes.
- [ ] Author: record both hashes in the ledger; keep the clone outside this repository; do not read the bundle.
- **Exit:** two hashes in the ledger; `git ls-files | grep -c sealed2` is 0 here. **Stop:** if `h4_check` cannot pass before the lock, the protocol records `h4: null` and Q3's independently authored part is unanswered.

### Operation 2: Benchmark and the cost decision
- [ ] Executor: `uv run python scripts/benchmark_v2.py --run --smoke --out results/v2/benchmark_smoke` (wiring only).
- [ ] Executor: one 16-vCPU pod, cap 3 USD from the ledger: `SCRIPT=scripts/benchmark_v2.py ROUT=results/v2/benchmark results/pods/explore_pod.sh <tarball> bench 3 results/v2/benchmark "--run"`; `promote_v2.py --kind benchmark`.
- [ ] Executor: `choose()` on the promoted timings at the pod's measured rate; report branch, cuts, development, evaluation, and total USD. Author: approve in writing when the total exceeds 40 USD (the sentence goes into the protocol). A "stop" from `choose` stops the program for the author.
- **Exit:** the decision and the approval (if needed) in the ledger; no other paid step before this exit.

### Operation 3: Comparator selection, whole-system tuning, fixtures
- [ ] Executor: one pod, `tune_v2.py --select comparator --markets <chosen> --workers <vcpu> --out results/v2/tune_comparator`, cap from `budget_v2.py --cap development <row estimate>`; pull; `promote_v2.py --kind comparator`.
- [ ] Executor: five pods in parallel, `--select B3-t | R3-t | R4-t | C*-t | fixtures --markets <chosen> --comparator experiments/v2/comparator.json --workers <vcpu>`, caps from the ledger; pull; promote each (`--kind system`, `--kind fixtures`).
- **Exit:** promotions recorded; development spend under 12 USD; otherwise stop for the author.

### Operation 4: Coverage check
- [ ] Executor: one pod per branch market, `coverage_v2.py --pools --market <m> --branch <chosen> --inputs experiments/v2 --workers <vcpu> --out results/v2/coverage`; pull the pools together; locally `--select` then `--validate`; `promote_v2.py --kind coverage`; then `promote_v2.py --final` writes `params.json`.
- **Exit:** `kappa_effective` for Q1 and Q4 (number or null).

### Operation 5: Protocol v2, review, lock
- [ ] Executor: draft `docs/revision/predictions-v2.md` (design 9.7 directions against development results); `lock_v2.py --write ...`; `lock_v2.py --check`.
- [ ] Sol high and Astra high review protocol and predictions to consensus.
- [ ] Author, in order: `git commit -S` (protocol and predictions); `ots stamp experiments/protocol-v2.yaml`; push the commit; `ots upgrade` until the proof holds a Bitcoin attestation; `git commit -S` the upgraded proof; `git tag -s protocol-v2` on that commit; push the commit and tag; record the tip height at the push (`published_height`).
- [ ] Executor: a fresh clean clone at `protocol-v2` (`results/v2/eval-checkout`); `lock_v2.py --check-commit` there.
- **Exit:** `check-commit` passes; the push height is below A + 144. **Stop:** a push at or after H keeps the draw, labelled nonconfirmatory (design 7.3).

### Operation 6: Draw, instances, H4 decision
- [ ] Executor (eval checkout): `mkdir -p results/v2/draw && uv run python scripts/block_draw.py --ots experiments/protocol-v2.yaml.ots --protocol experiments/protocol-v2.yaml --out results/v2/draw/draw.json`.
- [ ] Executor: `draw_v2.py --instances --draw results/v2/draw/draw.json --protocol experiments/protocol-v2.yaml --published-height <N> --out results/v2/draw`.
- [ ] Executor: one small pod (cap 1 USD) with the author's custody copy uploaded unopened: `draw_v2.py --h4-decision --protocol experiments/protocol-v2.yaml --bundle <upload> --out results/v2/draw`; pull `h4.json`.
- **Exit:** `instances.json` (six fresh labels, 200 seeds each, `confirmatory`), `h4.json`.

### Operation 7: Evaluation on pods
- [ ] Executor, per pod before any stage (eval checkout copied): `lock_v2.py --check-commit`; `params.json`, `h4.json`, and (when loaded) the bundle present; `OMP_NUM_THREADS=1`.
- [ ] Executor: six fresh-market pods first (`--markets freshK`), then two headline pods by context (`--select 'headline@rho0.2|*'`, `--select 'headline@rho1|*'`); each runs `search`, `reference`, `dependent`, `freeze`, `evaluate`, `cross`, `doubling` on one `--out` with `revision_v2.py --stage S --root <hash> --params experiments/v2/params.json --cuts <c> --h4-decision results/v2/draw/h4.json [--h4 DIR --h4-sha HEX] --workers <vcpu>`; caps from `budget_v2.py --cap evaluation <estimate>` so the total never passes 40 USD.
- [ ] Executor: pull every `--out` into `results/v2/eval/`; `revision_v2.py --stage verify` per market (read-only).
- **Exit:** verify clean except missing cells logged as cap stops; pods deleted and verified.

### Operation 8: Report and review
- [ ] Executor (eval checkout): `report_v2.py --out results/v2/eval --protocol experiments/protocol-v2.yaml --instances results/v2/draw/instances.json --h4 results/v2/draw/h4.json --report results/v2/report`.
- [ ] Sol high and Astra high review the report against the protocol to consensus; then the author opens the H4 clone for the first time and releases `sealed2/` into the repository.
- **Exit:** `report_v2.py --check` passes; consensus recorded.

### Operation 9: Artifact and paper revision
- [ ] Executor: revise `paper/main.tex` with both evaluations (design 2); Sol and Astra review to consensus.
- [ ] Executor: `artifact_v2.py --assemble ...`, then `--check` and `reproduce.py --artifact` on a fresh machine or clean clone, after the last paper change.
- [ ] Author: publish the GitHub release with the tarball and the Zenodo DOI (design 10).

---

## Disposition of round 1

| Finding (Sol / Astra) | Change |
|---|---|
| Failed validation keeps kappa (S1 / A1) | Task 3 `kappa_effective`; Task 5 checks admission, counts, resamples, endpoints; Task 6 writes `kappa_effective` |
| Draw not bound to the protocol (S2 / A3) | Task 7 checks digest, H = A + 144, headers, hash, tips; substitution tests |
| Report ignores `confirmatory` (S11 / A2) | Task 9 consumes `instances.json`; nonconfirmatory heading; test |
| Tag before proof (S3 / A10) | Operation 5 order: commit, stamp, upgrade, commit proof, signed tag; separate eval checkout; `check_commit` verifies the signature and `check` |
| H4 reader rule and per-pod decisions (S4 / A8, A9) | Global constraint lists automated access; sealed commit in its clone; Task 7 one decision; Task 8 pods enforce it |
| Promotion deadlock, fixture metadata (S5 / A6) | Task 5 staged kinds and `--final`; Task 2 fixture provenance |
| Coverage per market, workers (S6 / A7) | Task 3 `--market` and `--workers` |
| Cost ignores cuts and branches, pod sizing (S7 / A4, A5) | Task 4 manifest-derived counts, branches, utilisation, `choose`, budget ledger; Task 2 tuning workers |
| Local "check" runs episodes (S8 / A13) | Task 8 `--stage verify` |
| Report validates too little; provenance at a later commit (S9 / A15) | Task 9 calls verify; report and reproduction run in the `protocol-v2` checkout |
| Report incomplete (S10 / A11, A12) | Task 9 Q1-Q4, secondary, doubling values, W0 gain, no-feasible case, per-seed Q2 |
| Doubling and question dependencies (S11 / A13) | Task 9 dependency map; ruling: search-incomplete labels are reported, not decisive |
| Priority implementation (S12 / A14) | Task 8 tiers with dependency waves, `block` on jobs, dispatch test with full params; ruling accepted by both |
| Artifact misses ignored results (S13 / A16) | Task 10 tarball, tag signature, reproduction after the paper |
| Weak tests (S14 / A18) | producer-shaped fixtures, independent oracles, mutation cases named per task |
| Minor CLI gaps (S15 / A17) | `--smoke`, lock CLI, `mkdir -p`, `stream_index` / `rejections`, `calibrated_cfg` |
