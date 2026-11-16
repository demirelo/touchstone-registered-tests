VERDICT: reject

CORRECTIONS:

1. **Plan §§1,5 — Round-1 execution corrections are answered correctly.** No stage needs a frozen-file edit. New `docs/` drivers can retain `fresh0..5`, isolate outputs, use the `C*` label for C-thr(12), calibrate once on the pod, and pass saved `cfg=` values. The proposed continuation adapter addresses the direct-import reference error. Require its tests before acceptance.

2. **Plan §§1,5,7 — Fix the commitment mismatch.** Section 1 passes the plan to `block_draw.py --protocol`; section 5 stamps a separate manifest. The frozen reader requires the supplied bytes to match the proof’s digest. Pass the stamped manifest to both the block reader and `draw_v2.instances`, then verify every listed file hash. Bind the frozen code revision and imported helpers. Record publication height, not only push time. A private stamp can prove prior existence, but does not provide the public, uniquely identified commitment requested in round 1; distinguish these claims explicitly.

3. **Plan §§2,4,5 — Complete winner and failure rules.** The paired estimand is valid, including the p = 0 menu record and unchanged reference candidate replayed under churn. Continued-search winners can be primary because this choice precedes the draw. However, round-1 mismatch handling remains unspecified: require a stop and prohibit substitution. Distinguish missing continuation records, which permit a validated frozen fallback, from missing base evaluation or doubling records, which prevent scoring. State the inherited training-score tie rule. Confirm that reselected references affect diagnostics and stopping only.

4. **Plan §§2,3,8 — Finish scoring specifications.** Set interval coverage and paired bootstrap sampling explicitly. The descriptive support criterion is numeric and nontrivial; the −0.05 companion measures size separately. Restrict replication wording to that descriptive criterion when the material companion fails. Expectation 4’s probability of 0.5 answers round 1, but remains a subjective forecast. Replace “no directional information” with “no direct runner-up churn observations”: related comparator results provide indirect information.

5. **`cost_estimate.py`; Plan §§5,6 — Correct the stage schedule.** The 66 searches per family correctly include the ten-rule menus plus runner-up. `x7_cell` includes its larger search budget; explicit exclusion of X7 menu doubling resolves that question. However, X7 searches require D2+H3 records first, and gates need menu/reference inputs. Correct their schedule order. Apply churn slowdown to churn diagnostics. Add preparation, transfer, environment checks, and billing tails for each pod. Keep core-hour projections separate from actual pod billing.

6. **Plan §§5,6; `lessons.md` — Fix operational choices before stamping.** Specify deterministic cell priority under a cost stop, pod-memory admission checks, and validated reuse of saved configurations across pods. These controls prevent resource limits and execution order from silently determining the primary winner mixture.

CONFIDENCE: 0.95.