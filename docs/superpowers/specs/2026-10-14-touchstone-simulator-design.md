# Touchstone simulator: design

Date: 2026-10-14. Version 2, after a three-model review (Fable 5.1, Opus 5.5,
Astra). Status: draft for review. Section 14 maps review objections to
changes.

## 1. Goal

Build a simulator that draws one curve honestly: adversary gain against audit
spend, one line per market rule, one panel per adversary family. The curve
tests the claim in section 8. The simulator is generic. Application areas
(inference tokens, GPU hours) are configuration profiles added later.

Target venue: AAMAS or a NeurIPS/ICLR workshop. Written so that one
proposition from section 9 can become a theorem for an EC version.

## 2. Scope

In scope:

- A generic claimed-quality market with a trusted operator.
- Three fully specified, tuned baseline rules and an interface for one
  proposed rule.
- Parametrized provider policies with a pre-registered best-response search.
- An LLM actor in the provider role.
- A two-freeze pre-registration protocol (lock, then evaluation freeze).
- Metrics, the curve, and a formal claim predicate with a pass/fail script.

Out of scope for this paper:

- Strategic buyers. Buyers are passive and truthful.
- Collusion between providers.
- Decentralized or untrusted operators, chains, tokens.
- Any proposed rule. The rule is designed after the lock date, 2026-10-28.
- Application profiles. Section 10 lists them as later work.
- LLM actors in roles other than provider.

Participation is voluntary. A provider may abstain in any round. A buyer
accepts an offer only if its claimed value covers the price.

## 3. Market model

Time is discrete, rounds t = 1..T, default T = 200.

Jobs. Each round J unit jobs arrive, default J = 50. A job has value v_j > 0
per unit of delivered quality, drawn i.i.d. from a configured distribution.
All jobs have size 1. Buyer value for delivered quality y is v_j * y.

Providers. N providers, default N = 10. Each provider is an entity with a
current identity. An entity has:

- a quality ceiling q_max_i in (0, 1];
- a per-unit cost c_i(q) = a_i + b_i * q, with a_i >= 0, b_i > 0, for effort q;
- a capacity k_i jobs per round;
- an outside option of zero profit.

An entity may drop its identity and re-enter under a fresh one at entry cost
e >= 0, default e = 0. Entry cost is a destroyed resource: it enters surplus
and the entity's profit, not anyone's receipts.

Delivery. For a job served by provider i with effort q_i, delivered quality is
y = clip(q_i + eps, 0, 1), eps ~ N(0, sigma^2), default sigma = 0.05. Define
Q(q) = E[clip(q + eps, 0, 1)]. Cost a_i + b_i * q_i is paid per job served.

Round sequence. Every rule follows this order.

1. Draw the round's jobs.
2. Each active provider submits an offer or abstains. An offer is (claim
   c_i in [0, 1], per-unit bid, effort q_i in [0, q_max_i]). Effort is chosen
   now and applies to all jobs the provider serves this round. Rules that do
   not use bids ignore the bid.
3. The rule allocates jobs to offers. A job may stay unserved.
4. The rule computes payments per job. Payments are escrowed by the operator.
5. Delivery happens; y is realized per job.
6. The rule chooses jobs to audit within the budget. An audit reveals y for
   that job exactly, at cost alpha.
7. The rule enforces. A job fails its audit if y < c_i - tol, default
   tol = 0.05. Consequences are rule-specific and may include refund of that
   job's escrowed payment to the buyer, and a ban of the identity for L
   rounds, default L = 20. Refunds come from escrow and are always
   collectible.
8. Escrow is released. Exit and re-entry decisions take effect next round.

Observations. The operator sees offers, job values, audit results, and the
full public history. A provider sees its own parameters, its own history
(claims, allocations, payments, audits on it, penalties), the round index, and
posted prices. Buyers observe nothing and act by the acceptance rule above.

Audit budget. Let S_hat be the expected honest-max first-best surplus over T
rounds for the locked configuration, computed once by `scripts/calibrate.py`
and stored as a constant in the config. The operator's total audit budget is
B = beta * S_hat, a single number known to every rule. Unspent budget carries
over across rounds. Audits are integer. The operator never computes S* live.

Audit cost scale. Let m be the mean honest-max per-job surplus from the same
calibration. The dimensionless ratio rho = alpha / m is a locked parameter
with a stated source. Default rho = 0.2. An appendix sweep covers
rho in {0.05, 0.2, 1}. Alpha does not depend on the job.

