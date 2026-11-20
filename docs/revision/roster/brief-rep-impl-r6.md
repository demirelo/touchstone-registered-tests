# Churn replication: implementation and launcher review, round 6 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 5: `docs/revision/roster/{sol,astra}-rep-impl-r5.md` (both reject). The response ledger `docs/revision/followup3/rep-impl-r5-response.md` (items K1 to K5) lists every correction with the plan text it applies and the tests that failed first on the previous commit (ae2afad); `git diff ae2afad..HEAD -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Round 4's ledger now marks J2 to J6 incomplete. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (ruling 10). Plan of record: `docs/revision/followup3/replication-plan.md` (unchanged). Lessons: `docs/revision/lessons.md` (entries 2026-11-20).

Design decisions to check, not assume: a well-formed measured round 1 that disagrees with the cell's doubling record or frozen search is a round-1 mismatch (stop, exit 4, no primary set); a malformed round 1 is an invalid record (rerun on resume; not continued in the analysis). Round-1 evidence used: held-out knobs and mean, both changes, round 1's best knobs (doubling winner or frozen winner), and the doubling winner's held-out gains; Run B's records store no per-seed round-1 gains (frozen code). Records whose root is not a JSON object count as absent. The class guard now enumerates every node of seven record kinds.

Evidence you cannot rerun in a read-only sandbox: launcher and harness unchanged since `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (HARNESS OK, 47 of 47; header hashes equal the committed files); all 76 Run B continuation records with an identical round 1 (`results/v2/**/convergence/`) pass every round-1 check against their registered doubling and search records (`results/v2/**/doubling/`, `search/`) and are not mismatches; the round-3 Mac smoke records (commit 0bdc0cb) re-collected with this code: 72 of 72 scorable, 0 problems, audit counts for all 18 R3 cells. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/` (164 pass).

Check (first: is each round-5 correction answered correctly and completely?):
1. K1, K2: mismatch versus invalid; can a genuine round 1 be refused, or a disagreeing one avoid the stop, anywhere (gate, queue, resume, analysis)?
2. K3, K4: can any record still raise, or give a continued winner, an audit count or a gate pass it should not?
3. Ruling 10 as amended.
4. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
