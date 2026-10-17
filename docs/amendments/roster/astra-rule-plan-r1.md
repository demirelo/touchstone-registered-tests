1. **Fidelity: 5/10.** The grid and objective match, but audit ordering and falsification conditions depart from the registration.
2. **Admissible class and module rules: 4/10.** The proposed module boundary is sound; the planned repository changes violate the locked allow-list.
3. **Statistical correctness: 4/10.** The tuning formula is correct, but F2 changes the profit criterion and F3 uses an incorrect false-ban calculation.
4. **Executability: 3/10.** The sweep omits required cells; test fixtures and interfaces contain errors.
5. **H1 description honesty: 1/10.** Both proposed labels omit material behavior; T2 also describes the wrong statistic.
6. **Completeness before freeze: 3/10.** Required search, bank-transfer, doubling, logging, and verification steps remain incomplete.

**OBJECTIONS**

Line numbers below refer to the [implementation plan](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-proposed-rule.md).

- **MATERIAL — Tasks 1–6, lines 36, 127–141, 146–177: forbidden changes.** Committing changes to `sim/tuning.py`, existing tests, new scripts/tests, and `README.md` makes freeze verification fail. Support: `experiments/locked.yaml:81–82` excludes these paths; `sim/claimcheck.py:302–304` rejects changed and newly tracked files outside that list. **Repair:** preserve frozen files and place reproducible support scripts/tests under an allowed `docs/` path, or register a further amendment before changing the pipeline. Correct all commit commands and verify the complete committed tree.

- **MATERIAL — Task 1, lines 41, 61–65, 110: incorrect audit ordering.** A fixed identity order followed by each identity’s jobs does not implement dynamic T2 ranking. Updating counts without selecting the next minimum again is insufficient. Grouping identities can also violate T1’s job-key tie order. Support: amendment lines 103–110 require selection by audit key and T2 counts updated after each selection. The supplied T2 fixture must return **`[1, 3, 0, 2]`**, not `[3, 1, 0, 2]`. **Repair:** select targeted jobs individually; recompute T2 ratios after every selection. Add fixtures with multiple jobs per identity and interleaved audit keys.

- **MATERIAL — Tasks 4 and 6, lines 159, 175: missing sweep cells.** The command does not produce the proposed development or H3 cells needed by F4/F5. Support: `sim/manifest.py:97–121` removes proposed from the baseline list and appends only its six ablation full cells. An isolated manifest check returned six ablation cells, zero development/H3 cells, and zero proposed controls. **Repair:** specify explicit proposed development, H3, and doubling jobs in permitted orchestration code. Assert the expected cell inventory before execution and refuse incomplete reports.

- **MATERIAL — Tasks 4 and 6, lines 159, 175: bank transfer is absent.** A fresh proposed-only output directory cannot supply the registered baseline bank. Moreover, the existing bank stage excludes H3. Support: `scripts/sweep.py:143–155` builds bank membership only from development records in its output; lines 335–339 target only families in `FAMILIES`. **Repair:** define validated baseline-source ingestion, proposed-source inclusion, H3 transfer/projection handling, reference reselection, and provenance hashes. Test that a known transferred attack reaches both D2 and H3 evaluation.

- **MATERIAL — Task 4, line 159, F2: the kill test changes meaning.** Profit below honest-max can remain positive; it does not establish that sustained full cheating is unprofitable. The plan also substitutes every replacement entrant for the registered sole six-job entrant. Support: amendment lines 152–154; `IdentityReplacement` exits after a failed audit, not every round. **Repair:** retain the explicit six-job fixture and test entity profit, including entry costs, against zero. Define the allowance condition precisely. Do not modify the registered allocation or targeting to force a pass: with ten audits, T1 guarantees only five targeted jobs, so the sixth can miss the uniform selection. Report a genuine kill.

- **MATERIAL — Task 4, line 159, F3/F4: incorrect statistical checks.** `N*T*served*Phi(-tol/sigma)` is not an expected ban count. Failures depend on audited jobs; a ban event depends on at least one failure for an identity that round. F3 also omits the explicit efficiency-below-0.90 kill. F4 adds a D1 kill condition absent from the registration and leaves “two seed standard errors” undefined. **Repair:** distinguish expected failures from ban events, using audit exposure and `1-(1-p)^a` for `a` audits; account for actual ban duration when checking lost capacity. Restore the F3 kill, restrict registered F4 gates to D2, and define paired seed differences and their standard errors before execution.

- **MATERIAL — Tasks 1 and 3, lines 24, 95, 149–151: misleading description.** “Newest identities first” hides the uniform component and terminal reserve. “Lowest recent audit count first” additionally replaces cumulative audits-per-served-job with a recent raw count. Support: vocabulary lines 32–39; spec §5.4 explicitly prevents coarse descriptions from hiding features. `verify_describe_record` checks vocabulary membership and agreement with `describe()`, not behavioral truth. **Repair:** set `audit_selection: not expressible`; replace the test requiring its absence with a test for H1 INCONCLUSIVE.

- **MATERIAL — Task 2, lines 127–137: incomplete logging and contradictory smoke acceptance.** Existing `score_point` returns aggregate scores and discards search details (`sim/tuning.py:81–94`), so calling it does not meet “every evaluation” logging. The proposed quick-file acceptance test contradicts `scripts/sweep.py:57–58`, which rejects quick results. **Repair:** specify persistent evaluation/search/reference records for both families and all rechecks. Test that quick output is readable but rejected by the production loader. Resolve the two different `objective_proposed` signatures.

- **MINOR — Task 1, lines 68–84, and Task 6, line 177: fixture and closure errors.** The embedded test has a syntax error at line 74; `EpisodeResult` has neither `memory` nor `N0`; creation round need not equal first-offer round. Rounded B2 prices also differ from the locked values. **Repair:** provide runnable helpers, capture permitted rule memory through a test wrapper, derive first offers from history, and load exact locked prices. Add explicit terminal-settlement tests and restore the runbook’s post-tag verification.

**RULING**

Require **`audit_selection: not expressible`** for both targeting variants. Paper disclosure cannot correct the information supplied to H1. Under spec §5.4 and `sim/claimcheck.py:94–97`, H1 against this rule must be **INCONCLUSIVE**. Keep the vocabulary frozen.

Review was read-only; the sealed bundle remained unread. Checks covered source, test syntax, arithmetic, and isolated manifest enumeration. No full simulation or paid call ran.

**VERDICT: reject**  
**CONFIDENCE: 0.97**
