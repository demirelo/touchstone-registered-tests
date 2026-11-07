# Response to the round-4 external review

Thank you for a careful and useful review. Every sentence correction is applied; the four zero-cost analyses you
proposed were run on the existing records and are reported in the paper as exploratory. Two of them changed the paper's
substance (points A and B below). Section numbers refer to the revised draft attached (`main.pdf`).

Your review saw only the PDF. This time the materials are attached as separate files, so the report, the addendum, the
protocol, the predictions, the ledger, and H4's code and containment note can be checked directly.

## What changed in substance

**A. The welfare result was overstated, as you suspected (your Task 2.5).** W1 constrains the mean gain, so an
episode-level lottery between a welfare attack and a profitable attack is feasible. On the evaluation records, a lottery
that plays R3's W0 attack with probability 0.4195 and its H4 attack otherwise keeps the mean gain non-negative and
lowers R3's gross efficiency to 0.932, against 0.997 under the registered W1 search; for C* a lottery with W0 weight
0.4845 reaches 0.921 (`posthoc.json`, Table 11). The paper now says that the profit-constrained welfare
result depends on excluding randomised policies and is not a lower bound. The non-negativity rests on a nominal one-sided 95 percent normal
bound that is not adjusted for selection: the weight and the companion family were chosen on the evaluation seeds, so
this checks the policy class and is not an out-of-sample estimate. The exact weights matter: at a rounded 0.42 the
bound for R3 turns negative.

**B. The Q1 explanation was wrong (your point 6).** Splitting d = g_C* - g_R3 with the gain's own normalisation into
the attacked-profit and reference-profit terms shows that almost all of d is attacked profit (D2+H3: 0.019 of 0.021;
X7-SC: 0.0225 of 0.024). The paper had said the rules "differ mainly in the attacker's truthful reference profit"; it
now says the opposite, and labels the reference-profit row of the side-evidence table (Table 6) as raw profit units.

