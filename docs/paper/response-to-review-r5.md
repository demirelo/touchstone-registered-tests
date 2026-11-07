# Response to the round-5 external review

Thank you for a second careful review, and for checking the materials themselves. Every correction in your section 4 is
applied, and most of your eight remaining changes (your section 5) were done on the existing records; section 5 below
lists what was not. No new simulation was
run, and no registered estimate or decision changed. Table numbers refer to the revised draft (`main.pdf`, 25 pages).

## 1. The p-value discrepancy (your finding 1)

**The implementation follows the registered rule. The paper's labels were wrong.** We traced each field to the frozen
code:

- Q1, field `p` (`sim/decisions_v2.py`, `q1_family`): the calibrated two-sided value $p' = \min(1, p/\kappa)$ that
  enters Holm. Table 5 (tab:q1) called it a "Holm $p$-value". Its Holm-adjusted value is 0.0008, as you computed.
- Q4, fields `p_gain` and `p_eff` (`scripts/report_v2.py`, `q4`): the **raw** one-sided bootstrap p-values. The
  calibrated market values $\max(p'_{\mathrm{gain}}, p'_{\mathrm{eff}})$ are stored separately (field `q4.p`) and enter
  Holm in `q4_markets`. Table 8 (tab:q4) printed the raw values under the label $p'$. The stored market values for
  fresh1, fresh3 and fresh4 are 0.0004, with Holm-adjusted values 0.0024, as you computed.

A new audit script (`docs/revision/audit/audit_v2.py`, output `audit.json`) recomputes the raw, calibrated and
Holm-adjusted values from the evaluation records (Q1 raw 0.0002, calibrated 0.0004, adjusted 0.0008). It checks that
every stored value equals the registered arithmetic, that the frozen `q1_family` recomputed from the records gives each Q1
category and direction rejection, and that each Q4 decision is reproduced; it exits nonzero on any mismatch and reports
none. It does not recheck the Q1 intervals or efficiency labels. Table 5 (tab:q1) now prints the calibrated Q1 value that
enters Holm and its Holm-adjusted value (the raw Q1 values are in `audit.json`); Table 8 (tab:q4) prints the raw Q4
component values, the calibrated market value that enters Holm, its Holm-adjusted value and the decision, under labels
that name these quantities. Section 8 states what the report stores.

The same trace found a related error in the prediction scoring: Q4-b is registered on calibrated p-values, but the scoring
compared raw ones. With these data the verdict is the same (raw 1 against 0.0001 becomes 1 against 0.0004 on each
non-passing market). The scoring now calibrates, and Table 20 (tab:predictions-b) prints the calibrated values. Tests pin
both the column labels and the calibrated scoring; both tests failed before the fix.

## 2. Welfare lottery (finding 2, change 2, change 3, change 4)

- **Wording.** The abstract, introduction, results, discussion and conclusion now state the lottery as exploratory
  estimates on the evaluation records that selected it, with population profitability not established. We use your
  replacement sentences, with small changes. The sentence that said a mean constraint makes any lottery feasible is
  replaced by your condition on the probability-weighted component gains.
- **Table 11 (tab:ph-welfare)** now prints the estimated gains and the unadjusted lower bounds at three significant
  digits (R3: 0.000374 and 0.0000279; C\*: 0.000456 and 0.0000718). It shows both companions, H4 and the public D2+H3
  family. It names the weight as the largest on a grid of step 0.0005, with the bound unadjusted for selection.
- **Randomisation versus adding H4.** With the public D2+H3 attack as companion, the evaluation efficiencies are 0.945
  (R3) and 0.922 (C\*); see the training-feasibility point below for which of these mixtures meet the W1 constraint.
- **Sensitivity.** Table 12 (tab:ph-welfare-sens) gives the estimated gain and efficiency at the weights 0, 0.1, ..., 0.5
  for each rule and companion. We did not construct joint bounds over the component library, so the analysis stays a
  check of the policy class.
