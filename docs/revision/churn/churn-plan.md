# Honest-churn arm: plan (draft 6, 2026-11-11; for internal review; no spend yet)

**Why.** The Fable 5.2 fresh review (problem 4, `docs/revision/roster/fable52-paper-r1.md`; triage
`docs/paper/fable52-triage.md`): in both tests the nine honest opponents never replace their identities, so after the
start a new identity almost always belongs to the deviating provider. This arm lets the honest opponents replace their
identities and measures how R3's results change. The author asked on 2026-11-10 to "run all necessary sims"; nothing
runs before this plan has internal consensus and the reservation is recorded in the budget ledger.

**Status.** Draft 6. Exploratory follow-up outside the registered protocol, specified after the second test's results
were seen. Not an independent replication.

**Changes from draft 3** (internal review round 3, `docs/revision/roster/{sol,astra}-churn-plan-r3.md`, both reject; and
the cross-cutting rules of the author and the reset plan):
1. The cost admission runs again after the memory preflight chooses the workers; the first admission includes the
   preflight's serial tasks; the chosen worker limit is kept for every later stage, including the diagnostics.
2. The preflight runs real tasks (one evaluate task per rule, one doubling task) in child processes, takes the largest
   peak with a 25 percent margin for markets, rules and winners, and keeps their records; doubling is measured itself.
3. The pod gate requires bit identity (`--require-identical`, the semantics of the reset driver's `pod_gate_ok`; the
   author's decision on card `touchstone-reset-repro-pass`); the Mac gate keeps the tolerance criterion.
4. The launcher is a reviewed copy of `results/pods/reset_pod.sh` with `podctl.py` (draft in
   `docs/revision/churn/churn_pod.sh`): stages stop only between stages at the soft cap; the one exception is the
   watchdog, which deletes the pod at 1.3 times the cap at the price ceiling; attempts persist in its attempts file, with
   the bound at the ceiling; it passes the allocation time, the price and the earlier attempts' charges to the driver.

**Changes from draft 2** (internal review round 2, `docs/revision/roster/{sol,astra}-churn-plan-r2.md`: Sol
accept-with-caveat, Astra reject):
1. Production runs require the pod's allocation time (`--started`) and its actual hourly price (`--usd-per-hour`), and
   carry the charges of earlier failed attempts (`--prior-usd`); all three are saved in `run.json`. The 8 USD limit is
   described as an estimate-based stage-admission limit that an overrunning stage can exceed under the no-kill rule; pod
   deletion on completion or failure is the launcher's job (section 7).
2. The reservation command passes the unpadded estimate, 4.43 USD; the wrapper applies the factor 1.25.
3. Every production stage, including separate-stage and resumed runs, requires a saved passing gate record of this
   driver version; production cannot skip the gate (section 3 c).
4. A pod-side memory preflight before the nine-worker stages: the cgroup limit, one full evaluate task's peak (four
   profiles) in a child process, the parent's own memory, and fewer workers if needed (section 7).
5. The creation-time newest statistic is labelled as such, and the mechanism-relevant one is added: first-offer age among
   the identities holding assigned jobs (section 4).
6. Expectation 4 is narrowed to a cross-rule difference under churn (section 6).

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
  A smoke-size run of the whole path for fresh0 R3 at p = 0.05, including the gate path, both winners' diagnostics, and
  the memory preflight on its output; production refuses a missing `--started`, `--gate skip`, and a separate stage
  without a saved passing gate; the worker limit fits the memory limit. All pass: `uv run pytest -q docs/revision/churn`
  (32 passed: also the bit-identity pod gate, the preflight's real-task sample, admission after the preflight with
  the kept worker limit, a skipped record never counted as a measurement, a retry reusing only an applicable saved
  measurement, and the worker limit kept across separate-stage commands, the diagnostics included; round 5: rule coverage
  of a reused measurement, rejection of older records, and dispatch of measured jobs).
