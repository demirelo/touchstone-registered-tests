"""Amendment 1: the coverage extension for the paired H3 statistic gain_diff on the six registered cells, with B3 standing
in for R* against B2 (consensus of Sol high and Astra high, 2026-10-17). Validates the universe exactly as the base study
does, recomputes every provenance hash from the inputs it actually uses and refuses any difference from the base report,
runs the gate for the 12 extension endpoints at n = 40, observes the pool and the replications in chunks (one cell per
machine with --cell i), and merges the six cell files into coverage_report_amendment.json. Nothing here edits
experiments/locked.yaml or any registered artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.coverage_study import cell_statistics, provenance_hash, validated_universe  # noqa: E402
from scripts.sweep import check_bank_record, load_bank_doc  # noqa: E402
from sim.amendment import (AMEND_N, AMEND_STATISTICS, LIMITATION, CoverageExtSpec, admission_ext, amendment_hash, fixture_and_power_ext,  # noqa: E402
                           load_amendment, measure_ext, observe_ext, runs_per_seed_ext, seed_blocks_ext)
from sim.calibrate import load_calibration  # noqa: E402
from sim.coverage import reference_interval, select_cells, thresholds, write_report  # noqa: E402
from sim.locked import load_locked, seeds as locked_seeds, settings_hash  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.records import cfg_from_dict  # noqa: E402
from sim.rng import load_identity_salt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
PROVENANCE_KEYS = ("settings_hash", "salt_hash", "calibration_sha256", "tuned_sha256", "reference_records_sha256")


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_ext_spec(name: str, universe: dict, pair=("B2", "B3")) -> CoverageExtSpec:
    """The cell's market and focal position with, for each rule of the pair, that rule's locked parameters, its frozen
    attack knobs, and its selected reference candidate at the same family and position (None when it abstains)."""
    job, _ = universe[name]; spec = job["spec"]; params, knobs, refs = {}, {}, {}
    for rule in pair:
        pj, pr = next(v for v in universe.values() if v[0]["spec"]["rule"] == rule and v[0]["spec"]["family"] == spec["family"] and v[0]["spec"]["position"] == spec["position"])
        params[rule] = pj["params"]; knobs[rule] = pr["attack_knobs"]; cand = pr["candidate"]
        refs[rule] = None if cand["name"] == "abstain" else cand
    return CoverageExtSpec(name=name, cfg=job["cfg"], focal=positions(cfg_from_dict(job["cfg"]))[spec["position"]], family=spec["family"],
                           params_by_rule=params, attack_knobs_by_rule=knobs, ref_candidate_by_rule=refs, pair=tuple(pair))


def ext_provenance(universe: dict, base_report: dict, amend_doc: dict, selection: list, lk: dict, calibration, tuned) -> dict:
    """Measured, never copied: the hashes of the inputs this run actually uses; the caller refuses any difference from the base report."""
    return {"settings_hash": settings_hash(lk), "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest(), "calibration_sha256": sha(calibration),
            "tuned_sha256": {r: sha(Path(tuned) / f"tuned_{r}.json") for r in ("B1", "B2", "B3")} if tuned else None,
            "reference_records_sha256": {n: hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest() for n, (_, rec) in sorted(universe.items())},
            "base_report_sha256": base_report["_sha256"], "amendment_sha256": amendment_hash(amend_doc), "selection": list(selection)}


def input_hash_ext(spec: CoverageExtSpec, provenance: dict) -> str:
    return hashlib.sha256(json.dumps({"spec": asdict(spec), "provenance": provenance}, sort_keys=True, default=float).encode()).hexdigest()


def pool_observations_ext(spec: CoverageExtSpec, pool: np.ndarray, out: Path, index: int, workers: int, key: str) -> tuple:
    """The pool is observed once per cell under its input hash; a longer request extends the file with the missing seeds
    only, a shorter request returns the prefix. Returns the observations for the requested seeds and the new seed count."""
    path = Path(out) / f"poolx_{index}.npz"; have: dict = {}; have_seeds = np.zeros(0, dtype=np.int64)
    if path.exists():
        d = np.load(path)
        if str(d["input_hash"]) != key:
            raise SystemExit(f"{path}: saved under another input hash (other parameters, records, base report, amendment, or salt); use a fresh --out")
        have_seeds = d["seeds"]; have = {s: d[s] for s in AMEND_STATISTICS}
    k = min(len(have_seeds), len(pool))
    if k and not np.array_equal(have_seeds[:k], pool[:k]):
        raise SystemExit(f"{path}: the saved pool does not match the registered seed layout")
    new = pool[len(have_seeds):]
    if len(new):
        add = observe_ext(spec, new, workers=workers)
        have = {s: np.concatenate([have.get(s, np.zeros(0)), add[s]]) for s in AMEND_STATISTICS}; have_seeds = np.concatenate([have_seeds, new])
        np.savez(path, seeds=have_seeds, input_hash=key, **have)
    return {s: have[s][:len(pool)] for s in AMEND_STATISTICS}, int(len(new))


def run_cell_ext(args) -> tuple:
    name, spec, locked, index, pool_factor, rep_factor, smoke, out, workers, provenance, amend = args
    settings = dict(locked["intervals"]); key = input_hash_ext(spec, provenance)
    if smoke:
        settings["bootstrap_resamples"] = 200
    pool, reps = seed_blocks_ext(amend, index, pool_factor, rep_factor)
    if smoke:
        pool = pool[:200 * pool_factor]; reps = reps[:20 * rep_factor]
    pobs, new_pool_seeds = pool_observations_ext(spec, pool, out, index, workers, key)
    refs = {s: reference_interval(pobs[s], float(locked["intervals"]["reference_level"])) for s in AMEND_STATISTICS}
    flat = observe_ext(spec, reps.ravel(), workers=workers); samples = {s: flat[s].reshape(reps.shape) for s in AMEND_STATISTICS}
    measured = measure_ext(samples, {s: refs[s][:2] for s in AMEND_STATISTICS}, AMEND_N, settings)
    degenerate = {s: float(np.mean((samples[s] == samples[s][:, :1]).all(axis=1))) for s in AMEND_STATISTICS}
    return name, {"measured": measured, "pool_mean": {s: float(pobs[s].mean()) for s in AMEND_STATISTICS}, "pool_se": {s: refs[s][2] for s in AMEND_STATISTICS},
                  "pool_size": int(len(pool)), "replications": {str(AMEND_N): int(reps.shape[0])}, "replication_se": {str(AMEND_N): float(np.sqrt(0.95 * 0.05 / reps.shape[0]))},
                  "degenerate_share": degenerate, "runs": runs_per_seed_ext(spec) * int(reps.size), "pool_runs": runs_per_seed_ext(spec) * new_pool_seeds,
                  "pool_factor": int(pool_factor), "rep_factor": int(rep_factor), "input_hash": key, "provenance_hash": provenance_hash(provenance)}


def refuse(msg: str) -> None:
    print("REFUSED: " + msg, file=sys.stderr); sys.exit(2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-out", dest="sweep_out", required=True); ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--amendment", required=True)
    ap.add_argument("--base-report", dest="base_report", required=True); ap.add_argument("--selection", required=True)
    ap.add_argument("--repo", default=str(REPO)); ap.add_argument("--locked", default=None, help="default: experiments/locked.yaml under --repo"); ap.add_argument("--out", required=True)
    ap.add_argument("--cell", type=int, default=None); ap.add_argument("--merge", action="store_true")
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.cell is not None and not 0 <= a.cell <= 5:
        refuse(f"--cell {a.cell} is outside 0..5")
    a.locked = a.locked or str(Path(a.repo) / "experiments" / "locked.yaml")
    lk = load_locked(a.locked); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    amend = load_amendment(a.amendment, lk); cal = load_calibration(a.calibration); tuned = Path(a.tuned_dir) if a.tuned_dir else None
    base = json.loads(Path(a.base_report).read_text()); base["_sha256"] = sha(a.base_report)
    if bool(base.get("smoke")) != bool(a.smoke):
        refuse("smoke flags differ: a smoke base report needs --smoke and a registered base report refuses it")
    if base["_sha256"] != lk.get("coverage_report_sha256"):                       # in smoke mode the synthetic lock copy binds the smoke base report
        refuse(f"base report {a.base_report}: hash differs from the lock's coverage_report_sha256")
    if a.smoke and base.get("admission_basis") == "registered":
        refuse("smoke run on a registered base report")
    universe = validated_universe(Path(a.sweep_out), lk, cal, tuned, a.smoke)
    if not a.smoke:
        if list(cal.seeds) != list(locked_seeds(lk, "calibration")):
            refuse("the calibration must use the full calibration namespace")
        bank = load_bank_doc(Path(a.sweep_out))
        for name, (job, rec) in universe.items():
            check_bank_record(rec, bank, "coverage")
    if a.smoke:
        chosen = sorted(universe)[:6]                                   # the unranked smoke selection of the base script
    else:
        chosen = select_cells({name: cell_statistics(job, rec) for name, (job, rec) in universe.items()}, k=3)
    names_file = [c["name"] for c in json.loads(Path(a.selection).read_text())]; names_base = [c["name"] for c in base.get("selection", [])]
    if chosen != names_file or chosen != names_base:
        refuse(f"selection differs: recomputed {chosen}, --selection {names_file}, base report {names_base}")
    prov = ext_provenance(universe, base, amend, chosen, lk, a.calibration, tuned)
    bp = base.get("provenance") or {}
    for k in PROVENANCE_KEYS:
        if prov.get(k) != bp.get(k):
            refuse(f"{'reference records' if k == 'reference_records_sha256' else k}: this run's inputs differ from the base report's provenance")
    specs = {name: build_ext_spec(name, universe) for name in chosen}
    prov_key = {"selection": chosen, "smoke": bool(a.smoke), **prov}
    rng = np.random.default_rng(int(lk["intervals"]["bootstrap_seed"]))
    fp = fixture_and_power_ext(lk, amend, a.smoke, rng); rem = fp["remedies"][str(AMEND_N)]
    M = fp["base_M"] * rem["pool_factor"]; thr = {AMEND_N: thresholds(lk, M)}
    if a.merge:
        results = {}
        for pth in sorted(out.glob("cellx_*.json")):
            doc = json.loads(pth.read_text())
            if doc.get("provenance") != prov_key:
                refuse(f"{pth.name}: provenance differs from this run; use a fresh --out")
            r = doc["result"]
            if (r["pool_factor"], r["rep_factor"]) != (rem["pool_factor"], rem["rep_factor"]):
                refuse(f"{pth.name}: ran with factors {(r['pool_factor'], r['rep_factor'])}, the gate selects {(rem['pool_factor'], rem['rep_factor'])}")
            results[doc["cell"]] = r
        missing = [c for c in chosen if c not in results]
        if missing:
            refuse(f"--merge: no cellx file for {missing}")
        if len({r["provenance_hash"] for r in results.values()}) != 1:
            refuse("--merge: the cells do not share one provenance hash")
        adm = admission_ext({n: r["measured"] for n, r in results.items()}, thr, lk, fp["admissible_n"], chosen)
        report = {"smoke": bool(a.smoke), "admission_basis": "smoke (not an admission)" if a.smoke else "registered", "selection": [c for c in base["selection"]],
                  "base_report_sha256": base["_sha256"], "amendment_sha256": prov["amendment_sha256"], "cells": results,
                  "thresholds": {str(n): t for n, t in thr.items()}, "fixture_and_power": fp, **adm, "provenance": prov, "provenance_hash": provenance_hash(prov),
                  "limitation": LIMITATION, "manifest_runs": sum(r["runs"] + r["pool_runs"] for r in results.values())}
        h = write_report(out / "coverage_report_amendment.json", report)
        print(json.dumps({"sha256": h, "consequences": adm["consequences"], "runs": report["manifest_runs"]}))
        return
    if a.cell is None:
        refuse("pass --cell i (0 to 5) or --merge")
    name = chosen[a.cell]; path = out / f"cellx_{a.cell}.json"
    if path.exists() and json.loads(path.read_text()).get("provenance") != prov_key:
        refuse(f"{path.name} exists with other provenance; use a fresh --out")
    _, r = run_cell_ext((name, specs[name], lk, a.cell, rem["pool_factor"], rem["rep_factor"], a.smoke, out, a.workers, prov, amend))
    path.write_text(json.dumps({"result": r, "thr": {str(k): v for k, v in thr.items()}, "cell": name, "provenance": prov_key}, default=float))
    print(f"wrote {path} ({r['pool_runs'] // max(runs_per_seed_ext(specs[name]), 1)} new pool seeds)")


if __name__ == "__main__":
    main()
