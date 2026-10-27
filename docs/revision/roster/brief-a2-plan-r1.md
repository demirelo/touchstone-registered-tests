# Plan review, Part A2, round 1 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 1,000 words)

Review `docs/superpowers/plans/2026-10-27-revision-part-a2.md` (version 1). It implements design draft 7 (`docs/superpowers/specs/2026-10-22-revision-program-design.md`, accepted by you in round 9; section 14's "Code" column is the scope) on top of the Part A code on main `fee49c9`, which was built to draft 6 (`docs/superpowers/plans/2026-10-25-revision-operations.md`, version 9). Read the code the plan names: `experiments/revision-v2-manifest.yaml`, `sim/manifest_v2.py`, `sim/rules_v2.py`, `sim/mechanisms/credibility.py`, `sim/policies/x7.py`, `sim/policies/v2.py`, `sim/objectives_v2.py`, `sim/families_v2.py`, `sim/h4_loader.py`, `sim/calibration_v2.py`, `sim/decisions_v2.py`, `sim/intervals.py`, `scripts/revision_v2.py`, `scripts/h4_check.py`, `scripts/coverage_v2.py`, `scripts/tune_v2.py`, `scripts/promote_v2.py`, `scripts/benchmark_v2.py`, `scripts/lock_v2.py`, `scripts/report_v2.py`, and their tests.

Check with file:line evidence:
1. **Coverage:** does every item of design 14's Code column, and every draft-7 requirement in sections 3 to 9 and 11, have a task whose tests would fail against `fee49c9` and pass only with a correct implementation? Name any gap.
2. **Correctness against the code:** are the interfaces (names, signatures, record ids, counts 287 / 85 / 21 / 3 / 98 / 14 / 8 / 79 + 18, CELLS, COUNTS) consistent with the existing code and with each other across tasks? Name any wrong count, missing caller, or record the resume rule would wrongly reuse.
3. **Order and dependencies** between tasks; anything a later task needs that an earlier task does not produce.
4. **Review Focus:** are the five items the most likely failures, and are their tests sufficient?
5. **Part B changes (Task 11):** is the operations-plan revision complete (H4 after the defender freeze, decision after H4, commands, counts)?

Report only findings that change what a person running the operations gets; polish under Minor.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
FINDINGS: numbered, each with severity (Critical, Important, Minor), the task, file:line evidence, the failure scenario, and the repair.
CONFIDENCE: 0 to 1.
