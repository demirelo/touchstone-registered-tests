VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/benchmark_v2.py:95`, `:110`; `scripts/revision_v2.py:334`; `sim/manifest_v2.py:93`.** The benchmark supplies seven bank candidates per family. The headline runner uses the other eleven matched rules. The in-memory smoke probe confirmed seven versus eleven. Reference selection and doubling reselection therefore measure a smaller menu, which can understate costs and change cap decisions. **Repair:** derive the bank size from `bank_rules()` and test the candidate count after projection and deduplication.

2. **Important — `scripts/benchmark_v2.py:178`, `:46`.** The additional 160 evaluation seeds are priced by applying the D2+H3 evaluation fraction to every cell’s total cost. This incorrectly scales welfare and coalition search costs. In a component probe, increasing only coalition search time by ten seconds added **731.43 seconds of forecast evaluation work**, although evaluation time did not change. **Repair:** calculate additional evaluation costs from each kind’s measured evaluation component. Add a test that changes search time while holding evaluation time fixed.

3. **Minor — `scripts/revision_v2.py:517`, `:526`.** G3 does not implement one resume rule for every auxiliary record. Both calls use `check=lambda: None`, discard `reusable()`’s result, and always rewrite the envelope or bank. Two unchanged banks that passed `check_record()` were both rewritten in the probe. This violates Review Focus 5’s valid-record skip requirement. **Repair:** run the complete record check and skip valid records; retain foreign-provenance refusal.

G-test assessment against `109e597` and plausible partial fixes:

- **G1**, `tests/test_revision_v2.py:388`: rejects baseline by source comparison. It checks stage, dependency set, hashes, missing provenance, and foreign provenance. Its one-rule fixture can miss incomplete multi-rule dependency handling; my 146-record probe passed at HEAD.
- **G2**, `tests/test_revision_v2.py:406`: rejects baseline by source comparison. It checks missing/replaced freezes and both menu searches. With bank rules mocked empty, omission of other rules’ menu inputs could pass. HEAD’s full-context diagnostic recorded all 26 dependencies.
- **G3**, `tests/test_revision_v2.py:419`, `:430`: both reject baseline by source comparison. A partial fix limited to references and coalition prerequisites passes while finding 3 remains.
- **G4**, `tests/test_intervals_v2.py:101`, `tests/test_calibration_v2.py:182`: both failed against baseline and passed at HEAD in direct execution. They exercise invalid samples, decisions, p-values, and pools. The pool test covers NaN, but could admit an incomplete fix that omits short-pool checks.
- **G5**, `tests/test_intervals_v2.py:123`, `tests/test_calibration_v2.py:162`: both failed against baseline and passed at HEAD. The calibration test now calls `miss_counts()`. It compares aggregate misses, so compensating replication errors could pass; it does not compare every replication’s bounds.
- **G6**, `tests/test_benchmark_v2.py:65`, `:98`: rejects baseline. The order test alone permits faulty closures; the default smoke test adds useful wiring coverage. All 18 HEAD components completed with in-memory storage and reserved-seed generation disabled.
- **G7**, `tests/test_benchmark_v2.py:75`, `:89`: both failed against baseline and passed at HEAD in direct execution. Partial fixes still pass with the undersized bank and incorrect scaling above; line 85 explicitly asserts the latter formula.
- **G8**, `tests/test_credibility.py:66`: passes against baseline because the implementation was already correct. The added equal-count case rejects static residual ordering.

The three ledger rulings:

- **Line 73: accept.** Final-freeze acceptance before doubling follows design 6.4. The CLI preserves the full catalog.
- **Line 74: accept.** Pricing the runner’s repeated cross episodes is appropriate.
- **Line 75: accept the shared-cost allocation.** One reference per menu pair and one joint prerequisite pair per coalition group justify those shares. Findings 1–2 still prevent approval of the resulting cost table.

No required path was found blocked by stricter provenance refusal. In particular, `total` and `min` have identical group provenance; a selected `min` job reused valid shared prerequisites. Exit-round, empty-budget, seed-separation, and freeze checks showed no new regression. F1–F3, F5–F10, and F12 remain closed; F4 and F11 remain partly closed.

All twelve frozen files passed byte comparisons against `2a288f5` (`tests/test_frozen_files.py:15`).

Sol R1 #1 / Astra #5: closed.  
Sol R1 #2 / Astra #6: partly closed.  
Sol R1 #3 / Astra #1, cross: closed.  
Sol R1 #4 / Astra #1, doubling: closed.  
Sol R1 #5 / Astra #2: partly closed.  
Sol R1 #6 / Astra #3: closed.  
Sol R1 #7 / Astra #4: closed.  
Sol R1 #8 / Astra #7: closed.

DECLINED TO JUDGE: Paid performance, empirical coverage, live explorers, sealed contents, historical RED claims, and the full slow suite. Pytest used `-p no:cacheprovider`: **154 passed**. Temporary-file creation blocked **42 tests**: 28 runner, two calibration, six benchmark, and six tuning tests. In-memory probes supplement those blocked runs. No paid APIs were called, `sealed/` was not read, and no files changed.

CONFIDENCE: 0.94