**C. H4 contains D2+H3 exactly** (its author's containment note, `h4/containment.md`). The paper now calls H4 an
extension of the public family written in a separate session, not a disjoint attack concept.

**D. Related work.** All four references you suggested were verified from primary sources (publisher PDFs and Crossref) and added: Zarkoob, Fu, and Leyton-Brown (2020) in the introduction, as report-dependent checking that our admissible rules could use but we do not study; Wiedenbeck, Cassell, and Wellman (2014) beside the empirical-game method; Berger and Hsu (1996) for the equivalence and intersection-union logic; Morris, White, and Crowther (2019) for the calibration reporting.

## Sentence corrections (your Task 1)

| # | Your point | Change |
|---|---|---|
| 1 | Gain does not isolate the benefit of replacement | Discussion: measured against each rule's frozen reference; does not isolate the replacement benefit; would need replacement disabled |
| 2 | Q1 headline omits margin, X7-SC value, search flags; "only" | Abstract and introduction: pooled, within the registered margin, both families' values, prescribed searches; "only" removed |
| 3 | All Q4 passes are search-qualified | Abstract, introduction, section 9, conclusion |
| 4 | "Loss-accepting" confuses relative and absolute loss | Discussion and conclusion: for R3 and C* only (B3's W0 attack earns +0.254), a loss relative to the truthful reference, not necessarily negative profit |
| 5 | Coalition sizes mismatched; decoy family exception | Section 9: matched two- and five-member comparisons (total objective), the worst member under the separately selected minimum-member policy, decoy family 0.024 vs 0.025, no ordering claim |
| 6 | Q1 explanation unsupported | Point B above; new exploratory table (Table 4) |
| 7 | W1 "efficiency stays" too broad; B3's W1 | Section 9: W0 and W1 values for B3 and R3, finite-search outcomes, not lower bounds; point A |
| 8 | "The sign is established" | Section 9: registered calibrated procedure; nominal guarantees not established on fresh selected-rule distributions |
| 9 | Uniform auditing alone does not imply costless bans | Abstract, introduction, conclusion: B2 and B3 with refund-and-ban and no bonds (Corollary 1's condition) |
| 10 | Welfare claim covers unevaluated rules; H4 "selected" | Abstract: B3, R3, C* only; "selected" policy |
| 11 | "Stay below" suggests a bound | Introduction and section 9: training-selected envelopes, finite-search comparison, no family-level robustness |
| 12 | Pacing raises gain | Abstract, section 9, discussion: small increase (0.004 D2+H3, 0.005 X7-SC); repair values under D2+H3 |
| 13 | Interaction scale | Section 9: PG contrast defined as half the difference of G's conditional effects; "accounts for most of the measured reduction" |
| 14 | Which first-test clause failed | Abstract: rule clause passed; baseline clauses failed |
| 15 | "Best of four" | Abstract and section 9: development-selected from twelve configurations of four adaptations |
| 16 | Two generalisation statements | Section 9: Q4 does not test the complete amended claim; discussion: shared benefit, no ordering for every variant and market |
| 17 | Stability summary | Sections 8 and 10: frozen policies and references; search and reference selection not repeated; new table |
| 18 | Small shading condition | Limits: first-test parameters, zero-continuation round, same-offer shading |
| 19 | Conclusion | Rewritten along your replacement |
| 20 | Dependencies, H4 provenance, availability, Table 13 | Search-quality paragraph names what the addendum traces (Q1 and Q4) and what is descriptive (Q2, Q3); H4 provenance and containment; availability tense made consistent (future, before publication); the prediction table (now Tables 17 and 18, split so that it fits the page) prints each registered statement and condition, names every paired value (five decimals, so that close pairs such as Q3-e stay distinguishable; single values at four), shows Q1-c as C* minus F111 as registered, and the text says the count is not a validation score |

## Method (your Task 2)

- **Calibration and intervals** (2.1, 2.2): section 8 now states the role of kappa (it multiplies each nominal tail, so
  kappa < 1 widens intervals), the candidate set {1, 1/2, 1/4}, the fixtures (frozen development attacks and references,
  headline and dev0, 20,000 seeds per market), 10,000 selection and 20,000 validation replications, the Clopper-Pearson
  admission rule with m = 8 endpoints for Q1 and m = 36 for Q4 (24 evaluated on the two-market branch, denominator kept), 9,999 bootstrap resamples with seed pairing, what the bootstrap does and does not measure, the scope
  of each multiplicity guarantee, and the economic size of the margin (half a percent of the first-best surplus).
- **Deviations** (2.3): the stability table (Table 16, four decimals) sets the Q1 estimates beside their re-evaluation (0.0207 vs 0.0209,
  0.0243 vs 0.0245); categories and the Q4 count are unchanged; the largest change of any cell mean is 0.0074. The text
  says search and reference selection were not repeated. The cap change and its timing are in the ledger.
- **Attack strength** (2.4): the paper now states that doubling checks find missed improvements but cannot bound the
  remaining gap, and that the envelope values are finite-search results.
- **Heterogeneity** (your change 7): a per-market table (Table 7) splits Q4's difference: on every market it is almost
  all attacked profit, R3's audit spending is at its allowance and its served share near one; the failing markets show
  smaller attacked-profit reductions, and these descriptive diagnostics do not identify the cause.

## Not done, and why

- **Shortening to eight pages and anonymising.** The AAMAS 2027 main track has closed; the paper stays full length for
  now. We will anonymise and cut for the chosen venue.
- **A matched comparison with replacement disabled** (point 1): it needs new simulation outside the registered design;
  the paper states the limit instead.
## Questions for this round

1. Do the corrections and the two substantive changes resolve your Task 1 and Task 2 findings?
2. Is the welfare lottery analysis presented with the right weight and caveats?
3. With the materials now attached, does anything in the report, addendum, ledger, or H4 files contradict the paper?
4. Your updated scores and acceptance probabilities (AAMAS main track, WEIS 2027, EC), with confidence.
