# Churn replication in the paper: review round 4 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 3 (brief `docs/revision/roster/brief-rep-paper-r3.md`; reports `sol-rep-paper-r3.md`, `astra-rep-paper-r3.md`,
`fable-rep-paper-r3.md`) left two items: the Table 30 caption, and extract-only values (allocation shares, x, audit
counts) that an in-range hand edit could change without detection. Commit `e875923` claims to close both. Check the
files, not the commit message.

What changed (`git diff 184b608 e875923 -- docs/revision/`):
- `replication_extract.py --check` rebuilds the extract from the run records (after recomputing the analysis byte for
  byte) and compares it with the committed file. It was run on 2026-11-24 on the analysed clone of the pulled pod output:
  "ok: the extract rebuilt from the run records is byte-identical" (row "Paper extract" in
  `docs/revision/followup3/replication-publication.md`). The records are not in the worktree, so you cannot rerun it.
- `test_replication_extract.py` pins the committed extract's sha256 (`EXTRACT_SHA256`); the gate runs this test, so any
  later edit of the extract fails the gate until it is rebuilt from the records. Proved: an in-range edit of a share made
  the pin test fail; restoring the file made it pass.
- `_validate`: x must be an int in {0, 1}; shares must be present where the attacker's counts are nonzero. Refusal tests
  added. The extract refuses an --out without analysis.json before it touches that folder.
- Table 30 caption now describes the interval lines.

Check:
1. Are your round-3 items closed? Repeat your probes: does any edited extract now pass the gate's tests?
2. Is pinning plus a recorded rebuild an adequate authentication for values that only the run records hold? If not,
   say what would be, given that the records cannot ship inside the paper source.
3. Any new error in the diff.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with main.tex line, file, or site name, or "none".
CONFIDENCE: 0 to 1.
