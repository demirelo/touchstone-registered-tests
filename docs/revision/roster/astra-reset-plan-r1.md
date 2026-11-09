VERDICT: reject

CORRECTIONS:
1. **Section 1:** The four means, increments, paired SEs, 200-seed matches, reference hashes, and reported flags check out. Correct the registration history: design §8.1 included fresh-market D2 cells; budget cut 3 removed them. B2’s “no” flag means no scheduled check, not verified search quality.

2. **Sections 1–2, 5:** D2 is exactly D2+H3 with `x=0`; it disables the attacker’s replacement action. Frozen references cancel within each increment. However, separately searched winners also differ in other knobs. Search dimension, starts, and corner counts differ (128 versus 256), although restart/evaluation budgets match. Describe the estimand as the difference between prescribed searches over nested policy families, not an identified optimal replacement payoff or a system-wide replacement prohibition.

3. **Sections 2, 7; `sim/manifest_v2.py`, `scripts/revision_v2.py`:** “Only a new manifest” is not an executable plan. The manifest path is fixed; cut 3 excludes fresh D2; doubling eligibility is hard-coded; expanded requirements invalidate existing freezes. Existing launchers enforce the original lock. Specify a separate follow-up execution contract, preserved reference hashes, new freeze, and required adapter/deviations. Match the original Linux configuration hashes, including the recorded calibration deviation.

4. **Sections 3–4:** Specify the interval algorithm, paired resampling within each market, equal-weight pooled variance, and ratio-of-pooled-contrasts calculation. Define handling for zero, small, or negative denominators; do not clip shares. Retain the post-observation disclosure, but state that these markets’ D2+H3 outcomes were already observed. Only D2 outcomes are unseen.

5. **Section 5:** Delete the claim that failed expectations establish predominantly non-replacement causes. Mixed results or search error can also explain failure. Restrict successful claims to the tested families and conditional estimates.

6. **Section 6:** Arithmetic gives 38.88 units for A and 97.2 additional for B, before doubled-winner evaluation. Ledger spend is $39.449, but 696 describes the uncut design. Benchmark the actual workload. Existing evaluation headroom is $3.551, below A’s $4 cap; explicitly update applicable caps.

7. **Sections 2–3:** Report selected `x`, reset counts, probability of any reset, and ban exposure. Add fixed-policy `x→0` diagnostics to distinguish replacement effects from reoptimization.

CONFIDENCE: 0.97.