- **(c) The p = 0 gate, first on the pod.** The driver runs fresh0 R3 D2+H3 at p = 0 through the injected path (inputs,
  search, freeze, acceptance, evaluation, doubling) into `gate-p0/`, maps the id `|churn0` to the registered id, and
  compares search and evaluation by the reset driver's `compare` and the doubling check by `compare_doubling`
  (draft-5 criteria of the reset plan). **On the pod the gate requires bit identity** (`--require-identical`: search,
  evaluation and doubling identical to the registered records, the reset driver's `pod_gate_ok` semantics, the author's
  decision); on the Mac the draft-5 tolerance criterion applies. It saves `gate-p0/gate.json` (with `identical`,
  `require_identical` and `gate_ok`) and an inventory. On failure the driver stops before
  any churn cell is dispatched and reports. Every later production stage, also when run alone or resumed, first requires
  that saved gate record: passing its criterion (on the pod, bit-identical), for this cell and id mapping, and run by the
  same driver version (its hash in the gate's inventory); production runs cannot skip the gate.

## 4. Diagnostics (evaluation only, no search)

For every cell, the base and the doubled winner are rerun on the evaluation seeds under churn (`diagnostics` stage):
per-seed normalised profits; per episode the [served, audited] counts by identity age, in bins [0, 10), [10, 20),
[20, 50), [50, 200), for honest replacement identities, honest initial identities, and the focal provider's identities;
honest replacements per episode; and per episode two "newest" shares for the focal identity. (i) Creation-time newest:
the share of rounds in which its creation round is strictly the latest among all current identities; this is not the
order R3 uses. (ii) Mechanism-relevant: over the rounds in which it holds assigned jobs, the share in which its
first-offer round is strictly the latest among the identities holding assigned jobs, which is how R3 ages and ranks
identities (`sim/mechanisms/factorial.py`). Only (ii) is used to discuss R3's targeting.
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
4. At p = 0.05, the market-pooled audited share of honest replacement identities in their first ten rounds is higher
   under R3 than under C* and than under B3, for both winners (a cross-rule difference under churn; no no-churn baseline
   exists for honest replacement identities in these cells).

A failure is not read as evidence of a particular cause. Only if expectation 2 is met may the paper say that R3's
measured edge over C* shrinks when honest opponents churn; only if 4 is met that, under churn, R3 exposes honest newcomers
to more audits than C* and B3 do.

## 7. Cost and operations

**Work** (`experiments/v2/benchmark/timings.json`, 0.108 USD per core-hour): per cell a D2+H3 search (2,084 s), the
evaluation on 200 seeds (96.0 s per 160 seeds, scaled: 120 s), the doubling check with its held-out evaluation (998 s),
and two diagnostic profiles (60 s); churn slows an episode by 1.133 (p = 0.01) and 1.330 (p = 0.05) (section 1). 36
cells plus the gate cell: **41.1 core-hours, 4.43 USD** at the benchmark price.

**Memory** (`docs/revision/churn/churn_memory.py`): one 200-seed profile peaks at 981 MB without churn and 1,084 MB at
p = 0.05; an evaluate or doubling task keeps four profiles (2.5 GB without churn, operations ledger), so about 2.8 GB
under churn. Workers: search 16; evaluate, doubling and diagnostics 9 (about 25 GB, 23.3 GiB, below the pod's 28 GiB floor; an
independent four-profile check at p = 0.05 in review peaked at 2,532 MiB). **Pod-side preflight** before the evaluate and
the doubling stage (`memory_preflight`): real tasks in child processes, one evaluate task per rule and one doubling task,
each writing its production record (not run again); the largest peak times a margin of 1.25 for variation across
markets, rules and winners; the cgroup limit and the parent's own peak; workers = min(current limit,
floor((0.9 x limit - parent) / (1.25 x peak))), saved in `memory_preflight_<stage>.json`; the driver refuses if no task
fits. **A task whose record already exists is no measurement** (review r4): the child reports the task status, and a
"skipped" task is replaced by the next unfinished task of the same rule (evaluate) or stage (doubling). A retry reuses a
saved measurement only if it applies (record version 2 with an explicit "done" status for every measured task, so
draft-4 records are never reused; same memory limit and margin; measured jobs in the current job list; for the
evaluation, a measurement for every current rule); with neither, the driver refuses. **A measurement never removes a
job from dispatch** (review r5): every job of the stage passes through `_run_one`, which skips a valid record and
recomputes a missing or damaged one; only the cost admission counts the tasks measured in the same command as done. **The chosen limit persists across commands:** it is saved in
`memory_workers.json` with the memory limit, and every later command on that output (a separate stage, a resumed run)
starts from the lowest saved limit that matches its memory limit; the diagnostics (two profiles per task, below the
evaluate task) refuse to dispatch without such a saved limit. **Admission and the preflight:** before a stage the cost admission covers the preflight's serial tasks
plus the remaining jobs at the current limit; after the preflight it runs again for the remaining jobs at the chosen
limit, and stops between stages if the cap would be passed.

**Billed pod time** (one 16-vCPU pod, 0.56 USD per hour; `docs/revision/churn/churn_cost.py`): the gate cell serially,
then per rate the 18 searches in two waves of 16; the evaluation as three serial preflight tasks plus 15 jobs in two waves
of 9; the doubling as one serial preflight task plus 17 jobs in two waves of 9; the diagnostics in two waves of 9; plus
0.6 hours of preparation and idle: **6.88 hours, 3.85 USD** (5.95 hours and 3.33 USD without the serial preflight tasks).
If the preflight cuts the evaluation workers to 2, the same arithmetic gives 12.44 hours, 6.97 USD, still below the
stop cap; the admission after each preflight recomputes the stage cost at the chosen workers. The serial tasks add
billed time, not core-hours, so the reservation below still covers the expected 3.85 USD.

