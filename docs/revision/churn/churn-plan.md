# Honest-churn arm: plan (draft 1, 2026-11-10; for internal review; no spend yet)

**Why.** The Fable 5.2 fresh review (problem 4, `docs/revision/roster/fable52-paper-r1.md`; triage
`docs/paper/fable52-triage.md`): in both tests the nine honest opponents never replace their identities, so after the
start a new identity almost always belongs to the deviating provider, and R3's newest-first targeting may owe its effect
to that. This arm lets the honest opponents churn and asks how much of R3's measured advantage remains. The author
asked on 2026-11-10 to "run all necessary sims"; nothing runs before this plan has internal consensus and the author's
approval is recorded in the budget ledger.

**Status.** Draft 1. Exploratory follow-up outside the registered protocol, specified after the second test's results
were seen. Not an independent replication.

## 1. What exists (free; seen before this plan)

- `sim/policies/honest.py` `HonestMax` never exits. `sim/market.py` `run_episode`: an action with `exit=True` retires the
  identity and re-enters under a fresh one in the same round (entry cost `e = 0`); same-round entrants are ordered by a
  salted rank. `ProviderView.rng` is seeded from the episode's per-round, per-entity `policy_seed`.
- The registered values this arm is compared with (no churn; `docs/revision/posthoc/posthoc.json`, `doubled.D2+H3`;
  command in section 9): pooled mean gain C* 0.0856, R3 0.0649; pooled C* - R3 0.0207; pooled B3 - R3 0.1734.
- Registered honest-replacement diagnostic (headline, one replacement at round 50): R3 audits 1.000 and 0.917 of the
  replacement's jobs in its first two ten-round bins, C* 0.428 and 0.161, B3 about 0.250 (`posthoc.json` `honest`).
- **Disclosed peek (timing check, 2026-11-10).** To price the churn slowdown, the registered no-churn F111 D2+H3 attack on
  fresh0 was rerun on the first 40 evaluation seeds under churn
  (`docs/revision/churn/churn_timing.py`): mean normalised profit 0.468 (no churn), 0.487 (p = 0.01), 0.521 (p = 0.05); the focal
  provider used 54.0, 36.7 and 6.8 identities per episode; honest replacements per episode 0, 18.25, 89.2. This is one
  rule, one market, the old attack, and no reference; the expectations in section 6 were written after it.

## 2. Estimand

For rule r in {R3 (F111), C*, B3 (F000)}, fresh market m and churn rate p:

g_p(r, m) = mean over the 200 evaluation seeds of the normalised gain of the D2+H3 attack selected by the registered
search under churn p, against the rule's frozen truthful reference played under the same churn.

Contrasts: d_p(m) = g_p(C*, m) - g_p(R3, m) and q_p(m) = g_p(B3, m) - g_p(R3, m), pooled with equal market weights, and
their changes from the registered no-churn values on the same seeds. These are differences between finite searches in a
changed environment, not identified optimal values.

## 3. Cells and execution contract

- **Churn model.** Each of the nine honest opponents plays honest-max delivery and offer and, in each round, retires its
  identity and re-enters under a fresh one with probability p (`docs/revision/churn/churn_v2.py` `HonestChurn`). The draw
  uses the episode's `policy_seed[t, e]`, so it is deterministic and the same for every rule on the same seed (common
  random numbers). **Rates p in {0.01, 0.05}:** with T = 200, about 18 and 89 honest replacements per episode (measured,
  section 1); at p = 0.05 each honest opponent is inside R3's fresh window (L = 10) about 1 - 0.95^10 = 40 percent of the
  time, at p = 0.01 about 10 percent. The low rate is mild churn; the high rate makes "newest" uninformative most of the
  time.
- **Cells.** {R3, C*, B3} x fresh0..fresh5 x {0.01, 0.05} at rho 0.2, D2+H3, registered search budget (5 restarts, 300
  evaluations, 5 training seeds), the market's 200 evaluation seeds, a doubling check with its held-out evaluation on
  every cell: **36 cells**.
- **Driver.** `docs/revision/churn/churn_v2.py` (under `docs/`: the code freeze allows changes only there). It runs the
  frozen `revision_v2` stage functions through `_run_one` and reuses the reset driver's helpers
  (`docs/revision/followup/reset_followup_v2.py`: input copies, pre-episode checks, follow-up freeze, acceptance,
  inventory). Churn enters only through `Cell.others`: `install()` wraps `revision_v2.train_cell` (which `eval_cell`
  calls), so search, twin search, the doubling stage's reference menu, and evaluation all run under churn; process pools
  install the wrapper in their initialiser. Churn job ids carry the suffix `|churn<p>` so they never overwrite the
  copied registered D2+H3 records that the reference menus read; each rate writes to its own directory
  (`results/v2/followup-churn/p<p>/`), never to `eval/all`.
- **References: reused, not reselected.** Each (market, rule) keeps its frozen truthful reference candidate, and every
  reference episode runs under the same churn, so the gain stays "excess over a truthful policy in the same
  environment". Reselecting the references under churn would need the full menus under churn, 60 D2+H3 and 60 X7-SC
  searches per rate, about 12.19 USD per rate (24.37 USD for both) before the churn slowdown (command in section 9). Cost
  of reuse: if another menu candidate is better under churn, the gain is overstated for that rule. The doubling stage's
  existing diagnostic reselects among the frozen menu under churn on the training seeds; its `reference_change` is
  reported for every cell.
