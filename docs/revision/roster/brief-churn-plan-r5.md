# Honest-churn arm, plan draft 5: internal review round 5 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

`docs/revision/churn/` holds the plan (`churn-plan.md`, draft 5), the driver (`churn_v2.py`), the preflight child (`churn_memory.py`), the new cost script (`churn_cost.py`), and tests (`test_churn_v2.py`, 28 pass: `uv run pytest -q docs/revision/churn`). Commit 9a0ce9d. Rounds 1-4: `docs/revision/roster/{sol,astra}-churn-plan-r{1,2,3,4}.md`. Round 4 agreed that sections 2-6 are sound and raised three corrections; check each:

1. Preflight measuring a skipped record: `churn_memory.py --task` now prints the `_run_one` status; `memory_preflight` (`churn_v2.py`, `_preflight_groups`, `_saved_preflight`) never counts a "skipped" task, measures the next unfinished task of the same rule (evaluate) or stage (doubling), reuses a saved measurement only when it applies (same memory limit and margin, peaks only from real runs, measured jobs in the current list), and otherwise refuses. Tests: `test_r4_a_skipped_record_is_never_a_memory_measurement`, `test_r4_a_rule_with_only_skipped_records_and_no_saved_peak_is_refused`, `test_r4_a_partial_stage_retry_reuses_the_validated_saved_peak`; the smoke test now asserts the refusal on an existing record and then a real child run on an unfinished task.
2. Worker limit across commands: `saved_workers` / `save_workers` keep the lowest limit in `memory_workers.json`, keyed by the memory limit; `_run_rate` starts every command from it; diagnostics refuse without it. Tests: `test_r4_the_worker_limit_persists_across_separate_stage_commands`, `test_r4_diagnostics_without_memory_evidence_is_refused`.
3. Billed time: plan section 7 and section 9 now use `uv run python docs/revision/churn/churn_cost.py` (6.88 h, 3.85 USD with the serial preflight tasks; 5.95 h without; 12.44 h, 6.97 USD at two evaluation workers); reservation 5.54 USD, stop cap 8 USD.

The launcher (`churn_pod.sh`) is out of scope: it will be regenerated from the separately reviewed `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh` with `podctl.py`. Report anything else that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.
