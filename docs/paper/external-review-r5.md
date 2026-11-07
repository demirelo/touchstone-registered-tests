# External review, round 5 (condensed record of the findings; the author pasted the full review in the session on 2026-11-07)

**Verdict:** AAMAS main track 2/5 (reject), WEIS 3/5 (borderline), EC 1/5 (strong reject); review confidence 4, 3, 4.
Most important change: resolve the discrepancy between the registered p-value arithmetic and the printed numbers.
Forecasts: AAMAS 25% (32% after text changes), WEIS 50% (60%), EC 4% (6%).

Follow-through on round 4: most of the 20 sentence findings resolved; partly resolved: 5 (coalition caption), 16
("whole neighbourhood" sentence), 19 (conclusion's lottery sentence), 20 (artifact, availability of posthoc inputs).

## Audit of the new analyses
- Q1 decomposition: correct (attacked share 91.0% D2+H3, 92.3% X7-SC); pooled only (fresh4 reference share 19.3% and 26.8%).
- Welfare lottery: construction valid; weight and companion selected on evaluation outcomes; training feasibility
  unreported; certificate near its boundary; H4 changes family access. Public-family mixtures (D2+H3 companion):
  R3 weight 0.339, gain 0.000252853, efficiency 0.944510; C* weight 0.480, gain 0.000297150, efficiency 0.921852.
  W0 gain vectors and H4 seed-level vectors are not in the package, so the bound cannot be reproduced.
- Q4 diagnostics: decompositions correct; no causal explanation; spending denominator and "served share" unclear.
- Stability: summaries correct; maximum cell-mean movement 0.00737258; fresh4 0.18339 -> 0.17605; the Q4 export lacks
  per-market quantities.

## Findings, ranked
1. **p-value labels conflict with the registered arithmetic (major).** Table 8 calls its p-values calibrated, but prints
   0.0001; with B = 9999 and kappa = 0.25 the smallest calibrated value is 0.0004. Table 5 calls 0.0004 a Holm p-value;
   if both inputs are 0.0004 the Holm-adjusted values are 0.0008. Trace the fields to the frozen code; report raw,
   calibrated, market maximum, Holm-adjusted, and decisions; disclose any implementation difference. Under the obvious
   correction the Q4 Holm-adjusted values are 0.0024 and all decisions stand.
2. **Lottery still asserts established non-negative mean gain (major).** Replace the abstract clause with an estimate
   (0.00037, 0.932) and "population profitability is not established"; replace the sentence that a mean constraint
   makes any lottery feasible; give estimates instead of "keeps the mean gain non-negative"; replace "depends on
   excluding randomised policies" in introduction and conclusion; Table 11 should print gains and bounds, say
   "unadjusted for selection" and "largest tested weight".
3. **Extreme secondary intervals (important).** fresh1 fixed-reference contrasts P, PG, P|G=0 (six contrasts, both
   families, 12 entries) have intervals near +-7e5 to 1.4e6. Disclose, keep the frozen outputs, diagnose (standard
   errors, degenerate resamples); label any sensitivity interval separately.
4. **Provenance statements (definite).** Section 9's "All values below come from the report", Table 3's "every
   extremum selected on training data", and the availability sentence are false after the posthoc additions;
   replacements given.
5. **Coverage sentence too categorical.** Make Holm's control conditional on valid calibrated component p-values;
   replacement given.
6. **Coalition table caption.** The two columns can describe different selected policies.
7. **Q4 diagnostic units and scope.** Spending near 0.05 of realised S* does not establish budget exhaustion; define
   the service denominator; replace "does not carry over to the whole neighbourhood" with "does not establish that
   margin across all six sampled fresh markets".
8. **Stability documentation.** The addendum's "at most 0.007" should be 0.0074; add a full Q4 stability table.

Also noted: the ledger shows after-lock discretion (no evidence of outcome-driven retry selection); the cap increase is
a deviation although spending stayed below 40 USD; H4 is a defense-aware extension of D2+H3, not independent
replication; keep the addendum's dependency paths conservative.

## Remaining changes, ranked (all 0 USD)
1. Inference audit export (raw, calibrated, Holm-adjusted, decisions). 2. Repair every lottery sentence and the
provenance statements. 3. Make the mixture reproducible (per-seed components, script, training feasibility, public-family
mixtures). 4. Weight-sensitivity analysis; optional joint bounds over a finite component library. 5. Diagnose the extreme
intervals. 6. Full Q4 stability export; candidate-level reference provenance. 7. Local corrections and sharper
contribution framing. 8. Optional: compare the training-selected bank envelope with each rule's own searched attack.
No new simulation recommended.
