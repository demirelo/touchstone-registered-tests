VERDICT: reject

CORRECTIONS:

1. **main.tex:208:** Remove “differ most in the no-churn baselines.” For the pooled C*–R3 contrast, the winner sets differ by 0.02269 at p = 0, 0.03358 at p = 0.03, and 0.04576 at p = 0.05. Retain the statement that paired changes depend on search uncertainty at both rates, without attributing the failed frozen expectation to a cause.

2. **main.tex:208–237; tables/replication.tex:** Add or explicitly reference the planned per-market changes, absolute contrasts, and seed-bootstrap intervals. State the interval methods: 95% paired percentile bootstrap, 9,999 resamples, seed 0; 95% market t intervals with five degrees of freedom. The printed table agrees numerically with the analysis but reports only aggregate t intervals.

3. **main.tex:210; replication_paper.py:** Report the separate attack and reference profit terms and efficiency for all four rules, all three rates, and both winner sets, directly or in a referenced supplement. The analysis contains these terms; the paper reports only selected efficiency values.

4. **replication-extract.json; main.tex:210:** Complete or disclose the missing planned audit reporting. Primary audit counts at p = 0.03 cover only three markets. `rep_collect.py:689` generates continued-winner diagnostics only at p = 0 and 0.05. The extract also omits the planned draft-10 allocation statistics, including honest newcomer and established-job audit measures. Focal audit-share ranges do not fulfil that requirement.

5. **main.tex:206–208:** Report support and the material companion explicitly for both winner sets. All six material companions hold in each set; frozen support fails only for d at p = 0.03. Preserve the correct five-versus-four expectation scores. Include expectation 4’s recorded probability of 0.5 and expectation 5’s zero-denominator rule.

6. **replication_extract.py:14–41; replication_paper.py:56–74; test_replication_paper.py:** Bind the extract to the analysis and run identifiers. Validate unique cell identities, continuation status, complete expected inputs, and audit counts. Counting JSON filenames does not establish valid continuation. In-memory checks accepted a foreign continuation stem, `confirmatory=False`, and missing audit data. Current freshness checks detect changed generated files, not all wrong source inputs. Add tests for these cases and the extract itself.

7. **main.tex:252:** Qualify “the one verified-history comparator run under churn” as referring to the earlier follow-up. The replication now runs two.

CONFIDENCE: 0.97.