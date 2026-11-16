# Churn replication on new markets: plan (draft 1, 2026-11-16; for internal review; no spend)

**Why.** Two external reviews of draft 10 (`docs/revision/roster/astra-pro-paper-d10-ext.md`, `-ext2.md`; WEIS 3/5 upper
borderline) found the churn result reproducible but narrow: one market neighbourhood, one verified-history comparator
under churn, and searches with 21 of 72 cells flagged. Their top recommendation: a churn validation fixed before the
outcomes, on newly drawn markets, with the runner-up comparator and stronger search checks. The author chose on
2026-11-16 (card `touchstone-churn-replication`): "Plan it now (no spend)". Nothing runs before internal consensus and a
separate spend card.

**Status.** Draft 1. A prospective follow-up: this plan, its expectations and its analysis code are committed and stamped
before the block that draws the markets exists. It is still outside the registered protocol v2 and changes no registered
decision. It is the first churn result in this project whose markets were unknown when its expectations were written.

## 1. Design

- **Markets.** Six new markets from the protocol-v2 generator (`sim/instances.py`), seeded by a new block: this plan file
  is stamped with OpenTimestamps; A is the proof's earliest attestation; the draw block is H = A + 144, read with
  `scripts/block_draw.py --protocol <this file>`; `scripts/draw_v2.py --instances` derives the instances and 200
  evaluation seeds per market from the block root. The generator labels them `fresh0` to `fresh5`; in this plan and the
  paper they are `rep0` to `rep5`, and every run writes into its own output directory (no record shares a directory
  with the registered `fresh*` records). The headline market is not used.
- **Calibration.** The instances are calibrated once, on the pod's Linux x86 stack, by a wrapper that calls the frozen
  calibration; the configurations and their hashes are saved before any search and passed as `cfg=` to every job. No
  later stage recalibrates (lesson 2026-11-04, the 1-ulp deviation).
- **Rules.** R3 (`F111`), C* (C-mem(6, 20)), the runner-up C-thr(12) (as in Run A), and B3 (`F000`), at the registered
  budget, sanctions and parameters (rho = 0.2).
- **Rates.** p = 0, 0.03, 0.05: no churn, and the two rates at which draft 10 found a deterioration on every market under
  both search versions. Mean identity lifetimes 33 and 20 rounds.
- **Attacker family.** D2+H3 only, with the registered search budget and seeds. X7-SC is searched only as part of the
  reference menus (below).
- **References.** Faithful to the registered procedure: each rule's truthful reference is selected from its menu (its
  own D2+H3 and X7-SC winners plus the winners of the nine bank rules in both families, cuts 3) by the frozen
  `_run_reference`; C-thr(12) uses its own searches and a copy of the bank, as Run A did. The frozen candidates are
  replayed under churn (as in the churn arm); the menus are not regenerated under churn.

## 2. Estimands and primary analysis (fixed now)

- d = g(C*) - g(R3), q = g(B3) - g(R3), u = g(C-thr) - g(R3); per market m and rate p.
- **Primary:** the paired change from the same market's no-churn value, Delta_x(m, p) = x(m, p) - x(m, 0), for x in
  {d, q, u}, at p = 0.03 and 0.05. Reported per market and as the equal-weight mean over the six markets with a market
  t interval (5 degrees of freedom) and the count of markets with Delta < 0.
- **Primary winner set:** the final winners after continued search (section 4). The frozen winners are reported beside
  them as a sensitivity analysis.
- **Secondary (descriptive):** the absolute contrasts d, q, u at each rate with seed-bootstrap intervals (9,999
  resamples, seed 0) and market t intervals; R3's audit allocation (the draft-10 statistics, including p = 0); efficiency
  under attack.

## 3. Support criterion and expectations (written before the draw)

**Support criterion** for "churn worsens R3's relative position" for a comparator x at rate p: mean Delta_x(p) < 0 and
Delta_x(m, p) < 0 on at least 5 of 6 markets, with the primary winners; reported also with the frozen winners.

Expectations (each scored "met" or "not met" exactly as written, primary winners; frozen winners reported beside):
1. The support criterion holds for x = d at p = 0.05.
2. The support criterion holds for x = q at p = 0.05.
3. The support criterion holds for x = d and for x = q at p = 0.03.
4. **Risky:** the support criterion holds for x = u (the runner-up) at p = 0.05. Its direction is unknown: the runner-up
   has never been run under churn, and without churn it gave the attacker a slightly lower gain than R3 (Run A).
5. R3's audited share of the attacker's jobs at p = 0.05 is below its value at p = 0 on at least 5 of 6 markets.

A failure of an expectation is reported as such and is not read as evidence for a particular cause.

## 4. Search quality

Every evaluation cell at every rate gets the registered doubling check. Each flagged cell then gets continued search
with the Run B driver (`convergence_v2.run_cell`, up to three rounds, the same stopping rule), from a flag list written
from the new doubling records. A cell that does not pass within three rounds keeps its last winner and is reported as
unresolved; the count of unresolved cells is printed with every result.

## 5. Execution contract

- No change under `sim/` or `scripts/` (code freeze). New drivers live in `docs/revision/followup3/` and call the frozen
  functions directly (`R.market`, `R.job`, `R.stage_search`, `_run_one`, `R._run_reference`, `churn_v2.install` and
  `build_jobs`, `convergence_v2.run_cell`), bypassing `R.main` and the manifest-wide freeze, as the follow-ups did.
- Gates: a Mac smoke run of each wrapper; a pod gate that runs one p = 0 cell twice and requires bit identity; the
  evidence guards that point at registered cells are replaced by guards on this run's own records.
- Every record binds to this plan's hash, the draw record, the configuration hashes and the driver hashes.
- **Analysis code before the stamp:** `replication_analysis.py` and its tests on synthetic records are committed with this
  plan, before the OpenTimestamps stamp. The analysis cannot change after the draw.
- Inventory with hashes; verification of every pulled directory on every end state; pod deletion verified; spend
  recorded from the billing page.

## 6. Cost and controls

`python3 docs/revision/followup3/cost_estimate.py`: 210 core-hours (menus 113, runner-up 11, references 0.1, p = 0
evaluation and doubling 7.5, churn 58, continued search 20.5), 23.02 USD at 0.108 USD per core-hour plus preparation;
28.77 with the 1.25 headroom; 29.92 at the 1.3 watchdog bound. The follow-up budget has 48.36 of 72 USD left
(`scripts/budget_v2.py --show`). The churn arm ran 20 to 25 percent longer than its cost model, which the headroom
covers. Stop cap and reservation are set on the spend card.

## 7. Steps

1. Internal review (Sol, Astra) to consensus on this plan.
2. Write `replication_analysis.py` with tests on synthetic records; review; commit with the plan.
3. Stamp the plan with OpenTimestamps; wait for H = A + 144 and six confirmations; draw the markets.
4. Spend card to the author with the stop cap; reserve in the ledger.
5. Pod: calibration, menus, references, p = 0 and churn searches, evaluation, doubling, continued search, diagnostics.
6. Analysis on the Mac with the committed code; a paper section and table, labelled prospective-exploratory.

## 8. What the outcome would change in the paper

- Expectations 1 to 3 met: the deterioration replicates on new markets; the paper can state it beyond the first six.
- Expectation 4 met: the deterioration is not specific to C*; the comparator caveat narrows.
- Expectation 4 not met: robustness to churn is a property of C*'s design, not of verified-history targeting; the paper
  says so.
- Expectations 1 or 2 not met: the draft-10 churn result does not replicate; the paper reports that as its main caveat.
