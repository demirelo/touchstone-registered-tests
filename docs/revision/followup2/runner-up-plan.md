# Run A, the runner-up comparator on the fresh markets: plan (draft 3, 2026-11-10; for internal review; no spend)

**Draft 3 changes** (internal review round 2, `docs/revision/roster/{sol,astra}-runner-up-plan-r2.md`, both reject): each
bank copy's actual SHA-256 must equal the original freeze hash before the reference is built and at acceptance (a
changed bank with a rebuilt reference is refused, test); the evidence is the named set, bound to the current reset driver
and environment, with the pod gate `--reproduce --require-identical` required bit-identical on this machine; the
reservation is the full 3.00 USD stop cap; a paid run requires the pod allocation time and carries earlier failed
attempts (`--prior-spend-usd`).

**Draft 2 changes** (internal review round 1, `docs/revision/roster/{sol,astra}-runner-up-plan-r1.md`, both reject):
complete freeze validation with refusal tests; pinned search settings, budgets checked against the registered records,
the exact runner-up specification enforced; reproduction evidence and the pod gate required before the cells; base and
doubled contrasts for three pairs, expectation scored on unrounded values, missing and nonfinite results separate from
failures, per-market intervals; a run-specific inventory; the claim bounded to one development-selected alternative;
a dollar cap, ledger reservation, and a stop between stages.

**Why.** The Fable 5.2 review (problem 5, `docs/paper/fable52-triage.md`): C* was selected in development on gross
efficiency in effect. In the two full-budget development rechecks the runner-up C-thr(K = 12) left a lower D2+H3 gain
than C* (0.0761 against 0.0966 at the headline market, 0.0178 against 0.0381 at dev0; `experiments/v2/log/`, the two
`Cstar__*__recheck.json` records, field `detail`). This run measures that one alternative on the six fresh markets.

**Scope.** Exploratory follow-up after the report, not an independent replication: the six markets, their seeds, and
every registered rule's outcomes were already observed; only the runner-up's outcomes are unseen. It tests one
development-selected alternative; it does not identify the best gain-selected comparator among the twelve
configurations. Deferred, not in this run: full-budget rechecks of the other ten configurations, gain-based selection
across all twelve, an honest-churn arm, and searches to convergence (Run B). No registered estimate or decision changes.

## 1. Estimand

For family f in {D2+H3, X7-SC}: d'(f) = pooled over the six fresh markets (equal weights) of the mean over the 200
evaluation seeds of g(C-thr12) - g(R3), each rule against its own unchanged frozen truthful reference, paired by seed.
Beside it: g(C*) - g(C-thr12) and g(C*) - g(R3) by the same method, so that a category difference cannot come from the
inference method. All are differences between prescribed finite searches.

## 2. Cells and execution contract

- **Cells.** C-thr(K = 12) at tolerance 0.16, L = 10, R3's pacing (the recheck specification; the driver refuses any
  other: `check_spec`) x fresh0..fresh5 at rho 0.2 x {D2+H3, X7-SC}: 12 searches, 6 references, 12 evaluations on the 200
  evaluation seeds, 12 doubling checks with held-out evaluation.
- **Settings pinned.** `TOUCHSTONE_LOCKED` refused; `experiments/locked.yaml` and the manifest equal protocol-v2; each
  job's search budget equals the registered C* record's for the same market and family (X7-SC doubled, as registered).
- **Label.** The frozen code identifies a rule by its label; the runner-up runs under `C*` with its own `cred`, in its own
  output directory. Its records differ from C*'s by `rule_params_sha256`; `label.json` names the rule; an output holding
  a byte copy of a registered C* record is refused, and so is a job with C*'s rule parameters.
- **Reference.** The frozen reference stage on the registered C* menu construction: the runner-up's own D2+H3 and X7-SC
  searches plus the cuts-3 bank of the other rules' registered winners (F000..F111, C*/S0), copied and checked against
  the original freeze hashes; the registered C* winner is not in the bank, as C* excluded itself.
