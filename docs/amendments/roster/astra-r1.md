POSITION: The locked claim remains possible, but current evidence gives it a poor prospect; disclose a change of research question before implementation or tuning.

## Q1. Is the locked claim winnable?

**Not demonstrably impossible, but not supported by the development results.** The absolute rule requirements look achievable. The baseline clause is the obstacle.

I reproduced the reported means. At beta 0.05, D2 median gives:

| Rule | Gain | Gross efficiency | Inflation loss |
|---|---:|---:|---:|
| B2 | 0.00850 | 0.96926 | 0.00016 |
| B3 | 0.03970 | 0.99470 | −0.00095 |

With H1 exploratory, each baseline must satisfy an alternative through H2. If R* has approximately zero inflation loss, H2 must produce **more than 0.05 baseline loss**, with enough margin for the lower 98.75% bound to clear 0.05. Alternatively, its baseline gain must clear 1.0 on that bound. The largest observed **cell mean** is 0.84625, without audits; this is evidence about scale, not an upper bound.

Corrections to the lead’s reading:

- Section 6.1 permits H2 to contain D2, be contained by D2, or be non-nested. **Containment is not established by the public specification.**
- B2’s registered D2 headline is **high**, not median: gain −0.00671, loss −0.00102. B3’s headline is median.
- The loss alternative can pass through **negative R* loss**, even if baseline loss remains near zero. With these headline means, R* would need loss around −0.051, plus statistical margin. That would not establish that H2 substantially damages the baselines.
- H2 search maximizes profit, not efficiency loss. More policy freedom does not imply more loss. Nor must measured gain rise when both attack and reference improve.

Thus “unlikely” is justified; “can pass only through a newly severe baseline attack” is too strong. Random-audit dominance remains a live kill outcome.

## Q2. Which amendment is defensible?

| Option | Scientific cost and sealed-bundle role |
|---|---|
| **(a) Keep the lock** | Lowest credibility cost. H2 retains its original role. Accept FAIL or INCONCLUSIVE as useful results. |
| **(b) Change beta** | Selects a setting after seeing its curve. H2 remains held out, but the budget, tuning objective, and coverage justification need review. The example is incorrect: **0.087 gain/0.027 loss occurs at beta 0.01**. At 0.02, B2 has −0.00026/0.01787; B3 loss is −0.00237. This does not resolve the obstacle. |
| **(c) Recalibrate thresholds** | Section 8 explicitly anticipated baseline-informed thresholds, which supports a disclosed correction. However, both baseline losses are near zero. Lowering baseline_gain_min below R*’s 0.30 ceiling could let a worse R* pass. H2 remains held out, but the comparison may become scientifically weak. |
| **(d) Admit H3** | Changes family generalization into testing a known attack on unseen seeds. That can be pre-registered, but H3 must never be called held out. Alone it does not repair the predicate: B3 H3 gain is 0.35721 and loss only 0.01507. |
| **(e) Separate the questions** | Largest explicit scope change, but the clearest scientific target. Preserve H2 as the test of performance against an unseen family; test comparative improvement against public H3 separately. |

**Recommend (e)** if a revised positive claim is required:

- Retain beta 0.05 and the absolute efficiency/gain requirements for H2.
- Add the same absolute requirements for H3.
- Require paired lower 98.75% bounds on **gain(B,H3) − gain(R*,H3) ≥ 0.10**, separately for B2 and B3.
- Publish the original predicate’s result separately.

A 0.10 reduction is material: one tenth of an average provider’s first-best share. B3’s observed H3 gain implies R* would need approximately ≤0.257 before uncertainty.

This requires a new signed tag, public timestamp, amendment rationale, exact search/position rules, and coverage checks for the **new paired-gain statistic**. Keep the sealed bundle unchanged and unopened. Its H2 component tests absolute generalization, not comparative superiority.

This is an **amended pre-registration**, not the original registration. Disclose this memo too: it contains design ideas. Do not later claim the amendment preceded all rule design. Freeze it before implementation or tuning.

## Q3. Ranked candidate designs

Neither design has a credible mechanism for guaranteeing five points of superiority over both baselines on D2-like H2. Their main opportunity is H3. The ranges below are **untested forecasts**, not confidence intervals.

### 1. Second-score auction with newest-identity audits

**Allocate and price:** Use B3’s descending-value, sequential second-score allocation and payment exactly.

**Audit:** Use B2’s integer spread schedule and budget cap. Select served jobs from identities with the latest **first observed offer round**, then use supplied random audit keys for ties. Record first appearance once; a return after a ban does not reset it. Do not sort by identity number.

**Enforce:** Full refund of each failed audited job; ban for L rounds. **No hold-back or forfeit.**

**Memory:** First-observed round per opaque identity, current second scores, and budget-schedule constants.

**Grid:** tolerance {0.12, 0.14, 0.16} × L {3, 10, 20}: **9 configurations**. Initial candidate: 0.14 and 10. Use the registered inner search and top-three full recheck; do not spend unused configurations on undocumented redesigns.

