"""Robustness v1: the pre-stated 292-cell design of experiments/robustness-v1.yaml (Astra high round 2) on the exploratory
runner. Frozen rules; off the headline market the frozen parameters are transferred and labelled (param_transfer: true).
Exploratory and descriptive. Plan: docs/superpowers/plans/2026-10-21-theorem-and-robustness.md Task 3."""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import calibrate, load_calibration, save_calibration
from sim.config import MarketConfig, ProviderParams
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "experiments/robustness-v1.yaml"
CAL_DIR = ROOT / "experiments/robustness"


def doc() -> dict:
    return yaml.safe_load(DOC_PATH.read_text())


def variant(name: str, position: str | None = None) -> dict:
    d = doc(); v = {**d["defaults"], **(d["variants"][name] or {})}
    return {"name": name, "beta": float(v["beta"]), "rho": float(v["rho"]), "N": int(v["N"]), "J": int(v["J"]), "sigma": float(v["sigma"]),
            "T": int(v["T"]), "eta": float(v["eta"]), "position": position or "median"}


def headline_m() -> float:
    return float(load_calibration(ROOT / "experiments/calibration.json").m)


def build_market(v: dict) -> MarketConfig:
    base = market_config_from_locked(load_locked())
    if v["N"] == base.N:
        providers = base.providers
    else:
        arr = doc()["provider_arrays"][v["N"]]
        providers = tuple(ProviderParams(q_max=float(q), a=0.02, b=float(b), k=6) for q, b in zip(arr["q_max"], arr["b"]))
    cfg = MarketConfig(N=v["N"], J=v["J"], T=v["T"], sigma=v["sigma"], e=v["eta"] * headline_m(), v_min=base.v_min, v_max=base.v_max,
                       providers=providers, alpha=base.alpha, budget=base.budget)
    cfg.validate()
    return cfg


def calibration_path(v: dict) -> str:
    if v["name"] == "headline":
        return "experiments/calibration.json"
    p = CAL_DIR / f"cal_{v['name']}.json"
    if not p.exists():
        raise SystemExit(f"no calibration for variant {v['name']}; run scripts/robustness_v1.py --calibrate first")
    return str(p.relative_to(ROOT))


def calibrate_market(v: dict, out_dir: Path | None = None, seeds=None):
    """The frozen calibrate on the variant's own market (seeds 4000 to 4019); the headline variant keeps the registered file."""
    if v["name"] == "headline":
        return "experiments/calibration.json"
    out_dir = Path(out_dir or CAL_DIR); out_dir.mkdir(parents=True, exist_ok=True)
    seeds = list(seeds) if seeds is not None else [int(s) for s in locked_seeds(load_locked(), "calibration")]
    cal = calibrate(build_market(v), seeds)
    p = out_dir / f"cal_{v['name']}.json"; save_calibration(cal, p)
    return cal.as_dict()


def load_transfer_params(rule: str, tuned_dir: Path | None = None) -> tuple[dict, str]:
    """The frozen load_params against the original (headline) market, settings hash, and calibration seeds, so the source
    file is validated before its parameters are transferred."""
    from scripts.sweep import load_params
    lk = load_locked(); cal = load_calibration(ROOT / "experiments/calibration.json")
    td = Path(tuned_dir) if tuned_dir else ROOT / "experiments/tuned"
    params = load_params(rule, td, False, cal.market_key, settings_hash(lk), cal.seeds)
    src = ROOT / "experiments/proposed.yaml" if rule == "proposed" else td / f"tuned_{rule}.json"
    return params, hashlib.sha256(src.read_bytes()).hexdigest()


def cell_id(vname: str, rule: str, family: str, c: int | None, schedule: str | None, position: str) -> str:
    mid = f"_c{c}_{schedule}" if c is not None else ""
    return f"{vname}_{rule}_{family}{mid}_{position}"


