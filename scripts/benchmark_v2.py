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
WORKLOADS = KINDS + ("doubling_x7", "episode", "reference_eval")
CAPS = {"development": 12.0, "evaluation": 40.0, "approval": 40.0}
EPISODES = {"coverage": 14 * 20_000 * 3, "cross": 14 * 56 * 200}
COUNTS = {"comparator_inner": (72, 36), "comparator_recheck": (12, 6), "tuning_inner": (384, 192), "tuning_recheck": (48, 24), "fixtures_inner": (6, 3),
          "doublings": (82, 50)}
CELLS = {"plain": 208, "x7": 118, "welfare_h3": 8, "welfare_x7": 8, "coalition": 32}       # 374 cells, 126 on the X7-SC knob space
EPISODE_SEEDS = tuple(range(2000, 2020))                                                  # dev-val: timing never touches reserved ranges


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
    w, co = timings.get("w1", u) / u, timings.get("coalition_total", u) / u
    cells = CELLS["plain"] + CELLS["x7"] * x7 + CELLS["welfare_h3"] * w + CELLS["welfare_x7"] * w * x7 + CELLS["coalition"] * co
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


def _default_fns(out: Path) -> dict:
    """The workloads of design 8.2 on development seeds at the registered budgets (paid pod time; never in tests)."""
    import numpy as np
    from scripts import revision_v2 as RV
    from scripts import tune_v2 as TV
    from sim import calibration_v2 as C
    from sim.cell import Cell, SeedCache, run_focal
    from sim.policies.honest import HonestMax
    from sim.reference import evaluate_gain, select_reference
    tmp = Path(tempfile.mkdtemp(dir=out)); params = {"cred": {"variant": "thr", "K": 6, "M": None}}
    mkt = RV.market("headline", RV.DEV_ROOT, 0.2, dev=True)
    jobs = {f: RV.job(mkt, "F111", f, params=params) for f in ("D2+H3", "X7-SC")}
    w1 = RV.job(mkt, "F111", "D2+H3", "W1", params=params); co = RV.job(mkt, "F111", "X6-SE/v2", "total", 2, "synchronised", params=params)
    dev0 = TV._market("dev0", False); inner = TV.INNER; state = {}

    def cell_unit(f):
        return lambda: RV._run_one("search", jobs[f], str(tmp), 0, True)

    def inner_family(f):
        def run():
            from dataclasses import replace as rep
            from sim.reference import twin_search
            j = RV.job(dev0, "F111", f, params=params); T, L = RV.constants(j); fam = RV.family_for(f, T, L); cache = SeedCache()
            st = rep(RV.settings(j), restarts=inner[0], evals_per_restart=inner[1] * (2 if f == "X7-SC" else 1))
            cell = rep(RV.train_cell(j), seeds=tuple(dev0["seeds_train"][: inner[2]]))
            RV.search_family(cell, fam, cache, st, twin_search(cell, fam, cache, st, seed=0), {})
        return run

    def reference_and_eval():
        import scripts.revision_v2 as R
        recs = {f: R.read(R.path_of(tmp, jobs[f]["id"])) for f in jobs}
        from sim.records import search_from_json
        from sim.reference import reference_candidates
        from sim.locked import load_locked
        cell = R.train_cell(jobs["D2+H3"]); groups = {}
        for f, rec in recs.items():
            T, L = R.constants(jobs[f]); fam = R.family_for(f, T, L)
            for c in reference_candidates(cell, fam, search_from_json(rec["attack"]), search_from_json(rec["twin"]), [], tuple(load_locked()["reference_order"])):
                groups.setdefault(("bank" if c.name.startswith("bank_") else c.name, f), []).append(c)
        cands, _ = R.merge_menu(groups, R.MENU); ref = select_reference(cell, cands, SeedCache())
        ev = Cell(cfg=mkt["cfg"], rule_factory=R.rule_factory(jobs["D2+H3"]), focal=mkt["focal"], seeds=EPISODE_SEEDS, name="ev")
        evaluate_gain(ev, R.family_for("D2+H3", 200, 10), recs["D2+H3"]["attack"]["best_knobs"], ref.candidate, SeedCache())
        state["ref"] = ref

    def w1_run():
        R = RV
        T, L = R.constants(jobs["D2+H3"])
        R.write(R.path_of(tmp, f"reference/{mkt['context']}/F111"), {"candidates": [R.cand_to_json(state["ref"].candidate, None, T, L)] if state["ref"].candidate.knobs is None
                                                                    else [R.cand_to_json(state["ref"].candidate, "D2+H3", T, L)], "choice": 0,
                                                                    "per_seed_normalized": [float(v) for v in state["ref"].per_seed_normalized]})
        R._run_one("dependent", w1, str(tmp), 0, True)

    def coalition_run():
        RV.coalition_prereqs(co, tmp); RV._run_one("dependent", co, str(tmp), 0, True)

    def doubling(f):
        def run():
            from sim.records import search_from_json
            from sim.search import Objective
            j = jobs[f]; T, L = RV.constants(j); fam = RV.family_for(f, T, L); rec = RV.read(RV.path_of(tmp, j["id"]))
            RV.continue_search(Objective(RV.train_cell(j), fam, SeedCache()), fam, RV.settings(j), search_from_json(rec["attack"]))
        return run

    rng = np.random.default_rng(0); strata = [{s_: rng.normal(0, 1, 10_000) for s_ in C.Q1_STATS} for _ in range(6)]
    ep_cell = Cell(cfg=mkt["cfg"], rule_factory=RV.rule_factory(jobs["D2+H3"]), focal=mkt["focal"], seeds=EPISODE_SEEDS, name="ep")
    return {"d2h3_cell": cell_unit("D2+H3"), "x7_cell": cell_unit("X7-SC"), "reference_eval": reference_and_eval, "w1": w1_run,
            "coalition_total": coalition_run,
            "inner": inner_family("D2+H3"), "inner_x7": inner_family("X7-SC"),
            "coverage_batch": lambda: C.miss_counts(strata, "pooled", C.Q1_TAILS, [1.0], 100, 9999, 1),
            "cross_row": lambda: [run_focal(ep_cell, HonestMax, SeedCache()) for _ in range(8)],
            "doubling": doubling("D2+H3"), "doubling_x7": doubling("X7-SC"),
            "episode": lambda: run_focal(ep_cell, HonestMax, SeedCache())}


def measure(out: Path, workers: int, fns: dict | None = None) -> dict:
    """Seconds per workload (every one in WORKLOADS is measured): full searches with controls, the reference and a
    20-seed dev-val evaluation (scaled to the unit's 40 seeds), W1 and coalition cells, the inner searches of a D2+H3 and
    an X7-SC tuning family, continued searches for doubling, one bootstrap batch, and episodes on dev-val seeds."""
    f = fns if fns is not None else _default_fns(Path(out))
    missing = [k for k in WORKLOADS if k not in f]
    if missing:
        raise SystemExit(f"benchmark workloads missing: {missing}")
    t = {k: _timed(f[k]) for k in WORKLOADS if k not in ("episode", "reference_eval")}
    rx = _timed(f["reference_eval"]); t["d2h3_cell"] += 2 * rx; t["x7_cell"] += 2 * rx
    t["episode"] = _timed(f["episode"]) / len(EPISODE_SEEDS)
    t["bootstrap_batch"] = t.pop("coverage_batch") * (30_000 / 100) * 2
    t["eval200_extra_fraction"] = 4 * 160 * t["episode"] / max(t["d2h3_cell"], 1e-9)
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
