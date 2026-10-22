# Design review, round 4 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,000 words)

Draft 4 of `docs/superpowers/specs/2026-10-22-revision-program-design.md` revises draft 3 after your round-3 review. All earlier reviews: `docs/revision/roster/{sol,astra}-design-r{1,2,3}.md`; the disposition table is section 13. Context files and code as before (`sim/`, `scripts/`, the simulator spec, the paper, the robustness and final-evaluation records, `sim/policies/identity.py`, `sim/market.py`, `sim/intervals.py`, `sim/amendment.py`, `experiments/amendment-2026-10-17.yaml`).

Check: (1) each of your round-3 corrections is resolved, or say exactly what remains; (2) new errors draft 4 introduces (reference completeness and dependency order, coalition membership, publication rule, the reduced confirmatory scope, Holm decisions, coverage fixtures and admission, cost arithmetic); (3) the two questions of section 12. Accept only if the design, once executed, answers Q1 to Q4 soundly within its stated scope. A material objection must name the section, the effect, the evidence, and the repair; do not reopen points that you accepted as resolved unless draft 3 broke them.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with the section, the exact change, and the reason with evidence.
ANSWERS: (1) and (2) of section 12.
CONFIDENCE: 0 to 1.
