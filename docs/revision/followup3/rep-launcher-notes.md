# Churn replication: implementation and pod launcher (notes for review; no spend)

Scope of this review: the replication's code under `docs/revision/followup3/` against the consensus plan
(`replication-plan.md`, draft 3 with the r3 caveats, commit 3bcd6b1; the cost paragraph of section 6 updated in
implementation review r1), before the manifest is built and stamped. Round 1's corrections and their tests:
`rep-impl-r1-response.md`.

| File | Role |
|---|---|
| `replication_analysis.py` (+ tests) | paired changes over the six named markets, the support criterion, the five expectations, absolute contrasts, attack and reference terms, efficiency, seed-bootstrap intervals with one index array per market |
| `commitment.py` (+ tests) | manifest bytes, the required file set and the import closure, hash verification, frozen-code, frozen-input and environment-override checks |
| `continuation.py` (+ tests) | the churn-aware adapter: churn in every worker, every menu candidate replayed under the cell's churn |
| `rep_v2.py` (+ tests) | the driver: instances, calibrate, menu, cthr, gate0, rates (p0 / churn), continue, inventory, analyse; the output binding |
| `rep_collect.py` (+ tests) | the continuation gate and queue, the continued-winner diagnostics, the record loader with validation |
| `rep_pod.sh` (+ `test_rep_pod_harness.sh`) | the two-pod launcher, generated from the reviewed Run B launcher `followup2_pod.sh` |
| `cost_estimate.py` | the committed cost schedule (step estimates below come from it) |
| `test_notes.py` | every ruling below quotes the plan sentence it rests on |

