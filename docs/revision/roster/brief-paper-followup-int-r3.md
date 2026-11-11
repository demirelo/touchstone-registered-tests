# Paper changes after the follow-up external reviews: internal review round 3 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Follow-up reviews by Fable 5.2 (`docs/revision/roster/fable52-paper-r2.md`) and Astra (`docs/revision/roster/astra-paper-ext11-r1.md`), both WEIS 2/5, raised new problems. Commits fdfd83e, c37bf1c and HEAD respond (rounds 1-2: `docs/revision/roster/{sol,astra}-paper-followup-int-r{1,2}.md`, all reject; check each round-2 correction): `docs/revision/posthoc/posthoc_v2.py` (`direct_priority`, `nesting`, `envelope_interval`, `honest_relative`; tests; `posthoc.json`), `numbers_v2.py` kinds, `sites.json`, and main.tex (abstract, introduction, Section 4 comparator, Q1, Q2, honest-replacement sentence, search quality, mixture, conclusion, Q1 caption, results in brief). Data: `/Users/oemer.demirel/Projects/touchstone/results/v2/report/report.json`, `eval/all/`. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf33/main.pdf` (31 pages). Gate passes.

Check: (1) each new number against the data (recompute the direct priority contrast, the nesting shortfalls and count, the envelope interval, the relative profit); (2) whether each external new problem is addressed or still open, and which remain for compute; (3) overclaims or errors in the changed lines (in particular the sign-versus-size sentence, the priority-phase scope sentence, and the nesting interpretation, which compares evaluation-seed gains of training-selected winners).

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
