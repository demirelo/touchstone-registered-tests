# Reset pod launcher: internal review round 18 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 17 (`docs/revision/roster/{sol,astra}-reset-plan-r17.md`) rejected the launcher on three items. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

1. Billing wait and wall time (Sol 1): the watchdog writes `NAME.wdend` as "wall monotonic". `podctl.spend` needs at least 3600 s by both clocks. If monotonic time is below the recorded value (a restart), the wait cannot be verified and spend is refused (the author takes the spend from the billing page). On macOS the monotonic clock does not advance during sleep, which only lengthens the wait. Tests: a +4000 s wall jump with 30 s elapsed is refused; a restart is refused.
2. Spend overlapping a launch (Astra 1): `spend` takes `NAME.launchlock` (mkdir) for its whole run and refuses while a launch or watchdog holds it; the launcher takes the same lock before reading or archiving records. Test: refused while held; held during the run; released after.
3. Partial record (Astra 2): `NAME.spent` is written to a temporary file, flushed, fsynced, then published with `os.replace`; on failure no record exists. The launcher accepts only a complete record (`^[0-9]+(\.[0-9]+)? USD `). Test: a failing replace publishes nothing. New harness scenario: an empty `.spent` does not count as recorded.
4. Harness end states (Sol 2): the two `HARDX=1.0` scenarios accept `CREATION BLOCKED (hard deadline)`.

Tests: 53 pass (r18 tests seen RED). Harness: 14 scenarios; a smoke of the 4 refusal scenarios gave PARTIAL as designed; the full run is going (about 3 h). The launch is gated on "HARNESS OK (14 of 14 scenarios)" and this review.

Check: (1) each round-17 item is closed; (2) new defects in one pass; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
