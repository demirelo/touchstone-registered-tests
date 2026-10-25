# Revision program, operations phase: Implementation Plan (version 9)

Status: accepted by Sol high and Astra high in round 9 (both accept, no findings; confidence 0.90 and 0.89). Rounds and dispositions: `docs/revision/roster/{sol,astra}-ops-plan-r1.md` to `-r9.md` and the tables at the end.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the built and reviewed revision code (main `8569e07`) through design 11 steps 2 to 9 (sealed H4, paid benchmark, comparator selection and tuning, coverage, protocol v2 and lock, block draw, evaluation, report, artifact), with the code those steps still lack.

**Architecture:** Part A builds ten pieces test-first on development data and ends with a whole-branch review; its reviewed head is `code_commit`. Part B is the run book in design order; each operation names its actor (author or executor), commands, entry check, exit check, and stop rule. Every paid run goes through the existing capped pod launcher `results/pods/explore_pod.sh` (local, untracked: USD cap from allocation time, `SCRIPT` and `ROUT` overrides, pull then verified delete). Version 9 answers rounds 1 to 8 (`docs/revision/roster/sol-ops-plan-r{1,...,8}.md`, `astra-ops-plan-r{1,...,8}.md`); the dispositions are at the end.

**Tech Stack:** Python 3 with uv, numpy, scipy 1.18.1 (pinned in `uv.lock`), cma, pytest; OpenTimestamps client (`uvx --from opentimestamps-client ots`); Runpod CPU pods via `results/pods/runpod.py`.

**Spec:** `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 6, accepted; "design"). Build plan `docs/superpowers/plans/2026-10-22-revision-build.md` and its ledger `docs/revision/build-ledger-2026-10-22.md` hold the rulings this plan inherits.

## Global Constraints

- No paid API calls of any kind (design 1 non-goals). Paid compute is Runpod CPU pods only, 16 vCPU each unless an operation says otherwise, each started through `explore_pod.sh` with a USD cap reserved in the budget ledger before launch (Task 4); every pod is deleted, and the deletion verified, once its outputs are pulled.
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
- Produces: `_tune(rule, specs, markets, out, smoke, workers=1)` scores (configuration, market) pairs with `ProcessPoolExecutor(max_workers=workers)` (inner scores, then the top 2 configurations' rechecks, 2 x markets tasks), recombined per configuration and ordered by grid index so `rank` and ties are unchanged; workers return their market's margins and detail, and the parent alone writes one log per configuration and stage holding every market's detail (no worker writes a log); `fixture_searches(markets, out, cred, smoke, workers=1)` runs markets in parallel and writes `smoke`, `budget`, `markets`, and `commit` into `fixture_cstar_s2.json`; `main` passes `--workers`. `select_comparator` and `tune_system` write `budget_inner`, `budget_full`, `commit` (they already write `smoke`, `markets`).
- [ ] **Step 1: Failing tests:** `test_parallel_tuning_equals_serial` (smoke, `grid_limit=2`, `workers=2` vs 1: identical `scores`, `rechecked`, chosen spec; a recording executor patched in asserts `max_workers == 2` and one submission per (configuration, market) pair), `test_parallel_logs_hold_every_market` (after a parallel smoke run, `coverage_v2.fixture_inputs(out, m)` succeeds for every market and each log lists all markets), `test_fixture_file_carries_provenance`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_tune_v2.py -q --runslow` PASSES. **Step 5:** commit `ops: tuning and fixtures use --workers; fixture provenance`.

### Task 3: Coverage on many cores, admitted kappa only

**Files:** Modify `scripts/coverage_v2.py`, `sim/calibration_v2.py` (`build_pool` chunking only), `tests/test_calibration_v2.py`.

