# Draft 10 outline: rebuild around the churn result (2026-11-16)

Decision: the author's board answer on card `touchstone-paper-scope` (2026-11-16 10:29Z): "Rebuild around the churn
result, about 15 pages, new subtitle". Input: Fable 5.2 round 4 (`docs/revision/roster/fable52-paper-r4.md`, written on
draft 9 at 2066cdd, before 24b0c40 and before the churn rates 0.02 and 0.03, Run A and Run B existed), the churn
amendment (f682415), Run A (9bad3b1), Run B (09586ed).

Venue facts (WEIS 2026 call, the latest found; no 2027 call found on 2026-11-16): no page limit, PDF, double-anonymous
review (the submission must carry no author name or affiliation), deadline about 1 February. The 15-page target is the
author's choice, not a venue rule. Recheck when the 2027 call appears.

## 1. The story in one paragraph

A ban costs nothing under uniform audits when identities are free (theory). R3 answers with age-ranked audit priority.
In two registered tests, without honest churn, R3 beats uniform audits on every market and ties a verified-history
comparator C* within the margin (direction R3 lower, now positive on all six markets after Run B). Two exploratory
follow-ups locate where that advantage lives. (a) Reset: most of the B3 minus R3 gap disappears when the attacker cannot
replace its identity. (b) Churn: when honest opponents also replace identities, R3's audits move to honest newcomers and
its advantage falls with the churn rate, crossing C* between p = 0.01 and 0.02 and crossing B3 between 0.03 and 0.05.
R3's measured advantage exists only while the attacker is almost the only source of new identities.

## 2. Title

Keep the main title; new subtitle that states the exploratory status of the churn finding (advisor point):
"Checking Newcomers When Identities Are Free: Registered Tests of Age-Ranked Audits, and Their Limit Under Honest Churn".
Alternative for review: "... Two Registered Tests and an Exploratory Churn Limit". The abstract's first churn sentence
says "exploratory, specified after the report".

## 3. Registered and exploratory stay separate

- Registered labels unchanged ("equivalent, direction R3 lower"; Q4 k = 3 of 6; prediction tallies).
- Every follow-up (reset, churn at 0.01 to 0.05, Run A, Run B) carries "exploratory, after the report" at its first use
  in each section, and changes no registered decision.
- Run A covers C-thr(12) WITHOUT churn: churn robustness is shown for C* = C-mem(6, 20) only, never for
  "verified-history targeting" as a class.
- Run B re-searched the 19 registered flagged cells (no churn cells): the p = 0.01 C* contrast under churn stays "not
  resolved"; 13 of 36 (0.01, 0.05) and 8 of 36 (0.02, 0.03) churn cells are flagged.

## 4. The churn result (from the records, not from Fable's text)

Pooled, frozen searches (doubled in brackets), `churn.json` and `churn_mid.json`:

| p | g(R3) | C* - R3 | B3 - R3 |
|---|---|---|---|
| 0 | 0.065 | 0.021 (0.030) | 0.173 (0.170) |
| 0.01 | 0.065 | 0.001 (-0.004) | 0.175 (0.153) |
| 0.02 | 0.111 | -0.020 (-0.021) | 0.119 (0.127) |
| 0.03 | 0.167 | -0.090 (-0.063) | 0.068 (0.069) |
| 0.05 | 0.272 | -0.173 (-0.169) | -0.052 (-0.033) |

Mechanism, R3 under its selected attack, frozen (`review_r4.audit_allocation`): the attacker's audited share of jobs
falls 0.366, 0.190, 0.093, 0.042 at p = 0.01, 0.02, 0.03, 0.05, while under C* it stays 0.29 to 0.36 and under B3 it is
0.25. Honest identities younger than ten rounds hold 0.13, 0.21, 0.27, 0.39 of jobs and take 0.33, 0.54, 0.68, 0.82 of
R3's audits; established honest jobs are audited at 0.17, 0.14, 0.11, 0.08. Selected R3 attacks with replacement off:
2, 2, 3, 3 of six markets. Reading: a steady decline, not a threshold. The attacker's audit rate under R3 drops below
C*'s by p = 0.02 (the C* crossing) and below B3's 0.25 already near 0.02, while the B3 gain gap crosses later (0.03 to
0.05) because gain also depends on the selected attack's other knobs. Fable's quota-saturation point (p near 0.028) is
one way to read the B3 side; it does not explain the C* crossing, so the paper states the audit-rate curve and does not
claim saturation as the cause. Diagnostics describe, they do not isolate the cause (histories reset, bans end, attacks
change).

