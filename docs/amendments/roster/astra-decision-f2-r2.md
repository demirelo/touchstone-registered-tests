**Difference 1 — freshness window.** Choose `0 <= t - first_round[i] < L`: a replacement that behaves honestly for two rounds escapes first-round-only priority before cheating, but remains eligible under every registered `L`. Neither window prevents cheating after expiry; the longer window also spends priority audits on honest newcomers, although roughly 199 replacements do not imply 199 concurrent entrants because exited identities have no served jobs. At round zero, both windows allocate all 10 audits through priority among 50 jobs; this is acceptable under the unchanged quota, but the `L` window also affects subsequent startup rounds and must pass F3. Both preserve identity relabeling and require no entity linkage; amendment 1’s relative-age ordering supports newest-first ordering more directly than either particular cutoff.

**Difference 2 — priority order.** Choose descending `first_round`, then ascending `(audit_key, job_index)`. At round one with `L = 10`, initial identities remain fresh: key-only ordering can spend all 10 audits on their jobs and miss a six-job replacement, despite `k >= 6`. Newest-first ordering prevents that counterexample; for identities with equal arrival times, audit keys provide the registered random order, with job index only resolving exact ties.

**Other resolutions.** Priority selections count in `audits_i` before residual selection and persist into later rounds; omitting them would falsify T2’s registered statistic. The [harness](/Users/oemer.demirel/Projects/touchstone/.worktrees/proposed-rule/scripts/falsify_proposed.py:249) already runs `tests/test_proposed.py`, so new fixtures require no harness edit, and F2 remains unchanged. The stopping statements differ: “selected configuration” can exempt a registered early diagnostic kill; use “any registered kill,” while distinguishing tuning scores from falsification verdicts. Repeat all 36 configurations under R3, with no pruning from prior scores.

**FINAL CLAUSE:**

> **Status and registration.** Amendment 2 remains KILL, and its results remain reported. Amendment 3 registers one successor, R3, and one development cycle. Register this text and revised F1 fixtures under a signed, timestamped `lock-2026-10-17-amendment-3` tag before implementing R3. This addendum supersedes only the specified design and procedure provisions; retain the original amendment YAML and coverage artifacts unchanged. Verify the freeze and final evaluation against the new tag.
>
> **Design replacement: `audit_selection.split`.** Let `k` be the audit count after the unchanged schedule, served-job cap, and audits-left cap. An identity is fresh exactly when `0 <= t - first_round[i] < L`. `first_round` remains the round of its first offer, unchanged after a ban.
>
> List all served jobs of fresh identities in ascending `(-first_round[i], audit_key[j], job_index[j])` order. Select the first `q = min(k, length of list)` jobs. Count these selections in their identities’ audit totals before residual selection.
>
> Set `r = k - q`. From unselected served jobs, select `ceil(r/2)` jobs using registered T1 or T2, then `floor(r/2)` jobs uniformly without replacement through ascending `(audit_key, job_index)`. T2 includes all selections already made and recomputes its ratio after each targeted selection. Persist every audit count exactly once. Select no job twice.
>
> Apply this procedure at round zero and with simultaneous entrants. Use only opaque-identity history; never use generation, entity linkage, or identity labels for ordering. All other design provisions remain unchanged.
>
> **F1 fixtures.** Retain every existing contract requirement and isolated-module check; revise only expectations superseded by the new selection procedure. Add checks for:
>
> - Ages `0`, `1`, `L-1`, and `L`, for each registered `L`; first offer without service; ban return without age reset.
> - Round zero with 10 identities, 50 served jobs, and `k = 10`.
> - A six-job newest entrant competing with older fresh identities; simultaneous entrants; equal audit keys.
> - Priority sets below, equal to, and above quota; empty sets; zero quota; odd and even residual quotas; both targeting variants.
> - T2 priority-count persistence, sequential ratio updates, no duplicate selections or counts, and unchanged caps.
> - Identity relabeling across different ages and tied arrival times.
>
> **Tuning.** First run F1 and the unchanged full F2 diagnostic at prior parameters `A, T1, tol = 0.16, L = 10`, including F2’s T2 override. If neither kills, repeat the complete registered 36-point grid, objective, budgets, top-three recheck, seed namespaces, tie order, and logging under R3. No prior score may select, exclude, or prune configurations. Test no alternative window or priority policy.
>
> **Falsification and stopping.** F2–F5 retain their exact conditions, variants, thresholds, and seeds. Rebuild all affected searches, ablations, banks, references, evaluations, controls, and all-deviator records; reuse only verified unaffected records. Run complete F1–F5 and record the new `f5_bank`. Any registered kill, including the early diagnostic, ends R3 development: no replacement candidate, design revision, gate revision, or selection retry. Ordinary tuning scores are not kill verdicts. Freeze only after all required gates pass; then perform the registered final evaluation without another development cycle.
>
> **Permitted files.** Registration changes may touch `tests/test_proposed.py`, `tests/_proposed_fixtures.py`, and the Amendment 3 registration, ledger, and timestamp documents under the existing `docs/` permission. Freeze the tests in the registration tag. Subsequent implementation changes are limited to `sim/mechanisms/proposed.py`, `experiments/proposed.yaml`, and `experiments/proposed_describe.yaml`, with reports under `docs/` and fresh result directories. No harness or verifier edit is permitted.
>
> **Disclosure.** “After reporting Amendment 2’s anticipated F2 kill, we registered one successor using observed development results, retained F2 unchanged, and kept the sealed bundle unread until the registered final evaluation.”

**CONFIDENCE: 0.88** in this resolution, not in R3 passing.