**Interfaces:**
- Produces: `coverage_v2.py --pools --market LABEL --workers N` builds one market's pool, its seed range split into `N` chunks run in a process pool and concatenated in seed order (identical bytes to `workers=1`); `--select` and `--validate` read all pools of `--branch`. `coverage.json` gains top-level `smoke` (true when any replication or resample count is below the registered 10,000 / 20,000 / 9,999, or when `pool_size` differs from `calibration_v2.BRANCHES[branch][1]`), `pools: {market: {sha256, seeds, profile_lengths}}` for the pools actually read, and `inputs_manifest: {path: sha256}` of the tuning files the pools were built from (`comparator.json`, `log/*.json`, `fixture_cstar_s2.json` under `--inputs`), which `--pools` also writes into each pool file and `--select` and `--validate` require to agree across pools, `commit`, `branch`, `markets`, `pool_size`, `inputs_sha256` (of `experiments/v2/promotion.json`) and, per family, `kappa_effective` = `kappa` when `admitted` is true, else `null`, plus `resamples`, `selection_replications`, `validation_replications`, and the validation `endpoints` rows (identity, misses, upper bound, pass). `--select` and `--validate` refuse a `--branch` other than the pools' recorded branch.
- [ ] **Step 1: Failing tests:** `test_failed_validation_exports_null` (validate patched to `admitted: False`: `kappa_effective is None`, `kappa` kept), `test_pool_by_market_and_workers_equals_serial` (two-market synthetic inputs, 40-seed pools; a recording executor asserts `max_workers == N` and that the submitted chunks cover the seed range exactly once), `test_select_needs_every_branch_market`, `test_two20k_branch_end_to_end` (pools for headline and dev0 only, then `--select` and `--validate` with `--branch two20k` on small replication counts; `--branch three20k` refuses).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_calibration_v2.py -q` PASSES. **Step 5:** commit `ops: coverage pools per market on many cores; kappa_effective from admission only`.

### Task 4: Cost model for cuts and branches, and the budget ledger

**Files:** Modify `scripts/benchmark_v2.py`, `tests/test_benchmark_v2.py`; create `scripts/budget_v2.py`, `tests/test_budget_v2.py`.

**Interfaces:**
- Produces: the benchmark's `timings.json` also records `commit`, `markets` (`headline`, `dev0`), `vcpu`, the pod's measured `usd_per_pod_hour` (from `runpod.py list` at allocation), and the benchmark's own wall seconds. `cost_table(timings, cuts=0, h4_excluded=False, markets=("headline", "dev0", "dev1"), branch="three20k", vcpu=16)`: cell, reference-menu, doubling, and cross counts come from `manifest_v2.effective(cuts, h4_excluded)`, `doublings()`, and `cross_evaluations()` instead of constants (the defaults reproduce today's 374 / 118 / 132 / 14); configuration-markets scale with `len(markets)`; coverage episodes from `calibration_v2.BRANCHES[branch]`. Billed cost per phase = core-hours / (vcpu x u) pod-hours x `usd_per_pod_hour`, with each wave billed at the list-scheduling bound sum(t) / vcpu + (1 - 1 / vcpu) x max(t) seconds of pod time (an upper bound on the elapsed time of any greedy assignment of the wave's tasks with measured per-kind times t to vcpu workers), summed over the phase's waves: tuning inner (configurations x markets), rechecks (2 x markets), fixtures (markets), coverage (vcpu chunks per market), evaluation (the waves of Task 8's `dispatch_plan` per context and stage, serial prerequisites as one-task waves). `choose(timings, ledger) -> dict` returns the design 8.2 decision with the amounts spent before it counted (the benchmark's actual spend in development; a 1 USD reserve for the H4 decision pod in evaluation); Operation 2 writes it once, with a snapshot of the ledger, to `results/v2/benchmark/decision.json`, promoted as kind `decision`; later spend never changes it, and each later paid step only checks, through `reserve`, that its cap still fits the remaining budget (else stop for the author): development branch (three markets / two markets 20k / two markets 10k / stop), the smallest `cuts` in 0..4 under the evaluation cap (or stop), and `approval_required` on the total including spend.
- `budget_v2.py`: `docs/revision/budget-ledger.json` holds `{caps, reservations: [{op, tag, cap}], spent: [{op, tag, usd}]}`, updated under an exclusive file lock. `reserve(op, tag, estimate) -> float` grants `min(estimate x 1.25, cap - spent - outstanding)` and refuses when that is below the estimate, or when the combined spend plus outstanding reservations of both phases would pass the approval limit (40 USD, or the higher limit of a written approval recorded with `--approve LIMIT TEXT`, design 8.2); `record(tag, usd)` replaces the tag's reservation with its actual spend (replacement pods reserve under new tags). CLI `--reserve OP TAG ESTIMATE`, `--record TAG USD`, `--approve LIMIT TEXT`, `--show`.
- [ ] **Step 1: Failing tests:** `test_defaults_reproduce_the_current_table` (at u = 1), `test_cuts_and_branches_change_counts` (cuts 1..4 reduce cells by the manifest's numbers; branch `two10k` halves coverage episodes and scales configuration-markets by 2/3), `test_wave_bound_covers_unequal_tasks` (fifteen 1-second tasks and one 100-second task on 16 workers bill at least 100 seconds; for random task sets the bound is never below a simulated greedy schedule's elapsed time), `test_evaluation_bill_follows_the_dispatch_plan` (a synthetic plan with a serial prerequisite and two unequal parallel waves: billed pod-hours equal the sum of the wave bounds), `test_choose_follows_design_order` (over the development cap → `two20k`, then `two10k`, then stop; over the evaluation cap → smallest sufficient cut, else stop), `test_benchmark_spend_decides_a_borderline_case` (a development estimate that fits only when the recorded benchmark spend is omitted chooses the next branch), `test_reservations_are_aggregate` (10 USD left: two reservations of 3.75 and a third of 2.5 are granted, a fourth refused; `record` of an actual 1 USD releases the rest), `test_combined_total_needs_approval` (development 12 spent, evaluation 27 spent: a reservation of 4 against an estimate of 3.2 fits the evaluation cap but is refused at the 40 USD combined limit until `--approve 45 ...` is recorded), `test_concurrent_reservations_respect_the_cap` (eight processes released by a barrier each reserve an estimate of 2 USD, granted 2.50, against 10 USD: at most four succeed, the successful returned grants sum to at most 10, and each successful tag appears exactly once in the ledger), `test_lost_update_is_impossible` (a test hook between the ledger read and write sleeps in one process while a second process reserves: both reservations are present afterwards, or the second waits for the lock).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_benchmark_v2.py tests/test_budget_v2.py -q` PASSES. **Step 5:** commit `ops: cost model aware of cuts, branches, and utilisation; budget ledger with capped pod allocation`.

### Task 5: Staged promotion

**Files:** Create `scripts/promote_v2.py`, `tests/test_promote_v2.py`.

