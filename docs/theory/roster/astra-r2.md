THEOREM (final):

**Accept the renewal argument only after the following repairs.** It gives a conditional bound for a restricted policy class. It does not explain the reported D2+H3 gains by itself.

Let the public claim and bid remain fixed, with \(0\le\Delta\le c\le q_{\max}\). Set
\[
g=b\Delta,\quad d=\Phi((\Delta-\tau)/\sigma),\quad d_0=\Phi(-\tau/\sigma).
\]
For state \(z\), let \(S_z\) be service count, \(U_z\) the audit set, and \(K_z=|U_z|\). The exact current-round shading surplus is
\[
G_z=\mathbb E\!\left[S_zg-(d-d_0)\sum_{j\in U_z}M_j\right].
\]
The expression \(s[g-p_z(d-d_0)M]\) requires constant service and a valid factorization of audited payments. An unweighted mean payment is insufficient when audit selection and payments are correlated.

**Lemma 1: local incentives and uniform replacement.** Retain round 1’s identity:
\[
A(\Delta)=sg-\mathbb E\!\left[
(d-d_0)\sum_{j\in U}M_j+
\{(1-d_0)^K-(1-d)^K\}C_U
\right].
\]
Its assumptions include independent delivery noise and the specified continuation comparison.

Proof: shading saves \(sg\); each audited escrow has incremental refund probability \(d-d_0\); the incremental probability of at least one failure multiplies the continuation loss once.

Under uniform auditing, free immediate replacement, and identity-neutral opportunities, replacement removes the focal ban’s continuation loss. Thus Claim A holds **in expectation**, conditional on those opportunities. The focal ban length does not enter. This does not establish invariance when changing opponents’ bans or other market conditions.

