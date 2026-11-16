# Paper draft 10 (rebuilt around the churn result): internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

The author chose to rebuild the paper around the churn result after Fable 5.2's round-4 review (`docs/revision/roster/fable52-paper-r4.md`; WEIS 3/5). Plan: `docs/revision/paper-v2/outline-draft10.md`. Commits b958d69 to 7f194a7 (`git log --oneline b958d69~1..7f194a7`). Response to round 4: `/Users/oemer.demirel/Projects/touchstone/results/v2/review-fable52-r5/RESPONSE.md`. PDF: `/Users/oemer.demirel/Projects/touchstone/results/v2/review-fable52-r5/main.pdf` (35 pages; main text to page 17). Data: `docs/revision/posthoc/churn.json`, `churn_mid.json`, `churn_paper.json`, `docs/revision/followup2/convergence_analysis.json`, `runnerup_analysis.json`. The number gate passes (`numbers_v2.py`, `sites.json`); it checks values and their record paths, not the words around them.

Check:
1. Every comparative and universal word (falls, rises, reverses, every, all, only, never, survives) in the abstract, contributions, Section 10 (churn), the limits and the conclusion, against the tables and records, for both search versions (frozen and doubled). Are the claims split correctly between C* and B3?
2. The mechanism paragraph in Section 10 ("Where R3's audits go"): supported by `churn_paper.json` and the audit table, and no causal claim the design cannot carry.
3. Run A and Run B sentences (Q1 paragraph, abstract): correct and correctly labelled exploratory, with no churn cells.
4. The registered/exploratory separation: subtitle, abstract, Section 10 design paragraph (timing of amendment 1).
5. Structure: moved sections and floats (first test, registration detail, reset details, seven floats) still referenced correctly; nothing registered dropped from the paper.
6. The new code: `docs/revision/posthoc/churn_paper.py` and its tests, the gate changes in `docs/revision/paper-v2/numbers_v2.py` (new sections, kinds).

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
