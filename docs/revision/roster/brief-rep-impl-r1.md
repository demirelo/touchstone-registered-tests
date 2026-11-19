# Churn replication: implementation and launcher review, round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Start here: `docs/revision/followup3/rep-launcher-notes.md` (scope, smoke evidence, memory, the two pods, rulings 1 to 9, pre-launch steps). Plan of record: `docs/revision/followup3/replication-plan.md` (draft 3, consensus r3 with caveats; `docs/revision/roster/{sol,astra}-replication-plan-r3.md`). Code under review: `docs/revision/followup3/` (`replication_analysis.py`, `commitment.py`, `continuation.py`, `rep_v2.py`, `rep_collect.py`, `rep_pod.sh`, `test_rep_pod_harness.sh`, `cost_estimate.py`, and their tests). Reference implementations already reviewed: Run B (`docs/revision/followup2/convergence_v2.py`, `followup2_pod.sh`), the churn arm (`docs/revision/churn/churn_v2.py`), `results/pods/guards.py`, `results/pods/podctl.py`, `results/pods/budget_v2.py`. Lessons: `docs/revision/lessons.md`. Code freeze: only `docs/`, `experiments/v2/`, `paper/`, `sealed2/h4/` may change. Checks: `uv run --frozen pytest -q docs/revision/followup3/`; `bash docs/revision/followup3/test_rep_pod_harness.sh`.

Check:
1. Does the code implement the plan exactly (markets, rules, rates, families, estimands, the support criterion, the five expectations, the queue order, both gates)? Name every divergence with file and line.
2. Prospective claim: does the manifest cover everything that decides the result, and do the launcher and driver refuse to run on code that differs from it?
3. Launcher: cost cap across two pods (one tag, PRIOR = pod 1's spend, closed attempts at the ceiling), end codes 3/4/5/6 and the driver's cap stop, the restart on 3 workers, memory admission, the pod 2 bundle check. Any path that spends without a recorded cap, loses output, or reports success wrongly?
4. Rulings 1 to 9 in the notes: accept or correct each.
5. Anything that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
