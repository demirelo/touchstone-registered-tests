GPT-6 Astra Pro

## 1. Files read and scope of this review

I reviewed **review-d10b.zip** against the previous package.

I read the current main.pdf[main.pdf](sandbox:/workspace/scratch/d350cf940049/review-d10b/main.pdf), pages 1–38, in page ranges. I also inspected the rendered page containing the new paired-change table and churn figure. All page references below refer to this PDF.

The files used directly in this round were:

- **Instructions and responses:** `PROMPT.md`, `RESPONSE.md`, `PREVIOUS_REVIEW.md`, and `external_reviews/astra-pro-paper-d10-ext.md`. I compared the unchanged historical review documents and outline with the previous package.
- **Churn design and analysis:** `churn-plan.md`, `churn-plan-amendment-1.md`, the relevant driver and ledger sections, `churn_block.py`, `churn_paper.py`, their tests, both churn analysis JSON files, `churn_paper.json`, and the generated tables. I checked the evaluation, doubling, and diagnostic records used by these analyses.
- **Run A and Run B:** their plans, analysis summaries, relevant drivers and analysis code, the new Run B selection counts, and the continuation records.
- **Reset follow-up:** I checked that the records, reference files, analysis output, and table are unchanged. I carried forward the previous reproduction rather than rerunning identical work.

For source references below, I use:

| Key | File |
|---|---|
| **C** | churn.json[churn.json](sandbox:/workspace/scratch/d350cf940049/review-d10b/churn.json) |
| **M** | churn_mid.json[churn_mid.json](sandbox:/workspace/scratch/d350cf940049/review-d10b/churn_mid.json) |
| **P** | churn_paper.json[churn_paper.json](sandbox:/workspace/scratch/d350cf940049/review-d10b/churn_paper.json) |
| **A** | runnerup_analysis.json[runnerup_analysis.json](sandbox:/workspace/scratch/d350cf940049/review-d10b/runs/runnerup_analysis.json) |
| **B** | convergence_analysis.json[convergence_analysis.json](sandbox:/workspace/scratch/d350cf940049/review-d10b/runs/convergence_analysis.json) |

**Reproduction this round:** both churn analysis commands reproduced their JSON outputs exactly after excluding input-path and provenance fields. The paper-generation command reproduced its summary exactly. The combined gain table, audit table, market-interval table, runner-up table, and new paired-change table were all byte-identical to the supplied files.

My digest comparison found that all **260 files under `records/`** and all **9 files under `reset_reference/`** are unchanged. The new results therefore come from additional analysis of existing records, not additional simulations.

No attempted manuscript or analysis-file read failed. An unmodified import of `test_churn_paper.py` did fail because it points to a missing directory, discussed below. Full simulation reproduction remains unavailable because the simulator is absent. Original Run A evaluation records and the frozen X7-SC arrays needed for a complete Run B replay are also absent. I distinguish checks on supplied summaries from reconstruction from underlying records.

## 2. Summary verdict

**This revision resolves the substantive reporting problems from the previous round, and the new paired analysis is correct and useful.** It now shows more clearly that R3’s measured relative performance deteriorates within the sampled markets, while keeping that finding separate from an ordering that would hold across other markets. The reference-reselection diagnostic, Run B selection, low-rate comparisons, W1 scope, and theory qualification are corrected. I found no new numerical error in the revised results. One interval-scope sentence still needs correction, partly because my own proposed wording last round was too broad. There are also small abstract, response-document, and test-path fixes. My scores remain **WEIS 2027: 3/5, upper borderline; AAMAS main track: 2/5; ACM EC: 1/5**. The paper’s reporting is stronger, but its scientific reach still rests on the same markets, comparator coverage, and incomplete churn searches. Those disclosed limits constrain the contribution; they do not make the present narrow conclusions false.

## 3. Follow-through on round-5 problems 1–11

Quoted passages below are from the revised paper. Where the problem concerns package contents, there is no corresponding manuscript sentence to quote.

