# External review prompt, round 4 (paste this; attach the files listed under "Materials")

You are a senior referee and area chair with expertise in mechanism design (costly verification, repeated games, procurement), algorithmic game theory and multi-agent systems, security economics (Sybil attacks, whitewashing, audit games), and empirical methodology (pre-registration, adversarial evaluation, multiple testing). Review this paper as you would for a top venue. Be adversarial and specific. Do not soften findings. Give numbers where we ask for numbers, and say how confident you are.

## Context

The paper studies a repeated procurement market with noisy delivery, costly exact audits, and free identity replacement. It compares audit rules that target new or unverified identities and reports two registered tests.

- **First test (October 2026):** the original claim failed against a sealed attacker family; an amended claim, registered after development results were seen, passed on the public identity-replacement family.
- **Second test (November 2026):** registered before any outcome existed (signed tag `protocol-v2`, OpenTimestamps proof attested in Bitcoin), with six fresh market instances drawn after the lock from a Bitcoin block hash. Four questions: Q1 compares R3 with the best of four tested verified-history comparators (C*); Q2 decomposes R3 into three parts in a factorial; Q3 measures attack strength (stronger, independently authored, welfare, coalition attacks, and a repair at high audit cost); Q4 repeats the first test's comparison on the fresh markets.
- **Results, in short:** Q1 equivalent within the margin (R3 slightly lower attacker gain); Q2 the two targeting parts are substitutes and pacing adds little; Q3 an unconstrained welfare attack lowers every rule's efficiency, and the repair helps only partly; Q4 replicates on 3 of 6 markets. 10 of 18 registered predictions were fulfilled.
- **Two deviations, disclosed:** the fresh-market configurations differ from the registered ones by one unit in the last binary place (evaluation on Linux, registration on arm64); a re-evaluation with the registered configurations leaves every Q1 and Q4 decision unchanged. The evaluation budget cap was raised from 40 to 43 USD.
- **The results are final.** The registered evaluation will not be rerun. Internal reviewers (two models) reached consensus on the report and the paper; we want an independent judgement, not a confirmation.

## Materials (attached)

1. `PROMPT.md`: this prompt.
2. `main.pdf`: the paper, draft 9 (22 pages).
3. `report.md`: the report that the tagged code wrote from the evaluation records; `addendum.md`: interval labels, claim scope, both deviations with hashes, search-flag dependencies traced through the records, and per-market side fields. The addendum changes no estimate or decision.
4. `protocol-v2.yaml`: the registered protocol (decision rules, predictions, budget, calibration multipliers).
5. `revision-program-design.md`: the design of the second test. Section 9 holds the estimands, decision rules, and claim scope.
6. `predictions-v2.md`: the registered predictions and their scoring rules.
7. `operations-ledger.md`: what ran, when, at what cost, and every deviation and incident.
8. `h4/family.py`, `h4/containment.md`: the independently authored, defence-aware attacker (H4), released after the report review.

## Constraints (so that your suggestions are feasible)

- **No new registered runs.** Text changes are free. Descriptive analyses on the existing records are possible on a laptop. About 5 USD of pod compute remains in the approved budget; anything above needs the author's approval, so say what it would buy.
- **Stated non-goals:** no LLM attackers, no change to the market model, no rule outside the admissible class, no population-level claim about all markets. If a non-goal makes the paper unacceptable, say so.
- **Both tests stay as registered.** The paper reports the first test's failure and amendments as they happened.

## Task 1: Does the paper say what the evidence shows?

For each result sentence in the abstract, introduction, results (section 9), discussion, and conclusion, check it against `report.md` and `addendum.md`. List every sentence that overclaims, misstates a sign or a category, omits a required qualification (search flags, claim scope, deviations), or that a skeptical referee would read differently. Quote the sentence and give the exact correction.

## Task 2: Is the method sound?

1. Are the registered decision rules applied as registered (Holm within Q1 and within Q4, calibrated Bonferroni intervals, the Q1 categories with the efficiency condition, the Q4 intersection-union test)? Name any forking path that remained after the lock.
2. Is coverage admission by proxy (calibration on development fixtures) adequate for the confirmatory claims? What should the paper say about it that it does not?
3. Are the two deviations handled adequately? Is the decision-stability re-evaluation convincing?
4. Is the attack evaluation strong enough for the robustness claims (search budget, doubling checks, search-flagged cells, H4's independence)? Read `h4/containment.md`: does it change how H4's results should be stated?
5. Which attack or analysis would a skeptical referee try first that the paper does not cover?

## Task 3: Contribution and positioning

1. What is the paper's real contribution, in two sentences, given that R3 is not materially better than a verified-history comparator?
2. Is the related work adequate? Name missing work. Every citation must be real and verifiable (DOI or stable URL); if you cannot verify one, say so.
3. Does the negative and mixed evidence (Q1 equivalence, Q4 at 3 of 6, 8 failed predictions) strengthen or weaken the paper, and how should the framing use it?

## Task 4: Publication chance

1. Your score for the paper as it is, at (a) AAMAS main track, (b) a strong workshop or specialist venue of your choice (name it), (c) EC or another top venue of your choice (name it), each with confidence.
2. The probability of acceptance at each, as it is and after your recommended text-only changes.
3. The venues ranked for this paper, with each next deadline after November 2026. Verify the dates and give the source.

## Rigor rules

- Every citation you give must be real and verifiable; give a DOI or stable URL.
- Separate what the sources say from your own reasoning.
- Quote the paper's exact sentence when you criticise it.
- For every probability, say what would change it. Do not give a range wider than 30 percentage points without saying why.

## Output format

1. Summary verdict (one paragraph): your recommendation, scores, and the single most important change.
2. Task 1: the list of sentence corrections, ranked by severity.
3. Task 2: answers to items 1 to 5.
4. Task 3: answers to items 1 to 3.
5. Task 4: the score and probability table, then the venue ranking with sources.
6. The changes that would most improve the paper, ranked, each labelled **text only**, **analysis on existing records**, or **needs compute** (with a cost estimate in USD).
