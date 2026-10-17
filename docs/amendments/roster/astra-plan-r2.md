**VERDICT: reject. CONFIDENCE: 0.94.**

V2 resolves most round-1 objections. Reference provenance and the smoke-test path remain incomplete. Final evaluation also needs an explicit extension-report check.

Read-only review completed against the consensus, specified spec sections, and source code. No files changed. The sealed bundle remained unread. Tests were not run.

Round-1 status, using [Sol’s numbering](/Users/oemer.demirel/Projects/touchstone/results/roster/sol-plan-r1.md):

1. **RESOLVED — H2 gate.** Plan lines 205, 216–217, and 263 pass the original H2 rule-clause status into the amended conjunction and test FAIL and INCONCLUSIVE.

2. **RESOLVED — Binding design registration.** Lines 382–384 specify the reserve formula, cumulative quotas, terminal use, count-update times, tuning grid, objective, rechecks, tie order, logging, and baseline disclosure; one wording defect remains below.

3. **RESOLVED — Remedy seed capacity.** Lines 46–48 and 60–72 reserve 400,000 seeds per cell, start replications after 70,000 pool positions, and test prefixes and overlap.

4. **RESOLVED — H3 manifest scope.** Lines 299–311 add explicit beta and position selectors; the locked `final_eval_n` is 40, consistent with the required sample size.

5. **RESOLVED — H3 record verification.** Lines 205–206 and 263 require record checks against rebuilt jobs and final seeds, unique seeds, complete rule coverage, pairing, and demotion handling.

6. **OPEN — Reference provenance remains copied, not measured.** Task 2, line 146 copies `base_report["provenance"]`; Task 6, line 341 compares that copy with the base but provides no current-reference input. [`check_record`](/Users/oemer.demirel/Projects/touchstone/scripts/sweep.py:81) checks configuration metadata, not the attack knobs or selected candidate. A changed reference can therefore retain the copied hash and pass these checks. **Repair:** hash the actual validated reference records, compare the complete map with the base before execution, and test a changed candidate that leaves selection unchanged.

7. **OPEN — The smoke integration path still conflicts with its fixture.** Task 2, line 166 specifies a fabricated **registered** base report; line 149 requires a **smoke** base report in smoke mode. Line 173 promises a real-sweep smoke run, while Task 8, line 422 rejects that route and substitutes the registered fixture. The listed Task 2 CLI also lacks an explicit synthetic-lock selector. **Repair:** define separate registered and smoke fixtures, expose `--locked` or fully specified `--repo` loading, and require one passing end-to-end smoke subprocess test.

8. **RESOLVED — Factory and amendment hash.** Lines 47 and 51 define `_factory_ext` and one canonical `amendment_hash`; lines 74–85 test registration-field stability, separate references, and abstention.

9. **RESOLVED — Registration closure and compute allowance.** Lines 385 and 422–424 require `--proposed none`, copied-report checking, the recorded original-tag delta, amendment-tag verification, and allowance for 9.36 million episodes.

The additional Astra objection on **strict admission is RESOLVED** by lines 55 and 87–99: exactly six selected cells, both finite endpoint measurements, and rejection tests. Its reporting objection is also resolved by the required public-stress-test label and proxy limitation.

**NEW objections**

- **MATERIAL — Task 4, line 263: final evaluation does not explicitly verify the extension report.**  
  **Effect:** A final invocation can use an unregistered or smoke report supplied through `--coverage-ext`.  
  **Support:** The plan requires `verify_amendment_report` only for `--verify-only`. The existing CLI verifies the base report before either verification-only return or evaluation ([source](/Users/oemer.demirel/Projects/touchstone/scripts/check_claim.py:109)); no existing check covers the new report. Tree verification does not authenticate an arbitrary external path.  
  **Repair:** Require extension-report verification on every non-synthetic amended evaluation, before reading admission decisions. Test wrong hash, smoke status, changed consequences, and changed selection through the final CLI path.

- **MINOR — Task 7, line 383: T1 ordering contradicts itself.**  
  **Effect:** The binding registration states both ascending and descending `first_round`, allowing opposite audit priorities.  
  **Support:** The text says “ascending `first_round` descending (newest first)”; consensus §4 requires newest first.  
  **Repair:** Specify descending `first_round`, then ascending `audit_key`; add a fixture with two identity ages.

Scores:

| Criterion | Score | Basis |
|---|---:|---|
| Fidelity to consensus and spec | **9/10** | Main scientific and design requirements are now explicit. |
| Statistical correctness | **8/10** | Statistic, remedies, admission, and decision boundaries are specified. |
| Executability | **6/10** | Smoke fixtures and CLI routing still conflict. |
| Registration integrity | **6/10** | Actual reference hashes and final report verification remain incomplete. |
| Feasibility and compute | **8/10** | Remedy allowance and throughput measurement are required; calendar remains unmeasured. |
| Completeness before amendment tag | **7/10** | Closure is specified, but the remaining validation gaps must be repaired before implementation approval. |
