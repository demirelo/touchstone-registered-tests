# Run B, searches to convergence on the flagged cells: plan (draft 1, 2026-11-10; for internal review; no spend)

**Why.** The Fable 5.2 review (problem 3): 21 of 98 doubling checks are flagged (`report.json` `doubling[...].incomplete`),
so several Q1, Q4, Q2, and Q3 statements hold only for the prescribed search procedure. This run continues the flagged
profit searches until the doubling check passes or a cap is reached, and reports how much the estimates move.

**Status.** Exploratory sensitivity, after the report. The frozen estimates and every registered decision stay primary.

## 1. Cells

The 21 flagged checks (`convergence_v2.flagged(report)`): 14 profit cells and 7 coalition cells.

- **Profit (this run):** fresh0 C* D2+H3; fresh1 C* and F111 D2+H3; fresh3 C* D2+H3; fresh4 F111 D2+H3 (these five feed Q1
  and Q4); headline F000, F001, F100, F101, F111 D2+H3 and F011, F100, F101, F111 X7-SC (Q2 and Q3, headline).
- **Coalition (not in this run):** headline C* X6-SE/v2 total c2_synchronised, c5_staggered, c5_synchronised; C* X8-DB min
  c2_roles; F111 X6-SE/v2 min c2_staggered, total c2_synchronised, c5_staggered. They are Q3-descriptive; repeated
  doubling of a minimum-member search needs the joint-reference rescoring of the frozen coalition stages, which this
  driver does not reimplement. They stay flagged in the paper. A separate plan can add them.

## 2. Stopping rule and estimand

- **Round k** (k = 1, 2, 3) continues the search from the best result so far with as many new restarts as registered
  (`revision_v2.continue_search`, the previous best as incumbent, the merged archive), with restart seeds after every
  earlier round's (`round_seed(k) = 1 + (k - 1) R`; CMA seeds never repeat, tested). It then reselects the reference from
  the frozen menu plus the round's candidates, as the registered doubling stage does.
- **Pass.** A round passes when both changes against the previous round, the attacker's best training value and the
  reselected reference's mean normalised profit, are below the registered threshold 0.005 (the registered flag rule).
  Stop at the first passing round. **Cap:** three rounds, four times the registered restarts in all. A cell that does
  not pass is reported "not passed at the cap".
- **Round 1** recomputes the registered doubling check; its two changes are compared with the report's at 1e-9 (a
  built-in reproduction check; a disagreement is reported, not hidden).
- **Winner.** The best training value over all rounds, evaluated on the 200 evaluation seeds against the unchanged frozen
  reference (`gain_fields`, as the registered held-out diagnostic). The reselected references are diagnostics only.

## 3. Analysis (fixed now)

Per cell: the frozen gain, the final winner's gain, the rounds and their changes, the status. Q1 (C* - R3, D2+H3) and Q4
(B3 - R3, D2+H3) per fresh market and pooled, with the final winners substituted for the re-searched cells and the frozen
winners elsewhere (`recompute`), beside the frozen values; nominal paired percentile bootstrap (9,999 resamples, seed 0).
Descriptive; no decision is recomputed.

## 4. Expectations (written before any result)

None on direction. We report how many of the 14 cells pass within the cap and the largest change of a Q1 or Q4 market
difference.

## 5. Execution contract

`docs/revision/followup2/convergence_v2.py` (under `docs/`, code freeze). Preflight before any episode: salt, commit,
runner and `sim/` equal to protocol-v2, configuration hashes (fresh: recorded container hashes; headline: the registered
record's), pairing of each job with its frozen reference. Inputs copied and checked against the original freeze (the
cell's search record, its reference, the menu and bank records). Cells run in parallel, one process each; records in
`convergence/`, then `recompute.json` and an inventory with the environment. Validation before spend: the smoke-size
end-to-end test for fresh1 F111 D2+H3 with two rounds passes (`uv run pytest -q docs/revision/followup2`).

## 6. Cost

`python3 docs/revision/followup2/cost_estimate.py`: up to 16.88 core-hours, 1.82 USD at 0.108 USD per core-hour (14 cells,
3 rounds each, priced as registered doubling checks with held-out evaluation); on one 16-vCPU pod with 14 workers the
critical path is an X7-SC cell's three rounds, 2.14 hours, 1.20 USD at 0.56 USD per hour, 1.37 USD with 0.3 hours of
preparation and tail. The plan uses 1.82 USD.

## 7. Steps

1. Internal review to consensus; freeze the plan.
2. The author records the spend approval.
3. One pod: `convergence_v2.py --workers 14`; delete and verify; record the spend.
4. Analysis on the Mac; a paper sentence and table, exploratory, after review.
