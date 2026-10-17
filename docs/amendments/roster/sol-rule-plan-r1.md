Read-only review of [plan v1](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-proposed-rule.md). The sealed bundle remains unread. Tests were not run.

1. **Design and tuning fidelity: 5/10** — The objective matches the registration, but audit selection and falsification steps change registered choices.
2. **Admissible class and module rules: 3/10** — The proposed module boundary is sound; planned changes to frozen files prevent lock verification.
3. **Statistical correctness: 5/10** — The tuning formula and paired H3 bounds are correct; F3 and F4 need corrections.
4. **Executability: 3/10** — The sweep cannot produce required cells, and several prescribed tests contradict existing interfaces.
5. **H1 description honesty: 1/10** — The proposed labels omit the uniform half and terminal reserve; T2’s label also misstates its statistic.
6. **Completeness before freeze: 3/10** — Required development results, bank transfers, H3 doubling results, and terminal-settlement fixtures lack executable steps.

**OBJECTIONS**

1. **MATERIAL — Tasks 1–5, lines 36, 127–129, 146–157, 166.**  
   **Effect:** The final verification refuses the implementation.  
   **Support:** The [locked allow-list](/Users/oemer.demirel/Projects/touchstone/experiments/locked.yaml:81) excludes `sim/tuning.py`, new scripts, tests, and `README.md`. [verify_lock](/Users/oemer.demirel/Projects/touchstone/sim/claimcheck.py:302) rejects changed or newly tracked files outside that list. The amendment does not authorize these additions.  
   **Repair:** Keep development drivers and tests outside the frozen project tree. Use unchanged simulator interfaces. Commit only the three permitted rule artifacts and permitted documentation. Any broader change needs a separate registered amendment.

2. **MATERIAL — Task 1, lines 41, 110.**  
   **Effect:** Static identity ranking implements the wrong audit policy.  
   **Support:** Amendment lines 107–110 require T2’s ratio to change after **each** selection. Grouping all jobs of one ranked identity does not do this. T1 also requires job-level `audit_key` ordering across identities with equal `first_round`; identity grouping can violate that order.  
   **Repair:** Select one remaining job at a time. Recompute T2 priorities after each targeted selection. Break equal priorities by each job’s key. Add fixtures where the next selected identity changes.

3. **MATERIAL — Task 1, lines 41, 74, 110.**  
   **Effect:** Carry handling is incomplete and can discard unused quota.  
   **Support:** `audit_quota` lacks the served-job count, so it cannot determine final carry. Line 110 caps `k` without specifying the carry update. Amendment lines 93–97 require unused early quota to persist.  
   **Repair:** Define the helper as returning available quota. After selection, store `available_quota − actual_audits` during early rounds. Test consecutive undersubscribed rounds and entry into terminal rounds.

4. **MATERIAL — Tasks 1 and 3, lines 24, 95, 149–151.**  
   **Effect:** H1 receives an incomplete description while the tests certify it.  
   **Support:** [Vocabulary lines 32–39](/Users/oemer.demirel/Projects/touchstone/experiments/vocabulary.yaml:32) cannot describe this mixed policy or its reserve. `verify_describe_record` checks vocabulary membership and agreement with `rule.describe()`; it does not establish behavioural truth.  
   **Repair:** Set `audit_selection: not expressible` for both variants. Replace the test that prohibits this value with tests that require it and verify H1’s resulting status.

5. **MATERIAL — Task 6, line 175.**  
   **Effect:** The stated sweep produces no proposed-rule development or H3 search cells.  
   **Support:** [enumerate_manifest](/Users/oemer.demirel/Projects/touchstone/sim/manifest.py:97) removes `proposed` from the initial rules. Its later `with_proposed` cells are used for a bank-cost calculation, not appended. Proposed ablation cells are appended separately.  
   **Repair:** Add an external development driver that constructs the required `CellSpec` jobs explicitly. Assert the exact cell names, positions, budgets, seed sets, and record counts before launching.

6. **MATERIAL — Tasks 4 and 6, lines 159, 175.**  
   **Effect:** Neither the registered transfer bank nor the H3 doubling result is supplied.  
   **Support:** [build_bank](/Users/oemer.demirel/Projects/touchstone/scripts/sweep.py:143) uses development records in its output directory; the separate proposed directory contains no baseline sources. H3 is excluded from bank targets. The checks stage selects manifest `controls`, which contain neither proposed-rule nor H3 controls.  
   **Repair:** Specify validated baseline-source import, registered member transfers and projections, reference reselection, and an explicit H3 `doubling_check` call. Require complete provenance and a passing doubling result.

7. **MATERIAL — Task 4, line 159, F2.**  
   **Effect:** The test can miss the registered six-job failure.  
   **Support:** It specifies neither a sole six-job entrant fixture nor a precise unprofitability threshold. For T1 with `L=20`, early quota is eight or nine: only four or five audits are targeted. The uniform remainder does not guarantee coverage of all six entrant jobs, despite sufficient total allowance.  
   **Repair:** Test the literal registered corner with controlled entrant history and audit keys. Define the profit threshold explicitly. Report a resulting kill; do not increase targeting or weaken the gate to obtain a pass.

8. **MATERIAL — Task 4, line 159, F3.**  
   **Effect:** False-ban expectations are miscomputed, and the mandatory efficiency kill is absent.  
   **Support:** `N*T*served*Phi(...)` does not count audited exposure. With `a_it` audited jobs, expected failures use `a_it*p`; the provider-round probability of a ban is `1−(1−p)^a_it`. Amendment lines 155–157 explicitly kill efficiency below 0.90.  
   **Repair:** Use actual audited exposures, distinguish failures from ban events, report lost capacity, and implement the 0.90 kill. Keep 0.97 as a forecast.

9. **MATERIAL — Task 4, line 159, F4.**  
   **Effect:** The plan adds D1 kill conditions and leaves “two seed standard errors” ambiguous.  
   **Support:** Amendment lines 158–160 register **D2** at three positions. Shared seeds require the standard error of paired differences, not an unspecified combination of separate errors.  
   **Repair:** Restrict the registered gate to D2. Report D1 separately. Define paired differences, their standard errors, and the distinction between configuration failure and failure of the comparative claim.

10. **MINOR — Tasks 1–2, lines 65, 69–80, 127–137.**  
    **Effect:** Prescribed tests and signatures are inconsistent.  
    **Support:** Line 65 should expect `[1,3,0,2]`. `StateView` has no `assignment`; `EpisodeResult` has no `memory` or `N0`. `load_params` explicitly rejects quick results. The objective has two different signatures.  
    **Repair:** Correct the order, supply complete fixtures with a recording rule, test quick-result rejection, and select one objective signature.

11. **MINOR — Task 1, lines 17, 50.**  
    **Effect:** Rounded prices can break exact B2 equivalence.  
    **Support:** The locked B2 file stores full-precision prices.  
    **Repair:** Load those exact values in fixtures and production parameters.

**RULING**

`audit_selection` must be **`not expressible`**. Spec 5.4 explicitly prevents a coarse record from hiding a feature. Paper disclosure cannot correct the actor’s input. H1 against the proposed rule must therefore be **INCONCLUSIVE**.

**VERDICT: reject. CONFIDENCE: 0.97.**
