Model: GPT-6 Astra Pro

## 1. Files read and verification scope

I read **main.pdf[main.pdf](sandbox:/workspace/scratch/d350cf940049/review-d10/main.pdf), draft 10, in full**, in page ranges through all 37 pages. I also inspected rendered pages containing the theory and the main churn tables. Page references below use the paper’s printed page numbers.

I read or inspected the following supporting files:

| Area | Files used |
|---|---|
| Review instructions and history | `PROMPT.md`; `PREVIOUS_REVIEW.md`; the R4, R3 and R2 reviews; `RESPONSE.md`; the R5 and R4 prompts and responses; `SECOND_REVIEW_TRIAGE.md`; `outline-draft10.md`; all four internal reviews |
| Churn design and analysis | `churn-plan.md`; `churn-plan-amendment-1.md`; relevant driver sections in `churn_v2.py`; `churn_block.py`; `churn_paper.py`; their supplied tests; `churn.json`; `churn_mid.json`; `churn_paper.json`; the churn tables |
| Churn records | All supplied evaluation, doubling and diagnostic records at the four rates; inventories; run files; the zero-churn gate record |
| Runs A and B | Both plans, analysis summaries and analysis scripts; relevant run-driver code; all supplied continuation records; `recompute.json`; the convergence inventory |
| Reset follow-up | The experiment plan; relevant driver code; `reset_block.py`; its tests; `reset.json`; reset and reference records; diagnostic records; `posthoc_reset.tex` |
| Registered results | `protocol-v2.yaml`; `predictions-v2.md`; `records/report.json`; `addendum.md`; `audit.json`; `scoring.json`; `eligibility.json`; `stability-result.json`; relevant audit and scoring code |
| Process | Relevant sections of `operations-ledger.md` |

No supplied file I attempted to open failed. This does **not** mean every file in the archive received a complete independent audit.

**What I reproduced:** the churn analyses, their paper tables and aggregate output, the reset analysis, the principal D2+H3 Run B results, and the Run A market-level summaries.

**What I could not reproduce:** simulation trajectories or optimiser searches, because the simulator is absent; Run A’s seed-bootstrap intervals and search flags from original records, because those records are absent; the complete original registration chronology from independently verifiable timestamp evidence. The supplied test suites also could not run unchanged: `pytest` is unavailable, some tests import absent simulator modules, and one test assumes a different directory layout.

For compact source references below:

- **C** means churn.json[churn.json](sandbox:/workspace/scratch/d350cf940049/review-d10/churn.json).
- **M** means churn_mid.json[churn_mid.json](sandbox:/workspace/scratch/d350cf940049/review-d10/churn_mid.json).
- **P** means churn_paper.json[churn_paper.json](sandbox:/workspace/scratch/d350cf940049/review-d10/churn_paper.json).
- `base` in these files means the **frozen** search version.

## 2. Summary verdict

**WEIS: 3/5, upper borderline. AAMAS main track: 2/5. ACM EC: 1/5.** The numerical core survives this review. The churn and reset analyses reproduce, and most round-5 corrections are now present. The paper has a clear, defensible result: under the prescribed searches, R3’s advantage in markets without honest identity turnover deteriorates when honest providers also replace identities; its comparisons with C* and B3 deteriorate differently. The revision now reports those differences with appropriate qualifications. The remaining weakness is the reach of the result: one market neighbourhood, one verified-history comparator under churn, fixed audit parameters, restricted attackers, and unresolved search error. I found several factual and scope errors that should be corrected, but none overturns the main churn tables. The next substantial improvement should be a stronger scientific test or a result that explains how the effect changes with audit capacity and turnover. Another cycle of small wording repairs alone will not materially change the venue assessment. Sources: paper §§8–11; reproduced C, M and reset outputs.

## 3. Follow-through on round-5 problems

The statuses below distinguish a completed reporting correction from an unresolved scientific limitation.

