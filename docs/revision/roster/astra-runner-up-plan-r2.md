VERDICT: reject

CORRECTIONS:

1. **Block pod — §2; `docs/revision/followup2/runnerup_v2.py:152`.** Freeze validation still trusts bank hashes from `inputs.json`. It checks reference dependencies against current files, but does not compare those files directly with the original freeze hashes. An in-memory probe confirmed that a changed bank and rebuilt reference pass both `prefreeze()` and `check_freeze()`. Require exact bank membership and actual file hashes equal to the original freeze before reference construction and acceptance. Add a refusal test for this case.

2. **Block pod — §2; `docs/revision/followup2/guards.py:108`.** The evidence guard accepts one arbitrary `{"pass": true}` file. It does not require all specified checks, identify their cells, or establish that the pod check ran in the current environment. A probe also accepted `identical: false`. Require the complete evidence set, bind it to inputs, code and environment, and preserve the reset draft-5 pod criterion with `--require-identical`. Add refusal tests for missing, unrelated and nonidentical evidence.

3. **Block pod — §§5–6; `docs/revision/followup2/runnerup_v2.py:325`.** The USD 2.49 reservation does not cover the USD 3.00 execution allowance. Reserve the full allowance or limit execution to the granted reservation. Persist failed-attempt spending and subtract it from the remaining allowance: `CostStop` currently counts only elapsed time since the supplied allocation timestamp and defaults to the current time. Require that timestamp for paid execution. The benchmark arithmetic reproduces 17.65 core-hours and USD 1.99 billed cost, including reproduction.

4. **None — remaining round-1 corrections, §§1–4 and inventory.** The bounded estimand answers sensitivity to this alternative comparator. Deferrals, base/doubled contrasts, exact expectation scoring, missing/nonfinite handling, nominal conditional intervals and inventory identification are addressed. Live checks passed for all 12 job specifications, pairing, budgets, configurations, frozen code/settings and 108 original bank hashes. Registered base/doubled records contain 200 matched seeds per market. All 10 shared-analysis tests passed; the full 56-test suite was not rerun because it requires file writes.

CONFIDENCE: 0.97.