# Protocol v2: predictions (design 9.7)

Written in Operation 5 from v2 development results and previously published evaluation results; no v2 fresh outcome
exists. Reviewed by Sol and Astra with the protocol and hashed into `experiments/protocol-v2.yaml` (`predictions_sha256`).
Predictions are scored in the report with the scoring table at the end; they are not decision rules and change none.
Each prediction is marked **[evidence]** (a cited development result supports its direction) or **[conjecture]** (an
untested mechanistic hypothesis: the cited results do not measure that quantity).

## Evidence

Normalised gains (design 6.1) and gross efficiencies at the fixed pair (tol 0.16, L 10) unless stated.

- **Full-budget rechecks** (5 restarts x 300 evaluations for D2 and D2+H3, 5 restarts x 600 for X7-SC, on dev-train;
  scored on the 20 dev-val seeds; `experiments/v2/log/*__recheck.json`, field `detail`):

  | Rule | headline D2+H3 / X7-SC | dev0 D2+H3 / X7-SC |
  |---|---|---|
  | F111 (R3; the `R3-t` recheck at L 10) | 0.070 / 0.070 | 0.000 / 0.032 |
  | C* (C-mem K 6, M 20; the comparator recheck) | 0.097 / 0.097 | 0.038 / 0.038 |
  | B3 structure (the `B3-t` recheck at tol 0.16, **L 3**; no recheck exists at L 10) | 0.342 / 0.352 | 0.197 / 0.201 |

  Gross efficiency in the D2+H3 and X7-SC columns: F111 0.994 to 0.998, C* 0.994 to 0.997, B3-t 0.968 to 0.977.
- **Coverage pools** (frozen development attacks from the inner searches, 20,000 seeds per market;
  `experiments/v2/pools/<market>.json`): F000 - F111 under D2+H3 is 0.125 (headline) and 0.054 (dev0); F111's gross
  efficiency is 0.997 in both. The inner-search attacks found no positive mean gain against F111 or C* in any of the four
  market-family cells; they are weaker than the evaluation's full searches and are not used where a recheck exists.
- **Earlier evaluation data reused as development evidence for v2:** the first registered evaluation
  (`docs/final-evaluation-2026-10-20/`, final-evaluation seeds of that evaluation): headline D2+H3 gains B3 0.353, R3
  0.071. The killed predecessor without the priority phase reached H3 gain 0.073 (`docs/amendments/2026-10-18-amendment-3.md`).

## Q1 comparator (d = g_C* - g_F111, pooled over the six fresh markets; kappa_Q1 0.5)

- **Q1-a, D2+H3 [evidence]:** primary category **"equivalent, direction R3 lower"** (d = +0.027 headline, +0.038 dev0).
  Alternative: "ordered, size not established", direction R3 lower. Not expected: "C* materially lower gain".
- **Q1-b, X7-SC [evidence]:** primary category **"equivalent"** (with or without "direction R3 lower"; d = +0.027
  headline, +0.006 dev0).
- **Q1-c, efficiency [evidence]:** the pooled paired gross-efficiency difference (C* minus F111) lies in [-0.01, 0.01] in
  both families (scored as Q1-c); no rule earns "better" (scored separately as Q1-d).

## Q2 attribution (descriptive; fixed pair; pooled over the six fresh markets)

The available evidence does not identify the factorial main effects or interactions: the predecessor comparison (0.073
against about 0.070) is one conditional comparison under earlier searches and references. The directions and thresholds
below are hypotheses.

- **Q2-a [conjecture]:** the main effects of G and of S on the D2+H3 gain (separately searched attacks) are each at most
  -0.05.
- **Q2-b [conjecture]:** |main effect of P| < 0.03 on the D2+H3 gain.
- **Q2-c [conjecture]:** |PG| < 0.03 and |PS| < 0.03; GS <= 0 (the same sign as the G and S main effects).
- **Q2-d [conjecture]:** for each main effect (P, G, S) and each family (D2+H3, X7-SC), the fixed-attack contrast (the
  equal-weight mean over the eight attack rows, design 6.6) is smaller in absolute value than the separately searched
  contrast.

## Q3 attack strength (descriptive)

- **Q3-a [evidence]:** in every market, the X7-SC gain minus the D2+H3 gain is below 0.05 against F111 and against C* (an
  upper bound only; no sign is predicted; development: +0.000 headline, +0.032 dev0 for F111; +0.000 for C*).
- **Q3-b [conjecture]:** headline only: H4's gain against F111 is at most the X7-SC gain plus 0.05. H4 on fresh markets is
  cut (cuts 3) and not scored. H4's timing ratio (1.002, `experiments/v2/h4/timing.json`) bears on cost only, not on gain.
