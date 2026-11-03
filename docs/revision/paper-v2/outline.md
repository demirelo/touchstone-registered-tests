# Paper draft 9: outline (Operation 9, prepared during Operations 6 and 7)

Draft 8 (`paper/main.tex`) reports the first registered evaluation only. Draft 9 reports both evaluations and is written
around the questions of protocol v2 (triage T8, `docs/revision/gpt-pro-review-r2-triage-2026-10-27.md`): age-based versus
evidence-based release (Q1), the decomposition of R3 (Q2), attack strength and the failure boundary (Q3), and replication
on fresh markets (Q4). Procedure detail moves to a supplement. The first evaluation's record, errata, and claims are
unchanged (design 2, "The old record stays").

Working files: `docs/revision/paper-v2/main.tex` (draft), `docs/revision/paper-v2/numbers.tex` (generated), copied into
`paper/` at Operation 9, after the report (the data-only rule keeps `paper/` unchanged until then).

## Rules for the text

- **Every evaluation-2 number comes from `report.json`** through `numbers.py` (writes `numbers.tex` macros; `--check`
  fails when a macro differs from the report or the text holds a bare number where a macro exists). No hand-copied result.
- Every claim carries the scope of design 9.4: the six sampled markets, the stated neighbourhood, the fixed pair, the
  searched families, the frozen searches. No population claim; Q4 is an internal replication, not an independent team's.
- "Confirmatory" means specified before the draw; coverage admission is conditional on the development fixtures (9.5).
- Reviewer acceptance (Sol, Astra) is development assistance, never validation (T7).
- Predictions are scored with the hashed scoring table (`docs/revision/predictions-v2.md`), misses included.

## Sections

