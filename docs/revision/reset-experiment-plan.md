# Reset experiment: plan (draft 5, 2026-11-10; draft 4 had internal consensus and the author's approval, cap 10 USD; no spend yet)

**Why.** The round-9 fresh reviewer (problem 2, `docs/paper/external-review-r9.md`): the gain is excess profit when
identity replacement is available; it does not show how much of that profit comes from the ability to replace an
identity. This plan measures that, within the searched D2 family, on the second test's markets.

**Draft 5** (2026-11-10) applies the Fable 5.2 driver review (`docs/revision/roster/fable52-reset-driver-r1.md`, triage
`docs/paper/fable52-triage.md`): a reproduction criterion that a cross-platform run can meet, a pod gate, the driver's
location under `docs/`, the diagnostics built and run free before the pod, a doubling ground truth, and clarified scoring.
It needs one internal review round.

**Status.** Draft 4 applied the round-3 caveats (`docs/revision/roster/{sol,astra}-reset-plan-r{1,2,3}.md`; round 3: both accept-with-caveat).
After consensus: a decision card for the author. Nothing runs before the author approves the spend. This file is frozen
(commit hash in the operations ledger) before any paid cell starts.

## 1. What already exists (free; seen before this plan)

The D2+H3 family is D2 plus one binary knob `x` (`sim/policies/identity.py`: `x = 1` exits in the round after a failed
audit and re-enters under a fresh identity; `x = 0` is plain D2). Design 8.1 listed D2 on all seven markets ("Matched core
extras"); budget cut 3 removed the fresh-market D2 cells, so D2 was run at the headline market only. At `headline@rho0.2`,
same 200 evaluation seeds, same frozen reference per rule (checked: `seeds` and reference `upstream` hashes equal):

| Rule | g(D2+H3) | g(D2) | I = g(D2+H3) - g(D2) | Paired SE of I | D2+H3 doubling check |
|---|---:|---:|---:|---:|---|
| B2 | 0.5851 | 0.0027 | 0.5824 | 0.0011 | not scheduled |
| B3 (F000) | 0.3502 | 0.0435 | 0.3067 | 0.0012 | flagged |
| R3 (F111) | 0.0486 | 0.0361 | 0.0124 | 0.0009 | flagged |
| C* | 0.0872 | 0.0433 | 0.0439 | 0.0008 | not flagged |

Source: `results/v2/eval/all/evaluate/headline@rho0.2__{rule}__{D2+H3,D2}__profit.json`, field `gain`; flags from
`report.json` `search_flagged`; the D2 cells had no scheduled doubling check. At `headline@rho1`, R3 and C* are in the
terminal-reserve collapse and I is 0.0025.

Reading, exploratory: at the headline market the D2+H3 search leaves about 0.31 more gain than the D2 search against B3,
and about 0.01 against R3; the B3 - R3 gap is 0.302 under D2+H3 and 0.007 under D2.

## 2. Estimand

For rule r in {B3 (F000), R3 (F111), C*} and fresh market m:

I(r, m) = mean over the 200 evaluation seeds of g(D2+H3 winner) - g(D2 winner),

both against the same frozen truthful reference of (r, m), so the reference term cancels. **I is a difference between two
prescribed finite searches over nested families (D2 within D2+H3), not an identified optimal value of replacement and not
a system-wide prohibition of replacement.** The two searches differ in dimension, Sobol starts, and corner sets (D2 128,
D2+H3 256 corner vectors), with the same restart and evaluation budgets; the two winners can differ in every knob, not
only `x`. A negative I can come from search error. The fixed-policy diagnostic in section 4 separates the switch from
re-optimisation.

## 3. Cells and execution contract

- **New search cells.** D2 x {F000, F111, C*} x fresh0..fresh5 at rho 0.2: 18 cells, exactly the design-8.1 cells that cut
  3 removed, with their registered settings (D2 knob space and budget, the market's training seeds for search, its 200
  evaluation seeds), each with a doubling check (design 6.5, held-out evaluation of the doubled winner on the same seeds).
- **Driver.** A separate follow-up script (`docs/revision/followup/reset_followup_v2.py`, under `docs/` because the code
  freeze allows changes only there; written and tested before any spend) that
  imports the frozen stage functions of `scripts/revision_v2.py` at the protocol-v2 tag (`job`, `stage_search`, the
  evaluation and doubling stages) and builds the 18 jobs from the uncut cell list. It bypasses only three things, each
  recorded as a deviation: the fixed manifest path and cut list (`sim/manifest_v2.py` `effective`), the hard-coded doubling
  eligibility (`doublings`), and the original freeze. It writes to a new directory (`results/v2/followup-reset/`) and
  never writes to `results/v2/eval/all`.
- **Inputs the frozen stages read.** The search, evaluation, and doubling stages read their dependencies from the output
  directory (`menu()`, `reference_of()`, `select_reference()`). Before any episode, the driver copies into the new
  directory, read-only, every record those stages read for the 18 cells: the frozen reference records, the search
  records and bank-source records that build each (context, rule) menu, and the original cuts-3 bank membership. It
  takes the list from the `upstream` fields of the existing records and checks each copy's SHA-256 against them; it
  refuses on any missing record or mismatch.
- **Two freezes.** A pre-evaluation freeze after the 18 searches: selected policies, references, configurations, seeds,
  and search records, with their hashes (the frozen evaluation stage requires it). Evaluation and doubling then run
  against that freeze, and a final inventory lists every output record with its hash. The inventory is written after
  the outputs, so no record hashes itself.
- **Freeze validator.** The frozen `run()` calls `accept()`, which requires the original manifest's full record set, so it
  cannot admit the 18 restored cells. The driver therefore has its own acceptance check, run before evaluation and before
  doubling: every record of the follow-up dependency set (the copied inputs, the 18 search records, the pre-evaluation
  freeze) exists and matches its hash; the identity-salt hash matches; each new job's configuration hash equals the
  recorded container hash. Copied records keep their original provenance, including their recorded configuration
  hashes. Tests: it refuses a missing freeze, a changed selected-policy record, a changed salt, and a changed copied input.
- **References in doubling.** The held-out gain of a doubled winner uses the unchanged frozen reference. Any reference
  reselection the doubling stage computes is recorded as a diagnostic only.
- **References.** The existing frozen reference records are read, not re-selected; the driver refuses to start if any
  reference file's SHA-256 differs from the hash in the original records' `upstream`.
- **Configurations.** Linux pods from the same image as the evaluation; before any episode the driver checks that each
  fresh market's configuration hash equals the recorded container hash (`addendum.json` `deviations.configs`), so the
  new cells use the same configurations as the D2+H3 records they are paired with (the recorded 1-ulp deviation stays as
  it is).
- **Pairing and code checks (draft 5).** Before any episode the driver refuses a job whose runner, salt, configuration,
  root, seeds, rule parameters, or context differ from its frozen reference's provenance; an unknown commit; a runner or
  `sim/` that differs from protocol-v2; an output inside `--src` or `eval/all`; and a salt mismatch. The inventory records
  Python, numpy, machine, platform, and the driver's hash.
- **Validation before spend (free, on the Mac).** (a) Reproduction of the registered `headline@rho0.2|F111|D2` search and
  evaluation. Draft 4 required identical knobs and per-seed gains. Measured on 2026-11-09/10: a Mac arm64 run and a Linux
  amd64 container run both match on configuration, salt, runner, budget, rule parameters, episode count (15,660), archive
  sizes, and the twin result, with selected knobs equal to 2.6e-13 relative and per-seed gains to 2.0e-14; evaluating the
  registered knobs on the Mac gives per-seed gains within 5e-17 of the record (102 of 200 seeds bit-identical). The
  evaluation of fixed knobs is not always this close: one of the 128 corner controls of the Mac rerun differs by 1.5e-5
  with identical knobs (the other 127 within 2e-18), consistent with a near-tie flipping a discrete branch in an episode;
  in the Linux container all 128 controls are bit-identical to the record. The drift source is therefore not isolated to
  the optimiser. Last-bit
  arithmetic differences grow through the search; these runs did not reproduce bit identity across platforms, and the
  draft-4 rule is replaced as a recorded deviation. **Draft-5 criterion** (`compare()`). Exact: the provenance keys runner, salt, configuration, rule
  parameters, root, training, validation and evaluation seeds, context and budget (the commit may differ); the episode
  count; the attack and twin archive sizes; `best_source`; the discrete knobs; the search and evaluation dependency ids;
  the reference hash; the control set (knobs in order). Within 1e-9: the twin's best value. Reported, not gated: the
  corner controls' objective values (count and largest difference), because a near-tie in a non-selected corner policy
  can flip a discrete branch. Finite: the knobs, the attack, twin and control objective values, and the per-seed gains. Tolerance: continuous knobs within 1e-9 relative and per-seed
  gains within 1e-9 absolute (about 10^4 times the drift measured, and far below the paired standard error of about
  0.0009). The Mac runs pass this criterion. **Pod gate:** the pod first reruns the same reproduction (about 0.34 USD of
  billed time: 2,084 s search plus evaluation at 0.56 USD per hour); the author decided (card `touchstone-reset-repro-pass`,
  2026-11-10) that the 18 cells start only if the pod's reproduction is bit-identical (`--reproduce --require-identical`);
  any difference stops the pod and is reported. The draft-5 criterion applies to the Mac validations (`identical` requires bit-equal knobs, gains, twin value,
  attack objective and every control value). The reproduction path runs every pre-episode check
  (salt, commit, code, pairing, configuration) before its search and saves `gate.json` and an inventory with the
  environment (Python, numpy with BLAS and LAPACK, SciPy, CMA, CPU). (b) An
  integration test runs the complete path (input copies, search, pre-evaluation freeze, evaluation, doubling, inventory)
  for one fresh-market cell at smoke size, including the driver's acceptance check, which proves every dependency
  resolves (passed, 2026-11-09). (d) Doubling ground truth: the driver's doubling stage reruns the registered doubling
  check of `fresh0@rho0.2|F111|D2+H3|profit` on the Mac (`--reproduce-doubling`), after the full preflight, saving a record with provenance and dependency
  hashes, `gate.json`, and an inventory; compared by `compare_doubling()`: required fields present; finite values; exact on
  the flag, the seeds and the discrete knobs; 1e-9 on the continuous held-out knobs, the attack and reference
  changes, and the held-out per-seed gains. The saved result must pass before any pod is created. (c) Unit tests: the driver refuses a
  changed reference hash, a missing input record, a wrong configuration hash, and an output directory inside `eval/all`.

## 4. Diagnostics (evaluation only, no search)

For three rules on seven markets: the base and doubled D2+H3 winners (42 policies) and the base D2 winners (21; the doubled
D2 winners are not included), on the 200 evaluation seeds, re-run with reset and ban instrumentation (63 single-policy
evaluations; the existing gain records carry no reset counts, so none is reused); the selected `x`; per episode the number of resets, the probability of at least one reset, the rounds of resets,
and the rounds spent banned. Check that every D2 winner has zero resets. **Reverse switch (draft 5):** each of the 18 D2 winners re-evaluated with
`x = 1` and every other knob unchanged (18 more evaluations). The diagnostics are built and tested in the driver (`diagnostics`
stage) before any pod. Order: the instrumentation is validated on the registered headline cells before the pod; the
diagnostics of the 18 new D2 winners and their reverse switches run on the Mac after the pod's records are retrieved.
Construction: a D2 winner is embedded in D2+H3 by adding `x` (0 for itself, 1 for the reverse switch); each switch is
the mean difference of normalised profits on the evaluation seeds, the reference cancelling. Resets are the focal
provider's identities of generation 1 or more; ban rounds are the ban lengths imposed on its identities; rounds without
an offer are counted separately. Saved per policy: the seed identifiers, the per-seed normalised profits, the per-seed switch differences, and the
reset and ban counts per episode; a D2 winner with any reset stops the run. Spot check: `fresh0@rho0.2|F111` is also
diagnosed on the pod (`--diag-cells`); the Mac's reset and ban counts must equal the pod's exactly, and its numerical
values must
meet the draft-5 tolerance against it. **Fixed-policy switch:** each of the 42 D2+H3
winners re-evaluated with `x` set to 0 and every other knob unchanged (42 more; a winner that already has `x = 0` is
reported as identical and not re-run); g(winner) - g(winner, x = 0) is the effect of the switch
without re-optimisation, reported beside I.

## 5. Analysis (fixed now)

- **Intervals.** Per market: paired seed bootstrap (9,999 resamples, percentile, 95%), the same resampled seed indices for
  every rule and family of that market, so contrasts across rules stay paired. Pooled: equal market weights; in each
  replicate, seeds are resampled independently within each market and the pooled statistic is the mean of the six market
  means; percentile interval. Nominal and descriptive; conditional on the six markets and the frozen policies and
  references.
- **Statistics.** I(r, m) and pooled I(r); the contrasts I(B3) - I(R3) and I(C*) - I(R3); the absolute gaps
  G(D2+H3) = g_B3 - g_R3 under D2+H3 and G(D2) under D2, pooled.
- **Share.** S = 1 - pooled G(D2) / pooled G(D2+H3), a ratio of pooled contrasts, computed in every bootstrap replicate.
  S is reported only if the lower bound of pooled G(D2+H3) exceeds 0.05; otherwise "not defined". No clipping; S can be
  negative or above 1. The absolute gaps are always reported beside it.
- **Market sensitivity (draft 5).** The sign count of I(B3) - I(R3) and I(C*) - I(R3) over the six markets, and S with
  each market left out in turn (six values), each with its own five-market denominator gate (lower bound of the
  five-market pooled G(D2+H3) above 0.05; otherwise that value is "not defined"), for the base and the doubled results
  separately. A nested best-of sensitivity (the better of the D2 and D2+H3 winners per cell) is deferred: it is not
  part of this plan.
- **Doubling flags.** For each D2 cell, the attack change and the reference-reselection change of its doubling check are
  reported separately.
- **Doubled versions** of the same statistics, as in the paper's `tab:ph-doubled`. The base (frozen) searches are primary,
  as in the paper; the doubled versions are reported beside them.
- No confirmatory test, no multiplicity family, no change to any registered decision.

## 6. Pre-specified expectations and labels

Written before any fresh D2 result exists. **The six markets, their seeds, and their D2+H3 outcomes were already observed;
only the D2 outcomes are unseen.** This is a descriptive follow-up specified on 2026-11-09 after the round-9 review and
after the headline contrast was seen, not an independent replication.

Expectations: on all six fresh markets (each market counted; a single market against it fails the expectation), I(B3) > I(R3) and I(C*) > I(R3); pooled S defined and greater than 0.5. Expectations are
scored on point estimates (this is a descriptive follow-up; "met" does not mean that an interval excludes the threshold),
with the denominator gate of section 5 applied separately to the base and the doubled results. Each expectation is
scored as met, failed, or not established: **met** if it holds under both the base and the doubled searches; **failed** if
it fails under both; **not established (search-sensitive)** if the two disagree. An undefined S and a missing cell are
reported as such, separately from failures. A failure is not read as evidence for any particular cause (search error and
mixed outcomes are possible). Only if the pooled-S expectation is met may the paper say: within the D2 family, at the
fixed parameters and search budgets, most of the estimated B3 - R3 gap under the prescribed searches disappears when the
attacker cannot replace its identity.

## 7. Cost

**Work.** Measured benchmark (`experiments/v2/benchmark/timings.json`): one unit = a headline D2+H3 cell, 0.579
core-hours. Per D2 cell: 1 unit + 160 further seeds (0.046) + doubling with held-out evaluation (0.479); 18 cells = 27.45
units. Diagnostics: 63 instrumented evaluations + up to 42 switch evaluations = up to 105 single-policy evaluations of
200 episodes, priced conservatively at the profit-evaluation stage's cost for 200 seeds (0.058 units each, although that
stage evaluates more than one profile) = about 6.1 units. Total about 33.6 units = **about 19.4 core-hours**. Draft 5
moves the diagnostics to the Mac (free) and adds the pod gate (about 0.34 USD); the pod estimate below is kept as an
upper bound.

