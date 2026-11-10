VERDICT: reject

CORRECTIONS:
1. **§5; convergence_v2.py:309; guards.py:48.** Complete the result bindings. They still omit helper, plan, report, posthoc, and registered doubling-record hashes. Inventory hashes do not prevent stale-result reuse. This leaves a round-2 correction unresolved and now affects the embedded D2+H3 winner. Include these dependencies in bindings for both results and gate evidence before pod execution.

2. **§5; guards.py:119,126; convergence_v2.py:312.** Validate the full gate provenance and numerical environment. The checker verifies cell, site, smoke flag, input hash, and driver hash, but ignores the recorded budget and settings. Environment comparison omits SciPy, CMA, and BLAS/LAPACK. An in-memory check accepted evidence with an altered budget and altered numerical libraries. Require the expected full-budget provenance and numerical stack before pod execution.

3. **§§3,6; convergence_v2.py:220,345.** Enforce the stated fallback for cost-stopped cells. A cell stopped after an intermediate round receives held-out gains and enters `done`, so analysis substitutes its partial result. The plan says a refused cell keeps its frozen estimate. Exclude cost-stopped cells from primary substitutions; retain their partial results separately. An in-memory check confirmed the current substitution.

4. **§2; convergence_v2.py:88,217,285.** Apply the nesting minimum to reported pass rounds and permitted round limits. `passed_round()` can return 1 even when the nesting cell subsequently reaches the cap without an eligible pass. Five added cells already pass the registered round-one check. Compute the first pass at or after `min_rounds`, and reject full continuation runs with nesting cells and `--max-rounds 1`.

5. **none — §§1–4,6.** The bounded sensitivity claim, expectations timing, nominal conditional intervals, and explicit deferrals are appropriate. They address part of the review’s search concern. All 19 jobs pass pairing, budget, configuration, and code checks; all 111 input hashes match. The revised cost calculation reproduces USD 3.30, or USD 4.12 with the allowance, below the USD 4.25 admission cap. Thirty-five read-only tests pass; 30 write-dependent tests and full-budget reproduction were not run.

CONFIDENCE: 0.97.