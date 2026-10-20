THEOREM: statement, assumptions, proof, and the check list.

**Proposed theorem: refund limits, newcomer coverage, and conditional reset deterrence.**

The requested unconditional claim in part (b) is false. Full newcomer auditing does not imply that a reset costs \(L\) rounds of cheating profit. A correct theorem must use continuation values, account for false failures, and distinguish refunds per job from a ban imposed once per round.

**Assumptions and notation.** Consider one provider against honest-max opponents. There are no bonds or fees; initially \(e=0\). Fix its public offer, with claim \(c\le q_{\max}\), and compare truthful effort \(c\) with effort \(c-\Delta\). Allocation and payments therefore remain unchanged in this round. Effort is common to the provider’s \(s\) served jobs, as in the simulator.

Let

\[
g=b\Delta,\qquad
d=\Phi((\Delta-\tau)/\sigma),\qquad
d_0=\Phi(-\tau/\sigma).
\]

Here \(g\) is the cost saving per job. Let \(M_j\) be job \(j\)’s escrow payment. For B3 and R3,

\[
M_j=v_jc-s_{2,j},
\]

not the bid or the provider’s margin.

Condition on the selected audit set \(U\), rival outcomes, and all state transitions independent of the focal delivery noise. Write \(K=|U|\). Let \(V_U^+\) and \(V_U^-\) be continuation values after no focal failure and at least one focal failure. They must use the same specified continuation policy class. Set \(C_U=V_U^+-V_U^-\). Noise is independent across jobs and independent of audit selection.

**Statement.** The deviation’s incremental expected profit is exactly

\[
A(\Delta)=sg-
\mathbb E\!\left[
(d-d_0)\sum_{j\in U}M_j+
\big((1-d_0)^K-(1-d)^K\big)C_U
\right]. \tag{1}
\]

Thus \(A(\Delta)\le0\) is the exact local deterrence condition.

If all focal jobs have marginal audit probability \(p_E\), \(M_j\ge M\), and \(C_U\ge\underline C\), a sufficient condition is

\[
sg\le sp_E(d-d_0)M+
\big[D(d)-D(d_0)\big]\underline C,
\quad
D(z)=1-\mathbb E[(1-z)^K]. \tag{2}
\]

For one job this becomes

\[
g\le p_E(d-d_0)(M+\underline C).
\]

The brief’s \(pd(M+\Delta V)\) formula requires zero false-failure probability. It is an approximation here.

**Lemma 1: uniform auditing and free replacement.** Under B2/B3, identity age does not affect allocation, pricing, or audit selection. With free replacement, no bond, and otherwise identical state, a banned identity can recover the unbanned continuation opportunity next round. Consequently \(C_U=0\), and

\[
A(\Delta)=sg-(d-d_0)\mathbb E\sum_{j\in U}M_j.
\]

For equal payments, \(g>p(d-d_0)M\) makes shading profitable. Increasing the bypassable ban length cannot repair this inequality.

**Lemma 2: newcomer coverage and overload.** Let \(F_t\) be all served jobs whose identities first offered fewer than \(L\) rounds ago. R3 audits every such job whenever \(k_t\ge F_t\). If at most \(n_t\) fresh identities each serve at most \(s_{\max}\), then \(k_t\ge n_ts_{\max}\) suffices.

When capacity is insufficient, R3 orders age groups newest first. For the focal group, let \(H_t\) count strictly newer fresh jobs and let \(n\) count jobs with the same first-offer round. The group receives

\[
k'=\min\{n,\max(0,k_t-H_t)\}
\]

audits. If the focal identity has \(s\) jobs in that group,

