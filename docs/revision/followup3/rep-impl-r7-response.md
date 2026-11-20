# Replication implementation review r7: response ledger

Reviews: `docs/revision/roster/{sol,astra}-rep-impl-r7.md` (both reject; the findings agree). Plan of record:
`replication-plan.md` (unchanged). The new tests were run on commit 3a7bde1 before the fix: the 6 defect cases failed;
4 positive cases (a genuine Run B mismatch record, an infinite gain difference, NaN, a truly foreign provenance) already
passed and stay as guards. Round 6's items L1 and L5 were incomplete; their completions are M1 to M5.

| # | Correction (Sol #, Astra #) | Plan text | Status |
|---|---|---|---|
| M1 | A mismatch needs measured evidence: Run B's mismatch status counts only with its well-formed failing comparison; the status alone (or with an empty comparison or no rounds) is an invalid record, rerun on resume and not continued in the analysis, and `cont_problem` refuses it (S1, A1) | s4: mismatch "round 1 differs from this run's doubling record" | fixed in `rep_collect._mismatch`, `cont_problem`: test_a_mismatch_status_without_measured_evidence_is_an_invalid_record (failed first); test_a_genuine_run_b_mismatch_record_is_still_a_mismatch keeps the real case; three older tests now use the record run_cell writes (status plus failing comparison) |
| M2 | Comparison differences too large for a float are malformed, not errors; Run B's infinite gain difference stays allowed (S2, A3) | | fixed in `_gate_wellformed`: test_comparison_differences_too_large_for_a_float_are_malformed_not_errors (10**400 failed first) |
| M3 | Both doubling changes must be finite numbers before any disagreement counts; a malformed doubling change makes the cell unscorable with no mismatch (S4, A2) | s4: "missing or invalid is unscorable" | fixed in `_round1_ready`: test_a_malformed_doubling_change_is_not_a_mismatch (failed first) |
| M4 | A provenance refuses the resume only if it is well-formed (the job's own fields, each of the same JSON type and not empty) and names another job or run; {}, an id of None or [] is a malformed record, rerun (S3, A4) | s5: "reuse only this run's records" | fixed in `_prov_wellformed`, `_foreign`, `run_queue`: test_only_a_well_formed_foreign_provenance_refuses_the_resume (3 malformed cases failed first; the foreign case passes) |
| M5 | The guard asserts exact outcomes everywhere: doubling and evaluation damage gives an unscorable cell and no mismatch; on resume the rerun restores a valid record and the exit must be exactly 0 (or 4 with no rerun for a measured mismatch, or the refusal for a well-formed foreign provenance, by the same `_foreign` rule); queue construction must return exactly the flagged cell when `incomplete` is true and none otherwise. Completion claims of r6 corrected; ruling 10 amended (S3, S4, A5) | | test_every_mutation_of_every_record_kind_is_handled, test_queue_construction_survives_every_mutation_of_a_doubling_record; done in `rep-impl-r6-response.md`, `rep-launcher-notes.md` |

Checks: `uv run --frozen pytest -q docs/revision/followup3/` (183 pass). Launcher and harness unchanged (sha256 equal to
the 47 of 47 log header). The round-3 smoke records re-collected: 72 of 72 scorable, 0 problems, audit counts for all
18 R3 cells. All 76 Run B records with an identical round 1 pass every check and are not mismatches.
