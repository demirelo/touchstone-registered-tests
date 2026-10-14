# Touchstone simulator: design

Date: 2026-10-14. Version 4.5, after nine rounds of three-model review (Fable
5.1, Opus 5.5, Astra) and one external read (GPT Pro). Status: draft for
review. Section 14 maps review objections to changes.

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
- A closed admissible class of market rules (section 4.0), three fully
  specified, tuned baseline rules in that class, and an interface for one
  proposed rule in that class.
- Parametrized provider policies with an executable, pre-registered
  best-response search, and a matched truthful twin for every family.
- An LLM actor in the provider role.
- A two-freeze pre-registration protocol (lock, then evaluation freeze) with
  three seed namespaces and a bound measurement pipeline.
- Metrics, the curve, and a formal claim predicate with a pass/fail script.

Out of scope for this paper:

- Strategic buyers. Buyers are passive and truthful.
- Collusion between providers.
- Decentralized or untrusted operators, chains, tokens.
- Any proposed rule. The rule is designed after the lock date, 2026-10-28.
- Application profiles. Section 10 lists them as later work.
- LLM actors in roles other than provider.
- Equilibrium claims. Non-focal providers are scripted (honest-max), not
  equilibrium participants. The benchmark is unilateral deviation.

Participation is voluntary. A provider may abstain in any round. A buyer
accepts an offer only if its claimed value covers the price.

## 3. Market model

Time is discrete, rounds t = 1..T, default T = 200.

Jobs. Each round J unit jobs arrive, default J = 50. A job has value v_j > 0
per unit of delivered quality, drawn i.i.d. from a configured distribution
with known lower support bound v_min. All jobs have size 1. Buyer value for
delivered quality y is v_j * y.

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
clipping, so E[y] = q_i exactly. Small excursions of y outside [0, 1] are
delivery noise and are valued at v_j * y. Cost a_i + b_i * q_i is paid per job
served.

Claim semantics. A claim c in [0, 1] is a promise that expected delivered
quality is at least c. The semantics are fixed for every rule. A claim is
truthful iff c <= q_i, the effort chosen for that round. Claim inflation is
c - q_i > 0. Rules differ in how they audit and enforce this promise, never
in what it means.

Round sequence. Every rule follows this order.

1. Draw the round's jobs.
2. Each active provider privately chooses effort q_i in [0, q_max_i] for the
   round, and submits a public offer (claim c_i, per-unit bid) or abstains.
   Effort is not part of the offer. Rules that do not use bids ignore the
   bid.
3. The rule allocates jobs to offers. A job may stay unserved.
4. The rule computes payments per job. Payments are funded by the buyer into
   escrow (gross escrow funding).
5. Delivery happens; y is realized per job.
6. The rule chooses jobs to audit within the budget. An audit reveals y for
   that job exactly, at cost alpha.
7. The rule enforces within the admissible class (section 4.0). A job fails
   its audit if y < c_i - tol_R, where tol_R is the rule's own audit
   tolerance (a tuned parameter, section 4.1). Refunds come from that job's
   escrow and are always collectible.
8. Escrow is settled: refunds go back to buyers, the rest is released to
   providers as net released receipts, except amounts a rule holds back
   under 4.0. Exit and re-entry decisions take effect next round.

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
Section 8 adds a separate condition on realized spend.

Audit cost scale. Let m = S_hat / n_FB be the mean honest-max first-best
surplus per served job, where n_FB is the expected number of jobs served in
the first-best assignment over T rounds. The dimensionless ratio
rho = alpha / m is a locked parameter. The default rho = 0.2 is an
assumption until an application profile supplies a source. With this
definition B / alpha = (beta / rho) * n_FB audits in total; the fraction of
actually served jobs audited is reported, not assumed. The sweep over rho in
{0.05, 0.2, 1} is in the main text with the scope stated in section 5.3.

Configuration validity. A configuration is valid only if, for every
provider, v_min * q_max_i - a_i - b_i * q_max_i > 0 (every job has positive
first-best weight with every provider, so S* > 0 on every seed) and
0.9 * q90(v_j) > min_i (a_i + b_i * q_max_i) (section 4.1 grid).
`calibrate.py` refuses invalid configurations.

## 4. Mechanism interface, admissible class, and baselines

One abstract class with five methods.

```python
class Mechanism:
    def allocate(self, jobs, offers, state) -> Assignment
    def price(self, assignment, offers, state) -> Payments
    def audit(self, assignment, state, budget_left) -> list[JobId]
    def enforce(self, audit_results, state) -> State
    def describe(self) -> RuleDescription   # section 5.4
```

`offers` carries claims and bids only. `state` is the operator's memory:
per-identity history of claims, allocations, audits, failures, payments,
bans, and held-back balances, plus the remaining audit budget.

### 4.0 Admissible class (locked before any rule is designed)

Every rule, baseline or proposed, must satisfy all of the following. Tests in
section 12 enforce them mechanically.

Inputs. A rule may read only: the current offers, the current job values,
the audit results it has purchased, its own `state`, and the locked config.
It may not read entity ids, evaluator metadata, seeds, effort, unaudited
delivery, or any global. Identity ids are opaque tokens; a rule's decisions
must be invariant to relabeling them.

Transfers. All payments to providers are funded by buyer escrow for jobs
those providers served. The operator injects no money. The operator's net
position is the audit cost it spends, nothing else; forfeits go to buyers
(section 7). It is reported.