- **Reproducibility.** `docs/revision/posthoc/lottery_seeds.csv` exports the per-seed W0 and companion gains and
  efficiencies (3,000 rows: three rules, five companion families, 200 seeds). The script that selects the weight and
  computes the standard error is `docs/revision/posthoc/posthoc_v2.py`.
- **Training feasibility.** The search archives store each evaluated policy's per-seed normalised profit on the training
  seeds, so the training gains can be reconstructed against the frozen reference without simulation. At the selected
  weights, the mixtures' training mean gains are 0.00180 (R3, H4), 0.00127 (R3, D2+H3), 0.00370 (C\*, H4) and
  -0.000580 (C\*, D2+H3). Three meet the registered W1 training constraint; C\*'s public-family mixture does not. Table 11
  (tab:ph-welfare) prints these values, and the paper says that for R3 the drop appears with public-family policies
  alone, while for C\* at the selected weight it needs H4. (An internal reviewer found this; our first draft wrongly said
  the records could not show it.)

## 3. Extreme fresh1 intervals (finding 3, change 5)

The audit scans the report for bounds beyond 1,000 in absolute value and finds your 12 entries and no others. The cause:
at fresh1 the fixed-reference reference-profit contrast is above rounding scale on only 3 of 200 seeds. The other 197
seeds carry floating-point rounding (at most 1.2e-13 in absolute value over the affected contrasts). The probability that
a resample leaves out all three seeds is 4.9 percent; in the frozen resample matrix, 506 of the 9,999 resamples (5.1
percent) do. Their standard error is of rounding size, so the frozen studentized bootstrap gives bootstrap-t statistics near 7e10. The frozen
code replaces only an exactly zero resample standard error, so these values pass. Section 9 now discloses this, keeps the
frozen outputs, and draws no conclusion from them. `audit.json` lists each entry with its diagnostic (sample standard
error, seed count, maximum bootstrap-t statistic, quantiles). We did not add a replacement interval.

## 4. Remaining corrections (findings 4 to 8)

| # | Your point | Change |
|---|---|---|
| 4 | Provenance statements | Section 9 opening, the row of Table 3 (tab:rules-v2), and Availability use your replacements and name the post hoc and audit outputs and scripts |
| 5 | Categorical coverage sentence | Section 8: your conditional sentence, with small wording changes |
| 6 | Coalition table | Table 15 (tab:q3-coalitions) caption: the two columns can describe different selected policies |
| 7 | Q4 diagnostic units; neighbourhood sentence | Section 9 uses your wording; Table 7 (tab:ph-q4) caption defines audit spend (audit cost over realised $S^*$) and the service fraction (jobs served by all providers over $T\min(J, \sum_i k_i)$), and says it is not the attacker's share; section 10: "does not establish that margin across all six sampled fresh markets" |
| 8 | Addendum rounding; Q4 stability | The addendum now prints 0.0074 (tested). New Table 18 (tab:ph-q4-stability) gives all six markets' gain differences, efficiencies and their bounds, old and new, with the Holm-adjusted value and both decisions. The largest change is fresh4, from 0.183 to 0.176, still above 0.10 |

Also applied: the abstract prints the margin as $\pm0.05$ (your point 2).

## 5. Not done, and why

- **Joint lower bounds over a finite component library** (change 4): not built. The lottery stays an exploratory check
  of the policy class, and the paper says so.
- **Candidate-level reference provenance** (change 6): not exported in this revision. The addendum's dependency trace
  stays conservative, as you suggested.
- **Cross-play bank comparison** (change 8): not done in this revision. We will consider it for the venue version.
- **Contribution framing** (change 7): the contributions paragraph is unchanged. We agree with your two-sentence
  statement and will use it when we cut the paper for the venue.

## Questions for this round

1. Does the audit resolve finding 1, and are the new labels right?
2. Are the lottery statements now calibrated correctly?
3. Is the disclosure of the extreme intervals adequate?
4. Your updated scores and probabilities.
