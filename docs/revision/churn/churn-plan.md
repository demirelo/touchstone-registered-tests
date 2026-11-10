# Honest-churn arm: plan (draft 2, 2026-11-10; for internal review; no spend yet)

**Why.** The Fable 5.2 fresh review (problem 4, `docs/revision/roster/fable52-paper-r1.md`; triage
`docs/paper/fable52-triage.md`): in both tests the nine honest opponents never replace their identities, so after the
start a new identity almost always belongs to the deviating provider. This arm lets the honest opponents replace their
identities and measures how R3's results change. The author asked on 2026-11-10 to "run all necessary sims"; nothing
runs before this plan has internal consensus and the reservation is recorded in the budget ledger.

**Status.** Draft 2. Exploratory follow-up outside the registered protocol, specified after the second test's results
were seen. Not an independent replication.

**Changes from draft 1** (internal review round 1, `docs/revision/roster/{sol,astra}-churn-plan-r1.md`, both reject; and
the author's instructions of 2026-11-10):
1. Blocker: the doubling stage's reference reselection reran no candidate under churn (stored no-churn training profits
   were reused) and its `reference_change` subtracted the stored no-churn reference score. The driver now clears those
   values for churn cells and scores the frozen reference under churn on the training seeds (section 3; tests on the
   five training seeds).
2. Blocker: a standalone p = 0 gate through the injected path, with explicit id mapping, the same dependency checks,
   `gate.json` and an inventory, and no dispatch of the churn cells on failure (section 3 c).
3. Blocker: worker limits per stage, a memory check, the gate and the diagnostics in the billed time, a reservation in
   the shared `followup` category, and a stop cap of 8 USD enforced between stages; no running stage is killed (section 7).
4. The rates are illustrative sensitivity settings (mean identity lifetimes of 100 and 20 rounds); the unmeasured claim
   about "newest" is removed and the focal identity's share of rounds as uniquely newest is measured.
5. Base results are compared with base no-churn results (C* - R3 0.0207) and doubled with doubled (0.0296).
6. Intervals condition on the six markets and the selected policies.
7. Diagnostics for the doubled winners as well; market pooling defined; per-seed counts saved; empty bins reported as
   unavailable; audit exposure is not called a financial loss.
8. Cheap reselection among the frozen menu's candidates is distinguished from regenerating the menus.

## 1. What exists (free; seen before this plan)

- `sim/policies/honest.py` `HonestMax` never exits. `sim/market.py` `run_episode`: an action with `exit=True` retires the
  identity and re-enters under a fresh one in the same round (entry cost `e = 0`); same-round entrants are ordered by a
  salted rank. `ProviderView.rng` is seeded from the episode's per-round, per-entity `policy_seed`.
- Registered no-churn values (`docs/revision/posthoc/posthoc.json`, `doubled.D2+H3`; command in section 9): pooled mean
  gain C* 0.0856, R3 0.0649; pooled C* - R3 0.0207 (base) and 0.0296 (doubled); pooled B3 - R3 0.1734 (base) and 0.1698
  (doubled).
- Registered honest-replacement diagnostic (headline, one replacement at round 50): R3 audits 1.000 and 0.917 of the
  replacement's jobs in its first two ten-round bins, C* 0.428 and 0.161, B3 about 0.250 (`posthoc.json` `honest`).
- **Disclosed peek (timing check, 2026-11-10).** To price the churn slowdown, the registered no-churn F111 D2+H3 attack on
  fresh0 was rerun on the first 40 evaluation seeds under churn (`docs/revision/churn/churn_timing.py`): mean normalised
  profit 0.468 (no churn), 0.487 (p = 0.01), 0.521 (p = 0.05); the focal provider used 54.0, 36.7 and 6.8 identities per
  episode; honest replacements per episode 0, 18.25, 89.2. One rule, one market, the old attack, no reference; the
  expectations in section 6 were written after it.

## 2. Estimand

For rule r in {R3 (F111), C*, B3 (F000)}, fresh market m and churn rate p:

g_p(r, m) = mean over the 200 evaluation seeds of the normalised gain of the D2+H3 attack selected by the registered
search under churn p, against the rule's frozen truthful reference played under the same churn.

Contrasts: d_p(m) = g_p(C*, m) - g_p(R3, m) and q_p(m) = g_p(B3, m) - g_p(R3, m), pooled with equal market weights, and
their changes from the registered no-churn values on the same seeds. The attack and reference profits are reported
separately. These are differences between finite searches with a fixed reference candidate in a changed environment, not
identified optimal values. A weaker reference can raise a measured gain, and unequal reference losses can move either
contrast in either direction.

## 3. Cells and execution contract

