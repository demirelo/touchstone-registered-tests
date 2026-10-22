# Build-plan review, round 1 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,200 words)

Review the implementation plan `docs/superpowers/plans/2026-10-22-revision-build.md` against the accepted design `docs/superpowers/specs/2026-10-22-revision-program-design.md` (draft 6; your round-6 acceptance: `docs/revision/roster/{sol,astra}-design-r6.md`). The plan covers the build phase only (code and tests on development data); operations come in a later plan. Code context: `sim/`, `scripts/`, `tests/`, especially `sim/mechanisms/proposed.py`, `second_score.py`, `audit_random.py`, `sim/policies/exploratory.py`, `adaptive.py`, `identity.py`, `families.py`, `sim/search.py`, `sim/reference.py`, `sim/cell.py`, `sim/market.py`, `sim/intervals.py`, `sim/rng.py`, `scripts/explore_attackers.py`, and `git show 46694cb:sim/mechanisms/proposed.py`.

Check with file:line evidence: (1) every design requirement that needs code before paid runs has a task, and nothing contradicts the design; (2) the interfaces are consistent across tasks and match the existing code (names, signatures, memory keys, harness order); (3) the tests would fail on a wrong implementation (name the tests that would pass with a plausible bug); (4) the Review Focus items and the frozen-file rule; (5) anything an implementer cannot decide from the plan and the design.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with the task, the exact change, and the reason with evidence.
CONFIDENCE: 0 to 1.
