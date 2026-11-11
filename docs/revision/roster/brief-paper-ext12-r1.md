# Paper changes after external review r12 (GPT-6 Astra Pro): internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

The external review is `docs/revision/roster/astra-pro-ext12-r1.pdf`; the triage is `docs/paper/astra-pro-ext12-triage.md`. Commits: 54ee50c and 9f70f1d (`git show`). Data: `docs/revision/posthoc/reset.json`, `docs/revision/posthoc/reset_reference/reset_reference.json`, `/Users/oemer.demirel/Projects/touchstone/results/v2/report/report.json`. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf_ext12/main.pdf` (33 pages). Gate passes.

Check:
(1) Each new or changed number against the data: abstract pooled gaps (0.173 to -0.009; 0.021 to -0.003), C* switch effects, the reference discrepancy wording.
(2) Whether review problems 1 to 4 and the C* switch omission are resolved, and the field rename (test first).
(3) Guard question (lesson 2026-11-11): does any reviewer inference adopted in these commits contradict a qualification the paper already states? Quote both if so. In particular: the held-out order reversal text against the Search quality paragraph; the abstract priority sentence against the Q2 paragraph; the seed-versus-market sentence against the Q1 paragraph.
(4) Overclaims or errors in the changed lines.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with a main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