def manifest_specs() -> list[dict]:
    d = doc(); rules = d["rules"]; out = []
    dbl = d["doubling"]; dbl_set = {cell_id(v, r, dbl["family"], None, None, dbl["position"]) for v in dbl["variants"] for r in dbl["rules"]}
    for axis, a in d["axes"].items():
        fams = d["core_families"] if a["families"] == "core" else a["families"]
        for v in a["variants"]:
            for pos in a["positions"]:
                for f in fams:
                    profiles = [tuple(p) for p in a["x6_profiles"]] if f == "X6-SE" else [(None, None)]
                    for r in rules:
                        for c, sch in profiles:
                            cid = cell_id(v, r, f, c, sch, pos)
                            out.append({"id": cid, "axis": axis, "variant": v, "position": pos, "rule": r, "family": f, "c": c,
                                        "schedule": sch, "doubling": cid in dbl_set})
    return out


def jobs_for(specs: list[dict], smoke: bool) -> list[dict]:
    from scripts.explore_attackers import job_for_x
    jobs = []
    for s in specs:
        j = job_for_x(s["rule"], s["family"], s["c"], smoke, variant=variant(s["variant"], s["position"]), schedule=s["schedule"])
        j["doubling"] = bool(s["doubling"]); j["axis"] = s["axis"]
        jobs.append(j)
    return jobs


def assign_banks(jobs: list[dict], all_specs: list[dict], smoke: bool, selected: list | None = None) -> None:
    """Bank sources: every cell of the job's group (variant, family, position) across the four rules (X6: its five profiles)
    in a real run; in a smoke run, the manifest cells of the selected variants and rules (any family). A D2+H3 group embeds
    the same variant and position's D2 cells."""
    sel = selected if selected is not None else jobs
    vs = {j["variant_name"] for j in sel}; rs = {j["rule"] for j in sel}
    pool_specs = [s for s in all_specs if (not smoke) or (s["variant"] in vs and s["rule"] in rs)]
    pool = [{"name": s["id"], "bank_group": f"{s['variant']}_{s['family']}_{s['position']}", "family": s["family"],
             "variant_name": s["variant"], "position": s["position"]} for s in pool_specs]
    for j in jobs:
        g = j["bank_group"]
        j["bank_sources"] = [p["name"] for p in pool if p["bank_group"] == g]
        if j["family"] == "D2+H3":
            j["bank_embed"] = [p["name"] for p in pool if p["family"] == "D2" and p["variant_name"] == j["variant_name"] and p["position"] == j["position"]]


def dependency_jobs(jobs: list[dict], all_specs: list[dict], smoke: bool) -> dict:
    """Jobs for every bank source and embedding source the selected jobs depend on, built from the complete manifest so
    each keeps its own family, variant, position, and schedule."""
    need = {n for j in jobs for n in (j.get("bank_sources") or []) + (j.get("bank_embed") or [])} - {j["name"] for j in jobs}
    specs = [s for s in all_specs if s["id"] in need]
    return {j["name"]: j for j in jobs_for(specs, smoke)}