**Interfaces:**
- Produces: (coverage promotion copies the pool files with `coverage.json`) `promote_v2.py --kind comparator|system|fixtures|coverage|benchmark|decision --from DIR --to experiments/v2 --markets M [--branch B] [--final]` (`--branch` required for coverage); each kind is validated and copied on its own, appending `{path: sha256}` to `experiments/v2/promotion.json`; `--final` checks completeness (comparator, four systems, fixtures, coverage, benchmark) and writes `params.json` (`{"cred", "tuned": {name: {"tol", "L"}}}`, the `--params` of `revision_v2.py`).
- Schemas per kind (the producers write these fields: Tasks 2, 3, 4): every kind has `smoke`, `commit`; tuning kinds and coverage have `markets`; coverage has `branch`; the benchmark has `vcpu` and `usd_per_pod_hour`. Checks: `smoke` false, `commit` equals `code_commit`, markets equal `--markets` (the benchmark's fixed `headline`, `dev0`), coverage `branch` equals `--branch`; comparator 12 scored and 2 rechecked; each system 16 and 2, ties by grid index, C*-t's `cred` equal to the promoted comparator's; inner budget `(1, 100, 3, 20)` and the locked full budget; fixtures cover every market; coverage `kappa_effective` present per family (null allowed) and, when non-null, the validation rows equal exactly the endpoint set `calibration_v2.endpoints(family, branch)`, each row's upper bound recomputed as `clopper_pearson_upper(misses, 20000, 1 - 0.01 / m_F)`, admission recomputed as every upper bound <= alpha_e and equal to the recorded `admitted`, and a non-null `kappa_effective` equal to both the selected `kappa` and `validation.kappa` and one of 1, 1/2, 1/4, 10,000 selection and 20,000 validation replications, 9,999 resamples; `inputs_manifest` equal, path by path, to the comparator, system-log, and fixture entries already in `promotion.json` (the tuning kinds only, so no circular hash); `pool_size` equal to `BRANCHES[branch][1]` and, for every branch market, the promoted pool file's hash equal to `pools[market].sha256`, its seed list equal to `instances.coverage_pool(market, pool_size)`, and every profile array of that length; benchmark `smoke` false and its table recomputed equal by `cost_table`.
- [ ] **Step 1: Failing tests** built from the producers' own outputs at production arguments with the expensive calls stubbed (`tune_v2.market_searches` and `evaluate_gain` patched to return fixed values, so budgets, counts, and metadata are the registered ones; `coverage_v2.main` with `calibration_v2.endpoint_misses` patched; `benchmark_v2.main(["--run"])` with workloads stubbed), unedited for the passing case and with one field mutated per refusal; real smoke outputs are refusal cases: `test_unedited_producer_outputs_pass_schema`, `test_smoke_outputs_are_refused`, `test_each_refusal` (parametrised over every check, including a substituted endpoint, a wrong branch, `admitted: true` with one failing endpoint, a record selected and validated at 1/4 whose `kappa_effective` alone is changed to 1, a record with full replication and resample counts built on 40-seed pools, and valid coverage and pools built from tuning set A offered beside promoted tuning set B; the same records unchanged, at the registered pool size and with matching inputs, pass), `test_staged_kinds_promote_independently`, `test_final_needs_all_kinds_and_writes_params`.
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** commit `ops: staged promotion with validation and a final completeness check`.

### Task 6: Protocol v2 writer and checker

**Files:** Create `scripts/lock_v2.py`, `tests/test_lock_v2.py`, `docs/revision/predictions-v2.md` (template with design 9.7 headings).

**Interfaces:**
- Produces: `build(repo, code_commit, cuts, h4: dict | None, approval: str | None, branch: str, markets: list) -> dict`; `check(repo, protocol) -> list[str]` (every hash re-derived from its file; `cuts` and `branch` equal the promoted `decision.json`, whose hash is in the protocol; `approval` present when the decision's `total_usd > 40`; the protocol's `cost.spent_usd` equals the ledger's recorded spend); `check_commit(repo) -> None` (clean tree; `git tag -v protocol-v2` succeeds; `HEAD` is the tag's commit; `git diff --name-only code_commit HEAD` lists only the allowed paths; `check` passes). CLI `--write --code-commit SHA --cuts N --branch B --markets M (--h4-commit SHA --h4-sha HEX | --no-h4) --approval TEXT`, `--check`, `--check-commit`.
- Fields: `version: 2`, `code_commit`, `manifest_sha256`, `cuts`, `branch`, `development_markets`, `h4: {commit, bundle_sha256} | null`, `params_sha256`, `promotion_sha256`, `decision_sha256`, `kappa: {Q1, Q4}` (from `kappa_effective`), `coverage_sha256`, `cost: {development_usd, evaluation_usd, total_usd, spent_usd}`, `approval`, `predictions_sha256`, `block: {rule: "H = A + 144", depth: 6, explorers: [blockstream.info, mempool.space]}`, `seeds: {eval_range: [30000000, 40000000], per_market: 200}`, `markets: [headline, fresh0, ..., fresh5]`, `caps: {development: 12, evaluation: 40}`.
- [ ] **Step 1: Failing tests:** `test_build_and_check_round_trip`, `test_check_reports_each_changed_input` (params, coverage, manifest, predictions, promotion, benchmark, each mutated in turn; an expected-hash table written independently in the test), `test_total_above_40_needs_approval`, `test_kappa_comes_from_kappa_effective`, `test_decision_survives_later_spend` (benchmark decision promoted, then development spend recorded in the ledger, then `check` still passes and a changed decision file fails), `test_check_commit_refuses_other_head_or_unsigned_tag` (temporary repo with a test signing key: untagged HEAD, lightweight tag, code change after `code_commit`, and dirty tree each refuse; a signed tag on a data-only commit passes).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** PASS. **Step 5:** commit `ops: protocol v2 writer and checker`.

### Task 7: Draw to instances, and the single H4 decision

**Files:** Create `scripts/draw_v2.py`, `tests/test_draw_v2.py`; modify `scripts/block_draw.py` (`anchor` records every lower attestation it rejected, with the header served at that height, in the final record's `lower_attestations`), `tests/test_block_draw.py`.

**Interfaces:**
- Consumes: the committed upgraded proof `experiments/protocol-v2.yaml.ots` and its listing (`ots info`, as `block_draw.main` runs it); the `block_draw.py` final record (`status`, `height`, `hash`, `anchor`, `headers`, `tips`, `answers_at_h`, `protocol_sha256`, and the new `lower_attestations`) and its verifiers (`check_protocol`, `attestations`, `header_hash`, `merkle_root`, the header-chain and depth checks of `read_final`, re-run offline on the stored headers); `sim.instances.markets`, `eval_seeds`, `identity_salt_hex`, `calibrated`; `sim.records.cfg_to_dict`; `sim.h4_loader.load`.
- Produces: `instances(draw, protocol_bytes, ots_info, published_height) -> dict` (`root`, `height`, `markets: {label: {stream_index, rejections, cfg, calibrated_cfg}}`, `seeds: {label: [200]}`, `salt_sha256`, `confirmatory`); `h4_decision(bundle: Path | None, protocol) -> dict` (`{loaded, reason, bundle_sha256, h4_excluded}`); CLI `--instances --draw FILE --protocol FILE --ots FILE --published-height N --out DIR` and `--h4-decision --protocol FILE [--bundle DIR] --out DIR` (creates `--out`).
- Checks: `check_protocol(ots_info, protocol_bytes)` passes (the proof commits to these bytes) and equals `draw["protocol_sha256"]`; the anchor is the lowest valid attestation of the proof (design 7.3): its height and root are one of the proof's `attestations`, its root equals the stored header at A's Merkle root, and every lower attestation of the proof appears in `lower_attestations` with a header whose hash is that height's served hash and whose Merkle root differs from the attested root; `height` equals anchor height + 144; the stored headers link from A to H + 6 with valid proof of work and A's Merkle root equals the anchor's; `hash` equals the header hash at H and is 64 lowercase hex; both `tips` at least H + 6 and both explorers' `answers_at_h` equal `hash`. `confirmatory` is false when `published_height` is missing or at least H.
- [ ] **Step 1: Failing tests** (synthetic headers from `tests/test_block_draw.py`'s fixtures): `test_instances_follow_generator_and_streams` (a fixed root; labels fresh0..fresh5; a monkeypatched stream limit keeps label order), `test_substituted_draw_is_refused` (an unrelated valid draw whose `protocol_sha256` field is rewritten to this protocol's digest; an anchor height absent from the proof; a proof with two valid attestations and a draw built on the later one; a lower attestation missing from `lower_attestations`; H != A + 144; a broken header link; a hash mismatch; disagreeing answers; tips below H + 6: each refuses), `test_unchanged_reader_output_is_accepted` (the JSON written by `block_draw.main` with `http_fetch` and the `ots info` subprocess replaced by test substitutes, consumed unchanged; the same record without `protocol_sha256` is refused), `test_late_publication_is_nonconfirmatory`, `test_seeds_equal_an_independent_derivation` (re-derive v_n from the design 7.2 formula in the test; exact equality, disjoint from every reserved range), `test_h4_decision_loads_a_valid_bundle` (the toy bundle with its registered hash: `loaded` true, `h4_excluded` false, `bundle_sha256` equal to the protocol's), `test_h4_decision_records_exclusion` (toy bundle with a wrong hash: `loaded` false, `h4_excluded` true).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_draw_v2.py tests/test_block_draw.py tests/test_instances.py -q` PASSES. **Step 5:** commit `ops: draw to instances bound to the protocol; one H4 decision`.

### Task 8: Runner: priority dispatch, read-only verification, H4 decision

**Files:** Modify `scripts/revision_v2.py`, `tests/test_revision_v2.py`.

**Interfaces:**
- Consumes: `sim.manifest_v2.priority(cell)` (needs the cell's `block`); Task 7's `h4.json`.
- Produces: `job()` carries `block` and `priority`; the reference stage runs its (context, rule) menus through `_pool`, and the cross stage its (context, family) evaluations through `_pool` (both are independent per item); `dispatch_plan(stage, jobs) -> list[list[str]]` returns the waves `run` executes (ids per wave), and Task 4's evaluation pricing uses it; `run(stage, ...)` dispatches in priority tiers 0 to 3, and within a tier keeps the dependency waves (non-X7 searches before the same tier's X7-SC searches; W1 non-X7 before X7; coalition prerequisites before objectives), so no tier-k job runs before every tier-(k-1) job of the stage: each (tier, wave) is its own `_pool` call, which returns only when all its tasks have finished, so a call is a completion barrier; `dispatch_plan` lists exactly these calls in order. Freeze and derived records stay serial (no episodes). New `--stage verify`: a context with no freeze record is reported `unavailable` (all its cells missing); a context with a freeze goes through `accept` (a stale or incomplete freeze is an error), then every evaluate, cross, and doubling record is checked against its expected stage, provenance, dependency set and hashes, seeds (equal to the instance's), array lengths, and finiteness. Verify builds its expectations from recorded inputs only: market configurations from `instances.json` (`calibrated_cfg`) and the headline calibration file, the salt hash from `instances.json`, through new `market(label, root, rho, dev, smoke, cfg=None)` and `job(..., salt_sha256=None)` parameters, so no calibration episode runs and no ambient salt is read. Verify never calls a stage body, never imports the H4 bundle (it checks that `h4.json`'s bundle hash equals the protocol's and every H4 record's `h4_sha256`), never installs the salt, and writes nothing; it prints a JSON report to stdout. New `--h4-decision FILE` (required with `--root`): an excluded decision sets `h4_excluded`; a loaded decision requires `--h4`, the same bundle hash, and a successful load, else the run stops before any episode.
- Ruling (accepted by both seats in rounds 1 and 2): priority cannot waive the complete freeze (design 6.4); a context evaluates only after its freeze. Dispatch is ascending tiers 0 to 3 on every pod; fresh-market pods start before the headline pods.
- [ ] **Step 1: Failing tests:** `test_dispatch_follows_priority_tiers` (`_pool` patched to record order; full params: `cred` and tuned `B3-t`, `R3-t`, `R4-t`, `C*-t`; every tier-0 job, X7-SC included, precedes any tier-1 job, and every tier-2 job precedes any tier-3 job), `test_verify_stage_runs_no_episode` (a fresh spawned process, on a fresh-market context with every `lru_cache` of the runner empty, that patches to raise: `sim.calibrate.calibrate`, `sim.instances.calibrate`, `sim.calibrate.first_best_episode`, `sim.cell.run_focal`, every stage body, `sim.h4_loader.load`, the runner's `load_h4`, `sim.rng.load_identity_salt` and the runner's `load_identity_salt`, `install_salt`, and installs a `sys.addaudithook` guard that raises on every `open` event with a write, append, create, or truncate mode (which covers `builtins.open`, `io.open`, `os.open`, and `Path.write_text`) and on `os.mkdir`, `os.rename`, `os.replace`, `os.remove`, `os.rmdir`, `os.link`, `os.symlink`, `os.truncate`, `os.chmod`, `os.chown`, and `os.utime`, anywhere on the filesystem, and on every child-process event (`subprocess.Popen`, `os.system`, `os.exec`, `os.posix_spawn`, `os.spawn`, `os.fork`) without exception (verify takes the expected commit as `--commit SHA`, which the operator obtains with `git rev-parse protocol-v2^{commit}` before the run, so it starts no `git` process); it then calls `main(["--stage", "verify", ...])`, which for `verify` requires an existing `--out` and creates nothing; the guard's own test injects faulty verifiers that write through `Path.write_text` outside `--out`, create a missing directory, create a hard link, and start a child process (including `git rev-parse HEAD`), and all four must be rejected; a complete context verifies; a deleted evaluate record, a stale freeze, and a foreign record are each reported; a context stopped before its freeze is reported `unavailable`), `test_tiers_wait_for_slower_higher_tiers` (`workers=2`; a tier-0 stage body sleeps while a tier-1 body records its start time to a file: no tier-1 task starts before every tier-0 task has finished; the recorded `_pool` calls equal `dispatch_plan`), `test_reference_and_cross_run_through_the_pool` (recording `_pool`: every menu and every (context, family) item runs exactly once, in tier waves), `test_loaded_decision_runs_h4` (the unchanged loaded decision from Task 7's test, with `--h4` and the registered hash, on a smoke dev context: an H4 search record is written and its provenance carries `h4_sha256`), `test_pods_enforce_the_h4_decision` (excluded decision → manifest without H4 even with `--h4`; loaded decision with a different hash → `SystemExit` before any episode).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_revision_v2.py -q` PASSES. **Step 5:** commit `ops: runner priority tiers, read-only verify stage, enforced H4 decision`.

### Task 9: The report

**Files:** Create `scripts/report_v2.py`, `tests/test_report_v2.py`.

**Interfaces:**
- Consumes: records verified by Task 8's verify stage (the report calls its function first and refuses on any problem other than missing cells and unavailable contexts, whose cells count as missing); `sim.decisions_v2`; `sim.intervals`; the protocol (`kappa`), `instances.json` (`confirmatory`), `h4.json`.
- Produces: `build(out, protocol, instances, h4) -> dict` with `q1`, `q2`, `q3`, `q4`, `secondary`, `doubling`, `missing`, `unanswered`, `confirmatory`; CLI `--out DIR --protocol FILE --instances FILE --h4 FILE --report DIR [--check]` (writes `report.json`, `report.md`; `--check` rebuilds and compares).
- **Question dependencies** (a missing record of any listed cell makes the question unanswered; other questions stay answered): Q1 needs F111, C*, R4, C*/S2 x {D2+H3, X7-SC} on the six fresh markets; Q4 needs F000 and F111 under D2+H3 on each fresh market (a market with a missing cell is "not decided"); Q2 needs the eight factorial cells per market and family and their cross records; Q3 needs each core rule's envelope families, welfare, and coalition cells (H4's part unanswered when `h4.loaded` is false). Search-incomplete labels from doubling checks are reported beside the estimates and do not change decisions (design 6.4 "Doubling results never enter the frozen candidates"; ruling for the reviewers).
- **Q1:** per pair (F111 vs C*, R4 vs C*/S2) and family, six strata = per fresh market the per-seed difference of the two rules' gains; `q1_family(tests, kappa_Q1)`; estimate and the calibrated simultaneous interval at one-sided tails `kappa_Q1 x 0.05/8`; per-market and headline differences with nominal 95 percent intervals, labelled descriptive. **Q4:** per fresh market `p_a = bootstrap_pvalue(g_F000 - g_F111, 0.10, "lower")` under D2+H3 and `p_b = bootstrap_pvalue(eff_F111, 0.90, "lower")`; `q4_markets(pa, pb, kappa_Q4)` always over six slots (a market with a missing cell enters with p = 1 and is "not decided"); calibrated one-sided lower bounds at `kappa_Q4 x 0.05/6`; wording "replicated on k of 6 sampled markets", failing markets named, "generalisation not established" when any market is not decided. **Q2:** per seed the effect-coded contrasts (P, G, S, PG, PS, GS, PGS, G at P=0 and 1, P at S=0 and 1) over the eight cells' per-seed gains, on the diagonal and on the fixed-attack matrix (per-seed contrast within each attack row, then the mean over the 8 rows), then stratified nominal 95 percent intervals pooled over the six fresh markets; the per-rule bank envelope. **Q3:** per core rule the envelope family (its `envelope` record's choice) with the evaluation gain and interval; W0 and W1 lowest efficiency (winners selected on training seeds), its interval, the attacker's gain (W0: `normalized - profit_ref / (sstar / N)` from the rule's D2+H3 evaluation on the same seeds; W1: the stored constraint) and the W1 constraint interval, or "no feasible candidate found"; coalition G_tot and G_min with `gmin_bounds(member_rows, 0.05)`. **Secondary:** whole systems (B3-t, R3-t, R4-t, C*-t) and the rho = 1 repair cells, descriptive. **Doubling:** every scheduled check's measured changes and label. **Nonconfirmatory draw:** Q1 categories and Q4 passes are printed as descriptive results under the heading "nonconfirmatory (late publication)".
- [ ] **Step 1: Failing tests** with producer-shaped records (written through `revision_v2`'s own record writers on tiny contexts) and independent oracles computed in the test from the per-seed arrays: `test_q1_strata_tails_and_kappa` (a wrong tail or an unused kappa changes the asserted interval), `test_q2_per_seed_contrasts_against_an_oracle`, `test_q3_welfare_gain_and_no_feasible_case`, `test_q4_wording_bounds_and_named_failures`, `test_no_kappa_no_decision_but_estimates`, `test_missing_cells_make_dependent_questions_unanswered` (a missing F111 D2+H3 record leaves Q1, Q2, Q4 for that market and Q3 unanswered as listed, and the rest answered), `test_q3_unanswered_without_h4`, `test_nonconfirmatory_draw_has_no_confirmatory_claim`, `test_report_refuses_foreign_or_stale_records`, `test_check_mode_detects_a_changed_record`, `test_q4_keeps_six_holm_slots` (one market missing and the smallest calibrated p-value 0.009: not rejected, since 0.009 > 0.05/6, whereas five slots would reject), `test_unavailable_context_is_unanswered_not_an_error`, `test_doubling_label_does_not_change_decisions` (two record sets differing only in a doubling `incomplete` flag give identical decisions and different labels).
- [ ] **Step 2:** FAIL. **Step 3:** implement. **Step 4:** `uv run pytest tests/test_report_v2.py tests/test_decisions_v2.py -q` PASSES. **Step 5:** commit `ops: report with question dependencies, calibrated and descriptive intervals`.

### Task 10: Artifact assembly, reproduction, check

**Files:** Create `scripts/artifact_v2.py`, `scripts/reproduce.py`, `tests/test_artifact.py`.

**Interfaces:**
- Produces: `artifact_v2.py --assemble --eval DIR --draw DIR --report DIR --h4 DIR --out release/` builds `release/touchstone-v2.tar.gz` (records, draw record with headers, instances, report, the released H4 bundle, promoted inputs, protocol and upgraded proof, paper sources, `uv.lock`, a manifest of SHA-256s) because `results/` is ignored by git; `--check TARBALL` verifies every manifest hash, the tag signature (`git tag -v protocol-v2`), and the freeze records' hashes; `reproduce.py --artifact TARBALL` unpacks into a temporary directory, checks out `protocol-v2` in a fresh clone, runs `report_v2.py --check`, and exits non-zero on any difference.
- [ ] **Step 1: Failing tests:** `test_assemble_and_check_a_synthetic_release`, `test_check_reports_missing_and_changed_files`, `test_reproduce_passes_an_unchanged_release` (exit 0 and an empty difference list), then `test_reproduce_detects_a_changed_record` (synthetic tiny release with a temporary repo and tag; exit non-zero and the changed record named).
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
- [ ] Executor: `budget_v2.py --reserve development bench 2.4` (3 USD cap); one 16-vCPU pod: `SCRIPT=scripts/benchmark_v2.py ROUT=results/v2/benchmark results/pods/explore_pod.sh <tarball> bench 3 results/v2/benchmark "--run"`; `promote_v2.py --kind benchmark`.
- [ ] Executor: `budget_v2.py --record bench <actual>`; `choose()` on the promoted timings and the ledger, written once to `decision.json` and promoted (`--kind decision`); report branch, cuts, development, evaluation, and total USD. Author: approve in writing when the total exceeds 40 USD (the sentence goes into the protocol). A "stop" from `choose` stops the program for the author.
- **Exit:** the decision and the approval (if needed) in the ledger; no other paid step before this exit.

### Operation 3: Comparator selection, whole-system tuning, fixtures
- [ ] Executor: one pod, `tune_v2.py --select comparator --markets <chosen> --workers <vcpu> --out results/v2/tune_comparator`, cap from `budget_v2.py --reserve development tune-comparator <row estimate>`; pull; `promote_v2.py --kind comparator`.
- [ ] Executor: five pods in parallel, `--select B3-t | R3-t | R4-t | C*-t | fixtures --markets <chosen> --comparator experiments/v2/comparator.json --workers <vcpu>`, each cap reserved before its launch; pull; record each actual; promote each (`--kind system`, `--kind fixtures`).
- **Exit:** promotions recorded; development spend under 12 USD; otherwise stop for the author.

### Operation 4: Coverage check
- [ ] Executor: one pod per branch market (caps reserved), `coverage_v2.py --pools --market <m> --branch <chosen> --inputs experiments/v2 --workers <vcpu> --out results/v2/coverage`; pull the pools together; locally `coverage_v2.py --select --branch <chosen> --out results/v2/coverage` then `coverage_v2.py --validate --branch <chosen> --out results/v2/coverage`; `promote_v2.py --kind coverage --branch <chosen>`; then `promote_v2.py --final` writes `params.json`.
- **Exit:** `kappa_effective` for Q1 and Q4 (number or null).

### Operation 5: Protocol v2, review, lock
- [ ] Executor: draft `docs/revision/predictions-v2.md` (design 9.7 directions against development results); `lock_v2.py --write ...`; `lock_v2.py --check`.
- [ ] Sol high and Astra high review protocol and predictions to consensus.
- [ ] Author, in order: `git commit -S` (protocol and predictions); `ots stamp experiments/protocol-v2.yaml`; push the commit; `ots upgrade` until the proof holds a Bitcoin attestation; `git commit -S` the upgraded proof; `git tag -s protocol-v2` on that commit; push the commit and tag; record the tip height at the push (`published_height`).
- [ ] Executor: a fresh clean clone at `protocol-v2` (`results/v2/eval-checkout`); `lock_v2.py --check-commit` there.
- **Exit:** `check-commit` passes; the push height is below A + 144. **Stop:** a push at or after H keeps the draw, labelled nonconfirmatory (design 7.3).

### Operation 6: Draw, instances, H4 decision
- [ ] Executor (eval checkout): `mkdir -p results/v2/draw && uv run python scripts/block_draw.py --ots experiments/protocol-v2.yaml.ots --protocol experiments/protocol-v2.yaml --out results/v2/draw/draw.json`.
- [ ] Executor: `draw_v2.py --instances --draw results/v2/draw/draw.json --protocol experiments/protocol-v2.yaml --ots experiments/protocol-v2.yaml.ots --published-height <N> --out results/v2/draw`.
- [ ] Executor: one small pod (the 1 USD H4 reserve) with the author's custody copy uploaded unopened: `draw_v2.py --h4-decision --protocol experiments/protocol-v2.yaml --bundle <upload> --out results/v2/draw`; pull `h4.json`.
- **Exit:** `instances.json` (six fresh labels, 200 seeds each, `confirmatory`), `h4.json`.

### Operation 7: Evaluation on pods
- [ ] Executor, per pod before any stage (eval checkout copied): `lock_v2.py --check-commit`; `params.json`, `h4.json`, and (when loaded) the bundle present; `OMP_NUM_THREADS=1`.
- [ ] Executor: six fresh-market pods first (`--markets freshK`), then two headline pods by context (`--select 'headline@rho0.2|*'`, `--select 'headline@rho1|*'`); each runs `search`, `reference`, `dependent`, `freeze`, `evaluate`, `cross`, `doubling` on one `--out` with `revision_v2.py --stage S --root <hash> --params experiments/v2/params.json --cuts <c> --h4-decision results/v2/draw/h4.json [--h4 DIR --h4-sha HEX] --workers <vcpu>`; each pod's cap reserved with `budget_v2.py --reserve evaluation <tag> <estimate>` before launch and recorded after, so reservations plus spend never pass 40 USD.
- [ ] Executor: pull every `--out` into `results/v2/eval/`; `revision_v2.py --stage verify --commit $(git rev-parse protocol-v2^{commit})` per market (read-only, no H4 import, no writes, no child process).
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

## Disposition of round 2

| Finding (Sol / Astra) | Change |
|---|---|
| Draw not bound to the proof (S1 / A1) | Task 7 consumes the upgraded proof and its listing: `check_protocol`, anchor among the proof's attestations with matching root and header, explorer answers at H; rewritten-digest test |
| Promotion needs metadata producers lack (S2 / A3) | Tasks 3 and 4 add `commit`, `markets`, `branch`, `vcpu`, rate; Task 5 per-kind schemas tested on unedited producer outputs |
| Branch not passed to select and validate (S3 / A4) | Operation 4 full commands; Task 3 refuses a branch mismatch; two20k end-to-end test |
| Caps without reservations (S4 / A2) | Task 4 reservations under a file lock, actual spend replaces them; H4 pod and replacement pods reserve; aggregate test |
| Utilisation and pod sizes (S5) | 16 vCPU default; per-phase utilisation from task counts; measured pod rate; benchmark spend in `choose`; borderline test |
| Local verification and H4 custody (S6 / A5) | Task 8 verify imports no bundle, installs no salt, writes nothing; CLI test with all three patched to raise |
| Stop before freeze (S7 / A6) | Task 8 `unavailable` contexts; Task 9 treats their cells as missing; test |
| Q4 Holm family shrinks (S8 / A6) | Task 9 six slots, missing market p = 1; numerical boundary test |
| Tier order sentence (S9 / A7) | removed; ascending tiers tested across tiers 2 and 3 |
| Coverage admission consistency (S10 / A3) | Task 5 exact endpoint set, recomputed bounds and admission; mutation test |
| Weak tests (S11 / A8) | recording executors assert worker counts and chunk coverage; aggregate reservations; verify side effects; paired doubling-label test |

## Disposition of round 3

| Finding (Sol / Astra) | Change |
|---|---|
| Parallel tuning overwrites logs (S1 / A2) | Task 2: workers return detail, the parent writes one log per configuration with every market; `fixture_inputs` test on parallel output |
| Passing promotion test used relabelled smoke (S2 / A6) | Task 5: producers at production arguments with expensive calls stubbed; smoke outputs are refusal cases |
| Coverage `smoke`, promotion `--branch` (A1) | Task 3 writes `smoke`; Task 5 declares `--branch` |
| `answers_at_h`; lowest anchor (S3, S4 / A5) | Task 7 uses `answers_at_h`; `block_draw` records rejected lower attestations; draw on a later valid attestation refused; unchanged reader output accepted |
| Verify side effects through calibration and salt (S5) | Task 8 expectations from `instances.json` and recorded calibration; spawned-process test forbids calibration, episodes, both loader names, salt, writes |
| Decision drifts with the ledger (S6 / A4) | Task 4 writes `decision.json` once with a ledger snapshot; Task 6 checks it by hash; test across later spend |
| Serial stages priced as parallel (S7 / A3) | Task 8 runs reference and cross through `_pool` and exposes `dispatch_plan`; Task 4 bills its waves; test |
| Reservation lock untested (A7) | multiprocess barrier test |

## Disposition of round 4

| Finding (Sol / Astra) | Change |
|---|---|
| No live combined approval gate (S1 / A3) | Task 4 `reserve` refuses past the 40 USD combined limit unless a written approval raises it (`--approve`); crossing test |
| Reader test used output without the digest (S2) | Task 7 test consumes `block_draw.main`'s JSON with fetch and `ots` substituted; missing-digest record refused |
| Verify prohibitions miss aliases, first-best, default salt, writes elsewhere (S3 / A1) | Task 8 spawned test forbids both calibrate bindings, `first_best_episode`, both salt readers, and every write mode |
| Priority barriers unenforced (S4 / A4) | Task 8 one `_pool` call per (tier, wave) as a completion barrier; `dispatch_plan` equals the calls; slow-tier test with start and finish times |
| Unequal task durations underpriced (A2) | Task 4 wave bound sum / vcpu + (1 - 1 / vcpu) max; unequal-duration and simulated-schedule tests |

## Disposition of round 5

| Finding (Sol / Astra) | Change |
|---|---|
| Write guard misses `Path.write_text` and directory creation (S1 / A1) | Task 8 audit-hook guard on every write-mode `open` and filesystem mutation; verify needs an existing `--out`; faulty-verifier cases must be rejected |
| Concurrent reservation test can pass without the lock (S2) | exact assertions on grants, count, and ledger entries; forced read-write interleaving test |
| `kappa_effective` not tied to the validated multiplier (A2) | Task 5 equality with the selected and validated kappa in {1, 1/2, 1/4}; changed-kappa refusal and unchanged pass |

## Disposition of round 6

| Finding (Sol / Astra) | Change |
|---|---|
| Coverage pool size not bound to the branch (S2 / A1) | Task 3 marks reduced pools as smoke and records the pools read; Task 5 requires the branch's pool size, the pool hashes, seed lists, and array lengths; 40-seed refusal test |
| Child processes and hard links bypass the write guard (S1) | Task 8 guard refuses child processes except the read-only `git rev-parse HEAD`, adds `os.link` and `os.chown`; child-process and hard-link faulty verifiers |

## Disposition of round 7

| Finding (Sol / Astra) | Change |
|---|---|
| Coverage not bound to the promoted tuning inputs (S2 / A1) | Task 3 records `inputs_manifest` in pools and `coverage.json`; Task 5 compares it with the promoted tuning entries only; A-pools / B-inputs refusal test |
| Permitted `git` child can write (S1) | Task 8 verify starts no child process at all; the commit is an explicit `--commit` input; Operation 7 passes it |
| Reproduction lacks a passing case (A2) | Task 10 `test_reproduce_passes_an_unchanged_release` before the changed-record test |

## Disposition of round 8

Astra: accept, no findings. Sol: one finding.

| Finding (Sol) | Change |
|---|---|
| No successful H4 decision case (S1) | Task 7 `test_h4_decision_loads_a_valid_bundle`; Task 8 `test_loaded_decision_runs_h4` feeds that decision to the runner and requires an H4 record |
