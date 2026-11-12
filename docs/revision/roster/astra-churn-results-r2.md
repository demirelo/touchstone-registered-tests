VERDICT: accept-with-caveat

CORRECTIONS:

1. docs/revision/posthoc/churn_block.py:269 — Reject non-finite audit shares before tolerance comparisons, including at line 259. NaN passes because `abs(NaN - expected) > TOL` is false. Replacing both R3 pooled first-bin shares with NaN passes validation and changes expectation 4 from “met” to “failed.” Add a rejection test.

2. docs/revision/posthoc/churn_block.py:248 — Check seed identifiers, uniqueness, and agreement with the evaluation records. Array lengths alone do not establish “one episode per seed.” Replacing all 200 seed identifiers with one repeated identifier passes validation. Add a rejection test.

3. docs/revision/posthoc/churn_block.py:254 — Check the four expected bin boundaries and corresponding array lengths. Changing the first bin’s age label to `[10,20]` passes validation, although expectation 4 still treats it as `[0,10)`. Add a rejection test.

The round-1 text corrections are resolved. The supplied records pass independent seed, bin, and count checks. The read-only, 9,999-resample rerun reproduced every JSON field and the table; the registered check passed. All 23 test functions passed with file operations held in memory. The paper number check passed; the full paper gate was not rerun.

CONFIDENCE: 0.97.