Enforcement. The only consequences a rule may impose are:

- refund of up to the full escrowed payment of an audited job that failed;
- a ban of an identity for a finite number of rounds, at most L_max = 50;
- holding back up to H_max = 3 rounds of an identity's net released receipts
  as a bond, released or forfeited under a rule-stated schedule. A forfeit
  is booked once, to the buyers of the failed jobs that triggered it, up to
  the escrowed payments of those jobs; any excess is released to the
  provider. Bond ownership follows the entity: on exit, the identity's
  remaining bond is settled under the same schedule as if the identity had
  stayed, and the entity receives the releases. At the end of the episode
  (round T) every outstanding bond that no failed audit has claimed is
  released to its provider, and that terminal settlement is part of profit;
- allocation priority and audit selection as functions of allowed inputs.

No fees, no penalties beyond these, no consequences for unaudited jobs. The
operator never holds money at the end of an episode.

Budget. Audit spend never exceeds B in any seed.

### 4.1 Baselines

B1, posted prices, no audit.

- Tiers by claim: tier 1 for c in [0, 0.5), tier 2 for [0.5, 0.8), tier 3 for
  [0.8, 1]. Prices P1 < P2 < P3 per job, tuned per section 4.2.
- Allocation: jobs sorted by v_j descending. For each job, the eligible
  providers are those with remaining capacity whose tier price the buyer
  accepts, v_j * c_i >= P_tier(i). The job goes to a random eligible provider
  in the highest tier that has any eligible provider. Jobs with no eligible
  provider stay unserved.
- Payment: P_tier per job via escrow. No audits.

B2, posted prices, random audit. B1 plus a spread audit schedule: in round t
the number of audits is the stochastic rounding of
(budget_left / alpha) / (T - t + 1), then capped by the number of served
jobs, by max(1, floor(2 * B / (T * alpha))), and by floor(budget_left /
alpha); the rounding draw is keyed by (seed, round). Audited jobs are chosen
uniformly at random among served jobs. A failed audit refunds that job's
payment to the buyer and bans the identity for L rounds. Banned identities
cannot submit offers.

B3, second-score sequential auction, random audit.

- Each provider submits (claim, per-unit bid). Honest bid is own per-unit cost.
- Jobs processed in descending v_j. For job j the eligible set is providers
  with remaining capacity and score s_ij = v_j * c_i - bid_i >= 0.
- Winner is the highest score, ties broken at random. Payment to the winner is
  p = v_j * c_i - s_(2), where s_(2) is the second-highest eligible score, or
  0 if none. So p >= bid_i. The buyer pays p via escrow.
- Audits and enforcement as in B2.
- Worked example: one job, v = 10, two providers with claims 1 and 1 and bids 1
  and 3. Scores 9 and 7. Provider 1 wins and is paid 10 - 7 = 3.

B3 is a sequential scoring auction with capacity constraints. It is not
truthful and the paper will not call it VCG.

A no-ban diagnostic (L = 0) of B2 and B3 is reported alongside, so the cost
of false bans is visible.

### 4.2 Baseline tuning

Before the lock, each baseline's free parameters are tuned by a
pre-registered reduced procedure:

- outer grid: 27 ordered price triples. Let c_min be the lowest honest-max
  per-unit cost over providers and P_top = 0.9 * q90(v_j). P3 takes 3
  geometric points between c_min and P_top inclusive; P2 = f2 * P3 and
  P1 = f1 * P2 with f1, f2 in {0.5, 0.7, 0.9}. `tune_baselines.py` asserts
  0 < P1 < P2 < P3. Also tol_R in {0.08, 0.12, 0.16} (honest failure rates
  5.5%, 0.8%, 0.07% at sigma = 0.05) and L in {10, 20};
- inner search: D2 at the median position, 1 restart x 100 evaluations x 3
  dev-train seeds, with its truthful twin (section 5.2) searched first at
  the same budget;
- objective: the smaller of the two normalized predicate margins at
  beta = 0.05, min((gross efficiency - 0.90) / 0.90, (0.30 - gain) / 0.30);
- the top 3 grid points are re-checked at the full search budget of section
  5.3 and the best is locked.

The proposed rule's own parameters get the same outer budget (162
configurations) and the same inner search, logged.

## 5. Actors

### 5.1 Views and actions

A policy maps a provider's own view (section 3) to private effort, a public
offer or abstain, and an exit decision. An entity's policy persists across
its identities.

### 5.2 Honest-max and the matched truthful twin

Honest-max: effort q = q_max_i, claim c = q_max_i, bid = a_i + b_i * q_max_i,
never exits, never abstains. An honest-max provider fails an audit with
probability Phi(-tol_R / sigma). Honest-max is used for calibration, for
all-honest runs, and as the scripted policy of non-focal providers.

Truthful twin. For every adversary family F and every cell, the reference is
the same family run through the same procedure with one harness change: the
claim is clipped to min(c, q) before it reaches the market, so the twin can
adapt effort, bids, abstention, and (for H1) its round-by-round choices
exactly as F does, but cannot inflate. The twin is searched or run first
with the same budget. The reference policy for a cell is one policy, chosen
on dev-train seeds by mean profit among the twin, honest-max, and abstention
(profit 0); pi_ref on evaluation seeds is the per-seed profit of that one
chosen policy, never a per-seed maximum. Gain measures what inflation adds
on top of the best matched truthful behaviour.

