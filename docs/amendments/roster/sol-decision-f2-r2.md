**Difference 1 — freshness window.** Use `0 <= t - first_round[i] < L`: first-round-only priority ends before D2 can recover its markup and resume cheating one or two rounds after entry; the L window covers those delays, although it cannot prevent cheating after age L. Honest newcomers also consume priority audits for L rounds, but the stated corner usually has one active entrant with at most six jobs; old identities that have exited consume none. At round zero, both windows assign all ten audits to priority among fifty served jobs; the L window can also consume the entire quota during the initial L rounds, which is an explicit cost to test under unchanged F3. Both windows preserve identity relabeling and need no entity linkage, but neither follows directly from Amendment 1’s “newest identity first,” which specifies an order rather than a window.

**Difference 2 — priority order.** Use descending `first_round`, then ascending `(audit_key, job_index)`. With the L window, consider round one: a sole six-job replacement competes with still-fresh initial identities for ten audits; key-only ordering can select ten incumbent jobs and reproduce the F2 coverage failure. Recency ordering prevents that failure when the replacement is uniquely newest and its jobs fit the quota. Among identities with the same first round, audit keys provide the registered random ordering; identity numbers would introduce arbitrary preference.

**T2 counts.** Count priority selections before the first residual ratio comparison, then update after each targeted selection. Otherwise an identity audited during priority retains an artificially low ratio and can receive further targeted audits ahead of a less-audited identity.

**Fixtures and harness.** Register changes to both `tests/test_proposed.py` and `tests/_proposed_fixtures.py`, with the cases specified below. [The existing harness](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:248) already runs that F1 test file and checks unchanged F2 under both variants, so it needs no edit.

**Stopping.** The two formulations are not identical: “selected configuration” could permit dismissal of an earlier registered kill because that configuration was not ultimately selected. Use “any registered kill,” including a preliminary registered gate check; an ordinary low tuning score is not a kill.

**Tuning.** Repeat all 36 configurations under the changed selection procedure, with the registered search and recheck. No previous score may select, exclude, or prune a configuration.

**FINAL CLAUSE:**

> **Status.** Amendment 2 remains KILL, with its results preserved. Amendment 3 registers one successor, R3, and one development cycle. This signed, timestamped addendum supersedes only the provisions stated below; the original binding YAML and coverage artifacts remain unchanged.
>
> **Design replacement.** Let `k` be the audit count after the unchanged schedule, served-job cap, and audits-left cap. Identity `i` is fresh exactly when `0 <= t - first_round[i] < L`. Form the priority list from all served jobs of fresh identities, ordered by descending `first_round[i]`, ascending `audit_key[j]`, then ascending job index. Select its first `q = min(k, list length)` jobs.
>
> Remove those jobs and count their audits before residual selection. Set `r = k - q`; select `ceil(r/2)` remaining jobs using registered T1 or T2, then `floor(r/2)` uniformly without replacement using ascending `(audit_key, job_index)`. T2 uses cumulative served jobs through current allocation and audit counts including priority selections, updated after each targeted selection. Record every audit exactly once.
>
> Apply this procedure at round zero and with simultaneous newcomers. `first_round` remains the first-offer round, including offers receiving no jobs; a ban return does not reset it. Use only opaque-identity history, without generation indicators or entity linkage. All other design provisions remain unchanged.
>
> **Tuning.** Recompute the complete registered 36-point grid, objective, search budgets, twin and reference procedures, top-three full-budget recheck, seed namespaces, tie order, and logs. Prior scores cannot prune the grid. No alternative window or priority policy may be tested in this cycle.
>
> **Falsification.** Keep F2–F5 unchanged, including both F2 variants, applicability, per-seed profit, thresholds, and seeds. F1 retains all unaffected contracts and replaces only superseded selection expectations. Add fixtures for ages `0`, `L-1`, and `L` at each registered L; cheating after one or two honest rounds; first offers without service and ban returns; round-zero quota exhaustion; competing fresh identities with equal and unequal first rounds; key ties; zero, partial, and full priority use; odd/even residual splits; T2 counts before and during residual selection; unique selections, caps, and relabeling under both variants.
>
> Repeat all affected searches, descriptions, bank construction, and downstream records; reuse only records with verified unchanged dependencies. Record the new `f5_bank` and run complete F1–F5 before freeze.
>
> **Stopping.** Any registered kill ends R3 development, including a preliminary registered gate check. Report it; permit no further candidate, retuning, design change, or gate revision within this study.
>
> **Files.** Permit only `sim/mechanisms/proposed.py`, `experiments/proposed.yaml`, `experiments/proposed_describe.yaml`, `tests/test_proposed.py`, `tests/_proposed_fixtures.py`, and `docs/`, plus generated results. Include revised contracts in the signed Amendment 3 registration tag before R3 implementation; verify freeze and evaluation against that tag. No harness edit is permitted.
>
> **Disclosure.** “After the predicted Amendment 2 kill and inspection of development results, we registered one successor before implementation, preserved the kill and unchanged F2, and retained the sealed bundle unread.”

**CONFIDENCE: 0.86** in this resolution, not in R3 passing.
