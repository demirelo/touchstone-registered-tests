VERDICT: reject

CORRECTIONS:

1. **Blocker — §7; `docs/revision/churn/churn_v2.py:361–372`.** Run the cost check after memory preflight selects the worker count. It currently uses the requested count. A read-only check with 18 doubling jobs admitted 2,654 seconds at nine workers, then dispatched two workers, which require an estimated 11,944 seconds. Include preflight time and repeat admission after any worker reduction. This is an implementation error, separate from the disclosed risk of stage overruns.

2. **§7; `docs/revision/churn/churn_v2.py:370–374`.** Apply the memory limit to diagnostics. Each stage restores `workers_eval`, so diagnostics discard earlier reductions. Preflight also measures only `jobs[0]`; it does not cover variation across markets, rules, or doubled winners. Use a justified conservative peak and retain the resulting limit for each applicable stage.

3. **§7; `/Users/oemer.demirel/Projects/touchstone/results/pods/reset_pod.sh:85–92`.** Resolve the shutdown contradiction before launch. The launcher deletes the pod at its hard deadline, including during a stage; the plan says no running stage is ever killed. State the watchdog exception and its limit, or change the launcher. Preserve verified deletion and cumulative retry charges.

4. **none — §§2–6.** Honest replacement fairly tests sensitivity to the identity-age concern. It also changes history and ban escape, as disclosed. Rates 0.01 and 0.05 support illustrative sensitivity analysis without empirical calibration. Frozen references support the stated estimand; reference degradation can increase gains and move rule contrasts either way. Conditional intervals, matched baselines, the disclosed peek, and narrowed expectation 4 are adequate.

5. **none — §3.** Injection reaches search, evaluation, and doubling. Candidate-cache clearing, reference rescoring, separate records, mandatory allocation time and price, and the saved production gate address the corresponding round-2 corrections. The first-offer diagnostic matches R3’s age definition.

6. **§7, validation.** Cost arithmetic reproduces: 41.06 core-hours, USD 4.43 benchmark cost, USD 3.33 estimated pod cost; the reservation becomes USD 5.54. I could not independently rerun the 19 tests because Matplotlib requires writable cache storage. Add regression coverage for corrections 1–2 before the pod.

CONFIDENCE: 0.96.