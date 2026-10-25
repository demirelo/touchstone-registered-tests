# Revision program, operations phase: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the built and reviewed revision code (main `8569e07`) through design 11 steps 2 to 9: the sealed H4 session, the paid benchmark, comparator selection and tuning, coverage, protocol v2 and its lock, the block draw, the evaluation, the report, and the artifact, with the small pieces of code those steps still lack.

**Architecture:** Part A builds seven missing pieces test-first on development data: the H4 session kit, promotion of pulled outputs into `experiments/v2/`, the protocol-v2 writer and checker, the draw-to-instances step, the report, the reproduction and artifact check, and execution priority in the runner. Part B is the run book: each operation names its actor (author or executor), its commands, its entry check, its exit check, and its stop rule. Every paid run goes through the existing capped pod launcher `results/pods/explore_pod.sh` (local, untracked), whose `SCRIPT` and `ROUT` overrides select a v2 entry point.

**Tech Stack:** Python 3 with uv, numpy, scipy 1.18.1 (pinned in `uv.lock`), cma, pytest; OpenTimestamps client; Runpod CPU pods via `results/pods/runpod.py`.

**Spec:** `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 6, accepted; "design"). Build plan: `docs/superpowers/plans/2026-10-22-revision-build.md` ("build plan"); its ledger `docs/revision/build-ledger-2026-10-22.md` holds the rulings this plan inherits.

## Global Constraints

- No paid API calls of any kind (no LLM attackers, design 1 non-goals). Paid compute is Runpod CPU pods only, each started through `explore_pod.sh` with a USD cap; every pod is deleted, and the deletion verified, as soon as its outputs are pulled.
- Caps (design 8.2): development 12 USD, evaluation 40 USD; **the author's approval is required for any recomputed total above 40 USD**. Cut order and stop rules exactly as design 8.2; the benchmark decides, before any paid tuning.
- Development data only until the draw (design 2, build plan Global Constraints): seeds dev-train 1000-1004, dev-val 2000-2019, calibration 4000-4019, coverage pools in [40,000,000, 60,000,000); development root "dev-20261022". Evaluation seeds [30,000,000, 40,000,000) exist only after the draw.
- Frozen files stay byte-identical to `2a288f5` (`tests/test_frozen_files.py`). Registered files of the first evaluation (`experiments/locked.yaml`, `sealed/`, the first-evaluation records) are never changed; `sealed/` is never read.
- The H4 bundle (`sealed2/`) is written by a separate Codex session (fresh `gpt-6.1-sol`, high effort, its own clone at the lock-candidate commit, design 5.3) and kept outside this repository by the author until the report. Nobody in this program, executor included, reads `sealed2/` before the report; its only reader before then is `sim/h4_loader.load` inside evaluation processes on pods.
- Everything after the lock follows design 9.6: no change to rules, families, seeds, manifest, cuts, or decision rules; orchestration changes are logged in `docs/revision/operations-ledger.md`.
- Two commits matter. `code_commit` is the frozen code (the H4 base, after Part A's review); the protocol tag `protocol-v2` is `code_commit` plus data and documents only (`experiments/v2/`, `experiments/protocol-v2.yaml`, `docs/`). Every evaluation pod and local evaluation run executes the protocol tag exactly; record provenance carries the commit and runner hash, so a mismatched pod's records are refused by the resume rule rather than merged.
- Commits are unsigned (`git -c commit.gpgsign=false`) and end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; the author signs commits and every tag. Whole suite: `uv run pytest -q`.
- Code style matches the surrounding code: dense module docstrings citing the design section, short helper names, no chat formatting in comments.

## Review Focus

1. **A pod dies or is replaced mid-stage.** Rerunning the same stage on the same `--out` skips valid records and recomputes only missing or stale ones; records from a pod at another commit are refused, never merged. Pinned by Task 3 `test_check_commit_refuses_other_head` and Operation 7's preflight.
2. **The publication deadline.** The signed tag, protocol file, and upgraded proof must be public before block H = A + 144 is mined; a late push labels the draw nonconfirmatory (design 7.3). Pinned by Task 4 `test_draw_labels_late_publication_nonconfirmatory`.
3. **H4 fails after the lock.** A hash mismatch or load failure excludes H4, runs the manifest with `h4_excluded`, and reports the independently authored part of Q3 as unanswered; no repair. Pinned by Task 4 `test_h4_exclusion_is_recorded_and_changes_the_manifest` and Task 5 `test_q3_unanswered_without_h4`.
4. **A cap is hit during the evaluation.** Remaining cells are reported incomplete, no cell is replaced, and a question whose required cells are incomplete is reported unanswered (design 8.2). Pinned by Task 5 `test_incomplete_cells_make_questions_unanswered`.
5. **A family has no admitted multiplier.** kappa None gives "no confirmatory decision" for that family while estimates and descriptive intervals are still reported (design 9.5). Pinned by Task 5 `test_no_kappa_no_decision_but_estimates`.

---

## Part A: missing tools (test first, development data, no pods)

### Task 1: H4 session kit

**Files:**
- Create: `docs/revision/h4-brief.md`, `scripts/h4_check.py`, `tests/fixtures/h4_toy/h4/family.py`, `tests/fixtures/h4_toy/h4/containment.md`, `tests/test_h4_check.py`

**Interfaces:**
- Consumes: `sim.h4_loader.load`, `bundle_sha`, `_check`, `CHECK_CONSTANTS`, `BUNDLE_FILES`; `scripts.revision_v2.market`, `job`, `train_cell`, `eval_cell`; `sim.reference.twin_search`, `evaluate_gain`.
- Produces: `h4_check.load_check(bundle: Path) -> dict` (`{"ok": bool, "problem": str | None, "constants": [[200, 10], [100, 20]]}`); `h4_check.smoke(bundle: Path, rules=("F000", "F111"), markets=("dev0", "dev1")) -> dict` (per rule and market: twin and attack search at the smoke budget, gain on the smoke dev-val seeds); CLI `uv run python scripts/h4_check.py --bundle DIR` writes `DIR/h4/check.json` (`{"load": ..., "smoke": ..., "scipy": "1.18.1", "commit": <HEAD>}`) and prints `bundle_sha(DIR)`.
- The brief gives the session only: the `Family` interface (`sim/policies/families.py`), `ProviderView` (`sim/policies/base.py`), the admissible class (spec 4.0), the public constants T and L (design 5.1), the required exports `make_family(T: int, L: int) -> Family` named "H4" with `clip` last and binary, and `BINARY: tuple[str, ...]`, the containment note it must write, and the `h4_check.py` command. It names no rule internals beyond the describe record and nothing from `sealed/`.

- [ ] **Step 1: Write the failing tests** in `tests/test_h4_check.py`:

```python
def test_toy_bundle_passes_load_and_hash_round_trip(tmp_path):   # copy tests/fixtures/h4_toy, run h4_check.main(["--bundle", d, "--smoke"]); load(d, bundle_sha(d)) is an H4Source; check.json["load"]["ok"] is True
def test_missing_binary_or_wrong_name_fails_load_check(tmp_path): # toy variants: no BINARY -> ok False; Family named "X" -> problem mentions "H4"
def test_smoke_touches_development_seeds_only(tmp_path, monkeypatch):  # monkeypatch sim.instances.eval_seeds to raise; smoke() completes; every seed < 30_000_000
def test_check_json_is_inside_the_hash(tmp_path):                 # editing check.json changes bundle_sha
```

- [ ] **Step 2: Run** `uv run pytest tests/test_h4_check.py -q`; expected FAIL (no module).
- [ ] **Step 3: Implement** the toy family (D2+H3's knobs in a Family named "H4", `BINARY = ("x", "clip")`), `scripts/h4_check.py`, and the brief. `smoke` builds the family from the imported module's `make_family(T, L)` (the loader cannot be used yet: its hash covers `check.json`, which is written last).
- [ ] **Step 4: Run** `uv run pytest tests/test_h4_check.py tests/test_h4_loader.py -q`; expected PASS.
- [ ] **Step 5: Commit** `git add docs/revision/h4-brief.md scripts/h4_check.py tests/fixtures/h4_toy tests/test_h4_check.py && git -c commit.gpgsign=false commit -m "ops: H4 session kit (brief, load check, smoke, check.json)"`

### Task 2: Promotion of pulled outputs

**Files:**
- Create: `scripts/promote_v2.py`, `tests/test_promote_v2.py`
- Output (in operations): `experiments/v2/` (`comparator.json`, `tuned_{B3-t,R3-t,R4-t,C*-t}.json`, `fixture_cstar_s2.json`, `log/`, `params.json`, `coverage.json`, `benchmark/`, `promotion.json`)

**Interfaces:**
- Consumes: `scripts.tune_v2.COMMON_GRID`, `comparator_grid()`, `TOP`, `INNER`, `FAMILIES`; `scripts.coverage_v2` output layout; `scripts.benchmark_v2.cost_table`.
- Produces: `promote_v2.check_tuning(src: Path, markets: list[str]) -> list[str]` (problems; empty when valid); `promote_v2.check_coverage(src: Path) -> list[str]`; `promote_v2.params(dst: Path) -> dict` (`{"cred": comparator["cred"], "tuned": {name: {"tol", "L"}}}`, the `--params` file of `revision_v2.py`); CLI `--kind tuning|coverage|benchmark --from DIR --to experiments/v2 [--markets headline,dev0,dev1]` copies only after every check passes and appends `{path: sha256}` to `experiments/v2/promotion.json`.
- Checks (each a refusal with a message): `smoke` false everywhere; markets equal `--markets` (the development-cut branch of design 8.2 passes `headline,dev0`); the comparator has 12 scored configurations and 2 rechecks; each system has 16 scored configurations, 2 rechecks, grid order ties (`tune_v2.rank`), and C*-t's `cred` equals the comparator's; budgets equal `(1, 100, 3, 20)` inner and the locked full budget for rechecks; the fixture file has the C*/S2 searches for every market; coverage has `kappa` (number or null) for Q1 and Q4 and a `validation` block for every non-null kappa; the benchmark has `timings.json` with `smoke` false and `cost_table.json` recomputed equal by `cost_table`.

- [ ] **Step 1: Write the failing tests:** `test_valid_tuning_outputs_promote_and_params_match`, `test_smoke_or_partial_grid_is_refused` (one test per refusal above, parametrised), `test_cstar_t_cred_must_equal_comparator`, `test_coverage_null_kappa_is_allowed_but_needs_no_validation`, `test_benchmark_table_is_recomputed` (synthetic files written by the test from small dicts).
- [ ] **Step 2: Run** `uv run pytest tests/test_promote_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement** `scripts/promote_v2.py` (copy with `shutil.copy2`, hashes with `sim.records_v2.sha_file`).
- [ ] **Step 4: Run** `uv run pytest tests/test_promote_v2.py tests/test_tune_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `ops: promotion of pulled tuning, coverage, and benchmark outputs with validation`.

### Task 3: Protocol v2 writer and checker

**Files:**
- Create: `scripts/lock_v2.py`, `tests/test_lock_v2.py`, `docs/revision/predictions-v2.md` (filled in Operation 5; the task creates the template with the design 9.7 headings)
- Output (in operations): `experiments/protocol-v2.yaml`

**Interfaces:**
- Consumes: Task 2's `experiments/v2/promotion.json`, `params.json`, `coverage.json`, `benchmark/cost_table.json`; `sim.manifest_v2.doc()`, `effective(cuts, h4_excluded)`; `sim.h4_loader.bundle_sha` is not called (the author supplies the hash).
- Produces: `lock_v2.build(repo: Path, code_commit: str, cuts: int, h4_sha: str | None, approval: str | None) -> dict` and `lock_v2.check(repo: Path, protocol: dict) -> list[str]`; `lock_v2.check_commit(protocol: dict, repo: Path) -> None` (raises `SystemExit` unless the tree is clean, `HEAD` carries the tag `protocol-v2`, and `git diff --name-only code_commit HEAD` lists only paths under `experiments/v2/`, `experiments/protocol-v2.yaml`, `experiments/protocol-v2.yaml.ots`, or `docs/`); CLI `--write --code-commit SHA`, `--check`, `--check-commit`.
- `protocol-v2.yaml` fields: `version: 2`, `code_commit`, `manifest_sha256` (of `experiments/revision-v2-manifest.yaml`), `cuts`, `h4_bundle_sha256` (64 hex or `null` for "no bundle"), `params_sha256`, `promotion_sha256`, `kappa: {Q1: x|null, Q4: x|null}`, `coverage_sha256`, `cost: {development_usd, evaluation_usd, total_usd}`, `approval` (the author's sentence and date, required when `total_usd > 40`), `predictions_sha256`, `block: {rule: "H = A + 144", depth: 6, explorers: [blockstream.info, mempool.space]}`, `seeds: {eval_range: [30000000, 40000000], per_market: 200}`, `markets: [headline, fresh0..fresh5]`, `caps: {development: 12, evaluation: 40}`.

- [ ] **Step 1: Write the failing tests:** `test_build_and_check_round_trip`, `test_check_reports_each_changed_input` (parametrised over params, coverage, manifest, predictions, promotion), `test_total_above_40_needs_approval`, `test_check_commit_refuses_other_head` (temporary git repo: an untagged HEAD, a code change after `code_commit`, and a dirty tree each refuse; a data-only commit with the tag passes), `test_null_kappa_and_null_h4_are_written_as_null`.
- [ ] **Step 2: Run** `uv run pytest tests/test_lock_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement** `scripts/lock_v2.py` (YAML via `yaml.safe_dump(sort_keys=False)`).
- [ ] **Step 4: Run** `uv run pytest tests/test_lock_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `ops: protocol v2 writer and checker, predictions template`.

### Task 4: Draw to instances, and the H4 decision

**Files:**
- Create: `scripts/draw_v2.py`, `tests/test_draw_v2.py`
- Output (in operations): `results/v2/draw/instances.json`, `results/v2/draw/h4.json`

**Interfaces:**
- Consumes: `scripts/block_draw.py` final record (`{"status": "final", "height", "hash", "anchor", "headers", "tips"}`); `sim.instances.markets(root, 6)`, `eval_seeds(root, label)`, `identity_salt_hex(root)`, `calibrated(cfg)`; `sim.h4_loader.load`; Task 3's protocol.
- Produces: `draw_v2.instances(draw: dict, protocol: dict, published_at_height: int | None) -> dict` (`{"root", "height", "markets": {label: {"stream", "draws", "cfg", "calibration"}}, "seeds": {label: [200]}, "salt_sha256", "confirmatory": bool}`); `draw_v2.h4_decision(bundle: Path | None, protocol: dict) -> dict` (`{"loaded": bool, "reason": str | None, "h4_excluded": bool}`); CLI `--draw FILE --protocol FILE --published-height N [--h4 DIR] --out DIR`.
- `confirmatory` is false when `published_at_height` is missing or at least H (design 7.3); `root` must equal `draw["hash"]` as 64 lowercase hex; the anchor's Merkle root must match the protocol file's proof (block_draw already binds the file digest; `instances` re-checks `draw["anchor"]["status"] == "verified"`).

- [ ] **Step 1: Write the failing tests:** `test_instances_follow_the_generator_and_streams` (a fixed 64-hex test root; labels fresh0..fresh5, replacement order kept when a stream is monkeypatched to hit the limit), `test_draw_labels_late_publication_nonconfirmatory`, `test_root_must_be_lowercase_hex_and_final`, `test_h4_exclusion_is_recorded_and_changes_the_manifest` (toy bundle with a wrong hash: `h4_excluded` true and `manifest_v2.effective(cuts, True)` has no H4 cells), `test_seeds_are_in_the_evaluation_range_and_disjoint`.
- [ ] **Step 2: Run** `uv run pytest tests/test_draw_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement** `scripts/draw_v2.py`.
- [ ] **Step 4: Run** `uv run pytest tests/test_draw_v2.py tests/test_instances.py tests/test_block_draw.py -q`; expected PASS.
- [ ] **Step 5: Commit** `ops: draw to instances (confirmatory label, seeds, salt) and the H4 load decision`.