**Billed pod time.** One 16-vCPU pod at the recorded 0.56 USD per hour; searches with 16 workers, evaluation, doubling,
and diagnostics with at most 10 (operations ledger). Stage schedule with incomplete worker batches and equal benchmark
task times: searches, evaluation, and doubling about 1.77 hours (internal review's computation); diagnostics about 0.6
hours (105 evaluations in batches of 10); preparation 0.3 hours; idle tail 0.3 hours = **about 3.0 billed hours, about
1.66 USD**. The benchmark's unit price (0.0625 USD per unit, at its 0.108 USD per core-hour) gives about 2.10 USD; the plan
uses the larger.

| Item | Estimate | Cap |
|---|---:|---:|
| Option A: 18 D2 cells, doubling checks, diagnostics | 1.66 to 2.10 USD | **10.00 USD** (author, 2026-11-09) |

A failed attempt counts toward the cap; the cap leaves room for one early failure, not for a full second run. Option B (an X7-SC variant with replacement disabled) is dropped from this plan: its
constrained family, incumbents, and corner controls would need their own specification (the frozen X7-SC search inserts
D2+H3 incumbents that can replace), so it is not offered for approval.

**Budget.** `docs/revision/budget-ledger.json`: spent 50.869 USD of the 55 USD approval limit. The author approved option A
on the board on 2026-11-09 and set the cap to 10 USD ("make the cap $10 to ensure we're not blocked by a low cap"). The
ledger needs a new category `followup` with cap 10.00 and the approval limit raised to 61 USD (50.869 + 10 = 60.869,
`python3 -c "print(50.869+10)"`). `scripts/budget_v2.py` is frozen, so the tested wrapper
`docs/revision/followup/budget_followup.py --approve 61 10 TEXT` records both, refuses a limit below spend plus the cap,
and keeps the earlier approval text. The estimate is unchanged (1.66 to 2.10 USD); the higher cap only prevents a stop from a low
cap. Stop at the cap.

## 8. Steps

1. Internal review of this plan to consensus; freeze it (commit).
2. Decision card: approved on 2026-11-09, cap 10 USD (card `touchstone-reset-spend`).
3. On approval: write and test the driver (TDD); on the Mac (free), validations (a), (b) and (d) must pass through the
   corrected paths (preflight run, record with provenance and dependency hashes, `gate.json` and an inventory saved in a
   new directory each: `results/v2/followup-repro-v2`, `results/v2/followup-repro-doubling-v2`); earlier passes on the
   older path do not count and the diagnostics are validated on the registered headline
   cells, all before any pod is created.
4. One pod: the reproduction gate first (bit identity, `--require-identical`; stop and report on any difference), then `--stage all` with
   `--diag-cells fresh0@rho0.2|F111|D2|profit` (inputs, search, freeze, evaluate, doubling, spot diagnostics, inventory);
   records retrieved, the pod deleted and the deletion verified, the spend recorded.
5. On the Mac after retrieval: the diagnostics of all 18 D2 winners and their reverse switches (`--stage diagnostics`),
   checked against the pod's spot-check cell. The three headline cells (registered D2 records) run on the Mac before the
   pod (`--headline-diagnostics`, 200 seeds); with the 18 fresh cells this gives the 63 policies and 42 switch
   comparisons of section 4 plus the 21 reverse switches.
6. Analysis: a new `reset` block in `posthoc_v2.py` (tested first), a table, and a paragraph in section 9 with sites; the
   section-1 headline numbers enter at the same time, labelled exploratory.
7. Internal review of the paper change, then the next external package.
