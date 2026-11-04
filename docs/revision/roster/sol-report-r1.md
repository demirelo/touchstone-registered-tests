VERDICT: reject

CORRECTIONS:
1. `results/v2/report/report.md:31`, `:163`: Add “nominal 95 percent, unadjusted” to Q2 and Q3. The JSON contains these labels, but the Markdown omits them. At `:9` and `:11`, label the efficiency condition as descriptive, using nominal one-sided 97.5 percent bounds.
2. `results/v2/report/report.json:$.q1.tests["C*-F111|X7-SC"].search`: Check label propagation through reference and bank dependencies. This field is null although the references depend on search-flagged D2+H3 records. For example, fresh0 C* has a nonzero reference change in its doubling diagnostic. Apply the prescribed-search qualification to affected decisions.
3. `results/v2/report/report.md:1`; `report.json:$`: Disclose both deviations in the report: the substituted Linux configs and the author-approved evaluation cap increase from USD 40 to 43. Include the original and substituted config hashes and link the verification evidence.
4. `docs/revision/deviation/cfg_ulp.py:64`: Distinguish config verification from decision stability. The checks establish matching pod hashes, differences within 1 ulp, and successful verification with substituted configs. They do not establish unchanged simulation paths or decisions under the registered configs. Compare frozen-policy results under both configs, or explicitly state that decision stability remains unverified; discrete branches can amplify small input differences.
5. `results/v2/report/report.md:3`: Add the registered claim scope: conditional on the sampled markets, stated neighbourhood, fixed pair, attack families, and frozen searches. State that Q4 is an internal replication of the comparative gain and efficiency conditions.

CONFIDENCE: 0.93.