# Response to the round-7 external review

Thank you for the fourth review, and for testing the scorer on a case that separates the raw and calibrated comparisons.
We made your one pre-submission change and your text changes 2 and 3. No simulation was run, and no registered estimate,
decision, or original scorer output changed. Table numbers refer to the revised draft (`main.pdf`, 27 pages).

## 1. Prediction eligibility (your problem 1, change 1)

You are right that the scorer read the numbers and never the search flags. We checked your mapping against the report's
`search_flagged` list and got your counts: 6 of 14 Q3-a pairs, Q3-b's X7-SC input, and 7 of 10 Q3-d cells have a
directly flagged required search; Q3-e is not affected (the C\* X8-DB flag is on the minimum objective); Q3-c still fails
on unflagged pairs; Q4-b is not affected.

- **Eligibility map.** `score_v2.py --eligibility` now writes `eligibility.json`: for every prediction cell, the searches
  it requires and those that are flagged, and the status under three readings. The original `scoring.json` is
  byte-identical to the round-7 file. Four tests pin the map (they failed before the code).
- **One reading wider than yours.** Applied to every descriptive prediction, the same rule also reaches Q1-c (the
  efficiency difference uses the flagged D2+H3 searches on fresh0, fresh1, fresh3 and fresh4) and Q2-a to Q2-c (the pooled
  factorial contrasts include R3's flagged D2+H3 searches on fresh1 and fresh4). Q2-d still fails on its unflagged X7-SC
  cell. The predictions that score a confirmatory decision (Q1-a, its alternative, Q1-b, Q1-d, Q4-a, Q4-b) keep their
  status, as design 6.5 keeps the decision.
- **Tally.** Numerical (as scored): 10 fulfilled, 8 failed. Flagged inputs, Q3 (your reading): 7, 8, 3. Flagged inputs,
  every descriptive prediction: 6, 5, 7. No reading turns a failed prediction into a fulfilled one or changes a decision.
- **Paper.** Section 9 (Predictions) states that the scorer retains the estimates of flagged searches, that the rubric
  excludes incomplete targets, that the design does not say whether a prediction computed from a flagged search is itself
  incomplete, and gives both stricter readings. New Table 21 (tab:pred-eligibility) gives the three tallies and the
  predictions each reading leaves not assessed. In Table 19 (tab:predictions) and Table 20 (tab:predictions-b) a dagger
  marks the rows not assessed under both stricter readings (Q3-a, Q3-b, Q3-d) and a double dagger the rows not assessed
  under the descriptive reading only (Q1-c, Q2-a, Q2-b, Q2-c). Q3-b's 0.0200 stays visible. The Q2 paragraph now says
  that the three Q2 conjectures failed as scored and are not assessed under the descriptive reading, and the list of
  informative failures notes the same for the priority-phase prediction.

We did not choose one reading as official after seeing the outcomes. The rubric's text ("incomplete (design 6.5)")
points toward a strict reading, but it does not name which derived targets it covers; the paper gives all three.

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
2. Is the wider descriptive reading right to include Q1-c and Q2-a to Q2-c, and right to keep the decision predictions?
3. Anything else before the WEIS submission?
