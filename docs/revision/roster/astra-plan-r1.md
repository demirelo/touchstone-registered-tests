VERDICT: reject

CORRECTIONS:

Evidence notation: **P** = [build plan](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-22-revision-build.md); **D** = [accepted design](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/specs/2026-10-22-revision-program-design.md).

1. **Task 1 — Complete the pacing and selection interfaces.** Pass `L` to `ReservePacing`; `bind(cfg)` cannot obtain it from `MarketConfig` (`P:41`; `sim/config.py:17–27`). Specify independent priority and residual branches: the existing `select_audits` always applies priority and has no P/G switches (`P:75`; `sim/mechanisms/proposed.py:61–101`). Preserve B3’s stable assignment order for equal audit keys (`sim/mechanisms/audit_random.py:28–34`). Add positive-quota tests for every cell; `test_no_audit_when_budget_or_service_empty` would pass if F010 always returned no audits.

2. **Task 1 — Make the oracle checks executable and complete.** Return `EpisodeResult`, or records plus accounting, from the helper. `run_records` returns only records, while the test calls undefined `accounting_of`; records omit effort costs and terminal accounting (`P:44–55`; `sim/market.py:195–208`). Run the five-seed matrix with `--runslow -m slow`: the stated command skips it (`P:66–79`; `tests/conftest.py:37–47`). Pin the base commit and literal frozen-file hashes before implementation; retain the byte-identical rule in `P:17`.

3. **Task 2 — Correct the memory-window boundary.** Change `test_mem_window_boundary` to include passes at `t - M` and exclude `t - M - 1`, subject to the failure boundary. The current test explicitly requires the wrong implementation (`P:106`; `D:85–87`).

4. **Tasks 4–5 — Expand the policy contract tests.** Run X7 embedding checks across the common parameter grid and applicable rules, not only four rules at `(200,10)` (`P:172–178`; `D:186–188`). Specify the factory mapping from knob `lambda` to constructor argument `lam`; `Family.make` forwards keyword names unchanged (`P:166`; `sim/policies/families.py:73–74`). Force exits and assert replacement actions directly. Headline equivalence alone can pass with hardcoded constants (`P:208`). For X7, `k_F=0` still leaves claim subtraction `s` and bid markup `w`; do not require HonestMax unless those are zero (`D:183–184`).

5. **Task 6 — Specify replacement-stream assignment.** If stream 0 fails, retain streams 1–5 for labels fresh1–fresh5 and assign stream 6 to fresh0. “Skipping streams” can instead shift every label (`P:225`; `D:293–295`). Make `test_limit_replacement_keeps_label_order` assert stream indices, not just labels. Establish generator golden values independently; recording the first green output can preserve an incorrect draw algorithm (`P:235–238`).

6. **Task 7 — Connect proof verification to header verification.** Supply the verified anchor height and hash to the reader, verify the complete A-through-H+6 chain, and require its H hash to equal both explorers’ answer. Parsing `ots info` and independently testing `verify_chain` do not establish this connection (`P:252–262`; `D:305–315`). Add rejection tests for an unrelated valid chain and a truncated chain. `test_read_final_returns_agreed_hash` could otherwise pass without anchor verification.

7. **Tasks 4 and 10 — Define the frozen-search adapters.** Route X7 explicitly through its 769-vector control set and evaluate embedded H3 incumbents through a new wrapper around `cma_search`. The frozen `attack_search` accepts no extra incumbents, while `corner_controls` calls `Family.corners`, which enumerates all 8,192 X7 corners (`P:166,329–331`; `sim/reference.py:39–42`; `sim/search.py:155–157`; `sim/policies/families.py:76–84`). Test actual evaluated vectors and budget counts; standalone corner-construction tests do not check runner integration.

8. **Task 10 — Make references unambiguous.** Include configuration/rho in reference keys and paths. `reference/<market>/<rule>.json` collides between headline rho=0.2 and rho=1 (`P:330–331`; `D:334`). Store candidate family and injected constants, define cross-family tie order, and specify the bank’s source manifest. Existing candidate serialization stores only name and knobs and reconstructs using one supplied family (`sim/records.py:45–53`). `test_reference_menu_is_union_of_two_searches` would pass despite incorrect reconstruction after resume.

9. **Task 10 — Require completeness before final freeze.** Validate the required manifest, dependent searches, joint-reference freezes, envelope choices, and fixed-attack banks before writing the freeze. Checking only hashes listed in an existing freeze permits an empty or incomplete freeze (`P:331,340–345`; `D:249–253`). Test a valid-hash freeze missing required records and assert zero evaluation episodes. Define atomic record writes and crash recovery; provenance checks alone do not cover truncated records.

10. **Task 10 — Add the H4 loader contract now.** Build hash verification, family-interface validation, and the explicit exclusion state using synthetic bundles. No task currently specifies this code, although it must support the separate H4 session and precede evaluation (`P:329–346,452`; `D:200–206`). Test hash mismatch and load failure without accessing sealed material.

11. **Tasks 9–10 — Complete doubling diagnostics.** Specify merging the original and additional searches, separate attack/reference changes, objective-specific units, and the 0.005 incomplete threshold. Include W1’s transition from no feasible candidate to a feasible candidate (`D:257–267`). `test_doubling_does_not_touch_frozen_records` would pass if the diagnostic always reported success (`P:343`). Add deterministic tests for these outcomes.

12. **Task 11 — Correct the first cut.** Remove **48**, not 24, fresh whole-system cells: four rules × two families × six markets (`P:368`; `D:330,371–373`). Assert retained cell IDs as well as totals.

13. **Tasks 12–13 — Produce all coverage inputs and handle reduced branches.** Add the nine C*/S2 development searches and their three-family references; Task 12’s selection interfaces do not produce them (`P:384,408`; `D:352,440–445`). Make endpoints branch-aware: two-market Q4 has 24 tested endpoints while retaining denominator 36 (`P:409,415`; `D:473–474`). Test exact profile membership and shared seed alignment, not only endpoint counts.

14. **Tasks 8 and 13 — Add deterministic statistical failure tests.** Verify stratified studentization, independent resampling between strata, largest-passing-kappa selection, and rejection when any validation endpoint fails (`D:402–404,452–464`). Equal-weight and denominator tests can pass with incorrect variance or unconditional admission (`P:288,419`). Add constant-data and unattainable-crossing cases to p-value inversion; the bound need not equal the null in those cases (`P:284`; `sim/intervals.py:48–49`).

15. **Task 14 — Make the pod entry executable.** Add `--workers` support or provide a compatible adapter. The reused launcher always appends `--workers` and `--out`, but the proposed benchmark CLI does not accept `--workers` (`P:431–434`; `results/pods/explore_pod.sh:56`). Add a local argument-parsing smoke test; cost-table tests would pass despite immediate pod-command failure.

CONFIDENCE: 0.96