| R5 problem | Status | Revised sentence or evidence | Accuracy of `RESPONSE.md` |
|---|---|---|---|
| **1. Run A direction was overstated** | **Resolved** | Abstract, p.1: “a second verified-history comparator is also equivalent to R3 within the margin, with a direction that depends on the search version and is dominated by one market”. Section 8, p.11, gives the market counts and points to the four comparisons in Table 27. | Accurate. “Contributes most” correctly avoids claiming that fresh5 alone determines the frozen D2+H3 sign. |
| **2. C* crossing was stated too precisely** | **Resolved, with a small abstract ambiguity** | P.15: “With the frozen searches the pooled C∗ minus R3 difference changes sign between p = 0.01 and 0.02; with the doubled searches it is already −0.004 at 0.01.” The comparison is explicitly unresolved at both low rates. | Accurate for the main correction. The abstract’s clause about one market setting the frozen sign should explicitly refer to 0.02. |
| **3. “Survives moderate churn” concealed pooling** | **Resolved** | Abstract, p.1: “the pooled B3 minus R3 gap stays positive through 0.03, though negative on three markets there, and is negative at 0.05.” | Accurate. The vague word “moderate” is gone. |
| **4. Diagnostics were frozen-only and their timing unclear** | **Partly resolved** | Table 8, p.18, supplies both versions. Its caption says: “These statistics were defined after the results at p = 0.01 and 0.05 and before the runs at 0.02 and 0.03.” | Accurate about the completed changes. The zero-churn allocation row remains absent, and the split between replacing and non-replacing attacks is supplied in the text only at 0.05. |
| **5. Efficiency omitted doubled results and the low market value** | **Resolved** | P.16: “On fresh2 at p = 0.05, R3’s efficiency under attack is 0.893, below the registered threshold of 0.90; this is an exploratory point estimate, not a registered failure.” Both versions appear in Table 8. | Accurate. |
| **6. The abstract printed −0.052 alone** | **Resolved** | Abstract, p.1, and conclusion, p.19: “B3 minus R3 is −0.052 (−0.033 with the doubled searches; the frozen value includes one failed search).” | Accurate. Replace “failed search” with the formal term “search-flagged cell”; see below. |
| **7. Conclusion claimed a result about the comparator class** | **Resolved** | P.19: “Against C∗, the one verified-history comparator run under churn”. P.16 explicitly denies a class-wide robustness result. | Accurate. |
| **8. Mechanism discussion covered only attackers that stay old** | **Partly resolved** | P.15 now gives audit-rate ranges for attacks that replace and attacks that stay old, under both search versions. | Accurate about the added ranges. **Inaccurate** that the omitted newest-identity frequencies need another diagnostics pass. Those values already exist in the supplied records. |
| **9. Churn search flags remained** | **Resolved as a disclosure request** | Abstract, p.1: “21 of the 72 churn doubling checks are flagged incomplete.” | Accurate that no churn cells were re-searched. Round 5 allowed disclosure as an alternative. The underlying search uncertainty remains. |
| **10. Package lacked the amendment and run drivers** | **Resolved for the named omissions** | `churn-plan-amendment-1.md` and the Run A/B drivers are present. This is a package correction, so there is no revised paper sentence. | Accurate. Full simulation reproduction remains outside this package’s scope. |
| **11. Cross-references and small wording errors** | **Resolved** | The reset references now point to Section 9; p.11 uses “runner-up minus R3: −0.010”; p.15 gives C*’s audit shares directly. | Accurate. A separate page-count statement is wrong: the main text continues onto p.19, where Appendix A begins. |

Sources: PREVIOUS_REVIEW\.md[PREVIOUS_REVIEW.md](sandbox:/workspace/scratch/d350cf940049/review-d10/PREVIOUS_REVIEW.md), §7; RESPONSE.md[RESPONSE.md](sandbox:/workspace/scratch/d350cf940049/review-d10/RESPONSE.md); the cited paper pages.

## 4. The churn section

### (a) Plan fidelity

**The implementation and scoring agree with the written estimand and expectations. The claimed timing is internally consistent, but not independently proved by this archive.**

The original plan discloses the timing peek before expectations 1–4. The amendment discloses that the endpoint results were known before expectations 5–8 were written. It compares each search version with its own corresponding no-churn values, uses equal market weights, and keeps the reference candidate fixed while evaluating it under churn.

