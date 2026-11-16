# Churn replication on new markets: plan (draft 2, 2026-11-16; for internal review; no spend)

**Why.** Two external reviews of draft 10 (`docs/revision/roster/astra-pro-paper-d10-ext.md`, `-ext2.md`; WEIS 3/5 upper
borderline) found the churn result reproducible but narrow: one market neighbourhood, one verified-history comparator
under churn, and searches with 21 of 72 cells flagged. Their top recommendation: a churn validation fixed before the
outcomes, on newly drawn markets, with the runner-up comparator and stronger search checks. The author chose on
2026-11-16 (card `touchstone-churn-replication`): "Plan it now (no spend)". Nothing runs before internal consensus and a
separate spend card.

**Changes from draft 1** (internal review round 1, `docs/revision/roster/{sol,astra}-replication-plan-r1.md`, both reject):
1. Blocking: continuation under churn needs a churn-aware adapter (section 4); `convergence_v2.run_cell` imports
   `sim.reference.select_reference` directly and would reuse no-churn candidate scores.
2. The stamped commitment is a manifest that hashes this plan, the analysis code, its tests, the drivers, the parameter
   files and the dependency lock (section 5); one stamp, one draw, no restamping or redraw.
3. Winner rules for unflagged, flagged, unresolved, cost-stopped and missing cells; round 1 of continuation repeats the
   doubling (section 4). Normalised gain defined; attack and reference terms reported (section 2).
4. The support criterion is labelled descriptive and gets a material companion; expectation 4 states a prospective
   probability instead of "risky"; expectation 5's denominator is defined (section 3).
5. Gates: ordinary p = 0 against churn-path p = 0, and continuation round 1 against this run's doubling record; memory,
   worker limits, atomic saves and resume tests (section 5).
6. Cost from a stage schedule with memory-safe workers, gates, calibration, diagnostics and a flag-share sensitivity
   (section 6). 7. Interpretation without causal attribution and restricted to the generator's neighbourhood (section 8).

**Status.** Draft 2. A prospective follow-up: this plan, its expectations and its analysis code are committed and stamped
before the block that draws the markets exists. It is still outside the registered protocol v2 and changes no registered
decision. It is the first churn result in this project whose markets were unknown when its expectations were written.

## 1. Design

- **Markets.** Six new markets from the protocol-v2 generator (`sim/instances.py`), seeded by a new block: this plan file
  is stamped with OpenTimestamps; A is the proof's earliest attestation; the draw block is H = A + 144, read with
  `scripts/block_draw.py --protocol <this file>`; a wrapper under `docs/` calls `draw_v2.instances(..., calibrate=False)` (the CLI calibrates by
  default) to derive the instances, the 200 evaluation seeds per market and the identity salt from the block root; the
  wrapper installs the draw-derived salt and checks it in every job. The generator labels them `fresh0` to `fresh5`; in this plan and the
  paper they are `rep0` to `rep5`, and every run writes into its own output directory (no record shares a directory
  with the registered `fresh*` records). The headline market is not used.
- **Calibration.** The instances are calibrated once, on the pod's Linux x86 stack, by a wrapper that calls the frozen
  calibration; the configurations and their hashes are saved before any search and passed as `cfg=` to every job. No
  later stage recalibrates (lesson 2026-11-04, the 1-ulp deviation).
- **Rules.** R3 (`F111`), C* (C-mem(6, 20)), the runner-up C-thr(12), and B3 (`F000`), at the registered budget,
  sanctions and parameters (rho = 0.2). C-thr(12) runs under the existing `C*` label with the runner-up parameters in its
  own output directories, as Run A did (a new rule label would fail in the frozen `rule_spec`).
- **Rates.** p = 0, 0.03, 0.05: no churn, and the two rates at which draft 10 found a deterioration on every market under
  both search versions. Mean identity lifetimes 33 and 20 rounds.
- **Attacker family.** D2+H3 only, with the registered search budget and seeds. X7-SC is searched only as part of the
  reference menus (below).
