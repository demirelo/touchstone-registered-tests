VERDICT: reject

CORRECTIONS:
1. **Section 2; `runnerup_v2.py:126`, `runnerup_v2.py:144`.** Fix the freeze guards before the pod. Acceptance permits an empty `records` map; an in-memory probe confirmed this. Require the complete bank, search, and reference dependency sets, expected cuts and H4 status, current provenance, and matching hashes. Pre-freeze currently checks file existence only. Add tests for omitted dependencies and stale records.

2. **Section 2, validation.** Carry forward the reset draft-5 reproduction evidence and pod gate. A smoke run establishes that dependencies resolve; it does not establish full-budget numerical reproduction. Require the saved search/evaluation and doubling checks, then the pod reproduction gate before the 12 cells. Include its cost.

3. **Sections 3–4; `runnerup_v2.py:174`.** Complete the doubled analysis and expectation scoring before outcomes. The current analysis reads base evaluations only. Specify matched base and doubled contrasts for all three rules, using each rule’s unchanged frozen reference. Score the exact paired C* minus runner-up contrast, rather than the rounded 0.0207 threshold. Define ties and missing doubled records.

4. **Sections 1 and 3; `common.py:34`.** Keep the nominal intervals descriptive and conditional on these six markets and selected policies. Recompute C* minus R3 with the same nominal method beside the runner-up contrast; otherwise a category change can reflect the inference method. State that this tests one development-selected alternative. Defer gain-based selection across all configurations, honest churn, and search convergence explicitly.

5. **Sections 5–6.** The benchmark arithmetic reproduces 17.65 core-hours and USD 1.91. Set a numerical cap, separate ledger category/reservation, and stop rule before launch. The existing wrapper uses the reset’s `followup` category. Also account for six serial reference calls and any reproduction gate when setting the wall-time allowance.

6. **Section 2; `reset_followup_v2.py:118`.** Record hashes for `runnerup_v2.py` and `common.py` in the inventory. The reused environment helper records its own reset-driver hash under `driver_sha256`, which does not identify this driver.

CONFIDENCE: 0.95.