VERDICT: reject

CORRECTIONS:
1. **§3; `scripts/revision_v2.py:884–898`: Complete the execution contract.** The frozen doubling stage calls `menu()` and `select_reference()`. It needs original search and bank-source records, beyond the frozen reference files. Specify how the separate output directory accesses these inputs and checks their hashes. Distinguish diagnostic reference reselection from the unchanged reference used for held-out gains. Separate the pre-evaluation freeze from the final output inventory; otherwise, including evaluations that hash their own freeze creates a circular dependency. Add a free test of the complete search–freeze–evaluation–doubling path. Round-1 correction 3 remains partly unresolved.

2. **§7; `scripts/benchmark_v2.py:131–158`; operations ledger, Operation 7 preparation:** Replace the unit conversion with a billed pod-time estimate. The arithmetic checks: A is approximately 28.45 units/$1.779; B adds 63.48 units/$3.970. However, $0.108/core-hour is the design-rate input; the measured pod rate was $0.56/hour for 16 vCPUs. Price the execution schedule, the recorded 10-worker evaluation/doubling limit, setup time, and an explicit diagnostic workload. The ledger totals and proposed approval-limit arithmetic are correct. Round-1 correction 6 remains partly unresolved.

3. **§§5–6:** Specify how conclusions change when base and doubled searches disagree. Tie the “most of the gap” statement explicitly to a defined pooled share exceeding 0.5; report undefined shares and missing cells separately from failed expectations. This matters because external-review problem 1 already documents sensitivity to doubling.

4. **Round-1 closure, §§1–6:** Corrections 1, 2, 4, 5, and 7 are resolved. All four headline gain pairs, increments, SEs, seed matches, reference hashes, and flags check. D2 disables replacement within this family; search differences are disclosed. The conditional estimand, paired bootstrap, post-observation disclosure, and reset diagnostics are sound.

CONFIDENCE: 0.96.