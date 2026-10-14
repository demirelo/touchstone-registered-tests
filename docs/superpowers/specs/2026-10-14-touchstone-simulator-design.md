# Touchstone simulator: design

Date: 2026-10-14. Status: draft for review.

## 1. Goal

Build a simulator that draws one curve honestly: adversary gain against audit
spend, one line per market rule, one panel per adversary family. The curve
tests the claim in the README. The simulator is generic. Application areas
(inference tokens, GPU hours) are configuration profiles added later.

Target venue: AAMAS or a NeurIPS/ICLR workshop. Written so that one theorem can
be added later for EC.

## 2. Scope

In scope:

- A generic claimed-quality market with a trusted operator.
- Three baseline rules and an interface for proposed rules.
- Parametrized provider policies with a best-response optimizer.
- LLM actors as a first-class actor type for any role.
- A sealing protocol for held-out adversaries.
- Metrics, the curve, and a pass/fail check against the README claim.

Out of scope for this spec:

- Strategic buyers. Buyers are truthful and non-strategic.
- Collusion between providers.
- Decentralized or untrusted operators, chains, tokens.
- Any proposed rule. Rules are designed after the lock date, 2026-10-28.
- Application profiles. They are listed in section 10 as later work.

## 3. Market model

Time is discrete, rounds t = 1..T, default T = 200.

Jobs. Each round J jobs arrive, default J = 50. A job has a size s_j > 0 and a
value per unit v_j > 0. Buyer value for delivered quality q is v_j * s_j * q,
with q in [0, 1]. Job parameters are drawn each round from a configured
distribution. Buyers report values truthfully.

Providers. N providers, default N = 10. A provider has:

- a quality ceiling q_max_i in [0, 1], fixed per provider;
- a cost function c_i(q) per unit, increasing in q, default c_i(q) = a_i + b_i * q;
- a capacity k_i in units per round;
- an identity id. A provider may exit and re-enter with a fresh id at entry
  cost e >= 0. Default e = 0, which is the hard case.

Each round a provider's policy chooses:

- a true quality q_i in [0, q_max_i], the effort it will deliver;
- a claimed quality c_i in [0, 1];
- a bid, for rules that take bids;
- whether to exit and re-enter.

Delivered quality for a job is clip(q_i + eps, 0, 1), eps ~ N(0, sigma).
Cost is paid on true quality. The gap c_i - q_i is the lie. Lower q_i lowers
cost. That cost saving is the incentive to cheat.

Audits. One audit costs alpha per audited job and reveals delivered quality
exactly. The operator has an audit budget per round, expressed as a share of
first-best surplus.

Operator. Trusted. Sees claims, bids, job parameters, and audit results. Does
not see true quality unless audited.

## 4. Mechanism interface

One abstract class with four methods, called in order each round.

```python
class Mechanism:
    def allocate(self, jobs, offers, state) -> Assignment
    def price(self, assignment, offers, state) -> Payments
    def audit(self, assignment, state, budget) -> list[JobId]
    def enforce(self, audit_results, state) -> State
```

`offers` holds each provider's claim, bid, and capacity. `state` is the
operator's memory: per-identity history of claims, audits, failures, payments,
bans, and escrow balances. The interface is wide enough for reputation-weighted
audits, bonds, and score-based allocation without change.

Baselines:

- B1 posted, no audit. Three price tiers by claimed quality bands. Jobs fill the
  top tier first, random within a tier, up to capacity. No audits.
- B2 posted, random audit. B1 plus uniform random audits until the round budget
  is spent. A failed audit (delivered < claim - tol) refunds the payment and
  bans the identity for L rounds.
- B3 second-price, random audit. Per job, score = v_j * s_j * claim - bid.
  Highest score wins and pays the second-highest score equivalent. Same audits
  and enforcement as B2.

Defaults: tol = 0.05, L = 20.

## 5. Actors

A policy maps a provider's own view to an action. The view holds the
provider's own parameters, its own history (claims, audits on it, penalties,
payments), the round index, and public prices. No view of other providers'
private information.

Parametrized families, used in development:

- D1 fixed markup. q_i = q_max_i * (1 - u), claim = min(1, q_i + m). Knobs u, m.
- D2 adaptive. Knobs: base effort cut u0, base markup m0, drop in markup after
  an audit d, recovery rate r per round without audit, re-entry threshold on
  penalties.

Optimizer. CMA-ES over the knobs. Objective: the adversary's total profit over
T rounds against the frozen rule, single deviator with all other providers
honest, averaged over S seeds with common random numbers. All-deviators
(iterated best response, 3 sweeps) is a robustness table, not the headline.

LLM actors. An actor type that can fill any role: provider, buyer, or a
proposed-rule component. The actor receives the rules in plain text and its own
view each round, and returns an action in a fixed JSON schema. Fixed model,
temperature 0, every prompt and response logged to disk. Cost per run is
recorded. A malformed response falls back to the honest action and is counted.

## 6. Held-out families and sealing

Held-out families are never run against any proposed rule before the lock date.

- H1 LLM provider. The LLM actor in the provider role, with a sealed system
  prompt.
