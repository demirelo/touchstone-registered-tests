# Re-review of the revision-build fix pass, round 3 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 800 words)

You are run at the tip of the review branch. Round 2 (`docs/revision/roster/sol-build-fix-r2.md`, `docs/revision/roster/astra-build-fix-r2.md`) left five items, merged as H1-H5 and fixed in commit `467fc69`; the triage, tests, and one replacement ruling are at the end of `docs/revision/build-ledger-2026-10-22.md` ("Fix-pass re-review, round 2"). Plan: `docs/superpowers/plans/2026-10-22-revision-build.md`; design: `docs/superpowers/specs/2026-10-22-revision-program-design.md`.

- H1 (`scripts/benchmark_v2.py`: `n_bank`, `bank`): the stand-in bank has as many distinct projected points per family as the effective manifest's bank rules other than F111 (11); fewer is an error.
- H2, H3 (`scripts/benchmark_v2.py`: `measure`, `cost_table`, `REFERENCE_MENUS`): cells are search plus 40-seed evaluation; reference menus are priced once per (context, rule) in their own row; `eval160` prices each kind's further 160 seeds from its own evaluation.
- H4 (`scripts/revision_v2.py`: `derived_records`): valid envelope and bank records are reused, stale ones recomputed, foreign ones refused.
- H5 (`sim/intervals.py`: `_combine`): the equal-weight mean of equal stratum means is exact. Also added: `miss_counts(..., trace=)` and a per-replication parity test; Holm and Q4 refusal tests.

Known unrelated failures (sealed bundle opened on 2026-10-20; fixed on `main` in `4caa10b`, tests only): `test_h1_final_eval_namespace_refused_before_the_unseal`, `test_locked_loads_and_namespaces_are_disjoint`, `test_manifest_totals_follow_the_schedule`, `test_final_h3_cells_are_beta_headline_median_only`, `test_reference_records_carry_per_seed_values_and_foreign_rules_are_refused`. Do not report them.

Check with file:line evidence:
1. Your own round-2 findings: is each closed, with no narrower reading? Reproduce your round-2 probes where you can.
2. Each H test: would it fail against `05ca92b` (the round-2 review base) and against a plausible partial fix?
3. Regressions in anything closed in rounds 1 and 2, the plan's Review Focus items, the freeze order, and the development-only constraint.
4. The replacement ruling in the ledger (the cost unit and the reference row): accept or reject, with the reason.
5. The twelve frozen files are still byte-identical to `2a288f5`.

You run in a read-only sandbox: run pytest with `-p no:cacheprovider`; tests that write files may fail for that reason alone; say which you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of your round-2 findings, one line: closed | partly closed | open; then F1-F12, one line each.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
