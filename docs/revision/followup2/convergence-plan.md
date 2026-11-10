# Run B, continued searches on the flagged profit cells: plan (draft 2, 2026-11-10; for internal review; no spend)

**Draft 2 changes** (internal review round 1, `docs/revision/roster/{sol,astra}-convergence-plan-r1.md`, both reject):
the run is a capped search extension and the claim is bounded ("passed the registered incremental check within three
rounds", not convergence); pinned search settings and budgets; saved results reused only under the same binding;
round 1 compared with the registered doubling record before round 2, with a stop on mismatch, and a gate mode with saved
full-budget evidence for a headline X7-SC cell and a fresh D2+H3 cell; a run-specific inventory; per-market intervals and
the conditional scope of the intervals; headline Q2/Q3 contrasts deferred; a dollar cap, ledger reservation, and a stop
between rounds.

**Why.** The Fable 5.2 review (problem 3): 21 of 98 doubling checks are flagged (`report.json` `doubling[...].incomplete`).
This run extends the flagged profit searches and reports how much the estimates move.

**Scope.** Exploratory sensitivity after the report. The registered doubling outcomes are already known; the
expectations below precede only the new continuation outcomes. The frozen estimates and every registered decision stay
primary. Unchanged: unflagged cells, the frozen banks, X7-SC's original D2+H3 incumbents. Deferred: the 7 flagged
coalition cells (repeated doubling of a minimum-member search needs the joint-reference rescoring of the frozen coalition
stages), the fresh factorial cells without a doubling check (unresolved), and the headline Q2/Q3 contrasts.

## 1. Cells

`convergence_v2.flagged(report)`: 14 profit cells. Fresh, feeding Q1 and Q4: fresh0 C* D2+H3; fresh1 C* and F111 D2+H3;
fresh3 C* D2+H3; fresh4 F111 D2+H3. Headline: F000, F001, F100, F101, F111 D2+H3; F011, F100, F101, F111 X7-SC.

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
uncertainty and without registered calibration. Descriptive; no decision is recomputed.

## 4. Expectations (written before any continuation result)

None on direction. Reported: how many of the 14 cells pass within three rounds, and the largest change of a Q1 or Q4
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

**Gate evidence (free, on the Mac, before spend):** `convergence_v2.py --gate --cells headline@rho0.2|F111|X7-SC|profit,
fresh1@rho0.2|F111|D2+H3|profit` writes `gate/*.json`, which must pass. On the pod, the same gate runs first.

## 6. Cost and spending controls

`python3 docs/revision/followup2/cost_estimate.py`: up to 17.34 core-hours, 1.87 USD at 0.108 USD per core-hour (14 cells x
3 rounds priced as registered doubling checks, plus round-1 held-out evaluations); billed path 3.22 hours (gate 0.75 h,
an X7-SC cell's three rounds, 0.3 h preparation and tail) = 1.80 USD at 0.56 USD per hour. Estimate 1.99 USD;
reservation 2.48 USD (x 1.25) in ledger category `followup` (cap 22 USD shared; `budget_followup.py reserve`); **stop
cap 3.00 USD**, failed attempts counted. The cap is checked before the cells start and before each round of each cell;
a running round is never killed (author's instruction); a cell that meets the cap stops after its current round, is
evaluated, and is reported "stopped at the cost cap".

## 7. Steps

1. Internal review to consensus; freeze the plan; save the Mac gate evidence.
2. Reserve in the ledger; one pod: the gate, then `convergence_v2.py --workers 14 --evidence ... --cap-usd 3.00
   --started-at T`; delete and verify; record the spend.
3. Analysis on the Mac; a paper sentence and table, exploratory, after review.
