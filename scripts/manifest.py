from __future__ import annotations

import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals
from sim.schedule import SMOKE_BUDGET


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--ms-per-run", type=float, default=45.0)
    ap.add_argument("--smoke", action="store_true", help="counts at the smoke budget")
    args = ap.parse_args()
    cells = enumerate_manifest(load_locked(), args.rules.split(","), budget=SMOKE_BUDGET if args.smoke else None)
    for c in cells:
        tag = "exact" if c.exact else "upper bound"
        print(f"{c.name:60s} {c.runs:>10,d}  {tag}{'  post-lock' if c.post_lock else ''}")
    t = totals(cells)
    for k in sorted(t):
        hours = t[k] * args.ms_per_run / 3.6e6
        print(f"{k:24s} {t[k]:>12,d} runs  {hours:8.1f} core-hours at {args.ms_per_run:.0f} ms/run")


if __name__ == "__main__":
    main()
