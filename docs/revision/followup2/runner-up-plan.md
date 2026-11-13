# Run A, the runner-up comparator on the fresh markets: plan (draft 7, 2026-11-11; for internal review; no spend)

**Amendment (2026-11-13, shared launcher review r1, `docs/revision/roster/{sol,astra}-f2-launcher-r1.md`):** reservation input 3.12 (grant 3.90 USD = 1.3 x the 3.00 USD stop cap, which is unchanged); the follow-up category cap is 72 USD (the author's approval of 2026-11-12); the reservation covers the watchdog bound, 1.3 x the stop cap, because a stage admitted within the cap finishes and only the watchdog at 1.3 x the cap stops a running stage (churn launcher review r1, Sol and Astra); `guards.check_grant` against the stop cap is replaced by the launcher's check that one `followup` reservation tagged with this launch covers 1.3 x the stop cap minus the run's recorded spend. The launcher is `docs/revision/followup2/followup2_pod.sh`.

**Draft 7 changes** (internal review round 6, `docs/revision/roster/{sol,astra}-runner-up-plan-r6.md`, both reject): paid accounting counts the current pod from its recorded open event, never from a later `--started-at`
(refusal test); the ledger must have a `spent` list of rows with a tag and a finite, nonnegative amount, and the cap,
rate, and step estimate must be finite and valid (refusal tests); the reservation command is `budget_followup.py
--reserve`, and its returned grant must equal the stop cap (`guards.check_grant`);
the evidence check also requires the search record's stage and identity (and the evaluation record's identity), with
refusal tests on copies of the real evidence.

