# Follow-up plan `docs/revision/followup2/convergence-plan.md` (draft 7): internal review round 7 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

A fresh review (`docs/revision/roster/fable52-paper-r1.md`; triage `docs/paper/fable52-triage.md`) led the author to ask for this run. The plan, driver and tests are in `docs/revision/followup2/` (shared code `common.py`, `guards.py`; 94 tests). Rounds 1-6: `docs/revision/roster/{sol,astra}-convergence-plan-r{1,2,3,4,5,6}.md`; check each round-6 correction. The pod launcher will be a copy of `results/pods/reset_pod.sh` with `results/pods/podctl.py` (read both; the plan states its stop rule). Mac gate evidence (free, under the current code) is in `/Users/oemer.demirel/Projects/touchstone/results/v2/followup2-conv-gate` (Run B) and `.../followup2-a-gate-repro`, `.../followup2-a-gate-dbl` (Run A); check them if present. They reuse `scripts/revision_v2.py` stages and `docs/revision/followup/reset_followup_v2.py` helpers; the reset plan (`docs/revision/reset-experiment-plan.md`, draft 5) is the template. Registered records: `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all`, report `.../report/report.json`, development logs `experiments/v2/log/`.

Check: (1) the estimand and whether the design answers the review's point; (2) correctness of the driver against the frozen stages (labels, references, banks, dependency sets, records kept apart from the registered ones, guards); (3) analysis, expectations written before outcomes, nominal versus calibrated intervals, deferrals; (4) cost from the benchmark and the cap; (5) anything that should block the pod.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file:line, or "none".
CONFIDENCE: 0 to 1.


Scope note for this round: the pod launcher copy (a copy of `results/pods/reset_pod.sh`) is outside `docs/revision/followup2/`; this session may not edit `results/pods/`, so the launcher copy and its offline test are a separate, named prerequisite of pod allocation (plan, "Admission before every paid step"). Judge the plan and the driver side of the handoff (`guards.py admit`, `attempts_spend`, `ledger_spend`, STOP/deadline checks). Run B's Mac gate was rerun under this draft's code into `/Users/oemer.demirel/Projects/touchstone/results/v2/followup2-conv-gate/gate/` (earlier passing records under older code are kept in `gate-draft4/` to `gate-draft6/`).
