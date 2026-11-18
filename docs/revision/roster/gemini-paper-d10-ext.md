```python
# Check relationship between Table 9 columns and p.16 numbers at p=0.05
# In Table 9 at p=0.05:
# young honest jobs share = 0.391 (R3), 0.385 (C*), 0.383 (B3)
# audits to young honest (share of all audits) = 0.823 (R3), 0.523 (C*), 0.383 (B3)
# established honest audited = 0.078 (R3), 0.177 (C*), 0.250 (B3)
# Notice: overall audit budget is rho=0.2, beta=0.05 -> allowance = (0.05/0.2)*n_FB = 0.25 * n_FB (25% of jobs audited!)
# If 25% of all jobs are audited:
# For R3: (0.823 * 0.25) / 0.391 = 0.20575 / 0.391 = 0.5262... wait, why is p.16 0.571?
print("R3:", (0.823 * 0.25) / 0.391)
print("C*:", (0.523 * 0.25) / 0.385)
print("B3:", (0.383 * 0.25) / 0.383)


```

```text
R3: 0.5262148337595908
C*: 0.33961038961038964
B3: 0.25


```

```python
# Let's check Table 10 & Table 11 (Q2 factorial contrasts) vs Section 8 / Appendix A text
# Appendix A (p. 19): "the main effects on the gain are -0.083 for the priority phase P and -0.095 for newest-first residual targeting G, both reductions, and 0.004 for pacing S, a small increase (X7-SC: 0.005)."
# Table 10 (p. 20): P = -0.083, G = -0.095, S = 0.004.
# Table 11 (p. 21): P = -0.085, G = -0.094, S = 0.005.
# Appendix A (p. 19): "the PG factorial contrast, half the difference between G's conditional effects, is 0.082; G changes the gain by -0.177 without the priority phase and by only -0.014 with it, and the priority phase changes it by only -0.001 once G is in place"
# Check math: 0.5 * ((-0.014) - (-0.177)) = 0.5 * 0.163 = 0.0815 -> rounds to 0.082!
print("PG check:", 0.5 * (-0.014 - (-0.177)))

# Check Table 12 (p. 22) vs Table 13 (p. 22) and Appendix A text (p. 21)
# Look at Table 13 (p. 22) at w = 0.0:
# F111 + H4: w=0.0 -> 0.0685 / 0.998
# F111 + D2+H3: w=0.0 -> 0.0486 / 0.998
# C* + H4: w=0.0 -> 0.0891 / 0.997
# C* + D2+H3: w=0.0 -> 0.0872 / 0.997
# Wait! Look at Table 13: for F111 + D2+H3 at w=0.0, gain is 0.0486!
# And look at Table 22 (p. 28) Q3-a for headline F111: "headline F111 0.0000" where Q3-a is gain(X7-SC) - gain(D2+H3) = 0 -> so gain(X7-SC) = gain(D2+H3) = 0.0486 at headline!
# And look at Table 22 Q3-b: "gain(H4) - gain(X7-SC), F111 (headline): at most 0.05 ... headline F111 0.0200"
# Check: 0.0685 - 0.0486 = 0.0199 ~ 0.0200! Consistent!

# Check Table 15 (p. 23) vs Table 12 (p. 22):
# Table 15: F000 WO: eff 0.839, gain 0.254. Table 12: F000 WO eff 0.839, Est. gain 0.254, Mixed eff 0.8387.
# Table 15: F111 WO: eff 0.840, gain -0.094. Table 12: F111 WO eff 0.840.
# Table 15: F111 W1: eff 0.997, gain 0.000. Table 12: F111 W1 eff 0.997.
# Table 15: C* WO: eff 0.840, gain -0.094. Table 12: C* WO eff 0.840.
# Table 15: C* W1: eff 0.997, gain 0.000. Table 12: C* W1 eff 0.997.

# Let's check Table 12 linear combinations!
# F111 + H4: w = 0.4195.
# Pure H4 (w=0): gain = 0.0685, eff = 0.998 (from Table 13)
# Pure WO (w=1): gain = -0.094, eff = 0.84033 (from Table 15 & Table 22)
w = 0.4195
g_mix = (1 - w)*0.0685 + w*(-0.094)
eff_mix = (1 - w)*0.998 + w*0.84033
print(f"F111+H4 w={w}: g={g_mix:.6f} (Table 12: 0.000374), eff={eff_mix:.4f} (Table 12: 0.9320)")

w2 = 0.3390
g_mix2 = (1 - w2)*0.0486 + w2*(-0.094)
eff_mix2 = (1 - w2)*0.998 + w2*0.84033
print(f"F111+D2+H3 w={w2}: g={g_mix2:.6f} (Table 12: 0.000253), eff={eff_mix2:.4f} (Table 12: 0.9445)")


```

```text
PG check: 0.08149999999999999
F111+H4 w=0.4195: g=0.000331 (Table 12: 0.000374), eff=0.9319 (Table 12: 0.9320)
F111+D2+H3 w=0.339: g=0.000259 (Table 12: 0.000253), eff=0.9445 (Table 12: 0.9445)


```

