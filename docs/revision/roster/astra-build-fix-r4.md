VERDICT: approve-with-caveat

FINDINGS:

1. **Minor — `tests/test_benchmark_v2.py:111`.** The round-3 H1 test gap remains. An executed mutation returned eleven copies of one bank point per family; the complete smoke test still passed. It also lacks a shortage-refusal assertion. A future bank regression could therefore reduce the measured reference workload without failing this test. **Repair:** assert distinct projected candidates, exclusion of the best point, and refusal when fewer than eleven candidates exist. Current production code passed these independent probes.

Sol R3 #1: **closed** — `scripts/benchmark_v2.py:46`, `:141`, `:195`; all 231 inner configuration-markets and 30 rechecks are priced. One added reference-second increases development by 30 seconds and evaluation by 118 seconds.

Sol R3 #2: **partly closed** — finding 1 remains. Evaluation-component mutations, omitted reference totals, and missing pooled traces are now rejected (`tests/test_benchmark_v2.py:130`, `:144`; `tests/test_calibration_v2.py:203`). Envelope mutations and parameterized constants are covered (`tests/test_revision_v2.py:460`; `tests/test_intervals_v2.py:148`).

Astra R3 #1: **closed** — `scripts/benchmark_v2.py:141`; the real scorer selected a development reference and performed three evaluations.

Astra R3 #2: **closed** — `tests/test_calibration_v2.py:203`; removing every pooled trace entry now fails.

F1: **closed** — `scripts/block_draw.py:135`; digest-binding test passed.  
F2: **closed** — `scripts/revision_v2.py:483`; all 146 synthetic records validated; provenance and dependency mutations were rejected.  
F3: **closed** — `scripts/revision_v2.py:174`; H4 hash remains bound.  
F4: **closed** — `scripts/revision_v2.py:252`, `:707`; reuse, stale-record handling, and replacement-freeze probes passed.  
F5: **closed** — `scripts/revision_v2.py:853`; selected execution retains the full catalog.  
F6: **closed** — `scripts/revision_v2.py:774`; prerequisite-order test passed; unique temporary filenames remain.  
F7: **closed** — `scripts/revision_v2.py:671`; welfare metadata remains preserved.  
F8: **closed** — `sim/intervals.py:118`, `:139`; invalid-input and parameterized constant tests passed.  
F9: **closed** — `sim/calibration_v2.py:110`, `:113`; production-bound parity passed.  
F10: **closed** — `scripts/tune_v2.py:115`; tie-order test passed in memory.  
F11: **closed implementation** — `scripts/benchmark_v2.py:195`; test caveat above.  
F12: **closed** — `scripts/revision_v2.py:287`, `:411`; welfare embedding/control probe passed.

I1 passed at HEAD and rejected `441fc48`, including after supplying its missing constant to reach the behavioral assertion. Partial fixes omitting either inner costs or recheck references also failed (`tests/test_benchmark_v2.py:154`, `:155`).

**Replacement ruling: accept** — `docs/revision/build-ledger-2026-10-22.md:88`; development workload coverage is restored, with the stated conservative recheck composition.

Review Focus checks found no regression. Evaluation, cross, and doubling refused missing freezes. All 16 real smoke components completed. `dev_inner_config` used no reserved evaluation seed; observed seeds were development/calibration only (`scripts/tune_v2.py:56`, `:88`; `sim/instances.py:19`).

All twelve frozen files are byte-identical to `2a288f5`; all byte-comparison tests passed (`tests/test_frozen_files.py:15`).

DECLINED TO JUDGE: Paid performance, empirical coverage, live explorers, sealed contents, filesystem atomicity, and process concurrency. Pytest used `-p no:cacheprovider`: **192 passed**; 791 skipped. Temporary-file restrictions blocked 48 tests: benchmark 9, runner 29, tuning 6, calibration 2, records 2. In-memory probes supplemented these; the full suite was not run. No paid APIs, `sealed/` reads, or file changes.

CONFIDENCE: 0.94