VERDICT: reject

CORRECTIONS:

1. **`docs/revision/predictions-v2.md:57–58` — Restrict the H4 prediction to the headline market.** Replace it with: “Headline only: predict H4’s F111 gain ≤ X7-SC’s gain + 0.05. This is an untested hypothesis; no H4 gain result supports it. Fresh-market H4 predictions are not assessed because cuts 3 excludes those cells.” The manifest’s second cut removes H4 from all six fresh markets. The timing ratio, 1.002158, supports cost estimation; it provides no evidence about gain. The current five-of-seven prediction cannot be scored.

2. **`docs/revision/predictions-v2.md:7–28` — Correct the evidence description.**
   - Specify full-search budgets as **5 × 300 for D2/D2+H3 and 5 × 600 for X7-SC** (`scripts/tune_v2.py::_settings`).
   - Restrict the quoted efficiency ranges to the **D2+H3 and X7-SC columns**. Including D2 would make the F111 and C* ranges incorrect.
   - Replace “three of four market-family cells” with **“all four market-family cells.”** Recalculation from the promoted pools gives no positive mean gain against either F111 or C* in any of those cells.
   - Cite `experiments/v2/pools/<market>.json` as the retained pool source.
   - Describe the first registered evaluation as **earlier evaluation data reused as development evidence for v2**. Its seeds were not development seeds in that evaluation.

   The gain table, Q1 differences, coverage gaps, and quoted first-evaluation gains otherwise agree with their sources.

3. **`docs/revision/predictions-v2.md:44–51` — Separate Q2 hypotheses from measured attribution.** Add: “The available evidence does not identify the factorial main effects or interactions; these directions and thresholds are hypotheses.” The predecessor comparison, 0.073 versus approximately 0.070, concerns one conditional comparison under earlier searches. It does not estimate P’s factorial main effect, separate G from S, or establish interaction sizes. `paper/main.tex` expressly states this identification limit. Change “P × G and P × S small (below 0.03)” to **“|PG| < 0.03 and |PS| < 0.03”**; a large negative interaction currently satisfies “below 0.03.”

4. **`docs/revision/predictions-v2.md:42–68` — Define the remaining scoring targets before the lock.** Add a scoring table that specifies the family, market aggregation, attack selection, statistic, and inequality for each prediction.
   - **Fixed-attack contrasts:** name the contrasts and families to which “smaller” applies. Use the registered equal-weight average over the eight attack rows.
   - **Coalitions:** distinguish the separately selected total-maximising and minimum-maximising policies. Define which selected policy supplies X8-DB’s beneficiary gain. The current report summary exposes G_tot and G_min, but not that beneficiary comparison.
   - **Welfare:** use the training-selected family for each objective. Do not select the lowest evaluation result across families.
   - **Diagnostic:** replace “high” and “falls” with numerical comparisons and specified age bins, including treatment of terminal rounds.
   - **Unavailable results:** score cut, missing, excluded, or numerically refused targets as **not assessed**, not as fulfilled or failed.

   These changes make the predictions reproducibly scorable without changing the accepted decision rules.

5. **`docs/revision/predictions-v2.md:59–68` — Label unsupported extensions explicitly.** Add a source or mark each as an untested mechanistic hypothesis: X5-AG/v2 against C*, X8-DB’s beneficiary ordering, the welfare threshold, and R4’s numerical improvement of at least 0.10. The cited rechecks and coverage pools contain none of those tests. Earlier robustness results support motivation, but do not establish these new-family, new-comparator, or repaired-rule thresholds. Predictions may extend beyond observations; the document must distinguish those extensions from measured evidence.

6. **`docs/revision/predictions-v2.md:72–76` — Define Q4 success by the registered test.** Replace “Both conditions hold … k ≥ 5” with: **“Predict k ≥ 5, where k counts markets rejected by the registered six-market Holm procedure on the maximum of the two calibrated component p-values.”** Label the approximately 0.27/0.20 gaps as **L = 3 B3-t versus L = 10 F111 evidence**, rather than matched fixed-pair evidence. The table discloses that mismatch, but this paragraph drops it. Replace the categorical failure statement with a hypothesis about which component will be limiting. Failure to reject does not establish that condition (a) is false.

7. **`docs/revision/operations-ledger.md` — Append the review disposition of the four departures.** None establishes a compromise of Q1 or Q4’s confirmatory status:
   - **(a) H4 custody:** resuming the same separate session and performing only the recorded commit/hash operations preserves the stated separation, conditional on the custody record being accurate. Keep **aa28ed4** as the bundle commit; **c5227a0** is the check-time HEAD and defender commit. Do not replace one with the other. I did not independently inspect the prohibited clone or bundle. H4 concerns descriptive Q3.
   - **(b) Coverage order and budget:** the pre-coverage snapshot reproduces the promoted H4 decision exactly. The stopped calculation counted completed coverage again as remaining work. Keep that stopped record. Add **“actual development spend plus estimated evaluation cost: 49.5055825014347 USD”**, while retaining 49.15504976545906 USD as the frozen decision estimate. Actual development spend is 11.42 USD; both caps and the 52 USD approval remain satisfied.
   - **(c) Coverage driver and history rescue:** inspection of the driver found ordered seed slicing and concatenation around the frozen `build_pool`, with unchanged profiles and input construction. Both promoted pools have the expected 20,000 ordered seeds. The recorded 40-seed byte comparison supports equivalence. Fetching history changes ancestry evidence, not simulation code. Preserve the exact driver and equivalence receipt under `docs/revision/` for audit.
   - **(d) Parallel tuning:** B3-t and R3-t do not depend on comparator selection; C*-t followed comparator promotion. This changes execution order without changing selection inputs.

8. **`experiments/protocol-v2.yaml` — Regenerate after the document corrections, then rerun `--check`.** The present check returns **`ok`**. I also reproduced the H4 cost decision: **two20k, cuts 3, development 11.06946726402436 USD, evaluation 38.0855825014347 USD**. Cut 2 costs 40.37494431490278 USD, so cut 3 is required. The hashes, promoted parameters, admitted `kappa_effective` values **Q1 0.5 / Q4 0.25**, spend, and approval sentence agree with their sources. The branch has no net changes outside data and documents since 627a2de. Retain those values; update the prediction hash before signing, stamping, and tagging.

CONFIDENCE: 0.94
