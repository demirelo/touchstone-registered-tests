# Run B, continued searches on the flagged and nesting cells: plan (draft 3, 2026-11-10; for internal review; no spend)

**Draft 3 changes.** (1) Scope (Fable 5.2 r2, new problem 2; `docs/revision/posthoc/posthoc.json` `nesting`): the X7-SC
cells whose evaluated gain falls short of the better of the frozen and doubled D2+H3 winners by at least 0.005 join the
run: fresh0 C* (0.0061), fresh1 F111 (0.0059), fresh1 C* (0.0084), fresh3 C* (0.0199), fresh4 F111 (0.0053), headline F111
(0.0211, already flagged); 19 cells. From round 2 a nesting cell's continued X7-SC search also starts from the doubled
D2+H3 winner embedded in X7-SC (a deviation), and such a cell runs at least two rounds; each cell's shortfall is reported
before and after. (2) Internal review round 2 (`docs/revision/roster/{sol,astra}-convergence-plan-r2.md`, both reject):
gate evidence bound to both gate cells, the Mac and this pod, full budget, input hashes, the driver, and the environment;
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

**Gate evidence.** `convergence_v2.py --gate --site mac --cells headline@rho0.2|F111|X7-SC|profit,fresh1@rho0.2|F111|D2+H3|profit`
on the Mac (free), then the same with `--site pod` first on the pod; each writes `gate/<cell>__<site>.json` with the
comparison, the binding (full budget, the cell's input hashes, the driver hash), and the environment. The main run is
refused unless both cells have a passing Mac record and a passing pod record from this machine's environment.

## 6. Cost and spending controls

`python3 docs/revision/followup2/cost_estimate.py`: up to 29.48 core-hours, 3.18 USD at 0.108 USD per core-hour (19 cells x
3 rounds priced as registered doubling checks plus a held-out evaluation each round); the gate cells run serially, 1.06
hours; billed path 3.60 hours (gate, an X7-SC cell's three rounds with 16 workers starting the 9 X7-SC cells first, 0.3 h
preparation and tail) = 2.01 USD at 0.56 USD per hour. Estimate 3.30 USD (x 1.25 = 4.12); **stop cap and reservation
4.25 USD** in ledger category `followup` (cap 22 USD shared: reset 5, churn 8, Run A 3, Run B 4.25, total 20.25;
`budget_followup.py reserve`). A paid run requires `--started-at <allocation time>` and a positive rate, and counts
earlier failed attempts (`--prior-spend-usd`). Admission is checked before each gate cell and before every round of every
cell, including its first, with the round's estimate plus its evaluation and a 0.1-hour shutdown allowance; a running round
is never killed (author's instruction). A cell refused admission keeps its frozen estimate and is reported "stopped at the
cost cap"; after the last running round finishes, the pod is deleted and verified. This is an admission limit, not a
billing ceiling.

## 7. Steps

1. Internal review to consensus; freeze the plan; save the Mac gate evidence.
2. Reserve 4.25 USD in the ledger; one pod: the gate with `--site pod`, then `convergence_v2.py --workers 16 --evidence
   <four gate records> --cap-usd 4.25 --started-at T`; delete and verify; record the spend.
3. Analysis on the Mac; a paper sentence and table, exploratory, after review.
