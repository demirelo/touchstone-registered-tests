claude-fable-5-2

**→ Ambition.** The cheapest outside check is a nesting test on the records you already have: X7-SC contains D2+H3, so each X7-SC cell must reach at least the doubled D2+H3 gain. At least one cell fails this (new problem 2).

**Mistake:** my first report counted 11 of 14 embedded cells; the correct count is 12. **Guard:** I now count cell by cell from Table 23 and `stability-result.json`.

**Mistake:** my first report said the margin was set after the development values; the files do not support that. **Guard:** I state a timing claim only when a dated record is in the materials.

## 1. Files read

The session blocked Python and awk. All recomputation is hand arithmetic on values that I read with the file and search tools.

- **Read in full:** `main.pdf` (30 pages), `RESPONSE.md`, `PREVIOUS_REVIEW.md`, `posthoc_v2.py`, `predictions-v2.md`, `addendum.md`, `protocol-v2.yaml`.
- **Read in part:** `posthoc.json` (lines 1136 to 1778, plus the honest-replacement bins).
- **Read in part:** `report.md` (the first 160 characters of every line; full text of the Q1, Q2 conditional, envelope and flag-list entries).
- **Read in part:** `stability-result.json` (all `mean_old` values), `operations-ledger.md`, `revision-program-design.md` and `eligibility.json` (search hits only).
- **Not opened in this round:** `audit.json`, `audit_v2.py`, `scoring.json`, `score_v2.py`, `test_scoring.py`, `lottery_seeds.csv`, `lottery_train.csv`, `h4-family.py`, `h4-containment.md`. I make no new claim about them.
- **Not a text file:** `default.profraw`.

## 2. Summary verdict

The revision is honest and every new number that I could check reproduces. It adds no new evidence. The three main gaps (honest churn, comparator choice, search strength) are now stated but not closed.

The revision also introduces one distortion. It now stresses doubt about the sign of the Q1 difference, but the records make the sign fairly stable. The weak part is the size and the comparator.

Scores: **WEIS 2/5 (upper end), AAMAS 2/5, EC 1/5.**

## 3. Follow-through

| # | Item | Status | Revised sentence (page) | What remains |
|---|---|---|---|---|
| 1 | "Equivalent" and the margin | Partly resolved | "The D2+H3 interval contains zero and crosses the margin, so this analysis does not establish the category for the neighbourhood" (p. 13) | Figure 1 and Table 7 still show only [0.020, 0.022]. I withdraw the margin-timing point; the commit dates are not in the materials. |
| 2 | Two Q1 families | Resolved | "The two Q1 families are close to one test: X7-SC's search starts from the embedded D2+H3 winner, and in 10 of the 12 Q1 cells it selected that winner" (p. 13) | "Results in brief" (p. 3) still lists both families without this note. |
| 3 | Search strength | Partly resolved | "21 of the 98 doubling checks are flagged, and fresh-market factorial cells outside Q1 and Q4 have no doubling check, so their narrow intervals describe seed noise only." (p. 16) | Needs compute. See new problem 2. |
| 4 | Honest churn | Partly resolved | "so a new identity marks a replacement history, not dishonest delivery. Population churn among honest opponents is untested" (p. 4) | Needs compute. |
| 5 | Comparator selection | Partly resolved | "The efficiency margin was the smaller at every configuration, so the selection was in effect on gross efficiency" (p. 6) | Needs compute. See new problem 3. |
| 6 | Corollary 1 | Partly resolved | "against honest rivals whose play does not depend on the focal identity, when re-entry comes before the next allocation" (p. 7) | The introduction (p. 2) and conclusion (p. 26) omit the honest-rival condition. The response says the introduction has it. |
| 7 | Lemma 2, Theorem 1 | Resolved | "An identity's age is the number of rounds since its first offer." (p. 4); "No reported result depends on it." (p. 7) | Theorem 1 is still in the main text. |
| 8 | Contribution (iii) | Partly resolved | "the W1 search found no profitable welfare attack against them" (p. 15) | The conclusion still gives four sentences to mixtures. Table 16 still says "supported". |
| 9 | Priority phase | Resolved | "once it is in place, R3's priority window changes the attacker's gain by only −0.001" (abstract) | See new problems 4 and 5. |
| 10 | Statistics | Partly resolved | "this measures uncertainty over seeds in the six fixed markets, not over new markets or repeated searches" (p. 10) | Calibration detail still comes before the results. |
| 11 | Process facts | Resolved | "the executor resumed the same session at the author's instruction, without reading its log or bundle" (p. 10); "Q3-e passes by less than one hundred-thousandth" (p. 17) | "Executor" is not defined. |
| 12 | Related work | Resolved | "history-dependent audit groups under restricted penalties go back to [18]" (p. 3); [9] and [17] are cited on p. 3 | I could not check the DOIs online in this session. They match my memory. |
| 13 | Presentation | Partly resolved | "Four findings." (abstract) | The abstract still uses the codes B2, B3, R3, C*, D2+H3. The paper is 30 pages. |

