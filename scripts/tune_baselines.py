from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import cell_config, load_calibration
from sim.cell import SeedCache
from sim.locked import load_locked, market_config_from_locked, seeds, settings_hash
from sim.tuning import tune


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--rule", required=True, choices=["B1", "B2", "B3"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true", help="tiny budgets for a smoke run; never for the lock")
    args = ap.parse_args()
    lk = load_locked()
    cal = load_calibration(args.calibration)
    if not args.quick and list(cal.seeds) != seeds(lk, "calibration"):
        raise SystemExit("tuning for the lock needs the full calibration namespace (pass --quick for a smoke run)")
    cfg = cell_config(market_config_from_locked(lk), cal, rho=float(lk["rho"]["default"]), beta=float(lk["beta_headline"]))
    override = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16, "recheck_restarts": 1, "recheck_val_seeds": 2} if args.quick else None
    res = tune(args.rule, cfg, lk, SeedCache(), inner_override=override, grid_limit=3 if args.quick else None)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"rule": args.rule, "market_key": cal.market_key, "calibration_seeds": list(cal.seeds),
                                          "settings_hash": settings_hash(lk), "quick": bool(args.quick), "best_params": res.best_params,
                                          "rechecked": res.rechecked, "scores": res.scores}, indent=2) + "\n")
    print(json.dumps(res.best_params))


if __name__ == "__main__":
    main()
