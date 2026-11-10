# Triage of the Fable 5.2 reviews (2026-11-10)

Sources: `docs/revision/roster/fable52-paper-r1.md` (fresh referee: WEIS 2/5, AAMAS 2/5, EC 1/5) and
`docs/revision/roster/fable52-reset-driver-r1.md` (the reset driver and plan). Author's instruction: fix everything;
report any new simulation needed.

Verdicts come from commands on the records (`results/v2/report/report.json`, `results/v2/deviation/stability.json`,
`results/v2/eval/all`, `experiments/v2/comparator.json`, git history, Crossref).

## Paper review

| # | Claim | Verified | Action | Kind |
|---|---|---|---|---|
| 1 | "Equivalent" rests on the margin; market variation and search error can cross it | **Holds** in part: the t-interval over the six market differences is [-0.013, 0.054] (D2+H3) and [0.005, 0.044] (X7-SC); one doubled search raises fresh3's C* gain by 0.054 (C*-R3 contrast by 0.053). **Wrong** in part: the margin was not set after development (design 2a288f5, 2026-10-22; development d values c5227a0, 2026-10-28). | Exploratory market-level block in posthoc (t-interval, sign count, relative difference); the text says the registered interval holds the six markets fixed; "equivalent" glossed as "within the pre-set materiality margin"; the response rebuts the timing claim | analysis on existing records, text |
| 2 | The two Q1 families are mostly one test | **Holds**: the X7-SC winner is the embedded D2+H3 winner (`best_source` `incumbent:embedded_h3`, identical evaluated gains) in 10 of 12 Q1 cells and in 12 of 14 market-rule cells with the headline (Fable said 11 of 14); only fresh3 C* and fresh4 F111 differ | Count in posthoc; text states it at Q1 and in contributions; Q3-a's zeros explained | analysis on existing records, text |
| 3 | Searches too weak for "robust" or "equivalent" | **Holds**: 21 of 98 doubling checks flagged; X5-AG/v2 is C*'s training-selected envelope family on fresh1-3 (report q3.envelope; on fresh2 its evaluation gain is lower than X7-SC's, 0.072332 vs 0.072697) | Envelope difference (C* minus R3, each rule's strongest training-selected family) in posthoc; text | analysis on existing records, text; convergence search **needs compute** |
| 4 | No honest churn: age labels the attacker | **Holds** in part: the nine honest opponents never replace; a new identity marks a replacement history, which identifies neither dishonest delivery nor an attack (a truthful focal provider may replace after a false failure) | Limitation stated in model, discussion, abstract scope | text; honest-churn arm **needs compute** |
| 5 | C* not selected on gain | **Holds**: all 12 scores in `comparator.json` are 0.103-0.111, the efficiency term, so gain never binds. Correction (internal review r1): the gains **are** stored in `experiments/v2/log/Cstar__*.json` `detail`; at the inner budget every configuration's selected attack has gain 0 or below; in the full-budget rechecks the runner-up C-thr(12) leaves 0.076 vs C* 0.097 (headline) and 0.018 vs 0.038 (dev0) under D2+H3 | Text: efficiency in effect; the runner-up's lower development gain | text; C-thr(12) on the fresh markets **needs compute** |
| 6 | Corollary close to a restatement; abstract drops conditions | **Holds** (abstract) | Abstract and intro state the conditions; corollary text names honest non-reacting rivals, no lost round, no identity memory | text |
| 7 | Lemma: "audit dues", age undefined, "served" ambiguity, Theorem 1 unused | **Holds**: paper says "younger than L rounds", design measures age from the first offer | Drop "audit dues"; define age; Theorem 1 marked as not used by the results | text |
| 8 | Contribution (iii) is arithmetic; W1 returned the null policy | **Holds** in substance: W1 gain 0.0000 [0.0000, 0.0000]; the doubled W1 winners for R3 and C* have zero shading with the replacement option on (`x = 1`), i.e. truthful delivery, not a null policy | Text: W1 found no profitable attack; the mixture paragraph shortened (three sentences, the repeated closure claim removed), the abstract sentence removed, contribution (iii) now the honest-replacement cost | text |
| 9 | Priority phase redundant given G | **Holds**: P given G=1 is -0.0014 | Abstract and contributions state it | text |
| 10 | Statistics do not address the main uncertainty | **Holds** (same as 1, 3) | Covered by 1 and 3; calibration detail kept but after results in the venue cut | text |
| 11 | Process facts | **Holds**: the executor resumed the H4 session (ledger 2026-11-02) | Text: who ran the H4 session; H4 contains D2+H3; Q3-e margin; tally double count | text |
| C | Harrington 1988, Dellarocas 2005, Golle and Mironov 2001 | **Real** (Crossref: 37(1):29-53; 16(2):209-230; LNCS CT-RSA 2001, 425-440) | Add to related work | text |
| P | Presentation: abstract, codes, venue version | Holds | Abstract rewritten to four plain findings (about 490 to 328 source words, `wc -w` with each site counted as one word, after the round-3 scope corrections); full venue cut stays a separate task | text |

## Driver review

| # | Finding | Action |
|---|---|---|
| 1 | No cross-check of rule parameters, runner, root, seeds against the paired records | Check each job against its reference record's provenance |
| 2 | Code state not pinned; `git_commit: unknown` accepted; no environment record | Refuse "unknown"; check scripts/ and sim/ against protocol-v2; environment block in the inventory |
| 3 | Section 4 diagnostics not built | Build (free on the Mac) before the pod |
| 4 | Doubling path has no ground truth | Reproduce one registered D2+H3 doubling record |
| 5 | `check_out` ignores `--src` | Refuse out equal to or inside src |
| 6 | Salt check after the search | Check before the search |
| 7 | `inputs()` conflict gaps; freeze cuts and h4 not asserted | Fix and test |
| 8 | `accept` trusts inputs.json | Recompute from src when given |
| 9 | Follow-up tests outside `testpaths` | Add docs/revision/followup to the project's test command |
| 10 | Budget wrapper can lower the limit | Refuse a limit below spend plus the new cap |
| plan | Exact-identity rule unattainable; ambiguous per-market scoring; S bias; doubling flag mixes two causes | Plan draft 5 |

## Simulations needed (author decides)

1. Honest-churn arm (paper 4).
2. Search to convergence on the flagged Q1 and Q4 cells (paper 3).
3. The full-budget runner-up C-thr(12), which left a lower development gain than C*, on the six fresh markets under D2+H3 and X7-SC with doubling checks (paper 5): about 1.90 USD. The 12 configurations' development gains exist (inner budget, uninformative); full-budget rechecks of the other ten would add about 3.2 USD.
4. The reset experiment (already approved, cap 10 USD), with the reproduction gate on the pod (driver review).
