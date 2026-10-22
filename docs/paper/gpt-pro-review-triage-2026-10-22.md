# GPT Pro review (2026-10-22): triage

Verdict received: reject at AAMAS (2/5, confidence 4/5); strong reject at EC. The review text is kept by the author; this file records each finding, our check, and the action. "Text" actions are applied in draft 7; "Program" actions need new experiments and are a scope decision for the author.

## Novelty
| Finding | Check | Action |
|---|---|---|
| Newcomer-intensive verification is established (Sarmenta 2001 with explicit reentry analysis; BOINC adaptive replication; customs practice for new importers; CrowdEval; probation monitoring, Bhaskar 2025) | Accepted. Sarmenta 2001 analyses rejoining under new identities; BOINC requires full replication until hosts earn trust | Text: rewrite related work and contribution as an age-based, finite-budget variant of an established principle. Program: a budget-, sanction-, and pacing-matched credibility (BOINC/Sarmenta-style) comparator |
| Contribution narrowly original: exact constraint set, R3, quantified failure boundaries, auditable record | Accepted | Text: contribution paragraph |

## Claims
| # | Finding | Check | Action |
|---|---|---|---|
| 1 | "Our rule shares the intuition" understates Sarmenta | Accepted | Text |
| 2 | Verification is itself differential newcomer treatment; incidence | Accepted | Text |
| 3 | Friedman-Resnick stated as universal | Accepted | Text |
| 4 | [7] misclassified as scarce costly inspection | Accepted (ex post verification with limited penalties) | Text |
| 5 | Attribution: the killed predecessor (no priority phase) already had H3 dev-val gain 0.073 vs R3 0.070; the reduction is not attributable to newcomer priority | **Accepted and verified** (amendment 3, F5 of the amendment-2 rule). The H3 effect comes from age-based newest-first targeting and pacing, shared by both rules; the priority phase closed the F2 coverage gap | Text: reframe mechanism and title around age-based (newest-first) verification; state that priority's contribution is not identified. Program: factorial decomposition |
| 6 | "Prospectively registered" must distinguish staged registration | Accepted | Text |
| 7 | H2 "does not exit or re-enter" in amendment 1 vs disclosure | **Resolved**: public spec section 6 line 592 states "Neither H1 nor H2 exits or re-enters" (pre-lock interface) | Text: cite the spec |
| 8 | "A kill stops the rule" too compressed | Accepted | Text |
| 9 | Threat model: fixed entities, one active identity, no aliases or reserve identities | Accepted | Text: threat-model paragraph; cite Douceur |
| 10 | Theorem scope wording | Accepted | Text |
| 11 | "Targeting makes q_E large" false for small shading (q_E about 0.004 at truthful effort with six audits) | Accepted | Text |
| 12 | Supplement corollary still age-only | Accepted | Text (theory document) |
| 13 | Supplement equality needs G_E >= epsilon | **Accepted, a real error** | Text (theory document) |
| 14 | Checks narrative overinterprets; reset vs wait also changes fresh effort; stale "Proposition 6" | Accepted | Text (theory and checks documents) |
| 15 | "Hard to exploit" | Accepted | Text |
| 16 | README: "within noise" unsupported; H3 numbers called losses of honest surplus | **Accepted, two reporting errors** | Text: erratum in the final-evaluation README |
| 17 | Coalition result is a focal-payoff stress test | Accepted | Text |
| 18 | Entry costs do not establish protection | Accepted | Text |
| 19 | Model review is not independent validation | Accepted | Text |
| 3.2 | Common truthful rate h not automatic when d0 > 0; same-offer benchmark differs from the optimised reference | Accepted | Text: theorem remark |
| 3.4 | Robustness consequences must stay visible (beta 0.02 efficiency 0.841, etc.) | Accepted; mostly present | Text |
| 3.5 | Reproducibility: provider triples, bid domain, position ordering, S* definition, family definitions, raw results, artifacts | Accepted | Text: appendix with parameters and definitions. Program: public artifact release |

## Venue
Ranking received: AAMAS 2028, GameSec 2027, WINE 2027, EC 2027 (not as is), IJCAI 2027 (11 January 2027, verified by the reviewer), workshops WMAC 2027 (20 November 2026), WEIS 2027 (21 January 2027, tentative). Decision pending.

## Bibliography
No fabricated entries. Actions (Text): remove the "verified" note fields that print in the reference list; add DOIs and URLs; Tramèr et al. pages 1633-1645; cite the original Vlasiou 2011 encyclopedia entry; add the missing references after our own verification: Anderson and Reed 2009 (BOINC), Watanabe and Fukushi 2010, Qiu et al. 2018 (CrowdEval), Fernández Anta et al. 2015, Bhaskar 2025, Liu and Neilson 2013, Solan and Zhao 2021, Douceur 2002, Li 2021 (TE), Wellman 2006, Nosek et al. 2018, Simmons et al. 2011, Townsend 1979, Auletta et al. 2004, Walsh 2003, Gangl et al. 2014, Teutsch and Reitwießner 2019, Sarmenta CCGrid 2001.

## Program (needs the author's decision)
1. Matched credibility comparator (release from intensive verification after validated work, BOINC/Sarmenta-style), same budget, sanctions, and pacing.
2. Factorial decomposition of R3: priority phase, residual newest-first targeting, terminal pacing; include the killed predecessor; tune every rule with the same reset-aware objective and budget.
3. Stronger attacks: policies conditioning on age, remaining budget and horizon, targeting rank, wait versus reset, claims and bids; welfare-seeking attacks; coalition total and per-member payoffs.
4. Fresh market instances (varying provider costs, capacities, ceilings), a newly registered evaluation, and a public reproducible artifact.
