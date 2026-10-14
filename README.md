# Touchstone

Rules for markets of adaptive agents.

A touchstone is a cheap stone test of a gold claim. This project studies the
cheap test of a compute claim: which allocation and audit rules keep a market
efficient when the participants are heterogeneous, adaptive, and strategic.

## Thesis

Do not make every agent smarter. Design the institution. The object of study is
the rule set: what information is revealed, what commitments are enforced, how
outcomes are verified, and how participants can manipulate the rules.

## The falsifiable claim

Provisional numbers, locked on 2026-10-28 from the tuned-baseline runs. The
formal predicate lives in the design spec, section 8, and in
`scripts/check_claim.py`. This paragraph restates it and nothing more.

> In a simulated claimed-quality market with heterogeneous providers, with a
> total audit budget of **5% of the calibrated first-best surplus**, the
> proposed rule keeps gross efficiency at or above **90% of first-best**
> (lower 95% bound) and holds the best-found gain of the **headline adversary
> position** (for H2, selected on training seeds from three pre-registered
> positions; for H1, the median position) at or below **0.30 of the mean
> first-best surplus per provider** (upper 95% bound), where gain is profit
> beyond a **chosen truthful reference policy** (its matched truthful twin,
> honest-max, or abstention, selected per cell on training seeds), against the
> **sealed held-out adversary families that the pre-lock coverage study
> admits as confirmatory**, under a pre-registered search whose objective
> is that same gain statistic (for the LLM family, a fixed five-episode
> procedure rather than a search), while posted prices with random audits and a
> second-score auction with random audits, at the same budget, each either
> suffer at least **5 points more inflation-caused efficiency loss** than
> the proposed rule (loss measured against the same attack policy with its
> inflation removed) or allow best-found gain of **1.0 or more** in the same
> units (lower 98.75% bounds), for at least one confirmatory held-out
> family.

"Best-found" is deliberate. A search gives a lower bound on the true best
response, and gain is the difference of two searched values. The claim is
about the pre-registered search, not about all strategies. Each clause
returns PASS, FAIL, or INCONCLUSIVE; the claim passes only if every clause
passes.

If this claim fails, the project stops or the claim is rewritten. The rewrite
must be dated and must explain which number moved and why.

## Definitions

