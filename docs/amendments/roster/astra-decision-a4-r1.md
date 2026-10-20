VERDICT: reject — the draft gives a materially false account of the original cap. The pilot stored at `lock-2026-10-17` projects USD 1,829.952384; its ceiling is USD 1,830, not USD 300. Repair 1 corrects this checkable failure. The proposed one-time extension is otherwise acceptable with the conditions below.

REPAIRS:

1. Replace the sentence beginning “The cap `h1.cost_cap_usd = 300.0` was set…” with:

   “The original lock records `h1.cost_cap_usd = 300.0`. The Anthropic pilot stored at that tag records `projected_cost_usd = 1829.952384`; the pilot path in `scripts/lock.py` would round this to 1830 USD. Thus, the stored pilot does not establish the stated derivation of the 300 USD cap.”

   Delete “the pilot’s projection was about five percent too low over 12 cells”. Retain the measured cell costs as the stated basis for this extension.

2. Replace “the cumulative ledger … is unchanged” with:

   “The existing cumulative ledger is retained without reset and is updated by subsequent paid calls. With the same inputs and intact cache, matching requests replay without API calls; only cache misses incur new cost. Exactly one H1 process may use this cache and ledger during the resume.”

3. Replace reporting rule 4 with:

   “Before registration, run the verify-only check against amendment 3 and inspect the registration commit’s file list to confirm that it changes only `docs/`. After registration, repeat the check against amendment 4. After completion, run the full claim-check command with all required arguments and `--h1-dir results/h1_final`. Separately confirm all 12 expected cells, ten repetitions per cell, an empty partial list, and `cost_cap_usd = 330.0`. Verifier acceptance alone does not establish table completeness or compliance with the amended cap.”

4. Add to the reporting rules:

   “Preserve a dated copy of the pre-resume summary and eleven-cell table. Report R3’s H1 interpretation as INCONCLUSIVE because its audit selection is not expressible. The summary’s per-cell inconclusive flag records excess invalid repetitions only; a false flag does not remove this separate limitation.”

   Replace “The eleven cells already show the pattern the twelfth cell would complete” with “The twelfth cell’s outcome remains unknown.”

5. Replace the disclosure with:

   “The H1 run stopped at its registered 300 USD cap with eleven cells complete and `proposed|0.1` partly executed. After inspecting the eleven completed cells, but without reading the partial cell’s cached responses, the authors registered amendment 4 before further paid calls. It permits one cumulative cap increase to 330 USD. Existing cached responses are retained. The remaining cell will be reported regardless of its outcome; if the amended cap prevents completion, the table will be reported as incomplete, with no second increase. H1 remains exploratory, and R3’s H1 interpretation remains INCONCLUSIVE because its audit selection is not expressible. The recorded original FAIL and amended PASS verdicts remain unchanged.”

6. Replace “The cost is at most 30 USD” with:

   “The cap increases by 30 USD. At the stated ledger spend of 299.8872 USD, the remaining allowance is 30.1128 USD. Completion within this allowance is an estimate. The backend reserves funds before dispatch; an actual request exceeding its assumed token limits can cause a one-request overrun, which stops further calls.”

7. Expand “Permitted files” with:

   “Documentation includes `docs/lock-runbook.md`, the review memos, and `docs/lock-2026-10-17-amendment-4.txt` with its `.ots` receipt. Post-registration outputs also include the new claim-check verdict JSON and figures under `results/figures/`. Preserve `results/verdict_no_h1.json`. Running `scripts/plot.py` writes figure files; it does not require editing that script.”

ANSWERS:

1. A disclosed, outcome-independent extension to complete this exploratory table is acceptable. It remains a decision made after results were inspected. Register the corrected note before further paid calls, preserve the existing results, retain the interpretation limits, and enforce the fixed stopping rule. Reporting eleven cells is necessary only if completion fails under those conditions.

2. `verify_h1_summary` does not compare cost caps or enforce the full 12-cell grid. Cache hits bypass the paid backend; the ledger carries expenditure across restarts. This depends on unchanged inputs, intact cache, and one process. Registration can remain within `docs/`; repair 7 identifies omitted outputs. The abbreviated claim-check command lacks required arguments.

3. USD 330 is a reasonable fixed allowance based on the stated cell measurements, not a guaranteed completion cost. “No second lift” is appropriate. The measured costs were not independently audited because the excluded files were not read.

4. The disclosure needs the partial execution, cache retention, incomplete-run outcome, and R3 interpretation limit. Repair 5 supplies these. Claim signing and timestamping only after those steps occur.

5. The pilot derivation and five-percent explanation are unsupported by the repository. Other corrections concern the mutable ledger, cost allowance, verifier guarantees, and interpretation flags. The saved verdict confirms original FAIL and amended PASS. No files were changed, paid APIs called, or excluded contents read.

CONFIDENCE: 0.97.
