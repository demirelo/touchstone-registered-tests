VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup2/convergence_v2.py:278`: Save each bound record atomically inside the worker before result transfer. A read-only probe confirmed that another worker’s death can discard a completed function’s result during transfer. The current test delays the kill until both other results arrive; it does not test this failure.

2. `docs/revision/followup2/convergence_v2.py:272`: Handle `BrokenProcessPool` during submission as well as result collection. A probe confirmed that submission can raise it outside the handler, bypassing `lost_cells.json`, inventory creation, and exit 5. Add an early-death test.

3. `docs/revision/followup2/convergence_v2.py:419`: Check saved round-1 mismatches before returning exit 5. A mismatch plus worker loss currently triggers a paid restart; refused restart admission can then hide the gate failure behind a cost-stop state. Give the mismatch priority and test both conditions together.

4. `docs/revision/followup2/followup2_pod.sh:48`: Enforce a memory-based worker limit. The launcher accepts 16 workers on the same 28 GB minimum that cannot support the measured load. Seven workers provide estimated headroom, but one sampled Mac gate does not establish the peak for three rounds or repeated cells. Validate that workload and include parent-process memory.

5. `docs/revision/followup2/followup2_pod.sh:293`: Calculate restart admission from the remaining cells and retry worker count. An early loss can leave all 19 cells; the documented 29.48 core-hours require at least 9.83 hours with three workers, not 2.60. The watchdog bounds the attempt, but the stated 6.4-hour worst case excludes recovery.

6. `docs/revision/budget-ledger.json:20`: Reconcile the failed run before launch. The default ledger still contains the `convergence-1` reservation, with no 3.43 USD spend row or `convergence2-1` reservation. Require the old spend record and test that it remains in the follow-up total when the new tag receives its separate allowance.

7. `docs/revision/followup2/followup2_pod.sh:182`: Verify each available output directory even when another pull fails or times out. The shared `pulled` flag currently skips all verification after any pull failure. Add partial-pull and deadline tests.

CONFIDENCE: 0.96.