Configuration validity. A configuration is valid only if S_hat > 0 and every
provider has (v_bar - b_i) * Q(q_max_i) - a_i > 0 for the mean job value.
`calibrate.py` refuses invalid configurations.

## 4. Mechanism interface and baselines

One abstract class with four methods, called in the round order above.

```python
class Mechanism:
    def allocate(self, jobs, offers, state) -> Assignment
    def price(self, assignment, offers, state) -> Payments
    def audit(self, assignment, state, budget_left) -> list[JobId]
    def enforce(self, audit_results, state) -> State
```

`state` is the operator's memory: per-identity history of claims, audits,
failures, payments, bans, and escrow balances, plus the remaining audit
budget.

Baseline B1, posted prices, no audit.

- Tiers by claim: tier 1 for c in [0, 0.5), tier 2 for [0.5, 0.8), tier 3 for
  [0.8, 1]. Prices P1 < P2 < P3 per job, tuned per section 4.1.
- Allocation: jobs sorted by v_j descending. Each job goes to the highest tier
  with remaining capacity whose price it accepts (v_j * c_i >= P_tier for the
  offering provider), random among providers in that tier. Jobs that accept
  no tier stay unserved.
- Payment: P_tier per job, from buyer to provider via escrow. No audits.

Baseline B2, posted prices, random audit. B1 plus: each round, audit
floor(budget_left / alpha) jobs chosen uniformly at random among served jobs,
with a per-round cap of 2 * B / T to keep spend even. A failed audit refunds
that job's payment to the buyer and bans the identity for L rounds. Banned
identities cannot submit offers.

Baseline B3, second-score sequential auction, random audit.

- Each provider submits (claim, per-unit bid). Honest bid is own per-unit cost.
- Jobs processed in descending v_j. For job j the eligible set is providers
  with remaining capacity and score s_ij = v_j * c_i - bid_i >= 0.
- Winner is the highest score, ties broken at random. Payment to the winner is
  p = v_j * c_i - s_(2), where s_(2) is the second-highest eligible score, or
  0 if none. So p >= bid_i. The buyer pays p via escrow.
- Audits and enforcement as in B2.
- Worked example: one job, v = 10, two providers with claims 1 and 1 and bids 1
  and 3. Scores 9 and 7. Provider 1 wins and is paid 10 - 7 = 3.

This is a sequential scoring auction with capacity constraints. It is not
truthful and the paper will not call it VCG.

### 4.1 Baseline tuning

Before the lock, each baseline's free parameters (P1, P2, P3; tol; L) are
tuned with the same search budget the proposed rule will get (section 5.3):
maximize net efficiency against the D2 best response at beta = 0.05. Tuned
values are locked. The paper states the tuning budget.

## 5. Actors

### 5.1 Views and actions

A policy maps a provider's own view (section 3) to an offer or abstain, and
to an exit decision. An entity's policy persists across its identities.

### 5.2 Honest policies

Two honest policies are defined. Both never exit.

- Honest-max: effort q = q_max_i, claim c = c_h(q), bid = a_i + b_i * q.
- Best-truthful: effort q* chosen to maximize own profit with claim c = c_h(q*)
  and bid chosen freely, found by the same search as section 5.3 over the
  one-dimensional effort knob and a bid markup knob.

The truthful claim c_h(q) = clip(q + tol - z * sigma, 0, 1) with z = 2.326, so
an honest provider fails an audit with probability at most 1%. A claim of
q + tol is undetected with probability 1/2 under any audit rate, so the gap
z * sigma between c_h(q) and q + tol is a free lie. Its profit is a known
floor on gain and is drawn as a reference line on Figure 1.

Honest-max is used for calibration and for all-honest runs. Best-truthful is
the comparison point for adversary gain.

### 5.3 Development families and the search

- D1 fixed cheat: effort q = q_max_i * (1 - u), claim c = min(1, q + m), bid
  markup w on cost. Knobs u, m, w.
- D2 adaptive: knobs base effort cut u0, base markup m0, drop in markup after
  a failed audit d, recovery per round without audit r, bid markup w. D2 does
  not exit or re-enter.

Search. CMA-ES over the knobs. Objective: the entity's total profit over T
rounds against the frozen rule, single deviator, all other providers
honest-max, averaged over 5 training seeds with common random numbers.
Pre-registered budget: 5 restarts x 300 evaluations per cell. The best policy
by training objective is then evaluated on 20 disjoint evaluation seeds. All
reported numbers come from evaluation seeds.

