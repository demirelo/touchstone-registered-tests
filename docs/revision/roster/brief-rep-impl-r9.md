# Churn replication: implementation and launcher review, round 9 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 8: `docs/revision/roster/{sol,astra}-rep-impl-r8.md` (both reject on one shared finding: the status shortcut in `_mismatch`). The response ledger `docs/revision/followup3/rep-impl-r8-response.md` (items N1 to N3) lists the correction, the test that failed first on the previous commit (761e77c), and a new guard over every status times every well-formed round-1 disagreement; `git diff 761e77c..HEAD -- docs/revision/followup3/` shows the changes. Updated notes: ruling 10. Plan of record unchanged.

Evidence you cannot rerun in a read-only sandbox: launcher and harness unchanged since `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (HARNESS OK, 47 of 47); all 76 Run B continuation records with an identical round 1 pass every check and are not mismatches; the round-3 Mac smoke records re-collected with this code: 72 of 72 scorable, 0 problems, audit counts for all 18 R3 cells. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/` (205 pass).

Check:
1. N1, N2: does any status still change whether measured evidence counts, in collect or on resume?
2. Rulings 1 to 12 as amended across rounds 2 to 8: is any still unmet?
3. Anything that repeats a lesson in `lessons.md` or makes the result uninterpretable. Report only defects you can show (a probe or a line); accept-with-caveat is available for minor items.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
