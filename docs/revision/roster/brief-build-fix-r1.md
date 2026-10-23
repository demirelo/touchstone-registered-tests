# Re-review of the revision-build fix pass, round 1 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,200 words)

You are run at the tip of branch `revision-v2` (`109e597`). In the final whole-branch review both seats returned request-changes: `docs/revision/roster/sol-build-final.md` and `docs/revision/roster/astra-build-final.md`. The executor regraded them into twelve fixes F1-F12 (`docs/revision/build-ledger-2026-10-22.md`, section "Final review"). The fix pass is the range `963e04c..1374c75` (`git diff 963e04c 1374c75`; `109e597` adds only the ledger and review files). Plan: `docs/superpowers/plans/2026-10-22-revision-build.md`; design: `docs/superpowers/specs/2026-10-22-revision-program-design.md`.

Fixes and their commits:
- F1 block reader binds the proof to the protocol file's digest: `1e64869` (`scripts/block_draw.py`, `tests/test_block_draw.py`, `tests/fixtures/lock-2026-10-17.txt`).
- F8 constant samples in inference and calibration; F9 calibration uses the production bootstrap streams: `6c1b978` (`sim/intervals.py`, `sim/calibration_v2.py`).
- F10 recheck ties keep the original grid order: `7cf6e34` (`scripts/tune_v2.py`).
- F2 full expected provenance and dependency sets for every record; F3 H4 bundle hash in provenance; F4 validated resume, and evaluation, cross and doubling bound to the freeze; F5 acceptance uses the full catalog, `--select` limits execution only; F6 coalition prerequisites once before the pool, unique temporary files; F7 welfare doubling keeps its metadata; F12 welfare searches use the D2+H3 embedding and the corner controls: `8a5c6ad` (`scripts/revision_v2.py`, `sim/records_v2.py`).
- F11 the benchmark measures every workload kind on development seeds, and the cost table prices welfare and coalition cells from their own measurements: `1374c75` (`scripts/benchmark_v2.py`).

New ruling in the fix pass (ledger): the default benchmark workloads (`_default_fns`) run at the registered budgets and are exercised only on the pod; tests cover `measure()` with stub workloads. One test fix: `test_fresh_root_installs_salt_in_process` now pops the salt variable directly. Deferred minor: Sol final #12 (residual-picks test in `tests/test_credibility.py`).

Known unrelated failures: five tests fail on this branch because the sealed bundle was opened on 2026-10-20 (`test_h1_final_eval_namespace_refused_before_the_unseal`, `test_locked_loads_and_namespaces_are_disjoint`, `test_manifest_totals_follow_the_schedule`, `test_final_h3_cells_are_beta_headline_median_only`, `test_reference_records_carry_per_seed_values_and_foreign_rules_are_refused`). `main` fixes them in `4caa10b` (tests only). Do not report them.

Check with file:line evidence:
1. For each of F1-F12: does the code close the failure scenario of the original finding (both seats' text), with no narrower reading? Reproduce the original scenario where you can (in-memory probes are fine).
2. For each fix's test: would it fail against the pre-fix code at `963e04c` and against a plausible partial fix?
3. Regressions: does any fix break another design or plan requirement, especially the plan's Review Focus items (exit-round actions, empty rounds and exhausted budgets, evaluation before freeze, seed-range collisions, resume after a crash), the freeze order, or the development-only constraint?
4. The new benchmark ruling and the deferred minor: accept or reject, with the reason.
5. The twelve frozen files are still byte-identical to `2a288f5`.

You run in a read-only sandbox: run pytest with `-p no:cacheprovider`; tests that write files may fail for that reason alone; say which you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of F1-F12, one line: closed | partly closed | open.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