**Title (author's choice).** Keep "Audit Dues" or move to the comparison, e.g. "Age or Evidence? Audit Selection under
Free Identity Replacement".

**Abstract.** Problem and mechanism class (draft 8). The rule as persistent age-ranked targeting with a priority window
(T1). Evaluation 1 in one sentence (original claim fails against the sealed family; amended claim passes on D2+H3).
Evaluation 2: registered Q1 category per family against the credibility comparator; Q4 count k of 6; one sentence each
for Q2 and Q3 (descriptive). Scope sentence.

**1 Introduction.** Problem; the restriction (no fees, certification, collateral); serial replacement only. Prior
principle: intensive verification of newcomers (Sarmenta; BOINC adaptive replication as an optional trust-threshold
policy, T5; customs guidance). The question the paper answers: does release by age do better or worse than release by
verified history, at identical budget, payment, tolerance, ban, pacing, and sanctions? Two evaluations, staged
registration. Contributions: (i) the replacement corollary (ban costless under uniform audit); (ii) the matched
age-versus-evidence comparison and the factorial attribution; (iii) the attack envelope and the failure boundary
(reserve collapse and its repair R4; coalition overload; welfare attacks); (iv) two registered evaluations with the
original failure, amendments, and a fresh-market replication on instances drawn from a Bitcoin block after the lock.

**2 Related work.** Draft 8 with: T3 (Bhaskar scoped to its adverse-selection and moral-hazard model), T4 (weak or
incomplete attacks overstate robustness, Carlini et al., Tramer et al.), T5, the BOINC wiki for C-boinc; add Das, Yu,
Zhang, AAAI 2026 (optimal committed audits against the worst equilibrium, contrasted with our searched heuristic) and
Wellman, Tuyls, Greenwald, JAIR 2025 (empirical game-theoretic analysis). Bibliography: DOI or URL on every entry and a
style that prints them (R2); Sarmenta CCGrid pages and DOI; Walsh chapter DOI (pages only if read); CrowdEval proceedings
URL.

**3 Model.** Draft 8 (market, offers, round sequence, audit budget, identities, admissible rules, benchmark, metrics),
plus the two new objectives at the headline: welfare attacks (W0, W1: lower gross efficiency, design 6.2) and coalitions
(total G_tot and worst-member G_min, design 6.3).

**4 Rules.** Common core and the fixed pair (tol 0.16, L 10; design 3.1). The 2 x 2 x 2 factorial F_PGS (priority P,
newest-first residual targeting G, pacing S; F000 = B3, F111 = R3). The credibility comparator family (C-thr, C-mem,
C-taper, C-boinc; twelve development configurations) and the selected C* = C-mem(K 6, M 20), stated as the best of four
tested adaptations, not the strongest possible credibility rule. R4 (reserve capped at half the allowance; equals R3
except at rho = 1). Whole-system tuned variants B3-t, R3-t, C*-t (secondary).

**5 Theory.** Draft 8: Lemma 1, Corollary 1, Lemma 2 and the persistent-targeting statement (2b), Theorem 1 with T2
(a bound for regenerative policies, not established for the implemented R3), Proposition 1. Theory checks paragraph
shortened; detail to the supplement.

**6 Attackers.** D2 and D2+H3; X7-SC (state-conditioned, 15 knobs); X5-AG/v2; H4 (defence-aware, written in a sealed
session at the defender freeze, loaded once after the draw); welfare and coalition objectives (X6-SE/v2, X8-DB). One
table: family, observations, knobs, where it runs. Searches, references, freeze order, doubling checks (design 6.4, 6.5)
in brief; detail to the supplement.

**7 Evaluation 1 (first registered evaluation).** Compressed from draft 8 sections 6 and 7: lock, amendments, sealed H2,
the verdict table (unchanged), the exploratory LLM attacker in two sentences, the robustness failure modes in one
paragraph. Full timeline and robustness table to the supplement.

**8 Evaluation 2 (protocol v2).** Development (benchmark, comparator selection, tuning, defender freeze, H4 session,
coverage check with admitted kappa, predictions); the lock (signed tag `protocol-v2`, OpenTimestamps proof with the
earliest Bitcoin attestation at block 974307); the draw at H = A + 144 = 974451 with depth 6 on two explorers; six fresh
markets from the stated neighbourhood, 200 evaluation seeds each; budget and cuts. Decision rules: Q1 categories with
margin 0.05 and Holm (9.3); Q4 intersection-union test per market with Holm, reported as k of 6; Q2 and Q3 descriptive.
One table of the registered decision rules; the protocol file is the authority.

**9 Results of evaluation 2.** In question order, each a table or figure from `numbers.tex`:
- Q1: pooled d = g_C* - g_F111 with interval and category per family (D2+H3, X7-SC); efficiency difference; "better"
  labels if any. Figure: the two pooled intervals against the margin.
- Q4: per market F000 - F111 lower bound, F111 efficiency lower bound, calibrated p-values, Holm decision; k of 6.
- Q2: main effects and interactions (searched and fixed-attack), pooled; stated as descriptive.
- Q3: attack envelope (X7-SC, X5-AG/v2, H4 at the headline), welfare (W0, W1), coalitions (G_tot, G_min), the rho = 1
  repair block (R3 versus R4), the honest-replacement diagnostic.
- Secondary: whole-system tuned comparison.
- Search quality: doubling flags and missing cells, with their effect on each statement.
- Predictions: the scoring table, fulfilled, failed, and not assessed.

**10 Discussion and limitations.** What the two evaluations support together; what they do not (unilateral benchmark,
no equilibrium; bounded-gain claims; search-bounded exposure; coverage conditional on fixtures; six markets from one
neighbourhood; internal replication). Failure boundary and the tested repair. Remaining open questions.

**11 Conclusion.**

**Appendix.** Parameters (draft 8 A); proofs (draft 8 B); the market neighbourhood and the generator; the H4 custody
record. **Supplement** (artifact): evaluation-1 procedure and timeline, robustness table, protocol v2, predictions,
operations ledger, lessons, review rounds.

## Figures and tables

T1 rule set (factorial, comparator, R4, tuned). T2 attacker families. T3 evaluation-1 verdict (draft 8). T4 Q1. T5 Q4.
T6 Q2. T7 Q3 envelope. T8 predictions scoring. F1 Q1 intervals. F2 Q4 per-market bounds. F3 factorial contrasts.
Draft 8's figures 1 and 2 move to the supplement.

## Order of work

1. Now (no results needed): sections 1 to 8 except result sentences; bibliography fixes; `numbers.py` with a synthetic
   `report.json` test (positive and negative cases).
2. After the report: section 9, abstract and introduction result sentences, figures; `numbers.py --check`.
3. Sol high and Astra high review the draft against the protocol and the report to consensus; then copy into `paper/`.
