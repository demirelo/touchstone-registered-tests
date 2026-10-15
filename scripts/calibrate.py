from __future__ import annotations

import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked, seeds


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20, help="how many calibration seeds to use")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lk = load_locked()
    cal = calibrate(market_config_from_locked(lk), seeds(lk, "calibration")[: args.seeds])
    save_calibration(cal, args.out)
    print(json.dumps(cal.as_dict(), sort_keys=True))


if __name__ == "__main__":
    main()
