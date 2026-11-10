VERDICT: reject

CORRECTIONS:

1. **Blocker — §7; churn_v2.py:256, :307.** Omitting `--started` silently disables the spend check. Require a valid allocation timestamp for production runs and preserve cumulative charges across retries. The check limits dispatch using estimates; it cannot guarantee an $8 ceiling when stages overrun or the pod remains allocated. State this limit and specify deletion on completion or failure. Pass $4.43 to the reservation command: it already applies the 1.25 multiplier.

2. **Blocker — §3(c); churn_v2.py:319.** The mapped reproduction gate now checks search, evaluation, and doubling, and its failure stops the default full run. However, separate-stage commands and `--gate skip` require no saved passing gate. Require a matching gate record before production churn dispatch, including resumed stages.

3. **§7; churn-plan.md:150; churn_memory.py:17.** The stated 25 GB fits within 28 GiB: 25 decimal GB is 23.3 GiB. Even 9 × 2.8 GiB leaves 2.8 GiB. But the measurement covers one old R3 attack profile; the four-profile task estimate remains extrapolated. Before nine-worker evaluation, verify the actual cgroup limit and full-task peak memory, including parent overhead and variation across markets and policies. Reduce workers if necessary. The stated cost arithmetic reproduces: 41.06 core-hours, $4.43; 5.95 billed hours, $3.33.

4. **§4; churn_v2.py:131; sim/mechanisms/factorial.py:27, :69.** The newest diagnostic uses creation time across all current identities. R3 uses first-offer time and selects among identities with assigned jobs. Label the existing statistic precisely; add the mechanism-relevant statistic before using it to explain targeting.

5. **§6, expectation 4.** Higher newcomer audit shares under R3 than under C* and B3 establish a cross-rule difference. They do not establish that exposure “shifts” relative to no churn. Narrow that sentence or specify a matched baseline comparison.

6. **None — §§2–5 and remaining round-1 corrections.** Churn injection, cache clearing, frozen-reference rescoring, record separation, doubled diagnostics, pooling, and empty-bin handling appear correct. The rates support illustrative sensitivity analysis. Frozen references support the stated estimand, with the disclosed bias limits. Baselines reproduce; intervals and expectations retain appropriate exploratory limits. I could not rerun tests because imports require writable cache storage.

CONFIDENCE: 0.94.