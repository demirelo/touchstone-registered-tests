VERDICT: reject

CORRECTIONS:

1. **§§1,5,7 — Execution.** No stage requires a frozen-file edit. However, `draw_v2.py --instances` calibrates by default. Use a `docs/` wrapper calling `instances(..., calibrate=False)`, then calibrate once on the pod and pass saved `cfg=` values everywhere. Install and verify the draw-derived identity salt. Run C-thr under the existing `C*` label in separate directories, as Run A does; a literal new rule label will fail.

2. **§4; `convergence_v2.run_cell` — Blocking reference error.** This function imports `sim.reference.select_reference` directly. `churn_v2.install()` patches only `R.select_reference`. Thus continuation can reuse no-churn candidate scores, corrupting reference changes, stopping decisions, and round-1 agreement. An isolated synthetic check reproduced this reuse. Add a churn-aware continuation adapter under `docs/`, with tests that require candidate replay and agreement with this run’s doubling records.

3. **§§1,5,7 — Prospective commitment.** Stamping the plan alone does not bind its companion code. Include hashes of analysis code, tests, drivers, parameters, and dependencies in the stamped plan or a manifest it hashes. Publish that commitment before H. Preserve the upgraded proof, lowest-valid-anchor evidence, draw record, and publication evidence; prohibit outcome-dependent restamping or redraws. The block reader accepts Markdown bytes without a frozen edit.

4. **§§2,4 — Winner definition.** Continued-search winners can be primary if fixed prospectively. Specify whether unflagged cells use base or doubled winners; define tie handling, round-cap results, cost stops, mismatches, and missing records. Run B’s first round repeats doubling; three rounds are not three additional rounds after doubling. The paired estimand is valid when each version uses its own market’s corresponding p=0 menu-search baseline and unchanged reference candidate replayed at each rate. Report attack and reference terms separately.

5. **§3 — Scoring and risk.** The mean-negative/5-of-6 criterion is numeric and nontrivial, but permits arbitrarily small deterioration and establishes neither material size nor significance. Restrict the claim accordingly or fix a minimum effect. Expectation 4 is novel; absence of earlier churn runs does not establish that success would be surprising. Record its quantitative expectation before drawing. Define unavailable audit-share denominators and incomplete-data scoring.

6. **§6; `cost_estimate.py` — Cost.** The 60 paired-family menu searches plus six runner-up pairs are structured correctly. Add calibration, gates, p=0/final-winner diagnostics, and explicit X7 menu-check inclusion or exclusion. Apply churn slowdown to continuation; assess flag shares above 30%. Model stage dependencies, serial work, memory-limited workers, and billing tails. Core-hours/16 is not a billed-time estimate. Reserve against the selected stop cap’s watchdog bound.

7. **§5; `lessons.md` — Operational guards.** Require longest-run memory measurements, persistent worker limits, worker-side atomic saves, validated resume records, and failure-path tests. Compare ordinary p=0 execution with injected churn-zero execution; repeating one path only proves repeatability.

8. **§8 — Interpretation.** Failure of expectation 4 cannot establish that robustness belongs specifically to C*’s design. Report failure without causal attribution. New draws extend evidence within the same generator neighbourhood, not beyond it.

CONFIDENCE: 0.96.