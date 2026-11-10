VERDICT: reject

CORRECTIONS:

1. **§5; convergence_v2.py:160.** Pin the search settings and reject `TOUCHSTONE_LOCKED` overrides. Compare each job’s budget with its frozen search record. The current checks cover code, configurations, and reference pairing, but omit the search budget. All 14 reconstructed jobs pass pairing; all 111 dependency hashes match.

2. **§5; convergence_v2.py:171.** Validate existing outputs before reuse. File existence alone skips computation, so a smoke result or a result with fewer rounds can enter production analysis. Require matching provenance, input hashes, settings, seeds, and round limits. Restrict substitutions to the validated run manifest.

3. **§2; convergence_v2.py:169.** Make round-one reproduction a stopping gate. The driver checks agreement only after completing the cell and continues despite disagreement. Compare before round two; stop on mismatch. Before pod execution, save full-budget reproduction evidence for D2+H3 and X7-SC, including held-out winners and gains.

4. **§5; reset_followup_v2.py:118,256.** Record the correct driver identity and deviations. The imported inventory helper hashes the reset driver and lists reset-specific deviations. Include hashes for `convergence_v2.py`, `common.py`, imported helpers, the frozen plan, and the report that selects cells.

5. **§3; common.py:30.** Add per-market intervals or explicitly limit the interval promise to pooled estimates. The function currently returns market point estimates and one pooled interval. State that nominal intervals condition on these six markets and selected policies; they exclude search uncertainty and market sampling uncertainty.

6. **§§1–4.** Define the result as “passed the registered incremental check within three rounds.” This addresses flagged-search sensitivity, not optimality or a bound on remaining search error. Preserve the stated coalition deferral and identify fresh factorial checks as unresolved. Clarify that expectations precede new continuation outcomes; the registered doubling outcomes are already known.

7. **§§6–7.** Specify a dollar cap, budget reservation, failed-attempt accounting, and a timed shutdown rule before pod creation. The benchmark calculation reproduces 16.88 core-hours and USD 1.82, but this estimate is not a spending cap.

CONFIDENCE: 0.96.