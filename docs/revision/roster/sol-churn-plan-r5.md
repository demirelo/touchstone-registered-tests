VERDICT: reject

CORRECTIONS:
1. **Blocker — §7; `churn_v2.py:382`.** Saved measurements do not require coverage of every current evaluation rule. An in-memory probe confirmed that an F111-only sample is reused for a list containing F111, C*, and F000, with no new measurement. Require a valid measurement for each current rule, or refuse reuse when the rule set changes. Add a regression test.

2. **Blocker — §7; `churn_v2.py:477`.** A saved memory measurement is treated as proof that its production task is complete. The driver excludes every saved `measured` job without validating its output record. An in-memory probe confirmed that these jobs remain excluded when their records are absent. Dispatch them through `_run_one`, which can skip valid records and recompute missing or damaged records. Add regression tests for evaluation and doubling retries.

3. **none — §7; `churn_memory.py:11`, `churn_v2.py:408`.** The skipped-record correction works: the child reports status, and preflight measures the next task in the same rule or stage. It refuses exhausted groups without applicable saved evidence.

4. **none — §7; `churn_v2.py:425`, `churn_v2.py:459`, `churn_v2.py:481`.** Worker limits persist across commands for the same memory limit. Diagnostics refuse without saved evidence.

5. **none — §§7, 9; `churn_cost.py:13`.** Arithmetic reproduces: 6.88 hours/USD 3.85; 5.95 hours/USD 3.33 without serial preflight; 12.44 hours/USD 6.97 at two evaluation workers. Source review and in-memory checks completed; the full 28-test suite was not rerun.

CONFIDENCE: 0.95.