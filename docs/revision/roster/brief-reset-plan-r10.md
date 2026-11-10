# Reset pod launcher: internal review round 10 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 9 (`docs/revision/roster/{sol,astra}-reset-plan-r9.md`) rejected the launcher's pod-safety logic. It now lives in `/Users/oemer.demirel/Projects/touchstone/results/pods/podctl.py` (fail-closed listing; deletion verified within elapsed time; reconciliation true only when a successful listing shows no extra pod; a creation block from the hard deadline; a watchdog started with nohup before the first creation that, from the hard deadline, blocks creation and keeps deleting every pod named ts-r-TAG until a listing shows none, and otherwise exits only when the launcher's done file exists and no such pod is listed). Tests: `test_podctl.py` (6) with mutation checks (five deliberate defects, each caught with pytest exit 1), `test_runpod.py`. The launcher `reset_pod.sh` uses podctl for reconciliation before every attempt (fails closed), may-create before every attempt, deletion, and the watchdog; pulls are limited to the remaining recovery window and checked before each one; spend is recorded per attempt with the bound at MAXCPH. Harness `test_reset_pod_harness.sh` passes 5 scenarios with assertions on pods left and creation requests: price above the ceiling, lost creation responses, unreachable pod at the deadline, listing always failing (no creation), lost response then the hard deadline (no second creation). Known cosmetic issue: in the always-failing-listing scenario the final state label reads NOT STARTED.

Check: (1) each round-9 correction is closed; (2) new defects; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
