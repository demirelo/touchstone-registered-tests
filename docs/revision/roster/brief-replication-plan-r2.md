# Churn replication plan: internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

Plan: `docs/revision/followup3/replication-plan.md` (draft 2; its "Changes from draft 1" answers round 1, `docs/revision/roster/{sol,astra}-replication-plan-r1.md`; `git diff HEAD~1 -- docs/revision/followup3/`). Cost: `docs/revision/followup3/cost_estimate.py`. Background: the churn arm (`docs/revision/churn/churn-plan.md`, `churn-plan-amendment-1.md`, `churn_v2.py`), Run A (`docs/revision/followup2/runner-up-plan.md`, `runnerup_v2.py`), Run B (`convergence-plan.md`, `convergence_v2.py`), the registered pipeline (`scripts/revision_v2.py`, `scripts/manifest_v2.py`, `scripts/draw_v2.py`, `scripts/block_draw.py`, `sim/instances.py`), the external reviews (`docs/revision/roster/astra-pro-paper-d10-ext.md`, `-ext2.md`), the lessons (`docs/revision/lessons.md`). Code freeze: only `docs/`, `experiments/v2/`, `paper/`, `sealed2/h4/` may change. No spend before consensus and the author's spend card.

Check (first: is each round-1 correction answered correctly?):
1. Can every stage run with existing frozen functions plus new code under `docs/` (labels fresh0..5 in separate output directories; bypassing `R.main` and the manifest-wide freeze; calibration once on the pod with `cfg=`)? Name any stage that would need a frozen edit.
2. Is the prospective claim sound: plan, expectations and analysis code fixed and stamped before the draw block H = A + 144 exists? Gaps in the anchoring or draw procedure for a plan file instead of protocol-v2.yaml?
3. Estimands: is the primary paired change from each market's own p = 0 value well defined, including the p = 0 cell being the menu record and the frozen references replayed under churn? Is "continued-search winners primary, frozen as sensitivity" the right choice, and is it fixed tightly enough?
4. Support criterion and expectations: numeric, scorable as written, not trivially met; is expectation 4 (runner-up) genuinely risky?
5. Cost: is the estimate's structure right (menus of 10 rules x 2 families, churn slowdown, continued-search share), and is anything missing (gates, X7-SC menu doubling, diagnostics, pod-time vs core-hour pricing)?
6. Anything that would make the result uninterpretable or would repeat a lesson in `lessons.md`.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section or file, or "none".
CONFIDENCE: 0 to 1.
