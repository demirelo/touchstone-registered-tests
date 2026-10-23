VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/revision_v2.py:766`, `:675`.** F4 remains incomplete. Cross resume checks only dependencies already listed in the record. An old cross record without provenance or dependencies was **skipped**, even with a complete, accepted freeze. Doubling omits the freeze dependency and does not call `accept()`. **Repair:** validate cross stage, expected provenance, and the complete dependency set; bind doubling to an accepted freeze and all inputs used by its reference reconstruction.

2. **Important — `scripts/revision_v2.py:731`, `:734`.** Reference resume catches a provenance mismatch and overwrites the foreign record. An in-memory probe confirmed this. This violates the plan’s Review Focus requirement to refuse records with different provenance. **Repair:** distinguish foreign provenance from damaged or stale records. Refuse the former; recompute only records from the current provenance.

3. **Important — `sim/intervals.py:188`, `:152`; `sim/calibration_v2.py:98`, `:120`.** F8 handles the reported zero samples but does not reject all nonfinite inputs. Six all-NaN strata produced Q1 `p=0.0002`, rejection, and “C lower.” A pool containing one NaN reported zero misses when the sampled dataset omitted it, because the population mean remained NaN. **Repair:** validate every input pool, stratum, population mean, and computed statistic before inference or miss counting.

4. **Important — `sim/calibration_v2.py:110`; `sim/intervals.py:142`; `tests/test_calibration_v2.py:140`.** F9 fixes bootstrap streams but still differs from production for constant samples. For 200 copies of `0.3`, production returns exactly `0.3`; calibration returns `0.29999999999999993`. Against a constant 20,000-value pool, calibration counted an upper miss while production did not. The new test also **passed with pre-fix `miss_counts` substituted**, because it tests separate wrappers. **Repair:** share the exact constant-sample path and test actual calibration replications against production bounds.

5. **Important — `scripts/benchmark_v2.py:105`, `:140`.** `measure()` invokes W1 before `reference_eval`, although W1 requires `state["ref"]`. The actual W1 closure, with expensive workloads replaced by stubs, raised **`KeyError: 'ref'`** after the two search workloads. **Repair:** execute prerequisites in dependency order and test the default workload wiring with inexpensive substitutes. **Reject the new benchmark ruling:** this failure is detectable without a paid pod.

6. **Important — `scripts/benchmark_v2.py:95`, `:99`, `:118`, `:141`.** F11 still does not measure complete cell units. Reference construction receives an empty bank; both profit timings receive the same D2+H3 reference/evaluation measurement; scaling doubles reference selection as well as evaluation. W1 and coalition timings omit their included evaluation, and doubling measures only attack continuation. These omissions affect caps and cuts. **Repair:** measure separate search, bank, reference, evaluation, and continuation components, then price each workload from its required components.

7. **Minor — `tests/test_credibility.py:66`.** The deferred test still accepts an implementation that ignores current-round picks. **Accept deferral:** the implementation at `sim/mechanisms/credibility.py:51` is correct, and the equal-count probe returned `[0,3,1,2]`. **Repair later:** add that discriminating fixture.

Test assessment below compares source with `963e04c`. All added regression tests would reject that version, sometimes only because a new interface is absent. Partial-fix gaps remain:

F1: **closed** — `scripts/block_draw.py:135` binds the protocol before anchoring. `tests/test_block_draw.py:139` rejects changed bytes, but would pass if the CLI omitted the helper call.

F2: **closed** — `scripts/revision_v2.py:468` checks expected provenance and dependencies. Tests at `tests/test_revision_v2.py:280` cover references only; my probes also rejected foreign joint twins, joint references, envelopes, and banks.

F3: **closed** — `scripts/revision_v2.py:174` binds H4’s hash into job provenance. `tests/test_revision_v2.py:299` detects the missing field but does not exercise bundle-change resume.

F4: **partly closed** — findings 1–2. Tests at `tests/test_revision_v2.py:307` and `:316` catch wrong stages and changed evaluation freezes, but miss cross, doubling, and foreign-reference resume.

F5: **closed** — `scripts/revision_v2.py:819` retains the catalog. `tests/test_revision_v2.py:327` uses a narrowed manifest; my full 146-record headline probe accepted a selected evaluation.

F6: **closed** — `scripts/revision_v2.py:744` completes shared prerequisites before dispatch; `sim/records_v2.py:16` uses unique temporary names. The test at `tests/test_revision_v2.py:334` checks mocked ordering and source text, not concurrent writes.

F7: **closed** — `scripts/revision_v2.py:639` restores metadata. Before/after probes reproduced the old W1 `KeyError` and verified retained winners. `tests/test_revision_v2.py:348` does not assert exact W0 diagnostic values.

F8: **partly closed** — finding 3. Tests detect the original constant failures; rare-event misses changed from 0 to 97 in my probe. They omit nonfinite pools and strata.

F9: **partly closed** — finding 4. Fixed streams are implemented, but constant bounds differ and the new test misses a restored old calibration engine.

F10: **closed** — `scripts/tune_v2.py:112` preserves grid indices. The reversed-inner-ranking probe changed the tied winner from L=10 to L=3. `tests/test_tune_v2.py:88` catches this partial-fix scenario.

F11: **partly closed** — findings 5–6. `tests/test_benchmark_v2.py:44` replaces every workload, so it misses default wiring and scope failures; `:56` checks cost sensitivity only.

F12: **closed** — `scripts/revision_v2.py:272`, `:396` apply embedding and controls to W0/W1. `tests/test_revision_v2.py:359` covers only W0 and stubs controls; a W0-only partial fix would pass.

Verification: **159 tests passed**, including exit-round, empty/exhausted-budget, seed-range, and all twelve frozen-file checks. The twelve files are **byte-identical to `2a288f5`**. The full-catalog in-memory probe also refused evaluation before freeze.

DECLINED TO JUDGE: Paid performance, live explorer behaviour, sealed contents, historical RED claims, and the full slow suite. The sandbox blocked **35 temporary-file-dependent tests**: 24 runner tests, six tuning tests, three benchmark tests, and two calibration tests. These include runner integration/resume/doubling tests and CLI tests. Pytest used `-p no:cacheprovider`; plotting imports were disabled. No paid APIs were called, `sealed/` was not read, and no files were changed.

CONFIDENCE: 0.94