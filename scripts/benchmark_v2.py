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
             "coalition_reference", "coalition_final", "coalition_select", "coalition_eval", "dev_inner_config", "coverage_batch", "cross_row",
             "doubling", "doubling_x7", "episode")
CAPS = {"development": 12.0, "evaluation": 40.0, "approval": 40.0}
EPISODES = {"coverage": 8 * 20_000 * 3}                                                   # design draft 7, 9.5: 8 profiles
CROSS_ROWS = 14 * 8                                                                       # 14 cross-evaluations, 8 attack rows each
REFERENCE_MENUS = 79                                                                      # (context, rule) pairs with a D2+H3 and X7-SC menu
REDUCED_MENUS = 18                                                                        # fresh-market secondary systems: D2+H3 only (design 6.4)
CONFIG_MARKETS = {"comparator_inner": 36, "comparator_recheck": 6, "tuning_inner": 144, "tuning_recheck": 18}   # design 8.2's searches / 3
COUNTS = {"comparator_inner": (72, 36), "comparator_recheck": (12, 6), "tuning_inner": (288, 144), "tuning_recheck": (36, 18), "doublings": (64, 34)}
CELLS = {"plain": 145, "x7": 79, "h4": 21, "welfare_h3": 6, "welfare_x7": 6, "coalition": 30}   # 287 search cells (design draft 7, 8.1)
TRAIN_SEEDS = 5                                                                           # dev-train seeds of the registered search (bank matrix)
COALITION_EXTRAS_UNITS, HELDOUT_UNITS = 18.0, 2.0                                         # design 8.2's estimates when the components are unmeasured
EPISODE_SEEDS = tuple(range(2000, 2020))                                                  # dev-val: timing never touches reserved ranges
EVAL_SEEDS, FINAL_SEEDS = 20, 200


DEFAULT_MARKETS = ("headline", "dev0", "dev1")
DEV_BRANCHES = (("three20k", DEFAULT_MARKETS), ("two20k", ("headline", "dev0")), ("two10k", ("headline", "dev0")))
H4_RESERVE_USD = 1.0                                                                      # the H4 decision pod (Operation 6)


def counts(cuts: int = 0, h4_excluded: bool = False, markets=DEFAULT_MARKETS, branch: str = "three20k") -> dict:
    """The design 8.2 counts from the effective manifest, the tuning markets, and the coverage branch."""
    from sim import calibration_v2 as CAL
    from sim import manifest_v2 as MAN
    eff = MAN.effective(cuts, h4_excluded); cs = [c for c in eff if c["block"] != "diagnostic"]
    ids = {c["id"] for c in cs}; ctxs = {c["context"] for c in cs}
    kind = lambda c: ("coalition" if c["objective"] in ("total", "min") else ("welfare_x7" if c["family"] == "X7-SC" else "welfare_h3")
                      if c["objective"] in ("W0", "W1") else ("x7" if c["family"] == "X7-SC" else "h4" if c["family"] == "H4" else "plain"))
    cells = {k: 0 for k in ("plain", "x7", "h4", "welfare_h3", "welfare_x7", "coalition")}
    for c in cs:
        cells[kind(c)] += 1
    dbl = [d for d in MAN.doublings() if d in ids]
    k = len(markets) / 3
    M = CAL.BRANCHES[branch][1]; n_cov = len(CAL.BRANCHES[branch][0])
    menus = {(c["context"], c["rule"]) for c in cs if c["objective"] == "profit" and c["family"] in ("D2+H3", "X7-SC")}
    full = {m for m in menus if MAN.menu_families(m[0], m[1]) == MAN.MENU_FAMILIES}
    cross = sum(1 for ctx, _ in MAN.cross_evaluations() if ctx in ctxs)
    return {"cells": cells, "reference_menus": len(full), "reduced_menus": len(menus - full),
            "doublings": (sum("|X7-SC|" not in d for d in dbl), sum("|X7-SC|" in d for d in dbl)), "cross_rows": 8 * cross, "bank_train_items": cross,
            "coalition_groups": len({(c["context"], c["rule"], c["c"]) for c in cs if c["objective"] in ("total", "min")}),
            "diagnostic": sum(c["block"] == "diagnostic" for c in eff),
            "config_markets": {name: int(round(n * k)) for name, n in CONFIG_MARKETS.items()}, "coverage_episodes": len(CAL.PROFILES) * M * n_cov}


