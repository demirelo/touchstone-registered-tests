VERDICT: request-changes

FINDINGS:

1. **Important — `scripts/lock_v2.py:111`: Git failures can still pass.** `status --porcelain` and both `rev-parse` calls ignore exit codes. A corrupt index can make status fail while commit-to-commit comparison succeeds. An in-memory probe returned status 128 with empty stdout; `check_commit` accepted it. **Repair:** require success from every Git command. Test failed status, failed resolution, and failed diff separately. K3’s missing-object case closes the original example; its ancestor case already failed on the baseline and does not establish this protection.

2. **Important — `scripts/budget_v2.py:45`: a stored approval needs no written text.** `_valid` checks its limit but accepts an empty approval. An in-memory ledger with USD 12 spent and `{limit: 100, text: ""}` granted another USD 40, reaching USD 52 without written approval. **Repair:** validate nonempty string approval text on ledger load and creation. `tests/test_budget_v2.py:117` checks creation only; a partial fix that ignores stored approvals passes.

3. **Important — `scripts/revision_v2.py:893`: incomplete schemas still pass.** Coalition records without `total` or `min` pass because comparisons with the default NaN are false. Profit arrays containing only `null` also pass both schema and numeric checks. Both cases were reproduced in memory. They can reach reporting as missing or invalid numeric data. **Repair:** require every summary field and finite numeric array element; reject strings, nulls, and booleans. Add these mutations through the real verifier and report. `tests/test_revision_v2.py:703` truncates an array already checked before K8, so that integration test cannot distinguish the baseline or these partial fixes.

4. **Important — `scripts/revision_v2.py:1062`: verification is not unconditionally read-only.** The recorded-input requirement applies only without `--dev`; configuration completeness checks only names starting with `fresh`. A guarded `verify --dev --markets dev0` probe reached calibration. **Repair:** require recorded configurations and salt for every supported verification context, or refuse unsupported modes before job construction. Extend `tests/test_revision_v2.py:654` beyond fresh-market omissions. Also update Operation 7’s commands to supply the newly required inputs.

5. **Minor — `scripts/report_v2.py:280`: Markdown still omits required uncertainty.** Welfare output prints efficiency bounds and mean attacker gain, but omits `attacker_gain_interval` and W1’s `constraint_interval`, which are computed at `scripts/report_v2.py:184`. Thus the claimed complete Markdown still hides the constraint uncertainty. **Repair:** render these intervals and their labels. Assert their actual bounds in the Markdown test; section names and selected numbers do not detect this omission.

6. **Important — `scripts/artifact_v2.py:79`, `scripts/reproduce.py:64`: reproduction does not validate the draw.** Tag comparison covers `experiments/`; the report invocation never consumes `draw/draw.json`. Changed draw headers with a recomputed manifest can therefore pass without affecting report comparison. An in-memory artifact-check probe accepted malformed draw headers. The new reproduction fixture itself uses `b"proof"` and an empty draw (`tests/test_artifact.py:137`). **Repair:** verify the packed proof and draw, then check the instances’ root, seeds, salt, and publication classification against them. Use a valid synthetic release and mutate the draw while recomputing the manifest.

7. **Minor — `scripts/reproduce.py:40`: environment validation skips missing dependencies.** Returning “not installed” for every package produced no problems. Python compatibility is also unchecked. This does not establish a locked environment; later imports may merely fail. **Repair:** resolve applicable lock entries, require their presence and versions, and check Python compatibility. Test missing required packages and platform exclusions. The current test only changes NumPy’s version.

By inspection, K3–K7 and K9–K11 contain targeted cases that distinguish their intended fixes from the baseline, but the partial fixes above survive relevant tests. I directly ran K10’s component-wave test against the baseline implementation and HEAD: it failed then passed. K1–K2’s interface changed, so unchanged tests cannot provide a meaningful baseline comparison; their new proof-binding and wrong-height rejection checks passed. K8’s report integration case already passed before the fix. K12’s changed-Markdown test leaves the manifest stale (`tests/test_artifact.py:165`), so artifact hashing alone can reject it without testing real report comparison.

For the final-review rulings at `docs/revision/operations-build-ledger-2026-10-26.md:64`: accept replacement of saved listings and folded timing, and accept the calibration-test correction. At line 71, accept the real-verifier test as integration evidence only, not proof of complete schemas. At lines 74–75, accept the proof-parser and continuous-chain approach; absence of a red-first run is not itself a defect. Reject the broad K12 completion claim at line 76. At line 77, accept offline environment checking in principle, but reject the claim that this implementation verifies the locked environment.

Sol final finding 1 — closed.  
Sol final finding 2 — partly closed.  
Sol final finding 3 — closed (`scripts/coverage_v2.py:94`, `scripts/promote_v2.py:180`).  
Sol final finding 4 — closed (`scripts/promote_v2.py:227`, `scripts/lock_v2.py:84`).  
Sol final finding 5 — partly closed.  
Sol final finding 6 — closed (`scripts/draw_v2.py:138`, `scripts/revision_v2.py:1053`).  
Sol final finding 7 — partly closed.  
Sol final finding 8 — partly closed.  
Sol final finding 9 — closed (`scripts/benchmark_v2.py:99`).  
Sol final finding 10 — partly closed.  
Astra final finding 1 — closed (`scripts/draw_v2.py:58`).  
Astra final finding 2 — closed.  
Astra final finding 3 — closed.  
Astra final finding 4 — partly closed.  
Astra final finding 5 — partly closed.  
Astra final finding 6 — closed.  
Astra final finding 7 — partly closed.  
Astra final finding 8 — partly closed.  
Astra final finding 9 — partly closed.  
Astra final finding 10 — partly closed.

DECLINED TO JUDGE: Live publication, paid execution, actual billing, and H4 contents. `sealed/` was not read; no paid APIs were called. **81 tests passed**: 35 normally and 46 with optional Matplotlib import disabled. All twelve frozen files are byte-identical to `2a288f5`. The combined run failed collection because no writable Matplotlib cache existed. **168 temporary-file-dependent tests were deselected**, including signed-repository and reproduction integration tests. The full suite and complete baseline test matrix were not run. The working tree remains clean.

CONFIDENCE: 0.92.