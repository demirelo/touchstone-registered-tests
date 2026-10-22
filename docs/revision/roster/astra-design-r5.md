VERDICT: reject

CORRECTIONS:

1. **§13 — Close all six Sol round-4 corrections at design level.** The evidence now supports closure:
   - Correction 1: previously accepted repairs remain intact.
   - Correction 2: admission requires the upper miss-rate bound to be **at most alpha_e**.
   - Correction 3: independent validation and endpoint-adjusted Clopper–Pearson bounds address calibration selection and Monte Carlo multiplicity.
   - Correction 4: one multiplier per family defines calibrated p-values before Holm; Q4 takes the maximum of calibrated component p-values.
   - Correction 5: C*/S2 now receives all **nine** development searches, including D2.
   - Correction 6: omitting F000’s unused X7-SC attack explicitly justifies **14 profiles** and **840,000 episodes**.

   Keep earlier accepted mechanics closed. Mark Astra’s round-4 development-cut correction **partial**, for the remaining case below.

2. **§§8.2, 9.5 — Define the coverage fixture after both development cuts. This is the remaining material objection.** Section 8.2 first removes `dev1`, then permits pools to shrink to **10,000 seeds per retained market**. Section 9.5 still requires each retained market to supply three disjoint pools of **6,666**, requiring **19,998 seeds**. Thus the second cut leaves Q1’s required admission fixture impossible to construct. Execution would require an unregistered change, extra expenditure, or loss of confirmatory Q1.

   Register all branches explicitly:
   - Three markets, 20,000 seeds each: two strata of 10,000 per market.
   - Two markets, 20,000 seeds each: three strata of 6,666 per market.
   - Two markets, 10,000 seeds each: three strata of 3,333 per market.

   Specify deterministic seed allocation and discard the unused remainder. Retain equal stratum weights and sampling with replacement. For either two-market branch, use the retained full pools for Q4; keeping its validation denominator at 36 is conservative. Price the final branch as **280,000 profile episodes**, plus its bootstrap work. Update §13 accordingly.

3. **§9.2 — Correct the bootstrap-tail statement.** “About 62 resamples” applies only when `kappa = 1`. At `kappa = 1/4`, the smallest nominal tail is **0.0015625**, containing about **15.6 of 9,999 resamples**. State both values. This is a precision limitation, not a separate rejection reason: validation tests the calibrated procedure, and failed validation prevents confirmatory decisions.

4. **§8.2 — Retain the cost structure; distinguish estimates from measured costs.** The arithmetic reconciles under the stated multipliers: comparator selection **33.48 units**, whole-system tuning **142.56**, added searches **0.54**, coverage **56.67**, development **233.25**, and evaluation **868.79**. Total: approximately **1,102.04 units, or USD 49.59**. The rounded table is acceptable. Retain the required benchmark for bootstrap computation and the approval threshold above USD 40; neither runtime nor cap compliance is established by these calculations.

ANSWERS:

(1) **Yes, within the stated scope.** Pooled Q1 can compare the tested adaptations. Q2 and Q3 can report descriptive component effects and discovered attacks. Q4 can report replication of the specified B3–R3 comparison and efficiency condition on the six sampled markets. These results cannot establish general attack resistance, population-wide replication, or the complete earlier amended PASS predicate.

(2) **Yes, as a conditional empirical admission procedure, after correction 2 makes every fixture executable.** Independent validation removes the calibration-selection problem. The endpoint adjustment supports the stated **99 percent Monte Carlo confidence per family**. The common multiplier preserves nesting; calibrated p-values precede Holm; Q4’s component maximum remains valid. Holm supports family-wise control with valid input p-values. [Holm documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html)

Admission still does not establish nominal coverage on fresh distributions. Keep that limitation explicit. No further statistical redesign is required by this review.

CONFIDENCE: 0.95