Because pi_ref is itself a best-found quantity, the paper states that gain
is the difference of two searched values and can be biased in either
direction by search error; the search checks of 5.3 bound that error.

### 5.3 Development families and the search

All families act on the provider view of section 3. Knobs are mapped from
CMA-ES's unbounded space to their domains by a logistic transform; the
transform and domains are part of the locked families file.

D1 fixed cheat. Knobs u in [0, 1], m in [0, 1], s in [0, 0.3], w in [0, 2].
Effort q = q_max_i * (1 - u). Claim c = min(1, max(0, q + m - s)); s lets
the policy claim below effort, which lowers false failures. Bid = (1 + w) *
(a_i + b_i * q). Never abstains, never exits.

D2 adaptive cheat. Knobs u0, m0 in [0, 1]; s in [0, 0.3]; d in [0, 1];
r in [0, 0.2]; w in [0, 2]. State: markup level m_t, initialized m_1 = m0.
Each round: effort q_t = q_max_i * (1 - u0); claim
c_t = min(1, max(0, q_t + m_t - s)); bid as D1.
After the round: if the identity failed an audit this round, m_{t+1} =
m_t * (1 - d); else m_{t+1} = min(m0, m_t + r * m0). During a ban the
identity submits nothing and m_t is unchanged. Never abstains, never exits.
D2 contains D1 (d = r = 0).

Twins. D1-twin and D2-twin are D1 and D2 with the claim clipped to <= q; the
margin knob s stays free, so a twin can claim conservatively. The sealed H2
claim map must also permit claims below effort (section 6.1).

Search. CMA-ES (pycma) with population size 8, initial step 0.3 in the
transformed space, 5 restarts from fixed registered initial points in the
transformed space: the near-honest point (logit of 0.02 on every knob), the
near-full-cheat point (logit of 0.98 on every knob except the margin s,
which is at logit of 0.02), and three Sobol points; 300
evaluations per restart including incumbent re-evaluation every 10
iterations, no boundary handling beyond the transform. The exact corners
(knobs at 0 or 1) are evaluated once each as registered controls outside
the search budget and reported next to the best-found value. Objective: the mean
over 5 dev-train seeds of the headline statistic, per-seed normalized gain
(pi - pi_ref) / (S* / N), with pi_ref from the cell's chosen reference
policy (section 5.2) on the same seeds. The
best candidate by objective is then evaluated on 20 dev-val seeds during
development and on 20 final-eval seeds after the freeze. All reported
numbers come from the seed namespace stated in section 6.

Adversary position. Three pre-registered positions: the providers with the
lowest, median, and highest b_i * q_max_i. At beta = 0.05 the search runs at
all three. The headline position is selected separately for each (rule,
family) cell on that cell's dev-train seeds, as the one with the highest
objective; its evaluation statistics are reported, so no selection happens
on evaluation seeds. All three positions appear in a table. At other budgets
only the median position runs. H1 plays the median position only (section
5.4). The claim is about the headline position selected this way for H2 and
the median position for H1, not about every provider.

Search checks, reported in the paper: (a) on a fixed B1 fixture in which
every job accepts tier 3, P3 > a_i, and the focal provider has positive
expected allocation, the search must recover the analytic best response
(claim 1, effort 0) within 1% of its profit; (b) on two cells per rule,
doubling the budget changes best-found gain by less than 0.5 points; (c) the
spread of best-found gain across restarts; (d) the twin's objective is never
below honest-max's by more than 1%.

All-deviators (iterated best response, 3 sweeps, every provider on D2 with
1 restart x 100 evaluations x 3 dev-train seeds per sweep and provider, one
cell per rule at beta = 0.05, median rho) is a robustness table; it is in
the manifest at 3 sweeps x 10 providers x 300 runs x 4 rules x 2 (attack
and twin) = 72,000 runs.

Cell manifest and workload. `scripts/manifest.py` enumerates every cell
(rule, family, beta, rho, position, horizon, twin or attack, tuning or
control) and its run count, and the gate is a benchmark of the full path
through `sweep.py` for every baseline, not of one episode. Scope: the rho
sweep runs at beta = 0.05 only, D2 and its twin, median position, every
rule; H1 does not span rho. Expected counts at one rho: development 360,000;
twins 360,000; tuning about 300,000; controls about 50,000; all-deviators
about 72,000. The two extra rho values add about 2 x 2 x 3 x 7,500 =
90,000. Total about 1.3 million runs. Gate: the manifest completes in under
17 core-hours, which needs a run under 45 ms; cells are embarrassingly
parallel.

### 5.4 LLM actor and H1 procedure

Provider role only. The actor returns, in a fixed JSON schema, a private
effort q in [0, q_max_i] and either an offer (claim, bid) or abstain. Effort
goes to provider state and never to the Mechanism. The actor cannot exit.
Its twin is the same actor with the claim clipped to <= q by the harness.

Rule description. Each rule implements `describe()`, which returns a
structured record with locked fields and a locked vocabulary: allocation
order, eligibility, payment formula, audit selection, audit tolerance,
consequence of a failed audit, ban length, hold-back schedule. A sealed
template renders that record into prose identically for every rule. No
source code, comments, literals, or names reach the actor. A test asserts
every field value is in the vocabulary. Every field also admits the value
"not expressible"; if the proposed rule's record uses it in any field, H1
against that rule is INCONCLUSIVE, so a coarse record cannot hide a feature
from H1. The rule designer fills the record for the proposed rule, the
separate session checks at the unseal that the record matches the frozen
rule's behaviour on a fixture, and the record is frozen in the
evaluation-freeze tag; the vocabulary is frozen at the lock, before the rule
exists.

