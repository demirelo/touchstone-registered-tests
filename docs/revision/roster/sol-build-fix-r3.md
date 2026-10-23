VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/benchmark_v2.py:44`, `:53`, `:185`; `scripts/tune_v2.py:78`, `:87`.** Removing reference selection from the cell unit leaves development rechecks without a reference-cost component. Comparator and system rechecks construct **30 development reference menus**: six plus 24. The separate 118-menu row enters only the evaluation total. In the timing probe, adding one reference-second added 118 evaluation-seconds and **zero development-seconds**. This can understate the development cap and total approval estimate. **Repair:** measure development-menu selection and price it once per rechecked configuration and market; include the inner-search menus too. Add development-total sensitivity tests. **Replacement ruling (`docs/revision/build-ledger-2026-10-22.md:81`): reject as implemented.** Separate evaluation-reference pricing is correct, but this change affects workload coverage, not only normalization.

2. **Minor — regression-test coverage.** All H tests reject `05ca92b`, but plausible partial fixes still pass:
   - **H1**, `tests/test_benchmark_v2.py:109`: rejects the base’s missing bank-size result; permits hard-coded counts and does not test scarcity refusal or inspect candidate distinctness. The current implementation passed independent distinctness and scarcity probes.
   - **H2**, `tests/test_benchmark_v2.py:122`: rejects the base. An executed mutation that uses profit-evaluation costs for X7 and welfare still passes. **Repair:** vary every evaluation component separately.
   - **H3**, `tests/test_benchmark_v2.py:133`: rejects the base. An executed mutation that omits references from the totals still passes. **Repair:** assert evaluation units, USD totals, and cap effects.
   - **H4**, `tests/test_revision_v2.py:445`: rejects the base’s repeated writes. It mutates only the bank, so envelope-only stale/foreign defects can pass. **Repair:** apply both mutation checks to both record kinds.
   - **H5 constants**, `tests/test_intervals_v2.py:133`: rejects the base and distinguishes bounds-only or one-direction repairs. It tests one constant. **Repair:** parameterize values and stratum sizes.
   - **H5 parity**, `tests/test_calibration_v2.py:191`: rejects the base’s missing `trace` interface. An executed mutation that emits no pooled trace still passes because the loop is empty. **Repair:** assert pooled trace length. Holm/Q4 refusal checks already pass against the base.

Sol R2 #1: closed — `scripts/benchmark_v2.py:98`; real smoke supplied 11 distinct bank points per family and refused scarcity.  
Sol R2 #2: closed — `scripts/benchmark_v2.py:190`; further evaluation costs follow evaluation components.  
Sol R2 #3: closed — `scripts/revision_v2.py:511`; both derived kinds reuse valid records, recompute stale records, and refuse foreign records.  
Astra R2 #1: closed — `sim/intervals.py:139`, `:233`; exact constants preserve the true null in both directions.  
Astra R2 #2: closed — `scripts/benchmark_v2.py:98`.  
Astra R2 #3: closed — `scripts/benchmark_v2.py:53`; evaluation menus are priced exactly 118 times.

F1: closed — `scripts/block_draw.py:135`.  
F2: closed — `scripts/revision_v2.py:483`; full 146-record validation passed.  
F3: closed — `scripts/revision_v2.py:174`.  
F4: closed — `scripts/revision_v2.py:511`, `:723`, `:798`.  
F5: closed — `scripts/revision_v2.py:853`; selected execution retains the full catalog.  
F6: closed — `scripts/revision_v2.py:774`; concurrency itself remains unverified.  
F7: closed — `scripts/revision_v2.py:671`.  
F8: closed — `sim/intervals.py:118`, `:139`.  
F9: closed — `sim/calibration_v2.py:110`, `:113`; replication parity passed.  
F10: closed — `scripts/tune_v2.py:115`.  
F11: partly closed — finding 1.  
F12: closed — `scripts/revision_v2.py:287`, `:411`.

Review Focus checks found no further regression. Evaluation before freeze was refused; replacement freezes reran doubling with all 26 dependencies. Total/min shared provenance remained compatible. Development-seed smoke completed all 18 components. **All twelve frozen files are byte-identical to `2a288f5`** (`tests/test_frozen_files.py:15`).

DECLINED TO JUDGE: Paid performance, empirical coverage, live explorers, sealed contents, historical RED claims, filesystem atomicity, and process concurrency. Pytest used `-p no:cacheprovider`: **183 passed**, one slow test skipped. Temporary-file restrictions blocked **47 tests**: 29 runner, eight benchmark, six tuning, two calibration, and two records tests. In-memory probes supplemented these; they do not establish filesystem behavior. No paid APIs, `sealed/` reads, or file changes.

CONFIDENCE: 0.94