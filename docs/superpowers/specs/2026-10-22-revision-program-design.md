# Revision program: design (draft 7, accepted)

Status: draft 6 was accepted by Sol high and Astra high in round 6 (`docs/revision/roster/consensus-design.md`). A second
external review (GPT Pro, 2026-10-27; triage `docs/revision/gpt-pro-review-r2-triage-2026-10-27.md`) found a duplicate
comparison and 17 further corrections before the lock (D1 to D18). Draft 7 applies them; after rounds 7 and 8, both
seats accepted it in round 9 (`docs/revision/roster/consensus-design-r9.md`).
Reviewer acceptance is development assistance, not validation of the protocol. Nothing here is registered yet. After
consensus, this document is the specification of the implementation plan (the Part A code built to draft 6 changes where
section 13 says so), and section 9 becomes the second registered protocol ("protocol v2").
Rounds 1 to 5 (both seats: reject) and the disposition of each correction: `docs/revision/roster/sol-design-r1.md`,
`astra-design-r1.md`, `sol-design-r2.md`, `astra-design-r2.md`, `sol-design-r3.md`, `astra-design-r3.md`, `sol-design-r4.md`,
`astra-design-r4.md`, `sol-design-r5.md`, `astra-design-r5.md`, and section 13 below.

Inputs: the GPT Pro review triages (`docs/paper/gpt-pro-review-triage-2026-10-22.md`, "Program";
`docs/revision/gpt-pro-review-r2-triage-2026-10-27.md`), paper draft 8
(`paper/main.tex`), the final evaluation (`docs/final-evaluation-2026-10-20/`), robustness
(`docs/robustness/2026-10-22-results.md`), theory (`docs/theory/reset-deterrence.md`), and the simulator specification
(`docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md`, "spec").

## 1. Questions

- **Q1 comparator.** Does age-based selection (R3) do better or worse than the best of four tested budget-constrained
  adaptations of credibility-based verification (Sarmenta 2001; BOINC adaptive replication), at identical allocation,
  payment, tolerance, ban length, pacing, budget, and sanctions, and at what efficiency cost? The answer is limited to the
  tested adaptations at the fixed pair; it does not establish the strongest possible credibility rule. Under R3 the
  priority window expires, but newest-first residual targeting can keep a replacement under heavy inspection (Lemma 2b);
  Q1 compares persistent age-ranked targeting with verified-history targeting, and a diagnostic (6.7) measures whether
  inspection of an honest replacement ends.
- **Q2 attribution.** At fixed parameters, what do the priority phase (P), the newest-first residual targeting (G), and
  the pacing (S) contribute to the identity-replacement gain, alone and in interaction, both under separately searched
  attacks and with the attack held fixed?
- **Q3 attack strength.** Do the results hold against a state-conditioned attack family, an independently authored
  sealed family, welfare-seeking (sabotage) attacks, and coalitions scored by total and worst-member payoff?
- **Q4 replication.** Does the first evaluation's comparative result (B3 versus R3 under D2+H3) replicate on six market
  instances sampled after the lock from a stated synthetic neighbourhood, on fresh seeds?

Non-goals: no LLM attackers; no change to the market model (spec 3); no rule outside the admissible class (spec 4.0); no
population-level claim about all markets (section 9.4).

## 2. Principles

- **Staged registration.** Everything before the fresh draw (section 7) is development. Protocol v2 fixes the code
  commit, rules, families, tuned files, manifest, decision rules, predictions, and caps, in a signed tag with a completed
  OpenTimestamps proof, before the fresh instances exist.
- **Matched comparisons first.** Q1 and Q2 compare rules at one common, preselected parameter pair (section 3.1).
  Separately tuned rules ("whole systems", section 4) are a secondary, separately labelled comparison.
- **The old record stays.** The first evaluation, its errata, and its claims are unchanged. The paper reports both.
- **Outcomes do not choose cells.** The manifest, seeds, doubling checks, cuts, and stop rules are fixed before outcomes.

## 3. Rules

### 3.1 Common core and the fixed pair

Every rule uses B3's allocation and payment (spec 4.1), refund-and-ban enforcement, no hold-back, and the allowance
A_tot = floor(B / alpha). Rules differ only in pacing (the audit count k of round t) and selection (which k served jobs).
All memory is the rule's own (first-offer round, passed audits); inputs are those of spec 4.0.

**Fixed pair: tol = 0.16, L = 10.** Preselected because the registered tuning of B3 and of R3 chose it independently
(`experiments/tuned/tuned_B3.json`, `experiments/proposed.yaml`). At this pair F000 is the registered B3 and F111 is the
registered R3.

### 3.2 Factorial (2 x 2 x 2)

| Factor | Level 0 | Level 1 |
|---|---|---|
| P, priority phase | none | served jobs of identities younger than L rounds (age from the first offer) first, newest first, then audit key, then job index |
| G, residual targeting | residual audits uniform by audit key | ceil(r/2) newest first (T1), the rest uniform |
| S, pacing | B3's spread schedule (`spread_audit_count`: stochastic rounding of allowance_left / (T - t), cap max(1, floor(2B/(T alpha)))) | R3's schedule (terminal reserve min(J L, A_tot), cumulative early quota with carry, every served job audited in terminal rounds while audits remain) |

Cell names `F<P><G><S>`. Mechanical note for interpretation: when the priority phase uses the whole quota, G has no
effect in that round; interactions and conditional effects are therefore reported (section 9.3).

**Regression oracles** (tests, not one seed): F000 equals `SecondScore`; F111 equals `Proposed("A", "T1", ., .)`; F011
equals the killed amendment-2 rule (`git show 46694cb:sim/mechanisms/proposed.py`, copied verbatim into the test tree as an
independent oracle). Each identity is checked on every (tol, L) of the common grid, at least 5 seeds, and policy profiles
that cover replacement, return after a ban, abstention, tied audit keys, rounds with no service, quota carry, budget
exhaustion, and the terminal boundary. The comparison covers the complete round records (offers, assignment, payments,
audits, consequences) and the accounting. A relabelling test permutes identity tokens and requires the same decisions.

### 3.3 Credibility comparator (an adaptation)

C is a budget-constrained adaptation, not a reproduction, of Sarmenta's credibility-based spot-checking (which also
conditions result acceptance on credibility and analyses re-entry) and BOINC's adaptive replication (reduced replication
after consecutive validated results; error-rate estimates in the 2009 description).

- **Credibility state.** p_i = passed audits of identity i since its creation or its last failed audit. Batch update
  after round t's audit results: if any audited job of i failed in round t, p_i = 0 for round t + 1 (the identity is also
  banned, and returns after the ban with p_i = 0), whatever the passes in that batch; otherwise p_i increases by the
  round's passes. A replacement identity starts at 0. Selection in round t uses the counts at the start of round t;
  audits selected in round t are not passes.
- **C-thr(K).** Identity i is unproven if p_i < K. Priority phase: served jobs of unproven identities, ascending p_i, then
  audit key, then job index. Residual: ceil(r/2) targeted picks by ascending (p_i + picks of i in this round), then audit
  key, then job index; the rest uniform by audit key.
- **C-mem(K, M).** As C-thr, but p_i counts only the passes of rounds in [max(f_i + 1, t - M), t), where f_i is the round
  of i's last failure (or its creation round minus one); an identity whose recent passes fall below K is unproven again,
  so scrutiny returns to identities that are not audited.
- **C-taper(K)**, a fixed-quota adaptation motivated by BOINC's checking probability that decreases with validated
  history. No priority phase and no split:
  each served job j of identity i has weight w_j = K / (p_i + K) (1 for a new or just-failed identity, falling as passes
  accumulate); the round's k audits are the k jobs with the smallest exponential-race keys -ln(audit_key_j) / w_j
  (weighted sampling without replacement driven by the audit key), ties by job index. The weight is relative, not the
  marginal audit probability: with a fixed quota, that probability also depends on the competing jobs, and it cannot
  approach zero as BOINC's replication probability can.
- **C-boinc**, the documented BOINC adaptive-replication rule (BOINC wiki, "Adaptive Replication": a consecutive-valid
  count per host, zeroed on an invalid result; a host below 10 is not trusted; at 10 or above it is trusted with
  probability 1 - 1/CV) adapted to a fixed quota. As C-taper, with weight w_j = 1 if p_i < 10, else 1 / p_i. p_i is
  the consecutive-pass count of the credibility state above. The weights are relative selection weights, not BOINC's
  audit probabilities, and the fixed quota does not reproduce BOINC's saving of total verification work.
