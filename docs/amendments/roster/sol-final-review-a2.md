**FINDINGS**

1. **Important — [scripts/sweep.py:419](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:419): The H3 check filename differs from the filename required by the falsification harness.**  
   A completed sweep writes `checks/proposed_D2+H3_beta0.05_rho0.2_median_h3.json`; `_required_records` and F5 require the corresponding `_controls.json`. Thus, the documented sequence stops at the inventory check before F1. I confirmed both names in an in-memory test. **Fix:** use one shared check-record name in the producer and consumer, and test the sweep-to-falsification path.

2. **Important — [scripts/sweep.py:93](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:93): Ablation cells instantiate the ordinary rule without replacing its enforcement.**  
   `make_cell` uses the same factory for development and ablation cells. For proposed `L=3` or `L=20`, the ablation therefore retains that ban length instead of B2’s registered `L=10`. I confirmed this with a synthetic factory. The six records would report original-rule results as enforcement-matched ablations. **Fix:** wrap ablation factories with `EnforcementAblation` and the checked B2 enforcer for every search, bank, reference, evaluation, and check run.

3. **Important — [scripts/falsify_proposed.py:234](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:234): F4/F5 do not verify that their records match the current parameters, seeds, budget, or bank.**  
   After a parameter change or partial rerun, old evaluation rows and an old doubling result can pass while `f5_bank` records a different `bank.json`. The harness reads that document directly, without `load_bank_doc`. An in-memory test accepted stale smoke records and even an invalid bank document as F4/F5 PASS. **Fix:** rebuild and check the expected jobs, require the exact dev-val seeds and finite values, validate the bank and sources, and bind evaluation/check records to their reference and bank hashes before recording `f5_bank`.

4. **Important — [sim/claimcheck.py:350](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/claimcheck.py:350): Bank commitment verification accepts missing H3 reference records because it uses existing references as its checklist.**  
   With valid frozen bank A supplied, remove the final H3 references and retain evaluation records produced under bank B. This verifier performs no H3 comparisons; `verify_h3_records` separately checks evaluation metadata but requires no reference. I confirmed that missing all final bank/reference records returns `[]`. **Fix:** derive required H3 records from the expected manifest, refuse each missing bank/reference record, and bind each evaluation to its checked reference.

5. **Important — [scripts/falsify_proposed.py:135](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:135): The inventory check covers only the F4/F5 input subset, rather than the complete registered sweep.**  
   A directory can lack all rho-sweep results, all ablation results, the all-deviators output, and most development cells, yet pass this check. It also does not require the source, bank, or reference inventory. This defeats A6’s explicit completeness requirement. **Fix:** validate the complete output inventory for the documented sections and all four rules before reading result values, including the entries inside `all_deviators.json`.

6. **Minor — [tests/test_proposed.py:23](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/tests/test_proposed.py:23): The B-allocation contract tests use substitute prices instead of the registered B2 prices.**  
   The fixtures use `(0.25, 0.40, 0.55)`; the registered values are approximately `(0.1868882, 0.3737764, 0.5339663)`. A rule that ignores supplied prices and hardcodes the fixture values could pass. Running both B2 configurations on fixture seed 0 produced different assignments and payments. **Fix:** hash-check and load the registered price triple, use it in the equivalence test and harness, and assert the exact stored values.

7. **Minor — [sim/manifest.py:116](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/manifest.py:116): The proposed manifest still violates A1’s section and availability contract.**  
   Filtering `section == "all_deviators"` finds no proposed entry because its section remains `all_deviators_post_lock`. Also, the new executable cells are appended unconditionally: with the module absent, enumeration still lists 16 proposed development cells. The dispatcher workaround handles the alternate section, but the required manifest interface remains wrong. **Fix:** use section `all_deviators`, retain `post_lock=True`, and apply the required availability guard to executable proposed entries.

8. **Minor — [sim/bank.py:54](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/bank.py:54): D2 corners do not pass through the registered ordered embedding sequence with suffixed origins.**  
   For an empty bank, the expected first four `(x, clip)` pairs are `(0,0), (1,0), (0,1), (1,1)` with `corner|x=…` origins. Actual output is `(0,0), (0,1), (1,0), (1,1)`, all labelled `corner`. The member set is complete, but order and provenance differ from A2. **Fix:** embed the complete D2-compatible sequence first, then append and deduplicate H3 corners.

9. **Minor — [scripts/falsify_proposed.py:69](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:69): F3 reports observed lost capacity without its required Gaussian expectation.**  
   Supplying capacities produces `observed_lost_capacity`, but only unweighted `expected_lost_rounds`. The report therefore omits the specified capacity comparison. **Fix:** also accumulate `pb * min(L, remaining) * capacity[i]` and report that expected capacity.

**DECLINED TO JUDGE**

- Phase B rule correctness and actual F1–F5 outcomes: the rule module does not exist.
- The exact separate-directory heldout integration test could not run because the sandbox blocked temporary files. Nineteen unit checks passed with memory capture and optional plotting disabled; one skipped and two were deselected.
- Signed-tag publication and timestamp validity were not assessed. All 11 artifact hashes in the amendment note matched; `locked.yaml` and those artifacts are absent from the tag-to-head change list.
- The sealed bundle remained unread. No paid API ran.

**VERDICT: request-changes**  
**CONFIDENCE: 0.97**
