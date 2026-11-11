claude-fable-5-2

**→ Ambition.** The cheapest outside check of the reset result is a table of the replacement switch `x` in each of the 18 frozen truthful references. The reference records are not in this folder, so I could not make it (new problem 2).

## 1. Files read

- **Read in full:** `PROMPT.md`, `PREVIOUS_REVIEW.md`, `RESPONSE.md`, `main.pdf` (32 pages, in two ranges), `reset-experiment-plan.md`, `reset_block.py`, `reset.json`, `posthoc_reset.tex`.
- **Read by program (all fields that I use):** `records/eval_all/evaluate/` (24 records), `records/reset/evaluate/` (18), `records/reset/doubling/` (18), `records/report.json` (`doubling` block), `records/diagnostics.json`, `records/spot_compare.json`, `records/reset/inventory.json`, `records/reset/inputs.json`.
- **Read in part:** `posthoc.json` (`nesting`, `direct_priority`, `honest_cost`, `market_level`, `envelope_interval`), `posthoc_v2.py` (`direct_priority`), `revision-program-design.md` (section 6.4 and search hits), `operations-ledger.md` (search hits and last entries), `reset_followup_v2.py` (search hits only).
- **Run:** the reproduction command, the 27 tests of `test_reset_block.py` (27 passed), and my own recomputation script. All output went to the scratch folder.
- **Not opened this round:** `predictions-v2.md`, `protocol-v2.yaml`, `report.md`, `addendum.md`, `stability-result.json`, `audit.json`, `audit_v2.py`, `eligibility.json`, `scoring.json`, `score_v2.py`, `test_scoring.py`, `lottery_seeds.csv`, `lottery_train.csv`, `h4-family.py`, `h4-containment.md`. I make no new claim about them.
- **No network.** I could not check any DOI online. References [5], [8], [15] and [27] are dated 2025 or 2026, and I cannot confirm them.

## 2. Summary verdict

The revision resolves most round-2 text problems. The reset follow-up is honest, follows its plan, and reproduces exactly: every value in Table 11 and in the Section 9 paragraph matches the records. Its main sentence is supported, and it holds on each of the six markets, not only pooled.

Three things weaken it. The pooled "reversal" under D2 (S above 1) comes from one cell. The paper does not report the D2 doubling flags that the plan requires. The result appears only in one paragraph, while two other sentences still say that no such comparison exists.

The follow-up explains R3's advantage over B3. It does not change the main claim, and it makes the missing honest-churn arm more important.

Scores: **WEIS 2/5 (upper end), AAMAS 2/5, EC 1/5.**

## 3. Follow-through on round-2 problems 1 to 9

| # | Problem | Status | Revised sentence (page) | What remains |
|---|---|---|---|---|
| 1 | Sign versus size | Resolved | "The direction is therefore fairly stable across these analyses, while the size is not: every upper end is near the margin, so the equivalence label is the most fragile part" (p. 13) | "Results in brief" (p. 3) still says only "with the frozen searches the difference varies in sign across markets". |
| 2 | Under-searched X7-SC cells | Partly resolved | "in 6 of 21 cells the X7-SC winner's evaluated gain falls short of the better of the frozen and doubled D2+H3 winners on the same seeds by more than the doubling threshold (at most 0.021)" (p. 18) | I reproduced 6 of 21 and 0.0211 (`posthoc.json` `nesting`). The cause needs Run B. |
| 3 | Comparator arithmetic | Partly resolved | "This is a two-stage screen: it selects the winner among the two finalists and does not rank all twelve configurations at full budget." (p. 6) | Text is right. The evidence needs Run A. |
| 4 | Symmetric substitution | Resolved | "at a lower audit ratio or a larger attacker capacity, half of a round's audits may no longer cover one provider's jobs, and the substitution need not hold" (p. 15) | None. |
| 5 | Priority value below search error | Partly resolved | "R3's own comparison, F111 minus F011 (exploratory, from the evaluation records), is −0.003 pooled: exactly zero on four markets" (p. 15) | I reproduced −0.0029 (`posthoc.json` `direct_priority`). The abstract still gives the bare value "−0.003". I did not find the words "inside search error" that `RESPONSE.md` reports. |
| 6 | Welfare attack loses money | Resolved | "while earning less than the truthful reference against R3 (gain −0.094)" (abstract) | None. |
| 7 | Corollary conditions | Resolved | "against honest rivals whose play does not depend on the focal identity and with re-entry before the next allocation" (p. 2 and p. 27) | The abstract gives the rival condition and "can return at once". That is sufficient. |
| 8 | Deciding cells of the comparator table | Partly resolved | Table 25 now has the columns "Deciding cell" and "Its efficiency" (p. 28) | The score is still not recomputable. Efficiency minus score is 0.8893 for C-mem(6,20) inner and 0.8903 for C-thr(12) full (my arithmetic). State the formula. |
| 9 | Third finding quoted C*'s lowest bin | Resolved | "the replacement's profit per round under R3 differs from that under C* by a fraction of −0.044" (abstract) | Reproduced: −0.0442 (`posthoc.json` `honest_cost`). |

