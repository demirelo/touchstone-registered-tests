# Reset experiment: plan (draft 2, 2026-11-09; not approved; no spend)

**Why.** The round-9 fresh reviewer (problem 2, `docs/paper/external-review-r9.md`): the gain is excess profit when
identity replacement is available; it does not show how much of that profit comes from the ability to replace an
identity. This plan measures that, within the searched D2 family, on the second test's markets.

**Status.** Draft 2 answers internal review round 1 (`docs/revision/roster/{sol,astra}-reset-plan-r1.md`, both reject).
After consensus: a decision card for the author. Nothing runs before the author approves the spend. This file is frozen
(commit hash in the operations ledger) before any paid cell starts.

## 1. What already exists (free; seen before this plan)

The D2+H3 family is D2 plus one binary knob `x` (`sim/policies/identity.py`: `x = 1` exits in the round after a failed
audit and re-enters under a fresh identity; `x = 0` is plain D2). Design 8.1 listed D2 on all seven markets ("Matched core
extras"); budget cut 3 removed the fresh-market D2 cells, so D2 was run at the headline market only. At `headline@rho0.2`,
same 200 evaluation seeds, same frozen reference per rule (checked: `seeds` and reference `upstream` hashes equal):

| Rule | g(D2+H3) | g(D2) | I = g(D2+H3) - g(D2) | Paired SE of I | D2+H3 doubling check |
|---|---:|---:|---:|---:|---|
| B2 | 0.5851 | 0.0027 | 0.5824 | 0.0011 | not scheduled |
| B3 (F000) | 0.3502 | 0.0435 | 0.3067 | 0.0012 | flagged |
| R3 (F111) | 0.0486 | 0.0361 | 0.0124 | 0.0009 | flagged |
| C* | 0.0872 | 0.0433 | 0.0439 | 0.0008 | not flagged |

Source: `results/v2/eval/all/evaluate/headline@rho0.2__{rule}__{D2+H3,D2}__profit.json`, field `gain`; flags from
`report.json` `search_flagged`; the D2 cells had no scheduled doubling check. At `headline@rho1`, R3 and C* are in the
terminal-reserve collapse and I is 0.0025.

Reading, exploratory: at the headline market the D2+H3 search leaves about 0.31 more gain than the D2 search against B3,
and about 0.01 against R3; the B3 - R3 gap is 0.302 under D2+H3 and 0.007 under D2.

## 2. Estimand

For rule r in {B3 (F000), R3 (F111), C*} and fresh market m:

I(r, m) = mean over the 200 evaluation seeds of g(D2+H3 winner) - g(D2 winner),

both against the same frozen truthful reference of (r, m), so the reference term cancels. **I is a difference between two
prescribed finite searches over nested families (D2 within D2+H3), not an identified optimal value of replacement and not
a system-wide prohibition of replacement.** The two searches differ in dimension, Sobol starts, and corner sets (D2 128,
D2+H3 256 corner vectors), with the same restart and evaluation budgets; the two winners can differ in every knob, not
only `x`. A negative I can come from search error. The fixed-policy diagnostic in section 4 separates the switch from
re-optimisation.

## 3. Cells and execution contract

- **New search cells.** D2 x {F000, F111, C*} x fresh0..fresh5 at rho 0.2: 18 cells, exactly the design-8.1 cells that cut
  3 removed, with their registered settings (D2 knob space and budget, the market's training seeds for search, its 200
  evaluation seeds), each with a doubling check (design 6.5, held-out evaluation of the doubled winner on the same seeds).
- **Driver.** A separate follow-up script (`scripts/reset_followup_v2.py`, written and tested before any spend) that
  imports the frozen stage functions of `scripts/revision_v2.py` at the protocol-v2 tag (`job`, `stage_search`, the
  evaluation and doubling stages) and builds the 18 jobs from the uncut cell list. It bypasses only three things, each
  recorded as a deviation: the fixed manifest path and cut list (`sim/manifest_v2.py` `effective`), the hard-coded doubling
  eligibility (`doublings`), and the original freeze. It writes to a new directory (`results/v2/followup-reset/`) and a
  new freeze listing the 18 search, evaluation, and doubling records with their upstream hashes. It never writes to
  `results/v2/eval/all`.
- **References.** The existing frozen reference records are read, not re-selected; the driver refuses to start if any
  reference file's SHA-256 differs from the hash in the original records' `upstream`.
- **Configurations.** Linux pods from the same image as the evaluation; before any episode the driver checks that each
  fresh market's configuration hash equals the recorded container hash (`addendum.json` `deviations.configs`), so the
  new cells use the same configurations as the D2+H3 records they are paired with (the recorded 1-ulp deviation stays as
  it is).
- **Validation before spend (free, on the Mac).** (a) The driver reproduces the registered `headline@rho0.2|F111|D2`
  search and evaluation: identical selected knobs and per-seed gains. If not identical, stop and report. (b) Its tests:
  refuses a changed reference hash, a wrong configuration hash, and an output directory inside `eval/all`.

## 4. Diagnostics (evaluation only, no search)

For the base and doubled D2+H3 winners and the D2 winners, on all seven markets where they exist, on the 200 evaluation
seeds: the selected `x`; per episode the number of resets, the probability of at least one reset, the rounds of resets,
and the rounds spent banned. Check that every D2 winner has zero resets. **Fixed-policy switch:** each D2+H3 winner
re-evaluated with `x` set to 0 and every other knob unchanged; g(winner) - g(winner, x = 0) is the effect of the switch
without re-optimisation, reported beside I.

## 5. Analysis (fixed now)

- **Intervals.** Per market: paired seed bootstrap (9,999 resamples, percentile, 95%), the same resampled seed indices for
  every rule and family of that market, so contrasts across rules stay paired. Pooled: equal market weights; in each
  replicate, seeds are resampled independently within each market and the pooled statistic is the mean of the six market
  means; percentile interval. Nominal and descriptive; conditional on the six markets and the frozen policies and
  references.
- **Statistics.** I(r, m) and pooled I(r); the contrasts I(B3) - I(R3) and I(C*) - I(R3); the absolute gaps
  G(D2+H3) = g_B3 - g_R3 under D2+H3 and G(D2) under D2, pooled.
- **Share.** S = 1 - pooled G(D2) / pooled G(D2+H3), a ratio of pooled contrasts, computed in every bootstrap replicate.
  S is reported only if the lower bound of pooled G(D2+H3) exceeds 0.05; otherwise "not defined". No clipping; S can be
  negative or above 1. The absolute gaps are always reported beside it.
- **Doubled versions** of the same statistics, as in the paper's `tab:ph-doubled`.
- No confirmatory test, no multiplicity family, no change to any registered decision.

## 6. Pre-specified expectations and labels

Written before any fresh D2 result exists. **The six markets, their seeds, and their D2+H3 outcomes were already observed;
only the D2 outcomes are unseen.** This is a descriptive follow-up specified on 2026-11-09 after the round-9 review and
after the headline contrast was seen, not an independent replication.

Expectations: on each fresh market, I(B3) > I(R3) and I(C*) > I(R3); pooled S at least 0.5. Each failure is reported as a
failed expectation with the same weight as a success; a failure is not read as evidence for any particular cause (search
error and mixed outcomes are possible). A success supports only this statement: within the D2 family, at the fixed
parameters and search budgets, most of the B3 - R3 gap under the prescribed searches disappears when the attacker cannot
replace its identity.

## 7. Cost (benchmark rule of design 8.2)

Measured benchmark (`experiments/v2/benchmark/timings.json`): one unit = a headline D2+H3 cell at full utilisation, 0.579
core-hours, **0.0625 USD** at the benchmark's 0.108 USD per core-hour. Per D2 cell: 1 unit + 160 further seeds (0.046) +
doubling with held-out evaluation (0.479).

| Option | Units | USD | Cap |
|---|---:|---:|---:|
| A. 18 D2 cells with doubling checks, plus section 4 diagnostics (about 1 unit) | about 28.5 | about 1.78 | **2.50** |
| B. adds X7-SC with replacement disabled (`h_R = T`, `lambda = 1`; 18 cells x (2.248 + 0.046 + 1.232)) | about 63.5 more | about 3.97 more | 5.50 more |

Option B is a new family (no registered counterpart), so its result would be a new descriptive analysis; it is priced, not
recommended.

**Budget.** `docs/revision/budget-ledger.json`: spent 50.869 USD of the 55 USD approval limit (headroom 4.131); evaluation
39.449 of its 43 USD cap (headroom 3.551). Option A's cap (2.50) fits both, but it is new work: it needs its own approval
sentence, recorded verbatim, and a new ledger category `followup` with cap 2.50. Option B would need the approval limit
raised to at least 58.87 USD (50.869 + 2.50 + 5.50). A failed attempt counts toward the cap; stop at the cap.

## 8. Steps

1. Internal review of this plan to consensus; freeze it (commit).
2. Decision card: option A (recommended), A + B, or no run.
3. On approval: write and test the driver (TDD), run validation (a) and (b) on the Mac (free); then one pod for the 18
   cells, deleted and verified after the run.
4. Analysis: a new `reset` block in `posthoc_v2.py` (tested first), a table, and a paragraph in section 9 with sites; the
   section-1 headline numbers enter at the same time, labelled exploratory.
5. Internal review of the paper change, then the next external package.
