# Replication implementation review r8: response ledger

Reviews: `docs/revision/roster/{sol,astra}-rep-impl-r8.md` (both reject on one shared finding). Plan of record:
`replication-plan.md` (unchanged). Round 7's item M1 was incomplete; its completion is N1.

| # | Correction (Sol #, Astra #) | Plan text | Status |
|---|---|---|---|
| N1 | No status shortcut: with a well-formed comparison, a mismatch is a failing comparison or a well-formed measured round-1 disagreement, whatever the status says; a mismatch status is a valid record only with that evidence (S1, A1) | s4: a round-1 mismatch "stops all continuation, no continued winner of this run enters any result, and the primary analysis is reported as not available" | fixed in `rep_collect._mismatch`, `cont_problem`: test_a_measured_disagreement_is_a_mismatch_whatever_the_status (the mismatch-status case failed first on 761e77c, collection and resume) |
| N2 | Guard against the class: every status times every kind of well-formed round-1 disagreement (both changes, round 1's best knobs, the comparison's knobs and mean) must remove the primary set and stop the resume with exit 4 and no rerun | | test_every_status_with_every_well_formed_round1_disagreement_is_a_mismatch (20 cases) |
| N3 | Completion claims: r7 item M1 marked incomplete and completed here; ruling 10 states the evidence rule regardless of status | | done in `rep-impl-r7-response.md`, `rep-launcher-notes.md` |

Checks: `uv run --frozen pytest -q docs/revision/followup3/` (205 pass). Launcher and harness unchanged. The round-3
smoke records re-collected: 72 of 72 scorable, 0 problems, audit counts for all 18 R3 cells. All 76 Run B records with
an identical round 1 pass every check and are not mismatches.
