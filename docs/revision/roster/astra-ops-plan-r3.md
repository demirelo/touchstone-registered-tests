VERDICT: reject

FINDINGS:

References to “plan” mean `docs/superpowers/plans/2026-10-25-revision-operations.md`.

1. **Important — Task 3, plan:65; Task 5, plan:84–85.** Coverage promotion still requires `smoke`, but neither the built producer (`scripts/coverage_v2.py:83–92`) nor Task 3’s added fields supplies it. A valid coverage run therefore fails the stated schema. Also, Operation 4 passes `--branch`, which Task 5’s CLI does not declare. **Repair:** define coverage’s production/smoke metadata and add `--branch` to the promotion interface. Test the exact Operation 4 commands.

2. **Important — Task 2, plan:56–57; `scripts/tune_v2.py:95–98`.** Parallel scoring by configuration and market can overwrite tuning logs: the existing filename includes the rule, configuration, and recheck flag, but excludes the market. Recombining returned scores does not repair those files. Coverage then lacks fixture inputs (`scripts/coverage_v2.py:30–45`). The named equality test can pass while this failure remains. **Repair:** have workers return log data and let the parent write one complete configuration log, or use separate market filenames. Test coverage input extraction from the parallel run’s actual logs.

3. **Important — Task 4, plan:74–76; Task 8, plan:116.** Task-count utilisation does not necessarily match execution. Reference selection remains serial (`scripts/revision_v2.py:753–763`); cross-evaluations also run serially (`785–800`). Tasks sharing one dependency level are therefore not necessarily concurrent. Pricing them as concurrent understates billed pod time and can cause premature cap stops. The six-task and 32-task arithmetic tests cannot detect this. **Repair:** price the actual dispatch schedule, including serial work, or explicitly parallelise those stages. Test cost against a timed synthetic dispatch schedule.

4. **Important — Task 4, plan:74; Task 6, plan:94; Operations 2–5, plan:159–175.** `choose` requires a ledger and counts spent/reserved funds, but protocol checking specifies recomputation from the promoted benchmark without defining an immutable ledger snapshot or completed-work accounting. By the lock, tuning and coverage have already been paid. Adding their full estimates again can change the selected branch or produce “stop”; ignoring the ledger loses benchmark and reservation accounting. **Repair:** register the cost decision and its ledger snapshot, distinguish completed work from remaining estimates, and test benchmark → development → lock → clean-checkout verification.

5. **Important — Task 7, plan:104–107; `scripts/block_draw.py:86–97,120–121`.** Two draw-interface gaps remain. The plan names `answers`, but final records contain `answers_at_h`. Also, accepting any attested anchor permits a later valid attestation to change H, although the built reader selects the lowest valid anchor and design §7.3 fixes the anchor rule. The substitution tests do not cover two valid attestations. **Repair:** consume `answers_at_h`, enforce the canonical anchor selection, and test an unchanged producer record plus a substituted later valid anchor.

6. **Important — Task 5 tests, plan:85–86; `scripts/tune_v2.py:102–105`.** The proposed passing fixture runs tuning with `--smoke` and changes only `smoke` to false. Its recorded budgets remain smoke budgets, which the promotion checks must reject. Thus a correct validator fails the “passing” test; weakening budget checks would make it pass incorrectly. **Repair:** stub expensive computations while retaining production arguments, budgets, counts, and metadata. Keep relabelled smoke output as a refusal case.

7. **Important — Task 4 tests, plan:75–76.** `test_reservations_are_aggregate` checks sequential allocations. An implementation without the required exclusive lock can pass it while concurrent processes read the same balance and oversubscribe the cap. **Repair:** add a multiprocess test that synchronises competing reservations and checks the committed aggregate. The other new worker-dispatch, verification-side-effect, six-slot Holm, and doubling-label assertions directly target their stated failures.

Sol round-2 findings:

S1: closed — proof-to-protocol binding is explicit; finding 5 identifies separate remaining draw requirements.  
S2: partly closed — coverage metadata still conflicts with promotion.  
S3: closed — branch propagation and mismatch tests, plan:65–66,168.  
S4: closed — reservations and exclusive locking are specified, plan:75.  
S5: partly closed — actual serial dispatch remains unpriced explicitly.  
S6: closed — verification forbids H4 import, salt installation, and writes, plan:116–118.  
S7: closed — absent freezes become unavailable contexts, plan:116,126,130.  
S8: closed — six Holm slots and the numerical boundary test, plan:129–130.  
S9: closed — ascending tiers are explicit; the complete-freeze ruling remains accepted, plan:116–118.  
S10: closed — exact endpoints, recomputed bounds, and admission agreement, plan:85–86.  
S11: partly closed — worker assertions improved; findings 2, 6, and 7 remain. The diagnostic-only doubling ruling is accepted and directly tested, plan:128–130.

Previously partial Sol round-1 findings: S1 closed; S2 partly closed; S4 closed; S6 closed; S7 partly closed; S11 closed; S12 closed; S14 partly closed.

Astra round-2 cross-check: A1 closed; A2 closed; A3 partly closed; A4 closed; A5 closed; A6 closed; A7 closed; A8 partly closed.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of future tests. No paid APIs were called, no files were changed, and `sealed/` was not read.

CONFIDENCE: 0.92.