## 4. New-number checks

| Item | Paper | My value | Source |
|---|---|---|---|
| Market interval, D2+H3 frozen | [−0.013, 0.054], 5 of 6 | **[−0.0128, 0.0542], 5 of 6, reproduced** | Hand t interval (5 degrees of freedom) on `posthoc.json` `doubled.markets`; same values as report lines 13 to 18 |
| Market interval, X7-SC | [0.005, 0.044] | **[0.0047, 0.0440], reproduced** | Same method |
| Market interval, doubled D2+H3 | [0.014, 0.045], 6 of 6 | **[0.0139, 0.0453], reproduced** | Same method. I did not recompute the per-market doubled values. |
| Relative difference | 0.319 | **0.3192, reproduced** | 0.08563 / 0.06491 − 1, `posthoc.json` `absolute` |
| Embedding, 10 of 12 | 10 | **10, reproduced on cell means** | `stability-result.json` `mean_old`; the pairs differ at fresh3 C* (0.0345, 0.0684) and fresh4 R3 (0.0057, 0.0181) |
| Embedding, 12 of 14 | 12 | **12, reproduced** | Table 23 row Q3-a: 12 zeros; report line 19 |
| Envelope difference | 0.031; 0.070 on fresh1 | **0.0306; 0.0700, reproduced** | Report lines 165 and 166 |
| Doubling flags | 21 of 98 | **21 of 98, reproduced** (14 profit, 7 coalition) | Report lines 207 to 304 and line 310 |
| P given G=1 | −0.001 | **−0.0014 [−0.0015, −0.0013], reproduced**; X7-SC gives −0.0039 | Report lines 32 and 33 |
| Table 24 | scores 0.103, 0.098; C* gains 0.097, 0.038 | **Partly reproduced** | Ledger line 56 (0.1032, 0.0975); `predictions-v2.md` line 19 |
| Table 24, other cells | runner-up 0.076, 0.018; inner rows | **Not checkable** | No development records in the materials |
| Honest-replacement shares | R3 1.000, 0.917, 0.933; C* 0.428, 0.161, 0.231; B3 about 0.250 | **Reproduced** | `posthoc.json` `honest`; report lines 191 to 193 |
| Honest-replacement profit, refunds | 2.84, 2.74, 2.86; 0.78, 2.01, 0.59 | **Reproduced**; R3 is 4.4 percent below C* | `posthoc.json` `honest` means |

Not checkable: the `best_source` field behind the embedding count, and the "follow-up cap 22 USD" (the ledger copy has no such entry).

## 5. Theory

**→ Corollary 1 is now correctly scoped as a conditional statement.** Both inequalities in the proof hold under the two stated conditions. With zero continuation loss, Lemma 1 gives the stated shading condition.

**→ Two limits remain.** The claim that B2 and B3 satisfy both conditions rests on the rule definitions, which I cannot check without the code. The result uses the absence of identity-linked state, not audit uniformity, so the title "uniform auditing" names the wrong property.

**→ Lemma 2 wording is right.** The hypergeometric count with k′ = min{n, max(0, k − H)} is correct. The remark's bound min(s, ⌈r/2⌉) matches the selection rule on p. 5.

**→ One consistency check supports it (my reasoning).** The allowance is about 0.25 audits per job. That gives about 10.5 audits per round before the reserve. Half of that against 6 jobs gives 11/12 = 0.917, which is Table 6's value.

**→ Proposition 1 is unchanged and correct.** The bound is 0.0668 (1.4 × φ(3.2) / 0.05, my computation).

## 6. New problems, ranked

**1 → The paper now overstates doubt about the sign and understates doubt about the size. (Text only.)**
Quote (p. 26): "across markets the difference varies in sign, and this analysis does not establish the ordering for the neighbourhood."
- The only negative D2+H3 market is fresh3, and its cell is search-flagged. With the doubled winner it is +0.015 (Table 5).
- Doubled winners: 6 of 6 positive, [0.014, 0.045]. Envelope: 6 of 6 positive, t interval [0.010, 0.052] (my computation).
- The abstract quotes only the frozen interval.
- The upper ends (0.054, 0.045, 0.052) are at the margin. "Equivalent" is the fragile label, not "R3 lower".
- Fix: report all three intervals together. This point favours the authors' rule.