The ledger places amendment commit `2604ce6` before the new runs at `e1c925a`; the new records identify the latter commit in their provenance. This supports the stated sequence. The archive lacks the Git object history or independent timestamp evidence needed to verify that sequence independently. Sources: `churn-plan-amendment-1.md`, §§1–3; `operations-ledger.md`, “Churn amendment 1”; new-rate record provenance.

The amendment’s expectations reproduce as follows:

| Expectation | Frozen result | Doubled result | Verdict |
|---|---|---|---|
| **5. Honest replacement audit share decreases across the four rates** | 0.879783 → 0.788909 → 0.705878 → 0.570712 | 0.854462 → 0.789528 → 0.705798 → 0.570308 | Met |
| **6. C*−R3 is lower at 0.03 than 0.02** | −0.090350 < −0.020027 | −0.062919 < −0.020879 | Met |
| **7. R3 gain at 0.02 is below the endpoint midpoint** | 0.111122 < 0.168328 | 0.111975 < 0.169948 | Met |
| **8. B3−R3 is positive on at least five markets at 0.02** | 5 of 6 | 6 of 6 | Met |

Source: reproduced `M.expectations["5"…"8"]`. Expectations 1–4 also reproduce as met from `C.expectations`.

The paper is right to say that these expectations carried limited risk after the earlier observations. Their success is not an independent validation of the mechanism.

### (b) Numerical reproduction

The two churn commands reproduce **C and M exactly after removing only their `inputs` metadata**. The paper aggregation reproduces P exactly. The following generated tables are byte-identical to the submitted files:

- `posthoc_churn_all.tex`
- `posthoc_churn_audit.tex`
- `posthoc_churn_t.tex`
- `posthoc_runnerup.tex`

This checks aggregation of the supplied records. It does not verify that the absent simulator generated those records correctly.

#### Table 6: gains and contrasts

In each value cell below, the order is:

**R3 gain / C* gain / B3 gain; C*−R3 / B3−R3.**

| Item | Paper value | My reproduced value | Source |
|---|---|---|---|
| Frozen, p=0 | 0.065 / 0.086 / 0.238; 0.021 / 0.173 | 0.064907 / 0.085627 / 0.238302; 0.020720 / 0.173395 | C, `statistics.base["0"]` |
| Frozen, p=0.01 | 0.065 / 0.066 / 0.240; 0.001 / 0.175 | 0.064944 / 0.066412 / 0.239528; 0.001469 / 0.174584 | C, `statistics.base["0.01"]` |
| Frozen, p=0.02 | 0.111 / 0.091 / 0.230; −0.020 / 0.119 | 0.111122 / 0.091095 / 0.229624; −0.020027 / 0.118502 | M, `statistics.base["0.02"]` |
| Frozen, p=0.03 | 0.167 / 0.077 / 0.235; −0.090 / 0.068 | 0.166939 / 0.076589 / 0.234600; −0.090350 / 0.067661 | M, `statistics.base["0.03"]` |
| Frozen, p=0.05 | 0.272 / 0.098 / 0.220; −0.173 / −0.052 | 0.271749 / 0.098319 / 0.219767; −0.173430 / −0.051982 | C, `statistics.base["0.05"]` |
| Doubled, p=0 | 0.067 / 0.097 / 0.237; 0.030 / 0.170 | 0.067450 / 0.097075 / 0.237247; 0.029624 / 0.169797 | C, `statistics.doubled["0"]` |
| Doubled, p=0.01 | 0.086 / 0.082 / 0.240; −0.004 / 0.153 | 0.086286 / 0.082051 / 0.239605; −0.004235 / 0.153319 | C, `statistics.doubled["0.01"]` |
| Doubled, p=0.02 | 0.112 / 0.091 / 0.239; −0.021 / 0.127 | 0.111975 / 0.091095 / 0.239035; −0.020879 / 0.127060 | M, `statistics.doubled["0.02"]` |
| Doubled, p=0.03 | 0.167 / 0.104 / 0.236; −0.063 / 0.069 | 0.166908 / 0.103990 / 0.235586; −0.062919 / 0.068677 | M, `statistics.doubled["0.03"]` |
| Doubled, p=0.05 | 0.272 / 0.103 / 0.240; −0.169 / −0.033 | 0.272445 / 0.103484 / 0.239925; −0.168962 / −0.032520 | C, `statistics.doubled["0.05"]` |

