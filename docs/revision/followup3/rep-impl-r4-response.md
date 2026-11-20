# Replication implementation review r4: response ledger

Reviews: `docs/revision/roster/{sol,astra}-rep-impl-r4.md` (both reject). Plan of record: `replication-plan.md`
(unchanged). Every new test below failed on commit a8d80b9 before the fix (run in this worktree before the code changed).
Round 3's items H1, H2, H4 and H8 were incomplete; their completions are J1 to J5.

| # | Correction (Sol #, Astra #) | Plan text | Status |
|---|---|---|---|
| J1 | The primary audit count comes from the primary winner's own diagnostics: a continued winner uses its checked continued diagnostics whether or not the frozen diagnostics pass; frozen counts enter the primary set only for a frozen winner (S1, A4) | s3: "primary winners; frozen winners reported beside" | fixed in `rep_collect.collect`: test_a_continued_winners_audit_count_does_not_need_the_frozen_diagnostics (failed first) |
| J2 | A measured round 1 must agree with this cell's own doubling record: the comparison's round-1 winner equals the doubling's held-out knobs, its held-out mean equals np.mean of the doubling's held-out gains, round 1's two changes equal the doubling's; `identical` also needs Run B's empty problems list. Applied to the gate, every continuation record, saved records before reuse, and continued diagnostics (A1) | s5 Gates: "required identical"; s4: round 1 "is checked against this run's doubling record" | fixed in `rep_collect._round1_problem`, `cont_problem(doubling=...)`, `identical`: test_the_round1_comparison_must_match_this_cells_doubling_record (2 cases, continuation and gate; failed first). On real data: all 76 Run B continuation records with an identical round 1 agree exactly with a registered doubling record under the new check |
| J3 | Wrong types are invalid, never errors: `_finite` accepts only lists of numbers (not booleans), seeds must be a list, and `base_problem` and `cont_problem` turn any remaining type error into a problem (base cell unscorable, continuation not continued or rerun) (A2) | s4: "missing or invalid is unscorable"; "missing or nonfinite, keeps its validated frozen winner" | fixed: test_scalar_values_where_lists_belong_are_invalid_not_errors (6 cases; failed first with TypeError) |
| J4 | An unknown saved status is set aside and rerun like any other invalid record; a measured round-1 mismatch still stops all continuation (A3) | s4: "a resume continues the same queue from the first cell without a passing record"; round-1 mismatch "stops all continuation" | fixed in `rep_collect.run_queue`; test_a_saved_continuation_record_with_an_unknown_status_is_not_reused now requires the rerun and the set-aside (failed first: SystemExit) |
| J5 | Guard against the class (record checks were incomplete in rounds 2, 3 and 4): every field of the continuation, gate, evaluation and doubling records, at every nesting level, replaced by each of seven wrong values; collect must never raise, and a damaged continuation never gives a continued winner. It found one more gap at once: `round1_gate.problems` was unread (now part of J2) | | test_no_malformed_record_field_raises_in_collect (4 record kinds) |
| J6 | Completion claims corrected: r3 items H1, H2, H4, H8 marked incomplete and completed here; rulings 8 and 10 amended (S1, A5) | | done in `rep-impl-r3-response.md` and `rep-launcher-notes.md` |

Checks: `uv run --frozen pytest -q docs/revision/followup3/` (141 pass). The launcher and harness are unchanged (sha256
equal to the 47 of 47 log header). The round-3 smoke records re-collected with this code: 72 of 72 scorable, 0 problems,
gate_ok, frozen and primary audit counts for all 18 R3 cells (smoke records carry "not compared" round-1 gates, so J2 is
covered there only by the Run B records above).
