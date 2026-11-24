VERDICT: reject

CORRECTIONS:

1. **main.tex:208:** Remove “differ most in the no-churn baselines.” The pooled C*−R3 difference between winner sets is 0.02269 at p=0, 0.03358 at p=0.03, and 0.04576 at p=0.05. State that both baseline and churn searches change the contrasts. Keep the failed frozen expectation free of causal attribution.

2. **main.tex:208–237; replication.tex:** Supply the reporting required by plan §2: separate normalised attack and reference terms; per-market paired changes; seed-bootstrap intervals for absolute contrasts; and efficiency across all four rules, rates, and winner sets. These values exist in the analysis, but the paper omits them or reports only selected summaries. An appendix can hold them.

3. **main.tex:210; replication-extract.json:** Report R3’s full planned audit allocation, including honest-newcomer job and audit shares and established-honest audit rates. Attacker audit-share ranges alone do not satisfy the draft-10-statistics requirement. Primary audit counts at p=0.03 cover only three markets: rep2, rep3, and rep4 are missing. Complete these diagnostics or disclose the gap.

4. **main.tex:206–208; replication.tex:** Explicitly report support and material-companion outcomes for both winner sets. All six material companions hold in each set; frozen d at p=0.03 fails descriptive support despite meeting materiality. Show all five frozen expectation scores beside the primary scores. Include expectation 4’s recorded probability of 0.5 and expectation 5’s summed-count denominator and zero-denominator rule.

5. **replication_paper.py:56–74; replication_extract.py:14–42; test_replication_paper.py:** Strengthen input validation. The committed outputs reproduce, and ten read-only tests pass. However, altered audit counts yielding zero markets below baseline still produce five fulfilled expectations; duplicate continued cells also pass. Bind the extract to analysis/run hashes, validate unique cell identities and coverage, cross-check expectation 5, and preserve collector error/status fields. Derive the continued list from validated records, not filenames alone. Add tests for stale inputs with unchanged counts and for extract failures.

6. **main.tex:252:** Change “the one verified-history comparator run under churn” to “the comparator used in the earlier follow-up.” Qualify the replication conclusion as using primary winners. At line 248, specify “two nonzero churn rates plus a no-churn baseline.” The title’s “exploratory” label remains consistent with the plan; a title change is optional.

CONFIDENCE: 0.97.