The relevant fields within each source row are `g[rule].pooled.estimate`, `d.pooled.estimate` and `q.pooled.estimate`. **All associated seed-bootstrap interval endpoints also reproduce.**

#### Tables 7–8 and Section 10 text

Every numerical field in Table 8’s twelve rows reproduces, including both search versions, allocation shares, replacement counts and efficiency. The following checks cover the principal text claims.

| Item | Paper value | My value or verification | Source |
|---|---|---|---|
| R3 attacker audit share, frozen, increasing p | 0.366, 0.190, 0.093, 0.042 | Matches at displayed precision | C/M, `review_r4.audit_allocation` |
| Same, doubled | 0.505, 0.188, 0.093, 0.028 | Matches at displayed precision | Same |
| Young honest share of jobs, R3 at 0.05 | 0.391 / 0.394 | Matches | Same, frozen/doubled |
| Share of R3 audits going to young honest jobs, 0.05 | 0.823 / 0.828 | Matches | Same |
| Established honest jobs audited under R3, 0.05 | 0.078 / 0.078 | Matches | Same |
| R3 winners without replacement | Frozen: 2, 2, 3, 3; doubled: 0, 2, 3, 3 | Matches | P, `rates`; selected attack knobs |
| R3 efficiency, 0.05 | 0.967 / 0.949 | Matches | C, `review_r4.eff_attack` |
| C* efficiency, 0.05 | 0.993 / 0.993 | Matches | Same |
| B3 efficiency, 0.05 | 0.940 / 0.959 | Matches | Same |
| R3 fresh2 efficiency, 0.05 | 0.893 | 0.893498, both versions | C, `review_r5.eff_by_market` |
| Flagged checks | 13/36 plus 8/36 | 21/72 combined | C/M, `flag_summary` |
| Largest flagged attack change | 0.088 | 0.0877435015 | P, `flags.max_attack_change` |
| Reference-change diagnostics | 32/72; maximum 0.009 | 32/72; maximum 0.0094848813, **on training scores** | P, `flags.reselected`, `max_reference_change` |
| R3 attack-profit increase at 0.05 | 113.101 | 113.100728 raw profit units | C, `statistics.base["0.05"].change.profit.F111.attack.pooled` |
| R3 reference-profit change | −0.146 [−0.393, 0.098] | −0.145609 [−0.392719, 0.097955] | Corresponding `.reference.pooled` |
| Table 7 market intervals | All contain zero except doubled B3−R3 at 0.05 | All sixteen intervals reproduce | C/M, `review_r4.t95` |

The reference-diagnostic row needs a wording correction. Its value does not bound the change in held-out gain.

### (c) Comparative and universal word check

The substantive statements now mostly pass.

| Wording or claim | Assessment |
|---|---|
| R3’s attacker audit share **“falls”** across the sampled rates | Correct for both versions. |
| R3’s gain **“rises”** across the positive churn rates | Correct for both versions. |
| C*−R3 **“changes sign between”** 0.01 and 0.02 | Correct only for frozen searches. Section 10 now states the doubled result separately. |
| B3−R3 changes sign between 0.03 and 0.05 | Correct for both versions. |
| C*−R3 is negative on **“all six”** markets at 0.03 | Correct for both versions. |
| B3−R3 is negative on three markets at 0.03 despite a positive pooled value | Correct for both versions. |
| At 0.05 both contrasts are negative on six frozen markets and five doubled markets | Correct. |
| **“Every”** market t interval includes zero except doubled B3−R3 at 0.05 | Correct. |
| Frozen selected R3 attacks **“never replace”** on two or three markets | Correct as a statement about those selected policies. The doubled exception at 0.01 is disclosed. |
| **“All eight”** expectations are met | Correct under the written point-estimate scoring rule. |
| **“Only one”** verified-history comparator was run under churn | Correct. |
| B3 efficiency **“shows no trend”** | Acceptable as a description of the nonmonotonic sequence. It is not a statistical test establishing no trend. |

