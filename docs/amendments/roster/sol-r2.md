POSITION: Keep amendment (e); use the smaller grid, register H3-aware selection, validate the new endpoint, and qualify the audit and terminal-round claims.

## C1. Tuning grid

**Choose nine configurations for the first-ranked, second-score design:** tol ∈ {0.12, 0.14, 0.16}, L ∈ {3, 10, 20}. Fix the allocation design before tuning.

Correction: 9 tolerances × 9 bans is **81**, not 162. My round-1 total included two allocation designs. The 243 allowance is a ceiling; it does not require spending it. The implemented baseline grids contain 27, 243, and 9 points respectively. [Spec, lines 247–264](docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md#L247); [tuning.py, lines 32–42](sim/tuning.py#L32).

The original D2 objective cannot assess resistance to replacement. The observed median gains illustrate the gap:

| Rule | D2 gain | H3 gain |
|---|---:|---:|
| B2 | 0.00850 | 0.58117 |
| B3 | 0.03970 | 0.35721 |

These are means over 20 validation seeds in [development.csv](results/sweep/development.csv) and [h3.csv](results/sweep/h3.csv).

An honest registration need not optimize every claim endpoint. **However, I now recommend including H3**, because it is the amended comparative target. Register this explicit replacement for section 4.2:

\[
M=\min\left\{
m_{D2},
\frac{e_{H3}-.90}{.90},
\frac{.30-g_{H3}}{.30},
\min_{B2,B3}\frac{g_{B,H3}-g_{R,H3}-.10}{.10}
\right\}.
\]

Use median-position D2 and D2+H3, beta 0.05, the same reduced search separately for each family, reference selection last, and a fixed tie-break. Nine parameter points therefore cost **18 inner searches**, followed by full rechecks of the top three points on both families. Register seeds, baseline inputs, all extra evaluations, and selection on dev-val. Keep the baselines fixed, but disclose that their tuning objective differed. Do not claim unchanged section-4.2 tuning.

## C2. Validation of the amended endpoint

**Choose (ii). Admission does not transfer.** Separate gain bounds do not establish coverage for their paired difference; its variance and tails depend on covariance. The code admits named endpoints, and `gain_diff` is absent. [coverage.py, lines 21–25](sim/coverage.py#L21); [claimcheck.py, lines 47–67](sim/claimcheck.py#L47).

The cheapest defensible new study starts directly at **studentized n = 40**:

- Keep the six registered development contexts.
- Use **B3 as R* stand-in against B2**, with the reverse sign for the reverse comparison.
- For each rule, use its own frozen attack and selected truthful reference. Compute  
  \[
  X_s=[(\pi_{B2}-\pi_{\mathrm{ref},B2})-(\pi_{B3}-\pi_{\mathrm{ref},B3})]/(S_s^*/N).
  \]
- Validate both lower and upper 98.75% sides, since FAIL uses the opposite side.
- Register a separate endpoint gate, its fixture/power checks, remedies, hashes, and INCONCLUSIVE outcome before execution. Preserve the old admission report.

This is development-distribution **proxy admission**, not guaranteed coverage on H3.

With M = 35,000, R = 4,000 and four trajectories per seed:

\[
6(35{,}000+4{,}000\times40)\times4
=\mathbf{4{,}680{,}000\ episodes}.
\]

Abstention references and exact cache reuse can reduce this ceiling. There is no need to repeat n = 10/20. The settings are in [locked.yaml, lines 9–14](experiments/locked.yaml#L9).

Allow **one working day on six 16-vCPU pods**, as an estimate. The earlier n40 extension launched around 15:49 and merged at 20:44 on that fleet. Resampling and setup cost matter; episode timing alone understates calendar time. [Launch log](results/pods/launch40.log); [completion log, lines 68–73](results/pods/cov_watch40.log#L68).

## C3. Audit selection

H3 exits **after a failed audit**, not on an arbitrary timer. Its policy memory persists. The wrapper is in [identity.py, lines 8–33](sim/policies/identity.py#L8), while [families.py, lines 105–107](sim/policies/families.py#L105) defines D2.

| Schedule | Repeated replacement | Several entrants | Honest late entrant |
|---|---|---|---|
| **(a) Newest-first** | Each fresh identity becomes the main target. | Entrants share scarce capacity; randomize ties. | Can receive full audits indefinitely until someone newer appears. |
| **(b) Fewest audits/served job** | Fresh identity starts at zero; priority falls as coverage catches up. | Shares audits according to accumulated coverage deficits. | Receives catch-up audits, then ordinary exposure. |
| **(c) Half newest-first, half uniform** | Retains entry pressure and background checks. | Targeted half can be overloaded. | Entry burden remains, but uses only half the budget. |
| **(d) Half coverage-deficit, half uniform** | Fresh identities receive catch-up checks without permanent age priority. | Spread target slots across tied providers. | Catch-up ends after its coverage approaches others’. |

**Choose (d).** Define zero-history ratios explicitly and use random tie-breaks from allowed audit keys. At roughly 12–13 audits per round, six targeted slots can cover one six-job entrant; three entrants cannot all receive full coverage. An H2-type attacker can exploit accumulated audit credit under (b), or old age under (a). The uniform half gives (d) continuing exposure, approximately a 12.5% background audit fraction. This is a design argument, not a measured H2 ranking.

**Agree that first-observed time must persist for the same identity after a ban.** Otherwise a ban return changes audit priority without replacement. A genuinely fresh identity gets a new time; carrying its predecessor’s age requires an unavailable entity link. [market.py, lines 94–105](sim/market.py#L94); [spec, lines 165–169](docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md#L165).

## C4. Late-episode cheating

The premise needs correction: bans have **less** bite during the final L rounds, and zero future bite at T.

A concrete mitigation is to reserve **500 audits for the final ten rounds**, enough to audit all 50 jobs per round. Spend the remaining 2,000 over the preceding 190 rounds. Section 4.0 permits this; the baseline’s per-round cap of 25 is not a class-wide restriction.

Earlier coverage falls from 25% to **21.05%**: 375 fewer audits than the uniform schedule, a **15.8% reduction** in earlier audit counts. This removes the terminal *unaudited-job* route.

**It does not remove every cheating incentive.** At tol 0.16, even full auditing permits profitable small effort cuts. For fixed offers, the marginal detection probability is:

\[
\phi(3.2)/0.05=0.04768.
\]

Even maximum refund plus forfeit gives marginal expected sanction at most \(2P(0.04768)\). Since \(P\le1.4\), this is at most **0.1335**, below every provider’s effort-cost slope, **0.22–0.40**. Thus a small terminal effort cut can pay. [Locked costs](experiments/locked.yaml#L24); [enforcement caps](docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md#L176).

A hold-back released at T does not itself solve this; forfeiture still requires failed audits and has a per-job cap. [ledger.py, lines 81–87](sim/ledger.py#L81). I withdraw any claim of complete end-game deterrence at the proposed default.

## C5. Negative-loss route

**It is a valid PASS under the original formula, but an interpretation defect for “baseline failure.”** A baseline loss of zero and R* loss of −0.06 can satisfy the five-point difference without positive baseline loss. The formula explicitly allows this. [Spec, lines 860–864](docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md#L860).

Close the route in the amendment by **replacing the loss alternative with paired H3 gain reduction**, as amendment (e) proposes. Report both signed losses as diagnostics. Keep the original predicate unchanged for its separate verdict; do not retrofit a −0.01 guard into it.

## C6. Lead statements

1. **Confirm.** Register before proposed-rule code exists; disclose both memos as evidence that informed the amendment. Include objective, coverage protocol and checker changes in a new signed, timestamped amendment. The original lock excludes unlisted pipeline edits. [Spec, lines 532–570](docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md#L532).
2. **Confirm.** Report the original PASS/FAIL/INCONCLUSIVE verdict alongside the amended verdict.
3. **Confirm, including the per-seed budget cap.** H2 remains the sole confirmatory held-out-family test; H1 remains exploratory. H3 is a known-family test on fresh seeds, never a held-out family. [Coverage verdict](results/coverage/merge40.log#L2); [required families](sim/claimcheck.py#L105).

## CHANGED

I replace the broad grid with nine points, explicitly add H3 to selection, prefer mixed deficit audits, and reject complete terminal deterrence. These changes address objective mismatch, predictable audit gaps, and bounded terminal sanctions.

## UNRESOLVED

New-endpoint admission, actual H3 improvement, and H2 exploitation remain untested. The sealed bundle remains unread.

## CONFIDENCE

**0.90** on the protocol and arithmetic; **0.65** on the audit-design ranking before tests.