- **Q3-c [conjecture]:** X5-AG/v2's gain is below the D2+H3 gain against F111 and against C*.
- **Q3-d [conjecture]:** for X6-SE/v2 and X8-DB against F111 and C* at the headline, G_min (from the policy selected for
  the minimum objective) is at most half of G_tot (from the policy selected for the total objective): G_min <= 0.5 x G_tot,
  also when G_tot <= 0. Cells: X6-SE/v2 at both coalition sizes and both schedules, and X8-DB's roles schedule.
- **Q3-e [conjecture]:** X8-DB's beneficiary gain (member 0, under the policy selected for the total objective) is larger
  against F111 than against C*.
- **Q3-f [conjecture]:** at the headline, the gross efficiency of the training-selected welfare attack (per objective W0,
  W1) is at least 0.90 against F111 and C*, and F000's is lower than F111's.
- **Q3-g [conjecture]:** in the rho = 1 repair block, R4's D2 gain is below R3's by at least 0.10.
- **Unscored qualitative expectation:** the honest replacement under F111 keeps a high audit share past age L (Lemma 2b);
  under C* the share falls as passes accrue.

## Q4 replication (per fresh market; kappa_Q4 0.25)

- **Q4-a [evidence, by analogy]:** **k >= 5**, where k counts the markets rejected by the registered six-market Holm
  procedure on the larger of the two calibrated component p-values. Basis: B3-t (L 3) against F111 (L 10) shows gaps of
  about 0.27 (headline) and 0.20 (dev0) with full searches, against the 0.10 threshold; these are not matched fixed-pair
  estimates of the L 10 contrast. F111's gross efficiency is near 0.995, against 0.90.
- **Q4-b [conjecture]:** where a market does not pass, the limiting component is (a), the gain difference, not (b), the
  efficiency: p'_gain > p'_eff, strictly (a tie fails), in every assessed non-passing market; non-rejection does not
  establish that (a) is false.

## Scoring table

A target that is cut, missing, excluded, incomplete (design 6.5), or numerically refused is **not assessed**; it counts
neither as fulfilled nor as failed. Pooled values follow design 9.2 (equal market weights). A prediction over several
cells (markets, rules, families, coalition cells) is scored cell by cell: it **fails** if any assessed cell fails; it is
**fulfilled** only if every required cell is assessed and fulfilled; otherwise it is **not assessed**.

| Id | Statistic | Scope | Fulfilled if |
|---|---|---|---|
| Q1-a | Q1 category, D2+H3 | pooled fresh | primary: "equivalent, direction R3 lower"; scored separately: the alternative |
| Q1-b | Q1 category, X7-SC | pooled fresh | "equivalent" or "equivalent, direction R3 lower" |
| Q1-c | paired gross-efficiency difference C* - F111 | pooled fresh, both families | both point estimates in [-0.01, 0.01] |
| Q1-d | "better" label (design 9.3, `q1_better`) | pooled fresh, both families | neither family gives "R3 better" or "C* better" |
| Q2-a | main effects G, S, D2+H3, searched | pooled fresh | both point estimates <= -0.05 |
| Q2-b | main effect P, D2+H3, searched | pooled fresh | point estimate in (-0.03, 0.03) |
| Q2-c | PG, PS, GS, D2+H3, searched | pooled fresh | \|PG\| < 0.03, \|PS\| < 0.03, GS <= 0 |
| Q2-d | fixed-attack vs searched contrasts | pooled fresh, P, G, S x D2+H3, X7-SC | \|fixed\| < \|searched\| in all six |
| Q3-a | gain(X7-SC) - gain(D2+H3) | each market, F111 and C* | below 0.05 in every required market-rule pair |
| Q3-b | gain(H4) - gain(X7-SC), F111 | headline | at most 0.05 |
| Q3-c | gain(X5-AG/v2) - gain(D2+H3) | each market, F111 and C* | below 0 in every required market-rule pair |
| Q3-d | G_min - 0.5 x G_tot (separately selected policies) | headline, F111 and C*: X6-SE/v2 at both coalition sizes and both schedules, X8-DB roles schedule | <= 0 in every required cell |
| Q3-e | X8-DB beneficiary gain (total-objective policy) | headline | F111 > C* |
| Q3-f | gross efficiency of the training-selected welfare attack | headline, W0 and W1 | >= 0.90 for F111 and C*; F000 < F111 |
| Q3-g | gain(R3) - gain(R4), D2 | headline, rho = 1 | at least 0.10 |
| Q4-a | k (Holm on the market p-values) | six fresh markets | k >= 5 |
| Q4-b | calibrated component p-values p'_gain, p'_eff | each assessed non-passing market | p'_gain > p'_eff (strict; a tie fails) in every such market; not assessed if no such market |