- **Development selection.** Twelve configurations, C-thr with K in {2, 6, 12, 24}, C-mem with K in {2, 6} x M in
  {20, 50}, C-taper with K in {2, 6, 12}, and C-boinc, at the fixed pair and R3's pacing, scored by the common objective
  (section 4.1) with the inner search on the three tuning markets; the top 2 rechecked at the full budget (as in 4.2). The
  best is frozen as C* (variant, K, and M where it applies). C receives an additional development selection over twelve
  configurations at the fixed pair. R3 embodies earlier development choices, and the comparison does not equalise total
  historical adaptation or jointly optimise every comparator parameter; Q1 conclusions are limited to the fixed pair.
- **Pacing variants.** C* (R3's schedule) and C*/S0 (spread) at rho = 0.2; C*/S2 (R4's schedule, section 3.4) only in the
  rho = 1 repair test, where it differs from C*.

Mechanics stated before outcomes: credibility accrues only through passed audits, age through time. Under scarce audits,
unproven identities persist and the priority phase can use the whole quota (Lemma 2 overload, finite horizon). Under R3,
age does not end intensive targeting: a replacement can remain the newest identity after its fresh window (Lemma 2b).

### 3.4 Repaired R3 (R4)

R4 is R3 with reserve = min(J L, floor(A_tot / 2)). The fix comes from robustness (rho = 1: reserve = A_tot, no early
audits). **R4 differs from R3 only when J L > floor(A_tot / 2).** A_tot = floor((beta / rho) n_FB)
(`sim/calibrate.py` `cell_config`). `MarketConfig.validate()` requires positive first-best surplus, so every capacity
slot is served in the first best and n_FB = T min(J, K) = 200 min(50, K), where the total capacity K lies in [40, 80]
for the generator (k_i in {4, ..., 8}, N = 10; `sim/instances.py`). Hence at rho = 0.2, A_tot lies in [2,000, 2,500]
on the headline market and on every market the generator can produce, floor(A_tot / 2) >= 1,000 > J L = 500 at L = 10,
and R4 equals R3 and C*/S2 equals C*. At rho = 1, A_tot lies in [400, 500]; on the headline market R3's reserve is
500 = A_tot (no early audits) and R4's is 250. R4 and C*/S2 therefore appear only in the rho = 1 repair test, compared
with R3, B3, and C* (section 8.1).