Sources: the reproduced fields listed above; C/M `statistics[version][rate].{d,q}.markets`; P `rates`.

One abstract sentence remains ambiguous:

> “The comparison with C∗ is not resolved at p = 0.01 or 0.02, where one market dominates the pooled value (and sets its sign with the frozen searches)” (p.1).

The sign-setting clause is correct at **0.02**, not at **0.01**:

| Rate | Version | Pooled C*−R3 | Excluding fresh1 |
|---|---|---:|---:|
| 0.01 | Frozen | +0.001469 | +0.009016 |
| 0.01 | Doubled | −0.004235 | +0.009894 |
| 0.02 | Frozen | −0.020027 | +0.000431 |
| 0.02 | Doubled | −0.020879 | −0.000593 |

Source: my leave-one-market-out calculations from C/M `statistics[version][rate].d.markets`.

The comparison is unresolved at the low rates for different reasons. State those reasons separately.

### (d) Mechanism

The mechanism paragraph is now supported **as a description of allocation under the selected attacks**. Its main qualification is correct:

> “The diagnostics describe the setting; they do not isolate the cause, because churn also resets histories, ends bans, and changes the selected attacks.” (p.15).

The records support the following pattern: more audits go to young honest identities; the attacker’s audit share falls; some selected attackers stay old; replacing attackers can also receive few audits. The raw-profit decomposition supports the claim that the increase in measured R3 gain mainly comes from attack profit rather than deterioration of the frozen reference. Sources: Table 8; C/M `review_r4.audit_allocation`; C `statistics.base["0.05"].change.profit.F111`.

The paragraph does not establish a causal decomposition into age information, history resets, ban removal and policy selection. It also does not establish a threshold. The sentence “four rates cannot show whether the decline is smooth or has a threshold” is appropriate.

One useful omitted statistic is already available. For the three replacing R3 attacks at 0.05, the mean fraction of served rounds in which the attacker is uniquely newest among job-holding identities is:

| Market | Frozen | Doubled |
|---|---:|---:|
| fresh0 | 0.03335 | 0.01201 |
| fresh3 | 0.00834 | 0.00834 |
| fresh5 | 0.01820 | 0.00478 |

Source: my means of `records/churn/p0.05/diagnostics.json`, `cells[market|F111][version].shares.focal_newest_by_first_offer_assigned`. The driver defines this using first-offer dates and excludes ties.

This helps explain why an attacker that replaces its identity can still avoid much of the age-based targeting. Adding it requires analysis of existing records.

## 5. Run A and Run B

### Run A

Run A is placed and labelled correctly: exploratory, after the report, and without churn. Its proper implication is the paper’s sentence:

> “The registered direction holds for C∗, not for verified-history targeting in general.” (p.11).

The four rows in Table 27 reproduce from the six stored market means:

| Family | Version | Runner-up−R3 | Market-level t interval | Markets where R3 has lower gain | C*−runner-up |
|---|---|---:|---|---:|---:|
| D2+H3 | Frozen | −0.010235 | [−0.036377, 0.015908] | 4/6 | 0.030955 |
| D2+H3 | Doubled | −0.004518 | [−0.033535, 0.024499] | 4/6 | 0.034143 |
| X7-SC | Frozen | −0.007233 | [−0.034577, 0.020111] | 4/6 | 0.031552 |
| X7-SC | Doubled | 0.002820 | [−0.004373, 0.010013] | 5/6 | 0.021470 |

Source: `runs/runnerup_analysis.json`, `<family>.<version>.runner_up_minus_r3.markets`; my equal-weight means, sign counts and t calculations. The final column agrees with `.cstar_minus_runner_up.estimate`.

