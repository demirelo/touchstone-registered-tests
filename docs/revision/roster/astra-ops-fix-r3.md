VERDICT: request-changes

FINDINGS:

1. **Important — `tests/test_artifact.py:74`, `:239`: the artifact fixture is invalid under M1.** It copies the drawn configuration, including `budget=0.0` (`sim/instances.py:41`). In-memory execution confirms that HEAD rejects all six unchanged markets; `909c1d5` accepts them. Consequently, the positive artifact assertion at `:106` and unchanged-release reproduction assertion at `:172` cannot pass. The changed-report test at `:182` can now pass before report comparison. All five M1 mutation assertions also pass a partial fix that checks only positive budgets. **Repair:** give every fixture market an independent calibrated configuration with positive values. Assert clean acceptance before mutation, then require rejection of the specific changed market and field.

2. **Minor — `tests/test_revision_v2.py:753`, `:756`: L4 still permits a partial fix.** The test requests `dev0`, but its instances contain only `fresh0` (`:583`). A guard requiring only `--instances` passes every case: the instances-only case fails later because `dev0` is absent (`scripts/revision_v2.py:1084`). I reproduced this with an in-memory modification of the actual entry function. **Repair:** supply valid development instances and assert the specific missing-input error.

3. **Minor — `tests/test_revision_v2.py:767`: the boolean matrix test rejects the wrong mean without proving type rejection.** Its `True` entry differs from the expected `0.2`. An in-memory partial fix that permits finite boolean matrix entries passes the new helper test, while accepting `False` when the corresponding mean is zero. **Repair:** add boolean matrix entries whose numeric values match their row means. HEAD correctly rejects these cases; this is a test-coverage defect.

The M1 mutation assertions and M2 helper assertion fail against `909c1d5` in differential in-memory checks. The real-verifier probe also changes from acceptance on the baseline to stale-record rejection on HEAD. The full fixture-dependent tests were not executed.

L4/L5/L7/L8 should **pass** `909c1d5`: their production fixes already exist there. L5 now isolates each failed command with valid-looking output (`tests/test_lock_v2.py:204`). L7 detects missing transitive `six` and excludes inapplicable `tzdata` (`tests/test_artifact.py:226`); its exact test body passed against the current lock. L8 requires the constraint label and bounds (`tests/test_report_v2.py:255`). These address the specified partial fixes, except for L4 above.

All twelve frozen files listed at `tests/test_frozen_files.py:9` are byte-identical to `2a288f5`. No other production regression was found within the reviewed scope.

M1 — **closed** in production (`scripts/artifact_v2.py:78`): both round-2 `v_max` probes, 7 and 123, are rejected. All preserved fields and the key set are compared; both derived values must be finite positive numbers. **Accept** the replacement ruling at `docs/revision/operations-build-ledger-2026-10-26.md:91` for this stated boundary. Incorrect positive calibration values remain unchecked; reproduction does not independently recalibrate.

M2 — **closed** in production (`scripts/revision_v2.py:912`): boolean rows and `"nan"` matrix entries now fail. In-memory probes through the real verifier, with provenance and dependency checks held valid, marked them stale; report generation refused them (`scripts/report_v2.py:227`). Valid numeric records still passed.

DECLINED TO JUDGE: Paid execution, actual costs, publication timing, and sealed contents. No paid APIs or sealed directories were accessed. Pytest with `-p no:cacheprovider -s` passed **25 tests**, including the frozen-file checks; **108 temporary-file-dependent tests were deselected**. No writable temporary directory was available, so optional Matplotlib imports were disabled. M1 archive tests, M2 filesystem integration, L4 spawned verification, L5 signed-repository tests, and full reproduction/report tests were not run. No files changed.

CONFIDENCE: 0.95.