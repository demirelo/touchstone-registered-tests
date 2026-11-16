# Churn replication on new markets: plan (draft 3 with the review r3 caveats, 2026-11-16; consensus; no spend)

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

**Changes from draft 2** (internal review round 2, `docs/revision/roster/{sol,astra}-replication-plan-r2.md`, both reject):
1. The stamped manifest's bytes, not this plan, are the `--protocol` input of the block reader and of the instance
   wrapper, which then checks every listed hash; the manifest also binds the frozen code revision and the imported
   helpers (section 5). Private stamp and public commitment are distinguished; without publication before H the draw is
   recorded as nonconfirmatory.
2. The continuation gate runs at nonzero churn and tests candidate replay (section 5).
3. Failure rules: a round-1 mismatch stops all continuation, with no substitution; a missing continuation output falls back to the
   validated frozen winner; a missing base evaluation or doubling makes the cell unscorable; the inherited tie rule;
   reselected references affect only diagnostics and stopping (section 4).
4. Interval construction and coverage stated; replication wording tied to the criterion that holds; "not scorable"
   distinguished from "not met" (sections 2, 3, 8). Expectation 4: "no direct runner-up churn result", 0.5 subjective.
5. Cost schedule in execution order (D2+H3 menus before X7-SC, gates after their inputs), churn slowdown on diagnostics,
   preparation and transfer for each of two pods (section 6). 6. Deterministic continuation priority under a cost stop,
   pod-memory admission against the allocated pod, validated configuration reuse across pods (section 5).

**Review round 3** (`docs/revision/roster/{sol,astra}-replication-plan-r3.md`): Sol and Astra accept-with-caveat; the
caveats are applied below without another round: the gates are split and ordered (section 5); the frozen code is
verified at run time and publication evidence is kept (section 5); a continuation stopped between rounds keeps the
frozen winner (section 4); expectation 4 is an uncertain forecast (section 3).

**Status.** Draft 3, consensus. The implementation (drivers, adapter, analysis, tests) is reviewed separately before
the stamp. A prospective follow-up: this plan, its expectations and its analysis code are committed and stamped
before the block that draws the markets exists. It is still outside the registered protocol v2 and changes no registered
decision. It is the first churn result in this project whose markets were unknown when its expectations were written.

## 1. Design