Comprehension fixture. Before the unseal, the actor answers a locked set of
factual questions about each rule from its description (for example, what
happens after a failed audit). This does not run the market. A rule whose
description the actor answers worse than the baselines by more than one
question is reported, and H1 against it is INCONCLUSIVE.

Procedure. Pinned model snapshot ID, temperature 0, every request and
response cached by prompt hash so replay is deterministic. A malformed
response falls back to honest-max for that round and is counted. If more
than 5% of rounds in a repetition fall back, that repetition is invalid; if
more than 2 of 10 repetitions are invalid, the cell is INCONCLUSIVE. The
evaluated object is the adaptive procedure: 5 episodes of T = 100 rounds in
which the actor sees its profit between episodes. Episodes 1 to 4 use
dev-train seeds; episode 5 uses one seed from the evaluation namespace, and
its profit is the reported statistic. The procedure is repeated 10 times
with 10 evaluation seeds; the actor learns within a procedure, never across
repetitions. S_hat, B, and the twin are calibrated and run at T = 100. Scope:
beta in {0.02, 0.05, 0.10}, 4 rules, one rho. Calls: 3 x 4 x 10 x 5 x 100 =
60,000 for the attack and the same for the twin. A token and latency pilot
of 200 calls is run before the lock and its measured cost per call sets the
cost cap in the lock commit.

## 6. Pre-registration protocol

Seed namespaces. Three disjoint ranges are fixed at the lock: dev-train
(search objectives), dev-val (all pre-lock reporting, tuning re-checks, and
the coverage study), and final-eval (the predicate). Final-eval seeds are
generated by the separate session, held by it, never executed or inspected
by anyone until the evaluation freeze, and released with the sealed bundle.

Lock, 2026-10-28, after baselines are tuned and before any proposed rule
exists. The lock commit contains:

- `experiments/locked.yaml`: all distributions, N, J, T, k_i, sigma, e, rho
  grid and scope, beta grid, tuned baseline parameters including tol_R and
  L, the admissible-class constants L_max and H_max, the dev-train and
  dev-val seed ranges, the search settings of 5.3, the H1 budget and cost
  cap, and the interval algorithms of section 8;
- `experiments/families.md`: the executable definitions of D1, D2, their
  twins, and the knob transforms;
- the lock tag itself fixes every tracked file. `check_claim.py` refuses a
  run if any tracked file differs from the lock tag except those on the
  post-lock allow-list: the proposed-rule module
  `sim/mechanisms/proposed.py`, its tuned-parameter config, its `describe()`
  record, `scripts/plot.py`, `docs/`, `sealed/` (checked instead by the
  bundle hash), and `sealed/patches/` (logged repairs by the separate
  session). Everything else, including `sim/market.py`, `sim/search.py`,
  `sim/policies/` (with `llm.py` and `identity.py`), `sim/llm_actor.py`
  (schema, cache, episode procedure, and the `describe()` renderer),
  `sim/mechanisms/base.py` and the baselines, `sim/metrics.py`,
  `scripts/run.py`, `scripts/sweep.py`, the CSV schema, and
  `experiments/vocabulary.yaml`, is frozen at the lock. So the LLM harness
  and the H3 policy are built and tested on development families before the
  lock. After the evaluation freeze, `check_claim.py` compares allow-listed
  files to the freeze tag instead, and refuses any tracked file that is new
  since the lock and outside the allow-list. `sealed/` and
  `sealed/patches/` are excluded from both tag comparisons, because they
  arrive after the freeze: `sealed/` is checked against the bundle hash in
  the lock commit, and each patch against its own logged hash;
- `scripts/check_claim.py` with the predicate of section 8 and the final
  threshold numbers, tested on synthetic CSVs;
- the coverage-study report (section 8) and its pre-registered consequences
  for H1 and for the 20-seed bootstrap;
- the SHA-256 of the sealed held-out bundle (section 6.1);
- a statement that exactly one proposed rule will be evaluated.

`check_claim.py` refuses any config or pipeline file whose hash differs
from the locked one. The lock commit is tagged, the tag is signed, pushed to
a public remote, and its hash is posted to a third-party timestamp (OSF
registration or AsPredicted) the same day.

Evaluation freeze, 2026-11-11. The proposed rule, its `describe()` record,
and its tuned parameters are frozen in a second signed tag. Held-out
families and final-eval seeds are never executed before this tag exists.

Repairs. The original sealed bundle is preserved unchanged. A repair after
the unseal is a separately hashed patch, written by the separate session,
limited to interface errors, logged, and reported. A repair that changes any
decision of H1 or H2 on a dev-val seed, as opposed to making the code run,
demotes the affected cell from confirmatory to exploratory.

### 6.1 Held-out families

- H1 LLM provider (section 5.4), with a sealed system prompt.
- H2 a parametrized family with a sealed executable definition, knob
  domains, a claim map that permits claims below effort, and an explicit
  containment statement: whether H2 contains D2, is contained by it, or is
  non-nested, and which observation or memory it uses that D2 cannot.

