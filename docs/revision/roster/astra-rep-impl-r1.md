VERDICT: reject

CORRECTIONS:

1. `commitment.py:24,31`; `rep_pod.sh:108`: Enforce a required manifest file set, including configuration inputs and dependencies. Verify the executing launcher and helpers. Partial manifests pass; the driver also accepts an empty manifest.

2. `rep_v2.py:95,106,134,346`: Bind records and resumes to manifest, draw and driver hashes. Reject uncommitted parameter overrides, redraws and calibration overwrites. Enforce Linux/x86 calibration reuse.

3. `rep_pod.sh:71`: Verify that pod 2’s instances and records belong to the supplied committed draw. Inventory hashes alone do not establish this.

4. `rep_collect.py:140`: Validate doubling records, provenance, dependencies, flags, statuses and 200 ordered seeds before scoring. Fix missing-continuation counts and mismatches hidden by missing evaluations. A synthetic invalid evaluation with no doubling record was accepted.

5. `replication_analysis.py:51,84,105`: Require all six specified markets and matching seed vectors. Five-market input scored all five expectations “met.” Missing rates can crash; `zip` silently truncates unequal vectors.

6. `rep_v2.py:329`: Add absolute-contrast market intervals, per-market seed intervals, attack/reference terms and efficiency. Compute expectation 5 for primary winners; frozen-only diagnostics change the planned estimand.

7. `rep_v2.py:243`; `rep_collect.py:126`: Require both gates. Run the first p=0.05 gate before remaining churn work, regardless of flags. An empty queue currently skips it. `followup2/convergence_v2.py:152` permits differences of 1e-9 instead of requiring identity.

8. `rep_collect.py:122,127,136`: Isolate the gate in a worker; handle its failures through codes 5/6. Do not skip every saved record indiscriminately. A cost-stopped gate dispatched remaining work and returned 0, permitting false `RUN OK`.

9. `rep_pod.sh:218,222,327,360`: Write inventories on failure/stop paths. Retry incomplete pulls before deletion. Currently failures leave absent/stale inventories, and partial output can trigger deletion without another pull.

10. `rep_pod.sh:140,177,189`: Require the specific pod-1 spend and a shared launch lock. Identical launch tags are refused after recording spend; document separate launch suffixes.

11. `cost_estimate.py:38–47`: Recalculate actual scheduling: six churn-search waves, not three; include serial memory probes and the gate’s serial continuation rounds.

12. `churn/churn_v2.py:473`: Admit churn-search workers against memory; this path bypasses `admit_workers`.

13. `rep-launcher-notes.md:50`: Accept rulings 3,6,9; correct 1,2,5,7,8 above. Qualify ruling 4 for transfer/deletion overhead. Checks: 32 Python tests passed; the read-only sandbox blocked the launcher harness.

CONFIDENCE: 0.96