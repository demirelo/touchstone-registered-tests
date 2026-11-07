VERDICT: reject

CORRECTIONS:

1. `main.tex:247`; `docs/paper/response-to-review-r5.md:48`: The training-feasibility explanation is false. W0’s `welfare.archive` stores `per_seed_normalized`; subtracting the frozen reference gives training gain without new simulation. At the reported weights, mean training gains are R3/H4 **0.00180250**, R3/D2+H3 **0.00127081**, C*/H4 **0.00370487**, and C*/D2+H3 **−0.00057978**. Export and report these results. The C*/D2+H3 lottery at weight 0.480 fails the registered training constraint.

2. `audit_v2.py:117`; site `r_ext_share`; response letter:53–59: **4.8668% is the theoretical omission probability**, not the observed fraction of the frozen resamples. Exactly **506/9,999 = 5.0605%** omit all three substantive values. Label these quantities separately. The maximum rounding residual reaches **1.194×10⁻¹³** for the conditional contrasts, exceeding the letter’s stated 6×10⁻¹⁴. Replace “nonzero on only three seeds” with “above rounding scale on three seeds.”

3. `docs/paper/response-to-review-r5.md:20–24`; `main.tex:171`: Narrow the audit claims or extend its checks. `q1_audit` checks calibrated p-values and Holm direction rejections; it does not reproduce Q1 categories, intervals, or efficiency labels. Table 5 prints calibrated and Holm-adjusted values, but **no raw p-value**. The frozen arithmetic itself is correct: Q1 raw/calibrated/adjusted values are **0.0002/0.0004/0.0008**; passing Q4 markets have **0.0004/0.0024** market/adjusted values. Q4-b now uses calibrated components correctly.

4. `main.tex:250`; `posthoc_v2.py`, Table 11 row label: Replace “B3’s W0 attack is itself profitable” and “W0 profitable” with “positive estimated gain.” Keep the table’s exploratory and selection qualifications explicit.

CONFIDENCE: 0.98