```python
# Check Table 8 (p. 17): change of each market's d = C* - R3 and q = B3 - R3 from its no-churn value!
# Without churn (p=0):
# Frozen: d0 = 0.021 (or 0.0209 from Table 18), q0 = 0.173 (mean of Table 4: (0.0414+0.4691+0.0568+0.2626+0.1834+0.0271)/6)
q0_frozen = (0.0414 + 0.4691 + 0.0568 + 0.2626 + 0.1834 + 0.0271) / 6
print("q0_frozen:", round(q0_frozen, 4))

# In Table 6 (frozen):
# p=0.01: d = 0.001, q = 0.175 -> d - d0 = 0.001 - 0.0209 = -0.0199 (~ -0.019 in Table 8!), q - q0 = 0.175 - 0.1734 = +0.0016 (~ 0.001 in Table 8!)
# p=0.02: d = -0.020, q = 0.119 -> d - d0 = -0.020 - 0.0209 = -0.0409 (~ -0.041 in Table 8!), q - q0 = 0.119 - 0.1734 = -0.0544 (~ -0.055 in Table 8!)
# p=0.03: d = -0.090, q = 0.068 -> d - d0 = -0.090 - 0.0209 = -0.1109 (~ -0.111 in Table 8!), q - q0 = 0.068 - 0.1734 = -0.1054 (~ -0.106 in Table 8!)
# p=0.05: d = -0.173, q = -0.052 -> d - d0 = -0.173 - 0.0209 = -0.1939 (~ -0.194 in Table 8!), q - q0 = -0.052 - 0.1734 = -0.2254 (~ -0.225 in Table 8!)
print("All Table 8 means match Table 6 differences to rounding!")


```

```text
q0_frozen: 0.1734
All Table 8 means match Table 6 differences to rounding!


```

```python
import numpy as np
from scipy import stats

# Check Table 24 (p. 29) C* - R3, D2+H3 Frozen: 0.021, 0.053, 0.029, -0.038, 0.044, 0.016
x = np.array([0.021, 0.053, 0.029, -0.038, 0.044, 0.016])
mean = x.mean()
se = x.std(ddof=1) / np.sqrt(len(x))
ci = stats.t.interval(0.95, df=5, loc=mean, scale=se)
print(f"Section 8 p.11 frozen D2+H3 t-CI: mean={mean:.3f}, ci=[{ci[0]:.3f}, {ci[1]:.3f}] (paper: [-0.013, 0.054])")

# Check doubled D2+H3: 0.027, 0.055, 0.038, 0.015, 0.026, 0.016
x_d = np.array([0.027, 0.055, 0.038, 0.015, 0.026, 0.016])
mean_d = x_d.mean()
se_d = x_d.std(ddof=1) / np.sqrt(len(x_d))
ci_d = stats.t.interval(0.95, df=5, loc=mean_d, scale=se_d)
print(f"Section 8 p.11 doubled D2+H3 t-CI: mean={mean_d:.3f}, ci=[{ci_d[0]:.3f}, {ci_d[1]:.3f}] (paper: [0.014, 0.045])")

# Check Table 5 / Section 9 G(D2) frozen: -0.023, -0.002, 0.011, 0.002, 0.012, -0.055
g_d2 = np.array([-0.023, -0.002, 0.011, 0.002, 0.012, -0.055])
ci_gd2 = stats.t.interval(0.95, df=5, loc=g_d2.mean(), scale=g_d2.std(ddof=1)/np.sqrt(6))
print(f"Section 9 p.13 G(D2) t-CI: mean={g_d2.mean():.3f}, ci=[{ci_gd2[0]:.3f}, {ci_gd2[1]:.3f}] (paper: [-0.036, 0.018])")


```

```text
Section 8 p.11 frozen D2+H3 t-CI: mean=0.021, ci=[-0.013, 0.054] (paper: [-0.013, 0.054])
Section 8 p.11 doubled D2+H3 t-CI: mean=0.029, ci=[0.014, 0.045] (paper: [0.014, 0.045])
Section 9 p.13 G(D2) t-CI: mean=-0.009, ci=[-0.036, 0.018] (paper: [-0.036, 0.018])


```

```python
import numpy as np
from scipy.stats import norm

# First test / headline market parameters (Appendix E, p. 33) and fixed pair (Section 4, p. 6):
# v_max = 1.4, sigma = 0.05, tau = 0.16
# Wait: what were tau in the first test vs second test?
# At tau = 0.16, sigma = 0.05, v_max = 1.4:
rhs_016 = 1.4 * norm.pdf(0.16 / 0.05) / 0.05
print("At tau=0.16, sigma=0.05, v_max=1.4: RHS =", rhs_016)
# Wait! What tau gave RHS < 0.067? Let's solve 1.4 * norm.pdf(tau / 0.05) / 0.05 = 0.067
for tau in np.linspace(0.10, 0.20, 21):
    val = 1.4 * norm.pdf(tau / 0.05) / 0.05
    if 0.04 < val < 0.09:
        print(f"tau={tau:.3f} -> RHS={val:.5f}")


```

```text
At tau=0.16, sigma=0.05, v_max=1.4: RHS = 0.06675446964101564
tau=0.160 -> RHS=0.06675
tau=0.165 -> RHS=0.04823


```

### 1. Model ID

Gemini

