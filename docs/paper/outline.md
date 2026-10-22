# Paper outline (draft 1, 2026-10-22)

Working title: **Audit Dues: Newcomer-Priority Verification under Free Identity Replacement** (both referees, round 1)

Target: to be chosen. The AAMAS 2027 main-track deadline (8 October 2026) has passed. Candidates: EC 2027 (needs a stronger general theorem), NeurIPS 2027 (May), AAMAS 2028, or a workshop first. Length for an AAMAS-style venue: 8 main pages containing the essential evidence; extended proofs and records in supplementary material.

## Contribution (from the positioning note section 1, narrowed by the round-1 and round-2 referee reviews)
The cited static verification models omit identity replacement; inspection games optimise a scarce inspection stock; cheap-pseudonym models charge newcomers with fees or worse terms; credibility-based spot-checking in volunteer computing (Sarmenta 2001) already treats newcomers with suspicion. We study newcomer-priority auditing in a repeated procurement market with noisy verification and free identity replacement, with entry fees, identity certification, and collateral before receipts excluded from the mechanism class; the evaluated rules refund failed-job escrow and impose finite identity bans (the admissible class also permits bonds funded from earned receipts). We report a prospectively registered evaluation with disclosed amendments. No broad novelty claim.

## Sections, claims, evidence

1. **Introduction.** Problem; why bans fail under free replacement; audit dues; the protocol; results in one paragraph (original claim FAIL, amended claim PASS with its proxy-admission limit, theory and its scope, robustness with reserve collapse, high-noise efficiency loss, and coalition overload). Evidence: final-evaluation README; robustness results.
2. **Related work.** Distinguish Sarmenta 2001 explicitly (spot-checking with newcomer credibility and identity replacement in volunteer computing). Describe static verification models as omitting identity replacement, not as assuming persistent identities. Costly verification; inspection and audit games; cheap pseudonyms; noisy triggers; procurement with hidden effort; outsourced computation; evaluation methodology; mechanisms with verification (positioning note section 6; every citation verified against its primary source before it enters; report B entries only after verification).
3. **Model.** Market (N, J, T, values, providers, capacity), claims and effort, noisy audits with tolerance, escrow, refunds, bans, identity replacement, admissible rule class (no fees or bonds before receipts), metrics (gain decomposition into inflation and selection, gross and net efficiency, harm). Source: spec sections 3 to 7.
4. **Rules.** B1, B2, B3 (tuned before the lock); R3 (allocation, priority phase, residual split, schedule with terminal reserve and carry, enforcement). Source: `sim/mechanisms/`, amendments 2 and 3.
5. **Theory.** Lemma 1 and Corollary 1 (identity-neutral auditing plus immediate free replacement: the ban adds no continuation loss; refunds remain); Lemma 2 (coverage, overload hypergeometric); Lemma 2b (replacement targeting, with its conditions); recovery formula; Theorem (conditional renewal bound for stationary same-offer reset policies); Proposition: profitable small same-offer shading for served providers with zero continuation loss, under each studied rule at the locked parameters. Checks: 72 exploratory configurations on reused dev-val seeds; three pilot diagnostic outcomes preceded registration; renewal accounting uses measured cycle components, not an independent forecast; the surplus bound holds in 63 of 64 admitted seed cases. Keep theorem assumptions and essential proof arguments in the main text. Source: `docs/theory/reset-deterrence.md`, `checks-2026-10-21.md`. Proofs in Appendix A.
6. **Evaluation protocol.** Lock, amendments 1 to 4 with reasons, falsification tests F1 to F5 (including the amendment-2 kill), freeze, custodian-sealed H2 (its containment of D2 disclosed before unsealing), fresh final seeds, registered interval procedures admitted on development distributions (the amended comparisons use B3 proxy admission, without established nominal coverage for the selected R3), OpenTimestamps. Detailed hashes and review histories go to supplementary material. Table: timeline with tags and hashes. Source: lock run book, amendment notes, final-evaluation README.
7. **Results.** 7.1 Registered verdict (table: rule clause, baseline clause, amended clause with bounds; enforcement-matched ablations; gain decomposition; gross versus net efficiency; harm and false-ban costs). 7.2 H1 (exploratory; R3 INCONCLUSIVE because its audit rule is not expressible in the description vocabulary; the final cell completed after an outcome-informed cap amendment). 7.3 Exploratory and robustness (table by axis; reserve collapse, high-noise efficiency loss, coalition overload; entry-cost and position exceptions; no admitted coverage guarantee; coalition results do not isolate simultaneous timing; three incomplete doubling checks and nine failed twin controls; predictions against outcomes). Figures: gain against audit budget (H2), efficiency quadruple, robustness panel. Source: final-evaluation figures; robustness report.
8. **Discussion and limitations.** Search failures and twin-reference failures (nine failed twin checks; three incomplete doubling checks); initial overload in the first L rounds; finite-horizon limits; Amendments as forking paths and how the protocol bounds them; proxy admission of the amended clause; dev-val reuse in robustness; parameter transfer; unilateral benchmark, not equilibrium; terminal-reserve defect and a proposed cap (untested); coalitions; tolerance band.
9. **Conclusion.**

Appendices: A proofs; B amendment log with hashes and timestamps; C attacker families and search budgets; D robustness tables; E reproducibility (commands, commits, tags, seeds, salts).

## Figures and tables
- Fig. 1: gain against audit budget per rule (H2, final seeds) — exists (`docs/final-evaluation-2026-10-20/figures/figure1_gain_vs_audit.png`).
- Fig. 2: efficiency quadruple — exists.
- Fig. 3 (new): robustness panel, R3 against B2 and B3 under D2+H3 across variants.
- Fig. 4 (new): theory check, profit per round against shading level, reset and wait, B2/B3/R3.
- Table 1: registered verdict. Table 2: protocol timeline. Table 3: robustness predictions and outcomes.

## Open tasks
1. Verify every citation against its primary source (venue, year, pages, DOI); drop or mark any that fail.
2. Generate Fig. 3 and Fig. 4 from the committed JSON.
3. Draft sections 2 to 9; hostile referee reviews (Sol high and Astra high) before submission.

## Round-1 referee reviews (2026-10-22)
Sol high and Astra high both rejected draft 1 (0.94 each): overstated newcomer coverage, registration chronology, theory scope, and robustness; the amended result misstated as a share of a provider's profit; Sarmenta 2001 not distinguished; title too long; AAMAS 2027 deadline passed. Draft 2 applied many round-1 corrections; the round-2 vote (both reject, 0.95 and 0.96) listed the remainder, applied in draft 3.
