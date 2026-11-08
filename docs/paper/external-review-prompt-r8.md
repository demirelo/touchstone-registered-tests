# External review prompt, round 8 (paste this; attach every file listed under "Materials" separately)

You reviewed this paper in round 7 (AAMAS main track 2/5, WEIS 2027 4/5, EC 1/5) and asked for one change before
submission: a transparent note on prediction eligibility, because the scorer credited Q3 predictions from searches the
report flags incomplete. That is done, with your text changes 2 and 3. Our internal reviewers widened your check: an
estimate also depends on other searches through its reference, the attack bank, and warm starts, so the map now traces
the recorded dependency chain. Review the revision with the same standard: adversarial, specific, numbers where asked,
and your confidence. Please confirm which files you could read.

## Materials (attached separately)

1. `PROMPT.md`: this prompt.
2. `main.pdf`: the revised paper (27 pages).
3. `RESPONSE.md`: our point-by-point response to your round-7 review.
4. `score_v2.py`: the scorer, now with the eligibility map (`inputs`, `dependencies`, `eligibility`, `eligibility_map`).
5. `scoring.json`: the scorer's original output (byte-identical to the file behind round 7's tables).
6. `eligibility.json`: new. For every cell of every prediction: its direct inputs, the full traced set of searches it
   depends on (`required`), the flagged ones, and its status under three readings; tallies with and without tracing.
7. `test_scoring.py`: the scorer's tests (they need the repository's synthetic world to run; read for what they pin).
8. Unchanged since round 7: `report.md`, `addendum.md`, `audit.json`, `audit_v2.py`, `posthoc.json`, `posthoc_v2.py`,
   `lottery_seeds.csv`, `lottery_train.csv`, `stability-result.json`, `protocol-v2.yaml`, `predictions-v2.md`,
   `revision-program-design.md` (section 6.5: search-quality checks; section 9), `operations-ledger.md`, `h4-family.py`,
   `h4-containment.md`.

## Tasks

1. **Follow-through.** For each of your round-7 problems (section 4, items 1 to 3) and remaining changes (section 5,
   items 1 to 5), say resolved, partly resolved, or not resolved, quoting the revised sentence.
2. **Eligibility.** Check `eligibility.json` against `report.md`'s search flags and `score_v2.py`. Are the traced
   tallies right (numerical 10/8/0; Q3 reading 6/8/4; descriptive reading 5/4/9; direct inputs only 7/8/3 and 6/5/7)?
   Is tracing the recorded dependency chain the right notion of a required search? Is keeping the six decision
   predictions under the descriptive reading an acceptable convention? Is the disclosure in section 9 and Table 21
   adequate and neutral?
3. **New problems** introduced by the revision: overclaims, sign or category errors, missing qualifications.
4. **Submission readiness.** Is anything left that should block a WEIS submission of this version?
5. **Publication chance.** Your updated scores and acceptance probabilities for AAMAS main track, WEIS 2027, and EC,
   with confidence, and what would still move them.

## Rigor rules

- Quote the paper's exact sentence when you criticise it.
- Separate what the files say from your own reasoning.
- Every citation you give must be real and verifiable (DOI or stable URL).
- For every probability, say what would change it.

## Output format

1. Summary verdict (one paragraph) with scores.
2. Follow-through table (one line per point).
3. Eligibility.
4. New problems, ranked by severity, each with the exact correction.
5. Submission readiness, scores and probabilities, then the remaining changes that would most improve the paper, each
   labelled **text only**, **analysis on existing records**, or **needs compute**.
