# Churn replication in the paper: review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

The prospective churn replication has run and its results are now in the paper. Review the paper changes against the
plan and the records. Do not trust the commit messages; check the files.

Inputs:
- Plan (fixed and stamped before the draw): `docs/revision/followup3/replication-plan.md`, sections 2, 3, 4 and 8.
- Committed analysis output: `docs/revision/followup3/replication-analysis.json` (written by `rep_v2.py --stage analyse`).
- Post-analysis extract: `docs/revision/followup3/replication_extract.py` and `replication-extract.json` (R3 audit counts
  from `rep_collect.collect`; the continued-cell list).
- Paper summary generator and tests: `docs/revision/followup3/replication_paper.py`, `test_replication_paper.py`,
  `replication_paper.json`, `docs/revision/paper-v2/tables/replication.tex`.
- Run record: `docs/revision/followup3/replication-publication.md` (section "Run and analysis").
- Paper diff: `git diff 4f4f47d ccd5da2 -- docs/revision/paper-v2/` (main.tex, sites.json, floats.json, numbers_v2.py).
- PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf-rep1/main.pdf`
  (built before ccd5da2, which only rewords one sentence). The new text is at the end of Section "Honest identity churn".
- The number gate (`results/pods/paper_check.sh`) passes; it checks values, paths and kinds, not words.

Check:
1. Every sentence about the replication against the plan: the label (prospective-exploratory), the descriptive support
   criterion and the material companion, both winner sets, the scoring of the five expectations, no causal reading of
   the failed all-frozen expectation, and the scope limits in plan section 8.
2. Every number and comparative word in the new paragraphs, the table, the abstract, contributions, results in brief,
   limits and conclusion against `replication-analysis.json` and `replication_paper.json`.
3. Claims the plan requires that are missing (for example the attack and reference terms, efficiency under attack,
   R3's audit allocation, intervals), or claims that go beyond it.
4. The generator, the extract and their tests: correctness, and whether a stale or wrong input would be caught.
5. Stale text elsewhere in the paper that the replication now contradicts (for example claims that the runner-up was
   never run under churn, or the title).

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
