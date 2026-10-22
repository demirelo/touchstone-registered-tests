# Revision program: design (draft 6, accepted)

Status: accepted by Sol high and Astra high in round 6 (both accept, confidence 0.96; `docs/revision/roster/consensus-design.md`). Nothing here is registered yet. After consensus, this document is
the specification of the implementation plan, and section 9 becomes the second registered protocol ("protocol v2").
Rounds 1 to 5 (both seats: reject) and the disposition of each correction: `docs/revision/roster/sol-design-r1.md`,
`astra-design-r1.md`, `sol-design-r2.md`, `astra-design-r2.md`, `sol-design-r3.md`, `astra-design-r3.md`, `sol-design-r4.md`,
`astra-design-r4.md`, `sol-design-r5.md`, `astra-design-r5.md`, and section 13 below.

Inputs: the GPT Pro review triage (`docs/paper/gpt-pro-review-triage-2026-10-22.md`, "Program"), paper draft 8
(`paper/main.tex`), the final evaluation (`docs/final-evaluation-2026-10-20/`), robustness
(`docs/robustness/2026-10-22-results.md`), theory (`docs/theory/reset-deterrence.md`), and the simulator specification
(`docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md`, "spec").

## 1. Questions

- **Q1 comparator.** Does age-based selection (R3) do better or worse than the best of three tested budget-constrained
  adaptations of credibility-based verification (Sarmenta 2001; BOINC adaptive replication), at identical allocation,
  payment, tolerance, ban length, pacing, budget, and sanctions? The answer is limited to the tested adaptations; it does
  not establish the strongest possible credibility rule.
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
- **Development selection.** Twelve configurations, C-thr with K in {2, 6, 12, 24}, C-mem with K in {2, 6} x M in
  {20, 50}, and C-taper with K in {2, 6, 12, 24}, at the fixed pair and R3's pacing, scored by the common objective
  (section 4.1) with the inner search on the three tuning markets; the top 2 rechecked at the full budget (as in 4.2). The
  best is frozen as C* (variant, K, and M where it applies). This gives C a degree of freedom that R3 lacks; it favours the
  comparator.
- **Pacing variants.** C* (R3's schedule), C*/S0 (spread), and C*/S2 (R4's schedule, section 3.4).

Mechanics stated before outcomes: credibility accrues only through passed audits, age through time. Under scarce audits,
unproven identities persist and the priority phase can use the whole quota (Lemma 2 overload, finite horizon). Under R3,
age does not end intensive targeting: a replacement can remain the newest identity after its fresh window (Lemma 2b).

### 3.4 Repaired R3 (R4)

R4 is R3 with reserve = min(J L, floor(A_tot / 2)). The fix comes from robustness (rho = 1: reserve = A_tot, no early
audits). R4 is compared with C*/S2 (same schedule) for Q1, and with R3 at rho = 1 and rho = 0.2 to test the repair
(section 8.1).

### 3.5 Rule set

| Name | Role |
|---|---|
| F000 (= B3), F001, F010, F011 (= predecessor), F100, F101, F110, F111 (= R3) | factorial at the fixed pair |
| C*, C*/S0, C*/S2 | comparator at the fixed pair |
| R4 | repaired R3 at the fixed pair |
| B3-t, R3-t, R4-t, C*-t | whole systems, tuned by section 4 |
| B2 | registered parameters, headline only, reference |

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
  comparator's development selection (3.3, 12 configurations) is an extra cost that favours the comparator and is
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
| H4 | sealed, independently authored (5.3) |

