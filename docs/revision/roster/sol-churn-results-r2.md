VERDICT: accept-with-caveat

CORRECTIONS:
1. docs/revision/posthoc/churn_block.py:254 — Validate all four age bins and their order in market summaries, episode counts, and pooled summaries. A consistent swap of [0,10) with [10,20) passes validation and changes expectation 4 from “met” to “failed,” while retaining the first-ten-round label. Empty bin lists also pass. Add rejection tests.
2. docs/revision/posthoc/churn_block.py:259 — Reject non-finite market and pooled shares before tolerance comparisons, including at line 269. NaN passes because `abs(NaN - expected) > TOL` is false. Add rejection tests for both summary levels.
3. docs/revision/posthoc/churn_block.py:248 — Check seed identifiers against the corresponding evaluation record, including uniqueness, count, and order. The current length check accepts 200 duplicate seed identifiers and therefore does not establish one episode per evaluation seed.

The paper corrections are resolved. All 23 test functions pass with file operations held in memory. The 9,999-resample rerun reproduces every JSON field and the table exactly; the registered check and paper number check pass. The supplied diagnostics pass and contain none of the defects above.

CONFIDENCE: 0.97.