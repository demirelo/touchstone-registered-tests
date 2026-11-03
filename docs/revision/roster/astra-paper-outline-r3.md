VERDICT: reject

CORRECTIONS:

1. **Numbers rule — claim mapping:** Map each result site to its required report path. Add a test that substitutes another valid path of the same kind. Kind checks still accept a lower bound as the estimate: the in-memory probe using `\rvk{gain}{q4.markets.fresh0.gain_diff_lower}` returned no error. The current checks validate only the final field name and value type (`docs/revision/paper-v2/numbers_v2.py:26`, `:132–136`). Round-2 correction 1 remains open.

2. **Numbers rule — result coverage:** Add the requested source manifest and explicit checks that all result sites have region markers. Test omitted regions in both main text and included captions. The current scan detects only numbers with at least three decimal places that match report values (`docs/revision/paper-v2/numbers_v2.py:142–148`). In-memory probes accepted “Replicated on 4 of six markets” and an incorrect gain of `0.999`, including in an included caption. Round-2 correction 2 remains open.

3. **Rounding rule — tables:** Apply the p-value formatter to Q1 and Q4 table cells. Add table regression tests for small nonzero p-values. Prose macros now preserve `0.0001`, but the Q1 table probe still printed it as `0.000`. Tables use the general formatter for these cells (`docs/revision/paper-v2/tables_v2.py:26–27`, `:50`, `:71–72`), contrary to the rounding rule (`docs/revision/paper-v2/outline.md:32–33`). Round-2 correction 3 is only partly resolved.

CONFIDENCE: 0.98
