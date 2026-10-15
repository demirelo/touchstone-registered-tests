"""Run the coverage study (spec 8) on the sweep's reference records: validate the 18-cell universe against the current
calibration and tuned parameters, select 6 cells (ruling D12), compute thresholds with their simulation check, run the
joint fixture test and the power check with the registered remedies per n, run the pools and replications in chunks
(n = 10 and n = 20 first; n = 40 only when the remedy order reaches it), admit the procedures, and write the report."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import SMOKE_BUDGET, check_bank_record, check_record, job_for, load_bank_doc, load_params, make_cell, read_dir, train_val  # noqa: E402
from sim.calibrate import load_calibration  # noqa: E402
from sim.cell import SeedCache, run_focal  # noqa: E402
from sim.coverage import (BASE_N, CONDITIONAL_N, CoverageCellSpec, STATISTICS, PROCEDURES_AT_N, admission, fixture_and_power, measure, observe,  # noqa: E402
                          reference_interval, runs_per_seed, sarle_bimodality, seed_blocks, select_cells, skewness, thresholds, write_report)
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash  # noqa: E402
from sim.manifest import enumerate_manifest  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.records import cfg_from_dict  # noqa: E402
from sim.reference import participant_diagnostics  # noqa: E402
from sim.registry import available_families  # noqa: E402
from sim.rng import load_identity_salt  # noqa: E402
from sim.schedule import budget_from_locked  # noqa: E402


def validated_universe(sweep_out: Path, locked: dict, cal, tuned_dir: Path | None, smoke: bool) -> dict:
    """The 18 development cells at beta_headline with their reference records, each checked by the sweep's own
    check_record against a job rebuilt from the current calibration and tuned parameters (stale, foreign, or smoke
    records are refused in registered mode)."""
    budget = SMOKE_BUDGET if smoke else budget_from_locked(locked); base = market_config_from_locked(locked)
    rules = ["B1", "B2", "B3"]
    params = {r: load_params(r, tuned_dir, smoke, cal.market_key, settings_hash(locked), cal.seeds) for r in rules}
    specs = [c for c in enumerate_manifest(locked, rules, budget=budget) if c.section == "development" and float(c.beta) == float(locked["beta_headline"])]
    refs = read_dir(sweep_out / "reference"); out = {}
    for spec in specs:
        job = job_for(spec, locked, cal, base, params[spec.rule], budget, smoke)
        rec = refs.get(spec.name)
        if rec is None:
            raise SystemExit(f"{spec.name}: no reference record in {sweep_out}/reference")
        check_record(job, rec)
        if rec.get("smoke") and not smoke:
            raise SystemExit(f"{spec.name}: smoke record in a registered run")
        out[spec.name] = (job, rec)
    if len(out) != 18:
        raise SystemExit(f"expected 18 development cells at beta_headline, found {len(out)}")
    return out


def cell_statistics(job: dict, rec: dict) -> dict:
    gain = np.array(rec["attack_per_seed_normalized"]) - np.array(rec["reference_per_seed_normalized"])
    train, _, _ = train_val(job); fam = available_families()[job["spec"]["family"]]
    cell = make_cell(job, train); res = run_focal(cell, lambda: fam.make(dict(rec["attack_knobs"])), SeedCache()).results
    bans = np.array([participant_diagnostics(r, cell.cfg, cell.focal)["focal_bans"] for r in res], dtype=float)
    return {"skew_gain": skewness(gain), "sarle_bans": sarle_bimodality(bans), "n_train": int(len(gain))}


def build_spec(name: str, universe: dict) -> CoverageCellSpec:
    job, rec = universe[name]; spec = job["spec"]
    params, knobs = {}, {}
    for rule in ("B1", "B2", "B3"):
        pj, pr = next(v for v in universe.values() if v[0]["spec"]["rule"] == rule and v[0]["spec"]["family"] == spec["family"] and v[0]["spec"]["position"] == spec["position"])
        params[rule] = pj["params"]; knobs[rule] = pr["attack_knobs"]
    cand = rec["candidate"]
    return CoverageCellSpec(name=name, cfg=job["cfg"], focal=positions(cfg_from_dict(job["cfg"]))[spec["position"]], rule=spec["rule"], family=spec["family"],
                            params_by_rule=params, attack_knobs_by_rule=knobs, ref_candidate=None if cand["name"] == "abstain" else cand)


def provenance_hash(provenance: dict) -> str:
    """The run-level inputs every cell shares (settings and salt hashes, calibration, tuned, and reference-record hashes)."""
    return hashlib.sha256(json.dumps({k: v for k, v in provenance.items() if k != "sweep_out"}, sort_keys=True).encode()).hexdigest()


def input_hash(spec: CoverageCellSpec, provenance: dict) -> str:
    """Binds saved observations to everything that determines them: the cell specification (market, rules, parameters,
    attack knobs, reference candidate) and the run's provenance (settings hash, salt hash, calibration and tuned hashes,
    reference-record hashes). Cached data with another hash is never reused."""
    from dataclasses import asdict
    return hashlib.sha256(json.dumps({"spec": asdict(spec), "provenance": {k: v for k, v in provenance.items() if k != "sweep_out"}}, sort_keys=True, default=float).encode()).hexdigest()


def pool_observations(spec: CoverageCellSpec, pool: np.ndarray, out: Path, index: int, workers: int, key: str) -> tuple:
    """The pool is observed once per cell and saved under its input hash; a longer request extends the saved file with
    only its missing seeds, a shorter request returns the prefix; every n reads it back. Returns the observations for the
    requested seeds and the number of newly executed seeds."""
    path = out / f"pool_{index}.npz"; have: dict = {}; have_seeds = np.zeros(0, dtype=np.int64)
    if path.exists():
        d = np.load(path)
        if str(d["input_hash"]) != key:
            raise SystemExit(f"{path}: saved under another input hash (other parameters, records, or salt); use a fresh --out")
        have_seeds = d["seeds"]; have = {s: d[s] for s in STATISTICS}
    k = min(len(have_seeds), len(pool))
    if k and not np.array_equal(have_seeds[:k], pool[:k]):
        raise SystemExit(f"{path}: the saved pool does not match the registered seed layout")
    new = pool[len(have_seeds):]
    if len(new):
        add = observe(spec, new, workers=workers)
        have = {s: np.concatenate([have.get(s, np.zeros(0)), add[s]]) for s in STATISTICS}; have_seeds = np.concatenate([have_seeds, new])
        np.savez(path, seeds=have_seeds, input_hash=key, **have)
    return {s: have[s][:len(pool)] for s in STATISTICS}, int(len(new))


def run_cell(args) -> tuple:
    name, spec, locked, index, pool_factor, rep_factor, n_list, smoke, out, workers, provenance = args
    out = Path(out); settings = dict(locked["intervals"]); key = input_hash(spec, provenance)
    if smoke:
        settings["bootstrap_resamples"] = 200
    pool, reps = seed_blocks(locked, index, pool_factor, rep_factor, n_list=n_list)
    if smoke:
        pool = pool[:200]; reps = {n: r[:20] for n, r in reps.items()}
    pobs, new_pool_seeds = pool_observations(spec, pool, out, index, workers, key)
    refs = {s: reference_interval(pobs[s], float(locked["intervals"]["reference_level"])) for s in STATISTICS}
    measured = {}; degenerate = {}
    for n, S in reps.items():
        flat = observe(spec, S.ravel(), workers=workers)
        samples = {s: flat[s].reshape(S.shape) for s in STATISTICS}
        measured.update(measure(samples, {s: refs[s][:2] for s in STATISTICS}, int(n), PROCEDURES_AT_N[int(n)], settings))
        degenerate[str(n)] = {s: float(np.mean(samples[s].std(axis=1) == 0.0)) for s in STATISTICS}     # share of replications with identical values
    return name, {"measured": measured, "pool_mean": {s: float(pobs[s].mean()) for s in STATISTICS}, "pool_se": {s: refs[s][2] for s in STATISTICS},
                  "pool_size": int(len(pool)), "replications": {str(n): int(S.shape[0]) for n, S in reps.items()},
                  "replication_se": {str(n): float(np.sqrt(0.95 * 0.05 / S.shape[0])) for n, S in reps.items()}, "degenerate_share": degenerate,
                  "runs": runs_per_seed(spec) * sum(S.size for S in reps.values()), "pool_runs": runs_per_seed(spec) * new_pool_seeds,
                  "pool_factor": pool_factor, "rep_factor": rep_factor, "input_hash": key, "provenance_hash": provenance_hash(provenance)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep-out", dest="sweep_out", required=True); ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--out", required=True)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--select-only", dest="select_only", action="store_true"); ap.add_argument("--force-n40", dest="force_n40", action="store_true")
    ap.add_argument("--cell", type=int, default=None, help="run only this selected cell (0 to 5) and write cell_<i>.json; merge later with --merge")
    ap.add_argument("--merge", action="store_true", help="read cell_*.json from --out, run the fixture and power step, admit, and write the report")
    ap.add_argument("--register", action="store_true", help="copy the selection to experiments/coverage_cells.json for the manifest")
    a = ap.parse_args()
    lk = load_locked(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True); cal = load_calibration(a.calibration)
    tuned = Path(a.tuned_dir) if a.tuned_dir else None
    universe = validated_universe(Path(a.sweep_out), lk, cal, tuned, a.smoke)
    if not a.smoke:
        if list(cal.seeds) != list(locked_seeds(lk, "calibration")):
            raise SystemExit("the calibration must use the full calibration namespace")
        bank = load_bank_doc(Path(a.sweep_out))
        for name, (job, rec) in universe.items():
            check_bank_record(rec, bank, "coverage")
            if len(rec["attack_per_seed_normalized"]) != job["budget"][2] or len(rec["reference_per_seed_normalized"]) != job["budget"][2]:
                raise SystemExit(f"{name}: the record's dev-train vectors are not the full n_train = {job['budget'][2]}")
    stats_by_cell = {name: cell_statistics(job, rec) for name, (job, rec) in universe.items()}
    if a.smoke:
        chosen = sorted(universe)[:6]; unranked = True
    else:
        if any(v["n_train"] < 4 for v in stats_by_cell.values()):
            raise SystemExit("the ranking statistics need at least 4 dev-train seeds per cell")
        chosen = select_cells(stats_by_cell, k=3); unranked = False
        if len(chosen) != 6:
            raise SystemExit(f"the selection rule produced {len(chosen)} cells, not 6")
    specs = {name: build_spec(name, universe) for name in chosen}
    selection = [{"name": n, "rule": universe[n][0]["spec"]["rule"], "family": universe[n][0]["spec"]["family"], "position": universe[n][0]["spec"]["position"],
                  "runs_per_seed": runs_per_seed(specs[n]), **stats_by_cell[n]} for n in chosen]
    (out / "coverage_cells.json").write_text(json.dumps(selection, indent=1))
    if a.register:
        shutil.copy(out / "coverage_cells.json", "experiments/coverage_cells.json")
    print("selected: " + ", ".join(chosen) + (" (SMOKE, unranked)" if unranked else ""))
    if a.select_only:
        return
    provenance = {"settings_hash": settings_hash(lk), "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest(), "calibration_sha256": hashlib.sha256(Path(a.calibration).read_bytes()).hexdigest(),
                  "tuned_sha256": {r: hashlib.sha256((tuned / f"tuned_{r}.json").read_bytes()).hexdigest() for r in ("B1", "B2", "B3")} if tuned else None,
                  "reference_records_sha256": {n: hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest() for n, (_, rec) in sorted(universe.items())}, "sweep_out": str(a.sweep_out)}
    rng = np.random.default_rng(int(lk["intervals"]["bootstrap_seed"]))
    all_n = list(BASE_N) + list(CONDITIONAL_N)
    fp = fixture_and_power(lk, a.smoke, rng, all_n)             # the gates for every n, once, in one fixed order: identical on every machine and on every path
    n_list = list(CONDITIONAL_N) if (a.force_n40 and a.cell is not None and (out / f"cell_{a.cell}.json").exists()) else list(BASE_N) + (list(CONDITIONAL_N) if a.force_n40 else [])
    results: dict = {}; thr_by_n: dict = {}
    my_cells = [chosen[a.cell]] if a.cell is not None else list(chosen)

    def run_ns(ns):
        for n in ns:
            rem = fp["remedies"][str(n)]; M = fp["base_M"] * rem["pool_factor"]; thr_by_n[int(n)] = thresholds(lk, M)
            chunk_workers = a.workers if len(my_cells) == 1 else 1              # one cell: parallelize its chunks; many cells: one process per cell
            jobs = [(name, specs[name], lk, chosen.index(name), rem["pool_factor"], rem["rep_factor"], (int(n),), a.smoke, out, chunk_workers, provenance) for name in my_cells]
            got = dict(ProcessPoolExecutor(a.workers).map(run_cell, jobs)) if (a.workers > 1 and len(my_cells) > 1) else dict(map(run_cell, jobs))
            for name, r in got.items():
                results.setdefault(name, {"measured": {}, "runs": 0, "pool_runs": 0, "per_n": {}, "input_hash": r["input_hash"], "provenance_hash": r["provenance_hash"]})
                results[name]["measured"].update(r["measured"]); results[name]["runs"] += r["runs"]; results[name]["pool_runs"] += r["pool_runs"]   # executed work is summed
                results[name]["per_n"][str(n)] = {k: v for k, v in r.items() if k != "measured"}

    def needs_n40(adm):
        return adm["method_at_n"]["20"] is None and 40 not in thr_by_n and not a.smoke

    prov_key = {"selection": chosen, "smoke": bool(a.smoke), **{k: v for k, v in provenance.items() if k != "sweep_out"}}
    if a.merge:
        for pth in sorted(out.glob("cell_*.json")):
            doc = json.loads(pth.read_text())
            if doc.get("provenance") != prov_key:
                diff = sorted(k for k in set(prov_key) | set(doc.get("provenance") or {}) if (doc.get("provenance") or {}).get(k) != prov_key.get(k))
                raise SystemExit(f"{pth.name}: provenance differs from this run in {diff} (selection, smoke flag, settings, salt, calibration, tuned, reference-record hashes)")
            results.update(doc["results"]); thr_by_n.update({int(k): v for k, v in doc["thr_by_n"].items()})
        missing = [c for c in chosen if c not in results]
        if missing:
            raise SystemExit(f"--merge: no cell_*.json for {missing}")
        n_sets = {name: tuple(sorted(r["per_n"])) for name, r in results.items()}
        if len(set(n_sets.values())) != 1:
            raise SystemExit(f"--merge: the cells do not hold the same sample sizes: {n_sets}")
        for name, r in results.items():
            for n, pn in r["per_n"].items():
                rem = fp["remedies"][str(n)]
                if (pn["pool_factor"], pn["rep_factor"]) != (rem["pool_factor"], rem["rep_factor"]):
                    raise SystemExit(f"{name} at n = {n}: ran with factors {(pn['pool_factor'], pn['rep_factor'])}, the gates select {(rem['pool_factor'], rem['rep_factor'])}")
    else:
        if a.cell is not None and (out / f"cell_{a.cell}.json").exists():
            prev = json.loads((out / f"cell_{a.cell}.json").read_text())
            if prev.get("provenance") != prov_key:
                raise SystemExit(f"cell_{a.cell}.json exists with other provenance (selection, smoke flag, settings, salt, calibration, tuned, or reference-record hashes); use a fresh --out")
            results.update(prev["results"]); thr_by_n.update({int(k): v for k, v in prev["thr_by_n"].items()})
            n_list = [n for n in n_list if str(n) not in results[chosen[a.cell]]["per_n"]]      # a rerun never repeats an n the file already holds
        run_ns(n_list)
        adm0 = admission({n: r["measured"] for n, r in results.items()}, thr_by_n, lk, fp["admissible_n"]) if a.cell is None else None
        if a.cell is None and needs_n40(adm0):
            run_ns([40])                                          # the gates for n = 40 are already in fp
        if a.cell is not None:
            (out / f"cell_{a.cell}.json").write_text(json.dumps({"results": results, "thr_by_n": {str(k): v for k, v in thr_by_n.items()}, "cell": chosen[a.cell], "provenance": prov_key}, default=float))
            print(f"wrote {out / f'cell_{a.cell}.json'}; after all six cells exist run --merge (if the merge reports inconclusive at n = 20, rerun each cell with --force-n40, then --merge again)")
            return
    adm = admission({n: r["measured"] for n, r in results.items()}, thr_by_n, lk, fp["admissible_n"])
    if a.merge and needs_n40(adm):
        print("the n = 20 procedures are not admitted: rerun every cell with --cell i --force-n40, then --merge again", file=sys.stderr)
    report = {"smoke": bool(a.smoke), "unranked": unranked, "admission_basis": "smoke (not an admission)" if a.smoke else "registered", "selection": selection,
              "statistics": stats_by_cell, "thresholds": {str(n): t for n, t in thr_by_n.items()}, "fixture_and_power": fp, "cells": results, **adm,
              "provenance": provenance, "provenance_hash": provenance_hash(provenance), "manifest_runs": sum(r["runs"] + r["pool_runs"] for r in results.values())}
    h = write_report(out / "coverage_report.json", report)
    print(json.dumps({"sha256": h, "method_at_n": adm["method_at_n"], "consequences": adm["consequences"], "runs": report["manifest_runs"]}))


if __name__ == "__main__":
    main()
