"""The spec 5.3 gate: time every cell stage of sweep.py (search, bank, reference, evaluate, checks) for the
headline median D1, D2, and H3 cell of each baseline at the smoke budget, one cell per call so that each
(rule, family) gets its own ms-per-run figure, and extrapolate the pre-lock manifest with each figure weighted
by that (rule, family)'s share of the manifest (`manifest_weights`). All-deviators is left out so the benchmark
mix matches the manifest mix (it is 4% of the manifest and would be half of the benchmark). The blended
figure (total seconds over total runs) is printed next to the weighted one; the gate is the weighted figure.
Exits 1 above 20 core-hours."""
from __future__ import annotations

import argparse, sys, tempfile, time, warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bench import cpu_model
from scripts.sweep import run_stages
from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked, seeds
from sim.manifest import enumerate_manifest, manifest_weights, totals

GATE_HOURS = 20.0
FAMILIES_AND_SECTIONS = (("D1", "development"), ("D2", "development"), ("D2+H3", "h3"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    lk = load_locked(); base = market_config_from_locked(lk)
    rules = args.rules.split(",")
    tag = f"beta{lk['beta_headline']}_rho{lk['rho']['default']}_median"
    timings: dict[tuple[str, str], tuple[int, float]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        calp = Path(tmp) / "cal.json"; save_calibration(calibrate(base, seeds(lk, "calibration")[:2]), calp)
        for r in rules:
            for fam, section in FAMILIES_AND_SECTIONS:
                t0 = time.perf_counter()
                counted = run_stages({"stage": "all", "sections": section, "rules": r, "calibration": str(calp), "tuned_dir": None,
                                      "smoke": True, "workers": args.workers, "select": f"{r}_{fam}_{tag}", "limit": None,
                                      "out": str(Path(tmp) / r / fam.replace("+", "_"))})
                timings[(r, fam)] = (sum(counted.values()), time.perf_counter() - t0)
    cells = enumerate_manifest(lk, rules)
    weights = manifest_weights(cells)
    pre = totals(cells)["pre_lock"]
    runs = sum(n for n, _ in timings.values()); secs = sum(s for _, s in timings.values())
    blended = 1000.0 * secs / runs
    weighted = sum(weights[k] * 1000.0 * s / n for k, (n, s) in timings.items()) / sum(weights[k] for k in timings)
    for (r, fam), (n, s) in timings.items():
        print(f"{r} {fam:6s}: {n:5d} runs in {s:6.1f} s = {1000.0 * s / n:6.1f} ms/run  (manifest share {weights[(r, fam)] / pre:5.1%})")
    print(f"full staged path on {cpu_model()}: blended {blended:.1f} ms/run; manifest-weighted {weighted:.1f} ms/run; "
          f"pre-lock manifest {pre:,} runs = {pre * weighted / 3.6e6:.1f} core-hours weighted "
          f"({pre * blended / 3.6e6:.1f} blended), gate {GATE_HOURS}")
    sys.exit(0 if pre * weighted / 3.6e6 <= GATE_HOURS else 1)


if __name__ == "__main__":
    main()
