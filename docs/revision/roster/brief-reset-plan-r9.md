# Reset pod launcher: internal review round 9 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 8 (`docs/revision/roster/{sol,astra}-reset-plan-r8.md`) rejected the launcher `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh`. Changes: the watchdog starts before the first creation request and, at the hard deadline, deletes every pod in the IDS file and any pod named ts-r-TAG; all deadlines run from the first creation request at the price ceiling MAXCPH (a bound across attempts; the actual price is recorded); creation without an id triggers reconciliation (untracked pods named ts-r-TAG are deleted and verified); after RUN OK the pod is kept and pulls plus inventory verification retry every minute until success or two minutes before the hard deadline; deletion is retried every minute for 30 minutes and the watchdog stops only after verified deletion; the remote script checks STOP and the soft deadline before the gate as well. Evidence: `results/pods/test_reset_pod_harness.sh` (offline fake runpod/create16; scenarios: price above the ceiling, lost creation response, unreachable pod with the watchdog firing during readiness; passes with no pod left), `test_runpod.py`, dry run at fdfd83e, negative tarball tests.

Check: (1) each round-8 correction is closed; (2) new defects (watchdog and cleanup interaction, deadline arithmetic, reconciliation, the RUN OK retrieval loop); (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
