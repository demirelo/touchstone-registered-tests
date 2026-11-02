# Protocol v2: predictions (design 9.7)

Written in Operation 5 from development results only; no fresh data exists. Reviewed by Sol and Astra with the protocol and
hashed into `experiments/protocol-v2.yaml` (`predictions_sha256`). Each prediction states a direction and, where the design
gives one, a threshold. Predictions are scored in the report; they are not decision rules and do not change any.

## Development evidence used

All numbers are normalised gains (design 6.1) or gross efficiencies on development seeds, at the fixed pair (tol 0.16,
L 10) unless stated.

- **Full-budget rechecks** (5 restarts x 300 evaluations on dev-train, scored on the 20 dev-val seeds; files
  `experiments/v2/log/*__recheck.json`, read with the `detail` field):

  | Rule | headline D2+H3 / X7-SC | dev0 D2+H3 / X7-SC |
  |---|---|---|
  | F111 (R3; `R3-t` recheck at L 10) | 0.070 / 0.070 | 0.000 / 0.032 |
  | C* (C-mem K 6, M 20; comparator recheck) | 0.097 / 0.097 | 0.038 / 0.038 |
  | B3 structure (`B3-t` recheck at tol 0.16, L 3; no recheck exists at L 10) | 0.342 / 0.352 | 0.197 / 0.201 |

  Gross efficiency in these rechecks: F111 0.994 to 0.998, C* 0.994 to 0.997, B3-t 0.968 to 0.977.
- **Coverage pools** (frozen development attacks from the inner searches, 20,000 seeds per market;
  `results/v2/coverage/pools/<market>.json`, promoted by Operation 4): F000 - F111 under D2+H3 is 0.125 (headline) and
  0.054 (dev0); F111's gross efficiency is 0.997 and 0.997. The inner-search attacks found no positive gain against F111
  or C* in three of four market-family cells; they are weaker than the full searches of the evaluation and are not used
  for directions where a recheck exists.
- **The first registered evaluation** (`docs/final-evaluation-2026-10-20/`): headline D2+H3 gains B3 0.353, R3 0.071; the
  killed predecessor (no priority phase) reached development H3 gain 0.073.

## Q1 comparator (d = g_C* - g_F111, pooled over the six fresh markets)

- **D2+H3:** d positive and below 0.05. Expected category: **"equivalent, direction R3 lower"** (development: d = +0.027
  headline, +0.038 dev0). If the calibrated interval is wider than predicted, "ordered, size not established" in the same
  direction is the second most likely outcome. Not expected: "C* materially lower gain".
- **X7-SC:** d positive and below 0.05. Expected category: **"equivalent"**, with "direction R3 lower" if Holm rejects zero
  (development: d = +0.027 headline, +0.006 dev0).
- **Efficiency:** paired gross-efficiency differences within 0.01 in both families; neither rule earns the word "better"
  (category 1 is not expected).
- If Operation 4 admits no kappa for Q1, the outcome is "no confirmatory decision"; the directions above then apply to the
  descriptive estimates.

## Q2 attribution (descriptive, fixed pair, separately searched and fixed attacks)

- **G (newest-first residual targeting) and S (R3's pacing)** carry most of the reduction from F000 to F111: each main
  effect negative (lowers the D2+H3 gain), each of size at least 0.05 in the pooled estimate.
- **P (priority phase)** small: |main effect| below 0.03 (development: the predecessor without P reached 0.073 against
  R3's 0.070).
- **Interactions:** G x S of the same sign as the main effects (each component works better with the other); P x G and
  P x S small (below 0.03).
- **Fixed-attack contrasts** smaller in magnitude than the separately searched ones (an attack chosen against one cell
  transfers imperfectly).

## Q3 attack strength (descriptive)

- **Envelope:** X7-SC raises F111's gain above D2+H3 by less than 0.05 in every market (development: +0.000 headline,
  +0.032 dev0); the same holds for C*.
- **H4:** H4's gain against F111 is at most the X7-SC gain plus 0.05 in at least five of the seven markets (H4's timing
  equals X7-SC's: ratio 1.002, `experiments/v2/h4/timing.json`; no gain data from H4 exists, the bundle is unread).
- **X5-AG/v2:** below the D2+H3 gain against F111 and C*.
- **Coalitions:** for X6-SE/v2 and X8-DB, G_min well below G_tot (worst-member gain at most half of the total) against
  F111 and C*; X8-DB's beneficiary gains more against F111 than against C* (a decoy that refreshes identities exploits
  age more than credibility).
- **Welfare (W0, W1):** the lowest gross efficiency found against F111 and C* stays above 0.90 at the headline; F000's is
  lower than F111's.
- **Diagnostic (design 6.7):** the honest replacement under F111 keeps a high audit share past age L (Lemma 2b); under C*
  the share falls as passes accrue.
- **R4 (rho = 1 repair block):** R4 removes the rho = 1 collapse of R3 (R4's D2 gain at rho = 1 below R3's by at least
  0.10).

## Q4 replication (per fresh market)

- Both conditions hold in at least five of the six fresh markets: **k >= 5**. Basis: the B3 - R3 gap in development is
  about 0.27 (headline) and 0.20 (dev0) with full searches, against the 0.10 threshold; F111's gross efficiency is near
  0.995, against 0.90.
- The market most likely to fail is one where the gap is close to dev0's inner-search value (0.054): weak searches there
  could leave B3's gain low. A failing market fails condition (a), not condition (b).
