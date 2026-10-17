Read-only review of [v3](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/docs/superpowers/plans/2026-10-17-proposed-rule.md). No files changed. The sealed bundle remains unread. No tests or simulations ran.

Round-2 OPEN and NEW objections, with duplicate objections from both reviews combined:

- **RESOLVED — F2 and amendment scope.** Line 20 restores `k >= s` under both targeting variants, includes entry costs, states the expected kill at `L = 10`, and requires reporting that kill.
- **RESOLVED — H3 transfer.** A2 specifies shared family resolution, embedded D1 members, both transformations, deterministic order and origins, projections, and embedding metadata inside the hashed bank document.
- **OPEN — H3 doubling dispatch (MATERIAL).** The required result is stated, but A1 specifies only manifest changes; no task or test changes the [checks selector](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/sweep.py:379), which accepts only `development` records and silently skips H3.
- **RESOLVED — Evaluation logs.** A3 requires ordered logs that include repeated evaluations, carries them into `SearchResult.evaluations`, persists traces, and tests completeness for both families and rechecks.
- **OPEN — Registered workload execution (MINOR).** The rho cells and `all_deviators` section are corrected, but A6’s stated command omits required `--calibration` and the `--tuned-dir` needed for a production run.
- **RESOLVED — H3 workload accounting.** A1/A2 require H3 transfer and projection counts in `bank_members`, `_bank_total`, and post-lock totals.
- **RESOLVED — Final bank ingestion.** A6 specifies `--bank-from`, source-hash verification, refusal of missing or changed sources, and reuse of the bank and its embeddings.
- **RESOLVED — Registered-artifact preservation.** A6 requires all registered artifact hashes in the note and a closing `amend.py --check`.

The F3 clarification is also **RESOLVED**: line 20 counts one ban event per identity-round and clips lost capacity at the episode end.

To close the H3 dispatch objection, explicitly assign the `run_stages` change in Phase A: match H3 controls to section `h3`, retain `development` for D1/D2, and reject a missing required control input. Require an integration test that produces one H3 checks record per rule from the bank-finalized attack, twin, projections, and checked reference.

Complete the A6 sweep command with:

```text
uv run python scripts/sweep.py --stage all --sections development,rho_sweep,h3,all_deviators,ablation --rules B1,B2,B3,proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/sweep_proposed
```

**NEW — MINOR, A5 line 98: incorrect L = 20 quota fixture.** The registered formula gives `E = 1500` across 180 early rounds: 120 quotas of 8 and 60 quotas of 9, totaling 1500. The plan says the early quota is 8. Correct this assertion so that the test accepts the registered schedule.

**VERDICT: reject**  
**CONFIDENCE: 0.95**
