# Paper revision after external review round 7: internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 1 (`docs/revision/roster/sol-paper-ext7-r1.md`, `astra-paper-ext7-r1.md`) rejected: the eligibility map used direct inputs only; exclusion clauses were incomplete; the JSON did not list every cell; the decision exemption was called mandated. Commit aabaf69 (diff against the round-1 commit 8d16224 and its brief commit) responds. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf15/main.pdf` (27 pages). Letter: `docs/paper/response-to-review-r7.md`.

Changed: `docs/revision/paper-v2/score_v2.py` (`dependencies` follows every record's `upstream` file hashes from the cell's evaluation record; `eligibility(..., deps)`; `eligibility_map` exports every cell with inputs, flagged searches, and per-reading status, plus direct-input tallies; `_num` refuses non-finite; `_refused`/`_est` make "not decided: ..." entries not assessed in Q2 and Q3-d), tests in `test_scoring.py`; main.tex section 9 Predictions paragraph and Table 21 caption; `sites.json` (direct-input tally sites). Output: `/Users/oemer.demirel/Projects/touchstone/results/v2/paper/eligibility.json` (traced: 10/8/0, 6/8/4, 5/4/9; direct: 10/8/0, 7/8/3, 6/5/7). Records: `/Users/oemer.demirel/Projects/touchstone/results/v2/eval/all/`. The paper gate passes.

Check: (1) each round-1 correction from both seats is resolved, or say what remains; (2) the traced tallies and marks (dagger Q3-a, b, d, e; double dagger Q1-c, Q2-a to d) are right; (3) the Predictions paragraph, Table 21 caption, and letter are true and neutral; (4) new errors.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
