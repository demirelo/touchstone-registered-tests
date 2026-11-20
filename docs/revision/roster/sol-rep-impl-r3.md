VERDICT: reject

CORRECTIONS:

1. `rep_collect.py:194–222,357–359` (G3): Apply `cont_problem` before reuse. A saved record containing only provenance, status and an exact-comparison summary returned exit 0 without running a worker. The gate check also replaces `mkt` with `None`, which disables held-out seed validation. Check gate values and round contents, not only list length.

2. `rep_collect.py:245–247,330–334` (G2/G3): Reject zero normalizers before division. A continuation with `sstar=[0,1]` passed validation, then raised `ZeroDivisionError` in `terms_of`. Apply the required invalid-record outcome for each record kind.

3. `rep_collect.py:300–327,366–381` (G4): Require one audit episode per evaluation seed and the prescribed age-bin count. A row with 200 seeds, one episode and one bin passed `diag_ok`. Also bind frozen diagnostics to the job, rate and run; seeds and knobs alone cannot establish that identity. These gaps can change expectation 5.

4. `rep_collect.py:390–413` (G3): Preserve the plan’s nonfinite-continuation fallback. With valid base records and a passing gate, one NaN continuation gain made the entire primary set unavailable. Section 4 requires the validated frozen winner and a “not continued” count.

5. `replication_analysis.py:97` (G5): Suppress paired-change market t intervals unless all six markets exist. A five-market probe returned `complete=False` with a non-null t interval. The new test checks only absolute contrasts.

6. `rep_v2.py:404–405`; `rep_pod.sh:377` (G6/G7): Reduce diagnostic workers on the launcher’s restart. The restart changes only `--workers-cont`; diagnostics still use `workers_eval`. A 28 GB probe produced continuation counts 5→3 but diagnostic counts 5→5. Add a diagnostic-loss test through both layers.

7. `rep-impl-r2-response.md:G2–G9`; `rep-launcher-notes.md:Rulings 8,10,11`: Correct the completion claims after these fixes. G1, the x86 guard and the stated ruling-12 caveat are acceptable. All 105 Python tests pass. The supplied 47/47 harness hashes match, but those checks do not cover the failures above.

CONFIDENCE: 0.98