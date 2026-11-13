VERDICT: accept-with-caveat

CORRECTIONS:

1. `docs/revision/posthoc/churn_block.py:460`: Require `--first` for the amendment rates. Currently, `--rates 0.02,0.03` without it returns success with `"expectations": {}`, silently omitting expectations 5–8. Normalize rate order before selecting expectations: `0.05,0.01` also silently omits expectations 1–4. Add tests for both cases.

2. `docs/revision/posthoc/churn_block.py:476`: Generate the combined table promised in amendment section 3. The current table contains only 0, 0.02, and 0.03 for each search version; it never incorporates the original rates from `--first`. Merge the two arms’ statistics for table generation, check that their no-churn values agree, and test all five conditions.

CONFIDENCE: 0.94.