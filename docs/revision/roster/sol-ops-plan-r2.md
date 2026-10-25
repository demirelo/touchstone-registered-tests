VERDICT: reject

FINDINGS:

1. **Critical — Task 7, plan:104–107; `scripts/block_draw.py:62–67,86–97,120–121`.** The stated inputs lack the OTS listing required by `check_protocol(ots_info, protocol)`. Comparing the protocol digest with a field in the draw does not bind its anchor to the registered proof. Another valid chain with an edited digest can satisfy the listed checks. **Repair:** consume the upgraded proof; check its digest, attestation height, and Merkle root against the anchor. Test substitution with the digest field corrected.

2. **Important — Tasks 3–5, plan:65,74–85; `scripts/benchmark_v2.py:222–223`; `scripts/coverage_v2.py:86–92`.** Promotion requires `commit` and markets, but benchmark outputs provide neither. Coverage outputs also lack these provenance fields; Task 3 does not add them. Applying the stated checks stops promotion. Skipping them introduces an unstated exception. **Repair:** define metadata and checks for each kind, update both producers, and test promotion from their actual outputs.

3. **Important — Operation 4, plan:168; `scripts/coverage_v2.py:65,82`.** Only pool creation explicitly receives the chosen branch. Local `--select` and `--validate` default to `three20k`. After a development cut, they can request absent `dev1` pools or consume old ones. **Repair:** give complete commands with the chosen `--branch` and `--out` at both stages. Test the full `two20k` path.

4. **Important — Task 4, plan:75–76; Operations 3 and 7, plan:164,186.** The ledger contract does not require cap allocation to reserve funds. With USD 10 remaining, five concurrent requests for a USD 3 estimate can each receive USD 3.75. Each allocation passes the named remainder test; their sum exceeds the cap. **Repair:** reserve caps before launch, subtract active reservations, and release them when actual spend is recorded. Include the H4 decision pod and replacement pods. Test multiple outstanding allocations.

5. **Important — Task 4, plan:74; Operation 2, plan:158; `scripts/benchmark_v2.py:176–190`.** The benchmark still runs serially on the specified 16-vCPU pod. The default utilisation of 0.8 does not establish billed utilisation. Other pod sizes remain unspecified; tuning’s two rechecks cannot fill a large pod. **Repair:** specify pod sizes and measured billing rates, account for idle capacity by phase, and include actual benchmark spend in the cost decision.

6. **Important — Global constraint, plan:19; Task 8, plan:116; Operation 7, plan:187.** A loaded H4 decision requires a successful load, but the local verification step has no exemption. Loading locally conflicts with custody; refusing the load stops verification. **Repair:** define a verification path that checks bundle hashes without importing H4, or perform verification on authorised pods.

7. **Important — Tasks 8–9, plan:116,126; `scripts/revision_v2.py:555–567`.** Verification first calls `accept`. A cap stop during search leaves no freeze, which `accept` rejects before report construction. The report permits missing cells, but does not classify a missing freeze as an unavailable context. The named tests delete evaluation records only after a complete context exists. **Repair:** distinguish absent contexts from stale freezes. Report absent contexts as unanswered without running episodes. Test a stop before freeze.

8. **Important — Task 9, plan:128–130; `sim/decisions_v2.py:51–56`.** Handling missing Q4 markets does not explicitly preserve the six-market Holm family. Passing five available markets to the helper changes the threshold: a smallest calibrated p-value of 0.009 fails with six markets but passes with five. Status-only assertions can miss this error. **Repair:** retain all six slots, conservatively assign missing tests p=1, mark those markets undecided, and assert this numerical boundary.

9. **Important — Task 8, plan:116–118; `sim/manifest_v2.py:84–89`.** Tier order 0→3 conflicts with “headline pods run priority 2 work last.” Tier 3 contains the remaining work. Following the latter instruction places Q3 after lower-priority work. **Repair:** remove that clause and test actual dispatch with both tier-2 and tier-3 jobs.

10. **Important — Task 5, plan:85; `sim/calibration_v2.py:148–154`.** Admission checks specify endpoint count, but do not require endpoint identities, passing bounds, and `admitted` to agree. A coverage record with `admitted=True` and a failing endpoint can pass the stated checks. **Repair:** verify the exact endpoint set and derive admission from its bounds and replication counts. Add an inconsistent-admission mutation.

11. **Important — Planned tests, plan:57,66,76.** `test_parallel_tuning_equals_serial` and `test_pool_by_market_and_workers_equals_serial` can pass when `--workers` is ignored. `test_cap_for_never_exceeds_the_remainder` can pass without reservations. **Repair:** assert submitted work, worker counts, chunk coverage, and aggregate allocations. The numerical report oracles improve round 1, but these tests do not enforce their claimed behaviour.

S1: partly closed.  
S2: partly closed.  
S3: closed.  
S4: partly closed.  
S5: closed.  
S6: partly closed.  
S7: partly closed.  
S8: closed.  
S9: closed.  
S10: closed.  
S11: partly closed. The diagnostic ruling is accepted: doubling does not change the frozen estimand; the partial-run gap remains.  
S12: partly closed. The complete-freeze ruling remains accepted: priority cannot waive frozen references and banks.  
S13: closed.  
S14: partly closed.  
S15: closed.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and tests not executed. No paid APIs were called. Neither `sealed/` nor H4 bundle contents were read.

CONFIDENCE: 0.94.