| # | Judgment | Revised passage or evidence | Accuracy of `RESPONSE.md` |
|---|---|---|---|
| **1. Run A direction overstated** | **Resolved** | The abstract now says the direction “depends on the search version and is dominated by one market” (p. 1). Section 8 concludes: “The registered direction holds for C∗, not for verified-history targeting in general” (p. 11). Table 28 supplies all four comparisons (p. 31). | Accurate. The paper now distinguishes the pooled direction, market signs, and exploratory category. |
| **2. C∗ crossing stated too precisely** | **Resolved** | “With the frozen searches the pooled C∗ minus R3 difference changes sign between p = 0.01 and 0.02; with the doubled searches it is already −0.004 at 0.01” (p. 15). The abstract separates the two low-rate influence patterns (p. 1). | Accurate for the manuscript. The response’s shorter phrase that one market “sets the pooled sign at 0.02” should specify the **frozen** sign. |
| **3. “Survives moderate churn” concealed pooling** | **Resolved** | The abstract says the “pooled B3 minus R3 gap stays positive through 0.03, though negative on three markets there, and is negative at 0.05” (p. 1). | Accurate in substance. The response’s statement that the gap rises slightly at 0.01 applies to frozen searches only. |
| **4. Frozen-only diagnostics and unclear timing** | **Partly resolved** | Table 9 gives frozen and doubled values. Its caption states: “These statistics were defined after the results at p = 0.01 and 0.05 and before the runs at 0.02 and 0.03” (p. 19). | Accurate. The missing no-churn allocation row is expressly disclosed. That omission does not invalidate the current descriptions at nonzero rates. |
| **5. Efficiency omitted doubled results and the low market value** | **Resolved** | “On fresh2 at p = 0.05, R3’s efficiency under attack is 0.893, below the registered threshold of 0.90; this is an exploratory point estimate, not a registered failure” (p. 16). Both versions appear in Table 9. | Accurate. |
| **6. −0.052 reported without the doubled result** | **Resolved** | The abstract and conclusion now include “−0.033 with the doubled searches” and explain that the frozen value includes “one search-flagged cell with a large improvement under doubling” (pp. 1, 19). | Accurate in substance. The older response row still calls this a “failed-search note”; update that label. |
| **7. Claim about the whole comparator class** | **Resolved** | “Only one verified-history comparator, C∗, was run under churn” (p. 16). The conclusion repeats that scope (p. 19). | Accurate. |
| **8. Mechanism evidence covered only attacks that stay old** | **Resolved for the requested description** | The paper reports replacing and non-replacing attacks’ audit-rate ranges under both versions, then adds that the attacker is uniquely newest in “only 0.008 to 0.033 of the rounds in which it holds jobs (frozen)” (pp. 15–16). | The earlier response row is stale or ambiguous. The paper gives a range, and the JSON now supplies the per-market values. The later external-review response describes this correctly. |
| **9. Churn search flags remain** | **Resolved as disclosure; search limitation remains** | “21 of the 72 churn doubling checks are flagged incomplete” (abstract, p. 1). Section 10 reports the component counts and largest change (p. 15). | Accurate that no churn searches were continued. Disclosure was an allowed resolution of the reporting problem. |
| **10. Missing package files** | **Resolved for the named omissions** | The amendment and Run A/B drivers are present. This is a package correction, not a revised manuscript sentence. | Accurate. The separate test-path problem remains, as do the stated limits on full reproduction. |
| **11. Cross-references and small wording errors** | **Resolved** | The reset references point to Section 9; Run A uses “runner-up minus R3” (p. 11); audit rates are stated numerically (p. 15). | Accurate. The conclusion ends on p. 19; Availability and Appendix A begin on p. 20. |

### Follow-through on my immediate previous review

The important corrections are present:

- The reference diagnostic is now explicitly a **training-set reference-score change**, with an explicit statement that it does not bound held-out gain changes (p. 15).
- Run B is correctly described as **14 flagged cells plus 5 unflagged X7-SC cells** (p. 11).
- The abstract correctly separates the comparison at 0.01 from the influence pattern at 0.02 (p. 1).
- The theory remark now requires newer jobs to exhaust the relevant quota before claiming that coverage can be zero (p. 7).
- The zero-gain W1 statement is restricted to R3 and C∗ (p. 19).
- The newest-identity statistic has been extracted from existing diagnostics and reported with its denominator (p. 16).
- The paired-change analysis has been added with a clear post hoc label and all rates shown (pp. 15, 18).

