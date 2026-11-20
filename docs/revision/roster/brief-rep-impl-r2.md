# Churn replication: implementation and launcher review, round 2 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 1: `docs/revision/roster/{sol,astra}-rep-impl-r1.md` (both reject). The response ledger `docs/revision/followup3/rep-impl-r1-response.md` lists every correction with the plan text it applies and the test that failed first (or the old-code demonstration); `git diff 11a4937..6ad7739 -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (rulings 5 and 8 withdrawn; every ruling now quotes its plan sentence, enforced by `test_notes.py`). Plan of record: `docs/revision/followup3/replication-plan.md` (only the section 6 cost paragraph changed). Lessons: `docs/revision/lessons.md` (two new entries today).

Evidence you cannot rerun in a read-only sandbox: the launcher harness log `results/pods/logs_harness/rep_pod_r2c_20261119T224245Z.log` (its first line gives the sha256 of the harness and launcher it ran; they equal the committed files; result: HARNESS OK, 46 of 46 scenarios); the Mac smoke chain of every stage after the binding change: `rep-launcher-notes.md`, section "Smoke evidence", round 2. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/`.

Check (first: is each round-1 correction answered correctly and completely?):
1. Gate and continuation (`rep_collect.run_queue`, `rep_v2.gate_item`, `stage_continue`): the first p = 0.05 cell always, round 1 identical (0.0), child process, codes 3/4/5/6, resume rules, continued-winner diagnostics.
2. Validation and analysis (`rep_collect.collect`, `replication_analysis.analyse`): base-record checks, flagged-only continuation, six named markets, matched seeds, shared bootstrap indices, secondary outputs, expectation 5 on primary winners.
3. Commitment and binding (`commitment.py`, `rep_v2` binding, instance and calibration protection, Linux x86 reuse, listed parameters, the launcher's self-check).
4. Launcher (`rep_pod.sh`): one pod name and lock, `POD1TAG` and its spend row, pod 2 bundle binding, inventory on every failure exit, retried pulls, new admission hours.
5. Rulings 1 to 12: accept or correct each. Is ruling 12 (Mac helpers outside the repository) acceptable?
6. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
