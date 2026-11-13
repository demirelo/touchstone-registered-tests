VERDICT: reject

CORRECTIONS:
1. `docs/revision/followup2/followup2_pod.sh:53` — Take the run lock before taking and validating the ledger snapshot. The lock currently starts at line 144. Two processes with the same launch tag can validate the same reservation before either takes the lock. If one process is delayed until the first launch finishes and its spend is recorded, it can then acquire the released lock and launch with stale PRIOR and a consumed reservation. The later spend-file checks permit this because they archive completed records. Add a regression test that delays the second process between snapshot validation and lock acquisition.

2. `docs/revision/followup2/convergence_v2.py:387` — Preserve a measured gate failure when a later cell refuses admission. The loop currently saves a failed first-cell comparison, continues, and returns 3 if the second cell’s outer or inner admission refuses. I reproduced both cases with the extracted gate-loop code in memory. The launcher consequently reports a cost stop despite the measured mismatch. After saving a measured failure, write the inventory and return 4 before starting another cell. Add tests for both admission paths; retain exit 3 when no measured mismatch exists.

CONFIDENCE: 0.96.