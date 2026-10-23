VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/benchmark_v2.py:140`, `:105`.** `measure()` runs W1 before `reference_eval`, but W1 requires `state["ref"]`. The default closures reproduced `KeyError: 'ref'` with searches stubbed in memory. **Repair:** create the reference before W1. Test the default workload sequence with expensive operations replaced by stubs. **Reject the new benchmark ruling:** this failure can be detected without pod time.

2. **Important — `scripts/benchmark_v2.py:35`, `:95`, `:111`, `:127`.** F11 still measures incomplete workloads. Reference construction supplies no bank candidates; welfare and coalition timings omit their evaluations. The “cross row” runs eight honest-max profiles, and the cost table ignores its measured time. Thus cap and approval estimates still depend on substitute workloads. **Repair:** measure the declared cell scope and actual cross workload, then use those measurements in the table.

3. **Important — `scripts/revision_v2.py:765`.** Cross resume checks only dependency entries supplied by the old record. It does not require the expected stage, provenance, or dependency set. In memory, an accepted context with 146 required records skipped both cross records despite foreign provenance, a wrong stage, and empty dependencies. **Repair:** derive the complete expected cross record independently and validate it before skipping.

4. **Important — `scripts/revision_v2.py:680`, `:630`.** Doubling dependencies exclude the freeze and the additional searches read through `menu()`. A replacement freeze left an existing doubling record marked `skipped` in the probe. **Repair:** accept the current freeze before doubling and bind the result to its hash and every input used by the diagnostic.

5. **Important — `scripts/revision_v2.py:379`, `:385`, `:731`.** Auxiliary resume remains inconsistent. Coalition prerequisites reuse a matching-provenance record with a wrong stage; the probe preserved that wrong stage. Reference resume silently overwrites foreign provenance instead of refusing, contrary to the plan’s crash-resume requirement. **Repair:** use the complete expected-record validator for auxiliary resume. Refuse foreign provenance; recompute invalid same-provenance records.

6. **Important — `sim/intervals.py:120`, `:152`.** Production inference still accepts nonfinite input. Six strata containing one NaN each produced Q1 `p=0.0002`, rejection, and category `C lower`. Calibration’s finite-bound check does not protect inference. **Repair:** reject nonfinite or insufficient samples before all bound and p-value calculations. Add decision-level rejection tests.

7. **Important — `sim/calibration_v2.py:110`, `:117`.** Calibration does not fully reproduce production’s constant-sample rule. For 200 copies of `1.1`, production returns upper bound `1.1`; calibration returns `1.0999999999999996`. Against a constant 20,000-value pool, calibration counted three upper misses in three replications; production counted none. **Repair:** share production’s exact-constancy handling. Test parity through `miss_counts()`. The test at `tests/test_calibration_v2.py:140` still passed when `miss_counts()` was replaced with a function that always raises.

8. **Minor — `tests/test_credibility.py:66`.** The residual-picks test still cannot distinguish static from dynamic ordering. **Accept its deferral as non-blocking:** the proposed distinguishing case returned `[0,3,1,2]` in the current implementation. **Repair:** add that case to the test suite.

The baseline test assessments below are from source comparison, with additional in-memory probes where stated.

F1: **closed** — `scripts/block_draw.py:132` checks the protocol digest before anchoring. Test `tests/test_block_draw.py:139` would fail on baseline; a helper-only fix without CLI wiring would pass.

F2: **closed** — `scripts/revision_v2.py:468` checks independently derived provenance and dependency sets. Tests at `tests/test_revision_v2.py:280` and `:290` would fail on baseline, but a reference-only partial fix could pass. Full-catalog auxiliary probes rejected foreign records.

F3: **closed** — `scripts/revision_v2.py:174` includes H4’s hash in job provenance. Test `tests/test_revision_v2.py:299` would fail on baseline; it does not exercise two-bundle resume or freeze acceptance.

F4: **partly closed** — search and evaluation validation improved; findings 3–5 remain. Tests at `tests/test_revision_v2.py:307` and `:316` would fail on baseline but pass the current incomplete fix.

F5: **closed** — `scripts/revision_v2.py:821` retains the catalog before selection. Test `tests/test_revision_v2.py:327` would fail on baseline; it covers the API, so missing CLI wiring could still pass.

F6: **closed** — `scripts/revision_v2.py:743` creates prerequisites before dispatch; `sim/records_v2.py:15` uses unique temporary names. Test `tests/test_revision_v2.py:334` would fail on baseline, but mocked dispatch and source inspection do not establish concurrent-write behaviour.

F7: **closed** — `scripts/revision_v2.py:639` restores welfare metadata. Real W1 doubling failed with the baseline function and completed with the fix. Test `tests/test_revision_v2.py:348` catches that crash, but weakly checks W0 and unchanged-winner metadata.

F8: **partly closed** — zero-variance cases now complete, but findings 6–7 remain. Tests at `tests/test_intervals_v2.py:86` and `tests/test_calibration_v2.py:133` distinguish baseline failures; they omit nonfinite inputs and nonzero constant parity.

F9: **partly closed** — fixed production bootstrap streams are used at `sim/calibration_v2.py:110`; finding 7 prevents full procedure parity. Test `tests/test_calibration_v2.py:140` would fail on baseline because helpers are absent, but helper-only partial fixes pass.

F10: **closed** — `scripts/tune_v2.py:110` preserves grid indices. Test `tests/test_tune_v2.py:87` distinguishes the original scenario: the baseline selected `L=10`; the fix selected `L=3`.

F11: **partly closed** — development seeds and separate timing entries improved, but findings 1–2 remain. Tests at `tests/test_benchmark_v2.py:44` and `:56` would fail on baseline; stub workloads conceal the default-path faults.

F12: **closed** — `scripts/revision_v2.py:272` and `:395` apply welfare embedding and controls. Test `tests/test_revision_v2.py:359` would fail on baseline but covers only W0 with controls mocked. A separate W1 probe confirmed embedding, dependency binding, and invocation of the 769-control set.

DECLINED TO JUDGE: Paid performance, empirical coverage, live explorers, sealed contents, and historical RED claims. No paid APIs or `sealed/` access. With `-p no:cacheprovider`, 115 tests passed; 35 tests requiring temporary files were blocked across `test_revision_v2.py`, `test_tune_v2.py`, `test_benchmark_v2.py`, and `test_calibration_v2.py`. One slow test was skipped. Plotting imports were disabled. Exit-round, empty/exhausted-budget, and seed-separation checks passed. All twelve frozen-file byte comparisons against `2a288f5` passed. No files changed.

CONFIDENCE: 0.96