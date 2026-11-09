# Reset experiment: plan (draft 1, 2026-11-09; not approved; no spend)

**Why.** The round-9 fresh reviewer (problem 2, `docs/paper/external-review-r9.md`): the gain is excess profit when
identity replacement is available; it does not show how much of that profit comes from the ability to replace an
identity. The paper's premise is that free replacement makes a ban costless and that R3 removes that advantage. This
plan measures the value of replacement directly.

**Status.** Draft for internal review (Sol + Astra), then a decision card for the author. Nothing runs before the author
approves the spend. This file is frozen (commit hash recorded in the ledger) before any paid cell starts.

## 1. What already exists (free, seen before this plan)

The D2+H3 family is D2 plus one binary knob `x` (`sim/policies/identity.py`: `x = 1` exits in the round after a failed
audit and re-enters under a fresh identity; `x = 0` is plain D2). The second test registered D2 searches at the headline
market only (design 8.1, "Matched core extras"). At `headline@rho0.2`, same 200 evaluation seeds, same frozen reference
per rule (checked: `seeds` and reference `upstream` hashes equal):

| Rule | g(D2+H3) | g(D2) | Replacement increment I = g(D2+H3) - g(D2) | Paired SE of I | D2+H3 flagged |
|---|---:|---:|---:|---:|---|
| B2 | 0.5851 | 0.0027 | 0.5824 | 0.0011 | no |
| B3 (F000) | 0.3502 | 0.0435 | 0.3067 | 0.0012 | yes |
| R3 (F111) | 0.0486 | 0.0361 | 0.0124 | 0.0009 | yes |
| C* | 0.0872 | 0.0433 | 0.0439 | 0.0008 | no |

Source: `results/v2/eval/all/evaluate/headline@rho0.2__{rule}__{D2+H3,D2}__profit.json`, field `gain`; flags from
`report.json` `search_flagged`. (At `headline@rho1`, R3 and C* are in the terminal-reserve collapse and I is 0.0025.)

Reading: at the headline market, replacement accounts for about 88% of the attacker's gain against B3 and about a quarter
against R3; the B3 - R3 gap is 0.302 with replacement and 0.007 without. These numbers are exploratory: they were seen
before this plan, so the fresh-market part below is a replication on markets whose D2 results nobody has seen.

## 2. Estimand and design (fresh markets)

- **Estimand.** For rule r in {B3 (F000), R3 (F111), C*} and fresh market m: I(r, m) = mean over the 200 evaluation seeds
  of g(D2+H3) - g(D2), both evaluated against the same frozen truthful reference of (r, m). Pooled: equal market weights.
  Derived: the share of the B3 - R3 gap due to replacement, 1 - [g_B3(D2) - g_R3(D2)] / [g_B3(D2+H3) - g_R3(D2+H3)].
- **New cells.** D2 x {F000, F111, C*} x fresh0..fresh5 at rho 0.2: **18 search cells**, each with the registered D2
  search budget, the registered seeds (training seeds for search, the 200 evaluation seeds of the market for evaluation),
  and the existing frozen references and D2+H3 records (no reference is re-selected; no D2+H3 cell is rerun).
- **Doubling checks.** All 18 cells, as design 6.5 (doubled restarts; held-out evaluation of the doubled winner on the
  same seeds); flags reported beside the estimates.
- **Code.** The frozen second-test code at the protocol-v2 tag; only a new manifest lists the 18 cells. Any code change
  is a deviation and is recorded.
- **Not in scope (option B, priced below, not proposed by default).** An X7-SC variant with replacement disabled (`h_R = T`,
  `lambda = 1`, other knobs searched): 18 more cells. It is a new family, so its result would be a new descriptive
  analysis, not a replication of a registered cell.

## 3. Analysis (fixed now)

- Per market and pooled: I(r, m) with a paired nominal 95% interval over seeds (descriptive; the uncertainty is over seeds
  only, conditional on the six markets and the frozen policies and references, as in the paper).
- The contrasts I(B3) - I(R3) and I(C*) - I(R3), per market and pooled, and the derived share of the B3 - R3 gap.
- The doubled-winner versions of the same quantities, as in the paper's `tab:ph-doubled`.
- No confirmatory test, no multiplicity family, no change to any registered decision.

## 4. Pre-specified expectations (written before any fresh D2 result exists)

From the headline result in section 1 we expect, on each fresh market: I(B3) > I(R3); I(C*) > I(R3); and a pooled share of
the B3 - R3 gap due to replacement of at least 0.5. Any of these failing is reported as a failed expectation in the
paper, with the same weight as a success.

## 5. What the paper would say

- If the expectations hold: R3's advantage over B3 is mainly the removal of the replacement payoff, and C* leaves more
  value in replacement than R3 does (a mechanism-level account the reviewer asked for).
- If they fail: the gain differences come mostly from non-replacement behaviour (bidding, shading, allocation), and the
  paper's framing must say so.
- Either way, section 1's headline numbers are labelled exploratory, and the fresh result is labelled as a follow-up
  analysis specified on 2026-11-09, after the round-9 review and after the headline D2 contrast was seen.

## 6. Cost (estimate; the benchmark rule of design 8.2 applies)

Units as design 8.2: one D2 cell = 1 unit + 0.16 for 200 evaluation seeds; a doubling check = 1 unit plus its held-out
evaluation. Measured cost of the second test's evaluation: 39.45 USD for about 696 units = **0.057 USD per unit**
(addendum; design 8.2 table).

| Option | Units | USD at 0.057 | With 30% contingency |
|---|---:|---:|---:|
| A. D2 on 6 fresh markets (18 cells + 18 doubling checks) | about 39 | about 2.2 | **about 2.9** |
| B. adds X7-SC with replacement disabled (18 cells x 2.5 x 1.16 + 18 checks x 2.5) | about 97 more | about 5.5 more | about 7.2 more |

Pods: 16 vCPU at at most 0.56 USD per hour, the existing launchers and guards (snapshot, tarball, history, AppleDouble,
`same_code`), one pod per market or one pod for all, deleted and verified after each run.

**Caps and stop rules.** Option A cap 4 USD; option B cap 12 USD in total. Stop at the cap; a failed attempt counts
toward it. No other paid work. Spend recorded in `docs/revision/budget-ledger.json` with a new reservation and in the
operations ledger. The author's approval sentence is recorded verbatim before the first pod.

## 7. Steps

1. Internal review of this plan (Sol + Astra) to consensus; freeze it (commit).
2. Decision card: option A (recommended), A + B, or no run.
3. On approval: manifest for the 18 cells; a local dry run of one cell on 10 seeds (free); then the pods.
4. Analysis: a new `reset` block in `posthoc_v2.py` (tested first), a new table, and a paragraph in section 9 of the paper
   with sites; section 1's headline numbers enter at the same time, labelled exploratory.
5. Internal review of the paper change, then the next external package.