### Task 5: The report

**Files:**
- Create: `scripts/report_v2.py`, `tests/test_report_v2.py`
- Output (in operations): `results/v2/report/report.json`, `results/v2/report/report.md`

**Interfaces:**
- Consumes: the evaluate, cross, doubling, and freeze records under the evaluation `--out` (`scripts.revision_v2.eval_path`, `path_of`, `accept`); `sim.decisions_v2.q1_family`, `q2_contrasts`, `q4_markets`; `sim.intervals.bootstrap_pvalue`, `stratified_at`, `studentized_at`, `gmin_bounds`; Task 3's protocol (`kappa`, `cuts`); Task 4's `h4.json`.
- Produces: `report_v2.build(out: Path, protocol: dict, h4: dict, catalog: list[dict]) -> dict` with keys `q1`, `q2`, `q3`, `q4`, `doubling`, `incomplete`, `unanswered`; CLI `--out DIR --protocol FILE --h4 FILE --report DIR [--check]` (`--check` rebuilds and compares with an existing `report.json`, the reproduction entry of Task 6).
- Q1: per pair (F111 vs C*, R4 vs C*/S2) and family (D2+H3, X7-SC), six strata = per fresh market the per-seed difference of the two rules' gains on that market's evaluation seeds; `q1_family(tests, kappa_Q1)`. Q4: per fresh market, `p_a = bootstrap_pvalue(g_F000 - g_F111, 0.10, "lower")` under D2+H3, `p_b = bootstrap_pvalue(eff_F111, 0.90, "lower")`; `q4_markets([p_a...], [p_b...], kappa_Q4)`; wording "replicated on k of 6 sampled markets". Q2: `q2_contrasts` per market and family on the diagonal cell means and on the fixed-attack matrix rows (mean over the 8 rows), pooled over the six fresh markets with nominal 95 percent stratified intervals. Q3: per core rule the envelope family (the `envelope/<ctx>/<rule>` record's choice) with its evaluation gain; W0 and W1 lowest efficiency with the W1 constraint interval; coalition G_tot and G_min with `gmin_bounds(member_rows, 0.05)`. Doubling: per scheduled check the report's `incomplete` flag.

- [ ] **Step 1: Write the failing tests** (synthetic records written by a helper in the test, two-seed markets):

```python
def test_q1_strata_are_per_market_seed_differences():
def test_q4_wording_and_named_failures():                 # k of 6 and the failing market labels
def test_no_kappa_no_decision_but_estimates():            # kappa Q1 null -> category "no confirmatory decision", estimates present
def test_incomplete_cells_make_questions_unanswered():    # a missing evaluate record of a Q4 cell -> q4 unanswered, others answered
def test_q3_unanswered_without_h4():                      # h4.json loaded False -> q3["independent"] == "unanswered"
def test_report_refuses_an_unaccepted_context():          # a stale freeze -> SystemExit before any number is read
def test_check_mode_detects_a_changed_record():
```

- [ ] **Step 2: Run** `uv run pytest tests/test_report_v2.py -q`; expected FAIL.
- [ ] **Step 3: Implement** `scripts/report_v2.py` (`report.md` tables: Q1 categories, Q4 k of 6, Q2 contrasts, Q3 envelope, welfare, coalition, doubling; every interval labelled calibrated or nominal unadjusted, design 9.2).
- [ ] **Step 4: Run** `uv run pytest tests/test_report_v2.py tests/test_decisions_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `ops: report (Q1-Q4, doubling, incomplete and unanswered questions)`.

### Task 6: Reproduction and artifact check

**Files:**
- Create: `scripts/reproduce.py`, `scripts/artifact_check.py`, `tests/test_artifact.py`

**Interfaces:**
- Consumes: Task 5 `report_v2.build` and `--check`; Task 3 `protocol-v2.yaml`; Task 4 `instances.json`.
- Produces: `reproduce.main(argv) -> int` (rebuilds every report table from the records and exits non-zero on any difference); `artifact_check.required(repo: Path) -> list[str]` (protocol, proof, tag name, draw record with headers, instances, promoted inputs, all evaluation records, report, generator source, `uv.lock`) and `artifact_check.main` (missing files and hash mismatches against `promotion.json` and the freeze records).

- [ ] **Step 1: Write the failing tests:** `test_reproduce_matches_a_synthetic_report`, `test_artifact_check_lists_missing_and_changed_files`.
- [ ] **Step 2: Run** `uv run pytest tests/test_artifact.py -q`; expected FAIL.
- [ ] **Step 3: Implement** both scripts.
- [ ] **Step 4: Run** `uv run pytest tests/test_artifact.py -q && uv run pytest -q`; expected PASS, whole suite green.
- [ ] **Step 5: Commit** `ops: reproduction entry and artifact check`.

### Task 7: Execution priority in the runner

**Files:**
- Modify: `scripts/revision_v2.py` (`build_jobs`), `tests/test_revision_v2.py`

**Interfaces:**
- Consumes: `sim.manifest_v2.priority(cell) -> int` (0: Q1 and Q4 rules' matched cells; 1: other matched; 2: welfare, coalition, X5, H4; 3: the rest).
- Produces: `build_jobs` returns jobs in a stable order by `(market order, priority, manifest order)`; every stage's waves keep that order, so a stopped run has completed the highest-priority searches and evaluations first (design 8.2 "Execution priority").
- Ruling for the reviewers: a context evaluates nothing until all its required records are frozen (design 6.4), so priority orders work but cannot let a context evaluate early; a cap reached before a context's freeze leaves every question that needs that context unanswered. Operation 2 therefore sizes the caps on the full search budget, and Operation 7 runs the fresh markets (Q1, Q4) before the headline market's welfare and coalition work.

- [ ] **Step 1: Write the failing test** `test_jobs_run_in_priority_order` (`build_jobs(["dev0"], DEV_ROOT, True, True, CRED, 0, None, True)`: priorities are non-decreasing within each context, and ties keep manifest order).
- [ ] **Step 2: Run** `uv run pytest tests/test_revision_v2.py::test_jobs_run_in_priority_order -q`; expected FAIL.
- [ ] **Step 3: Implement** the stable sort in `build_jobs`.
- [ ] **Step 4: Run** `uv run pytest tests/test_revision_v2.py -q`; expected PASS.
- [ ] **Step 5: Commit** `ops: the runner builds jobs in execution-priority order`.

Part A ends with a Sol high and Astra high whole-branch review of Tasks 1 to 7 to consensus (as for the build), before any paid operation. The reviewed head is `code_commit`.

---

## Part B: operations (design 11 steps 2 to 9)

Each operation is logged in `docs/revision/operations-ledger.md` (date, commit, command, pod ids, cost, outputs and their hashes, deviations). "Author" steps are the author's; the executor prepares and checks.

### Operation 1: H4 sealed session (design 5.3) — author

- [ ] Executor: after Part A's review, tag `code_commit` as `h4-base` (author signs); hand the author `docs/revision/h4-brief.md`.
- [ ] Author: in a fresh clone at `h4-base`, start a fresh Codex `gpt-6.1-sol` session at high effort with the brief; the session writes `sealed2/h4/family.py` and `containment.md` and runs `uv run python scripts/h4_check.py --bundle sealed2`.
- [ ] Author: record the printed bundle hash in the operations ledger; move `sealed2/` to custody outside the repository; do not read it.
- **Exit check:** a 64-hex hash in the ledger; `sealed2/` absent from every tracked tree (`git ls-files | grep -c sealed2` is 0).
- **Stop rule:** if the session cannot make `h4_check` pass before the lock, the protocol records `h4_bundle_sha256: null` and Q3's independently authored part is unanswered.

### Operation 2: Benchmark and cost approval (design 8.2 "Benchmark first")

- [ ] Executor: `uv run python scripts/benchmark_v2.py --run --smoke --out results/v2/benchmark_smoke` locally (wiring check, no cost estimate).
- [ ] Executor: one 16-vCPU pod, cap 3 USD: `SCRIPT=scripts/benchmark_v2.py ROUT=results/v2/benchmark results/pods/explore_pod.sh <tarball> bench 3 results/v2/benchmark "--run"`; promote with `promote_v2.py --kind benchmark`.
- [ ] Executor: report the recomputed table (development, evaluation, total USD; flags). Author: approve in writing if `total_usd > 40`; the sentence goes into the protocol's `approval`.
- [ ] Executor: if `development_over_cap`, apply design 8.2 development cuts (markets `headline,dev0`, coverage branch `two20k`, then `two10k`); if still over, stop for the author. If `evaluation_over_cap`, choose the smallest `cuts` in 1..4 (`manifest_v2.CUT_ORDER`) that brings the evaluation under 40 USD; if none, stop for the author.
- **Exit check:** promoted `experiments/v2/benchmark/`; the chosen markets, coverage branch, and `cuts` in the ledger.

### Operation 3: Comparator selection, whole-system tuning, fixtures (design 3.3, 4)

- [ ] Executor: comparator first (C*-t needs its `cred`): one pod, `tune_v2.py --select comparator --markets <chosen> --out results/v2/tune_comparator`; pull; `promote_v2.py --kind tuning`.
- [ ] Executor: four pods in parallel, `--select B3-t | R3-t | R4-t | C*-t --comparator experiments/v2/comparator.json`, and one for `--select fixtures`; caps from the benchmark's per-row cost plus 25 percent; pull, promote, `params.json` written.
- **Exit check:** `promote_v2.py` exit 0; `experiments/v2/promotion.json` lists every file; development spend so far under 12 USD.

### Operation 4: Coverage check (design 9.5)

- [ ] Executor: one pod per coverage market, `coverage_v2.py --pools --inputs experiments/v2 --branch <chosen> --out results/v2/coverage`; pull the pools together; on one pod or locally, `--select` then `--validate`; promote `coverage.json`.
- **Exit check:** `kappa` for Q1 and Q4 (a number or null) with validation for each non-null value.

### Operation 5: Protocol v2, review, lock (design 2, 7.3, 9.7)

- [ ] Executor: draft `docs/revision/predictions-v2.md` from design 9.7 against the development results (directions only; no fresh data exists).
- [ ] Executor: `lock_v2.py --write --code-commit <h4-base sha> --cuts <c> --h4-sha <hash|none> --approval "<text>"`; `lock_v2.py --check`.
- [ ] Sol high and Astra high review the protocol and predictions to consensus (briefs in `docs/revision/roster/`).
- [ ] Author: `git commit -S` the protocol, `git tag -s protocol-v2`, `ots stamp experiments/protocol-v2.yaml`, push the tag, protocol, and pending proof; `ots upgrade` until the proof holds a Bitcoin attestation (hours); push the upgraded proof.
- **Exit check:** `lock_v2.py --check-commit` passes at the tag; the upgraded proof is public; the ledger records the push time and the tip height at the push (the `published_at_height` of Task 4).
- **Stop rule:** if the upgraded proof is pushed at or after block H, the draw is kept and labelled nonconfirmatory (design 7.3).

### Operation 6: Draw, instances, H4 decision (design 7)

- [ ] Executor: `uv run python scripts/block_draw.py --ots experiments/protocol-v2.yaml.ots --protocol experiments/protocol-v2.yaml --out results/v2/draw/draw.json` (polls hourly until final).
- [ ] Executor: `uv run python scripts/draw_v2.py --draw results/v2/draw/draw.json --protocol experiments/protocol-v2.yaml --published-height <N> --h4 <custody path> --out results/v2/draw` (H4 is loaded and verified here, before any evaluation-seed episode; the author provides the custody path without opening it).
- **Exit check:** `instances.json` with six fresh labels and 200 seeds per market; `h4.json`; `confirmatory` recorded.

### Operation 7: Evaluation on pods (design 6.4, 8.2)

- [ ] Executor: preflight on every pod, before any stage: `lock_v2.py --check-commit`; the protocol, `experiments/v2/params.json`, and (if loaded) the H4 bundle path present; `OMP_NUM_THREADS=1`.
- [ ] Executor: one pod per fresh market (`--markets fresh0` … `fresh5`) and two for the headline market, split by context (`--markets headline --select 'headline@rho0.2|*'` and `--select 'headline@rho1|*'`; a context never spans pods, because its dependent records need its own references), each running the stages in order with the same `--out`: `search`, `reference`, `dependent`, `freeze`, `evaluate`, `cross`, `doubling` (`revision_v2.py --stage S --root <hash> --params experiments/v2/params.json --cuts <c> [--h4 DIR --h4-sha HEX] --workers <vcpu>`). Pod caps sum to the evaluation estimate plus 25 percent and never past 40 USD in total.
- [ ] Execution priority (design 8.2): Q4 and Q1 cells first, then Q2, then Q3, then the rest; if a cap is hit, the remaining cells stay incomplete, nothing is replaced, and the ledger records the stop.
- [ ] Executor: pull each market's `--out` into `results/v2/eval/`; run `revision_v2.py --stage evaluate` locally once per market to confirm every context is accepted (no episode runs: every record is skipped).
- **Exit check:** every context's freeze accepted; spend under the evaluation cap; pods deleted and verified.

### Operation 8: Report and review

- [ ] Executor: `uv run python scripts/report_v2.py --out results/v2/eval --protocol experiments/protocol-v2.yaml --h4 results/v2/draw/h4.json --report results/v2/report`.
- [ ] Sol high and Astra high review the report against the protocol to consensus; the author then opens `sealed2/` for the first time and moves it into the repository (as `sealed/` entered after the first evaluation).
- **Exit check:** `report_v2.py --check` passes; reviews and consensus recorded.

### Operation 9: Artifact and paper revision

- [ ] Executor: `uv run python scripts/artifact_check.py` and `uv run python scripts/reproduce.py` pass on a fresh clone at the report commit.
- [ ] Executor: revise `paper/main.tex` with both evaluations (design 2, "the old record stays"); Sol and Astra review to consensus.
- [ ] Author: publish the GitHub release and the Zenodo DOI (design 10).
