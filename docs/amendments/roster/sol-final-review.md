**FINDINGS**

1. **Important — [sim/claimcheck.py:239](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/sim/claimcheck.py:239): Confirmatory verification accepts an amendment whose binding content differs from the registered report.**  
   Scenario: Copy the registered amendment outside the repository, change `gain_reduction_min` from `0.10` to `0.0`, retain its registration fields, and pass it through `--amendment`. The report checks pass, and evaluation uses the changed threshold. Tree verification does not cover that external file. An in-memory check confirmed that verification returns no problems despite a canonical amendment-hash mismatch.  
   **Fix:** Compare the report’s `amendment_sha256` with `amendment_hash(amend)`. Also verify that the supplied amendment matches the amendment in the registration tag.

2. **Important — [sim/claimcheck.py:190](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/sim/claimcheck.py:190): Early returns replace a known failure with INCONCLUSIVE.**  
   Scenario: An H2 rule-clause FAIL combined with an unadmitted extension returns amended INCONCLUSIVE. I reproduced this in memory. Missing or demoted H3 data can also hide the H2 failure. This contradicts the binding decision rule: “FAIL if any of these is FAIL.”  
   **Fix:** Preserve known FAIL statuses on every return path. Combine unavailable clauses as INCONCLUSIVE with the statuses already established.

3. **Important — [scripts/amend.py:82](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/amend.py:82): The registrar accepts gate evidence from unregistered check parameters.**  
   Scenario: In an otherwise accepted report, change the threshold check to `pools=1`, `reps=1`, or change the negative-control deficit from `1.5` to `90.0`. `validate_ext` still returns no problems. It also accepts inconsistent `analytic`, `simulated`, and `gap` values when the recorded flag satisfies its limited arithmetic check. Thus an easier or incomplete study can retain confirmatory admission.  
   **Fix:** Require the registered pool and replication counts and control deficit. Check value ranges, derive `gap` from the reported values, and verify the analytic value against the registered calculation.

4. **Important — [scripts/amend.py:53](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/amend.py:53): Registration does not verify all original registered artifacts.**  
   Scenario: Change `experiments/calibration_T100.json` or the registered pilot while leaving the extension inputs unchanged. Neither artifact is checked, so registration can still succeed. Changing the T100 hash in the supplied lock dictionary also produced no validation problems in memory. This misses the plan’s explicit requirement to verify registered artifacts against the original lock.  
   **Fix:** Verify `locked.yaml` and all original registered artifacts against the original lock tag. Check the T100 calibration against its committed hash before registration and `--check`.

5. **Minor — [scripts/amend.py:132](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/amend.py:132), [scripts/coverage_ext.py:110](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/coverage_ext.py:110): The new commands omit the required `--repo` option.**  
   Scenario: Supplying `--repo <checkout>` causes an argument error; the default lock always comes from the script’s checkout.  
   **Fix:** Add `--repo` and resolve default paths beneath it, as required by the Global Constraints.

**DECLINED TO JUDGE**

- Full-suite and end-to-end smoke results: pytest could not start because the sandbox denied temporary files; verification used code inspection and in-memory checks.
- Extension throughput, calendar estimates, and Task 8 operations: these remain pending.
- Proposed-rule forecasts and sealed-family performance: no proposed-rule evaluation was performed; the sealed bundle stayed unread.

**VERDICT: request-changes**  
**CONFIDENCE: 0.94**
