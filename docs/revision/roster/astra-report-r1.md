VERDICT: reject

CORRECTIONS:

1. `results/v2/report/report.md:3`; `report.json:$`: Disclose the Linux configuration substitution and the author-approved budget increase from USD 40 to 43. The 17 changed values are each within one ulp, and the substituted hashes match the pods. However, `docs/revision/deviation/cfg_ulp.py:64` checks configurations and record integrity, not decision sensitivity. State that unchanged decisions under the original configurations remain unverified; small input differences alone do not prove this.

2. `results/v2/report/report.md:9`, `:31`, `:163`: Label Q1’s efficiency condition as descriptive, using nominal one-sided 97.5% bounds. Label Q2 and the ordinary Q3 intervals “nominal 95%, unadjusted.” Label G_min separately with its registered member-bound tails of 0.05/c. Identify confirmatory intervals as calibrated Bonferroni intervals, separate from Holm decisions.

3. `report.json:$.q1.descriptive`; `results/v2/report/report.md:13`: Add the required side fields beside each per-market and headline Q1 result: paired gross/net efficiency, reference profit, audit spending, focal/other false-failure refunds, and served share. These currently appear only for pooled results.

4. `results/v2/report/report.md:3`; `report.json:$`: Add section 9.4’s claim limits: results depend on the sampled neighbourhood, fixed parameters, searched families, and frozen searches. Q4 is an internal replication of the comparative and efficiency conditions, not the complete earlier PASS predicate. Registration does not establish exact nominal error control on fresh selected-policy distributions.

CONFIDENCE: 0.97.