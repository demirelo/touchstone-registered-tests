import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SYNTH = '''
from sim.mechanisms.base import Mechanism
from sim.mechanisms.posted_audit import PostedRandomAudit   # a synthetic stand-in for tests only; the real module never imports a baseline

class Proposed(PostedRandomAudit):
    name = "proposed"

def make(params):
    p = dict(params); prices = (p.get("P1", 0.25), p.get("P2", 0.40), p.get("P3", 0.55))
    r = Proposed(*prices, tol=p["tol"], L=p["L"]); r.allocation = p["allocation"]; r.targeting = p["targeting"]; return r
'''


def fabricate_h3_references(sweep: Path, cal_path: Path, lk: dict, gains: dict) -> None:
    """Two H3 reference records that pass check_record against the manifest's smoke jobs, with the given dev-train gains."""
    from scripts.sweep import SMOKE_BUDGET, job_for, load_params
    from sim.calibrate import load_calibration
    from sim.locked import market_config_from_locked, settings_hash
    from sim.manifest import enumerate_manifest
    cal = load_calibration(cal_path); base = market_config_from_locked(lk)
    (sweep / "reference").mkdir(parents=True, exist_ok=True)
    for rule, g in gains.items():
        spec = next(c for c in enumerate_manifest(lk, ["B1", "B2", "B3"], budget=SMOKE_BUDGET) if c.section == "h3" and c.rule == rule)
        job = job_for(spec, lk, cal, base, load_params(rule, None, True, cal.market_key, settings_hash(lk), cal.seeds), SMOKE_BUDGET, True)
        rec = {k: job[k] for k in ("spec", "params", "cfg", "settings_hash", "budget", "smoke", "salt_hash")}
        rec.update({"eval_namespace": "dev_val", "gain_train": g, "candidate": {"name": "honest_max", "knobs": None}, "attack_knobs": {}})
        (sweep / "reference" / f"{spec.name}.json").write_text(json.dumps(rec))


@pytest.mark.slow
def test_tune_proposed_quick_run_logs_both_families_and_the_loader_rejects_quick_output(tmp_path, cal_path_session, monkeypatch):
    from scripts.sweep import load_params
    from sim.locked import load_locked
    lk = load_locked(); mod = tmp_path / "proposed.py"; mod.write_text(SYNTH)
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_MODULE", str(mod))
    sweep = tmp_path / "sweep"; fabricate_h3_references(sweep, cal_path_session, lk, {"B2": 0.58, "B3": 0.36})
    tuned = ROOT / "experiments" / "tuned"
    out = tmp_path / "proposed.yaml"; log = tmp_path / "log"
    cmd = [sys.executable, str(ROOT / "scripts" / "tune_proposed.py"), "--calibration", str(cal_path_session), "--sweep-out", str(sweep), "--tuned-dir", str(tuned), "--out", str(out), "--log", str(log), "--quick"]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env={**__import__("os").environ, "OMP_NUM_THREADS": "1"})
    assert r.returncode == 0, r.stderr[-2000:]
    doc = yaml.safe_load(out.read_text())
    assert doc["rule"] == "proposed" and doc["quick"] is True and doc["objective"] == "amendment-1" and doc["h3_baseline_gains"] == {"B2": 0.58, "B3": 0.36}
    assert set(doc["h3_reference_sha256"]) == {"B2", "B3"} and len(doc["amendment_sha256"]) == 64 and doc["grid_order"][:2] == ["A|T1|0.12|3", "A|T1|0.12|10"]
    assert set(doc["best_params"]) >= {"allocation", "targeting", "tol", "L"} and all({"eff_d2", "gain_d2", "eff_h3", "gain_h3", "objective"} <= set(s) for s in doc["scores"])
    tags = sorted(p.name for p in log.iterdir()); assert tags and all({(log / t / "D2.json").exists(), (log / t / "D2+H3.json").exists()} == {True} for t in tags)
    one = json.loads((log / tags[0] / "D2.json").read_text()); assert len(one["attack"]["evaluations"]) == one["attack"]["evals"] + len(one["attack"]["incumbent_scores"]) + 1 and one["reference"]["choice"]   # budget + incumbents + projection
    import importlib, sim.registry as reg
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_PARAMS", str(out)); importlib.reload(reg)
    with pytest.raises(SystemExit, match="quick"):
        load_params("proposed", tuned, False, doc["market_key"], doc["settings_hash"], doc["calibration_seeds"])
    good = dict(doc, quick=False); (tmp_path / "ok.yaml").write_text(yaml.safe_dump(good)); monkeypatch.setenv("TOUCHSTONE_PROPOSED_PARAMS", str(tmp_path / "ok.yaml"))
    importlib.reload(reg)
    assert load_params("proposed", tuned, False, doc["market_key"], doc["settings_hash"], doc["calibration_seeds"]) == doc["best_params"]
    stale = json.loads(next((sweep / "reference").glob("B2_*.json")).read_text()); stale["params"] = {"x": 1}; next((sweep / "reference").glob("B2_*.json")).write_text(json.dumps(stale))
    r2 = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT); assert r2.returncode != 0 and "B2" in (r2.stderr + r2.stdout)
