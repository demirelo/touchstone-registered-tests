claude-fable-5-2

# External review, round 4: "Checking Newcomers When Identities Are Free" (draft 9, 33 pages)

## 1. Files read

- **Read in full:** `PROMPT.md`, `RESPONSE.md`, `SECOND_REVIEW_TRIAGE.md`, `PREVIOUS_REVIEW.md`, `churn-plan.md` (sections 1 to 6 and 9 in full; section 7 in part), `churn_block.py`, `posthoc_churn.tex`, `posthoc_reset.tex`, `records/churn/run.json`, `records/churn/gate-p0/gate.json`, `records/reset/gate.json`.
- **`main.pdf` (33 pages, converted with `pdftotext -layout`):** pages 1 to 19 and 27 to 29 read in full (abstract to Section 9, Sections 10 and 11, Table 26). Pages 20 to 26 and 30 to 33 were searched for the words "churn", "untested", "replacement" and "every market", not read line by line. I make no new claim about them.
- **Read by program (all fields that I use):** the 36 churn evaluation records and 36 churn doubling records, both `records/churn/p*/diagnostics.json`, both inventories, the 18 registered D2+H3 records in `records/eval_all/evaluate/`, `records/report.json` (`doubling` block), `churn.json`, `reset.json`, `reset_reference/reset_reference.json`, `posthoc.json` (`direct_priority`, `doubled`).
- **Read in part:** `operations-ledger.md` (the two follow-up sections), `churn_v2.py` (`HonestChurn` and `install`), `reset_block.py` (`_t95`, `market_level`), `revision-program-design.md` (search hits for the attack knobs), `PREVIOUS_REVIEW_R2.md` (not reopened this round; I wrote it).
- **Not opened this round:** `reset-experiment-plan.md`, `reset_followup_v2.py`, `test_*.py` (run, not read), `predictions-v2.md`, `protocol-v2.yaml`, `report.md`, `addendum.md`, `stability-result.json`, `audit.json`, `audit_v2.py`, `eligibility.json`, `scoring.json`, `score_v2.py`, `test_scoring.py`, `lottery_*.csv`, `h4-family.py`, `h4-containment.md`, `records/reference/`, `records/diagnostics.json`, `records/spot_compare.json`. I make no new claim about them.
- **Run (Python 3.11 with numpy 2.3.1, flag `-I`; all output in the scratch folder):**
  - The churn command of `PROMPT.md`. It reproduces `churn.json` exactly (all fields except the two `inputs` paths) and `posthoc_churn.tex` byte for byte.
  - The reset command. It needs `scipy`, which `PROMPT.md` does not say. I supplied the 0.975 t quantile from a table. With that, `posthoc_reset.tex` is byte-identical and `reset.json` is identical except the `inputs` paths and the twelve `review_r3` t bounds, which differ by less than 2e-11.
  - The `summarize` command of `ref_resets.py`. Its output is identical to `reset_reference/reset_reference.json`.
  - The tests of `test_churn_block.py` (26 passed) and `test_reset_block.py` (33 passed). `pytest` did not load in this environment, so I ran the test functions with a small stand-in for `approx`, `raises`, `parametrize` and `tmp_path`. This is not a full pytest run.
  - My own recomputation of every churn value from the records (different code, bootstrap seed 4242): `recompute_churn.py` and `sat.py` in the scratch folder.
  - Read-only `git log` and `git show` on the repository, to check commit times that the package does not hold. This is outside the package; I say so where I use it.
- **No network.** I could not check any DOI online.

## 2. Summary verdict

