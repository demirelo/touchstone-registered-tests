# Paper draft 9 outline review, round 4 (read-only; no paid APIs; do not read `sealed/`, `sealed2/`, or `~/touchstone-h4`; reasoning effort high; under 500 words)

Round 3 (`docs/revision/roster/{sol,astra}-paper-outline-r3.md`) asked for three corrections. Commit fcca0a8 applies them: the result-site manifest (`sites.json`, `\site{}`) and its checks in `docs/revision/paper-v2/numbers_v2.py`, p-values in `tables_v2.py`, and the outline (version 4; "Result sites" bullet and the round-3 disposition table, which states one residual limit). Tests: `uv run pytest -q docs/revision/paper-v2/` (32 pass).

Check only: (1) each round-3 correction is resolved, or whether the stated residual limit (a same-kind swap within one section, covered by the final PDF read against report.md) is acceptable; (2) no new error. Do not reopen resolved points.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered (section, exact change, reason with file:line), or "none".
CONFIDENCE: 0 to 1.