def wave_bound(times, vcpu: int) -> float:
    """Pod seconds for one wave of tasks with times `times` on `vcpu` workers: sum / vcpu + (1 - 1 / vcpu) max, an upper
    bound on the elapsed time of any greedy (list-scheduling) assignment."""
    t = [float(x) for x in times]
    return (sum(t) / vcpu + (1 - 1 / vcpu) * max(t)) if t else 0.0


STAGES_BILLED = ("search", "reference", "dependent", "evaluate", "cross", "doubling")


def eval_pods(cuts: int = 0, h4_excluded: bool = False) -> dict:
    """Manifest cells as runner-shaped jobs, grouped by pod (Operation 7): one pod per fresh market, the headline market split
    by context."""
    from sim import manifest_v2 as MAN
    pods = {}
    for c in MAN.effective(cuts, h4_excluded):
        j = {k: c.get(k) for k in ("id", "context", "rule", "family", "objective", "c", "schedule", "block")}; j["priority"] = MAN.priority(c)
        label = c["context"].split("@", 1)[0]
        pods.setdefault(c["context"] if label == "headline" else label, []).append(j)
    return pods


def _ratio(h4_timing: dict | None) -> float:
    """An H4 cell's cost relative to an X7-SC cell, from the sealed session's timing payload (design draft 7, 5.3)."""
    return float(h4_timing["h4_seconds"]) / float(h4_timing["x7_seconds"]) if h4_timing else 1.0


def _task(ts: dict, st: str, j: dict, h4: float = 1.0) -> float:
    fam = j.get("family"); x7 = fam in ("X7-SC", "H4"); obj = j.get("objective"); scale = h4 if fam == "H4" else 1.0
    if st == "search":
        return ts["search"][("x7" if x7 else "profit") if obj == "profit" else ("W0_x7" if x7 else "W0")] * scale
    if st == "reference":
        return ts["reference"]
    if st == "joint_twin":
        return ts["prereqs"]
    if st in ("joint_reference_pre", "joint_reference", "coalition_select"):
        return ts[{"joint_reference_pre": "coalition_reference", "joint_reference": "coalition_final", "coalition_select": "coalition_select"}[st]]
    if st == "dependent":
        return ts["coalition"] if obj in ("total", "min") else ts["W1_x7" if x7 else "W1"]
    if st == "evaluate":
        if obj == "diagnostic":
            return ts["evaluate"]["diagnostic"]
        return ts["evaluate"]["coalition" if obj in ("total", "min") else "welfare" if obj in ("W0", "W1") else "x7" if x7 else "profit"] * scale
    if st == "cross":
        return ts["cross_item"]
    return ts["doubling_x7" if x7 else "doubling"] * scale


def pod_plan(timings: dict, jobs: list[dict], h4: float = 1.0) -> list[list[float]]:
    """One pod's waves, exactly the runner's dispatch (`revision_v2._waves`) per stage, each task at its measured component
    time (`task_seconds`): searches, reference menus, W1 searches, coalition prerequisites and objectives, each context's
    freeze (its training bank matrices, serial), evaluations on 200 seeds, cross items, and doublings, every one in its own
    wave."""
    from scripts import revision_v2 as RV
    from sim import manifest_v2 as MAN
    ts = timings["task_seconds"]; ctxs = {j["context"] for j in jobs}
    matrix = 8 * ts["cross_item"] * TRAIN_SEEDS / FINAL_SEEDS          # one family's 8 x 8 bank matrix on the dev-train seeds
    freeze = [[sum(matrix for c, _ in MAN.cross_evaluations() if c == ctx)] for ctx in sorted(ctxs)]   # serial, in the freeze (design 6.6)
    waves = {stage: [[_task(ts, st, i, h4) for i in items] for st, items in RV._waves(stage, jobs, jobs)] for stage in STAGES_BILLED}
    return [w for stage in STAGES_BILLED for w in waves[stage] + ([f for f in freeze if f[0] > 0] if stage == "dependent" else [])]


