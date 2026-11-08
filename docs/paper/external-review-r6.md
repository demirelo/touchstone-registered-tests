# External review, round 6 (condensed record; the author pasted the full review in the session on 2026-11-08)

**Verdict:** AAMAS main track 2/5 (weak reject), WEIS 2027 4/5 (weak accept, up from 3), EC 1/5 (strong reject);
confidence 4, 3, 4. Forecasts: AAMAS 30% (35% after text changes), WEIS 65% (70%), EC 5% (6%).
Round-5 finding 1 (p-values) withdrawn. Follow-through: findings 1, 3, 4 (results), 5, 6, 7, 8 resolved; 2 partly. Changes
1, 4, 5 resolved; 2, 3, 6, 7 partly; 8 not resolved (optional). No new compute needed.

## Remaining problems, ranked
1. **C* "needs H4" is wrong.** On the paper's grid, C* with the public D2+H3 companion at W0 weight 0.4765 has training gain
   +0.0000474, evaluation gain 0.000931, unadjusted lower bound 0.000699, efficiency 0.9224 (H4: 0.9212; W1: 0.9971);
   training break-even 0.47676. Replace the sentence, keep the failed 0.4800 row, add the 0.4765 row with how it was chosen;
   "at the same weights" -> each pair's own weight.
2. **Disclose the Q4-b scoring correction in the paper** (raw compared, registered on calibrated: 1 vs 0.0004; no verdict change).
3. **Availability blurs the tag's scope.** The paper artifact has its own release commit and hash; it identifies the frozen
   code by `protocol-v2`, preserves the original report, and includes the dated stability, exploratory, scoring-correction and
   audit material, with the revised scorer and its regression test.
4. **Conclusion and introduction:** name the W1 comparator (about 0.997); "no efficiency bound for randomised policies"
   instead of "does not extend".
5. **Small labels:** Q1 sentence (calibrated input p' = 0.0004; Holm-adjusted 0.0008); multiplicity sentence; Tables 11 and
   12 "two displayed companions of five"; Table 18 description; side evidence (refunds on false failures, service fraction).

## Remaining changes, by value (all 0 USD)
1. Add the C* 0.4765 row. 2. Correct the takeaway and disclose Q4-b. 3. Training export (seed ids, policy ids, normalised
returns, reference identity) and an assertion that W1's seed order matches W0's. 4. Lead the venue paper with three results
(Q1 pooled equivalence; targeting components substitute; mixtures expose a welfare weakness W1 missed). 5. Optional for
AAMAS: cross-play comparison (R3, D2+H3: fresh4 bank 0.0245 vs own search 0.00573; fresh2 0.0356 vs 0.04416).
