claude-fable-5-2

# External review, round 5: "Checking Newcomers When Identities Are Free: Registered Tests of Age-Ranked Audits and Their Limit Under Honest Churn" (draft 10, 35 pages)

## 1. Files read

All paths are in `results/v2/review-fable52-r5/` unless stated.

- **Read in full:** `PROMPT.md`, `RESPONSE.md`, `PREVIOUS_REVIEW.md` (round 4), `outline-draft10.md`, `churn-plan.md` (draft 6), `runs/runner-up-plan.md`, `runs/run_a_analysis.py`, `runs/run_b_analysis.py`, `churn_paper.json`, `posthoc_churn_audit.tex`, `records/churn/run.json`, `records/churn/run_mid.json`, `records/churn/gate-p0/gate.json`.
- **`main.pdf` (35 pages, converted with `pdftotext -layout`):** pages 1 to 18 read in full (abstract to conclusion and availability). Pages 19 to 24 and 29 to 32 read in full. Pages 25 to 28 (prediction tables, Tables 19 to 25) read in part; the tool output was cut in the middle of Tables 20 to 22. Pages 33 to 35 (references) searched, not read line by line. Page numbers below are the printed page numbers.
- **Read by program (every field that I use):** `churn.json`, `churn_mid.json` (statistics, flags, expectations, `review_r4`), the 72 churn evaluation records and 72 churn doubling records, the four `records/churn/p*/diagnostics.json`, the 18 registered D2+H3 records in `records/eval_all/evaluate/`, `runs/runnerup_analysis.json`, `runs/convergence_analysis.json`, `records/diagnostics.json` (structure and the reset counts only), `reset.json`.
- **Read in part:** `operations-ledger.md` (the sections for the churn arm, churn amendment 1, Run A, Run B), `churn_block.py` (`audit_allocation`, `review_r4`, the command-line block), `SECOND_REVIEW_TRIAGE.md`, `RESPONSE_R4.md` (first 2,500 characters), `runs/convergence-plan.md` (not opened beyond its name; I use only the analysis output).
- **Not opened this round:** `PREVIOUS_REVIEW_R2.md`, `PREVIOUS_REVIEW_R3.md`, `PROMPT_R4.md`, `churn_v2.py`, `churn_paper.py` (run, not read), `test_*.py` (run, not read), `reset-experiment-plan.md`, `reset_followup_v2.py`, `reset_block.py` (run and searched for one field name), `reset_reference/`, `records/reference/`, `records/reset/`, `records/report.json` (used only as an input of the commands), `records/spot_compare.json`, `records/convergence/` (the 19 records and `recompute.json`; I rely on `convergence_analysis.json`), `protocol-v2.yaml`, `predictions-v2.md`, `revision-program-design.md`, `report.md`, `addendum.md`, `stability-result.json`, `audit.json`, `audit_v2.py`, `eligibility.json`, `scoring.json`, `score_v2.py`, `posthoc_v2.py`, `posthoc.json` (input only), `lottery_*.csv`, `h4-family.py`, `h4-containment.md`. I make no new claim about them.
- **A file that the brief names and the package does not contain:** `PROMPT.md` says that `churn-plan.md` holds "amendment 1 for p = 0.02 and 0.03 with expectations 5 to 8". The package copy is draft 6 only (266 lines; no line contains "amendment 1", "0.02" as a rate, or an expectation 5 to 8). I read the amendment in the repository instead: `docs/revision/churn/churn-plan-amendment-1.md`. This is outside the package, and I say so wherever I use it.
- **Run (the repository's `.venv` Python with numpy and scipy, flag `-I`; all output in the scratch folder):**
  - The two churn commands of `PROMPT.md`. Result: `churn.json` and `churn_mid.json` are identical to the package files except the `inputs` paths and one `run_json_sha256`; `posthoc_churn_all.tex` is byte-identical.
  - The `churn_paper.py` command. Result: `posthoc_churn_audit.tex` and `churn_paper.json` are byte-identical.
  - The reset command. Result: `posthoc_reset.tex` is byte-identical; `reset.json` is identical except the two `inputs` paths.
  - `pytest` on copies of `test_churn_paper.py` and `test_churn_block.py`: 42 passed.
  - My own recomputation from the raw records (`recompute.py` in the scratch folder; different code, bootstrap seed 777, 4,000 resamples). Interval bounds can differ from the paper's by 0.001.
  - Read-only `git log`, `git show` and `git diff` in the repository, for commit times and for the amendment text. This is outside the package.
- **No network.** I verified no DOI online, and I cite no source outside the paper's own reference list.

## 2. Summary verdict

Draft 10 does what round 4 asked. The paper now has one centre, the honest-churn result; it has four churn rates instead of two; the mechanism paragraph is corrected and careful; and every number in Section 10, Table 6 and Table 7 reproduces from the records, byte for byte for the tables and by my own recomputation for the text. The amendment for p = 0.02 and 0.03 was committed about nine hours before the pod started, and its four expectations are scored as written. The central finding stands under both search versions: at p = 0.05 the measured gain against R3 is 0.272, C* minus R3 is -0.173 (frozen) or -0.169 (doubled), and at p = 0.03 C* minus R3 is negative on all six markets in both versions. What does not stand as written is the precision around that finding. (1) "The pooled comparison with C* reverses between p = 0.01 and 0.02" is true for the frozen searches only, and at p = 0.02 it is one market (fresh1, -0.122); the other five average +0.001. (2) "Its advantage over uniform audits survives moderate churn" hides that at p = 0.03 B3 minus R3 is zero or slightly negative on three of six markets in both versions. (3) The new Run A sentence in the abstract, "a second verified-history comparator ... gives the attacker a lower gain than R3 (runner-up minus R3: -0.010)", rests on one market (fresh5, -0.059); R3 has the lower gain on 4 of 6 markets, and with the doubled X7-SC searches the pooled sign is +0.003 with the label "equivalent, direction R3 lower". (4) The headline diagnostics (0.366 to 0.042) and the efficiency sentence use the frozen winners only, and the doubled winners change two of the statements. All four are fixable with text and with analysis on existing records. Scores: **WEIS 2027: 3/5 (firm; 45%). AAMAS main track: 2/5 (upper end; 15%). ACM EC: 1/5 (3%).** WEIS moves from the lower end of 3 to a firm 3 because the paper no longer argues around its strongest result; it does not reach 4 because the main claim rests on one comparator under churn, 21 of 72 churn cells are flagged, and the abstract still states three things more exactly than the records allow.

## 3. Follow-through on round-4 problems 1 to 10

| # | Round-4 problem | Status | Revised sentence (printed page) | Is `RESPONSE.md` accurate? |
|---|---|---|---|---|
| 1 | Paper contradicted its churn arm | Resolved | "Without honest churn, R3 lowers the attacker's measured gain relative to B3 on every fresh market" (abstract, p. 1). "Section 10 relaxes this: honest opponents replace their identities at a fixed rate." (p. 5). "with honest churn it shares the newest positions with honest newcomers, and the bound is zero whenever a newer identity holds jobs or the quota is already spent (Section 10)" (p. 7). "R3's registered advantage is measured only when the attacker is almost the only source of new identities." (p. 17). The conclusion has the churn sentences (p. 18). No sentence with "untested" remains in pages 1 to 18. | Accurate on the content. Two small slips: the response says "Main text now ends on page 17 (the conclusion)", but the conclusion and the availability paragraph are on p. 18; and "Section 10, pp. 13 to 15" leaves out its Table 6 and Figure 1 (p. 16) and Table 7 (p. 17). |
| 2 | The stated mechanism was wrong | Resolved | "On two or three of the six markets, depending on the rate, R3's selected attack never replaces its identity (Table 7); there the attacker does not hide among the newcomers but stays old, and is audited only from what the priority phase and newest-first targeting leave." (p. 15). Table 7 gives the six columns that round 4 asked for, at four rates. | Accurate. Table 7 and `churn_paper.json` regenerate byte-identical. The refusal of my "overload case of Lemma 2" wording is correct: Lemma 2 bounds audits of young and replacement identities, and an identity that stays old is outside it. I withdraw that wording. One limit, see new problem 4: the table is for the frozen winners only. |
| 3 | Two rates on two sides of a saturation point | Resolved, with a better answer than the one I proposed | "The decline is gradual, not a threshold, and it does not explain both crossings" (p. 15). The rates 0.02 and 0.03 were run. | Accurate. The measured first-bin audited share of honest replacements under R3 is 0.880, 0.789, 0.706, 0.571 (`churn.json` and `churn_mid.json`, `expectations.5`): a steady decline. My round-4 threshold near p = 0.028 is not visible in the data, and the paper is right not to use it. |
| 4 | Efficiency under churn not in the paper | Partly resolved | "Under its selected attack, R3's gross efficiency falls from 0.989 at p = 0.01 to 0.967 at 0.05; C*'s stays at 0.993 and B3's is 0.940. The registered efficiency condition is a no-churn result." (p. 15) | Partly accurate. The response says the per-market value "is in `churn.json` (`review_r4.eff_attack` holds pooled values only)", which contradicts itself. The value is in the evaluation records: R3 on fresh2 at p = 0.05 is 0.893 with both the frozen and the doubled winner (my computation, mean of `eff_attack` over 200 seeds), below the registered Q4 threshold of 0.90. `outline-draft10.md` section 4 lists this value under "Also reported"; the paper does not report it. The sentence is also frozen-only (new problem 5). |
| 5 | Qualifications at p = 0.05 | Partly resolved | "At p = 0.05 C* minus R3 is negative on 6 of the six markets and B3 minus R3 on 6 with the frozen searches, and on 5 and 5 with the doubled searches (C* minus R3: -0.169; B3 minus R3: -0.033). Exploratory t intervals ... are [-0.352, 0.005] ... and [-0.119, 0.015] ...; they reach zero because the market values are very unequal, not because the sign varies. The frozen B3 value at this rate depends on one flagged cell (Table 6, doubled row)." (pp. 14 to 15) | Accurate for Section 10. Not carried to the abstract or the conclusion: both give "B3 minus R3 is -0.052" alone (pp. 1, 18). The frozen B3 winner on fresh4 at p = 0.05 has the knobs u0 = 1, m0 = 1, s = d = r = w = 0 (`records/churn/p0.05/diagnostics.json`), which is a search that did not move; its gain is 0.094 against 0.196 doubled. The per-market d and q block that round 4 asked for is not in the paper. |
| 6 | p = 0.01 read too strongly | Resolved in Section 10; not in the abstract | "At p = 0.01 the C* minus R3 difference is 0.001 with the frozen searches and -0.004 with the doubled ones, so the comparison with C* is not resolved there, while the B3 minus R3 gap is 0.175 and 0.153." (p. 15) | Accurate (the response gives p. 14; the sentence is on p. 15). The abstract then says the comparison "reverses between p = 0.01 and 0.02", which treats 0.01 as resolved positive (new problem 2). |
| 7 | Finding 1 conditional | Resolved for C*; the added Run A sentence is a new overclaim | "a second verified-history comparator, evaluated without churn, gives the attacker a lower gain than R3 (runner-up minus R3: -0.010)" (abstract, p. 1) | The response describes the change accurately. The sentence itself is not supported as written (new problem 1). |
| 8 | Reporting gaps | Resolved | "the largest flagged change is 0.088. Reselecting each rule's reference from its frozen menu under churn changes the reference in 32 of the 72 cells, by at most 0.009 in gain." (p. 15). "in raw profit units it rises by 113.101" (p. 15). "after a timing check on one market had shown the old attack's profit under R3 rising with p" (p. 14). "the reference menus were not regenerated" (p. 14). | Accurate on content: 0.0877 (`churn_paper.json` `flags.max_attack_change`, cell 0.03, fresh0, C*); 32 of 72 and 0.0095 (`flags`); 113.101 and -0.146 (my recomputation). The response gives p. 13 for the timing and menu sentences; they are on p. 14. |
| 9 | Process records | Resolved | Ledger, line 218: "the file as run is the one at commit ef17139 (2026-11-12 11:45:42 UTC), one minute before the pod request at 11:46". Appendix C: "ran under a separate follow-up cap of 72 USD ... Recorded spend: identity-replacement follow-up 1.65 USD; churn at p = 0.01 and 0.05, 4.99 USD; ..." (p. 30). | Accurate. `reset_block.py`, `reset.json` and `test_reset_block.py` now use `heldout_order_reversals` and no longer contain `nesting_failures` (my `grep`). The package copy of the plan is identical to the repository file at ef17139 (my `diff`, outside the package). The spend figures are not checkable. |
| 10 | Length | Resolved in pages; the centre still arrives late | Main text is 17.7 pages (draft 9: 30). | Accurate, with the page slip of row 1. See section 6. |

Other statements in `RESPONSE.md`:

- **"Not done" is accurate.** 21 flagged churn cells remain (13 + 8; `flag_summary.incomplete_n`). Run A and Run B hold no churn cell.
- **"Some round-4 quotations were already changed before round 4 was read" is consistent with the files.** `git log` shows 24b0c40 at 2026-11-12 21:47 UTC; I cannot check when round 4 was read.

## 4. The churn section (Section 10)

### (a) Plan fidelity

**Draft 6 (p = 0.01 and 0.05).** Unchanged since round 4. The package plan equals the repository file at ef17139. `records/churn/run.json` gives the pod allocation at 2026-11-12 11:46:11 UTC (my conversion of `started`). `gate-p0/gate.json` says `identical: true` with every difference 0.0. Expectations 1 to 4 score "met" under both versions (`churn.json` `expectations`); I agree.

**Amendment 1 (p = 0.02 and 0.03).** From the repository, outside the package:

- The amendment file was added in commit 2604ce6 at 2026-11-13 06:52:01 UTC. Its section 2 holds expectations 5 to 8.
- It was changed once, in e1c925a at 15:46:10 UTC. The diff touches only the launcher paragraph of section 1. Expectations 5 to 8 are the same text in both commits.
- `records/churn/run_mid.json` gives the pod allocation at 2026-11-13 15:53:33 UTC. The result commit is f682415 at 2026-11-14 02:55 (ledger).
- So the expectations were fixed about nine hours before the pod started. They were written after the 0.01 and 0.05 results and after round 4, and the amendment and the paper both say so.
- `churn_block.py` was changed in d3597ed at 15:56:19 UTC, three minutes after the pod allocation and eleven hours before the results. I read that diff: it adds the combined table, makes `--first` required, and makes the rate order free. It does not change `expectations_mid`.

**Are expectations 5 to 8 scored as written?** Yes.

| # | Amendment text (repository) | Frozen | Doubled | Score |
|---|---|---|---|---|
| 5 | R3 first-bin audited share of honest replacements below its 0.01 value and above its 0.05 value at both new rates, and lower at 0.03 than at 0.02 | 0.880, 0.789, 0.706, 0.571 | 0.854, 0.790, 0.706, 0.570 | met |
| 6 | Pooled C* minus R3 lower at 0.03 than at 0.02 | -0.020, -0.090 | -0.021, -0.063 | met |
| 7 | Pooled g(R3) at 0.02 below the midpoint of the no-churn and 0.05 values (0.168; 0.170) | 0.111 | 0.112 | met |
| 8 | B3 minus R3 positive on at least five of six markets at 0.02 | 5 | 6 | met |

Source: `churn_mid.json` `expectations`; sign counts also from my recomputation. The paper's summary of expectation 5, "that share under R3 falling across the four rates" (p. 15), is equivalent to the amendment text.

**Limits.**

- The amendment text is not in the package, so a reader of the package alone cannot do this check. Add the file.
- The paper is right that the expectations "carried little risk". Expectations 5, 6 and 7 are monotonicity statements between two known end points. Expectation 8 was the only one that could fail, and it passes with the frozen searches at exactly five.
- Table 7 and the abstract's audit shares come from `review_r4.audit_allocation`, which `churn_block.py` labels "post hoc, after external review round 4; not part of the plan". The plan's own diagnostic is the first-bin audited share of honest replacements (expectations 4 and 5). The paper's Table 7 caption says "Exploratory follow-up" but does not say that these statistics were defined after the 0.01 and 0.05 data were seen. They were defined before the 0.02 and 0.03 runs (commit 2604ce6), which is worth one clause.

### (b) Reproduction

"Recomputation" is my own script on the raw records. "Command" is the author's command, run by me.

| Item | Paper value | My value | Source |
|---|---|---|---|
| Table 6 (`posthoc_churn_all.tex`), all 50 point estimates and intervals | as printed | byte-identical file | Command |
| Table 6 point estimates, eight churn rows | as printed | all reproduced to three decimals | Recomputation |
| Table 6 intervals for d, q and g(R3) | as printed | reproduced; two bounds differ by 0.001 (q frozen 0.05: [-0.056, -0.049]; q frozen 0.01 upper 0.177) | Recomputation (other seed) |
| Table 7 (`posthoc_churn_audit.tex`), all 72 entries | as printed | byte-identical file | Command |
| Table 7, R3 attacker's audited share | 0.366, 0.190, 0.093, 0.042 | 0.366, 0.190, 0.093, 0.042 | Recomputation from the per-market `focal` counts in the four `diagnostics.json` |
| Table 7, efficiency column | as printed | reproduced for all 12 entries | Recomputation, mean of `eff_attack` per market, then market mean |
| Table 7, winners without replacement (R3) | 2, 2, 3, 3 of 6 | 2, 2, 3, 3 (frozen); **0, 2, 3, 3 (doubled)** | `diagnostics.json` `knobs.x` |
| Honest replacements per episode | 17.901, 35.777, 53.790, 89.582 | 17.901, 35.777, 53.790, 89.582 | `diagnostics.json`, R3 frozen cells, mean of six markets |
| Mean identity lifetimes 100, 50, about 33, 20 | stated | 1/p | Arithmetic |
| g(R3) 0.065 to 0.272 [0.268, 0.275] | p. 14 | 0.0649 to 0.2717 [0.268, 0.275] | Recomputation |
| g(C*) 0.086 to 0.098; g(B3) 0.238 to 0.220 | p. 14 | 0.0856 to 0.0983; 0.2383 to 0.2198 (frozen). Doubled: 0.097 to 0.103; 0.237 to 0.240 | `churn.json` |
| C* minus R3: 0.021, 0.001, -0.020, -0.090, -0.173 | p. 14 | reproduced (frozen). Doubled: 0.030, -0.004, -0.021, -0.063, -0.169 | `churn.json`, `churn_mid.json` |
| B3 minus R3: 0.173, 0.175, 0.119, 0.068, -0.052 | p. 14 | reproduced (frozen). Doubled: 0.170, 0.153, 0.127, 0.069, -0.033 | same |
| "more than three times the materiality margin" | p. 14 | 0.173 / 0.05 = 3.5; doubled 3.4 | Arithmetic |
| Sign counts at 0.05: 6 and 6 frozen; 5 and 5 doubled | pp. 14 to 15 | 6, 6; 5, 5 | Recomputation |
| t intervals at 0.05: [-0.352, 0.005], [-0.119, 0.015] | p. 15 | reproduced (frozen). Doubled: [-0.339, 0.001], [-0.064, -0.001], not printed | `review_r4.t95` |
| "At p = 0.03 ... negative on 6 of six markets, but at p = 0.02 only on 2" | p. 15 | 6 and 2 in both versions | Recomputation |
| Flags: 13 of 36, 8 of 36, largest 0.088 | p. 15 | 7 + 6 and 3 + 5; 0.0877 | Doubling records, `incomplete`, `attack_change` |
| Reselection: 32 of 72, at most 0.009 | p. 15 | 16 + 16; 0.0095 | `flag_summary.reference_changed`, `churn_paper.json` |
| Young honest: 0.391 of jobs, 0.823 of audits, established 0.078 (p = 0.05) | p. 15 | 0.3906, 0.8229, 0.0778 | `review_r4.audit_allocation` |
| C* attacker share "near a third (0.292 at p = 0.05)"; B3 0.251 | p. 15 | 0.363, 0.347, 0.335, 0.292; 0.251 | same |
| Attack profit +113.101; reference -0.146 [-0.393, 0.098] | p. 15 | +113.101; -0.146 (interval not recomputed) | Recomputation, raw profit, market means |
| Efficiency: R3 0.989 to 0.967; C* 0.993; B3 0.940 | p. 15 | reproduced (frozen). **Doubled at 0.05: R3 0.949, B3 0.959** | `review_r4.eff_attack`; recomputation |
| Expectation 4: 0.571 against 0.356 and 0.250 | p. 15 | 0.5707, 0.3560, 0.2502 | `churn.json` `expectations.4` |
| Expectations 1 to 8 "met" | p. 15 | all "met" | `churn.json`, `churn_mid.json` |
| Abstract: 0.366, 0.042, -0.173, -0.052 | p. 1 | reproduced (frozen only) | as above |
| Section 8: 0.028, 0.169, largest market change 0.054 (Run B) | p. 11 | 0.0282, 0.1695, 0.0538 (fresh3) | `runs/convergence_analysis.json` |
| Section 8: t intervals [-0.013, 0.054], [0.005, 0.044], [0.014, 0.045] | p. 11 | reproduced | My t intervals on the per-market values in `runnerup_analysis.json` |
| Section 8 and abstract: runner-up minus R3 -0.010 [-0.011, -0.009] | pp. 1, 11 | -0.0102 [-0.0113, -0.0092] | `runnerup_analysis.json` `D2+H3.base.runner_up_minus_r3` |
| "the two arms' p = 0 values agree" | implied by Table 6 | `combined_no_churn_check: ok`; `registered_check.ok: true` | `churn_mid.json` |
| Figure 1 | plotted | not checked point by point; the command regenerates a figure from the same two files | Command |
| Plan and amendment written before the runs | pp. 14 | consistent with commit and pod times | `git log`, `run.json`, `run_mid.json`; partly outside the package |
| Spend figures (p. 30) | stated | not checkable | Ledger text only |
| The simulator, the churn search and freeze records | - | not checkable | Not in the package |

One reconciliation with round 4. I reported 0.355 of jobs and 0.808 of audits for honest newcomers at p = 0.05; the paper has 0.391 and 0.823. Both are right. My values counted replacement identities only; the paper's also count the initial identities in their first ten rounds (`audit_allocation` docstring). I recomputed 0.355 and 0.808 with my old definition.

### (c) Word check

"Frozen" and "doubled" are the two search versions. A claim passes only if both support it, or if the sentence names the version.

**Section 10 (pp. 13 to 15).**

| Sentence | Verdict |
|---|---|
| "The advantage falls with the churn rate." (heading) | Holds. d falls at every step in both versions. q falls at every step with the doubled searches; with the frozen ones it moves from 0.173 to 0.175 first, which is no change. |
| "the gains against C* and B3 change much less" | Holds for the end points. Between them g(C*) moves by up to 0.03 with no pattern (frozen 0.086, 0.066, 0.091, 0.077, 0.098; doubled 0.097, 0.082, 0.091, 0.104, 0.103). That is search noise of the same size as d at 0.01 and 0.02, and the sentence should say so. |
| "The pooled comparison with C* thus reverses between p = 0.01 and 0.02" | **Frozen only.** With the doubled searches d is -0.004 [-0.005, -0.003] at 0.01, already negative. Two sentences later the paper itself says the comparison is "not resolved there". |
| "and the comparison with uniform audits between 0.03 and 0.05" | Holds pooled, both versions. See the per-market note below. |
| "at p = 0.05 the attack earns more against R3 than against the rule without audit priority" | Holds pooled, both versions (5 of 6 markets doubled). |
| "they reach zero because the market values are very unequal, not because the sign varies" | Holds for the frozen searches, which are the ones the intervals belong to. With the doubled searches fresh0 has the other sign (+0.005, +0.009). |
| "at p = 0.02 only on 2: the pooled reversal at that rate comes mostly from one market" | Holds, and it is stronger than stated: fresh1 is -0.122; the other five average +0.001 (my computation from `churn_mid.json`: +0.009, +0.004, -0.030, +0.006, +0.014). "Entirely" is the accurate word. |
| "under C* it stays near a third" | Loose. It falls from 0.363 to 0.292, a fifth. Give the four values. |
| "On two or three of the six markets, depending on the rate, R3's selected attack never replaces its identity" | Frozen only. Doubled at 0.01: none of six. |
| "R3's audit rate on the attacker falls below B3's between p = 0.01 and 0.02" | Holds for the pooled value in both versions (0.366 or 0.505, then 0.190 or 0.188, against 0.251). For the attacks that do not replace it is below B3's at every rate: 0.081 and 0.108 at p = 0.01 (my computation, fresh1 and fresh3, frozen). |
| "because the gain also depends on the rest of the selected attack" | A reason given without a test. Write "the gain also depends on". |
| "R3's gross efficiency falls from 0.989 at p = 0.01 to 0.967 at 0.05; C*'s stays at 0.993 and B3's is 0.940" | **Frozen only, and the order changes.** Doubled: R3 0.994 to 0.949; B3 0.959. With the doubled winners R3's efficiency under attack at 0.05 is below B3's. |
| "all eight expectations are met" | Holds. |
| "R3's measured advantage over C* exists only while the attacker is almost the only source of new identities" | "only" is carried by one comparator, six markets and four rates, and at 0.01 the result is unresolved. Acceptable inside the Scope paragraph, which lists these limits. |
| "its advantage over uniform audits survives moderate churn but not the highest rate tested" | **Pooled only.** At p = 0.03, q is negative on 3 of 6 markets in both versions (fresh0 -0.003, fresh2 -0.002, fresh5 -0.002; seed intervals [-0.005, -0.002], [-0.004, -0.000], [-0.003, 0.000]; `churn_mid.json` `ci95_markets`). The pooled 0.068 comes from fresh1, fresh3 and fresh4. It is also below the registered Q4 threshold of 0.10. "How firm the reversals are" gives the sign count for d at 0.03 and not for q. |

**Abstract (p. 1).**

- "R3's audits move to honest newcomers: the share of the attacker's jobs that R3 audits falls from 0.366 at p = 0.01 to 0.042 at p = 0.05". The direction holds in both versions (doubled: 0.505 to 0.028). The number 0.366 is a mixture: four winners that replace (0.425 to 0.642) and two that do not (0.081, 0.108), and those two are the flagged, under-searched cells of round 4 (fresh1 and fresh3 at 0.01; doubled gains 0.130 and 0.082 against 0.036 and 0.056). There is no p = 0 value of this statistic in the paper or in the records, so "move" has no measured starting point. The colon reads as a cause; Section 10 says the diagnostics "do not isolate the cause".
- "where C* minus R3 is -0.173 and B3 minus R3 is -0.052". Frozen only. -0.052 includes the failed fresh4 search; the doubled value is -0.033.
- "The pooled comparison with C* reverses between p = 0.01 and 0.02, and on every market at p = 0.03". The second half holds in both versions. The first half fails as above.
- "its advantage over uniform audits survives moderate churn". As above. "Moderate" also gives a size to rates that the paper calls "illustrative, not calibrated".
- "a second verified-history comparator ... gives the attacker a lower gain than R3". Not supported as a direction; see section 5.
- "one comparator under churn". Correct and necessary.

**Contributions (pp. 2 to 3).** "its pooled measured advantage reverses against the comparator at a churn rate between 0.01 and 0.02 per round (on every market at 0.03) and against uniform audits between 0.03 and 0.05": same two problems. "an attacker that keeps its identity is rarely audited" holds at every rate (0.012 to 0.108).

**Limits (p. 17).** "With honest churn it falls and reverses ...; that follow-up is exploratory, uses illustrative rates and frozen references, runs one verified-history comparator, and leaves the comparison with C* unresolved at the lowest rate." This is the best single statement of the result in the paper. The abstract should not be more exact than this sentence.

**Conclusion (p. 18).** "Against verified-history targeting, age-ranked audit priority holds its own in this model only while the attacker is almost the only newcomer". This drops "the one comparator run under churn" and so states the class claim that the Scope paragraph on p. 15 says the section does not show.

**Is the split between C* and B3 correct?** Yes in structure. The paper states the two contrasts separately everywhere, gives each its own crossing, and does not let the C* result stand in for B3. The errors are in the precision of each crossing, not in the split.

### (d) The mechanism paragraph

**Supported.**

- The description of where audits go. Every value regenerates, and the three audit columns are properties of the rule under its selected attack.
- "there the attacker does not hide among the newcomers but stays old". On the markets with x = 0 the attacker's newest share is exactly 0.00 and its audited share is 0.012 to 0.015 at p = 0.05 (my computation from `diagnostics.json`).
- "Lemma 2 does not cover such an attacker". Correct.
- "The decline is gradual, not a threshold". Correct for every column of Table 7.
- "The diagnostics describe the setting; they do not isolate the cause, because churn also resets histories, ends bans, and changes the selected attacks." This is the right limit, stated in the right place.
- "the rise in R3's gain comes mainly from the attack's profit". +113.1 against -0.146 in raw profit units; I add that the attack term rises with the rate: +0.07, +25.0, +55.9, +113.1 at the four rates (my recomputation).

**Missing, and it would strengthen the paragraph.**

- The decline holds inside each kind of attack, not only in the mixture. For winners that replace, the audited share falls from 0.43 to 0.64 at p = 0.01 to 0.04 to 0.10 at p = 0.05. For winners that do not replace, it falls from 0.08 to 0.11 to 0.012 to 0.015 (my computation, frozen). Without this split a reader can suspect that the pooled fall is only the switch from x = 1 to x = 0 on one more market.
- The reversal is not confined to the markets where the attacker stays old. fresh3 at p = 0.05 has x = 1, a newest share of 0.01, an audited share of 0.041, and d = -0.270. There the attacker does replace and is still not audited. The paragraph speaks only about the x = 0 markets.
- No matched comparison holds the attack fixed. The plan's timing check did this on one market for the old attack. Evaluating the registered no-churn winners under each churn rate, for the three rules, needs no search and would separate "churn changes the audits" from "churn changes the selected attack". This needs compute, but little.

**One causal slip.** The abstract's colon and the heading "Where the advantage lives" (Section 9) read as explanation. Section 10's own text is careful. Bring the abstract in line with it.

## 5. Run A and Run B

**Placement and labels.** Both appear only in Section 8 (p. 11), in the abstract, and in the Scope paragraph (p. 15). Both are called "exploratory follow-ups after the report". The paper says of the runner-up "evaluated on the same six markets without churn" and, in Scope, "evaluated without churn only". This is correct. The ledger says "No churn cells" for Run A, and the 19 Run B cells in `convergence_analysis.json` `status` are registered cells (10 fresh-market Q1 cells and 9 headline cells).

**Run B.** The three values reproduce (section 4b). "all passed within three rounds" matches `passed_within_three_rounds: 19`. Two things the paper should add: the Mac recomputation equals the pod's (`mac_equals_pod: true`), and passing a doubling check after continued search is still not convergence, in the paper's own words on p. 24: "an unflagged cell is not a converged one".

**Run A. The paper's sentence is not supported as a direction.**

Quote (p. 11): "The development runner-up comparator, C-thr(12), evaluated on the same six markets without churn, gives the attacker a pooled gain lower than R3 by -0.010 ([-0.011, -0.009]; "equivalent, direction comparator lower"): the registered direction holds for C*, not for verified-history targeting in general."

What `runs/runnerup_analysis.json` says (runner-up minus R3; positive means R3 leaves the lower gain):

| Family, version | Pooled | Markets positive | fresh5 | Pooled without fresh5 (my computation) | Label in the file |
|---|---|---|---|---|---|
| D2+H3, frozen | -0.010 | 4 of 6 | -0.059 | -0.0005 | equivalent, direction comparator lower |
| D2+H3, doubled | -0.005 | 4 of 6 | -0.059 | +0.006 | equivalent, direction comparator lower |
| X7-SC, frozen | -0.007 | 4 of 6 | -0.059 | +0.003 | equivalent, direction comparator lower |
| X7-SC, doubled | **+0.003** | 5 of 6 | **+0.004** | +0.003 | **equivalent, direction R3 lower** |

- The pooled sign is one market. On fresh5 the runner-up's X7-SC doubling check is flagged (`X7-SC.flags.fresh5.attack_change` 0.041), and the doubled X7-SC winner moves that market's difference from -0.059 to +0.004. X7-SC contains D2+H3, so the D2+H3 cell on fresh5 is under-searched by about 0.06 although its own doubling check is not flagged.
- 3 of the 6 D2+H3 runner-up cells are flagged (fresh0, fresh2, fresh4; changes 0.026, 0.016, 0.019). Run B did not continue them.
- A t interval over the six market differences, which the paper gives for C* minus R3 in the same paragraph, is [-0.036, 0.016] for the frozen D2+H3 values (my computation). It contains zero.
- The paper reports one of the four rows, without the sign count, the doubled value, the flags or the t interval. For C* minus R3 it reports all of them.
- "lower than R3 by -0.010" is a double negative. Write "lower than R3 by 0.010" or "runner-up minus R3 is -0.010".

**What Run A does and does not change.**

- It does not change the registered label. "Equivalent, direction R3 lower" is a statement about C* under the prescribed searches, and it stays.
- It does support the paper's negative statement: the registered direction is not established for verified-history targeting in general. The runner-up and R3 are within 0.01 of each other in every row, far inside the margin.
- It does not support the positive statement in the abstract that the second comparator "gives the attacker a lower gain than R3". The supported sentence is: "A second verified-history comparator, evaluated without churn, is also equivalent to R3 within the margin; its direction depends on one market and on the search version (runner-up minus R3 from -0.010 to +0.003)."
- It gives one clear result that the paper does not state: C* minus runner-up is +0.031 (frozen D2+H3; +0.034 doubled, positive on 6 of 6, t interval [0.006, 0.062]; my computation). So the registered comparator was the weaker of the two finalists on attacker gain, as the development recheck suggested and as the Run A expectation predicted ("met"). The paper may say that R3's measured edge of 0.021 over C* is an edge over the weaker finalist.
- It sharpens the main open question. The comparator that is at least as good as R3 without churn has not been run with churn. If C-thr(12) keeps its gain near 0.07 to 0.10 under churn, as C* does, the paper's main claim holds for both finalists. If not, the claim is about C-mem(6, 20).

## 6. Structure and length

**Is there a clear centre?** Yes, and that is the main gain of this draft. Title, abstract, contributions, limits and conclusion all lead to Section 10, and Figure 1 shows the result in one picture. Main text is 17.7 pages against 30.

**The centre arrives late.** The churn section starts on p. 13 of 18, and its table and figure are on pp. 16 and 17, after the section's text and inside Section 11. A reader meets nine pages of model, theory, attack families and registration detail first.

What should move or be cut:

1. **Section 7, "Calibration" and the inference paragraph (pp. 9 to 10, about 0.7 page).** Fixture pools, Clopper-Pearson bounds and Holm families support Q1 and Q4 labels that are no longer the centre. Keep three sentences and Table 2; move the rest to Appendix C.
2. **Section 8, the Q1 paragraph (pp. 11 to 12).** It is one paragraph of about 70 lines with eight interval statements. Split it: the registered result (10 lines), sensitivity (Run B, doubled, strongest family, t intervals; a small table instead of prose), the comparator caveat with Run A, and the honest-replacement diagnostic. The fresh1 "numerically extreme studentized intervals" passage (pp. 10 to 11) belongs in the appendix.
3. **Section 5, Theorem 1 (p. 7).** The paper says "No reported result depends on it." Move the theorem and its caveat to Appendix E. Keep Lemma 1, Corollary 1, Lemma 2 and Proposition 1.
4. **Table 1 (p. 8).** The results in the main text use D2, D2+H3 and X7-SC; the other six rows (H2, X5-AG/v2, H4, the welfare attacks and the two coalition families) carry results that are now in Appendices A and B. Name the three families in the text and move the table.
5. **FlashProve.** It appears in the introduction (p. 1 to 2), in related work (p. 4) and in "Exact but costly checks" (p. 17). Once is enough; the p. 17 paragraph itself says it "changes none of their claims".
6. **Section 9.** One paragraph of 45 lines. The S statistic with its leave-one-out range can go to Appendix A; the text needs the two gaps, the t interval and the expectations.
7. **The conclusion (p. 18).** One paragraph of 27 lines that repeats the abstract with more numbers. Cut it to the three results and the one open question.
8. **Float placement.** Table 5 (reset) sits in the middle of Section 10 (p. 14), and Tables 6 and 7 and Figure 1 follow the section. Place Figure 1 on page 2 or 3 beside "Results in brief", and Tables 6 and 7 inside Section 10.
9. **Cross-references.** "Section 8 reports an exploratory matched comparison with replacement disabled, within the D2 family only" (p. 5) and "the exploratory D2-family comparison of Section 8" (p. 16) point to the wrong section. The reset follow-up is Section 9.
10. **"Results in brief" (p. 3)** lists Q1, Q4, Q2 and Q3 and ends "The two follow-ups are in Sections 9 and 10." In a paper built around the follow-ups, this paragraph should give their results first.

With items 1 to 7 the main text is about 14 pages and the churn section starts near p. 9.

**Is the subtitle honest?** Mostly. "Registered Tests of Age-Ranked Audits and Their Limit Under Honest Churn" can be read as "registered tests of (age-ranked audits and their limit)", which would make the churn limit a registered result. The abstract corrects this at once ("Two exploratory follow-ups, specified after the report"). `outline-draft10.md` section 2 already has the unambiguous form: "... Two Registered Tests and an Exploratory Churn Limit". Use it, or "Registered Tests of Age-Ranked Audits and an Exploratory Limit Under Honest Churn".

## 7. New problems, ranked by severity

**1. The Run A sentence states a direction that depends on one market and reverses with the doubled X7-SC searches. (Text only, with one small analysis on existing records.)**
- Quotes: abstract, p. 1: "a second verified-history comparator, evaluated without churn, gives the attacker a lower gain than R3 (runner-up minus R3: -0.010)". Section 8, p. 11, quoted in section 5.
- Evidence: the table in section 5.
- Fix (text): replace the abstract clause with "a second verified-history comparator, evaluated without churn, is also equivalent to R3 within the margin, with a direction that depends on one market and on the search version (runner-up minus R3: -0.010 to +0.003)". In Section 8 give the four rows, the sign counts, the flags (3 of 6 and 1 of 6) and the t interval, as for C*. Remove the double negative.
- Fix (analysis on existing records): add a small table from `runnerup_analysis.json`; add C* minus runner-up (+0.031, +0.034).

**2. The C* crossing is stated more exactly than the searches resolve. (Text only.)**
- Quotes: abstract, p. 1: "The pooled comparison with C* reverses between p = 0.01 and 0.02". Contributions, p. 3: "reverses against the comparator at a churn rate between 0.01 and 0.02 per round". Section 10, p. 14: "thus reverses between p = 0.01 and 0.02".
- Evidence: doubled d at 0.01 is -0.004 [-0.005, -0.003]; at 0.02, d is -0.122 on fresh1 and +0.001 on average elsewhere, with 4 of 6 markets positive in both versions; the t intervals at 0.02 are [-0.075, 0.035] and [-0.075, 0.033] (`churn_mid.json` `review_r4.t95`); g(C*) itself moves by 0.02 to 0.03 between search versions at 0.01 and 0.03.
- Fix: "The comparison with C* is not resolved at p = 0.01 or 0.02 (pooled -0.004 to 0.001 and -0.020; one market sets the sign) and is negative on every market at p = 0.03 (-0.090; doubled -0.063) and on five or six at 0.05." Use this in the abstract, the contributions and Section 10. Print the t intervals at all four rates, not only at 0.05; they are already in the two JSON files.

**3. "Survives moderate churn" is a pooled statement that half the markets do not support. (Text only.)**
- Quotes: abstract, p. 1; Scope, p. 15; conclusion, p. 18: "its advantage over uniform audits survives moderate churn but not the highest rate tested".
- Evidence: section 4c. At p = 0.03 three of six markets have q at or below zero in both versions, and the pooled q is 0.068, below the registered 0.10 threshold of Q4. At p = 0.02 the pooled q is 0.119 to 0.127 with 5 or 6 markets positive.
- Fix: "Against uniform audits the pooled gap shrinks from 0.173 to 0.12 at p = 0.02 and 0.07 at p = 0.03, where it is carried by three markets and is zero on the other three, and it is negative at p = 0.05 (-0.033 to -0.052)." Add the q sign count at 0.03 to "How firm the reversals are". Drop "moderate".

**4. The headline diagnostics are post hoc and frozen-only, and the abstract's starting value is a mixture that includes two under-searched cells. (Analysis on existing records.)**
- Quotes: abstract, p. 1: "falls from 0.366 at p = 0.01 to 0.042 at p = 0.05"; Table 7 caption, p. 17: "under the rule's selected attack (frozen searches)".
- Evidence: doubled values 0.505 and 0.028; winners without replacement 0 of 6 at 0.01 with the doubled searches; `review_r4` label "not part of the plan"; no p = 0 value.
- Fix: add the doubled rows to Table 7 (all values are in `review_r4.audit_allocation`, keys `F111|doubled` and so on). Add two columns or a short lower block: the attacker's audited share for winners that replace and for winners that do not. In the abstract write "falls from 0.37 to 0.51 at p = 0.01 to 0.03 to 0.04 at p = 0.05, depending on the search version". Say in the caption that these statistics were defined after the 0.01 and 0.05 results and before the 0.02 and 0.03 runs.
- A p = 0 row for Table 7 **needs compute** (a diagnostics pass over the 18 registered winners; no search). It would give "move" a starting point.

**5. The efficiency sentence is frozen-only; the doubled winners reverse its order, and one market is below the registered threshold. (Analysis on existing records.)**
- Quote (p. 15): "Under its selected attack, R3's gross efficiency falls from 0.989 at p = 0.01 to 0.967 at 0.05; C*'s stays at 0.993 and B3's is 0.940."
- Evidence: doubled at 0.05: R3 0.949, C* 0.993, B3 0.959 (`churn.json` `review_r4.eff_attack.doubled`). B3's frozen 0.940 comes from the fresh4 cell whose search did not move (problem 5 of round 4). B3's column in Table 7 is 0.959, 0.950, 0.976, 0.940, which is the selected attack changing, not churn. R3 on fresh2 at 0.05 is 0.893 in both versions; with the doubled winners fresh0 is 0.941 and fresh5 is 0.947 (my computation).
- Fix: give both versions; replace "B3's is 0.940" with "B3's is 0.940 to 0.959, without a trend"; add "on fresh2 R3's efficiency under attack is 0.893, below the registered 0.90 threshold of Q4; this is an exploratory point estimate, not a registered failure".

**6. The abstract and the conclusion give -0.052 without the doubled value that Section 10 says is the sounder one. (Text only.)**
- Quotes: abstract, p. 1, and conclusion, p. 18: "B3 minus R3 is -0.052".
- Fix: "-0.052 (-0.033 with the doubled searches; the frozen value includes one failed search)".

**7. The conclusion states the class claim that the Scope paragraph denies. (Text only.)**
- Quote (p. 18): "Against verified-history targeting, age-ranked audit priority holds its own in this model only while the attacker is almost the only newcomer".
- Scope (p. 15): "this section does not show that verified-history targeting in general is robust to churn".
- Fix: "Against the one verified-history comparator run under churn, ...".

**8. The mechanism text covers only the markets where the attacker stays old. (Analysis on existing records.)**
- Evidence: section 4d. fresh3 at p = 0.05 replaces, is audited on 0.041 of its jobs, and has d = -0.270.
- Fix: one sentence: "Where the selected attack does replace, it is the newest job-holding identity in 0.01 to 0.03 of rounds at p = 0.05 and is audited on 0.04 to 0.10 of its jobs." Values from `diagnostics.json` (`focal_newest_by_first_offer_assigned`, `focal` counts).

**9. Search quality in the churn arm is unchanged, and the flags sit on cells that set the uncertain statements. (Needs compute.)**
- 21 of 72 cells are flagged, 29 percent. The largest changes are on C* at p = 0.03 (fresh0 0.088, fresh1 0.076), which is why d at 0.03 is -0.090 frozen and -0.063 doubled, and on B3 at p = 0.05 (fresh4 0.087).
- The conclusions that survive without further search: d at 0.03 negative on 6 of 6 in both versions; d at 0.05 near -0.17 in both; q at 0.05 negative pooled in both.
- Fix: continue the 21 flagged churn cells with the Run B driver, or state in the abstract that 21 of 72 churn cells are flagged. The paper already says so on p. 15.

**10. Package completeness. (Text only.)**
- `churn-plan-amendment-1.md` is not in the package although `PROMPT.md` says the plan file contains it.
- The Run A and Run B drivers are not in the package (stated in `PROMPT.md`).
- `churn_mid.json` `inputs.churn` points to `results/v2/followup`, while the amendment says the output is `results/v2/followup-churn-mid/`. The numbers are not affected; the path record is confusing.

**11. Small errors. (Text only.)**
- Cross-references to "Section 8" for the reset follow-up (pp. 5, 16).
- "lower than R3 by -0.010" (p. 11).
- "stays near a third" for a value that falls from 0.363 to 0.292 (p. 15).
- The opening of Section 8 (p. 10) lists exploratory tables by number and does not mention Tables 5 to 7.

**Not a problem, checked because round 4 raised it:** the gain definition (largest deviation from the formula below 1e-12 on the cell I tested), the seed pairing between churn and no-churn records (equal seed lists in all 24 R3 cells), and the audit ratio in the churn cells (0.250 to 0.254 over all 144 diagnostic profiles; my computation).

**A post hoc choice that could drive a conclusion.** The choice of the frozen searches as primary is the paper's standing convention and is not post hoc. But in the churn arm it decides three printed numbers in the abstract (0.366, -0.052, and the 0.01 to 0.02 crossing), and each of the three is the less favourable to R3 of the two versions or the more exact of the two. No conclusion about the sign at 0.03 or 0.05 depends on it. The young-identity cut at ten rounds equals L and is not a free choice.

## 8. Decision

| Venue | Score (1 to 5) | Acceptance probability | Confidence | Change that moves it most |
|---|---|---|---|---|
| WEIS 2027 | 3 (firm) | 45% | Medium | Run the runner-up C-thr(12) under churn at the four rates (the same 36-cell design as amendment 1; the ledger puts one such arm at 5 to 8 USD). If it is also robust, the main claim holds for both finalists of the comparator family and the score goes to 4. Together with the text fixes of problems 1 to 7, which are required either way. |
| AAMAS main track | 2 (upper end) | 15% | Medium | Continued searches on the 21 flagged churn cells and the 4 flagged Run A cells, plus a fixed-attack evaluation under churn that separates the audit effect from the change of the selected attack. The 29 percent flag rate and the single comparator are the obstacles here. |
| ACM EC | 1 | 3% | High | A theorem. The data now suggest its form: under a per-round quota k, an identity older than every newcomer receives at most its share of max(0, k - Y) residual audits, with Y the jobs of identities younger than L; with honest entry rate p, Y grows like 1 - (1 - p)^L of honest capacity. A bound of this kind with the measured curve of Table 7 as its check would make the paper an EC submission. No simulation does. |

The acceptance probabilities are my judgement; no file supports them. I do not know the WEIS 2027 deadline or page limit; `outline-draft10.md` says no 2027 call was found on 2026-11-16.

**What I could not check:** the simulator and the search code (not in the package); the churn search and freeze records; the 19 Run B records themselves (I used the analysis output and its `mac_equals_pod` flag); the Run A records (analysis output only); every spend figure; whether the amendment was written before the author saw any 0.02 or 0.03 result other than through the commit and pod times; and every DOI. I cite no source beyond the paper's own reference list, and I verified none of its entries online.