- **Markets.** Six new markets from the protocol-v2 generator (`sim/instances.py`), seeded by a new block: this plan file
  is listed in a manifest (section 5) that is stamped with OpenTimestamps; A is the proof's lowest valid attestation;
  the draw block is H = A + 144, read with `scripts/block_draw.py --protocol <the manifest>`; a wrapper under `docs/` calls `draw_v2.instances(..., calibrate=False)` (the CLI calibrates by
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
- **Intervals.** Seed-bootstrap: 95 percent paired percentile intervals, 9,999 resamples, seed 0; seeds are resampled
  within each market, with one index vector per market shared by every rule, rate and winner set (the churn arm's
  pairing). Market level: 95 percent t intervals over the six market values (5 degrees of freedom), which treat the
  markets as a sample from the generator's neighbourhood. Neither covers search uncertainty.
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
4. The support criterion holds for x = u (the runner-up) at p = 0.05. Subjective prospective probability, recorded now:
   0.5. There is no direct runner-up churn result; the R3 churn results and the two comparators' mechanics give only
   indirect information. This is an uncertain forecast, not evidence that the prediction is difficult.
5. R3's audited share of the attacker's jobs (audited jobs over served jobs of the attacker's identities, summed over the
   200 seeds of a market) at p = 0.05 is below its value at p = 0 on at least 5 of 6 markets; a market where the attacker
   serves no job at either rate (a zero denominator at either rate) counts as not below.

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
counted as unresolved; a cell whose continuation stops between rounds at the cost cap keeps its validated frozen winner,
its partial rounds are excluded from every result, and it is counted as stopped; a cell not continued because of the
cost cap, or whose continuation output is missing or
nonfinite, keeps its validated frozen winner and is counted as not continued. A round-1 mismatch (round 1 differs from
this run's doubling record) signals an environment or code fault, as in Run B (exit 4): it stops all continuation, no
continued winner of this run enters any result, and the primary analysis is reported as not available; the all-frozen
set is then reported, labelled as such, and no fallback is substituted. A cell whose base evaluation or doubling record is missing or
invalid is unscorable, and so is every expectation that needs it. Ties in reference selection follow the frozen
`select_reference` rule (training score, then its fixed order). A reference reselected during continuation affects only
the diagnostics and the stopping decision; gains always use the rule's selected no-churn reference candidate.
Continuation order, fixed now (it decides which cells a cost stop leaves out): p = 0.05, then 0.03, then 0; within a
rate, markets rep0 to rep5; within a market, R3, C*, C-thr(12), B3. The five continuation workers take cells from one
queue in this order, and a resume continues the same queue from the first cell without a passing record. Passing the
continuation's incremental check is not a claim of convergence or of bounded search error.

## 5. Execution contract

- No change under `sim/` or `scripts/` (code freeze). New drivers live in `docs/revision/followup3/` and call the frozen
  functions directly (`R.market`, `R.job`, `R.stage_search`, `_run_one`, `R._run_reference`, `churn_v2.install` and
  `build_jobs`, `convergence_v2.run_cell`), bypassing `R.main` and the manifest-wide freeze, as the follow-ups did.
- Gates, in order: a Mac smoke run of each wrapper; on the pod, after the menus and references, one p = 0 cell through
  the churn path with churn zero (search, evaluation and doubling) against the ordinary menu search and its evaluation
  and doubling, required bit-identical in all three; then, after the first p = 0.05 cell's search, evaluation and
  doubling (reused in production), its continuation round 1 against its own doubling record, required identical, with a
  test that every menu candidate was replayed under churn (a zero-churn gate cannot expose cached no-churn scores).
- Frozen code at run time: before the draw, before each stage and before any resume, the drivers check that `sim/`,
  `scripts/` and the frozen configuration inputs equal the manifest's git commit (no working-tree change), that no
  environment override is set, and that every manifest-listed file matches its hash. The evidence guards that point at registered cells are replaced by guards on this run's own records.
- Memory: the longest task of each stage measured on the Mac (as the churn arm and Run B did); on each pod, before each
  stage, the worker count is admitted against the pod's cgroup memory limit with 25 percent headroom over the measured
  peak and lowered if needed, then kept across restarts; the saved configurations are reused on the second pod only
  after their hashes match the first pod's record; worker-side atomic saves (Run B's pattern); resume reuses only records with this run's
  binding; failure paths (lost worker, cell error, cost stop) tested before any spend, as in Run B.
- Every record binds to this plan's hash, the draw record, the configuration hashes and the driver hashes.
- **Commitment:** a manifest file lists the git commit of the frozen code and the SHA-256 of this plan,
  `replication_analysis.py`, its tests, the drivers and adapters, every imported helper outside `sim/` and `scripts/`, the
  parameter files and `uv.lock`. The manifest's bytes are the `--protocol` input of `block_draw.py` and of the instance
  wrapper, which refuses to draw unless every listed file matches its hash. The stamp, the upgraded proof, the lowest
  valid attestation A and the draw record are kept. One stamp and one draw at H = A + 144: no restamping, no redraw, no
  replacement of a market after any record exists. A valid anchor at A proves that the manifest existed before H; a
  public, uniquely identified commitment also needs the manifest published before H (a push, which needs the author's
  consent), with its publication height recorded and the evidence for it kept (the pushed commit, the remote's record and a block
explorer read at that time); `draw_v2.instances` only compares the given height with H and does not authenticate it. Without publication before H, the draw wrapper records the draw as
  nonconfirmatory (the `--published-height` rule of `draw_v2.py`), and the paper says so.
- Inventory with hashes; verification of every pulled directory on every end state; pod deletion verified; spend
  recorded from the billing page.

## 6. Cost and controls

`python3 docs/revision/followup3/cost_estimate.py`, a stage schedule in execution order at the memory-safe workers
(search 16, evaluation and doubling 9, continuation 5), with calibration, gates, diagnostics, and preparation and transfer
for each of two pods: flag share 0.30 gives 221 core-hours, 25.2 billed pod-hours; 0.50 gives 238 core-hours, 28.9
pod-hours. Actual billing is per pod-hour (14.12 and 16.21 USD at 0.56); the conservative estimate is the larger of that
and core-hour pricing at 0.108: 23.84 and 25.72 USD, with the 1.25 headroom 29.80 and 32.15. The follow-up budget has 48.36 of 72 USD
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

- Expectations 1 to 3 met: the deterioration replicates on new markets under the descriptive criterion; "material" is
  claimed only where the companion also holds.
- Expectation 4 met: the deterioration is not specific to C*; the comparator caveat narrows.
- Expectation 4 not met: "runner-up deterioration not supported", reported without a causal reading.
- Expectations 1 or 2 not met: the draft-10 churn result does not replicate on these markets; the paper reports that as
  its main caveat. An expectation that is not scorable is reported as "not scorable", never as met or not met.
- Every claim is restricted to the generator's market neighbourhood, the four rules, the D2+H3 family and the prescribed
  finite searches.
