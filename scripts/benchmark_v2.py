"""Benchmark v2 (design 8.2): time one job of each kind on a pod, then recompute the cost table and check the caps
(development 12 USD, evaluation 40 USD) and the author-approval threshold (40 USD in total). Units: one headline D2+H3
cell at the registered budget. Pod entry: `SCRIPT=scripts/benchmark_v2.py ARGS="--run" results/pods/explore_pod.sh ...`;
the launcher appends --workers and --out. --dry-run builds the job plan and exits without episodes."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

KINDS = ("d2h3_cell", "x7_cell", "w1", "coalition_total", "inner", "inner_x7", "coverage_batch", "cross_row", "doubling")
CAPS = {"development": 12.0, "evaluation": 40.0, "approval": 40.0}
EPISODES = {"coverage": 14 * 20_000 * 3, "cross": 14 * 56 * 200}
COUNTS = {"comparator_inner": (72, 36), "comparator_recheck": (12, 6), "tuning_inner": (384, 192), "tuning_recheck": (48, 24), "fixtures_inner": (6, 3),
          "cells": (374 - 126, 126), "doublings": (82, 50)}


def cost_table(timings: dict, usd_per_core_hour: float) -> dict:
    """Design 8.2's rows in units of the measured headline D2+H3 cell, then core-hours and USD."""
    u = float(timings["d2h3_cell"])
    x7, inner, inner_x7 = timings["x7_cell"] / u, timings["inner"] / u, timings["inner_x7"] / u
    dbl, dbl_x7, ep = timings["doubling"] / u, timings["doubling_x7"] / u, timings["episode"] / u
    mix = lambda pair, a, b: pair[0] * a + pair[1] * b
    rows = {"comparator_selection": mix(COUNTS["comparator_inner"], inner, inner_x7) + mix(COUNTS["comparator_recheck"], 1.0, x7),
            "tuning": mix(COUNTS["tuning_inner"], inner, inner_x7) + mix(COUNTS["tuning_recheck"], 1.0, x7),
            "fixtures": mix(COUNTS["fixtures_inner"], inner, inner_x7),
            "coverage": EPISODES["coverage"] * ep + timings["bootstrap_batch"] / u}
    cells = mix(COUNTS["cells"], 1.0, x7)
    rows.update({"cells": cells, "eval200_extra": float(timings["eval200_extra_fraction"]) * cells, "cross": EPISODES["cross"] * ep,
                 "doublings": mix(COUNTS["doublings"], dbl, dbl_x7)})
    dev = rows["comparator_selection"] + rows["tuning"] + rows["fixtures"] + rows["coverage"]
    ev = rows["cells"] + rows["eval200_extra"] + rows["cross"] + rows["doublings"]
    usd_unit = u / 3600.0 * float(usd_per_core_hour)
    out = {"rows": rows, "development_units": dev, "evaluation_units": ev, "unit_core_hours": u / 3600.0,
           "development_usd": dev * usd_unit, "evaluation_usd": ev * usd_unit, "total_usd": (dev + ev) * usd_unit}
    out["flags"] = {"development_over_cap": out["development_usd"] > CAPS["development"], "evaluation_over_cap": out["evaluation_usd"] > CAPS["evaluation"],
                    "approval_required": out["total_usd"] > CAPS["approval"]}
    return out


def plan() -> list[dict]:
    return [{"kind": k, "market": "headline" if k not in ("inner", "inner_x7", "coverage_batch") else "dev0", "rule": "F111"} for k in KINDS]


def _timed(f) -> float:
    t0 = time.perf_counter(); f(); return time.perf_counter() - t0


def measure(out: Path, workers: int) -> dict:
    """One job of each kind at the registered budgets (paid pod time; never in tests)."""
    from scripts import revision_v2 as RV
    from scripts import tune_v2 as TV
    from sim import calibration_v2 as C
    from sim.cell import SeedCache
    tmp = Path(tempfile.mkdtemp(dir=out)); cred = {"variant": "thr", "K": 6, "M": None}
    mkt = RV.market("headline", RV.DEV_ROOT, 0.2, dev=True); params = {"cred": cred}
    j_h3, j_x7 = RV.job(mkt, "F111", "D2+H3", params=params), RV.job(mkt, "F111", "X7-SC", params=params)
    t = {}
    t["d2h3_cell"] = _timed(lambda: RV._run_one("search", j_h3, str(tmp), 0, True))
    t["x7_cell"] = _timed(lambda: RV._run_one("search", j_x7, str(tmp), 0, True))
    dev0 = TV._market("dev0", False); inner, _ = TV._budgets(False)
    t["inner"] = _timed(lambda: TV.market_searches("F111", {"tol": 0.16, "L": 10}, dev0, inner, SeedCache())) / 3.0
    t["inner_x7"] = 2.5 * t["inner"]
    t["doubling"], t["doubling_x7"] = t["d2h3_cell"], t["x7_cell"]
    from sim.cell import Cell, run_focal
    from sim.policies.honest import HonestMax
    cell = Cell(cfg=mkt["cfg"], rule_factory=RV.rule_factory(j_h3), focal=mkt["focal"], seeds=tuple(range(30_000_000, 30_000_100)), name="ep")
    t["episode"] = _timed(lambda: run_focal(cell, HonestMax, SeedCache())) / 100.0
    import numpy as np
    rng = np.random.default_rng(0); strata = [{s: rng.normal(0, 1, 10_000) for s in C.Q1_STATS} for _ in range(6)]
    t["bootstrap_batch"] = _timed(lambda: C.miss_counts(strata, "pooled", C.Q1_TAILS, [1.0], 100, 9999, 1)) * (30_000 / 100) * 2
    t["eval200_extra_fraction"] = 4 * 160 * t["episode"] / t["d2h3_cell"]
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--table", default=None)
    ap.add_argument("--out", default="."); ap.add_argument("--workers", type=int, default=1); ap.add_argument("--dry-run", dest="dry_run", action="store_true")
    ap.add_argument("--usd-per-core-hour", dest="rate", type=float, default=0.108)
    a = ap.parse_args(argv)
    if a.table:
        d = json.loads(Path(a.table).read_text())
        print(json.dumps(cost_table(d["timings"], float(d.get("usd_per_core_hour", a.rate))), default=float))
        return 0
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark_plan.json").write_text(json.dumps({"kinds": plan(), "workers": a.workers}))
    if a.dry_run:
        return 0
    t = measure(out, a.workers)
    (out / "timings.json").write_text(json.dumps({"timings": t, "usd_per_core_hour": a.rate}))
    (out / "cost_table.json").write_text(json.dumps(cost_table(t, a.rate), default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
