**FINDINGS**

1. **Important — [scripts/falsify_proposed.py:137](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:137): The harness requires an H3 checks filename that the sweep never writes.**  
   **Failure:** A completed sweep writes `checks/proposed_D2+H3_beta0.05_rho0.2_median_h3.json`, because the checks stage retains the source job’s name. The harness requires `..._median_controls.json` here and at line 235. Thus, the prescribed sweep → falsify sequence stops at inventory validation before F1–F5. I verified both names from the manifest and dispatch code.  
   **Fix:** Use one shared mapping from control cells to stored checks records. Add a test that passes actual sweep output to the harness without renaming files.

2. **Important — [scripts/falsify_proposed.py:225](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:225): F4/F5 accept unchecked result records and can commit a bank that did not produce those results.**  
   **Failure:** Keep evaluation/checks files from an earlier configuration or smoke run, then replace `bank.json` with a rebuilt bank. The harness reads only the rows and doubling value, without checking parameters, configuration, budget, smoke status, namespace, or expected seeds. Lines 237–246 then record the current bank as `f5_bank`, without validating its sources or connecting it to those results. A probe confirmed that two paired observations outside dev-val can satisfy both numerical gates.  
   **Fix:** Validate each complete record against its expected job and exact seed list. Preserve and check bank/reference identities in evaluation and checks records. Use `load_bank_doc` and verify the complete chain before writing `f5_bank`.

3. **Important — [sim/claimcheck.py:345](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/claimcheck.py:345): Final bank verification can accept H3 evaluation results without evidence that they used the frozen bank.**  
   **Failure:** Retain final H3 evaluation records from bank A and remove their bank/reference records. The verifier iterates only over existing reference records, so it returns no problems. It also accepts evaluation records from A alongside matching bank/reference records from B: it never reads evaluation records. Both cases returned `[]` in in-memory probes. Source-file existence and hashes are also not checked here.  
   **Fix:** Derive the required H3 record set from expected jobs, require every intermediate record, and verify the evaluation-to-reference-to-bank chain. Reuse the bank source validator to reject changed or missing sources.

4. **Important — [scripts/sweep.py:93](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:93): The required ablation cells execute the ordinary proposed rule instead of the registered enforcement ablation.**  
   **Failure:** With proposed `L=3` and locked B2 `L=10`, an ablation cell still constructs `make_rule("proposed", params)`. Its failed audit therefore produces a three-round ban. The existing `EnforcementAblation` adapter is never applied. A synthetic factory probe confirmed this path. The resulting ablation table cannot support the interpretation required by spec §8.  
   **Fix:** Construct ablation cells with the proposed allocation, prices, audit selection, and tolerance, wrapped with B2’s locked enforcement. Use that factory consistently for search, bank, reference, and evaluation.

5. **Important — [scripts/falsify_proposed.py:130](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:130): The inventory check covers only F4/F5 inputs, not the complete sweep required by A6.**  
   **Failure:** A directory containing the 15 selected evaluation files and one checks file passes this check even if all rho-sweep, ablation, and all-deviators outputs are absent. Missing development cells can also leave required bank sources absent. This permits an incomplete run to proceed toward freeze despite the material requirement to verify all registered workloads.  
   **Fix:** Derive the complete expected output inventory from the prescribed manifest sections and rules. Check aggregate all-deviators contents and the expected bank source set before reading result values.

6. **Important — [tests/test_proposed.py:71](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/tests/test_proposed.py:71): The T2 contract test does not detect omitted ratio updates after each selection.**  
   **Failure:** I executed the existing test against a selector that sorts the initial ratios once and never updates them; every assertion passed. Its interleaved keys already produce the expected order. With the same job ownership and keys `[0.1, 0.3, 0.2, 0.4]`, that incorrect selector returns `[0, 2]`; registered dynamic T2 must return `[0, 1]`. Thus, the frozen test can certify the exact implementation error rejected during plan review.  
   **Fix:** Add a case where the two smallest keys belong to one identity, so the second selection must change because of the updated ratio. Retain the input-mutation assertion.

**DECLINED TO JUDGE**

- Phase B rule correctness and the actual F2 outcome: the proposed module does not exist.
- Full separate-directory heldout execution: inspected the named integration test, but `/tmp` permissions prevented running it.
- The retained `all_deviators_post_lock` section label: it differs from the plan, but the dispatcher explicitly accepts it.
- Conservative H3 workload bounds: no demonstrated omission of attacks follows from the overcount alone.

Validation: all 11 listed artifact hashes matched; the 26 changed files outside `docs/` matched the declared delta; `locked.yaml` was unchanged; amendment registration verification passed. Nine targeted tests passed using in-memory capture with plotting disabled; two skipped. No files were changed, paid APIs called, or sealed content read.

**VERDICT: request-changes**  
**CONFIDENCE: 0.97**