- **Churn model.** Each of the nine honest opponents plays honest-max delivery and offer and, in each round, retires its
  identity and re-enters under a fresh one with probability p (`docs/revision/churn/churn_v2.py` `HonestChurn`). The draw
  uses the episode's `policy_seed[t, e]`, so it is deterministic and the same for every rule on the same seed. The model
  keeps provider capacity and quality fixed and changes identity age; it also resets an honest provider's history and
  lets it leave a false ban, so it does not isolate age information alone. **Rates p in {0.01, 0.05}** are illustrative
  sensitivity settings without empirical calibration: mean identity lifetimes of 100 and 20 rounds, about 18 and 89
  honest replacements per episode (measured, section 1). Whether the focal identity stays the newest is measured (section 4).
- **Cells.** {R3, C*, B3} x fresh0..fresh5 x {0.01, 0.05} at rho 0.2, D2+H3, registered search budget (5 restarts, 300
  evaluations, 5 training seeds), the market's 200 evaluation seeds, a doubling check with its held-out evaluation on
  every cell: **36 cells**, plus the gate cell.
- **Driver.** `docs/revision/churn/churn_v2.py` (under `docs/`: the code freeze allows changes only there). It runs the
  frozen `revision_v2` stage functions through `_run_one` and reuses the reset driver's helpers
  (`docs/revision/followup/reset_followup_v2.py`: input copies, pre-episode checks, follow-up freeze, acceptance,
  comparators, inventory). `install()` wraps three `revision_v2` names, also in every pool worker's initialiser (tested):
  `train_cell` (which `eval_cell` calls), so search, twin search, the doubling stage's reference menu, and evaluation run
  under churn; `select_reference`, so a cell with churning opponents never reuses a candidate's stored no-churn training
  profits (only the abstain candidate, whose profit is zero, keeps its value); and `reference_of`, so a churn job's
  frozen reference carries its training-seed score evaluated under the same churn, which the doubling stage's
  `reference_change` subtracts. Churn job ids carry the suffix `|churn<p>` so they never overwrite the copied registered
  D2+H3 records that the reference menus read; each rate writes to its own directory (`results/v2/followup-churn/p<p>/`),
  never to `eval/all`.
- **References: frozen candidate, played under churn.** Each (market, rule) keeps its frozen truthful reference
  candidate. Two reselections are distinguished. Reselecting among the frozen menu's candidates under churn needs only
  their evaluation on the training seeds; the doubling stage does it for every cell (with the fix above), and its
  `reference_change` is reported as a diagnostic, not as a bound on held-out bias. Regenerating the menus under churn
  would need 60 D2+H3 and 60 X7-SC searches per rate, about 12.19 USD per rate before the churn slowdown (section 9); it
  is not done.
- **Checks before any episode** (reset driver, plan draft 5): configuration hash equals the container hash; salt; known
  commit; runner and `sim/` equal protocol-v2; each job's runner, salt, configuration, root, seeds, rule parameters and
  context equal its frozen reference's provenance; output not inside `--src` or `eval/all`. Inputs are copied read-only
  and hash-checked against the original records and freeze; the follow-up freeze and acceptance run before evaluation
  and doubling; a final inventory records every output hash, the environment, and the churn driver's hash.
- **Validation before spend (free, on the Mac).** (a) Unit tests: the churn policy is truthful and exits at rate p,
  deterministically; p = 0 never exits; the wrapper adds churning opponents to training and evaluation cells, also in
  pool workers, and leaves other jobs unchanged; churn ids and provenance are distinct; under churn every menu candidate
  is rerun on the five training seeds and the frozen reference's score is recomputed; newcomer counts, unavailable
  bins, the focal newest share, market pooling; the gate's id mapping; a failed gate stops dispatch; the cap check. (b)
  A smoke-size run of the whole path for fresh0 R3 at p = 0.05, including the gate path and both winners' diagnostics.
  All pass: `uv run pytest -q docs/revision/churn` (14 passed).
- **(c) The p = 0 gate, first on the pod.** The driver runs fresh0 R3 D2+H3 at p = 0 through the injected path (inputs,
  search, freeze, acceptance, evaluation, doubling) into `gate-p0/`, maps the id `|churn0` to the registered id, and
  compares search and evaluation by the reset driver's `compare` and the doubling check by `compare_doubling`
  (draft-5 criteria of the reset plan). It saves `gate-p0/gate.json` and an inventory. On failure the driver stops before
  any churn cell is dispatched and reports.

## 4. Diagnostics (evaluation only, no search)

For every cell, the base and the doubled winner are rerun on the evaluation seeds under churn (`diagnostics` stage):
per-seed normalised profits; per episode the [served, audited] counts by identity age, in bins [0, 10), [10, 20),
[20, 50), [50, 200), for honest replacement identities, honest initial identities, and the focal provider's identities;
honest replacements per episode; and per episode the share of rounds in which the focal identity is uniquely the newest.
A bin with no served job is reported as unavailable. Pooling over markets: per rule, winner and bin, the mean of the
market shares over the markets where the share is available, with that count. A higher audited share of honest
newcomers is greater audit exposure; it is not by itself a financial loss.

## 5. Analysis (fixed now)

