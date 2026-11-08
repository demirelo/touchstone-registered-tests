# Response to the round-7 external review

Thank you for the fourth review, and for testing the scorer on a case that separates the raw and calibrated comparisons.
We made your one pre-submission change and your text changes 2 and 3. No simulation was run, and no registered estimate,
decision, or original scorer output changed. Table numbers refer to the revised draft (`main.pdf`, 27 pages).

## 1. Prediction eligibility (your problem 1, change 1)

You are right that the scorer read the numbers and never the search flags. Counting direct inputs, we got your counts: 6 of
14 Q3-a pairs, Q3-b's X7-SC input, and 7 of 10 Q3-d cells have a flagged required search. Our internal reviewers then found
that direct inputs are not enough: an evaluated estimate also depends on other searches through its frozen reference, the
fixed-attack bank, and warm-start incumbents, and every record stores these links as file hashes (all 4,462 links resolve).
Traced through those links, Q3-d is flagged in all 10 cells, Q3-e becomes flagged (its coalition references depend on the
flagged minimum-objective searches), Q2-d's X7-SC cells become flagged, and Q4-b's fresh0 cell depends on the flagged C\*
D2+H3 search through the reference. Q3-c still fails on pairs that are not flagged.

- **Eligibility map.** `score_v2.py --eligibility --records` writes `eligibility.json`: for every cell of every
  prediction, its direct inputs, every flagged search it depends on (directly or through recorded upstream links), and its
  status under three readings, plus the tallies counting direct inputs only. An input without a record raises an error
  instead of passing as unflagged. The original `scoring.json` is byte-identical to the round-7 file. Eight tests pin the
  map (each failed before its code).
- **Readings and tally.** Numerical (as scored): 10 fulfilled, 8 failed. Flagged inputs, Q3 (your reading, with
  dependencies): 6, 8, 4 (Q3-a, Q3-b, Q3-d, Q3-e not assessed; counting direct inputs only, 7, 8, 3 as you found). Flagged
  inputs, every descriptive prediction: 5, 4, 9 (also Q1-c and Q2-a to Q2-d). No reading turns a failed prediction into a
  fulfilled one or changes a decision.
- **Decision predictions.** Under the descriptive reading, Q1-a, its alternative, Q1-b, Q1-d, Q4-a and Q4-b keep their
  status even when their inputs are flagged (Q4-b's fresh0 cell is). Design 6.5 keeps the decisions; it does not say how
  predictions about them are scored, so the paper calls this a convention of the sensitivity.
- **Other exclusion clauses.** Cut, missing and excluded cells reach the scorer as absent values and are not assessed.
  Numerical refusals ("not decided: numerical refusal") are now not assessed in the Q1-d, Q2 and coalition
  entries, as they already were in Q1-a and Q1-b, and non-finite values are refused (tested). The round-7 report contains no refused entry,
  so no status changed.
- **Paper.** Section 9 (Predictions) states that the scorer retains the estimates of flagged searches, that the rubric
  excludes incomplete targets, that it does not say whether a prediction computed from a flagged search is itself
  incomplete, that no reading was chosen as official after the outcomes, and gives both stricter readings with the
  direct-input count. New Table 21 (tab:pred-eligibility) gives the three tallies and the predictions each reading leaves
  not assessed. In Table 19 (tab:predictions) and Table 20 (tab:predictions-b) a dagger marks the rows not assessed under
  both stricter readings (Q3-a, Q3-b, Q3-d, Q3-e) and a double dagger the rows not assessed under the descriptive reading
  only (Q1-c, Q2-a to Q2-d). Q3-b's 0.0200 stays visible. The Q2 paragraph and the list of informative failures say that
  the Q2 conjectures failed as scored and are not assessed under the descriptive reading.

## 2. Contributions paragraph (your problem 2)

Both replacements are in, with small changes: (i) "On the six fresh markets, the prescribed searches classified R3 and
the development-selected verified-history comparator as pooled-equivalent in attacker gain within ±0.05 under both Q1
attack families." (iii) "At the headline market, an exploratory analysis of episode-level mixtures of public-family
policies found substantially lower empirical gross efficiency than the registered W1 search, at non-negative estimated
gain; population profitability remains unestablished." Finding (ii) is unchanged.

## 3. Conclusion labels (your problem 3)

The conclusion now reads: W1 near 0.997 for both rules; mixtures selected on the evaluation records yield, with H4,
0.932 for R3 and 0.921 for C\*; public D2+H3 mixtures meeting the empirical training constraint yield 0.945 and 0.922;
all at non-negative estimated evaluation gain; the population-profitability caveat stays. The values come from
`posthoc.json` through the paper's number check (the C\* public value is the training-feasible row of Table 11
(tab:ph-welfare)).

## 4. Not done

- **Venue cut (change 3).** Not done in this revision.
- **Release manifest (change 4).** At release: the paper-artifact commit, archive hash and persistent URL beside the
  frozen tag and the original report, with the scorer, its tests, `scoring.json`, `eligibility.json`, and both lottery
  CSVs.
- **Cross-play comparison (change 5).** Not done; only if we target AAMAS.

## Questions for this round

1. Is the eligibility disclosure (Section 9 (Predictions), Table 21 (tab:pred-eligibility), and the marks) adequate?
2. Is tracing recorded dependencies the right notion of a required search, and is the decision-prediction convention acceptable?
3. Anything else before the WEIS submission?
