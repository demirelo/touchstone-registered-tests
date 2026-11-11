VERDICT: reject

CORRECTIONS:
1. podctl.py:170 — The one-hour billing wait still uses wall time. Offline reproduction: the watchdog ends at wall time 1000; after 30 elapsed seconds and a forward clock step to 5000, `spend()` accepts the balance and writes `.spent`. Delayed charges can therefore be omitted. Verify the wait with elapsed time across CLI calls, and refuse recording when that verification is unavailable. Add a regression test.
2. test_reset_pod_harness.sh:106 — The unreachable-pod scenario excludes the actual terminal state. With `HARDX=1.0`, the soft and hard deadlines coincide. After the unreachable pod is deleted, reset_pod.sh:123 returns `CREATION BLOCKED (hard deadline)` before the soft-deadline check. An offline execution of these shell statements reproduced this result. Correct the expected state and check the related expectation at test_reset_pod_harness.sh:107. Keep the pod blocked until the corrected full run reports `HARNESS OK (13 of 13 scenarios)`.

CONFIDENCE: 0.97