Read-only source review complete. The sealed bundle remained unread. I did not run the test suite.

1. **Fidelity: 6/10** — The clause matches the consensus, but required design registration details are missing.
2. **Statistical correctness: 6/10** — The statistic and decision boundaries are correct; the seed layout cannot support the remedies.
3. **Executability: 4/10** — Several tests, interfaces, and commands require decisions or repairs.
4. **Registration integrity: 6/10** — Artifact preservation and disclosures are explicit; verification and provenance requirements have gaps.
5. **Feasibility and compute: 6/10** — Six pods are plausible; remedy costs and calendar estimates need explicit treatment.
6. **Completeness before tag: 4/10** — The plan permits registration before required design choices and validation paths are complete.

**OBJECTIONS**

Line references below concern the [implementation plan](/Users/oemer.demirel/Projects/touchstone/docs/superpowers/plans/2026-10-17-amendment-1.md).

1. **MATERIAL — Task 7, lines 360–380: incomplete design registration.**  
   **Effect:** Required design choices remain open when the amendment is tagged.  
   **Support:** Consensus lines 17–21 require terminal reserves and cumulative integer quotas for each L, unused-reserve treatment, zero-history ratios, count update times, the tuning objective, rechecks, and the baseline-objective disclosure. The specified YAML has no design or tuning block. Copying the consensus preserves requirements but does not resolve its unspecified choices.  
   **Repair:** Add a binding design-and-tuning registration. Resolve every specified choice before tagging. Record the falsification sequence from consensus section 5 and identify its later execution gate.

2. **MATERIAL — Tasks 1–2 and 7, lines 44–61, 100, 150, 360: seed layout cannot support remedies.**  
   **Effect:** Doubling must either exceed the block, reuse pool seeds in replications, or change replication seeds between attempts.  
   **Support:** The three attempts require 195,000, 230,000, and 390,000 seeds per cell. The block holds 200,000. The test requires replications immediately after the initial pool. Existing `sim/coverage.py:79–95` reserves the doubled pool before replication ranges.  
   **Repair:** Reserve at least 390,000 seeds per cell, preferably 400,000. Reserve 70,000 pool positions, then 320,000 replication positions. Add pool/replication factors to `seed_blocks_ext`; pass the selected factors through execution and merge. Test disjointness and prefix preservation for all attempts. Six 400,000 blocks from 6,600,000 end at 9,000,000.

3. **MATERIAL — Task 1, lines 51, 79–84: admission can represent fewer than 12 endpoints.**  
   **Effect:** The proposed test approves a two-cell study as confirmatory.  
   **Support:** `good` contains only `"a"` and `"b"`, yet admission must return confirmatory. Existing `admission` accepts any nonempty cell set (`sim/coverage.py:344–356`).  
   **Repair:** Require the exact six registered names before admission. Require both finite endpoint measurements for every cell. Replace the two-cell positive test and add missing-cell, extra-cell, missing-side, and nonfinite-value rejection tests.

4. **MATERIAL — Tasks 3–4, lines 173–217 and 239–259: H3 verification is not specified end to end.**  
   **Effect:** An implementation can calculate a verdict from H3 rows without checking their registered provenance and exact seed sequence. Duplicate seeds can also produce a misleading merge.  
   **Support:** The current CLI explicitly calls `verify_records` for the records returned by `h2_from_sweep` (`scripts/check_claim.py:127–130`). The new task defines an H3 loader but does not explicitly connect its records to that check.  
   **Repair:** Require H3 record verification before evaluation. Require 40 unique, matching final-evaluation seeds for each rule and a one-to-one merge. Specify demotion handling. Add production-path tests for wrong seeds, duplicate seeds, stale records, missing rules, and demotions.

5. **MATERIAL — Tasks 2 and 5, lines 129–140 and 280–290: tests and manifest behavior conflict.**  
   **Effect:** The promised test commands cannot pass as written.  
   **Support:** `smoke_sweep` does not exist in `tests/test_coverage.py` or `tests/conftest.py`. A newly generated smoke base report cannot satisfy line 124’s hash comparison with the registered lock. Task 5 uses undefined `b`. Adding only `positions` leaves `_full_cells` iterating all six beta values (`sim/manifest.py:30–35`), contrary to its beta-0.05 assertion.  
   **Repair:** Define shared fixtures and a temporary synthetic lock with matching hashes. Separate smoke selection from registered selection. Define `b`; add explicit beta selection or construct the headline H3 cells directly. Supply complete subprocess commands.

6. **MATERIAL — Tasks 1–2 and 6, lines 41–48, 150, 320: incompatible interfaces and hash definitions.**  
   **Effect:** Reference execution can fail, and report validation can reject correctly generated output.  
   **Support:** Imported `_factory` reads `spec.ref_candidate` (`sim/coverage.py:131`), but `CoverageExtSpec` provides `ref_candidate_by_rule`. Task 2 names an amendment-file hash; Task 6 requires a hash with lock-time fields null.  
   **Repair:** Define an extension factory that selects the reference by rule. Define one canonical amendment-hash function, including serialization and excluded fields, and use it everywhere. Test hashing before and after registration and cache reuse afterward.

7. **MATERIAL — Tasks 7–8, lines 380–396: incomplete verification procedure.**  
   **Effect:** The final command fails, and the original-lock audit is omitted.  
   **Support:** `scripts/check_claim.py:94` requires `--proposed`; line 396 omits it. Consensus line 10 requires the original tag’s verification to be reported again. The existing verifier will report amendment code changes outside the original allow-list.  
   **Repair:** Supply complete commands, including `--proposed none` before rule creation. Run `amend.py --check` before tagging. Record the original-tag differences explicitly and verify that registered artifacts are unchanged. Do not describe the expected original-tree differences as a clean verification.

8. **MINOR — Tasks 4–5 and 8, lines 239, 273–309, 396: reporting and compute details are incomplete.**  
   **Effect:** Console reports can omit the proxy limitation, call H3 held out, or imply an unsupported completion time.  
   **Support:** Consensus requires the limitation in every verdict report and says H3 is public. The base extension requires at most 4.68 million episodes; both remedies raise this to 9.36 million, excluding statistical computation.  
   **Repair:** Print the limitation with every amended verdict. Label H3 “public stress test on fresh final-evaluation seeds,” even if its internal section remains `heldout`. Record actual trajectory counts, measured throughput, remedy allowances, and a calendar estimate before launch.

**VERDICT: reject**

**CONFIDENCE: 0.94**