The honest-churn arm that round 3 asked for is done, and it is done well. It follows its plan, the pod gate is bit-identical, and every value in Table 12 and in the Section 9 paragraph reproduces from the records. The result is the most important one in the paper: at p = 0.05 the measured gain against R3 rises from 0.065 to 0.272, R3 becomes worse than C* by 0.173 and worse than B3 by 0.033 to 0.052, and at p = 0.01 nothing clear changes. But the paper does not yet use this result. The abstract, the model section and the limits still say that honest churn "is untested", the conclusion does not mention it, and the first and fourth findings in the abstract are stated without the condition that the new arm shows they need. The paragraph's explanation is also wrong in one part: on the three markets that carry the reversal, the winning attack never replaces its identity. The attacker does not hide among newcomers. It stays old, and R3 has no audits left for old identities, because honest newcomers hold 0.355 of the jobs and take 0.808 of all audits (my computation from the diagnostics). The two rates lie on the two sides of this saturation point, and the paper has no rate between them. All of this can be fixed with text and with analysis on existing records. Scores: **WEIS 2027: 3/5 (lower end; 35%). AAMAS main track: 2/5 (12%). ACM EC: 1/5 (3%).** The WEIS score is 3 and not 2 because the missing experiment now exists and its result is clear; it is at the lower end because the manuscript still argues around its own strongest result and is 33 pages.

## 3. Follow-through on round-3 problems 1 to 8

| # | Round-3 problem | Status | Revised sentence (page) | Is `RESPONSE.md` accurate? |
|---|---|---|---|---|
| 1 | Paper contradicted its reset follow-up | Resolved for the reset follow-up | "Section 9 reports an exploratory matched comparison with replacement disabled, within the D2 family only." (p. 5). "it does not isolate the marginal benefit of being allowed to replace identities beyond the exploratory D2-family comparison of Section 9" (p. 27). Table 1 lists D2 on "the six fresh markets in an exploratory follow-up after the report" (p. 8). Abstract and conclusion each have one labelled sentence. | Accurate. The same class of error now exists for the churn follow-up (new problem 1). |
| 2 | Truthful reference may replace its identity | Partly resolved | "The truthful references can: 17 of the 18 frozen references replace an identity on the evaluation seeds." and "it is not a re-evaluation with non-replacing references" (p. 15) | Accurate. I regenerated the summary: 17 of 18; largest replacement value 0.0089; G shift 0.0005; S 1.0496; C* minus R3 shift -0.0013; largest validation difference 0.0074 (`reset_reference.json` `summary`). The limit is stated. A Linux re-evaluation is still not done. |
| 3 | S above 1 read as a finding | Resolved | "It exceeds one because the pooled D2 gap is slightly negative. ... the exploratory t interval across the six market means, [-0.036, 0.018], includes zero ... We therefore do not establish a negative average gap across the market neighbourhood." (p. 15) | Accurate. Reproduced: t interval [-0.0361, 0.0177], 3 of 6 positive (`reset.json` `review_r3.base.G_D2`); leave-one-out 0.967 to 1.093. |
| 4 | D2 doubling flags missing | Resolved | "3 of the 18 D2 doubling checks are flagged (largest change 0.044), and on fresh0 the D2 gap moves from -0.023 to 0.012 under doubling; an unflagged cell is not a converged one." (p. 16) | Accurate (`reset.json` `review_r3.flags`: 3 of 18, 0.0441). |
| 5 | Nesting | Resolved, with a better reading than mine | "These reversals can reflect finite search or differences between training and evaluation outcomes; they disappear under doubling, which does not establish convergence. We keep the frozen searches as primary and report the doubled results as sensitivity." (p. 16) | The response is accurate. The second referee's point is correct, and I withdraw my round-3 advice to call the doubled value "more reliable". One error in `SECOND_REVIEW_TRIAGE.md`: it says the field was renamed `heldout_order_reversals`. In this package `reset_block.py` (line 210), its test (line 303) and `reset.json` still use `nesting_failures`. |
| 6 | Per-market gaps | Resolved | "The lower block gives the gaps per market (D2+H3 / D2)." (Table 11, p. 18) | Accurate. Byte-identical table. |
| 7 | Timing records | Resolved for the reset follow-up | Ledger section "Reset follow-up": plan commit 140b906 (05:52), pod 13:43, code 3e286c1 (16:47:33), first run 41bafd2 (16:48:02) | Accurate. I confirmed the three commit times with `git log` in the repository (outside the package). `records/reset/gate.json` says `identical: true`. The statement that the block was not run on the records before the commit is not checkable. |
| 8 | Length | Not resolved | The paper is 33 pages (round 3: 32; round 2: 30). | Accurate ("Not changed"). |

