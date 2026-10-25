# Review of the operations plan, round 1 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,200 words)

Plan: `docs/superpowers/plans/2026-10-25-revision-operations.md`. Spec: `docs/superpowers/specs/2026-10-22-revision-program-design.md` (accepted, round 6), especially sections 2, 5.3, 7, 8.2, 9.3 to 9.7, 10, 11. The code it runs is on this branch as built and reviewed (`docs/revision/build-ledger-2026-10-22.md`; consensus in `docs/revision/roster/consensus-design.md`): `scripts/revision_v2.py`, `tune_v2.py`, `coverage_v2.py`, `benchmark_v2.py`, `block_draw.py`, `sim/h4_loader.py`, `sim/manifest_v2.py`, `sim/decisions_v2.py`, `sim/intervals.py`. The pod launcher `results/pods/explore_pod.sh` is local and untracked; take its interface from the plan (USD cap, `SCRIPT`/`ROUT` overrides, pull then verified delete).

Check with file:line evidence:
1. Coverage: does every design 11 step 2 to 9 have an operation, and every piece of missing code a task? Name any step that cannot run with the code as built plus Tasks 1 to 7.
2. Interfaces: do the plan's commands and signatures match the built CLIs and functions (arguments, file layouts, record fields)? Name every mismatch.
3. Registration integrity: the H4 custody and no-read rule, the two-commit scheme (`code_commit`, protocol tag) and `check_commit`, the publication deadline and the nonconfirmatory label, the draw-to-instances checks, and the H4 load decision before any evaluation-seed episode.
4. Money: caps, the approval threshold, cut order, stop rules, pod sizing; can any paid step run before the benchmark and the approval?
5. The report (Task 5): do Q1, Q2, Q3, Q4 follow design 9.3 exactly (strata, tails, kappa use, wording, unanswered rules)?
6. The ruling in Task 7 (priority versus the complete freeze): accept or reject, with the reason.
7. Tests: would each named test fail against a plausible wrong implementation? Name weak ones.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
FINDINGS: numbered, each with severity (Critical, Important, Minor), plan section or file:line, failure scenario, repair.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