Neither H1 nor H2 exits or re-enters. Identity replacement is tested only by
H3 (section 6.2).

The sealed bundle (spec, prompts, code for H1 and H2 and their twins,
final-eval seeds) is written before the lock by a separate AI session that
has no access to any rule-design work and whose output the author does not
read until the unseal. Random salt included. The policy interface is frozen
at the lock. Before the lock, the separate session runs the sealed code
against B1 only and records pass or fail; B1 reveals nothing about the
proposed rule. The bundle enters the repo at the unseal in week 5 and CI
checks the hash.

The hash commits to content. The two freezes, the custodian-held seeds, the
public timestamp, and the disclosed access log are what support the claim
that nothing was run early.

### 6.2 Pre-declared stress test

H3 identity replacement: exit after a failed audit, re-enter under a fresh
identity at cost e. It is public in this spec, so it is not held out. It is
reported in its own table as a stress test, and the rule may be designed with
it in mind.

## 7. Metrics

All totals are over T rounds on the seed namespace stated for the run. S* is
computed per seed.

- First-best S*. Per round, the maximum over assignments of unit jobs to
  provider capacity slots and over effort, with the option not to serve, of
  the sum over served jobs of v_j * E[y] - a_i - b_i * q. With E[y] = q and
  linear cost, each served pair is best at q = q_max_i, common to all jobs of
  that provider, so the pair weight is max(0, v_j * q_max_i - a_i - b_i *
  q_max_i) and S* is an exact maximum-weight assignment (Hungarian on k_i
  duplicated slots).
- Ledger. Per identity and round: gross escrow funding G (buyers' payments
  into escrow for its jobs), refunds F (returned to buyers), held-back
  amounts K (bond), bond releases K_rel (including terminal settlement in
  round T and post-exit releases credited to the entity), forfeits K_forf
  (to buyers, booked once), net released receipts R = G - F - K + K_rel,
  production cost C, entry cost E. Entity profit pi = sum over rounds and
  over all its identities of (R - C - E), after terminal settlement, so no
  money owed to a provider is outside pi. A cash-conservation test checks,
  every round and at the end, that cumulative buyer funding equals
  cumulative provider receipts plus refunds plus forfeits plus the
  outstanding bond balance, and that the outstanding balance is zero after
  round T. The operator's net position is audit cost only.
- Net surplus W. Sum over served jobs of v_j * y - a_i - b_i * q_i, minus
  entry costs paid, minus audit cost. Uses true quantities, never claims.
- Gross efficiency = (W + audit cost) / S*. Net efficiency = W / S*. The claim
  uses gross; tables report both.
- Audit spend = audit cost / S*, per seed; also the fraction of served jobs
  audited.
- Reference run. For a focal entity in a cell, the reference run is the run
  of the cell's chosen reference policy (section 5.2: twin, honest-max, or
  abstention, selected once on dev-train seeds) with every other provider on
  honest-max, same seeds.
- Adversary gain. Per seed, gain = (pi_attack - pi_ref) / (S* / N). The
  statistic is the mean over evaluation seeds with a paired bound. Tables
  also report (pi_attack - pi_ref) / pi_ref where pi_ref > 0.
- Harm to others, per seed in units of S*:
  harm = [(W_ref - W_attack) + (pi_attack - pi_ref)] / S*. This equals the
  change in the summed utility of buyers (value minus funding plus refunds
  plus forfeits received), non-focal providers (their pi), and the operator
  (minus audit cost), which the code computes directly after terminal
  settlement. The equality is a test, run on fixtures with outstanding,
  released, and forfeited bonds.
- Efficiency triple, per rule and budget: all-honest gross efficiency,
  gross efficiency in the reference run, gross efficiency with the attack.
  The inflation-caused loss is eff(ref) - eff(attack). The gap
  eff(honest-max) - eff(ref) is truthful re-optimization and is reported
  separately.
- Scripted-participant diagnostics: expected profit, audit exposure,
  false-ban frequency, and lost capacity of non-focal providers, per rule.

Noise and the benchmark. S* uses E[y]. W uses draws. A single seed can exceed
S*. The test is: mean gross efficiency over evaluation seeds <= 1 + 2
standard errors in the all-honest run.

Common random numbers. Job values and delivery noise are drawn from
`numpy.random.SeedSequence` children keyed by (seed, round, job) and
(seed, round, provider, job slot), independent of any action. Policy
randomness is keyed by (seed, round, provider). Action-independent draws and
S* are precomputed per seed and shared across cells.

## 8. The claim and its check

Budget grid: beta in {0, 0.01, 0.02, 0.05, 0.10, 0.20}. For each rule R, each
family F, and each beta, run the search of section 5.3 (or the H1 procedure)
and its twin, and record gain, gross and net efficiency, audit spend, and
the efficiency triple on evaluation seeds (20 for parametrized families, 10
for H1).

Figure 1: gain against audit spend, one line per rule, one panel per family,
mean and bound, with the honest failure rate Phi(-tol_R / sigma) of each
rule annotated. Figure 2: efficiency triple against audit spend.

Interval algorithms, locked. Parametrized families: percentile bootstrap on
the per-seed paired statistic, 10,000 resamples, seed as the resampling
unit, one-sided; if all per-seed values are identical the bound equals that
value and the cell is flagged degenerate. H1: one-sided t bound on 10
repetitions, or the bootstrap if the coverage study selects it.

