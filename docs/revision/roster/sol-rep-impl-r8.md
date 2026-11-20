VERDICT: reject

CORRECTIONS:
1. `docs/revision/followup3/rep_collect.py:333–334` — The status branch can hide a measured mismatch. With an identical comparison, valid round-1 `attack_change=0.02`, and doubling `attack_change=0.0`, `_mismatch` returns true for status `passed` but false for the mismatch status. In-memory checks confirmed that collection keeps the primary set and reports no mismatch; resume reruns the cell and exits 0. Check measured disagreement independently of status. This violates plan section 4 and ruling 10’s requirement that a well-formed round-1 disagreement stop continuation. Add regression checks in `test_rep_collect.py` for collection and resume that require no primary set and exit 4 without rerunning. The single-field mutation guard misses this combination.

The 183 tests pass. M2’s overflow handling, M4’s provenance rule, and M5’s exact assertions for generated inputs address their reported defects. The launcher and harness hashes match the cited 47-of-47 log.

CONFIDENCE: 0.99.