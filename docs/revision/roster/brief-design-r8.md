# Design review, round 8 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 800 words)

Draft 7 of `docs/superpowers/specs/2026-10-22-revision-program-design.md` revises the round-7 version after your round-7 review (`docs/revision/roster/{sol,astra}-design-r7.md`; both: reject). The disposition of each correction is the table "Round 7 (both seats: reject) and its disposition" at the end of section 14. See the change with `git diff f9c16cf HEAD -- docs/superpowers/specs/2026-10-22-revision-program-design.md`. Context as in round 7 (`docs/revision/roster/brief-design-r7.md`), including the GPT Pro triage `docs/revision/gpt-pro-review-r2-triage-2026-10-27.md` (section 6 records its corrections).

Check: (1) each of your round-7 corrections is resolved, or say exactly what remains; (2) new errors this revision introduces, in particular the six-step coalition order and its rescoring (6.3), the X7-SC wait rule and the X8-DB timing (5.2), H4's bounded controls and the cost recomputation after H4 (5.3, 11), the two cell statuses (6.5, 8.1a), the efficiency wording (9.3), and the cost table (8.2); (3) whether the Code column of section 14 is now complete. Accept only if the design, once executed, answers Q1 to Q4 soundly within its stated scope. A material objection must name the section, the effect, the evidence, and the repair; do not reopen points that you accepted in round 7 unless this revision broke them.

Read-only sandbox: say what you could not run.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with the section, the exact change, and the reason with evidence. Then, for each of your round-7 corrections, one line: resolved | partly resolved | open.
CONFIDENCE: 0 to 1.