Run the checks: `uv run --frozen pytest -q docs/revision/followup3/` and `bash docs/revision/followup3/test_rep_pod_harness.sh`
(about an hour; the reviewers' read-only sandbox cannot run it, so its log is named in the brief).

## Smoke evidence (Mac; scratchpad `repsmoke`)

Round 1 (2026-11-19, `run2`): the full chain ran in smoke mode on the registered draw (instances reproduce the registered
ones; calibration matches the registered Mac calibration; menus, references, C-thr, every rate, the churn-zero gate
bit-identical, continuation with round 1 equal to the doubling record at differences 0.0, the analysis). Round 2
(`run3`, after the record binding changed the provenance): every stage, instances to inventory, ran (`chain3.sh`): the continuation gate ran with no flagged cell and its round 1 matched the doubling record at differences 0.0; every evaluation and reference provenance carries the manifest and draw hashes (spawned workers included); the analysis scored all 72 cells (0 unscorable, 0 problems); the root inventory verifies (1355 records, 0 bad, 0 not inventoried). No smoke cell was flagged, so the continued-winner diagnostics were run on a copy (`diagprobe.py`) with the gate's continued record: with the frozen winner's knobs they reproduce the frozen diagnostics exactly (audit 23 of 1325 jobs, identical per-seed profits).
Round 3 (`run4`, commit 0bdc0cb, manifest built at that commit; `chain4.sh`): every stage, instances to inventory, ran
(CHAIN_OK); each of the six rate directories has `diagnostics_binding.json` in its inventory; the analysis scored all 72
cells (0 unscorable, 0 problems, gate_ok true, no mismatch); expectation 5 is scored in both sets, so every frozen R3
audit count passed the binding and completeness checks (6 markets at p = 0 and 0.05); the root inventory verifies with
the launcher's verifier (1361 records, 0 bad, 0 not inventoried; 6 more than round 2, the binding files).

## Memory (plan section 5)

Mac peaks, one task in a child process (`ru_maxrss`): a target's reference 254 MB (16.7 s); a full X7-SC menu search
232 MB (5669 s; fresh0, R3, registered market; scratchpad `memsearch`); a full D2+H3 search 183 MB (operations ledger);
one Run B X7-SC continuation cell over three rounds 3.54 GB (`results/pods/memprobe3`). The launcher uses 254 MB for
searches and refuses before any marker unless 16 search workers and 5 continuation workers fit the 28 GB pod floor at
1.25 x the peak plus 2 GB; on the pod every search stage (menu, C-thr, churn search, gate0) admits its workers against
the cgroup limit and keeps the lowest count for the output (`search_workers.json`); evaluation and doubling use the churn
arm's pod-side preflight, whose counts are kept the same way.

## The two pods

| Pod | Step (launcher admission `--hours`, from `cost_estimate.py` at flag share 0.5) | Driver call |
|---|---|---|
| 1 | instances 0.05; calibrate 0.25; menu 7.60 (4 of 5 search waves of both families + references); cthr 1.95 (1 wave of each family); inventory | `rep_v2.py --stage <s> --out results/v2/followup3-rep --manifest <bundle>/draw/manifest.json --draw <bundle>/draw/draw.json` |
| 2 | rates p0 1.68; gate0 1.20; rates churn 9.05; continue 0.51 (the gate cell's round; every later round is admitted inside); inventory | the same, with pod 1's verified output copied in as `results/v2/followup3-rep` |

End states on pod 2: a churn stage stopped by the driver's cap (`churn arm stopped between stages`, exit 1) is "STOPPED
BEFORE a <step> stage (cap, driver admission)"; the churn-zero gate failing is "GATE FAILED at gate0"; continue exit 3 is
"STOPPED BEFORE a continuation round", 4 "GATE FAILED at continue", 5 restarts once on 3 workers with the driver's own
restart estimate, 6 "RUN FAILED at continue (a cell error)". Every failure or stop exit writes the inventory first.

## Rulings

Each ruling quotes the plan text it applies (`test_notes.py`); anything the plan does not say is marked as an addition.

1. **One run tag, one stop cap, one pod name for both pods.** Plan: "The run may use two pods (menus and references; then
   evaluation, churn and continuation) to stay under a day per pod. The stop cap is set on the spend card; the
   reservation covers 1.3 times that cap." Both pods record spend under `replication-<launch tag>` and run under the pod
   name `ts-rep`, so one launch lock covers the replication and pod 2 is refused while pod 1's spend is unrecorded. Pod 2
   names pod 1's launch tag (`POD1TAG`): that spend row must be in the ledger exactly once, pod 1's output must name the
   same launch (`launch.json`), and the two launch tags differ. Pod 2's PRIOR is pod 1's recorded spend.
2. **PLANCAP 33 USD.** Plan: "with the 1.25 headroom 29.78 and 32.13" (rounded up); the spend card sets the cap at or
   below it; the reservation must cover 1.3 x the cap less PRIOR (42.9 at the full 33).
3. **The driver's own admissions count PRIOR plus this launch's closed attempts at the ceiling** (`--prior-usd`, the
   rule of `guards.paid_cost_stop`). Plan: "the reservation covers 1.3 times that cap". The launcher computes it from the
   fixed attempts file.
4. **Menu and C-thr searches have no in-stage cost check** (the frozen `R._pool` runs a whole family); the launcher's
   step admission and the watchdog bound them. Plan: "the reservation covers 1.3 times that cap". A long stage can pass
   the cap by at most that stage (the author's rule: do not kill jobs), plus the transfer and deletion time after it; the
   watchdog deletes the pod at 1.3 x the cap.
5. **The continuation gate is the first p = 0.05 cell, rep0 R3, whether flagged or not** (r1 ruling withdrawn: it had
   taken the first flagged cell). Plan: "then, after the first p = 0.05 cell's search, evaluation and doubling (reused in
   production), its continuation round 1 against its own doubling record, required identical". The gate runs round 1
   in a child process before any queued cell, also when no cell is flagged; its record (`continuation/gate/`) never
   enters a result. "Identical" means all three of Run B's differences are exactly 0.0, for the gate and for every
   continued cell; a gate without a measured comparison does not pass (smoke runs excepted).
6. **References run serially** (18 targets plus 6 C-thr, 12.7 s each in the benchmark). Plan: "C-thr(12) uses its own
   searches and a copy of the bank, as Run A did".
7. **The calibration runs once, on pod 1.** Plan: "The instances are calibrated once, on the pod's Linux x86 stack".
   Pod 2 reuses it only after the launcher and every driver stage check the configuration hash against the calibration
   record and the record says Linux x86 (the launcher's pod 2 bundle guard checks both the system and the machine, review
   r2); no stage overwrites an existing calibration or `instances.json`.
8. **Expectation 5 uses the primary winners** (r1 ruling withdrawn: it had used the frozen winners). Plan: "primary
   winners; frozen winners reported beside". The continue stage reruns the churn arm's diagnostics for every R3 menu cell
   at p = 0 and 0.05 whose continued winner enters the primary set; a missing one makes that market's expectation 5
   "not scorable" for the primary set. Every diagnostics row is checked before its counts are used or reused (the
   winner's knobs, the ordered evaluation seeds, finite profits, one episode per evaluation seed with the four age bins
   of `churn_v2.AGE_EDGES`; for continued rows also stage, id and provenance; review r2, r3). A frozen row also needs
   `diagnostics_binding.json`, written by the rate stage after the diagnostics step and before the inventory: it names
   the rate, the hash of `diagnostics.json`, and per cell the job id, its provenance and the hashes of the search and
   doubling records the diagnostics reran (review r3). The primary set's count comes from the primary winner's own
   diagnostics: a continued winner's from its continued diagnostics, independent of the frozen row; a frozen winner's
   from the frozen row (review r4).
9. **Publication height.** `PUBH` is required: a block height, or `none`. Plan: "Without publication before H, the draw
   wrapper records the draw as nonconfirmatory". The push of the manifest commit needs the author's consent first.
10. **The record binding.** Plan: "Every record binds to this plan's hash, the draw record, the configuration hashes and
    the driver hashes." Every provenance built by the driver carries the manifest's hash (which covers the plan, the
    drivers, the analysis and the parameters) and the draw record's hash, beside the draw root, seeds, salt and
    configuration hash it already had; every stage checks `binding.json` against its `--manifest` and `--draw`. Before
    scoring, every evaluation and doubling record is checked for stage, id, provenance and values, its exact dependency
    set and every dependency hash, positive normalizers, and the doubling flag against the frozen rule; every
    continuation and gate record for stage, id, provenance, a known status, its own identical comparison with a finite
    round-1 winner, rounds that agree with the status (Run B's pass rule) and a held-out winner equal to the last
    round's, on the job's own evaluation seeds (the gate included); a measured round 1 must also agree with the cell's
    own doubling record and frozen search (held-out knobs and mean, both changes, round 1's best knobs, the doubling
    winner's held-out gains) and carry Run B's empty problems list; a well-formed round 1 that disagrees is a round-1
    mismatch (all continuation stops, no primary set), a malformed one an invalid record. A wrong value type anywhere,
    a record root that is not an object, a number too large for a float, or a normalizer that is not positive after
    the division by N is a failed check, not an error; identity comparisons use strict JSON equality (review r4, r5). The same check runs before a saved record is reused
    on resume; a record that fails it, an unknown status included, is set aside and its cell rerun (review r4). In the analysis, a flagged cell whose
    continuation record fails it keeps its validated frozen winner and counts as not continued, as section 4 says for
    missing or nonfinite output (review r2, r3).
11. **Kept worker counts.** Plan: "lowered if needed, then kept across restarts". Search workers: `search_workers.json`;
    continuation: `continuation_workers.json`; continued diagnostics: `diagnostics_workers.json` (review r2), requested
    from `--workers-cont`, which the launcher lowers on its restart after a lost worker, so a diagnostics loss also
    restarts on fewer workers (review r3); evaluation and doubling: the churn arm's saved counts.
12. **What the manifest cannot list** (partial decline of Astra r1 item 1). Plan: "every imported helper outside `sim/`
    and `scripts/`". The Mac-side launcher helpers (`results/pods/podctl.py`, `runpod.py`, `case_end_check.py`) are not
    in the repository and are not imported by the drivers; the launcher checks its own bytes against the manifest's
    `rep_pod.sh`, and the pod-side code guard checks every listed file in the tarball. Caveat (Astra r2): the launcher's
    self-check does not verify these Mac helpers, so their correctness rests on their own harnesses
    (`test_rep_pod_harness.sh` runs the real `podctl.py` and `case_end_check.py`), not on the manifest.

## Pre-launch steps (after review consensus; none done yet)

1. Commit every correction; build the manifest (`commitment.py build`, which refuses a list without the required set
   and the drivers' import closure).
2. Author's consent, then push the manifest commit (no `sealed/` files); record the publication height.
3. Stamp the manifest (OpenTimestamps); wait for H = A + 144 and six confirmations; draw once.
4. Spend card with the stop cap; reserve `replication-<pod 1 tag>` in the ledger (1.3 x cap).
5. Code tarball from a clean clone at the launch commit (`tar --uid 0 --gid 0`, `COPYFILE_DISABLE=1`); bundle 1 =
   `draw/{manifest.json, manifest.json.ots, draw.json}`.
6. `DRYRUN=1` guard check; launch pod 1 detached with a pid file.
7. After pod 1: record its spend; bundle 2 = bundle 1 + `rep/` (pod 1's verified output); reserve
   `replication-<pod 2 tag>`; dry run with `POD1TAG`; pod 2.
