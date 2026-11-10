VERDICT: reject

CORRECTIONS:

1. **Block pod: validate the complete freeze.** `docs/revision/followup2/runnerup_v2.py:126` and `:144`: `prefreeze()` checks existence, but not record provenance or dependencies. `accept()` permits an empty `records` map; I confirmed this in memory. Require all bank inputs, both searches, and the reference for each market. Validate their provenance, dependency sets, original bank hashes, and freeze metadata. Add refusal tests for omitted and changed records.

2. **Block pod: pin all execution settings.** Plan §2; `runnerup_v2.py:109`: checking the runner and `sim/` does not pin `experiments/locked.yaml` or the manifest. `TOUCHSTONE_LOCKED` can change search settings, while pairing omits budgets. Reject this override, verify registered settings and family-specific budgets, and enforce the exact runner-up specification. A parameter hash merely different from C* is insufficient.

3. **Complete analysis before outcomes.** Plan §§3–4; `runnerup_v2.py:174`: analysis reads only base evaluations. Implement doubled contrasts, expectation scores, separate attack/reference doubling flags, and the promised per-market intervals. Compare runner-up and C* using corresponding base or doubled records. Use unrounded values, not 0.0207 as a decision threshold. Define missing/nonfinite results separately from failures. State that 95% nominal intervals condition on these six markets and frozen searches; they do not inherit registered calibration or Holm guarantees.

4. **Bound the scientific claim.** Plan §§1, 4: the estimand answers sensitivity to this specific alternative comparator. It does not identify the best gain-selected comparator among all twelve configurations. Explicitly defer full-budget rechecks of the other ten. State that existing market outcomes were already observed; only runner-up outcomes are unseen. Label this a follow-up, not an independent replication.

5. **Block pod: specify spending controls.** Plan §§5–6: the benchmark reproduces 17.65 core-hours and USD 1.91. State an explicit cap, ledger category, reservation, remaining program allowance, and stopping rule that includes failed attempts. The reset experiment’s USD 10 approval does not authorize this run. Account for six serial reference calls in billed time.

6. **Correct the inventory.** `runnerup_v2.py:222` calls the reset helper, which records reset deviations and hashes `reset_followup_v2.py`. Record Run A’s deviations and hashes for its driver, `common.py`, and helper. Nine shared-analysis tests passed here; tests requiring file writes were not rerun.

CONFIDENCE: 0.96.