Other statements in `RESPONSE.md`:

- **The note on the superseded quotations is accurate.** The four old sentences do not occur in `main.pdf`. The four current ones do: "It exceeds one because the pooled D2 gap is slightly negative" (p. 15); "added the signed difference to the stored Linux gains" (p. 15); "These reversals can reflect finite search or differences between training and evaluation outcomes" (p. 16); "search uncertainty for this contrast is not quantified" (abstract).
- **The correction in item 5 of the second-review block is accurate and necessary.** The first line of the response still says "Every change below is text, or an analysis on existing records". The reference check and the churn arm are new computation. Delete that line.
- **"both negative on all six markets" is true for the frozen searches only.** With the doubled searches both contrasts are negative on 5 of 6; fresh0 is +0.005 (C* minus R3) and +0.009 (B3 minus R3) (`churn.json` `statistics.doubled.0.05`).
- **"caveats applied (... wording on causes and on raw profit units)" is only partly visible.** The churn paragraph gives "rises by 113.101" with no unit, and it still makes a causal statement ("The diagnostics show how", "thus"; see 4c).
- **Test counts are accurate:** 26 and 33 (my stand-in runner).
- **Not checkable:** the 4.99 USD spend, the internal review rounds, and the discarded partial first run.

## 4. The honest-churn follow-up

### (a) Plan fidelity

The analysis implements plan sections 2, 4, 5 and 6 as written.

- **Estimand (section 2).** `gain` equals (attack profit minus reference profit) divided by S*/10 in every cell; largest deviation 1.1e-16 (my check on all 108 arrays).
- **Pairing (section 5).** One index vector per market and replicate serves every rule, rate, version and the no-churn records (`analyse`). The seed lists are equal across all of them (the loader refuses otherwise; I checked it separately). Base is compared with base and doubled with doubled.
- **Pooling.** The pooled value is the equal-weight mean of six market means; replicates resample seeds inside each market.
- **References.** The reference profit is the same array in the base and doubled records of each churn cell, and it differs from the no-churn array. So the frozen candidate was replayed under churn, as planned.
- **Expectations (section 6).** `expectations` scores point estimates, each version against its own no-churn value, with "met" only if both versions hold. Expectation 4 reads the first age bin of honest replacement identities at p = 0.05. All four score "met"; I agree.
- **Diagnostics (section 4).** The paper uses statistic (ii), newest by first offer among identities with assigned jobs, as the plan requires. `validate_diagnostics` checks the pooled shares against the per-episode counts. My own sums from the per-episode counts give the same values.
- **Execution.** `gate-p0/gate.json`: `identical: true`, `require_identical: true`, all differences 0.0. The 37 record files of each rate that are in the package match their inventory hashes; the other 169 inventory entries per rate (search and freeze records) are not in the package. The churn records carry the registered runner hash, configuration hash, salt and root; only the commit and the id differ.
- **Timing.** The package copy of the plan is byte-identical to the repository file at commit ef17139 (2026-11-12 11:45:42 UTC). The pod was requested at 11:46. Sections 2, 4, 5 and 6 are unchanged since commit bd2d719 (2026-11-11 01:16 UTC). The analysis code was committed at 21:02:24 and the first run at 21:04:19, after the pod ended at 20:34. I took these times from `git log`; the ledger copy names no plan commit for this arm.

Deviations and limits:

- **The reselection diagnostic is not in the paper.** Plan section 5 lists "the reselection diagnostic per cell". `churn.json` has it: `reference_change` is nonzero in 16 of 36 cells, largest 0.0046 (fresh2, B3, p = 0.05). The value is small and supports the paper; it should be printed.
- **The paper gives the flag count but not the largest change.** It is 0.087 (fresh4, B3, p = 0.05). The reset paragraph gives its equivalent (0.044).
- **Nine tests were added after the first run** (17 at commit c15580d, 26 now). The ledger says they are a validator and an input guard. They do not change an estimate.
- **The expectations had little risk** (my reasoning). The disclosed peek showed the old attack's profit under R3 rising with p (0.468, 0.487, 0.521; plan section 1). The paper says a timing check "had been seen"; it does not say that the check showed the direction.

