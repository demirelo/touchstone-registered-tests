# Reset pod launcher: internal review round 14 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 13 (`docs/revision/roster/{sol,astra}-reset-plan-r13.md`) rejected the launcher; both seats closed the price parser and the timeout floor. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

Rule: every deletion records the pod's price first (`podctl.record_price`: raises `NAME.acct`, or writes `NAME.unpriced`). Audit of every deletion path (`grep -n delete reset_pod.sh podctl.py`):
1. `podctl.reconcile` (before each request and in cleanup): now calls `record_price` for each pod before `delete_verified` (r13 Sol 2 / Astra 3).
2. `podctl.watchdog`: calls `record_price` before deleting (r13).
3. `reset_pod.sh` cleanup delete of `$id`: if the launcher stopped before the price check (`cph` still 0), it calls `record-price` first; on failure it writes `NAME.unpriced`.
4. `reset_pod.sh` unreachable-pod delete: always after the `record-price` call.

Unknown price (r13 Astra 4): when `NAME.unpriced` exists, the launcher prints "UNRESOLVED BILLING: a pod had an unknown price, so no spend bound is proven; take the spend from the Runpod console", exits non-zero, and prints no "spend bound so far" and no instruction to record a bound. The watchdog prints no "final spend bound" in that case.

Tests: `test_podctl.py` + `test_runpod.py` 39 pass, including the new parametrized `test_r14_reconcile_records_a_pod_price_before_deleting_it` (9.0 and null; seen RED). Harness: 9 scenarios; the null-price scenario now also fails if launcher output or the watchdog log contains "spend bound so far" or "final spend bound". The harness is running now (about 2.5 h); the pod launch is gated on HARNESS OK as well as on this review.

Check: (1) each round-13 correction is closed; (2) any other path that deletes a pod, or prints a bound, without the price rule; (3) new defects; (4) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
