# Re-review of the operations Part A fix pass, round 1 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,200 words)

You are run at the tip of the branch. Your final review (`docs/revision/roster/sol-ops-build-final.md`, `docs/revision/roster/astra-ops-build-final.md`) was merged into twelve fixes K1-K12, made in `cd61014..HEAD`; the triage, each fix's tests, and the rulings are at the end of `docs/revision/operations-build-ledger-2026-10-26.md` ("Final review"). Plan: `docs/superpowers/plans/2026-10-25-revision-operations.md`; design: `docs/superpowers/specs/2026-10-22-revision-program-design.md`.

- K1 `scripts/ots_proof.py` (new: proof parser), `scripts/block_draw.py`, `scripts/draw_v2.py`: the draw is bound to the committed proof's bytes.
- K2 `scripts/block_draw.py` (`anchor` records the headers from the lowest rejected attestation to A), `scripts/draw_v2.py`: the lowest anchor on one continuous chain; tests on a synthetic chain whose Merkle roots are real proof commitments (`tests/_chain.py`).
- K3 `scripts/lock_v2.py`: commit object, ancestry, and git exit codes.
- K4 `scripts/coverage_v2.py`, `scripts/promote_v2.py`: pool provenance and the same pools at select and validate.
- K5 `scripts/promote_v2.py` (`verify_promoted`, `derive_params`), `scripts/lock_v2.py`: promoted bytes at --final and the lock.
- K6 `scripts/budget_v2.py`: amounts, caps, approvals.
- K7 `scripts/draw_v2.py`, `scripts/revision_v2.py`: one H4 decision, checked against the protocol before execution.
- K8 `scripts/revision_v2.py` (`_schema_problems`, `_cross_problems`): complete schemas; the report tested over the real verify.
- K9 `scripts/revision_v2.py`: verify requires the recorded inputs.
- K10 `scripts/benchmark_v2.py` (`task_seconds`, `pod_plan`): every dispatch wave at measured component times.
- K11 `scripts/report_v2.py`: headline whole systems, a complete Markdown, --check over both files.
- K12 `scripts/artifact_v2.py`, `scripts/reproduce.py`: tag binding, signature, artifact check, locked environment, the real report.

Check with file:line evidence:
1. Your own final-review findings: is each closed by its fix, with no narrower reading? Reproduce your earlier probes where you can.
2. Each fix's test: would it fail against `cd61014` and against a plausible partial fix?
3. Regressions anywhere in Part A, the plan's Review Focus items, and the frozen files (byte-identical to `2a288f5`).
4. The new rulings in the ledger's final-review section: accept or reject, with the reason.

Read-only sandbox: run pytest with `-p no:cacheprovider` (set `MPLCONFIGDIR` to a writable path if Matplotlib blocks collection); say which tests you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of your final-review findings, one line: closed | partly closed | open.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
