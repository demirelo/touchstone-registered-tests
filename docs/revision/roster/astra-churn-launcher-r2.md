VERDICT: accept-with-caveat

CORRECTIONS:

1. `docs/revision/churn/churn-plan.md:250` — Change the remaining reservation instruction from 5.54 USD to 10.40 USD. At `:222`, update the shared follow-up cap from 22 USD to 72 USD. Keep the arm’s stop cap at 8 USD.

2. `docs/revision/churn/churn_pod.sh:89` — Verify `followup-churn/run.json` separately or include it in a parent inventory. The driver writes this file at `docs/revision/churn/churn_v2.py:528`, outside the three verified directories. A missing or corrupt local copy can therefore pass verification. Extend `docs/revision/churn/test_churn_pod_harness.sh:119` to test this case.

CONFIDENCE: 0.95