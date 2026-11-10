# Triage of the Fable 5.2 reviews (2026-11-10)

Sources: `docs/revision/roster/fable52-paper-r1.md` (fresh referee: WEIS 2/5, AAMAS 2/5, EC 1/5) and
`docs/revision/roster/fable52-reset-driver-r1.md` (the reset driver and plan). Author's instruction: fix everything;
report any new simulation needed.

Verdicts come from commands on the records (`results/v2/report/report.json`, `results/v2/deviation/stability.json`,
`results/v2/eval/all`, `experiments/v2/comparator.json`, git history, Crossref).

## Paper review

| # | Claim | Verified | Action | Kind |
|---|---|---|---|---|
| 1 | "Equivalent" rests on the margin; market variation and search error can cross it | **Holds** in part: the t-interval over the six market differences is [-0.013, 0.054] (D2+H3) and [0.005, 0.044] (X7-SC); one doubled search moves fresh3 by 0.053. **Wrong** in part: the margin was not set after development (design 2a288f5, 2026-10-22; development d values c5227a0, 2026-10-28). | Exploratory market-level block in posthoc (t-interval, sign count, relative difference); the text says the registered interval holds the six markets fixed; "equivalent" glossed as "within the pre-set materiality margin"; the response rebuts the timing claim | analysis on existing records, text |
| 2 | The two Q1 families are mostly one test | **Holds**: the X7-SC winner is the embedded D2+H3 winner (`best_source` `incumbent:embedded_h3`, identical mean gain) in 10 of 12 Q1 cells; only fresh3 C* and fresh4 F111 differ | Count in posthoc; text states it at Q1 and in contributions; Q3-a's zeros explained | analysis on existing records, text |
| 3 | Searches too weak for "robust" or "equivalent" | **Holds**: 21 of 98 doubling checks flagged; X5-AG/v2 beats X7-SC against C* on fresh1-3 (report q3.envelope) | Envelope difference (C* minus R3, each rule's strongest training-selected family) in posthoc; text | analysis on existing records, text; convergence search **needs compute** |
| 4 | No honest churn: age labels the attacker | **Holds** (model: nine honest providers never replace) | Limitation stated in model, discussion, abstract scope | text; honest-churn arm **needs compute** |
| 5 | C* not selected on gain | **Holds**: all 12 scores in `comparator.json` are 0.103-0.111, the efficiency term; the gain term is about 0.7 at the gains seen, so it never binds; per-configuration gains are not stored | Text: the selection was in effect on efficiency | text; gains of the 12 configurations **need compute** |
| 6 | Corollary close to a restatement; abstract drops conditions | **Holds** (abstract) | Abstract and intro state the conditions; corollary text names honest non-reacting rivals, no lost round, no identity memory | text |
| 7 | Lemma: "audit dues", age undefined, "served" ambiguity, Theorem 1 unused | **Holds**: paper says "younger than L rounds", design measures age from the first offer | Drop "audit dues"; define age; Theorem 1 marked as not used by the results | text |
| 8 | Contribution (iii) is arithmetic; W1 returned the null policy | **Holds**: W1 gain 0.0000 [0.0000, 0.0000]; the doubled W1 winner has every knob 0 | Text: W1 found no attack; the mixture shrinks to one sentence | text |
| 9 | Priority phase redundant given G | **Holds**: P given G=1 is -0.0014 | Abstract and contributions state it | text |
| 10 | Statistics do not address the main uncertainty | **Holds** (same as 1, 3) | Covered by 1 and 3; calibration detail kept but after results in the venue cut | text |
| 11 | Process facts | **Holds**: the executor resumed the H4 session (ledger 2026-11-02) | Text: who ran the H4 session; H4 contains D2+H3; Q3-e margin; tally double count | text |
| C | Harrington 1988, Dellarocas 2005, Golle and Mironov 2001 | **Real** (Crossref: 37(1):29-53; 16(2):209-230; LNCS CT-RSA 2001, 425-440) | Add to related work | text |
| P | Presentation: abstract, codes, venue version | Partly | Abstract rewrite to plain findings; full venue cut stays a separate task | text |

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
3. Gains of the 12 comparator configurations, and a gain-selected comparator on the fresh markets if another is lower (paper 5).
4. The reset experiment (already approved, cap 10 USD), with the reproduction gate on the pod (driver review).
