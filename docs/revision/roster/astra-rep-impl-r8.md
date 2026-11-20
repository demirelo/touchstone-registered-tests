VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup3/rep_collect.py:333–337` — M1 remains incomplete. The status branch returns before checking measured round-1 values. An in-memory probe with an identical comparison and finite `attack_change=0.02` against doubling’s `0.0` returns mismatch `True` with status `"passed"`, but `False` with `"stopped: round 1 differs from the registered doubling"`. `_round1_ready` returns `True` in both cases. Thus collection can retain the primary set, and resume can rerun a measured mismatch instead of stopping. Remove the status shortcut and evaluate both evidence paths independently. Add collection and resume regression tests in `test_rep_collect.py`, requiring primary-set removal and exit 4 without rerunning. Update M1/M5 completion claims in `rep-impl-r7-response.md`; ruling 10 must preserve the measured-evidence rule regardless of status. All 183 existing tests pass, so they do not catch this defect.

CONFIDENCE: 0.99.