def report_all(out: Path, jobs: list[dict]) -> dict:
    from scripts.explore_attackers import read_record, upper_bound, validate_record, verify_bank_group, write_record, _sha_json, git_commit, X6
    cells, sources = [], {}
    for job in jobs:
        n = job["name"]
        se = read_record(out / "search" / f"{n}.json"); bk = read_record(out / "bank" / f"{n}.json")
        ref = read_record(out / "reference" / f"{n}.json"); ev = read_record(out / "evaluate" / f"{n}.json")
        dbl = read_record(out / "doubling" / f"{n}.json")
        validate_record(job, "search", se, {})
        if bk is not None or not job["smoke"]:
            validate_record(job, "bank", bk, {"search": se})
        validate_record(job, "reference", ref, {"search": se, **({"bank": bk} if bk is not None else {})})
        validate_record(job, "evaluate", ev, {"reference": ref})
        if bk is not None:
            verify_bank_group(out, job)
        if job.get("doubling"):
            validate_record(job, "doubling", dbl, {"search": se, **({"bank": bk} if bk is not None else {})})
        rows = ev["rows"]
        if [int(r["seed"]) for r in rows] != list(job["seeds_val"]):
            raise SystemExit(f"{n}: the evaluation rows do not carry exactly the job's evaluation seeds")
        sources[n] = _sha_json(ev); g = [r["gain"] for r in rows]; ub, deg = upper_bound(g, job["intervals"])
        x6 = job["family"] == X6
        mean = lambda k: float(np.mean([r[k] for r in rows]))
        cells.append({"cell": n, "axis": job.get("axis"), "variant": job["variant_name"], "position": job["position"], "rule": job["rule"],
                      "family": job["family"], "c": job["c"], "schedule": job["schedule"], "param_transfer": job["provenance"].get("param_transfer"),
                      "n": len(rows), "gain_mean": float(np.mean(g)), "gain_upper95_studentized": ub, "degenerate_bound": deg,
                      "inflation_term": mean("inflation_term"), "selection_term": mean("selection_term"), "eff_attack": mean("eff_attack"),
                      "eff_clip": mean("eff_clip"), "eff_ref": mean("eff_ref"), "eff_honest": mean("eff_honest"), "net_eff_attack": mean("net_eff_attack"),
                      "harm": mean("harm_outsiders" if x6 else "harm_direct"), "audit_spend": mean("audit_spend_attack"),
                      "focal_failures": mean("failures_focal_attack"), "focal_identities": mean("focal_identities"),
                      "fresh_audit_coverage_focal": sum(r["fresh_audited_focal"] for r in rows) / max(1, sum(r["fresh_served_focal"] for r in rows)),
                      "rounds_fresh_exceeds_audits": mean("rounds_fresh_exceeds_audits"), "knobs": ref["attack_knobs"], "source": ref["attack_source"],
                      "reference": ev["reference_candidate"], "restart_gain_spread": se["restart_spread"]["gain_spread"],
                      "twin_vs_honest_passed": se["twin_vs_honest"]["passed"], "bank_improved": bk["transfer"]["improved"] if bk else None,
                      "doubling_delta": dbl["doubling"]["delta_gain"] if dbl else None})
    rep = {"status": "exploratory robustness v1; descriptive bounds at n = 20; frozen rules; parameter transfer off the headline market",
           "smoke": bool(jobs[0]["smoke"]) if jobs else None, "git_commit": git_commit(), "sources": sources, "cells": cells}
    write_record(out / "report.json", rep)
    return rep


def run(o: dict) -> dict:
    from scripts.explore_attackers import RULES, run as xrun
    specs = manifest_specs(); smoke = bool(o.get("smoke"))
    sel = lambda key, s: o.get(key) in (None, "all") or s in str(o[key]).split(",")
    chosen = [s for s in specs if sel("variants", s["variant"]) and sel("rules", s["rule"]) and sel("families", s["family"])]
    if not smoke and o.get("rules") not in (None, "all") and set(str(o["rules"]).split(",")) != set(RULES):
        raise SystemExit("a real robustness run takes all four rules (bank sources span them)")
    jobs = jobs_for(chosen, smoke); assign_banks(jobs, specs, smoke)
    lookup = dependency_jobs(jobs, specs, smoke)
    oo = {**o, "rules": ",".join(sorted({j["rule"] for j in jobs})), "families": ",".join(sorted({j["family"] for j in jobs}))}
    return xrun(oo, jobs=jobs, report_fn=report_all, lookup=lookup)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true"); ap.add_argument("--stage", default="all"); ap.add_argument("--variants", default="all")
    ap.add_argument("--rules", default="all"); ap.add_argument("--families", default="all"); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--out", default="results/robustness"); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--pilot", action="store_true")
    a = ap.parse_args()
    if a.calibrate:
        for name in doc()["variants"]:
            print(name, calibrate_market(variant(name)) if name != "headline" else "registered")
        return
    print(json.dumps(run(vars(a))))


if __name__ == "__main__":
    main()
