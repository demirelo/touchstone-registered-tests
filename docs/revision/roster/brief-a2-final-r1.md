# Whole-branch review, Part A2, round 1 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 1,200 words)

Review the Part A2 implementation, `git diff fee49c9 HEAD` (main `fee49c9` was Part A built to design draft 6). It implements the accepted plan `docs/superpowers/plans/2026-10-27-revision-part-a2.md` (version 4; tasks 1 to 12) of design draft 7, `docs/superpowers/specs/2026-10-22-revision-program-design.md` (section 14's "Code" column is the scope). The executor's record is `docs/revision/part-a2-ledger-2026-10-27.md`: read every `Ruling:` line and weigh each decision; the Task 5 process deviation and the Task 12 quoted-path finding are recorded there. The operations plan's Part B was revised (`docs/superpowers/plans/2026-10-25-revision-operations.md`, "Changes in Part A2"), and the H4 brief (`docs/revision/h4-brief.md`).

Check, with file:line evidence:
1. **Correctness against design draft 7**, section by section (3.3-3.5, 5.2, 5.3, 6.2-6.7, 8.1, 8.1a, 8.2, 9.2-9.5, 11): anything implemented differently, missing, or reachable only through a test.
2. **The plan's Review Focus**, deliberately (quoted below): is each failure mode handled in the code, and do the named tests exercise the real path?
3. **The operations path**: run Part B in your head with this code (benchmark, tuning, defender freeze, H4 session and handoff, decision after H4, coverage, final, lock, draw, evaluation pods, verify, report). Name any command that would fail or any record that a later stage would refuse.
4. **Regressions** in Part A behaviour that draft 7 did not change, and the frozen files (`tests/test_frozen_files.py`, byte-identical to `2a288f5`). The frozen list also lives in `tests/test_robustness_v1.py` (`FROZEN`). Check `scripts/revision_v2.gain_fields`: it keeps the four profiles' episode results by rebinding `sim.reference.run_focal` for one `evaluate_gain` call, since `sim/cell.py` and `sim/reference.py` are frozen.
5. **Test quality**: tests that would pass against a wrong implementation.

Review Focus (from the plan):
1. Draft-6 records on disk after the change (R4 cells at rho 0.2, per-schedule joint references, 14-profile pools): refused as foreign, never reused.
2. A coalition group whose reference steps are incomplete or out of order: G_min not before the preliminary reference; evaluation not before the final reference and rescoring.
3. An H4 bundle outside the envelope (more than 15 knobs, no projection, unbounded knob): excluded at load with the reason; the runner never enumerates `Family.corners()` for it.
4. The distinct-rule check at the generator's ends (K = 40 and 80; rho = 1).
5. A fresh-market secondary system with a stray X7-SC record: its menu stays D2+H3-only and equal for B3-t, R3-t, C*-t.

Report only findings that change what a person running the operations gets; polish under Minor. Read-only sandbox: run pytest with `-p no:cacheprovider` (set `MPLCONFIGDIR` to a writable path if needed); say what you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, the failure scenario, and the repair.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
