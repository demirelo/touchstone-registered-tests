VERDICT: reject

FINDINGS:

References to “plan” mean `docs/superpowers/plans/2026-10-25-revision-operations.md`.

1. **Important — Task 8, plan:116–118,266.** The write guard closes the two stated bypasses, but does not enforce the full prohibition on filesystem changes. The audit hook applies to its Python process; a verifier can start a helper that writes a cache without triggering the parent’s write guard. The event list also omits `os.link`. An audit-event-only probe confirmed both gaps without changing files. The built runner already uses subprocesses for provenance (`scripts/revision_v2.py:58–60`), so subprocess handling needs an explicit boundary. **Repair:** prohibit unapproved child processes during verification, permit only specified read operations, and include the omitted mutation events. Add faulty-verifier cases for a child-process write and hard-link creation. The current two mutation cases can both pass while these faults remain.

2. **Important — Tasks 3 and 5, plan:65–66,85–86.** A remaining registration gap concerns coverage pool size. The built CLI permits `--pool-size` to override the branch size when building and consuming pools (`scripts/coverage_v2.py:68,75–79,82`; `sim/calibration_v2.py:26,62–64`). Task 3 determines `smoke` from replication and resample counts. Task 5 checks those counts and the branch, but does not require the pool size to match that branch. Thus, a 40-seed pool with production replication counts can produce passing endpoint rows and be promoted as `three20k`. Admission then concerns a different empirical fixture from the registered procedure. **Repair:** require the branch’s exact pool size, verify actual seed and profile-array lengths, and bind coverage to the pools used. Add a production-count fixture with only pool size changed; promotion must refuse it. This is an overlooked gap, not an established version-6 regression.

Sol round-5 finding 1: **partly closed** — `Path.write_text` and directory creation are covered; the broader write prohibition still has finding 1’s gaps.

Sol round-5 finding 2: **closed** — plan:76 checks successful grant totals, at most four grants, and every successful ledger entry; the forced competing-update test targets the lost-update failure.

Astra round-5 finding 1: **partly closed** — same remaining boundary as finding 1.

Astra round-5 finding 2: **closed** — plan:85–86 requires equality between selected `kappa`, `validation.kappa`, and `kappa_effective`, candidate-set membership, and unchanged-pass/changed-value-refusal cases.

Previously partial round-1 findings: **S1 closed for failed admission and multiplier identity** (plan:65,85–86,95); **S2 closed** (104–107); **S4 closed** (19,116–118); **S6 closed** (56–57,65–66,168); **S7 closed at the interface-contract level** (74–76); **S11 closed** (126–130); **S12 closed** (116–118); **S14 partly closed** because findings 1–2 identify remaining test gaps.

Both rulings remain accepted. Task 9 reports doubling labels without changing decisions and requires a paired-record test (plan:128–130). Task 8 preserves the complete freeze before evaluation, with completion barriers between priority tiers (116–118), consistent with spec:249–253. The slow-tier test checks execution timing; sorting alone cannot satisfy it.

The other strengthened tests specify useful failure cases: unchanged producer output, substituted draws, foreign records, incorrect interval tails, missing Holm slots, and aggregate approval crossings. Their stated assertions target those faults. Passing them would still leave findings 1–2 undetected.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of future tests. Review used source inspection and an audit-event-only probe. No paid APIs were called, no files were changed, and `sealed/` was not read.

CONFIDENCE: 0.91.