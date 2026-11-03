VERDICT: reject

CORRECTIONS:
1. **Numbers rule and step 1:** Bind each prose result site to its exact report path, including question, family, market, and statistic. Add a regression test that swaps two valid paths of the same kind. The revised check validates only field names and types. An in-memory probe accepted Q4’s `gain_diff` as Q1’s estimate. Round-2 path mapping remains incomplete (`docs/revision/paper-v2/outline.md:21`; `docs/revision/paper-v2/numbers_v2.py:132-136`).

2. **Numbers rule and step 1:** Add the requested source and result-site manifest. Require every registered result site, including included captions, to have result-region markers. Add tests for unmarked counts and incorrect decimals. The outside-region check only detects decimals with at least three places that match report values. In-memory probes accepted “replicated on 4 of six markets” and “gap 0.999”, including in an included caption. Input scanning is improved, but coverage remains incomplete (`docs/revision/paper-v2/numbers_v2.py:109-118`; `docs/revision/paper-v2/numbers_v2.py:121-148`).

3. **Rounding rule and table generation:** Apply the shared p-value formatter to Q1 and Q4 table cells. Add small-p-value tests for both tables. Prose formatting is corrected, but tables still use the three-decimal formatter: an in-memory Q1 table probe rendered `0.0001` as `0.000`. This violates the stated precision rule (`docs/revision/paper-v2/outline.md:32-33`; `docs/revision/paper-v2/tables_v2.py:26-27`; `docs/revision/paper-v2/tables_v2.py:50`; `docs/revision/paper-v2/tables_v2.py:71-72`).

CONFIDENCE: 0.98
