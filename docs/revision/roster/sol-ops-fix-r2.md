VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/revision_v2.py:906`, `scripts/revision_v2.py:986`: cross records still accept invalid numeric types.** In-memory probes passed both `_cross_problems` and `_numbers_ok` with boolean per-seed rows and with `"nan"` matrix entries. The report’s contrast calculation accepted the boolean rows and returned P = 1 (`scripts/report_v2.py:143`). L3 protects evaluation records, but the complete numeric-schema requirement remains partly open. **Repair:** apply `_num` to every cross-row and matrix element. Test these mutations through verification and reporting.

2. **Important — `scripts/artifact_v2.py:72`: the calibration exception removes the whole configuration from comparison.** Changing `fresh0.calibrated_cfg.v_max` to 123 passed `_draw_problems`. Calibration changes only `alpha` and `budget`; it preserves the other market fields (`sim/calibrate.py:58`). Reporting then uses the packed configuration (`scripts/report_v2.py:337`). Agreement between records and that configuration does not prove that it follows from the draw. **Repair:** compare all fields that calibration preserves. Validate the derived fields, with full recomputation available during reproduction. **Reject** the ruling at `docs/revision/operations-build-ledger-2026-10-26.md:84` as written: requiring presence alone is too weak.

**Accept** the publication-height ruling at `docs/revision/operations-build-ledger-2026-10-26.md:85` as an operator-recorded external fact. The offline check can verify classification from that height; it cannot establish historical publication. Actual publication timing remains outside this review.

Fix-test assessment below combines source inspection and in-memory probes. Temporary-file tests were not executed.

| Fix | Against `34d9016` | Protection against partial fixes |
|---|---|---|
| L1 | Stored blank approvals pass before; HEAD refuses them. | Tests catch creation-only and whitespace-only repairs (`tests/test_budget_v2.py:124`). |
| L2 | The old unbound decision reaches job construction; HEAD refuses it. | Checks refusal before execution (`tests/test_revision_v2.py:716`). |
| L3 | The new helper test fails before and passes now. | Profit-null integration adds useful coverage. Cross types remain uncovered; see finding 1 (`tests/test_revision_v2.py:727`, `:738`). |
| L4 | Development verification reaches job construction before; HEAD refuses missing inputs. | The new test omits both arguments together. A development check requiring only one could pass (`tests/test_revision_v2.py:748`). |
| L5 | Failed status and two failed resolutions pass before; HEAD refuses them. | The resolution test fails both calls together. Separate failures would strengthen it (`tests/test_lock_v2.py:204`). |
| L6 | Exact baseline fails on the new interface; its old check lacks draw validation. | Mutations isolate headers, seeds, and root after rebuilding the manifest. They do not detect finding 2 (`tests/test_artifact.py:203`). |
| L7 | Missing packages and incompatible Python pass before; HEAD reports them. | A NumPy-only dependency check could pass the new test. My extra probe confirmed rejection of missing transitive `opentelemetry-api` and exclusion of inapplicable `tzdata` (`tests/test_artifact.py:221`). |
| L8 | All three new interval assertions fail on baseline output and pass now. | **Minor:** removing W1 constraint text still passes. Its bounds equal the attacker-gain bounds. Assert the label within the relevant row (`tests/test_report_v2.py:253`). |
| L9 | Previous command templates omit required arguments. | Current templates contain the required arguments; no command-completeness test was added (plan:188–189). |
| L10 | The corrected test should also pass the baseline’s working report comparison. | Rebuilding the manifest removes the earlier false assurance from hash rejection (`tests/test_artifact.py:181`). |

Sol round-1 finding 1: closed — `scripts/budget_v2.py:47`.  
Sol round-1 finding 2: closed — `scripts/revision_v2.py:1060`.  
Sol round-1 finding 3: partly closed — evaluation cases fixed; cross gap remains, finding 1.  
Sol round-1 finding 4: closed — `scripts/revision_v2.py:1069`.  
Sol round-1 finding 5: partly closed — finding 2.  
Sol round-1 finding 6: closed — `scripts/reproduce.py:43`, `scripts/reproduce.py:64`.  
Sol round-1 finding 7: closed — `scripts/report_v2.py:282`.  
Sol round-1 finding 8: closed — operations plan:188–189.

Astra round-1 finding 1: closed — `scripts/lock_v2.py:112`, `scripts/lock_v2.py:117`.  
Astra round-1 finding 2: closed — `scripts/budget_v2.py:47`.  
Astra round-1 finding 3: partly closed — finding 1.  
Astra round-1 finding 4: closed — `scripts/revision_v2.py:1069`, `scripts/revision_v2.py:1080`.  
Astra round-1 finding 5: closed — `scripts/report_v2.py:282`.  
Astra round-1 finding 6: partly closed — finding 2.  
Astra round-1 finding 7: closed — `scripts/reproduce.py:43`, `scripts/reproduce.py:64`.

DECLINED TO JUDGE: Paid execution, billing, actual publication, and sealed contents. Neither sealed directory was read. No paid APIs were used. With `-p no:cacheprovider`, **95 tests passed; 205 temporary-file-dependent tests were deselected**. All twelve frozen-file comparisons against `2a288f5` passed. No writable temporary directory was available; optional Matplotlib imports were disabled. Signed-repository, artifact, reproduction, spawned-verifier integration, and full baseline test runs were not completed. No other regression was found within this coverage. No files were changed.

CONFIDENCE: 0.92.