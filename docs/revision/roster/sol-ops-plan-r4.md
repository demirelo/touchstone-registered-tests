VERDICT: reject

FINDINGS:

1. **Important — Plan Task 4:74–76; Operation 2:159; spec:361–362.** The fixed cost decision has no later total-spend approval gate. A forecast of USD 39 needs no approval, but reservations with 25% headroom can permit expenditure above USD 40 while both phase caps remain satisfied. Later steps explicitly check only the remaining phase budget. **Repair:** enforce a combined USD 40 limit on spent funds plus outstanding reservations until written approval raises that limit. Add a test where each phase fits its cap but their combined allocation requires approval. Keep the registered branch and cuts fixed.

2. **Important — Plan Task 7:104–107; `scripts/block_draw.py:120–121,135–141`.** `test_unchanged_reader_output_is_accepted` consumes unchanged output from `read_final` and `anchor`. That output lacks `protocol_sha256`; only `main` adds it. An in-memory check confirmed this. A correct consumer therefore rejects the specified passing fixture. **Repair:** test the JSON produced by `main`, with explorer requests and the OTS subprocess replaced by test substitutes. Keep the missing-digest record as a refusal case.

3. **Important — Plan Task 8:116–118; `sim/instances.py:13,72–73`; `sim/calibrate.py:44–47`; `sim/rng.py:59–67`.** The verification test still permits prohibited work. Patching `sim.calibrate.calibrate` leaves the imported `sim.instances.calibrate` alias active; an in-memory check confirmed this. Unsetting `TOUCHSTONE_IDENTITY_SALT` also permits reading the default salt file. Thus verification can recalibrate or read ambient salt while passing the named checks. **Repair:** forbid the actual calibration alias, `first_best_episode`, and the runner’s salt-reader alias. Test these prohibitions on a fresh-market context with calibration caches empty.

4. **Important — Plan Task 8:116–118; `scripts/revision_v2.py:734–739`.** The reference-pool test requires one `_pool` call containing every menu, while the dispatch contract requires separate priority waves. A wrong implementation can submit all menus in sorted order and pass the recording test, yet start a lower-priority menu while higher-priority work remains unfinished. **Repair:** assert the priority barriers during execution. Either require one pool call per wave or test barriers inside `_pool`. Check that `dispatch_plan` and billed waves match that execution.

Sol round-3 finding 1: **closed** — parent-owned, complete market logs and fixture extraction are specified (plan:56–57).  
Sol round-3 finding 2: **closed** — production arguments with expensive calls replaced by test substitutes replace relabelled smoke outputs (plan:85–86).  
Sol round-3 finding 3: **partly closed** — `answers_at_h` is correct; the passing producer test remains invalid (finding 2).  
Sol round-3 finding 4: **closed** — lowest-valid-anchor selection and later-anchor refusal are explicit (plan:106–107).  
Sol round-3 finding 5: **partly closed** — recorded verification inputs are specified, but the test misses active aliases and default salt reads (finding 3).  
Sol round-3 finding 6: **closed** — the decision and ledger snapshot are fixed; later ledger changes occur outside the clean evaluation checkout (plan:20,74,94–96).  
Sol round-3 finding 7: **closed** — reference and cross work use the pool, and pricing consumes dispatch waves (plan:74,116); finding 4 concerns priority enforcement.

Astra round-3 finding 1: **closed** (plan:65,84).  
Astra round-3 finding 2: **closed** (plan:56–57).  
Astra round-3 finding 3: **closed** (plan:74,116).  
Astra round-3 finding 4: **closed** (plan:20,74,94–96).  
Astra round-3 finding 5: **partly closed** — anchor and field requirements are fixed; the producer test needs repair.  
Astra round-3 finding 6: **closed** (plan:85–86).  
Astra round-3 finding 7: **closed** — a concurrent reservation test is specified (plan:76).

Previously partial Sol round-1 findings: **S1 closed; S2 closed; S4 closed; S6 closed; S7 partly closed** (total approval gap); **S11 closed; S12 partly closed** (priority test gap); **S14 partly closed** (findings 2–4).

Both rulings remain accepted: search-incomplete doubling labels do not change decisions (plan:128–130); priority cannot waive the complete freeze (plan:117; spec:249–253). The paired doubling-label test directly tests its ruling. The complete-freeze requirement remains intact.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of future tests. Review used source inspection and two in-memory checks. No paid APIs were called, no files were changed, and `sealed/` was not read.

CONFIDENCE: 0.92.