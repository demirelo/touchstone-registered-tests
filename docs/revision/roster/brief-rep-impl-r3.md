# Churn replication: implementation and launcher review, round 3 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 2: `docs/revision/roster/{sol,astra}-rep-impl-r2.md` (both reject). The response ledger `docs/revision/followup3/rep-impl-r2-response.md` (items G1 to G9) lists every correction with the plan text it applies and the test that failed first; `git diff 30605c9..f2ac8bc -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (rulings 7, 8, 10, 11 and the ruling 12 caveat). Plan of record: `docs/revision/followup3/replication-plan.md` (unchanged in this round). Lessons: `docs/revision/lessons.md` (entry 2026-11-20).

Record kinds `rep_collect` reads, with their checks: evaluation and doubling (`base_problem`), continuation and gate (`cont_problem`), frozen diagnostics rows (`diag_ok`), continued diagnostics (`cont_diag_ok`). Each has a parametrized test that changes one field at a time.

Evidence you cannot rerun in a read-only sandbox: the launcher harness log `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (its first line gives the sha256 of the harness and launcher it ran; they equal the committed files; result: HARNESS OK, 47 of 47 scenarios); the x86 scenario run on the old launcher (fails) and the new one (passes): `docs/revision/roster/rep-impl-r3-x86.log` (each part starts with the sha256 of the launcher and harness it ran; the harness equals the committed one; the scenario is the block after `== pod 2: a calibration not made on x86 is refused`, and with the old launcher it fails with a pod creation request and exit 142, with the new one it refuses with exit 1 and no pod; the later SCENARIO FAILED lines in both parts are expected, because `ONLY=` skips the scenarios that produce the files those checks read); the new checks on the round-2 Mac smoke records (made at commit 328bff6, so the probe pins that commit for provenance): 72 of 72 cells scorable, 0 problems, gate passed, audit counts for 18 of 18 R3 cells; with the current commit, every cell is refused (provenance differs), as intended. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/`.

Check (first: is each round-2 correction answered correctly and completely?):
1. G1: manifest set (runner-up recheck record, `churn_memory.py`, string-literal scripts in the import closure), git return codes.
2. G2 to G4: every record check; is any field a later stage relies on still unchecked?
3. G5: absolute-contrast intervals at every rate; t interval only with six markets.
4. G6 and G7: lost workers on resume and in diagnostics, through the launcher's restart; kept worker counts; pod 2's x86 guard.
5. Rulings 1 to 12 as amended.
6. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
