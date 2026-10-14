# Touchstone simulator: design

Date: 2026-10-14. Version 6.5, after fourteen rounds of three-model review
(Fable 5.1, Opus 5.5, Astra) and three external reads (GPT Pro). Status:
draft for review. Section 14 maps review objections to changes.

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
    def enforce(self, audit_results, state) -> (Consequences, PolicyMemory)
    def describe(self) -> RuleDescription   # section 5.4
```

`offers` carries claims and bids only. `enforce` returns the consequences
it imposes (from the section 4.0 menu) and the rule's own policy memory;
the harness ledger applies the consequences to the economic fields of
`state` (bans, hold-back balances, releases, forfeits, receipts), which a
rule reads but never writes. The output-type test of section 12 checks the
consequences object. `state` is the operator's memory:
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
  is booked once, to the buyers of the failed jobs that triggered it, and
  the forfeit for a failed job is at most that job's escrowed payment. The
  refund cap and the forfeit cap are separate: one failed job with escrow P
  can cost the provider up to P in refund plus up to P in forfeit, so the
  class permits stronger immediate consequences than B2 and B3 use. The
  paper reports refund and forfeit contributions separately and includes an
  enforcement-matched ablation (section 8) before attributing any win to
  allocation or audit selection. Any excess over the cap is released to the
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
  5.5%, 0.8%, 0.07% at sigma = 0.05) and L in {10, 20, 50}, so a long ban is
  not an advantage reserved for the proposed rule;
- inner search: D2 at the median position, 1 restart x 100 evaluations x 3
  dev-train seeds, with its truthful twin (section 5.2) searched at the
  same budget and the reference selected last by the section 5.2 rule over
  the candidates that inner search discovered;
- objective: the smaller of the two normalized predicate margins at
  beta = 0.05, min((gross efficiency - 0.90) / 0.90, (0.30 - gain) / 0.30);
- the top 3 grid points are re-checked at the full search budget of section
  5.3 and the best is locked.

The proposed rule's own parameters get the same outer budget (243
configurations, matching 27 x 3 x 3) and the same inner search, logged.

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
with the same budget, and its objective is the same normalized statistic
the attacker uses: the mean over dev-train seeds of pi / (S* / N). The
reference policy for a cell is one policy, chosen on dev-train seeds by that
same normalized objective among the twin, honest-max, and abstention
(profit 0), and among every other admissible truthful candidate discovered
for that cell before final evaluation: any attack-search candidate or
compatible candidate-bank member whose market-facing claim is at most its
effort in every round of its dev-train runs, whatever its clip value, and
the clip = 1 projection of the selected attack evaluated on dev-train
seeds. Reference selection is therefore the last step before
evaluation, after the attack search and the bank pass, and gains and the
headline position are recomputed with the finalized reference. Ties are
broken deterministically by the registered candidate order. pi_ref on
evaluation seeds is the per-seed profit of that one chosen policy, never a
per-seed maximum, and the reference is fixed on evaluation seeds. One
preference ordering is used throughout, so subtracting the fixed reference
does not change the attacker's ranking of candidates.

Decomposition, reported per cell on evaluation seeds with a registered
interpretation rule: headline gain = (pi_attack - pi_clip) / (S* / N) +
(pi_clip - pi_ref) / (S* / N), where pi_clip is the profit of the
clipped-attack run (section 7). The first term is the profit effect of
allowing inflation for the selected policy; the second is the difference
between the clipped policy and the reference. Only the first term is ever
described as profit from inflation. If the selected attacker is itself
truthful the first term is zero and the paper says so.

Containment. Every reference policy must be executable by the unrestricted
attacker. For parametrized families this is enforced by construction: the
attacker family is closed under the clip, with a binary knob clip in
{0, 1} that applies the same harness projection (section 5.3), so every twin
policy is a point of the attacker family. For H1, the twin's realized
actions are in the attacker's action space (any claim <= q is a legal
output), and the paper states that this is action containment, not policy
containment. Abstention is not a point of D1 or D2 and is not claimed to be
contained; a cell whose chosen reference is abstention is labeled as such.
The best twin point (clip = 1) and the honest-max point are in the
registered incumbent set of the attack search, and the clip = 1
projection of the selected attack is evaluated as an attack candidate too
and replaces the incumbent when it scores higher. Even so, best-found
dev-train gain can be negative (for example when the reference is
abstention, or when a late truthful candidate outscores the selected
attack); no nonnegativity is claimed, and negative gain is reported as
such. A pre-lock test checks that every twin
candidate re-run as an attacker with clip = 1 reproduces its trajectory
exactly, and that the honest-max point of each family reproduces honest-max;
for H2 the separate session runs both tests against B1 before the lock.

Because pi_ref is itself a best-found quantity, the paper states that gain
is the difference of two searched values and can be biased in either
direction by search error; the search checks of 5.3 are diagnostics of that
error, not a bound on it.

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

Clip knob and twins. Both families carry a binary knob clip in {0, 1},
searched as one more logistic coordinate thresholded at 0.5 (registered
initial values: 1 at the near-honest point, 0 at the near-full-cheat point,
0.5 threshold on the Sobol points); it costs no extra evaluations. With
clip = 1 the market-facing claim is min(c, q). D1-twin and D2-twin are D1
and D2 with clip fixed at 1; the attacker searches over clip too, so the
attacker family contains its twin by construction. The margin knob s stays
free in both, so a twin can claim conservatively. The sealed H2 family must
carry the same knob and the same containment (section 6.1).

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
(pi - pi_ref) / (S* / N). Because pi_ref is a per-seed constant for a
fixed reference, the search optimizes the mean of pi / (S* / N) and pi_ref
is subtracted after reference selection, which is the last step (section
5.2); the ranking of candidates is the same either way. The
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
twins 360,000; tuning about 572,000 (3 rules x 243 grid points x (100
attack + 100 twin) evaluations x 3 seeds = 437,400, plus 9 full re-checks
at 15,000 each); controls about 50,000; all-deviators about 72,000;
candidate bank about 46,000 (section 8); ablation about 90,000 (section
8). The two extra rho values add about 2 x 2 x 3 x 7,500 = 90,000. Total
about 1.64 million runs (360,000 + 360,000 + 572,000 + 50,000 + 72,000 +
46,000 + 90,000 + 90,000). The coverage study's manifest entry includes
the 35,000-seed pools and, only if the joint fixture test fails, one M
doubling and one R doubling. These prose totals are generated from
`manifest.py`, which separates pre-lock, post-lock, simulator, interval,
and LLM workloads; the manifest is authoritative. Gate: the pre-lock entries of the search manifest complete in under 20
core-hours, which needs a run under 45 ms; post-lock entries (bank and
ablation against the proposed rule) are estimates. Cells are
embarrassingly parallel. The coverage
study (section 8, about 0.5 million runs) is outside this gate and has its
own entry in the manifest.

### 5.4 LLM actor and H1 procedure

Provider role only. The actor returns, in a fixed JSON schema, a private
effort q in [0, q_max_i] and either an offer (claim, bid) or abstain. Effort
goes to provider state and never to the Mechanism. The actor cannot exit.
Its twin is the same actor with the claim clipped to <= q by the harness;
containment is at the action level (section 5.2).

Rule description. Each rule implements `describe()`, which returns a
structured record with locked fields and a locked vocabulary: allocation
order, eligibility, payment formula, audit selection, audit tolerance,
consequence of a failed audit, ban length, hold-back schedule. A locked
template in `sim/llm_actor.py`, frozen at the lock, renders that record into
prose identically for every rule. No
source code, comments, literals, or names reach the actor. A test asserts
every field value is in the vocabulary. Every field also admits the value
"not expressible"; if the proposed rule's record uses it in any field, H1
against that rule is INCONCLUSIVE, so a coarse record cannot hide a feature
from H1. The rule designer fills the record for the proposed rule, the
separate session checks at the unseal that the record matches the frozen
rule's behaviour on a fixture, and the record is frozen in the
evaluation-freeze tag; the vocabulary is frozen at the lock, before the rule
exists.

Comprehension fixture. At the unseal, before any market run with H1, the
actor answers a locked set of factual questions about each rule from its
description (for example, what happens after a failed audit). This does not
run the market. A rule whose
description the actor answers worse than the baselines by more than one
question is reported, and H1 against it is INCONCLUSIVE.

Procedure. Pinned model snapshot ID, temperature 0, every request and
response cached by prompt hash so replay is deterministic. A malformed
response falls back to honest-max for that round and is counted. The
statistic always includes all 10 attempted repetitions with their fallback
behaviour; no repetition is ever dropped or replaced, so the paired
comparison with the twin and the baselines keeps the same seeds. A
repetition with more than 5% fallback rounds is marked invalid; invalidity
gates only whether the cell can support a claim: if more than 2 of 10 are
invalid, the cell is INCONCLUSIVE, and a required cell that becomes
INCONCLUSIVE after the freeze stays in the confirmatory quantifiers as
INCONCLUSIVE. H1 is a five-episode adaptive procedure with profit feedback,
not the normalized-gain search of section 5.3; section 8 and the README
state this exception. The
evaluated object is the adaptive procedure: 5 episodes of T = 100 rounds in
which the actor sees its profit between episodes. Episodes 1 to 4 use
dev-train seeds; episode 5 uses one seed from the evaluation namespace, and
its profit is the reported statistic. The procedure is repeated 10 times
with 10 evaluation seeds; the actor learns within a procedure, never across
repetitions. S_hat, B, and the twin are calibrated and run at T = 100. Scope:
beta in {0.02, 0.05, 0.10}, 4 rules, one rho. Calls: 3 x 4 x 10 x 5 x 100 =
60,000 for the attack, the same for the twin on evaluation seeds, up to the
same again for the twin on dev-train seeds during reference selection, and
up to 12,000 more for the closed-loop clipped-attack run (episode 5 only,
3 x 4 x 10 x 100): 192,000 worst case. The invalidity rule (more than 5%
fallback rounds in a repetition) applies to every H1 run that enters a
predicate term: attack, twin, and clipped-attack. A token and latency pilot of 200 calls is run before the
lock and its measured cost per call sets the cost cap in the lock commit.

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
  lock. After the evaluation freeze, `check_claim.py` compares `proposed.py`, its
  config, and its `describe()` record to the freeze tag, checks `sealed/`
  against the bundle hash in the lock commit and each file in
  `sealed/patches/` against its logged hash, does not check `scripts/plot.py`
  or `docs/` (neither enters the predicate), and refuses any tracked file
  that is new since the lock and outside the allow-list;
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
  domains, a claim map that permits claims below effort, the same binary
  clip knob so that H2 contains its twin by construction, and an explicit
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
  of the cell's chosen reference policy (section 5.2: the best, on dev-train
  seeds, among the twin, honest-max, abstention, and every discovered
  admissible truthful candidate, selected once as the last step before
  evaluation) with every other provider on honest-max, same seeds.
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
- Clipped-attack run. The selected attacker policy re-run with its
  parameters unchanged and the harness clip applied, same seeds. For H1 the
  frozen procedure itself is re-run on the counterfactual history: the clip
  is applied in episode 5 only, prompts that match a cached prompt replay
  from cache, prompts that differ because clipping changed allocation,
  payment, or bans are new calls, and those calls are in the cost budget
  (at most 12,000, since the clip applies in episode 5 only). This is the intervention "same decision
  procedure, inflation removed", not action replay, and the paper says so.
  A test runs a case where clipping changes the next prompt and asserts a
  new call is made.
- Efficiency quadruple, per rule and budget: all-honest gross efficiency,
  gross efficiency in the reference run, gross efficiency in the
  clipped-attack run, gross efficiency with the attack. The
  inflation-caused loss is eff(clipped attack) - eff(attack): the effect of
  the intervention that prevents inflation for that policy. The gap
  eff(ref) - eff(clipped attack) is selection difference, and
  eff(honest-max) - eff(ref) is truthful re-optimization; both are reported
  separately and neither enters the predicate.
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
the efficiency quadruple on evaluation seeds (20 for parametrized families, 10
for H1).

Figure 1: gain against audit spend, one line per rule, one panel per family,
mean and bound, with the honest failure rate Phi(-tol_R / sigma) of each
rule annotated. Figure 2: efficiency quadruple against audit spend.

Interval algorithms, locked. Parametrized families: percentile bootstrap on
the per-seed paired statistic, 10,000 resamples, seed as the resampling
unit, one-sided; if all per-seed values are identical the bound equals that
value and the cell is flagged degenerate. H1: one-sided t bound on 10
repetitions, or the bootstrap if the coverage study selects it.

Coverage study, pre-lock, on dev-val seeds. Locked design: from the
universe of 18 development cells at beta = 0.05 (3 baselines x 2 families x
3 positions), take the top 3 by per-seed skewness of gain and the top 3 by
the Sarle bimodality coefficient of per-seed ban counts on dev-train seeds,
filling ties or overlaps from the other ranking, for 6 distinct cells;
selected by that mechanical rule, not by hand. Degenerate inputs: a cell
with zero variance in the ranking statistic (for example B1 ban counts) is
excluded from that ranking, undefined moments rank last, and if a ranking
is exhausted the other ranking fills.

Reference means. One reference pool per cell, shared by every sample size
n, because the pool estimates the per-seed mean and does not depend on n:
M = 35,000 dev-val seeds per cell (about 210,000 runs, in the manifest,
outside the search gate). At that size the coverage error induced by the
pool, about phi(z) * sqrt(n / M), is at most 0.35 points at n = 40. The
pool standard error is reported next to the replication standard error.

Replications. R = 2,000 replications of each bound procedure per cell and
endpoint (R = 4,000 at n = 40), each drawing the final sample size from a
fresh disjoint dev-val sub-range. Coverage is scored conservatively
against a 95% interval for the reference mean (an upper bound against the
interval's upper endpoint, a lower bound against its lower endpoint).

Endpoints. The four (statistic, side, level) triples the predicate uses:
gain upper 95%, gross efficiency lower 95%, inflation-caused-loss
difference lower 98.75% with a baseline pair (B2 versus B3) standing in
for the proposed rule, and gain lower 98.75%.

Threshold. For each (n, level, side) the threshold is the expected
conservative coverage of an exactly calibrated procedure under this
scoring, computed analytically from the noncentral t distribution and
checked by averaging an exact one-sided t bound on normal data over 200
simulated pools of size M with 20,000 replications each, minus a margin:
1.5 points at n = 10 and n = 20, 1.75 points at n = 40. There is no "too
wide" band and no routine pool doubling (the only doubling is the
joint-fixture remedy below): a procedure is admitted at a cell if its
measured conservative coverage is at least the threshold at every tested
endpoint, and admitted overall if it is admitted at every cell.

Joint fixture test, pre-registered. The exact procedure is pushed through
the complete joint gate (6 cells x 4 endpoints, one shared threshold per
endpoint, fresh pools and replications) 200 times; it must be admitted
overall with probability at least 0.9. If it is not, the remedy order is:
double M (once), then double R (once); if the joint test still fails, the
interval procedure is recorded as not admissible at that (n, level) and
every clause that depends on it is exploratory. The paper reports the
measured joint admission probability. The alternative of keeping M = 2,000
with a margin of z(1 - 0.1 / 24) * sqrt(SE_rep^2 + SE_pool^2) (about 2.7
points at n = 20 and 3.7 at n = 40) is not used, because it has little
power to reject an undercovering bootstrap.

The remedy order for the interval procedure itself is percentile
bootstrap, then studentized bootstrap, then 40 seeds with the studentized
bootstrap. The paper states that this calibrates the procedures on
development distributions and is not a guarantee for the unseen held-out
distributions under the later rule.

Pre-registered consequences. The H1 admission is a proxy calibration: the
10-observation t bound is tested on the D1/D2 development distributions at
sample size 10, because the H1 procedure cannot run before the freeze; the
paper calls it that. H1 is confirmatory only if that proxy bound meets the
criterion; otherwise H1 is exploratory and the rule clause
uses H2 only. For the 20-seed bootstrap of parametrized families: if it
fails the criterion, the locked remedy is a studentized bootstrap; if that
fails, the final-eval namespace becomes 40 seeds and the manifest and gate
are recomputed; if 40 seeds still fail, every clause that depends on that
bound is reported as exploratory with nominal intervals and the claim is
INCONCLUSIVE. No remedy admits a bound that failed the criterion.

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
  [eff(B, clip_B) - eff(B, F)] - [eff(R*, clip_R*) - eff(R*, F)] >= 0.05,
  paired per seed, where clip is each rule's clipped-attack run (section
  7); or
- lower 98.75% bound of gain(B, F) >= 1.0, in units of S* / N.

Enforcement-matched ablation, reported outside the predicate: the proposed
rule's allocation and audit selection combined with B2's enforcement
(refund plus ban at B2's tuned L, no hold-back); pricing and audit
tolerance stay the proposed rule's. The consequence outputs of `enforce`
are replaced, and the authoritative economic state (bans, hold-back
balances, releases, forfeits, receipts) is recomputed from the consequences
the ablation actually applies; only non-economic policy memory of the
original rule is retained, and it operates on the counterfactual history.
The split is typed: `base.py`, frozen at the lock, defines a State with
economic fields (bans, hold-back balances, releases, forfeits, receipts)
owned by the harness ledger and a separate policy-memory field a rule may
use freely. Exclusion is defined as zero allocation of an eligible offer
after a failed audit, whatever mechanism produces it; exclusion through
allocation priority is reported in the ablation table next to bans.
Ablation tests: exclusion duration by ban equals B2's L, hold-back balance
is zero throughout, and the ledger conserves cash. Because pricing and
tolerance are retained, a retained win is attributed to the non-enforcement
components collectively, not to allocation or audit selection alone.
Against the ablated rule the twin and the attack are searched again at the
full budget, the bank pass is applied, and then the reference is selected
as the last step by the section 5.2 rule. Cells: D1 and D2 at beta = 0.05,
all three positions, median rho (2 families x 3 positions x 2 searches x
7,500 = 90,000 runs, in the manifest as a post-lock estimate). H2 is not
ablated; the ablation is a development-family diagnostic. The paper
attributes a retained win to the non-enforcement components collectively
(allocation, audit selection, pricing, and tolerance together), never to
allocation or audit selection alone.

Candidate bank, registered before the lock, development families only.
Order: a first search pass per cell without the bank; then every best-found
attack policy and exact-corner control from every (rule, family, budget)
cell is stored; then for each cell every bank member is evaluated once on
dev-train seeds against that cell's frozen rule, through a typed
compatibility filter (a D1 member enters a D2 cell through d = r = 0; a D2
member never enters a D1 cell; members that are truthful by behaviour
also enter reference selection, section 5.2), and the incumbent is replaced if a
member scores higher on the normalized objective; a transfer table reports
how each rule fares against attacks found elsewhere. The
bank does not seed H2 unless the sealed H2 definition declares an embedding
of D2, in which case the embedding is applied; otherwise the bank is a
diagnostic for H2. Bank members found against the proposed rule exist only
after the lock and are applied to the baselines' post-lock re-runs. Members: every best-found policy from every (rule, family, budget,
position) cell, about 64 for four rules, plus the exact-corner controls of
D2 with the clip knob (128), de-duplicated; D1 members enter D2 cells
through d = r = 0; members do not cross between D2 and H2 except through a
declared embedding. Bank runs are in the manifest at about 4 rules x 2
families x 6 budgets x 192 members x 5 seeds = 46,000 runs, listed as a
post-lock estimate for the proposed rule's cells. This tests whether a rule's robustness
survives a profitable policy discovered against another rule.

The all-honest gap, the selection difference, and the truthful
re-optimization gap are reported as
labeled results outside the predicate.

B1 is reported but is not part of the predicate, because it spends no audit
budget.

Decision rule per clause: PASS if the stated one-sided bound clears the
threshold; FAIL if the opposite one-sided bound at the same level misses it;
INCONCLUSIVE otherwise. The claim is PASS only if every clause is PASS, FAIL
if any clause is FAIL, and INCONCLUSIVE otherwise. INCONCLUSIVE counts as
not PASS for the kill criteria and is reported.

The gain in every H2 clause is the gain achieved by the search of section
5.3, whose objective is that same statistic; the gain in every H1 clause is
the output of the section 5.4 procedure, which is not a search. The paper
calls both best-found gain and never maximal gain. Efficiency in the predicate is measured under that
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
  e = infinity. The weak statement (a history-conditioned rule reaches gain
  at most epsilon at weakly lower expected spend than any uniform rule) is
  class inclusion, since uniform rules are history-measurable, and is not a
  result. The target is a strict reduction with a lower bound that depends
  on rho, sigma, T, the audit-opportunity count, and the incentive
  constraint (payment P, effort-cost scale b, and epsilon); the conditions
  under which the reduction is strictly positive are to be identified
  before any theorem is claimed.
  Known qualitatively in tax-audit theory (Landsberger and Meilijson 1982;
  Greenberg 1984); the contribution would be the quantitative bound.
- Proposition B, cheap identities. Stationary setting: fixed prices, fixed
  allocation probabilities, the audit budget uncoupled from identity
  history, and consequences limited to identity-linked continuation value
  with fresh identities treated as clean. Let g be the raw stage cheat
  profit in currency units, measured against the stage truthful comparator
  (the best truthful stage action under the same prices), and let s be the
  deterministic per-round first-best surplus. Then with e = 0 and immediate
  re-entry the raw episode gain is at least T * g, and in the section 7
  normalized units the episode gain is at least N * g / s, not T times a
  per-round normalized gain. Outside that setting the bound is a
  conjecture. Rules
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
    metrics.py       # S*, ledger, W, efficiency, gain, harm, quadruple
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
- Spread schedule: the scheduler's per-round expected audit count equals
  (budget_left / alpha) / (T - t + 1) before caps (exact check on the
  rounding rule); feasibility and terminal budget accounting hold on every
  seed; and over 200 seeds of a fixture with 20 expected audits per half,
  the mean absolute half-difference is within 2 standard errors of its
  hypergeometric expectation. No single realization is a correctness test.
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
| 10-18 to 10-24 | Search with namespaces, D1, D2, twins, LLM harness and renderer on development families, H3 policy, manifest, calibrate, tune baselines, coverage study, token pilot | B1 fixture check passes; search manifest under 20 core-hours |
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

Round 8 (4.2 to 4.4):

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
  (Astra, Opus): post-freeze check scoped to the rule files; sealed paths
  by hash; plot and docs unchecked; README names the exception.
- Template location and comprehension-fixture timing (Opus): locked
  template in the harness; fixture at the unseal before any H1 market run.

Consensus (round 9) on version 4.6: Fable 5.1 accept-with-caveat, Opus 5.5
accept, Astra accept-with-caveat.

Second external read (GPT Pro, on 4.6) and the changes in version 5:

- Reference selected by mean profit while the attacker optimized normalized
  gain: one normalized objective for twin, reference selection, and attack.
- Clipped twin not contained in the D2 representation (counterexample with
  two failed audits): binary clip knob in the attacker family; containment
  by construction; action-level containment stated for H1; re-run test.
- Loss contrast confounded selection with inflation: clipped-attack run
  (same policy, inflation removed) defines inflation-caused loss; selection
  difference reported separately.
- Coverage gate admitted 90% for nominal 95% and left 98.75% untested, with
  no final failure branch: locked study design with Monte Carlo error, both
  endpoints, nominal minus 1 point, and a terminal INCONCLUSIVE branch.
- One or two invalid H1 repetitions undefined: all ten always included;
  invalidity gates claim support only; H1 exception stated in section 8.
- Enforcement menu stronger than baselines: caps stated as separate;
  L grid includes 50; enforcement-matched ablation outside the predicate.
- Proposition A weak form is class inclusion; Proposition B units:
  restated.
- Spread test deterministic on one realization: expectation, feasibility,
  and repeated-seed criterion.
- Candidate bank registered as the cheapest guard against optimizer-specific
  wins.
- "Search checks bound the error" softened to diagnostics.
- Caveat on 1/N: in a heterogeneous-capacity market one provider can serve
  most jobs, so 1/N is not a ceiling; the 0.05 threshold is a pre-registered
  practical effect size set at the lock.

Round 10 (5 to 5.2):

- H1 clipped-attack run by cache replay was ill-defined once clipping
  changed the history (Astra): the frozen procedure re-runs on the
  counterfactual history with new calls, budgeted and tested.
- Clip knob had no search mapping (Astra): logistic coordinate thresholded
  at 0.5, registered initial values.
- Tuning budget said 162 after the L grid grew (Astra): 243 everywhere;
  manifest and gate updated.
- H1 call count omitted the twin's reference-selection calls and the
  counterfactual (Opus): 240,000 worst case.
- Abstention not contained; search not guaranteed to find the twin point
  (Opus): reference point in the incumbent set; abstention labeled.
- Candidate bank scope, order, and count (Opus): development families
  only; first pass, then bank; H2 only via a declared embedding; in the
  manifest.
- Coverage study selection, triples, seeds, order (Opus): mechanical cell
  rule; four named triples; fresh seed sub-ranges; in the manifest.
- Ablation attack reuse (Opus): fresh search against the ablated rule;
  state updates kept.
- Text drift: quadruple, header, forfeit cap, H2 clip knob, custodian runs
  the H2 containment test (Opus).

Round 11 (5.2 to 5.3):

- Tuning workload used 150 evaluations per grid point where section 4.2
  requires 200 (Astra): 437,400 plus re-checks; total 1.55 million; gate
  20 core-hours; coverage study stated outside the gate.
- Ablation reference not re-selected, cells unnamed (Opus): twin and
  reference re-selected; cells and count stated; development only.
- Bank member count (Opus): de-duplicated corners with clip, D1 via D2,
  about 192 members, 46,000 runs.
- Coverage cell rule (Opus): universe of 18, top 3 by each of two named
  statistics, tie rule.
- H1 counterfactual calls and invalidity scope (Opus): 12,000; rule applies
  to every H1 run in a predicate term.
- Gate scope, layout comment, round label, H2 honest-max test (Opus): fixed.

Consensus (round 11) on version 5.3: Fable 5.1 accept-with-caveat, Opus
5.5 accept, Astra accept-with-caveat. No material objection outstanding.

Third external read (GPT Pro, on 5.4) and the changes in version 6:

- Coverage gate treated a 2,000-seed reference mean as truth; a calibrated
  bound could fail the 94% threshold from reference error alone:
  reference-mean interval, conservative scoring, separate error reporting,
  registered pool doubling, analytic fixture.
- Ablation kept state updates that could re-impose the original bans or
  fictitious bond balances: economic state recomputed from applied
  consequences; tests; attribution to non-enforcement components
  collectively.
- Candidate bank could install a better truthful policy as the attack
  while the reference stayed stale (construction: two truthful tier-3
  policies differing only in effort): reference selection is the last
  step and includes every discovered truthful candidate; typed
  compatibility filter; deterministic ties.
- H1 coverage admission is a proxy calibration and is labeled so;
  degenerate ranking inputs defined.
- Stale workload counts: generated from the manifest; 12,000 H1
  counterfactual calls stated consistently.
- Gain decomposition into inflation effect and clipped-versus-reference
  difference, reported with a registered interpretation rule.

Round 12 (6 to 6.1):

- README and section 7 kept the old three-candidate reference list (Astra):
  aligned with the section 5.2 rule.
- Ablation wording kept the old selection order and attribution (Astra):
  reference last; collective attribution.
- Workload total did not match its components (Astra): corrected.

Round 12, second pass (6.1 to 6.2):

- Endpoint scoring over the reference interval rejected exact bounds, so
  the gate was INCONCLUSIVE by construction (Opus, by simulation):
  threshold calibrated on an exact fixture through the identical path,
  minus 1.5 points; fixture admission test; "too wide" defined; terminal
  outcome stated.
- Behaviourally truthful clip = 0 candidates were excluded from reference
  selection; incumbent sentence and objective wording predated late
  selection (Opus): truthful-by-behaviour admission; wording fixed.
- Ablation state split untyped; exclusion by priority uncovered (Opus):
  typed State at the lock; exclusion defined and reported.
- README claim block, total (1.64 million), tuning reference rule,
  doubling runs (Opus): fixed.

Round 13 (6.2 to 6.3):

- Fixture admission test doubled replications against an error that lives
  in the reference pool; an exact procedure was admitted only about 79% of
  the time (Astra, numerically): threshold calibrated as the 10th
  percentile across 200 independent reference pools; independent
  validation on 50 pools; M doubling and recalibration with a stopping
  limit and terminal exploratory outcome.
- "Gain at least 0 by construction" was false (Astra): removed; the
  projection also enters attack selection; negative gain reported.

Round 13, second pass (6.3 to 6.4):

- The calibrated gate still rejected exact procedures: pool variance at
  M = 2,000 (SD up to 1.46 points at n = 40), a one-run threshold, and a
  two-sided "too wide" band that could not shrink (Opus, by simulation;
  Astra's percentile fix in 6.3 addressed only part of it): one 35,000-seed
  pool per cell shared across n; analytic expected-coverage threshold
  checked over 200 pools; margins 1.5/1.5/1.75 points; no "too wide" band,
  no pool doubling; joint fixture test across all cells and endpoints at
  0.9 with remedy order M then R and a terminal exploratory outcome.
- Bank filter still said clip = 1 (Opus): truthful by behaviour.
- Interface still returned a whole State from enforce (Opus): returns
  consequences and policy memory; the ledger owns economic fields.

Round 14 (6.4 to 6.5):

- Pool-doubling statements conflicted across sections 5.3 and 8 (Astra):
  aligned; the only doubling is the joint-fixture remedy.
