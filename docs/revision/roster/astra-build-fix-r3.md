VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/benchmark_v2.py:44`, `:53`, `:185`; `scripts/tune_v2.py:78`.** Removing reference costs from the cell unit also removes them from development rechecks. The new reference row contributes only to evaluation. Development still selects references for each configuration and market; the inner benchmark also omits this selection. A synthetic probe added one reference-second: development cost increased by **zero**, versus 45 seconds before this change. A real development smoke probe confirmed that reference selection executes additional episodes. Near the development cap, this omission can permit excess spending. **Repair:** measure development reference selection with its actual menu and cache use, price it once per configuration/market, and test development totals.

2. **Minor — `tests/test_calibration_v2.py:202`.** The pooled parity loop does not check trace length or completeness. An in-memory mutation that omitted every pooled trace entry still passed `test_h5_every_replication_bound_equals_production`. Thus, the test can silently stop comparing pooled replications. Current production tracing works. **Repair:** assert the complete expected set of replication/statistic/side/tail/kappa entries before comparing bounds.

H-test assessment against `05ca92b` and partial fixes:

- **H1 — `tests/test_benchmark_v2.py:97`:** rejects the baseline by source inspection: its result lacks `bank_sizes`. It permits removal of the short-bank refusal. Supplemental execution completed all 18 real smoke components, supplied 11 points per family, and refused a shortened archive. Projection and deduplication are enforced at `scripts/benchmark_v2.py:108`.
- **H2 — `tests/test_benchmark_v2.py:122`:** failed against substituted baseline code and passed at HEAD. The original coalition-search probe changed additional evaluation cost by **731.43 seconds** at baseline and **zero** at HEAD. Homogeneous evaluation timings leave some incorrect component mappings undetected; the unequal timings in G7 provide additional coverage.
- **H3 — `tests/test_benchmark_v2.py:133`:** failed against baseline and passed at HEAD. It rejects allocation through profit cells. It does not check development reference costs or inclusion of the reference row in aggregate totals.
- **H4 — `tests/test_revision_v2.py:445`:** failed against baseline and passed with in-memory storage. It tests valid reuse for both record types, but stale/foreign handling only for banks. Supplemental probes confirmed recomputation and refusal for both banks and envelopes.
- **H5 — `tests/test_intervals_v2.py:133`; `tests/test_calibration_v2.py:191`:** both failed against baseline and passed at HEAD. The constant test rejects a mean-only partial fix because it also checks bounds and both p-value directions. The parity test permits finding 2. Holm and Q4 refusal checks passed.

**Replacement ruling — reject as implemented**, `docs/revision/build-ledger-2026-10-22.md:81`. The search-plus-40-seed unit and separate 118-menu evaluation row are valid. However, this change does more than normalize units: it removes development reference costs without replacement.

Sol R2 #1: **closed** — manifest-derived bank size; `scripts/benchmark_v2.py:99`.  
Sol R2 #2: **closed** — independent evaluation components; `scripts/benchmark_v2.py:191`.  
Sol R2 #3: **closed** — validated derived-record reuse; `scripts/revision_v2.py:511`.  
Astra R2 #1: **closed** — exact equal-stratum mean; `sim/intervals.py:139`.  
Astra R2 #2: **closed** — bank size and shortage refusal; `scripts/benchmark_v2.py:113`.  
Astra R2 #3: **closed** — 118 evaluation references; `scripts/benchmark_v2.py:53`.

F1: **closed** — digest-binding test passed; `tests/test_block_draw.py:139`.  
F2: **closed** — provenance/dependencies; `scripts/revision_v2.py:483`.  
F3: **closed** — H4 hash binding; `scripts/revision_v2.py:174`.  
F4: **closed** — resume and freeze checks; `scripts/revision_v2.py:511`.  
F5: **closed** — full catalog retained; `scripts/revision_v2.py:853`.  
F6: **closed** — prerequisites precede workers; `scripts/revision_v2.py:771`.  
F7: **closed** — welfare metadata retained; `scripts/revision_v2.py:671`.  
F8: **closed** — exact constants and input refusal; `sim/intervals.py:139`.  
F9: **closed implementation** — production bounds; `sim/calibration_v2.py:110`; test caveat in finding 2.  
F10: **closed** — original grid tie order; `scripts/tune_v2.py:51`.  
F11: **partly closed** — development cost omission in finding 1.  
F12: **closed** — welfare embedding and controls; `scripts/revision_v2.py:411`.

Review Focus checks found no further regression. A 150-record synthetic context passed validation; evaluation, cross, and doubling refused a missing freeze. Exit-round, empty-budget, and seed-separation tests passed. **All twelve frozen files are byte-identical to `2a288f5`.**

DECLINED TO JUDGE: Paid performance, empirical coverage, live explorers, sealed contents, and the full slow suite. Pytest used `-p no:cacheprovider`: **161 passed**. Temporary-file setup blocked 45 tests: 29 runner, eight benchmark, six tuning, two calibration. One slow test was skipped. In-memory probes do not verify filesystem or process concurrency. No paid APIs, `sealed/` reads, or file changes.

CONFIDENCE: 0.94.