VERDICT: reject

CORRECTIONS:

1. **Plan §§1,5,7 — Commitment remains inconsistent.** Section 5 stamps the manifest, but §1 passes the plan to `block_draw.py --protocol`. The verifier requires the supplied bytes to match the proof’s digest. Pass the stamped manifest bytes to both `block_draw` and `draw_v2.instances`, then verify every listed file hash. No frozen edit is needed. A valid Bitcoin anchor at A establishes commitment before H. Optional publication does not satisfy round 1’s public-commitment requirement; record publication height when available and preserve `confirmatory=False` otherwise.

2. **Plan §§1,4,5 — Execution corrections are substantially answered.** No identified stage requires a frozen-file edit. Separate directories, `fresh0..5`, runner-up parameters under `C*`, direct stage calls, saved `cfg=`, and a churn-aware continuation adapter are sufficient in principle. Require the continuation gate to use **nonzero churn** and test candidate replay. A zero-churn gate alone cannot expose the original cached-score error. Bind all imported helpers and frozen code to the commitment.

3. **Plan §§2–4 — Estimands are sound; failure rules remain incomplete.** Each winner set can use its own market’s corresponding p=0 menu record and unchanged reference candidate replayed under churn. Continued-search winners are a valid prospective primary choice. Distinguish missing continuation output, which permits a validated frozen fallback, from missing base evaluation, which makes the expectation unscorable. Explicitly stop on round-1 mismatch; do not treat it as an ordinary fallback. Fix continuation order before execution because a cost stop determines which cells receive additional search. State tie handling.

4. **Plan §§2,3,8 — Scoring corrections are mostly answered.** The support criterion is numeric, scorable, and nontrivial. The material companion addresses effect size separately. Specify interval coverage and bootstrap construction; round 1 requested these. State that either zero audit denominator makes that market “not below.” Distinguish “not scorable” from “not met” in §8.

5. **Plan §3, expectation 4 — Risk wording needs qualification.** Probability 0.5 answers the request for a quantitative forecast, but does not establish that the prediction is empirically difficult. Replace “no directional information” with “no direct runner-up churn result.” Existing R3 churn results and comparator mechanics provide indirect information. Keep 0.5 explicitly subjective.

6. **Plan §6; `cost_estimate.py` — Counts and arithmetic check out; scheduling needs correction.** The 66 searches per family, explicit X7 doubling exclusion, continuation slowdown, and flag-share scenarios are coherent. Run D2+H3 before X7-SC: `stage_search` requires its embedded winner. Place gates after their menu/reference dependencies. Include preparation and transfer tails for each pod; apply or justify the omitted churn slowdown in diagnostics.

7. **Plan §5; `lessons.md` — Memory protection remains incomplete.** Validate measured worker limits against each pod’s actual memory limit, with headroom. A fixed count derived on the Mac does not establish safety on the allocated pod.

CONFIDENCE: 0.95.