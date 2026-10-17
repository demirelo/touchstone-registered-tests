# Final whole-branch review: amendment 1 (branch amendment-1, worktree is your working directory)

You are a senior code reviewer. Review the completed work against its plan and the consensus it implements, and identify issues before the branch is tagged as a registration point. Read-only sandbox; you may run targeted tests with `.venv/bin/python -m pytest <file> -q -p no:cacheprovider` if the sandbox permits writes to /tmp only; never run paid APIs; the sealed bundle stays unread. Reasoning effort high. Under 1,500 words.

## What was implemented
Amendment 1 to the lock of 2026-10-17: `sim/amendment.py` (paired statistic gain_diff, reserved seed layout with remedy factors, 12-endpoint gate at n = 40, strict admission, canonical amendment hash), `scripts/coverage_ext.py` (the extension study: measured provenance, pools, cells, merge, report, refusals), the amended predicate and H3 record checks in `sim/claimcheck.py`, the two-verdict `scripts/check_claim.py` (draft refusal, extension-report verification, H3 extraction), the final H3 stress-test cells in `sim/manifest.py`, `scripts/amend.py` (validator and registrar), the binding amendment file `experiments/amendment-2026-10-17.yaml`, the note and roster record under `docs/amendments/`, the run book and README, tests for all of it, plus three post-lock test-expectation fixes and a call-time `TOUCHSTONE_LOCKED` override in `sim/locked.py` that `scripts/check_claim.py` refuses.

## Requirements
- Plan: docs/superpowers/plans/2026-10-17-amendment-1.md (v4, accepted by both seats). Its Global Constraints and Review Focus bind.
- Consensus: docs/amendments/roster/consensus-final.md; spec sections 4.0, 4.2, 6.2, 8 of docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md.
- Ledger with the executor's rulings: .superpowers/sdd/2026-10-17-amendment-1/progress.md (every `Ruling:` line is a decision you may contest).

## Git range
Base e245853f5512380a793cf9cb1917c7b108cff2d0, head HEAD (`git diff --stat e245853..HEAD`; the full diff is also at .superpowers/sdd/2026-10-17-amendment-1/review-e245853..2d56f8a.diff).

## The spec is a vision document
For behaviour the spec is silent on, judge by what a reasonable person using this software would expect; grade by effect on that person. Verify each finding by reading the code (and running a test where possible); do not report what you have not verified.

## Review Focus (from the plan; check each deliberately)
1. A cell whose selected reference for B2 or B3 is abstain: gain_diff uses reference profit 0 and never raises.
2. H3 rows with a duplicate seed, wrong namespace, stale parameters, or a missing rule: INCONCLUSIVE with the reason or refused before evaluation, never an exception or a silent partial merge.
3. `scripts/check_claim.py` without an amendment file: original behaviour and output unchanged.
4. Doubled pool or doubled R: the base pool and replications stay prefixes and never overlap.
5. A self-consistent extension report from a changed tuned file or reference record: `scripts/amend.py` refuses.
Also: the registration-integrity properties (locked.yaml and registered artifacts untouched; both verdicts reported; draft amendment refused in confirmatory mode; the override guard), and the statistics of the extension (statistic, seeds, gate, admission, decision rule) against the consensus.

## Output
FINDINGS, each: severity (Critical | Important | Minor), file:line, the defect in one sentence, the concrete failure scenario (inputs -> wrong output), the fix. Then DECLINED TO JUDGE (behaviours you noticed but did not grade, one line each). Then VERDICT: approve | approve-with-fixes | request-changes, and CONFIDENCE 0-1.
