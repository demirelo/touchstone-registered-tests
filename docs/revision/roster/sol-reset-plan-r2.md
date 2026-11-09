VERDICT: accept-with-caveat

CORRECTIONS:
1. **§7; `scripts/benchmark_v2.py:150`; operations ledger:** The arithmetic checks: A ≈28.446 units/$1.779; B ≈63.483 additional units/$3.970. Ledger totals and headroom also match. However, $0.108/core-hour is the benchmark’s default conversion rate. The recorded pod charged $0.56/hour for 16 vCPUs. Add a billed-time estimate for the proposed schedule, including preparation, diagnostics, idle capacity, and the recorded 10-worker limit for evaluation and doubling. Round-1 cost correction 6 remains partly open.

2. **§3, lines 50–58; `scripts/revision_v2.py:345,400,887`:** Specify how the new output directory receives verified copies of the frozen references **and the search records needed by `menu()` during doubling**. Those stages read dependencies from `out`; reference hashes alone do not supply them. Record the original cuts=3 bank membership. Add a free integration check that resolves these dependencies. The separate driver addresses the manifest restriction, but this execution detail remains incomplete.

3. **§3, lines 54–55:** Separate the pre-evaluation freeze from the final output inventory. Freeze selected policies, references, configurations, seeds, and search records before evaluation. Record evaluation and doubling outputs afterward. The frozen runner requires a freeze before evaluation; a single freeze containing those future outputs would create a circular dependency.

4. **§7, option B:** Before offering B for execution approval, define its constrained family and incumbent handling. Enforce `h_R=T` and `lambda=1` for every candidate, including embedded incumbents and corner controls. Require zero-reset checks and specify its comparisons and analysis. The frozen X7-SC search otherwise inserts a D2+H3 incumbent that can permit replacement.

CONFIDENCE: 0.96