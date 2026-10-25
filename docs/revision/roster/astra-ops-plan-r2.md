VERDICT: reject

FINDINGS:

References below use **plan** for `docs/superpowers/plans/2026-10-25-revision-operations.md` and **S1–S15** for `docs/revision/roster/sol-ops-plan-r1.md`.

1. **Critical — Task 7, plan:104–107.** The imported draw is still not bound to the registered timestamp proof. Its interface receives the draw and protocol bytes, but no proof. An unrelated valid draw with its `protocol_sha256` replaced can satisfy the listed checks. `scripts/block_draw.py:62–67` requires the proof listing; checking the draw’s asserted digest cannot replace that input. **Repair:** consume the committed upgraded proof, derive its digest and anchor, and compare them with the draw. Check `answers_at_h` agreement too. Test an unrelated draw whose digest field has been rewritten.

2. **Important — Task 4, plan:74–76; Operations 2–7, plan:158–186.** The aggregate budget contract remains incomplete. `cap_for` does not explicitly reserve outstanding allocations. Five parallel calls can each pass against the same remaining balance. The named remainder test would permit this implementation. Also, `choose(timings, rate)` does not specify how benchmark spend and the H4-check pod affect affordability and approval. **Repair:** define atomic reservations, deduct outstanding caps, reconcile actual charges, and make cost selection include spend and overhead. Test concurrent allocations and a development estimate that fits only when benchmark spend is omitted.

3. **Important — Tasks 3–5, plan:65,84–86.** Promotion requires metadata that the producers do not supply. The benchmark writes timings, rate, and `smoke`, without `commit` or `markets` (`scripts/benchmark_v2.py:222`); coverage lacks the common promotion metadata (`scripts/coverage_v2.py:87–91`), and Task 3 does not add it. Valid runs can therefore fail promotion. Admission checks also specify endpoint counts without requiring endpoint identities, results, and agreement with the chosen branch. **Repair:** define producer-specific schemas, add required metadata, and validate the complete coverage evidence. Test unedited producer outputs and wrong-branch or substituted-endpoint records.

4. **Important — Operation 4, plan:168.** The selected branch is passed to pool construction but omitted from local selection and validation. Both default to `three20k` (`scripts/coverage_v2.py:65,82`). A two-market run then requests the absent `dev1` pool. **Repair:** pass the chosen branch explicitly to both commands and promotion. Add an end-to-end test for each reduced branch.

5. **Important — Tasks 8–9, plan:19,116,126,187.** Local verification conflicts with H4 custody. The loaded-decision contract requires a successful bundle load, while local verification and reporting run before H4 release. The existing CLI also writes `salt.hex` before dispatch (`scripts/revision_v2.py:73–76,840`). Patching stage bodies does not detect either action. **Repair:** specify a verification entry point that validates recorded H4 identity without importing the bundle, performs no episodes, and writes nothing. Test the actual CLI with H4 loading, episode execution, and filesystem writes forbidden.

6. **Important — Tasks 8–9, plan:116,126–130.** Reporting a cap stop before freeze remains undefined. Verification first calls `accept`, which raises when no freeze exists (`scripts/revision_v2.py:555–558`); the test deletes an evaluation record but does not cover an unfinished context. Missing-market Q4 handling also leaves room to shorten the Holm family: `sim/decisions_v2.py:54–55` uses the supplied list length. **Repair:** classify an absent freeze as an unavailable context, retain rejection of stale freezes, and define missing-market handling that preserves the six-market correction. Test both cases.

7. **Minor — Task 8, plan:116–117.** Ascending tiers 0–3 conflict with “headline pods run priority 2 work last.” Headline whole-system work is tier 3 (`sim/manifest_v2.py:84–89`). **Repair:** remove the contradictory sentence or specify one consistent order. Test all tiers, including headline dispatch. The accepted complete-freeze ruling remains valid.

8. **Important — Planned tests, plan:57,66,76,107,118,130,139.** Several tests still permit plausible wrong implementations. Serial/parallel equality passes when `workers` is ignored. A per-call cap test misses outstanding allocations. Stage-body patches miss verification side effects. The report tests do not explicitly assert that an `incomplete=True` doubling label leaves decisions unchanged. **Repair:** add worker-dispatch assertions, reservation tests, verification side-effect checks, and a paired report test differing only in the doubling label. Retain the independent numerical oracles and record mutations already specified.

S1: partly closed — null export fixed; coverage evidence checks remain incomplete.  
S2: partly closed — digest comparison added; proof-to-anchor binding remains missing.  
S3: closed — proof precedes the signed tag; evaluation uses a separate checkout (plan:174–175).  
S4: partly closed — custody commit and global decision added; local verification conflicts remain.  
S5: partly closed — staged promotion fixed; producer metadata remains incompatible.  
S6: partly closed — market sharding added; local branch propagation remains missing.  
S7: partly closed — cost model expanded; aggregate allocation remains underspecified.  
S8: partly closed — verification stage added; read-only execution is not secured.  
S9: closed — record validation and tag-based reproduction are specified (plan:116,126,138).  
S10: closed — required report outputs are specified (plan:129).  
S11: partly closed — diagnostic-only doubling ruling accepted; pre-freeze stop handling remains undefined.  
S12: partly closed — complete-freeze ruling accepted; headline ordering conflicts remain.  
S13: closed — explicit artifact assembly and final reproduction added (plan:138,197).  
S14: partly closed — stronger oracles added; listed test gaps remain.  
S15: closed — CLI flag and directory creation specified (plan:42,179).

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, publication services, and execution of future tests. No paid APIs were called. `sealed/` was not read. No files were changed.

CONFIDENCE: 0.94.