# Paper draft 10: internal review round 4 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 450 words)

Round 3 (`docs/revision/roster/astra-paper-d10-r3.md`, reject, 6 corrections) was applied in 37fe4fd (`git show 37fe4fd`); earlier: round 2 in a7f8857, round 1 in d496c04, Fable round 5 in 2cfd7f0. PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf_d10d/main.pdf` (main text to page 17 or 18). Data: `docs/revision/posthoc/churn.json`, `churn_mid.json` (new `review_r5` block), `churn_paper.json` (new fields), `docs/revision/followup2/runnerup_analysis.json`, `convergence_analysis.json`. The number gate passes; it checks values and paths, not words.

Check:
1. Each of your six round-3 corrections is applied correctly, or name what is missing. Items you deferred as needs-compute (no-churn diagnostic row, newest-identity frequency) stay listed as not done.
2. Every comparative and universal word in the abstract, contributions, Section 10, limits and conclusion against the records, for both search versions; the C* and B3 claims split correctly; no class claim beyond C*.
3. The new code: `review_r5` in `docs/revision/posthoc/churn_block.py` (other fields must be byte-identical), the summary fields and the byte-for-byte figure check in `churn_paper.py`, the new kinds in `numbers_v2.py`, and their tests.
4. New errors introduced by the two commits.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
