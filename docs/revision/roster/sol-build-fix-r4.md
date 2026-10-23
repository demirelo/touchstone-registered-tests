VERDICT: approve-with-caveat

FINDINGS:

1. **Minor — `tests/test_benchmark_v2.py:110-111`.** Sol round-3 finding 2 remains partly open. The bank test checks only the current count of 11. An implementation that hard-codes 11 or supplies duplicate points can satisfy this assertion; shortage refusal is not tested. **Repair:** vary the manifest count, assert projected candidate distinctness, and require a short archive to fail. Independent probes confirmed that the current implementation returns distinct points and refuses shortages (`scripts/benchmark_v2.py:106-121`).

Sol R3 #1: closed — `scripts/benchmark_v2.py:47,141,195`; all 231 inner configuration-markets and 30 rechecks include reference costs. I1 rejects `441fc48`, including a semantic check with its missing constant supplied, and rejects a partial fix that omits recheck references.

Sol R3 #2: partly closed — finding 1 remains. The other test gaps are closed at `tests/test_benchmark_v2.py:130,144`, `tests/test_revision_v2.py:460`, `tests/test_intervals_v2.py:146`, and `tests/test_calibration_v2.py:197,203`.

Astra R3 #1: closed — `scripts/benchmark_v2.py:195`; adding one reference-second adds 30 development-seconds and 118 evaluation-seconds. Adding one inner-configuration-second adds 231 development-seconds.

Astra R3 #2: closed — `tests/test_calibration_v2.py:203`; the missing-pooled-trace mutation now fails. Wrong-X7-cost and omitted-reference-total mutations also fail.

F1: closed — `scripts/block_draw.py:135`; protocol digest binding.  
F2: closed — `scripts/revision_v2.py:483`; expected provenance and dependencies.  
F3: closed — `scripts/revision_v2.py:174`; H4 hash binding.  
F4: closed — `scripts/revision_v2.py:511,555,707`; validated reuse and freeze dependencies.  
F5: closed — `scripts/revision_v2.py:853`; selection preserves the full catalog.  
F6: closed — `scripts/revision_v2.py:774`; prerequisites precede workers; unique temporary names at `sim/records_v2.py:14`.  
F7: closed — `scripts/revision_v2.py:671`; welfare metadata retained.  
F8: closed — `sim/intervals.py:118,139`; invalid inputs refused; constants remain exact.  
F9: closed — `sim/calibration_v2.py:110,113`; production-bound parity and complete traces.  
F10: closed — `scripts/tune_v2.py:115`; rechecks retain grid order.  
F11: closed — `scripts/benchmark_v2.py:141,195`; all 16 real smoke components passed with in-memory storage. No reserved seed was used: smoke episodes used 1000, 2000, 2001; registered inner scoring uses 1000–1002 (`scripts/tune_v2.py:68`).  
F12: closed — `scripts/revision_v2.py:287,411`; welfare embedding and controls.

Replacement ruling: **accept** (`docs/revision/build-ledger-2026-10-22.md:88`). Development and evaluation reference costs now reach USD totals. The composed recheck workload is a conservative estimate; actual runtime remains unverified.

Review Focus checks found no regression. A complete 62-record development context passed in-memory validation; evaluation, cross, and doubling refused a missing freeze. **All twelve frozen files are byte-identical to `2a288f5`** (`tests/test_frozen_files.py:15`).

DECLINED TO JUDGE: Filesystem atomicity, process concurrency, paid performance, empirical coverage, live explorers, and sealed contents. With `-p no:cacheprovider`, **171 tests passed**. Temporary-file restrictions blocked **48 tests**: nine benchmark, 29 runner, six tuning, two calibration, two records. In-memory probes supplemented these. The selected suites’ 791 slow cases were deselected; the full suite was not run. No paid APIs, `sealed/` reads, or file changes.

CONFIDENCE: 0.94