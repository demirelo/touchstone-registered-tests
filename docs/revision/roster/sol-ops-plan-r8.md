VERDICT: reject

FINDINGS:

1. **Important — Tasks 7–8, `docs/superpowers/plans/2026-10-25-revision-operations.md:107,118`.** The H4 decision tests lack a successful loaded-bundle case. `test_h4_decision_records_exclusion` uses a wrong hash. The runner test checks exclusion and rejection of a loaded decision with a different hash. An implementation that always excludes H4 can pass these assertions and leave the independent part of Q3 unanswered even when the bundle is valid. Existing successful loader tests exercise `load`, not the new decision function (`tests/test_h4_loader.py:35–39`; `sim/h4_loader.py:53–71`). **Repair:** pass a valid toy bundle through `h4_decision`; require `loaded=True`, `h4_excluded=False`, and the registered hash. Feed that unchanged decision into the runner and require an H4 record. Retain the exclusion and mismatch cases.

The two rulings remain satisfied. Task 9 reports doubling labels without changing decisions, and its paired-record test checks both outcomes (plan:128–130). Task 8 retains the complete freeze and completion barriers between priority tiers; the timing test detects sorted submission without a barrier (plan:116–118; spec:249–253).

The version-8 coverage and verification changes address their stated faults. The coverage mutation test rejects A-pools/B-inputs combinations while retaining an unchanged passing case (plan:65,85–86). Verification now prohibits every child process, including Git, and takes an explicit commit input (plan:118,187). Task 10 also adds successful reproduction before the changed-record refusal case (plan:139). I found no additional version-8 interface or money-control defect.

Sol round-7 finding 1: **closed** — the permitted subprocess exception is removed; the fault test includes `git rev-parse HEAD` (plan:118).

Sol round-7 finding 2: **closed** — pool construction records the tuning manifest; promotion compares its file hashes with the promoted tuning entries, without including coverage’s own additions (plan:65,85–86).

Previously partial round-1 findings: **S1, S2, S4, S6, S7, S11, S12 closed** at the plan-contract level (plan:19,56–57,65–66,74–76,85–86,104–107,116–130,168). **S14 partly closed** — finding 1 leaves a specified test path that can pass with incorrect behaviour.

DECLINED TO JUDGE: Live prices, paid performance, launcher internals, external publication, and execution of future tests. This review used source inspection. No paid APIs were called; `sealed/` was not read.

CONFIDENCE: 0.89.