---

### 2. Summary Verdict

This paper investigates a clean, well-motivated mechanism-design question—how a buyer with a hard ex-post audit budget should target quality checks when sanctioned providers can immediately re-enter under free new identities—and sets a rare standard for methodological transparency by reporting two Bitcoin-timestamped, staged-registration simulation studies alongside failed predictions, configuration deviations, and post-report exploratory follow-ups. Its empirical findings are internally coherent and honestly bounded: without honest identity turnover, age-ranked auditing (`R3`) lowers measured attacker gain relative to uniform auditing (`B3`) on all six fresh markets (passing the registered joint gain-and-efficiency criterion on 3 of 6, all search-flagged) and is pooled-equivalent within $\pm 0.05$ to one development-selected verified-history rule (`C*`), whereas exploratory follow-ups indicate that this advantage relies on attacker replacement (Section 9) and reverses on the sampled markets when honest providers also churn at rates $p \ge 0.03$ per round (Section 10). However, the paper's evidentiary reach is constrained by incomplete attack searches (21 of 98 main-test and 21 of 72 churn doubling checks flagged), evaluation of only a single verified-history comparator under churn, wide market-level confidence intervals across $n=6$ markets that include zero in 15 of 16 churn cells, unverified renewal assumptions in Theorem 1, and dense audit-log prose that obscures the economic core. **Scores (out of 5): WEIS 2027: 3.5; AAMAS (main track): 3.0; ACM EC: 2.5.**

---

### 3. Main Claims Table

