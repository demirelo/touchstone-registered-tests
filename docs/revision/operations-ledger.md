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