- H2 a parametrized family whose strategy space D2 cannot express. Spec sealed.
- H3 identity replacement. Exit after a failed audit, re-enter with a fresh id
  at entry cost e. Spec sealed.

Protocol:

1. Before the lock date, write `sealed/heldout.md` outside the repo with the
   full spec of H1, H2, H3, including prompts and knob ranges.
2. On the lock date, commit the SHA-256 of that file into the README together
   with the final threshold numbers and the commit hash of the baseline run.
3. In week 5, add the file to the repo and verify the hash in CI.

The engine does not enforce this. The git history does.

## 7. Metrics

All quantities are totals over T rounds unless stated.

- First-best surplus S*. Per round, the assignment on true quality ceilings
  that maximizes sum of v_j * s_j * q - c_i(q) * s_j subject to capacity, with
  q = q_max_i and no audits. Solved by linear assignment on unit slots.
- Realized surplus. Sum over delivered jobs of v_j * s_j * q_delivered minus
  c_i(q_true) * s_j. Uses true quantities, never claims.
- Efficiency = realized surplus / S*. Audit cost is excluded here and reported
  as its own axis. Net efficiency = (realized - audit cost) / S* appears in
  tables.
- Audit spend = total audit cost / S*.
- Adversary gain = (profit of adversary - profit of the same identity under the
  honest policy, same seeds) / S*.
- Loss to others = (S* - realized surplus) attributable to the adversary,
  reported in tables.

## 8. The curve and the claim check

Sweep the audit budget over {0, 1, 2, 5, 10, 20} percent of S*. For each rule,
each adversary family, and each budget, run the optimizer and record the best
adversary gain, efficiency, and audit spend. 20 seeds. Plot mean and 95%
confidence band.

Figure 1: adversary gain against audit spend, one line per rule, one panel per
family. Figure 2: efficiency against audit spend, same layout.

`scripts/check_claim.py` reads the results and prints PASS or FAIL for each
clause of the README claim at the 5% budget.

## 9. Candidate results to derive

These are hypotheses to test, not claims.

- Inspection-game bound. Under random audits with probability p and penalty P,
  cheating by margin g is deterred when p * P >= g. The curve should show the
  gain dropping to zero near that p for B2 and B3.
- Reputation lowers the price of deterrence. Audit probability conditioned on
  history should reach the same gain at lower audit spend than uniform audits.
- Zero entry cost kills bans. With e = 0, any rule whose only penalty is a ban
  has adversary gain bounded below by the per-round cheating profit. Only
  escrow-funded penalties (bonds) deter.
- Noise floor. With delivery noise sigma, any tolerance tol < sigma produces
  false failures for honest providers, and the efficiency line of honest
  markets falls. This sets a floor on useful audit precision.

If the second and third hold, they are the candidate theorem for an EC version.

## 10. Application profiles (later)

A profile is a YAML file that fixes distributions and names:

- inference tokens: quality is fidelity to the promised model and precision;
  size is tokens; audit cost from touchstone-meter's per-probe cost.
- GPU hours: quality is delivered over promised throughput; size is GPU hours;
  audit is a benchmark job.

No code changes are expected for a profile.

## 11. Layout

```
touchstone/
  sim/
    market.py        # entities, round loop, RNG with common random numbers
    mechanisms/      # base.py, posted.py, posted_audit.py, second_price.py
    policies/        # honest.py, markup.py, adaptive.py, llm.py, identity.py
    optimize.py      # CMA-ES best response
    metrics.py       # S*, efficiency, gain, audit spend
    llm_actor.py     # prompt building, JSON schema, logging, fallback
  experiments/       # YAML configs: market, rule, family, budget sweep, seeds
  scripts/
    run.py           # one config -> results CSV
    sweep.py         # the budget sweep
    plot.py          # Figures 1 and 2
    check_claim.py   # PASS/FAIL against README thresholds
  tests/
  docs/superpowers/specs/
```

Dependencies: numpy, scipy, cma, pyyaml, pandas, matplotlib, pytest. The LLM
actor uses the Anthropic SDK behind a thin interface so another provider can be
swapped in.

## 12. Tests

- Honest policy gives adversary gain of exactly zero under every rule.
- Efficiency is never above one.
- One provider, one job: S* matches the closed form.
- Same config and seed give a byte-identical CSV.
- Audit spend never exceeds the round budget.
- B1 with full markup and zero effort gives positive adversary gain.
- Every mechanism passes one shared harness test: a full run on a tiny market.
- LLM actor: a malformed response falls back to honest and is counted.
- Sealing: a test verifies the sealed file hash once the file is present.

## 13. Timeline

| Weeks | Dates | Work |
|---|---|---|
| 1 to 2 | 2026-10-14 to 2026-10-28 | Market, B1 to B3, D1, D2, optimizer, metrics, sweep. Lock. |
| 3 to 4 | 2026-10-29 to 2026-11-11 | Proposed rule(s). LLM actor. H3. |
| 5 | 2026-11-12 to 2026-11-18 | Unseal. Run all families. Figures. |
| 6 | 2026-11-19 to 2026-11-25 | One page. Decide. |
