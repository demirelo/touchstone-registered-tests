VERDICT: reject

CORRECTIONS:
1. `docs/revision/followup3/rep_collect.py:204–220` — `_round1_ready` omits the round number, `attack_f`, and `reference_f` checks required at lines 191–193. An in-memory probe with an identical comparison, `rounds[0].attack_f=None`, and `attack_change=0.02` against doubling’s `0.01` makes `cont_problem` report “round 1 malformed or nonfinite”. However, collection removes the primary set, and resume exits 4 without rerunning. Ruling 10 requires the invalid-record path for a malformed round 1. Validate the required first-round fields independently of status before classifying a recomputed disagreement. Add collection and resume tests that combine malformed fields with disagreements. N1/N2’s status shortcut is corrected; this classification defect remains.

CONFIDENCE: 0.99.