def default_eval_plan(timings: dict, cuts: int = 0, h4_excluded: bool = False, h4: float = 1.0) -> list[list[float]]:
    return [w for jobs in eval_pods(cuts, h4_excluded).values() for w in pod_plan(timings, jobs, h4)]


def _pod_table(timings: dict, cuts: int, h4_excluded: bool, markets, branch: str, vcpu: int, plan, h4_timing: dict | None = None) -> dict:
    from sim import calibration_v2 as CAL
    n = counts(cuts, h4_excluded, markets, branch); m = len(markets); v = int(vcpu); P = len(CAL.PROFILES)
    ic, rc = float(timings["dev_inner_config"]), float(timings["dev_recheck_config"])
    stage = lambda inner_tasks: wave_bound([ic] * inner_tasks, v) + wave_bound([rc] * (2 * m), v)
    M_markets = n["coverage_episodes"] // P
    n_cov = len(CAL.BRANCHES[branch][0]); per_market = P * (M_markets // n_cov) * float(timings["episode"])
    rows = {"comparator_selection": stage(12 * m), "tuning": 3 * stage(16 * m),                         # three tuned systems, no fixtures
            "coverage": n_cov * wave_bound([per_market / v] * v, v) + wave_bound([float(timings["bootstrap_batch"])], v)}
    rows["evaluation"] = sum(wave_bound(w, v) for w in (plan if plan is not None else default_eval_plan(timings, cuts, h4_excluded, _ratio(h4_timing))))
    rate = float(timings["usd_per_pod_hour"]) / 3600.0
    dev = rows["comparator_selection"] + rows["tuning"] + rows["coverage"]
    out = {"rows_seconds": rows, "vcpu": v, "counts": n, "development_usd": dev * rate, "evaluation_usd": rows["evaluation"] * rate,
           "total_usd": (dev + rows["evaluation"]) * rate}
    out["flags"] = {"development_over_cap": out["development_usd"] > CAPS["development"], "evaluation_over_cap": out["evaluation_usd"] > CAPS["evaluation"],
                    "approval_required": out["total_usd"] > CAPS["approval"]}
    return out


def cost_table(timings: dict, usd_per_core_hour: float | None = None, *, cuts: int = 0, h4_excluded: bool = False, markets=DEFAULT_MARKETS,
               branch: str = "three20k", vcpu: int = 16, plan=None, h4_timing: dict | None = None) -> dict:
    """Without `usd_per_core_hour`: billed pod time at the measured `usd_per_pod_hour`, every wave at the list-scheduling
    bound (`wave_bound`), counts from the effective manifest (`counts`), development per configuration and market, and the
    evaluation from `plan` (default: `default_eval_plan`). With `usd_per_core_hour`: design 8.2's rows in units of the
    measured headline D2+H3 cell at full utilisation (design-unit timings reproduce the design's table): a cell is its search
    and 40-seed evaluation, the reference menus once per (context, rule), the 160 further seeds from each kind's own
    evaluation (`eval160`), the cross row scaled from 20 to 200 seeds."""
    if usd_per_core_hour is None:
        return _pod_table(timings, cuts, h4_excluded, markets, branch, vcpu, plan, h4_timing)
    n = counts(cuts, h4_excluded, markets, branch); C = n["cells"]; k = len(markets) / 3; h4 = _ratio(h4_timing)
    u = float(timings["d2h3_cell"])
    x7 = timings["x7_cell"] / u
    dbl, dbl_x7 = timings["doubling"] / u, timings["doubling_x7"] / u
    mix = lambda pair, a, b: pair[0] * a + pair[1] * b
    if "dev_inner_config" in timings:
        ic, rc, cm = timings["dev_inner_config"] / u, timings["dev_recheck_config"] / u, n["config_markets"]
        rows = {"comparator_selection": cm["comparator_inner"] * ic + cm["comparator_recheck"] * rc, "tuning": cm["tuning_inner"] * ic + cm["tuning_recheck"] * rc}
    else:
        inner, inner_x7 = (timings["inner"] + timings.get("inner_d2", timings["inner"])) / 2 / u, timings["inner_x7"] / u
        sc = lambda pair: (pair[0] * k, pair[1] * k)
        rows = {"comparator_selection": mix(sc(COUNTS["comparator_inner"]), inner, inner_x7) + mix(sc(COUNTS["comparator_recheck"]), 1.0, x7),
                "tuning": mix(sc(COUNTS["tuning_inner"]), inner, inner_x7) + mix(sc(COUNTS["tuning_recheck"]), 1.0, x7)}
    rows["coverage"] = n["coverage_episodes"] * timings["episode"] / u + timings["bootstrap_batch"] / u
    w, co = timings.get("w1", u) / u, timings.get("coalition_total", u) / u
    cells = C["plain"] + C["x7"] * x7 + C["h4"] * x7 * h4 + C["welfare_h3"] * w + C["welfare_x7"] * w * x7 + C["coalition"] * co
    e = timings.get("eval160")
    extra = ((C["plain"] * e["profit"] + (C["x7"] + C["h4"]) * e["x7"] + (C["welfare_h3"] + C["welfare_x7"]) * e["welfare"]
              + C["coalition"] * e["coalition"]) / u) if e else float(timings["eval200_extra_fraction"]) * cells
    if "coalition_reference" in timings:                    # design 6.3: per group, the preliminary and final references and the selection
        co_x = n["coalition_groups"] * (timings["coalition_reference"] + timings["coalition_final"] + timings["coalition_select"]) / u
    else:
        co_x = COALITION_EXTRAS_UNITS
    rows.update({"cells": cells, "references": (n["reference_menus"] + n["reduced_menus"]) * float(timings.get("reference", 0.0)) / u,
                 "eval200_extra": extra, "cross": n["cross_rows"] * timings["cross_row"] * (FINAL_SEEDS / EVAL_SEEDS) / u,
                 "doublings": mix(n["doublings"], dbl, dbl_x7), "coalition_extras": co_x,
                 "bank_train": n["bank_train_items"] * 8 * timings["cross_row"] * (TRAIN_SEEDS / EVAL_SEEDS) / u,
                 "heldout": 0.0 if timings.get("doubling_includes_heldout") else HELDOUT_UNITS,
                 "diagnostic": n["diagnostic"] * FINAL_SEEDS * timings["episode"] / u})
    dev = rows["comparator_selection"] + rows["tuning"] + rows["coverage"]
    ev = sum(rows[k] for k in ("cells", "references", "eval200_extra", "cross", "doublings", "coalition_extras", "bank_train", "heldout", "diagnostic"))
    usd_unit = u / 3600.0 * float(usd_per_core_hour)
    out = {"rows": rows, "development_units": dev, "evaluation_units": ev, "unit_core_hours": u / 3600.0,
           "development_usd": dev * usd_unit, "evaluation_usd": ev * usd_unit, "total_usd": (dev + ev) * usd_unit}
    out["flags"] = {"development_over_cap": out["development_usd"] > CAPS["development"], "evaluation_over_cap": out["evaluation_usd"] > CAPS["evaluation"],
                    "approval_required": out["total_usd"] > CAPS["approval"]}
    return out


def choose(timings: dict, ledger: dict, vcpu: int = 16) -> dict:
    """Design 8.2's decision from the benchmark: the first development branch whose cost plus the spend so far fits the
    development cap, the smallest cut whose evaluation cost plus the H4 decision reserve fits the evaluation cap, and the
    approval flag on the total; "stop" names the phase that fits under no option."""
    spent = sum(float(r["usd"]) for r in ledger.get("spent", []) if r["op"] == "development")
    out = {"branch": None, "markets": None, "cuts": None, "spent_usd": spent, "h4_reserve_usd": H4_RESERVE_USD, "stop": None}
    for branch, markets in DEV_BRANCHES:
        dev = cost_table(timings, markets=markets, branch=branch, vcpu=vcpu)["development_usd"] + spent
        if dev <= CAPS["development"]:
            out.update(branch=branch, markets=list(markets), development_usd=dev); break
    else:
        out["stop"] = "development"; return out
    for cuts in range(0, 5):
        ev = cost_table(timings, cuts=cuts, vcpu=vcpu)["evaluation_usd"] + H4_RESERVE_USD
        if ev <= CAPS["evaluation"]:
            out.update(cuts=cuts, evaluation_usd=ev); break
    else:
        out["stop"] = "evaluation"; return out
    out["total_usd"] = out["development_usd"] + out["evaluation_usd"]; out["approval_required"] = out["total_usd"] > CAPS["approval"]
    return out


def choose_after_h4(timings: dict, ledger: dict, frozen: dict, h4_timing: dict, vcpu: int = 16) -> dict:
    """Design draft 7, 5.3 and 8.2: the decision after the H4 timing. The frozen branch and markets are kept (the defenders
    are frozen); development is the recorded development spend plus the remaining development work (the coverage only),
    each completed item counted once, and stops above the 12 USD cap; the evaluation is recomputed with H4 priced from its
    timing, plus the H4 decision reserve, at the smallest cut within the 40 USD cap; approval is flagged on the new total."""
    spent = sum(float(r["usd"]) for r in ledger.get("spent", []) if r["op"] == "development")
    branch, markets = frozen["branch"], list(frozen["markets"])
    out = {"branch": branch, "markets": markets, "cuts": None, "spent_usd": spent, "h4_reserve_usd": H4_RESERVE_USD, "h4_ratio": _ratio(h4_timing), "stop": None}
    t = cost_table(timings, markets=tuple(markets), branch=branch, vcpu=vcpu)
    out["development_usd"] = spent + t["rows_seconds"]["coverage"] * float(timings["usd_per_pod_hour"]) / 3600.0
    if out["development_usd"] > CAPS["development"]:
        out["stop"] = "development"; return out
    for cuts in range(0, 5):
        ev = cost_table(timings, cuts=cuts, vcpu=vcpu, h4_timing=h4_timing)["evaluation_usd"] + H4_RESERVE_USD
        if ev <= CAPS["evaluation"]:
            out.update(cuts=cuts, evaluation_usd=ev); break
    else:
        out["stop"] = "evaluation"; return out
    out["total_usd"] = out["development_usd"] + out["evaluation_usd"]; out["approval_required"] = out["total_usd"] > CAPS["approval"]
    return out


def plan() -> list[dict]:
    return [{"kind": k, "market": "headline" if k not in ("inner", "inner_x7", "coverage_batch") else "dev0", "rule": "F111"} for k in KINDS]


def _timed(f) -> float:
    t0 = time.perf_counter(); f(); return time.perf_counter() - t0


def stand_in_bank(entries, best_knobs: dict, fam, n: int) -> list[dict]:
    """The n best distinct projected archive points other than the projected best, standing in for the other matched
    rules' attacks in a matched rule's menu; fewer than n is an error."""
    from sim.policies.families import exact_key
    best, seen, out = exact_key(fam.project(best_knobs)), set(), []
    for e in sorted(entries, key=lambda e: -e.f):
        k = fam.project(e.knobs); key = exact_key(k)
        if key != best and key not in seen:
            seen.add(key); out.append(k)
        if len(out) == n:
            return out
    raise SystemExit(f"benchmark: only {len(out)} distinct archive points for a bank of {n}")


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
    from sim.policies.honest import HonestMax
    from sim.records import search_from_json
    from sim.reference import reference_candidates, select_reference
    from sim.search import Objective
    tmp = Path(tempfile.mkdtemp(dir=out)); params = {"cred": {"variant": "thr", "K": 6, "M": None}}; order = tuple(load_locked()["reference_order"])
    mkt = RV.market("headline", RV.DEV_ROOT, 0.2, dev=True, smoke=smoke); ctx = mkt["context"]
    jobs = {f: RV.job(mkt, "F111", f, smoke=smoke, params=params) for f in RV.MENU}
    w1 = RV.job(mkt, "F111", "D2+H3", "W1", smoke=smoke, params=params)
    co = RV.job(mkt, "F111", "X6-SE/v2", "total", 2, "synchronised", smoke=smoke, params=params)
    step = lambda kind, suffix="": {**co, "id": f"{kind}/{ctx}/F111_c2{suffix}", "record_id": f"{kind}/{ctx}/F111_c2{suffix}"}
    inner = TV.SMOKE_INNER if smoke else TV.INNER
    seeds = EPISODE_SEEDS[:2] if smoke else EPISODE_SEEDS; state = {"bank_sizes": {}}
    n_bank = {f: len([o for o in MAN.bank_rules(RV.manifest_ctx(ctx), f, 0, False) if o != "F111"]) for f in RV.MENU}

    def search(f):
        return lambda: RV._run_one("search", jobs[f], str(tmp), 0, True)

    def reference():
        cell = RV.train_cell(jobs["D2+H3"]); groups = {}
        for f, j in jobs.items():
            rec = RV.read(RV.path_of(tmp, j["id"])); T, L = RV.constants(j); fam = RV.family_for(f, T, L)
            b = stand_in_bank(search_from_json(rec["attack"]).archive.values(), rec["attack"]["best_knobs"], fam, n_bank[f]); state["bank_sizes"][f] = len(b)
            for c in reference_candidates(cell, fam, search_from_json(rec["attack"]), search_from_json(rec["twin"]), b, order):
                groups.setdefault(("bank" if c.name.startswith("bank_") else c.name, f), []).append(c)
        cands, fams = RV.merge_menu(groups, RV.MENU); ch = select_reference(cell, cands, SeedCache())
        T, L = RV.constants(jobs["D2+H3"]); idx = next(i for i, c in enumerate(cands) if c is ch.candidate)
        state.update(cands=cands, ref=ch.candidate)
        RV.write(RV.path_of(tmp, f"reference/{ctx}/F111"), {"stage": "reference", "provenance": RV.reference_provenance(jobs["D2+H3"]), "upstream": {},
                                                           "candidates": [RV.cand_to_json(c, f, T, L) for c, f in zip(cands, fams)], "choice": idx,
                                                           "per_seed_normalized": [float(v) for v in ch.per_seed_normalized]})

    def dev_inner_config():
        """One inner configuration on one tuning market through the production scorer: D2, D2+H3, and X7-SC searches,
        the development reference from their menu, and the three evaluations."""
        TV.score_config("C*", {**TV.FIXED, "cred": params["cred"]}, ["dev0"], (*inner, 2 if smoke else 20), False, tmp / "tune_log")

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
            RV.gain_fields(rep(RV.eval_cell(j), seeds=seeds), fam, new.best_knobs, state["ref"], cache)      # the held-out diagnostic (design 6.5)
        return run

    rng = np.random.default_rng(0); B = (2, 99) if smoke else (100, 9999)
    strata = [{s_: rng.normal(0, 1, 10_000) for s_ in C.Q1_STATS} for _ in range(6)]
    ep_cell = Cell(cfg=mkt["cfg"], rule_factory=RV.rule_factory(jobs["D2+H3"]), focal=mkt["focal"], seeds=seeds, name="ep")
    return {"search_d2h3": search("D2+H3"), "search_x7": search("X7-SC"), "reference": reference,
            "eval_d2h3": lambda: RV.stage_evaluate(jobs["D2+H3"], tmp), "eval_x7": lambda: RV.stage_evaluate(jobs["X7-SC"], tmp),
            "w1_search": lambda: RV._run_one("dependent", w1, str(tmp), 0, True), "w1_eval": lambda: RV.stage_evaluate(w1, tmp),
            "coalition_prereqs": lambda: RV.coalition_step("joint_twin", step("joint_twin", "_synchronised"), tmp, [co]),
            "coalition_search": lambda: RV._run_one("dependent", co, str(tmp), 0, True),
            "coalition_reference": lambda: RV.coalition_step("joint_reference_pre", step("joint_reference_pre"), tmp, [co]),
            "coalition_final": lambda: RV.coalition_step("joint_reference", step("joint_reference"), tmp, [co]),
            "coalition_select": lambda: RV.coalition_step("coalition_select", step("coalition_select"), tmp, [co]),
            "coalition_eval": lambda: RV.stage_evaluate(co, tmp),
            "dev_inner_config": dev_inner_config,
            "coverage_batch": lambda: C.miss_counts(strata, "pooled", C.Q1_TAILS, [1.0], B[0], B[1], 1),
            "cross_row": cross_row, "doubling": doubling("D2+H3"), "doubling_x7": doubling("X7-SC"),
            "episode": lambda: run_focal(ep_cell, HonestMax, SeedCache()), "_meta": {"eval_seeds": len(mkt["seeds_eval"]), "episodes": len(seeds),
                                                                                  "coverage_replications": B[0], "state": state, "n_bank": n_bank}}


def measure(out: Path, workers: int, fns: dict | None = None, smoke: bool = False, usd_per_pod_hour: float | None = None) -> dict:
    """Seconds per kind, composed from the components measured in WORKLOADS order. A profit cell is its search and its
    evaluation scaled from the measured dev-val seeds to 40; the reference menu (with its bank) is a kind of its own,
    priced once per (context, rule); W1 is its search and evaluation; a coalition objective half the group's joint twin
    and joint reference (shared by total and min), its search, and its evaluation; `eval160` holds each kind's 160
    further evaluation seeds; an inner development configuration-market as measured, a recheck composed of two D2+H3-cost
    searches (D2 and D2+H3), an X7-SC search, a reference menu, and three 20-seed evaluations (an upper bound: the
    evaluation searches run corner controls and the evaluation menu carries the bank, the development ones do not);
    the cross row and doublings as measured."""
    f = fns if fns is not None else _default_fns(Path(out), smoke)
    missing = [k for k in WORKLOADS if k not in f]
    if missing:
        raise SystemExit(f"benchmark workloads missing: {missing}")
    meta = f.get("_meta", {}); n_eval = int(meta.get("eval_seeds", EVAL_SEEDS)); n_ep = int(meta.get("episodes", len(EPISODE_SEEDS)))
    t0 = time.perf_counter(); r = {k: _timed(f[k]) for k in WORKLOADS}; wall = time.perf_counter() - t0
    to40 = 40 / n_eval
    t = {"d2h3_cell": r["search_d2h3"] + to40 * r["eval_d2h3"], "x7_cell": r["search_x7"] + to40 * r["eval_x7"], "reference": r["reference"],
         "coalition_reference": r["coalition_reference"], "coalition_final": r["coalition_final"], "coalition_select": r["coalition_select"],
         "doubling_includes_heldout": True,
         "w1": r["w1_search"] + to40 * r["w1_eval"], "coalition_total": r["coalition_prereqs"] / 2 + r["coalition_search"] + to40 * r["coalition_eval"],
         "dev_inner_config": r["dev_inner_config"],
         "dev_recheck_config": 2 * r["search_d2h3"] + r["search_x7"] + r["reference"] + 3 * r["eval_d2h3"] * 20 / n_eval,
         "cross_row": r["cross_row"] * EVAL_SEEDS / n_ep,
         "doubling": r["doubling"], "doubling_x7": r["doubling_x7"], "episode": r["episode"] / n_ep,
         "bootstrap_batch": r["coverage_batch"] * (30_000 / int(meta.get("coverage_replications", 100))) * 2}
    to160 = (FINAL_SEEDS - 40) / n_eval
    t["eval160"] = {"profit": to160 * r["eval_d2h3"], "x7": to160 * r["eval_x7"], "welfare": to160 * r["w1_eval"], "coalition": to160 * r["coalition_eval"]}
    to200, x7 = FINAL_SEEDS / n_eval, r["search_x7"] / max(r["search_d2h3"], 1e-12)
    t["task_seconds"] = {"search": {"profit": r["search_d2h3"], "x7": r["search_x7"], "W0": r["w1_search"], "W0_x7": r["w1_search"] * x7},
                         "reference": r["reference"], "W1": r["w1_search"], "W1_x7": r["w1_search"] * x7, "prereqs": r["coalition_prereqs"],
                         "coalition": r["coalition_search"], "coalition_reference": r["coalition_reference"], "coalition_final": r["coalition_final"],
                         "coalition_select": r["coalition_select"],
                         "evaluate": {"profit": to200 * r["eval_d2h3"], "x7": to200 * r["eval_x7"], "welfare": to200 * r["w1_eval"], "coalition": to200 * r["coalition_eval"],
                                      "diagnostic": FINAL_SEEDS * r["episode"] / n_ep},
                         "cross_item": 8 * t["cross_row"] * FINAL_SEEDS / EVAL_SEEDS, "doubling": r["doubling"], "doubling_x7": r["doubling_x7"]}
    t["components"] = r; t["bank_sizes"] = dict(meta.get("state", {}).get("bank_sizes", {}))
    from scripts.revision_v2 import git_commit
    t.update(vcpu=int(workers), usd_per_pod_hour=usd_per_pod_hour, markets=["headline", "dev0"], commit=git_commit(), wall_seconds=wall, smoke=bool(smoke))
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--table", default=None)
    g.add_argument("--decide", default=None, help="timings.json: write the design 8.2 decision once, with a ledger snapshot")
    g.add_argument("--decide-h4", dest="decide_h4", default=None, help="the H4 timing export record: write the decision after the H4 timing once")
    ap.add_argument("--timings", default=None); ap.add_argument("--frozen", default=None, help="the promoted decision.json")
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--out", default="."); ap.add_argument("--workers", type=int, default=1); ap.add_argument("--dry-run", dest="dry_run", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="the same workloads at the smoke budget (wiring check; not a cost estimate)")
    ap.add_argument("--usd-per-core-hour", dest="rate", type=float, default=0.108)
    ap.add_argument("--usd-per-pod-hour", dest="pod_rate", type=float, default=None, help="the pod's measured price (runpod.py list); bills pod time")
    a = ap.parse_args(argv)
    if a.decide:
        import hashlib
        target = Path(a.out)
        if target.exists():
            raise SystemExit(f"{target} exists: the decision is written once")
        raw = Path(a.decide).read_bytes(); ledger = json.loads(Path(a.ledger).read_text())
        tm = json.loads(raw)["timings"]
        d = {"decision": choose(tm, ledger, vcpu=int(tm.get("vcpu") or 16)), "ledger": ledger,
             "timings_sha256": hashlib.sha256(raw).hexdigest()}
        target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(d, indent=1, default=float))
        print(json.dumps(d["decision"], default=float))
        return 0
    if a.decide_h4:
        import hashlib
        target = Path(a.out)
        if target.exists():
            raise SystemExit(f"{target} exists: the decision after the H4 timing is written once")
        if not (a.timings and a.frozen and a.ledger):
            raise SystemExit("--decide-h4 needs --timings, --frozen, and --ledger")
        raw, fr = Path(a.timings).read_bytes(), Path(a.frozen).read_bytes()
        tm = json.loads(raw)["timings"]; ledger = json.loads(Path(a.ledger).read_text()); h4 = json.loads(Path(a.decide_h4).read_text())
        d = {"decision": choose_after_h4(tm, ledger, json.loads(fr)["decision"], h4, vcpu=int(tm.get("vcpu") or 16)), "ledger": ledger, "h4_timing": h4,
             "timings_sha256": hashlib.sha256(raw).hexdigest(), "frozen_sha256": hashlib.sha256(fr).hexdigest()}
        target.parent.mkdir(parents=True, exist_ok=True); target.write_text(json.dumps(d, indent=1, default=float))
        print(json.dumps(d["decision"], default=float))
        return 0
    if a.table:
        d = json.loads(Path(a.table).read_text())
        print(json.dumps(cost_table(d["timings"], float(d.get("usd_per_core_hour", a.rate))), default=float))
        return 0
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "benchmark_plan.json").write_text(json.dumps({"kinds": plan(), "workers": a.workers}))
    if a.dry_run:
        return 0
    t = measure(out, a.workers, smoke=a.smoke, usd_per_pod_hour=a.pod_rate)
    (out / "timings.json").write_text(json.dumps({"timings": t, "usd_per_core_hour": a.rate, "smoke": a.smoke}))
    table = cost_table(t, vcpu=a.workers) if a.pod_rate else cost_table(t, a.rate)
    (out / "cost_table.json").write_text(json.dumps(table, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
