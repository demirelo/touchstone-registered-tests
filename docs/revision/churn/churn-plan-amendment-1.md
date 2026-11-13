# Honest-churn arm, amendment 1: rates 0.02 and 0.03 (2026-11-13; for internal review; no spend yet)

**Why.** External review round 4 (Fable 5.2, `docs/revision/roster/fable52-paper-r4.md`, section 4c and "Saturation")
found that the two rates of draft 6 lie on either side of the rate at which honest newcomers' jobs exceed R3's audit
quota: R3 audits 0.880 of honest replacements' jobs in their first ten rounds at p = 0.01 and 0.571 at p = 0.05
(`docs/revision/posthoc/churn.json`, pooled first bin, frozen winners), and the reviewer's arithmetic puts the crossing
near p = 0.028 for these parameters. The paper cannot say where between 0.01 and 0.05 R3's measured advantage ends. The
author chose on 2026-11-13 (board card `touchstone-churn-mid-rates`, answered in chat) to add p = 0.02 and p = 0.03
before Runs A and B.

**Status.** Exploratory follow-up outside the registered protocol. Written after the p = 0.01 and p = 0.05 results and
the round-4 review were seen; no p = 0.02 or p = 0.03 simulation has run, and no timing check was made at these rates.

## 1. What changes

Only the rate set. Everything else in draft 6 applies unchanged: the churn model, estimand (section 2), cells per rate
(B3, R3, C* x fresh0..fresh5 at rho 0.2, D2+H3, registered search budget, 200 evaluation seeds, a doubling check per cell),
the execution contract and gate (section 3), diagnostics (section 4), analysis (section 5), and the cost controls
(section 7). **Rates p in {0.02, 0.03}**: mean identity lifetimes 50 and about 33 rounds. 36 cells plus the p = 0 gate cell.

- Driver: `docs/revision/churn/churn_v2.py --rates 0.02,0.03` (no code change; its cost admission prices every p > 0 at
  the p = 0.05 slowdown, 1.33, which over-states these rates).
- Launcher: the reviewed `docs/revision/churn/churn_pod.sh` with `RATES=0.02,0.03` (a new environment setting, default
  0.01,0.05, refused unless every rate is in {0.01, 0.02, 0.03, 0.05} and none repeats; it passes `--rates` to every
  driver call and verifies each rate directory after RUN OK). The same review also fixes the end-state parse: the polled
  log tail holds several markers, and the launcher now reports the last one (it reported the first). Harness
  `test_churn_pod_harness.sh`, three new scenarios.
- Local output `results/v2/followup-churn-mid/` (the first arm's records are not touched). Run tag `churn-mid`; PRIOR 0.

## 2. Pre-specified expectations (written now, before any p = 0.02 or p = 0.03 search)

Scored as in draft 6 section 6: met (holds under both the frozen and the doubled searches, each against its own
values), failed (fails under both), not established (the two disagree); on point estimates; pooled values are
equal-weight means over the six markets. The p = 0.01 and p = 0.05 values are those of `churn.json`.

5. The pooled audited share of honest replacement identities in their first ten rounds under R3 is below its p = 0.01
   value and above its p = 0.05 value at both new rates, and lower at p = 0.03 than at p = 0.02.
6. Pooled C* minus R3 is lower at p = 0.03 than at p = 0.02.
7. Pooled g_0.02(R3) is below the midpoint of the no-churn and p = 0.05 values of pooled g(R3) (frozen: 0.168;
   doubled: 0.170).
8. B3 minus R3 is positive on at least five of the six markets at p = 0.02.

A failure is not read as evidence of a particular cause. The reviewer's crossing near p = 0.028 is an approximation; none
of these expectations depends on it holding exactly.

## 3. Analysis

`docs/revision/posthoc/churn_block.py` gains a `--rates` option (default 0.01,0.05), tested first; with `--rates
0.02,0.03` it reads the new records and writes `churn_mid.json` with the same statistics, pairing and bootstrap (the same
fixed seed), and the scoring of expectations 5 to 8. A combined table lists the five conditions p = 0, 0.01, 0.02, 0.03,
0.05 for both search versions. The analysis code is committed before any run on the new records.

## 4. Cost

The first arm cost 4.99 USD (8.87 billed hours at 0.56 USD/h) for p = 0.01 and 0.05, whose measured slowdowns sum to
2.463. Interpolating the slowdown linearly in p (1.182 at 0.02, 1.232 at 0.03; sum 2.414) gives about 8.7 billed hours,
**about 4.9 USD**. Stop cap 8 USD, as in draft 6; watchdog bound 1.3 x 8 = 10.40 USD; reservation
`python3 docs/revision/followup/budget_followup.py --reserve churn-mid-pod 8.32` (grant 10.40). Ledger: 57.51 USD spent
of the 123 USD limit; follow-up category 6.64 of 72 USD.

## 5. Steps

1. Internal review of this amendment and the launcher change to consensus; commit.
2. Reserve; dry-run guard; one pod: the gate, then the 36 cells; delete and verify; record the spend after the author's
   billing check.
3. Analysis (code first), paper text after review.
