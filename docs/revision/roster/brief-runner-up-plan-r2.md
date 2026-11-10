# Follow-up plan `docs/revision/followup2/runner-up-plan.md` (draft 2): internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

A fresh review (`docs/revision/roster/fable52-paper-r1.md`; triage `docs/paper/fable52-triage.md`) led the author to ask for this run. The plan, driver and tests are in `docs/revision/followup2/` (shared code `common.py`, `guards.py`; 56 tests). Round 1 (both reject): `docs/revision/roster/{sol,astra}-runner-up-plan-r1.md`; check each correction. They reuse `scripts/revision_v2.py` stages and `docs/revision/followup/reset_followup_v2.py` helpers; the reset plan (`docs/revision/reset-experiment-plan.md`, draft 5) is the template. Registered records: `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all`, report `.../report/report.json`, development logs `experiments/v2/log/`.

Check: (1) the estimand and whether the design answers the review's point; (2) correctness of the driver against the frozen stages (labels, references, banks, dependency sets, records kept apart from the registered ones, guards); (3) analysis, expectations written before outcomes, nominal versus calibrated intervals, deferrals; (4) cost from the benchmark and the cap; (5) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.
