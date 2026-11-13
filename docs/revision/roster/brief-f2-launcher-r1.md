# Follow-up Runs A and B: shared launcher, internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

Runs A (runner-up comparator on the fresh markets, `docs/revision/followup2/runner-up-plan.md`, draft 7) and B (continued
searches, `convergence-plan.md`, draft 7) reached plan consensus earlier (commit 140b906). Their pod launcher is new: one
script for both runs, generated from the reviewed churn launcher (`docs/revision/churn/churn_pod.sh`, churn launcher
reviews r1 and r2, itself from the reviewed reset launcher).

Files:
- `docs/revision/followup2/followup2_pod.sh` (installed copy `/Users/oemer.demirel/Projects/touchstone/results/pods/followup2_pod.sh`, identical). Diff against the base: `diff docs/revision/churn/churn_pod.sh docs/revision/followup2/followup2_pod.sh`.
- `docs/revision/followup2/launcher-notes.md`: what each run does on the pod, the bundle, and eight rulings for you to accept or reject (reservation size, Run B's stale Mac gate evidence, PRIOR from the ledger, attempts pushed once, step hours, cap limits, the end-state parse, bash 3.2).
- `docs/revision/followup2/test_followup2_pod_harness.sh` (29 scenarios) and its log `/Users/oemer.demirel/Projects/touchstone/results/pods/logs_harness/followup2_harness1.log` (HARNESS OK, 29 of 29).
- The bundle `/Users/oemer.demirel/Projects/touchstone/results/v2/followup2-bundle/` (outside git).
- The drivers: `docs/revision/followup2/{runnerup_v2.py,convergence_v2.py,guards.py,common.py}`, `docs/revision/followup/{reset_followup_v2.py,budget_followup.py}`; tests `uv run --frozen pytest -q docs/revision/followup2` (95 pass).

Check: (1) every edit keeps the reviewed launcher's safety behaviour (creation, price, watchdog, deletion, locks, spend records); (2) each run's remote script follows its plan's sections 5 to 7 exactly: admission before every paid step with the right flags, the reset gate bit-identical before the driver, every driver flag valid for that driver, outputs and inventories, end-state classification by the drivers' real exit codes and messages; (3) the bundle holds what the drivers read and nothing they would refuse; (4) the harness exercises the new paths, including the remote script with stub tools; (5) the rulings; (6) defects the harness misses.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
