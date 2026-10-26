# Final whole-branch review of the operations plan's Part A (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,500 words)

You are run at the tip of the branch. Range: `6173cad..HEAD` (`git diff 6173cad...HEAD`). Plan (accepted by both seats, round 9): `docs/superpowers/plans/2026-10-25-revision-operations.md`, Part A, Tasks 1 to 10; design: `docs/superpowers/specs/2026-10-22-revision-program-design.md`. The executor's ledger, with every ruling and deviation (`Ruling:` lines) and each task's test run, is `docs/revision/operations-build-ledger-2026-10-26.md`.

New and changed code: `scripts/h4_check.py`, `docs/revision/h4-brief.md`, `scripts/tune_v2.py`, `scripts/coverage_v2.py`, `scripts/benchmark_v2.py`, `scripts/budget_v2.py`, `scripts/promote_v2.py`, `scripts/lock_v2.py`, `docs/revision/predictions-v2.md`, `scripts/draw_v2.py`, `scripts/block_draw.py`, `scripts/revision_v2.py`, `scripts/report_v2.py`, `scripts/artifact_v2.py`, `scripts/reproduce.py`, and their tests (`tests/test_h4_check.py`, `test_tune_v2.py`, `test_calibration_v2.py`, `test_benchmark_v2.py`, `test_budget_v2.py`, `test_promote_v2.py`, `test_lock_v2.py`, `test_draw_v2.py`, `test_block_draw.py`, `test_revision_v2.py`, `tests/_verify_child.py`, `test_report_v2.py`, `test_artifact.py`).

The plan's Review Focus (input classes its tests do not fully exercise); check each deliberately:

1. **A pod dies, is replaced, or runs another commit.** Rerunning a stage on the same `--out` reuses valid records, recomputes stale ones, and refuses foreign ones (the resume rule); a pod whose checkout is not the protocol tag stops before any episode. Pinned by Task 6 `test_check_commit_refuses_other_head_or_unsigned_tag` and Task 8 `test_verify_stage_runs_no_episode`.
2. **The publication deadline.** Tag, protocol, and upgraded proof public before block H = A + 144; else the draw is kept and every claim is labelled nonconfirmatory (design 7.3). Pinned by Task 7 `test_late_publication_is_nonconfirmatory` and Task 9 `test_nonconfirmatory_draw_has_no_confirmatory_claim`.
3. **H4 fails or differs between pods.** One recorded decision; every pod enforces it; a failure excludes H4 for all and the independently authored part of Q3 is unanswered. Pinned by Task 7 `test_h4_decision_records_exclusion`, Task 8 `test_pods_enforce_the_h4_decision`, Task 9 `test_q3_unanswered_without_h4`.
4. **A cap is hit.** Missing cells are reported, nothing is replaced, and each question whose required cells are missing is unanswered. Pinned by Task 9 `test_missing_cells_make_dependent_questions_unanswered`.
5. **A family's multiplier fails validation.** Only an admitted kappa reaches the protocol; otherwise "no confirmatory decision" with estimates and descriptive intervals. Pinned by Task 3 `test_failed_validation_exports_null` and Task 9 `test_no_kappa_no_decision_but_estimates`.

Check with file:line evidence: (1) each task matches the plan's interfaces and the design (registration integrity: admitted kappa only, draw bound to the proof's lowest anchor, two commits and the signed tag, H4 custody and the one decision; money: wave bounds, reservations, the combined approval gate, the frozen decision; the read-only verify; the report's question dependencies, tails, kappa use, wording, and nonconfirmatory handling); (2) correctness bugs that would change a registered number, let a paid step run without its gate, let evaluation run on a stale freeze, or let a report claim more than the records support; (3) tests that would pass with a plausible wrong implementation; (4) the rulings: say which you reject and why; (5) the twelve frozen files are byte-identical to `2a288f5`.

You run in a read-only sandbox: run pytest with `-p no:cacheprovider`; tests that write files may fail for that reason alone; say which you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
