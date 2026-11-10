# Run A, the runner-up comparator on the fresh markets: plan (draft 1, 2026-11-10; for internal review; no spend)

**Why.** The Fable 5.2 review (problem 5, `docs/paper/fable52-triage.md`): C* was selected in development on gross
efficiency in effect. The development log shows that in the two full-budget rechecks the runner-up C-thr(K = 12) left a
lower D2+H3 gain than C* (0.0761 against 0.0966 at the headline market, 0.0178 against 0.0381 at dev0;
`experiments/v2/log/Cstar__*thr*12*recheck.json` and the C* recheck, field `detail`). A comparator selected on attacker
gain could change the Q1 direction label. This run measures the runner-up on the six fresh markets.

**Status.** Exploratory, after the report. No registered estimate or decision changes; the registered Q1 result stays
primary. Nothing runs before internal consensus, the author's spend approval in the ledger, and a passing smoke run.

## 1. Estimand

For family f in {D2+H3, X7-SC}: d'(f) = pooled over the six fresh markets of the mean over the 200 evaluation seeds of
g(C-thr12) - g(R3), equal market weights, each rule against its own frozen truthful reference, paired by seed. Beside it:
g(C*) - g(C-thr12). Both are differences between prescribed finite searches, as the registered Q1 estimand is.

## 2. Cells and execution contract

- **Cells.** C-thr(K = 12) (tolerance 0.16, L = 10, R3's pacing, as in the development recheck) x fresh0..fresh5 at rho 0.2
  x {D2+H3, X7-SC}: 12 search cells, 6 references, 12 evaluations on the 200 evaluation seeds, 12 doubling checks with
  held-out evaluation. Registered settings (search budget, seeds, configurations).
- **Label.** The frozen code identifies a rule by its label and reads its credibility parameters from `params["cred"]`.
  The runner-up runs under the label `C*` with `cred = {variant: thr, K: 12, M: null}`, in its own output directory; its
  records differ from the registered C* records by `rule_params_sha256`, and `label.json` names the rule. The driver
  refuses an output that holds a byte copy of a registered C* record, and refuses a job whose rule parameters equal the
  registered C*'s.
- **Reference.** Built by the frozen reference stage from the registered C* menu construction: the runner-up's own D2+H3
  and X7-SC searches plus the cuts-3 bank of the other rules' registered winners (F000..F111, C*/S0), copied and checked
  against the original freeze hashes. The registered C* winner is not in the bank, as C* excluded itself; this keeps the
  construction identical to the registered one for a C*-labelled rule.
- **Driver.** `docs/revision/followup2/runnerup_v2.py` (code freeze: under `docs/`), frozen stages through
  `revision_v2._pool` and `_run_reference`. Preflight before any episode: salt, commit, runner and `sim/` equal to
  protocol-v2, configuration hashes equal to the recorded container hashes, and every pairing key except the rule
  parameters equal to the registered C* reference's. A follow-up freeze after the references; acceptance before
  evaluation and before doubling; inventory with the environment.
- **Validation before spend (free, on the Mac).** The smoke-size end-to-end test for fresh0 (both families, search to
  inventory) passes (`uv run pytest -q docs/revision/followup2`).

## 3. Analysis (fixed now)

Per family: d'(f) and g(C*) - g(C-thr12), per market and pooled; a nominal paired percentile bootstrap (9,999
resamples, seed 0, seeds resampled within each market, the same indices for both rules); the registered Q1 categories
applied to that nominal interval with the margin 0.05 (`common.q1_category`), labelled exploratory. Doubled-search
winners reported beside, as in the paper's doubled table. No calibration, no Holm, no change to any registered decision.

## 4. Expectations (written before any runner-up result)

From the development rechecks: d'(D2+H3) < d(D2+H3) = 0.0207 (report Q1), that is, the runner-up leaves a lower gain than
C*, pooled, under D2+H3. Scored met, failed, or not established (base and doubled disagree). No expectation on the
category.

## 5. Cost

`python3 docs/revision/followup2/cost_estimate.py`: 17.65 core-hours, 1.91 USD at the benchmark's 0.108 USD per
core-hour; on one 16-vCPU pod the critical path (D2+H3 search, X7-SC search, reference, X7-SC evaluation and doubling) is
2.63 hours, 1.47 USD at 0.56 USD per hour, 1.64 USD with 0.3 hours of preparation and tail. The plan uses 1.91 USD.

## 6. Steps

1. Internal review of this plan to consensus; freeze it.
2. The author records the spend approval (`docs/revision/followup/budget_followup.py` or a successor category).
3. One pod: `runnerup_v2.py --stage all --workers 12`; delete and verify the pod; record the spend.
4. Analysis on the Mac from the retrieved records; a paper paragraph and table labelled exploratory, after review.