Adversary position. Gain is the maximum over three pre-registered positions:
the providers with the lowest, median, and highest b_i * q_max_i.

Search checks, reported in the paper: (a) on B1 the search must recover the
analytic best response (claim in tier 3, effort 0) within 1% of its profit;
(b) on two cells per rule, doubling the budget changes best-found gain by less
than 0.5 points; (c) the spread of best-found gain across restarts.

All-deviators (iterated best response, 3 sweeps, every provider on D2) is a
robustness table.

### 5.4 LLM actor

Provider role only. The actor receives the rules in plain text and its own
view each round and returns an offer in a fixed JSON schema. Pinned model
snapshot ID, temperature 0. Every request and response is cached by prompt
hash; reruns read the cache, which makes replay deterministic. A malformed
response falls back to honest-max for that round and is counted. The actor
plays K = 5 episodes per cell and sees its profit between episodes; the best
episode is reported, and that is stated as a weaker adversary than a search.
Scope in this paper: beta in {0.02, 0.05, 0.10}, 10 evaluation seeds,
T = 100. Estimated calls: 3 budgets x 4 rules x 10 seeds x 5 episodes x 100
rounds = 60,000, all cached. The cost cap is set in the lock commit.

## 6. Pre-registration protocol

Two freezes.

Lock, 2026-10-28, after baselines are tuned and before any proposed rule
exists. The lock commit contains:

- the locked evaluation config `experiments/locked.yaml` (all distributions,
  N, J, T, k_i, sigma, tol, L, e, rho, beta grid, tuned baseline parameters,
  evaluation seed range, training seed range, search budget);
- `scripts/check_claim.py` with the predicate of section 8 and the final
  threshold numbers, tested on synthetic CSVs;
- the SHA-256 of the sealed held-out bundle (spec and code, section 6.1);
- a statement that exactly one proposed rule will be evaluated.

`check_claim.py` refuses any config whose hash differs from the locked one.
The lock commit is tagged, the tag is signed, pushed to a public remote, and
its hash is posted to a third-party timestamp (OSF registration or
AsPredicted) the same day.

Evaluation freeze, 2026-11-11. The proposed rule, metrics, and analysis
scripts are frozen in a second signed tag. Held-out families are never
executed before this tag exists. Any change after it is reported as a
deviation in the paper.

### 6.1 Held-out families

- H1 LLM provider (section 5.4), with a sealed system prompt.
- H2 a parametrized family with an explicit expressiveness statement: it uses
  at least one observation or memory that D2 cannot use. Spec and knob ranges
  sealed.

The sealed bundle (spec, prompts, code for H1 and H2) is written before the
lock by a separate AI session that has no access to any rule-design work and
whose output the author does not read until the unseal. Random salt included.
The bundle enters the repo at the unseal in week 5 and CI checks the hash.

The hash commits to content. The two freezes, the public timestamp, and the
disclosed access log are what support the claim that nothing was run early.

### 6.2 Pre-declared stress test

H3 identity replacement: exit after a failed audit, re-enter under a fresh
identity at cost e. It is public in this spec, so it is not held out. It is
reported in its own table as a stress test, and the rule may be designed with
it in mind.

## 7. Metrics

All totals are over T rounds on evaluation seeds.

- First-best S*. Per round, the maximum over assignments of unit jobs to
  provider capacity slots, over effort q in [0, q_max_i], with the option not
  to serve, of sum over served jobs of v_j * Q(q) - a_i - b_i * q. With linear
  cost the optimum per pair is at q = q_max_i or no service, so the weight of
  pair (i, j) is max(0, v_j * Q(q_max_i) - a_i - b_i * q_max_i) and S* is an
  exact maximum-weight assignment (Hungarian on k_i duplicated slots).
- Realized surplus. Sum over served jobs of v_j * y - a_i - b_i * q_i, minus
  entry costs paid. Uses true quantities, never claims.
- Gross efficiency = realized surplus / S*. Net efficiency = (realized surplus
  - audit cost) / S*. The claim uses gross; tables report both.
- Audit spend = total audit cost / S*.
- Adversary gain. Per entity, across all its identities: profit = receipts -
  refunds - production cost - entry costs. Gain = (profit of the searched
  policy - profit of best-truthful for the same entity) / profit of
  best-truthful, same evaluation seeds. Tables also give gain in units of S*.
