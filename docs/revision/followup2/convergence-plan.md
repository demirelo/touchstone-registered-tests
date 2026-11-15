# Run B, continued searches on the flagged and nesting cells: plan (draft 7, 2026-11-11; for internal review; no spend)

**Amendment (2026-11-13, shared launcher review r1, `docs/revision/roster/{sol,astra}-f2-launcher-r1.md`):** reservation input 4.42 (grant 5.525 USD = 1.3 x the 4.25 USD stop cap, which is unchanged); the follow-up category cap is 72 USD (the author's approval of 2026-11-12); the reservation covers the watchdog bound, 1.3 x the stop cap, because a stage admitted within the cap finishes and only the watchdog at 1.3 x the cap stops a running stage (churn launcher review r1, Sol and Astra); `guards.check_grant` against the stop cap is replaced by the launcher's check that one `followup` reservation tagged with this launch covers 1.3 x the stop cap minus the run's recorded spend. The launcher is `docs/revision/followup2/followup2_pod.sh`.

**Rerun amendment (2026-11-14; the author's board answer "Fix and rerun", card `touchstone-runb-rerun`).** The first Run B
(pod 9mjos5t359bfcs, launch tag `convergence-1`) passed its gate, then lost every convergence result after 3.6 h: one of 16
workers was killed with signal 9, most likely out of memory, and the driver wrote results only after every cell ended. Its
spend is recorded under `convergence-1` after the author's billing check; nothing from it enters the analysis; the rerun
runs its own gate on its own pod. Changes, all tested before any spend:
- Driver (`convergence_v2.run_cells`, after internal review r1, both reject): each cell runs in a worker process (also
  with one worker or one cell, so a kill cannot take the driver) and the worker writes its record (atomic) before
  anything returns to the parent, so another worker's death cannot discard a finished result in transit. A broken pool,
  at submission or later, is a lost worker; the records on disk, not the pool, say which cells are saved
  (`guards.reusable`). Lost cells go to `lost_cells.json` with the driver's restart estimate for 1 to 16 workers
  (`restart_hours`: the lost cells' worst-case hours, longest first onto the least-loaded worker, plus 0.1 h), and the
  driver exits 5; a saved round-1 mismatch outranks a lost worker (exit 4, no restart). Tests: a real worker killed with
  signal 9 loses only its own cell; a sibling that dies the moment a record is on disk; one worker; a broken pool at
  submission; through `main()`, exit 5 then a restart that runs only the lost cell; a mismatch with a lost worker
  returns 4; the restart schedule. An ordinary exception in a cell is not a lost worker (review r2): the driver reads
  every future, writes `cell_errors.json` with each message and the inventory, and exits 6, which the launcher reports
  as "RUN FAILED at convergence" with no restart (a mismatch still outranks it, exit 4).
- Worker count: one X7-SC cell (round 1 and its evaluations, `--gate --site mac`) peaked at 2.39 GB resident on the Mac
  (15 s sampling). The full three-round cell, sampled every 2 s, peaked at 3.53 GB (3534160 kB, round 3; the cell passed
  all three rounds against the Mac reference; `results/pods/memprobe3/rss.log`), so `PEAKGB` = 3.54. The launcher refuses a worker
  count for which workers x PEAKGB x 1.25 + 2 GB (the driver) exceeds the 28 GB minimum pod memory: 6 workers need
  28.6 GB and are refused. The fit is an estimate: 5 workers need about 24.1 GB, a margin of 3.9 GB below 28 GB, and
  the Mac probe does not establish the Linux peak or memory kept across successive cells in a long-lived worker; a
  worker lost to memory is the exit-5 path below. Workers = 5; on exit 5 the launcher admits the restart with the driver's estimate for 3
  workers and restarts once; a second exit 5 ends the run ("RUN FAILED ... a worker lost twice"). An early loss can leave
  most cells: then the restart's admission (12.65 h for all 19 cells on 3 workers) exceeds the cap and the run stops
  with the saved cells kept ("STOPPED BEFORE convergence restart"); the watchdog bounds spend, not completion.
- Launcher: every directory that arrived is verified on every end state, also after a failed or partial pull of it or
  of another directory (lessons.md), and also when the hard deadline leaves no time to pull (review r2); retried only
  after RUN OK. The rerun is refused until the first Run B's spend is
  recorded under `convergence-` and its reservation is closed, so the follow-up total holds both runs.
- Cost: run tag `convergence2`, stop cap **7 USD** (the author raised it from 5 on 2026-11-15, after the three-round
  probe), watchdog bound 9.10 USD, reservation `convergence2-1` 9.10 USD. Normal run (no lost worker; three rounds for
  every cell, 5 workers, benchmark timings, the driver's longest-first schedule): 7.65 h of convergence + 1.06 h gate +
  0.3 h preparation = 9.0 h, 5.0 USD at 0.56 USD/h and 6.3 USD at the 0.70 ceiling; the convergence step is admitted at
  7.70 h. A restart is admitted at the driver's estimate for the lost cells, within the
  same cap. A cell refused by the cap keeps its frozen estimate, as before. The 7 USD cap governs admission (no step
  starts unless its estimate fits); it is not a ceiling on the bill. The spend bound is the watchdog's hard deadline,
  1.3 x 7 USD = 9.10 USD at the 0.70 USD/h ceiling (13 h), plus any delay in a verified deletion. Completion after a lost
  worker is not guaranteed. Before launch the ledger must be reconciled: the first Run B's spend recorded under
  `convergence-1`, its reservation closed, and `convergence2-1` reserved at 9.10 USD (the launcher refuses otherwise).

**Draft 7 changes** (internal review round 6, `docs/revision/roster/{sol,astra}-convergence-plan-r6.md`, both reject): paid accounting counts the current pod from its recorded open event, never from a later `--started-at`
(refusal test); the ledger must have a `spent` list of rows with a tag and a finite, nonnegative amount, and the cap,
rate, and step estimate must be finite and valid (refusal tests); the reservation command is `budget_followup.py
--reserve`, and its returned grant must equal the stop cap (`guards.check_grant`);
the Mac gate is rerun under this code.

**Draft 6 changes** (internal review round 5, `docs/revision/roster/{sol,astra}-convergence-plan-r5.md`, both reject): attempt records are validated strictly (finite, ordered epochs; exactly one open attempt, the current pod; an
allocation time between that attempt's start and now; refusal tests); a launcher calls `guards.py admit` before every
paid step, including the reset reproduction gate, with the same cap, attempts, ledger, and run tag, so earlier spend
is counted before any paid work; the exact reservation is `budget_followup.py --reserve <tag> 3.40`, whose grant
(3.40 x 1.25) equals the 4.25 USD stop cap (`guards.reservation_input`); obsolete attempts references removed;
the Mac gate is rerun under this code.

**Draft 5 changes** (internal review round 4, `docs/revision/roster/{sol,astra}-convergence-plan-r4.md`, both reject): the attempts handoff follows the launcher's real event format and the ledger carries earlier launches; the STOP file
and soft deadline are checked before each round and gate cell; the Mac gate is rerun under this final code.

**Draft 4 changes** (internal review round 3, `docs/revision/roster/{sol,astra}-convergence-plan-r3.md`, both reject):
gate evidence must carry exactly the expected binding (full-budget provenance, gate settings, input hashes, driver, and
dependencies) and, for the pod, the same numerical stack (SciPy, CMA, BLAS and LAPACK included); result and gate bindings
include the hashes of the helper, `guards.py`, `common.py`, this plan, the report, the posthoc file, the cell's registered
doubling record, and the embedded doubled D2+H3 incumbent (a changed incumbent changes the binding; test); a pass counts
only from the minimum round and only with a "passed" outcome, and `--max-rounds 1` is refused for a continuation run with
nesting cells; a cost-stopped cell keeps its frozen estimate as primary and its partial result goes to a separate field
(`partial`), never substituted; failed-attempt spend comes from the launcher's attempts file (required); the launcher's
stop rule is stated; the Mac gate is rerun under the final code.

**Draft 3 changes.** (1) Scope (Fable 5.2 r2, new problem 2; `docs/revision/posthoc/posthoc.json` `nesting`): the X7-SC
cells whose evaluated gain falls short of the better of the frozen and doubled D2+H3 winners by at least 0.005 join the
run: fresh0 C* (0.0061), fresh1 F111 (0.0059), fresh1 C* (0.0084), fresh3 C* (0.0199), fresh4 F111 (0.0053), headline F111
(0.0211, already flagged); 19 cells. From round 2 a nesting cell's continued X7-SC search also starts from the doubled
D2+H3 winner embedded in X7-SC (a deviation), and such a cell runs at least two rounds; each cell's shortfall is reported
before and after. (2) Internal review round 2 (`docs/revision/roster/{sol,astra}-convergence-plan-r2.md`, both reject):
the Mac gate compares round 1 with the frozen stage on the same machine and the pod gate with the registered record
(flagged cells diverge across platforms, measured); gate evidence bound to both gate cells, the Mac and this pod, full budget, input hashes, the driver, and the environment;
the analysis substitutes only this run's validated cells, with complete bindings, identities, finite values, and lengths;
cost admission before every gate cell and before every round, including a cell's first; a paid run requires the
allocation time and a positive rate and counts earlier failed attempts; the gate cells run serially and the estimate
follows; the cap is an admission limit, not a billing ceiling. Cost and cap updated (section 6).

**Draft 2 changes** (internal review round 1, `docs/revision/roster/{sol,astra}-convergence-plan-r1.md`, both reject):
the run is a capped search extension and the claim is bounded ("passed the registered incremental check within three
rounds", not convergence); pinned search settings and budgets; saved results reused only under the same binding;
round 1 compared with the registered doubling record before round 2, with a stop on mismatch, and a gate mode with saved
full-budget evidence for a headline X7-SC cell and a fresh D2+H3 cell; a run-specific inventory; per-market intervals and
the conditional scope of the intervals; headline Q2/Q3 contrasts deferred; a dollar cap, ledger reservation, and a stop
between rounds.

**Why.** The Fable 5.2 review (problem 3): 21 of 98 doubling checks are flagged (`report.json` `doubling[...].incomplete`).
Its round-2 review (new problem 2): X7-SC contains D2+H3, yet 11 of 21 X7-SC cells evaluate below the better D2+H3 winner
on the same seeds, 6 by at least 0.005. This run extends those searches and reports how much the estimates move.

**Scope.** Exploratory sensitivity after the report. The registered doubling outcomes are already known; the
expectations below precede only the new continuation outcomes. The frozen estimates and every registered decision stay
primary. Unchanged: unflagged cells, the frozen banks, X7-SC's original D2+H3 incumbents. Deferred: the 7 flagged
coalition cells (repeated doubling of a minimum-member search needs the joint-reference rescoring of the frozen coalition
stages), the fresh factorial cells without a doubling check (unresolved), and the headline Q2/Q3 contrasts.

## 1. Cells

`convergence_v2.cells_for(report, nesting)`: the 14 flagged profit cells (fresh, feeding Q1 and Q4: fresh0 C* D2+H3;
fresh1 C* and F111 D2+H3; fresh3 C* D2+H3; fresh4 F111 D2+H3; headline: F000, F001, F100, F101, F111 D2+H3; F011, F100,
F101, F111 X7-SC) and the 5 further nesting X7-SC cells (fresh0 C*, fresh1 F111, fresh1 C*, fresh3 C*, fresh4 F111): 10
D2+H3 and 9 X7-SC cells.

## 2. Rounds, stopping rule, and claim

- **Round k** (k = 1, 2, 3) adds R new restarts (R = the registered restarts) to the best result so far
  (`revision_v2.continue_search`, the previous best as incumbent, the merged archive), with CMA seeds after every earlier
  round's (`round_seed(k) = 1 + (k - 1) R`; tested never to repeat). Later rounds add R restarts each; they do not double
  the accumulated budget. The reference is then reselected from the frozen menu plus the round's candidates, as the
  registered doubling stage does (diagnostic only).
- **Round-1 gate.** Round 1 is the registered doubling check. Before round 2, its held-out winner (round 1's search
  winner, evaluated on the evaluation seeds against the frozen reference) and both changes are compared with the
  registered doubling record: exact seeds and discrete knobs, 1e-9 on continuous knobs, changes, and held-out gains, all
  values finite. On a mismatch the cell stops ("stopped: round 1 differs"), no recompute is written, and the run exits 4.
- **Nesting cells.** Round 1 is unchanged (the gate). From round 2 the round's incumbents add the doubled D2+H3 winner
  (the report's held-out knobs) embedded in X7-SC (`embed_h3`), and the cell runs at least two rounds. Its shortfall
  (better D2+H3 winner minus X7-SC evaluated gain, same seeds) is reported before (posthoc) and after (final winner).
- **Pass.** A round passes when both changes against the previous round (attacker best training value; reselected
  reference mean normalised profit) are below the registered threshold 0.005. Stop at the first pass; cap three rounds
  (four times the registered restarts in all). Reported as "passed the registered incremental check within three rounds"
  or "not passed at the cap"; this is not convergence, not optimality, and not a bound on the remaining search error.
- **Winner.** The best training value over all rounds, evaluated on the 200 evaluation seeds against the unchanged frozen
  reference.

## 3. Analysis (fixed now)

Per cell: the frozen and final gains, the rounds and their changes, the round-1 comparison, the status. Q1 (C* - R3,
D2+H3) and Q4 (B3 - R3, D2+H3), per fresh market and pooled, with the final winners substituted for the re-searched cells
and the frozen winners elsewhere, beside the frozen values (`recompute`; only validated full-run records with this run's
binding are substituted). Per market and pooled nominal paired percentile intervals (9,999 resamples, seed 0),
conditional on these six markets and the selected policies and references, without search or market-sampling
uncertainty and without registered calibration. Q1 under X7-SC is recomputed the same way. Only this run's cells enter, each with its complete binding, its identity,
finite gains, and the evaluation seeds' length; any other result in the directory is ignored. Descriptive; no decision
is recomputed.

## 4. Expectations (written before any continuation result)

None on direction. Reported: how many of the 19 cells pass within three rounds, each nesting cell's shortfall before and after, and the largest change of a Q1 or Q4
market difference.

## 5. Execution contract

`docs/revision/followup2/convergence_v2.py` (under `docs/`, code freeze). Before any episode: `TOUCHSTONE_LOCKED` refused,
`experiments/locked.yaml` and the manifest equal protocol-v2; salt, commit, runner and `sim/` equal to protocol-v2;
configuration hashes (fresh: recorded container hashes; headline: the registered record's); each job paired with its
frozen reference; each job's budget equal to its frozen search record's. Inputs copied and checked against the original
freeze. Each result binds to its input hashes, job provenance, smoke flag, stopping settings, and driver hash; a saved
result is reused only under the same binding and refused otherwise. Inventory: every output with its hash, Run B's
deviations, hashes of `convergence_v2.py`, `common.py`, `guards.py`, the imported helpers, this plan, and the report, the
run arguments, the environment. A full run is refused unless every `--evidence` file reports a pass.

**Gate evidence.** Measured on 2026-11-11 (Mac, full budget): round 1 of fresh1 F111 D2+H3 differs from the registered
pod record (held-out gains by up to 0.0204, changes by 0.0034), and the frozen doubling stage itself
(`reset_followup_v2.py --reproduce-doubling`, `results/v2/followup2-diag-dbl-fresh1`) differs from it by exactly the same
amounts; headline F111 X7-SC differs similarly (gains 0.0221). Round 1 therefore equals the frozen stage, and flagged
cells diverge between the Mac and the pods: a small arithmetic difference sends the doubled search elsewhere in these
rugged cells. The gate is split accordingly. `convergence_v2.py --gate --site mac --cells headline@rho0.2|F111|X7-SC|profit,
fresh1@rho0.2|F111|D2+H3|profit` on the Mac (free) compares round 1 with the frozen doubling stage run on the same machine
(the driver reproduces the frozen code); the same with `--site pod`, first on the pod, compares round 1 with the
registered record (the pod reproduces the registered run). Each writes `gate/<cell>__<site>.json` with the comparison,
round 1's own values, the binding (full-budget provenance, gate settings, input hashes, driver, dependency hashes), and
the environment. The main run is refused unless both cells have a passing Mac record and a passing pod record from this
machine's numerical stack, each with exactly the binding recomputed now. If
the pod gate fails, the run stops and is reported; the frozen estimates stay primary.

## 6. Cost and spending controls

`python3 docs/revision/followup2/cost_estimate.py`: up to 29.48 core-hours, 3.18 USD at 0.108 USD per core-hour (19 cells x
3 rounds priced as registered doubling checks plus a held-out evaluation each round); the gate cells run serially, 1.06
hours; billed path 3.60 hours (gate, an X7-SC cell's three rounds with 16 workers starting the 9 X7-SC cells first, 0.3 h
preparation and tail) = 2.01 USD at 0.56 USD per hour. Estimate 3.30 USD (x 1.25 = 4.12); **stop cap
4.25 USD**; **reservation 5.525 USD** (1.3 x the stop cap, the watchdog bound; amendment above) in ledger category `followup`
(cap 72 USD shared by all follow-up runs; `budget_followup.py reserve`). A paid run requires `--started-at <allocation time>`, a positive rate, and the launcher's attempts file
(`--attempts`). Admission is checked before each gate cell and before every round of every
cell, including its first, with the round's estimate plus its evaluation and a 0.1-hour shutdown allowance; a running round
is never killed (author's instruction). A cell refused admission, or stopped by it after a completed round, keeps its frozen estimate as primary and is
reported "stopped at the cost cap"; any partial result is kept under `partial` and never substituted; after the last running round finishes, the pod is deleted and verified. This is an admission limit, not a
billing ceiling.

**Launcher handoff (draft 5).** The launcher copy pushes to the pod, before every paid driver call, its current
`<name>.attempts` file and the ledger, and passes `--attempts`, `--ledger`, `--run-tag`, `--started-at` (the current pod's
allocation time), `--usd-per-hour` (the price ceiling MAXCPH), `--stop-file /root/STOP`, and `--soft-deadline` (its soft
deadline). The driver reads the launcher's own event lines (`<pod> <epoch> start`, `<pod> <epoch> deleted`;
`guards.attempts_spend`): each closed attempt counts at the ceiling, and the open start is the current pod, counted from
its recorded `start` event (a later `--started-at` cannot shorten it; it must lie between that event and now); malformed or unordered lines are refused (tests with lines in the launcher's exact format); spend of
earlier launches comes from the ledger rows tagged with the run tag, since the launcher truncates its file per launch. The
driver checks the STOP file and the soft deadline before each gate cell and before every round of every cell, so it
honours the launcher's between-stage stop without a mid-round stop (test).

**Admission before every paid step (draft 6).** Before the pod's first paid step, and before each later one (the reset
reproduction gate included), the launcher runs `python3 docs/revision/followup2/guards.py admit --cap-usd 4.25
--usd-per-hour <ceiling> --started-at <allocation> --attempts <file> --ledger <ledger> --run-tag convergence --hours <step estimate>
--stop-file /root/STOP --soft-deadline <soft>` and starts the step only on exit 0. Reservation: `python3 docs/revision/followup/budget_followup.py --reserve convergence-<n> 4.42`; the
launcher requires one `followup` reservation `convergence-<n>` (its launch tag) of at least 1.3 x the stop cap minus the run's
recorded spend (5.525 USD on a first launch; the ledger grants less when the category is nearly full), else no pod; the reservation covers the watchdog bound, 1.3 x the stop cap, because a stage admitted within the cap finishes and only the watchdog at 1.3 x the cap stops a running stage (churn launcher review r1, Sol and Astra); `guards.check_grant` against the stop cap is replaced by the launcher's check that one `followup` reservation tagged with this launch covers 1.3 x the stop cap minus the run's recorded spend. The launcher copy itself (a copy of `results/pods/reset_pod.sh`) is not part
of this folder and is to be written and tested offline before allocation.

**Launcher and the cap.** The pod launcher is a copy of `results/pods/reset_pod.sh` with `results/pods/podctl.py`. Its soft
deadline is the cap at the price ceiling MAXCPH, counted from the first creation request of the launch, so it holds across
attempts; at the soft deadline the remote script stops before its next stage (a STOP file read between stages), and the
driver's own admission check (`--cap-usd`, `--started-at`, `--attempts`) stops between stages or rounds as well. A running
stage is never stopped (the author: do not kill jobs). The single exception is the watchdog, which deletes the pod at 1.3 x
the cap at the price ceiling; that is the only mid-stage stop. Closed attempts are listed in the launcher's
`<name>.attempts` file (event lines `<pod> <epoch> start` and `<pod> <epoch> deleted`), which the driver reads
(`guards.attempts_spend`) and counts toward the
cap before each paid attempt; a paid run without it is refused (no default of zero); after the launch the spend is recorded
in the ledger (`budget_v2.py --record`).

## 7. Steps

1. Internal review to consensus; freeze the plan; save the Mac gate evidence.
2. Reserve 5.525 USD in the ledger (input 4.42); one pod: the gate with `--site pod`, then `convergence_v2.py --workers 16 --evidence
   <four gate records> --cap-usd 4.25 --started-at T --attempts A --ledger L --run-tag convergence --stop-file /root/STOP --soft-deadline S`; delete and verify; record the spend.
3. Analysis on the Mac; a paper sentence and table, exploratory, after review.
