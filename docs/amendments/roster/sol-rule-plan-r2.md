Read-only review of [v2](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/superpowers/plans/2026-10-17-proposed-rule.md). The sealed bundle remains unread. No simulations or tests ran.

Round-1 objections, in the Sol review’s original order:

1. **RESOLVED — Frozen-file changes.** Phase A registers the pipeline changes before Phase B; Phase B uses the allow-listed paths (lines 7, 15, 102–110).
2. **RESOLVED — Audit ordering.** Job-level selection and T2 recomputation after each selection match amendment lines 103–110 (lines 17, 96, 121).
3. **RESOLVED — Carry.** Available quota and the subsequent carry update are explicit, with undersubscription fixtures (lines 17, 98, 121).
4. **RESOLVED — H1 description.** Both variants require `audit_selection: not expressible`; H1 is INCONCLUSIVE (lines 18, 84).
5. **RESOLVED — Missing development/H3 cells.** A1 specifies their addition and the required inventory (lines 42–44).
6. **OPEN — Bank transfer and H3 doubling.** The common output directory supplies baseline sources, but A1 adds only the two locked D1/D2 controls; the checks selector still requires `section == "development"` (`scripts/sweep.py:378–383`). No executable H3 doubling path is specified.
7. **OPEN — F2.** Line 20 conditions full coverage on **targeted quota** `k_t ≥ s`, replacing the registered “allowance permits” condition. With six entrant jobs and ten available audits, it can accept five targeted audits and a missed sixth job. Restore the six-job fixture with sufficient total allowance; report a missed job as a kill. The entity-profit-at-most-zero criterion is now correct.
8. **RESOLVED — F3.** Expected failures use audited exposure; expected ban events use `1−(1−p)^a`; the mean-efficiency-below-0.90 kill is explicit (line 20). These formulas fit the independent Gaussian job noise. Count ban events once per identity-round and truncate lost-capacity accounting at the episode end.
9. **RESOLVED — F4.** The gate is restricted to D2 and uses paired per-seed differences; D1 is reported separately (line 20).
10. **RESOLVED — Interfaces and fixtures.** Recording helpers replace nonexistent result fields, quick files are rejected, and one objective signature is specified (lines 70–75, 93–98).
11. **RESOLVED — B2 prices.** Production parameters and fixtures use the full-precision, hash-checked file (lines 17, 73).

Amendment 2 is a legitimate registration route for the missing orchestration. It needs a public signed tag, timestamp, recorded delta against amendment 1, and verification that the registered artifacts retain their hashes. Verification against the **new tag alone** cannot establish that preservation. The F2 change prevents the current package from being described as “orchestration only.” Preserve the original gate, or explicitly register and disclose a substantive gate amendment.

New objections:

- **MATERIAL — A2, lines 53–59: incomplete H3 transfer definition and execution path.**  
  **Effect:** H3 bank evaluation can fail or omit compatible candidates.  
  **Support:** `Bank.evaluate` calls `_compatible` directly; changing `members_for` alone does not change evaluation. `_compatible` and `projected_members_for` index `FAMILIES[target]`, while `FAMILIES` contains only D1/D2 (`sim/bank.py:29–65`; `sim/policies/families.py:108`).  
  **Repair:** Specify one public-family resolver and shared compatibility path for membership, evaluation, corners, and projections. Compose D1→D2→H3 transfers. Define `x=0` as the behavior-preserving embedding and `x=1` as an additional exit-policy transfer: it changes D2 behavior after failures. Test `x=0` trajectory equivalence, both transfer variants, and clip projections. Update bank-hash creation and verification together.

- **MATERIAL — A3, lines 71–75: the selected serializer loses required logs.**  
  **Effect:** The persisted records cannot establish every evaluation or recover the promised search trace.  
  **Support:** `search_to_json` omits `SearchResult.trace`; its archive stores unique policies, and the search trace itself records iteration incumbents (`sim/records.py:25–31`; `sim/search.py:60–68,132`).  
  **Repair:** Add an ordered evaluation log with knobs, source, seeds, and scores, including repeated evaluations. Persist traces explicitly. Test log completeness for both families and rechecks.

- **MATERIAL — A1/A6/B2, lines 42–44, 108, 129: registered workloads remain omitted.**  
  **Effect:** The completed run lacks required diagnostics despite the proposed cell inventory passing.  
  **Support:** Spec 5.3 requires the rho sweep for every rule. A1 excludes it. The run command excludes `all_deviators`; its executor also selects `section == "all_deviators"`, whereas the existing proposed entry uses `all_deviators_post_lock` (`sim/manifest.py:116`; `scripts/sweep.py:389–391`).  
  **Repair:** Add the proposed rho cells, correct the all-deviators selection, include both in the run command, and assert output completeness.

- **MINOR — A1/A2, line 42: H3 bank workload is uncounted.**  
  **Effect:** The authoritative manifest understates the amended workload.  
  **Support:** `_bank_total` counts only families returned by `bank_members`, currently D1/D2 (`sim/manifest.py:55–62`).  
  **Repair:** Include H3 transfer and projection bounds in the amended accounting.

| Criterion | Score |
|---|---:|
| Design and tuning fidelity | 7/10 |
| Admissible class and module rules | 8/10 |
| Statistical correctness | 8/10 |
| Executability | 5/10 |
| H1 description honesty | 10/10 |
| Completeness before freeze | 5/10 |

**VERDICT: reject. CONFIDENCE: 0.97.**