Coverage study, pre-lock, on dev-val seeds. Simulate the bound procedures on
development cells chosen to include rare profitable histories and
ban-induced multimodality, and report empirical coverage. Pre-registered
consequences: H1 is confirmatory (in the predicate) only if the
10-repetition bound achieves at least 90% empirical coverage at nominal 95%
in that study; otherwise H1 is reported as exploratory and the predicate's
rule clause uses H2 only, and the paper says so. For the 20-seed bootstrap
used by parametrized families, if empirical coverage is below 90%, the
locked remedy is a studentized bootstrap; if that is still below 90%, the
final-eval namespace is 40 seeds instead of 20, and the manifest and gate
are recomputed before the lock.

Claim predicate, evaluated by `scripts/check_claim.py` at beta = 0.05 on
final-eval seeds. R* is the proposed rule. The rule clause requires every
bound to hold, so its bounds use level 95%. The baseline clause passes
through any one of four alternatives (two families times two metrics), so
its bounds use level 98.75%. Numbers are provisional until the lock.

Rule clause. For each confirmatory held-out family F, all of:

- lower 95% bound of gross efficiency(R*, F) >= 0.90;
- upper 95% bound of gain(R*, F) <= 0.30, gain in units of S* / N;
- total audit cost <= B in every evaluation seed. Mean audit cost / S* is
  reported next to it.

Baseline clause. For each baseline B in {B2, B3} at the same beta, there is at
least one confirmatory F such that at least one of the two alternatives
below holds; the clause is PASS if any (family, alternative) pair is PASS,
FAIL if all are FAIL, and INCONCLUSIVE otherwise:

- lower 98.75% bound of the inflation-caused loss difference
  [eff(B, ref_B) - eff(B, F)] - [eff(R*, ref_R*) - eff(R*, F)] >= 0.05,
  paired per seed, where ref is each rule's own reference run; or
- lower 98.75% bound of gain(B, F) >= 1.0, in units of S* / N.

The all-honest gap and the truthful re-optimization gap are reported as
labeled results outside the predicate.

B1 is reported but is not part of the predicate, because it spends no audit
budget.

Decision rule per clause: PASS if the stated one-sided bound clears the
threshold; FAIL if the opposite one-sided bound at the same level misses it;
INCONCLUSIVE otherwise. The claim is PASS only if every clause is PASS, FAIL
if any clause is FAIL, and INCONCLUSIVE otherwise. INCONCLUSIVE counts as
not PASS for the kill criteria and is reported.

The gain in every clause is the gain achieved by the search of section 5.3,
whose objective is that same statistic; the paper calls it best-found gain
and never maximal gain. Efficiency in the predicate is measured under that
attack at the cell's headline position for H2, and under the section 5.4
procedure at the median position for H1; the paper states that this does
not bound efficiency under other attacks or positions.

Units note. S* / N is the mean first-best surplus per provider. A gain of 0.30
means the adversary captures 30% of an average provider's first-best share
beyond what matched truthful play gives it. The provisional 0.30, 1.0, and
0.05 are set from the baseline runs at the lock, and the paper states that
gain is the primary clause.

## 9. Candidate results

Hypotheses to test, with conditions. Validation cases are checks on the
simulator; propositions are candidates for the EC version and are stated
with the supremum over the policy class of section 5.1, never best-found.

- Validation: inspection inequality. Fix the claim at q_max and the
  allocation, and consider an effort cut delta under uniform audits at rate
  p with full refund of the audited job's payment P and no bans. Truthful
  failure probability is d0 = Phi(-tol_R / sigma); with the cut it is
  d1(delta) = Phi((delta - tol_R) / sigma). The cut is unprofitable iff
  p * P * (d1(delta) - d0) >= b * delta. On B2 with L = 0 and a fixed fixture
  in which p* = b * delta / (P * (d1 - d0)) <= 1, the measured gain from
  effort cuts must cross zero within seed noise of p*; a second fixture with
  p* > 1 must show no crossing.
- Proposition A, history-dependent audits. Fix B2's allocation, pricing,
  and enforcement, and vary only the audit-selection rule within the
  admissible class; hold participation and T fixed; measure expected audit
  spend. Restrict to the nondegenerate subclass in which each identity is
  served in at least two rounds with an audit opportunity between them, and
  e = infinity. Statement: for any uniform selection rule with positive
  expected spend that holds supremum gain at most epsilon, there exists a
  history-conditioned selection rule that holds gain at most epsilon at
  weakly lower expected spend; the target is a strict reduction with a
  lower bound in terms of rho, sigma, T, and the audit-opportunity count.
  Known qualitatively in tax-audit theory (Landsberger and Meilijson 1982;
  Greenberg 1984); the contribution would be the quantitative bound.
- Proposition B, cheap identities. Stationary setting: fixed prices, fixed
  allocation probabilities, the audit budget uncoupled from identity
  history, and consequences limited to identity-linked continuation value
  with fresh identities treated as clean. Then the stage cheat gain g is the
  same in every round, and with e = 0 and immediate re-entry supremum gain
  is at least T * g. Outside that setting the bound is a conjecture. Rules
  with refunds or hold-backs (B2, B3, and anything in 4.0 that uses them)
  are outside the proposition's class; experiments on them test deterrence
  by immediate consequences, which the proposition does not cover. The
  newcomer-cost escape (probation) is the Friedman and Resnick (2001)
  trade-off and is measured, not assumed.