The separation of registered calibration from exploratory intervals is also improved. The remaining issue is the blanket statement that all follow-up intervals condition on fixed markets. **My own suggested replacement last round used that wording too broadly. The author followed that recommendation; the correction below also corrects my recommendation.**

## 4. Honest-churn section

### A. Plan fidelity and amendment timing

**The supplied files support the stated sequence, and expectations 5–8 are scored as written.**

The amendment expressly says it was written after the endpoint results were known and before searches at the two new rates. Its scoring rule is unchanged: an expectation is “met” when it holds under both search versions, each using its own values, on point estimates.

The operations ledger records the amendment at commit `2604ce6`, the launch at `e1c925a`, and the subsequent results separately. This is internally consistent with the plan and run metadata. I cannot independently authenticate the historical commit sequence from a ZIP without its repository history. I therefore accept this as **documented prospective specification within an exploratory follow-up**, rather than independently verified registration.

The numerical scoring is straightforward:

| Expectation | Frozen searches | Doubled searches | Judgment and source |
|---|---|---|---|
| **5. First-bin audited share falls across the four rates** | 0.880, 0.789, 0.706, 0.571 | 0.854, 0.790, 0.706, 0.570 | Met as written. **M**, `expectations["5"]`. |
| **6. C∗−R3 is lower at 0.03 than at 0.02** | −0.090 < −0.020 | −0.063 < −0.021 | Met. **M**, `expectations["6"]`. |
| **7. R3 gain at 0.02 is below the endpoint midpoint** | 0.111122 < 0.168328 | 0.111975 < 0.169948 | Met. **M**, `expectations["7"]`. |
| **8. B3−R3 is positive on at least five markets at 0.02** | 5 of 6 | 6 of 6 | Met. **M**, `expectations["8"]`. |

Expectations 1–4 also remain met under both versions, as recorded in **C**, `expectations`.

The paper correctly distinguishes three stages: expectations specified before their relevant searches, allocation statistics defined after the first endpoint results, and the new paired comparison added after external review. The new table is not presented as another registered confirmation.

### B. Numerical reproduction

Here, \(d=g(C^*)-g(R3)\) and \(q=g(B3)-g(R3)\). Positive values mean that R3 leaves the attacker less measured gain. In the JSON, `base` means frozen searches, `F111` is R3, and `F000` is B3.

| Item | Paper value | My value or check | Source |
|---|---|---|---|
| **Table 6, all gains, contrasts, and seed intervals** | As printed, p. 17 | Exact regenerated table, including all intervals | **C/M**, `statistics`; `posthoc_churn_all.tex` |
| **Table 7, all market-level intervals** | As printed, p. 17 | Exact regenerated table | **C/M**, `review_r4.t95`; `posthoc_churn_t.tex` |
| **Table 9, all allocation, replacement, and efficiency entries** | Frozen/doubled entries, p. 19 | Exact regenerated table | **C/M**, `review_r4`, diagnostics; **P**, `rates`; `posthoc_churn_audit.tex` |
| **Table 8, paired changes** | All rates and both versions, p. 18 | Exact regenerated table; independently checked pairing and t-interval arithmetic | **C/M**, per-market `d` and `q`; `churn_paper.py::deltas` |
| R3 gain at 0.05 | 0.272 under both versions | 0.271749 frozen; 0.272445 doubled | **C**, `statistics[version]["0.05"].g.F111.pooled.estimate` |
| C∗−R3 at 0.05 | −0.173 / −0.169 | −0.173430 / −0.168962 | **C**, `statistics[version]["0.05"].d.pooled.estimate` |
| B3−R3 at 0.05 | −0.052 / −0.033 | −0.051982 / −0.032520 | **C**, corresponding `q.pooled.estimate` |
| R3 attacker audit rates across the four rates | Frozen: 0.366, 0.190, 0.093, 0.042. Doubled: 0.505, 0.188, 0.093, 0.028 | Match at printed precision | **C/M**, `review_r4.audit_allocation`; **P**, `rates` |
| R3 allocation at 0.05 | Young honest job share 0.391/0.394; audit share 0.823/0.828; established honest audit rate 0.078/0.078 | Match | **C**, `review_r4.audit_allocation` |
| R3 winners without replacement | Frozen: 2, 2, 3, 3. Doubled: 0, 2, 3, 3 | Match | **P**, `rates[rate].R3.x_off` and `x_off_doubled` |
| Efficiency at 0.05 | R3: 0.967/0.949; C∗: 0.993/0.993; B3: 0.940/0.959 | Match | **C**, `review_r4.eff_attack`; **P**, `rates["0.05"]` |
| R3 efficiency on fresh2 at 0.05 | 0.893 | 0.893498 under both versions | **C**, `review_r5.eff_by_market` |
| Replacing attackers’ audit-rate ranges at 0.05 | 0.041–0.095 frozen; 0.037–0.051 doubled | Match at printed precision | **C**, `review_r5.focal_audit_rate_by_market`, classified using selected attack knobs |
| Non-replacing attackers’ audit-rate range at 0.05 | 0.012–0.015 under both versions | Match | Same fields and classification |
| Churn flags | 13/36 plus 8/36; total 21/72 | Exact | **C/M**, `flag_summary` |
| Largest flagged change | 0.088 | 0.0877435 | **P**, `flags.max_attack_change` |
| Reference-score diagnostic | 32/72 nonzero changes; largest absolute change about 0.009 | 32/72; 0.00948488 | **P**, `flags.reselected`, `flags.max_reference_change` |
| Raw R3 attack-profit change at 0.05 | +113.101 | +113.100728 | **C**, `statistics.base["0.05"].change.profit.F111.attack.pooled` |
| Raw reference-profit change | −0.146, interval [−0.393, 0.098] | −0.145609, [−0.392719, 0.097955] | Same branch, `reference.pooled` |
| Honest replacements per episode | 17.901, 35.777, 53.790, 89.582 | Match at printed precision | **C/M**, `diagnostics[rate]["F111\|base"].honest_replacements_per_episode` |
| No-churn audit-allocation baseline | Not supplied | **Not checkable from the supplied allocation outputs** | No corresponding p=0 allocation block |

