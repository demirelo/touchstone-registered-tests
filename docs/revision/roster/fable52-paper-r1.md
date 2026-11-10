claude-fable-5-2

**→ Ambition.** The outside check this paper most needs is an honest-churn arm (honest providers also replace identities), because the main findings depend on its absence; see problem 4.

## 1. Files read

I could not run code: the session blocked Python. All recomputation below is hand arithmetic on values in the files.

- **Read in full:** `main.pdf` (29 pages), `protocol-v2.yaml`, `predictions-v2.md`, `addendum.md`, `stability-result.json`, `audit.json`, `scoring.json`, `operations-ledger.md`, `h4-family.py`, `h4-containment.md`.
- **Read in part:** `revision-program-design.md` (sections 3 to 9 only).
- **Read in part:** `report.md` (lines 1 to 40 in full; lines 163 to 302 cut at 400 characters; Q2 per-market lines 41 to 162 not read).
- **Read in part:** `eligibility.json` (flag list and tallies only), `posthoc.json` (Q1 split and lottery blocks only).
- **Read in part:** `lottery_seeds.csv` and `lottery_train.csv` (header, first rows, row counts).
- **Outline only:** `score_v2.py`, `test_scoring.py`, `audit_v2.py`, `posthoc_v2.py` (function names and assert lines). I make no claim about their logic.
- No file failed to open.

## 2. Summary verdict

The paper is honest and its numbers match its outputs. Its conclusions are narrower than its framing. The main result is a null: R3 and a history-based comparator differ by 0.021 in attacker gain. The "equivalent" label comes from a wide margin, and three things can change it: search error as large as the margin, variation between markets, and a comparator that was not selected on gain. The two Q1 "families" are mostly one test. The model has no honest churn, so identity age labels the attacker almost perfectly. The theory is correct but thin. The paper reads as an audit record, not as a finding.

Scores: **WEIS 2/5, AAMAS 2/5, EC 1/5** (details in section 8).

## 3. Claims

| # | Claim | Evidence | Verdict |
|---|---|---|---|
| 1 | Under uniform audits with free replacement, a ban costs nothing | Corollary 1, proof sketch | **Narrower.** True if rivals are honest and do not react, re-entry loses no round, and the rule keeps no identity memory. B2's memory is not checkable. |
| 2 | R3 and C* are equivalent within ±0.05, R3 lower, under two attack families | Report Q1 lines 9 to 18 | **Narrower.** The point estimates reproduce. "Equivalent" depends on the margin, and "two families" is mostly one (problems 1, 2). |
| 3 | Priority phase and newest-first targeting are substitutes | Report line 32 | **Supported** for the prescribed searches. The direct reading is stronger: the priority phase adds −0.001 once newest-first targeting is on. |
| 4 | B3 to R3 gain reduction replicates on 3 of 6 fresh markets | Report lines 23 to 29, `audit.json` | **Supported as stated.** |
| 5 | Welfare attacks and mixtures lower efficiency to 0.84 and 0.92 to 0.95 | Report lines 170 to 181, `posthoc.json` | **Narrower.** The 0.84 result is solid. The mixture result is arithmetic on two existing points, and the W1 search returned the null policy (problem 8). |

## 4. Correctness checks

| Item | Paper | My value | Source |
|---|---|---|---|
| Q1 pooled d, D2+H3 | 0.021 | **0.0207, reproduced** | Mean of six per-market values, report lines 13 to 18 |
| Q1 pooled d, X7-SC | 0.024 | **0.0243, reproduced** | Same lines |
| Q1 mean gains (C*, R3) | 0.086, 0.065; 0.091, 0.067 | **0.0856, 0.0649; 0.0913, 0.0670, reproduced** | `stability-result.json`, `mean_old` |
| Q1 category, p-values | equivalent, R3 lower; 0.0004, 0.0008 | **Reproduced** (0.0002 / 0.5; times 2) | `audit.json` q1 |
| Q1 doubled-search d | 0.030, 0.024 | **0.0295, 0.0243, reproduced** | Paper Table 5 columns |
| Q2 contrasts | P −0.083, G −0.095, S 0.004, PG 0.082, G given P=0 −0.177, G given P=1 −0.014 | **Reproduced**; conditional effects average to the main effects | Report line 32 |
| Q4 gain differences | 0.041, 0.469, 0.057, 0.263, 0.183, 0.027 | **Reproduced** to 4 decimals | `stability-result.json`, F000 minus F111 |
| Q4 passing count | 3 of 6 | **3, reproduced**; Holm 0.0004 × 6 = 0.0024 | `audit.json` q4 |
| Welfare efficiency | 0.839, 0.840, 0.840; W1 0.997 | **Reproduced** | Report lines 170 to 181 |
| Lottery, R3 with H4 | weight 0.4195, gain 0.000374, efficiency 0.932 | **0.00037 and 0.932, reproduced** from the two end points | Report lines 165, 174; Table 14 |
| Lottery, C* with H4 | 0.4845, 0.000456, 0.921 | **0.00044 and 0.921, reproduced** | Same method |
| Lottery, R3 with D2+H3 | 0.339, 0.000253, 0.9445 | **Reproduced** | `posthoc.json` F111 block |
| Prediction tallies | 10/8/0; 6/8/4; 5/4/9; 7/8/3; 6/5/7 | **Reproduced.** I counted 10 and 8 in `scoring.json`; the others match `eligibility.json` | `tally`, `tally_direct_inputs` |
| Proposition 1 bound | below 0.067 | **0.0668, reproduced** (1.4 × φ(3.2) / 0.05) | My computation, Appendix A values |
| First-test Table 2 | several | **Not checkable** | No first-test records in the materials |
| Lottery training gains | 0.00180 and others | **Partly checked**: R3 with D2+H3, 0.00127, matches `posthoc.json` `train_mix`. Others not checked. | `posthoc.json` |

