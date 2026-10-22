# Design review, round 1 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,500 words)

You review the design of the revision program for the Touchstone paper: `docs/superpowers/specs/2026-10-22-revision-program-design.md`. The author chose the full program after an external review (triage: `docs/paper/gpt-pro-review-triage-2026-10-22.md`, section "Program"). Context: paper `paper/main.tex` (draft 8), final evaluation `docs/final-evaluation-2026-10-20/README.md`, robustness `docs/robustness/2026-10-22-results.md`, theory `docs/theory/reset-deterrence.md`, simulator spec `docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md` (admissible class section 4.0), code in `sim/` and `scripts/` (R3: `sim/mechanisms/proposed.py`; B3: `sim/mechanisms/second_score.py`, `audit_random.py`; tuning: `sim/tuning.py`; attackers: `sim/policies/exploratory.py`, `scripts/explore_attackers.py`; robustness runner `scripts/robustness_v1.py`; killed predecessor `git show 46694cb:sim/mechanisms/proposed.py`).

Judge whether this design, once executed, answers the four questions of its section 1 at the standard of a strong AAMAS or GameSec main-track paper, and whether it is internally sound. Check with evidence (file:line, primary sources for Sarmenta 2001 and BOINC adaptive replication):
1. The credibility comparator is a fair, matched, and strong form of the established principle inside the admissible class.
2. The factorial decomposition identifies the components' contributions; the equivalence tests are correct and sufficient.
3. The common tuning procedure is equal across rules and does not favour R3 or R4.
4. The attack families and objectives are strong enough; X7-SC uses only allowed observations; the welfare and coalition objectives are well defined.
5. The generator, the block-hash randomness, the seed ranges, and the lock procedure prevent outcome-dependent choices.
6. The decision rules and the interval method are valid for the estimands (pairing, multiplicity, pooling over 6 instances, the 5-of-6 rule).
7. Cost: which cells to cut, if any, to stay within the caps without weakening Q1 to Q3.
8. Answer the seven questions of section 11.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with the section, the exact change, and the reason with evidence.
ANSWERS: (1) to (7).
CONFIDENCE: 0 to 1.