The reference-score wording is now accurate. In particular, the paper no longer turns the small training-score change into a bound on held-out gain.

#### The new paired-change result

I checked the calculation

\[
\Delta d_m(p)=d_m(p)-d_m(0),\qquad
\Delta q_m(p)=q_m(p)-q_m(0),
\]

using each market’s own baseline and the same search version on both sides. The intervals use the variation across those market-level changes, with five degrees of freedom.

The following values reproduce Table 8, rounded as in the paper. The source is **C/M**, `statistics[version][rate].d.markets` and `.q.markets`, followed by the calculation above.

| Version | Rate | Change in C∗−R3, market t interval | Markets lower | Change in B3−R3, market t interval | Markets lower |
|---|---:|---|---:|---|---:|
| Frozen | 0.01 | −0.019 [−0.069, 0.030] | 5/6 | +0.001 [−0.033, 0.035] | 4/6 |
| Frozen | 0.02 | −0.041 [−0.112, 0.030] | 5/6 | −0.055 [−0.098, −0.011] | 6/6 |
| Frozen | 0.03 | −0.111 [−0.220, −0.002] | 6/6 | −0.106 [−0.193, −0.018] | 6/6 |
| Frozen | 0.05 | −0.194 [−0.381, −0.008] | 6/6 | −0.225 [−0.415, −0.036] | 6/6 |
| Doubled | 0.01 | −0.034 [−0.084, 0.016] | 6/6 | −0.016 [−0.025, −0.008] | 6/6 |
| Doubled | 0.02 | −0.051 [−0.117, 0.016] | 6/6 | −0.043 [−0.086, 0.001] | 6/6 |
| Doubled | 0.03 | −0.093 [−0.179, −0.006] | 6/6 | −0.101 [−0.185, −0.017] | 6/6 |
| Doubled | 0.05 | −0.199 [−0.378, −0.019] | 6/6 | −0.202 [−0.376, −0.029] | 6/6 |

This supports the new sentence:

> “at p = 0.03 and 0.05, both contrasts are lower than without churn on every sampled market under both search versions.” (p. 15)

The paper also correctly states:

> “These paired comparisons were computed after an external review, are unadjusted, rest on six markets, and omit search uncertainty.” (p. 15)