Fresh5 contributes most to the frozen D2+H3 mean, but removing it leaves a slightly negative mean, **−0.000469**. Thus the revision’s wording is accurate; saying it determines that sign would be wrong. Source: my calculation from the same market means.

Run A does **not** invalidate the registered comparison with C*. It limits what that comparison says about other comparator choices.

A small inferential clarification would help. Run A applies the same materiality margin to nominal percentile intervals. Its direction label does not use the registered calibration and Holm procedure. This is disclosed in the plan and analysis file, but should be stated beside the paper’s quoted category. Source: `runs/drivers/common.py::q1_category`; `runs/runner-up-plan.md`, §3.

### Run B

The numerical results reproduce, but the paper misstates the selected cells:

> “Continued searches of the 19 registered cells whose doubling check was flagged…” (p.11).

Run B contains **14 flagged profit cells and five additional, unflagged X7-SC cells selected for held-out shortfalls**. I checked the continuation IDs against `records/report.json.doubling[id].incomplete`. This agrees with `runs/drivers/convergence_v2.py::cells_for`.

The independently reproduced principal results are:

| Contrast | Frozen | Final continuation winners |
|---|---:|---:|
| C*−R3, D2+H3 | 0.020720 | 0.028191 |
| B3−R3, D2+H3 | 0.173395 | 0.169469 |

Source: recomputation from `records/eval_all/evaluate/` and `records/convergence/convergence/`, exactly matching `records/convergence/recompute.json.q1` and `.q4`, including their paired seed-bootstrap intervals.

Fresh3’s C*−R3 change is **0.053827**, which supports the reported rounded change of 0.054. Source: `.q1.converged.markets.fresh3` minus `.q1.frozen.markets.fresh3`.

All supplied continuation records pass their stated incremental-improvement check within the permitted rounds. This establishes that check, **not global convergence or a bound on remaining search error**. No churn cells were included. The original registered decisions remain unchanged.

## 6. Structure and length

**The paper has a clear centre, but it still reaches that centre too late.**

The current title explicitly says:

> “Registered Tests of Age-Ranked Audits and an Exploratory Limit Under Honest Churn.”

That subtitle is honest. It resolves the previous ambiguity about whether the churn result was registered.

The main structural problem is visible in the PDF: honest churn starts on p.14, its main table appears on p.16, its figure appears on p.17 after Section 11 has begun, and its audit-allocation table appears on p.18. The conclusion and Availability continue on p.19. The response’s statement that the main text ends on p.18 is incorrect.

I would make these changes:

1. **Move the churn figure and its main empirical statement into the introduction.** Keep the full analysis in Section 10.
2. **Move Theorem 1 to the appendix.** The paper itself says: “No reported result depends on it” (p.7).
3. **Shorten the calibration discussion in the main text.** Retain the uncertainty target and its limitations; move implementation detail and extreme-bootstrap diagnostics.
4. **Split the long Q1 discussion.** Separate the registered result, search sensitivity and comparator-selection sensitivity.
5. **Reduce the attack catalogue in the main text.** Define the families needed for the main argument; retain the full catalogue in the appendix.
6. **Shorten the repeated FlashProve discussion.** It motivates costly checks, but does not carry the experimental contribution.
7. **Keep the churn tables inside the churn section.**

