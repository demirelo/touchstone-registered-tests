VERDICT: reject

CORRECTIONS:

1. `docs/revision/followup3/replication_analysis.py:97` — G5 remains incomplete. `paired_changes` still produces a five-degree-of-freedom t interval with fewer than six markets. An in-memory five-market example returned `complete=False` with a non-null interval. Require all six markets, as `absolute` now does.

2. `docs/revision/followup3/rep_collect.py:318` — G4/ruling 8 remains incomplete. Require one `shares.per_episode` entry per evaluation seed. `diag_ok` accepted one episode for two seeds, and `_audit_of` used its counts. Truncated diagnostics can therefore change expectation 5.

3. `docs/revision/followup3/rep_collect.py:245,330` — G2 misses a downstream requirement. A zero `sstar` passes `base_problem`, then causes `ZeroDivisionError` in `terms_of`. Validate the normalization denominator before scoring; mark an invalid base cell unscorable.

4. `docs/revision/followup3/rep_collect.py:197–230` — G3/ruling 10 remains incomplete on resume. `run_queue` does not apply `cont_problem` before reusing saved records. A saved gate with the wrong stage, wrong ID and empty rounds returned exit 0 when provenance and comparison fields matched. Validate saved gate and continuation records before reuse or further work.

5. `docs/revision/followup3/rep_collect.py:390–412` — Restore the section-4 fallback. A nonfinite continuation currently sets `bad_cont` and removes the entire primary analysis. The plan requires that cell to retain its validated frozen winner and count as “not continued.” An in-memory NaN mutation reproduced this failure.

6. `docs/revision/followup3/rep_pod.sh:377`; `docs/revision/followup3/rep_v2.py:404` — G6 does not complete diagnostic-loss recovery. The restart reduces only continuation workers. Diagnostics still use `workers_eval`; at 28 GB, the reproduced counts were continuation 5→3, diagnostics 5→5. Reduce the failed pool’s workers and test that path through the launcher.

7. `docs/revision/followup3/rep-impl-r2-response.md`, G2–G6/G8/G9 — Update the affected completion claims and rulings after these fixes. All 105 tests passed; the supplied 47/47 harness hashes match. Those checks do not cover the failures above.

CONFIDENCE: 0.98.