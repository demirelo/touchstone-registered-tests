# Reset pod launcher: internal review round 12 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 11 (`docs/revision/roster/{sol,astra}-reset-plan-r11.md`) rejected the launcher. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

Design change for the unprovable case: an AMBIGUOUS creation answer now ends creation for the whole launch. No further request is sent, so two pods can never overlap. The launcher writes `NAME.ambiguous`, reconciles, writes DONE, and exits non-zero. The watchdog then deletes any pod named NAME that appears, and settles for AMBIGUOUS_SETTLE = 1800 s (normal: 300 s). We state a service assumption: a Runpod pod from a request either appears within 30 minutes or never. Residual: the next launch with the same name reconciles first. Plan step 4 (`docs/revision/reset-experiment-plan.md`) adds a manual Runpod console check the next day after any launch that ends AMBIGUOUS or UNRESOLVED BILLING, before any relaunch.

Other fixes:
- `podctl.classify_creation`: only HTTP 4xx other than 408/429 is a definite refusal; exceptions, timeouts, 5xx, gateway errors and unreadable answers are ambiguous. `create_one.py` uses it.
- Watchdog settle counts only from DONE onwards; it prints a final spend bound on exit from `NAME.acct` (first request time, rate).
- Rate = max(MAXCPH, observed price) when a pod comes back above the ceiling. Billing is UNRESOLVED (exit non-zero, final bound taken from watchdog.log) after an unverified deletion, a failed reconciliation, an ambiguous answer, or an unknown price.
- Fractional timeouts are passed through (no rounding up). The spurious `600` KEEP_ID argument is removed.
- The harness waits on the exact watchdog PID (`NAME.wdpid`), not on a name pattern.

Tests: `test_podctl.py` + `test_runpod.py` 23 pass, including the four r12 tests (seen RED). Harness, 7 scenarios with exact creation counts, zero pods or pending creations left, and watchdog-log checks: price above ceiling (1); ambiguous ends creation (1, "for 1800s"); unreachable at deadline (1); listing always fails (0); pod created ~10 min after an ambiguous answer is deleted (1, "WATCHDOG: deleting"); stuck deletion after deadline (1); RUN OK with a corrupt pull (1). Result: HARNESS OK (results/pods/test_reset_pod_harness.sh, run 2026-11-11, ended 04:24 UTC): all 7 scenarios ended with 0 pods left and the expected creation-request count (1,1,1,0,1,1,1). Scenario 2 and 5 watchdogs settled 1800 s after DONE; scenario 5's late pod (it appears after a countdown of 20 fake API calls, more than 300 s after the ambiguous answer) was deleted by the watchdog; scenario 4's watchdog stayed alive (fail-closed) and was stopped by PID for test isolation. Unit tests: 23 pass (test_podctl.py, test_runpod.py).

Check: (1) each round-11 correction is closed; (2) new defects; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
