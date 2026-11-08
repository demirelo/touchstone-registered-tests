# External review prompt, round 7 (paste this; attach every file listed under "Materials" separately)

You reviewed this paper in round 6 (AAMAS main track 2/5, WEIS 2027 4/5, EC 1/5). You found that our claim "C* needs H4"
was wrong and asked for two changes before submission: correct that passage and disclose the Q4-b scoring correction in the
paper. Both are done, with your other corrections and your remaining changes 1 to 3. Review the revision with the same
standard: adversarial, specific, numbers where asked, and your confidence. Please confirm which files you could read.

## Materials (attached separately)

1. `PROMPT.md`: this prompt.
2. `main.pdf`: the revised paper (26 pages).
3. `RESPONSE.md`: our point-by-point response to your round-6 review.
4. `report.md` and `addendum.md`: the report written by the tagged code, and the addendum.
5. `audit.json` and `audit_v2.py`: the inference audit (unchanged since round 6).
6. `posthoc.json`, `posthoc_v2.py`, `lottery_seeds.csv`: the exploratory analyses, now with the training-feasible weight.
7. `lottery_train.csv`: new. The training observations behind the lottery's training gains: per rule, component, and
   dev-train seed, the search record, the selected policy's knobs, its normalised profit, the frozen reference's name and
   normalised profit, and the gain (90 rows).
8. `score_v2.py`: new in the package. The corrected prediction scorer (Q4-b on calibrated p-values).
9. `stability-result.json`: the re-evaluation with the registered configurations.
10. `protocol-v2.yaml`, `predictions-v2.md`, `revision-program-design.md` (section 9: estimands, decision rules, scope).
11. `operations-ledger.md`, `h4-family.py`, `h4-containment.md`.

## Tasks

1. **Follow-through.** For each of your round-6 problems (section 4, items 1 to 5) and remaining changes (section 5, items
   1 to 5), say resolved, partly resolved, or not resolved, quoting the revised sentence.
2. **The C* passage.** Is section 9 and the new training-feasible row of Table 11 now right? Check the training means against
   `lottery_train.csv`. Is the way the 0.4765 weight was chosen described honestly?
3. **Disclosure and release.** Is the Q4-b disclosure in the paper adequate? Does the Availability paragraph now separate
   the frozen tag from the paper artifact correctly?
4. **New problems** introduced by the revision: overclaims, sign or category errors, missing qualifications. Check the new
   contributions paragraph against the results.
5. **Submission readiness.** Is anything left that should block a specialist-venue (WEIS) submission of this version?
6. **Publication chance.** Your updated scores and acceptance probabilities for AAMAS main track, WEIS 2027, and EC, with
   confidence, and what would still move them.

## Rigor rules

- Quote the paper's exact sentence when you criticise it.
- Separate what the files say from your own reasoning.
- Every citation you give must be real and verifiable (DOI or stable URL).
- For every probability, say what would change it.

## Output format

1. Summary verdict (one paragraph) with scores.
2. Follow-through table (one line per point).
3. The C* passage, the disclosure, and the release description.
4. New problems, ranked by severity, each with the exact correction.
5. Submission readiness, scores and probabilities, then the remaining changes that would most improve the paper, each
   labelled **text only**, **analysis on existing records**, or **needs compute**.
