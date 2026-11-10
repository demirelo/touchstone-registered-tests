claude-fable-5-2

## 1. Recommendation

**→ Do not spend yet.** The rule fired. Follow it: stop, report, and amend the plan (draft 5, a recorded deviation, one review round). Do not loosen the rule silently.

**→ The rule was badly chosen.** Bit identity across arm64 and amd64 was never achievable. Three platforms give three results (`jq` on the three search records): the twin best value is bit-identical (0.05595120675524875), the archive sizes are equal (1485 and 1615), and the attack best value differs at 1.5e-14. The episode code therefore looks platform-stable, and the drift probably starts in the optimizer's linear algebra (unverified). The emulated x86 container is not the pod CPU, so that run could not pass either.

**→ Correct pass criterion, in three parts.**
- **Exact:** runner, config, salt and rule-parameter hashes, seeds, budget, episode count, archive sizes, `best_source`, discrete knobs, dependency sets, twin best value and corner-control values.
- **Tolerance:** continuous knobs relative 1e-9, per-seed gains absolute 1e-9. That is about 10^6 below the paired SE of 0.0009 and about 10^4 above the observed drift.
- **New, free:** evaluate the registered knobs through the driver on the Mac. Bit-identical gains prove the evaluation path and isolate the drift to the search.

**→ Add a pod gate.** Run the same reproduction first on the real pod (about 0.58 core-hours, about 0.3 USD of billed time). Only that test can meet the original rule. If it also drifts, apply the tolerance.

## 2. Findings, ranked

**1 → High: no cross-check of invariant provenance against the paired records.** `reset_followup_v2.py:61-67,151-170`. The driver checks only the config and salt hashes. `--params` comes from `experiments/v2/params.json`, which the freeze permits to change. A changed tuned C* or comparator gives D2 cells under other rule parameters than their D2+H3 pair and reference. Fix: each job's `rule_params_sha256`, `runner_sha256`, `root` and seeds must equal the reference record's provenance.

**2 → High: the code state is not pinned.** The Linux repro record has `git_commit: "unknown"` (Grep on the record). The driver accepts that at `revision_v2.py:60-64` and never compares `scripts/` and `sim/` with protocol-v2. No record holds the driver hash, Python, numpy, BLAS or CPU (`:177-184`). Python is `>=3.12`, unpinned. Refuse "unknown" and add an environment block to the inventory.

**3 → Medium: section 4 diagnostics do not exist.** There is no instrumented evaluation and no x=0 switch in the driver, but the cost in section 7 includes them on the same pod. They are evaluation only, so run them free on the Mac under the tolerance, or write them first.

**4 → Medium: the doubling path has no ground truth.** Validation (a) covers search and evaluation (`:190-214`). Doubling ran only at smoke size, but it feeds the met/failed scores. Reproduce one registered D2+H3 doubling record (18 exist for the fresh markets, Glob) with the same criterion.

**5 → Medium: `check_out` protects only the hard-coded path.** `:55-58`. On a pod, `--src` is another path. If `--out` equals it, the search writes D2 records into the registered copy before `prefreeze` refuses. Compare with `a.src` too.

**6 → Low-medium: the salt check comes after the search.** `:242-247`. A mismatch between `draw.json` and `instances.json` shows only after the search spend. Run it before the search.

**7 → Low: the conflict detection in `inputs()` has a gap.** `:94-99`. The `k not in need` filter drops a second, different hash for a known record, and `todo.update` overwrites pending entries. Search-copy hashes are also not compared with the original freeze, and `fr["cuts"]` and `fr["h4_excluded"]` are not asserted.

**8 → Low: `accept` trusts `inputs.json`.** `:130-131,164`. It does not recompute `inputs(src, jobs)`, so a freeze made without the inputs stage passes it. Evaluation then fails loudly, so this is not silent.

**9 → Low: the tests can be skipped.** `pyproject.toml` has `testpaths = ["tests"]`, so the follow-up tests do not run by default. `test_reset_followup.py:149-157` locks the exact compare that must now change. `:160` holds an absolute Mac path, so validation (b) skips silently elsewhere.

**10 → Low: budget wrapper.** `budget_followup.py:21-29` does not check `new_limit >= used + cap` and can lower the limit. It also replaces the earlier approval text. `:33` creates a default ledger if the path is absent.

**→ No misuse of the frozen stage functions found.** `_pool` with `catalog=jobs` gives the registered dependency sets.

## 3. Plan concerns

**→ The plan text is stale.** It names `scripts/reset_followup_v2.py` and a change to `budget_v2.py`. Both live under `docs/`. Correct this in draft 5.

**→ The scoring of the per-market expectations is ambiguous.** "On each fresh market" does not say whether it means all six or a count. Fix it now.

**→ S can be too high from weak search.** The B3 and R3 D2+H3 searches are flagged at the headline market. A weak D2 search on B3 lowers G(D2) and raises S. Add the reverse switch (the D2 winner with x=1, 18 cheap evaluations) and a nested best-of sensitivity.

**→ The intervals understate uncertainty.** Winners come from 5 training seeds, and the SEs are conditional on the winners and on six markets. Report the sign count and a leave-one-market-out S.

**→ The doubling flag for D2 has a second cause.** It mixes attack change and reference reselection with D2 candidates (`revision_v2.py:890-895`). Report the two separately.

**→ Cost is sound.** The pod gate adds about 0.3 USD, far below the cap.

## 4. Confidence

- Stop and amend, three-part criterion: **high**.
- Drift source is the optimizer: **medium** (inferred from the identical twin value, no archive diff run).
- Findings 1, 2, 3, 5: **high** (read in code). Finding 4: **high** on the gap, **medium** on its importance.
- Findings 6 to 10: **medium**.
- Plan concerns: **medium**. The S bias direction is an argument, not a measurement.

**Unsure:** I could not run Python here (approval denied), so I did not locate the first diverging archive entry. That check would settle the drift source.
