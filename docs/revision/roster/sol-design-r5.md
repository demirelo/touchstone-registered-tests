VERDICT: reject

CORRECTIONS:

1. **§13 — Close the resolved round-4 corrections; retain the budget-cut fixture issue as partial.** Sol corrections 2–6 are resolved: admission now requires an upper miss-rate bound ≤ alpha_e; independent validation accounts for calibration selection; one multiplier per family defines the p-values, Holm decisions, Q4 component maximum, and reported intervals; C*/S2 receives all nine development searches; omitting F000’s X7-SC attack justifies 14 coverage profiles. Astra’s sampling-with-replacement correction and Q4 scope clarification are also resolved. Previously accepted points remain closed. The cost arithmetic checks: approximately **233.6 development units**, **868.8 evaluation units**, and **1,102.4 total units**, subject to the required benchmark.

2. **§§8.2, 9.5 — Define the coverage fixtures after the second development cut.** Replace the fixed replacement-pool size with: “For each retained market with M coverage seeds, form three disjoint Q1 strata of floor(M/3) seeds; discard the remainder for Q1. Q4 uses all M seeds.” State the deterministic partition rule before the lock and recalculate its cost.

   **Effect:** the current fallback cannot be executed as specified. **Evidence:** §8.2 permits shrinking each market pool to **10,000**, but §9.5 still requires three disjoint pools of **6,666**, requiring **19,998** seeds per market. The first cut is repaired; the second remains undefined. At M = 10,000, three strata of 3,333 seeds resolve this conflict without changing the six-stratum procedure. This is the remaining blocking correction.

3. **§9.2 — Correct the bootstrap tail-count statement.** Replace “the smallest confirmatory tail … about 62 resamples” with: “Before calibration, the smallest tail contains about 62 resamples; with kappa = 1/4, it contains about 16.”

   **Evidence:** 9,999 × 0.00625 / 4 = **15.62**. This correction concerns precision reporting. It does not invalidate the calibration algorithm: §9.5 explicitly validates the bounds at the selected calibrated tails.

ANSWERS:

(1) **Yes, within the stated scope.** Pooled Q1 supports comparisons conditional on the six sampled markets and frozen searches. Q4 supports the specified market-by-market replication result, rather than the complete earlier PASS predicate. Descriptive Q2 and Q3 can answer the stated attribution and attack questions through estimates and discovered attacks; they cannot establish confirmed factor effects or general attack resistance.

(2) **Yes, after correction 2 makes every budget branch executable.** A common family multiplier gives a coherent calibration map. Independent validation of the selected multiplier, with Bonferroni-adjusted Clopper–Pearson bounds over 32 or 36 endpoints, addresses the round-4 selection objection. For example, at Q1’s first tail, 88 misses in 20,000 validation replications give an adjusted upper bound of approximately **0.006238**, below 0.00625; 89 misses fail. Holm uses calibrated p-values, and Q4 correctly takes the maximum of its calibrated components. The guarantee remains conditional on the empirical fixtures; transfer to fresh-market distributions remains an assumption, as stated.

CONFIDENCE: 0.96
