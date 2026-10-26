VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/artifact_v2.py:72`: the artifact check accepts changes to the actual market configuration.** It removes all of `calibrated_cfg` before comparison. An in-memory probe changed only `fresh0.calibrated_cfg.v_max` to `7.0`; `_draw_problems` returned no problems. Calibration changes only `alpha` and `budget` (`sim/calibrate.py:58`). Reporting builds expected jobs from the unchecked configuration (`scripts/report_v2.py:337`), so matching records establish consistency with the wrong market. **Repair:** compare every field that calibration preserves against the drawn configuration. Validate the remaining fields and provide calibration evidence or recomputation. Add a changed-configuration test with a rebuilt manifest.

2. **Important — `scripts/revision_v2.py:906`: cross-evaluation records still accept boolean observations.** `_cross_problems` checks lengths and means without applying `_num`; `_numbers_ok` accepts booleans. An in-memory probe through the real verifier returned `ok=True` for boolean cross rows, with provenance and dependency checks held valid. The Q2 calculation then treated those values as 0/1 and produced a fixed-attack P estimate of `1.0` (`scripts/report_v2.py:143`). **Repair:** require finite numeric values, excluding booleans, in every cross row and matrix entry. Test the mutation through verification and reporting. This is an additional Part A gap; the reported evaluate-record cases are fixed.

**L6 rulings:** Reject the `calibrated_cfg` ruling as written (`docs/revision/operations-build-ledger-2026-10-26.md:84`): slow calibration does not justify omitting inexpensive checks of unchanged fields. Accept the `published_height` ruling at line 85 as operator-supplied evidence. Publication height cannot be derived from the draw. Recalculating the classification checks consistency, but does not independently prove timely publication.

**Test sensitivity:** Differential in-memory probes confirmed baseline acceptance and HEAD refusal for L1, L2, L4, L5 and L7. The L3 helper test failed against the baseline and passed at HEAD. A synthetic L8 report omitted the required bounds before the fix and included them now. Inspection found these limits:

- **L1:** `tests/test_budget_v2.py:124` detects absent, blank and whitespace text; a partial string-coercion fix could still pass.
- **L2:** `tests/test_revision_v2.py:715` detects the missing identity field. It does not exercise the complete decision-generation path.
- **L3:** `tests/test_revision_v2.py:727` covers the reported evaluate-record mutations; line 742 connects null rejection to the real verifier and report. Cross records remain uncovered.
- **L4:** `tests/test_revision_v2.py:754` omits both inputs together. A partial guard that refuses only when both are absent could pass.
- **L5:** `tests/test_lock_v2.py`, `test_l5_every_git_command_must_succeed`, fails both `rev-parse` calls with empty output. An empty-head check alone could pass. Add separate failures with valid-looking output.
- **L6:** `tests/test_artifact.py:203` detects changed headers, seeds and root after adapting the baseline’s missing `offset` argument. It permits finding 1.
- **L7:** `tests/test_artifact.py:221` detects missing packages and incompatible Python, but a NumPy-only dependency check could pass. Add missing transitive-package and platform-marker cases.
- **L8:** `tests/test_report_v2.py:255` checks bounds, but shared gain/constraint bounds permit omission of the W1 constraint label.
- **L9:** Operation 7’s commands now contain the required arguments (`docs/superpowers/plans/2026-10-25-revision-operations.md:188`). No command-completeness test was added.
- **L10:** rebuilding the manifest at `tests/test_artifact.py:181` removes the former false reason for rejection. With interface adaptation, this test need not fail against old production code: report comparison already existed.

The partial-test limits above do not reopen correctly implemented fixes.

Sol round-1 finding 1 — closed.  
Sol round-1 finding 2 — closed.  
Sol round-1 finding 3 — closed for the stated evaluate-record failures.  
Sol round-1 finding 4 — closed.  
Sol round-1 finding 5 — partly closed; finding 1 remains.  
Sol round-1 finding 6 — closed for the current lock.  
Sol round-1 finding 7 — closed.  
Sol round-1 finding 8 — closed.  
Astra round-1 finding 1 — closed.  
Astra round-1 finding 2 — closed.  
Astra round-1 finding 3 — closed for the stated evaluate-record failures.  
Astra round-1 finding 4 — closed.  
Astra round-1 finding 5 — closed.  
Astra round-1 finding 6 — partly closed; finding 1 remains.  
Astra round-1 finding 7 — closed for the current lock.  
Round-1 changed-report test criticism — closed.

DECLINED TO JUDGE: Paid execution, actual costs, live publication timing and sealed contents. No paid APIs or sealed directories were accessed. **122 tests passed**, including all 12 frozen-file comparisons against `2a288f5`. **198 temporary-file-dependent tests were deselected**, including signed-repository, guarded-process and artifact reproduction integration tests. Pytest used `-p no:cacheprovider`; optional Matplotlib imports were disabled because no writable cache existed. The full suite was not reproduced. No files were changed.

CONFIDENCE: 0.92.