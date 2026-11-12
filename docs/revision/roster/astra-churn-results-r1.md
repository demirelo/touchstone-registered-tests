VERDICT: reject

CORRECTIONS:

1. `docs/revision/paper-v2/main.tex:246`: Correct the profit explanation. R3’s reference profit **falls** by 0.146; its interval is [−0.393, 0.098]. Replace “not from a weaker reference” with “predominantly from higher attack profit.” Label these as raw profit units. In normalized units, the attack change is +0.206563 and the reference change is −0.000278.

2. `docs/revision/paper-v2/main.tex:246`: Replace “The diagnostics show how” and “priority thus moves audits … while the attacker’s identity hides” with descriptive statements. The diagnostics establish greater newcomer audit exposure and a low attacker newest share. They do not isolate the cause of the gain increase: histories, bans, and selected attacks also change.

3. `docs/revision/paper-v2/main.tex:246`: Define “newest” precisely: **strictly latest first-offer round**, excluding ties, among identities with assigned jobs. State that the reported value averages per-episode shares, then market means. It is not a single pooled fraction of rounds.

4. `docs/revision/posthoc/churn_block.py:210`: Validate the diagnostic summaries against their per-episode counts and expected cells before scoring expectation 4. The current code trusts `pooled` without checking its consistency; the tests supply synthetic pooled values and miss this failure. Add a test that rejects a conflicting summary. The supplied records pass this independent consistency check.

The read-only, 9,999-resample rerun reproduced every JSON field and the table exactly; `registered_check.ok` is true. All four expectation scores are supported. The requested commit diff changes only `incomplete_n`.

CONFIDENCE: 0.97.