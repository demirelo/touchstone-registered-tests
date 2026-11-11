VERDICT: reject

CORRECTIONS:

1. **Blocker — §7; churn_v2.py:355, :369; scripts/revision_v2.py:1097.** Memory preflight can measure a skipped task. On resume, `_run_one` reuses a valid record, so the child reports memory use without executing evaluation or doubling. The driver then treats this as a full-task peak. Force actual measurement or retain a validated conservative peak. Add a regression check with existing production records.

2. **Blocker — §7; churn_v2.py:391, :407, :411.** Retain memory limits across separate-stage commands. Each `_run_rate` call resets the limit to `workers_eval`; standalone diagnostics perform no preflight. A read-only control-flow probe confirmed two-worker evaluation and diagnostics, followed by nine-worker standalone diagnostics. Load the saved limit, validate its applicability, and refuse dispatch without sufficient memory evidence.

3. **§7; churn-plan.md:204.** Update billed-time arithmetic for serial preflight tasks. At nine workers, evaluation requires three serial tasks plus two waves; doubling requires one serial task plus two waves. Using the plan’s timings and slowdowns gives approximately **6.88 hours, USD 3.85**, including preparation, before worker reductions. The stated 5.95 hours and USD 3.33 omit this scheduling cost.

4. **none — §§2–6.** Honest replacement fairly tests sensitivity to identity age, with disclosed history-reset and ban-escape effects. Rates 0.01 and 0.05 are acceptable illustrative settings without empirical calibration. Frozen references support the stated estimand; reference deterioration can inflate gains and move contrasts either way. Separate profit terms, conditional intervals, matched baselines, and expectations written after the disclosed peek support exploratory interpretation.

5. **none — §3.** Injection reaches search, evaluation, and doubling. Candidate-cache clearing, reference rescoring, suffixed IDs, and separate output directories address the earlier corrections and protect registered records.

6. **none — §§3(c), 7.** Round-3 corrections now cover admission after worker reduction, bit-identity gating through `--require-identical`, and the documented watchdog exception with cumulative attempt charges. Memory corrections remain incomplete as specified above. Launcher implementation remains outside this review. I did not rerun the full 23-test suite.

CONFIDENCE: 0.96.