# Honest-churn arm, plan draft 1: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

A fresh review (`docs/revision/roster/fable52-paper-r1.md`, problem 4) says the model has no honest churn, so identity age marks the attacker. The author asked to run the necessary simulations. `docs/revision/churn/` holds the plan (`churn-plan.md`), the driver (`churn_v2.py`, reusing `scripts/revision_v2.py` stages and `docs/revision/followup/reset_followup_v2.py` helpers), and tests (`test_churn_v2.py`, 6 pass). Registered records: `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all`, report `.../report/report.json`. The reset plan (`docs/revision/reset-experiment-plan.md`, draft 5) is the template.

Check: (1) is the churn model (honest opponents retire and re-enter at rate p) a fair test of the identity-age concern, and are p in {0.01, 0.05} justified; (2) is reusing the frozen references under churn, rather than reselecting, acceptable, and what does it bias; (3) is the runtime injection into `train_cell` correct for search, evaluation and doubling, and are records kept apart from the registered ones; (4) estimands, analysis, expectations (note the disclosed partial outcome seen before they were written), cost and cap; (5) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.