**Budget** (author, 2026-11-10). The arm uses the shared ledger category `followup` (cap 72 USD for all follow-up runs since the author's approval of 2026-11-12, earlier 22 USD; the arm's stop cap stays 8 USD).
Before the pod: `docs/revision/followup/budget_followup.py --reserve churn-pod 8.32` (amended 2026-11-12, launcher review
r1: the wrapper reserves 8.32 x 1.25 = 10.40 USD, the watchdog bound of 1.3 x the stop cap; the earlier 4.43 USD
estimate padded to 5.54 USD would not cover that bound). **Stop cap 8.00 USD, an estimate-based stage-admission limit.** No running
stage is ever killed (author, 2026-11-10): before each stage the driver adds the pod time billed since allocation at the
pod's actual hourly price, the charges of earlier failed attempts, and the stage's estimate, and stops between stages
if the sum would pass the cap, then reports. Production runs refuse to start without `--started` (the allocation time)
and `--usd-per-hour`; with `--prior-usd`, all are saved in `run.json`. A stage that overruns its estimate can end above
the cap.

**Launcher** (a copy of `results/pods/reset_pod.sh` with `podctl.py`, unchanged pod safety; draft
`docs/revision/churn/churn_pod.sh`, installed in `results/pods/` after review): code and tarball guards; creation only
before the hard deadline; the price checked against the ceiling `MAXCPH`; the memory floor (28 GiB); the gate, then the
stages, each started only if no STOP file exists and the soft deadline has not passed (the soft deadline is the cap at
the ceiling, net of earlier attempts' charges); at the soft deadline it writes STOP, so the pod stops after the running
stage. **The one exception to "no running stage is killed":** the `podctl.py` watchdog deletes the pod at 1.3 times the
cap at the price ceiling (10.40 USD at most for this arm), also mid-stage, as an absolute guard against a hung pod. Spend
(amended 2026-11-12, launcher review r1) is recorded as the account balance difference (`podctl.py spend NAME`, at
least an hour after the watchdog ends); the launcher prints only estimates. Its attempts file holds each pod's id,
request time and deletion time. The launcher passes to the driver the live pod's request time as `--started`, its
actual price, and as `--prior-usd` the operator's `PRIOR` (recorded spend of earlier launches of this arm) plus this
launch's deleted attempts charged at the ceiling from their request times, rounded up. Both deadlines are net of
`PRIOR`, so the 10.40 USD bound holds across launches. An EXIT, INT or TERM trap pulls the records, verifies them against the inventories, deletes the pod, and
verifies the deletion; the watchdog keeps deleting until no pod of this name remains.

## 8. Steps

1. Internal review of this plan to consensus; freeze it (commit).
2. The author's approval of the follow-up limit is recorded; the reservation of 10.40 USD under `followup` (1.3 x the 8 USD stop cap).
3. One pod: the p = 0 gate, then the 36 cells; delete the pod and verify the deletion; record the spend.
4. Analysis in `docs/revision/posthoc/` (tested first); a paper paragraph and table, labelled exploratory.

## 9. Commands behind the numbers

- Registered values: `python3 -c "import json;p=json.load(open('docs/revision/posthoc/posthoc.json'))['doubled']['D2+H3'];print(p['absolute'],p['pooled'])"`
  (C* 0.0856, R3 0.0649; C* - R3 0.02072 base, 0.02962 doubled; B3 - R3 0.1734 base, 0.1698 doubled).
- Timing and peek: `uv run python docs/revision/churn/churn_timing.py` (40 fresh0 evaluation seeds; 6.48, 7.34, 8.62 s).
- Memory: `uv run python docs/revision/churn/churn_memory.py none` and `... 0.05` (981.0 and 1,084.4 MB).
- Cost: benchmark arithmetic over `experiments/v2/benchmark/timings.json` with the measured slowdowns, the worker limits
  above and two waves per stage (41.06 core-hours, 4.43 USD).
- Billed time: `uv run python docs/revision/churn/churn_cost.py` (6.28 hours of stages plus 0.6, 6.88 billed hours,
  3.85 USD; 5.95 hours, 3.33 USD without the serial preflight tasks; 12.44 hours, 6.97 USD at two evaluation workers).
- Reselection-by-regeneration cost: `sim/manifest_v2.py` `menu_families` and `bank_rules(ctx, fam, 3, False)` over the six
  markets and three rules: 60 D2+H3 and 60 X7-SC searches per rate, 12.19 USD per rate.
- Tests: `uv run pytest -q docs/revision/churn` (32 passed, 146 s).