- **Checks before any episode** (reset driver, plan draft 5): configuration hash equals the container hash; salt; known
  commit; runner and `sim/` equal protocol-v2; each job's runner, salt, configuration, root, seeds, rule parameters and
  context equal its frozen reference's provenance; output not inside `--src` or `eval/all`. Inputs (references, menu
  searches, bank sources) are copied read-only and hash-checked against the original records and freeze; the follow-up
  freeze and acceptance run before evaluation and doubling; a final inventory records every output hash, the
  environment, and the churn driver's hash.
- **Validation before spend (free, on the Mac).** (a) Unit tests: the churn policy is truthful and exits at rate p,
  deterministically; p = 0 never exits; the wrapper adds churning opponents to training and evaluation cells and leaves
  other jobs unchanged; churn job ids and provenance are distinct; newcomer audit shares by age. (b) A smoke-size run of
  the whole path for fresh0 R3 at p = 0.05 (input copies, search, freeze, acceptance, evaluation, doubling, diagnostics,
  inventory), which must show honest replacements in the evaluated episodes. Both pass:
  `uv run pytest -q docs/revision/churn` (6 passed). (c) Before the 36 cells, the pod runs the reset plan's reproduction
  gate if both arms share one pod; otherwise this arm's pod first reruns one registered no-churn cell
  (fresh0 F111 D2+H3) with p = 0 through this driver and must pass the reset plan's draft-5 criterion.

## 4. Diagnostics (evaluation only, no search)

For every cell, the selected attack is rerun on the evaluation seeds under churn with audit instrumentation
(`diagnostics` stage, `newcomer_shares`): the audited share of served jobs by identity age, in bins [0, 10), [10, 20),
[20, 50), [50, 200), separately for honest replacement identities, honest initial identities, and the focal provider's
identities; and the honest replacements per episode. The first bin answers whether R3's targeting now falls on honest
newcomers; the focal rows show whether the attacker is still found.

## 5. Analysis (fixed now)

- Per market and pooled g_p(r), d_p, q_p, with paired seed bootstrap intervals (9,999 resamples, percentile, 95 percent;
  the same resampled seed indices for every rule and rate of a market; pooled replicates resample seeds within each
  market and average the six market means), as in the reset plan, section 5.
- Changes from no churn: g_p(r, m) - g_0(r, m), d_p - d_0, q_p - q_0, paired by seed with the registered records (the
  same seeds; S* does not depend on churn).
- Doubled versions beside the base results; the reference-reselection diagnostic per cell.
- Sign counts over the six markets for d_p and q_p.
- No confirmatory test, no multiplicity family, no change to any registered decision; all results are labelled
  exploratory follow-up.

## 6. Pre-specified expectations

Written after the disclosed peek in section 1 and before any churn search. Scored on point estimates, as met (holds
under both the base and the doubled searches), failed (fails under both), or not established (the two disagree).

1. Pooled g_0.05(R3) exceeds the registered pooled no-churn g(R3) of 0.0649.
2. Pooled d_0.05 = C* - R3 is below the registered 0.0207.
3. q_0.01 = B3 - R3 is positive on all six markets.
4. Under R3 at p = 0.05, the audited share of honest replacement identities in their first ten rounds exceeds that
   under C* and under B3 (pooled over markets).

A failure is not read as evidence of a particular cause. Only if expectation 2 is met may the paper say that R3's
measured edge over C* shrinks when honest opponents churn; only if 4 is met that the targeting cost shifts to honest
newcomers.

## 7. Cost

Measured benchmark (`experiments/v2/benchmark/timings.json`, 0.108 USD per core-hour): per cell a D2+H3 search (2,084
s), the evaluation on 200 seeds (96.0 s per 160 seeds, scaled), the doubling check with its held-out evaluation (998 s),
and the diagnostic (a quarter of the evaluation), 3,232 s; churn slows an episode by 1.133 (p = 0.01) and 1.330
(p = 0.05) (section 1). 36 cells: **39.8 core-hours, 4.30 USD** at the benchmark price. Billed pod time on one 16-vCPU pod
at 0.56 USD per hour, 18 cells per rate in two waves, plus 0.6 hours of preparation and idle: **about 5.0 hours, 2.81
USD**. The plan uses the larger figure, 4.30 USD, with a cap of 7 USD (one early failure).

## 8. Steps

1. Internal review of this plan to consensus; freeze it (commit).
2. The author records the approval (limit and the follow-up cap) with `docs/revision/followup/budget_followup.py` or its
   successor for a second follow-up category.
3. One pod for the 36 cells after the gate in section 3 (c); delete it and verify the deletion; record the spend.
4. Analysis in `docs/revision/posthoc/` (tested first); a paper paragraph and table, labelled exploratory.

## 9. Commands behind the numbers

- Registered values: `python3 -c "import json;p=json.load(open('docs/revision/posthoc/posthoc.json'))['doubled']['D2+H3'];print(p['absolute'],p['pooled'])"`.
- Timing and peek: `uv run python docs/revision/churn/churn_timing.py` (40 fresh0 evaluation seeds; seconds 6.48, 7.34, 8.62).
- Cost: the benchmark arithmetic over `experiments/v2/benchmark/timings.json` in the fork report of 2026-11-10 (per
  cell 3,232.1 s; 36 cells 39.8 core-hours, 4.30 USD; billed 5.02 hours, 2.81 USD).
- Reselection cost: `sim/manifest_v2.py` `menu_families` and `bank_rules(ctx, fam, 3, False)` over the six markets and
  three rules: 60 D2+H3 and 60 X7-SC searches per rate, 12.19 USD per rate.
- Tests: `uv run pytest -q docs/revision/churn` (6 passed, 70 s).
