# Round 2: cross-examination (same constraints as round 1: read-only, no paid APIs, sealed unread, reasoning effort high, under 900 words)

Both seats independently recommended option (b1): a fresh-identity priority phase before the registered k_t/k_u split, F2 unchanged, the full 36-point re-tune, one iteration only, stop on any kill. The two clauses differ. Resolve the differences with arguments and counterexamples, not preference; then give your final clause text.

## Difference 1: the freshness window
- Sol: an identity is fresh in round t exactly when 0 <= t - first_round[i] < L (L the rule's ban length, 3/10/20).
- Astra: fresh exactly when first_round[i] == t (the identity's first round only).
Weigh: (i) the H3 family's x = 1 transformation exits in the round after a failed audit, so the replacement cheats from its first round; but D2's adaptive knobs (d, r) can delay or recover, so a replacement may behave for a round or two before cheating; (ii) under the L window, honest newcomers consume priority audits for L rounds; at the corner there are about 199 replacements per episode, so in most rounds the priority set is one entrant with up to 6 jobs; (iii) under either window, what happens at round 0 when all 10 initial identities are fresh (k = 10, 50 served jobs): does the priority phase swallow the whole quota, and is that acceptable; (iv) relabeling invariance and the no-entity-linkage rule; (v) which window the amendment-1 design text ("newest identity first") sits closer to.

## Difference 2: the order inside the priority set
- Sol: descending first_round, then ascending audit_key, then job index.
- Astra: ascending (audit_key, job index) only.
Weigh: when several fresh identities compete for a quota smaller than their jobs, which order is defensible and which is arbitrary.

## Also settle
- Whether the priority selections count as audits_i for T2's ratio before the split (both said yes; confirm or object).
- The exact F1 fixture additions the amendment must register (tests/ is outside the allow-list, so amendment 3 must name every file it permits to change; tests/test_proposed.py, tests/_proposed_fixtures.py; does scripts/falsify_proposed.py need any change? Both said F2 unchanged: confirm the harness needs no edit).
- The stopping rule text: "a kill of the selected configuration ends proposed-rule development" (Astra) vs "any registered kill stops R3; no further design or gate revision" (Sol): the same? If not, which.
- The tuning: full 36-point grid repeated (both). Confirm that tuning on the unchanged grid with the changed selection is the registered procedure and that no prior score may prune it.

## Output
For each difference: your resolution in at most four sentences with the decisive counterexample or argument. Then FINAL CLAUSE: the complete registered text (design replacement, tuning, falsification and stopping, files permitted to change, disclosure sentence). CONFIDENCE 0 to 1.

## The two round-1 memos
=== SOL round 1
**RECOMMENDATION:** **(b1), one bounded Amendment 3:** give identities first seen within the last `L` rounds priority before the remaining quota is split; keep F2 unchanged; permit one development cycle, then stop on any kill.

**RATIONALE:** A disclosed iteration is scientifically acceptable because the sealed bundle remains unread, provided Amendment 2’s kill remains a reported result and Amendment 3 defines one successor before implementation. The arithmetic establishes a coverage defect at the selected `L = 10`; it does not establish that the entire registered design family is impossible. Nonpositive profit is the substantive economic target, while full coverage is a stronger structural safeguard: T1’s −1.44 establishes loss for this corner on these seeds, without establishing resistance to other strategies. T2 shows a separate economic failure—profitable sustained replacement under its audit-ratio policy—so merely removing coverage from F2 would still leave a kill. Option (c) weakens the gate, (b2) removes uniform sampling without ensuring T2 covers newcomers, and (b3) relies on the particular six-job capacity while leaving T2 unresolved. One further cycle is justified by the opportunity to reach a confirmatory evaluation, but its budget must include the final evaluation and prohibit another repair cycle after failure.

**IF AMENDMENT 3 — exact registered clause text**

> **Status and scope.** The Amendment 2 rule is stopped following its F2 kill and shall not be frozen or evaluated as a surviving rule. Amendment 3 registers one successor, R3. All Amendment 2 results remain in the public record. This amendment shall receive a signed tag and timestamp before implementation changes.

> **Design: replacement of `audit_selection.split`.** Let `k` be the round’s audit count after the existing quota, served-jobs, and audits-left caps. An identity is fresh in round `t` exactly when `0 <= t - first_round[i] < L`. Form a list of all served jobs belonging to fresh identities, ordered by descending `first_round[i]`, then ascending `audit_key[j]`, then ascending job index. Select the first `min(k, number of listed jobs)` jobs for audit. Let `q` be the number selected and `r = k - q`. From the remaining served jobs, select `ceil(r/2)` jobs using the registered T1 or T2 procedure, followed by `r - ceil(r/2)` jobs uniformly without replacement using ascending audit keys. T2 shall count the `q` priority selections before its first ratio comparison and update counts after each further selection. No job shall be selected twice. Priority uses only opaque-identity `first_round`, never identity generation or entity linkage. All other design provisions remain unchanged.

> **Tuning.** Repeat the complete registered 36-point grid, objective, search budgets, top-three recheck, seed namespaces, logging, and tie-breaking procedure for R3. Previous scores shall not select or exclude configurations. No alternative freshness window or priority policy shall be tested in this cycle.

> **Falsification and stopping.** F2 through F5, including both F2 targeting variants, applicability condition, per-seed profit condition, thresholds, and seed sets, remain unchanged. F1 retains every existing contract requirement, with selection fixtures updated to the registered priority procedure. Its fixtures shall additionally cover freshness boundaries, oversubscribed fresh-job sets, residual splitting, and T2 counts after priority selection. Any registered kill stops R3; no further design or gate revision is permitted within this study.

The priority rule removes the known quota obstacle for a sole newest six-job entrant when `k >= 6`. It does **not** guarantee coverage when multiple fresh identities exhaust the quota, or establish that R3 will pass the economic tests.

**Re-run scope and compute**

- Register the addendum, its explicit file permissions, and any required registration-verification changes. Include the affected F1 test files; Amendment 2’s current allow-list does not permit their revision by itself. Bind the freeze and final checks to Amendment 3.
- Run the revised contracts and isolated module check, then an inexpensive F2 diagnostic at the previous selected parameters. A kill ends the cycle before tuning.
- Repeat full tuning, regenerate the description, and rebuild the complete sweep inventory. Repeat proposed and ablation searches; reuse baseline search records only after their inputs and provenance verify unchanged. Rebuild the shared bank and every downstream record affected by it across all four rules, including reference, evaluation, doubling checks, and all-deviators. Record a new `f5_bank`, then run F1–F5 in full.
- Budget approximately **four laptop hours for tuning**, **one hour on three pods for proposed search**, and **up to nine hours on the previously loaded pod for later stages**; falsification takes minutes. Use the observed **USD 10–15 development-cycle cost** as a planning estimate, with the final evaluation’s compute and capped H1 costs reserved separately.
- Freeze only after every required gate passes. Then run sealed H2, public H3 on 40 fresh final-evaluation seeds, and the registered H1 runs within their cap. R3’s H1 result remains **INCONCLUSIVE** while its audit selection is not expressible.

**Disclosure sentence for the paper**

“Amendment 2 explicitly predicted an F2 kill at L = 10; we nevertheless executed the registered tests before any repair, reported the kill, and stopped that rule, then registered Amendment 3 after observing the development results and before implementing its successor, with the sealed bundle unread and F2 unchanged.”

**PAPER FRAMING:** The study reports a registered mechanism’s predicted structural failure, its measured development benefits, and one disclosed design iteration that retained the falsification gate. Any subsequent confirmatory claim concerns only the frozen successor and the registered final tests; the original rule remains killed, and its development results remain exploratory.

**RISKS:**

- **Scientific:** Reused development data and another amendment increase adaptation to the benchmark; disclosure and a single final evaluation cannot eliminate that limitation.
- **Mechanism:** Identity aging and simultaneous fresh entrants can evade or exhaust priority coverage; passing F2 would not establish general resistance to identity replacement.

**CONFIDENCE:** 0.84.

=== ASTRA round 1
**RECOMMENDATION:** **(b), variant b1 with `first_round == t`**, for one final registered iteration. Give new identities priority before splitting the remaining audit quota. Keep F2 unchanged, retain the full tuning grid, and stop if the revised rule is killed.

**RATIONALE:** The [registered kill](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/amendments/2026-10-17-amendment-2.md) stops the existing R*; a separately identified successor is legitimate registered iteration if the amendment precedes implementation, discloses all observed results, and commits to one attempt. F2 coverage is a stronger structural requirement than economic deterrence: T1’s −1.44 shows that incomplete coverage need not make this corner profitable, but does not prove that all cheating is unprofitable. T2’s approximately +154 to +158 shows a profitable replacement strategy under that variant, not economic failure of the selected T1 configuration. Fresh-identity priority addresses both the quota split and T2’s priority defect; b2 does not guarantee newcomer priority under T2, while b3 depends on the six-job capacity and still leaves T2 unresolved. Option c weakens the gate: profit-only F2 would still kill T2, and passing T1 alone would require another disclosed restriction. One further cycle is worth the stated USD 10–15 and roughly one day of elapsed compute if funds remain for final evaluation; options a/d preserve a useful negative result but provide no confirmatory R* result.

**IF AMENDMENT 3 — exact registered clauses:**

> **Design replacement: audit selection.** Let `k` be the round’s audit count after the unchanged schedule, served-job cap, and audits-left cap. Let `F` contain all served jobs whose identity has `first_round == t`. Select `f = min(k, |F|)` jobs from `F` in ascending `(audit_key, job_index)` order. Remove those jobs and increment their identities’ audit counts before further selection. Set `r = k − f`. Select `ceil(r/2)` remaining jobs using the registered T1 or T2 ordering, then select `floor(r/2)` jobs uniformly without replacement from the remaining served jobs using ascending `(audit_key, job_index)` order. T2 includes the priority selections in its audit counts and updates its ratio after each targeted selection. No job is selected twice. This procedure also applies at round zero and when several identities first offer together. The mechanism uses no generation indicator or entity linkage. All other design clauses remain unchanged.

> **Tuning.** Retain the full registered 36-point grid, search budgets, objective, top-three recheck, seed namespaces, tie order, and logging. Recompute all proposed-rule scores under the revised mechanism. Previously inspected development data remain development data.

> **Falsification and stopping.** Retain F1–F5, including both F2 targeting variants, its `k >= s` coverage condition, and its per-seed episode-profit condition. Add contract checks for the priority phase, simultaneous newcomers, quota exhaustion, audit-count updates, and relabeling invariance. These checks supplement F1; they do not replace existing checks. The amendment-2 result remains KILL. This study permits one successor design under amendment 3; a kill of its selected configuration ends proposed-rule development without another candidate or gate change.

The priority clause guarantees full coverage of a sole current-round newcomer when its jobs fit within `k` and no other newcomers compete for that quota. It does **not** establish deterrence against delayed cheating; that remains a search and evaluation question.

**Registration and re-run scope:**

- Register the addendum, signed tag, and timestamp before implementation. Name the successor and preserve all original artifacts. Explicitly register any required change to frozen test or harness files; do not treat those files as already allow-listed.
- Run contract checks and a cheap F2 diagnostic before expensive searches. Keep this diagnostic separate from the complete official F1–F5 report.
- Repeat tuning, describe generation, all 25 proposed search cells, and every affected reference, bank, evaluation, doubling, ablation, and all-deviators stage. Rebuild the bank and `f5_bank`; repeat baseline bank-dependent stages where bank membership changes. Reuse only unaffected records whose dependencies and hashes still validate.
- Budget about four laptop hours for tuning, one hour on three pods for proposed searches, and up to nine hours for later stages on the previously loaded pod; falsification takes minutes. Treat USD 10–15 as the supplied estimate, not a guaranteed ceiling.
- After all gates pass, freeze and verify against amendment 3. Then run sealed H2 and the registered 40 fresh final-evaluation seeds, including public H3, with required H1 work within its cap. Reserve this cost before starting the iteration; H1 against R* remains INCONCLUSIVE because its audit selection is not expressible.

**Disclosure sentence for the paper:**

“The authors expected F2 to kill the L = 10 design when amendment 2 was registered and nevertheless ran it as registered before any repair; after observing the kill and all development results, they registered amendment 3, retained the original kill and unchanged F2 criteria, and evaluated one revised design before opening sealed H2.”

**PAPER FRAMING:** The study reports an anticipated structural falsification, substantial development-set H3 gains over B2 and B3, and one disclosed design revision. Only the subsequent frozen evaluation can support confirmatory claims for the successor; any pass remains limited to the registered markets, attacker families, budgets, and statistical procedure.

**RISKS:**

- An identity can age before cheating, and several newcomers can consume the priority quota; passing F2 does not establish general resistance to identity replacement.
- Repeated use of development results increases selection bias, and another cycle can consume funds needed for final evaluation.

**CONFIDENCE:** 0.83 in this decision; this is not an estimated probability that the successor will pass.
