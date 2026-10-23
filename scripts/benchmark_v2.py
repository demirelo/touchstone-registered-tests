"""Benchmark v2 (design 8.2): time one job of each kind on a pod, then recompute the cost table and check the caps
(development 12 USD, evaluation 40 USD) and the author-approval threshold (40 USD in total). Units: one headline D2+H3
cell at the registered budget. Pod entry: `SCRIPT=scripts/benchmark_v2.py ARGS="--run" results/pods/explore_pod.sh ...`;
the launcher appends --workers and --out. --dry-run builds the job plan and exits without episodes; --smoke runs every
workload at the smoke budget (a wiring check before paid pod time, not a cost estimate)."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

KINDS = ("d2h3_cell", "x7_cell", "w1", "coalition_total", "inner", "inner_x7", "coverage_batch", "cross_row", "doubling")
# measured components, in dependency order (a component may read the records of the ones before it)
WORKLOADS = ("search_d2h3", "search_x7", "reference", "eval_d2h3", "eval_x7", "w1_search", "w1_eval", "coalition_prereqs", "coalition_search",
             "coalition_eval", "inner_d2", "inner", "inner_x7", "coverage_batch", "cross_row", "doubling", "doubling_x7", "episode")
CAPS = {"development": 12.0, "evaluation": 40.0, "approval": 40.0}
EPISODES = {"coverage": 14 * 20_000 * 3}
CROSS_ROWS = 14 * 8                                                                       # 14 cross-evaluations, 8 attack rows each
REFERENCE_MENUS = 118                                                                     # (context, rule) pairs with a D2+H3 and X7-SC menu
COUNTS = {"comparator_inner": (72, 36), "comparator_recheck": (12, 6), "tuning_inner": (384, 192), "tuning_recheck": (48, 24), "fixtures_inner": (6, 3),
          "doublings": (82, 50)}
CELLS = {"plain": 208, "x7": 118, "welfare_h3": 8, "welfare_x7": 8, "coalition": 32}       # 374 cells, 126 on the X7-SC knob space
EPISODE_SEEDS = tuple(range(2000, 2020))                                                  # dev-val: timing never touches reserved ranges
EVAL_SEEDS, FINAL_SEEDS = 20, 200


def cost_table(timings: dict, usd_per_core_hour: float) -> dict:
    """Design 8.2's rows in units of the measured headline D2+H3 cell, then core-hours and USD. Measured timings price a
    cell as its search and 40-seed evaluation, the reference menus once per (context, rule) (`reference`), and the 160
    further evaluation seeds from each kind's own evaluation (`eval160`); design-unit timings (no `reference`, an
    `eval200_extra_fraction`) reproduce the design's table. The non-X7 inner share (D2 and D2+H3, equal counts) is priced
    at the mean of the two measured inner searches; the cross-evaluation at the measured row (one attack against the 8
    factorial rules and their references) scaled from 20 to 200 seeds."""
    u = float(timings["d2h3_cell"])
    x7, inner_x7 = timings["x7_cell"] / u, timings["inner_x7"] / u
    inner = (timings["inner"] + timings.get("inner_d2", timings["inner"])) / 2 / u
    dbl, dbl_x7 = timings["doubling"] / u, timings["doubling_x7"] / u
    mix = lambda pair, a, b: pair[0] * a + pair[1] * b
    rows = {"comparator_selection": mix(COUNTS["comparator_inner"], inner, inner_x7) + mix(COUNTS["comparator_recheck"], 1.0, x7),
            "tuning": mix(COUNTS["tuning_inner"], inner, inner_x7) + mix(COUNTS["tuning_recheck"], 1.0, x7),
            "fixtures": mix(COUNTS["fixtures_inner"], inner, inner_x7),
            "coverage": EPISODES["coverage"] * timings["episode"] / u + timings["bootstrap_batch"] / u}
    w, co = timings.get("w1", u) / u, timings.get("coalition_total", u) / u
    cells = CELLS["plain"] + CELLS["x7"] * x7 + CELLS["welfare_h3"] * w + CELLS["welfare_x7"] * w * x7 + CELLS["coalition"] * co
    e = timings.get("eval160")
    extra = ((CELLS["plain"] * e["profit"] + CELLS["x7"] * e["x7"] + (CELLS["welfare_h3"] + CELLS["welfare_x7"]) * e["welfare"]
              + CELLS["coalition"] * e["coalition"]) / u) if e else float(timings["eval200_extra_fraction"]) * cells
    rows.update({"cells": cells, "references": REFERENCE_MENUS * float(timings.get("reference", 0.0)) / u, "eval200_extra": extra,
                 "cross": CROSS_ROWS * timings["cross_row"] * (FINAL_SEEDS / EVAL_SEEDS) / u, "doublings": mix(COUNTS["doublings"], dbl, dbl_x7)})
    dev = rows["comparator_selection"] + rows["tuning"] + rows["fixtures"] + rows["coverage"]
    ev = rows["cells"] + rows["references"] + rows["eval200_extra"] + rows["cross"] + rows["doublings"]
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


def _default_fns(out: Path, smoke: bool = False) -> dict:
    """The workloads of design 8.2 on development seeds (headline market with dev-train and dev-val seeds; dev0 for the
    inner searches) at the registered budgets: paid pod time. `smoke` runs the same wiring at the smoke budget (tests).
    The reference menu carries a stand-in bank of distinct projected archive points, as many per family as the effective
    manifest's bank rules other than F111 (11: a matched rule's menu holds the other matched rules' attacks); the cross
    row and the doubling reselection use the measured reference."""
    import numpy as np
    from dataclasses import replace as rep
    from scripts import revision_v2 as RV
    from scripts import tune_v2 as TV
    from sim import calibration_v2 as C
    from sim import manifest_v2 as MAN
    from sim.cell import Cell, SeedCache, run_focal
    from sim.locked import load_locked
    from sim.policies.families import exact_key
    from sim.policies.honest import HonestMax
    from sim.records import search_from_json
    from sim.reference import reference_candidates, select_reference, twin_search
    from sim.search import Objective
    tmp = Path(tempfile.mkdtemp(dir=out)); params = {"cred": {"variant": "thr", "K": 6, "M": None}}; order = tuple(load_locked()["reference_order"])
    mkt = RV.market("headline", RV.DEV_ROOT, 0.2, dev=True, smoke=smoke); ctx = mkt["context"]
    jobs = {f: RV.job(mkt, "F111", f, smoke=smoke, params=params) for f in RV.MENU}
    w1 = RV.job(mkt, "F111", "D2+H3", "W1", smoke=smoke, params=params)
    co = RV.job(mkt, "F111", "X6-SE/v2", "total", 2, "synchronised", smoke=smoke, params=params)
    dev0 = RV.market("dev0", RV.DEV_ROOT, 0.2, dev=True); inner = TV.SMOKE_INNER if smoke else TV.INNER
    seeds = EPISODE_SEEDS[:2] if smoke else EPISODE_SEEDS; state = {"bank_sizes": {}}
    n_bank = {f: len([o for o in MAN.bank_rules(RV.manifest_ctx(ctx), f, 0, False) if o != "F111"]) for f in RV.MENU}

    def search(f):
        return lambda: RV._run_one("search", jobs[f], str(tmp), 0, True)

    def bank(rec, fam, n):
        """Distinct projected archive points after the best, standing in for the other matched rules' attacks."""
        best, seen, out_ = exact_key(fam.project(rec["attack"]["best_knobs"])), set(), []
        for e in sorted(search_from_json(rec["attack"]).archive.values(), key=lambda e: -e.f):
            k = fam.project(e.knobs); key = exact_key(k)
            if key != best and key not in seen:
                seen.add(key); out_.append(k)
            if len(out_) == n:
                break
        if len(out_) < n:
            raise SystemExit(f"benchmark: only {len(out_)} distinct archive points for a bank of {n}")
        return out_

    def reference():
        cell = RV.train_cell(jobs["D2+H3"]); groups = {}
        for f, j in jobs.items():
            rec = RV.read(RV.path_of(tmp, j["id"])); T, L = RV.constants(j); fam = RV.family_for(f, T, L)
            b = bank(rec, fam, n_bank[f]); state["bank_sizes"][f] = len(b)
            for c in reference_candidates(cell, fam, search_from_json(rec["attack"]), search_from_json(rec["twin"]), b, order):
                groups.setdefault(("bank" if c.name.startswith("bank_") else c.name, f), []).append(c)
        cands, fams = RV.merge_menu(groups, RV.MENU); ch = select_reference(cell, cands, SeedCache())
        T, L = RV.constants(jobs["D2+H3"]); idx = next(i for i, c in enumerate(cands) if c is ch.candidate)
        state.update(cands=cands, ref=ch.candidate)
        RV.write(RV.path_of(tmp, f"reference/{ctx}/F111"), {"stage": "reference", "provenance": RV.reference_provenance(jobs["D2+H3"]), "upstream": {},
                                                           "candidates": [RV.cand_to_json(c, f, T, L) for c, f in zip(cands, fams)], "choice": idx,
                                                           "per_seed_normalized": [float(v) for v in ch.per_seed_normalized]})

    def inner_family(f):
        def run():
            j = RV.job(dev0, "F111", f, params=params); T, L = RV.constants(j); fam = RV.family_for(f, T, L); cache = SeedCache()
            st = rep(RV.settings(j), restarts=inner[0], evals_per_restart=inner[1] * (2 if f == "X7-SC" else 1))
            cell = rep(RV.train_cell(j), seeds=tuple(dev0["seeds_train"][: inner[2]]))
            RV.search_family(cell, fam, cache, st, twin_search(cell, fam, cache, st, seed=0), {})
        return run

    def cross_row():
        """One attack row (stage_cross): the D2+H3 attack and a reference against each factorial rule on dev-val seeds."""
        k = RV.read(RV.path_of(tmp, jobs["D2+H3"]["id"]))["attack"]["best_knobs"]; cache = SeedCache()
        for r in MAN.FACTORIAL:
            j = RV.job(mkt, r, "D2+H3", smoke=smoke); T, L = RV.constants(j); fam = RV.family_for("D2+H3", T, L)
            cell = rep(RV.eval_cell(j), seeds=seeds)
            run_focal(cell, lambda: fam.make(dict(k)), cache); run_focal(cell, state["ref"].policy_factory, cache)

    def doubling(f):
        """stage_doubling's profit check: the continued search, then the reference reselected from the menu and the new
        search's candidates."""
        def run():
            j = jobs[f]; T, L = RV.constants(j); fam = RV.family_for(f, T, L); rec = RV.read(RV.path_of(tmp, j["id"])); cell = RV.train_cell(j); cache = SeedCache()
            new = RV.continue_search(Objective(cell, fam, cache), fam, RV.settings(j), search_from_json(rec["attack"]))
            extra = reference_candidates(cell, fam, new, search_from_json(rec["twin"]), [], order)
            select_reference(cell, state["cands"] + [c for c in extra if c.knobs is not None], cache)
        return run

    rng = np.random.default_rng(0); B = (2, 99) if smoke else (100, 9999)
    strata = [{s_: rng.normal(0, 1, 10_000) for s_ in C.Q1_STATS} for _ in range(6)]
    ep_cell = Cell(cfg=mkt["cfg"], rule_factory=RV.rule_factory(jobs["D2+H3"]), focal=mkt["focal"], seeds=seeds, name="ep")
    return {"search_d2h3": search("D2+H3"), "search_x7": search("X7-SC"), "reference": reference,
            "eval_d2h3": lambda: RV.stage_evaluate(jobs["D2+H3"], tmp), "eval_x7": lambda: RV.stage_evaluate(jobs["X7-SC"], tmp),
            "w1_search": lambda: RV._run_one("dependent", w1, str(tmp), 0, True), "w1_eval": lambda: RV.stage_evaluate(w1, tmp),
            "coalition_prereqs": lambda: RV.coalition_prereqs(co, tmp), "coalition_search": lambda: RV._run_one("dependent", co, str(tmp), 0, True),
            "coalition_eval": lambda: RV.stage_evaluate(co, tmp),
            "inner_d2": inner_family("D2"), "inner": inner_family("D2+H3"), "inner_x7": inner_family("X7-SC"),
            "coverage_batch": lambda: C.miss_counts(strata, "pooled", C.Q1_TAILS, [1.0], B[0], B[1], 1),
            "cross_row": cross_row, "doubling": doubling("D2+H3"), "doubling_x7": doubling("X7-SC"),
            "episode": lambda: run_focal(ep_cell, HonestMax, SeedCache()), "_meta": {"eval_seeds": len(mkt["seeds_eval"]), "episodes": len(seeds),
                                                                                  "coverage_replications": B[0], "state": state}}


