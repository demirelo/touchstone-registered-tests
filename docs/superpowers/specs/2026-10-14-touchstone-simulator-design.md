# Touchstone simulator: design

Date: 2026-10-14. Version 3, after two rounds of three-model review (Fable
5.1, Opus 5.5, Astra). Status: draft for review. Section 14 maps review
objections to changes.

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
y = q_i + eps, eps ~ N(0, sigma^2), default sigma = 0.05. There is no
clipping, so E[y] = q_i exactly and the benchmark in section 7 is linear in
effort. Small excursions of y outside [0, 1] are delivery noise and are
valued at v_j * y. Cost a_i + b_i * q_i is paid per job served.

Round sequence. Every rule follows this order.

1. Draw the round's jobs.
2. Each active provider privately chooses effort q_i in [0, q_max_i] for the
   round, and submits a public offer (claim c_i in [0, 1], per-unit bid) or
   abstains. Effort is not part of the offer. Rules that do not use bids
   ignore the bid.
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
full public history. It never sees effort or unaudited delivery. The
`Mechanism` interface receives offers only; effort lives in provider state
and reaches the operator only through audit results. A provider sees its own
parameters, its own history (claims, allocations, payments, audits on it,
penalties), the round index, and posted prices. Buyers observe nothing and
act by the acceptance rule above.

Audit budget. Let S_hat be the expected honest-max first-best surplus over T
rounds for the locked configuration, computed once by `scripts/calibrate.py`
and stored as a constant in the config. The operator's total audit budget is
B = beta * S_hat, a single number known to every rule. Unspent budget carries
over across rounds. Audits are integer. The operator never computes S* live.
Section 8 adds a separate ex-post condition on realized spend.

Audit cost scale. Let m be the mean honest-max per-job surplus from the same
calibration. The dimensionless ratio rho = alpha / m is a locked parameter
with a stated source. Default rho = 0.2. An appendix sweep covers
rho in {0.05, 0.2, 1}. Alpha does not depend on the job.

Configuration validity. A configuration is valid only if S_hat > 0 and, for
every provider, v_bar * q_max_i - a_i - b_i * q_max_i > 0 at the mean job
value. This guarantees that serving at full effort is efficient for the
average job. It does not guarantee positive provider profit under any rule;
section 7 handles that.

## 4. Mechanism interface and baselines

One abstract class with four methods, called in the round order above.

```python
class Mechanism:
    def allocate(self, jobs, offers, state) -> Assignment
    def price(self, assignment, offers, state) -> Payments
    def audit(self, assignment, state, budget_left) -> list[JobId]
    def enforce(self, audit_results, state) -> State
```

`offers` carries claims and bids only. `state` is the operator's memory:
per-identity history of claims, audits, failures, payments, bans, and escrow
balances, plus the remaining audit budget.

Baseline B1, posted prices, no audit.

- Tiers by claim: tier 1 for c in [0, 0.5), tier 2 for [0.5, 0.8), tier 3 for
  [0.8, 1]. Prices P1 < P2 < P3 per job, tuned per section 4.1.
- Allocation: jobs sorted by v_j descending. For each job, the eligible
  providers are those with remaining capacity whose tier price the buyer
  accepts, v_j * c_i >= P_tier(i). The job goes to a random eligible provider
  in the highest tier that has any eligible provider. Jobs with no eligible
  provider stay unserved.
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

Before the lock, each baseline's free parameters are tuned by a
pre-registered reduced procedure, because the full search inside a tuning
loop is not affordable:

- outer grid: 27 price triples (P1, P2, P3) on a geometric grid between the
  lowest and highest honest cost, 3 values of tol in {0.03, 0.05, 0.08},
  2 values of L in {10, 20};
- inner best response: D2, 1 restart x 100 evaluations x 3 training seeds;
- objective: net efficiency against that best response at beta = 0.05.

Tuned values are locked. The paper states the procedure and its budget. The
proposed rule's own parameters get the same outer budget (162 configurations)
with the same inner search.

## 5. Actors

### 5.1 Views and actions

A policy maps a provider's own view (section 3) to private effort, a public
offer or abstain, and an exit decision. An entity's policy persists across
its identities.

### 5.2 Honest policies

Two honest policies are defined. Both never exit.

- Honest-max: effort q = q_max_i, claim c = c_h(q), bid = a_i + b_i * q.
- Best-truthful: effort q* chosen to maximize own profit with claim c = c_h(q*)
  and bid chosen freely, found by the same search as section 5.3 over the
  one-dimensional effort knob and a bid markup knob.

The truthful claim is c_h(q) = clip(q + tol - z * sigma, 0, 1) with z = 2.326.
With unclipped noise, a provider with effort q and claim c fails an audit
with probability Phi((c - tol - q) / sigma), so an honest provider fails with
probability Phi(-z) = 1%. Claim inflation above c_h raises that probability
toward and past 50% at c = q + tol. This trade-off is drawn as a reference
curve on Figure 1. It is not a floor on gain.

