# Reset pod launcher: internal review round 15 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Round 14 (`docs/revision/roster/{sol,astra}-reset-plan-r14.md`) rejected the launcher on accounting details. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

Fixes:
1. Stale price on a retry (Sol 2, Astra 2): each attempt resets `cph=0; id=""` before its creation request, and cleanup now calls `record-price` for the current `$id` unconditionally before deleting it. No interruption point can skip it.
2. Cached rate (Sol 3, Astra 3): cleanup reads the rate from `NAME.acct` after reconciliation and before printing any bound.
3. Concurrent records (Sol 4): `record_price` holds an exclusive `fcntl.flock` on `NAME.lock` for the whole read-compare-write of `NAME.acct`.
4. New, found while fixing 1: a pod absent from a successful listing returns `podctl.ABSENT` (CLI exit 2) and writes no `NAME.unpriced`, because whoever deleted it (watchdog or reconcile) priced it first. Cleanup marks unpriced only on exit 1 (unknown price or failed listing). At creation, any non-zero exit (including absent) still marks the price unknown.

Writers of `NAME.acct`: the launcher once, before the first request (no pod exists then); `record_price` under the lock otherwise.

Tests: `test_podctl.py` + `test_runpod.py` 41 pass, including `test_r15_record_price_waits_for_the_accounting_lock_and_keeps_the_maximum` and `test_r15_a_pod_absent_from_a_good_listing_is_not_unpriced` (both seen RED). Harness: 10 scenarios; new: a 9.0 USD/h pod that appears during cleanup after an ambiguous answer must show "at 9.0 USD/h" in the launcher output and the watchdog log. The harness is running (about 3 h); the launch is gated on HARNESS OK and on this review. An interruption at a chosen line is not in the harness; fix 1 removes the condition instead.

Please report every remaining defect you can find in one pass, including minor ones, so the next round can close all of them.

Check: (1) each round-14 correction is closed; (2) new defects; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
