# Coverage pool drivers (orchestration, Operation 4)

The frozen `scripts/coverage_v2.py --pools` (`build_market_pool`) holds every episode record of a worker's slice and ran out
of memory on 16-vCPU pods at 20,000 seeds. These drivers call the frozen `sim.calibration_v2.build_pool` on 25-seed slices
and write the pool exactly as `coverage_v2.py --pools` does. They are not repository code; they ran inside the pod tarballs
at `results/v2/cov_driver.py`.

| File | SHA-256 | Used for | Difference |
|---|---|---|---|
| `cov_driver.v1-dev0.py` | `2a8488d97a5c6cdc75051d27e9214113db7167efd0cd709ae876b2b4ab881644` | dev0 pool (pod `ha01wlzmuxe0ds`, tarball at bc33bc0) | checks `same_code` after the pool |
| `cov_driver.v2-headline.py` | `9a07d49a9a5ed3bb23cdd177159e6c4c66d7a7098e87936f2469d319f2c9ec03` | headline pool (pod `e1na3wvb8bbi5r`, tarball at 7328b56) | checks `same_code` before any episode |

## Equivalence check (2026-11-02, local, at bc33bc0)

```bash
uv run python scripts/coverage_v2.py --pools --market headline --branch two20k --inputs experiments/v2 --code-commit 627a2de9ad6c838e4228893c3107d173118d5d62 --pool-size 40 --workers 3 --out eqA
uv run python results/pods/cov_driver.py --market headline --branch two20k --inputs experiments/v2 --code-commit 627a2de9ad6c838e4228893c3107d173118d5d62 --pool-size 40 --workers 4 --chunk 7 --out eqB
cmp eqA/pools/headline.json eqB/pools/headline.json
```

Result: both exit 0; `cmp` reports no difference (byte-identical pool files). The driver used was v1; v2 adds a `same_code` check
before pool construction (three lines at the start of `build`) and keeps the final check. The promoted pools have 20,000 ordered seeds each and pass
`promote_v2.py --kind coverage`.

## dev0 history rescue

The dev0 pod's tarball was a shallow clone; before the run ended, a git bundle of the branch history was fetched into the
pod's repository and `.git/shallow` removed, so the frozen check could prove that 627a2de is an ancestor of bc33bc0. The
simulation code on the pod did not change.
