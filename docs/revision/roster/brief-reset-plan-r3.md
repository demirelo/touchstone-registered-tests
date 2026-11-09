# Reset experiment plan: internal review round 3 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 350 words)

Round 2 (`docs/revision/roster/{sol,astra}-reset-plan-r2.md`: Sol accept-with-caveat, Astra reject) asked for the stages' input records, two freezes, billed pod time, base-versus-doubled scoring, and option B. Draft 3 responds (option B dropped). Review `docs/revision/reset-experiment-plan.md` (draft 3). It answers the round-9 external review's problem 2 (`docs/paper/external-review-r9.md`): how much attacker gain comes from free identity replacement. It proposes 18 new D2 search cells (B3, R3, C* x six fresh markets) against the frozen references, with doubling checks, cap 3 USD.

Check: (1) the section-1 numbers against `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all/evaluate/headline@rho0.2__*__{D2+H3,D2}__profit.json` (fields `gain`, `seeds`, `upstream`); (2) that D2 with the frozen references is a valid "replacement disabled" counterfactual (read `sim/policies/identity.py`, `sim/families_v2.py`, and the design's D2 cells), and whether anything else differs between D2 and D2+H3; (3) whether the estimand, analysis, and pre-specified expectations are sound and honest about the headline result having been seen; (4) the cost arithmetic against the design's section 8.2 and the operations ledger; (5) whether the frozen code can run D2 on fresh markets with only a new manifest (look at the runner and manifest code under `sim/` and `experiments/`); (6) each round-1 and round-2 correction is resolved; (7) anything missing that a reviewer would ask for (for example, reset frequency of the selected policies).

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with plan section, file, or line, or "none".
CONFIDENCE: 0 to 1.