- **Freeze.** After the references, each market's freeze holds exactly its bank inputs (each copy's actual hash equal to
  the original freeze's), both searches, and its reference. Each new record must carry the current job's provenance, the expected dependency set, and dependencies whose
  current hashes equal the recorded ones; the freeze states `followup`, cuts 3, and H4 loaded. Acceptance before
  evaluation and before doubling recomputes all of this and the bank inputs from the original freeze; an empty,
  incomplete, or stale freeze is refused (tests).
- **Saved results.** The frozen stages reuse a record only under its exact provenance (registered resume rule).
  `run.json` binds the output to the input hashes, the job provenance, the smoke flag, the settings, and the driver hash;
  a different binding is refused, never overwritten.
- **Reproduction gate.** Required before any search (`check_run_evidence`): `--reset-mac`, the reset driver's reproduction
  gate run on the Mac (its `gate.json` passes and its inventory names the current reset driver); `--reset-pod`, the same
  gate run first on this pod with `--reproduce --require-identical` (bit-identical, environment equal to this machine's,
  same driver); `--doubling-evidence`, the saved fresh0 F111 D2+H3 doubling reproduction (passes).
- **Inventory.** Every output with its hash; Run A's deviations; hashes of `runnerup_v2.py`, `common.py`, `guards.py`, the
  imported helpers, this plan, and the report; the run arguments; the environment (Python, numpy with BLAS and LAPACK,
  SciPy, CMA, CPU).
- **Validation before spend (free, on the Mac).** `uv run pytest -q docs/revision/followup2`, including the smoke-size
  end-to-end run for fresh0 (both families, inputs to inventory).

## 3. Analysis (fixed now)

Per family, base and doubled: runner-up minus R3, C* minus runner-up, and C* minus R3, each against the rule's unchanged
frozen reference (doubled: the runner-up's doubling records and the report's held-out records for R3 and C*), from
unrounded per-seed values. Per market and pooled estimates, each with a nominal paired percentile bootstrap interval
(9,999 resamples, seed 0, seeds resampled within each market, the same indices for both rules). The registered Q1
categories are applied to the nominal pooled interval with the margin 0.05, labelled exploratory. The intervals are
conditional on these six markets and the selected policies and references; they exclude search and market-sampling
uncertainty and carry no registered calibration or Holm guarantee. The doubling check's attack and reference changes
and its flag are reported per cell.

## 4. Expectation (written before any runner-up result)

E: pooled g(C*) - g(C-thr12) > 0 under D2+H3, computed exactly from the paired per-seed values (not against a rounded
threshold). Met if it holds under both base and doubled records; failed if it fails under both (a tie, exactly 0, is not
met); not established if they disagree; "not available" if a record is missing or a value is nonfinite (reported
separately, never a failure). No expectation on the category.

## 5. Cost and spending controls

`python3 docs/revision/followup2/cost_estimate.py`: 17.65 core-hours, 1.91 USD at the benchmark's 0.108 USD per
core-hour; billed path on one 16-vCPU pod 3.56 hours (reproduction gate 0.61 h, searches, six serial reference calls,
X7-SC evaluation and doubling, 0.3 h preparation and tail) = 1.99 USD at 0.56 USD per hour. Estimate 1.99 USD
(x 1.25 = 2.49); **stop cap and reservation 3.00 USD**, the full allowance, in the ledger category `followup` (cap 22 USD
shared by all follow-up runs: reset 5, churn 8, Run A 3, Run B 4.25, total 20.25; `budget_followup.py reserve`). A paid run
requires `--started-at <allocation time>` and counts earlier failed attempts (`--prior-spend-usd`). The driver checks
the cap between stages: a stage starts only if the billed time so far
plus its estimate stays within the cap; a running stage is never killed (author's instruction); the run stops, writes
`cost_stop.json` and an inventory, and reports. This is an admission limit, not a billing ceiling: a stage that starts
within the cap finishes, and the pod is deleted after it.

## 6. Steps

1. Internal review to consensus; freeze this plan.
2. Reserve 3.00 USD in the ledger; one pod: `reset_followup_v2.py --reproduce --require-identical`, then `runnerup_v2.py
   --stage all --workers 12 --reset-mac M --reset-pod P --doubling-evidence D --cap-usd 3.00 --started-at T`; delete and verify the pod; record the spend.
3. Analysis on the Mac from the retrieved records; a paper paragraph and table labelled exploratory, after review.