This is a useful addition. A contrast can deteriorate consistently from its own baseline while its absolute level remains uncertain across markets. Table 8 therefore does not conflict with Table 7. Showing every rate, including the positive frozen change in \(q\) at 0.01 and intervals that contain zero, also avoids selecting only the strongest rows.

### C. Comparative and universal wording

I found no new sign error in the abstract, contributions, Section 10, limits, or conclusion.

| Claim | Check under both search versions |
|---|---|
| **R3’s attacker audit rate “falls” across the tested rates** | Correct under both versions. Table 9 and **P**, `rates`. |
| **The comparison with C∗ is unresolved at the two lowest rates** | Supported. At 0.01 the pooled sign changes across versions; at 0.02 both pooled values are negative, but the market values are strongly unequal. **C/M**, per-market and pooled `d`. |
| **One market determines the sign at 0.02** | Correct with the new **frozen-search** qualification. It should not be extended to both versions. **M**, per-market `d`, with leave-one-market-out averaging. |
| **C∗−R3 is negative on every market at 0.03** | Correct under both versions. **M**, `statistics[version]["0.03"].d.markets`. |
| **B3−R3 remains positive through 0.03** | Correct as a **pooled** statement. The paper now states that three market values are negative there under each version. **M**, corresponding `q` fields. |
| **Both pooled advantages reverse at 0.05** | Correct. The paper also preserves the distinction between six negative market values frozen and five doubled. **C**, per-market and pooled `d` and `q`. |
| **B3−R3 rises slightly at 0.01** | Correct for frozen searches only. The paper distinguishes the versions; the response should add that qualifier. **C**, `q.pooled.estimate`. |
| **Selected attacks “never” replace** | Correctly restricted to selected policies, rates, and search versions. The doubled 0.01 exception is stated. **P**, replacement counts. |
| **R3 efficiency falls; B3 shows no clear monotone pattern** | Consistent with both versions of Table 9. **C/M**, `review_r4.eff_attack`. |
| **“Every fresh market” in the registered advantage statement** | Correctly restricted to no honest churn and measured gain. The paper separately reports the registered replication failures. Abstract and conclusion, pp. 1, 19. |
| **“Only one” comparator under churn** | Correct. Run A has no churn arm. Section 10 and the Run A plan. |
| **All eight expectations are met** | Correct under their point-estimate scoring rule. **C/M**, `expectations`. |
| **Both contrasts deteriorate on every sampled market at the two higher rates** | Correct under both versions. New Table 8. |

The claim that almost all market-level intervals contain zero concerns **the contrast at a given churn rate in Table 7**. It should continue to be read separately from the paired-change intervals in Table 8.

### D. Mechanism

**The mechanism paragraph is now adequately supported as a descriptive account.**

It covers both relevant selected behaviours. Some attackers remain old and receive little attention after their priority window. Others replace, but are rarely uniquely newest among identities holding jobs. The new statistic adds direct evidence for the latter description.

For the replacing R3 attacks at 0.05, I checked these frequencies against the raw diagnostic arrays:

| Market | Frozen | Doubled |
|---|---:|---:|
| fresh0 | 0.033350 | 0.012010 |
| fresh3 | 0.008340 | 0.008340 |
| fresh5 | 0.018200 | 0.004783 |

Source: `records/churn/p0.05/diagnostics.json`, `shares.focal_newest_by_first_offer_assigned`, reproduced in **C**, `review_r5.focal_newest_by_market["0.05"]`.

The denominator matters. These are means of within-episode shares of rounds **in which the attacker holds jobs**, using first-offer dates and excluding ties. The paper states the main definition correctly.

One interpretive distinction should remain clear: being uniquely newest among all job-holding identities is stronger than being uniquely newest among established identities. The new frequency is useful descriptive evidence, but it is not the exact frequency with which every condition of the residual-targeting lemma holds. The paper does not currently make that stronger inference.

The causal qualification is appropriate:

> “The diagnostics describe the setting; they do not isolate the cause, because churn also resets histories, ends bans, and changes the selected attacks.” (p. 16)

No new causal claim needs to be removed. The missing no-churn allocation baseline would improve the description, but it is not needed to validate the allocation measurements at nonzero rates or the new paired performance analysis.

## 5. Run A and Run B

### Run A