**Draft 6 changes** (internal review round 5, `docs/revision/roster/{sol,astra}-runner-up-plan-r5.md`, both reject): attempt records are validated strictly (finite, ordered epochs; exactly one open attempt, the current pod; an
allocation time between that attempt's start and now; refusal tests); a launcher calls `guards.py admit` before every
paid step, including the reset reproduction gate, with the same cap, attempts, ledger, and run tag, so earlier spend
is counted before any paid work; the exact reservation is `budget_followup.py --reserve <tag> 2.40`, whose grant
(2.40 x 1.25) equals the 3.00 USD stop cap (`guards.reservation_input`); obsolete attempts references removed;
the evidence check also verifies every copied input with its hash, the freeze contents and metadata, and the stage,
provenance, dependency set and dependency hashes of the evaluation and doubling records (refusal tests on copies of the
real evidence, with the real comparison functions); the real Mac evidence passes.

**Draft 5 changes** (internal review round 4, `docs/revision/roster/{sol,astra}-runner-up-plan-r4.md`, both reject): the evidence check now requires every supporting record (search, evaluation, freeze for the reproduction; the doubling
record for the doubling gate) listed in the inventory with hashes equal to the files, and recomputes `compare()` and
`compare_doubling()` against the registered records (refusal tests for missing, unlisted, and changed records and for a
failing recomputation); the attempts handoff follows the launcher's real event format and the ledger carries earlier
launches; the STOP file and soft deadline are checked before each stage of `--stage all`. Mac evidence under the current
code: `results/v2/followup2-a-gate-repro` (pass; knobs 2.5e-13, gains 2.0e-14) and `results/v2/followup2-a-gate-dbl` (pass;
knobs 1.8e-13, gains 2.2e-16), both valid under the new check with the comparisons recomputed.

**Draft 4 changes** (internal review round 3, `docs/revision/roster/{sol,astra}-runner-up-plan-r3.md`, both reject): the
evidence is verified per named check (`guards.check_reset_evidence`): the headline F111 D2 reproduction gate from the Mac
and, bit-identical, from this machine, and the fresh0 F111 D2+H3 doubling gate; each directory's gate record must have
the right stage and cell and pass, its inventory must list the current gate and input hashes and name the current reset
driver, its inputs must equal those recomputed from the original records, and its search record must carry the full
budget (refusal tests for unrelated, incomplete, stale, and edited evidence); the environment comparison covers SciPy,
CMA, BLAS and LAPACK; bank copies are checked against the original freeze before reference construction, also when
resumed at `--stage reference` (test); the run binding includes the hashes of the helper, `guards.py`, `common.py`, this
plan, and the report; failed-attempt spend comes from the launcher's attempts file (required); the launcher's stop rule
is stated.

**Draft 3 changes** (internal review round 2, `docs/revision/roster/{sol,astra}-runner-up-plan-r2.md`, both reject): each
bank copy's actual SHA-256 must equal the original freeze hash before the reference is built and at acceptance (a
changed bank with a rebuilt reference is refused, test); the evidence is the named set, bound to the current reset driver
and environment, with the pod gate `--reproduce --require-identical` required bit-identical on this machine; the
reservation is the full 3.00 USD stop cap; a paid run requires the pod allocation time and carries earlier failed
attempts (`--prior-spend-usd`, replaced in draft 4 by the launcher's attempts file).

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
- **Reproduction gate.** Required before any search (`check_run_evidence`, `guards.check_reset_evidence`): `--reset-mac`, the
  reset driver's headline F111 D2 reproduction gate directory from the Mac; `--reset-pod`, the same gate run first on this
  pod with `--reproduce --require-identical`, bit-identical, with the same numerical stack (CPU, platform, Python, numpy,
  SciPy, CMA, BLAS and LAPACK); `--doubling-evidence`, the reset driver's fresh0 F111 D2+H3 doubling gate directory. Each
  is verified: stage and cell, a pass, inventory hashes of the gate and input records equal to the files, the current
  reset driver, the inputs recomputed from the original records, the registered full budget.
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
(x 1.25 = 2.49); **stop cap 3.00 USD**, the full allowance; **reservation 3.90 USD** (1.3 x the stop cap, the watchdog bound;
amendment above) in the ledger category `followup` (cap 72 USD shared by all follow-up runs; `budget_followup.py reserve`). A paid run
requires `--started-at <allocation time>` and the launcher's attempts file (`--attempts`). The driver checks
the cap between stages: a stage starts only if the billed time so far
plus its estimate stays within the cap; a running stage is never killed (author's instruction); the run stops, writes
`cost_stop.json` and an inventory, and reports. This is an admission limit, not a billing ceiling: a stage that starts
within the cap finishes, and the pod is deleted after it.

**Launcher handoff (draft 5).** The launcher copy pushes to the pod, before every paid driver call, its current
`<name>.attempts` file and the ledger, and passes `--attempts`, `--ledger`, `--run-tag`, `--started-at` (the current pod's
allocation time), `--usd-per-hour` (the price ceiling MAXCPH), `--stop-file /root/STOP`, and `--soft-deadline` (its soft
deadline). The driver reads the launcher's own event lines (`<pod> <epoch> start`, `<pod> <epoch> deleted`;
`guards.attempts_spend`): each closed attempt counts at the ceiling, and the open start is the current pod, counted from
its recorded `start` event (a later `--started-at` cannot shorten it; it must lie between that event and now); malformed or unordered lines are refused (tests with lines in the launcher's exact format); spend of
earlier launches comes from the ledger rows tagged with the run tag, since the launcher truncates its file per launch. The
driver checks the STOP file and the soft deadline before each internal stage or round, so a single `--stage all` call
honours the launcher's between-stage stop (test).

**Admission before every paid step (draft 6).** Before the pod's first paid step, and before each later one (the reset
reproduction gate included), the launcher runs `python3 docs/revision/followup2/guards.py admit --cap-usd 3.00
--usd-per-hour <ceiling> --started-at <allocation> --attempts <file> --ledger <ledger> --run-tag runner-up --hours <step estimate>
--stop-file /root/STOP --soft-deadline <soft>` and starts the step only on exit 0. Reservation: `python3 docs/revision/followup/budget_followup.py --reserve runner-up-<n> 3.12`; the
launcher requires one `followup` reservation `runner-up-<n>` (its launch tag) of at least 1.3 x the stop cap minus the run's
recorded spend (3.90 USD on a first launch; the ledger grants less when the category is nearly full), else no pod; the reservation covers the watchdog bound, 1.3 x the stop cap, because a stage admitted within the cap finishes and only the watchdog at 1.3 x the cap stops a running stage (churn launcher review r1, Sol and Astra); `guards.check_grant` against the stop cap is replaced by the launcher's check that one `followup` reservation tagged with this launch covers 1.3 x the stop cap minus the run's recorded spend. The launcher copy itself (a copy of `results/pods/reset_pod.sh`) is not part
of this folder and is to be written and tested offline before allocation.

**Launcher and the cap.** The pod launcher is a copy of `results/pods/reset_pod.sh` with `results/pods/podctl.py`. Its soft
deadline is the cap at the price ceiling MAXCPH, counted from the first creation request of the launch, so it holds across
attempts; at the soft deadline the remote script stops before its next stage (a STOP file read between stages), and the
driver's own admission check (`--cap-usd`, `--started-at`, `--attempts`) stops between stages or rounds as well. A running
stage is never stopped (the author: do not kill jobs). The single exception is the watchdog, which deletes the pod at 1.3 x
the cap at the price ceiling; that is the only mid-stage stop. Closed attempts are listed in the launcher's
`<name>.attempts` file (event lines `<pod> <epoch> start` and `<pod> <epoch> deleted`), which the driver reads
(`guards.attempts_spend`) and counts toward the
cap before each paid attempt; a paid run without it is refused (no default of zero); after the launch the spend is recorded
in the ledger (`budget_v2.py --record`).

## 6. Steps

1. Internal review to consensus; freeze this plan.
2. Reserve 3.90 USD in the ledger (input 3.12); one pod: `reset_followup_v2.py --reproduce --require-identical`, then `runnerup_v2.py
   --stage all --workers 12 --reset-mac M --reset-pod P --doubling-evidence D --cap-usd 3.00 --started-at T --attempts A --ledger L --run-tag runner-up --stop-file /root/STOP --soft-deadline S`; delete and verify the pod; record the spend.
3. Analysis on the Mac from the retrieved records; a paper paragraph and table labelled exploratory, after review.
