VERDICT: accept-with-caveat

CORRECTIONS:

1. **§5; `runner-up-plan.md:139`; `guards.py:121`.** Remove the stale statement that accounting starts at `--started-at`. The corrected code counts from the recorded open event. The round-6 probe now refuses admission: USD 3.06 already spent plus USD 0.3416 for reproduction.

2. **None — remaining round-6 Run A corrections.** Ledger structure and amount checks, search-stage and identity checks, evaluation identity, the corrected reservation command, and full-grant verification are present. Malformed-ledger and insufficient-grant probes refuse admission. Run A retains the corrected accounting start and checks STOP/deadline before each internal stage.

3. **None — §§1–4 and driver correctness.** The estimand answers sensitivity to one development-selected alternative; it does not establish the best gain-selected comparator. Matched base/doubled contrasts, advance expectations, nominal conditional intervals, and deferrals are appropriate. All 12 specifications, pairings, budgets, configurations, reference dependency sets, and 108 bank hashes passed. Both Run A Mac gates passed recomputation. Cost reproduces: 17.65 core-hours, USD 1.99 billed estimate, USD 3.00 admission cap.

4. **Before allocation — §§2, 5–6.** Retain the separately named launcher-copy and offline-test prerequisite. Verify cumulative admission before reproduction, argument transfer, STOP/deadline handling, retrieval, and deletion. Its absence does not reject this Run A driver review. Forty-two read-only tests passed; 52 tests requiring writes, including smoke execution, were not rerun. Require the full suite before allocation and bit-identical pod reproduction before searches.

5. **Run B only; `convergence_v2.py:368`.** Pass `stop.started` into `cargs`, rather than `a.started`. Worker reconstruction currently loses the corrected accounting start. An in-memory probe counted USD 4.48 against a USD 4.25 cap: the validated stopper refused, but the reconstructed worker admitted another round. Fix and test before Run B allocation.

6. **Run B evidence; `followup2-conv-gate/gate/`.** Both saved records report passes, but their `guards.py` and convergence-plan hashes still differ from this checkout. The current-code rerun remains unverified. Require matching final-code evidence before Run B.

CONFIDENCE: 0.98