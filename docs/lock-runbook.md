# Lock run book

## Compute notes

The simulator is branchy single-thread Python: a GPU does not help, core count does. Set `OMP_NUM_THREADS=1` before any multi-worker run. The search manifest splits across machines with `scripts/sweep.py --stage search --shard K/N` (copy the shards' `search/` directories together before the later stages). The coverage study splits with `scripts/coverage_study.py --cell i --workers 16` (six machines, one cell each; one cell's chunks spread over the pod's cores; measure the per-cell time on the smoke run before estimating), followed by `--merge` on one machine. `scripts/pod_setup.sh` prepares a fresh CPU pod.

## Lock day (2026-10-28), in order

```bash
export OMP_NUM_THREADS=1
uv run python scripts/calibrate.py --out experiments/calibration.json
uv run python scripts/calibrate.py --T 100 --out experiments/calibration_T100.json
uv run python scripts/tune_baselines.py --calibration experiments/calibration.json --rule B1 --out experiments/tuned/tuned_B1.json
uv run python scripts/tune_baselines.py --calibration experiments/calibration.json --rule B2 --out experiments/tuned/tuned_B2.json
uv run python scripts/tune_baselines.py --calibration experiments/calibration.json --rule B3 --out experiments/tuned/tuned_B3.json
uv run python scripts/sweep.py --stage all --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/coverage_study.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --register --workers 8
uv run python scripts/h1.py --backend fake-cheat --rules B1,B2,B3 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/h1_fake
uv run python scripts/h1.py --backend anthropic --rules B2 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_anthropic --pilot
uv run python scripts/h1.py --backend jev --rules B2 --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --out results/pilot_jev --pilot
cp results/coverage/coverage_report.json experiments/coverage_report.json
cp results/coverage/coverage_cells.json experiments/coverage_cells.json
cp results/pilot_anthropic/pilot_anthropic.json experiments/pilot_anthropic.json
uv run python scripts/lock.py --tuned-dir experiments/tuned --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --coverage-report experiments/coverage_report.json --bundle-hash <from the custodian> --salt-hash <from the custodian> --pilot experiments/pilot_anthropic.json
uv run python scripts/lock.py --tuned-dir experiments/tuned --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --coverage-report experiments/coverage_report.json --pilot experiments/pilot_anthropic.json --check
git add experiments/locked.yaml experiments/tuned experiments/calibration.json experiments/calibration_T100.json experiments/coverage_report.json experiments/coverage_cells.json experiments/pilot_anthropic.json
git commit -S -m "lock: 2026-10-28"
uv run python scripts/check_claim.py --verify-only --verify-lock HEAD --coverage-report experiments/coverage_report.json --proposed none
git tag -s lock-2026-10-28 -m "Touchstone lock 2026-10-28" && git push origin main lock-2026-10-28
```

The lock commit carries `locked.yaml`, the tuned files, both calibrations, the coverage report and selection, and the pilot (spec 6 lists the coverage report as lock-commit content); the verify-only check runs against the committed tree (`HEAD`), after the commit and before the signed tag, so a lightweight tag is never needed (this machine signs every tag). Then post the tag hash to the public timestamp (OSF or AsPredicted) the same day. The coverage study's base entry is about 2.85 million episodes (about a day on 8 cores, or under an hour on six 16-vCPU pods with `--cell`); the conditional n = 40 run starts by itself only when the remedy order reaches it.

## Pods

The tuned files, the calibrations, and the sweep outputs are untracked, so every pod gets them by copy (`rsync` over SSH or `runpodctl send`/`receive`); `<pod>` stands for the pod's SSH address.

```bash
# on each fresh pod: clone the branch being run (HTTPS, no key needed for a public or token-authorized repo), install, and set the thread variable
curl -fsSL https://raw.githubusercontent.com/demirelo/touchstone/plan-2b/scripts/pod_setup.sh | bash -s -- https://github.com/demirelo/touchstone.git plan-2b
# from the author's machine: the tuned files and calibrations to every pod
rsync -a experiments/tuned experiments/calibration.json experiments/calibration_T100.json <pod>:touchstone/experiments/
# search shards (N pods), then collect the shards' search/ directories into one results/sweep on the author's machine
ssh <pod> 'cd touchstone && OMP_NUM_THREADS=1 uv run python scripts/sweep.py --stage search --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 16 --shard K/N --out results/sweep'
rsync -a <pod>:touchstone/results/sweep/search/ results/sweep/search/
# the later stages once, on the author's machine (or one pod with the merged search/ directory)
uv run python scripts/sweep.py --stage bank --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/sweep.py --stage reference --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/sweep.py --stage evaluate --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
uv run python scripts/sweep.py --stage checks --rules B1,B2,B3 --calibration experiments/calibration.json --tuned-dir experiments/tuned --workers 8 --out results/sweep
# coverage cells (six pods): every pod needs the merged results/sweep (reference records and bank.json); then the cell files come back to one machine
rsync -a results/sweep <pod>:touchstone/results/
ssh <pod> 'cd touchstone && OMP_NUM_THREADS=1 uv run python scripts/coverage_study.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --cell i --workers 16'
rsync -a <pod>:touchstone/results/coverage/cell_i.json results/coverage/
uv run python scripts/coverage_study.py --sweep-out results/sweep --calibration experiments/calibration.json --tuned-dir experiments/tuned --out results/coverage --merge --register
```

## Freeze day (2026-11-11)

Rules for the proposed rule's module `sim/mechanisms/proposed.py`, enforced by `scripts/check_claim.py` (`check_proposed_module`): imports only `sim.mechanisms.base`, `numpy`, `scipy`, `math`, `dataclasses`, `typing`, `__future__`, `itertools`, `functools`, in absolute form; no `__import__`, `exec`, `eval`, `compile`, `globals`, `vars`; no `importlib`, `builtins`, or `sys` calls; no `getattr`, `setattr`, or `delattr` with a dunder or computed name; no `__builtins__`; no access to `__subclasses__`, `__globals__`, `__dict__`, `__base__`, `__bases__`, `__mro__`, `__class__`, `__code__`, `__closure__`, `__loader__`, or `__spec__`. Importing the module, and calling `make(params)`, must change no attribute of any `sim.*` module. Before the freeze tag:

```bash
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-28 --proposed proposed
git tag -s freeze-2026-11-11 -m "Touchstone evaluation freeze"
uv run python scripts/check_claim.py --verify-only --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11 --proposed proposed
```

## Evaluation (after the unseal, 2026-11-12)

```bash
export TOUCHSTONE_IDENTITY_SALT=$(cat sealed/identity_salt.hex)
uv run python scripts/sweep.py --stage all --sections heldout --rules B1,B2,B3,proposed --calibration experiments/calibration.json --tuned-dir experiments/tuned --eval-namespace final_eval --workers 8 --out results/final
uv run python scripts/h1.py --backend anthropic --rules B1,B2,B3,proposed --calibration experiments/calibration.json --calibration-t100 experiments/calibration_T100.json --tuned-dir experiments/tuned --eval-namespace final_eval --prompt sealed/h1_prompt.txt --out results/h1_final
uv run python scripts/check_claim.py --verify-lock lock-2026-10-28 --verify-freeze freeze-2026-11-11 --sweep-out results/final --h1-dir results/h1_final --calibration experiments/calibration.json --tuned-dir experiments/tuned --coverage-report results/coverage/coverage_report.json --proposed proposed --proposed-describe experiments/proposed_describe.yaml
uv run python scripts/plot.py --sweep-out results/final --out results/figures --coverage-report results/coverage/coverage_report.json --h1-dir results/h1_final
```

The test that `proposed.py` imports only the base module and mutates nothing runs inside `scripts/check_claim.py`, so no new test file is needed after the lock.
