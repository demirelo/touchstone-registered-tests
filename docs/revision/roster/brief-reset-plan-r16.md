# Reset pod launcher: internal review round 16 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Round 15 (`docs/revision/roster/{sol,astra}-reset-plan-r15.md`) rejected the launcher with a full list. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

Design change: the self-made spend bound is removed (no `NAME.acct`, `.unpriced`, `.lock`, `record_price`, ABSENT). The spend record is the account balance difference: `NAME.bal0` (balance before the first request; no balance, no launch) minus the balance read by `podctl.py spend NAME`, refused until the watchdog ended at least 3600 s ago (`NAME.wdend`) and a successful listing shows no pod named NAME; rounded up to a cent. Other account usage is included, so it can overstate, never understate. Assumption: the balance shows a charge within an hour. The launcher prints only labelled estimates (rounded up).

Round-15 items:
- Outstanding request (Sol 2, Astra 2): `NAME.request` is "pending" before every request, "clear" only after a clear answer; the watchdog settles 1800 s while pending.
- ABSENT, unsynchronized `.acct`, exit-status handling, rounding (Sol 3-5, 9; Astra 3, 4, 13): removed with the bound.
- Launch lock (Sol 6, Astra 6): `mkdir NAME.launchlock` before any marker changes; the watchdog releases it on exit; the launcher releases it only if no request was sent.
- Above-ceiling or unknown price (Astra 5): deleted at once; retrieval runs only after the remote run started.
- Watchdog liveness (Astra 7): checked after start and before every request.
- Upload and remote-start failures (Astra 8): stop the run. Whitespace in paths (Astra 9): refused.
- Monotonic clock for elapsed budgets (Sol 9). Tests no longer write to the production directory (Astra 12).
- Harness (Sol 7-8, Astra 10-11): fakes lock `state.json` per call; each scenario checks the exit status, an anchored end state, that the watchdog ended by itself (except the fail-closed case) and released the lock. New: stop during creation (TERM while the request is outstanding; late pod deleted; 1800 s settle), held lock, unknown balance, upload failure.

Tests: `test_podctl.py` + `test_runpod.py` 45 pass (new r16 tests seen RED). Harness: 12 scenarios; a smoke run of 3 passed; the full run is going (about 3 h). The launch is gated on HARNESS OK and this review.

Check: (1) each round-15 item is closed; (2) new defects in one pass; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