Honest-max is used for calibration and for all-honest runs. Best-truthful is
the reference policy for adversary gain and harm (section 7).

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

Adversary position. Three pre-registered positions: the providers with the
lowest, median, and highest b_i * q_max_i. At beta = 0.05 the search runs at
all three, and the headline position is the one with the highest training
objective; its evaluation-seed statistics are reported, so no selection
happens on evaluation seeds. At other budgets only the median position runs.
The claim is about these three positions, not about every provider.

Search checks, reported in the paper: (a) on a fixed B1 fixture in which
every job accepts tier 3 (v_j >= P3 for all j), the search must recover the
analytic best response (claim 1, effort 0) within 1% of its profit; (b) on two
cells per rule, doubling the budget changes best-found gain by less than 0.5
points; (c) the spread of best-found gain across restarts.

All-deviators (iterated best response, 3 sweeps, every provider on D2) is a
robustness table.

Workload. Development sweep: 3 rules x 2 families x (5 budgets x 1 position +
1 budget x 3 positions) x 5 restarts x 300 evaluations x 5 seeds = about
360,000 runs. Gate: under 4 hours, which needs a run under 40 ms.

### 5.4 LLM actor and H1 procedure

Provider role only. The actor receives the rules in plain text and its own
view each round and returns an offer in a fixed JSON schema. Pinned model
snapshot ID, temperature 0. Every request and response is cached by prompt
hash; reruns read the cache, which makes replay deterministic. A malformed
response falls back to honest-max for that round and is counted.

The evaluated object is the adaptive procedure: 5 episodes of T = 100 rounds
in which the actor sees its profit between episodes. Episodes 1 to 4 use
training seeds; episode 5 uses one evaluation seed, and its profit is the
reported statistic. The procedure is repeated 10 times with 10 evaluation
seeds; uncertainty is across repetitions. The actor learns within a
procedure, never across repetitions (fresh context each time). Scope: beta
in {0.02, 0.05, 0.10}, 4 rules. Calls: 3 x 4 x 10 x 5 x 100 = 60,000, all
cached. The cost cap is set in the lock commit. The paper states that H1 is a
weaker adversary than a search, and that H1 uses 10 evaluation seeds where
parametrized families use 20.

## 6. Pre-registration protocol

Two freezes.

Lock, 2026-10-28, after baselines are tuned and before any proposed rule
exists. The lock commit contains:

- the locked evaluation config `experiments/locked.yaml` (all distributions,
  N, J, T, k_i, sigma, tol, L, e, rho, beta grid, tuned baseline parameters,
  evaluation seed range, training seed range, search budget, H1 budget);
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

All totals are over T rounds on evaluation seeds. S* is computed per seed.

- First-best S*. Per round, the maximum over assignments of unit jobs to
  provider capacity slots and over effort, with the option not to serve, of
  the sum over served jobs of v_j * E[y] - a_i - b_i * q. With E[y] = q and
  linear cost, each served pair is best at q = q_max_i, common to all jobs of
  that provider, so the pair weight is max(0, v_j * q_max_i - a_i - b_i *
  q_max_i) and S* is an exact maximum-weight assignment (Hungarian on k_i
  duplicated slots).
- Net surplus W. Sum over served jobs of v_j * y - a_i - b_i * q_i, minus
  entry costs paid, minus audit cost. Uses true quantities, never claims.
- Gross efficiency = (W + audit cost) / S*. Net efficiency = W / S*. The claim
  uses gross; tables report both.
- Audit spend = audit cost / S*, per seed.
- Reference run. For a focal entity, the reference run is the run in which it
  plays best-truthful and every other provider plays honest-max, on the same
  seeds. Gain and harm both use this run.
- Adversary gain. Per entity, across all its identities: profit pi = receipts
  - refunds - production cost - entry costs. Per seed,
  gain = (pi_attack - pi_ref) / (S* / N). The statistic is the mean of this
  ratio over evaluation seeds with a paired confidence bound. The denominator
  is always positive. Tables also report (pi_attack - pi_ref) / pi_ref where
  pi_ref > 0, and mark cells where it is not.
- Harm to others, per seed in units of S*:
  harm = [(W_ref - W_attack) + (pi_attack - pi_ref)] / S*. This equals the
  change in the summed utility of buyers, non-focal providers, and the
  operator's net position, which the code computes directly. The equality is
  a test.
- Efficiency triple, per rule and budget: all-honest gross efficiency, gross
  efficiency with the adversary, and their paired difference.

Noise and the benchmark. S* uses E[y]. W uses draws. A single seed can exceed
S*. The test is: mean gross efficiency over evaluation seeds <= 1 + 2
standard errors in the all-honest run.

