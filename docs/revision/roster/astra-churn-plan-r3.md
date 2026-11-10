VERDICT: reject

CORRECTIONS:

1. **Blocker — §7; churn_v2.py:361–372.** Recheck the cap after memory preflight selects the worker count. The current check uses the requested count. A read-only control-flow test reproduced admission for 2,654 seconds followed by one-worker dispatch requiring an estimated 23,887 seconds. Include preflight time in the estimate and update billed-time estimates when workers decrease.

2. **§7; churn_v2.py:370–374.** Complete the round-2 memory correction. Preflight measures only `jobs[0]`, without checking variation across markets or policies. Diagnostics revert to the requested worker count. Use a justified maximum task peak, retain the selected limits across stages, and check doubling’s additional memory requirements. Reading the cgroup limit and measuring a full evaluation task are useful corrections.

3. **Blocker — §7; reset_pod.sh:85, :92, :124.** Reconcile the launcher with “no running stage is ever killed.” Its watchdog deletes the pod at 1.3 times the cap, and its hard-deadline exit also triggers deletion. Adapt and review the churn launcher before allocation: pass allocation time, actual price and accumulated retry charges; preserve between-stage stopping and verified cleanup. The existing retry calculation uses one start time and the latest hourly price, which does not accurately total attempts at different prices.

4. **§3(c); churn_v2.py:261; reset-experiment-plan.md:107–112.** Resolve the gate-policy difference. Churn accepts tolerance-based `pass`; the template’s pod gate requires bit identity. State the intended churn criterion explicitly and enforce it. The saved gate requirement now covers separate and resumed production stages, and checks the driver hash.

5. **none — §§2–6.** Honest replacement fairly tests sensitivity to identity age, with disclosed history-reset and ban-escape effects. The rates support illustrative sensitivity analysis, not empirical calibration. Frozen references support the stated estimand; reference deterioration can inflate gains and move contrasts either way. Injection reaches search, evaluation and doubling; cache corrections and record separation are sound. The first-offer diagnostic and narrowed expectation 4 address round 2.

6. **none — §§5–7.** Baselines reproduce. Conditional intervals, separate profit terms and the disclosed prior peek support exploratory interpretation. The nominal 41.06 core-hours and USD 4.43 arithmetic checks; reserving USD 4.43 produces approximately USD 5.54. Required timing and price inputs address the earlier omission. I did not rerun the full test suite.

CONFIDENCE: 0.95.