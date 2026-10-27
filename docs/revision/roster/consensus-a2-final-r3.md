# Part A2 whole-branch review: consensus (round 3, 2026-10-27)

Seats: Sol high (gpt-6.1-sol) and Astra high (gpt-6-astra), read-only, through `run_seat.sh`.

| Round | Sol | Astra | Outcome |
|---|---|---|---|
| 1 (`brief-a2-final-r1.md`) | request-changes (6 Important, 1 Minor) | request-changes (6 Important) | 7 distinct findings, all graded Important by effect; fixed with tests that failed first (ab47d9c, ece90d0, 1478c9a) |
| 2 (`brief-a2-final-r2.md`) | request-changes (1 Important) | request-changes (1 Important) | shared finding: the freeze bank matrix priced 8 times too high; fixed (cb85609) |
| 3 (`brief-a2-final-r3.md`) | approve-with-caveat | approve-with-caveat | consensus |

Both seats confirmed each fix on the real path; each new or corrected test fails against the code before its fix.

Caveat (both seats, set aside by both): the core-hour helper in `scripts/benchmark_v2.cost_table` (the `usd_per_core_hour` path) does not scale the extra 160 evaluation seeds of H4 cells by the H4 timing ratio. The registered decisions (`choose`, `choose_after_h4`) use pod billing, which applies the ratio, so no operations decision changes. Recorded in the ledger as a ruling.

Before the review, the executor found and fixed two suite failures: Task 8 had changed the frozen `sim/cell.py` (restored; `gain_fields` keeps the episodes another way), and a stale draft-6 assertion in `test_k8_real_verify_behind_the_report`.
