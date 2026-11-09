# Paper revision after external review round 9 (fresh reviewer): internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 350 words)

The round-9 review (`docs/paper/external-review-r9.md`; response `docs/paper/response-to-review-r9.md`) asked for text changes and analyses on existing records. Commits cc24e65, d3ff73d and b8cadfd respond: `docs/revision/posthoc/posthoc_v2.py` (new `doubled` and `honest`, tables `posthoc_doubled.tex` and `posthoc_honest.tex`, tests in `test_posthoc_v2.py`); `docs/revision/paper-v2/tables_v2.py` (Q4 decision column marks inherited flags from `addendum.json`); `numbers_v2.py` (gain leaves and a `share` kind); `sites.json` (`r_dbl_*`, `r_abs_*`, `r_hon_*`); main.tex: audit-dues sentence (Section 1), gain caveat (Section 3), comparator selection (Section 4), Corollary 1 statement and proof (both inequalities), Lemma proof keys, Q1 paragraph (absolute gains, margin wording, doubled winners, honest replacement), lottery pointer, Gilpatric et al. 2015, Q4 caption, two new tables. Data: `/Users/oemer.demirel/Projects/touchstone/results/v2/report/report.json` (`doubling`, `q3.diagnostic`), `report/addendum.json`, `eval/all/evaluate/`. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf22/main.pdf` (29 pages). The paper gate passes.

Check: (1) each change is correct against the data and the code (recompute the doubled and honest values); (2) the corollary proof is valid and the B2/B3 argument is right; (3) overclaims or new errors in the changed lines; (4) whether the letter states anything the paper does not do.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
