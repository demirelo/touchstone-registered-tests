"""Decision-stability check for the 1-ulp deviation (author's board decision, 2026-11-04). Re-evaluates, on the
registration platform (the author's arm64 Mac) with the registered configurations of instances.json, the frozen policies
of every fresh-market cell that Q1 and Q4 use, against the frozen references, and compares per-seed gains and every
Q1 and Q4 decision with the report. The frozen search and reference records are read, never rewritten.

Usage: stability.py --checkout CHECKOUT --records EVAL/all --instances instances.json --h4 h4.json --protocol protocol-v2.yaml
       --report report.json --work DIR --out stability.json [--workers N]
"""
import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

FRESH = tuple(f"fresh{i}" for i in range(6))
RULES = ("F000", "F111", "C*")
FAMS = ("D2+H3", "X7-SC")


def compare(old: dict, new: dict) -> list[str]:
    """Decision fields that differ between the report's Q1/Q4 and the re-evaluated ones (estimates may move)."""
    diffs = []
    for name, t in old["q1"]["tests"].items():
        for k in ("category", "reject", "efficiency", "better"):
            if t.get(k) != new["q1"]["tests"][name].get(k):
                diffs.append(f"q1 {name} {k}: {t.get(k)!r} -> {new['q1']['tests'][name].get(k)!r}")
    for k in ("k", "passing", "failing", "undecided", "decided"):
        if old["q4"].get(k) != new["q4"].get(k):
            diffs.append(f"q4 {k}: {old['q4'].get(k)!r} -> {new['q4'].get(k)!r}")
    return diffs


def _setup(checkout: str):
    co = Path(checkout).resolve(); sys.path[:0] = [str(co / "scripts"), str(co)]
    import os; os.chdir(co)


def _evaluate(args):
    checkout, records, job, work = args
    _setup(checkout)
    import revision_v2 as RV
    p = Path(work) / (RV._safe(job["id"]) + ".json")
    if p.exists():
        return job["id"], "cached"
    rec = RV.stage_evaluate(job, Path(records))
    p.write_text(json.dumps(rec, default=float))
    return job["id"], "done"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for k in ("--checkout", "--records", "--instances", "--h4", "--protocol", "--report", "--work", "--out"):
        ap.add_argument(k, required=True)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args(argv)
    records, work = Path(a.records).resolve(), Path(a.work).resolve(); work.mkdir(parents=True, exist_ok=True)
    inst = json.loads(Path(a.instances).read_text()); dec = json.loads(Path(a.h4).read_text())
    report = json.loads(Path(a.report).read_text())
    import yaml
    protocol = yaml.safe_load(Path(a.protocol).read_text())
    _setup(a.checkout)
    import revision_v2 as RV
    import report_v2 as RP
    from sim.records import cfg_from_dict
    cfgs = {k: cfg_from_dict(v["calibrated_cfg"]) for k, v in inst["markets"].items()}
    root = json.loads((Path(a.instances).parent / "draw.json").read_text())["hash"]
    h4 = {"dir": None, "sha": dec["bundle_sha256"]} if dec.get("loaded") else None
    catalog = RV.build_jobs(list(FRESH) + ["headline"], root, False, False, json.loads(Path("experiments/v2/params.json").read_text()),
                            int(protocol.get("cuts", 3)), h4, not dec.get("loaded"), cfgs, None, inst["salt_sha256"])
    want = {RV.cell_id(f"{m}@rho0.2", r, f, "profit") for m in FRESH for r in RULES for f in FAMS}
    jobs = [j for j in catalog if j["id"] in want]
    if len(jobs) != len(want):
        raise SystemExit(f"stability: {len(want) - len(jobs)} cells not in the catalog")
    with ProcessPoolExecutor(a.workers) as ex:
        for rid, st in ex.map(_evaluate, [(a.checkout, str(records), j, str(work)) for j in jobs]):
            print(rid, st, flush=True)

    class Mixed(RP.Records):                      # the re-evaluated cells, every other cell as recorded
        def rec(self, rid):
            if rid in want:
                return json.loads((work / (RV._safe(rid) + ".json")).read_text())
            return super().rec(rid)

    R = Mixed(records, catalog, set(report["missing"]), set(report["search_flagged"]))
    kappa = protocol.get("kappa") or {}
    new = {"q1": RP.q1(R, kappa.get("Q1"), True), "q4": RP.q4(R, kappa.get("Q4"), True)}
    cells = {}
    for rid in sorted(want):
        g_old = np.asarray(json.loads(RV.eval_path(records, rid).read_text())["gain"], dtype=float)
        g_new = np.asarray(json.loads((work / (RV._safe(rid) + ".json")).read_text())["gain"], dtype=float)
        cells[rid] = {"max_abs_seed_diff": float(np.max(np.abs(g_new - g_old))), "seeds_changed": int(np.sum(g_new != g_old)),
                      "mean_old": float(g_old.mean()), "mean_new": float(g_new.mean())}
    diffs = compare(report, new)
    res = {"platform": "registration platform (arm64), registered configurations", "cells": cells, "decision_diffs": diffs,
           "decisions_unchanged": not diffs, "q1_new": new["q1"]["tests"], "q4_new": {k: new["q4"][k] for k in ("k", "passing", "failing")}}
    Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(f"decisions unchanged: {not diffs}; cells with any seed changed: {sum(1 for c in cells.values() if c['seeds_changed'])} of {len(cells)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
