# Response to the round-6 external review

Thank you for the third careful review, and for recomputing the lottery grid. You found that our C\* conclusion was wrong;
the paper now states your counterexample. Every correction in your section 4 is applied, as are your remaining changes 1 to
4. No new simulation was run, and no registered estimate or decision changed. Table numbers refer to the revised draft
(`main.pdf`, 26 pages).

## 1. C\* does not need H4 (your problem 1, change 1)

You are right: one failed weight does not show that the public family cannot produce the drop. The post hoc script now
searches, for every mixture whose evaluation-selected weight fails the training constraint, the largest weight on the same
grid at which both the evaluation bound and the training mean gain are non-negative. For C\* with the D2+H3 companion this
gives your values: weight 0.4765 (training break-even 0.47676), training gain 0.0000474, estimated evaluation gain 0.000931,
unadjusted lower bound 0.000699, gross efficiency 0.9224.

- Table 11 (tab:ph-welfare) keeps the failed 0.4800 row and adds the 0.4765 row, labelled "training-feasible". The caption
  says how the weight was chosen and that the row was added after your review.
- Section 9 replaces the sentence with your text, with small changes: both rules show substantial empirical efficiency
  losses with public-family mixtures alone, H4 is not needed for a drop of this size, and population profitability remains
  unestablished. "At the same weights" now reads "each at its rule-companion pair's weight in Table 11 (tab:ph-welfare)".
- A test pins the new weight search, and another pins the table row; both failed before the code.

## 2. Q4-b scoring correction in the paper (your problem 2)

Section 9 (Predictions) now says that the original scorer compared raw component p-values, that the corrected scorer
compares the registered calibrated values (1 against 0.0004 on fresh0, fresh2 and fresh5), that the prediction remains
fulfilled with the total unchanged, and that this is a scoring correction separate from the label corrections of Table 5 (tab:q1)
and Table 8 (tab:q4). The revised scorer (`docs/revision/paper-v2/score_v2.py`) and its regression test
(`test_scoring.py::test_q4b_compares_calibrated_p_values_as_registered`) will be in the artifact.

## 3. Release description (your problem 3)

Availability now opens: the paper artifact has its own release commit and archive hash; it identifies the frozen evaluation
code by the signed tag `protocol-v2`, preserves the original tagged-code report, and contains, separately dated, the
stability re-evaluation, the exploratory analyses with their evaluation and training inputs, the prediction-scoring
correction with its regression test, the inference audit, and the paper sources.

## 4. Conclusion, introduction, and small labels (your problems 4 and 5)

| Your point | Change |
|---|---|
| Conclusion | Your replacement: W0 efficiency about 0.840 against all three rules; W1 near 0.997 for R3 and C\*; mixtures 0.932 and 0.921; "the registered W1 search therefore supplies no efficiency bound for randomised policies" |
| Introduction | The results paragraph names the W1 comparator (0.997) and says the drop appears with public-family attacks alone |
| Q1 sentence | "Both direction tests reject d = 0 (calibrated input p' = 0.0004; Holm-adjusted p = 0.0008 for each)" |
| Multiplicity | "The two questions have separate multiplicity families; no paper-wide five percent guarantee is claimed." |
| Table 11 (tab:ph-welfare) and Table 12 (tab:ph-welfare-sens) | Captions: two displayed companions, H4 and D2+H3, of five examined, all in `posthoc.json`; Table 12 (tab:ph-welfare-sens) at fixed display weights, not separately optimised |
| Description of Table 18 (tab:ph-q4-stability) | Section 9 says what it compares, as you wrote |
| Side evidence | "refunds on false audit failures" and "service fraction", in the text and in the column headers of Table 6 (tab:q1-side) and Table 7 (tab:ph-q4) |

## 5. Your remaining changes

- **Change 3 (reproducibility export): done.** `lottery_train.csv` (90 rows) gives, per rule, component, and dev-train seed,
  the search record, the selected policy's knobs, its normalised profit, the frozen reference's name and normalised profit,
  and the gain. Its component means equal `train_w0` and `train_companion` in `posthoc.json` to 1e-12 (C\*: -0.0937682027
  and +0.0854403021, as you used). The script now refuses a W1 record whose seed order differs from W0's (tested); there is
  no mismatch in the records.
- **Change 4 (lead with the result): partly done.** The contributions paragraph now leads with your three findings (Q1
  pooled equivalence; the two targeting components substitute; mixtures expose a welfare weakness the W1 search does not
  cover), and the procedural contributions follow. The full venue cut (shorter paper, history in a supplement) is not done.
- **Change 5 (cross-play comparison): not done.** We will use your fresh4 and fresh2 example if we target AAMAS.

## Questions for this round

1. Is the C\* passage and the new row of Table 11 (tab:ph-welfare) now right?
2. Is the Q4-b disclosure and the release description adequate?
3. Anything else that blocks a specialist-venue submission?