Common random numbers. Job values and delivery noise are drawn from
`numpy.random.SeedSequence` children keyed by (seed, round, job) and
(seed, round, provider, job slot), independent of any action. Policy
randomness is keyed by (seed, round, provider).

## 8. The claim and its check

Budget grid: beta in {0, 0.01, 0.02, 0.05, 0.10, 0.20}. For each rule R, each
family F, and each beta, run the search of section 5.3 (or the H1 procedure)
and record best-found gain, gross and net efficiency, audit spend, and the
efficiency triple on evaluation seeds (20 for parametrized families, 10 for
H1).

Figure 1: best-found gain against audit spend, one line per rule, one panel
per family, mean and 95% band, with the truthful-claim trade-off curve of
section 5.2 as a reference. Figure 2: efficiency triple against audit spend.

Claim predicate, evaluated by `scripts/check_claim.py` at beta = 0.05. R* is
the proposed rule. All bounds are one-sided over evaluation seeds. Because
the baseline clause is "at least one of two families", bounds in that clause
use level 97.5% (Bonferroni over families); bounds in the rule clause use
95%. Numbers are provisional until the lock.

Rule clause. For each held-out family F in {H1, H2}, all of:

- lower 95% bound of gross efficiency(R*, F) >= 0.90;
- upper 95% bound of gain(R*, F) <= 0.30, gain in units of S* / N;
- audit cost / S* <= 0.05 in every evaluation seed (ex-post, in addition to
  the calibrated budget B).

Baseline clause. For each baseline B in {B2, B3} at the same beta, there is at
least one F such that:

- lower 97.5% bound of the paired difference gross efficiency(R*, F) -
  gross efficiency(B, F) >= 0.20, or
- lower 97.5% bound of gain(B, F) >= 1.0, in units of S* / N.

B1 is reported but is not part of the predicate, because it spends no audit
budget.

If a bound straddles a threshold, the script prints INCONCLUSIVE for that
clause and the paper reports it as such. Efficiency in the predicate is
measured under each rule's own gain-maximizing attack at the headline
position; the paper states that this does not bound efficiency under other
attacks or positions.

Units note. S* / N is the mean first-best surplus per provider. A gain of 0.30
means the adversary captures 30% of an average provider's first-best share
beyond what truthful play gives it. The provisional 0.30 and 1.0 are set from
the baseline runs at the lock.

## 9. Candidate results

Hypotheses to test, with conditions. Validation cases are checks on the
simulator; propositions are candidates for the EC version.

- Validation: inspection inequality. Fix the claim at c_h(q_max) and the
  allocation, and consider an effort cut delta under uniform audits at rate
  p with full refund of the audited job's payment P and no bans. Truthful
  failure probability is d0 = Phi(-z); with the cut it is
  d1(delta) = Phi((c - tol - q_max + delta) / sigma). The cut is unprofitable
  iff p * P * (d1(delta) - d0) >= b * delta. On B2 with L = 0 and a fixed
  fixture, the measured gain from effort cuts must cross zero within seed
  noise of the p that solves this with equality.
- Proposition A, history-dependent audits. In the model of section 3 with
  e = infinity (no re-entry), T > 1, and a uniform audit rule with positive
  spend that reaches best-found gain at most epsilon, there exists an audit
  rule conditioned on identity history that reaches at most epsilon at weakly
  lower spend. Strict improvement is a conjecture under conditions to be
  identified (small sigma, enough rounds for history to accumulate). Known
  qualitatively in tax-audit theory (Landsberger and Meilijson 1982;
  Greenberg 1984); the contribution is the quantitative spend reduction as a
  function of rho and sigma.
- Proposition B, cheap identities. With e = 0 and immediate re-entry, any rule
  whose only consequence is loss of identity-linked continuation value has
  best-found gain bounded below by the one-round cheat profit. Refunds and
  escrow are not identity-linked and are unaffected. This is the setting of
  Friedman and Resnick (2001); the contribution is the measured minimum audit
  spend for deterrence as a function of e, rho, and sigma.
- Trade-off, not threshold: failure probability Phi((c - tol - q) / sigma)
  sets a trade-off between honest failures and undetected claim inflation.
  Reported as a curve.

## 10. Application profiles (later)

A profile is a YAML file that fixes distributions, rho with its source, and
names: inference tokens (quality is fidelity to the promised model; rho from
touchstone-meter's per-probe cost), GPU hours (quality is delivered over
promised throughput; audit is a benchmark job). No code change expected.

## 11. Layout

