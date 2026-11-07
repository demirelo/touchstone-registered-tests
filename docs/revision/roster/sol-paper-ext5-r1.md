VERDICT: reject

CORRECTIONS:

1. `docs/revision/paper-v2/main.tex:247`; `docs/paper/response-to-review-r5.md:48`: Correct the training-feasibility statement. W0 search archives contain `per_seed_normalized`; subtracting the frozen reference reconstructs training gains without simulation. At the reported weights, training mean gains are R3/H4 **0.00180250**, R3/D2+H3 **0.00127081**, C*/H4 **0.00370487**, and C*/D2+H3 **−0.00057978**. Thus, the reported public-family C* mixture fails the registered training constraint. Disclose this beside Table 11 and revise the claim that feasibility cannot be established from the records. The evaluation estimates themselves reproduce.

2. `docs/revision/paper-v2/main.tex:172`; `docs/revision/audit/audit_v2.py:45`; response letter, lines 20–22: Narrow “each Q1 … decision” to **Q1 direction rejections**, or extend the audit. It checks rejection flags but does not verify Q1 categories, efficiency conditions, or “better” labels. Changing those fields produces no audit mismatch. Independent recomputation confirms the current categories.

3. `docs/paper/response-to-review-r5.md:23`: Table 5 prints calibrated and Holm-adjusted Q1 values; it does **not** print raw Q1 values. Identify the audit output as their location. The revised table labels, p-value arithmetic, and calibrated Q4-b scoring are correct.

4. `docs/paper/response-to-review-r5.md:55`: Distinguish bootstrap probability from the realized resamples. The omission probability is about **4.87%**; **506/9,999 = 5.06%** of the frozen resamples omit all three seeds. Rounding reaches approximately **1.2e−13** in the conditional contrasts, rather than at most 6e−14. The underlying explanation remains correct.

CONFIDENCE: 0.98