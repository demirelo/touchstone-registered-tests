# Churn replication: implementation and launcher review, round 4 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 3: `docs/revision/roster/{sol,astra}-rep-impl-r3.md` (both reject, six shared findings). The response ledger `docs/revision/followup3/rep-impl-r3-response.md` (items H1 to H8) lists every correction with the plan text it applies and the test that failed first on the old code (f2ac8bc); `git diff eb4c1fd..HEAD -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Round 2's ledger now marks G2 to G6 incomplete and points to their completions. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (rulings 8, 10, 11; "Smoke evidence", round 3). Plan of record: `docs/revision/followup3/replication-plan.md` (unchanged). Lessons: `docs/revision/lessons.md` (entries 2026-11-20).

Design decisions to check, not assume: an invalid saved record is set aside and rerun (plan section 4: "a resume continues the same queue from the first cell without a passing record"); an invalid continuation in the analysis keeps the frozen winner as "not continued" (section 4), while a round-1 mismatch or a missing identical gate still removes the primary set; frozen diagnostics are bound by a new file `diagnostics_binding.json` that the rate stage writes after the diagnostics step and before the inventory (the frozen churn arm code is unchanged).

Evidence you cannot rerun in a read-only sandbox: the launcher and its harness are unchanged since `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (HARNESS OK, 47 of 47; its header hashes equal the committed `rep_pod.sh` and `test_rep_pod_harness.sh`); the x86 scenario evidence `docs/revision/roster/rep-impl-r3-x86.log` (unchanged); the Mac smoke chain at commit 0bdc0cb, described in the notes, round 3 (72 of 72 scorable, expectation 5 scored in both sets through the binding, inventory 1361 records, 0 bad). Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/` (128 pass).

Check (first: is each round-3 correction answered correctly and completely?):
1. H1, H2, H4: record checks before reuse, rounds and gate contents, the fallback; can any invalid record still give a continued winner, or any valid one be lost?
2. H3: normalizers in every record kind that terms_of or the analysis divides by.
3. H5: episode and bin counts; does the binding tie each frozen row to this job, rate and run, and can a stale diagnostics file still pass?
4. H6, H7: six-market t intervals everywhere; diagnostics workers on the launcher's restart.
5. Rulings 8, 10, 11 as amended.
6. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
