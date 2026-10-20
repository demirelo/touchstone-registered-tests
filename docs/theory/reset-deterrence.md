# Reset deterrence under capped sanctions: local identity, coverage, renewal bound, and a terminal impossibility

Status: post-verdict theory for the paper (exploratory programme; no registered claim depends on it). Design and proofs: Astra high, rounds 1 and 2 (`docs/theory/roster/astra-r1.md`, `astra-r2.md`), assembled and checked by the authors. Numerical checks: `scripts/check_reset_theory.py` (pre-stated in `experiments/robustness-v1.yaml`).

## 1. Setting

One provider (the focal entity) faces honest-max opponents. In each round it chooses one effort level for all its served jobs, a public claim $c \le q_{\max}$, and a bid. Job $j$ served by it pays the escrow $M_j$; under the second-score allocation of B3 and of R3 (allocation A), $M_j = v_j c - s_{2,j}$, the job value times the claim minus the second-highest score. Production costs $a + b\,e$ per served job at effort $e$. Delivery is $y_j = e + \varepsilon_j$ with $\varepsilon_j \sim N(0, \sigma^2)$ independent across jobs and of everything the rule observes before delivery. An audited job fails when $y_j < c - \tau$. A failure refunds that job's escrow and bans the serving identity for $L$ rounds; there are no fees, bonds, or hold-backs. An entity may replace its identity at once; the new identity costs the entry charge $e_{\mathrm{in}} \ge 0$ (zero in the registered market) and starts at age 0.

Shading by $\Delta \in [0, c]$ (effort $c - \Delta$ at an unchanged offer) saves $g = b\Delta$ per served job and raises the per-audit failure probability from $d_0 = \Phi(-\tau/\sigma)$ to $d = \Phi((\Delta - \tau)/\sigma)$. Because the offer is unchanged, the round's allocation and payments are unchanged.

## 2. Lemma 1: the exact local identity

Let $s$ be the focal entity's served jobs in a round, $U$ the audited subset, $K = |U|$, and condition on the state, the rival outcomes, and $U$ (all independent of the focal delivery noise). Fix a continuation policy class and let $V_U^{+}$ and $V_U^{-}$ be the best continuation values after no focal failure and after at least one focal failure; $C_U = V_U^{+} - V_U^{-}$. Then the expected profit of shading by $\Delta$ relative to truthful effort is

$$A(\Delta) = s g - \mathbb{E}\Big[(d - d_0)\sum_{j \in U} M_j + \big((1 - d_0)^K - (1 - d)^K\big)\,C_U\Big]. \qquad (1)$$

*Proof.* Shading saves $sg$. Each audited escrow is refunded with probability $d$ instead of $d_0$. Given $K$, independence gives the probabilities $1 - (1-d)^K$ and $1 - (1-d_0)^K$ of at least one failure; the continuation loss is incurred once, however many jobs fail. Taking expectations over $U$ gives (1). $\square$

**Corollary 1 (uniform auditing with free replacement).** If allocation, prices, and audit selection do not depend on identity age (B2 and B3), replacement is immediate, and $e_{\mathrm{in}} = 0$, then the best continuation after a failure replaces the identity and reaches the same distribution of future play as after no failure (the ban stays with the retired identity). Hence $C_U = 0$ and
$$A(\Delta) = s g - (d - d_0)\,\mathbb{E}\sum_{j \in U} M_j,$$
which does not depend on the ban length $L$. With a per-job audit probability $p$ independent of payments, $A(\Delta) = s\,[\,g - p(d - d_0)\bar M\,]$: shading pays whenever $g > p(d - d_0)\bar M$, and lengthening a bypassable ban cannot change this. $\square$

## 3. Lemma 2: newcomer coverage and overload

