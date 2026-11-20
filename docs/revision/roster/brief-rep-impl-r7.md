# Churn replication: implementation and launcher review, round 7 (read-only; no paid APIs; do not read `sealed/`, `~/touchstone-h4`, or `~/h4-session.out`; `sealed2/h4/` may be read; reasoning effort high; under 400 words)

Round 6: `docs/revision/roster/{sol,astra}-rep-impl-r6.md` (both reject). The response ledger `docs/revision/followup3/rep-impl-r6-response.md` (items L1 to L5) lists every correction with the plan text it applies and the tests that failed first on the previous commit (0711a21); `git diff 0711a21..HEAD -- docs/revision/followup3/ docs/revision/lessons.md` shows the changes. Round 5's ledger now marks K1, K3 and K4 incomplete. Updated notes: `docs/revision/followup3/rep-launcher-notes.md` (ruling 10). Plan of record: `docs/revision/followup3/replication-plan.md` (unchanged). Lessons: `docs/revision/lessons.md` (entries 2026-11-20).

Design decisions to check, not assume: only a well-formed comparison (Run B's shape) or well-formed round-1 values can make a mismatch; everything malformed is an invalid record; a fresh gate without a measured comparison exits 6. A saved record whose well-formed provenance names another job or run still refuses the resume (plan section 5); one with no or malformed provenance is rerun. Mismatches are checked for every cell before base-record exclusions.

Evidence you cannot rerun in a read-only sandbox: launcher and harness unchanged since `results/pods/logs_harness/rep_pod_r3_20261120T023740Z.log` (HARNESS OK, 47 of 47; header hashes equal the committed files); all 76 Run B continuation comparisons (`results/v2/**/convergence/`) are well-formed and identical, pass every round-1 check against their registered doubling and search records, and are not mismatches; the round-3 Mac smoke records re-collected with this code: 72 of 72 scorable, 0 problems, audit counts for all 18 R3 cells. Checks you can run: `uv run --frozen pytest -q docs/revision/followup3/` (173 pass).

Check (first: is each round-6 correction answered correctly and completely?):
1. L1, L2: invalid versus mismatch in every path (gate, queue, resume, analysis), including cells excluded as unscorable.
2. L3, L4: queue construction; normalizers in the shared validation.
3. L5: does the guard require the one prescribed outcome for every input class it generates?
4. Ruling 10 as amended.
5. Anything new that repeats a lesson in `lessons.md` or makes the result uninterpretable.

Output exactly:
VERDICT: accept | accept-with-caveat | reject
CORRECTIONS: numbered, each with file and line or section, or "none".
CONFIDENCE: 0 to 1.
