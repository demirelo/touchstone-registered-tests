# Brief: the proposed Touchstone rule, after the lock (round 1, independent position)

You are one seat of a two-seat roster (Sol high, Astra high). Work alone from this brief and the repository; you do not see the other seat. Reasoning effort: high. Reply in the exact format at the end. Read-only sandbox: inspect files and run short read-only Python if useful (pandas is installed in .venv; use `.venv/bin/python`).

## Objective
Advise the author on (A) whether the locked claim is winnable and whether a disclosed pre-registration amendment is warranted before any rule design starts, and (B) the design of the proposed rule R* inside the admissible class, with concrete mechanisms, parameters, and the tests that would falsify each design claim.

## Inputs to read (in this order)
1. docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md: sections 3 (market), 4 and 4.0 (interface, admissible class), 4.1 and 4.2 (baselines, tuning), 5.2 and 5.3 (twins, families D1/D2, search), 6.1 and 6.2 (held-out families; H3 identity replacement is public and may be designed against), 7 (metrics), 8 (claim predicate and decision rule), and the kill criteria in README.md.
2. experiments/locked.yaml: the lock of 2026-10-17 (signed tag lock-2026-10-17). The `claim` block is locked: beta 0.05, eff_min 0.90, gain_max 0.30, loss_diff_min 0.05, baseline_gain_min 1.0. `coverage_consequences`: final_eval_n 40, H1 exploratory, parametrized bound studentized bootstrap at n = 40.
3. experiments/tuned/tuned_B{1,2,3}.json: the locked baseline parameters (B2: P1 0.187, P2 0.374, P3 0.534, tol 0.16, L 10; B3: tol 0.16, L 10; B1: P 0.108/0.216/0.24).
4. results/sweep/development.csv, h3.csv, no_ban.csv, rho_sweep.csv, headline.json, all_deviators.json: the registered sweep (dev-train/dev-val seeds, beta grid, 3 positions). sim/mechanisms/*.py: the baseline implementations and base.py (the frozen interface and State). sim/policies/families.py and experiments/families.md: D1, D2, D2+H3. docs/lock-runbook.md "Freeze day": the import and mutation rules the proposed module must obey (scripts/check_claim.py enforces them).

## Facts the lead has established from the registered results (verify them yourself)
At beta = 0.05 (the claim budget; audited fraction of served jobs 0.25), means over 20 dev-val seeds, gain in S*/N units, loss = eff(clip) - eff(attack):

| rule | family | position | gain | eff(attack) | loss | focal bans |
|---|---|---|---|---|---|---|
| B1 | D1/D2 | median | 0.41 | 0.869 | 0.10 | 0 (no audit) |
| B2 | D2 | median | 0.009 | 0.969 | 0.000 | 0.2 |
| B2 | D2 | low | -0.012 | 0.937 | -0.007 | 0.8 |
| B3 | D2 | median | 0.040 | 0.995 | -0.001 | 6.6 |
| B3 | D2 | high | 0.018 | 0.994 | -0.010 | 1.0 |

By budget, B2 at D2 median: gain 0.846 at beta 0, 0.087 at 0.01, 0.000 at 0.02, 0.009 at 0.05; loss 0.104, 0.027, 0.018, 0.000. B3: gain 0.598, 0.099, 0.065, 0.040.
H3 (identity replacement, D2 + exit knob, beta 0.05, median): B2 gain 0.58, eff 0.868, about 180 identities and 171 bans per episode; B3 gain 0.36, eff 0.974. No-ban diagnostic (L = 0): B2 gain 0.59, B3 0.36. Highest gain seen anywhere, any rule, any budget: 0.85 (B2 at beta 0).

Consequences the lead draws, for you to confirm or refute:
- The baseline clause (section 8) needs, for each of B2 and B3, a confirmatory held-out family F with either lower-98.75% gain(B, F) >= 1.0, or lower-98.75% [eff(B, clip) - eff(B, F)] - [eff(R*, clip) - eff(R*, F)] >= 0.05. H1 is exploratory, so F must be H2. H2 contains D2 and does not exit (section 6.1). Against D2 at beta 0.05, B2 and B3 show gain <= 0.04 and loss <= 0.00. A gain of 1.0 exceeds the largest gain ever observed (0.85, with no audits at all).
- Therefore the baseline clause can pass only if H2 extracts, at 25% audit coverage without identity churn, at least 5 points of inflation loss more from B2 and from B3 than from R*. The lead considers this unlikely; the kill criterion "a plain random-audit rule dominates the proposed rule" is a live outcome.
- The claim thresholds were meant to be "set from the baseline runs at the lock" (section 8, units note) but the lock tooling carried the draft values unchanged. Nothing post-lock has been designed or run; the sealed bundle is unopened; the custodian has not been contacted since. A disclosed amendment (new signed tag, amendment note, public timestamp, with the reason) is possible now and never later.

## Constraints on R*
Section 4.0 in full: inputs limited to offers, values, purchased audit results, own state, locked config; identity ids opaque and relabeling-invariant; consequences only refund (<= escrow), ban (<= 50 rounds), hold-back bond (<= 3 rounds of net released receipts, schedule stated, forfeit <= that job's escrow, booked to the failed jobs' buyers), allocation priority and audit selection; audit spend <= B every seed; operator holds no money at episode end. Module rules of docs/lock-runbook.md "Freeze day". The rule gets the same tuning budget as the baselines (243 configurations, section 4.2) and must publish a describe() record in the controlled vocabulary (experiments/vocabulary.yaml) that an LLM actor can comprehend (sim/describe.py).

## Questions to answer
Q1. Is the locked claim winnable as it stands? Give the quantitative argument, including what H2 would have to achieve, and name any error in the lead's reading of section 8.
Q2. If not, which disclosed amendment is scientifically defensible before any rule design: (a) none, proceed and report; (b) change the claim budget beta (for example 0.02, where B2 leaks 0.087 gain and 0.027 loss); (c) recalibrate baseline_gain_min and loss_diff_min from the baseline runs as section 8 intended; (d) admit H3 into the predicate as a confirmatory family (it is public and the rule may be designed against it); (e) other. For each: what it costs in credibility, what it changes in the sealed bundle's role, and whether it is still a pre-registration. Recommend one.
Q3. Propose two or three candidate designs for R* inside 4.0, ranked. For each: allocate, price, audit selection, enforce (refund, ban, hold-back schedule), the policy memory it keeps, its free parameters and their tuning grid (<= 243 configurations), the mechanism by which it beats B2 and B3 on H3 and on a D2-like H2 at the claim budget, the mechanism by which it keeps gross efficiency >= 0.90 and the honest failure rate low, and its expected numbers (gain, loss, efficiency) with the reasoning. Flag anything that would violate 4.0 or the module rules.
Q4. For the recommended design: the five tests that would falsify its design claims cheapest (which cells, which statistic, what result would kill it), and the risks that the search of section 5.3 or an LLM actor exploits.

## Reply format (markdown; keep it under 1,800 words)
POSITION: <one line>
Q1 ... Q4 as sections with the headings above.
EVIDENCE: files and numbers you relied on.
ASSUMPTIONS: what you could not verify.
CONFIDENCE: 0-1 with one sentence.
FAILURE MODES: what would make this advice wrong.
