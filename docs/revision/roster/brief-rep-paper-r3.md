# Churn replication in the paper: review round 3 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 500 words)

Round 2 (brief `docs/revision/roster/brief-rep-paper-r2.md`; reports `sol-rep-paper-r2.md`, `astra-rep-paper-r2.md`,
`fable-rep-paper-r2.md` in the same folder) asked for corrections. Commit `852c45e` claims to apply all of them. Check the
files, not the commit message.

Inputs:
- Plan: `docs/revision/followup3/replication-plan.md`, sections 2, 3, 4 and 8.
- Analysis: `docs/revision/followup3/replication-analysis.json`; committed draw and manifest
  `experiments/v2/replication-draw.json`, `experiments/v2/replication-manifest.json`.
- Extract: `docs/revision/followup3/replication_extract.py` (now recomputes the analysis from the collected records and
  writes only on a byte-identical match; records R3's replacement switch x), `replication-extract.json`, tests.
- Generator: `docs/revision/followup3/replication_paper.py`, tests, `replication_paper.json`, five tables
  `docs/revision/paper-v2/tables/replication*.tex`.
- Diff: `git diff 7d8d273 852c45e -- docs/revision/paper-v2/ docs/revision/followup3/`.
- Gate `results/pods/paper_check.sh` passes; it now also refuses an unlabelled "prospective replication".
- PDF: `/private/tmp/claude-502/-Users-oemer-demirel-Projects-touchstone/a48c0006-982d-4d16-9bac-5ae26e145fac/scratchpad/pdf-rep3/main.pdf`.

Check:
1. Each round-2 correction of all three reports: fixed, partly fixed, or not fixed.
2. Repeat your round-2 probes against the new `_validate` (edited extract with the same analysis hash). Does any wrong
   or stale input still pass? Is any new check too strict or wrong for the committed data?
3. The new sentences and table columns against the JSON (the 0.03 allocation gap and its markets, replacing markets,
   paired seed-bootstrap intervals, four-decimal bounds).
4. Any new overclaim, contradiction with the plan or other sections, or stale text.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
