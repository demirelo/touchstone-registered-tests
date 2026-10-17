V2 resolves most round-1 objections. Two remain open, and one new material validation gap remains. This was a read-only source review. No files changed; the sealed bundle remained unread. I did not run tests.

All plan line references below refer to [v2](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md).

Round-1 objections, in the original Sol numbering:

1. **RESOLVED — H2 gate.** Lines 17, 205–217, and 263 require the original H2 rule-clause status in the amended conjunction and test H2 FAIL and INCONCLUSIVE.

2. **RESOLVED — Binding design registration.** Lines 382–384 specify the reserve, cumulative quotas, carry, targeting, count updates, tuning grid, objective, rechecks, logging, and baseline-objective disclosure.

3. **RESOLVED — Remedy seed capacity.** Lines 20 and 46–65 reserve 400,000 seeds per cell, separate the doubled pool from replications, and test prefixes and disjointness.

4. **RESOLVED — Manifest scope.** Lines 298–310 add an explicit beta selector and require median-only, beta-0.05 final H3 cells; lines 18 and 385 require the public stress-test label.

5. **RESOLVED — H3 verification requirement.** Lines 205–206 and 263 require record checks, exact final-evaluation seeds, unique rows, complete rules, and seed pairing; a minor signature defect remains below.

6. **OPEN — Provenance of the reference records actually used.** Task 2, line 146 copies reference hashes from the base report; Task 6, line 341 compares those copied hashes with the base again. Neither step explicitly hashes the current universe records. Changing only a reference candidate can evade [the existing record check](/Users/oemer.demirel/Projects/touchstone/scripts/sweep.py:81). Require freshly computed hashes to equal the base commitments before simulation, and test this mutation.

7. **OPEN — Executable smoke integration.** Task 2, line 144 provides no `--locked` or `--repo` option for the synthetic lock at line 166. Line 173 still requires the real sweep, while Task 8, line 422 requires the fixture. That fixture fabricates a registered base report, but line 149 requires a smoke base report under `--smoke`. Specify one successful synthetic CLI path, its lock option, and compatible smoke artifacts; test it before operations.

8. **RESOLVED — Factory and amendment hash.** Lines 47 and 51 define `_factory_ext` and one canonical hash; lines 74–85 test registration-field stability and different references, including abstention.

9. **RESOLVED — Closure and compute allowance.** Lines 22, 385, and 422–424 require `--proposed none`, copied-report checking, recorded original-tag differences, amendment-tag verification, and allowance for 9.36 million episodes.

The other seat’s separate **strict six-cell admission objection is RESOLVED** by lines 55 and 90–99.

New objections:

- **MATERIAL — Task 6, line 341: cell sample sizes are not validated.**  
  **Effect:** A report can satisfy the specified validator with six finite coverage measurements while a cell records fewer pool observations or replications than the selected attempt requires.  
  **Support:** Line 341 checks attempt-level M/R, but omits each cell’s `pool_size`, `replications["40"]`, and factors. The base validator explicitly checks these at [scripts/lock.py:94](/Users/oemer.demirel/Projects/touchstone/scripts/lock.py:94). Admission cannot recover sample counts from coverage proportions.  
  **Repair:** Require every cell’s factors and counts to match the selected attempt. Add rejection tests that change only a cell’s count or factor while leaving its measurements and attempt evidence unchanged.

- **MINOR — Task 3, line 206: missing proposed-rule input.**  
  **Effect:** The specified rule-presence check refers to `proposed`, but the function signature does not supply it.  
  **Support:** `verify_h3_records(records, locked, jobs, expected_seeds)` requires `BASELINES + (proposed,)`; the caller’s `--proposed` value is not an input.  
  **Repair:** Add `proposed` to the signature and update the CLI call and fixtures, or explicitly define how the required rule is derived from `jobs`.

| Criterion | Score | Support |
|---|---:|---|
| Fidelity to consensus and spec | **9/10** | The H2/H3 conjunction, public-family label, and design registration now match. |
| Statistical correctness | **8/10** | Statistic, bounds, seeds, and admission gate are specified; cell-count validation remains incomplete. |
| Executability | **6/10** | The smoke path and one verification signature still need repair. |
| Registration integrity | **6/10** | Current reference records are not explicitly checked against their copied commitments. |
| Feasibility and compute | **8/10** | Base and remedy episode allowances are correct; measured throughput determines the calendar. |
| Completeness before amendment tag | **6/10** | Closing steps are specified, but successful integration and complete report validation remain requirements to fix. |

**VERDICT: reject**  
**CONFIDENCE: 0.94**