**Distinct-rule check.** For every block and market of the manifest, no two rules compared in that block may have the same
selection and the same pacing schedule on that market (the reserve min(J L, A_tot) or min(J L, floor(A_tot / 2)) is
computed from the market's calibrated A_tot); the build refuses a manifest that fails, and a test covers it, including the
generator bound above at both ends of [40, 80].

### 3.5 Rule set

| Name | Role |
|---|---|
| F000 (= B3), F001, F010, F011 (= predecessor), F100, F101, F110, F111 (= R3) | factorial at the fixed pair |
| C*, C*/S0 | comparator at the fixed pair |
| R4, C*/S2 | repair test at rho = 1 only |
| B3-t, R3-t, C*-t | whole systems, tuned by section 4 |
| B2 | registered parameters, headline only, reference |

R4-t is dropped: on the common grid it differs from R3-t only at L = 50, and the repair question is answered at rho = 1.

## 4. Tuning (whole systems only)

### 4.1 Objective

J(theta) = min over the three tuning markets of min(m_D2, m_H3, m_X7), where
m_F = min((eff_F - 0.90) / 0.90, (0.30 - gain_F) / 0.30), eff_F is gross efficiency under the selected attack of family F,
and gain_F is the normalised excess profit against that rule's development reference (section 6.4). No baseline gain enters.
X7-SC is in the objective symmetrically, so X7-SC is development evidence, not held out; the sealed family (5.3) is the
held-out attack.

### 4.2 Grid and budget

- Common grid: tol in {0.08, 0.12, 0.14, 0.16} x L in {3, 10, 20, 50} (16 points; every value of both registered grids).
- Every whole system gets exactly 16 configurations. C*-t keeps C*'s variant, K, and M frozen and tunes (tol, L). The
  comparator's development selection (3.3, 12 configurations) is an extra cost that provides additional development
  selection (historical adaptation is not equalised) and is
  reported.
- Markets: the headline market and the development instances `dev0`, `dev1` (section 7.2).
- Search per configuration and family: the registered inner search (1 restart x 100 evaluations, 3 dev-train seeds; X7-SC
  200 evaluations). The top 2 configurations are rechecked at the full budget (5 restarts x 300; X7-SC x 600) on
  dev-train and scored on the 20 dev-val seeds; ties by grid order. Total episode counts per rule are written into the
  tuned file.

## 5. Attack families

### 5.1 Public constants and observations

Every family reads only the provider view (`sim/policies/base.py` `ProviderView`: own history across identities,
round, own parameters, identity token for equality) and the rule's public constants T and L (from its describe record),
injected at construction. The current exploratory code hardcodes T = 200 and W = 10; the new families do not.
Remaining global budget and other identities' targeting ranks are not observable.

### 5.2 Families

| Family | Use |
|---|---|
| D2 | registered; no replacement |
| D2+H3 | registered; searched failure-triggered reset |
| X5-AG/v2 | X5-AG with the injected constants and n_age in [0, 60] (covers L = 50) |
| X7-SC | state-conditioned (below) |
| X6-SE/v2 | entrant coalition with shared knobs and member schedules, c in {2, 5}, synchronised and staggered, injected constants |
| X8-DB | role-asymmetric coalition at c = 2: a decoy and a beneficiary (below) |
| H4 | sealed, independently authored, defence-aware (5.3) |

**X7-SC** knobs, in this coordinate order (15; `clip` last): u0 in [0, 1], m0 in [0, 1], s in [0, 0.3], d in [0, 1],
r in [0, 0.2], w in [0, 2], k_F in [0, 1], k_T in [0, 2], a_F in [0, 60], n_P in [0, 30], h_R in [0, T], a_R in [0, T],
e_P in [0, 1], lambda in [0, 1], clip in {0, 1} (binary through the family's logistic threshold at 0.5). Real thresholds
are compared without rounding.

State: the markup m (initial m0), persisting across identities as in D2+H3; the current identity's creation round c,
its own per-round served, audited, and failed counts (identity-local), and its pass count since its last failed audit
(p_own, the provider's own image of C's credibility state: 0 at creation; batch update after each round's audit results,
as C's: if any audited job of the identity failed in that round, p_own = 0, otherwise p_own increases by the round's
passes).

Round t, in this order (the harness asks for the action before it creates a replacement, and applies an exit before the
action's offer, `sim/policies/identity.py`, `sim/market.py`):

1. Markup update from round t - 1, exactly once, as `AdaptiveCheat`: after a failed audit m <- m (1 - d); else, if the
   entity was banned in t - 1, unchanged; else m <- min(m0, m + r m0).
2. Failure trigger (reset or wait): the identity that served in t - 1 had a failed audit in t - 1, T - t > h_R, and
   its age t - c < a_R. An identity with age at least a_R waits out its ban and keeps its age and its pass history; a_R = T
   resets after every failure. (Whether keeping age helps depends on the rule: under R3 a replacement can remain the
   newest identity, Lemma 2b; under C credibility is zero after a failure either way.)
3. Voluntary trigger: over rounds [max(c, t - L), t), served >= 1 and audited / served > lambda. It is not evaluated in a
   round where the failure trigger fired, nor in a round where a failure in t - 1 was rejected by the age gate, nor while
   the identity is banned, so that a "wait" decision is not overridden; it is evaluated again once the identity has
   served after the ban.
4. If a trigger fires: exit; the identity-local counters and p_own are cleared and the replacement's creation round is t.
5. Phase of the identity that will serve in round t (the replacement if one was created): terminal if T - t <= L; else
   fresh if (t - c) < a_F, or p_own < n_P, or (over rounds [max(c, t - L), t), served >= 1 and audited / served > e_P);
   else established. The last condition keeps the fresh multiplier k_F while the provider's own observed audit exposure
   is high, so the established multiplier applies only at low exposure; e_P = 1 disables it.
6. Action: k = k_F (fresh), 1 (established), k_T (terminal); effort = q_max (1 - min(1, k u0)); claim =
   min(1, max(0, effort + k m - s)), and min(claim, effort) if clip = 1; bid = (1 + w)(a + b effort).

Every input is the provider's own history or the public constants (5.1); no remaining global budget, no other identity's
rank. Embedding of D2+H3: k_F = k_T = 1, a_F = n_P = 0, e_P = 1, lambda = 1, a_R = T, h_R = 0 if x = 1 and h_R = T if
x = 0; the other knobs unchanged. Required test: identical round records to D2+H3 for both x values on every common-grid
rule, at least 5 seeds. Embedded D2+H3 attacks from the same cell's D2+H3 search are inserted as incumbents.

**X7-SC corner controls** (a bounded diagnostic, not exhaustive coverage): `scipy.stats.qmc.Sobol(d=15, scramble=True,
seed=20261028).random_base2(9)` (512 points; the scipy version is pinned by `uv.lock` and recorded); coordinate i maps to
bit 1 if its value >= 0.5, else 0; bit 0 gives the knob's lower bound and bit 1 its upper bound (for clip, the value of
the bit); points are de-duplicated by exact key in generation order; the all-low and all-high corners are appended if
absent; each corner is evaluated as is and with its truthful projection (clip = 1), as `corner_controls` does for smaller
families, de-duplicated by exact key across corners and projections. The distinct count is computed by the build,
recorded, and fixed in protocol v2 (draft 6's 769 was for 13 knobs).

**X8-DB** (decoy and beneficiary, c = 2). Members: `coalition_members(cfg, focal, 2)`; member 0 (the focal provider) is
the beneficiary, member 1 the decoy. The coalition shares its members' own histories (collusion is allowed; each member's
history is still only its own `ProviderView` history). Knobs (9; `clip` last): decoy n_D in [1, 2L] (real), u_D in
[0, 1] (decoy effort q_max (1 - u_D), claim equal to effort), w_D in [0, 2] (decoy bid multiplier); beneficiary u_B in
[0, 1], m_B in [0, 1], s_B in [0, 0.3], w_B in [0, 2] (as X7-SC's u0, m0, s, w, with k = 1 and no reset; the
beneficiary never replaces its identity), g_B in {0, 1}, clip in {0, 1} for the beneficiary's claim. The beneficiary's
markup is constant m_B.

Timing in round t (the harness asks for actions before it applies exits, `sim/market.py`): (1) the decoy decides
whether to replace: it exits if its identity failed an audit in t - 1, or if its current identity's integer age t - c_D
satisfies t - c_D >= n_D (real comparison, no rounding); after any replacement (failure or schedule) c_D = t and the
schedule clock restarts. (2) The gate is computed from the decoy identity that will make round t's offer (the
replacement if one was created in step 1): if g_B = 1, the beneficiary uses its shading action only when that identity's
age t - c_D < L, and plays honest-max otherwise; if g_B = 0, it always uses its shading action. (3) Both actions. The
result does not depend on the order in which the harness calls the members' policies. Objectives G_tot and G_min (6.3).
Required tests: the decoy's identity schedule at real n_D, including restarts after failures; the gate at the
replacement boundary; independence from the policy-call order; members read only member histories.

### 5.3 Sealed family H4 (defence-aware)

An adaptive evaluation needs an attacker author who can study the defence; independent authorship alone does not make an
attack strong. Order: H4 is written **after** comparator selection and whole-system tuning have frozen every defender
(section 11, step 4), and no defender is changed after H4 exists.

A separate Codex session (a fresh `gpt-6.1-sol` session at high effort, in its own clone at the defender-freeze commit)
receives a brief with the family interface, the allowed observations (5.1), the admissible class, the frozen rule source
(`sim/mechanisms/`, the frozen C*, the tuned files, the fixed pair), the development simulator and instances (headline,
`dev0`, `dev1`, development seeds), the existing families and their development results, and the scoring definitions
(6.1, 6.4). It must not read `sealed/` or any other clone's `sealed2/`. The running policy sees only the provider view
and the public constants; the source is for the author, not the policy.

Resource envelope (so that the cost is known): at most 15 real or binary knobs with finite bounds and a truthful
projection (`Family.project`). The evaluation of an H4 cell uses the X7-SC search budget (5 restarts x 600 on dev-train,
the same twin search, and a doubling check at the X7-SC budget where scheduled) and the X7-SC bounded control
procedure instead of `Family.corners()` (which would give up to 2^15 corners): Sobol with d equal to H4's knob count,
the same scramble seed and 2^9 points, the same bit mapping, de-duplication, appended all-low and all-high corners, and
truthful projections (5.2). The session's own development runs are on the author's machine, CPU only, no paid API, at
most 8 core-hours. It writes `sealed2/h4/family.py` and `sealed2/h4/containment.md`, runs the load check (which also
checks the envelope) and a smoke evaluation against F000, F111, and C* on the development instances, and records them
in `sealed2/h4/check.json`, together with the measured wall time and episode count of one full-budget H4 search with
its controls on the headline market, all before the commitment; the check prints the bundle hash and the timing record,
so the author reads them from that output without opening the bundle. **Cost after H4:** before the protocol is written, the
cost table (8.2) is recomputed with H4 priced from that measurement (scaled to the benchmark's pod timing); if the
evaluation cap is exceeded, the cuts of 8.2 apply in their order. The
author records the bundle hash in protocol v2 and does not read the bundle until the report. The evaluation code loads H4
from the bundle after the lock and before any evaluation-seed episode, and verifies the hash. No repair is allowed after
the lock: if H4 fails to load, it is excluded, the exclusion is reported, and the independently authored part of Q3 is
unanswered.

## 6. Objectives, references, and checks

### 6.1 Profit

Focal per-seed normalised gain g = (pi - pi_ref) / (S*/N), with S* the seed's first-best surplus; the cell's estimate is
the mean over seeds.

### 6.2 Welfare (sabotage), headline only

- W0: minimise expected gross efficiency, no constraint.
- W1: the rule's final reference (6.4) is frozen first; then minimise expected gross efficiency subject to
  E[(pi_focal - pi_ref) / (S*/N)] >= 0 on the dev-train seeds. Selection is feasibility-first: among evaluated points that
  satisfy the constraint on the training seeds, the lowest training efficiency; if none, the report says "no feasible
  candidate found" (a bounded search cannot prove infeasibility). On the evaluation seeds the constraint mean is
  re-estimated with its nominal 95 percent interval and classified: lower bound >= 0, profitability supported; upper
  bound < 0, profitability contradicted; otherwise unresolved. A W1 attack is called profitable only when supported.
- Both on the D2+H3 and X7-SC knob spaces; winners selected on training seeds. Reported per rule and objective: the
  training-selected winner (the lower training efficiency of the two families) evaluated unchanged on the evaluation
  seeds, its interval, and the attacker's gain; the other family's result is reported beside it. No extremum is selected
  on evaluation data.

### 6.3 Coalition, headline only

Members are `sim/policies/exploratory.py::coalition_members(cfg, focal, c)`: the focal provider, then the providers
nearest to it in the positions score order, ties to the lower index; member j of that ordered list (j = 0 is the focal
provider) gets schedule index j. Members play shared knobs with member schedules (X6-SE/v2) or the decoy and beneficiary
roles (X8-DB, c = 2); non-members play honest-max. Member gain
g_j = (pi_j - pi_j^0) / (S*/N), where pi_j^0 is member j's profit under the frozen joint truthful reference of that
coalition (one per rule, market, and c). Objectives: total G_tot = sum_j E[g_j] and worst member G_min = min_j E[g_j]
(not E[min_j g_j]).

Because G_tot's reference term is a constant, the G_tot searches do not need the reference; G_min's do. Truthful
projection of a coalition profile (spec 5.2, `Family.project`): every member's claim is clipped to its effort
(clip = 1 for X6-SE/v2 members; for X8-DB the beneficiary's clip = 1 and every decoy knob, including u_D, n_D, and w_D,
unchanged, since the decoy's claim already equals its effort). Order per rule and c, all on dev-train seeds:

1. The joint twins: the registered search (5 restarts x 300) over the X6-SE/v2 knobs with clip = 1 forced for every
   member, maximising sum_j (pi_j / (S*/N)), once with the synchronised and once with the staggered schedule.
2. The G_tot searches (X6-SE/v2 synchronised and staggered; X8-DB at c = 2).
3. Preliminary reference: the candidate with the highest training mean of sum_j (pi_j / (S*/N)) among, in this tie
   order: all members honest-max, all members abstain, the synchronised twin, the staggered twin, then the truthful
   projections of the step-2 winners and of every point in their archives, in search order.
4. The G_min searches against the preliminary reference, with the reference profile inserted as an incumbent where the
   family can represent it.
5. Final reference: the same rule over the step-3 menu plus the truthful projections of the step-4 winners and archive
   points, in search order; freeze.
6. Every archived G_min point (step 4) is rescored against the final reference on the same training seeds; the final
   reference profile itself is added as a candidate wherever the G_min family can represent it (it scores exactly zero
   against itself); the G_min winner is the best of these candidates. G_tot winners are unchanged (constant reference
   term). Then evaluation. Required regression test: a final reference taken from a step-5 projection, with every
   archived point negative against it, selects the reference profile where it is representable.

Claims are gains relative to this coordinated truthful profile; they say nothing about coalition stability or each
member's best unilateral alternative.

### 6.4 References and freeze order

- **Menu.** A rule's truthful reference is selected on training seeds by the registered order (spec 5.2) from one menu:
  abstain, honest-max, and the twin, projection, and archive candidates of its D2+H3 and X7-SC searches. Every rule in the
  evaluation, including B2 and the rho = 1 repair cells, has exactly these two searches at the same budget (8.1), so
  matched pairs have equivalent menus. **Exception:** the secondary whole systems (B3-t, R3-t, C*-t) on fresh markets
  have no X7-SC cell (8.1); their fresh-market reference menu is abstain, honest-max, and the D2+H3 candidates, the same
  reduced menu for all three systems, and their fresh-market results are labelled accordingly. Its D2, X5-AG/v2, H4, and welfare gains use the same frozen reference; no other
  family adds candidates. Coalitions use their own joint reference (6.3).
- **Development reference** (tuning, comparator selection): the same construction with the tuning objective's families
  (D2, D2+H3, X7-SC) on the tuning markets. H4 is never available in development.
- **Dependency and freeze order per market.** (1) Profit attack and twin searches and banks; (2) reference selection and
  freeze; (3) the searches that need a frozen reference (W1) and the coalition steps 1 to 6 of 6.3 in their order; (4) envelope
  family choices (9.3 Q3), the fixed-attack bank and its training-seed matrix (6.6); (5) final freeze. Only then may any
  evaluation-seed episode of that market run; the evaluation stage refuses to run otherwise. Doubling results never enter
  the frozen candidates (6.5 says how they are used).

### 6.5 Search-quality checks

A doubling check continues the registered search with as many additional restarts as the registered budget (new restart
seeds), so the total budget doubles; it is reported as a diagnostic. Scheduled checks (fixed in the manifest):

- headline: the 10 matched rules (F000 to F111, C*, C*/S0) x {D2+H3, X7-SC} (20), the 12 welfare cells, and the 30
  coalition cells (24 X6-SE/v2, 6 X8-DB);
- fresh markets: the Q1 and Q4 rules (F000, F111, C*) x {D2+H3, X7-SC} x 6 (36).

98 checks. Units and threshold 0.005: gain (normalised by S*/N) for profit; G_tot and G_min (each normalised) for
coalitions; gross efficiency (a share of the first best) for welfare. Attack-profit and reference-profit changes are
reported separately. A W1 check that finds a feasible point where the original found none, or a feasible point with
efficiency lower by at least 0.005, labels the cell incomplete. Cells without a scheduled check (factorial cells on fresh
markets, whole systems, X5, H4, D2 extras) carry no search-quality claim.

**Two statuses.** A cell is **missing** if it did not run to completion or is invalid: not run (cap stop or cut), a
refused sample, a nonfinite statistic (9.2), a search with no finite candidate, or a failed load (H4). A cell is
**search-flagged** if it ran to completion but its scheduled doubling check exceeded the threshold above ("incomplete" in
the check's own wording). Consequences: a missing cell removes every confirmatory decision that uses it (the test is
reported "not decided: missing cell") and makes that part of its question unanswered (8.1a). A search-flagged cell keeps
its estimate as the estimate of the prescribed (frozen) search procedure; a confirmatory decision that uses it is still
made and is reported as a decision about the prescribed search procedure only; the robustness statement for that rule
and family (Q3) is reported unanswered ("search flagged"), never as "no attack found". **Held-out diagnostic:** for every scheduled check, the doubled search's winner (selected on its training
seeds) is evaluated unchanged on the cell's evaluation seeds against the same frozen reference, and reported beside the
cell; it never replaces or adds to the frozen estimate.

### 6.6 Fixed-attack cross-evaluation (Q2)

For each market and family in {D2+H3, X7-SC}: the bank is the 8 selected attacks of the 8 factorial cells (frozen with
the references). Each attack is evaluated against all 8 factorial rules on the evaluation seeds, each against its own
frozen reference: an 8 x 8 gain matrix. For every fixed-attack contrast the report gives the gain contrast and its two
terms separately, since g_R(a) - g_C(a) = [pi_R(a) - pi_C(a)] / (S*/N) - [pi_R(r_R) - pi_C(r_C)] / (S*/N): the change in
attacker profit and the change in the truthful reference payoff; beside them, gross and net efficiency. Fixed-attack
contrasts use the same effect coding as 9.3 within each attack's row, then the equal-weight mean over the 8 rows (an
average over this bank, not over attacks in general). **Bank envelope:** the same 8 x 8 matrix is also evaluated on the
dev-train seeds of the registered search (part of step 4 of the freeze order); for each rule the attack with the highest
training gain is selected there and its evaluation-seed gain is reported with its nominal interval. No extremum is
selected on evaluation data.

### 6.7 Honest-replacement diagnostic (descriptive)

Whether inspection of a replacement ends: on the headline market, the focal provider plays honest-max, replaces its
identity once at round 50, and plays honest-max after; every other provider plays honest-max. Rules F000, F111, and C*;
the 200 evaluation seeds; no search. Reported per identity age (rounds since the replacement's creation, in bins of 10):
the share of the focal provider's served jobs that are audited, its profit per round, and its refunds from false
failures. Three fixed-policy cells; the cost is evaluation episodes only.

## 7. Market instances and randomness

### 7.1 Generator (a synthetic neighbourhood of the headline market)

`instance(stream) -> MarketConfig` with fixed N = 10, J = 50, T = 200, sigma = 0.05, eta = 0, beta = 0.05, rho = 0.2,
v_min = 0.6, and per draw: q_max = 10 sorted draws from Uniform[0.55, 1.0]; b_lo ~ U[0.18, 0.26], b_hi ~ U[0.34, 0.46],
b_i = b_hi - (b_hi - b_lo) * rank_i / 9 + U[-0.02, 0.02] (rank by q_max, ascending; the negative quality-cost association
of the headline market); a_i ~ U[0, 0.05]; k_i uniform in {4, ..., 8}; v_max ~ U[1.2, 1.6]. Draws repeat inside the same
stream until `MarketConfig.validate()` passes (at most 10,000; the count is recorded). Calibration per instance with the
frozen calibrate on seeds 4000 to 4019. The claim population is this neighbourhood: fixed scale, noise, budget ratio,
audit cost, and cost-quality association.

### 7.2 Streams

- Digest: d(root, domain, n) = SHA-256 of the ASCII bytes of root + "|touchstone-v2|" + domain + "|" + decimal(n).
- Instance stream i: `numpy.random.Generator(numpy.random.PCG64(int.from_bytes(d(root, "instance", i)[:16], "big")))`.
- Development root: the string "dev-20261022"; `dev0`, `dev1` = instance streams 0 and 1. Public now.
- Fresh root: the block hash at height H (7.3) as 64 lowercase hex characters in the usual big-endian display order;
  fresh instances = streams 0 to 5, labelled `fresh0` to `fresh5`. If a stream hits the 10,000-draw limit, it is replaced
  by the next stream index (6, 7, ...), in order, keeping the labels in order.
- Evaluation seeds for market label m in {`headline`, `fresh0`, ..., `fresh5`}: v_n = 30,000,000 +
  int.from_bytes(d(root, "seeds/" + m, n)[:8], "big") mod 10,000,000 for n = 0, 1, ...; duplicates skipped; the first 200.
  The range [30,000,000, 40,000,000) is disjoint from every reserved range (`sim/amendment.py`, the amendment-1 block
  ending at 9,000,000, the final-evaluation range) and from the new coverage range (9.5), checked by a test.
- Identity salt: d(root, "salt", 0) in hex. It is public after the draw; rules never receive the salt or entity ids
  (spec 4.0), which a test enforces.

### 7.3 Block height and finality

- **Anchor.** The protocol file is stamped with OpenTimestamps and the proof is upgraded until it holds a Bitcoin
  attestation. A = the lowest Bitcoin block height attested in the upgraded proof, as reported by `ots verify`. H = A + 144.
  The rule, not the number, is in the protocol file; H follows deterministically.
- **Publication.** One authoritative protocol: the signed tag, the protocol file, and the upgraded proof are pushed to
  the public repository before block H is mined. If that deadline fails, the original draw is kept and reported, but its
  results are labelled nonconfirmatory; any replacement registration must be public before its own target block.
- **Reading.** The hash at H is read once both explorers (blockstream.info and mempool.space) report a tip height of at
  least H + 6 and give the same hash at H. If they disagree, the reader waits one hour and reads again, until they agree at
  a tip of at least H + 6; the first agreeing read is final. The reader also downloads the headers from A to H + 6 and
  checks every hash link and proof of work from A's header, whose Merkle root carries the protocol commitment. Trust
  assumption stated in the paper: the chain both explorers serve at the final read is the accepted chain; a later
  reorganisation deeper than 6 blocks is not handled, and would be reported. A second assumption: no miner chooses the
  block at H to influence this evaluation.
- **Confirmation draw.** If a substantive fix is needed after outcomes (9.6), the fixed code and an amendment are locked
  and stamped the same way, giving anchor A2; the fixed code is evaluated on fresh markets and seeds from the block at
  H2 = A2 + 144, and both results are reported.

## 8. Manifest and compute

### 8.1 Cells (focal provider at the median position; markets: headline + 6 fresh = 7)

| Block | Rules | Families | Markets | Cells |
|---|---|---|---|---|
| Matched factorial and comparator | F000..F111, C*, C*/S0 (10) | D2+H3, X7-SC | 7 | 140 |
| Matched core extras | F000, F111, C* | D2, X5-AG/v2, H4 | 7 | 63 |
| Whole systems | B3-t, R3-t, C*-t | D2+H3 (7 markets), X7-SC (headline) | 7 / 1 | 24 |
| Reference | B2 | D2, D2+H3, X7-SC | headline | 3 |
| Welfare | F000, F111, C* | W0, W1 x {D2+H3, X7-SC} | headline | 12 |
| Coalition | F000, F111, C* | X6-SE/v2: c {2, 5} x {sync, staggered} x {total, min}; X8-DB: c = 2 x {total, min} | headline | 30 |
| Repair test | F000, F111, R4, C*, C*/S2 | D2, D2+H3, X7-SC | headline at rho = 1 | 15 |
| Diagnostic (6.7) | F000, F111, C* | honest replacement, fixed | headline | 3 (no search) |

287 search cells (85 on the X7-SC knob space, 21 H4 cells priced as X7-SC), 3 fixed-policy cells, 14 fixed-attack
cross-evaluations (6.6), 98 doubling checks (6.5). Every cell is evaluated on 200 seeds. Draft 6's R4 and C*/S2 cells at
rho = 0.2 (61 cells) duplicated R3 and C* (3.4) and are removed; the whole-system X7-SC cells on fresh markets and R4-t
are removed to fund X8-DB and the diagnostics.

### 8.1a Questions and their cells

Statuses as in 6.5: a missing required cell makes that part unanswered (and removes the confirmatory decisions that use
it); a search-flagged cell keeps confirmatory decisions (labelled as about the prescribed search procedure) and makes the
Q3 robustness statement for that rule and family unanswered. Scheduled doubling checks (6.5) are listed with their
question.

| Question | Required cells, and scheduled checks |
|---|---|
| Q1 (confirmatory) | F111 and C* x {D2+H3, X7-SC} x 6 fresh markets, with their references; checks: those 24 cells; descriptive: headline, C*/S0 |
| Q2 (descriptive) | the 8 factorial cells x {D2+H3, X7-SC} x 7 markets and the 14 cross-evaluations; checks: the headline factorial cells (16) |
| Q3 (descriptive) | per core rule (F000, F111, C*): D2+H3, X7-SC, X5-AG/v2, H4 on 7 markets; welfare; coalitions; the diagnostic. If H4 is cut on fresh markets (8.2) or fails to load, the independently authored part of Q3 is reported as not run on those markets, never as "no attack found"; checks: every core-rule profit, welfare, and coalition check of 6.5 |
| Q4 (confirmatory) | F000 and F111 x D2+H3 x 6 fresh markets, with their references; checks: those 12 cells |
| Repair | the rho = 1 block |
| Whole systems (secondary) | B3-t, R3-t, C*-t cells |

### 8.2 Cost

Unit: one headline D2+H3 cell (search, bank, reference, 40-seed evaluation) at the registered budget, about 25
core-minutes, about 18,000 episodes, and about 0.045 USD on pods (robustness: 322 cell-equivalents, 14 USD). X7-SC
multiplier 2.5 (double evaluations, about 770 corner-control vectors; the build records the exact count for 15 knobs); a doubling check 1 unit (X7-SC 2.5); inner tuning
searches 0.04 (X7-SC 0.1). The additional cost of increasing the evaluation from 40 to 200 seeds (the unit already
includes 40) is priced conservatively at 16 percent of a cell; episode-based estimates are lower and the benchmark
decides.

| Item | Units |
|---|---|
| Comparator selection: 108 inner (6.5) + top 2 rechecked x 3 families x 3 markets (27) | 33.5 |
| Whole-system tuning: 432 inner (25.9) + 3 systems x 2 rechecks x 3 families x 3 markets (81) | 106.9 |
| Coverage (9.5): 8 profiles x 20,000 seeds x 3 markets = 480,000 episodes (26.9) + bootstrap computation (about 3 core-hours, 10) | 36.9 |
| **Development total** | **about 177.3 (about 8.0 USD)** |
| Evaluation cells: 287 + (85 X7-SC + 21 H4) x 1.5 | 446 |
| Coalition extras (6.3): the second joint twin per rule and c (6); step-3 and step-5 truthful-projection evaluations of archive points (new episodes, since clipping can change trajectories; about 8, benchmarked); step-6 G_min archive rescoring (stored member payoffs where possible, about 4) | 18 |
| Additional cost of 200 instead of 40 evaluation seeds: 0.16 x 446 | 71.4 |
| Fixed-attack cross-evaluation: 14 x 56 attack profiles x 200 seeds = 156,800 episodes (9), plus the training-seed matrix for the bank envelope (1) | 10 |
| Doubling checks: 64 at 1 + 34 X7-SC at 2.5, plus the held-out evaluation of each doubled winner (about 2) | 151 |
| Diagnostic (6.7): 3 x 200 episodes | about 0 |
| **Evaluation total** | **about 696 (about 31.3 USD)** |

Total about 874 units, about 39.3 USD (draft 6: about 1,103 units, 50 USD). **The author's approval is required for any
total above 40 USD** (the range quoted when the program was chosen); the caps below do not by themselves authorise
spending their sum. The table is an estimate; the benchmark decides.

Caps and stop rules:

- **Benchmark first.** Before any paid tuning, one cell of each kind and one coverage fixture run on a pod, and the table
  is recomputed.
- **Development cap 12 USD.** If the recomputed development cost exceeds it: (1) the comparator selection and tuning use
  the headline market and `dev0` only, and the coverage fixtures use the replacement design of 9.5; (2) the coverage pools
  shrink to 10,000 seeds per market. If it still exceeds the cap, work stops and the author decides.
- **Evaluation cap 40 USD.** If the recomputed evaluation cost exceeds it, cuts apply in this order before the lock: (1)
  whole-system cells on fresh markets (keep headline); (2) H4 on fresh markets (Q3's independently authored part is then
  headline only, stated in the protocol, 8.1a); (3) D2 matched extras on fresh markets; (4) C*/S0 cells on fresh markets.
  If it still exceeds the cap, work stops before the lock and the author decides.
- **Execution priority.** Q4 and Q1 cells first, then Q2, then Q3, then the rest. If a cap is hit during a run, the
  remaining cells are reported incomplete, no cell is replaced, and a question whose required cells are incomplete is
  reported unanswered.

## 9. Protocol v2: estimands and decision rules

### 9.1 Estimands

For a cell: the expected gain of the frozen attack (selected on dev-train) against the frozen reference, over the seed
distribution of that market, conditional on the frozen searches. Contrasts between rules use per-seed differences on
common seeds (the same seeds, salt, and job values for every rule in a market).

### 9.2 Intervals and tests

- **Bootstrap.** Studentized (percentile-t) bootstrap over seeds, 9,999 resamples, resample seed fixed in the protocol;
  `sim/intervals.py` extended to arbitrary tail levels. Before calibration, the smallest confirmatory tail (0.05/6, Q4)
  contains about 83 of the 9,999 resamples; with kappa = 1/4 it contains about 21. This is a precision limit; validation
  (9.5) tests the calibrated procedure itself.
- **p-values.** For a one-sided hypothesis about a mean, the bootstrap p-value is the smallest tail level at which the
  studentized one-sided bound crosses the null value; two-sided p = 2 min(one-sided p's).
- **Calibrated p-values.** Each confirmatory family F has one multiplier kappa_F in {1, 1/2, 1/4}, frozen by 9.5 before
  the lock. The calibrated p-value is p' = min(1, p / kappa_F) (one-sided), and for a two-sided test
  p' = min(1, 2 min(p_lower, p_upper) / kappa_F). The map is the same for every test of the family, so Holm's ordering
  and nesting are preserved.
- **Decisions** use Holm's step-down procedure on the calibrated p-values within each confirmatory family. **Reported
  intervals** for confirmatory families are Bonferroni simultaneous intervals at the calibrated nominal level (tail
  kappa_F times the Bonferroni tail); they are a separate procedure and can contain the null despite a Holm rejection.
  Descriptive intervals are nominal 95 percent, labelled unadjusted.
- **Pooled mean over the six fresh markets.** The equal-weight mean of the market means; stratified bootstrap (seeds
  resampled independently within each market, since seed streams are independent across markets), studentized by the
  stratified standard error; conditional on the six markets.
- **G_min** (descriptive). Bounds as the minimum over members of the members' bounds at level 0.05 / c.
- **Numerical rules (as implemented in `sim/intervals.py`, frozen with the code).** A sample with a nonfinite per-seed
  value is refused and its cell is missing (6.5). A nonfinite standard error, bootstrap statistic, bound, or p-value is
  refused in the same way: the affected decision is withheld ("not decided") and the cell is missing. A constant sample (all values exactly equal) has standard error
  0: its bounds equal its mean, and its one-sided p-value is 0 if the mean is strictly beyond the null and 1 otherwise. A
  resample with zero standard error is studentized by the full-sample standard error. p-values have resolution
  1 / (B + 1) with B = 9,999: p = (count + 1) / (B + 1), where count is the number of resampled statistics at least as
  extreme (ties count as extreme), and p = 1 if every resample is at least as extreme. Quantiles use numpy's default
  (linear) interpolation. A search that returns no finite candidate leaves its cell incomplete.

### 9.3 Decision rules

- **Q1, confirmatory on the pooled fresh markets.** Family of 2 tests: F111 vs C*, families D2+H3 and X7-SC, each on
  the pooled mean d = g_C* - g_F111 of the per-seed differences over the six fresh markets. Statistical direction and
  practical size are reported separately. Holm on the calibrated two-sided p-values for H0: d = 0 (one-sided tails
  0.05/4, 0.05/2) decides the direction; the calibrated Bonferroni interval I (two-sided 0.05/2 times kappa_Q1) decides
  the size against the margin 0.05. Exclusive categories, in order:
  1. **materially lower**: I lies entirely above 0.05 ("R3 materially lower gain") or entirely below -0.05 ("C*
     materially lower gain");
  2. **equivalent**: I lies inside [-0.05, 0.05] (a conservative two one-sided tests procedure); if Holm also rejects
     zero, the label is "equivalent, direction R3 (or C*) lower";
  3. **ordered, size not established**: Holm rejects zero, and neither category 1 nor category 2 applies;
  4. **inconclusive**.
  The margin 0.05 is half the registered comparative margin 0.10 and below the headline B3 - R3 difference (0.28).
  **Efficiency condition.** The word "better" for a rule needs category 1 in its favour and, for the same family, the
  pooled paired gross-efficiency difference (that rule minus the other) with a nominal one-sided 97.5 percent lower bound
  of at least -0.01 (descriptive, not calibrated). Any combined "better" statement says that its efficiency part is
  descriptive evidence without a calibrated joint error guarantee. If the lower bound is below -0.01, the result is
  reported by its gain category with "efficiency non-inferiority unresolved"; only if the nominal one-sided 97.5 percent
  upper bound is below -0.01 is it reported as "lower gain with an efficiency loss" (descriptive). Beside every Q1 result: paired gross and net efficiency, the truthful
  reference profit, audit spending, refunds from false failures of the focal and the other providers, and the served
  share. Per-market and headline Q1 results are descriptive (the headline market was used in development).
- **Q2, descriptive.** Per market and family, effect coding over the 8 cells: main effect of P = mean of the 4 cells with
  P = 1 minus the mean of the 4 with P = 0 (likewise G, S); two-way interaction PG = (mean of cells with P = G) minus
  (mean with P != G), likewise PS, GS; three-way PGS = (mean of cells with an odd number of 1s) minus (mean with an even
  number); conditional effects G at P = 0 and P = 1, P at S = 0 and S = 1, P at G = 0 and G = 1, and G at S = 0 and
  S = 1. Both versions: separately searched attacks (diagonal) and fixed attacks (6.6, with the attacker-profit and
  reference terms and efficiency beside each contrast). Pooled over the 6 fresh markets as in 9.2. Nominal 95 percent
  intervals, no decisions. Every factorial cell uses the fixed pair; no factorial cell is tuned separately.
- **Q3, descriptive.** Per core rule (F000, F111, C*), the attack envelope: the family among {D2+H3, X7-SC, X5-AG/v2,
  H4} with the highest training gain, evaluated unchanged; the training-selected lowest efficiency under W0 and W1 (6.2)
  with the W1 classification; coalition G_tot and G_min for X6-SE/v2 and X8-DB; the diagnostic (6.7). An incomplete
  scheduled check makes that rule's statement for that family unanswered (6.5).
- **Q4, confirmatory on sampled markets.** Per fresh market, an intersection-union test: (a) H0: g_F000 - g_F111 <= 0.10
  under D2+H3 and (b) H0: F111's gross efficiency <= 0.90, each one-sided; the market's p-value is the larger of the two
  calibrated component p-values. A market passes if Holm across the 6 market p-values rejects it (one-sided tails 0.05/6 down to
  0.05/1). Reported: k of 6 markets passing, and the markets. Wording: "replicated on k of 6 sampled markets"; failing
  markets are named; "generalisation not established" when a market is not decided. No population claim.

### 9.4 Claim scope

All claims are conditional on the six sampled markets, the stated neighbourhood, the fixed pair (Q1, Q2, Q4), the searched
families, and the frozen searches. Q4 replicates the B3 - R3 comparison under D2+H3 and R3's efficiency condition, not the
complete amended PASS predicate of the first evaluation. Multiplicity is controlled within Q1 and within Q4 separately;
there is no paper-wide 5 percent familywise guarantee across all confirmatory statements, and the paper does not claim
one. "Confirmatory" means specified before the fresh draw; it does not mean exact nominal error control on the fresh,
selected-policy distributions (9.5). Q4 is an internal replication on fresh instances, not an independent-team
replication.

### 9.5 Coverage check and calibration (before the lock)

- **Fixtures.** On the headline market, `dev0`, and `dev1`, frozen development attacks (the inner searches at the fixed
  pair from tuning and comparator selection) and development references (6.4) are run on pools of 20,000 seeds per market
  in the new range [40,000,000, 60,000,000). Profiles per seed (8): F000's D2+H3 attack (its X7-SC attack is not needed
  for any confirmatory statistic and is omitted), the D2+H3 and X7-SC attacks of F111 and C*, and the three rules'
  references (one reference profile per rule; the two references of a rule's families are the same frozen reference, 6.4,
  so a family-specific reference profile is not needed). Every profile of a seed uses that seed's common random numbers,
  so per-seed differences keep their dependence.
- **Q1 fixture (pooled).** Six strata: each of the three markets split into two disjoint pools of 10,000. A replication
  draws 200 seeds with replacement from each stratum, independently across strata and replications, and computes the
  pooled statistic and its bounds; the truth is the equal-weight mean of the six stratum pool means.
- **Q4 fixtures (per market).** A replication draws 200 seeds with replacement from the market's 20,000-seed pool; the
  truth is the pool mean. The multiplier must pass on all three market fixtures and is then applied to the six fresh
  markets (a stated transfer assumption).
- **Endpoints.** Q1: both sides of the two pooled differences at the Holm tails 0.05/4 and 0.05/2 (8 endpoints; the
  Bonferroni interval of 9.3 uses tail 0.05/4, which is among them). Q4: the one-sided lower bounds of the gain difference
  and of the efficiency at tails 0.05/6, 0.05/5, ..., 0.05/1 on each of the three markets (36 endpoints). For an endpoint
  with allocated tail alpha_e, a candidate kappa uses the bound at nominal tail kappa alpha_e.
- **Selection.** On 10,000 selection replications per fixture, kappa_F is the largest of 1, 1/2, 1/4 for which every
  endpoint of family F, on every fixture, has a Clopper-Pearson upper bound of its miss rate, at confidence
  1 - 0.01 / m_F, at most alpha_e (the validation criterion applied to the selection replications), so that a candidate
  with near-nominal size is not selected only to fail validation.
- **Validation.** On 20,000 independent validation replications per fixture (new resampling seeds), the selected kappa_F
  is admitted if, for every endpoint of the family, the Clopper-Pearson upper bound of the miss rate at confidence
  1 - 0.01 / m_F is at most alpha_e (m_F = 8 for Q1, 36 for Q4; Bonferroni over the family's endpoints, so the
  guarantee holds jointly with Monte Carlo confidence at least 99 percent). Only the selected procedure is validated, so
  the selection does not affect this guarantee. There is no fallback to another candidate after a failed validation.
- **Failure.** If no candidate passes selection, or the selected one fails validation, the family receives no
  confirmatory decision (estimates and descriptive intervals are still reported).
- **Fixture branches (registered for every development-cut case of 8.2).** Seeds of a market's coverage pool are taken
  in the order of their derivation index; stratum s of a market takes the s-th consecutive block of floor(M / k) seeds,
  where M is the market's pool size and k the number of strata per market; the remainder is discarded for Q1 only. Q1
  always has six equal-weight strata, sampled with replacement:
  - three markets, M = 20,000: k = 2 strata of 10,000 per market (the default);
  - two markets (headline, `dev0`), M = 20,000: k = 3 strata of 6,666 per market;
  - two markets (headline, `dev0`), M = 10,000: k = 3 strata of 3,333 per market (8 profiles x 10,000 x 2 = 160,000
    profile episodes, about 9 units, plus bootstrap work).
  Q4 uses each retained market's full pool; with two markets its validation keeps the denominator m_Q4 = 36, which is
  conservative.
- **Guarantee and limits.** Admission is conditional on the empirical fixture distributions. It does not establish
  nominal coverage on the fresh, selected-rule distributions, nor for the Q2 and Q3 statistics; the report says so.

### 9.6 After the lock

No change to rules, families, seeds, manifest, cuts, or decision rules. Orchestration changes are logged. A substantive
fix after outcomes: a documented amendment, pre-fix and post-fix results both reported, and the fixed code re-evaluated on
the confirmation draw (7.3).

### 9.7 Predictions (completed before the lock)

Draft directions: Q1 equivalent or C lower under D2+H3 and X7-SC at the headline, with C lower where K exceeds the audits
an identity receives; Q2: S and G carry most of the reduction, P small at the fixed pair, and fixed-attack contrasts
smaller than searched ones; Q3: X7-SC raises R3's gain above D2+H3 by less than 0.05; coalition G_min well below G_tot; the
honest replacement under F111 keeps a high audit share past age L (Lemma 2b), and under C* the share falls as passes
accrue; R4 removes the rho = 1 collapse; Q4: k >= 5. Final predictions, including X8-DB and H4, are written from
development results before the lock.

## 10. Artifact

A public release at the report commit: code, tuned files, all records (including incomplete, failed, and cut cells, and
both evaluations), the generator, the block headers, a one-command reproduction of every table (`scripts/reproduce.py`),
and the paper sources. These release contents are stated in protocol v2 before the lock. The author publishes it (GitHub
release, Zenodo DOI); the plan prepares and checks the bundle.

## 11. Order of work

1. Build, test first, on development seeds: rules (3), families and objectives (5, 6), references and freeze order (6.4),
   cross-evaluation (6.6), the diagnostic (6.7), generator, streams, and block reader (7), interval extensions (9.2),
   manifest with the distinct-rule check (3.4), benchmark.
2. Benchmark on a pod; recompute the cost; the author approves the total if it exceeds 40 USD.
3. Comparator selection (3.3); whole-system tuning (4) on pods. Every defender is now frozen (defender-freeze commit).
4. H4: the sealed session, at the defender-freeze commit with the frozen defender source (5.3), writes, checks, and
   commits the family; the author records the hash and the timing record without reading the family. No defender changes
   after this step. The cost table is recomputed with the measured H4 timing (5.3).
5. Coverage check (9.5).
6. Protocol v2 with predictions; Sol and Astra review; lock (signed tag, OpenTimestamps proof upgraded, pushed).
7. Block H; draw; calibrate; load and verify H4.
8. Evaluation on pods; report; review.
9. Artifact; paper revision; review.

## 12. Remaining questions for the reviewers

1. Is the reduced confirmatory scope (Q1 pooled, Q4 per market; Q2 and Q3 descriptive) acceptable for the paper's claims?
2. Is the calibration (one multiplier per family, selected and then validated on independent replications with
   Bonferroni-adjusted Clopper-Pearson bounds at the allocated tails, the same criterion at selection) acceptable?
3. Draft 7: is dropping R4-t (it differs from R3-t only at L = 50) and keeping R4 and C*/S2 only at rho = 1 right?
4. Draft 7: are the X7-SC reset-or-wait and exposure conditions (a_R, e_P, p_own) and the X8-DB decoy family enough to
   represent the two attacks a skeptical referee would try first (5.2)?
5. Draft 7: are the Q1 categories and the efficiency condition (9.3) well defined, and is a descriptive efficiency bound
   acceptable beside a calibrated gain decision?

## 13. Disposition of rounds 1 to 5

| Correction | Status | Where |
|---|---|---|
| Rounds 1 and 2: matched parameters and pacing, regression suites, tuning grid, neighbourhood, common references, sampled-market scope, credibility updates, X7-SC transition order and embedding, Sobol construction, fixed-attack comparisons, scheduled checks, seed encoding, H4 order, finality (except publication) | resolved (both seats, round 3) | 3 to 7 |
| Round 3, Sol 2 / Astra 2: reference searches missing for B2 and the rho = 1 cells; dependency order | X7-SC searches added for both blocks; five-step dependency and freeze order | 6.4, 8.1 |
| Round 3, Sol 3: coalition membership and schedules | `coalition_members` and schedule index j | 6.3 |
| Round 3, Sol 4 / Astra 3: Holm versus Bonferroni | decisions by Holm only; Bonferroni intervals labelled as a separate procedure; Q4 by Holm on the market p-values | 9.2, 9.3 |
| Round 3, Sol 5 / Astra 4: coverage tolerance | endpoint-specific admission with a Monte Carlo bound; calibrated-tail remedy; confirmatory scope reduced to 4 + 6 tests | 9.3, 9.5 |
| Round 3, Sol 6 / Astra 5: coverage fixtures | pool-resampling fixtures with common random numbers, six pooled strata, all Holm-step endpoints; Q2 and Q3 descriptive | 9.5 |
| Round 3, Sol 7: late publication | nonconfirmatory if not public before H | 7.3 |
| Round 3, Sol 8 / Astra 6: cost scaling, cross-evaluation, corner count | 16 percent seed cost, cross-evaluation episodes, 769 corner vectors, coverage workload; caps and approval | 5.2, 8.2 |
| Round 3 answers: C-taper is a fixed-quota adaptation; weights are relative | stated | 3.3 |
| Round 4 (both seats): round-3 corrections on references, dependency order, coalition membership, publication, Holm versus Bonferroni | resolved (both seats, round 4) | 6.3, 6.4, 7.3, 9.2 |
| Round 4, Sol 2 / Astra 2: admission at 1.5 alpha_e | admission at alpha_e | 9.5 |
| Round 4, Sol 3-4 / Astra 3: calibration selection and mapping | one multiplier per family; calibrated p-values before Holm; Q4 maximum of calibrated components; selection then independent validation with Bonferroni Clopper-Pearson bounds; transfer from three fixtures stated | 9.2, 9.3, 9.5 |
| Round 4, Sol 5: C*/S2 D2 development search | added (9 searches) | 8.2 |
| Round 4, Sol 6 / Astra 5: profile count; seed-cost wording | 14 profiles with F000's X7-SC attack omitted; "additional cost of 200 instead of 40 seeds" | 8.2, 9.5 |
| Round 4, Astra 4: fixtures under the development cut; sampling with replacement | replacement design; with replacement, independent | 8.2, 9.5 |
| Round 4, Astra answer 1: Q4 is not the complete amended PASS predicate | stated | 9.4 |
| Round 5 (both seats): all round-4 corrections except the second development-cut fixture | resolved (both seats, round 5) | 8.2, 9.2, 9.3, 9.5 |
| Round 5, Sol 2 / Astra 2: fixture after both development cuts | three registered branches with a deterministic partition | 9.5 |
| Round 5, Sol 3 / Astra 3: bootstrap tail count | 62 before calibration, about 16 at kappa = 1/4 | 9.2 |
| Round 5, Astra 4: estimates versus measured costs | the table is an estimate; the benchmark decides (unchanged) | 8.2 |
| Round 6: draft 6 accepted by both seats | accepted (consensus) | `docs/revision/roster/consensus-design.md` |

## 14. Draft 7: disposition of the second external review (GPT Pro, 2026-10-27)

Triage with the checks: `docs/revision/gpt-pro-review-r2-triage-2026-10-27.md`. Part A code built to draft 6 changes where
the last column says "code".

| Finding | Draft 7 | Where | Code |
|---|---|---|---|
| D1 R4 = R3 and C*/S2 = C* at rho = 0.2 (A_tot in [2,000, 2,500] on the whole generator support) | removed from rho = 0.2 blocks; R4, C*/S2 only at rho = 1; R4-t dropped; Q1 2 tests; distinct-rule check | 3.3, 3.4, 3.5, 8.1, 9.3, 9.5 | manifest and distinct-rule check, tuned-rule lists and tuning orchestration (`promote_v2.SYSTEMS` without R4-t), coverage fixtures and coverage promotion (no `fixture_cstar_s2.json`), parameter construction, Q1 decision, benchmark counts, report; context-dependent reference menu for the fresh-market secondary systems (`revision_v2.menu`, `expected_upstream`, freeze verification, report labels), with tests that require D2+H3 alone there and both families elsewhere |
| D2 H4 blind to the defence | defence-aware brief after the defender freeze; resource envelope; no defender change after H4 | 5.3, 11 | H4 brief, load check with the envelope, runner budget dispatch and bounded controls for H4 (`revision_v2.controls`), C* in the smoke check, timing record in `h4_check` |
| D3 X7-SC reset depends only on the horizon | reset-or-wait by age (a_R), exposure gate (e_P), credibility image p_own; 15 knobs | 5.2 | X7-SC family, corner count |
| D4 no role-asymmetric coalition | X8-DB decoy and beneficiary, c = 2, 6 cells | 5.2, 6.3, 8.1 | new family, manifest |
| D5 coalition reference menu too narrow | both objectives' truthful projections; G_tot searches before the reference; G_min search against a preliminary reference; final reference freeze; archive rescoring with the reference as a candidate | 6.3, 6.4 | coalition objective adapters (G_tot, G_min), the six-step order, shared reference records and their reconstruction, dependency validation, verification |
| D6 W1 reporting rule | supported, contradicted, unresolved | 6.2 | report |
| D7 BOINC adaptation | C-boinc replaces C-taper K = 24 | 3.3 | comparator |
| D8 comparator neutrality wording | reworded; Q1 limited to the fixed pair | 1, 3.3 | none |
| D9 fixed-attack contrast mixes attacker and reference terms | both terms, efficiency; extra conditional effects | 6.6, 9.3 | cross-evaluation records with both terms and efficiency, the added conditional contrasts in `sim/decisions_v2.py`, report |
| D10 does probation end | honest-replacement diagnostic | 6.7, 8.1 | new stage |
| D11 statistical versus practical difference | four Q1 categories | 9.3 | Q1 decision |
| D12 no efficiency condition | "better" needs the efficiency bound; trade-offs reported | 9.3 | evaluation-record fields and schemas (`GAIN_FIELDS` and the record schema: service share, false-failure refunds, audit spend), Q1 report |
| D13 multiplicity scope | stated | 9.4 | none |
| D14 coverage selection and numerical rules | Clopper-Pearson at selection; no fallback; numerical rules stated | 9.2, 9.5 | coverage selection by the Clopper-Pearson criterion, nonfinite-statistic refusal in `sim/intervals.py` callers |
| D15 search-quality consequences | incomplete means prescribed-procedure only; held-out doubled winners | 6.5 | doubling stage, report |
| D16 extrema selected on evaluation data | training selection for the bank envelope and welfare | 6.2, 6.6 | training-seed bank matrix and envelope selection, welfare winner selection and freeze records, report |
| D17 question-to-cell map | table; H4 cut reduces Q3's scope | 8.1a, 8.2 | status propagation (missing versus search-flagged) and question dependencies in verify and report |
| D18 budget | recomputed: about 39.3 USD (H4 re-priced after its timing, 5.3) | 8.2 | benchmark constants, cost accounting |

Every code change above gets a regression test that fails against the draft-6 code first (TDD), in the plan revision.

### Round 7 (both seats: reject) and its disposition

| Correction | Draft 7 after round 7 | Where |
|---|---|---|
| Sol 1 / Astra 1: "A_tot = 2,500 in every market" rested on draws | generator-wide bound: K in [40, 80], A_tot in [2,000, 2,500] at rho = 0.2, [400, 500] at rho = 1; test at both ends | 3.4 |
| Astra 2: fresh whole systems lost the X7-SC reference searches | same reduced D2+H3 menu for all three secondary systems on fresh markets, labelled | 6.4 |
| Sol 2 / Astra 3: X8-DB projection changed the decoy | beneficiary clip = 1 only; decoy knobs unchanged | 6.3 |
| Sol 3: G_min projections excluded | six-step order with a preliminary and a final reference and archive rescoring | 6.3, 6.4 |
| Sol 4 / Astra 3-4: timing and prose | X8 real n_D, restart after every replacement, gate from the offering identity, call-order independence; X7 voluntary trigger suppressed while waiting; "newest" sentence removed; "fresh multiplier" wording; p_own batch update; both joint twins | 5.2, 6.3 |
| Sol 5 / Astra 5: H4 cost not bounded | X7-SC bounded controls and budgets for H4; timing record in the check; cost recomputed after H4 | 5.3, 11 |
| Sol 6 / Astra 6: reporting rules | category 3 as "neither 1 nor 2"; efficiency non-inferiority unresolved versus loss; descriptive label; tail 0.05/6 (83, 21); nonfinite statistics refused | 9.2, 9.3 |
| Astra 7: missing versus search-flagged | two statuses with separate consequences; checks listed per question | 6.5, 8.1a |
| Sol 7 / Astra 8: Code column | expanded; regression tests | 14 |
| Sol 8: section 4.2 wording | "provides additional development selection" | 4.2 |

### Round 8 (Sol: reject; Astra: accept-with-caveat) and its disposition

| Correction | Change | Where |
|---|---|---|
| Sol 1: the final reference could not be selected as the G_min winner | added as a candidate where representable; regression test | 6.3 |
| Sol 2 / Astra 1: Code column lacked the reduced fresh menu | added to D1's code entry with tests | 14 |
| Astra 2: D5 summary described the obsolete order | corrected | 14 |
| Astra 3: projection evaluations not priced | separate cost item (new episodes), benchmarked | 8.2 |

### Round 9: both seats accept (Sol 0.94, Astra 0.95); consensus

No corrections. Both seats note that acceptance covers the design only; the implementation and the measured costs are
unverified until the plan revision, the benchmark, and the cost recomputation after H4.

