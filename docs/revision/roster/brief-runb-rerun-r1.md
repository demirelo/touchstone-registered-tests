# Run B rerun: per-cell saves, worker count, restart, verify on every end state; internal review round 1 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 400 words)

Run B (convergence, 19 cells) failed on pod ts-f2b: one worker was killed with signal 9 after 3.6 h, and
`convergence_v2.py` lost every cell because it wrote results only after `list(ex.map(...))` returned. Cause: out of
memory. A Mac probe measured a peak of 2.39 GB per cell (16 workers about 38 GB, pod 29 GB). The author chose "fix and
rerun" with a new cap of 5 USD.

Files (the change is commit f1a8f8a: `git show f1a8f8a`):
- Driver `docs/revision/followup2/convergence_v2.py`: `run_cells` saves each cell when it ends (serial and pool paths);
  a `BrokenProcessPool` loses only unfinished cells; `main` writes `lost_cells.json` and returns 5. Saved cells are
  skipped on the next call (existing skip of cells whose record exists).
- Tests `test_convergence_v2.py`: a worker killed with `os.kill(getpid(), 9)`; the serial path; a restart through
  `main()` (exit 5, then 0, the second call runs only the lost cell). `pytest docs/revision/followup2/`: 103 pass.
- Launcher `followup2_pod.sh` and harness `test_followup2_pod_harness.sh` (installed copies in
  `/Users/oemer.demirel/Projects/touchstone/results/pods/`, identical): `CONVWORKERS` default 7 (refused outside 1 to
  16), one restart with 3 workers on exit 5, a second 5 ends "RUN FAILED"; run tag `convergence2`, cap 5.00; pulled
  records are verified on every end state, not only RUN OK. Red log (new harness, old launcher):
  `results/pods/logs_harness/f2_harness_red.log`; green log: `results/pods/logs_harness/f2_harness_green.log`.
- Plan `convergence-plan.md`: "Rerun amendment (2026-11-14)": cause, fix, memory, cost (worst case 6.4 h, 3.6 USD
  billed rate, 4.5 USD ceiling; admission 5.10 h and 2.60 h; reservation `convergence2-1` 6.50).
- Lessons `docs/revision/lessons.md` (last three entries).

Check: (1) no finished cell can be lost by a killed worker, and a restart cannot re-run or overwrite a saved cell or mix
records across the two runs; (2) 7 workers is safe on a 28 GB pod and the restart path is bounded in time and cost; (3)
the launcher keeps every reviewed safety behaviour (cost stop, admission, watchdog, ledger, verify) and the new tag
cannot hide the failed run's 3.43 USD from the follow-up total; (4) the plan amendment changes nothing in the analysis;
(5) defects the tests miss.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
