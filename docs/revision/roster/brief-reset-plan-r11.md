# Reset pod launcher: internal review round 11 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 300 words)

Round 10 (`docs/revision/roster/{sol,astra}-reset-plan-r10.md`) rejected the launcher. Files: `/Users/oemer.demirel/Projects/touchstone/results/pods/{reset_pod.sh,podctl.py,create_one.py,runpod.py,test_podctl.py,test_runpod.py,test_reset_pod_harness.sh}`.

Changes since round 10:
- `create_one.py` replaces `create16.py`: exactly one POST per call, no internal retries; it reports `ambiguous` for any unclear outcome. The launcher runs reconcile (fails closed), may-create and the soft-deadline check before EVERY request; an ambiguous answer is followed by a 30 s wait and a successful reconciliation before the next request.
- `podctl.py`: every list/delete command timeout is bounded by the remaining elapsed-time budget; success after the budget is not success; reconciliation stops starting deletions after its budget.
- The watchdog (one loop) ends only when the done file exists AND successful listings show no pod named ts-r-TAG for SETTLE = 300 consecutive seconds. After the done file (the launcher reconciles first) any such pod is an orphan and is deleted; from the hard deadline it also writes the block file and deletes every such pod with no retry limit. This closes the delayed-creation case found by our own harness (scenario 5 below failed before this fix).
- Accounting: reconciliation before every request keeps at most one pod alive, so the launcher prints a bound from the first request to the end of its final reconciliation at MAXCPH, covering lost-response intervals. If a deletion is unverified or the watchdog later deletes an orphan, the launcher says billing may continue, and the recorded spend uses the watchdog's exit time (logged in watchdog.log) instead.
- Tests: `test_podctl.py` 9 pass under a 30 s alarm, including `test_r10_delete_respects_the_budget_even_with_slow_commands`, `test_r10_watchdog_after_the_deadline_needs_done_and_a_settled_empty_listing`, `test_r11_watchdog_before_the_deadline_settles_so_a_delayed_creation_is_deleted` (seen RED). Harness: 7 scenarios with EXACT creation counts and zero pods or pending creations left: price above ceiling (1), ambiguous x3 (3), unreachable at the deadline (1), listing always fails (0), delayed creation behind ambiguous answers (3), stuck deletion handled by the watchdog after the deadline (1), RUN OK with a corrupt pull retried until verified (1). Result: HARNESS OK, all 7 (log: harness4.log). After that run I added a per-scenario isolation step: a watchdog still alive after the wait (expected only while listings fail) is stopped so it cannot touch the next scenario's fake state; in the run above the scenario-4 watchdog ended only when scenario 5 reset the shared state.

Check: (1) each round-10 correction is closed; (2) new defects; (3) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
