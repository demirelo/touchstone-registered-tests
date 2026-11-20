# Replication implementation review r10: consensus and caveats

Reviews: `docs/revision/roster/{sol,astra}-rep-impl-r10.md`: both **accept-with-caveat** (confidence 0.96 each). By the
review rule, accept-with-caveat is consensus; the caveats are applied here without another round.

| # | Caveat (Sol #, Astra #) | Status |
|---|---|---|
| Q1 | A cost-stopped record with measured rounds now has those rounds validated (numbered, finite, well-formed knobs); malformed rounds make it an invalid record, counted as not continued instead of stopped. Either way the frozen winner is kept and a resume reruns the cell, so only the counts changed (S1, A1) | fixed in `rep_collect.cont_problem`, `_round_fields_problem`: test_a_cost_stopped_record_with_a_malformed_measured_round_counts_as_not_continued (failed first on 12c912c) |
| Q2 | Claim limited (S2): P1 in `rep-impl-r9-response.md` concerns recomputed disagreements only. A well-formed failing comparison is mismatch evidence by itself, even when the round data are malformed (ruling 10's first evidence path), so such a record removes the primary set and stops the resume with exit 4 | documented here and in P1 |

Checks: `uv run --frozen pytest -q docs/revision/followup3/` (230 pass, 1 skip). Launcher and harness unchanged since the
47 of 47 harness log.
