# Re-review of the revision-build fix pass, round 2 (read-only; no paid APIs; do not read `sealed/`; reasoning effort high; under 1,000 words)

You are run at the tip of the review branch. Round 1 (`docs/revision/roster/sol-build-fix-r1.md`, `docs/revision/roster/astra-build-fix-r1.md`) found F4, F8, F9, and F11 partly closed. The executor merged both seats' findings into G1-G8 and fixed them in `109e597..HEAD`; the triage, the commits, the tests, and three new rulings are at the end of `docs/revision/build-ledger-2026-10-22.md` ("Fix-pass re-review, round 1"). Plan: `docs/superpowers/plans/2026-10-22-revision-build.md`; design: `docs/superpowers/specs/2026-10-22-revision-program-design.md`.

- G1-G3 (`scripts/revision_v2.py`: `reusable`, `cross_expected`, `stage_upstream`, `coalition_prereqs`, `run`): one resume rule for every record; cross and doubling bound to the accepted freeze and their full inputs.
- G4-G5 (`sim/intervals.py`, `sim/calibration_v2.py`, `sim/decisions_v2.py`): nonfinite and short inputs refused; one exact constant-sample rule; calibration equal to production replication by replication.
- G6-G7 (`scripts/benchmark_v2.py`): components measured in dependency order and composed into the cost-table kinds; `--smoke` runs the real default wiring.
- G8 (`tests/test_credibility.py`): the equal-count residual case.

Known unrelated failures (sealed bundle opened on 2026-10-20; fixed on `main` in `4caa10b`, tests only): `test_h1_final_eval_namespace_refused_before_the_unseal`, `test_locked_loads_and_namespaces_are_disjoint`, `test_manifest_totals_follow_the_schedule`, `test_final_h3_cells_are_beta_headline_median_only`, `test_reference_records_carry_per_seed_values_and_foreign_rules_are_refused`. Do not report them.

Check with file:line evidence:
1. Your own round-1 findings: is each closed, with no narrower reading? Reproduce your round-1 probes where you can.
2. For each G test: would it fail against `109e597` and against a plausible partial fix?
3. Regressions in F1-F12 (closed in round 1), the plan's Review Focus items, the freeze order, and the development-only constraint; in particular, does the stricter resume rule (refuse any record with another provenance) block a legitimate path the design or plan requires?
4. The three new rulings in the ledger: accept or reject, with the reason.
5. The twelve frozen files are still byte-identical to `2a288f5`.

You run in a read-only sandbox: run pytest with `-p no:cacheprovider`; tests that write files may fail for that reason alone; say which you could not run.

Output exactly:
VERDICT: approve | approve-with-caveat | request-changes
FINDINGS: numbered, each with severity (Critical, Important, Minor), file:line, failure scenario, repair. Then, for each of your round-1 findings, one line: closed | partly closed | open.
DECLINED TO JUDGE: anything you set aside.
CONFIDENCE: 0 to 1.
