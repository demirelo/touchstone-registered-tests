VERDICT: reject

CORRECTIONS:

1. **`docs/revision/predictions-v2.md`, Q3 H4:** Replace “in at least five of the seven markets” with “at the headline market.” State: “Fresh-market H4 comparisons are cut and are not scored. If H4 is excluded or incomplete, this prediction is unanswered.” Cuts 3 includes the second cut in `experiments/revision-v2-manifest.yaml`: H4 on fresh markets. The current prediction cannot be scored. Also replace the timing-based justification with “untested conjecture”: the verified runtime ratio, 1.002158, provides no evidence about gain.

2. **`docs/revision/predictions-v2.md`, evidence section:** Make these exact corrections:
   - Change “three of four market-family cells” to “all four market-family cells for each rule.” The selected inner-search logs contain no positive gain for F111 or C* in any of those cells.
   - Specify “5 restarts × 300 evaluations for D2/D2+H3; × 600 for X7-SC.” `scripts/tune_v2.py::_settings` doubles X7-SC’s evaluation budget.
   - Cite the committed pools at `experiments/v2/pools/<market>.json`.
   - Replace “development results only” with “v2 development results and previously published evaluation results; no v2 fresh outcomes.” The cited October 20 results used final-evaluation seeds.
   - Cite `docs/amendments/2026-10-18-amendment-3.md` for the predecessor’s 0.073. That number is correct but does not come from the cited final-evaluation record.

   The displayed recheck gains, efficiency ranges, Q1 differences, and pool contrasts otherwise match their sources to the stated precision.

3. **`docs/revision/predictions-v2.md`, Q2–Q4 evidence:** Separate measured evidence from conjecture. Label the G/S effect thresholds, interaction signs, fixed-attack attenuation, X5 ordering, coalition ordering, welfare threshold, and R4 improvement threshold as conjectures unless a specific development result supports them. The cited evidence does not measure these quantities. The historical 0.073 versus 0.070 comparison does not identify P’s factorial main effect; it neither averages over G/S nor holds the searches and references constant. In Q4, explicitly describe the 0.27/0.20 gaps as **B3-t at L=3 versus F111 at L=10**. They support a forecast by analogy, but they are not matched-pair estimates of Q4’s fixed-L=10 contrast.

4. **`docs/revision/predictions-v2.md`, scoring:** Add a scoring table with one row per prediction, its statistic, scope, threshold, and missing-result treatment. In particular:
   - Define Q4’s `k` as the number of Holm-rejected intersection-union tests, using Q4 kappa 0.25. Replace “both conditions hold” with “the registered decision passes.” Non-rejection does not establish that condition (a) is false.
   - Specify whether “X7-SC raises … by less than 0.05” means only an upper bound on the difference or also predicts a positive difference; the headline development difference is zero.
   - Write small interactions as absolute magnitudes: `|PG| < 0.03`, `|PS| < 0.03`.
   - Specify the fixed-attack rows and coalition objective used. The report’s G_tot and G_min come from separately selected policies; the X8 beneficiary comparison needs a stated policy selection.
   - Move “high audit share” and “falls as passes accrue” to unscored qualitative expectations unless numerical criteria are supplied.
   - Score the stated primary Q1 category separately from its alternative. Mark unavailable results unanswered.

5. **`docs/revision/operations-ledger.md`, departure (b):** Add: “The frozen decision estimates USD 49.15505 using the pre-coverage ledger. Actual development spend plus estimated evaluation cost is USD 49.50558.” Preserve both decision records and the frozen protocol cost fields. I verified that the snapshot equals the current ledger with only the two coverage charges removed. The stopped calculation is 11.42 + 1.309467 = 12.729467; the reconstructed calculation is 9.76 + 1.309467 = 11.069467. Cuts 2 costs USD 40.37494 for evaluation; cuts 3 costs USD 38.08558. Thus cuts 3 remains the first admissible cut. **This order departure does not compromise Q1/Q4:** it changes neither their data nor their rules, and actual development spend remains below USD 12. The existing USD 52 approval covers the current forecast.

6. **`docs/revision/operations-ledger.md`, departure (a):** Add the full clone commit identifier, `aa28ed40fde184ba888ac7a1545db4a76b7b0d56`, and explicitly distinguish “bundle commit” from “HEAD when checked.” Keep `timing.json.commit = c5227a0…` unchanged. Its difference from the later bundle commit is expected. **The recorded resume and mechanical commit do not compromise Q1/Q4 or, by themselves, H4’s independent authorship**, provided the recorded non-inspection and unchanged bundle are accurate. The bundle hashes agree across the permitted records, and the promoted defenders match the defender commit. I did not independently verify the excluded clone or bundle.

7. **`docs/revision/operations-ledger.md` and a documentation attachment, departure (c):** Preserve the exact driver versions used, their hashes, and the 40-seed equivalence commands/results under `docs/revision/`. The driver is currently outside the reviewed worktree’s tracked artifacts. I inspected the main checkout’s `results/pods/cov_driver.py`: it calls frozen `build_pool`, preserves seed order, and concatenates the same profile arrays. The promoted pools pass seed, length, hash, input-manifest, and coverage-admission checks. **No confirmatory compromise is evident from slicing or the history fetch.** However, the ledger’s small-pool equality claim is not a substitute for preserving the actual orchestration source. The history rescue is acceptable as recorded because it changed history availability, not simulation code.

8. **`docs/revision/operations-ledger.md`, departure (d):** Add: “B3-t and R3-t have no comparator-input dependency; C*-t started after comparator promotion.” The frozen tuning dispatch passes comparator parameters only to C*-t. **Parallel execution does not compromise any confirmatory claim**, and no rerun is required for this departure.

9. **`experiments/protocol-v2.yaml`:** After correcting predictions, regenerate the protocol and repeat the check before signing, stamping, and tagging. No current numerical binding needs correction: all six hashes, derived parameters, branch `two20k`, cuts 3, admitted kappas 0.5/0.25, cost fields, approval sentence, and fixed block/seed/cap values re-derived correctly. The standard `uv` invocation failed on sandbox cache access; the same checker passed with optional plotting imports disabled, and complete protocol reconstruction matched the file. Coverage endpoint bounds and the H4 cost decision also passed separate checks. Treat this as verification of the present draft, not completion of the lock.

CONFIDENCE: 0.94