| Claim (in reviewer's words) | Support | Evidence (page, table/figure) | Comment |
| --- | --- | --- | --- |
| **1. Free identity replacement eliminates the continuation cost of bans under uniform audits (Corollary 1).** Under `B2`/`B3` with refund-and-ban enforcement, no bonds, free immediate re-entry ($e=0$), and honest rivals indifferent to focal identity labels, $C_U = 0$ regardless of ban length. | **Supported** | Sec. 5 (p. 7); App. F (p. 34) | Proof is algebraically valid within the stated model assumptions. Does not cover rules with bonds, history-dependent priority (`R3`, `C*`), or positive entry costs. |
| **2. Per-round coverage for `R3` (Lemma 2), inevitability of small-shading profitability in zero-continuation-loss rounds (Proposition 1), and a conditional renewal bound (Theorem 1).** | **Partly supported** | Sec. 5 (p. 7); App. E (p. 33); App. F (pp. 33–35) | Lemma 2 and Proposition 1 are proved for their narrow single-round conditions (though Prop. 1's text says $b > 0.22$ while App. E p. 33 gives $b_{10} = 0.22$). Theorem 1's i.i.d. renewal assumptions are explicitly unverified for the finite-horizon adaptive simulation (p. 7, p. 34). |
| **3. Registered Q4: Without honest churn, `R3` reduces measured `D2+H3` attacker gain relative to `B3` on every sampled market, passing the joint gain-and-efficiency test on 3 of 6 fresh markets.** | **Partly supported** | Abstract (p. 1); Sec. 8 (pp. 10, 12); Table 4 (p. 12); Fig. 4, Table 19 (p. 26); Table 22 (p. 28) | Supported as a finding about the *prescribed search procedure* on these 6 markets (`B3 - R3` ranges from `0.027` to `0.469`; R3 efficiency $\ge 0.985$), and invariant to the 1-ULP config fix (Table 19). However, all 3 passing markets (`fresh1`, `fresh3`, `fresh4`) carry direct or inherited doubling-check flags (Table 4), and the registered prediction of $\ge 5$ passes failed (`Q4-a`, Table 22). |
| **4. Registered Q1: Without churn, `R3` and `C*` are pooled-equivalent within $\pm 0.05$ with `R3` directionally lower (`0.021` under `D2+H3`, `0.024` under `X7-SC`), though sensitive to comparator and market.** | **Partly supported** | Sec. 8 (pp. 10–12); Table 3 (p. 12); Table 14 (p. 23); Fig. 3 (p. 24); Table 18 (p. 25); Table 24 (p. 29); Table 28 (p. 30) | Holds on the 6 fixed markets for `C*`, but `X7-SC` repeats `D2+H3` in 10 of 12 Q1 cells (p. 11), `D2+H3` relies on flagged cells, the 6-market `t`-interval `[-0.013, 0.054]` spans zero and the margin (p. 11), and the development runner-up `C-thr(12)` yields `-0.010` pooled under frozen `D2+H3` (Table 28). |
| **5. Registered Q2 & Q3: Priority (`P`) and newest-first residual targeting (`G`) act as substitutes; pacing (`S`) collapses at high audit cost ($\rho=1$); unconstrained welfare attacks (`W0`) cut gross efficiency to `~0.840`, and `W1` misses lower-efficiency episode mixtures.** | **Supported** | Sec. 1 (p. 3); App. A (pp. 19–22); Fig. 2 (p. 20); Tables 10–17 (pp. 20–25) | Main effects `P = -0.083`, `G = -0.095`, `PG = 0.082` (Table 10) and `W0` efficiency `0.839–0.840` (Table 15) are well supported. Appropriately qualified: fresh-market factorial cells outside Q1/Q4 had no doubling checks (p. 21), and lottery weights (Table 12) were selected in-sample on evaluation seeds. |
| **6. Exploratory Section 9: Most of `R3`'s measured advantage over `B3` disappears when attacker identity replacement is disabled.** | **Partly supported** | Sec. 9 (pp. 12–13); Table 5 (p. 14); App. A (pp. 24–25) | Within the `D2` family at fixed parameters, pooled `B3 - R3` drops from `0.173` (`D2+H3`) to `-0.009` (`D2`; `-0.004` doubled), with 6-market `t`-interval `[-0.036, 0.018]` (p. 13). Limited to one attack family, 3 of 18 `D2` checks flagged (p. 25), and 17 of 18 frozen truthful references still replace identities after false failures (checked only via a Mac additive approximation $\le 0.009$, p. 25). |
| **7. Exploratory Section 10: Under honest identity churn ($p \in \{0.01, 0.02, 0.03, 0.05\}$), `R3`'s audit share on the attacker falls from `0.366` to `0.042` and its measured advantage over `C*` and `B3` reverses on the sampled markets.** | **Partly supported** | Abstract (p. 1); Fig. 1 (p. 3); Sec. 10 (pp. 13–17); Tables 6–9 (pp. 16–17) | Pooled `C* - R3` falls to `-0.090` (`p=0.03`) and `-0.173` (`p=0.05`), and `B3 - R3` reaches `-0.052` (`-0.033` doubled) at `p=0.05` (Table 6). However, 15 of 16 6-market `t`-intervals include zero (Table 7), 21 of 72 searches are flagged incomplete (p. 15), reference menus were not regenerated under churn (p. 15), only `C*` was tested under churn (p. 16), and attacker strategy shifts (halting replacement on 3 of 6 markets under `R3`, Table 9) confound pure audit diversion. |

---

### 4. Problems Ranked by Severity

#### Problem 1 (High): Unresolved search incompleteness and unregenerated references in the flagship churn study (Section 10)

* **Quoted sentence and page**:
> "13 of the 36 doubling checks at $p=0.01$ and 0.05 and 8 of the 36 at $p=0.02$ and 0.03 are flagged incomplete; the largest flagged change is 0.088. Reselection within each rule's frozen reference menu under churn gives a nonzero training-set reference-score change in 32 of the 72 cells, with a largest absolute change of about 0.009; this diagnostic does not bound the change in held-out gain, and the menus themselves were not regenerated." (Section 10, p. 15)


* **Why it is a problem**:
* *What the paper says*: 21 of the 72 `D2+H3` churn cells fail the doubling check (shifts up to `0.088`, which is larger than the entire `B3 - R3` reversal of `-0.052` frozen / `-0.033` doubled at $p=0.05$ in Table 6, p. 16), and the truthful reference policies were frozen from the no-churn regime rather than re-searched under churn.
* *Reviewer reasoning*: Because attacker gain $g = (\pi^A - \pi^T)/(S^*/N)$ is the difference of two searched quantities (Section 3, p. 5), asymmetric search convergence across rules (`B3`, `R3`, `C*`) or under-optimised truthful references under churn can shift contrasts by amounts comparable to the estimated reversal at $p=0.05$. In particular, the paper notes on p. 14 that the frozen `B3 - R3` reversal at $p=0.05$ (`-0.052`) depends on one flagged cell (under doubling, `B3 - R3` shrinks by 37% to `-0.033`, Table 6 p. 16).
* *What cannot be checked without records*: Without the raw CMA-ES trajectories and reference-menu candidates, a reader cannot tell whether further search restarts would widen or narrow the `p=0.05` `B3 - R3` gap or alter the `p=0.01` `C* - R3` sign.


* **Exact fix**: **`needs new runs`** — Run continued CMA-ES restarts on the 21 flagged churn cells until incremental gains fall below `0.005`, and regenerate the truthful reference menus under churn (at least at $p=0.01$ and $0.05$) to verify that frozen no-churn references do not bias `g(R3)` upward relative to `g(C*)` and `g(B3)`.

#### Problem 2 (High): Generalising from a single efficiency-selected comparator (`C*`) to verified-history targeting, especially under churn

* **Quoted sentence and page**:
> "Only one verified-history comparator, $C^{*}$, was run under churn; the runner-up comparator of Section 8 was evaluated without churn only, so this section does not show that verified-history targeting in general is robust to churn." (Section 10, p. 16)


* **Why it is a problem**:
* *What the paper says*: `C* = C-mem(6, 20)` was chosen in development on a composite objective decided at every configuration by gross efficiency rather than attacker gain (Section 4, p. 6; Table 30, p. 34), while the development runner-up `C-thr(12)` left a *lower* attacker gain than `C*` in development (`0.076` vs `0.097` at headline; `0.018` vs `0.038` at `dev0`, Table 30 p. 34) and beats `R3` in pooled point estimate without churn (`-0.010`, Table 28 p. 30). Yet `C-thr(12)` was never run in Section 10.
* *Reviewer reasoning*: `C-mem(6, 20)` forgets passes older than $M=20$ rounds, whereas `C-thr(12)` retains cumulative passes until failure. Under honest churn, an honest provider's credibility resets upon replacement in *both* rules, while an attacker that stops replacing (which occurs on 3 of 6 markets under `R3` at $p=0.05$, Table 9 p. 17) faces very different long-run audit rates under a sliding window (`C-mem`) versus a permanent threshold (`C-thr`). Testing only `C*` leaves open whether threshold-based history rules outperform or underperform `C*` under churn.


* **Exact fix**: **`needs new runs`** — Evaluate `C-thr(12)` (and ideally `C-boinc`) across the four churn rates $p \in \{0.01, 0.02, 0.03, 0.05\}$ on the six fresh markets alongside `C*`.

#### Problem 3 (Medium-High): Over-compressed causal narrative for the churn reversal in the Abstract and Conclusion

* **Quoted sentence and page**:
> "R3's audits then move to honest newcomers: with the frozen searches, the share of the attacker's jobs it audits falls from 0.366 to 0.042 between churn rates of $p=0.01$ and 0.05 per round, and at $p=0.03$ and 0.05 both contrasts are lower than without churn on every sampled market." (Abstract, p. 1; similar phrasing in Conclusion, p. 18)


* **Why it is a problem**:
* *What the paper says*: In Section 10 (p. 15), the authors explicitly caution that *"Audit share alone does not determine gain: R3's audit rate on the attacker falls below B3's between $p=0.01$ and 0.02, while the pooled B3 minus R3 gap stays positive through 0.03. The diagnostics describe the setting; they do not isolate the cause, because churn also resets histories, ends bans, and changes the selected attacks."* Indeed, Table 9 (p. 17) shows that under `R3` at $p=0.05$, the selected attacker *never replaces its identity* on 3 of 6 markets (getting audited at `0.012–0.015`, p. 15), whereas on the other 3 markets it replaces (getting audited at `0.041–0.095`).
* *Reviewer reasoning*: In the Abstract (p. 1) and Conclusion (p. 18), omitting the behavioural regime shift (the attacker abandoning identity replacement on half the markets once established identities are shielded by honest newcomers) makes the mechanism sound like passive dilution of audits on a replacing attacker, which the experimental design does not isolate. Also, the Abstract reports $p=0.05$ values for both contrasts without noting that `C* - R3` and `B3 - R3` diverge sharply at $p=0.03$ (`-0.090` vs `+0.068`, Table 6 p. 16).


* **Exact fix**: **`text only`** — Revise the Abstract (p. 1) and Conclusion (p. 18) to state that honest churn both diverts `R3`'s audits to honest newcomers and induces the attacker to stop replacing on half the markets (with the design not isolating individual channels), and explicitly distinguish the $p=0.03$ crossover for `C* - R3` from the $p=0.05$ crossover for `B3 - R3`.

#### Problem 4 (Medium): Unlabelled exploratory result embedded inside the registered-tests sentence of the Abstract

* **Quoted sentence and page**:
> "In two registered simulation tests, the second locked before six fresh markets were drawn from a Bitcoin block hash, we compare R3 at matched budget and sanctions with uniform audits (B3) and a verified-history comparator, $C^{*}$ Without honest identity turnover, R3 lowers the attacker's measured gain relative to B3 on every fresh market (the registered replication passes on 3 of six), and R3 and $C^{*}$ are "equivalent, direction R3 lower" within a pre-set margin ( $C^{*}$ minus R3: 0.021); a second verified-history comparator, evaluated without churn, shows no consistent direction." (Abstract, p. 1)


* **Why it is a problem**:
* *What the paper says*: The second verified-history comparator (`C-thr(12)`) is introduced in Section 8 (p. 11) and Table 28 (p. 30) explicitly as an *"exploratory follow-up after the report"*.
* *Reviewer reasoning*: Placing `"a second verified-history comparator, evaluated without churn, shows no consistent direction"` inside the sentence summarizing the two registered tests—and *before* the next sentence starting `"Exploratory follow-ups after the report..."`—blurs the strict registered/exploratory boundary that the paper otherwise maintains well (note also the missing period after `$C^{*}$` in line 7 of the Abstract, p. 1). Elsewhere (Sections 8–12, pp. 10–18, and Appendix A, pp. 19–25), exploratory analyses are consistently labelled.


* **Exact fix**: **`text only`** — Fix the missing period after `$C^{*}$` on p. 1, move `"a second verified-history comparator, evaluated without churn, shows no consistent direction"` into the `"Exploratory follow-ups after the report..."` sentence, and label it exploratory.

#### Problem 5 (Medium): Internal interval/metric mismatches across tables and text

* **Quoted sentences and pages**:
1. Table 3 (p. 12): `D2+H3 | 0.021 | [0.020, 0.022]` vs. Table 6 (p. 16): `frozen | 0 (registered) | ... | d = C*-R3: 0.021 [0.020, 0.021]`.
2. Section 10 (p. 16): *"the audited share of honest replacements in their first ten rounds higher under R3 than under $C^{*}$ and B3 at 0.05, 0.571 against 0.356 and 0.250 ("met")"* vs. Table 9 (p. 17) at $p=0.05$: `young honest jobs` (`0.391`, `0.385`, `0.383`) and `audits to young honest` (`0.823`, `0.523`, `0.383`).
3. Section 9 (p. 13): *"The share of the gap that disappears without replacement, $S=1-G(D2)/G(D2+H3)$, is 1.053 (doubled searches: 1.022)."* vs. Table 5 (p. 14): `S | 1.05 [1.04, 1.06] | 1.02 [1.01, 1.03]`.


* **Why it is a problem**:
* *What the paper says & reviewer computation*:
1. Table 3 (p. 12) and Table 6 (p. 16, row `p = 0 (registered)`) report the exact same point estimate (`0.021`) on the exact same no-churn evaluation seeds, but display different upper bounds (`0.022` vs `0.021`) because Table 3 uses calibrated Bonferroni intervals ($\kappa = 0.5$, Appendix C p. 32) while Table 6 uses uncalibrated 95% percentile bootstrap intervals, without alerting the reader in Table 6's caption.
2. In Table 9 (p. 17), dividing `audits to young honest` by `young honest jobs` (at total audit rate $\beta/\rho = 0.25$, Section 3 p. 5) yields `0.526` for `R3` and `0.340` for `C*` (reviewer computation), whereas p. 16 reports `0.571` and `0.356` because p. 16 excludes initial round-1 identities (age $<10$ in rounds 1–10) and counts only post-start honest replacements—a quantity never defined or tabulated in Table 9.
3. Rounding precision differs between text (`1.053`, `1.022` on p. 13) and Table 5 (`1.05`, `1.02` on p. 14). Also, minor typesetting/OCR defects appear in the main text (`"of ther remaining audits"` on p. 6; `"90.05(R3)"` and `"90.02 (R3)"` for $g_{0.05}(R3)$ and $g_{0.02}(R3)$ on p. 16).




* **Exact fix**: **`text only`** — Note in Table 6's caption (p. 16) that the `p = 0` interval is uncalibrated 95% percentile bootstrap (unlike Table 3's calibrated Bonferroni interval); define the post-start replacement audit rate (`0.571` vs `0.356`) explicitly on p. 16; harmonize decimal precision in Table 5 (p. 14); and fix the typos on pp. 6 and 16.

#### Problem 6 (Medium): Truthful references that replace identities in Section 9 and additive Mac-vs-Linux sensitivity check

* **Quoted sentence and page**:
> "The truthful references can: 17 of the 18 frozen references replace an identity on the evaluation seeds. Each rule's reference cancels in I but not in G. As a sensitivity calculation, we measured on the Mac each frozen reference's profit with replacement and with replacement disabled, and added the signed difference to the stored Linux gains; the adjustment can increase or decrease a gain, and it is not a re-evaluation with non-replacing references." (Appendix A, pp. 24–25)


* **Why it is a problem**:
* *What the paper says*: Section 9 claims to measure what happens when identity replacement is disabled, yet in `G(D2) = g_{B3}(D2) - g_{R3}(D2)`, the subtracted truthful references $\pi^T$ still use identity replacement after Gaussian false audit failures in 17 of 18 cells. Moreover, the sensitivity check was run on a different architecture (Mac arm64, which differs by up to `0.007` in mean reference profit from stored Linux x86 results, p. 25) and applied additively rather than re-evaluating on the target platform.
* *Reviewer reasoning*: While `0.009` is small relative to `G(D2+H3) = 0.173`, it is of the exact same order of magnitude as `G(D2) = -0.009` (frozen) and `-0.004` (doubled) (Table 5, p. 14), meaning the sign of `G(D2)` is directly sensitive to whether truthful references are allowed to replace after false failures.


* **Exact fix**: **`needs analysis of existing results`** (or minor re-evaluation on the Linux environment) — Report the exact Linux evaluation of `G(D2)` using non-replacing truthful references in Table 5 (p. 14) rather than relying on a cross-platform additive proxy.

#### Problem 7 (Low-Medium): Missing dynamic-monitoring and cold-start literature in Section 2

* **Quoted sentence and page**:
> "Tournament-based dynamic targeting allocates a fixed inspection capacity by relative compliance rank and compares it with standards-based and random inspection [16]; R3 ranks by identity age instead. Our rules are searched and tuned heuristics, not optima of these models." (Section 2, p. 4)


* **Why it is a problem**:
* *Reviewer reasoning*: Section 2 covers classical spot-checking [28, 29], cheap pseudonyms [13, 11], and audit games [6, 8], but omits three directly relevant papers on dynamic inspection timing, reputation memory windows, and newcomer cold-start monitoring:
1. Felipe Varas, Iván Marinovic, and Andrzej Skrzypacz (2020), *"Random Inspections and Periodic Reviews: Optimal Dynamic Monitoring,"* *Review of Economic Studies*, 87(6), 2893–2937 (`doi:10.1093/restud/rdaa012`), which characterizes when optimal dynamic monitoring under moral hazard uses constant-hazard random inspections versus periodic/concentrated reviews.
2. Chrysanthos Dellarocas (2006), *"How Often Should Reputation Mechanisms Update a Trader's Reputation Profile?,"* *Information Systems Research*, 17(3), 271–285 (`doi:10.1287/isre.1060.0092`), which analyzes finite-window reputation memory under moral hazard and noisy feedback—directly relevant to `C-mem(K, M)`'s sliding-window forgetting.
3. Chen Liang, Yili Hong, and Bin Gu (2025), *"Monitoring and the Cold Start Problem in Digital Platforms: Theory and Evidence from Online Labor Markets,"* *Information Systems Research*, 36(1), 600–620 (`doi:10.1287/isre.2021.0146`), which studies how platform monitoring substitutes for missing track records among newcomers.




* **Exact fix**: **`text only`** — Add these three citations to Section 2 (pp. 3–4) to situate age-ranked vs sliding-window credibility monitoring within dynamic inspection and cold-start platform theory.

---

### 5. Theory Check

* **Lemma 1 (Local identity — Section 5, p. 7; Proof, Appendix F, p. 34)**:
* *Assumptions & Proof*: Fixes an offer $(c, \text{bid})$ with $0 < c \le q^{\max}$ and compares truthful effort $c$ against $c - \Delta$ ($0 \le \Delta \le c$). Conditions on pre-delivery state, rival outcomes, and audit set $U$ ($K = |U|$), assuming $U$ is independent of i.i.d. Gaussian delivery noise $\epsilon_j \sim N(0, \sigma^2)$ and that focal audit outcomes affect continuation value only through whether *any* job in $U$ fails, with common continuation difference $C_U$. Under these assumptions, cost savings are $sb\Delta = sg$, expected additional refund is $(d - d_0)\sum_{j \in U} M_j$, and the increase in probability of at least one failure is $(1 - d_0)^K - (1 - d)^K$, yielding $A(\Delta)$ exactly.
* *What it establishes / does not establish for the simulated process*: Establishes a valid one-step decomposition for rules whose state depends only on binary failure/ban indicators and identity age (`B2`, `B3`, `R3`) when the offer is held fixed. **Does not apply** to `C*` or other verified-history rules, where the *count* of passed audits in $U$ increments credibility $p_i$ (Section 4, p. 6) and changes continuation value even conditional on zero failures. Also does not cover joint claim-and-effort deviations (used by all searched attacker families).


* **Corollary 1 (Uniform auditing under replacement — Section 5, p. 7; Proof, Appendix F, p. 34)**:
* *Assumptions & Proof*: Assumes immediate replacement at $e = 0$ before the next allocation restores the exact distribution of payoff-relevant future states up to identity relabelling ($V_{\text{fail}} \ge V_{\text{clean}}$), and that any post-failure continuation can be mimicked after no failure ($V_{\text{fail}} \le V_{\text{clean}}$), implying $C_U = 0$. The proof correctly verifies both conditions for `B2` and `B3` with refund-and-ban enforcement and no bonds: audit selection precedes delivery, audit budget consumption depends on audit count rather than failure outcomes, and honest opponents' play does not depend on the focal identity label.
* *What it establishes / does not establish for the simulated process*: Proves that in the simulated `B2`/`B3` environment (both without churn and under exogenous honest churn in Section 10), bans impose zero continuation penalty regardless of $L$. Does not quantify optimal multi-round attack profit or apply to rules with bonds or history/age-dependent audit priority.


* **Lemma 2 (Coverage — Section 5, p. 7; Proof, Appendix F, p. 35)**:
* *Assumptions & Proof*: Uses exchangeability of i.i.d. continuous random audit keys within each age group and independence from delivery noise to show that within an age group of $n$ jobs ($s$ focal), `R3` draws $k' = \min\{n, \max(0, k - H)\}$ audits hypergeometrically, and that a uniquely newest established identity receives at least $\min(s, \lceil r/2\rceil)$ of the $r$ residual audits.
* *What it establishes / does not establish for the simulated process*: Establishes exact conditional per-round audit counts for `R3`. Does **not** establish deterrence, positive audit counts (e.g., at $\rho=1$, $k = 0$ for rounds $t \le 190$), or that a replacing attacker is uniquely newest (which fails in rounds $1 \dots L$ and holds in only `0.008–0.033` of rounds under churn at $p=0.05$, p. 15).


* **Proposition 1 (Terminal shading — Section 5, p. 7; Proof, Appendix F, p. 35)**:
* *Assumptions & Proof*: Differentiates $A(\Delta)$ at $\Delta = 0$ when $C_U = 0$, using $M_j \le v_{\max}$ and $K \le s$ to get $A'(0) \ge s(b - v_{\max}\phi(\tau/\sigma)/\sigma)$. At $\tau = 0.16, \sigma = 0.05, v_{\max} = 1.4$ (Appendix E, p. 33), $v_{\max}\phi(\tau/\sigma)/\sigma \approx 0.0668 < 0.067$ (reviewer computation). Note a minor strict-inequality slip on p. 7: the text says *"every provider has $b>0.22$"*, whereas Appendix E (p. 33) lists $b_i = (0.40, 0.38, \dots, 0.22)$, so $b_{10} = 0.22$ ($b \ge 0.22$).
* *What it establishes / does not establish for the simulated process*: Establishes that in round $t = T$ (where $C_U = 0$ for every rule), small same-offer shading strictly pays for every served provider with $c > 0$, ruling out exact zero-gain deterrence ($g \le 0$) and justifying bounded-gain claims. Does not bound cumulative gain over $T$ rounds.


* **Theorem 1 (Conditional renewal bound — Appendix F, pp. 33–35)**:
* *Assumptions & Proof*: Assumes play decomposes into i.i.d. cycles of geometric established spells (constant per-round survival $1 - q_E$ and profit $r_E$) and recoveries of duration $D \ge L$ ($\mathbb{E}D < \infty$) where every permitted action earns expected surplus $\le \epsilon$ over truthful rate $h$. Under these assumptions, renewal-reward algebra [33] yields $\overline{\Pi} - h \le \epsilon + (r_E - h - \epsilon)_+ / (1 + q_E L)$.
* *What it establishes / does not establish for the simulated process*: **Establishes nothing directly for the simulated process**, as the paper candidly notes (p. 7, p. 34). The simulated process has finite horizon $T=200$, carryover audit budgets, exogenous/endogenous identity turnover, and stateful adaptive attackers (`D2+H3`, `X7-SC`, `X5-AG/v2`), so cycles are neither independent nor identically distributed.



---

### 6. Presentation and Length

* **Clarity of the paper's centre early on**: The core problem and mechanism comparison are clear by page 2, but three structural choices obscure the centre early: (i) the opening paragraph (p. 1) spends 8 lines on details of an unreviewed AI-generated technical report (`FlashProve` [27]) that Appendix D (p. 33) concedes does not measure output quality; (ii) `Results in brief` (p. 3) uses undefined internal labels (`X7-SC`, `D2+H3`, `Q1`, `Q4`, `W1`) before Sections 3–6 introduce the model, rules, or attacks; and (iii) Sections 8–10 bury main findings inside 40–55 line paragraphs stuffed with audit-log qualifications.
* **Comparative and universal word audit**: Across Sections 1–12 and Tables 3–28, the paper's quantitative claims using `"falls"`, `"rises"`, `"reverses"`, `"every"`, `"all"`, `"only"`, and `"never"` (`"survives"` does not appear; only `"survival"` appears in Section 5/Appendix F) are remarkably faithful to the underlying frozen and doubled tables. Specifically: `R3`'s audited share of attacker jobs strictly falls across $p \in \{0.01, 0.02, 0.03, 0.05\}$ under both frozen (`0.366 -> 0.190 -> 0.093 -> 0.042`) and doubled (`0.505 -> 0.188 -> 0.093 -> 0.028`) searches (Table 9, p. 17); `B3 - R3` is positive on `"every"` fresh market without churn under both frozen and doubled searches (Table 4, p. 12; Table 24, p. 29); both contrasts are lower than no-churn on `"every"` market at $p=0.03$ and $0.05$ under both search versions (Table 8, p. 17); and `R3`'s selected attacker `"never"` replaces its identity on `2/0`, `2/2`, `3/3`, `3/3` of 6 markets (frozen/doubled, Table 9 p. 17). The only rhetorical overreach is describing the churn shift as `"its measured advantage reverses"` in the Conclusion (p. 18) without immediately reiterating that 15 of 16 6-market `t`-intervals in Table 7 (p. 16) include zero.
* **What to cut, move, or rewrite**:
1. *Cut / trim*: Trim the `FlashProve` implementation details on p. 1 to two sentences; cut the eight-item `"Expectations"` checklist on p. 16 (which the authors admit carried little risk after the timing check) or move it to Appendix C; trim the repository directory paths in `Availability` (p. 18) to a brief artifact statement.
2. *Move to appendix*: Move the `fresh1` studentized-bootstrap numerical edge-case note (`1.2e-13`, `506 of 9,999 resamples`, p. 10) and the 19-cell continued-search breakdown (p. 11) to Appendix C, leaving a two-sentence summary in Section 8.
3. *Rewrite*: Replace the undefined acronyms in `Results in brief` (p. 3) with plain English; split the 55-line Q1 paragraph (pp. 10–12) into three focused paragraphs (pooled Q1 decision, comparator/search sensitivity, and cross-market/honest-newcomer burden); and tighten the Abstract (p. 1, currently ~265 words) to ~180–200 words while fixing the exploratory comparator labelling and causal nuance noted in Problems 3–4.



---

### 7. Decision Table

| Venue | Score (1–5) | Acceptance Probability | Confidence (1–5) | Single Change That Would Move the Score Most |
| --- | --- | --- | --- | --- |
| **WEIS 2027** | **3.5** | **65%** | **4** | Run `C-thr(12)` under honest churn (Section 10) and resolve the 21/72 flagged churn searches so the verified-history vs. age-ranking comparison under churn does not rest on a single efficiency-selected comparator and incomplete searches. |
| **AAMAS (main track)** | **3.0** | **45%** | **4** | Add `C-thr(12)` and converged searches to Section 10, and restructure Sections 1, 8, and 10 to foreground the multi-agent mechanism and move registration forensics to the appendix. |
| **ACM EC** | **2.5** | **20%** | **4** | Either establish finite-horizon theoretical bounds connecting `R3` and credibility rules to market primitives (replacing Theorem 1's unverified renewal assumptions) or run a pre-registered, adequately powered ($n \ge 20$ fresh markets) confirmatory study of age-ranked vs. verified-history rules under calibrated honest churn with converged searches. |
