VERDICT: reject

CORRECTIONS:

1. **§13 — Separate resolved and partial corrections.** At design level, S2/A2, S3/A3, S5/A4, S6/A5, S10/A10, A7, and A12 are resolved: overload wording, matched parameters and pacing, regression suites, tuning grid, neighbourhood scope, common references, and sampled-market inference. A1 is substantially resolved. S1 remains partial; the other corrections retain gaps below. The disposition table currently implies closure that the specified procedures do not support.

2. **§3.3 — Complete or qualify S1’s comparator repair.** C-mem adds finite memory but retains C-thr’s threshold and residual split. Either add the tapered, failure-responsive development candidate requested by Sol, or mark S1 partial and restrict Q1 explicitly to these counter-based adaptations. [BOINC 2009, §4.6](https://boinc.berkeley.edu/boinc_papers/hicss_08/hicss_08.pdf) specifies an error estimate and a replication probability that decreases with that estimate; it does not establish the proposed split as an equivalent policy.

3. **§§3.2, 6.5, 9.3 — Add the missing common-attack cross-evaluation.** For each market and family, freeze a shared candidate bank and evaluate each selected attack across all eight factorial cells. Report fixed-attack contrasts separately from contrasts under separately searched responses. A common truthful reference and Q3’s family envelope do not supply this experiment. Without it, S4 remains unresolved: Q2 mixes rule effects with changes in the selected attack.

4. **§5.2 — Specify X7-SC’s round transition order.** The equations now reproduce D2 algebraically at the stated embedding. However, define failure as the previous round’s failure, apply D2’s update exactly once, decide exit, and define which identity supplies this round’s phase counters. State whether exit resets counters before the action. Evidence: `IdentityReplacement.act` computes the wrapped action before requesting exit; `market.py` applies exit before that action’s offer. An unspecified order can break trajectory equivalence. Replace “tested” with a required test until implementation exists.

5. **§5.2 — Make the Sobol subset executable.** Specify the ordered 13 coordinates, `random_base2(9)`, the threshold-to-bit mapping, seed, version, and deduplication rule. A local check using seed 20261028 and threshold 0.5 produced 512 distinct corners, excluding both endpoints; thus 514 controls are feasible. This is a sampled corner check, not exhaustive coverage.

6. **§§6.2–6.4 — Complete the objective definitions.** Restore W1’s constraint to \(E[(\pi-\pi_{\rm ref})/(S^*/N)]\ge0\), consistent with the registered normalised-profit objective. Expected raw profit is a different constraint because \(S^*\) varies by seed. Replace “infeasible” with “no feasible candidate found”; bounded search cannot prove infeasibility. For coalitions, define the search that produces “all twin,” its normalised total-profit score, member selection, tie order, and honest-max non-members. The joint reference and \( \min_j E[g_j] \) definitions otherwise repair S8/A8.

7. **§§6.5, 8.1 — Schedule the checks that §6.5 promises.** The 56 listed doublings cover only core profit cells. They omit welfare, W1 feasibility, coalition objectives, and most factorial cells. Add fixed checks for these objectives, or explicitly limit the search-quality claim. Freeze whether doubled-search winners enter the final candidate set before evaluation. Merely naming the correct diagnostic units does not complete S9/A7.

8. **§§7.2, 9.5 — Repair seed encoding and namespace reuse.** Replace `int(d(...)[:8])` with `int.from_bytes(d(...)[:8], "big")`. Specify market-index string encoding. Also allocate a genuinely new coverage range: **[6,600,000, 9,000,000) is already reserved by amendment 1**, as recorded in `experiments/amendment-2026-10-17.yaml:75–80`. The present “new namespace” assertion is false.

9. **§§7.3, 9.6 — Complete finality and confirmation rules.** Define a unique anchor-attestation choice, the publication deadline failure rule, and reorganisation handling. Seven linked proof-of-work headers do not establish membership in the accepted chain; specify chain validation or an explicit trusted-source assumption. [Bitcoin’s documentation](https://developer.bitcoin.org/devguide/block_chain.html#block-height-and-forking) permits competing blocks at one height. Require the confirmation root to be mined **after the amended-code lock**: H+1008 may already be known when a later fix is made.

10. **§§5.3, 11 — Reconcile H4’s opening and repair order.** Section 5.3 opens H4 before the draw; step 7 opens it afterwards. Choose one order. Specify how an allowed load repair is committed without violating §9.6’s frozen-family rule. Prefer completing load validation before the authoritative lock. An excluded H4 must leave the independently authored attack part of Q3 explicitly unanswered.

11. **§§9.2–9.5 — Finish the inference specification.** Define valid Holm test inversion, conditional-effect multiplicity, and the pooled interval algorithm; variance alone does not define that interval. Admit the actual adjusted tail levels, including Q1’s extreme two-sided tail of \(0.05/56\). Existing coverage machinery admits specified endpoints, not arbitrary new levels. Add coverage procedures for W1’s constraint and coalition \(G_{\min}\); the latter is a minimum of member means, not an ordinary scalar sample mean. Preserve the prior record’s warning that development admission does not establish nominal coverage on fresh selected-rule distributions.

12. **§§8.2, 11 — Correct arithmetic and make caps operational.** The manifest has **368 cells, including 120 X7 cells**. Under the stated flat multipliers, the surcharge is **180** units and full doubled runs cost **196**, giving **744 evaluation units**, before omitted checks. Initial tuning contributes 34.56 units and rechecks 162, before comparator selection and fixed overhead. Define comparator-selection expenditure. Benchmark before tuning: all four cuts reduce evaluation expenditure, so none repairs a tuning-and-coverage overrun. Add a stop-before-lock rule if either cap remains unmet, and prioritise primary cells in the execution order.

ANSWERS:

(1) No. The embedding equations are repaired, but transition timing and the exact Sobol construction remain incomplete. The 512-corner subset is acceptable as a bounded diagnostic.

(2) Yes, for a coordinated-profile comparison, after correction 6. It does not establish coalition stability or unilateral participation incentives.

(3) Partly. The cuts preserve the principal factorial comparisons, and incomplete reporting is correct. They do not address development-cap overruns, H4 scope loss, or execution priority.

CONFIDENCE: 0.96