### (b) Reproduction

"Recomputation" is my own script on the records. Intervals use my bootstrap seed, so a bound can differ by 0.001.

| Item | Paper value | My value | Source |
|---|---|---|---|
| Table 12, all 30 point estimates | as printed | all reproduced | Recomputation; also the churn command (byte-identical table) |
| Table 12, all 30 intervals | as printed | reproduced; one bound differs: q frozen p = 0.05 upper -0.049 against -0.048 | Recomputation (different seed) |
| Honest replacements per episode | 17.901 and 89.582 | 17.901 and 89.582 | Diagnostics, `honest_replacements_per_episode`, mean of six markets |
| g(R3) at p = 0.05 | 0.065 to 0.272 [0.268, 0.275] | 0.0649 to 0.2717 [0.268, 0.275] | Recomputation |
| g(C*), g(B3) at p = 0.05 | 0.086 to 0.098; 0.238 to 0.220 | 0.0856 to 0.0983; 0.2383 to 0.2198 | Recomputation |
| C* minus R3 at p = 0.05 | -0.173 [-0.177, -0.170]; negative on 6 of 6 | -0.1734 [-0.177, -0.170]; 6 of 6 frozen, **5 of 6 doubled** | Recomputation |
| B3 minus R3 at p = 0.05 | -0.052 [-0.055, -0.048]; negative on 6 | -0.0520 [-0.055, -0.049]; 6 of 6 frozen, **5 of 6 doubled** | Recomputation |
| Attack profit change against R3 | 113.101 | 113.101 [111.3, 114.9], raw profit units; about 0.209 after division by the pooled S*/N of 541.8 | Recomputation |
| Reference profit change against R3 | -0.146 [-0.393, 0.098] | -0.146 [-0.387, 0.097] | Recomputation |
| C* minus R3 at p = 0.01 | 0.001 [0.000, 0.003]; doubled -0.004 | 0.0015 [0.000, 0.003]; -0.0042 | Recomputation |
| B3 minus R3 at p = 0.01 | "stays at 0.175" | 0.1746 frozen; **0.1533 doubled** (no churn: 0.1698) | Recomputation |
| Newest share at p = 0.05 | 0.010 (R3), 0.107 (C*), 0.452 (B3) | 0.0100, 0.1066, 0.4522 frozen; 0.004, 0.137, 0.454 doubled | Diagnostics, `focal_newest_by_first_offer_assigned`, episode means, then market means |
| Audited share of honest replacements, first ten rounds | 0.571 (R3), 0.356 (C*), 0.250 (B3) | 0.5707, 0.3560, 0.2502 | Per-episode counts, summed by me per market, then market means |
| Expectations 1 to 4 | all "met" | all "met" | `churn.json` `expectations`; values recomputed |
| Flags | 13 of 36 | 13 of 36 (7 at p = 0.01, 6 at p = 0.05; R3 4, C* 6, B3 3) | Doubling records, `incomplete` |
| "at p = 0.05 the doubled searches give the same sign for every pooled gain and contrast" | stated | true for the pooled values | Recomputation |
| Registered no-churn values | 0.0207, 0.0296, 0.1734, 0.1698 | reproduced to 1e-9 | `churn.json` `registered_check` |
| Mean identity lifetimes 100 and 20 rounds | stated | 1/p; arithmetic | My computation |
| Plan and expectations written before any churn search | stated | consistent with the commit times in 4a | `git log`, outside the package |
| Spend 4.99 USD | `RESPONSE.md` | not checkable | Ledger text only |

### (c) Interpretation

**Supported.**

- "The rise comes from the attack's profit, not from a weaker reference" (pp. 16 to 17). The attack term is +113.1 and the reference term is -0.15, and reselecting the reference among the frozen menu under churn changes a training gain by at most 0.0046. Add the unit and the reselection value.
- The audit-share diagnostic and expectation 4. The plan permits the statement that R3 exposes honest newcomers to more audits.
- The exploratory label, the "illustrative, not calibrated" label, and the sentence that the model "does not isolate age information".

**Not supported as written.**