- Trade-off, not threshold: honest failure probability Phi(-tol_R / sigma)
  against the undetected inflation tol_R. Reported as a curve per rule.

## 10. Application profiles (later)

A profile is a YAML file that fixes distributions, rho with its source, and
names: inference tokens (quality is fidelity to the promised model; rho from
touchstone-meter's per-probe cost), GPU hours (quality is delivered over
promised throughput; audit is a benchmark job). No code change expected.

## 11. Layout

```
touchstone/
  sim/
    market.py        # entities, round sequence, keyed RNG, private effort, ledger
    mechanisms/      # base.py (interface + admissible-class checks), posted.py,
                     # posted_audit.py, second_score.py
    policies/        # honest.py, fixed_cheat.py, adaptive.py, llm.py, identity.py,
                     # twin.py (claim-clipping wrapper)
    search.py        # CMA-ES best response, registered settings, seed namespaces
    metrics.py       # S*, ledger, W, efficiency, gain, harm, triple
    llm_actor.py     # schema, cache, fallback, episode procedure, describe() renderer
  experiments/       # locked.yaml, families.md, vocabulary.yaml, sweep configs
  scripts/
    calibrate.py     # S_hat, m, n_FB, validity check
    manifest.py      # every cell and its run count
    tune_baselines.py
    coverage_study.py
    run.py, sweep.py, plot.py, check_claim.py
  sealed/            # empty until the unseal; hash in README
  tests/
```

Dependencies: numpy, scipy, cma, pyyaml, pandas, matplotlib, pytest; the
Anthropic SDK behind a thin interface for the LLM actor.

## 12. Tests

- Honest-max equals its twin exactly, round by round, under every rule.
- Headline gain of honest-max in a cell whose chosen reference is honest-max
  is exactly 0; in a cell whose chosen reference is abstention it equals
  pi_honest_max / (S* / N).
- All-honest mean gross efficiency <= 1 + 2 SE.
- One provider, one job, zero noise: S* matches the closed form.
- Same config and seed give a byte-identical CSV for every non-LLM family;
  LLM replay from cache is byte-identical.
- Total audit spend never exceeds B; the per-round cap holds; a fractional
  remaining budget in the last round never produces an audit that exceeds
  it.
- Spread schedule: on a fixture with at least 20 expected audits per half,
  audits in the two halves differ by less than 10%.
- On the B1 fixture of section 5.3, D1 at u = 1, m = 1 gives positive gain
  and the search recovers it within 1%.
- A deviation in round t changes no job draw or noise draw in round t + 1.
- Cash conservation holds every round; the harm identity holds to
  floating-point tolerance.
- Admissible class: the interface rejects an effort field; two runs with
  identical visible histories and different hidden effort or unaudited noise
  produce identical mechanism decisions; relabeling identity ids produces
  the same decisions up to relabeling; no consequence outside 4.0 is
  reachable (property test over the enforce output type); operator injects
  no money.
- Honest failure rate under audit equals Phi(-tol_R / sigma) within binomial
  tolerance.
- S* > 0 on every seed of a valid configuration.
- Twin wrapper: a twin's market-facing claim never exceeds its effort.
- Every rule's `describe()` record uses only vocabulary values; the
  rendered text contains no token from the rule's source.
- Every mechanism passes one shared harness test on a tiny market, with a
  worked-example assertion for B3's payment.
- Locked config and pipeline hash check refuses a modified file; after the
  freeze, allow-listed files are compared to the freeze tag and a new
  tracked file outside the allow-list is refused.
- `proposed.py` imports only `sim/mechanisms/base.py` and standard numerical
  libraries, and no frozen module's attributes change after importing it.
- Sealed bundle hash check passes once the bundle is present.

## 13. Timeline and gates

| Dates | Work | Gate |
|---|---|---|
| 10-14 to 10-17 | Market, ledger, B1 to B3, honest-max, twin wrapper, metrics, tiny-market tests | One T = 200 B2 episode under 45 ms on one core |
| 10-18 to 10-24 | Search with namespaces, D1, D2, twins, LLM harness and renderer on development families, H3 policy, manifest, calibrate, tune baselines, coverage study, token pilot | B1 fixture check passes; full manifest under 17 core-hours |
| 10-25 to 10-28 | Separate session writes sealed bundle and final-eval seeds; vocabulary; check_claim.py; lock | Signed tag, public timestamp |
| 10-29 to 11-11 | Proposed rule within 4.0; its describe() record; its tuning; H3 runs on the proposed rule | Evaluation freeze tag |
| 11-12 to 11-18 | Unseal; comprehension fixture; run H1, H2 and twins on frozen rule and baselines; figures | Hash verified; check_claim output |
| 11-19 to 11-25 | One page. Decide. | |

If the second gate slips, cut beta in {0.01, 0.20} first, then the rho
sweep to {0.2, 1}, then D1, never the seed namespaces, the twins, or the
baseline tuning.

## 14. Review changelog

Round 1 (version 1 to 2), three independent reviews on 2026-10-14: S*
fixed effort and used a slot LP; honest policy undefined; search a lower
bound and seeds unsplit; lock forbade nothing, H3 inside D2, hash not
third-party; eval config and rule count unlocked; claim quantifiers;
baselines untuned, B3 misnamed; audit scale and budget semantics; round
timing and settlement; section 9 imprecise; feasibility; CRN; loss to
others. All changed as recorded in versions 2 and 3.

