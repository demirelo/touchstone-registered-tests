VERDICT: reject

CORRECTIONS:

1. **Blocker — §7; churn_v2.py:391, :407–413.** Worker reductions persist only within one `_run_rate` call. Separate-stage and resumed commands reset `w_mem` to `workers_eval`; diagnostics load no saved limit. A read-only control-flow test reproduced evaluation at two workers followed by separate diagnostics at nine. Load validated preflight limits across invocations, retain the lowest applicable limit, and test separate-stage execution.

2. **Blocker — §7; churn_v2.py:349–375.** A resumed preflight can measure record reuse instead of task execution. The child calls `_run_one`, which returns `"skipped"` for valid existing records (`scripts/revision_v2.py:1097`). The resulting low RSS can overwrite the earlier measurement and admit too many workers. Reuse a validated full-task measurement, or measure an actual unfinished task. Reject skipped measurements and test partial-stage retries.

3. **§7; churn-plan.md:204–206, :243–244.** Update billed-time estimates for serial preflight tasks. Even with nine workers throughout, evaluation now needs three serial tasks plus two parallel waves; doubling needs one serial task plus two waves. This adds approximately 0.93 hours: about **6.88 hours/$3.85**, before worker reductions. The $4.43 benchmark estimate remains larger, so this alone does not require a larger reservation.

4. **none — §§2–6.** Honest replacement fairly tests sensitivity to identity age, with disclosed history-reset and ban-escape effects. Rates 0.01 and 0.05 are justified as illustrative settings, not calibrated rates. Frozen references support the stated estimand; reference deterioration can inflate gains and move rule contrasts either way. Separate profit terms and the training-only reselection caveat are adequate.

5. **none — §3; churn_v2.py:62–107, :256–314, :403–409.** Injection reaches search, evaluation and doubling. Cache clearing, reference rescoring and record separation are sound. Round 3’s repeated cost admission and optional bit-identity gate are implemented. The launcher must pass `--require-identical`; its separate review remains outside this review.

6. **none — §§5–7.** Matched baselines reproduce. Conditional intervals, exploratory labels, the disclosed prior peek and expectation scoring are adequate. The watchdog exception resolves the shutdown contradiction in the plan. The reported 23-test suite was not rerun; current coverage misses corrections 1–2.

CONFIDENCE: 0.97.