# Operations ledger, revision program (protocol v2)

Part B of `docs/superpowers/plans/2026-10-25-revision-operations.md`. One entry per operation step: date, commit, command, pod ids, USD, outputs and hashes, deviations. Paid spend is also recorded in `docs/revision/budget-ledger.json` with `budget_v2.py --record`.

`code_commit` = `627a2de9ad6c838e4228893c3107d173118d5d62` (Part A2 merged, signed).

## Operation 2: Benchmark and the cost decision

### 2.1 Smoke benchmark (wiring only), 2026-10-28

- Commit: 627a2de (worktree `claude/vigorous-villani-bbac79`).
- Command: `uv run python scripts/benchmark_v2.py --run --smoke --out results/v2/benchmark_smoke`
- Result: exit 0, 4 min 33 s on the laptop (1 worker); `timings.json`, `cost_table.json`, `benchmark_plan.json` written. No spend.

### 2.2 Benchmark pod, 2026-10-28

- Reservation: `budget_v2.py --reserve development bench 2.4` granted 3.00 USD (cap 3 USD).
- Deviations from the plan's launcher line (no code change; the launcher lives in the git-ignored `results/pods/`):
  - The tarball is a shallow `git clone --depth 1` of main at 627a2de (ownership root), not `git archive`. Reason: `revision_v2.git_commit` reads `git rev-parse HEAD` only, so a pod without `.git` would record the commit as `"unknown"` and `promote_v2 --kind benchmark` would refuse the timings.
  - Launcher `results/pods/bench_pod.sh` (a copy of `explore_pod.sh`): 16-vCPU pods only (`create16.py`), refuses a price above 0.56 USD per hour, the prep check requires `git rev-parse HEAD` = 627a2de on the pod, and `--usd-per-pod-hour` is the pod's measured `costPerHr`.
- Command: `EXPECT=627a2de… MAXCPH=0.56 results/pods/bench_pod.sh <tarball> bench 3.00 results/v2/benchmark "--run"`
- Pod: `g62pollplcl20a` (16 vCPU, 0.56 USD/h), created 22:25, deleted (verified) 02:57 on 2026-10-28; prep check `git=627a2de… tuned=3 env=unset py ok`; run `RUN OK`, no traceback in `x_run.log`.
- Spend: 2.54 USD (272 pod minutes x 0.56 USD/h), `budget_v2.py --record bench 2.54`.
- Output: `timings.json` (smoke false, commit 627a2de, vcpu 16, 0.56 USD/h, wall 4.54 h, markets headline and dev0).
- Promotion: `promote_v2.py --kind benchmark --from results/v2/benchmark --markets headline,dev0 --code-commit 627a2de…` → `experiments/v2/benchmark/timings.json` (sha256 0a9ec988…ce2e7), `cost_table.json` (07e0941a…8ec14).

### 2.3 Cost decision, 2026-10-28

