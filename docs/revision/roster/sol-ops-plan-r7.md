VERDICT: reject

FINDINGS:

References to “plan” mean `docs/superpowers/plans/2026-10-25-revision-operations.md`.

1. **Important — Task 8, plan:118; `scripts/revision_v2.py:58–60`.** The subprocess exception leaves the full write prohibition incomplete. The guard permits `git rev-parse HEAD` based on its arguments, but cannot observe writes inside that process or its descendants. For example, inherited `GIT_TRACE` settings can make Git write a trace file. On this host, the initial Git probe also attempted to create Xcode cache files. The faulty-child test rejects an unapproved command; it does not test writes from the permitted command.

   **Repair:** remove the subprocess from verification and obtain the checked commit identity through file reads or an explicit input. Alternatively, enforce write restrictions on the permitted process and its descendants. Add a test for a write attempt from the permitted subprocess. The present exception closes the unapproved-helper case, but gives the broader prohibition a narrower meaning.

2. **Important — Tasks 3 and 5, plan:65,84–86; `scripts/coverage_v2.py:24–45`.** Pool hashes now bind coverage to particular pool files. However, promotion does not require coverage’s `inputs_sha256` to match the tuning inputs being promoted. Those inputs determine the comparator, attacks, and references used to build the pools. Coverage from an earlier run at the same commit, branch, markets, and pool size can therefore accompany different promoted tuning outputs while satisfying the listed checks. Admission then concerns another empirical fixture.

   **Repair:** check the coverage input digest against an immutable manifest of its tuning dependencies. Exclude coverage’s own additions from that manifest to avoid a circular hash. Add a refusal case that combines valid coverage with different, individually valid tuning outputs; retain an unchanged passing case. This is a remaining registration gap, not a demonstrated version-7 regression.

The two rulings remain accepted. Task 9 reports doubling labels without changing decisions and specifies a paired-record test (plan:128–130). Task 8 retains the complete freeze before evaluation and requires completion barriers between priority tiers (plan:116–118; spec:249–253). The timing test targets execution order, beyond submission order.

The named producer, mutation, numerical-oracle, reservation, and timing tests target their stated faults. They do not detect findings 1–2 as currently specified.

Previously partial round-1 findings: **S1, S2, S4, S6, S7, S11, and S12 closed** at the plan-contract level (plan:19,56–57,65–66,74–76,85–86,104–107,116–130,168). **S14 partly closed:** the remaining test gaps are findings 1–2.

Sol round-6 finding 1: partly closed — hard-link creation and unapproved child processes are covered; the permitted subprocess remains outside the write guard (plan:118,275).

Sol round-6 finding 2: closed — exact branch size, pool hashes, derived seed lists, profile lengths, and reduced-pool refusal are required (plan:65,85–86,274). Finding 2 above concerns upstream fixture identity.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of tests not yet implemented. Review used source inspection. No paid APIs were called, no files were changed, and `sealed/` was not read.

CONFIDENCE: 0.89.