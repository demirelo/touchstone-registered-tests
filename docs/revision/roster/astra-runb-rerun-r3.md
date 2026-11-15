VERDICT: accept-with-caveat

CORRECTIONS:

1. `docs/revision/budget-ledger.json:20`: Complete the stated accounting prerequisite before launch: record verified `convergence-1` spend, close its reservation, and reserve 9.10 USD for `convergence2-1`. The current ledger remains unreconciled. The launcher correctly refuses it; this does not block acceptance of the code fixes.

2. `docs/revision/followup2/test_followup2_pod_harness.sh:352`: Add explicit exit-6 cases for the initial convergence run and its restart. The existing crash case returns 1. Read-only probes confirmed that both exit-6 paths report “RUN FAILED at convergence” without another restart, so this is a regression-test gap.

3. `docs/revision/followup2/test_convergence_v2.py:406`: Add an ordinary-error-plus-saved-mismatch case that asserts exit 4 and inventory creation. The implementation preserves mismatch priority, but the new test does not cover this combination.

CONFIDENCE: 0.94.