The novelty should be stated narrowly. Credibility-based checking with identity replacement already appears in Sarmenta’s work, and BOINC’s adaptive replication uses verified history to vary checking. The paper acknowledges this correctly. Its contribution is the controlled comparison and the observed failure under honest turnover, rather than the basic idea of checking newcomers. [groups.csail.mit.edu](https://groups.csail.mit.edu/cag/bayanihan/papers/ccgrid01/ccgrid01.pdf?utm_source=chatgpt.com)

I checked the short arguments for Lemma 1, Corollary 1 and the conditional renewal bound under their stated assumptions. I did not find an algebraic error. Their assumptions, especially those of the renewal bound, do not establish the behaviour of the implemented finite-horizon process. The paper now says that explicitly.

## 7. New problems and exact fixes

### 1. The reference-reselection diagnostic is described too broadly

> “Reselecting each rule’s reference from its frozen menu under churn changes the reference in 32 of the 72 cells, by at most 0.009 in gain.” (p.15).

The reported maximum is a **training-score change**, not a measured bound on held-out gain. It is also approximately 0.009485, so “at most 0.009” is not a literal upper bound. Sources: P `flags.max_reference_change`; `churn_v2.py::reference_of`; `churn-plan.md`, §3.

**Exact fix, text only:**

> “Reselection within the frozen reference menus gives a nonzero training-set reference-score change in 32 of 72 cells, with a maximum absolute change of 0.0095. This diagnostic does not bound the change in held-out gain and does not regenerate the reference menus.”

This is the most consequential remaining wording issue because it concerns what the reference sensitivity establishes.

### 2. Run B’s cell selection is factually misdescribed

> “Continued searches of the 19 registered cells whose doubling check was flagged…” (p.11).

The correct split is given in Section 5 above.

**Exact fix, text only:**

> “Continued searches of 14 flagged profit cells and five additional X7-SC cells with held-out shortfalls all passed the incremental-improvement check within three rounds. These runs included no churn cells.”

Retain the reproduced numerical results.

### 3. The conclusion blurs registered calibration and exploratory intervals

> “These conclusions concern frozen searches and references, with interval calibration admitted on development fixtures.” (p.19).

The preceding conclusions include churn and reset results. Their percentile intervals are not the calibrated registered Q1/Q4 procedure. The paragraph also discusses doubled-search sensitivities.

**Exact fix, text only:**

> “The registered Q1/Q4 inferences use calibration admitted on development fixtures. The follow-up intervals are exploratory and condition on the six markets, selected policies and frozen reference menus. Doubled searches are sensitivity analyses.”

The distinction is already explained elsewhere; it should remain correct in the conclusion.

### 4. The abstract combines two different low-rate influence patterns

The problematic sentence is quoted in Section 4(c). At one low rate the sign differs between search versions; at the other, one market determines the frozen pooled sign.

**Exact fix, text only:**

> “At p = 0.01 the pooled C* minus R3 difference changes sign across search versions. At p = 0.02 it is negative under both versions, but fresh1 dominates its magnitude and determines its frozen-search sign.”

The detailed Section 10 discussion already handles this more accurately than the abstract.

### 5. The theory remark gives an overly broad zero-coverage condition

> “with honest churn it shares the newest positions with honest newcomers, and the bound is zero whenever a newer identity holds jobs or the quota is already spent” (p.7).

A newer identity holding a job does not itself force coverage to zero.

For a constructed counterexample, take a residual quota of ten audits. Five go to newest-first targeting. Suppose a newer established identity has one job and the focal next-newest identity has two. Both focal jobs still receive targeted audits. These are counterexample inputs, not simulation results.

**Exact fix, text only:**

> “With honest churn, the uniquely-newest guarantee may no longer apply. Coverage can be zero if newer jobs exhaust the relevant quota.”

This is a local wording error, not a refutation of the empirical result.

### 6. Two short scope corrections remain in the conclusion and abstract

**W1 scope.**

> “The registered W1 search found no profitable welfare attack (gross efficiency near 0.997)” (p.19).

That statement applies to R3 and C*. Table 14 reports a profitable W1 attack against B3, with efficiency 0.839 and gain 0.254.

**Exact fix, text only:**

> “Against R3 and C*, the registered W1 searches selected policies with zero estimated gain and gross efficiency near 0.997.”

**Search status.**

> “the frozen value includes one failed search” (pp.1, 19).

The paper formally distinguishes a missing or failed execution from a completed search flagged by its doubling check.

**Exact fix, text only:**

> “the frozen value includes one search-flagged cell with a large improvement under doubling”.

### 7. The response incorrectly says the newest-identity statistic needs another run

> “The p = 0 diagnostic row and the newest-identity frequency (both need a diagnostics pass).”  
> `RESPONSE.md`, “Still open”.

The second statistic already exists, as shown in Section 4(d).

**Exact fix, analysis on existing records:**

Add the existing newest-identity frequencies, with their denominator defined, and change the response to say that only the zero-churn allocation baseline still needs a diagnostics pass.

For release preparation, also repair the hard-coded test path to `runnerup_analysis.json` and include the Run A raw records needed to replay its intervals. These are reproducibility improvements; the missing records do not demonstrate that the reported result is wrong.

### A useful additional analysis: deterioration versus reversal

This is an extension I computed during this review, **not a registered result or a discovered error**.

The paper correctly says:

> “The churn reversals therefore have narrow seed-bootstrap intervals on these six markets … and they are not established beyond these markets.” (p.15).

That concerns the **absolute ordering at each churn rate**. A separate question is whether churn reduces R3’s advantage relative to the same market without churn.

I paired each market’s contrast with its own no-churn contrast:

\[
\Delta d_i(p)=d_i(p)-d_i(0),\qquad
\Delta q_i(p)=q_i(p)-q_i(0).
\]

Here \(d=C^*-R3\) and \(q=B3-R3\). Negative changes mean that R3’s relative position deteriorates. Each version uses its own no-churn baseline.

| p | Version | Mean change in C*−R3, with exploratory market t interval | Mean change in B3−R3, with exploratory market t interval |
|---|---|---|---|
| 0.01 | Frozen | −0.019 [−0.069, 0.030] | 0.001 [−0.033, 0.035] |
| 0.01 | Doubled | −0.034 [−0.084, 0.016] | −0.016 [−0.025, −0.008] |
| 0.02 | Frozen | −0.041 [−0.112, 0.030] | −0.055 [−0.098, −0.011] |
| 0.02 | Doubled | −0.051 [−0.117, 0.016] | −0.043 [−0.086, 0.001] |
| 0.03 | Frozen | −0.111 [−0.220, −0.002] | −0.106 [−0.193, −0.018] |
| 0.03 | Doubled | −0.093 [−0.179, −0.006] | −0.101 [−0.185, −0.017] |
| 0.05 | Frozen | −0.194 [−0.381, −0.008] | −0.225 [−0.415, −0.036] |
| 0.05 | Doubled | −0.199 [−0.378, −0.019] | −0.202 [−0.376, −0.029] |

Source: my calculations from C/M `statistics[version][rate].{d,q}.markets`, using ordinary two-sided 95% t intervals over the six paired market changes.

At **0.03 and 0.05, both contrasts deteriorate on every sampled market under both search versions**. That is a clearer descriptive result than a general claim that the ranking reverses.

These intervals are post hoc, unadjusted and based on few markets. They omit search uncertainty, and the nominal exclusions of zero should not be promoted into a new confirmatory claim. The complete rate table should be reported if this analysis is added.

**Suggested addition, analysis on existing records:**

> “The market-level intervals above concern the absolute ordering at each churn rate. In an exploratory paired comparison with each market’s no-churn result, both contrasts decreased on every sampled market at p = 0.03 and p = 0.05 under both search versions. This supports deterioration of R3’s measured relative performance, while the population ordering under churn remains uncertain.”

## 8. Decision

These acceptance probabilities are my judgement of the submitted paper, not estimates derived from conference acceptance statistics.

| Venue | Score | Acceptance probability | Confidence | Single change most likely to move the score |
|---|---:|---:|---|---|
| **WEIS 2027** | **3/5, upper borderline** | **50%** | Medium | A prospectively specified churn replication on new market draws, including both C* and the runner-up, with sufficient continued search to assess the cells that determine the result. |
| **AAMAS main track** | **2/5** | **15%** | Medium | A result that predicts how audit allocation and exploitation change with honest turnover and audit capacity, supported by stronger adaptive-attack evaluation. |
| **ACM EC** | **1/5** | **3%** | High | A substantive theorem about achievable or unavoidable incentive costs under free replacement and honest turnover. The current conditional renewal theorem does not establish such a result for the implemented mechanism. |

For WEIS, I would now treat this as a credible but narrow empirical paper with a useful negative result. Its numerical reporting is no longer the main obstacle. The highest-value next step is to test how far the churn result extends, with the design fixed before seeing the new outcomes.