- Per market and pooled g_p(r), d_p, q_p, with paired seed bootstrap intervals (9,999 resamples, percentile, 95 percent;
  the same resampled seed indices for every rule and rate of a market; pooled replicates resample seeds within each
  market and average the six market means). The intervals condition on the six markets and the selected policies; they
  do not include search uncertainty or uncertainty across markets.
- Changes from no churn, paired by seed with the registered records: base with base, doubled with doubled.
- Attack and reference profit terms separately; the reselection diagnostic per cell; sign counts over the six markets.
- No confirmatory test, no multiplicity family, no change to any registered decision; all results are labelled
  exploratory follow-up.

## 6. Pre-specified expectations

Written after the disclosed peek in section 1 and before any churn search. Scored on point estimates, as met (holds
under both the base and the doubled searches, each against its own no-churn baseline), failed (fails under both), or not
established (the two disagree).

1. Pooled g_0.05(R3) exceeds the registered pooled no-churn g(R3) (base 0.0649; doubled against the doubled value).
2. Pooled d_0.05 = C* - R3 is below the registered no-churn value (base 0.0207; doubled 0.0296).
3. q_0.01 = B3 - R3 is positive on all six markets.
4. Under R3 at p = 0.05, the market-pooled audited share of honest replacement identities in their first ten rounds
   exceeds that under C* and under B3, for both winners.

A failure is not read as evidence of a particular cause. Only if expectation 2 is met may the paper say that R3's
measured edge over C* shrinks when honest opponents churn; only if 4 is met that R3's audit exposure shifts to honest
newcomers.

## 7. Cost and operations

**Work** (`experiments/v2/benchmark/timings.json`, 0.108 USD per core-hour): per cell a D2+H3 search (2,084 s), the
evaluation on 200 seeds (96.0 s per 160 seeds, scaled: 120 s), the doubling check with its held-out evaluation (998 s),
and two diagnostic profiles (60 s); churn slows an episode by 1.133 (p = 0.01) and 1.330 (p = 0.05) (section 1). 36
cells plus the gate cell: **41.1 core-hours, 4.43 USD** at the benchmark price.

**Memory** (`docs/revision/churn/churn_memory.py`): one 200-seed profile peaks at 981 MB without churn and 1,084 MB at
p = 0.05; an evaluate or doubling task keeps four profiles (2.5 GB without churn, operations ledger), so about 2.8 GB
under churn. Workers: search 16; evaluate, doubling and diagnostics 9 (about 25 GB, below the pod's 28 GiB floor).

**Billed pod time** (one 16-vCPU pod, 0.56 USD per hour): the gate cell serially, then per rate the 18 searches in two
waves of 16 and the evaluation, doubling and diagnostics in two waves of 9, plus 0.6 hours of preparation and idle:
**5.95 hours, 3.33 USD**.

**Budget** (author, 2026-11-10). The arm uses the shared ledger category `followup` (cap 22 USD for all follow-up runs).
Before the pod: reserve the estimate times 1.25, 4.43 x 1.25 = 5.54 USD, with
`docs/revision/followup/budget_followup.py --reserve`. **Stop cap 8.00 USD.** No running stage is ever killed: before
each stage the driver compares the pod time billed since allocation plus the stage's estimate with the cap
(`--started`, `--stop-usd 8`), and if the cap would be passed it stops between stages and reports. A failed attempt
counts toward the cap.

## 8. Steps

1. Internal review of this plan to consensus; freeze it (commit).
2. The author's approval of the follow-up limit is recorded; the reservation of 5.54 USD under `followup`.
3. One pod: the p = 0 gate, then the 36 cells; delete the pod and verify the deletion; record the spend.
4. Analysis in `docs/revision/posthoc/` (tested first); a paper paragraph and table, labelled exploratory.

## 9. Commands behind the numbers

- Registered values: `python3 -c "import json;p=json.load(open('docs/revision/posthoc/posthoc.json'))['doubled']['D2+H3'];print(p['absolute'],p['pooled'])"`
  (C* 0.0856, R3 0.0649; C* - R3 0.02072 base, 0.02962 doubled; B3 - R3 0.1734 base, 0.1698 doubled).
- Timing and peek: `uv run python docs/revision/churn/churn_timing.py` (40 fresh0 evaluation seeds; 6.48, 7.34, 8.62 s).
- Memory: `uv run python docs/revision/churn/churn_memory.py none` and `... 0.05` (981.0 and 1,084.4 MB).
- Cost: benchmark arithmetic over `experiments/v2/benchmark/timings.json` with the measured slowdowns, the worker limits
  above and two waves per stage (41.06 core-hours, 4.43 USD; 5.35 hours of stages plus 0.6, 5.95 billed hours, 3.33 USD).
- Reselection-by-regeneration cost: `sim/manifest_v2.py` `menu_families` and `bank_rules(ctx, fam, 3, False)` over the six
  markets and three rules: 60 D2+H3 and 60 X7-SC searches per rate, 12.19 USD per rate.
- Tests: `uv run pytest -q docs/revision/churn` (14 passed, 137 s).