- Harm to others = (utility of buyers + profit of honest providers + operator
  net, all honest run) - (same, adversary run), divided by S*. Consistency
  identity, tested: harm to others = total surplus loss + adversary gain in
  S* units.
- Efficiency triple, per rule and budget: all-honest efficiency, efficiency
  with the adversary, and their difference. The difference is the loss the
  adversary causes.

Noise and the benchmark. S* uses Q(q). Realized surplus uses draws. A single
seed can exceed S*. The test is: mean gross efficiency over evaluation seeds
<= 1 + 2 standard errors in the all-honest run.

Common random numbers. Job values and delivery noise are drawn from
`numpy.random.SeedSequence` children keyed by (seed, round, job) and
(seed, round, provider, job slot), independent of any action. Policy
randomness is keyed by (seed, round, provider).

## 8. The claim and its check

Budget grid: beta in {0, 0.01, 0.02, 0.05, 0.10, 0.20}. For each rule R, each
family F, and each beta, run the search of section 5.3 (or the LLM procedure)
and record best-found gain, gross efficiency, net efficiency, audit spend, and
the efficiency triple on 20 evaluation seeds.

Figure 1: best-found gain against audit spend, one line per rule, one panel
per family, mean and 95% band. Figure 2: efficiency triple against audit
spend.

Claim predicate, evaluated by `scripts/check_claim.py` at beta = 0.05. R* is
the proposed rule. Bounds are one-sided 95% over evaluation seeds. Numbers are
provisional until the lock.

For each held-out family F in {H1, H2}, all of:

- lower bound of gross efficiency(R*, F) >= 0.90;
- upper bound of best-found gain(R*, F) <= 0.05, gain in units of
  best-truthful profit;
- realized audit spend(R*, F) <= 0.05 * S* in every seed.

For each baseline B in {B2, B3} at the same beta, for at least one F:

- upper bound of gross efficiency(B, F) <= gross efficiency(R*, F) - 0.20, or
- lower bound of best-found gain(B, F) >= 0.25.

B1 is reported but is not part of the predicate, because it spends no audit
budget.

If a bound straddles a threshold, the script prints INCONCLUSIVE for that
clause and the paper reports it as such. Efficiency in the predicate is
measured under each rule's own gain-maximizing attack; the paper states that
this does not bound efficiency under other attacks.

## 9. Candidate results

Hypotheses to test, with conditions. Validation cases are checks on the
simulator; propositions are candidates for the EC version.

- Validation: inspection inequality. Under uniform audits at rate p with full
  refund of the audited job's payment P and no bans, a one-round cheat that
  saves b * delta per job and is detected with probability d(delta) is
  deterred iff p * d(delta) * P >= b * delta. On B2 with L = 0 the measured
  gain must cross zero within seed noise of that p.
- Proposition A, history-dependent audits. In the model of section 3 with
  e = infinity (no re-entry), for any uniform audit rule there exists an
  audit rule conditioned on identity history that reaches the same best-found
  gain at weakly lower audit spend, strictly lower when T > 1 and sigma is
  small enough that honest failures are rare. Known in tax-audit theory
  (Landsberger and Meilijson 1982; Greenberg 1984); the contribution is the
  quantitative spend reduction as a function of rho and sigma.
- Proposition B, cheap identities. With e = 0 and immediate re-entry, any rule
  whose only consequence is loss of identity-linked continuation value has
  best-found gain bounded below by the one-round cheat profit. Refunds and
  escrow are not identity-linked and are unaffected. This is the setting of
  Friedman and Resnick (2001); the contribution is the measured minimum audit
  spend for deterrence as a function of e, rho, and sigma.
- Trade-off, not threshold: an honest provider fails an audit with probability
  Phi(-(c - q + tol) / sigma); the tolerance sets a trade-off between honest
  failures and the undetectable lie. Reported as a curve, not a hypothesis.

## 10. Application profiles (later)

A profile is a YAML file that fixes distributions, rho with its source, and
names: inference tokens (quality is fidelity to the promised model; rho from
touchstone-meter's per-probe cost), GPU hours (quality is delivered over
promised throughput; audit is a benchmark job). No code change expected.

## 11. Layout

