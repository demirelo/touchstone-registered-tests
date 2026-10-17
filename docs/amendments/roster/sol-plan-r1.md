Read-only review completed. No files changed; the sealed bundle stayed unread. I checked the source and schedule arithmetic. I did not run the test suite.

1. **Fidelity to consensus and spec: 5/10** — The H3 bounds match, but the amended verdict omits H2 and the registration omits required rule-design details.
2. **Statistical correctness: 6/10** — The paired statistic, two-sided admission, and decision boundary are sound; the seed layout cannot support the remedies.
3. **Executability: 4/10** — Several interfaces and tests conflict, including the smoke-report hash check and manifest budget selection.
4. **Registration integrity: 6/10** — Both verdicts and disclosures are retained, but provenance and final-record verification need explicit requirements.
5. **Feasibility and compute: 7/10** — The base estimate is credible; remedy capacity and the full calendar allowance are missing.
6. **Completeness before amendment tag: 4/10** — The design registration and final verification sequence are incomplete.

**OBJECTIONS**

All task and line references below concern [the implementation plan](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md).

1. **MATERIAL — Task 3, lines 173–175: amended PASS can bypass H2.**  
   **Effect:** H3 can produce an “amended claim: PASS” when the unchanged H2 absolute clause fails.  
   **Support:** `evaluate_amendment` receives no H2 result and combines only H3 absolute and comparative statuses. Consensus §2 retains the H2 absolute clause; spec §8 requires every applicable clause.  
   **Repair:** Pass the original H2 absolute status into the amended predicate and include it in the conjunction. Add a regression test with H2 FAIL and H3 PASS.

2. **MATERIAL — Task 7, line 360: required design registration is absent.**  
   **Effect:** Material choices remain open after the amendment tag, contrary to the consensus order.  
   **Support:** Consensus §4 requires terminal reserves and cumulative quotas for each L, unused-reserve treatment, T2 zero-history behavior and count-update times, the 36-configuration grid, tuning objective, rechecks, seed/tie logging, and the baseline-objective disclosure. The specified YAML contains none of these. Copying the consensus does not resolve details that it explicitly delegates to the amendment.  
   **Repair:** Add a normative design-and-tuning registration, with these choices fully specified, before tagging.

3. **MATERIAL — Tasks 1–2 and 7, lines 44–45, 58–61, 100, 150, 360: remedies exceed the seed block.**  
   **Effect:** Doubling either moves replication seeds, overlaps the pool, exceeds the cell block, or cannot run.  
   **Support:** Required unique seeds per cell are 195,000 initially, 230,000 after doubling M, and 390,000 after doubling R. The block is 200,000, and `seed_blocks_ext` has no remedy-factor parameters. Existing `sim.coverage.seed_blocks` reserves doubling space explicitly.  
   **Repair:** Reserve 400,000 seeds per cell, place replications after the reserved 70,000-seed pool, and add factor parameters with prefix/disjointness tests. Six blocks from 6,600,000 end below 10,000,000.

4. **MATERIAL — Task 5, lines 280–290: manifest scope contradicts its test.**  
   **Effect:** The implementation generates H3 searches at all six budgets; the test requires beta 0.05 only. This also adds avoidable compute.  
   **Support:** `_full_cells` iterates over `locked["beta_grid"]`; adding `positions` does not restrict budgets. Its current behavior was checked directly. Spec §6.2 also states that H3 is public, not held out.  
   **Repair:** Add an explicit budget selector and request only beta 0.05, median, n=40. Call these “final H3 stress-test cells” in documentation; explain any internal reuse of the `heldout` section.

5. **MATERIAL — Task 4, line 239: H3 record verification is unspecified.**  
   **Effect:** Forty development rows or stale records could reach the amended predicate unless the implementer supplies missing checks.  
   **Support:** The current CLI calls `verify_records` only on records returned by `h2_from_sweep` (`scripts/check_claim.py:127–129`). Merely adding `h3_from_sweep` does not extend that verification.  
   **Repair:** Explicitly verify every H3 record against rebuilt jobs and the exact final-eval seed sequence before evaluation. Test wrong namespace, stale parameters, duplicate seeds, and missing baseline rows; require one-to-one seed pairing.

6. **MATERIAL — Tasks 2 and 6, lines 124, 150, 320: extension provenance is insufficiently anchored.**  
   **Effect:** A report can match the current environment while using changed baseline inputs or attack/reference records.  
   **Support:** `validated_universe` checks records against current calibration and parameters. Task 6 checks the base report’s hash, but does not explicitly require the extension’s frozen-input hashes to equal the registered base provenance.  
   **Repair:** Require exact registered selection and matching calibration, tuned-file, salt, settings, and reference-record hashes against the base report and lock commitments. Add rejection tests for changed-but-self-consistent inputs.

7. **MATERIAL — Task 2, lines 124–140: the smoke integration test cannot satisfy the base-hash requirement.**  
   **Effect:** The main offline integration test refuses its own generated smoke base report.  
   **Support:** Line 124 requires its hash to equal the real locked report hash. The proposed `smoke_sweep` fixture and `run_coverage_study_smoke` helper also do not exist in `tests/test_coverage.py`.  
   **Repair:** Specify temporary-repository fixtures with a synthetic lock binding the generated base report. Define their ownership and CLI path support. Keep smoke reports ineligible for real admission.

8. **MINOR — Tasks 1–2 and 6, lines 41, 100, 150, 320: two interface gaps.**  
   **Effect:** Reference execution and amendment-hash reproduction depend on unstated choices.  
   **Support:** Existing `_factory` reads singular `spec.ref_candidate`; the new spec provides `ref_candidate_by_rule`. Task 2 leaves amendment hashing unspecified while Task 6 requires hashing with registration fields null.  
   **Repair:** Define `_factory_ext` and one canonical amendment-hash function shared by both scripts. Test unequal references, abstention, and hash stability after registration fields are filled.

9. **MATERIAL — Tasks 7–8, lines 380–396: registration closure is incomplete.**  
   **Effect:** The final command fails, and original-lock verification required by consensus §2 is absent.  
   **Support:** `check_claim.py` requires `--proposed`; Task 8 omits it. Comparing against the original tag will also report intentional amendment code changes outside its allow-list.  
   **Repair:** Supply complete commands, run `amend.py --check` on the copied report, record original-tag results and expected amendment deltas, and verify unchanged registered artifact hashes. Budget for up to **9.36 million episodes** under both remedies, versus **4.68 million** initially, plus setup, transfer, merge, review, signing, and timestamping.

**VERDICT: reject**

**CONFIDENCE: 0.94**
