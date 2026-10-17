POSITION: The locked claim is possible but poorly supported; register a narrower H3 comparison before implementation or tuning, and retain the original verdict.

## Q1. Is the locked claim winnable as it stands?

**I would not plan on a PASS. This is not a proof that PASS is impossible.**

The lock admits only H2 as confirmatory. For **each** baseline, the predicate therefore requires either:

- lower 98.75% gain bound ≥ 1.0; or
- lower 98.75% bound on \(L_B-L_{R*}\) ≥ 0.05, where \(L=\mathrm{eff}_{clip}-\mathrm{eff}_{attack}\).

At beta 0.05, I verified these D2 median means:

| Baseline | Gain | Attack efficiency | Inflation loss |
|---|---:|---:|---:|
| B2 | 0.00850 | 0.96926 | 0.00016 |
| B3 | 0.03970 | 0.99470 | −0.00095 |

If R* has approximately zero inflation loss, H2 must produce **more than five points of baseline loss**, with enough margin for the confidence bound. That requires about a five-point increase over the observed D2 losses for both baselines. The gain alternative requires a large increase: 1.0 exceeds the largest development cell mean, 0.84625, observed for B2 without audits.

Four qualifications correct the lead’s reading:

1. Section 6.1 requires H2 to declare its relation to D2; it does **not** require containment. I could not verify containment without opening sealed material.
2. B2’s development headline is **high**, not median. Its high-position D2 gain is −0.00671 and loss −0.00102. Positions are selected separately for each rule.
3. Loss can be negative. The predicate could pass through sufficiently negative R* loss, without five points of positive baseline loss. Such a result needs careful interpretation.
4. D2 results do not bound H2. Additional memory or observations can expose attacks that D2 misses.

The lead’s practical concern is sound. The random-audit kill criterion remains a credible outcome.

## Q2. Which disclosed amendment is defensible?

| Option | Credibility cost | Sealed bundle’s role and registration status |
|---|---|---|
| **(a) Keep the lock** | Lowest. Accept a likely negative result. | Bundle retains its original confirmatory role; registration is unchanged. |
| **(b) Change beta** | Changes the resource question after seeing baseline curves. Baselines were tuned at 0.05. | H2 remains unseen, but the new budget needs disclosed tuning and coverage decisions. This is an amended registration. |
| **(c) Recalibrate thresholds** | Supported by section 8’s stated intent, but near-zero B2 leakage leaves little meaningful superiority margin. Lowering thresholds enough to pass can weaken the scientific claim. | Bundle remains an unseen-family test. Exact thresholds and their calibration rule must be registered before design; retain the original thresholds and verdict. |
| **(d) Admit H3** | Changes the claim from unseen-family generalization to performance on a known family. Existing H3 results informed this choice. | Fresh seeds can confirm performance on H3, but cannot make its family held out. H2 remains the independent transfer test. This is an amended registration. |
| **(e) Separate the claims** | Explicitly narrows the original objective, without making small baseline leakage count as a large failure. | Preserve H2’s unseen status and distinguish it from H3 validation. Register the new predicate prospectively. |

**Correction:** option (b)’s example uses beta **0.01**. At 0.02, B2 median gain is −0.00026 and loss 0.01787, not 0.087 and 0.027.

**Recommendation: (e).** Retain the H2 absolute requirements: efficiency ≥ 0.90, gain ≤ 0.30, and the budget cap. Replace the required baseline-failure clause with a separate H3 comparison:

- R* satisfies those same absolute requirements on H3.
- Against each baseline, the lower 98.75% bound of paired **gain reduction** is ≥ 0.10.

This tests an improvement where the registered data show a substantial weakness: H3 gains are 0.58117 and 0.35721.

Validate the added gain-difference interval on development data before design work proceeds. The existing coverage report does not validate this new endpoint. Preserve the original lock, publish its eventual verdict, and issue a new signed tag, amendment note, and public timestamp. Keep the sealed bundle unchanged. This remains a **disclosed amended pre-registration**, not the original registration fulfilled.

## Q3. Candidate designs for R*

I rank two simple designs. Neither has a credible mechanism for producing the original five-point D2 separation.

### 1. Second-score allocation with newest-identity audits

**Allocate and price:** reproduce B3’s sequential allocation and second-score payment. Use active offers with remaining capacity and nonnegative scores.

**Audit:** retain B2/B3’s spread count and budget caps. Order served jobs by the provider’s first-observed round, newest first. Break equal-age ties with the supplied audit keys. All initial identities have the same age.

The budget permits 2,500 audits: about 12.5 per round. One replacement provider serves at most six jobs. Thus, after replacement, all its jobs can be audited each active round. The rule needs no link to its predecessor.

**Enforce:** full refund for each failed audited job; default tolerance 0.16 and ban 10 rounds. Hold-back: **none**.

