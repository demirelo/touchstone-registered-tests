VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/budget_v2.py:45`: saved approval needs no written text.** An in-memory probe loaded `approval={"limit":45,"text":""}`. With USD 39 spent, `reserve` granted USD 4, reaching USD 43 without written approval. **Repair:** validate approval text when loading the ledger. Test missing and blank saved text; `tests/test_budget_v2.py:116` tests only the `approve()` input.

2. **Important — `scripts/revision_v2.py:1053`: an unbound H4 exclusion passes.** An old decision containing `loaded:false` and `bundle_sha256:null`, but no `registered_sha256`, passes against a protocol that registers H4. The default substitutes the expected identity instead of checking recorded identity. A guarded in-memory CLI probe passed this gate. **Repair:** require the identity field and validate both loaded and excluded decisions. Add an excluded-decision mismatch test.

3. **Important — `scripts/revision_v2.py:894`: coalition summaries remain optional and can be nonfinite strings.** The real `_check_evaluate` accepted valid member arrays with both summaries absent. It also accepted `total:"nan"`. Missing fields become NaN during comparison; `_numbers_ok` accepts strings at line 868. Reports can fail or contain unsupported values. **Repair:** require finite numeric scalars for both summaries and numeric array elements. Test these mutations through verification and reporting.

4. **Important — `scripts/revision_v2.py:1062`: development verification still runs calibration.** The new recorded-input requirement applies only without `--dev`. A probe of `--stage verify --dev --markets dev0` reached `INST.calibrated`. This violates the plan’s unconditional verification contract. **Repair:** require recorded configurations and salt for every verification mode, or refuse development verification before job construction. Extend the guarded omission tests.

5. **Important — `scripts/artifact_v2.py:79`, `scripts/reproduce.py:64`: reproduction does not validate the draw.** With signature verification and tagged registration bytes held valid, an in-memory artifact probe accepted changed draw headers and hash after the manifest was rebuilt. Reproduction passes `instances.json` to reporting but never checks `draw.json` against the tagged proof. **Repair:** validate the draw and bind the recorded instance root, streams, seeds, and salt to it before reporting. Add a changed-draw test that rebuilds the manifest.

6. **Important — `scripts/reproduce.py:40`: absent dependencies pass the environment check.** With every package lookup returning `None`, `environment_problems(uv.lock)` returned `[]`. The check therefore does not establish the locked environment. **Repair:** evaluate applicable dependency markers and require all applicable locked packages, plus the Python constraint. Test absent required packages.

7. **Minor — `scripts/report_v2.py:280`: Markdown still omits required intervals.** JSON contains `attacker_gain_interval` and W1’s `constraint_interval` at lines 184–185. Markdown prints only attacker gain’s estimate. **Repair:** render these intervals and assert their values. The substring test at `tests/test_report_v2.py:242` permits this partial result.

8. **Minor — `docs/superpowers/plans/2026-10-25-revision-operations.md:188`: the run-book command no longer works.** Evaluation now requires `--protocol`, which the command omits. Line 189 also lacks the recorded inputs required for verification. **Repair:** update both command templates and check their argument completeness.

Test sensitivity against `cd61014` and plausible partial fixes:

- **K1/K2:** the rewritten tests use a new interface, so unchanged baseline execution is not a meaningful comparison. The real-proof and substitution assertions cover the main faults.
- **K3:** the missing-object probe passed before and refuses now. The ancestry test already refused before; add an unrelated commit with the same tree to isolate ancestry.
- **K4/K5:** the new mutation cases distinguish the baseline failures. Finalisation, lock, and parameter derivation receive separate checks.
- **K6/K7:** the tests detect the reported input and reversal faults, but permit findings 1–2.
- **K8:** helper tests fail on the baseline’s absent helpers. A partial fix that adds the helpers without connecting them can pass those tests. The integration test’s truncated gain already failed before.
- **K9:** fresh-input tests detect the omission fault; development mode remains uncovered.
- **K10:** the differential probe priced the prerequisite wave at zero before and 100 seconds per task now. The component assertions detect the reported folding fault.
- **K11:** headline and Markdown-change tests detect baseline faults; completeness assertions remain too weak.
- **K12:** the rebuilt-manifest registration test detects missing tag binding. However, the changed-report test at `tests/test_artifact.py:159` fails at manifest checking, so it does not isolate the real report check. Missing dependencies and changed draw data remain uncovered.

Rulings: accept the K1/K2 test-method explanations at ledger lines 74–75 and the K3 qualification at line 66. Accept keeping K8’s integration test as limited coverage, but reject it as sufficient schema evidence. Reject the environment ruling at line 77 as implemented. The blanket claim at line 64 that all rejected rulings are superseded is only partly supported.

Sol 1: closed — `scripts/draw_v2.py:42`.
Sol 2: closed — `scripts/lock_v2.py:119`.
Sol 3: closed — `scripts/coverage_v2.py:95`, `scripts/promote_v2.py:180`.
Sol 4: closed — `scripts/promote_v2.py:248`, `scripts/lock_v2.py:84`.
Sol 5: closed for invalid monetary values — `scripts/budget_v2.py:27`; finding 1 is an additional approval gap.
Sol 6: partly closed — finding 2.
Sol 7: partly closed — finding 3.
Sol 8: partly closed — finding 4.
Sol 9: closed — `scripts/benchmark_v2.py:102`.
Sol 10: partly closed — findings 5–6.

Astra 1: closed — `scripts/draw_v2.py:58`.
Astra 2: closed — `scripts/promote_v2.py:180`.
Astra 3: closed — `scripts/lock_v2.py:84`.
Astra 4: closed — `scripts/lock_v2.py:119`.
Astra 5: partly closed — finding 1.
Astra 6: closed — `scripts/benchmark_v2.py:102`.
Astra 7: partly closed — finding 4.
Astra 8: partly closed — finding 3.
Astra 9: partly closed — finding 7.
Astra 10: partly closed — finding 6.

DECLINED TO JUDGE: Paid execution, publication timing, actual costs, outcomes, and sealed contents. No paid APIs were called; `sealed/` was not read. With `-p no:cacheprovider`, 96 tests passed, including all twelve frozen-file checks against `2a288f5`. Another 193 tests required temporary files and could not run across the Part A suites. The combined run initially failed Matplotlib collection; subsequent runs disabled optional plotting. No writable cache path was available. The full suite and ledger’s 1,173-pass claim were not independently reproduced. The working tree remains clean.

CONFIDENCE: 0.91.