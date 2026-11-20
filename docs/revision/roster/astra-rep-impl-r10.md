VERDICT: accept-with-caveat

CORRECTIONS:
1. `docs/revision/followup3/rep_collect.py:282–297, 633–637`: A cost-stop status still bypasses round validation. An in-memory probe with `attack_f=None` and a disagreeing `attack_change` returns no validation problem and selects “stopped”, rather than “not continued”. Validate malformed measured rounds for this status and add a regression test. This affects counts only: collection retains the frozen winner, and resume reruns the cell. The P1 correction otherwise passes the supplied tests: 229 passed, 1 skipped.

CONFIDENCE: 0.96.