**Lemma 2: coverage and failure probability.** Adequate coverage audits every fresh job. Under overload, let \(H\) count strictly newer fresh jobs, \(n\) all jobs in the focal age group, and \(s\) its focal jobs. Then
\[
k'=\min(n,\max(0,k-H)),\qquad
K\sim\operatorname{Hypergeom}(n,s,k').
\]
Therefore
\[
q_z=1-\mathbb E[(1-d)^{K_z}].
\]
Proof: newer groups consume quota first; independent continuous audit keys give uniform sampling within a tied group. Conditional independence of delivery noise gives the last expression.

The proposed \(1-(1-p_Ed)^s\) requires independent Bernoulli audit selection. The simulator does not generally satisfy this assumption.

**Main theorem: conditional renewal bound.** Consider immediate-reset policies with:

- A fixed established-state action; fresh-state actions specified separately.
- Stationary, independent cycles, each beginning with an established spell and ending after recovery from its failure.
- Established rounds with constant conditional expected profit \(r_E\) and failure hazard \(q_E>0\).
- Recovery duration \(D\ge L\), with finite mean, total profit \(R_F\) before entry charges, and \(N_R\) replacements per cycle.
- Independent delivery noise and finite expected cycle rewards.

Then long-run profit is exactly
\[
\bar\Pi=
\frac{r_E/q_E+\mathbb E R_F-e\mathbb E N_R}
     {1/q_E+\mathbb E D}. \tag{4}
\]

Proof: the established spell has mean \(1/q_E\). Summing conditional expected rewards over surviving rounds gives expected reward \(r_E/q_E\), even though the last round’s reward and failure can be correlated. Add recovery rewards and entry charges. Divide expected cycle reward by expected cycle length.

For the surplus corollary, additionally require that the same-offer truthful expected profit equals a common rate \(h\) throughout both states, and that \(h\) is the comparison benchmark. Suppose every permitted fresh action has conditional surplus at most \(\epsilon\ge0\). At \(e=0\),
\[
\bar\Pi-h
\le
\epsilon+
\frac{(G_E-\epsilon)_+}{1+q_EL}. \tag{5}
\]
Indeed, the cycle’s surplus is at most \(G_E/q_E+\epsilon\mathbb ED\). Divide and use \(\mathbb ED\ge L\). Optimize the right side over actions; \(G_E\) and \(q_E\) must vary together. The zero-hazard case uses its limiting value.

Claim B’s equality requires \(D=L\), zero fresh surplus, and the common benchmark assumption. “Roughly constant” payments require a measured error bound; they are not a theorem assumption.

**Required corrections and exclusions.**

False failures can restart recovery. If fresh play is honest, service is always \(s\), and every failure causes replacement, put \(r=(1-d_0)^s\). Recovery requires \(L\) consecutive successful rounds:
\[
\mathbb ED=\frac{1-r^L}{(1-r)r^L},
\]
with limit \(L\) at \(r=1\). This follows from the waiting-time recurrence for consecutive successes.

Waiting is not always worse. It preserves the old identity’s audit priority and avoids fresh-state false-failure restarts. Apply (4) separately to waiting and replacement, or solve their state-dependent control problem. Nonnegative fresh profit alone proves no dominance.

For a general benchmark \(h_*\), use (4) minus \(h_*\). Local truthful profits need not equal \(h_*\), particularly when false failures change occupation frequencies.

Allocation A ignores age directly. However, opponent availability and offers affect allocation and payment:
\[
M_j=v_jc-s_{2,j}.
\]
Holding the public offer fixed isolates effort shading. Changing claims or bids does not. D2 changes its claim after audit outcomes; the registered D2+H3 family is therefore outside the stationary theorem in general.

Define the in-band allowance by maximizing the actual surplus over \(0\le\Delta\le\tau\). It is rule-dependent. A common conservative envelope is \(s_{\max}b\tau\). Detection is not negligible throughout this interval: at \(\Delta=\tau\), \(d=1/2\). To use this allowance in (5), separately verify that every permitted beyond-band fresh action has nonpositive surplus.

Claim C follows from Lemma 2 and the payment-weighted surplus formula. If fresh surplus becomes positive, the zero-fresh-surplus bound fails; the renewal identity remains valid. Multiple fresh age groups cannot be pooled.

Finite runs require explicit initial, incomplete-cycle, and terminal accounting. \(T\gg L\) alone is insufficient when established spells are long. Apply the exact finite reward sum to these parts. Terminal full coverage requires sufficient remaining allowance; it does not follow from the reserve label.

**Paper layout:** Lemma 1, Lemma 2, the recovery calculation, then the conditional renewal theorem. Retain the terminal impossibility proposition: at the locked parameters, marginal refund deterrence is at most
\[
1.4\,\phi(3.2)/0.05<0.067<0.22\le b.
\]
Thus sufficiently small terminal shading is profitable whenever service occurs. No theorem here establishes unrestricted incentive compatibility, equilibrium, coalition resistance, or search completeness.

CHECKS:

Record by round, identity generation, age, and terminal status:

- \(S,K,U\), payment totals, audited-payment totals, quota, carry, remaining allowance, and fresh demand.
- Claims, bids, effort, \(\Delta,d,d_0\), failures, refunds, replacement charges, and profit.
- Established-spell lengths, recovery durations, fresh restarts, waiting periods, and censored cycles.
- Separate audit rates for initial established identities and replacement established identities.

Estimate \(p_z=\sum K/\sum S\), but compute hazards from the conditional distribution of \(K\), not from \(p_z\) alone. Check observed refunds, failure frequencies, cycle rewards, and durations against the formulas. Estimate in-band optima numerically and report their shading levels.

**The headline numerical explanation is currently unsupported.** A uniquely newest established identity serving six jobs receives at least five targeted audits when residual quota is 10, and six when it is 11. Thus its rate can be at least \(5/6\), not approximately 0.21. At \(d\approx1\), its failure hazard is near one. Also, the initial ten rounds can violate adequate coverage because all original identities are fresh.

The arithmetic \(1/(1+10[1-.79^6])\approx0.117\) is correct. Its applicability is unverified.

The reported optimized-gain ratios are descriptive comparisons. They are not a renewal test: attack knobs, offers, references, and possibly normalization differ across rules. Test fixed offers and actions across rules, use raw profit per calendar round, account for fresh and terminal rewards, and compare each measured numerator and denominator separately. Report paired seed uncertainty; avoid ratios with near-zero denominators.

ROBUSTNESS (final):

Use the 276-cell cut, remove eight invalid horizon/X4 cells, and add 24 audit-cost cells: **292 search cells**.

Defaults: \(\beta=.05,\rho=.2,N=10,J=50,\sigma=.05,T=200,L=10,e=0\). Every row uses B1, B2, B3, and R3. “Core” means D2, D2+H3, X4. Rows exclude duplicate defaults.

| Axis | Values | Positions | Families | Cells |
|---|---|---|---|---:|
| Budget | \(\beta=.02,.05,.10\) | Low, median, high | Core | 108 |
| Audit cost | \(\rho=.05,1\) | Median | Core | 24 |
| Scale | \((N,J)=(5,25),(20,100)\) | Median | Core | 24 |
| Load | \(N=10;\ J=25,60\) | Median | Core | 24 |
| Noise | \(\sigma=.025,.10\) | Median | Core | 24 |
| Entry cost | \(e/m=.1,1,10\); zero above | Median | Core | 36 |
| Horizon | \(T=100,400\) | Median | D2, D2+H3 | 16 |
| Timing and aging | Default | Median | X1, X2, X3, X5 | 16 |
| Fresh congestion | Sizes 1, 2, 5; synchronized/staggered for 2 and 5 | Median focal | X6 | 20 |
| **Total** | | | | **292** |

Freeze interpolated provider arrays for changed \(N\), as specified in round 1. Use the existing position-selection procedure.

Add **72 fixed diagnostic configurations**: three budgets × three audited rules × four established shading levels \(\{0,.08,.16,.24\}\) × immediate reset/wait. Use \(T=200\), median provider, claim \(q_{\max}\), fixed bid equal to truthful production cost, and honest fresh effort. These are diagnostic controls, not additional search families. Twenty development-validation seeds give **1,440 episodes**.

Predictions:

- Fresh surplus tracks coverage and audited escrow. Adequate coverage alone does not guarantee nonpositive surplus.
- Replacement targeting can suppress established surplus more than the proposed duration factor predicts.
- Higher entry costs reduce fixed-policy reset profits. A smaller R3 advantage is a testable hypothesis; optimization and waiting prevent a general monotonicity theorem.
- Increased noise raises false failures. Scale and load effects must be explained through service, payment, and coverage measurements.
- Horizon changes alter reserve pressure and boundary effects. X6 tests capacity under joint deviation.

Report violations of the measured inequalities, all positions, search spread, gain, harm, efficiency decomposition, and spend.

Retain registered search budgets, corners, compatible banks, reference selection, and preselected doubling checks. Use training seeds 1000–1004, validation 2000–2019, and separate calibration 4000–4019. Transfer frozen rule parameters with an explicit transfer label. No new horizon-aware policies.

At 16,300 episodes per search cell, the base estimate is **4,761,040 episodes**, including diagnostics, before calibration and extra checks. Legacy throughput suggests 35.6 pod-hours for search alone; a 30% allowance gives about 46.3 hours. Replace this estimate with measured pilot costs. No experiments were launched.

VERDICT on the round-1 plus round-2 package: **accept-with-caveat**. The local identity, coverage result, conditional renewal theorem, and impossibility proposition form a valid package. Reject the unconditional waiting claim and the numerical ratio explanation until their assumptions pass the stated checks.

CONFIDENCE: **0.95**.