The placement and labels are now correct. It is an exploratory comparison without churn. Its category uses nominal intervals and the registered margin, rather than repeating the registered calibration and Holm procedure.

The unchanged summary gives:

| Family | Version | Runner-up−R3 | Market t interval | Markets where R3 has lower gain | C∗−runner-up |
|---|---|---:|---|---:|---:|
| D2+H3 | Frozen | −0.010235 | [−0.036377, 0.015908] | 4/6 | +0.030955 |
| D2+H3 | Doubled | −0.004518 | [−0.033535, 0.024499] | 4/6 | +0.034143 |
| X7-SC | Frozen | −0.007233 | [−0.034577, 0.020111] | 4/6 | +0.031552 |
| X7-SC | Doubled | +0.002820 | [−0.004373, 0.010013] | 5/6 | +0.021470 |

Source: **A**, each family/version’s `runner_up_minus_r3.markets` and `cstar_minus_runnerup`; market intervals calculated from those values. These files are unchanged from the previous review.

Fresh5 contributes most of the frozen D2+H3 pooled difference, but removing it does not reverse that difference’s sign. The revised wording is accurate.

Run A limits the permitted generalisation from the registered comparison. The registered direction remains a result about the particular C∗. The runner-up results do not establish the same direction for verified-history targeting as a class, and they provide no churn comparison.

The reported search-flag counts agree with the analysis summary. Their original Run A evaluation and doubling records remain unavailable, so I cannot independently reconstruct the seed intervals and flags from raw Run A records.

### Run B

The corrected main-text description is accurate:

> “Continued searches of 19 registered cells, 14 whose doubling check was flagged and 5 unflagged X7-SC cells with held-out shortfalls…” (p. 11)

I independently checked the new selection count by matching the continuation cells against `records/report.json`. It agrees with **B**, `selection`.

The aggregate results remain:

- C∗−R3 under D2+H3: **0.028191**.
- B3−R3 under D2+H3: **0.169469**.
- Largest market change in the first contrast: **0.053827**, on fresh3.

Source: `records/convergence/recompute.json`, `q1.converged`, `q4.converged`, and the per-market comparison; the previous independent D2+H3 reconstruction carries forward because these inputs are unchanged.

The paper correctly describes passing an incremental-improvement check and explicitly states that this bounds neither global convergence nor remaining search error. It also says that Run B contains no churn cells. It therefore does not resolve the churn search flags, and the revised main text does not imply that it does.

One obsolete shorthand remains in the abstract: “continued searches of the flagged cells.” Change that to “continued searches of selected cells.”

## 6. Structure, length, and title

**The paper has a clear scientific centre, but that centre still arrives too late in the reading sequence.**

The actual subtitle is:

> “Registered Tests of Age-Ranked Audits and an Exploratory Limit Under Honest Churn” (p. 1)

That is honest about the status of the churn result.

The present layout is less effective. Honest churn begins on p. 14. Section 11 begins on p. 16, but the churn tables continue on pp. 17–19. Figure 1 appears on p. 18. The audit-allocation table sits immediately above the conclusion on p. 19. These placements separate the evidence from the paragraphs interpreting it.

The abstract is approximately **533 whitespace-separated words**, by my count of the extracted abstract text. It now carries nearly the whole review history: registered results, continuation results, runner-up results, reset results, churn levels, market influence, uncertainty, search flags, and comparator selection.

My editorial changes would be:

1. **Move Figure 1 near the introduction**, with its exploratory status retained in the caption.
2. **Keep the main churn evidence together**, before Section 11 begins.
3. **Move the conditional renewal theorem and detailed calibration account to the appendix**, retaining the assumptions and inferential scope needed to read the main results.
4. **Shorten the abstract substantially**, preserving the central result and its principal limits.
5. **Reduce repeated qualifications across Sections 10–12.** State the full scope carefully once, then use short reminders where necessary.

The response accurately says these structural changes have not been made. The new paired table is worth keeping; it does not justify expanding the surrounding prose further.

## 7. Remaining problems, ranked by severity

I found no new calculation error. The remaining corrections are limited.

### 1. The global interval-scope wording is too broad

**Severity: moderate precision problem. Fix: text only.**

Section 10 says:

> “It is an exploratory follow-up after the report: it changes no registered decision, and its intervals hold the six markets and the selected policies fixed.” (p. 14)

