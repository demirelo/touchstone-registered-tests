"""The spec 5.3 gate: time every cell stage of sweep.py (search, bank, reference, evaluate, checks) for the
headline median D1, D2, and H3 cells of each baseline at the smoke budget, and extrapolate the pre-lock
manifest. All-deviators is left out so the benchmark mix matches the manifest mix (it is 4% of the manifest
and would be half of the benchmark). Exits 1 above 20 core-hours."""
from __future__ import annotations

import argparse, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.bench import cpu_model
from scripts.sweep import run_stages
from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked, seeds
from sim.manifest import enumerate_manifest, totals

GATE_HOURS = 20.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()
    lk = load_locked(); base = market_config_from_locked(lk)
    with tempfile.TemporaryDirectory() as tmp:
        calp = Path(tmp) / "cal.json"; save_calibration(calibrate(base, seeds(lk, "calibration")[:2]), calp)
        per_rule = {}
        for r in args.rules.split(","):
            t0 = time.perf_counter()
            counted = run_stages({"stage": "all", "sections": "development,h3", "rules": r, "calibration": str(calp), "tuned_dir": None,
                                  "smoke": True, "workers": args.workers, "select": f"beta{lk['beta_headline']}_rho{lk['rho']['default']}_median",
                                  "limit": None, "out": str(Path(tmp) / r)})
            per_rule[r] = (sum(counted.values()), time.perf_counter() - t0)
    runs = sum(n for n, _ in per_rule.values()); secs = sum(s for _, s in per_rule.values())
    ms = 1000.0 * secs / runs
    pre = totals(enumerate_manifest(lk, args.rules.split(",")))["pre_lock"]
    hours = pre * ms / 3.6e6
    for r, (n, s) in per_rule.items():
        print(f"{r}: {n} runs in {s:.1f} s = {1000.0 * s / n:.1f} ms/run")
    print(f"full staged path: {runs} runs in {secs:.1f} s = {ms:.1f} ms/run on {cpu_model()}; pre-lock manifest {pre:,} runs = {hours:.1f} core-hours (gate {GATE_HOURS})")
    sys.exit(0 if hours <= GATE_HOURS else 1)


if __name__ == "__main__":
    main()
