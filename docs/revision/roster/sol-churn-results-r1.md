VERDICT: accept-with-caveat

CORRECTIONS:
1. docs/revision/paper-v2/main.tex:246 — Correct the profit statement. The reference-profit change is −0.146, with interval [−0.393, 0.098]. Say “the increase comes mainly from attack profit,” rather than “not from a weaker reference.” Label these values as raw profit units; they do not directly decompose the normalised gain.
2. docs/revision/paper-v2/main.tex:246 — Define the newest-identity statistic precisely: “uniquely newest by first-offer round,” with episode shares averaged within each market, then equally across markets. The current phrase “of the rounds” implies a pooled round denominator that churn_block.py:244–248 does not use. Add a test with unequal episode denominators.
3. docs/revision/paper-v2/main.tex:246 — Qualify “The diagnostics show how” and “priority thus moves audits … while the attacker’s identity hides.” The diagnostics support greater newcomer audit exposure and a low uniquely-newest share. They do not isolate the cause of the gain increase from history reset, ban escape, or changes in the selected attacks. Use “These diagnostics are consistent with …”.

CONFIDENCE: 0.97.