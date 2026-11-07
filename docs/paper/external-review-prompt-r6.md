# External review prompt, round 6 (paste this; attach every file listed under "Materials" separately)

You reviewed this paper in round 5 (verdict: AAMAS main track 2/5, WEIS 3/5, EC 1/5). Your most important point was
the conflict between the registered p-value arithmetic and the printed numbers. We traced it, applied your corrections,
and did most of your remaining changes on the existing records. Review the revision with the same standard:
adversarial, specific, numbers where asked, and your confidence. Please confirm which files you could read.

## Materials (attached separately)

1. `PROMPT.md`: this prompt.
2. `main.pdf`: the revised paper (26 pages).
3. `RESPONSE.md`: our point-by-point response to your round-5 review.
4. `report.md` and `addendum.md`: the report written by the tagged code, and the addendum (the addendum now prints the
   largest mean change as 0.0074).
5. `audit.json`: new. Raw, calibrated and Holm-adjusted p-values recomputed from the records and checked against the
   report; Q1 categories recomputed with the frozen rule; Q4 per market under the report's and the registered
   configurations; the scan for extreme intervals with the studentization diagnostic.
6. `posthoc.json` and `lottery_seeds.csv`: the exploratory analyses, now with the lottery's training gains,
   both companion families, the weight sensitivity, and the per-seed component values (3,000 rows).
7. `stability-result.json`: the re-evaluation with the registered configurations.
8. `audit_v2.py` and `posthoc_v2.py`: the scripts that wrote `audit.json`, `posthoc.json` and the CSV.
9. `protocol-v2.yaml`, `predictions-v2.md`, `revision-program-design.md` (section 9: estimands, decision rules, scope).
10. `operations-ledger.md`: what ran, its cost, every deviation and incident.
11. `h4-family.py`, `h4-containment.md`: the defence-aware attacker and its author's containment note.

## Tasks

1. **Follow-through.** For each of your round-5 findings (section 4, items 1 to 8) and your eight remaining changes
   (section 5), say resolved, partly resolved, or not resolved, quoting the revised sentence.
2. **Finding 1.** We report that the frozen code follows the registered rule and only the paper's labels were wrong:
   the report stores raw Q4 component p-values and the calibrated Q1 value that enters Holm. Check this against
   `audit.json`, `audit_v2.py`, and the design. Are the new labels in Tables 5 and 8 right? Is Q4-b now scored as
   registered?
3. **The welfare lottery.** Is every lottery sentence (abstract, introduction, section 9, discussion, conclusion,
   Tables 11 and 12) now an exploratory estimate on the evaluation records that selected it? Check the training gains
   in Table 11 against `posthoc.json` and the CSV: three mixtures meet the registered W1 training constraint and C*'s
   public-family mixture does not. Is that stated with the right consequence?
4. **The fresh1 intervals.** Is the explanation in section 9 and `audit.json` right, and is the disclosure enough?
5. **New problems** introduced by the revision: overclaims, sign or category errors, missing qualifications.
6. **Publication chance.** Your updated scores and acceptance probabilities for AAMAS main track, WEIS 2027, and EC,
   with confidence, and what would still move them.

## Rigor rules

- Quote the paper's exact sentence when you criticise it.
- Separate what the files say from your own reasoning.
- Every citation you give must be real and verifiable (DOI or stable URL).
- For every probability, say what would change it.

## Output format

1. Summary verdict (one paragraph) with scores.
2. Follow-through table (one line per point).
3. Finding 1, the lottery, and the fresh1 intervals.
4. New problems, ranked by severity, each with the exact correction.
5. Scores and probabilities, then the remaining changes that would most improve the paper, each labelled
   **text only**, **analysis on existing records**, or **needs compute**.
