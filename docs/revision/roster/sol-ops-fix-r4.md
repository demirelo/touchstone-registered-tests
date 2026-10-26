VERDICT: approve-with-caveat

FINDINGS: None.

N1 — closed — `tests/test_artifact.py:74` supplies independent calibrated configurations with positive alpha and budget. The unchanged six-market fixture passes the in-memory artifact check. All five M1 test bodies pass HEAD; the budget-only partial fix fails four cases (`tests/test_artifact.py:237`, `:240`). Both original `v_max` probes, 7 and 123, are rejected by HEAD and accepted by `909c1d5`.

N2 — closed — `tests/test_revision_v2.py:756` requires the missing-input diagnostic. In-memory execution of the actual entry function confirms that HEAD produces it for all three omissions. The `--instances`-only partial guard fails the revised assertion when only instances are supplied: its later missing-`dev0` error cannot satisfy the assertion.

N3 — closed — `tests/test_revision_v2.py:768` pairs the boolean matrix entry with observations whose mean is 1.0. The revised test passes HEAD and fails the row-only partial fix. HEAD also rejects boolean rows and string `"nan"` matrix entries while accepting valid numeric records (`scripts/revision_v2.py:913`, `:916`).

The fixture change did not hide a further defect in the checks examined. All six configurations validate. With recorded inputs supplied through an in-memory filesystem, the real report CLI returns 0 for the unchanged report and 1 after the same Markdown mutation used at `tests/test_artifact.py:181`. The positive reproduction assertion remains intact at `:172`. The fixture still represents an evaluation without frozen results (`:139`); it does not establish calibration accuracy or successful evaluation.

No production regression was found in the changes since `909c1d5`. The production changes are confined to the M1 configuration checks (`scripts/artifact_v2.py:80`) and M2 numeric checks. Both remain closed under the accepted ruling at `docs/revision/operations-build-ledger-2026-10-26.md:91`.

Pytest passed **25 tests**, including all **12 byte comparisons against `2a288f5`** (`tests/test_frozen_files.py:9`, `:15`).

DECLINED TO JUDGE: Full filesystem integration. No writable temporary directory was available, so **108 temporary-file-dependent tests were deselected**, including archive/reproduction, signed-repository, spawned L4, and filesystem verifier/report cases. In-memory artifact probes mocked archive access and Git; they do not replace those integration tests. Pytest used `-p no:cacheprovider -s`; optional Matplotlib imports were disabled for collection. Paid execution, publication, and calibration accuracy were outside scope. Neither sealed directory was read. No paid APIs or repository writes were used.

CONFIDENCE: 0.95