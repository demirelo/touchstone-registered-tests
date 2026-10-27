VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/benchmark_v2.py:121`: freeze cost is eight times too high.** `measure()` already converts the measured attack row into a complete 8 × 8 family matrix at `scripts/benchmark_v2.py:387`. The freeze calculation multiplies that matrix timing by eight again. With the existing POD fixture, this prices the training matrices at 2,688 seconds instead of 336 seconds. A probe with the unchanged USD 40 evaluation cap produced cut level 1; the corrected calculation produced level 0.

   **Repair:** use `ts["cross_item"] * TRAIN_SEEDS / FINAL_SEEDS`. Keep the single serial task per context. Correct the test at `tests/test_benchmark_v2.py:312`, which repeats the erroneous factor. Also correct `docs/revision/part-a2-ledger-2026-10-27.md:74`: `cross_item` represents the complete matrix. The rulings at ledger lines 69 and 70 agree with the design.

DECLINED TO JUDGE: Full file-based suite and paid execution. The sandbox has no writable temporary or Matplotlib cache directory. With optional plotting disabled in memory, 13 focused pytest tests passed using `-p no:cacheprovider`. Six report regression checks and the extended G_min check passed with record storage replaced by memory; all failed against `3272b1b`. The profit and billing regression tests also failed against the old code and passed on HEAD, although the billing test has the incorrect expected value described above. No further operation-changing defect was found in the other six fixes. Neither sealed directory was read.

CONFIDENCE: 0.96