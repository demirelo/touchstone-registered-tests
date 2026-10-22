VERDICT: reject

CORRECTIONS:

1. **§13 — Separate completed repairs from remaining gaps.** Close the round-3 corrections on B2 and `rho=1` reference searches, dependency order, coalition membership and schedule assignment, publication before H, and the distinction between Holm decisions and Bonferroni intervals. §§6.3–6.4, 7.3, 8.1 and 9.2 now specify these correctly. Keep coverage admission and workload accounting partial for the reasons below. Earlier accepted points remain closed.

2. **§9.5 — Tighten admission if the decisions retain nominal 5 percent error control.** Replace “upper bound … at most 1.5 alpha_e” with “at most alpha_e,” including for calibrated remedies. The present criterion allows an endpoint error allowance 50 percent above its allocation. For example, at `alpha_e = 0.00625`, 71 misses in 10,000 replications pass: the exact Clopper–Pearson 99 percent upper bound is approximately **0.009309**, below `0.009375` but above `0.00625`. Thus admission does not support the stated Holm error budget; endpoint allowances of this size permit a family bound of 0.075 rather than 0.05. Alternatively, retain the gate solely as a diagnostic and remove nominal confirmatory error-control claims. Preserve the warning about transfer to fresh distributions.

3. **§9.5 — Account for selection among calibration remedies.** Use independent validation replications after calibration, or simultaneous Monte Carlo bounds across the candidate procedures. Evidence: the same replications select among the original, half-tail and quarter-tail procedures. A marginal 99 percent bound for each fixed procedure is not a simultaneous 99 percent guarantee for the selected procedures. The specification contains **68 endpoint checks** before remedies: 32 for Q1 and 36 for Q4. State the confidence guarantee and its multiplicity treatment explicitly.

4. **§§9.2–9.5 — Define one executable calibration rule for decisions and intervals.** State how fixture-specific, side-specific and step-specific admission results become evaluation thresholds. “Holm … at the calibrated tail levels” does not specify which calibration applies when fixtures disagree, or how calibration enters Q4’s component-maximum p-value. One repair is to freeze a common conservative multiplier for each confirmatory family that passes every required fixture, side and step. Define calibrated p-values before Holm ranking; form Q4’s maximum from calibrated component p-values; apply the same calibration to the separate Bonferroni intervals. This preserves the corrected Holm/interval distinction and makes decisions reproducible.

5. **§§6.4, 8.2, 9.5 — Complete the development reference searches.** Add C*/S2’s D2 inner search on each development market, making **nine** additional searches rather than six, or explicitly register a consistent reduced reference menu for all coverage fixtures. §6.4 requires development references from D2, D2+H3 and X7-SC, while §8.2 budgets only six C*/S2 searches, sufficient for two families across three markets. Without the change, its coverage reference cannot be constructed as specified. At the stated inner-search prices, nine searches cost **0.54 units**, versus 0.42 for six.

6. **§8.2 — Correct or substantiate the coverage profile count.** Budget up to **15 profiles per market**: two attacks and one frozen reference for each of five rules. This gives **900,000 episodes**, or 50 units under the stated 18,000-episode convention, before bootstrap computation. Retain 14 only if the manifest identifies a valid omitted or reused profile; reference abstention or duplicate trajectories must be established explicitly. The main revised arithmetic otherwise reconciles: **374 cells, 126 X7 cells, 132 checks, 207 doubling units, and 156,800 additional cross-evaluation episodes**. The benchmark and approval boundaries can remain.

ANSWERS:

(1) **Yes, within the stated scope.** Pooled Q1 and market-specific Q4 can support conditional comparative and replication claims. Descriptive Q2 and Q3 can report attribution estimates and discovered attacks. They cannot establish confirmed factor effects or general robustness. The specification already states these limits.

(2) **No, for nominal 5 percent confirmatory decisions.** The endpoint-specific Monte Carlo bound improves on draft 3, but the 1.5 multiplier, remedy selection and unspecified calibration mapping leave corrections 2–4 unresolved. Conditional empirical admission also remains distinct from coverage on fresh markets.

CONFIDENCE: 0.96