The conclusion says:

> “The registered Q1 and Q4 inferences use calibration admitted on development fixtures; the follow-up intervals are exploratory and condition on the six markets, the selected policies, and the frozen reference menus, and the doubled searches are sensitivity analyses.” (p. 19)

The fixed-market description applies to the seed-bootstrap intervals. The market-level t intervals use variation across markets and treat those markets as a sample.

**Replace the scope wording on p. 14 with:**

> “This exploratory follow-up changes no registered decision. Its seed-bootstrap intervals condition on the six markets. Its market-level t intervals use variation across those markets. Both condition on the selected search outputs and omit search uncertainty.”

**Replace the quoted conclusion sentence with:**

> “The registered Q1 and Q4 inferences use calibration admitted on development fixtures. The follow-up intervals are exploratory: seed-bootstrap intervals condition on the six sampled markets, while market-level t intervals treat those markets as a sample. Both hold selected attacks and references fixed and omit search uncertainty. The doubled searches are sensitivity analyses.”

Again, the previous wording partly follows my own overly broad recommendation. This is a correction to that recommendation, not a failure to apply it.

### 2. The supplied test still uses a repository-specific path

**Severity: minor reproduction problem. Fix: analysis on existing records.**

`test_churn_paper.py` contains:

```python
RUNNERUP = json.loads(
    (HERE.parent / "followup2" / "runnerup_analysis.json").read_text()
)
```

An unmodified import fails with `FileNotFoundError`. The supplied file is under `runs/`.

**Exact fix:**

```python
RUNNERUP = json.loads(
    (HERE / "runs" / "runnerup_analysis.json").read_text()
)
```

Then run the packaged tests against the supplied records. This requires no new simulation. It does not affect the successful reproduction commands used above.

### 3. The abstract retains the old Run B selection shorthand

**Severity: minor factual shorthand. Fix: text only.**

The abstract says:

> “after exploratory continued searches of the flagged cells” (p. 1)

The continuation set also contains unflagged cells.

**Exact fix:**

> “after exploratory continued searches of selected cells”

The detailed sentence on p. 11 is already correct.

### 4. The response document mixes earlier and current states

**Severity: minor documentation problem. Fix: text only.**

The older round-5 response says:

> “The newest-identity frequency per market is not added.”

The paper now reports a range, and the JSON contains the per-market values. The later external-review section correctly describes the addition.

**Replace the older sentence with:**

> “The paper now gives the frozen newest-identity frequency range for replacing attacks at p = 0.05. Complete per-market values under both search versions are in `review_r5.focal_newest_by_market`. The p = 0 audit-allocation baseline remains absent.”

Also qualify the response’s sign statement at 0.02 as **frozen**, qualify the slight increase in B3−R3 at 0.01 as **frozen**, and replace “failed-search note” with the current search-flag wording.

These are small consistency edits. They should not trigger another broad rewrite or another required experiment.

## 8. Venue decisions

The acceptance probabilities below are subjective editorial judgments, not calibrated forecasts. The unchanged scores reflect the remaining scope of the evidence, rather than a penalty for reporting failed predictions or incomplete searches honestly.

| Venue | Score | Acceptance probability | Confidence | Single change most likely to move the score |
|---|---:|---:|---|---|
| **WEIS 2027** | **3/5, upper borderline** | **50%** | Medium | A prospectively specified churn validation on newly drawn markets, including the runner-up comparator and stronger search checks. This would test whether the central finding survives the present market and comparator choices. |
| **AAMAS, main track** | **2/5** | **15%** | Medium | A churn-adapted audit rule with a clear design principle and demonstrated benefit against the current rules under strong attack searches. That would broaden the paper from a limitation study into a more general mechanism contribution. |
| **ACM EC** | **1/5** | **3%** | High on the current score; low on the precise probability | A substantive incentive result under endogenous identity turnover, connecting audit capacity, replacement incentives, and provider behaviour. The current empirical contribution is too narrow for a strong EC case in my judgment. |

**I would treat the correctness review as nearly complete.** Fix the interval wording, abstract shorthand, response consistency, and test path. Then shorten the presentation. The current limited empirical claim is defensible; a stronger publication case now depends mainly on broader evidence or a more general result.