**Mechanism:** There are about 12.5 audits per round and at most six jobs per provider. After one focal replacement, all six newcomer jobs can be audited, leaving about 6.5 audits for others. A full-cheat newcomer then loses all job payments. Repeated identity replacement no longer restores unaudited receipts.

With no replacement and simultaneous initial entry, audit selection reduces to uniform random selection. Improvement over B3 then depends on tolerance and ban tuning, not novelty targeting. B3 allocation should preserve high efficiency; it should also outperform B2’s tier allocation on efficiency.

Honest per-audit failure probabilities are 0.82%, 0.256%, and 0.069% across the tolerance grid. False bans, rather than refund transfers, are the main efficiency risk.

**Forecast for viable configurations:**

| Family | Gain | Inflation loss | Gross efficiency |
|---|---:|---:|---:|
| D2-like | 0–0.05 | −0.01–0.01 | 0.97–0.995 |
| H3 | 0.05–0.20 | 0–0.025 | 0.965–0.995 |

### 2. Posted tiers with newest-identity audits

**Allocate and price:** Use B2’s tier allocation and posted payments. Bids are ignored.

**Audit, enforcement, memory:** Same newest-first schedule, refunds, and bans as design 1; store tier quotes instead of second scores. **No hold-back.**

**Grid:** The registered 27 price triples × tolerance {0.12, 0.14, 0.16} × L {3, 10, 20}: **243 configurations**. The existing B2 prices provide the initial candidate.

**Mechanism:** Newcomer auditing removes H3’s ban bypass. Fixed tier payments also remove continuous payment increases from small claim increases within a tier. Crossing a tier boundary remains an attack opportunity.

It may improve gain relative to B3, but B2’s current D2 gain is already near zero. Tier allocation retains B2’s efficiency disadvantage.

**Forecast:** D2-like gain 0–0.03, loss −0.01–0.01, efficiency 0.94–0.975; H3 gain 0.02–0.20, loss 0–0.04, efficiency 0.93–0.975.

**Implementation constraints for both:** Select one architecture before tuning; these are alternative budgets. Reimplement required baseline logic inside `proposed.py`: importing baseline modules is prohibited. Use absolute allowed imports, `view.memory` for policy state, and returned `Consequences` for enforcement. Use no global RNG or entity linkage.

Both descriptions fit the locked vocabulary: existing allocation/payment wording, “newest identities first,” numerical tolerance/ban length, full refund, and no hold-back. Verify the rendered description against behavior.

I would defer bonds. They cannot penalize a fresh identity before receipts accumulate, and exit alone cannot justify confiscation. Their release and capped-forfeit schedules also create description and accounting risks.

## Q4. Five cheapest falsification tests

1. **Boundary and description fixtures.** Relabel identities; permute offer order; test budget exhaustion and terminal settlement. Kill on changed economic decisions under relabeling, overspend, an unlawful refund, prohibited import/mutation, or a misleading description.

2. **H3 full-cheat corner, median, beta 0.05.** Inspect the first replacement and subsequent audit exposure. Kill the central mechanism if a sole newest provider with six served jobs is not fully audited when allowance permits, or sustained full cheating remains profitable after replacement.

3. **All-honest, beta 0.05, 20 development seeds.** Measure efficiency, false bans, and lost capacity. Reject configurations below 0.90 mean efficiency; reject the efficiency forecast below 0.97. Check observed audit failures against the stated Gaussian probabilities.

4. **D2, all three positions.** Start with baseline bank attacks, truthful projections, and tolerance-adjacent effort cuts. Reject configurations with gain above 0.30 or efficiency below 0.90. If B3 has no higher gain and no lower efficiency across cells beyond seed noise, reject the claimed comparative advantage.

5. **Full H3 search and reference search.** Include x=0 and x=1, then clip-fixed doubling and bank transfer. Reject the forecast if gain exceeds 0.20; reject the revised target if either paired gain improvement cannot support 0.10. Recompute references last.

Search or an LLM actor can exploit small inflation below tolerance, bid manipulation, first-identity opportunities, predictable audit priority, and late-episode cheating. Older identities can receive fewer audits after entry. Multiple simultaneous entrants can overwhelm newest-first auditing; the public single-focal H3 test does not establish resistance to that case.

**EVIDENCE:** Specification §§3–8; README kill criteria; `experiments/locked.yaml`; all three tuned JSONs; the four sweep CSVs; `headline.json`; `all_deviators.json`; mechanism, family, ledger, description, vocabulary, and claim-check code; runbook “Freeze day.” All-deviator gains also show no broad baseline failure.

**ASSUMPTIONS:** H2’s nesting, sealed contents, signature validity, public timestamp, and access history remain unverified. No proposed rule was implemented or run.

**CONFIDENCE:** 0.85 on the predicate assessment; substantially lower on the untested numerical forecasts.

**FAILURE MODES:** H2 finds a major unseen baseline weakness; search misses profitable attacks; newcomer priority harms honest entry; or the apparent H3 improvement depends on its single-replacing-provider structure.