def measure(out: Path, workers: int, fns: dict | None = None, smoke: bool = False) -> dict:
    """Seconds per kind, composed from the components measured in WORKLOADS order. A profit cell is its search and its
    evaluation scaled from the measured dev-val seeds to 40; the reference menu (with its bank) is a kind of its own,
    priced once per (context, rule); W1 is its search and evaluation; a coalition objective half the group's joint twin
    and joint reference (shared by total and min), its search, and its evaluation; `eval160` holds each kind's 160
    further evaluation seeds; inner searches, the cross row, and doublings as measured."""
    f = fns if fns is not None else _default_fns(Path(out), smoke)
    missing = [k for k in WORKLOADS if k not in f]
    if missing:
        raise SystemExit(f"benchmark workloads missing: {missing}")
    meta = f.get("_meta", {}); n_eval = int(meta.get("eval_seeds", EVAL_SEEDS)); n_ep = int(meta.get("episodes", len(EPISODE_SEEDS)))
    r = {k: _timed(f[k]) for k in WORKLOADS}
    to40 = 40 / n_eval
    t = {"d2h3_cell": r["search_d2h3"] + to40 * r["eval_d2h3"], "x7_cell": r["search_x7"] + to40 * r["eval_x7"], "reference": r["reference"],
         "w1": r["w1_search"] + to40 * r["w1_eval"], "coalition_total": r["coalition_prereqs"] / 2 + r["coalition_search"] + to40 * r["coalition_eval"],
         "inner_d2": r["inner_d2"], "inner": r["inner"], "inner_x7": r["inner_x7"], "cross_row": r["cross_row"] * EVAL_SEEDS / n_ep,
         "doubling": r["doubling"], "doubling_x7": r["doubling_x7"], "episode": r["episode"] / n_ep,
         "bootstrap_batch": r["coverage_batch"] * (30_000 / int(meta.get("coverage_replications", 100))) * 2}
    to160 = (FINAL_SEEDS - 40) / n_eval
    t["eval160"] = {"profit": to160 * r["eval_d2h3"], "x7": to160 * r["eval_x7"], "welfare": to160 * r["w1_eval"], "coalition": to160 * r["coalition_eval"]}
    t["components"] = r; t["bank_sizes"] = dict(meta.get("state", {}).get("bank_sizes", {}))
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--table", default=None)
    ap.add_argument("--out", default="."); ap.add_argument("--workers", type=int, default=1); ap.add_argument("--dry-run", dest="dry_run", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="the same workloads at the smoke budget (wiring check; not a cost estimate)")
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
    t = measure(out, a.workers, smoke=a.smoke)
    (out / "timings.json").write_text(json.dumps({"timings": t, "usd_per_core_hour": a.rate, "smoke": a.smoke}))
    (out / "cost_table.json").write_text(json.dumps(cost_table(t, a.rate), default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