Also reported: efficiency under attack per rate (`eff_attack`; R3 0.994, 0.989, 0.985, 0.981, 0.967; fresh2 at 0.05
is 0.893, below the registered 0.90 threshold, exploratory); market-level t intervals (`t95`) with sign counts for both
search versions; the reselection diagnostic (16 of 36 nonzero, largest 0.0046); the largest flag change (0.087); raw
profit units or gain units for the profit decomposition.

## 5. Section map and page budget (about 15 pages of main text)

| # | Section (label) | Pages | Content |
|---|---|---|---|
| | Abstract | 0.4 | Problem; theory; registered results with "without honest churn"; reset; churn curve with both crossings; limits. |
| 1 | Introduction (`intro`) | 1.5 | Problem, mechanism class, the rule, the two tests, contributions rewritten around the limit. Related work folded in (0.5 page). |
| 2 | Model, rules and theory (`model`) | 2.5 | Market model, the rules, Corollary (uniform ban costless), Lemma (coverage) with its overload case, attack families in brief. |
| 3 | Registered tests and results (`results`) | 3.5 | Design in one page; Q1 and Q4 with Run B as sensitivity; Q2 and Q3 in one paragraph each with pointers to the appendix. |
| 4 | Where the advantage lives: identity replacement (`reset`) | 1.5 | The reset follow-up, shortened. |
| 5 | Honest churn (`churn`) | 3 | Design; the five-rate table and one figure (the two contrasts against p); audit allocation; efficiency; t intervals and flags; Run A note. |
| 6 | Limits (`discussion`) | 1.5 | Exploratory status; one comparator; frozen references; flagged cells; fixed parameters; unilateral deviation; exact checks paragraph. |
| 7 | Conclusion (`conclusion`) | 0.5 | One paragraph; availability. |
| A | Appendix (`app-*`) | open | First test; registration detail; Q2, Q3, welfare, coalitions, repair, stability, predictions tables; parameters; proofs. |

## 6. Number gate changes (tests first)

- `numbers_v2.py`: new section keys `reset`, `churn` and the appendix result sections join `FULL` and `NOBARE`;
  `churn` joins `REQUIRED`. A failing test first (a bare number in a `churn` section must be refused).
- `sites.json`: every moved site gets its new section; deleted sentences drop their sites (the gate refuses unused
  sites); new sites for the 0.02 and 0.03 rates, audit allocation, efficiency, t intervals, Run A and Run B, with kinds
  that the existing KINDS accept or a tested extension.
- `floats.json`: the listed evaluation-2 floats follow their tables into the appendix; every listed float must stay
  wholly inside one result region.
- New tables: `posthoc_churn.tex` extended to five rates (generator in `churn_block.py`, byte-identical regeneration
  test), a churn figure, an audit-allocation table.

## 7. Fable round-4 problems: where each is handled

1 (paper contradicts its churn arm): abstract, intro, model, limits, conclusion rewritten. 2 (mechanism): section 5,
from `audit_allocation`; 24b0c40 already removed "hides among them". 3 (saturation): replaced by the measured curve at
five rates. 4 (efficiency): section 5. 5 (qualifications at 0.05): sign counts, t intervals, doubled values. 6 (p = 0.01):
"not resolved" for C*. 7 (abstract finding 1 conditional): "without honest churn". 8 (reporting gaps): reselection,
largest flag, units, the timing-check direction, frozen menus. 9 (process): ledger plan commit ef17139 and pod time;
follow-up spend stated (reset 1.65, churn 4.99, churn mid 7.70 bound, Run A 3.14 bound, Run B 2.76 + 3.40); scipy
dependency note. 10 (length): this rebuild.

## 8. Order of work

1. Gate tests and `numbers_v2.py` section keys (red, then green).
2. Churn table and figure generators for five rates (tests first).
3. Rewrite `main.tex` section by section; `paper_check.sh` after each section.
4. Anonymised build check (no author name) as a gate item for the submission copy.
5. Sol/Astra review to consensus.
