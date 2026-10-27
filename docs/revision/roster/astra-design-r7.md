VERDICT: reject

CORRECTIONS:

1. **§3.4 — Replace the universal `A_tot = 2,500` claim with a bound.** `sim/instances.py` permits total capacity \(K\) from 40 to 80; validation does not require \(K\ge50\). Positive surplus gives \(n_{FB}=200\min(50,K)\), hence \(A_{tot}\in[2000,2500]\) at rho = 0.2. Therefore both reserves equal 500 at L = 10: **R4 equals R3, and C*/S2 equals C*, throughout the generator’s support.** At rho = 1, \(A_{tot}\in[400,500]\), so the reserves differ; on the headline market they are 500 and 250. The removal is correct, but 30 draws cannot prove the stated constant.

2. **§§6.4, 8.1, 8.2 — Repair the reference dependency broken by the whole-system cut.** Section 6.4 requires D2+H3 and X7-SC searches for every rule. Section 8.1 removes X7-SC from all three tuned systems on fresh markets. `scripts/revision_v2.py::expected_upstream` requires both searches for each reference. Either retain X7-SC as auxiliary reference-building searches and price them, or explicitly give all three secondary systems the same D2+H3-only menu on fresh markets. The current specification cannot execute its freeze order as written.

3. **§§5.2, 6.3 — Correct and complete X8-DB.** Its truthful projection must set beneficiary `clip = 1` **without changing `u_D`**. The decoy already has claim equal to effort. Forcing `u_D = 0` changes a truthful action and can omit a stronger reference, contrary to D5 and the simulator spec’s §5.2 clipping intervention. Keep full-effort decoys as additional candidates if wanted. Also specify the real-valued `n_D` rounding rule, whether failure resets restart its clock, and whether the beneficiary gate uses age after the current round’s reset. `sim/market.py` requests actions before applying exits, so this boundary matters. Specify which X6 schedule supplies the joint twin, or include both. **G_tot before reference selection, followed by G_min, is otherwise sound.**

4. **§5.2 — Make the X7 prose match its controller.** An age-rejected failure reset can still trigger a voluntary reset immediately or during the ban. State that this override is intended, or suppress it while waiting. Remove “an old identity is not the newest”: a replacement can remain newest indefinitely, as §3.3 itself states. Replace “shades only” at low exposure with “uses the fresh multiplier”; `k_F > 0` still permits shading. Specify the batch update of `p_own`: any failure sets it to zero; otherwise add passes. The stated D2+H3 embedding is algebraically preserved.

5. **§§5.3, 8.2, 11 — Bound H4’s actual evaluation work.** Fifteen knobs and 5 × 600 search evaluations do not bound corner checks. `revision_v2.controls` uses `Family.corners()` for H4, yielding up to **32,768** vectors, whereas X7 uses bounded Sobol controls. Register an equivalent bounded control procedure for H4, apply its doubled search budget in the runner, and require sealed-author timing evidence before the final cost decision. The initial benchmark occurs before H4 exists. The new defender-freeze order is correct; the claimed X7-equivalent cost is not yet supported.

6. **§§9.2–9.3 — Make the new reporting rules exact.** Define category 3 as “Holm rejects, and neither category 1 nor 2 applies”; “meets the margin boundary” is ambiguous. Failure of the efficiency lower-bound condition does **not** establish an efficiency cost. Report “efficiency non-inferiority unresolved” unless separate evidence supports a loss. Label any combined “better” statement as using descriptive efficiency evidence. Update the smallest bootstrap tail to 0.05/6: approximately 83 resamples, or 21 at κ = 1/4. Explicitly reject nonfinite bootstrap statistics or bounds; finite input checking alone does not state that rule.

7. **§§6.5, 8.1a — Separate missing results from search inadequacy.** Section 6.5 permits a confirmatory decision about the prescribed search procedure after a failed doubling check. Section 8.1a says any incomplete required cell makes that part unanswered. Use separate statuses for missing/invalid execution and a completed search that fails its quality check. State which status prevents Q1/Q4 decisions and which removes Q3 robustness claims. Include the scheduled checks in the question dependencies.

8. **§14 — Expand the Code column.** Add: D1/D18, tuned-rule lists, tuning orchestration, benchmark counts and cost accounting; D2, runner budgets and corner controls; D5, objective adapters, shared reference records and dependency validation; D12, evaluation-record production and schemas for service and false-failure refunds; D16, welfare winner selection and freeze records, not only cross-evaluation; D17, status propagation and question dependencies. Existing `GAIN_FIELDS`, H4 budget dispatch, and benchmark constants demonstrate these omissions. Add regression tests for these changes.

9. **Disposition and counts — Retain the other repairs.** D6–D10, D13, D16, and the selection/independent-validation change in D14 are sound in the design. No accepted finding needs reversal. The printed arithmetic checks: 287 search cells, 85 X7 cells, 21 H4 cells, 98 doubling checks, eight coverage profiles, and eight Q1 endpoints—not the triage’s 16. Costs remain provisional pending corrections 2 and 5. Python checks could not run: `uv run --no-sync python` was blocked by sandbox cache access. No pytest run completed.

ANSWERS:

**3.** Yes. Dropping R4-t is reasonable within the stated scope. On the common grid, reserve differences occur only at L = 50; rho = 1 directly tests the repair.

**4.** They represent both attack ideas as bounded tests, after corrections 3–4. They do not establish exhaustive attack coverage. X7 can retain age and condition shading on exposure; X8 provides distinct decoy and beneficiary roles.

**5.** Yes, after correction 6. A descriptive efficiency bound can accompany calibrated gain results, provided the combined “better” statement is not presented as a calibrated joint conclusion.

CONFIDENCE: 0.94.