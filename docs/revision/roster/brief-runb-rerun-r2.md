# Run B rerun: internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

Round 1 (`sol-runb-rerun-r1.md`, `astra-runb-rerun-r1.md`, both reject) reviewed commit f1a8f8a. The fixes are in
commit 4edb8fa (`git show 4edb8fa`; `git diff f1a8f8a 4edb8fa`). Installed launcher and harness copies in
`/Users/oemer.demirel/Projects/touchstone/results/pods/` are identical to the worktree files.

Round-1 corrections and their fixes (tests first; red logs show each new check failing on the old code):
1. Submission break (Sol 1, Astra 2): `run_cells` catches `BrokenProcessPool` at submission; the disk is the record of
   what is saved. Test `test_a_pool_broken_during_submission_is_a_lost_worker_not_a_crash`.
2. Save before transfer (Sol 2, Astra 1): each worker writes its bound record atomically (`_run_and_save`) before it
   returns. Tests `test_each_cell_is_saved_by_its_worker...`, `test_a_cell_that_ends_just_before_a_sibling_dies...`.
3. One worker (Sol 3): every cell runs in a pool process. Test `test_one_worker_still_runs_each_cell_in_its_own_process`.
4. Mismatch outranks loss (Astra 3): exit 4, with `lost_cells.json` and inventory. Test `test_a_round1_mismatch_outranks_a_lost_worker`.
5. Restart estimate (Sol 4, Astra 5): the driver writes `restart_hours` (longest-first schedule of the lost cells' three-round
   hours, per worker count) and the launcher admits the restart at the 3-worker value; no estimate ends the run.
   Harness `run=lostnoest`, `--hours 2.75`.
6. Memory (Sol 5, Astra 4): a full three-round X7-SC cell, 2 s sampling, peaked at 3.53 GB
   (`results/pods/memprobe3/rss.log`, driver exit 0, "passed", 3 rounds). PEAKGB 3.54; the launcher refuses
   workers x PEAKGB x 1.25 + 2 > 28 GB (6 workers refused). The author then chose 5 workers and a cap of 7 USD
   (worst case 9.0 h, 5.0 USD at 0.56 USD/h, 6.3 at 0.70; step 7.70 h; reservation `convergence2-1` 9.10).
7. Partial pulls (Sol 6, Astra 7): each arrived directory is verified after a failed or partial pull. Two harness scenarios.
8. First Run B's spend (Astra 6): the launch is refused until `convergence-` has a spend row and no open reservation.
   Two harness scenarios; the default harness ledger holds `convergence-1` 3.43.

Evidence: `pytest docs/revision/followup2/` (107 passed, `results/pods/logs_harness/f2_pytest_r2.log`); red logs `results/pods/logs_harness/f2_harness_red2.log`,
`red3.log`, `red4.log` (remote-check failures in red2 come from the ONLY filter, see lessons.md); green log
`results/pods/logs_harness/f2_harness_green2.log` ("HARNESS OK (46 of 46 scenarios)"). Plan: `convergence-plan.md`, rerun amendment. Lessons: last
three entries of `docs/revision/lessons.md`.

Check: (1) each round-1 correction is fixed and tested; (2) 5 workers fit 28 GB with margin, and Linux memory may differ
from the Mac figure; (3) the run and the restart are bounded in time and cost under the 7 USD cap; (4) no reviewed
safety behaviour is lost; (5) the amendment changes nothing in the analysis; (6) defects the tests miss.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
