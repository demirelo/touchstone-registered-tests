# Run B rerun: internal review round 3 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

Round 2 (`sol-runb-rerun-r2.md`, `astra-runb-rerun-r2.md`, both reject) reviewed commit 4edb8fa. The fixes are in
commit 96c6d91 (`git diff 4edb8fa 96c6d91 -- docs/revision/followup2 docs/revision/lessons.md`). Installed launcher
and harness copies in `/Users/oemer.demirel/Projects/touchstone/results/pods/` are identical to the worktree files.

Round-2 corrections and their fixes (tests first; red evidence shows each new check failing on the old code):
1. Ordinary cell errors (Sol 2, Astra 1): `run_cells` reads every future and returns (lost, failed); an exception other
   than `BrokenProcessPool` is a failed cell with its message, never lost. `main` writes `cell_errors.json` and the
   inventory and exits 6 (the launcher reads it as "RUN FAILED at convergence", no restart); a mismatch still exits 4.
   Tests `test_an_ordinary_cell_error_is_reported_not_lost`, `test_a_cell_error_ends_the_run_without_a_restart`.
   Red: `results/pods/logs_harness/f2_pytest_red_r2.log` (the old `run_cells` returns the `ValueError` cell as lost).
2. Deadline exit (Sol 1): when the hard deadline leaves no time to pull, the loop still verifies each directory on
   disk. Harness scenario "a pull that hangs past the deadline still verifies the directory already on disk".
   Red: `results/pods/logs_harness/f2_harness_red5.log` (other failures there come from the ONLY filter, lessons.md).
3. Memory (Sol 3, Astra 4), cost (Sol 4, Astra 3), ledger (Astra 2): `convergence-plan.md`, rerun amendment, now states
   the fit is an estimate (24.1 GB, 3.9 GB margin, Linux and per-worker growth not established; a memory loss is the
   exit-5 path), that 7 USD governs admission and the spend bound is 9.10 USD plus deletion delay, that completion after
   a lost worker is not guaranteed, and that the ledger is reconciled before launch (spend `convergence-1` recorded, its
   reservation closed, `convergence2-1` reserved at 9.10). The real ledger is updated only after the author's billing
   check, before the dry run; the launcher refuses until then.

Evidence: `pytest docs/revision/followup2/` 109 passed, `results/pods/logs_harness/f2_pytest_r3.log`; green log `results/pods/logs_harness/f2_harness_green3.log`
HARNESS OK (47 of 47 scenarios). Lessons: last entry of `docs/revision/lessons.md`.

Check: (1) each round-2 correction is fixed and tested; (2) no round-1 fix or reviewed safety behaviour is lost;
(3) exit 6 and the deadline path are handled on the pod as stated; (4) the amendment changes nothing in the analysis;
(5) defects the tests miss.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
