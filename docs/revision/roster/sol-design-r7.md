VERDICT: reject

CORRECTIONS:

1. **§§3.4, 14 — Replace “A_tot = 2,500 in every market” with a generator-wide proof.** `sim/instances.py` permits total capacity K from 40 to 80. Validation requires positive first-best surplus, so `n_FB = 200 min(50,K)` and A_tot ranges from 2,000 to 2,500 at rho = 0.2. Thus both reserves equal 500 at L = 10 on **every** permitted market. On the headline repair market at rho = 1, the reserves are 500 and 250, so the rules differ. The duplicate removals are correct, but the stated evidence is false. Apply the corrected assertion to the distinct-rule tests.

2. **§§5.2, 6.3 — Correct X8’s truthful projection.** Preserve `u_D`, bids, and reset parameters; set only the beneficiary’s `clip = 1`. The decoy already claims its effort and is truthful for every `u_D`. Forcing `u_D = 0` changes its effort, costs, allocation, and payoff. This contradicts the simulator’s definition of truthfulness and `Family.project`, which clips claims. It can omit a profitable truthful counterpart and inflate measured coalition gain. This part of D5 makes the design worse.

3. **§§6.3–6.4 — Include the G_min searches’ truthful projections and archives.** Their explicit exclusion is narrower than D5’s accepted repair. A concrete finite order is: G_tot searches; preliminary reference; G_min searches; add truthful projections from both objectives’ archives; freeze the final reference; rescore the archived G_min candidates against it and select the winner; evaluate. This avoids a circular search while preventing positive coalition findings caused by omission of an observed truthful alternative. The G_tot-before-reference order itself is sound because its reference term is constant.

4. **§5.2 — Complete the attack timing rules.** For X8, specify replacement when integer identity age reaches the real threshold `n_D`, with the counter restarted after every replacement. Compute the beneficiary’s gate from the decoy identity that will make the current round’s offer, independently of policy-call order. `sim/market.py` obtains actions before applying exits; “current identity” otherwise permits two implementations. For X7, state explicitly that the voluntary trigger can override a failed age-gated reset decision, and remove “an old identity is not the newest”: §3.3 and Lemma 2b establish that it can remain newest. The D2+H3 embedding remains valid with the stated knob values.

5. **§§5.3, 8.2, 11 — Bound H4’s controls and check its actual runtime before the lock.** Fifteen knobs and 5 × 600 search evaluations do not establish an X7-sized cost. `scripts/revision_v2.py::controls` applies bounded controls only to X7; H4 uses `Family.corners`, allowing 32,768 corners. Register a bounded H4 control procedure, include its twin and control evaluations, and measure the frozen bundle locally before final cost approval and cuts. The revised defence-aware authorship order resolves D2’s main objection; its cost envelope does not.

6. **§§9.2–9.3 — Complete the numerical and efficiency reporting rules.** Explicitly refuse nonfinite bootstrap statistics or bounds and withhold the affected decision; rejecting nonfinite input samples alone does not cover D14. Update the smallest confirmatory tail to `0.05/6`: approximately 83 bootstrap resamples before calibration and 21 at kappa = 1/4. Also distinguish an established efficiency loss from unresolved noninferiority. Failure to obtain a lower bound above −0.01 does not itself establish an “efficiency cost.” The revised gain categories and the selection/validation criterion are otherwise sound.

7. **§14 — Expand the Code column.** D1/D18 also require tuning, promotion, parameter construction, benchmark, and report changes. Evidence: `scripts/promote_v2.py::SYSTEMS` still requires R4-t; coverage promotion requires `fixture_cstar_s2.json`; `scripts/benchmark_v2.py` retains four-system and fourteen-profile assumptions. D2 requires H4 budget dispatch and controls, plus the C* smoke check, beyond the brief and loader. D5 requires coalition objective, reference reconstruction, dependency, and verification changes. D9 requires the added conditional contrasts in `sim/decisions_v2.py`. D14 requires interval handling. D16 requires welfare reporting as well as cross-evaluation.

8. **§§4.2, 14 — Finish D8’s wording repair.** Replace “favours the comparator” with “provides additional development selection; historical adaptation is not equalised.” The qualification in §3.3 should also govern §4.2. D6, D7, D9–D11, D13, and D15–D17 are otherwise resolved in the design. The counts are consistent: **287 search cells, 85 X7 cells, 21 H4 cells, 98 doubling checks, eight Q1 coverage endpoints**, and approximately **38.5 USD** under the stated unit assumptions. H4’s unresolved cost prevents treating that estimate as complete.

ANSWERS:

3. **Yes.** Dropping R4-t is reasonable within the stated scope and budget. At common grid points through L = 20, its pacing equals R3’s throughout the generator’s range. Keep the distinct rho = 1 repair comparisons.

4. **Yes, as bounded attack families, after the timing and reference repairs above.** X7 represents age-dependent reset decisions and credibility/exposure-dependent shading. X8 represents a rotating decoy protecting an established beneficiary. Neither supports unrestricted attack-resistance claims.

5. **The gain categories are well defined.** A descriptive efficiency bound beside a calibrated gain decision is acceptable if the combined “better” statement remains explicitly descriptive. It has no calibrated joint error guarantee.

This was a read-only source-and-diff review. Python checks could not run because `uv run python` could not create a temporary directory in the sandbox. No paid APIs or sealed directories were used.

CONFIDENCE: 0.93