1. **"while the attacker's identity hides among them" (p. 17) is a category error.** The files say:
   - The frozen R3 winner at p = 0.05 has the replacement switch off (`x = 0`) on fresh1, fresh2 and fresh4. Its newest share there is exactly 0.000 (`diagnostics.json` `knobs` and `focal_newest_by_first_offer_assigned`).
   - These three markets carry the reversal: C* minus R3 is -0.446, -0.089 and -0.213 there, against -0.016, -0.270 and -0.006 on the others.
   - Pooled, the attacker's jobs are audited at 0.042 under R3 (0.012 to 0.095 by market), against 0.292 under C* and 0.251 under B3 (my sums of the `focal` counts over all age bins).
   - Under R3, honest identities younger than ten rounds hold 0.355 of the served jobs and receive 0.808 of all audits. Established honest jobs are audited at 0.078. The attacker holds 0.088 of the jobs and receives 0.015 of the audits (my computation, `sat.py`).
   - My reading: the attacker is not one newcomer among many. It stops being a newcomer. R3's priority phase spends the quota on honest newcomers, and an identity that stays old is almost never audited. The winning attack is then plain shading without replacement, which is a D2 policy. This is the overload case of Lemma 2 (p. 7), and the first test already named it for entrant coalitions: "coalitions of entrants overload the newcomer priority" (p. 10).
2. **"The diagnostics show how" (p. 17) gives the newest share a causal role that the design cannot give it.** The three values (0.010, 0.107, 0.452) come from three different selected attacks. The B3 winner replaces often because a ban costs it nothing; that is why it is often the newest. There is no no-churn value of this statistic in the paper. The plan itself says "A failure is not read as evidence of a particular cause". Report the shares "under each rule's selected attack" and move the weight to the audit shares, which are properties of the rule.
3. **"the B3 minus R3 gap stays at 0.175" (p. 17) holds for the frozen searches only.** With the doubled searches the gap falls from 0.170 to 0.153 and g(R3) rises from 0.067 to 0.086. Table 12 shows this; the sentence does not.
4. **The frozen row at p = 0.01 is visibly under-searched.** The frozen R3 winners on fresh1 and fresh3 have `x = 0` and gains 0.036 and 0.056; the doubled winners have `x = 1` and gains 0.130 and 0.082. The frozen C* winner on fresh1 has a gain of -0.000; at p = 0 it is 0.149 and at p = 0.05 it is 0.134. The pooled C* minus R3 value at p = 0.01 is set by fresh1 alone: -0.036 frozen and -0.075 doubled there, and positive on the other five markets with the doubled searches (0.003 to 0.014). Both fresh1 cells are flagged, each with a change of 0.053. The paper's caveat ("changes sign under doubling") is correct but too weak. The supported statement for p = 0.01 is: no reversal against B3 on any market; the C* contrast is not resolved by these searches.
5. **The frozen g(B3) of 0.220 at p = 0.05 is one failed search.** The frozen fresh4 winner against B3 has a gain of 0.094; the doubled one has 0.196, and the no-churn value is 0.189. This is the largest flag in the arm (0.087). So "from 0.238 to 0.220" is not an effect of churn, and the frozen gap of -0.052 is too large. With the doubled searches it is -0.033; with the better of the two winners per cell it is -0.036, negative on 6 of 6 (my computation; this envelope is post hoc).
6. **The closing sentence needs three conditions.** Quote (p. 17): "Within this model, at the higher rate, R3's measured advantage over C* and B3 does not survive honest churn."
   - It is true for the pooled point estimates and for the seed intervals.
   - The paper applies a market-level t interval to the D2 gap and to Q1, but not here. Here it gives [-0.352, 0.005] frozen and [-0.339, 0.001] doubled for C* minus R3, and [-0.119, 0.015] frozen and [-0.064, -0.001] doubled for B3 minus R3 (my computation, t with 5 degrees of freedom). The intervals touch zero because the market values are very unequal (-0.006 to -0.446), not because the sign varies. Report them with the sign counts (6 of 6 frozen, 5 of 6 doubled).
   - For C* the sentence is too weak. A difference of -0.173 is more than three times the paper's own materiality margin of 0.05, in C*'s favour.
   - For B3 it is about right: R3 is not better than B3 and may be slightly worse.
   - It holds past the point where honest newcomers' jobs exceed the audit quota (new problem 3), and for frozen reference candidates.