- **References.** Faithful to the registered procedure: each rule's truthful reference is selected from its menu (its
  own D2+H3 and X7-SC winners plus the winners of the nine bank rules in both families, cuts 3) by the frozen
  `_run_reference`; C-thr(12) uses its own searches and a copy of the bank, as Run A did. The frozen candidates are
  replayed under churn (as in the churn arm); the menus are not regenerated under churn.

## 2. Estimands and primary analysis (fixed now)

- Normalised gain g = (attack profit - reference profit) / (S*/N), per seed, averaged over the 200 evaluation seeds, as
  in the registered tests; the attack and reference terms are reported separately.
- d = g(C*) - g(R3), q = g(B3) - g(R3), u = g(C-thr) - g(R3); per market m and rate p.
- The p = 0 cell of each rule is its menu D2+H3 search record, evaluated and doubled; at p > 0 each rule keeps its
  selected no-churn reference candidate, replayed under the same churn.
- **Primary:** the paired change from the same market's no-churn value, Delta_x(m, p) = x(m, p) - x(m, 0), for x in
  {d, q, u}, at p = 0.03 and 0.05. Reported per market and as the equal-weight mean over the six markets with a market
  t interval (5 degrees of freedom) and the count of markets with Delta < 0.
- **Primary winner set:** per cell, the frozen winner if its doubling check is not flagged, and the final winner of the
  continued search (section 4) if it is; the all-frozen set is reported beside it as a sensitivity analysis.
- **Secondary (descriptive):** the absolute contrasts d, q, u at each rate with seed-bootstrap intervals (9,999
  resamples, seed 0) and market t intervals; R3's audit allocation (the draft-10 statistics, including p = 0); efficiency
  under attack.

## 3. Support criterion and expectations (written before the draw)

**Support criterion (descriptive)** for "churn worsens R3's relative position" against comparator x at rate p: mean
Delta_x(p) < 0 and Delta_x(m, p) < 0 on at least 5 of 6 markets, with the primary winners. It allows arbitrarily small
changes and is not a significance test. **Material companion:** mean Delta_x(p) <= -0.05 (the registered Q1 margin).
Both are reported for both winner sets, beside the market t interval, which treats the six markets as a sample and
omits search uncertainty.

Expectations (each scored "met" or "not met" exactly as written, primary winners; frozen winners reported beside):
1. The support criterion holds for x = d at p = 0.05.
2. The support criterion holds for x = q at p = 0.05.
3. The support criterion holds for x = d and for x = q at p = 0.03.
4. The support criterion holds for x = u (the runner-up) at p = 0.05. Prospective probability, recorded now: 0.5. The
   plan has no directional information: the runner-up has never run under churn, and its threshold rule may react to
   honest newcomers differently from C*'s memory rule.
5. R3's audited share of the attacker's jobs (audited jobs over served jobs of the attacker's identities, summed over the
   200 seeds of a market) at p = 0.05 is below its value at p = 0 on at least 5 of 6 markets; a market where the attacker
   serves no job at either rate counts as not below.

Incomplete data: a cell without a valid record at the end of the run makes every expectation that needs it "not
scorable", reported as such; no cell is imputed.

A failure of an expectation is reported as such and is not read as evidence for a particular cause.

## 4. Search quality

