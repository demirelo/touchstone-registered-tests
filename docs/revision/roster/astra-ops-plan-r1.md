VERDICT: reject

FINDINGS:

1. **Critical — Plan:70,87,204; `scripts/coverage_v2.py:86–91`.** Failed validation leaves the selected numeric `kappa` intact and sets `admitted=False`. Promotion requires only a validation block. This permits an unvalidated confirmatory decision. **Repair:** export an effective kappa only when validation admits it; otherwise export null. Verify replication counts, resamples, branch, and endpoint results.

2. **Critical — Plan:103–104,119–121.** The draw records `confirmatory=False`, but the report interface does not consume that status. A late publication can therefore produce confirmatory Q1/Q4 claims. **Repair:** bind the report to `instances.json` and suppress confirmatory claims when publication was late or unverified.

3. **Important — Plan:102–106; `scripts/block_draw.py:135–142`.** Checking `anchor.status=="verified"` does not bind an imported draw to this protocol. The built reader emits `protocol_sha256`, which Task 4 omits. **Repair:** compare the exact protocol digest and verify H=A+144, header/hash consistency, explorer agreement, and depth. Reject substituted draw records.

4. **Important — Operation 2; `scripts/benchmark_v2.py:23–33,45–68`.** Every design §11 step has an operation, but step 3’s cut branches lack implementation. `cost_table` uses fixed counts and accepts no cuts or coverage branch. Tasks 1–7 add no replacement. **Repair:** add branch-aware costing, including changed reference menus and pool sizes, before selecting cuts or seeking approval.

5. **Important — Plan:190–203,224; `scripts/benchmark_v2.py:185–190`; `scripts/tune_v2.py:156–169`.** The 16-vCPU benchmark executes workloads serially; tuning also ignores `--workers`. Core-hour estimates can understate billed pod time. Benchmark spend, coverage caps, and development headroom lack a common allocation. **Repair:** specify pod sizes, actual billing rates, utilization, remaining budgets, and aggregate stops. Only the capped benchmark should precede cost approval.

6. **Important — Plan:69–70,197–198.** Promotion requires comparator, four systems, and fixtures together, yet Operation 3 promotes the comparator alone before launching dependent work. This deadlocks. Fixture output also lacks `smoke` and budget fields (`scripts/tune_v2.py:141–148`). **Repair:** define staged promotion and final completeness validation; add fixture metadata.

7. **Important — Plan:203; `scripts/coverage_v2.py:65–80`.** There is no market selector: each proposed coverage-market pod builds every market. This duplicates paid work and output paths. **Repair:** add tested sharding or use one appropriately sized pod. Carry the chosen branch through selection and validation.

8. **Important — Plan:19,182–185,218,226.** Custody permits pre-report loading only on evaluation pods, but Operations 6 and 7 load locally. Operation 1 also omits the sealed-session commit required by design §11 step 2. **Repair:** specify the private commit receipt, pod-only load decision, external custody path, and a local validator that never loads H4.

9. **Important — Plan:103,223–224; `scripts/revision_v2.py:842–845`.** Each pod independently excludes unavailable H4; it does not consume the recorded H4 decision. Pods can freeze different manifests while the report trusts one `h4.json`. **Repair:** enforce one global decision and hash on every pod before evaluation; reconcile any failure before proceeding.

10. **Important — Plan:86,211–212.** The two-commit separation is sound, but the proof is created and upgraded after tagging. Publishing it requires additional commits or leaves the tag checkout dirty, conflicting with `check_commit`. **Repair:** define separate proof-publication commits and an immutable evaluation checkout. Verify the signed tag and protocol inputs, not merely the permitted diff paths.

11. **Important — Task 5, Plan:121,136.** Q1’s six strata and Q4’s lower-tail calls are correct, but reporting is incomplete: Q1/Q4 simultaneous interval tails are unspecified; Q1 headline/per-market descriptive results and Q4’s “generalisation not established” wording are omitted. Q2 cell means alone cannot supply paired seed uncertainty. **Repair:** specify calibrated tails, descriptive fallbacks, and per-seed contrasts before stratified resampling.

12. **Important — Plan:121; `scripts/revision_v2.py:583–591,636–653`.** Q3 lacks explicit training-based welfare winner selection, “no feasible candidate found,” and attacker gains. W0 records contain normalized profit, not gain against the reference. Doubling reporting retains only `incomplete`, omitting measured changes. **Repair:** add the missing record/report work; preserve W1 constraint intervals, coalition member bounds, and diagnostic values.

13. **Important — Plan:129–131,226–227; `scripts/revision_v2.py:555–567,716–730`.** The stop path cannot reliably report partial runs: an unfinished freeze causes rejection, while the proposed local “check” executes missing evaluations. A missing F111/D2+H3 record also affects Q1/Q2/Q3, contrary to “others answered.” **Repair:** add a read-only validator and explicit question dependencies; report unavailable contexts as unanswered.

14. **Important — Task 7.** **Accept the complete-freeze ruling; reject the proposed priority implementation.** `priority` needs `block`, absent from jobs (`sim/manifest_v2.py:84`; `scripts/revision_v2.py:169`). Family waves still execute lower-priority non-X7 work before Q1 X7 (`revision_v2.py:747–752`). **Repair:** order manifest cells and dependency-ready waves; enforce fresh-before-headline scheduling explicitly.

15. **Important — Plan:147,237; `scripts/revision_v2.py:179–182,492–495`.** Reproduction at the report commit constructs provenance using that HEAD, then rejects records from `protocol-v2`. **Repair:** validate against pinned evaluation provenance in a separate checkout or explicit immutable catalog.

16. **Important — Task 6 / Operation 9; `.gitignore:12`.** Results are ignored, and no task assembles the promised fresh-clone artifact. Required files omit paper sources and the released H4 bundle; checks precede paper revision. **Repair:** package all records, sources, bundle, proof, and metadata; verify reproduction after the final paper change.

17. **Minor — Plan:44,50,86,209,217.** The H4 test uses undocumented `--smoke`; lock commands add undocumented `--cuts`, `--h4-sha`, and `--approval`. The draw command does not create its output directory (`block_draw.py:142`). Generator fields are `stream_index`/`rejections`, and `calibrated` returns only a configuration (`sim/instances.py:64,72`). **Repair:** complete CLI contracts and define output conversions/calibration capture.

18. **Important — Plan:50–53,72,89,106,126–132,149,165.** Weak tests include synthetic promotion/reproduction round trips, late-publication boolean checks, H4 exclusion without runner execution, and seed tests checking only an upper bound. The priority test’s `CRED` lacks tuned parameters (`tests/test_revision_v2.py:18`; `revision_v2.py:121–123`). **Repair:** use producer-shaped fixtures, independent numerical oracles, exact seed allowlists, and mutations for rejected coverage, stale evaluation records, substituted draws, missing freezes, and actual stage order.

DECLINED TO JUDGE: Paid performance, live prices/publication, launcher internals, filesystem atomicity, and process concurrency. No tests or paid operations were run. Neither sealed bundle was read.

CONFIDENCE: 0.95.