### (d) Contribution and placement

It changes the main claim. This is no longer a limit; it is a result.

- **Finding (i) becomes conditional.** Without honest churn, R3 and C* are equivalent within 0.05 with R3 lower. At p = 0.05, C* is lower by 0.173, outside the margin on the other side. C*'s own gain moves little (0.086 to 0.098) and its gross efficiency under attack does not move (0.993 at every rate; my computation from `eff_attack`).
- **The fourth finding becomes conditional.** "R3 lowers the attacker's gain relative to uniform audits on every fresh market" is false at p = 0.05 on 5 or 6 of 6 markets.
- **The third finding gets its population version.** The registered diagnostic had one honest replacement. Now, with 90 per episode, R3 audits 0.571 of honest newcomers' jobs and they absorb 0.808 of the audits.
- **The reset and churn follow-ups give one consistent account** (my reasoning). R3's whole measured advantage is in the replacement channel, and it exists only while the attacker is almost the only newcomer. A rule that ranks by verified history does not depend on that. This is the paper's best contribution, and it agrees with the theory the paper cites on cheap pseudonyms (its references [13] and [11]).
- **Placement.** It must be in the abstract, the contributions, "Results in brief", Section 10 and the conclusion. It should be a subsection of its own, not the third paragraph inside Q4.
- **Wording for the abstract** (replaces "so honest churn is untested"): "An exploratory follow-up lets each honest opponent replace its identity with probability p per round. At p = 0.01 the comparison with B3 is unchanged and the comparison with C* is not resolved by the searches. At p = 0.05, where honest newcomers' jobs exceed the audit quota, the measured gain against R3 rises from 0.065 to 0.272, above the gain against C* (0.098) and B3 (0.220 to 0.240) on 5 or 6 of the six markets: R3 spends 0.81 of its audits on honest newcomers, and an attacker that keeps its identity is audited on 0.04 of its jobs. The rates are illustrative, the references are the frozen ones, and intermediate rates are untested."
- **Wording for the limits:** "R3's advantage is measured only when the attacker is almost the only source of new identities."
- **Title.** "Checking Newcomers When Identities Are Free" now promises more than the paper supports. A subtitle such as "... and Why Age-Ranked Audits Fail Under Honest Churn" is the honest version (my judgement).

## 5. New problems, ranked

**1. The paper contradicts its own churn follow-up. (Text only.)**
- Quote (abstract, p. 1): "honest opponents that never replace their identities, so honest churn is untested".
- Quote (p. 5): "Population churn among honest opponents is untested, except for the single replacement of the second test's honest-replacement diagnostic (Section 10)."
- Quote (p. 27): "population churn of honest identities is untested. With such churn, newest-first targeting would spend audits on honest newcomers and could lose much of its targeting power".
- Quote (p. 7): "with honest churn it would share the newest positions with honest newcomers."
- Quote (p. 27): "the prescribed D2+H3 searches yield a lower measured gain for R3 than for B3 on every sampled market".
- The conclusion (p. 28) does not mention churn. The opening of Section 9 (p. 12) lists the exploratory tables without Tables 11 and 12.
- This is round-3 problem 1 again, for the new arm.
- Fix: replace all five sentences with the measured result and its conditions (wording in 4d). Add "without honest churn" to the first and fourth findings of the abstract, to contribution (i), and to the first sentence of Section 10. Add one sentence to the conclusion.

**2. The stated mechanism is wrong. (Analysis on existing records, then text.)**
- Quote (p. 17): "R3's newcomer priority thus moves audits to honest newcomers while the attacker's identity hides among them."
- Evidence in 4c, point 1.
- Fix: replace the sentence with: "R3's priority phase spends the quota on honest newcomers (0.355 of the served jobs, 0.808 of the audits), so established identities are almost never audited (0.078 of honest established jobs; 0.042 of the attacker's jobs, against 0.251 under B3). On three of the six markets the selected attack does not replace its identity at all." Add to Table 12, or to a new table, per rule and rate: the attacker's audited share, the share of audits that go to honest newcomers, and the number of winners with `x = 0`. All are in `diagnostics.json`.

