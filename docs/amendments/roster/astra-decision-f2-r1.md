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
