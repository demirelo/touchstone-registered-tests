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

> In a simulated compute market with heterogeneous buyers and providers, an
> allocation-plus-audit rule with audit spend of at most **5% of first-best
> surplus** keeps realized efficiency at or above **90% of first-best** and
> holds any single adversary's best-response gain below **3% of first-best
> surplus**, against **two adversary families and one identity-replacement
> attack** not used during development, while posted prices and a second-price
> auction under the same audit budget either lose **20 or more points of
> efficiency** or allow adversary gain above **10%**.

If this claim fails, the project stops or the claim is rewritten. The rewrite
must be dated and must explain which number moved and why.

## Definitions

| Term | Definition |
|---|---|
| First-best surplus, S* | Total buyer value minus total true provider cost under honest reporting and optimal allocation. |
| Efficiency | Realized surplus divided by S*, measured with true (not claimed) quality. |
| Adversary gain | An adversary's best-response profit minus its honest profit, divided by S*. |
| Audit spend | Total verification cost divided by S*. |
| Held-out adversary | An adversary family that was not run against any version of the proposed rule before the threshold lock. |

## Setting

A simulated compute market with a trusted operator.

- Buyers have workloads, budgets, and a value that depends on delivered quality.
- Providers have a true quality, a claimed quality, and a cost.
- The operator allocates workloads, pays providers, and spends an audit budget
  to verify claims.
- An audit reveals the true quality of one delivered job at a fixed cost.

The operator is trusted in this phase. Removing the operator is out of scope.

## Baselines

1. Posted prices with no audits.
2. Posted prices with random audits at the same audit budget.
3. Second-price auction with random audits at the same audit budget.

A proposed rule that does not beat all three on the stated thresholds is not a
result.

## Adversary model

Adversaries are optimizers, not hand-written scripts. Each provider policy is
trained to maximize its own profit against the frozen mechanism.

Development adversaries:

- Quality overclaiming with a fixed markup.
- Learned overclaiming (RL or LLM policy) against the frozen rule.

Held-out adversaries (chosen and sealed before the lock, not run until
evaluation):

- Family A: to be sealed on the lock date.
- Family B: to be sealed on the lock date.
- Identity replacement: a provider that exits after a bad audit and re-enters
  as a new identity.

## Threshold lock protocol

1. Build the market and run the three baselines first.
2. On the lock date, fix every number in the claim and seal the held-out
   adversary families. Record the commit hash in this file.
3. Only then design the proposed rule.

Lock date: **2026-10-28**. Lock commit: _not yet locked_.

## Plan

| Weeks | Dates | Work |
|---|---|---|
| 1 to 2 | 2026-10-14 to 2026-10-28 | Smallest market. Three baselines. Lock thresholds. |
| 3 to 4 | 2026-10-29 to 2026-11-11 | Optimizer adversaries. Proposed rule. Identity replacement. |
| 5 | 2026-11-12 to 2026-11-18 | The one curve: adversary gain against audit spend, one line per rule. |
| 6 | 2026-11-19 to 2026-11-25 | One page. Decide. |

## Kill criteria

Stop the project if either of these holds at the end of week 5:

- All rules produce the same curve within seed noise.
- A plain random-audit rule dominates every proposed rule.

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

Related prior work by the author (links to be added):

- Proof-of-demand and proof-of-useful-work work: layer 1 input.
- Commodity-market and regulatory work: layer 3 consumer of this project.

## Prior art

Read before designing the rule.

- Bergemann and Morris, Robust Mechanism Design.
- Duetting et al., Optimal Auctions through Deep Learning (RegretNet).
- Zheng et al., The AI Economist (two-level RL; a different question).
- Live decentralized compute markets: Akash, Gensyn, Bittensor.
- Verifiable inference and proof-of-useful-work literature.

## Status

Week 1. Repository created 2026-10-14. No code yet.
