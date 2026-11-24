# Fable 5.2, review round 3 (rep-paper-r3), as returned to the session on 2026-11-24

VERDICT: accept-with-caveat

CORRECTIONS:
1. main.tex:382 (caption of Table 30): new gap. The table prints a second line of paired seed-bootstrap intervals and a pooled interval under "Mean"; the caption describes only the changes and the mean. Add the Table 31 wording.
2. replication_paper.py _validate: partly fixed, rest does not block. All requested guards present and hold on the committed data. Still passing with the same analysis hash: an in-range allocation share edit; audit counts edited together with focal_audit_rate; flipped x; x = True; a share set to None with nonzero counts. These values exist only in the extract and binding.recomputed is self-declared. Closure: pin the sha256 of replication-extract.json in the gate or a test; require type(x) is int and non-None shares where counts are nonzero.
3. replication_extract.py recompute binding: fixed by code reading only (records not in the worktree); state that the byte-identical recompute was run on the pod records.
4. Other round-2 corrections fixed: run-code attribution and rep2-rep4; winner-set qualifiers; label everywhere (gate refuses); 95% t intervals; replacement switch (Table 33: 6/6, 1/3, 4/6 primary; 5/6, 3/6, 3/6 frozen); four-decimal bounds.
5. No new check is too strict; --check ok; 49 tests pass; continued cells 20 = 20 differing cells. Note in the docstring that the rule would refuse a future continued winner with identical terms.
6. Brief items 3 and 4: none. No new overclaim, contradiction or stale text.

CONFIDENCE: 0.88
