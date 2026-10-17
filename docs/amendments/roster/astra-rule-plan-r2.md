**VERDICT: reject. CONFIDENCE: 0.97.**

Reviewed [v2](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/superpowers/plans/2026-10-17-proposed-rule.md), both round-1 reviews, the registered blocks, specified spec sections, allow-list, and code. Review was read-only. The sealed bundle remained unread. No simulations ran.

**Round-1 objections**

1. **RESOLVED — Forbidden file changes.** Phase A provides a separate amendment and lock tag; Phase B uses permitted paths (lines 7, 15, 102–110). Amendment scope still needs correction below.
2. **RESOLVED — Audit ordering.** Lines 17 and 98 require job-level selection, dynamic T2 ratios, and registered key ties.
3. **RESOLVED — Carry.** Lines 17 and 121 define available quota and store the unused early quota after selection.
4. **RESOLVED — H1 description.** Lines 18 and 84 require `not expressible` and acknowledge H1 INCONCLUSIVE.
5. **RESOLVED — Missing proposed search cells.** A1 adds development and H3 cells and tests their inventory (lines 42–46).
6. **OPEN — Bank and doubling completeness.** Shared development sources are supplied, but H3 doubling dispatch and final-evaluation bank ingestion remain unspecified.
7. **OPEN — F2.** The literal corner and profit-at-most-zero criterion are correct; replacing “allowance permits” with `k_t >= s` weakens coverage.
8. **RESOLVED — F3.** Line 20 uses audited exposure, distinguishes ban events from failed jobs, and restores the 0.90 kill.
9. **RESOLVED — F4.** Line 20 restricts gates to D2 and uses paired per-seed standard errors.
10. **RESOLVED — Fixtures and interfaces.** Recording helpers, dynamic T2 fixtures, quick-file rejection, and one objective signature replace the earlier contradictions.
11. **RESOLVED — B2 prices.** Lines 17, 69, and 73 require full precision and the locked file hash.

**NEW objections**

1. **MATERIAL — A4/A6, lines 20 and 108: F2 changes a registered condition.**  
   **Effect:** A missed sixth job can pass the coverage check despite sufficient round allowance.  
   **Support:** Amendment lines 152–154 require full auditing of a sole six-job entrant “when the allowance permits.” With `k=10`, `k_t=5`, and six entrant jobs, v2 requires only five targeted audits. It therefore exempts the counterexample identified in round 1. For T2, even `k_t >= s` does not guarantee full coverage: the entrant’s ratio rises after each selection.  
   **Repair:** Retain the six-job fixture and require full coverage when the total available round quota permits it. Test both targeting variants with controlled histories and keys; report failures as kills. Alternatively, explicitly register the weaker condition as a substantive change. Do not call that change orchestration-only.

2. **MATERIAL — A1/A2, lines 42 and 53–59: H3 transfer execution and accounting are incomplete.**  
   **Effect:** The implementation can omit compatible members or fail, while manifest totals omit the new work.  
   **Support:** `x=0` preserves D2 behavior. `x=1` adds exit-after-failure behavior; it is an additional policy transformation, not behavior-preserving containment. Both maps are precise, but [Bank](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/bank.py:29) routes evaluation through `_compatible` and obtains projections from `FAMILIES[target]`; `FAMILIES` contains only D1 and D2. [Manifest accounting](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/manifest.py:55) likewise excludes H3. Merely using `with_proposed` does not fix this.  
   **Repair:** Define transfer over the complete D2-compatible set, including embedded D1 members and corners; specify family resolution, deterministic ordering, origins, both projections, and shared hash validation. Add explicit H3 bank/reference run bounds and tests. Describe `x=1` as the additional replacement-policy transformation.

3. **MATERIAL — A1/A4, lines 42–44 and 85–88: H3 doubling still has no executable path.**  
   **Effect:** F5 cannot obtain its required doubling result from the prescribed sweep.  
   **Support:** A1 adds only the two locked D1/D2 controls. The [checks dispatcher](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:376) searches only `development` records. Adding an H3 control alone would still miss the `h3` record.  
   **Repair:** Specify either H3 dispatch in the sweep or an explicit harness call to `stage_checks`/`doubling_check`. Supply the bank-finalized attack, twin, projected members, and checked reference; persist the result and require `abs(delta_gain) < 0.005`.

4. **MATERIAL — A6/B2, lines 108 and 131: the final run loses development bank members.**  
   **Effect:** The final H3 comparison can use a different transfer set from F5.  
   **Support:** The retained evaluation run book starts `results/final` with only `heldout` cells. [build_bank](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:143) collects members only from development records in that same output directory. That final directory supplies none.  
   **Repair:** Specify validated ingestion of the frozen post-lock development bank into final evaluation. Verify source hashes, preserve its members and embedding definition, and refuse missing sources.

Amendment 2 is a legitimate way to register pipeline repairs before rule implementation. It needs no new claim merely because it adds drivers and tests. However, the F2 change must be removed or explicitly disclosed as substantive. The signed tag must cover the complete corrected procedure.

F3’s definitions are now sound. Count one ban event per identity-round with any failure. Measure lost capacity over actual banned rounds, clipped at the episode end; do not count each failed job as another ban.

| Criterion | Score |
|---|---:|
| Design and tuning fidelity | 7/10 |
| Admissible class and module rules | 9/10 |
| Statistical correctness | 8/10 |
| Executability | 6/10 |
| H1 description honesty | 10/10 |
| Completeness before freeze | 6/10 |
