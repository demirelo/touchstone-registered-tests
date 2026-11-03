# Paper draft 9: outline, version 2 (Operation 9, prepared during Operations 6 and 7)

Version 2 applies outline review round 1 (`docs/revision/roster/{sol,astra}-paper-outline-r1.md`; both reject; the
disposition table is at the end).

Draft 8 (`paper/main.tex`) reports the first registered evaluation only. Draft 9 reports both evaluations and is written
around the questions of protocol v2 (triage T8, `docs/revision/gpt-pro-review-r2-triage-2026-10-27.md`): **persistent
age-ranked targeting versus verified-history targeting** (Q1; T1), the decomposition of R3 (Q2), attack strength and the
failure boundary (Q3), and replication on fresh markets (Q4). R3's priority window expires, but its newest-first residual
targeting can keep a replacement identity under heavy inspection (Lemma 2b); the text keeps this distinction everywhere.
Procedure detail moves to a supplement. The first evaluation's record, errata, and claims are unchanged (design 2).

Working files: `docs/revision/paper-v2/main.tex` (draft), `numbers.tex` and `tables/*.tex` (generated), copied into
`paper/` at Operation 9, after the report (the data-only rule keeps `paper/` unchanged until then).

## Rules for the text

- **Numbers.** Every evaluation-2 number comes from `report.json`:
  - Tables are **generated whole** by `tables_v2.py` from named row specifications (statistic, report path, row label);
    the text never fills a result table by hand. Tests: swapped labels, missing cells, refused cells, nonfinite values.
  - **Result sites.** `sites.json` names every result sentence's statistic: site name -> exact report path (question,
    family or market, statistic), kind, and section; it is written from this outline before the report exists and
    reviewed with it. Result regions use only `\site{name}`; raw report paths are refused there. The check requires each
    site exactly once outside comments (comments removed before `\input` files are expanded), inside a region, in its
    declared section (every `\section` carries `\label{sec:...}`; `sec:` labels only on sections; the keys abstract,
    intro, results, discussion, and conclusion must exist); every caption read whole and, outside a region, free of
    numbers and result macros; the abstract and the results section wholly inside regions; no unmarked
    number of any form outside the regions in the abstract, introduction, results, discussion, and conclusion, or in any
    caption; and no unmarked number with three or more decimals anywhere (evaluation-1 values in `\evone{}`, constants in
    `\const{}`). Stated limit, pinned by a test: a swap of any two sites within one section passes
    the check; the final read of the compiled PDF against `report.md` (step 2) covers it. Tables print p-values with the
    same formatter as prose.
  - Prose outside the manifest uses `\rvk{<kind>}{<report path>}` (kinds: count, p, gain, eff, label); the check
    verifies that the field name and the value type fit the kind, so a gain cannot stand where a count belongs. Plain
    `\rv` is refused inside result regions. The check inlines every `\input` file (generated tables excepted, checked by
    `tables_v2.py --check`) and flags any number with three or more decimals outside the regions that equals a report
    value (evaluation-1 values that coincide are wrapped in `\evone{}`).
  - `numbers_v2.py` writes the macros. `--check` fails on an unknown path, a stale
    `numbers.tex`, a nonfinite value, or any bare number (decimal, integer, or percentage, not part of an identifier
    such as F111 or X7-SC) inside a `% BEGIN-EV2` ... `% END-EV2` region. Every evaluation-2 result sentence, the
    abstract's and introduction's result sentences, captions, and figure notes sit inside such regions; counts in prose
    are written as words only when they are protocol constants ("six markets").
  - Figures are drawn from `report.json` by a script; figure data are written beside the figure and checked.
  - Rounding: three decimals for gains and efficiencies; p-values with four significant digits (small values in
    scientific form, never `0.000`).
- **Scope (design 9.4), in the main text:** the six sampled markets from the stated neighbourhood; the fixed pair for Q1,
  Q2, Q4; the searched families and frozen searches. No population claim. Q4 replicates the B3-R3 comparison under D2+H3
  and R3's efficiency condition, **not the complete amended PASS predicate**. Multiplicity is controlled within Q1 and
  within Q4 separately; **no paper-wide 5 percent guarantee**. Q4 is an internal replication, not an independent team's.
