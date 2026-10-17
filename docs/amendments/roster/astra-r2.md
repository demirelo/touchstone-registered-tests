POSITION: Retain amendment (e), use a smaller grid with an explicit H3 objective, validate the new endpoint separately, and withdraw any claim that newcomer audits eliminate cheating.

## C1. Tuning grid

**Choose the 3 × 3 grid for each of the two designs: 18 configurations total.** My round-1 count of 162 meant **two designs × 81**, not 9 × 9 alone.

The registered D2 objective rewards efficiency once gain is small. It does not directly select for H3 improvement. Current H3 mean gains are **0.581168 for B2 and 0.357215 for B3**; a 0.10 improvement requires R* gain below approximately **0.257215**, before confidence-bound allowance. These are recomputed from [h3.csv](/Users/oemer.demirel/Projects/touchstone/results/sweep/h3.csv).

Honesty does **not logically require** tuning against every evaluation endpoint. A disclosed D2-only selection followed by an H3 test is valid. But I now recommend explicit H3 tuning because H3 motivates this design.

Register, before implementation:

- Grid: tol ∈ {0.12, 0.14, 0.16}, L ∈ {3, 10, 20}; both allocation designs; fixed audit schedule.
- For each configuration, run the registered inner procedure separately on D2 and D2+H3.
- Maximize  
  \( \min\{m_{D2},m_{H3},\min_B[(g_B-g_{R*}-0.10)/0.10]\} \),  
  where \(m_F=\min\{(eff_F-0.90)/0.90,(0.30-g_F)/0.30\}\).
- Recheck the top three configurations overall on both families.

This costs **36 inner-search units**, not 18. Current accounting gives **22,572 inner episodes plus 90,630 recheck episodes**, before additional controls. See [schedule.py:84–92](/Users/oemer.demirel/Projects/touchstone/sim/schedule.py:84). Both broad grids with both objectives would consume **324 inner-search units**, exceeding 243.

The amendment must disclose that baseline parameters remain selected under the original objective. Do not call this an unchanged tuning protocol. Section [4.2:258–264](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md:258) requires that distinction.

## C2. Validation of the amended endpoint

**Choose (ii), with an endpoint-only extension at n = 40.** Existing admission does not transfer. A difference of correlated gains can have different skewness and tail behaviour. Studentization gives no finite-sample, distribution-free guarantee.

Use **B3 as the R* stand-in and B2 as comparator**, following the original baseline-pair precedent. Retain all six registered cells, including their families and positions. Use each rule’s separately selected truthful reference:

\[
X_s=\frac{\pi_{B2,a,s}-\pi_{B2,r,s}-\pi_{B3,a,s}+\pi_{B3,r,s}}{S_s^*/N}.
\]

Current code stores only the focal rule’s reference candidate; the other rule contributes attack and clipped-attack trajectories. Therefore extend the observation schema and provenance hashes. A clipped attack cannot substitute for the selected reference. See [coverage.py:99–149](/Users/oemer.demirel/Projects/touchstone/sim/coverage.py:99).

Validate **both lower and upper 98.75% bounds**, since FAIL uses the opposite side. Register a separate 12-endpoint extension gate: six cells × two sides, with the same conservative scoring, fixture, power requirements, and remedies. Preserve original admissions.

With four trajectories per seed:

**6 × (35,000 + 4,000 × 40) × 4 = 4,680,000 episodes.**

No n = 10/20 rerun is needed if this restriction is registered. Existing cached statistics cannot reconstruct the new paired observations.

Plan **4–6 hours on six 16-vCPU pods**, or roughly **30–40 hours on eight comparable workers**, plus setup and validation. These are estimates: the previous n40 run took **4h53m** for its slowest cell ([log](/Users/oemer.demirel/Projects/touchstone/results/pods/logs40/wz3b3f8i9vigce/cov_remote.log:1)). Doubling remedies can double episode cost. Failed admission means exploratory/INCONCLUSIVE, not automatic approval.

This remains development-distribution proxy validation, not guaranteed coverage under R* on H3.

## C3. Audit selection

The H3 exit wrapper is actually in [identity.py:17–33](/Users/oemer.demirel/Projects/touchstone/sim/policies/identity.py:17): it replaces an identity after a failed audit; its binary exit knob also permits no exit.

