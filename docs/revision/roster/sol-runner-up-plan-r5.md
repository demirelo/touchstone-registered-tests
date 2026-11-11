VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `docs/revision/followup2/guards.py:195`.** Round-4 evidence validation remains incomplete. In-memory probes accepted wrong evaluation provenance, wrong doubling provenance/dependencies, and a reproduction directory missing all 21 copied inputs, with matching inventories and successful recomputed comparisons. Require every copied input, its expected hash, valid freeze metadata, and correct supporting-record stages, provenance, dependency sets, and dependency hashes. Add refusal tests using the real comparison functions.

2. **Block pod — §§5–6; `results/pods/reset_pod.sh:84`, `:126`; `runnerup_v2.py:359`.** Apply cumulative admission checks before the reproduction gate and carry prior-launch spending into launcher deadlines. The template resets deadlines each launch and runs reproduction before the runner-up driver checks spending. With USD 2.90 previously spent, another USD 0.34 gate can start before refusal. Test the adapted launcher’s attempts/ledger transfer, allocation timestamp, price, stop handling, retrieval, and verified deletion.

3. **§5; `docs/revision/followup2/guards.py:115`, `:162`; plan line 134.** Complete attempts validation. Probes accepted reverse-ordered events, two open pods, and a NaN timestamp; paid accounting discards the open-pod list. Require finite ordered timestamps and exactly one current open attempt consistent with the allocation time. Remove the obsolete four-field format and nonexistent `prior_from_attempts` reference.

4. **§5; `scripts/budget_v2.py:99`.** Specify the exact reservation command. Passing 3.00 as the wrapper’s estimate reserves USD 3.75 because it adds 25%. Use an input that grants USD 3.00 and verify the returned grant. Benchmark arithmetic otherwise reproduces: 17.65 core-hours, USD 1.99 billed estimate.

5. **§2 validation.** Both Run A Mac gates now pass current-code validation and recomputed comparisons. Run B’s available gates have stale driver and `guards.py` bindings; refresh them before Run B. Forty read-only test cases passed. The full 78-test suite and smoke execution remain required before launch.

6. **none — §§1, 3–4 and remaining round-4 corrections.** The estimand answers sensitivity to this development-selected alternative. Matched base/doubled contrasts, advance expectations, nominal interval limits, and deferrals are appropriate. All 12 specification, pairing, budget, and configuration checks passed; all 108 bank hashes matched. STOP/deadline checks now cover internal stages.

CONFIDENCE: 0.98.