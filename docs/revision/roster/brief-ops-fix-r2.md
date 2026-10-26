# Re-review of the operations Part A fix pass, round 2 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 1,000 words)

You are run at the tip of the branch. Your round-1 re-review (`docs/revision/roster/sol-ops-fix-r1.md`, `docs/revision/roster/astra-ops-fix-r1.md`) was merged into findings L1-L10, fixed in `34d9016..HEAD` (commits d1fec51, 1ad00a8, 909c1d5). The triage, each fix's test, and the new rulings are at the end of `docs/revision/operations-build-ledger-2026-10-26.md` (from "Closed in round 1"). Plan: `docs/superpowers/plans/2026-10-25-revision-operations.md`; design: `docs/superpowers/specs/2026-10-22-revision-program-design.md`.

- L1 `scripts/budget_v2.py` (`_valid`): a saved approval needs its written text on load.
- L2 `scripts/revision_v2.py`, `scripts/draw_v2.py` (`h4_decision`): the decision carries `registered_sha256`, and fresh runs refuse a decision that does not match the protocol.
- L3 `scripts/revision_v2.py` (`_schema_problems`, `_num`): finite numeric summaries and elements, also through the real verifier and report.
- L4 `scripts/revision_v2.py` (main): verify needs `--instances` and `--protocol` in every mode.
- L5 `scripts/lock_v2.py` (`check_commit`): every git command's exit code.
- L6 `scripts/artifact_v2.py` (`_draw_problems`, `check(..., offset)`), `scripts/draw_v2.py` (`instances(..., calibrate)`), `scripts/reproduce.py` (`--offset`): the packed draw verifies against the packed protocol and proof, and the packed instances equal the ones the draw gives (all fields except `calibrated_cfg`; see the rulings).
- L7 `scripts/reproduce.py` (`environment_problems`): `requires-python`, and the project's transitive runtime dependencies in `uv.lock` (markers evaluated here) installed at a locked version.
- L8 `scripts/report_v2.py`: Markdown intervals.
- L9 plan Operation 7: run-book commands carry the arguments the runner requires.
- L10 `tests/test_artifact.py`: the changed-report test rebuilds the manifest, so only the real report check can catch it.

Check with file:line evidence:
1. Your own round-1 findings: is each closed by its fix, with no narrower reading? Reproduce your earlier probes where you can.
2. Each fix's test: would it fail against `34d9016` and against a plausible partial fix?
3. Regressions anywhere in Part A, the plan's Review Focus items, and the frozen files (byte-identical to `2a288f5`).
4. The two new L6 rulings in the ledger (calibrated_cfg not recomputed; published_height read from the packed instances): accept or reject, with the reason.

Report only findings that change what a person running the operations gets. Polish goes under Minor.

Read-only sandbox: run pytest with `-p no:cacheprovider` (set `MPLCONFIGDIR` to a writable path if Matplotlib blocks collection); say which tests you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of your round-1 findings, one line: closed | partly closed | open.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