Round 2 (2 to 3.1): clipped noise made E[y] nonlinear; effort in the offer;
zero reference profit; mismatched reference runs; H1 procedure; point
estimate against bound; audit units; failure-probability formula; B1 check
fixture; Proposition A strictness; bilevel tuning; sweep gate; audit
schedule emptied by T/2; spend clause per seed; INCONCLUSIVE rule;
allocation-only efficiency gap; tuning objective; H1 rule text; H1 horizon;
sealed smoke test; supremum in propositions; rho source.

Round 3 (3.1 to 3.3): Bonferroni count; S* > 0 per seed; clipped truthful
claim; README drift; position by gain; price grid cap; AST-stripped rule
text; family domain; tuning units; H1 position and bounds; workload count;
Proposition B content.

Rounds 4 to 6 (3.3 to 3.8): ordered price grid; README H1 exception and
gate; P_top requirement; hard audit cap; H1 effort in schema and no exit;
Proposition B newcomer cost; tuning reference; position scope; claim upper
bound; per-round cap floor; tuning position. Three-seat consensus on 3.8.

External read (GPT Pro, on 3.8; it read the public meter README, not this
repo's, so its README remarks are moot) and the changes in version 4:

- Static truthful reference versus adaptive attackers; conservative claims
  excluded by the equality: matched truthful twin per family with claims
  clipped to <= effort; reference = max(twin, honest-max, abstain); gain
  stated as a difference of two searched values.
- Search maximized profit while the statistic is normalized gain: the
  search objective is the headline statistic.
- Loss contrast used honest-max, not the gain reference: contrast uses each
  rule's reference run; truthful re-optimization gap reported separately.
- Tolerance tuning changed the meaning of a truthful claim: claim semantics
  fixed (promise on expected quality, truthful iff claim <= effort); tol_R
  is rule-only; grid moved to {0.08, 0.12, 0.16}; validity conditions on the
  claim removed.
- Mechanism class not closed: section 4.0 admissible class (inputs,
  transfers, enforcement menu with L_max and H_max, budget) with
  information-flow, relabeling, and output-type tests.
- Adversary search not reproducible: executable D1/D2 recurrences, domains,
  transforms, CMA-ES settings, registered initial points; H2 containment
  statement; families file hashed at lock.
- Seed namespaces and unbound measurement code: dev-train, dev-val,
  final-eval held by the custodian; pipeline hashes in the lock; repair
  rule with confirmatory demotion.
- LLM description pipeline: structured `describe()` with locked
  vocabulary; comprehension fixture; fallback thresholds to INCONCLUSIVE.
- Bound coverage at n = 10: locked interval algorithms; pre-lock coverage
  study with a pre-registered consequence for H1's confirmatory status.
- Workload omitted rho; H1 cost unmeasured: cell manifest, full-path
  benchmark, rho scope, token pilot, 16 core-hour gate.
- Proposition A unconstrained: fixed objects, audit-selection class only,
  nondegenerate subclass, expected spend.
- Proposition B cumulative bound and refunds: stationary setting stated;
  refund-capable rules outside its class.
- Scripted participants, ledger terms, m denominator, fixture conditions:
  labeled; ledger with cash-conservation test; m = S_hat / n_FB; conditions
  added.

Round 7 (4 to 4.1):

- Bonds had no terminal settlement, exit ownership, or single-booked
  forfeits (Astra): defined in 4.0 and the ledger; tests on bond fixtures.
- Logistic transform cannot reach corner starts (Astra): near-corner
  registered points; exact corners as controls outside the budget.
- README gain definition and honest-max test ignored the full reference
  (Astra): aligned.
- D-families and twins could not claim below effort (Opus): margin knob s;
  H2 claim map must permit it.
- Lock hashed only the metric scripts (Opus): the lock tag fixes every
  tracked file; post-lock allow-list named.
- Reference was a per-seed maximum of three runs (Opus): one reference
  policy per cell chosen on dev-train seeds.
- Coverage remedy for the 20-seed bootstrap (Opus): studentized bootstrap,
  then 40 seeds.
- All-deviators budget and manifest entry (Opus): stated.
- describe() could hide a novel feature (Opus): "not expressible" value
  makes H1 INCONCLUSIVE; custodian check at the unseal.
- README said analysis scripts freeze at the second tag (Opus): aligned.

Round 8 (4.2 to 4.3):

- Section 4.0 put forfeits in the operator's position (Astra): audit cost
  only.
- README claim, freeze summary, and gate wording lagged the spec (Astra):
  aligned.
- Whole-tree lock froze the LLM harness and H3 that the timeline built after
  the lock, and the allow-list lacked the sealed folder and repairs (Opus):
  harness and H3 moved before the lock; sealed/ and sealed/patches/
  allow-listed; post-freeze comparison to the freeze tag; import test.
- Near-full-cheat start put the margin near its maximum (Opus): s at its
  minimum there.
- All-deviators count, lock list wording, README adversary wording (Opus):
  corrected.

Round 9 (4.4 to 4.5):

- Blanket freeze-tag comparison contradicted the sealed-folder hash check
  (Astra): sealed paths excluded from tag comparison and checked by their
  hashes; README names the exception.
