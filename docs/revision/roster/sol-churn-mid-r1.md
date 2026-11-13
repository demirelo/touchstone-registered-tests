VERDICT: accept-with-caveat
CORRECTIONS:
1. docs/revision/posthoc/churn_block.py:460 — Require `--first` for amendment scoring and select expectations by rate set, independent of order. Both `--rates 0.02,0.03` without `--first` and `--rates 0.05,0.01` return success with empty expectations. The 32 tests pass with RAM-backed file operations but miss these cases.
2. docs/revision/posthoc/churn_block.py:476 — Generate the combined table promised in amendment section 3. The current amendment table contains only p = 0, 0.02 and 0.03; merge the first-arm statistics to include 0.01 and 0.05 for both search versions.
CONFIDENCE: 0.95.