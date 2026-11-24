# Churn replication in the paper: review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

Round 1 (brief `docs/revision/roster/brief-rep-paper-r1.md`; reports `sol-rep-paper-r1.md`, `astra-rep-paper-r1.md` in the
same folder; a third reviewer gave accept-with-caveat with overlapping points) asked for corrections. Commit `3405926`
claims to apply them. Check the files, not the commit message.

Inputs:
- Plan (fixed and stamped before the draw): `docs/revision/followup3/replication-plan.md`, sections 2, 3, 4 and 8.
- Analysis output: `docs/revision/followup3/replication-analysis.json`.
- Extract: `docs/revision/followup3/replication_extract.py`, `replication-extract.json`, tests `test_replication_extract.py`.
- Generator: `docs/revision/followup3/replication_paper.py`, tests `test_replication_paper.py`, output
  `replication_paper.json`, tables `docs/revision/paper-v2/tables/replication*.tex` (five files).
- Paper diff: `git diff f040b38 3405926 -- docs/revision/paper-v2/ docs/revision/followup3/`.
- Gate: `results/pods/paper_check.sh` (now also runs the two replication test files); it passes.
- PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf-rep2/main.pdf`
  (built from 3405926). Replication text: end of Section "Honest identity churn"; tables 30 to 33 in Appendix B.

Check:
1. Each round-1 correction of both reports: fixed, partly fixed, or not fixed. Name any you think was missed.
2. The new sentences against the JSON: the primary minus all-frozen differences, the two-market concentration (and the
   claim that the other contrasts and p = 0.03 show the same pattern with the primary winners), C* minus R3 at 0.03,
   the support and companion counts, the all-frozen expectation verdicts, the allocation values and the missing p = 0.03
   markets, the pooled seed-bootstrap interval, and the interval methods against plan section 2.
3. The appendix tables: correct values, labels and column order; the allocation statistics against
   `docs/revision/posthoc/churn_block.py` (audit_allocation).
4. The extract and generator: does the binding, status check, continued-list derivation (wrapped `select_winner`) and
   the allocation (wrapped `_audit_of`) leave the collector's decisions unchanged? Would a stale or wrong input still pass?
5. Any new overclaim, contradiction with the plan or with other sections, or stale text.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
