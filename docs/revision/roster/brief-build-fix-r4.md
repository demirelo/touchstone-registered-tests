# Re-review of the revision-build fix pass, round 4 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 600 words)

You are run at the tip of the review branch. Round 3 (`docs/revision/roster/sol-build-fix-r3.md`, `docs/revision/roster/astra-build-fix-r3.md`) closed every round-2 finding and left one shared item, the development reference cost (F11 partly closed), plus test-strength notes. Both are fixed in commit `a1f4ed7` (I1, I2); the triage and the replacement ruling are at the end of `docs/revision/build-ledger-2026-10-22.md` ("Fix-pass re-review, round 3").

- I1 (`scripts/benchmark_v2.py`: `CONFIG_MARKETS`, `dev_inner_config`, `measure`, `cost_table`): 231 inner configuration-markets measured whole through `scripts/tune_v2.py::score_config`; 30 rechecks composed of two D2+H3-cost searches, an X7-SC search, a reference menu, and three 20-seed evaluations (an upper bound).
- I2 (tests): trace completeness, each evaluation component, reference effects on USD totals, envelope mutations, constants over values and stratum sizes.

Known unrelated failures (sealed bundle opened on 2026-10-20; fixed on `main` in `4caa10b`, tests only): `test_h1_final_eval_namespace_refused_before_the_unseal`, `test_locked_loads_and_namespaces_are_disjoint`, `test_manifest_totals_follow_the_schedule`, `test_final_h3_cells_are_beta_headline_median_only`, `test_reference_records_carry_per_seed_values_and_foreign_rules_are_refused`. Do not report them.

Check with file:line evidence:
1. Your round-3 findings: closed, with no narrower reading? Reproduce your round-3 probes where you can.
2. The I1 test against `1689253~2` (`441fc48`) and a plausible partial fix.
3. Regressions in anything closed in rounds 1 to 3, the Review Focus items, the freeze order, and the development-only constraint (does `dev_inner_config` touch any reserved seed?).
4. The replacement ruling in the ledger: accept or reject, with the reason.
5. The twelve frozen files are still byte-identical to `2a288f5`.

Read-only sandbox: run pytest with `-p no:cacheprovider`; say which tests you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of your round-3 findings, one line: closed | partly closed | open; then F1-F12, one line each.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