Every evaluation cell at every rate gets the registered doubling check; the menu X7-SC winners get none (reference
selection uses training scores). Each flagged cell then gets continued search with Run B's stopping rule, up to three
rounds in total, where round 1 repeats the doubling (it is checked against this run's doubling record). Under churn the
continuation runs through a churn-aware adapter under `docs/`: it installs churn in every worker and replaces the
direct `sim.reference.select_reference` import of `convergence_v2.run_cell`, so that every menu candidate is replayed
under the cell's churn and no cached no-churn score is used; tests require the replay and the round-1 agreement.
Winners: a cell that passes keeps its final winner; a cell that reaches the round cap keeps its last winner and is
counted as unresolved; a cell stopped by the cost cap or with a missing or nonfinite record keeps its frozen winner and
is counted as not continued; all three counts are printed with every result.

## 5. Execution contract

- No change under `sim/` or `scripts/` (code freeze). New drivers live in `docs/revision/followup3/` and call the frozen
  functions directly (`R.market`, `R.job`, `R.stage_search`, `_run_one`, `R._run_reference`, `churn_v2.install` and
  `build_jobs`, `convergence_v2.run_cell`), bypassing `R.main` and the manifest-wide freeze, as the follow-ups did.
- Gates: a Mac smoke run of each wrapper; on the pod, one p = 0 cell through the ordinary path and through the churn path
  with churn zero, required bit-identical; one continuation round 1 against its own doubling record, required
  identical. The evidence guards that point at registered cells are replaced by guards on this run's own records.
- Memory: the longest task of each stage measured on the Mac (as the churn arm and Run B did), worker limits fixed per
  stage and kept across restarts; worker-side atomic saves (Run B's pattern); resume reuses only records with this run's
  binding; failure paths (lost worker, cell error, cost stop) tested before any spend, as in Run B.
- Every record binds to this plan's hash, the draw record, the configuration hashes and the driver hashes.
- **Commitment:** a manifest file lists the SHA-256 of this plan, `replication_analysis.py`, its tests, the drivers and
  adapters, the parameter files and `uv.lock`. The manifest is stamped with OpenTimestamps (not only this plan), and the
  stamp, the upgraded proof, the lowest valid attestation A, and the time the manifest was pushed to the repository are
  recorded. One stamp and one draw at H = A + 144: no restamping, no redraw, and no replacement of a market after any
  record exists. Publishing the manifest before H (a push) needs the author's consent; without it, the stamp alone
  fixes the commitment and the manifest is released with the paper.
- Inventory with hashes; verification of every pulled directory on every end state; pod deletion verified; spend
  recorded from the billing page.

## 6. Cost and controls

`python3 docs/revision/followup3/cost_estimate.py`, a stage schedule at the memory-safe workers (search 16, evaluation
and doubling 9, continuation 5), with calibration, gates and diagnostics: flag share 0.30 gives 221 core-hours, 25.2
billed pod-hours; 0.50 gives 238 core-hours, 28.9 pod-hours. Estimate (the larger of core-hour pricing at 0.108 and pod
pricing at 0.56): 23.87 and 25.75 USD; with the 1.25 headroom 29.84 and 32.18. The follow-up budget has 48.36 of 72 USD
left. The run may use two pods (menus and references; then evaluation, churn and continuation) to stay under a day per
pod. The stop cap is set on the spend card; the reservation covers 1.3 times that cap.

## 7. Steps

1. Internal review (Sol, Astra) to consensus on this plan.
2. Write `replication_analysis.py`, the drivers and the churn-aware continuation adapter, with tests on synthetic records
   (including the replay and failure-path tests); review; build the manifest.
3. Stamp the manifest with OpenTimestamps; wait for H = A + 144 and six confirmations; draw the markets once.
4. Spend card to the author with the stop cap; reserve in the ledger.
5. Pod: calibration, menus, references, p = 0 and churn searches, evaluation, doubling, continued search, diagnostics.
6. Analysis on the Mac with the committed code; a paper section and table, labelled prospective-exploratory.

## 8. What the outcome would change in the paper

- Expectations 1 to 3 met: the deterioration replicates on new markets; the paper can state it beyond the first six.
- Expectation 4 met: the deterioration is not specific to C*; the comparator caveat narrows.
- Expectation 4 not met: "runner-up deterioration not supported", reported without a causal reading.
- Expectations 1 or 2 not met: the draft-10 churn result does not replicate on these markets; the paper reports that as
  its main caveat.
- Every claim is restricted to the generator's market neighbourhood, the four rules, the D2+H3 family and the prescribed
  finite searches.
