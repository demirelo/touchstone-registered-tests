VERDICT: reject

FINDINGS:

References to “plan” mean `docs/superpowers/plans/2026-10-25-revision-operations.md`.

1. **Important — Task 8, plan:116–118; `sim/instances.py:13,72–73`; `sim/calibrate.py:44–47`.** The verification test still permits calibration episodes. `instances` imports its own `calibrate` binding. Patching `sim.calibrate.calibrate` after that import does not replace this binding. Calibration calls `first_best_episode`, which bypasses the proposed `run_focal` patch. An implementation that recalibrates before checking records can therefore pass. Also, unchanged output-directory hashes do not prohibit writes elsewhere. **Repair:** patch `sim.instances.calibrate` and the actual first-best execution binding; prohibit filesystem writes throughout verification. Test these faults explicitly. The recorded-configuration interface is sound, but its test does not yet enforce the full requirement.

2. **Important — Task 4, plan:74–76; `scripts/revision_v2.py:734–750`.** Task-count utilisation does not price waves with unequal task durations correctly. For 16 tasks on 16 workers, comprising fifteen one-second tasks and one 100-second task, the stated formula gives 115/16 = 7.1875 billed seconds. The wave requires at least 100 seconds. Search waves contain different families, so equal duration is not assured. `test_evaluation_bill_follows_the_dispatch_plan` uses equal-duration tasks and cannot detect this error. **Repair:** price the elapsed duration of each worker schedule, or use a conservative bound. Include unequal durations and compare costs against the runner’s recorded dispatch, including serial prerequisites.

3. **Important — Tasks 4 and 6, plan:74–76,94; Operations 2 and 7, plan:159,186.** Freezing the cost decision leaves a later approval gap. A forecast below USD 40 requires no approval. Actual development spend can then reach USD 12, and evaluation spend USD 27. The stated reservation rule grants another USD 4 against an estimate of USD 3.20: both phase caps hold, but combined spend plus reserved funds reaches USD 43. Neither `reserve` nor the later operations require approval at this boundary. **Repair:** retain the frozen registration decision, but add a live approval check before reservations can take the combined total above USD 40. Test this crossing after a previously unapproved forecast below USD 40.

4. **Important — Task 8 tests, plan:118; dispatch contract, plan:116; `scripts/revision_v2.py:734–739`.** The priority tests check order at a patched `_pool` boundary. The reference test also requires one pool call containing every menu. A sorted submission list can pass both tests while lower-priority tasks start before slower higher-priority tasks finish. This violates the explicit tier-completion requirement. **Repair:** specify a completion barrier between tiers. Test task start and finish events with a blocked higher-priority task. Make the reference test permit the required tier waves and assert that every menu executes exactly once. Retain the complete-freeze rule.

Sol round-3 finding 1: **closed** — parent-only merged logs and coverage-input extraction are explicit, plan:56–57.  
Sol round-3 finding 2: **closed** — production arguments with expensive work stubbed replace relabelled smoke outputs, plan:85–86.  
Sol round-3 finding 3: **closed** — `answers_at_h` and unchanged-reader acceptance are explicit, plan:104–107.  
Sol round-3 finding 4: **closed** — lowest-valid-anchor checks and later-attestation refusal are explicit, plan:106–107.  
Sol round-3 finding 5: **partly closed** — recorded inputs remove the intended side effects; finding 1 identifies remaining test gaps.  
Sol round-3 finding 6: **closed** — the decision and ledger snapshot are frozen and the decision hash is checked, plan:74,94–96. Finding 3 concerns later spending authority.  
Sol round-3 finding 7: **partly closed** — reference and cross parallelism are required, plan:116; findings 2 and 4 prevent closure of dispatch-based billing and verification.

Astra round-3 finding 1: **closed** — coverage `smoke` and promotion `--branch`, plan:65,84.  
Astra round-3 finding 2: **closed** — plan:56–57.  
Astra round-3 finding 3: **partly closed** — findings 2 and 4.  
Astra round-3 finding 4: **closed** — plan:74,94–96.  
Astra round-3 finding 5: **closed** — plan:104–107.  
Astra round-3 finding 6: **closed** — plan:85–86.  
Astra round-3 finding 7: **closed** — the multiprocess reservation test is specified, plan:76.

Previously partial round-1 findings: S1 **closed** (plan:65,85); S2 **closed** (104–107); S4 **closed** (19,116); S6 **closed** (56–57,65–66,168); S7 **partly closed** (findings 2–3); S14 **partly closed** (findings 1 and 4). S11 **closed**: diagnostic doubling labels remain reported and nondecisive, with a paired-label test (128–130). S12’s complete-freeze ruling remains **accepted** (117); finding 4 concerns dispatch enforcement.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication services, and execution of future tests. Checks used source inspection and small arithmetic probes. No paid APIs were called; `sealed/` and H4 bundle contents were not read. No files were changed.

CONFIDENCE: 0.94.