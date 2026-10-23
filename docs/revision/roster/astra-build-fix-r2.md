VERDICT: request-changes

FINDINGS:

1. **Important — `sim/intervals.py:144`, `:228`.** The pooled path does not preserve exact constants. Reproduced with six strata containing 200 copies of `1.1`: pooled mean and bounds are `1.0999999999999999`; `stratified_pvalue(strata, 1.1, "upper", 99)` returns **0**, while the single-sample path returns **1**. The true-null rejection remains possible. **Repair:** apply the exact-constant rule when combining stratum means. Test the bound against `1.1` and test both p-value directions. `tests/test_intervals_v2.py:130` compares functions that share this error.

2. **Important — `scripts/benchmark_v2.py:95`, `:110`.** The benchmark supplies at most seven bank candidates per family. Production uses eleven other matched rules in the default context (`scripts/revision_v2.py:334`; `sim/manifest_v2.py:94`). Thus the measured reference workload can omit four required candidates per family, and the cost table can underestimate reference work. **Repair:** derive the bank size from the effective manifest and test the supplied candidates before deduplication. The G6 smoke test checks completion, not this workload scope.

3. **Minor — `scripts/benchmark_v2.py:45`, `:173`.** Half-reference allocation is applied to every profit cell, including extra families that share an already-priced reference. The manifest has **326 profit cells but 118 reference menus**. The current formula charges **163 reference equivalents**, an excess of 45. A synthetic timing probe confirmed that one additional reference-second adds 163 cell-seconds. This can cause unnecessary cap cuts. **Repair:** price reference menus once per context/rule, separately from searches and evaluations; test the aggregate against manifest counts.

Test assessment against `109e597` and plausible partial fixes:

- **G1**, `tests/test_revision_v2.py:388`: rejects baseline by source comparison. Its one-rule fixture permits a partial fix that omits other rules’ references. My 146-record probe confirmed the current full-context resume checks.
- **G2**, `:406`: rejects baseline by source comparison. The fixture lacks other rules’ bank inputs. My full-context doubling probe found 26 dependencies, refused a missing freeze, and recomputed after freeze replacement.
- **G3 reference/coalition**, `:419`, `:430`: both reject baseline by source comparison. They permit omissions in envelope/bank handling and untested coalition mutations. Current shared validation covers those stages by inspection.
- **G4 samples/pools**, `tests/test_intervals_v2.py:100`, `tests/test_calibration_v2.py:182`: both rejected substituted baseline code. Partial validation confined to tested entry points could pass; direct Holm/Q4 rejection coverage remains absent.
- **G5 exactness/parity**, `tests/test_intervals_v2.py:123`, `tests/test_calibration_v2.py:162`: both rejected substituted baseline code. Exactness misses finding 1. The parity test exercises `miss_counts`, but compares accumulated misses, not each replication’s bounds.
- **G6 order/smoke**, `tests/test_benchmark_v2.py:65`, `:98`: baseline lacks the required component/smoke interfaces. Both passed supplemental execution; smoke used real workloads with records stored in memory. Incomplete workload contents can still pass.
- **G7 composition/cost**, `:75`, `:89`: reject baseline; composition was inspected and the cost test rejected substituted baseline code. Both permit findings 2–3 because they do not verify manifest-wide workload accounting.
- **G8**, `tests/test_credibility.py:76`: passes the already-correct baseline implementation. It rejected an in-memory mutation that removed current-round picks from residual ordering.

Ledger rulings (`docs/revision/build-ledger-2026-10-22.md`):

- **Line 73: accept.** Reaccepting the freeze before doubling preserves the required stage order. Selected execution retains the full catalog.
- **Line 74: accept.** Pricing the implemented 64-profile matrix, including repeated references, reflects the current execution scope rather than the earlier reuse estimate.
- **Line 75: reject as implemented.** Sharing coalition prerequisites across total/min is valid. The blanket profit-cell allocation produces finding 3.

Own round-1 findings, from the Sol report:

- R1 #1: **closed** — default benchmark order; `scripts/benchmark_v2.py:171`.
- R1 #2: **partly closed** — workload accounting; findings 2–3.
- R1 #3: **closed** — cross validation; `scripts/revision_v2.py:789`.
- R1 #4: **closed** — doubling freeze and menu dependencies; `:707`, `:802`.
- R1 #5: **closed** — auxiliary provenance refusal and validation; `:252`, `:394`, `:756`.
- R1 #6: **closed** — nonfinite/short sample refusal; `sim/intervals.py:118`.
- R1 #7: **closed** — reported calibration/production mismatch; `sim/calibration_v2.py:110`. Finding 1 is a separate pooled defect.
- R1 #8: **closed** — discriminating residual fixture; `tests/test_credibility.py:76`.

F1: **closed**.  
F2: **closed**.  
F3: **closed**.  
F4: **closed**.  
F5: **closed**.  
F6: **closed**.  
F7: **closed**.  
F8: **partly closed** — finding 1.  
F9: **closed**.  
F10: **closed**.  
F11: **partly closed** — findings 2–3.  
F12: **closed**.

No additional regression was found in the Review Focus checks. Total/min jobs reused shared prerequisites; the stricter provenance rule blocked no required path identified in this review. Development-seed, exit-round, empty-budget, and freeze checks passed. **154 pytest tests passed**, plus supplemental in-memory probes. **All twelve frozen files are byte-identical to `2a288f5`.**

DECLINED TO JUDGE: Paid performance, empirical coverage, live explorers, sealed contents, and historical RED claims. The sandbox blocked 42 temporary-file tests: 28 runner, six benchmark, six tuning, and two calibration tests. Supplemental probes do not establish filesystem or process-concurrency behaviour. One slow test was skipped. Pytest used `-p no:cacheprovider`; plotting imports were disabled. No paid APIs, `sealed/` reads, or file changes.

CONFIDENCE: 0.94