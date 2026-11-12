# Honest-churn results and paper text: internal review round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; reasoning effort high; under 350 words)

Round 1 (`docs/revision/roster/{sol,astra}-churn-results-r1.md`): Sol accept-with-caveat (3), Astra reject (4). Every brief, file and command of round 1 (`docs/revision/roster/brief-churn-results-r1.md`) still applies. Changes since round 1, all in the last commit (`git diff HEAD~1 -- docs/revision/posthoc docs/revision/paper-v2/main.tex`):

1. Profit sentence: "mainly from higher attack profit", raw profit units, the reference's change with its interval, and that raw terms do not decompose the normalised gain exactly.
2. The newest statistic is defined: strictly latest first-offer round among identities holding assigned jobs, ties excluded, averaged over a market's episodes and then over markets; `diag_summary` documents the same, and a test with unequal per-episode shares and a None episode pins the averaging.
3. The diagnostics are described, not given causal force: "consistent with ...; they do not isolate the cause ... histories, bans, selected attacks".
4. `validate_diagnostics` (run by the CLI before scoring): every cell present with one episode per seed; bin totals equal the per-episode sums; shares equal audited / served; the pooled shares equal the mean of the available market shares with that count; newest shares in [0, 1]. Four tests, each seen failing first; the real diagnostics pass, and churn.json and the table are unchanged by the rerun.

Tests: `uv run --frozen pytest -q docs/revision/posthoc/test_churn_block.py` (23 pass). `results/pods/paper_check.sh`: gate ok.

Check: (0) each round-1 correction is resolved; (1) to (4) as in round 1.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file:line, or "none".
CONFIDENCE: 0 to 1.