**2 → Unflagged X7-SC cells are under-searched. (Analysis on existing records.)**
- X7-SC embeds D2+H3 (design line 230).
- On fresh3 against C*, the doubled D2+H3 winner reaches about 0.088. I infer this from Table 5 and report lines 225 and 229.
- The X7-SC cell there is 0.068, and its doubling check passed (change 0.0011, report line 226).
- So the doubling check passes a cell that is at least 0.018 short. "Answered" labels for X7-SC do not hold.
- Fix: run the nesting test on every cell pair and list the failures.

**3 → The comparator caveat lacks its arithmetic, and the runner-up is not a gain-selected comparator. (Text only.)**
Quote (p. 6): "C* is the best of four tested adaptations under the development objective".
- The runner-up's development gain is lower by 0.021 (headline) and 0.020 (dev0). The pooled Q1 difference is 0.021.
- If that offset holds on the fresh markets, the difference is near zero (my reasoning).
- Table 24 shows five inner scores tied at 0.106 behind 0.107. The paper does not say how it picked the runner-up.
- The inner searches found no attack, so the selection compared efficiency under non-attacks on 3 seeds (design line 169).
- "Best of four" is too strong. Only two configurations got a full-budget check.

**4 → "Newest-first targeting does almost all the work" is one side of a symmetric result. (Text only; a budget sweep needs compute.)**
- P alone gives −0.165 and G alone gives −0.177, of −0.178 total (report line 32).
- The substitution is close to mechanical (my reasoning). Half the round's quota already covers nearly all jobs of one provider.
- It can fail at a lower audit ratio or a larger attacker capacity. The paper does not state this scope.

**5 → The −0.001 is below the search error. (Text only.)**
Headline factorial cells move by up to 0.044 under doubling (report line 283). X7-SC gives −0.004. Write "small against −0.165", not a value.

**6 → The abstract's welfare sentence omits that the attack loses money. (Text only.)**
Against R3 and C* the gain is −0.094 (report lines 174 and 178).

**7 → The corollary's conditions differ between abstract, introduction and conclusion. (Text only.)** See row 6 above.

**8 → Table 24 does not show the deciding cells. (Text only.)** The scores cannot be recomputed from the columns shown.

**9 → The third finding quotes C*'s lowest bin. (Text only.)** C* is 0.161 in bin two, and 0.19 to 0.23 afterwards (`posthoc.json`).

## 7. Readiness for WEIS 2027

**Not ready.** I do not know the WEIS 2027 deadline or page limit; verify both.

Blockers, in order:
- **1 →** No honest-churn result. The main findings depend on its absence.
- **2 →** The Q1 direction depends on a comparator that a 0.001 efficiency difference selected.
- **3 →** No short version. The 30-page paper reads as an audit record.
- **4 →** New problems 1 and 2. They are free and change how Q1 reads.

## 8. Decision

| Venue | Score (1 to 5) | Acceptance probability | Confidence | Change that moves it most |
|---|---|---|---|---|
| WEIS 2027 | 2 (upper end) | 25% | Medium | The honest-churn arm, with the paper cut to 12 pages around it |
| AAMAS main track | 2 | 10% | Medium | Converged searches plus the nesting test on every cell |
| ACM EC | 1 | 3% | High | A real theorem on age-ranked audits under a quota. No planned simulation helps. |

**Which simulations change my decision:**

- **→ Honest-churn arm: yes, the most.** Either outcome moves WEIS to 3 and about 40 to 45 percent. If R3 keeps its advantage, the result is positive with a measured newcomer cost. If it loses it, the result is a clean negative.
- It must include B3, R3 and C*, at least two churn rates, and the fresh markets. A headline-only arm at one rate changes nothing.
- **→ Runner-up comparator: it changes the claim, not the score.** If the difference falls to near zero, finding (i) becomes "no measurable difference", which is cleaner. If it stays near 0.02, "R3 lower" gains support, about +5 points for WEIS.
- Label it exploratory. It was chosen after the results.
- **→ Convergence searches: only for AAMAS.** If all 14 cells pass and the nesting test passes, AAMAS moves to about 15 to 20 percent. For WEIS the effect is small.
- Convergence on the 14 flagged cells alone is not enough, because unflagged cells also fail (new problem 2).

**Next action:** run the nesting test and rewrite the Q1 sign statement first. Both use existing records.
