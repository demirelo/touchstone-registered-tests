VERDICT: reject

FINDINGS:

1. **Important — Task 2, plan:56–57; `scripts/tune_v2.py:83–98`; `scripts/coverage_v2.py:30–45`.** Market tasks for the same configuration write the same log filename. The second task overwrites the first market’s `detail`; coverage then cannot find its fixture inputs. An in-memory check confirmed this overwrite. Score equality and executor-submission assertions can both pass. **Repair:** merge market details into one configuration log before promotion. Test `fixture_inputs` for every chosen market using parallel tuning outputs.

2. **Important — Task 5, plan:85–86; `scripts/tune_v2.py:102–105`.** The passing promotion test uses smoke outputs and changes only `smoke` to false. Their budgets remain `(1,16,1,2)`, which the required budget checks must reject. Thus the test either fails against correct validation or encourages a validation exception. **Repair:** call producers with production arguments and stub the expensive work. Preserve production budgets and replication metadata; use smoke outputs as refusal cases.

3. **Important — Task 7, plan:104; `scripts/block_draw.py:120–121`.** The declared draw input contains `answers`; the built reader produces `answers_at_h`. Reading the declared key stops Operation 6; defaulting it away can omit explorer agreement. The named synthetic tests need not detect this mismatch. **Repair:** use `answers_at_h` and add a passing test that consumes the reader’s unchanged output.

4. **Important — Task 7, plan:106–107; spec:305–307.** Requiring A to be *one of* the proof’s attestations permits a later valid attestation and therefore another H and draw. Registration requires the lowest anchor. Testing an absent anchor does not reject a later attested anchor. **Repair:** enforce the registered anchor-selection rule. Add a proof with two valid attestations and reject a draw based on the later one.

5. **Important — Task 8, plan:116–118; `scripts/revision_v2.py:31,86–95,145,179–182`; `sim/instances.py:72–73`.** The verification test still permits side effects outside stage bodies. Catalogue construction can call calibration, which runs `first_best_episode` (`sim/calibrate.py:44–47`). Patching `h4_loader.load` also misses the runner’s imported `load_h4` alias. Without salt installation, existing provenance construction reads the ambient salt. **Repair:** build verification expectations from recorded configurations and the root-derived salt hash. Test a fresh CLI process with calibration, the actual loader alias, episode execution, and filesystem writes forbidden.

6. **Important — Tasks 4 and 6, plan:74,94; Operations 2–5, plan:159,164,172.** `choose` now depends on a changing ledger, but lock validation must reproduce its earlier branch and cuts. No remaining-work calculation or frozen decision input is specified. An implementation that adds recorded tuning spend to the full development forecast can select a reduced branch—or stop—after that tuning has already completed. The benchmark-only boundary test misses this case. **Repair:** separate actual spend from remaining work; freeze and hash the approved decision inputs. Test benchmark decision → completed development → lock validation.

7. **Important — Task 4, plan:74–76; `scripts/revision_v2.py:753–762,785–800`.** Task-count utilisation can assume parallel execution for reference and cross work that the runner executes serially. Task 8 specifies priority changes but does not require these loops to become parallel. Estimates can therefore understate billed time and select insufficient cuts. The six-task and 32-task utilisation tests do not cover this mismatch. **Repair:** price the actual dispatch waves, including serial stages, or explicitly parallelise them. Test billed time against a recorded dispatch schedule.

Sol round-2 finding 1: closed — proof-to-anchor binding is specified; finding 4 is a separate anchor-selection gap.  
Sol round-2 finding 2: partly closed — producer metadata is specified; the required passing integration test remains invalid.  
Sol round-2 finding 3: closed.  
Sol round-2 finding 4: closed — aggregate reservations are explicit.  
Sol round-2 finding 5: partly closed — serial-stage billing remains unresolved.  
Sol round-2 finding 6: closed — the verification exemption is explicit; finding 5 concerns its implementation and test coverage.  
Sol round-2 finding 7: closed.  
Sol round-2 finding 8: closed — six slots and the numerical boundary test are explicit.  
Sol round-2 finding 9: closed — ascending dispatch is consistent; the complete-freeze ruling remains accepted.  
Sol round-2 finding 10: closed — endpoint identities, bounds, and admission are checked.  
Sol round-2 finding 11: partly closed — worker and reservation assertions improve; findings 1, 2, and 5 remain. The diagnostic-only doubling ruling and paired-label test are accepted.

Sol round-1 items previously partly closed: S1 closed; S2 closed; S4 closed; S6 partly closed (finding 1); S7 partly closed (findings 6–7); S11 closed; S12 closed; S14 partly closed (test gaps above).

Astra round-2 cross-check: A1 partly closed (finding 3); A2 partly closed (finding 6); A3 partly closed (finding 2); A4 closed; A5 partly closed (finding 5); A6 closed; A7 closed; A8 partly closed.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of future tests. No paid APIs were called. Neither sealed bundle was read. No files were changed. Verification included source inspection and in-memory probes.

CONFIDENCE: 0.93.