```
touchstone/
  sim/
    market.py        # entities, round sequence, keyed RNG, private effort
    mechanisms/      # base.py, posted.py, posted_audit.py, second_score.py
    policies/        # honest.py, fixed_cheat.py, adaptive.py, llm.py, identity.py
    search.py        # CMA-ES best response with restarts and seed split
    metrics.py       # S*, W, efficiency, gain, harm, triple
    llm_actor.py     # prompt, schema, cache, fallback, episode procedure
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
- On the B1 fixture of section 5.3, D1 at u = 1, m = 1 gives positive gain
  and the search recovers it within 1%.
- A deviation in round t changes no job draw or noise draw in round t + 1.
- Harm identity: the accounting formula equals the directly computed utility
  change of others, to floating-point tolerance.
- The mechanism interface cannot read effort: a test passes offers with an
  effort field and asserts it is rejected.
- Honest failure rate under audit is 1% within binomial tolerance.
- Every mechanism passes one shared harness test on a tiny market, with a
  worked-example assertion for B3's payment.
- Locked config hash check refuses a modified config.
- Sealed bundle hash check passes once the bundle is present.

## 13. Timeline and gates

| Dates | Work | Gate |
|---|---|---|
| 10-14 to 10-17 | Market, B1 to B3, honest policies, metrics, tiny-market tests | Timed pilot: one 20-seed run of B2 under 10 s |
| 10-18 to 10-24 | Search with seed split, D1, D2, sweep, calibrate, tune baselines | B1 fixture check passes; full sweep for B1 to B3 under 4 h |
| 10-25 to 10-28 | Separate session writes sealed bundle; check_claim.py; lock | Signed tag, public timestamp |
| 10-29 to 11-11 | Proposed rule; LLM actor plumbing on development families only; H3 | Evaluation freeze tag |
| 11-12 to 11-18 | Unseal; run H1, H2 on frozen rule and baselines; figures | Hash verified; check_claim output |
| 11-19 to 11-25 | One page. Decide. | |

If the second gate slips, cut beta in {0.01, 0.20} first, then D1, never the
seed split or the baseline tuning.

## 14. Review changelog

Round 1 (version 1 to 2), three independent reviews on 2026-10-14:

- S* fixed effort at q_max and used unit-slot LP on sized jobs: unit jobs;
  S* maximizes over effort with a no-serve option.
- Honest policy undefined; gain per identity: honest-max and best-truthful
  defined; gain per entity.
- Search is a lower bound; seeds not split: claim worded as best-found under
  a pre-registered search; train/eval split; restarts; doubling check.
- "Before the lock date" forbade nothing; H3 inside D2; hash not third-party:
  evaluation freeze; H3 relabeled; re-entry removed from D2;
  separate-session authorship; sealed code; signed tags; public timestamp.
- Eval config and rule count unlocked: locked.yaml with hash check; one rule.
- Claim quantifiers ambiguous: formal predicate.
- Baselines untuned and underspecified; B3 misnamed: full specification,
  worked example, tuning, renamed second-score.
- Audit cost scale and budget semantics; S* leaked to operator: rho,
  calibrated S_hat constant, total budget with carry-over.
- Round timing, settlement, participation, entry cost: explicit sequence.
- Section 9 imprecise, partly known, partly false: restated with citations.
- Feasibility: gates, fixed budgets, reduced H1 scope with cache.
- CRN: keyed SeedSequence. Loss to others: harm with identity test.

Round 2 (version 2 to 3):

- Clipped noise made E[y] nonlinear, so S* at q_max was wrong and
  job-specific effort contradicted common effort: noise is unclipped,
  E[y] = q, S* exact at common effort q_max.
- Effort was part of the public offer: effort is private; the interface
  receives offers only; a test enforces it.
- Best-truthful profit can be zero: headline gain in units of S* / N, mean of
  per-seed ratios; profit-relative gain in tables where defined; validity
  condition corrected to b_i * q_max_i.
- Harm and gain used different reference runs: one reference run
  (best-truthful focal entity, honest-max others), W net of audits, identity
  tested against direct computation.
- H1 procedure inconsistent: evaluated object is the 5-episode procedure,
  episode 5 on an evaluation seed, 10 repetitions, T = 100, stated in
  section 8.
- Efficiency comparison used a point estimate against a bound: paired
  difference with a one-sided bound; Bonferroni over families; position
  chosen on training seeds; claim limited to three positions.
- Audit predicate mixed units: cost / S* <= 0.05 per seed, ex-post, stated
  as separate from the calibrated budget.
- Failure probability formula and inspection validation wrong: corrected
  formula; validation with fixed claim and allocation and truthful failures;
  "free lie floor" removed.
- B1 analytic check not valid for all configs: restricted to a fixture.
- Proposition A strictness had a zero-spend counterexample: positive spend
  required; strictness demoted to a conjecture.
- Bilevel baseline tuning unaffordable (Fable): pre-registered reduced grid
  and inner search, same outer budget for the proposed rule.
- Development sweep over the 4-hour gate (Fable): three positions only at
  beta = 0.05.
- README carried version-1 definitions: aligned.