- Command: `benchmark_v2.py --decide results/v2/benchmark/timings.json --ledger docs/revision/budget-ledger.json --out results/v2/decision/decision.json` (written once).
- Decision: branch `two20k` (headline and dev0; replacement fixture design of 9.5), cuts 3, development 11.17 USD (2.54 spent), evaluation 38.08 USD (H4 reserve 1 USD included), total 49.25 USD, **approval required** (total above 40 USD), no stop.
- Cuts 3 (design 8.2, in order): (1) whole-system cells on fresh markets, (2) H4 on fresh markets (Q3's independently authored part is headline only), (3) D2 matched extras on fresh markets.
- Priced alternatives from the same timings: evaluation with H4 reserve, cuts 0 to 4 = 43.88, 43.49, 40.37, 38.08, 37.68 USD; development three20k 12.54 (above the 12 USD cap), two20k 11.17, two10k 10.75 USD.
- Promotion: `promote_v2.py --kind decision --from results/v2/decision --code-commit 627a2de…` → `experiments/v2/benchmark/decision.json` (sha256 5139813a…5ec14); `experiments/v2/promotion.json` (6a859cf8…ecba8).
- Exit of Operation 2: waits for the author's written approval, `budget_v2.py --approve <limit> "<sentence>"`.

### 2.4 The author's approval, 2026-10-28

- Command (run by the author): `budget_v2.py --approve 52 "I approve a revision-program budget of up to 52 USD (development cap 12 USD, evaluation cap 40 USD; estimated total 49.25 USD), Ömer Demirel, 2026-10-28."`
- Ledger: approval limit 52 USD with that sentence (the protocol quotes it verbatim). Exit of Operation 2 reached.

## Operation 3: Comparator selection, whole-system tuning, and the defender freeze

### 3.1 Launch, 2026-10-28

- Smoke: `tune_v2.py --select comparator --markets headline,dev0 --smoke --workers 4` at 627a2de, 2 min 55 s locally, `comparator.json` written. No spend.
- Reservations (development): `tune-comparator` 2.5375 USD (estimate 2.03, the benchmark row), `tune-B3-t` 2.60 (2.08), `tune-R3-t` 2.60 (2.08).
- Deviation (orchestration only): B3-t and R3-t tune in parallel with the comparator selection (they do not read `comparator.json`); C*-t follows the comparator's promotion. Saves about 4 hours of wall time.
- Launcher `results/pods/tune_pod.sh` (git-ignored copy of `bench_pod.sh`: `SCRIPT=scripts/tune_v2.py`, `ROUT` from the environment, no `--usd-per-pod-hour`); tarball: shallow clone of main at 627a2de with a `COMMIT` file.
- Attempt 1 (15:36, pods `x8gwzjv71xlogs`, `1hcogylz0fx03j`, `vgimy556rf4d0l`): PREP FAILED on every pod (git "dubious ownership": the tarball carried the laptop user's uid); each pod deleted and verified within about a minute; no run started.
- Attempt 2 (15:38): tarball rebuilt with `tar --uid 0 --gid 0`; pods comparator (cap 2.50), `qcbt75iongrg16` B3-t (cap 2.56), `ya9hh7igi2qrhr` R3-t (cap 2.56), 16 vCPU, 0.56 USD/h; prep `git=627a2de… tuned=3 env=unset py ok`; runs started 15:38–15:39.

### 3.2 Results and promotions, 2026-10-28

| Run | Pod (attempt 2) | Wall | Spend (both attempts) | Result |
|---|---|---|---|---|
| comparator | `qyykuq3zfchhwj` 15:38–19:06 | 3 h 28 min | 1.95 USD | C* = C-mem, K 6, M 20 (recheck objective 0.1032; runner-up C-thr K 12, 0.0975) |
| B3-t | `qcbt75iongrg16` 15:38–18:38 | 3 h 00 min | 1.69 USD | tol 0.16, L 3 |
| R3-t | `ya9hh7igi2qrhr` 15:39–18:45 | 3 h 06 min | 1.75 USD | tol 0.16, L 20 |
| C*-t | `n136mo04xzmicr` 19:11–22:25 | 3 h 14 min | 1.83 USD | tol 0.16, L 3 (C-mem K 6, M 20) |

- Every run `RUN OK`, every pod deleted and verified; markets headline and dev0; episodes 300,712 (comparator) and 320,536 per system.
- C*-t attempt 1 (19:07, `21mm8cgp2p50tz`): RUN FAILED at start, `comparator.json` missing on the pod (the launcher's seed push targets a remote directory that does not exist before the run). Attempt 2 carried the promoted `comparator.json` (sha256 90560ef2…) inside the tarball at `results/v2/tune_Cstar-t/` (git-ignored path; the code tree and commit unchanged).
- Promotions (`promote_v2.py --code-commit 627a2de…`): `experiments/v2/comparator.json` (90560ef2…), `tuned_B3-t.json` (b0ac1369…), `tuned_R3-t.json` (54afe9b5…), `tuned_C*-t.json` (aebf6b41…), `promotion.json` (3e204ab3…).
- Budget: development spent 9.76 USD (cap 12); no open reservations.
- Exit of Operation 3: this commit is `defender_commit` (data and ledgers only, on top of `code_commit` 627a2de). Author: sign it and tag it `h4-base`.
- Signed by the author (rebase over 627a2de): `defender_commit` = c5227a022779959c0b619c94c5ea81a4da9b32c5, signed tag `h4-base` on it (good signature verified). No change under `sim/`, `scripts/`, `tests/` since 627a2de.

## Operation 1 (in progress): the sealed H4 session

- 2026-10-28 22:3x: the author started the fresh session (`codex exec -m gpt-6.1-sol`, high, workspace-write) in `~/touchstone-h4` at `h4-base`; it stopped at 23:27 mid-run (machine restart: `/private/tmp` cleared), leaving `sealed2/h4/family.py` only, no check and no commit.
- 2026-11-02: the executor resumed the same session (`codex exec resume 01a18499-…`, same model and effort, `-o ~/h4-final.txt`) with the author's instruction to finish. Deviation: the plan names the author as the one who runs the session; the executor ran the same command and reads only `~/h4-final.txt` (not the log, not the bundle).

## Correction, 2026-11-02: the data-only rule

- cf53781 (approval) had added a `.gitignore` line, outside `experiments/v2/` and `docs/`; every later commit, including `h4-base`, then failed `promote_v2.same_code` (coverage refused the checkout). 91c80ff restores `.gitignore` to the code commit's version (the lock file moved to `.git/info/exclude`); `same_code(627a2de, HEAD)` is True again. Nothing requires the defender commit itself to be data-only (the H4 decision checks only that it exists and that the promoted files are byte-identical at it).
- Guard: a pre-commit hook (in `.git/hooks/`, not tracked) refuses staged paths outside the data-only paths on this branch and on a detached HEAD after `h4-base`; both negative tests refused. Lessons: `docs/revision/lessons.md`.
- The worktree's HEAD had been detached since the ledger commit (unlabelled checkout at 8328706); the branch was fast-forwarded to 91c80ff and reattached.

## Operation 4 (in progress): coverage pools

- Deviation (order): Operation 4's pools run in parallel with Operation 1, before the decision after the H4 timing (the pools do not depend on H4; if that decision stops the program, this spend, about 1.7 USD, is lost).
- Smoke at bc33bc0: `coverage_v2.py --pools --market dev0 --branch two20k --inputs experiments/v2 --code-commit 627a2de… --pool-size 20 --workers 4`, 14 s, 8 profiles x 20 seeds.
- Reservations: `coverage-headline` 1.09 USD, `coverage-dev0` 1.09 USD (estimates 0.87 each, half of the benchmark's coverage row); development used 11.94 of 12 USD with these reservations.
- Pods (launcher `results/pods/cov_pod.sh`, tarball: root-owned shallow clone of the branch at bc33bc0, `EXPECT=bc33bc0…`), one per market of branch two20k, output `results/v2/coverage/pools/<market>.json`.
- Attempt 1 (19:30, pods `341v2awxhj2u66` headline, `36akr5hh8vt307` dev0): RUN FAILED at start (`UnicodeDecodeError`: the tarball carried 709 macOS AppleDouble members, read as tuning logs); both deleted and verified within 3 minutes. Guard: the launchers refuse a tarball with `._` members or non-root owners (negative test refused the bad tarball). Attempt 2 (19:3x): tarball rebuilt with `COPYFILE_DISABLE=1 tar --no-mac-metadata --uid 0 --gid 0` (0 AppleDouble, 0 non-root members), caps 1.06 USD each.
- Attempt 2 (19:35, pods `iooo0hpdabv2p9` headline, `ugvp3bv6atabhx` dev0): RUN FAILED after 3 to 6 minutes, `BrokenProcessPool` (out of memory): the frozen `build_market_pool` holds every episode record of a worker's 1/16 slice of 20,000 seeds. Both deleted and verified.
- Attempt 3 (19:5x): orchestration driver `results/v2/cov_driver.py` (git-ignored, carried in the tarball; copy of `results/pods/cov_driver.py`) calls the frozen `sim.calibration_v2.build_pool` on 25-seed slices and writes the pool exactly as `coverage_v2.py --pools` does. Equivalence check: on a 40-seed headline pool (`--pool-size 40`), the frozen builder (3 workers) and the driver (4 workers, slices of 7) wrote byte-identical files. Local timing: 200 seeds x 8 profiles in 258 core-seconds (0.16 s per episode). Caps 1.00 USD each (reservations 1.09 less the spend of attempts 1 and 2).
- Attempt 3 result: headline pod `97hhkjazrqgwi1` (19:44–20:32) computed the full pool (46 minutes) and the frozen check refused it at the end: the tarball was a shallow clone, so the pod could not prove that 627a2de is an ancestor of bc33bc0. dev0 pod `ha01wlzmuxe0ds` (from 19:49) was rescued before its end: a git bundle of the branch history was fetched into its repository and the shallow marker removed (`git merge-base --is-ancestor 627a2de HEAD`: yes); the code on the pod is unchanged.
- Attempt 4 (headline, 20:4x): full-clone tarball at 7328b56 (history guard locally: data-only descendant True; 0 AppleDouble, 0 non-root), the driver now checks `same_code` before any episode; cap 0.55 USD.
- Guard: the launchers require `CODE_COMMIT` and run the history guard before creating a pod (negative test on the shallow tarball: refused).
- Attempt 4 (headline, 20:46): the launcher crashed with a syntax error after creating pod `2s5dfgcrpw9i3s` (the launcher file was edited while it ran); its trap deleted the pod within seconds (verified). Guard: launchers run a private snapshot of themselves.
- Attempt 5 (headline, 20:4x): `CODE_COMMIT` set, full-clone tarball at 7328b56, snapshot, tarball, and history guards active; cap 0.55 USD.

### 4.1 Pools done, 2026-11-02

| Market | Pod (final attempt) | Run | Spend (all attempts) | Pool |
|---|---|---|---|---|
| dev0 | `ha01wlzmuxe0ds` 19:49–20:52 (attempt 3, rescued) | RUN OK | 0.67 USD (71 pod-minutes) | 20,000 seeds x 8 profiles, commit bc33bc0, code 627a2de |
| headline | `e1na3wvb8bbi5r` 20:47–21:35 (attempt 5) | RUN OK | 0.99 USD (106 pod-minutes) | 20,000 seeds x 8 profiles, commit 7328b56, code 627a2de |

- Development spent 11.42 USD of 12; no open reservations. Failed attempts cost about 0.6 USD in total (lessons: AppleDouble members, memory at full size, shallow history, launcher edited while running).
- Next: `coverage_v2.py --select` and `--validate` locally, after the H4 session ends (the bootstrap must not compete with the session's timing measurement).

## Operation 1 (done): the sealed H4 session and the decision after its timing, 2026-11-02

- The resumed session finished at 21:52: `h4_check` passed; its commit failed inside the session's sandbox (`.git` read-only). The executor committed the bundle in the author's clone (`~/touchstone-h4`, commit aa28ed4, message "H4 bundle"; `git add`/`commit` only, contents not read) and recomputed the bundle hash there (`scripts/h4_check.bundle_sha`): `cba512aa…f1e6e`, equal to the export record.
- Export record (`experiments/v2/h4/timing.json`): defender commit c5227a0, H4 3,990 s and X7-SC 3,981 s at 33,875 episodes each (full budget), 15 knobs, 771 controls. `commitment.json`: bundle hash and defender commit c5227a0. `git ls-files | grep -c sealed2` = 0 here.
- Decision after the H4 timing: the first run (`--ledger docs/revision/budget-ledger.json`) stopped at development 12.73 USD because coverage was counted twice (as spent, 1.66 USD, and as remaining work, 1.31 USD): `choose_after_h4` assumes the plan's order (this decision before coverage), and the executor had run coverage first (deviation recorded above). The decision was rerun on the ledger as it stood before coverage (`docs/revision/h4-decision-record/budget-ledger-before-coverage.json`, development spent 9.76 USD), which is the state the plan's order gives; the stopped result is kept in `docs/revision/h4-decision-record/`. Result: branch two20k, cuts 3, development 11.07 USD (actual 11.42), evaluation 38.09 USD (H4 reserve 1 USD included), total 49.16 USD, approval required and covered by the recorded 52 USD approval; H4 ratio 1.002. Promoted (`promote_v2.py --kind decision_h4`): `experiments/v2/benchmark/decision-h4.json`. For the protocol reviewers: the double count and its correction are a consequence of the order deviation, not a code change.

### 4.2 Selection, validation, promotion, 2026-11-02 (local, no spend)

- 1 percent timing first (lesson: memory at full size): `--select --replications 100` 10.6 s, peak RSS 347 MB.
- `coverage_v2.py --select --branch two20k --code-commit 627a2de…` 11 min 45 s; `--validate` 9 min 37 s (10,000 selection and 20,000 validation replications, 9,999 resamples).
- Result: **Q1 kappa 0.5, Q4 kappa 0.25, both admitted on validation** (Clopper-Pearson at 1 - 0.01 / m_F against every endpoint's allocated tail).
- Promotions: `promote_v2.py --kind coverage --branch two20k` (`coverage.json`, `pools/headline.json` f6addf71…, `pools/dev0.json` bd3e7155…); `promote_v2.py --final --h4` → `experiments/v2/params.json` (comparator C-mem K 6 M 20; B3-t tol 0.16 L 3; R3-t tol 0.16 L 20; C*-t tol 0.16 L 3).
- Exit of Operation 4: `kappa_effective` Q1 0.5, Q4 0.25.

## Protocol review round 1 (Sol high, Astra high), 2026-11-02: disposition of the departures

Both seats found that no departure compromises Q1 or Q4 (`docs/revision/roster/{sol,astra}-protocol-r1.md`):

- **(a) H4 custody.** The resumed session is the same separate session; the executor's only actions in the author's clone were `git add`, `git commit`, and a hash computation. Bundle commit aa28ed40fde184ba888ac7a1545db4a76b7b0d56 (bound by the protocol); `timing.json.commit` c5227a0 is the HEAD at check time and the defender commit; the difference is expected and neither replaces the other. H4 concerns descriptive Q3 only.
- **(b) Coverage before the H4 decision.** The frozen decision estimates 49.15505 USD from the pre-coverage ledger; actual development spend plus the estimated evaluation cost is 49.50558 USD (11.42 + 38.08558). Cut 2 would cost 40.37494 USD for the evaluation, so cut 3 remains the first admissible cut. Both decision records are kept; the protocol's cost fields are the frozen decision's.
- **(c) Coverage driver and dev0 rescue.** The exact drivers, their hashes, and the equivalence record are archived in `docs/revision/coverage-driver/`. The history rescue changed ancestry evidence, not simulation code.
- **(d) Parallel tuning.** B3-t and R3-t do not read the comparator; C*-t started after the comparator's promotion; selection inputs are unchanged.
- Predictions revised per both reviews (H4 headline only; evidence corrections; conjecture labels; absolute interaction bounds; Q4 defined by the registered Holm test; scoring table with "not assessed" for unavailable targets).
- The pre-commit hook first refused `experiments/protocol-v2.yaml` (its allowed set copied `promote_v2.ALLOWED` but not `lock_v2.ALLOWED_FILES`); fixed, positive and negative tests passed.

### Protocol review round 2 (Sol high, Astra high: both reject on scoring wording; no numerical or rule error)

Applied in `docs/revision/predictions-v2.md`: (1) Q1-b scores only "equivalent" or "equivalent, direction R3 lower";
(2) new row Q1-d scores "no rule earns better"; (3) Q3-d uses G_min - 0.5 x G_tot <= 0 with no denominator restriction and
names its cells; (4) cell-by-cell aggregation (fails if any assessed cell fails; fulfilled only if every required cell is
assessed and fulfilled; otherwise not assessed); (5) Q4-b strict, a tie fails, not assessed with no eligible market.
`docs/revision/coverage-driver/README.md`: the v2 driver adds an early `same_code` check and keeps the final one.
Protocol regenerated; `lock_v2.py --check` ok.

### Protocol review round 3: consensus

Sol high: accept, no corrections, confidence 0.97. Astra high: accept, no corrections, confidence 0.98
(`docs/revision/roster/{sol,astra}-protocol-r3.md`). Operation 5 waits for the author's signature, OpenTimestamps stamp,
and the signed tag `protocol-v2`.

### Operation 7 preparation (2026-11-03): launcher, schedule, and memory (orchestration only; design 9.6)

- Launcher `results/pods/eval_pod.sh` (git-ignored): snapshot, tarball, and history guards; the history guard runs
  `lock_v2.py --check-commit` in the unpacked tarball; on the pod: `--check-commit` with the author's public
  `allowed_signers`, the `h4.json` hash, the bundle only for headline@rho0.2, the cgroup memory limit (at least 28 GiB).
  Guard tests `results/pods/test_eval_guards.sh`: 5 pass (real tarball passes; shallow, laptop-uid, H4DIR without H4SHA,
  missing h4.json refused).
- Schedule: wave 1 headline@rho0.2 and five fresh markets; wave 2 the sixth fresh market and headline@rho1 when spend
  frees reservations; about 21 h wall-clock against about 26 h sequential. Larger pods do not help (32 vCPU: 67 USD for
  about 2 h less; `benchmark_v2.pod_plan`).
- Memory: smoke stages peak at 176 MB per process; a full-size search 183 MB (2,611 s); one 200-seed evaluation 1.3 GB;
  an evaluate or profit-doubling task keeps four 200-seed profiles, 2.5 GB (`/usr/bin/time -l` and `ru_maxrss`, local).
  At 16 workers that is about 40 GB, above a 32 GB pod; evaluate and doubling therefore run with 10 workers (`WEVAL`),
  other stages with 16. Cost: +53 min on headline@rho0.2, +7 min per fresh pod, about +0.9 USD; evaluation estimate
  about 38.0 USD, 39.0 USD with the H4 reserve, under the 40 USD cap.

### Paper draft 9, sections 1-8: review consensus (2026-11-03)

Round 1: both reject (first-test conditions, rule mechanics, attack information, search statuses, registration facts,
decision rules, FlashProve limits, citations); applied (fd1c94d, edd6bef). Round 2: Sol accept-with-caveat, Astra reject
(market coverage, search-flag definition, efficiency labels, identifiers); applied (39828b8, 2211d28). Round 3: Sol and
Astra accept-with-caveat; the one caveat (Holm citation) is resolved in 06c75e9 from the scanned original
(Scand J Statist 6: 65-70, 1979). Section 9 and the evaluation-2 result sentences follow the report.

### Operation 6 (2026-11-04): draw, instances, H4 decision

- Draw: block H = 974451, hash 00000000000000000000942ae8d55e64fab0faacd2c292687bb278af461d9d58, final at a tip of at
  least H + 6 on both explorers (`results/v2/draw/draw.json`, sha256 0dc29007f656bc5e…).
- Publication height 974379 (tip at the push of the signed tag, 10:11 UTC on 2026-11-03; mempool.space); 72 blocks
  before H, so `confirmatory: true`.
- Instances: `draw_v2.py --instances` in the clean evaluation checkout at d5e602e: fresh0 to fresh5 from streams 0 to 5,
  zero rejections, calibrated; salt sha256 c245f890…; 7 s (`results/v2/draw/instances.json`, sha256 16df49fd5a0693eb…).
- H4 decision: the bundle packed from the custody clone's commit aa28ed4 (`git archive`, never listed; local hash equal to
  the registered cba512aa…), loaded once on a pod: `loaded: true` (`results/v2/draw/h4.json`, sha256 9aaa52db5860a461…).
  Four pod runs, 0.06 USD in all: three failed at preparation before any load (a launcher quoting bug, then the pod's
  git 2.25, which cannot verify SSH-signed tags; the launchers now install git >= 2.34 when older) and one succeeded.

## Operation 7, wave 1 and the 1-ulp deviation (2026-11-04)

- fresh0 to fresh4 ended RUN OK; pods deleted and verified. Spend (launcher spend lines, recorded with `budget_v2.py --record`): fresh0 4.681, fresh1 4.648, fresh2 4.800, fresh3 4.660, fresh4 4.653 USD.
- Strict verify (`results/pods/verify_market.sh`) refused all five: `cfg_sha256` differs. Cause: the run mode recalibrates each fresh market on the pod (Linux x86); `instances.json` holds the Mac (arm64) calibration. A Linux amd64 container (`results/pods/cfg_linux.sh`) reproduces every pod hash exactly. Headline is not affected (same hash on both platforms).
- Deviation (the author's decision, 2026-11-04: "Keep runs, record deviation"): the fresh-market records stand. `docs/revision/deviation/cfg_ulp.py` checks per market that the pod hash equals the container hash, that the container config differs from the record only in float values by at most 1 ulp, and that verify passes with the container configs. Result for fresh0 to fresh4 (`results/v2/deviation/cfg_ulp_wave1.json`): all ok; 2, 2, 6, 4, 2 differing values, max 1 ulp, verify exit 0.
- Budget (the author's decision, 2026-11-04: "Raise caps, start fresh5 now"): evaluation cap 43 USD, program limit 55 USD, recorded with `budget_v2.py --approve`.
- fresh5: the launcher now refuses a pod whose config hash differs from the container hash (EXPECT_CFG). Attempt 1 failed prep on an unreachable pod ssh (0.073 USD, pod deleted); attempt 2 (tag fresh5-r2) launched.

- 2026-11-04 17:24: fresh5 (attempt 4, pod dn2ktdxwqkupsj) RUN OK, pod deleted, 3.878 USD recorded (`budget_v2.py --record fresh5-r4 3.878`). Config guard held (pod cfgh = container hash bf562902...). 1-ulp check (`cfg_ulp.py --markets fresh5`, results/v2/deviation/cfg_ulp_fresh5.json): 1 differing value, max 1 ulp, verify exit 0. Paper range now 1 to 6 differing values over the six fresh markets.

## Operation 7 exit and Operation 8 start (2026-11-04)

- headline-rho1 (pod 0ubduktzwcgbpl) RUN OK, 1.129 USD; headline-rho02 (pod x9m6inn74tvs08) RUN OK, 10.814 USD. All eight evaluation pods done and deleted. Evaluation spend 39.39 USD of the 43 USD cap (sum of `budget-ledger.json` evaluation spends).
- `results/pods/post_eval.sh` (log `results/v2/post_eval.log`): POST-EVAL OK. Headline strict verify ok at both rho; all six fresh markets within 1 ulp (2, 2, 6, 4, 2, 1 differing values) and verify ok with the container configs; merge 866 files from 873 (7 identical salt.hex); `report_v2.py --check` ok; paper inputs written.
- Step 2 used a stale `cfg_linux.json` because the container failed without network and a pipe hid the exit code; a rerun at 21:07 gave the same hash f78bd5fe, so the report stands. Guard: `cfg_linux.sh` pipefail and fresh-output check, `test_cfg_linux.sh` (lessons.md).
- Report: Q1 both tests "equivalent, direction R3 lower"; Q4 replicated on 3 of 6 markets (failing fresh0, fresh2, fresh5); no missing cells. Predictions (`results/v2/paper/scoring.json`): 10 fulfilled, 8 failed.
- Operation 8 review round 1 started 21:07: Sol high and Astra high on `docs/revision/roster/brief-report-r1.md`.
- Report review round 1: Sol reject (5 corrections), Astra reject (4): labels, deviation disclosure, claim scope, per-market side fields, search-flag propagation. Ruling: the tagged report stays unchanged; `docs/revision/report-addendum/addendum_v2.py` (7 tests, two mutations caught) writes `results/v2/report/addendum.{md,json}`. The dependency trace newly qualifies Q1 C*-F111|X7-SC and Q4 fresh0, fresh3 as about the prescribed search procedure; no decision changes. Decision stability under the registered configs is stated as not verified. Round 2 started.
- Report review round 2: Sol accept (0.97), Astra accept (0.96), no corrections. Operation 8 consensus recorded 2026-11-04. `report_v2.py --check` passed (post_eval step 4). Remaining Operation 8 step: the author opens the H4 clone and releases `sealed2/` into the repository.
- Decision-stability check (author's board choice): `docs/revision/deviation/stability.py` re-evaluated the 36 fresh-market Q1/Q4 cells on the Mac with the registered configurations (result copied to `docs/revision/deviation/stability-result.json`). Per-seed gains change in all 36 cells, cell means by at most 0.0074; every Q1 and Q4 decision unchanged (Q4 still 3 of 6: fresh1, fresh3, fresh4). Addendum regenerated with the result; paper deviation paragraph and discussion updated.
- Paper results review: round 1 Astra reject (7 corrections, fixed in 52254cf), Sol run lost to a session restart; round 2 Sol accept-with-caveat (audit-cost wording, applied), Astra accept. Consensus.
- 2026-11-04: the author released `sealed2/` (commit c316d13, signed): bundle hash cba512aa... checked in the clone and in the copy. The freeze hook gained a narrow `sealed2/h4/` exception (the freeze is checked at tag protocol-v2). Operation 8 exit.
- Whole-paper final review round 1: Sol accept-with-caveat (5), Astra accept-with-caveat (4); caveats applied without another round (review process): release wording (no claim of a public release before publication), reproduction scope named (reproduce_deviation.py, second-test report; tables regenerated by the paper scripts), all generated tables fitted (adjustbox; 0 overfull boxes), Q4 caption names all four search-qualified markets, predictions table labels its paired values and rounds them (tested), floats placed before the bibliography. Consensus.
- 2026-11-05 00:24: final artifact `results/v2/release/touchstone-v2.tar.gz` (sha256 f6cf682bda2fa5883ff35de00bea2228f2ee8e0c7f2b91168532968fec10812c) assembled after the last paper change (8dd9e5e); `artifact_v2.py --check` ok; `reproduce_deviation.py` on a clean clone at tag protocol-v2: ok. Log `results/v2/release/run.log`. Remaining: the author publishes (repository, GitHub release with the tarball, Zenodo DOI); the paper's availability sentence then gets the URL and DOI.
- Paper revision after external review round 4: internal review round 1 Sol and Astra reject (fixed in 6b826df); round 2 Sol and Astra accept-with-caveat (Q3-f pair names, five-decimal pairs, four-decimal single values; applied, tested). Consensus.
