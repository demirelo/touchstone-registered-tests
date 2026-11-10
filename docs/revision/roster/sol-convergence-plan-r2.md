VERDICT: reject

CORRECTIONS:

1. **Plan §5; guards.py:108; convergence_v2.py:184.** Bind gate evidence to the required cells, full budgets, input hashes, code hashes, and environment. The current check accepts any record containing `"pass": true`. I confirmed that one unrelated file satisfies it. Require both specified cells and separate Mac and pod evidence before the main run.

2. **Plan §3; convergence_v2.py:191,201,279.** Restrict substitutions to this run’s validated cell list and verify each complete binding. Analysis currently accepts `"binding": {"smoke": false}` with matching seeds. I confirmed this acceptance. A stale result outside the selected jobs can enter the analysis without passing `reusable()`. Also verify record identity, finite gains, and array lengths.

3. **Plan §6; convergence_v2.py:156,252,265; guards.py:94.** Apply cost checks before the gate and before each worker starts its first round. The gate bypasses `CostStop`; queued cells start without another check. Require a valid billing start and positive rate. Include failed-attempt spend and an allowance for final evaluation and shutdown. Preserve the instruction to let running rounds finish.

4. **Plan §6; cost_estimate.py:18; convergence_v2.py:253.** Match the cost schedule to execution. The estimator assumes parallel gate cells, but the driver runs them serially. The benchmark gives approximately **1.06 gate hours**, **3.53 total billed hours**, and **USD 1.98**, instead of 0.75 hours, 3.22 hours, and USD 1.80. The larger USD 1.99 estimate remains sufficient under these assumptions. Reserve enough ledger capacity for the permitted USD 3.00 spend.

CONFIDENCE: 0.97.