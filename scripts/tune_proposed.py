"""Amendment 1, tuning block (orchestration registered by amendment 2): tune the proposed rule on the registered 36-point
grid with the H3-inclusive objective, the baselines' registered H3 gains read from the registered sweep's reference
records (checked), every evaluation logged, and write experiments/proposed.yaml."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import SMOKE_BUDGET, check_record, job_for, load_params  # noqa: E402
from sim.amendment import amendment_hash  # noqa: E402
from sim.calibrate import cell_config, load_calibration  # noqa: E402
from sim.cell import SeedCache  # noqa: E402
from sim.locked import load_locked, market_config_from_locked, seeds, settings_hash  # noqa: E402
from sim.manifest import enumerate_manifest  # noqa: E402
from sim.schedule import budget_from_locked  # noqa: E402
from sim.tuning import grid_tag, tune_proposed, tuning_grid  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True); ap.add_argument("--sweep-out", dest="sweep_out", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", required=True); ap.add_argument("--out", required=True); ap.add_argument("--log", required=True)
    ap.add_argument("--amendment", default=str(REPO / "experiments" / "amendment-2026-10-17.yaml"))
    ap.add_argument("--quick", action="store_true", help="tiny budgets for a smoke run; never for the freeze")
    a = ap.parse_args()
    lk = load_locked(); cal = load_calibration(a.calibration)
    if not a.quick and list(cal.seeds) != seeds(lk, "calibration"):
        raise SystemExit("tuning for the freeze needs the full calibration namespace (pass --quick for a smoke run)")
    b2_path = Path(a.tuned_dir) / "tuned_B2.json"; b2 = json.loads(b2_path.read_text())
    if not a.quick and hashlib.sha256(b2_path.read_bytes()).hexdigest() != (lk.get("tuned") or {}).get("B2"):
        raise SystemExit("tuned_B2.json: hash differs from the lock")
    prices = tuple(float(b2["best_params"][k]) for k in ("P1", "P2", "P3"))
    budget = SMOKE_BUDGET if a.quick else budget_from_locked(lk); base = market_config_from_locked(lk)
    gains, hashes = {}, {}
    for rule in ("B2", "B3"):                                           # the baselines' registered dev-train H3 gains, from checked reference records
        spec = next(c for c in enumerate_manifest(lk, ["B1", "B2", "B3"], budget=budget) if c.section == "h3" and c.rule == rule)
        path = Path(a.sweep_out) / "reference" / f"{spec.name}.json"
        if not path.exists():
            raise SystemExit(f"{rule}: no H3 reference record at {path}")
        rec = json.loads(path.read_text())
        params = load_params(rule, None if a.quick else Path(a.tuned_dir), a.quick, cal.market_key, settings_hash(lk), cal.seeds)
        job = job_for(spec, lk, cal, base, params, budget, a.quick)
        try:
            check_record(job, rec)
        except SystemExit as e:
            raise SystemExit(f"{rule}: H3 reference record refused: {e}")
        gains[rule] = float(rec["gain_train"]); hashes[rule] = hashlib.sha256(path.read_bytes()).hexdigest()
    cfg = cell_config(base, cal, rho=float(lk["rho"]["default"]), beta=float(lk["beta_headline"]))
    override = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16, "recheck_restarts": 1, "recheck_val_seeds": 2} if a.quick else None
    res = tune_proposed(cfg, lk, SeedCache(), prices, gains, a.log, inner_override=override, grid_limit=2 if a.quick else None)
    amend = yaml.safe_load(Path(a.amendment).read_text()) if Path(a.amendment).exists() else {}
    doc = {"rule": "proposed", "market_key": cal.market_key, "calibration_seeds": list(cal.seeds), "settings_hash": settings_hash(lk), "quick": bool(a.quick),
           "best_params": res.best_params, "rechecked": res.rechecked, "scores": res.scores, "objective": "amendment-1", "h3_baseline_gains": gains,
           "h3_reference_sha256": hashes, "amendment_sha256": amendment_hash(amend), "grid_order": [grid_tag(p) for p in tuning_grid("proposed", cfg, lk, prices)],
           "b2_prices": list(prices)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(yaml.safe_dump(doc, sort_keys=False))
    print(json.dumps(res.best_params))


if __name__ == "__main__":
    main()