**X7-SC** knobs, in this coordinate order (13; `clip` last): u0 in [0, 1], m0 in [0, 1], s in [0, 0.3], d in [0, 1],
r in [0, 0.2], w in [0, 2], k_F in [0, 1], k_T in [0, 2], a_F in [0, 60], n_P in [0, 30], h_R in [0, T], lambda in
[0, 1], clip in {0, 1} (binary through the family's logistic threshold at 0.5). Real thresholds are compared without
rounding.

State: the markup m (initial m0), persisting across identities as in D2+H3; the current identity's creation round c and
its own per-round served, audited, and failed counts (identity-local).

Round t, in this order (the harness asks for the action before it creates a replacement, and applies an exit before the
action's offer, `sim/policies/identity.py`, `sim/market.py`):

1. Markup update from round t - 1, exactly once, as `AdaptiveCheat`: after a failed audit m <- m (1 - d); else, if the
   entity was banned in t - 1, unchanged; else m <- min(m0, m + r m0).
2. Failure trigger: the identity that served in t - 1 had a failed audit in t - 1, and T - t > h_R.
3. Voluntary trigger (only if no failure trigger): over rounds [max(c, t - L), t), served >= 1 and audited / served >
   lambda.
4. If a trigger fires: exit; the identity-local counters are cleared and the replacement's creation round is t.
5. Phase of the identity that will serve in round t (the replacement if one was created): terminal if T - t <= L; else
   fresh if (t - c) < a_F or (audited - failed of this identity) < n_P; else established.
6. Action: k = k_F (fresh), 1 (established), k_T (terminal); effort = q_max (1 - min(1, k u0)); claim =
   min(1, max(0, effort + k m - s)), and min(claim, effort) if clip = 1; bid = (1 + w)(a + b effort).

Embedding of D2+H3: k_F = k_T = 1, a_F = n_P = 0, lambda = 1, h_R = 0 if x = 1 and h_R = T if x = 0; the other knobs
unchanged. Required test: identical round records to D2+H3 for both x values on every common-grid rule, at least 5
seeds. Embedded D2+H3 attacks from the same cell's D2+H3 search are inserted as incumbents.

**X7-SC corner controls** (a bounded diagnostic, not exhaustive coverage): `scipy.stats.qmc.Sobol(d=13, scramble=True,
seed=20261028).random_base2(9)` (512 points; the scipy version is pinned by `uv.lock` and recorded); coordinate i maps to
bit 1 if its value >= 0.5, else 0; bit 0 gives the knob's lower bound and bit 1 its upper bound (for clip, the value of
the bit); points are de-duplicated by exact key in generation order; the all-low and all-high corners are appended if
absent (514 corners); each corner is evaluated as is and with its truthful projection (clip = 1), as `corner_controls`
does for smaller families, de-duplicated by exact key across corners and projections (769 distinct knob vectors with
scipy 1.18.1).

### 5.3 Sealed family H4

A separate Codex session (a fresh `gpt-6.1-sol` session at high effort, in its own clone at the lock-candidate commit)
receives a brief with only the family interface, the allowed observations, and the admissible class. It writes
`sealed2/h4/family.py` and `sealed2/h4/containment.md`, runs the load check and a smoke evaluation against F000 and F111
on the development instances, and records them in `sealed2/h4/check.json`, all before the commitment. The author records
the bundle hash in protocol v2 and does not read the bundle until the report. The evaluation code loads H4 from the bundle
after the lock and before any evaluation-seed episode, and verifies the hash. No repair is allowed after the lock: if H4
fails to load, it is excluded, the exclusion is reported, and the independently authored part of Q3 is unanswered.

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
  re-estimated with its interval.
- Both on the D2+H3 and X7-SC knob spaces; winners selected on training seeds. Reported: the lowest efficiency found, its
  interval, and the attacker's gain.

### 6.3 Coalition, headline only

Members are `sim/policies/exploratory.py::coalition_members(cfg, focal, c)`: the focal provider, then the providers
nearest to it in the positions score order, ties to the lower index; member j of that ordered list (j = 0 is the focal
provider) gets schedule index j. Members play shared knobs with member schedules (X6-SE/v2); non-members play
honest-max. Member gain
g_j = (pi_j - pi_j^0) / (S*/N), where pi_j^0 is member j's profit under the frozen joint truthful reference. The joint
reference is the candidate with the highest training mean of sum_j (pi_j / (S*/N)) among, in this tie order: all members
honest-max, all members abstain, all members playing the joint twin. The joint twin is the result of the registered
search (5 restarts x 300, dev-train seeds) over the X6-SE/v2 knobs with clip = 1 forced for every member, maximising the
same total. Objectives: total G_tot = sum_j E[g_j] and worst member G_min = min_j E[g_j] (not E[min_j g_j]). Claims are
gains relative to this coordinated truthful profile for shared-knob coalitions; they say nothing about coalition
stability or each member's best unilateral alternative.

### 6.4 References and freeze order

- **Menu.** A rule's truthful reference is selected on training seeds by the registered order (spec 5.2) from one menu:
  abstain, honest-max, and the twin, projection, and archive candidates of its D2+H3 and X7-SC searches. Every rule in the
  evaluation, including B2 and the rho = 1 repair cells, has exactly these two searches at the same budget (8.1), so
  matched pairs have equivalent menus. Its D2, X5-AG/v2, H4, and welfare gains use the same frozen reference; no other
  family adds candidates. Coalitions use their own joint reference (6.3).
- **Development reference** (tuning, comparator selection): the same construction with the tuning objective's families
  (D2, D2+H3, X7-SC) on the tuning markets. H4 is never available in development.
- **Dependency and freeze order per market.** (1) Profit attack and twin searches and banks; (2) reference selection and
  freeze; (3) the searches that need a frozen reference (W1) and the coalition joint-twin search, joint-reference freeze,
  then the coalition G_tot and G_min searches; (4) envelope family choices (9.3 Q3) and the fixed-attack bank (6.6);
  (5) final freeze. Only then may any evaluation-seed episode of that market run; the evaluation stage refuses to run
  otherwise. Doubling results never enter the frozen candidates.

### 6.5 Search-quality checks

A doubling check continues the registered search with as many additional restarts as the registered budget (new restart
seeds), so the total budget doubles; it is reported as a diagnostic. Scheduled checks (fixed in the manifest):

- headline: all 12 matched rules x {D2+H3, X7-SC} (24), the 16 welfare cells, and the 32 coalition cells;
- fresh markets: the Q1 and Q4 rules (F000, F111, C*, R4, C*/S2) x {D2+H3, X7-SC} x 6 (60).

132 checks. Units and threshold 0.005: gain (normalised by S*/N) for profit; G_tot and G_min (each normalised) for
coalitions; gross efficiency (a share of the first best) for welfare. Attack-profit and reference-profit changes are
reported separately. A W1 check that finds a feasible point where the original found none, or a feasible point with
efficiency lower by at least 0.005, labels the cell incomplete. Cells without a scheduled check (factorial cells on fresh
markets, whole systems, X5, H4, D2 extras) carry no search-quality claim.

### 6.6 Fixed-attack cross-evaluation (Q2)

For each market and family in {D2+H3, X7-SC}: the bank is the 8 selected attacks of the 8 factorial cells (frozen with
the references). Each attack is evaluated against all 8 factorial rules on the evaluation seeds, each against its own
frozen reference: an 8 x 8 gain matrix. Fixed-attack contrasts use the same effect coding as 9.3 within each attack's row,
then the equal-weight mean over the 8 rows; the per-rule maximum over the bank (bank envelope) is also reported.

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
| Matched factorial and comparator | F000..F111, C*, C*/S0, C*/S2, R4 (12) | D2+H3, X7-SC | 7 | 168 |
| Matched core extras | F000, F111, C*, R4 | D2, X5-AG/v2, H4 | 7 | 84 |
| Whole systems | B3-t, R3-t, R4-t, C*-t | D2+H3, X7-SC | 7 | 56 |
| Reference | B2 | D2, D2+H3, X7-SC | headline | 3 |
| Welfare | F000, F111, C*, R4 | W0, W1 x {D2+H3, X7-SC} | headline | 16 |
| Coalition | F000, F111, C*, R4 | c {2, 5} x {sync, staggered} x {total, min} | headline | 32 |
| Repair test | F000, F111, R4, C*, C*/S2 | D2, D2+H3, X7-SC | headline at rho = 1 | 15 |

374 search cells (126 on the X7-SC knob space), 14 fixed-attack cross-evaluations (6.6), 132 doubling checks (6.5). Every
cell is evaluated on 200 seeds.

### 8.2 Cost

Unit: one headline D2+H3 cell (search, bank, reference, 40-seed evaluation) at the registered budget, about 25
core-minutes, about 18,000 episodes, and about 0.045 USD on pods (robustness: 322 cell-equivalents, 14 USD). X7-SC
multiplier 2.5 (double evaluations, 769 corner-control vectors); a doubling check 1 unit (X7-SC 2.5); inner tuning
searches 0.04 (X7-SC 0.1). The additional cost of increasing the evaluation from 40 to 200 seeds (the unit already
includes 40) is priced conservatively at 16 percent of a cell; episode-based estimates are lower and the benchmark
decides.

| Item | Units |
|---|---|
| Comparator selection: 108 inner (6.5) + top 2 rechecked x 3 families x 3 markets (27) | 33.5 |
| Whole-system tuning: 576 inner (34.6) + 4 systems x 2 rechecks x 3 families x 3 markets (108) | 142.6 |
| Development searches for the coverage fixtures (C*/S2: D2, D2+H3, X7-SC inner on 3 markets, 9 searches) | 0.5 |
| Coverage (9.5): 14 profiles x 20,000 seeds x 3 markets = 840,000 episodes (47) + bootstrap computation, 10,000 selection and 20,000 validation replications per fixture with 9,999 resamples each, resample indices shared across a fixture's statistics (about 3 core-hours, 10) | 57 |
| **Development total** | **about 233.6 (about 10.5 USD)** |
| Evaluation cells: 374 + 126 X7-SC x 1.5 | 563 |
| Additional cost of 200 instead of 40 evaluation seeds: 0.16 x 563 | 90 |
| Fixed-attack cross-evaluation: 14 x 56 attack profiles x 200 seeds = 156,800 episodes (references reuse the cells' evaluations) | 9 |
| Doubling checks: 82 at 1 + 50 X7-SC at 2.5 | 207 |
| **Evaluation total** | **about 869 (about 39.1 USD)** |

Total about 1,103 units, about 50 USD. **The author's approval is required for any total above 40 USD** (the range quoted
when the program was chosen).

Caps and stop rules:

- **Benchmark first.** Before any paid tuning, one cell of each kind and one coverage fixture run on a pod, and the table
  is recomputed.
- **Development cap 12 USD.** If the recomputed development cost exceeds it: (1) the comparator selection and tuning use
  the headline market and `dev0` only, and the coverage fixtures use the replacement design of 9.5; (2) the coverage pools
  shrink to 10,000 seeds per market. If it still exceeds the cap, work stops and the author decides.
- **Evaluation cap 40 USD.** If the recomputed evaluation cost exceeds it, cuts apply in this order before the lock: (1)
  whole-system cells on fresh markets (keep headline); (2) H4 on fresh markets; (3) D2 matched extras on fresh markets;
  (4) C*/S0 cells on fresh markets. If it still exceeds the cap, work stops before the lock and the author decides.
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
  `sim/intervals.py` extended to arbitrary tail levels. Before calibration, the smallest confirmatory tail (0.05/8)
  contains about 62 of the 9,999 resamples; with kappa = 1/4 it contains about 16. This is a precision limit; validation
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

### 9.3 Decision rules

- **Q1, confirmatory on the pooled fresh markets.** Family of 4 tests: pairs F111 vs C* and R4 vs C*/S2, families
  D2+H3 and X7-SC, each on the pooled mean of the per-seed differences over the six fresh markets. Exclusive categories in
  order: ordered (Holm rejects zero in the two-sided test on calibrated p-values: "R lower" or "C lower"); else
  equivalent (the calibrated Bonferroni interval, two-sided 0.05/4 times kappa_Q1, lies inside [-0.05, 0.05], a
  conservative two one-sided tests procedure); else inconclusive.
  The margin 0.05 is half the registered comparative margin 0.10 and below the headline B3 - R3 difference (0.28). Holm
  steps use one-sided tails 0.05/8, 0.05/6, 0.05/4, 0.05/2. Per-market and headline Q1 results are descriptive (the
  headline market was used in development).
- **Q2, descriptive.** Per market and family, effect coding over the 8 cells: main effect of P = mean of the 4 cells with
  P = 1 minus the mean of the 4 with P = 0 (likewise G, S); two-way interaction PG = (mean of cells with P = G) minus
  (mean with P != G), likewise PS, GS; three-way PGS = (mean of cells with an odd number of 1s) minus (mean with an even
  number); conditional effects G at P = 0 and P = 1, P at S = 0 and S = 1. Both versions: separately searched attacks
  (diagonal) and fixed attacks (6.6). Pooled over the 6 fresh markets as in 9.2. Nominal 95 percent intervals, no
  decisions.
- **Q3, descriptive.** Per core rule, the attack envelope: the family among {D2+H3, X7-SC, X5-AG/v2, H4} with the highest
  training gain, evaluated unchanged; the lowest efficiency under W0 and W1 with the W1 constraint estimate; coalition
  G_tot and G_min.
- **Q4, confirmatory on sampled markets.** Per fresh market, an intersection-union test: (a) H0: g_F000 - g_F111 <= 0.10
  under D2+H3 and (b) H0: F111's gross efficiency <= 0.90, each one-sided; the market's p-value is the larger of the two
  calibrated component p-values. A market passes if Holm across the 6 market p-values rejects it (one-sided tails 0.05/6 down to
  0.05/1). Reported: k of 6 markets passing, and the markets. Wording: "replicated on k of 6 sampled markets"; failing
  markets are named; "generalisation not established" when a market is not decided. No population claim.

### 9.4 Claim scope

All claims are conditional on the six sampled markets, the stated neighbourhood, the fixed pair (Q1, Q2, Q4), the searched
families, and the frozen searches. Q4 replicates the B3 - R3 comparison under D2+H3 and R3's efficiency condition, not the
complete amended PASS predicate of the first evaluation.

### 9.5 Coverage check and calibration (before the lock)

- **Fixtures.** On the headline market, `dev0`, and `dev1`, frozen development attacks (the inner searches at the fixed
  pair from tuning and comparator selection, plus C*/S2's development searches) and development references (6.4) are run
  on pools of 20,000 seeds per market in the new range [40,000,000, 60,000,000). Profiles per seed (14): F000's D2+H3
  attack (its X7-SC attack is not needed for any confirmatory statistic and is omitted), the D2+H3 and X7-SC attacks of
  F111, C*, R4, and C*/S2, and the five rules' references. Every profile of a seed uses that seed's common random numbers,
  so per-seed differences keep their dependence.
- **Q1 fixture (pooled).** Six strata: each of the three markets split into two disjoint pools of 10,000. A replication
  draws 200 seeds with replacement from each stratum, independently across strata and replications, and computes the
  pooled statistic and its bounds; the truth is the equal-weight mean of the six stratum pool means.
- **Q4 fixtures (per market).** A replication draws 200 seeds with replacement from the market's 20,000-seed pool; the
  truth is the pool mean. The multiplier must pass on all three market fixtures and is then applied to the six fresh
  markets (a stated transfer assumption).
- **Endpoints.** Q1: both sides of the four pooled differences at the Holm tails 0.05/8, 0.05/6, 0.05/4, 0.05/2 (32
  endpoints). Q4: the one-sided lower bounds of the gain difference and of the efficiency at tails 0.05/6, 0.05/5, ...,
  0.05/1 on each of the three markets (36 endpoints). For an endpoint with allocated tail alpha_e, a candidate kappa uses
  the bound at nominal tail kappa alpha_e.
- **Selection.** On 10,000 selection replications per fixture, kappa_F is the largest of 1, 1/2, 1/4 for which every
  endpoint of family F, on every fixture, has an observed miss rate at most alpha_e.
- **Validation.** On 20,000 independent validation replications per fixture (new resampling seeds), the selected kappa_F
  is admitted if, for every endpoint of the family, the Clopper-Pearson upper bound of the miss rate at confidence
  1 - 0.01 / m_F is at most alpha_e (m_F = 32 for Q1, 36 for Q4; Bonferroni over the family's endpoints, so the
  guarantee holds jointly with Monte Carlo confidence at least 99 percent). Only the selected procedure is validated, so
  the selection does not affect this guarantee.
- **Failure.** If no candidate passes selection, or the selected one fails validation, the family receives no
  confirmatory decision (estimates and descriptive intervals are still reported).
- **Fixture branches (registered for every development-cut case of 8.2).** Seeds of a market's coverage pool are taken
  in the order of their derivation index; stratum s of a market takes the s-th consecutive block of floor(M / k) seeds,
  where M is the market's pool size and k the number of strata per market; the remainder is discarded for Q1 only. Q1
  always has six equal-weight strata, sampled with replacement:
  - three markets, M = 20,000: k = 2 strata of 10,000 per market (the default);
  - two markets (headline, `dev0`), M = 20,000: k = 3 strata of 6,666 per market;
  - two markets (headline, `dev0`), M = 10,000: k = 3 strata of 3,333 per market (14 profiles x 10,000 x 2 = 280,000
    profile episodes, about 16 units, plus bootstrap work).
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
smaller than searched ones; Q3: X7-SC raises R3's gain above D2+H3 by less than 0.05; coalition G_min well below G_tot; R4
removes the rho = 1 collapse; Q4: k >= 5.

## 10. Artifact

A public release at the report commit: code, tuned files, all records, the generator, the block headers, a one-command
reproduction of every table (`scripts/reproduce.py`), and the paper sources. The author publishes it (GitHub release,
Zenodo DOI); the plan prepares and checks the bundle.

## 11. Order of work

1. Build, test first, on development seeds: rules (3), families and objectives (5, 6), references and freeze order (6.4),
   cross-evaluation (6.6), generator, streams, and block reader (7), interval extensions (9.2), manifest, benchmark.
2. H4: the sealed session writes, checks, and commits the family; the author records the hash without reading it.
3. Benchmark on a pod; recompute the cost; the author approves the total if it exceeds 40 USD.
4. Comparator selection (3.3); whole-system tuning (4) on pods.
5. Coverage check (9.5).
6. Protocol v2 with predictions; Sol and Astra review; lock (signed tag, OpenTimestamps proof upgraded, pushed).
7. Block H; draw; calibrate; load and verify H4.
8. Evaluation on pods; report; review.
9. Artifact; paper revision; review.

## 12. Remaining questions for the reviewers

1. Is the reduced confirmatory scope (Q1 pooled, Q4 per market; Q2 and Q3 descriptive) acceptable for the paper's claims?
2. Is the calibration (one multiplier per family, selected and then validated on independent replications with
   Bonferroni-adjusted Clopper-Pearson bounds at the allocated tails) acceptable?

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
