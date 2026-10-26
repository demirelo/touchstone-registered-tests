# Re-review of the operations Part A fix pass, round 3 (read-only; no paid APIs; do not read `sealed/` or `sealed2/`; reasoning effort high; under 800 words)

You are run at the tip of the branch. In round 2 (`docs/revision/roster/sol-ops-fix-r2.md`, `docs/revision/roster/astra-ops-fix-r2.md`) both seats raised the same two Important findings. They were fixed in `909c1d5..HEAD` (commit b5f6d17). The triage, tests, and the replacement ruling are at the end of `docs/revision/operations-build-ledger-2026-10-26.md` (from "Fix-pass re-review round 2").

- M1 `scripts/artifact_v2.py` (`_draw_problems`): `calibrated_cfg` must equal the drawn `cfg` in every field except `alpha` and `budget`, and those two must be finite positive numbers. Test: `tests/test_artifact.py::test_m1_the_calibrated_configuration_follows_from_the_draw`.
- M2 `scripts/revision_v2.py` (`_cross_problems`): per-seed rows and matrix entries must be finite numbers (no booleans, strings, or nulls). Tests: `tests/test_revision_v2.py::test_m2_cross_rows_and_matrix_must_be_finite_numbers`, `::test_m2_boolean_cross_rows_are_stale_through_the_real_verifier`.
- Test strengthening you asked for: L4 (each input omitted alone), L5 (each git command fails alone with valid-looking output), L7 (transitive package `six`; marker exclusion of `tzdata`), L8 (the W1 constraint label).

Check with file:line evidence:
1. Are your round-2 findings closed, with no narrower reading? Reproduce your round-2 probes.
2. Would each new test fail against `909c1d5` and against a plausible partial fix?
3. Regressions in the touched files, and the frozen files (byte-identical to `2a288f5`).
4. The replacement calibrated_cfg ruling: accept or reject, with the reason.

Report only findings that change what a person running the operations gets. Polish goes under Minor.

Read-only sandbox: run pytest with `-p no:cacheprovider` (set `MPLCONFIGDIR` to a writable path if Matplotlib blocks collection); say which tests you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of your round-2 findings, one line: closed | partly closed | open.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
