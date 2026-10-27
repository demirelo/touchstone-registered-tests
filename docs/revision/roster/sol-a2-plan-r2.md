VERDICT: reject

FINDINGS:

1. **Important — Task 12: coverage collection still has a commit mismatch.** Evidence: `2026-10-27-revision-part-a2.md:209` applies `same_code` to promotion checks; `scripts/coverage_v2.py:87` defaults collection to current HEAD, and `:95` requires exact pool-commit equality. If an operations-ledger commit follows pool generation, local `--select` refuses valid pools before promotion. The synthetic promotion inputs at plan `:213` bypass this path. **Repair:** carry the reviewed `code_commit` through pool generation, selection, validation, and promotion. Apply code-equivalence checks where needed. Test those producer commands across a documentation-only commit and a changed-code commit.

2. **Important — Tasks 10/12: the replacement decision omits budget checks.** Evidence: plan `:179` specifies an evaluation-cap check but no development-cap check; `:211` defers approval enforcement to the lock. Existing `scripts/benchmark_v2.py:35` reserves USD 1 for the later H4 decision pod, and `:184` includes it in evaluation cost. If actual development spend plus remaining coverage exceeds USD 12, the new decision can permit continuation until reservation fails. Omitting the reserve can also select insufficient cuts. A revised total above USD 40 has no explicit approval gate before coverage. **Repair:** preserve the development cap and H4 reserve, stop when either phase cannot fit, and require renewed approval before further paid work. Add boundary tests for all three cases.

3. **Important — Task 8: the new welfare freeze record has no defined “no feasible candidate” state.** Evidence: plan `:141` makes `welfare_select` mandatory before freeze; `:143` defines a selector returning a family with lower training efficiency. However, `sim/objectives_v2.py:44–52` permits W1 to return no candidate. If one family has no feasible candidate, it must be excluded from selection; if both lack candidates, there is no winning family. The plan does not define either case. This can stop the final freeze instead of producing the required report. **Repair:** define both cases, store an explicit no-feasible-candidate selection record when necessary, and test freeze → evaluation → report for each case.

4. **Important — Task 9: per-test withholding needs fixed multiplicity slots.** Evidence: plan `:160` adds withholding per test, but `:164` does not test the remaining test’s rejection threshold. Existing `sim/decisions_v2.py:31–33` uses the supplied tests for Holm and their count for intervals. Dropping a refused Q1 test would let the remaining calibrated p-value of 0.04 reject with one slot; it must not reject with two slots. **Repair:** retain two Q1 slots and six Q4 slots, use p = 1 for unavailable tests, and retain the registered interval denominator. Test the boundary through the report.

5. **Minor — Tasks 7/10/12: timing contracts conflict.** Evidence: plan `:126` and `:128` specify and test `seconds`/`episodes`; `:183` still changes `h4_timing["seconds"]`; `:210` replaces these with `h4_seconds`/`x7_seconds` and separate episode counts. The sequence test at `:213` supplies synthetic timing. It cannot detect incompatible producer and consumer fields. **Repair:** specify one final export schema and pass actual smoke-check output through promotion and both billing paths. Keep the bundle hash in the printed outer record, calculated after writing `check.json`, because `sim/h4_loader.py:14–21` includes that file in the bundle hash.

Sol round-1 finding 1: resolved  
Sol round-1 finding 2: resolved  
Sol round-1 finding 3: resolved  
Sol round-1 finding 4: resolved  
Sol round-1 finding 5: resolved  
Sol round-1 finding 6: partly resolved  
Sol round-1 finding 7: resolved  
Sol round-1 finding 8: resolved  
Sol round-1 finding 9: partly resolved  
Sol round-1 finding 10: resolved  
Sol round-1 finding 11: partly resolved  

Astra round-1 finding 1: resolved  
Astra round-1 finding 2: resolved  
Astra round-1 finding 3: resolved  
Astra round-1 finding 4: partly resolved  
Astra round-1 finding 5: resolved  
Astra round-1 finding 6: resolved  
Astra round-1 finding 7: partly resolved  
Astra round-1 finding 8: resolved  
Astra round-1 finding 9: resolved  
Astra round-1 finding 10: partly resolved  
Astra round-1 finding 11: partly resolved  

CONFIDENCE: 0.91.