| Schedule | Repeated replacement | Simultaneous entrants | Honest late entrant |
|---|---|---|---|
| **(a) Newest-first** | Each replacement returns to highest priority. | Random ties share scarce audits; full coverage is no longer assured. | Remains a priority target until newer identities appear. |
| **(b) Fewest audits/served jobs** | Fresh identities start at zero exposure. Priority falls after audits. | Random ties distribute exposure. | Eventually joins the common exposure rate. |
| **(c) Half targeted, half uniform** | Targeted quota catches replacements; uniform quota covers established identities. | Targeted coverage falls as entrants multiply. | Extra exposure remains, but cannot consume the whole budget. |

For (b), define zero-history ratios explicitly and update counts after each selected audit. Otherwise one identity can consume a batch. Its weakness is predictable exposure balancing: an attacker can behave honestly while under-audited, then cheat when its ratio is high.

**I prefer (c), with newest-first targeting, random ties, and uniform selection without replacement from remaining jobs.** With 12–13 audits, six targeted slots cover one six-job entrant. Two entrants remove that guarantee.

For an H2-type attacker, the uniform component provides the strongest protection against predictable exclusion among these choices. This is a design judgement, not a measured ranking. Under simultaneous initial entry and no replacement, newest-first ties are uniform anyway.

**Agree:** first-observed time must never reset when the *same identity* returns from a ban. A replacement identity gets a new time. Carrying its predecessor’s time across replacement would require forbidden entity linkage ([spec:165–169](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md:165)).

## C4. Late-episode cheating

The premise needs correction: bans have **reduced**, not zero, effect throughout the last L rounds. Their future effect is zero at T.

A concrete budget-neutral repair is to reserve enough audits to inspect every served job in the last L rounds. With **2,500 audits, T = 200, J = 50**, earlier coverage becomes:

| L | Terminal reserve | Earlier audits/round | Earlier coverage |
|---:|---:|---:|---:|
| 3 | 150 | 11.93 | 23.86% |
| 10 | 500 | 10.53 | 21.05% |
| 20 | 1,000 | 8.33 | 16.67% |

Against 25% spread coverage, L = 10 costs **375 earlier audits**, a **15.79% reduction**. Use cumulative integer quotas and retain unused capacity. This fits section 4.0’s total budget; the baseline’s per-round cap is not a class constraint.

However, **this does not remove every cheating incentive**. Positive tolerance permits small effort reductions with little change in failure probability. Full terminal auditing removes unaudited terminal jobs, not this incentive.

A bond also supplies no universal cure: forfeiture is capped, fresh identities lack accumulated bonds, and unclaimed funds return at T ([ledger.py:54–87](/Users/oemer.demirel/Projects/touchstone/sim/ledger.py:54)). Thus register back-loading as a falsifiable repair, not a guarantee. It also weakens newcomer targeting earlier; my six-slot assurance no longer holds there.

## C5. Negative-loss route

**It is a legitimate PASS under the original formula, but insufficient evidence that a baseline fails.** For example, baseline loss 0 and R* loss −0.06 produce a 0.06 difference. Negative loss can reflect real allocation effects; it is not necessarily numerical error.

The amendment should close this interpretation gap through the **paired gain-reduction clause already proposed**. Do not add an arbitrary −0.01 floor and silently introduce another unvalidated endpoint. Preserve and explain any original PASS driven by negative R* loss. The original algebra is explicit at [spec:855–864](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md:855).

## C6. Lead statements

1. **Confirm as the amendment’s prospective boundary.** Register before proposed-rule implementation or tuning. Disclose both rounds’ memos: design reasoning already exists, so “before any design” would be false.
2. **Confirm.** Report the original predicate’s verdict alongside the amended verdict.
3. **Confirm.** H2 remains the sole confirmatory held-out-family test, including its budget requirement. H1 remains exploratory. H3 is a known-family test on fresh seeds, never a held-out family ([locked.yaml:104](/Users/oemer.demirel/Projects/touchstone/experiments/locked.yaml:104); [spec:608–613](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/specs/2026-10-14-touchstone-simulator-design.md:608)).

## CHANGED

Smaller grid; explicit H3 tuning; mixed audits preferred; quantified coverage extension; withdrawal of complete deterrence and unchanged-trajectory claims.

## UNRESOLVED

New endpoint admission, actual H3 improvement, and the cost of back-loading remain untested. The sealed bundle and other seat’s text stayed unread.

## CONFIDENCE

**0.88** on protocol and accounting; lower on untested mechanism performance.