**Memory:** first-observed round per identity, plus B3’s current second scores. Identity numbers serve only as opaque dictionary keys.

**Why it can improve H3:** replacement removes the ban but makes the fresh identity the first audit target. A large effort cut then loses receipts on all served jobs. With no replacement, the rule reduces to B3, which already contains D2 gain well.

**Efficiency and honest failures:** allocation retains B3’s strong honest efficiency. At tolerance 0.16, an honest audited job fails with probability 0.000687. Extra audit exposure is concentrated on replacements; allocation imposes no entry restriction.

### 2. Posted prices with newest-identity audits

Use the same audit selection and enforcement. Allocate by B2’s tiers and charge its locked prices: 0.186888, 0.373776, 0.533966. Ignore bids.

Memory contains first-observed rounds; no second-score map is needed. Hold-back remains **none**.

This also removes the gain from escaping bans through replacement. Its weaker allocation and tier boundaries make it second choice. Within-tier effort cuts remain possible.

**Parameters and tuning:** for each design, use:

- tolerance: {0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20};
- ban: {1, 2, 3, 5, 10, 15, 20, 30, 50} rounds.

That is **162 configurations total**, below 243. Keep prices fixed. Use the registered inner search and full-budget recheck procedure; do not add an unlogged H3 tuning objective.

**Expected means at default parameters:**

| Design and family | Gain | Loss | Efficiency |
|---|---:|---:|---:|
| 1, D2 median | 0.040 | −0.001 | 0.995 |
| 1, H3 median | −0.01–0.12 | −0.01–0.02 | 0.97–1.00 |
| 2, D2 median | 0.009 | 0.0002 | 0.969 |
| 2, H3 median | −0.01–0.15 | −0.01–0.03 | 0.94–0.98 |

The D2 entries follow from equality with the baselines when no identities change. H3 ranges are **untested estimates**: replacement should become unattractive, but small inflation and the no-exit strategy remain available.

Both designs fit the vocabulary: baseline allocation/payment, active-capacity eligibility, “newest identities first,” numeric tolerance and ban, full refund, and no hold-back. Implement them within `proposed.py`, using absolute imports from the permitted modules. Importing baseline implementations would violate the module rules.

A bond alone cannot solve first-round replacement attacks: a fresh identity has no prior bond. Arbitrary bond forfeiture, charges on unaudited jobs, or hidden entity linkage would violate section 4.0.

## Q4. Five cheapest falsification tests

For design 1, run these in order:

1. **Interface and description fixtures.** Check module imports, mutation restrictions, identity relabeling, budget exhaustion, refunds, and terminal settlement. Any violation kills the implementation. Any mismatch between rendered description and behavior kills its description.

2. **All-honest runs, five training seeds then twenty validation seeds.** Measure gross efficiency, audited-job failure rate, and lost capacity. Kill the efficiency claim if its upper 95% bound is below 0.90. Investigate failure rates outside the corresponding binomial interval.

3. **H3 attack replay, median position.** Transfer the registered B2/B3 H3 attacks, their projections, and exact corners onto R*. Confirm that a sole newest provider receives full audit coverage when the round allowance is at least six. Failure of that coverage kills the proposed mechanism; gain reliably above 0.30 kills containment.

4. **D2 equality check, all three positions.** At tolerance 0.16 and ban 10, compare trajectories with B3 on five training seeds. Any difference without replacement indicates an implementation error. Then check the selected configuration on twenty validation seeds; worse gain and efficiency than B3 defeats the claimed trade-off.

5. **Full H3 search and bank transfer.** Search attack and twin, select the reference last, and evaluate on twenty validation seeds. Kill the proposed H3 advantage if the upper 98.75% bound on gain reduction is below 0.10 against either baseline. Apply the registered doubling check.

Main exploitation risks are small inflation below tolerance, bid manipulation, late-episode cheating, and choosing no exit. A capable actor can alternate truthful and inflated behavior or change effort after building history. D2 cannot test all such behavior. Newest-first auditing also depends on the registered single-focal setting; several simultaneous entrants can exceed audit capacity.

## EVIDENCE

Read the specified design sections, README kill criteria, `locked.yaml`, and all three tuned files. Recomputed means from all four sweep CSVs; checked `headline.json` and `all_deviators.json`. Inspected mechanism sources, family definitions, ledger checks, vocabulary/renderer, claim checker, and freeze rules.

## ASSUMPTIONS

I did not inspect sealed content, final seeds, custodian communications, or independent timestamp verification. No proposed rule was implemented or run.

## CONFIDENCE

0.88: the predicate assessment is strong; H3 performance estimates need search tests.

## FAILURE MODES

H2 exposes much larger baseline weaknesses; newcomer auditing admits an unforeseen profitable policy; tuning selects harmful false-ban rates; or the amended endpoint fails coverage validation.
