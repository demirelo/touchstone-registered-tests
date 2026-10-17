Reviewed [v3](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/superpowers/plans/2026-10-17-proposed-rule.md) against both round-2 reviews, found in the main checkout, the registration, and current code. Read-only; sealed bundle unread; no tests or simulations ran. Duplicate objections are combined below.

- **RESOLVED — F2 and amendment scope.** Line 20 restores `k >= s` under both variants, retains the profit gate, states the expected kill at `L = 10`, and requires reporting the kill.
- **RESOLVED — H3 transfer execution.** A2 specifies shared registry-based family resolution, embedded D1 members, both transformations, deterministic order and origins, projections, and hash validation.
- **RESOLVED — H3 doubling.** Lines 20 and 42 require H3 controls for every rule, checks-stage execution with the bank-finalized inputs, and `abs(delta_gain) < 0.005`; line 86 rejects a missing result.
- **RESOLVED — Evaluation logs.** Lines 71–75 require ordered logs including repeated evaluations, explicit trace serialization, and completeness tests for both families and rechecks.
- **RESOLVED — Missing workloads.** A1 adds rho cells and fixes `all_deviators`; A6 includes both sections and requires output-inventory validation.
- **RESOLVED — H3 workload accounting.** A1/A2 explicitly add transfer and projection bounds to `bank_members`, `_bank_total`, and manifest totals.
- **OPEN — Final-bank ingestion.** A6 defines source validation for the bank stage, but does not specify how later reference/evaluate/checks stages load that external bank and resolve its source records.
- **RESOLVED — Registered-artifact preservation.** A6 requires all registered artifact hashes, the amendment-1 delta, and the closing `amend.py --check`.
- **RESOLVED — F3 clarification.** Line 20 counts one ban per identity-round and clips lost capacity at episode end.

The remaining ingestion issue is concrete: [run_stages](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:348) loads `out/bank.json` during later stages, while `load_bank_doc(out)` checks sources under `out/search`. Final evaluation contains heldout records there, not the development sources. Specify a shared bank/source resolver for all stages, or a validated import layout. Require a passing synthetic end-to-end test with separate development and final directories, including resumed stages.

**NEW — MATERIAL: the “frozen” bank has no freeze commitment.**  
A6/B2, lines 108 and 131, verify internal bank/source consistency but do not bind the bank used by F5 to the freeze tag. The existing [freeze verifier](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/sim/claimcheck.py:25) protects only the three rule files. A rebuilt bank with updated source hashes can therefore pass the stated checks while differing from the bank tested by F5.

**Repair:** Record the F5 bank hash, including its source map and embeddings, in a freeze-committed artifact. Require final ingestion and claim verification to match that commitment. Test rejection of a different, internally valid bank.

**NEW — MINOR: the stated complete sweep command is incomplete.**  
A6 line 108 omits required `--calibration` and the baseline `--tuned-dir`. The current CLI requires the former. Supply the full command and replace `amend.py ... --check` with its complete invocation.

**VERDICT: reject. CONFIDENCE: 0.95.**
