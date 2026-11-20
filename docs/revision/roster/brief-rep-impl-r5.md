# Churn replication: implementation and launcher review, round 5 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 4: `docs/revision/roster/{sol,astra}-rep-impl-r4.md` (both reject). The response ledger `docs/revision/followup3/rep-impl-r4-response.md` (items J1 to J6) lists every correction with the plan text it applies and the test that failed first on the previous commit (a8d80b9); `git diff a8d80b9..HEAD -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Round 3's ledger now marks H1, H2, H4 and H8 incomplete and points to their completions. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (rulings 8 and 10). Plan of record: `docs/revision/followup3/replication-plan.md` (unchanged). Lessons: `docs/revision/lessons.md` (entries 2026-11-20).

Design decisions to check, not assume: round-1 identity is now recomputed from this cell's own doubling record (held-out knobs, the np.mean of its held-out gains, both changes) and Run B's empty problems list; a continued winner's primary audit count no longer depends on the frozen diagnostics; an unknown saved status is set aside and rerun; type errors in a record are failed checks (a decorator is the last line behind explicit type checks). New guard against the class: test_no_malformed_record_field_raises_in_collect mutates every field of every record kind.

Evidence you cannot rerun in a read-only sandbox: the launcher and harness are unchanged since `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (HARNESS OK, 47 of 47; header hashes equal the committed files); the round-1 check accepts all 76 Run B continuation records with an identical round 1 against a registered doubling record (`results/v2/**/convergence/` against `results/v2/**/doubling/`); the round-3 Mac smoke records (commit 0bdc0cb) re-collected with this code: 72 of 72 scorable, 0 problems, audit counts for all 18 R3 cells. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/` (141 pass).

Check (first: is each round-4 correction answered correctly and completely?):
1. J1: primary audit counts for continued and frozen winners.
2. J2: is the round-1 identity check complete and correct against Run B's compare_round1; can a forged or stale comparison still pass, or a genuine one fail?
3. J3, J5: can any malformed record still raise, or give a continued winner?
4. J4: resume rules (rerun, set-aside, the mismatch stop).
5. Rulings 8 and 10 as amended.
6. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