**3. The two rates lie on the two sides of a saturation point, and the paper does not say so. (Text only for the statement; needs compute for the rates between.)**
- The share of honest identities younger than L = 10 rounds is 1 - (1 - p)^10: 0.096 at p = 0.01 and 0.401 at p = 0.05 (my arithmetic). The measured job shares are 0.085 and 0.355.
- The audit ratio is 0.25 (audits over served jobs in every churn cell; `sat.py`).
- At p = 0.01 the priority phase fits in the quota (R3 audits 0.880 of honest newcomers' jobs). At p = 0.05 it does not (0.571). The crossing is near p = 0.028 for these parameters (my arithmetic, ignoring capacity differences and the terminal reserve).
- So "does not survive honest churn" is a statement about one regime: honest newcomer volume above the audit quota. It depends on p, L, the audit ratio and the honest share of capacity, all fixed here.
- Fix (text): state the condition and the arithmetic beside the result, and say that the range between 0.01 and 0.05 is untested. Fix (compute): run p = 0.02 and p = 0.03 for the three rules. By the ledger, two rates cost about 5 USD.

**4. Efficiency under churn is in the records and not in the paper. (Analysis on existing records.)**
- Pooled gross efficiency under the selected attack, frozen searches (`eff_attack`, my computation): R3 0.994 (p = 0), 0.989 (0.01), 0.967 (0.05). C* 0.993, 0.993, 0.993. B3 0.959, 0.959, 0.940.
- On fresh2 at p = 0.05, R3's value is 0.893. The registered Q4 efficiency threshold is 0.90 (Table 3). This is a point estimate in an exploratory arm, not a registered failure.
- R3's gain at p = 0.05 is 0.580 on fresh1 and 0.365 on fresh3. The first test's absolute ceiling for R3's gain was 0.30 (p. 9).
- Fix: add efficiency columns to Table 12 and one sentence. State that the registered efficiency label "condition met" is also a no-churn result.

**5. The p = 0.05 result lacks the qualifications the paper gives elsewhere. (Analysis on existing records.)**
- Doubled searches: 5 of 6 markets, not 6 (fresh0 has the other sign for both contrasts).
- Market-level t intervals are missing (values in 4c, point 6).
- The frozen B3 value depends on one flagged cell (4c, point 5).
- Fix: print the per-market d and q for both versions (as the lower block of Table 11 does), the sign counts for both versions, and the t intervals. Replace "from 0.238 to 0.220" with "0.238 to 0.220 with the frozen searches (one flagged cell, fresh4) and 0.237 to 0.240 with the doubled ones".

**6. The p = 0.01 sentences read more from the frozen row than it can carry. (Text only; Run B would settle it.)**
- Evidence in 4c, points 3 and 4.
- Fix: "At p = 0.01 the B3 minus R3 gap is 0.175 with the frozen searches and 0.153 with the doubled ones, positive on every market. The C* minus R3 difference is 0.001 and -0.004; its sign is set by fresh1, where both cells are flagged (change 0.053), so it is not resolved." Add that 7 of the 18 cells at p = 0.01 are flagged.

**7. The abstract's first finding and its "direction R3 lower" label are now conditional, and the paper does not connect them to the churn result. (Text only.)**
- Quote (abstract): "R3 and C* are 'equivalent, direction R3 lower' within a pre-set margin of ±0.05".
- The registered label stays. But a reader must learn in the same place that the direction reverses by 0.173 at p = 0.05.
- The comparator caveat ("selected in development on gross efficiency in effect") now cuts the other way: a comparator that was not chosen for attacker gain is the one that is robust to churn. Whether that holds for another credibility rule is not known (see Run A).

**8. Reporting gaps against the plan. (Text only.)**
- Print the reselection diagnostic (16 of 36 nonzero, largest 0.0046) and the largest flag change (0.087).
- Add "raw profit units" to "rises by 113.101", or give 0.209 in gain units.
- Say that the timing check showed the old attack's profit rising with p.
- Say that the reference candidates are frozen and that the menus were not regenerated under churn (the plan says it; the paper says only "frozen truthful reference played under the same churn").

**9. Process records. (Text only.)**
- The ledger names no plan commit for the churn arm. Add ef17139 (11:45:42 UTC) and the pod request time (11:46).
- `SECOND_REVIEW_TRIAGE.md` reports a field rename that the package does not contain (section 3, row 5).
- The reset reproduction command needs `scipy`; say so, or remove the dependency.
- The paper states an authorisation of 55 USD (p. 12). The ledger gives a program total of 57.51 USD under a limit of 123 USD after the follow-ups. A search of the paper text for "USD" finds only the 12, 40, 43, 52 and 55 USD statements (pp. 10 and 12); the follow-up spend (1.65 and 4.99 USD by the ledger) is not stated. Add it.

**10. Length. (Text only.)**
- 33 pages. Each round adds pages. With the churn result the paper has a clear centre; see section 7.

## 6. Open runs, ranked

Neither approved run must be done before a WEIS submission. The text fixes of problems 1 to 6 must be.

**1. Run A, the runner-up comparator. It changes my score more, if it includes the churn cells.**
- As approved (six fresh markets, no churn), it tests the "direction R3 lower" label. That label matters less now.
- Extended with p = 0.05 (and p = 0.01), it answers the question the churn arm opened: is robustness to honest churn a property of verified-history targeting, or of one configuration, C-mem(6, 20)?
- If C-thr(12) is also robust, the paper's main claim becomes general across the comparator family, and WEIS moves to a firm 3 or to 4. If it is not, the claim stays about one rule, and the paper must say so.
- Recommended before WEIS. Not required, if the abstract keeps the comparator caveat.

**2. Run B, continued searches. It changes the p = 0.01 statements and little else.**
- Extend it to the 13 flagged churn cells. The cells that matter are fresh1 (R3 and C*, p = 0.01) and fresh4 (B3, p = 0.05).
- It cannot change the p = 0.05 result against C*: the gap there is 0.17, and the largest flag is 0.087 on a B3 cell.
- Required for AAMAS. Not required for WEIS.

**A run that is not on the list would move my score more than either: churn rates between 0.01 and 0.05** (new problem 3). It turns two points into a dose-response curve and tests the saturation account. It is the cheapest of the three.

## 7. Decision

| Venue | Score (1 to 5) | Acceptance probability | Confidence | Change that moves it most |
|---|---|---|---|---|
| WEIS 2027 | 3 (lower end) | 35% | Medium | Rebuild the paper around the reset and churn results in about 12 to 15 pages: abstract, title and conclusion state that age-ranked priority works only while the attacker is almost the only newcomer, with the saturation condition, the corrected mechanism, and rates at 0.02 and 0.03. That takes it to a firm 3 or to 4. |
| AAMAS main track | 2 | 12% | Medium | Run B on every flagged cell, churn cells included, plus the same restructuring. The 36 percent flag rate in the new arm (13 of 36) is the main obstacle for this venue. |
| ACM EC | 1 | 3% | High | A theorem: for age-ranked audits under a quota q, a bound on the attacker's audit probability as a function of the honest entry rate, L and q, with the threshold that the simulation shows. No planned simulation helps. |

The acceptance probabilities are my judgement; no file supports them. I do not know the WEIS 2027 deadline or page limit. Verify both.

**What I could not check:** the simulator itself (not in the package), the search and freeze records of the churn arm (169 of 206 inventory entries per rate are not in the package), the spend, and any DOI. The paper's references [13] (Friedman and Resnick, "The Social Cost of Cheap Pseudonyms", 2001, DOI 10.1111/j.1430-9134.2001.00173.x) and [11] (Feldman, Papadimitriou, Chuang and Stoica, "Free-Riding and Whitewashing in Peer-to-Peer Systems", 2006, DOI 10.1109/JSAC.2006.872882) are quoted from the paper's reference list (p. 30); the DOIs agree with my memory of these works, and I did not verify them online.