```
touchstone/
  sim/
    market.py        # entities, round sequence, keyed RNG
    mechanisms/      # base.py, posted.py, posted_audit.py, second_score.py
    policies/        # honest.py, fixed_cheat.py, adaptive.py, llm.py, identity.py
    search.py        # CMA-ES best response with restarts and seed split
    metrics.py       # S*, efficiency, gain, harm, triple
    llm_actor.py     # prompt, schema, cache, fallback
  experiments/       # locked.yaml and sweep configs
  scripts/
    calibrate.py     # S_hat, m, validity check
    tune_baselines.py
    run.py, sweep.py, plot.py, check_claim.py
  sealed/            # empty until the unseal; hash in README
  tests/
```

Dependencies: numpy, scipy, cma, pyyaml, pandas, matplotlib, pytest; the
Anthropic SDK behind a thin interface for the LLM actor.

## 12. Tests

- Honest-max against every rule: gain relative to best-truthful is <= 0 within
  search tolerance, and exactly 0 when the search is skipped.
- All-honest mean gross efficiency <= 1 + 2 SE.
- One provider, one job, zero noise: S* matches the closed form.
- Same config and seed give a byte-identical CSV for every non-LLM family;
  LLM replay from cache is byte-identical.
- Total audit spend never exceeds B; the per-round cap holds for B2 and B3.
- B1 with D1 at u = 1, m = 1 gives positive gain; the search recovers it.
- A deviation in round t changes no job draw or noise draw in round t + 1.
- Harm identity holds to floating-point tolerance.
- Every mechanism passes one shared harness test on a tiny market, with a
  worked-example assertion for B3's payment.
- Locked config hash check refuses a modified config.
- Sealed bundle hash check passes once the bundle is present.

## 13. Timeline and gates

| Dates | Work | Gate |
|---|---|---|
| 10-14 to 10-17 | Market, B1 to B3, honest policies, metrics, tiny-market tests | Timed pilot: one 20-seed run of B2 under 10 s |
| 10-18 to 10-24 | Search with seed split, D1, D2, sweep, calibrate, tune baselines | B1 analytic check passes; full sweep for B1 to B3 under 4 h |
| 10-25 to 10-28 | Separate session writes sealed bundle; check_claim.py; lock | Signed tag, public timestamp |
| 10-29 to 11-11 | Proposed rule; LLM actor plumbing on development families only; H3 | Evaluation freeze tag |
| 11-12 to 11-18 | Unseal; run H1, H2 on frozen rule and baselines; figures | Hash verified; check_claim output |
| 11-19 to 11-25 | One page. Decide. | |

If the second gate slips, cut beta in {0.01, 0.20} first, then D1, never the
seed split or the baseline tuning.

## 14. Review changelog

Three independent reviews on 2026-10-14. Material objections and the change
made:

- S* fixed effort at q_max and used unit-slot LP on sized jobs (all three):
  unit jobs; S* maximizes over effort with a no-serve option; expected-noise
  benchmark; test on the mean.
- Honest policy undefined; gain per identity (all three): honest-max and
  best-truthful defined; gain per entity relative to best-truthful profit.
- Gain in S* units scales with N (Fable, Astra; Opus on efficiency clauses):
  gain in units of best-truthful profit; efficiency triple and harm metric.
- Search is a lower bound; seeds not split (all three): claim worded as
  best-found under a pre-registered search; train/eval split; restarts;
  doubling check; analytic check; three adversary positions.
- "Before the lock date" forbade nothing; H3 inside D2; hash not third-party
  (all three): evaluation freeze; H3 relabeled; re-entry removed from D2;
  separate-session authorship; sealed code; signed tags and public timestamp.
- Eval config and rule count unlocked (Opus, Astra): locked.yaml with hash
  check; exactly one proposed rule.
- Claim quantifiers ambiguous (Opus, Astra): formal predicate in section 8.
- Baselines untuned and underspecified; B3 misnamed (all three): full
  specification, worked example, tuning with the same budget, renamed.
- Audit cost scale and budget semantics; S* leaked to operator (Opus, Astra):
  rho, calibrated S_hat constant, total budget with carry-over.
- Round timing, settlement, participation, entry cost (Astra): explicit
  sequence, escrow, refund scope, voluntary participation, e destroyed.
- Section 9 imprecise, partly known, partly false (all three): restated with
  conditions and citations; exclusivity of bonds removed.
- Feasibility (all three): gates, fixed budgets, reduced H1 scope with cache.
- CRN (Fable, Opus): keyed SeedSequence.
- Loss to others (Opus, Astra): harm to others, with identity test.