\[
K\sim\operatorname{Hypergeom}(n,s,k'),\qquad
P(K=0)=\frac{\binom{n-s}{k'}}{\binom n{k'}}.
\]

The probability of escaping **detection** is

\[
1-D(d)=
\sum_\ell
\frac{\binom s\ell\binom{n-s}{k'-\ell}}{\binom n{k'}}
(1-d)^\ell. \tag{3}
\]

Use this distribution in (1)–(2). Older fresh groups can receive zero audits. Pooling all fresh jobs into one hypergeometric sample would be incorrect.

**Lemma 3: reset cost is conditional.** For an immediate-reset continuation plan,

\[
C_U=V_{E,U}-V_{F,U}+e.
\]

A lower bound \(V_E-V_F\ge\sum_{r=1}^{h}\gamma_r\), where \(h=\min(L,T-t-1)\), requires a separate argument: every admissible fresh continuation must have an established counterpart with expected net reward at least \(\gamma_r\) higher in those rounds and no lower continuation value afterward. Comparing with an optimal fresh continuation proves the bound.

Only under this additional condition may (2) use

\[
\underline C=e+\sum_{r=1}^{h}\gamma_r.
\]

The \(\gamma_r\) are net continuation advantages, not gross cheating gains \(sg\). If the provider may wait instead of resetting, compute \(V^-\) by a Bellman recursion that includes immediate reset, delayed reset, waiting out the ban, and abstention. Immediate-reset loss alone can overstate punishment.

**Proof.** Shading saves \(sg\). Each audited job’s failure probability increases by \(d-d_0\), giving the incremental refund term in (1). Conditional on \(K\), independence gives failure probabilities \(1-(1-d)^K\) and \(1-(1-d_0)^K\). Their difference multiplies the continuation loss once, irrespective of how many jobs fail. This proves (1); the stated lower bounds prove (2). Free replacement establishes Lemma 1 by identity relabeling. R3’s sorted priority list proves full coverage; independent continuous audit keys give uniform sampling within a tied age group, proving Lemma 2. The continuation comparison proves Lemma 3.

For a global result within the restricted action class, compute truthful continuation values, optimize permitted identity decisions, and verify (1) at every reachable state and every allowed \(\Delta\). Backward induction from \(V_T=0\) then excludes every profitable shading plan. Testing selected states or searched policies does not establish that certificate.

**A concrete impossibility at the locked parameters.** Even full terminal auditing cannot eliminate all shading. In the last round, continuation loss is zero. At \(\Delta=0\), marginal refund deterrence per job is at most

\[
M_j\frac{\phi(3.2)}{0.05}
\le1.4(0.0477)<0.067,
\]

whereas every provider has \(b\ge0.22\). Therefore a sufficiently small effort reduction, with the offer unchanged, increases expected profit whenever service has positive probability. Exact truthfulness is impossible under these parameters. A bounded-gain claim remains possible.

The terminal reserve covers every terminal job if \(A_{\rm tot}\ge JL\), with

\[
A_{\rm tot}=\lfloor(\beta/\rho)n_{\rm FB}\rfloor.
\]

Below that threshold, the code audits only while allowance remains.

**Scope and checks.**

- Claim changes can alter allocation, second scores, and payments. Claims above \(q_{\max}\) lack the same-offer truthful comparator. Keep these outside the theorem; evaluate them through the registered attack/clip/reference decomposition.
- Record first-offer age, \(F_t,k_t,H_t,n,K\), payment sums, and fresh/established/terminal audit rates.
- Check refund and failure frequencies against (1) and (3), including false failures.
- Estimate matched-state continuation values with remaining quota, time, competitors, and recovery options held comparable. “Reset every round versus never reset” is not this value difference.
- Report H3 and X6 gains alongside coverage. X6 is a joint-deviation capacity test, not unilateral incentive compatibility.
- At the headline setting, \(A_{\rm tot}=2500\), reserve \(500\), and early quotas are 10/11 before carry and caps. Two six-job entrants already exceed capacity.
- Aging past \(L\) does not remove T1 priority: a replacement remains newer than initial identities.

ROBUSTNESS PLAN: the grid with predictions and the counts.

Freeze the manifest, predictions, parameter hashes, and reporting rules before new outcomes. This is a prospective exploratory extension. Existing dev-val seeds are not a fresh holdout.

Use B1, B2, B3, and R3 throughout. Define the core family set as D2, D2+H3, X1 audit-hazard, and X4 reset-option.

| Axis | Grid and reason | Prediction | Evidence against the proposed generalization |
|---|---|---|---|
| Budget and audit cost | Full \(\beta=\{.02,.05,.10\}\), \(\rho=\{.05,.2,1\}\) cross; tests audit capacity | H3 protection improves as early quota covers fresh demand. At \((.02,.2)\), quota is only 2/3 | R3 retains large H3 gains despite adequate coverage, or gains do not track capacity |
| Position | Low, median, high in every main condition | Effect size varies with cost savings and payments; adequate-coverage H3 advantage persists | Advantage exists only at median |
| Market scale | \((N,J)=(5,25),(10,50),(20,100)\) | Similar behavior when workload and capacity scale together | Advantage disappears with scale despite comparable coverage |
| Market load | \(N=10,\ J=\{25,50,60\}\) | Competition, service counts, and payments change deterrence | Results contradict measured payment/coverage conditions |
| Noise | \(\sigma=\{.025,.05,.10\}\) | High noise increases honest failures and weakens welfare performance; gain need not be monotone | Claimed efficiency survives only at the original noise level |
| Entry cost | \(e/m=\{0,.1,1,10\}\) | Uniform baselines improve; R3’s incremental advantage shrinks | Tiny positive entry cost removes the practical advantage |
| Horizon | \(T=\{100,200,400\}\), \(L=10\) fixed | Short horizons devote more budget to the reserve and reduce early protection | Benefits depend narrowly on \(T=200\) |

For \(N=5,20\), interpolate \(q_{\max}\) and \(b\) linearly along the original ordered type list at evenly spaced endpoints; retain \(a=.02,k=6\). Freeze the resulting arrays. State that type composition also changes.

Run the budget-cost-position cross first. For other axes, change one factor from the headline setting and use all three positions. This gives:

- Budget-cost-position: \(27\times4\) rules \(\times4\) families = **432 cells**.
- Eleven additional market settings: \(11\times3\times4\times4=\mathbf{528}\).
- X2 tranche, X3 timing, X5 aging at the headline setting, all positions: **36**.
- X6 at all three budgets, default cost and median position: coalition sizes 1, 2, 5; synchronized and staggered schedules for sizes 2 and 5. Five profiles × three budgets × four rules = **60**.

**Total: 1,056 search cells.**

Predict X2/X5 will expose timing weaknesses without eliminating R3’s adequate-capacity H3 advantage. Predict X3 will exploit early budget shortages. Terminal shading can remain profitable, as the theorem shows. Predict synchronized X6 will increase R3’s gain when fresh demand exceeds quota; test the staggered comparison without assuming it must favor R3.

Use registered gain, harm, gross/net efficiency, spend, and the full efficiency decomposition. Report every cell and all positions. For adequate-capacity, low-noise, free-entry H3 conditions, pre-state gain reduction of at least 0.10 against each audited baseline, R3 gain below 0.30, and gross efficiency above 0.90 as descriptive targets. Report misses explicitly. Overload failures delimit capacity; they do not contradict the coverage lemma.

For every cell, retain five restarts × 300 evaluations × five training seeds for attack and twin, registered incumbents/corners, compatible candidate-bank evaluation, and reference selection last. Evaluate on dev-val 2000–2019. Report restart spread and fixed, preselected doubling checks. No H1 calls, H2 access, or final-evaluation seeds.

Changed markets require separate calibration on 4000–4019, with \(\alpha=\rho m\) and \(B=\beta\hat S\). Transfer frozen baseline parameters unchanged. Their original tuning certificates do **not** establish tuning quality in changed markets; label all such runs “parameter transfer.” Do not bypass provenance checks by substituting a new market hash.

Existing exploratory policies hard-code \(T=200\) and public ban length 10. New horizon-aware implementations must reproduce the originals at \(T=200,L=10\). Keep all rules and ban lengths frozen.

At the supplied rate, 1,056 cells imply approximately **17.21 million episodes, 129 pod-hours, and USD 62**. Allow 30% provisionally for diagnostics, bank work, and runtime variation: **167 hours, USD 80**. These are planning estimates; larger markets and replacement histories can cost more. Generate exact trajectory counts and benchmark before launch.

A preselected cut retains three budgets at default cost, all positions, and D2/H3/X4; all eleven market changes at median; X1/X2/X3/X5 at headline median; and headline X6 profiles. This is **276 cells**, about **4.50 million episodes, 34 pod-hours, USD 16**, or **44 hours/USD 21** with the same provision. It sacrifices cost interactions and changed-market position coverage.

IMPLEMENTATION: the new files and functions needed (no frozen file changes).

- `docs/theory/reset-deterrence.md`: theorem, assumptions, counterexamples, proof.
- `experiments/robustness-v1.yaml`: immutable grids, predictions, type arrays, seeds, transfer provenance, and cut.
- `scripts/calibrate_robustness.py`: `build_market()`, `calibrate_market()`; reuse calibration functions and write separate outputs.
- `sim/policies/robustness_v1.py`: horizon-aware exploratory factories; no global monkey-patching.
- `scripts/robustness_v1.py`: `build_manifest()`, `load_transfer_params()`, `run_cell()`, `finalize_bank_reference()`, `report_all_cells()`.
- `scripts/check_reset_theory.py`: `coverage_distribution()`, `deviation_advantage()`, `solve_continuations()`, and matched-state diagnostics. Numerical value estimates must be labeled estimates unless certified bounds are available.
- New tests for hypergeometric enumeration, terminal shading, wait/reset options, baseline identity neutrality, policy equivalence, seed restrictions, and provenance.
- Separate result directories and hash manifests. Do not alter the registered verdict or frozen sweep.

No files were changed and no experiments were launched.

RISKS: the three most likely ways either part fails review.

1. **Theoretical scope:** continuation losses are assumed rather than proved; restricted shading results are presented as full mechanism incentive compatibility.
2. **Empirical attribution:** transferred baseline tuning, allocation changes, or X6 coalition behavior are mistaken for evidence about unilateral newcomer deterrence.
3. **Statistical strength:** reused development seeds, search error, and many comparisons are presented as fresh confirmatory evidence or certified robustness.

CONFIDENCE: 0.90.
