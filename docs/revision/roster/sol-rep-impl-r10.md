VERDICT: accept-with-caveat
CORRECTIONS:
1. `docs/revision/followup3/rep_collect.py:282–297` — Round validation excludes cost-cap records. An in-memory probe with `attack_f=None`, `attack_change=0.02`, and the cost-cap status counts the cell as “stopped,” not “not continued.” The frozen winner remains available, and resume reruns the cell. Correct this minor classification difference or document the exception.
2. `docs/revision/followup3/rep-impl-r9-response.md`, P1 — Limit the claim to recomputed disagreements. At `rep_collect.py:335–337`, a well-formed failing comparison independently establishes a mismatch, even with malformed round data: collection removes the primary set, and resume exits 4 without rerunning. Unchanged ruling 10 explicitly permits this evidence path.

CONFIDENCE: 0.96.