Let $F_t$ be the served jobs in round $t$ of identities whose first offer was fewer than $L$ rounds earlier, and $k_t$ R3's audit count. R3 audits every such job when $k_t \ge F_t$ (its priority phase lists all fresh jobs first). Under overload, age groups are served newest first. For the focal identity's age group, let $H$ be the fresh jobs of strictly newer identities and $n$ the jobs of its group; the group receives $k' = \min\{n, \max(0, k_t - H)\}$ audits, and with $s$ focal jobs in the group,
$$K \sim \mathrm{Hypergeometric}(n, s, k'), \qquad q = 1 - \mathbb{E}\big[(1 - d)^K\big]. \qquad (2)$$

*Proof.* The priority list is ordered by age group, newest first; within a group, independent continuous audit keys make the selected set uniform among the group's jobs; delivery noise is independent of the selection. $\square$

Fresh groups cannot be pooled into one hypergeometric draw: an older fresh group can receive zero audits.

**Lemma 2b (targeting after the fresh window).** In R3's residual phase with newest-first targeting (T1), $\lceil r/2 \rceil$ of the $r = k_t - F_t$ remaining audits go to established identities in decreasing order of first-offer round. A replacement identity that has left its fresh window is newer than every initial identity; if it is the newest established identity with $s$ served jobs, it receives at least $\min(s, \lceil r/2 \rceil)$ audits. At the headline market ($r = 10$ or $11$ before carry, $s = 6$) that is at least 5 of 6 jobs. Replacement therefore buys no low-audit established state while no newer identity exists.

## 4. Recovery with false failures

Suppose fresh play is honest, every fresh job is audited (adequate coverage), and every failure triggers replacement. A fresh round passes with probability $r = (1 - d_0)^s$, and recovery requires $L$ consecutive passing rounds. The expected recovery duration is
$$\mathbb{E}D = \frac{1 - r^L}{(1 - r)\,r^L}, \qquad \lim_{r \to 1}\mathbb{E}D = L. \qquad (3)$$
*Proof.* The waiting time for $L$ consecutive successes in independent trials with success probability $r$ satisfies the standard first-step recurrence, whose solution is (3). $\square$ At $\tau = 0.16$, $\sigma = 0.05$, $s = 6$, $L = 10$: $d_0 = 6.9 \times 10^{-4}$, $r = 0.9959$, $\mathbb{E}D \approx 10.2$.

## 5. Theorem: the conditional renewal bound

Consider immediate-replacement policies with a fixed established-state action and separately specified fresh-state actions, such that play decomposes into stationary, independent cycles, each an established spell followed by a recovery. Assume established rounds have constant conditional expected profit $r_E$ and failure hazard $q_E > 0$ given survival; the recovery has duration $D \ge L$ with finite mean, total profit $R_F$ before entry charges, and $N_R$ replacements; delivery noise is independent; expected cycle rewards are finite. Then the long-run profit per round is

$$\bar\Pi = \frac{r_E / q_E + \mathbb{E}R_F - e_{\mathrm{in}}\,\mathbb{E}N_R}{1/q_E + \mathbb{E}D}. \qquad (4)$$

*Proof.* The spell length $N$ is geometric with mean $1/q_E$. Since survival to round $t$ is determined by earlier rounds, $\mathbb{E}\sum_{t \le N} R_t = \sum_t \Pr(N \ge t)\,\mathbb{E}[R_t \mid N \ge t] = r_E\,\mathbb{E}N = r_E/q_E$, even though the last round's reward and failure may be correlated. Add the recovery's rewards and entry charges and divide the expected cycle reward by the expected cycle length (renewal-reward theorem; standard, citation to be verified against a primary source before submission). $\square$

**Corollary 2 (surplus bound).** Suppose further that same-offer truthful play earns a common expected rate $h$ in both states, that $h$ is the benchmark, and that every permitted fresh action has conditional surplus at most $\epsilon \ge 0$ over $h$. Write $G_E = r_E - h$ for the established surplus. With $e_{\mathrm{in}} = 0$,
$$\bar\Pi - h \;\le\; \epsilon + \frac{(G_E - \epsilon)_+}{1 + q_E L}. \qquad (5)$$
*Proof.* A cycle's surplus is at most $G_E/q_E + \epsilon\,\mathbb{E}D$; divide by $1/q_E + \mathbb{E}D$ and use $\mathbb{E}D \ge L$. $G_E$ and $q_E$ must be optimised jointly over the established action. $\square$

Under Corollary 1 the same calculation gives a cycle with no recovery (or one that earns the established rate), so the uniform rule's long-run surplus is the one-round surplus $G_U = s[\,g - p(d - d_0)\bar M\,]$: the factor $1/(1 + q_E L)$ is what newcomer-first auditing adds, and Lemma 2b says that under T1 the established hazard $q_E$ of a replacement identity is itself high.

Equality in (5) holds when the recovery lasts exactly $L$ rounds ($D = L$), every fresh round earns exactly $h + \epsilon$, and the established action attains $G_E$ with hazard $q_E$; fresh surplus need not be zero (for example $G_E = 2$, $\epsilon = 1$, $q_E = 1$, $D = L = 10$ gives $12/11$ on both sides). In the special case $\epsilon = 0$ the bound reads $(G_E)_+/(1 + q_E L)$ and equality needs honest fresh play at the benchmark rate. Payments that are only roughly constant across states need a measured error bound; they are not an assumption of the theorem.

## 6. Proposition: terminal shading is always profitable at the locked parameters

In any round with zero continuation loss (the last round; and every round under Corollary 1), small shading at an unchanged offer is profitable whenever the focal entity is served. *Proof.* From (1) with $C_U = 0$, $A'(0) = s b - \Phi'(-\tau/\sigma)\,\sigma^{-1}\,\mathbb{E}\sum_{j \in U} M_j \ge s\,(b - v_{\max}\,\phi(\tau/\sigma)/\sigma)$, since $M_j \le v_j c \le v_{\max}$. At the locked parameters $v_{\max} = 1.4$, $\tau/\sigma = 3.2$, $\phi(3.2)/0.05 = 0.0477$, so the subtracted term is below $0.067$, while every provider has $b \ge 0.22$. Hence $A'(0) > 0$. $\square$ Exact truthfulness is therefore impossible under every studied rule, R3's full terminal audit included; the tolerance creates an in-band allowance, and the paper's claims are bounded-gain claims. Detection is not negligible across the band: at $\Delta = \tau$, $d = 1/2$.

## 7. What the package does not cover

Changes of claim or bid alter allocation, second scores, and payments, so they fall outside the same-offer comparison; they are measured through the registered decomposition of the gain into inflation and selection terms. D2 adapts its claim after audit outcomes, so the registered D2+H3 family is outside the stationary theorem. Waiting out a ban is not always worse than replacing (it keeps the old identity's place in the targeting order and avoids fresh-state restarts); the two plans are compared by applying (4) to each. Coalitions (the exploratory X6 family), equilibrium of the ten-provider game, and completeness of the search are not covered. Finite runs need explicit initial, incomplete-cycle, and terminal accounting; the first $L$ rounds violate adequate coverage because every initial identity is fresh.

## 8. Checks (pre-stated; results in `docs/theory/checks-<date>.md`)

Fixed configurations: $\beta \in \{0.02, 0.05, 0.10\}$, rules B2, B3, R3, established shading $\Delta \in \{0, 0.08, 0.16, 0.24\}$, immediate replacement or waiting, $T = 200$, median provider, claim $q_{\max}$, bid equal to the truthful production cost, honest fresh effort; 20 dev-val seeds (72 configurations, 1,440 episodes). Per round: served and audited counts, audited and total payments, fresh demand, age, generation, terminal status, failures, refunds, entry charges, profit. Per configuration: payment-weighted surplus by state; failure hazards from the empirical distribution of $K$ (not the pooled rate); spell and recovery lengths with censoring; the prediction (4) and the bound (5) against the measured long-run profit per round with paired seed uncertainty; the rates of initial versus replacement established identities (Lemma 2b). The optimised-gain ratios between rules (for example B2 0.570 against R3 0.071 under D2+H3) are descriptive and are not a test of (5): attack knobs, offers, and references differ by rule.
