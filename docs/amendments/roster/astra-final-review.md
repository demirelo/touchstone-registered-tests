**FINDINGS**

1. **Important — [scripts/check_claim.py:121](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/check_claim.py:121), [sim/claimcheck.py:240](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/sim/claimcheck.py:240): An external amendment can change the confirmatory threshold without failing verification.**  
   **Scenario:** Copy the registered YAML outside the repository, change `gain_reduction_min` from `0.10` to `0`, and retain its report hash and consequences. Pass this copy through `--amendment`. Git checks cover the repository, and report verification never compares `amendment_sha256` with the supplied document. A probe confirmed no verification errors despite the hash mismatch. With H2 PASS and H3 gains near `R=0.05`, `B2=B3=0.10`, the change turns FAIL into PASS.  
   **Fix:** Bind confirmatory input to the canonical amendment protected by the registration tag. Also compare the report’s amendment hash with `amendment_hash(amend)`.

2. **Important — [scripts/amend.py:97](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/amend.py:97), [sim/amendment.py:216](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/sim/amendment.py:216): A NaN threshold allows zero measured coverage to receive confirmatory admission.**  
   **Scenario:** In an otherwise valid report, set the `40|0.9875` threshold to NaN and both measured coverages to zero in every cell. The threshold comparison and admission comparisons do not reject NaN. A probe returned no validation errors and retained `h3_comparative: confirmatory`.  
   **Fix:** Require finite thresholds in the valid probability range before comparison or admission. Reject non-finite JSON values and compare the threshold with its recomputed value.

3. **Important — [sim/claimcheck.py:190](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/sim/claimcheck.py:190): Failed extension admission suppresses failures in independent clauses.**  
   **Scenario:** Supply valid H3 rows, an exploratory extension report, and `h2_rule_status=FAIL`. The function returns INCONCLUSIVE immediately. It also returns INCONCLUSIVE when H2 passes but H3 efficiency fails an admitted absolute bound. Both cases were reproduced. The binding decision rule requires FAIL when any component fails.  
   **Fix:** Evaluate the available absolute clauses independently. Set the unadmitted comparative clause to INCONCLUSIVE, then combine all statuses so an established H2 or H3 failure remains FAIL.

4. **Important — [scripts/amend.py:82](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/scripts/amend.py:82): The registrar accepts gate evidence that contradicts the registered test design.**  
   **Scenario:** Starting from a valid report, change the threshold check to one pool and one replication, with `simulated=0` but the old `gap=0` and passing flag. Validation still returns no problems. A separate probe with `power_200=power_400=50` and an incorrect deficit also passes. Thus registration can accept evidence that does not establish the required gate.  
   **Fix:** Check registered pool counts, replication counts, and deficits; constrain probabilities to `[0,1]`; and derive the threshold-check gap from the analytic and simulated values before checking its pass flag.

5. **Important — [tests/test_coverage_ext_script.py:55](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/tests/test_coverage_ext_script.py:55): The required end-to-end smoke test contains an assertion that cannot pass.**  
   **Scenario:** Smoke mode uses ten fixture trials. Even ten admissions produce a lower confidence limit of approximately `0.664`, below `0.9`, so the gate selects both remedies and every cell uses `pool_factor=2`. The test requires `pool_factor=1`. A direct gate probe confirmed `(2,2)`. The run-book smoke command therefore fails if execution reaches this assertion.  
   **Fix:** Check cell factors against the gate’s selected remedy and verify the corresponding sizes. Run and record the full smoke path before registration; leaving it skipped does not satisfy the plan’s required passing subprocess test.

6. **Minor — [docs/lock-runbook.md:81](/Users/oemer.demirel/Projects/touchstone/.worktrees/amendment-1/docs/lock-runbook.md:81): The timestamp command names a file that the instructions never create.**  
   **Scenario:** Follow the registration commands: `ots stamp docs/lock-2026-10-17-amendment-1.txt` has no input file. That file is absent, and preceding commands do not generate it.  
   **Fix:** Add a command that writes the resolved registration tag commit and required metadata to the file before stamping it.

The specified abstain cases, seed prefixes and separation, four H3 record-error cases, and changed tuned/reference provenance checks behaved as required in read-only probes. The original predicate and registered artifacts are unchanged in the reviewed range.

**DECLINED TO JUDGE**

- Full-suite and end-to-end execution: pytest collection was blocked by Matplotlib’s writable-cache requirement; four pure test functions and targeted probes ran with optional plotting disabled.
- Production coverage results, throughput estimates, signatures, and timestamp completion: these remain Task 8 operations.
- Sealed-family behavior and paid APIs: neither was accessed.

**VERDICT: request-changes**  
**CONFIDENCE: 0.96**