| Term | Definition |
|---|---|
| First-best surplus, S* | Maximum-weight assignment of jobs to providers at full effort on true quality, no audits. Computed per seed. |
| Truthful claim | A claim at or below the effort chosen for the round. Claim semantics are the same under every rule. |
| Gross efficiency | Realized surplus before audit cost, divided by S*, measured with true delivered quality. |
| Adversary gain | (Adversary's profit minus its reference profit, same seeds) divided by S*/N, per seed, where the reference is one policy chosen per cell on training seeds among its matched truthful twin, honest-max, and abstention; reported as the mean of per-seed ratios. |
| Audit spend | Total audit cost; must not exceed the calibrated budget B in any seed. Reported also as cost divided by S*. |
| Held-out family | A family sealed before the lock by a separate session and never executed before the evaluation freeze, on final evaluation seeds held by that session. |

## Setting

A simulated compute market with a trusted operator.

- Buyers have jobs and a value per unit of delivered quality. They are passive.
- Providers have a true quality, a claimed quality, and a cost.
- The operator allocates workloads, pays providers, and spends an audit budget
  to verify claims.
- An audit reveals the true quality of one delivered job at a fixed cost.

The operator is trusted in this phase. Removing the operator is out of scope.

## Baselines

1. Posted prices with no audits (reported, not in the predicate).
2. Posted prices with random audits at the same audit budget.
3. Second-score sequential auction with random audits at the same budget.

Baselines are tuned before the lock by a pre-registered procedure with the
same budget the proposed rule gets. A proposed rule that does not beat
baselines 2 and 3 on the predicate is not a result.

## Adversary model

Adversaries are optimizers, not hand-written scripts. Each provider policy is
searched to maximize normalized gain over its chosen truthful reference
against the frozen mechanism, under a search budget fixed at the lock.

Development families: fixed cheat (D1) and adaptive cheat (D2). Neither can
exit or re-enter.

Held-out families, sealed before the lock by a separate session, never run
before the evaluation freeze: an LLM provider (H1) and a parametrized family
that uses information D2 cannot (H2).

Pre-declared stress test, public and reported separately: identity
replacement (H3), exit after a failed audit and re-enter under a fresh
identity.

## Pre-registration protocol

Two freezes.

1. Lock, **2026-10-28**: locked evaluation config, the admissible rule class,
   tuned baselines, executable family definitions, hashes of the measurement
   pipeline, the claim predicate script, the coverage study, the sealed
   held-out bundle hash, and a statement that exactly one proposed rule will
   be evaluated. Signed tag, public timestamp. Only then is the proposed rule
   designed.
2. Evaluation freeze, **2026-11-11**: the proposed rule, its parameters, and
   its rule description are frozen in a second signed tag. Everything else
   was already fixed by the lock tag, except a named allow-list (the
   proposed-rule module, its config and description, the plot script, and
   docs), and the sealed bundle and its logged repair patches, which are
   checked by their own hashes. Held-out families run only after this
   tag.

Lock commit: _not yet locked_. Freeze commit: _not yet frozen_.

## Plan

| Dates | Work | Gate |
|---|---|---|
| 10-14 to 10-17 | Market, baselines, honest policies, metrics | Timed pilot |
| 10-18 to 10-24 | Search, families and twins, LLM harness, stress-test policy, manifest, calibration, baseline tuning, coverage study, token pilot | B1 fixture check; full manifest under 17 core-hours |
| 10-25 to 10-28 | Sealed bundle by a separate session; claim script; lock | Signed tag, public timestamp |
| 10-29 to 11-11 | Proposed rule and its description; stress test on it | Evaluation freeze |
| 11-12 to 11-18 | Unseal; held-out runs; figures | Hash verified; claim check |
| 11-19 to 11-25 | One page. Decide. | |

## Kill criteria

Stop the project if either of these holds at the end of week 5:

- All rules produce the same curve within seed noise.
- A plain random-audit rule dominates the proposed rule.

Either outcome is a cheap, honest answer.

## Out of scope

- Blockchains, tokens, and decentralized operators. A chain earns a place only
  when the trusted-operator assumption must be removed. That is a later phase.
- Pricing of compute as a financial instrument. This project sits before that
  layer, see Positioning.
- Visual simulation, dashboards, or a general agent framework.

## Positioning

Compute becomes a commodity only after it can be graded. Grain needed grading
standards before futures could trade on it. Compute today is sold on claimed
quality: latency, correctness, availability. Touchstone studies the layer that
turns a claimed quality into a graded one at a cost the market can bear.

Three layers, bottom to top:

1. Verification primitives. Proof of useful work, verifiable inference, and
   related schemes set the cost of one audit. Touchstone takes that cost as a
   parameter and does not propose new primitives.
2. Market rules. Allocation and audit rules given a verification cost. This is
   Touchstone.
3. Standardized contracts. Once quality is graded, compute can trade as a
   commodity with standard delivery terms. Regulatory and contract-design work
   lives here.

Related prior work by the author:

- `../touchstone-meter`: buyer-side auditor for paid inference (model, precision,
  token billing). A layer 1 primitive. It measures one audit; this project
  decides when to spend one.
- Proof-of-demand and proof-of-useful-work work: layer 1 input (link to add).
- Commodity-market and regulatory work: layer 3 consumer of this project
  (link to add).

## Prior art

Read before designing the rule.

- Bergemann and Morris, Robust Mechanism Design.
- Duetting et al., Optimal Auctions through Deep Learning (RegretNet).
- Zheng et al., The AI Economist (two-level RL; a different question).
- Live decentralized compute markets: Akash, Gensyn, Bittensor.
- Verifiable inference and proof-of-useful-work literature.

## Status

Week 1. Repository created 2026-10-14. No code yet.
