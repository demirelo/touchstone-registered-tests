VERDICT: accept-with-caveat

CORRECTIONS:

1. **§7; churn_v2.py:256, :307.** Require a valid allocation timestamp through `--started` in the pod launch command. Omitting it disables the cap check. Record the actual hourly price and previous failed-attempt charges. Ensure pod deletion on every exit. Describe USD 8 as an estimate-based stage-admission limit: an overrunning stage can exceed it under the approved no-kill policy.

2. **§7; churn-plan.md:159; scripts/budget_v2.py:99.** Specify the reservation command’s amount explicitly. Pass the unpadded USD 4.43 estimate; the wrapper applies 1.25 and reserves about USD 5.54. Passing USD 5.54 reserves about USD 6.93.

3. **none — §§2–6.** Honest replacement fairly tests sensitivity to identity age, while also changing identity history and ban escape. The rates are adequately labelled illustrative, without empirical calibration. Frozen references are acceptable for the stated estimand; their degradation can increase gains and move rule contrasts either way. The corrected baselines, conditional intervals, doubled diagnostics, and disclosed prior peek support exploratory conclusions.

4. **none — §3; churn_v2.py:62.** Injection reaches search, evaluation, and doubling. Candidate-cache clearing and frozen-reference recomputation address round 1’s environment mismatch. The mapped p=0 gate stops the full production path on failure. Separate IDs and directories protect registered records.

5. **none — §7.** Cost arithmetic checks: 41.06 core-hours, USD 4.43 benchmark cost, and USD 3.33 estimated pod charges. An independent read-only, 200-seed four-profile check at p=0.05 peaked at 2,532 MiB; nine such workers imply 22.3 GiB, below 28 GiB. This supports the proposed memory allocation. Seven tests requiring no file writes passed.

CONFIDENCE: 0.95.