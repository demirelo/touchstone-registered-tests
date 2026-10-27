# Whole-branch review, Part A2, round 2 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 1,000 words)

Round 1 (your own reviews: `docs/revision/roster/sol-a2-final-r1.md`, `docs/revision/roster/astra-a2-final-r1.md`) found seven defects. The executor fixed them in `git diff 3272b1b HEAD` (commits ab47d9c, ece90d0, 1478c9a), each with a test that failed first; the ledger `docs/revision/part-a2-ledger-2026-10-27.md` records each fix and two new rulings (lines starting "Final:"). The whole branch is still `git diff fee49c9 HEAD` against design draft 7 (`docs/superpowers/specs/2026-10-22-revision-program-design.md`) and the plan `docs/superpowers/plans/2026-10-27-revision-part-a2.md`.

Check, with file:line evidence:
1. **Each round-1 finding**: is it fixed on the real path, and does its new test fail against the old code?
   - report: missing cells counted only for scheduled cells (`Records.rec`, `scheduled`), including cut families;
   - search status (flagged, scheduled check missing, missing cell) on Q3 robustness, welfare, coalition, and Q4 labels; families without a scheduled check read "no search-quality claim";
   - Q2: parts withheld separately; per market and headline searched and fixed-attack contrasts with intervals, both profit terms, gross and net efficiency; envelope per market;
   - W1 and coalition numerical refusals withheld and rendered;
   - G_min doubling: one winner (step 6's frozen winner unless the continued search beats it) for the objective change and the held-out diagnostic;
   - honest-replacement profit from the ledger's profit flows, rendered with false refunds;
   - pod billing: each context's freeze (training bank matrices) as one serial task.
2. **New defects the fixes introduced**, and any remaining defect from round 1's scope that changes what a person running the operations gets.
3. **Rulings**: the two new "Final: Ruling:" lines.

Report only findings that change what a person running the operations gets; polish under Minor. Read-only sandbox: run pytest with `-p no:cacheprovider` (set `MPLCONFIGDIR` to a writable path if needed); say what you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, the failure scenario, and the repair.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
