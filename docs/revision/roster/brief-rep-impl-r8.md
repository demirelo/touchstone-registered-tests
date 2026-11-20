# Churn replication: implementation and launcher review, round 8 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 7: `docs/revision/roster/{sol,astra}-rep-impl-r7.md` (both reject). The response ledger `docs/revision/followup3/rep-impl-r7-response.md` (items M1 to M5) lists every correction with the plan text it applies and the tests that failed first on the previous commit (3a7bde1); `git diff 3a7bde1..HEAD -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Round 6's ledger now marks L1 and L5 incomplete. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (ruling 10). Plan of record: `docs/revision/followup3/replication-plan.md` (unchanged).

Design decisions to check, not assume: a mismatch needs measured evidence (a well-formed failing comparison, or well-formed round-1 values and doubling changes that disagree); a well-formed provenance is one with the job's own fields, each of the same JSON type and not empty; only such a provenance that names another job or run refuses the resume.

Evidence you cannot rerun in a read-only sandbox: launcher and harness unchanged since `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (HARNESS OK, 47 of 47; header hashes equal the committed files); all 76 Run B continuation records with an identical round 1 pass every check against their registered doubling and search records and are not mismatches; the round-3 Mac smoke records re-collected with this code: 72 of 72 scorable, 0 problems, audit counts for all 18 R3 cells. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/` (183 pass).

Check (first: is each round-7 correction answered correctly and completely?):
1. M1 to M3: mismatch versus invalid in every path; can a status, a malformed comparison or malformed doubling values still stop everything, or a genuine mismatch be missed?
2. M4: provenance well-formedness and the refusal rule.
3. M5: does the guard require the exact prescribed outcome for every generated input, in collect, on resume and in queue construction?
4. Ruling 10 as amended.
5. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
