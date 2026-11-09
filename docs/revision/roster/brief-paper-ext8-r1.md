# Paper revision after external review round 8: internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 300 words)

The round-8 external review (`docs/paper/external-review-r8.md`) says submit to WEIS and asks for three text fixes: (1) the trace gives recorded ancestors of the listed inputs, not searches a cell "requires"; an inherited flag does not show that the flagged candidate was selected or that the statistic would change; (2) the broader reading excludes flagged scored cells (a prediction still fails on any eligible failing cell) outside six decision-related predictions kept by convention, and is renamed "Flagged inputs, all non-exempt cells"; (3) the original numerical scoring path is separated from the eligibility analysis, and Table 21 (now numbered 19, `tab:pred-eligibility`) carries both direct-input tallies (7/8/3 and 6/5/7). Commit 3512673 responds: main.tex section 9 Predictions paragraph and the captions of `tab:predictions` and `tab:pred-eligibility`; `tables_v2.py` (two direct-input rows, renamed label) with a new test in `test_tables.py`; sites `r_pred_dd_*` in `sites.json`. No scorer output changed. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf16/main.pdf` (28 pages). The paper gate passes.

Check: (1) each of the three fixes is made and accurate against `score_v2.py` and `/Users/oemer.demirel/Projects/touchstone/results/v2/paper/eligibility.json`; (2) new errors in the changed lines (wording, numbers, labels, any remaining "descriptive reading" that should now say "broader").

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
