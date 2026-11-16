VERDICT: reject

CORRECTIONS:

1. **Plan §§1,5 — Execution.** No stage requires a frozen-file edit. Use new drivers under `docs/`. Keep `fresh0..5` internally. Run C-thr(12) under the `C*` label with runner-up parameters in a separate directory. Call `draw_v2.instances(..., calibrate=False)` before pod calibration; the CLI currently calibrates by default. The manifest module is `sim/manifest_v2.py`.

2. **Plan §§1,5,7 — Commitment.** Stamping the plan does not bind the analysis files committed beside it. Put analysis, tests, drivers and dependency hashes in the stamped plan. Publish that package before H. Record the upgraded proof, lowest valid Bitcoin attestation A, and publication height below H. Fix one draw; prohibit restamping or replacing markets after inspection. The block reader accepts Markdown bytes without a frozen edit.

3. **Plan §4; `convergence_v2.run_cell` — Churn references.** The function imports `select_reference` directly from `sim.reference`, bypassing `churn_v2.install`’s replacement of `R.select_reference`. Frozen-menu candidates can therefore retain no-churn scores. An isolated check confirmed cached scores prevent replay. Adapt the continuation path under `docs/` to clear those scores, install churn in every worker, and compare round 1 with this run’s churn doubling record.

4. **Plan §§2,4 — Winners and baseline.** Continued-search winners can be primary because that choice precedes the draw. Specify whether unflagged cells retain frozen or doubled winners. State that Run B’s three rounds include recomputation of doubling, rather than three additional rounds. Define handling of cost stops, missing records and nonfinite values. Explicitly define normalized gain, reuse the p=0 menu search record, and retain each rule’s selected no-churn reference under churn. Report attack and reference terms separately.

5. **Plan §§2,3 — Scoring.** The support criterion is numeric, scorable and non-tautological, but permits arbitrarily small changes. Label it descriptive; specify interval coverage and uncertainty scope. Expectation 4 is new, but “never run” alone does not establish substantial predictive risk. Record a prospective probability or remove “Risky.” Define expectation 5’s audit denominator, seed aggregation and zero-job handling.

6. **Plan §5; `lessons.md` — Gates.** Repeating one p=0 cell proves repeatability only. Require ordinary-versus-injected p=0 equivalence and churn continuation-versus-doubling equivalence. Add longest-path memory measurements, worker limits, atomic cell saves and tested resume/error handling.

7. **Plan §6; `cost_estimate.py` — Cost.** The 10-rule, two-family menu structure plus runner-up searches is correct; `x7_cell` already includes its larger budget. Add calibration, gates, p=0/final-winner diagnostics, and churn slowdown for continuation. Resolve whether menu X7-SC searches receive doubling checks; price those with `doubling_x7`. Replace ideal core-hours/16 with stage scheduling at memory-safe worker counts and billed pod pricing. A 30% flag share is an assumption. Derive watchdog exposure from the approved stop cap.

8. **Plan §8 — Interpretation.** Delete the causal conclusion from expectation 4 failing. Report “runner-up deterioration not supported.” Restrict successful replication claims to the generator’s market neighbourhood and prescribed finite searches.

CONFIDENCE: 0.96.