# Operation 8: report review round 2 (read-only; no paid APIs; do not read `sealed/`, `sealed2/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 1 (`docs/revision/roster/{sol,astra}-report-r1.md`; both reject) asked for labels, disclosures, claim scope, per-market side fields, and search-flag propagation. Ruling: the report stays exactly as `scripts/report_v2.py` at tag protocol-v2 wrote it (reproducible from the tag); a separate addendum, `/Users/oemer.demirel/Projects/touchstone/results/v2/report/addendum.{md,json}`, written by `docs/revision/report-addendum/addendum_v2.py` (tests in `test_addendum_v2.py`), states what round 1 asked for and changes no estimate or decision:
- interval and decision labels for Q1 (Holm decisions; calibrated Bonferroni intervals; descriptive efficiency condition at nominal one-sided 97.5 percent), Q2, Q3 (G_min at 0.05/c per member), Q4;
- design 9.4's claim scope;
- both deviations: per-market registered and reproduced config hashes, differing-value counts, the evidence file's sha256, an explicit statement that decision stability under the registered configs is not verified; the cap change 40 to 43 USD with the recorded approval;
- search-flag dependencies traced through the upstream links of evaluate, reference, search and bank records (freeze records excluded as integrity anchors): Q1 C*-F111|X7-SC and Q4 fresh0 and fresh3 are newly qualified as about the prescribed search procedure;
- Q1 side fields per market and for the headline market.

Check only: (1) each round-1 correction is resolved by the addendum; (2) whether keeping the tagged report unchanged and adding the addendum is acceptable; (3) the dependency tracing rule (freeze excluded) and its results; (4) new errors.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, or "none".
CONFIDENCE: 0 to 1.