## 4. The reset follow-up

### (a) Plan fidelity

The analysis implements plan sections 2, 5 and 6 as written.

- **Estimands.** I, G and S in `_market_stats` and `_share` match plan sections 2 and 5. S is a ratio of pooled gaps, computed in every replicate, with no clipping.
- **Pairing.** One index vector per market and replicate serves every rule and family. Markets are resampled independently. The pooled value is the mean of six market means.
- **Pairing of records (my check).** For all 18 cells, the D2 record and its D2+H3 partner agree on runner hash, configuration hash, salt, root, seeds, budget, rule parameters, reference hash, and the `profit_ref` values. The D2 records carry commit `fdfd83e`; the runner hash equals the registered one.
- **Gate.** `_gated_share` applies the 0.05 floor to the lower bound of pooled G(D2+H3), separately for frozen and doubled searches.
- **Leave-one-out.** Six values, each with its own five-market gate, for frozen and doubled.
- **Sign counts and scoring.** Counts are per market on point estimates. "Met" needs both versions; disagreement gives "not established (search-sensitive)".
- **Tests.** 27 passed (`pytest test_reset_block.py`).

Deviations and limits:

- **The paper omits the D2 doubling flags.** Plan section 5 says they "are reported separately". `reset.json` has them; the paragraph and Table 11 do not. Three of 18 D2 cells are flagged: fresh0 B3 (0.036), fresh0 C* (0.009), fresh5 C* (0.044) (`records/reset/doubling/*`, `attack_change`).
- **The paper omits the leave-one-out values.** They are in `reset.json` only.
- **Plan section 4** asks for the fixed-policy switch "beside I". The paper gives B3 and R3 only. C* is 0.155 and 0.017 (`reset.json` `switches`).
- **Timing is not checkable.** The plan says its freeze hash is in the operations ledger. The ledger copy here ends on 2026-11-05 and has no reset entry. I cannot confirm that the plan and the analysis code came before the results.

### (b) Reproduction

The command reproduced `reset.json` exactly, except the `inputs` paths, and `posthoc_reset.tex` byte for byte. "Recomputation" means my own script on the records, with different code and bootstrap seed 12345.

| Item | Paper value | My value | Source |
|---|---|---|---|
| Headline I(B3), I(R3) | 0.307, 0.012 | 0.3067, 0.0124, reproduced | Recomputation, `eval_all` headline records |
| Headline gap under D2+H3, D2 | 0.302, 0.007 | 0.3016, 0.0073, reproduced | Same |
| G(D2+H3) frozen | 0.173 [0.172, 0.175] | 0.1734 [0.1721, 0.1747], reproduced | Recomputation |
| G(D2) frozen | −0.009 [−0.011, −0.008] | −0.0092 [−0.0107, −0.0076], reproduced | Recomputation |
| G doubled | 0.170 and −0.004 | 0.1698 and −0.0037, reproduced | Recomputation |
| S frozen | 1.053; table 1.05 [1.04, 1.06] | 1.0529 [1.044, 1.062], reproduced | Recomputation |
| S doubled | 1.022; table 1.02 [1.01, 1.03] | 1.0215 [1.012, 1.031], reproduced | Recomputation |
| I(B3), I(R3), I(C*) frozen | 0.228, 0.045, 0.069 | 0.2276, 0.0450, 0.0690, reproduced | Recomputation |
| I doubled | 0.221, 0.047, 0.080 | 0.2206, 0.0471, 0.0802, reproduced | Recomputation |
| I(B3) − I(R3) | 0.183; doubled 0.173 | 0.1826; 0.1734, reproduced | Recomputation |
| I(C*) − I(R3) | 0.024; doubled 0.033 | 0.0240; 0.0331, reproduced | Recomputation |
| Markets with I(B3) > I(R3) | 6 and 6 | 6 and 6, reproduced | Recomputation |
| Markets with I(C*) > I(R3) | 5 and 6 | 5 and 6, reproduced | Recomputation |
| fresh3 contrast, frozen | −0.041 | −0.0407, reproduced | `reset.json` `contrast` |
| Switch off, D2+H3 winner | 0.371 (B3), 0.091 (R3) | 0.3711, 0.0906, reproduced | `diagnostics.json`, pooled by me |
| Switch on, D2 winner | 0.033, 0.009 | 0.0331, 0.0086, reproduced | Same |
| "No D2 winner replaces its identity" | zero resets | 0.0 in all 18 cells, reproduced | `diagnostics.json` `d2_base.mean_resets` |
| Expectation labels | met; not established; met | Same, reproduced | Command output |
| Table 5, B3 − R3 columns | six frozen and six doubled values | All 12 reproduced | Recomputation |
| Pod reproduced a registered record bit for bit | stated in `RESPONSE.md` | Not checkable | No gate record in the folder |
| Mac against pod spot check | pass | Pass, largest difference 2.2e-16 | `spot_compare.json` (read, not rerun) |

