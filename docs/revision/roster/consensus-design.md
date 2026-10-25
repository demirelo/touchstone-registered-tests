# Consensus on the revision-program design (2026-10-22)

Roster: Sol high (`gpt-6.1-sol`), Astra high (`gpt-6-astra`), through the Codex CLI, read-only, no paid APIs.
Rule: qualified consensus (both accept or accept with caveat; no unresolved material objection).

| Round | Draft | Sol | Astra | Main issues |
|---|---|---|---|---|
| 1 | 1 | reject 0.94 | reject 0.94 | comparator strength and failure handling; matched versus tuned comparisons; factorial at a common pair; X7 specification; welfare and coalition equations; randomness protocol; inference; cost |
| 2 | 2 | reject 0.96 | reject 0.95 | fixed-attack cross-evaluation; X7 transition order and Sobol; reference menus; seed encoding and coverage range; finality; H4 order; inference levels; cost arithmetic |
| 3 | 3 | reject 0.96 | reject 0.97 | references for B2 and rho = 1; dependency order; coalition membership; Holm versus Bonferroni; coverage tolerance and fixtures; late publication; seed cost |
| 4 | 4 | reject 0.96 | reject 0.96 | admission at 1.5 alpha; calibration selection and mapping; profile count |
| 5 | 5 | reject 0.96 | reject 0.95 | coverage fixture after the second development cut; bootstrap tail count |
| 6 | 6 | **accept 0.96** | **accept 0.96** | none |

Accepted scope (both seats, round 6): Q1 pooled and Q4 per market are confirmatory under conditional empirical admission; Q2 and Q3 are descriptive. The results do not establish general attack resistance, population-wide replication, or the complete amended PASS predicate of the first evaluation. Costs in section 8.2 are estimates; the benchmark decides, and any total above 40 USD needs the author's approval.

## Build plan (`docs/superpowers/plans/2026-10-22-revision-build.md`)

| Round | Sol | Astra | Main issues |
|---|---|---|---|
| 1 | reject 0.96 | reject 0.96 | pacing needs L; independent P and G phases; B3 tie order; oracle accounting; window boundary; public constants; X7 adapters (lambda, 769 controls, incumbents); reference contexts and families; freeze completeness; doubling; inference functions; coverage inputs; anchor binding; H4 loader; cut count; pod arguments |
| 2 | reject 0.95 | reject 0.95 | chained assertion; freeze acceptance; doubling execution; anchor hash; H4 constants; stratified streams; Q2 expectations; task order; command outputs |
| 3 | accept-with-caveat 0.95 | accept-with-caveat 0.94 | fixture missing from the commit step; anchor from the verified attestation (both applied) |

## Build fix pass (`revision-v2`, range 963e04c..HEAD)

| Round | Sol | Astra | Main issues |
|---|---|---|---|
| 1 | request-changes 0.96 | request-changes 0.94 | F4, F8, F9, F11 partly closed: cross and doubling resume, auxiliary resume, nonfinite inputs, constant-sample parity, benchmark order and scope (G1-G8) |
| 2 | request-changes 0.94 | request-changes 0.94 | bank size, extra-seed pricing, reference allocation, derived-record reuse, pooled constants (H1-H5) |
| 3 | request-changes 0.94 | request-changes 0.94 | development reference costs; test strength (I1-I2) |
| 4 | **approve-with-caveat 0.94** | **approve-with-caveat 0.94** | bank test distinctness and shortage (applied) |

## Operations plan (`docs/superpowers/plans/2026-10-25-revision-operations.md`)

| Round | Version | Sol | Astra | Main issues |
|---|---|---|---|---|
| 1 | 1 | reject 0.96 | reject 0.95 | failed validation kept kappa; draw not bound; late publication; tag before proof; H4 custody and per-pod decisions; promotion; costs; verify; report scope; artifact |
| 2 | 2 | reject 0.94 | reject 0.94 | proof binding; producer metadata; branch propagation; reservations; utilisation; verify custody; stop before freeze; Q4 Holm slots |
| 3 | 3 | reject 0.93 | reject 0.92 | tuning logs; promotion fixtures; `answers_at_h`; lowest anchor; verify side effects; frozen cost decision; serial stages |
| 4 | 4 | reject 0.92 | reject 0.94 | combined approval gate; reader test; verify aliases; priority barriers; unequal task durations |
| 5 | 5 | reject 0.93 | reject 0.92 | write guard; reservation test; kappa equality |
| 6 | 6 | reject 0.91 | reject 0.91 | coverage pool size; child processes |
| 7 | 7 | reject 0.89 | reject 0.89 | coverage input identity; permitted git child; reproduction passing case |
| 8 | 8 | reject 0.89 | **accept 0.89** | successful H4 decision case |
| 9 | 9 | **accept 0.90** | **accept 0.89** | none (Sol's first round-9 run hit model capacity and was rerun on the same brief) |
