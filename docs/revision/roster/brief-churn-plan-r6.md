# Honest-churn arm, plan draft 6: internal review round 6 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

`docs/revision/churn/` holds the plan (`churn-plan.md`, draft 6), the driver (`churn_v2.py`), the preflight child (`churn_memory.py`), the cost script (`churn_cost.py`), and tests (`test_churn_v2.py`, 32 pass: `uv run pytest -q docs/revision/churn`). Commit: see `git log -1 -- docs/revision/churn`. Rounds 1-5: `docs/revision/roster/{sol,astra}-churn-plan-r{1,2,3,4,5}.md`. Round 5 accepted the skipped-record fix, the worker limit across commands, and the billed-time arithmetic, and raised two blockers; check each:

1. Saved-measurement reuse (`_saved_preflight`, `PREFLIGHT_VERSION = 2`): reuse needs version 2 with an explicit "done" status per measured task (draft-4 records are never reused), and, for the evaluation, a measurement for every current rule. Tests: `test_r5_a_saved_measurement_must_cover_every_current_rule`, `test_r5_an_older_saved_record_without_run_evidence_is_rejected`.
2. Measured jobs and dispatch (`_run_rate`, evaluate/doubling branch): every job now passes through `run_stage` and so `_run_one`, which skips a valid record and recomputes a missing or damaged one; only the admission counts tasks measured in the same command as done. Test: `test_r5_measured_jobs_are_still_dispatched_so_missing_records_are_recomputed` (reused and fresh), plus updated r3/r4 dispatch assertions.

The launcher (`churn_pod.sh`) is out of scope: it will be regenerated from the separately reviewed `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh` with `podctl.py`. Report anything else that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.