### (c) Interpretation

**The main sentence is supported.** Quote (p. 15): "most of the estimated B3 minus R3 gap under the prescribed searches disappears when the attacker cannot replace its identity." The plan permits it because pooled S above 0.5 is met in both versions.

It also holds per market, which the paper does not say. Per-market S is 1.56, 1.00, 0.81, 0.99, 0.94, 3.02 with frozen searches. With doubled searches it is 0.70, 1.00, 0.88, 0.99, 0.93, 3.01 (my computation). The lowest value is 0.70.

**I is described correctly.** Quote (p. 15): "The difference between the two prescribed searches ... it does not identify the optimal value of replacement." The text also says "The two searched winners can differ in every knob, not only x."

**The exploratory label is correct.** Quote (p. 14): "after the headline contrast and the six fresh-market D2+H3 outcomes had been seen. This is a descriptive follow-up, not an independent replication, and it changes no registered decision."

**The explanation of S above 1 is correct arithmetic but an incomplete reading.** Quote (p. 15): "a value above one means the gap reverses slightly under D2."

- The pooled G(D2) of −0.0092 is one cell. Without fresh5, the five-market G(D2) is −0.0001 and S is 1.0004 (`reset.json` `S_leave_one_out`).
- On fresh5, the D2 winner against B3 has a gain of −0.028. It earns less than the truthful reference and is banned for 59.6 of 200 rounds (`diagnostics.json`). Its doubling check shows no change.
- G(D2) is positive on 3 of 6 markets (frozen) and 4 of 6 (doubled). A t interval over the six market values is [−0.036, 0.018] (my computation).
- The printed intervals, [−0.011, −0.008] for G(D2) and [1.04, 1.06] for S, show seed noise only. A reader can take them to mean that S is above 1. The data do not show that.
- Correct reading: under D2 the gap is not different from zero, and its sign is not established.

**The expectations had little risk (my reasoning).** When the plan was written, G(D2+H3) of 0.173 and the headline D2 gap of 0.007 were known. "S above 0.5" was close to certain. The paper discloses the timing, so this is a weight, not an error.

### (d) Contribution

It explains the main claim; it does not change it.

- **What it adds.** In these searches, R3's whole advantage over B3 is in the replacement channel. Under D2 the pooled gains are 0.011 (B3), 0.020 (R3) and 0.017 (C*) (my computation). The three rules are not distinguishable.
- **One more result is in the records but not in the paper.** The Q1 difference also goes away under D2. C* minus R3 is 0.021 under D2+H3 and −0.003 under D2, with a market t interval of [−0.018, 0.012] (my computation). I(C*) − I(R3) carries this implicitly; the paper should say it.
- **It agrees with Corollary 1.** Under B3 the ban costs nothing with replacement and is a real cost without it.
- **It limits scope.** Without free identities, R3 shows no measured benefit over B3, and its cost on honest newcomers stays.
- **It raises the weight of the honest-churn gap (my reasoning).** All of R3's measured value is in the channel that honest churn would contaminate.
- Q1, Q4, and all registered decisions are unchanged.

## 5. New problems, ranked

**1 → The paper contradicts its own follow-up. (Text only.)**
- Quote (p. 5): "it does not isolate how much of that profit comes from the ability to replace an identity, which would need a matched comparison with replacement disabled."
- Quote (p. 26): "it does not isolate the marginal benefit of being allowed to replace identities, which would need a matched comparison with replacement disabled."
- Section 9 now reports that comparison within the D2 family. Table 1 still says D2 ran "second test: headline only".
- The abstract, contributions, Section 10 and conclusion do not mention the follow-up.
- Fix: change both sentences to point to the Section 9 paragraph with its limits. Correct Table 1. Add one sentence to the abstract and one to the conclusion, labelled exploratory.

