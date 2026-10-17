**VERDICT: reject. CONFIDENCE: 0.97.**

Read-only review of v3 and both round-2 reviews. No files changed. The sealed bundle remained unread. Tests were not run.

Round-2 objections, with line references to [v3](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md):

1. **RESOLVED — Reference provenance.** Task 2, lines 146 and 165–166 require recomputed reference hashes, comparison before simulation, and rejection of a changed candidate.
2. **OPEN — Smoke integration.** Task 2, lines 149–166 still require ranked selection for smoke data, which cannot produce that selection; see below.
3. **RESOLVED — Cell sample sizes.** Task 6, lines 357 and 366–367 require each cell’s factors and counts to match the selected attempt, with mutation tests.
4. **RESOLVED — Proposed-rule input.** Task 3, lines 218 and 239–241 supply `proposed` explicitly in the interface and tests.
5. **OPEN — Extension-report verification.** Task 4, line 275 verifies only amendments “with a recorded hash”; it does not require refusal when an amended evaluation has no recorded hash.
6. **RESOLVED — T1 ordering.** Task 7, line 399 specifies descending `first_round`, then ascending `audit_key`.

The remaining smoke defect is **MATERIAL**. The existing smoke budget uses one training seed ([source](/Users/oemer.demirel/Projects/touchstone/sim/schedule.py:20)). Both ranking statistics therefore return NaN, and `select_cells` excludes them ([source](/Users/oemer.demirel/Projects/touchstone/sim/coverage.py:36)). The base smoke script instead selects `sorted(universe)[:6]` ([source](/Users/oemer.demirel/Projects/touchstone/scripts/coverage_study.py:154)). Thus, Task 2’s unconditional comparison with `select_cells` rejects the required smoke fixture. **Repair:** specify the same unranked six-cell selection for extension smoke runs; retain ranked selection for registered runs.

The remaining verification defect is **MATERIAL**. Task 7, line 398 explicitly creates an amendment with a null report hash. Task 4 neither verifies nor explicitly blocks admission use in that state. **Repair:** refuse non-synthetic amended evaluation without both registration fields. If verification-only mode permits a draft amendment, explicitly skip amended evaluation and report its unregistered state. Add a null-hash CLI refusal test.

**NEW — MINOR — Task 2, line 152; Task 6, line 362: fixture wiring is inconsistent.**  
**Effect:** Tests can fail during setup before they reach the required checks. **Support:** The existing `cal_path` is module-scoped and defined only in [test_sweep.py](/Users/oemer.demirel/Projects/touchstone/tests/test_sweep.py:9); the new session-scoped fixture cannot directly depend on it. Task 6 also requests `fake_registered_inputs`, while Task 2 defines `registered_inputs`. **Repair:** move or create a shared session-scoped calibration fixture, use one registered-fixture name, and include `tests/conftest.py` in Task 2’s file and commit lists.