## 5. Problems, ranked

**1 → "Equivalent" is a margin effect, and three sources of error can change it.**
Quote (abstract): "the registered procedure classifies R3 and C* as 'equivalent, direction R3 lower' within the registered margin of ±0.05".
- **Margin.** It is 58 to 77 percent of R3's own gain (0.065 to 0.086). The estimated difference is a 32 percent relative increase (0.0856 / 0.0649).
- **Search error.** The doubling check moves one cell by 0.054 (fresh3, C*, D2+H3; report line 225). That exceeds the margin.
- **Markets.** A t-interval over the six market values gives [−0.013, 0.054] for D2+H3 (my computation, 5 degrees of freedom). It includes zero and crosses the margin. With the doubled-search values it gives [0.014, 0.045].
- **Design.** The margin was set after development showed d of 0.027 and 0.038 (`predictions-v2.md`).
- **Effect.** The paper's interval [0.020, 0.022] gives a false sense of precision. Neither "equivalent" nor "R3 lower" holds for the neighbourhood.
- **Fix (analysis on existing records, plus text).** Report the market-level interval and the relative difference. Replace "equivalent" with "difference below the pre-set materiality margin".

**2 → The two Q1 families are mostly one test.**
Quote (p. 2): "pooled-equivalent in attacker gain within ±0.05 under both Q1 attack families".
- X7-SC takes the D2+H3 winner as an incumbent (design 5.2). In 4 of 6 markets both the C* and R3 X7-SC cells have the same means as the D2+H3 cells (`stability-result.json`).
- The X7-SC winners carry the embedding values (k_F = 1, a_F = 0, lambda = 1; report lines 208, 214, 220).
- The paper does not say this. Prediction Q3-a is "fulfilled" with 11 of 14 cells at exactly zero for the same reason.
- **Fix (text only).** State it. Report Q1 as one test with a partial second.

**3 → The attack searches are too weak for "robust" or "equivalent".**
- 21 of 98 doubling checks are flagged (`eligibility.json`).
- A 7-knob family (X5-AG/v2) beats the 15-knob X7-SC against C* on fresh1, fresh2, and fresh3 (report line 166).
- Searches select on 5 training seeds (`lottery_train.csv`, 5 rows per policy).
- Fresh-market factorial cells have no doubling check, but Q2 reports intervals of width 0.001.
- The paper mostly avoids "robust". Its Q2 "substitutes" claim and its Q1 label still depend on these searches.
- My envelope check: using each rule's strongest family, d is 0.031 pooled and 0.070 on fresh1 (my computation from Table 15).
- **Fix (needs compute).** Repeat the search until doubling passes on all Q1 and Q4 cells. Add the envelope d as an exploratory row (existing records).

**4 → With no honest churn, age labels the attacker.**
Quote (p. 7): "In a fixed population, a provider that keeps replacing can stay the newest identity, so R3's targeting of replacements persists beyond the window."
- Nine honest providers never replace. "Newest" therefore always means the attacker.
- Table 6 shows the cost: an honest replacement is audited at 92 to 93 percent after its window and earns about 4 percent less than under C* (2.74 against 2.86).
- With honest entry, the attacker loses the "newest" position and honest newcomers pay the cost.
- **Effect.** The G effect and the R3-against-C* result may not hold outside this model.
- **Fix (needs compute).** Add an arm with an honest replacement rate.

**5 → C* was not selected on attacker gain.**
Quote (p. 6): "by the development tuning objective, which combines gross efficiency and attacker gain".
- The objective is min((eff − 0.90)/0.90, (0.30 − gain)/0.30) (design 4.1). The first term is at most 0.111. The second binds only if gain exceeds 0.267.
- C*'s score is 0.1032 (ledger 3.2). That is an efficiency of 0.993. Gain did not enter the choice (my reasoning).
- **Effect.** Q1 compares on gain against a comparator chosen on efficiency. A gain-selected comparator can change the direction label.
- **Fix (analysis on existing records).** Report the gains of all 12 configurations. If another has lower gain, run it on the fresh markets (needs compute).

**6 → Corollary 1 is correct but close to a restatement, and the abstract drops its conditions.**
Quote (abstract): "immediate free replacement makes the ban costless."
- The corollary assumes that replacement restores the same state distribution. The zero continuation loss then follows at once.
- The real content is the check for B2 and B3. That is one parenthesis and three proof lines.
- Hidden conditions: honest rivals that do not react, re-entry with no lost round, no identity memory in B2's price posting (not checkable).
- **Fix (text only).** State it as a remark with the conditions. Prove the B2 and B3 check from the rule definitions.

