# Fable 5.2, review round 4 (rep-paper-r4), as returned to the session on 2026-11-24

VERDICT: accept-with-caveat

CORRECTIONS:
1. main.tex:382 (Table 30 caption): closed.
2. _validate_counts and the test pin: closed. In-memory probes: x = True, x = 1.0, missing job or young-honest audit shares, recomputed false are refused by _validate; an in-range share edit, flipped x, doubled rep0 counts, swapped x, count edited with its rate, established rate None pass _validate but fail the pin. No edited extract passes the gate tests. Committed file hashes to 36e7c69b..., equal to the pin and the publication row. 53 tests pass.
3. replication-publication.md "Paper extract": adequate against accidental or one-file edits, not a full authentication: the row is self-recorded, names no digest of the run records and no commit of the extract code. Closure without shipping the records: record a sha256 over the sorted record inventory, the commit of replication_extract.py, deposit the records in the public replication archive; optionally have --check print the digest.
4. results/pods/paper_check.sh and paper_commit.sh enforce the pin but are untracked; state the pytest commands in replication-publication.md. Non-blocking.
5. established_honest_audit_rate may be None with nonzero counts (caught by freshness and pin). Optional. Non-blocking.
6. New errors in the diff: none.

CONFIDENCE: 0.9