**2 → The truthful reference may replace its identity; the D2 attacker cannot. (Analysis on existing records.)**
- Quote (p. 5): "a truthful focal provider may also replace after a false failure."
- The reference menu includes truthful projections of D2+H3 winners (`revision-program-design.md` section 6.4). These can keep `x = 1`.
- The reference cancels in I. It does not cancel in G, because each rule has its own reference.
- If B3's reference replaces and R3's does not, G(D2) is biased downward and S upward (my reasoning). I could not check this; the reference records are not in the folder.
- Three D2 winners have negative gain: fresh0 B3 (−0.002, a truthful projection, `clip = 1`), fresh2 R3 (−0.006, `clip = 1`), and fresh5 B3 (−0.028). The first two are what this bias would produce.
- Fix: report `x` and the source of each of the 18 frozen references. If any has `x = 1`, add "while its truthful reference can" to the main sentence and re-evaluate those references with `x = 0`.

**3 → S above 1 reads as a finding; it is one cell. (Text only, with one analysis on existing records.)**
- See section 4(c).
- Fix: replace "the gap reverses slightly under D2" with "under D2 the gap is not different from zero (3 of 6 markets positive; 4 of 6 with doubled searches)". Add the leave-one-out range, 0.97 to 1.09 over both versions. Add a market-level t interval beside the seed interval, as the Q1 paragraph does.

**4 → The D2 doubling flags are missing, and the check missed a bad cell. (Text only.)**
- Plan section 5 requires the flags. Three of 18 cells are flagged, with changes up to 0.044.
- That is larger than G(D2) on every market except fresh5.
- The fresh5 B3 winner earns less than the reference and is not flagged. So an unflagged D2 cell is not a converged cell.
- Fix: report "3 of 18 flagged, largest change 0.044" in the paragraph. State that fresh0 G(D2) changes sign under doubling (−0.023 to +0.012).

**5 → Two frozen D2+H3 cells violate nesting against D2. (Analysis on existing records.)**
- D2 is inside D2+H3, so I cannot be negative for a complete search.
- I is −0.0024 on fresh3 for C* and −0.0060 on fresh4 for R3 (frozen).
- The D2 winner with `x = 1` beats the frozen D2+H3 winner by 0.023 and 0.010 on the same seeds (my computation from `diagnostics.json`). The doubled searches remove both.
- The paper reports only the fresh3 contrast. The plan deferred a best-of sensitivity.
- Fix: list the two cells as nesting failures. For the C* contrast, state that the doubled value (0.033, 6 of 6) is the more reliable one.

**6 → Pooling hides that the share is weakly determined where the gap is small. (Text only.)**
- G(D2+H3) is 0.469 and 0.263 on fresh1 and fresh3. It is 0.041, 0.057 and 0.027 on fresh0, fresh2 and fresh5.
- On those three markets the gap is similar in size to the D2 doubling changes. Those are the Q4-failing markets.
- Fix: add the per-market G pairs to Table 11 or to the text.

**7 → The timing claims have no record in the package. (Text only.)**
- Quote (p. 14): "under a plan and expectations written before any fresh D2 result existed."
- Fix: add the plan's freeze commit, the analysis-code commit and the pod gate record to the ledger copy.

**8 → Length. (Text only.)**
- The paper is now 32 pages; it was 30. The round-2 request for a short version is not met.

## 6. Open runs, ranked

**1. Honest-churn arm. Changes my score most.**
- Either outcome moves WEIS to 3. The reset result raises its value, because R3's whole measured advantage is in the replacement channel.
- It needs B3, R3 and C*, at least two churn rates, and the fresh markets.
- **It must be done before a WEIS submission.** Without it, the title claim is tested only in a world where every newcomer is the attacker.

**2. Run A, the runner-up comparator. Changes the Q1 claim, and the score by a small amount.**
- If the difference falls to near zero, finding (i) becomes "no measurable difference". If it stays near 0.02, "R3 lower" gains support.
- Strongly recommended before WEIS, but not required, if the comparator caveat stays in the abstract.
- Add the D2 cells for the runner-up, to extend the reset comparison.

**3. Run B, searches to convergence. Matters for AAMAS only.**
- Extend it to the D2 cells: the three flagged cells and fresh5 B3 (new problem 4).
- Not required for WEIS.

## 7. Decision

| Venue | Score (1 to 5) | Acceptance probability | Confidence | Change that moves it most |
|---|---|---|---|---|
| WEIS 2027 | 2 (upper end) | 28% | Medium | The honest-churn arm on the fresh markets, with the paper cut to about 12 pages around the reset result and that arm |
| AAMAS main track | 2 | 10% | Medium | Run B on every flagged and nesting-short cell, D2 cells included, plus the honest-churn arm |
| ACM EC | 1 | 3% | High | A theorem on age-ranked audits under a quota with free identities; no planned simulation helps |

I do not know the WEIS 2027 deadline or page limit. Verify both.

**Next action:** fix new problems 1, 3 and 4 in the text, and make the reference table of problem 2. All four use existing records.
