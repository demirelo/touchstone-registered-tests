VERDICT: reject

FINDINGS:

1. **Important — Tasks 3 and 5, `docs/superpowers/plans/2026-10-25-revision-operations.md:65,85–86`.** Coverage promotion does not check the registered pool size. The built CLI accepts `--pool-size` for pool creation, selection, and validation (`scripts/coverage_v2.py:68,75,82`). A run that retains `--pool-size 40` at all three stages, but uses 10,000 selection replications, 20,000 validation replications, and 9,999 resamples, receives `smoke=False` under Task 3’s definition. If its endpoints pass, it also satisfies Task 5’s listed checks. Its multiplier can then enter the protocol despite using 40 seeds per market instead of the registered 20,000 or 10,000 (`sim/calibration_v2.py:26`; spec:465–474).

   **Repair:** require `pool_size == BRANCHES[branch][1]`, and verify the actual pool seed counts and aligned profile lengths. Mark reduced test pools as smoke. Add a refusal test with full replication/resample counts and a 40-seed pool; retain an unchanged registered-size passing case. The current small-pool tests and promotion mutations do not require this rejection. This is an overlooked registration gap, not a demonstrated regression introduced by version 6.

Sol round-5 finding 1: **closed** — plan:118 adds an audit-hook guard and deliberate `Path.write_text` and directory-creation faults, including writes outside `--out`. A local probe confirmed interception of `Path.write_text`, `os.open`, and `os.mkdir` before mutation.

Sol round-5 finding 2: **closed** — plan:76 checks successful returned grants, the maximum success count, and every successful tag’s ledger entry. The added interleaving test targets lost updates. The earlier five-grants/four-records failure cannot satisfy these assertions.

Astra round-5 finding 1: **closed** — the same Task 8 correction covers its write-guard finding.

Astra round-5 finding 2: **closed** — plan:85–86 requires equality between selected, validated, and effective kappa, candidate-set membership, and the specific 0.25-to-1 mutation refusal.

Previously partial Sol round-1 findings: **S1 closed** for failed-admission handling and multiplier binding (plan:65,85–86,95); **S2 closed** (104–107); **S4 closed** (19,116–118); **S6 closed** (56–57,65–66,168); **S7 closed at the plan-contract level** (74–76); **S11 closed** (126–130); **S12 closed** (116–118); **S14 partly closed**, because finding 1 leaves a registration fault that the specified tests can miss.

Both rulings remain accepted. Task 9 explicitly reports search-incomplete doubling labels without changing decisions, and its paired-record test checks both unchanged decisions and changed labels (plan:128–130). Task 8 preserves the complete freeze before evaluation, while requiring completion barriers between priority tiers (plan:116–118; spec:249–253). The dispatch and timing tests address the earlier submission-order error.

The revised round-5 tests target their stated wrong implementations. I found no additional version-6 interface regression or money-control regression. This does not establish that every future test implementation will enforce its description.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of future tests. A coverage probe could not complete because importing its dependencies required a writable Matplotlib cache. The coverage finding therefore rests on source and contract inspection. No files were changed, no paid APIs were called, and `sealed/` was not read.

CONFIDENCE: 0.91.