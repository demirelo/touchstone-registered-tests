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