**7 → Lemma 2 is correct but proves less than the text suggests.**
- It counts audits. It says nothing about deterrence. The term "audit dues" suggests a charge.
- The persistence remark is correct only while the identity is uniquely newest (see problem 4).
- "Served newest first" uses "served" for audits; elsewhere it means allocation.
- The design measures age from the first offer (design 3.2). The paper says "younger than L rounds". An identity that offers but wins no jobs can age out unaudited.
- Theorem 1 is correct by my derivation. It is never given numbers and never used.
- **Fix (text only).** Remove "audit dues", define age, move Theorem 1 to a supplement.

**8 → Contribution (iii) is arithmetic, not a finding about R3.**
Quote (p. 2): "an exploratory analysis of episode-level mixtures of public-family policies found substantially lower empirical gross efficiency than the registered W1 search".
- A mixture of two policies has the weighted mean of their gains and efficiencies. I reproduced each row from two end points.
- The W1 "attack" has gain exactly 0.0000 [0.0000, 0.0000], and the doubled winner has all knobs zero (report lines 175, 244). W1 returned the null policy. The label "supported" is degenerate.
- **Fix (text only).** Say that W1 found no attack. Reduce the mixture to one sentence.

**9 → The headline rule element is redundant, and the paper does not say so directly.**
- P given G = 1 is −0.0014 (report line 32). G alone gives −0.177 of the total −0.178.
- Amendment 3 added the priority phase after the predecessor was "killed". The second test does not support that addition. The title is "Checking Newcomers".
- **Fix (text only).** State it in the abstract.

**10 → The statistics do not address the main uncertainty.**
- Every confirmatory p-value is at the resolution floor or equals 1 (`audit.json`).
- The calibration multipliers (0.5 and 0.25) show that the bootstrap undercovers at 200 seeds on the fixtures.
- Search error and market variation are outside every interval.
- **Fix (text only).** Move the calibration detail to a supplement. Lead with the market-level variation.

**11 → Process facts that the paper omits.**
- The design says a fresh model session wrote H4 within 8 core-hours (design 5.3). An executor resumed that session and committed the bundle (ledger). The paper says only "written in a separate session".
- H4 contains D2+H3 and ran on the development market only.
- The prediction tally counts Q1-a-alt and Q1-d, which Q1-a decides. Q3-e passes by 0.000009.
- **Fix (text only).**

## 6. Novelty and related work

The contribution is modest. Probation, credibility thresholds, and cheap-pseudonym costs are known, and the paper cites them fairly. The new parts are newest-first residual targeting under a hard audit quota and a registered comparison. The comparison is a null result.

Missing, with my confidence:
- **Harrington (1988)**, "Enforcement leverage when penalties are restricted", Journal of Public Economics 37(1). doi:10.1016/0047-2727(88)90003-5. It is the standard source for history-based audit groups with limited penalties. The paper cites its successors [15, 19]. I am confident of this citation.
- **Dellarocas (2005)**, "Reputation mechanism design in online trading environments with pure moral hazard", Information Systems Research 16(2). doi:10.1287/isre.1050.0054. It treats identity changes. I am fairly sure of the DOI; verify it.
- **Golle and Mironov (2001)**, "Uncheatable distributed computations", CT-RSA. doi:10.1007/3-540-45353-9_31. I am unsure of the DOI digits; verify it.

I could not verify references [8], [14], and [24]. I do not know them.

## 7. Presentation

A reader gets lost in three places: the abstract (330 words, undefined labels), section 8 (calibration and block-hash detail before any result), and the prediction-eligibility text on pages 16 to 17.

**Keep for a 12-page version:**
- The model, the rules, and Corollary 1 as a remark.
- One Q1 table with per-market values, frozen and doubled.
- The Q2 table for one family.
- The Q4 table.
- Table 6 (the honest-replacement cost).
- One welfare paragraph.

**Move to a supplement:**
- The first test, except three sentences.
- The ulp deviation and Tables 19 and 20.
- Tables 21 to 23 (predictions).
- Tables 13 and 14 (lotteries), Table 12, coalitions, the repair block.
- Theorem 1 and the calibration procedure.

**Rewrite:** the abstract, to four findings in plain words. Give rules and attack families descriptive names, not codes.

## 8. Decision

| Venue | Score (1 to 5) | Acceptance probability | Confidence | Change that moves it most |
|---|---|---|---|---|
| WEIS 2027 | 2 | 20% | Medium | Add the honest-churn arm and present the paper as a negative result with the newcomer cost |
| AAMAS main track | 2 | 10% | Medium | Search to convergence, so that the empirical-game claims hold |
| ACM EC | 1 | 3% | High | A real theorem: a bound on gain under age-ranked audits with a quota, against history-based rules |

**Next action:** do the analyses in problems 1 and 5 first. They use existing records, and they decide whether the Q1 label stays.
