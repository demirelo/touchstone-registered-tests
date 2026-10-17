- **RESOLVED — Reference provenance.** Task 2, [line 146](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md:146), requires fresh hashes from the validated universe, comparison before simulation, and a changed-candidate refusal test.
- **OPEN — Smoke integration.** The lock option and separate fixtures are specified, but the required smoke path still conflicts with the selection check; details below.
- **RESOLVED — Cell sample sizes.** Task 6, [line 357](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md:357), checks every cell’s factors and counts against the selected attempt; line 366 adds mutation tests.
- **RESOLVED — Proposed-rule input.** Task 3, [line 218](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md:218), supplies `proposed`; the tests use the new signature.
- **OPEN — Final extension-report verification.** Task 4 adds the check, but its “with a recorded hash” condition leaves an unchecked path; details below.
- **RESOLVED — T1 order.** Task 7, [line 399](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md:399), specifies descending `first_round`, then ascending `audit_key`.

The two OPEN objections need these repairs:

- **MATERIAL — Task 2, [lines 149 and 152](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md:149): incompatible smoke selection.** **Effect:** The required successful subprocess test cannot satisfy the specified selection check. **Support:** The fixture uses the existing smoke sweep, whose [`SMOKE_BUDGET.n_train` is 1](/Users/oemer.demirel/Projects/touchstone/sim/schedule.py:20). Both ranking statistics therefore return NaN, and [`select_cells`](/Users/oemer.demirel/Projects/touchstone/sim/coverage.py:49) returns no cells. The smoke base report instead selects [`sorted(universe)[:6]`](/Users/oemer.demirel/Projects/touchstone/scripts/coverage_study.py:154). **Repair:** Specify that extension smoke mode uses and checks the same unranked selection as the smoke base report. Retain recomputed ranked selection for registered runs.

- **MATERIAL — Task 4, [line 275](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md:275): null registration hash skips verification.** **Effect:** The specification permits an amended evaluation to read admission decisions from an unregistered extension report. **Support:** Verification applies only when the amendment has a recorded hash; Task 7 initially sets that hash to null, and no evaluation refusal is specified for this case. **Repair:** Refuse non-synthetic amended evaluation when the registration hash is absent. Permit an unregistered amendment in `--verify-only` only if no extension admission decisions are read. Add a null-hash CLI refusal test.

**NEW objections:** None separate from these remaining round-2 issues.

Read-only source review. No tests run. The sealed bundle remained unread.

**VERDICT: reject**  
**CONFIDENCE: 0.96**