- **Status words.** "Confirmatory" means specified before the draw; coverage admission is conditional on the development
  fixtures (9.5) and does not establish nominal coverage on the fresh, selected-rule distributions. A **missing** cell
  removes every decision that uses it ("not decided: missing cell"); a **search-flagged** cell keeps its decision,
  labelled as about the prescribed search procedure, and makes that rule's Q3 robustness statement unanswered. H4 on
  fresh markets is **cut** (cuts 3); H4 runs at the headline only. Each affected claim names its status next to it.
- Reviewer acceptance (Sol, Astra) is development assistance, never validation (T7).
- Predictions are scored with the hashed scoring table (`docs/revision/predictions-v2.md`), misses included, by a
  script from `report.json`.

## Sections

**Titles (the author's request, 2026-11-03): easy to understand.** The paper title and every section and subsection title
say plainly what the part is about, in everyday words; codes (Q1, F111, X7-SC) go in parentheses after the plain words,
never alone. Paper title options (author's choice): "Auditing New Identities When Sellers Can Change Names Freely";
"Which Sellers Should a Buyer Check? Auditing Newcomers under Free Identity Replacement"; "Checking Newcomers When
Identities Are Free: Two Registered Tests of an Audit Rule". Section titles, in order: Introduction; Related work; The
market model; The audit rules we compare; What the theory shows; The attacks we test against; The first test (October
2026); The second test: design and registration; The second test: results; What the results show and what they do not;
Conclusion. Result subsections: Age-ranked versus history-based checking (Q1); Which parts of R3 matter (Q2); Stronger
attacks and where R3 fails (Q3); Repeating the comparison on six new markets (Q4).

**Abstract.** Problem and mechanism class (draft 8). R3 as a priority window plus persistent newest-first targeting
(T1). Evaluation 1 in one sentence with its conditions (original claim fails against the sealed family; amended claim,
registered after development results, passes on D2+H3 with interval admission by proxy). Evaluation 2: Q1 category per
family against the best of four tested credibility adaptations; Q4 k of six; one descriptive sentence each for Q2 and Q3.
Scope sentence.

**1 Introduction.** Problem; the restriction (no fees, certification, collateral); serial replacement only. Prior
principle: intensive verification of newcomers (Sarmenta; BOINC adaptive replication as an optional trust-threshold
policy, T5; customs guidance). The question: does persistent age-ranked targeting do better or worse than
verified-history targeting at identical allocation, payment, tolerance, ban, pacing, budget, and sanctions? Two
evaluations, staged registration. Contributions: (i) the replacement corollary; (ii) the matched comparison and the
factorial attribution; (iii) the attack envelope and the failure boundary (reserve collapse and the tested repair R4;
coalition overload; welfare attacks); (iv) two registered evaluations, including the original failure, the amendments,
and a fresh-market replication on instances drawn from a Bitcoin block after the lock.

**2 Related work.** Draft 8 with: T3 (Bhaskar scoped to adverse selection and moral hazard), T4 (weak or incomplete
attacks overstate robustness), T5 and the BOINC wiki for C-boinc; add Das, Yu, Zhang, AAAI 2026 (optimal committed
audits against the worst equilibrium versus our searched heuristic), Gatta, Naviglio, Tarantelli, arXiv:2609.02992
(reputation without persistent identity in agent markets; closest motivation, no verification budget), and Wellman,
Tuyls, Greenwald, JAIR 2025. Holm 1979 is cited where the decision rules use it, after a direct check of the entry.
Bibliography (R2): DOI or URL on every entry and a style that prints them; Sarmenta CCGrid pages and DOI; Walsh chapter
DOI (pages only after reading the chapter); Wellman 2006 "(Extended Abstract)" (pages only from the official PDF);
CrowdEval proceedings URL. The compiled reference list is checked for printed identifiers.

**3 Model (common to both evaluations).** Market, offers, round sequence, audit budget, identities, admissible rules,
the unilateral benchmark, metrics (gain, gross and net efficiency). Settings that differ by evaluation (the provider
population and markets, families, search budgets, seed counts) are stated in sections 7 and 8, not here. New objectives
at the headline of evaluation 2: welfare attacks (W0, W1; design 6.2) and coalitions (G_tot, G_min against the
coordinated truthful reference; design 6.3). No coalition-stability claim.

**4 Rules.** Common core and the fixed pair (tol 0.16, L 10; design 3.1). The 2 x 2 x 2 factorial F_PGS (priority P,
newest-first residual targeting G, pacing S; F000 = B3, F111 = R3). The credibility family (C-thr, C-mem, C-taper,
C-boinc; twelve development configurations) and C* = C-mem(K 6, M 20), stated as the best of four tested adaptations,
not the strongest possible credibility rule. R4: reserve min(JL, floor(A_tot / 2)); it differs from R3 only when
JL > floor(A_tot / 2): it equals R3 in the registered rho = 0.2 blocks and differs in the registered rho = 1 repair
block. Whole-system tuned variants B3-t, R3-t, C*-t (secondary).

**5 Theory.** Draft 8, each result with its assumptions beside it: Lemma 1, Corollary 1, Lemma 2 and the
persistent-targeting statement (2b), Theorem 1 with T2 (a bound for regenerative policies, not established for the
implemented R3), Proposition 1. T6: the theory note's "within half a standard error" becomes "about half a standard
error" (`docs/theory/reset-deterrence.md:70`); the paper keeps "about 0.51 standard errors". Detailed checks to the
supplement.

**6 Attackers.** D2 and D2+H3; X7-SC (state-conditioned, 15 knobs); X5-AG/v2; H4 (defence-aware, written in a sealed
session at the defender freeze, loaded once after the draw; headline only under cuts 3); welfare (W0, W1) and coalition
(X6-SE/v2, X8-DB) objectives. One table: family, observations, knobs, markets where it runs. Searches, references, freeze
order, and doubling checks (design 6.4, 6.5) in brief; detail to the supplement.

**7 Evaluation 1 (first registered evaluation).** In the main text: both predicates defined compactly (original claim
with rule and baseline clauses; amended claim on D2+H3 with absolute part and paired reductions), when each was
registered relative to what had been seen, the unchanged verdict table with its caption conditions (amended PASS also
requires the H2 rule clause and admission of the comparison bounds; admission by proxy; nominal coverage for the
selected R3 not established), material errata, H1's exploratory and inconclusive status, and the robustness failure
modes in one paragraph. Detailed chronology and the robustness table go to the supplement.

**8 Evaluation 2 (protocol v2).** What was completed, in order, and what was planned: development on headline and dev0 (branch `two20k`)
(benchmark, comparator selection, tuning, defender freeze, the sealed H4 session, coverage with admitted
kappa Q1 = 0.5 and Q4 = 0.25, predictions), cuts 3, the budget. The lock: signed tag `protocol-v2`, the OpenTimestamps
proof with the earliest Bitcoin attestation at block 974307, publication before the target block (the push height and
the condition of design 7.3), and the trust assumptions: the chain both explorers serve at the final read is the
accepted chain; no miner selects the target block to influence this evaluation; a later reorganisation deeper than six
blocks is not handled and would be reported. The draw: H = A + 144 = 974451 at depth 6; six fresh markets from the stated neighbourhood; 200
evaluation seeds each. Decision rules table: Q1 direction by Holm on calibrated two-sided p-values (tails 0.05/4, 0.05/2)
and size by the calibrated Bonferroni interval against the margin 0.05, the four exclusive categories, the "better" gate
(category 1 plus a nominal one-sided 97.5 percent gross-efficiency lower bound of at least -0.01, descriptive, no
calibrated joint guarantee) and the labels "efficiency non-inferiority unresolved" and "lower gain with an efficiency
loss"; Q4 intersection-union test per market with Holm over six slots, reported as k of six with failing markets named
and undecided markets marked "generalisation not established"; Q2 and Q3 descriptive. Hashes and custody records go to
the supplement; the protocol file is the authority.

**9 Results of evaluation 2.** In question order, from generated tables:
- **Q1.** Per family: pooled d = g_C* - g_F111, interval, category, and the efficiency label; beside it the paired gross
  and net efficiency, truthful reference profit, audit spending, refunds from false failures (focal and other
  providers), and served share. Per-market and headline Q1 results descriptive (the headline was used in development).
  Figure: pooled intervals against the margin.
- **Q4.** Per market: F000 - F111 estimate and calibrated lower bound, F111 efficiency and lower bound, the two calibrated
  p-values, the Holm decision; k of six; failing and undecided markets named; search-flagged markets labelled.
- **Q2.** Pooled main effects, two- and three-way interactions, and the registered conditional effects (G at P = 0 and 1,
  P at S = 0 and 1, P at G = 0 and 1, G at S = 0 and 1), under separately searched attacks and fixed attacks; fixed-attack
  contrasts as the equal-weight mean over the eight attack rows (design 6.6), each with its attacker-profit and
  reference-profit terms and gross and net efficiency beside it. Nominal intervals, no decisions. Per-market and
  per-family tables to the supplement.
- **Q3.** Per core rule (F000, F111, C*) on each market: the attack envelope, the family with the highest training gain
  among D2+H3, X7-SC, X5-AG/v2, and H4 (headline only), evaluated unchanged; welfare: the training-selected lowest
  efficiency under W0 and W1, the other welfare family beside the selected one, and W1's supported / contradicted /
  unresolved profitability class; coalitions: G_tot and G_min for X6-SE/v2 (both sizes and schedules) and X8-DB (roles
  schedule) against the coordinated truthful reference; the rho = 1 repair block (R3 versus R4); the honest-replacement
  diagnostic; the separate doubled-winner diagnostic. Missing and search-flagged consequences named beside each claim.
- **Secondary.** The whole-system tuned comparison, labelled secondary.
- **Search quality.** Doubling flags and missing cells, and the statements each one affects.
- **Predictions.** The scoring table (fulfilled, failed, not assessed), generated.

**10 Discussion and limitations.** What the two evaluations support together; what they do not: unilateral benchmark,
no equilibrium or incentive compatibility; bounded-gain claims (Proposition 1); exposure bounded by the searched
families and optimiser; coverage conditional on fixtures; six markets from one neighbourhood; internal replication;
headline used in development. The failure boundary and the tested repair. Open questions.

**11 Conclusion.**

**Availability.** A paragraph in the main text: the public release at the report commit with code, tuned files, all
records of both evaluations (including incomplete, failed, and cut cells), the generator, the block headers, the paper
sources, and a one-command reproduction of every table (`scripts/reproduce.py`), with its release and DOI status stated
as it is at submission (design 10). Preparation and checks are the executor's; publication is the author's.

**Appendix.** Parameters (draft 8 A, labelled by evaluation); proofs (draft 8 B); the market neighbourhood and the
generator. **Supplement** (in the release): evaluation-1 procedure and timeline, robustness table, draft 8 figures 1
and 2; protocol v2, predictions, operations ledger, lessons, review rounds; per-market and per-family Q2 and Q3 tables;
hashes and the H4 custody record.

## Figures and tables

T1 rule set (factorial, comparator, R4, tuned). T2 attacker families. T3 evaluation-1 verdict (draft 8). T4 evaluation-2
decision rules. T5 Q1. T6 Q4. T7 Q2. T8 Q3 envelope, welfare, coalitions. T9 predictions scoring. F1 Q1 intervals. F2 Q4
per-market bounds. F3 factorial contrasts.

## Order of work

1. **Now (no results needed):** sections 1 to 8 except result sentences; bibliography fixes and checks; T6 in the theory
   note; `numbers_v2.py` (done; extend: integers, percentages, nonfinite values) and `tables_v2.py` with synthetic
   `report.json` tests (swapped labels, missing and refused cells, stale outputs); the prediction-scoring script with
   tests; the artifact checklist.
2. **After the report:** rebuild and verify it (`report_v2.py --check`); generate numbers, tables, figures, and the
   scoring table; write section 9 and the result sentences of the abstract and introduction; `numbers_v2.py --check`;
   prepare the artifact and run `reproduce.py` on a clean clone; compile the draft and check the PDF (references print
   identifiers; no `??` markers).
3. **Review:** Sol high and Astra high review the draft against the protocol and the report to consensus.
4. **Copy and recheck:** copy into `paper/`; recompile; rerun every check on the copied sources and the release bundle.

## Disposition of outline review round 1

| Correction (Sol / Astra) | Change |
|---|---|
| T1 framing (S1 / A1) | Persistent age-ranked targeting versus verified-history targeting, throughout; title option qualified |
| R4 identity (S2) | Condition JL > floor(A_tot/2); equal in rho 0.2 blocks, differs in the rho 1 block |
| Q1 side evidence and "better" gate (S3 / A3) | Section 8 decision table and section 9 Q1 bullet |
| Q2 conditional effects and decomposition (S4 / A4) | Section 9 Q2 bullet; per-market tables to the supplement |
| Q3 selection, W1 class, coalition reference (S5 / A5) | Sections 3 and 9 |
| Scope and status words (S6 / A2) | "Rules for the text": scope and status words |
| Evaluation 1 compression (S7 / A6) | Section 7: predicates, timing, caption conditions, errata, H1 status in the main text |
| Common versus evaluation-specific model (A6) | Section 3 |
| Branch, kappa, cuts, publication condition, trust assumption (A7) | Section 8 |
| Artifact (S8 / A9) | "Availability" paragraph; order of work |
| Citations, T6 (S9 / A8) | Section 2; section 5 |
| Numbers pipeline (S10 / A10) | Generated tables, integer and percentage checks, nonfinite values, figure data, scoring script |
| Order of work (S11 / A10) | Four steps, with rebuild, reproduction, compile, and recheck after copying |

## Disposition of outline review round 2

| Correction (Sol / Astra) | Change |
|---|---|
| Prose path mapping (S1 / A1) | `\rvk{kind}{path}` with field-name and type checks; plain `\rv` refused in regions; tests: a gain used as a count fails |
| Coverage across included files (S2 / A1) | Inlined `\input` files; report-valued numbers outside regions flagged; tests |
| p-value rounding (S3 / A2) | Four significant digits, scientific form for small values; test with 0.0001 and 3e-05 |
| Branch and chain assumptions (S4 / A3) | Section 8: `two20k`, no miner selection, deeper reorganisation unhandled and reported |
| Author's note (2026-11-03) | Plain-language titles throughout |

## Disposition of outline review round 3

| Correction (Sol / Astra) | Change |
|---|---|
| Site-to-path binding, same-kind swaps (S1 / A1) | `sites.json` manifest; `\site{}` only in regions; each site once, in its section; tests for wrong section, double use, unused, unknown site, bad manifest path; residual limit stated |
| Coverage of unmarked results (S2 / A2) | Abstract and results section wholly in regions; every unmarked three-decimal number outside regions flagged, including included captions; tests |
| Table p-values (S3 / A3) | Tables use `_fmt_p`; test for small p in the Q1 and Q4 tables |

## Disposition of outline review round 4

| Correction (Sol / Astra) | Change |
|---|---|
| Results key (S1) | Section keys from `\label{sec:...}` on any line; the check fails without `sec:results`; test |
| Unmarked counts in captions and other sections (S2 / A2) | No unmarked number in abstract, introduction, results, discussion, conclusion, or any caption; tests (caption in an included file, discussion sentence) |
| Limit wording (A1) | "any two sites within one section", pinned by a test that the swap passes |
| Commented sites (A3) | Comments stripped before counting; test: a site only in a comment is unused |

## Disposition of outline review round 5

| Correction (Sol / Astra) | Change |
|---|---|
| Section keys (S1 / A2) | Every `\section` needs `\label{sec:...}`; `sec:` labels elsewhere refused and ignored; five required keys; tests |
| Captions (S2 / A1) | Whole captions by brace matching across lines; outside regions no number and no result macro; tests (multiline, macro) |
| Comments (A3) | Comments removed per file before `\input` expansion, `\\%` handled; tests |
