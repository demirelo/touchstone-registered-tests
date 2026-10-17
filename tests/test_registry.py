import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from sim.config import MarketConfig
from sim.locked import load_locked, settings_hash

ROOT = Path(__file__).resolve().parents[1]
PROPOSED_SRC = '''
from sim.mechanisms.posted_audit import PostedRandomAudit

def make(params):
    return PostedRandomAudit(params["P1"], params["P2"], params["P3"], tol=params["tol"], L=params["L"])
'''
H2_SRC = '''
from sim.policies.adaptive import AdaptiveCheat
from sim.policies.families import D2, Family
# A synthetic family named H2: D2 without the w knob, so its corner count differs from D2's (schedule test).
H2 = Family("H2", ("u0", "m0", "s", "d", "r", "clip"), {k: v for k, v in D2.bounds.items() if k != "w"}, lambda **k: AdaptiveCheat(w=0.0, **k))
CONTAINMENT = "H2 is D2 with w fixed at 0 (synthetic test family)"
'''


def synthetic_env(tmp_path, monkeypatch, with_sealed=True):
    (tmp_path / "proposed.py").write_text(PROPOSED_SRC)
    lk = load_locked()
    (tmp_path / "proposed.yaml").write_text(yaml.safe_dump({"rule": "proposed", "best_params": {"P1": 0.25, "P2": 0.4, "P3": 0.55, "tol": 0.1, "L": 5},
                                                             "market_key": "k", "settings_hash": settings_hash(lk), "calibration_seeds": [1]}))
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_MODULE", str(tmp_path / "proposed.py"))
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_PARAMS", str(tmp_path / "proposed.yaml"))
    if with_sealed:
        s = tmp_path / "sealed"; (s / "h2").mkdir(parents=True); (s / "h2" / "family.py").write_text(H2_SRC)
        monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(s))
        if lk.get("sealed_bundle_sha256"):                                                      # after the lock: a lock copy that commits to the synthetic bundle
            from sim.sealed import bundle_hash
            lk2 = dict(lk, sealed_bundle_sha256=bundle_hash(s)); (tmp_path / "locked.yaml").write_text(yaml.safe_dump(lk2, sort_keys=False))
            monkeypatch.setenv("TOUCHSTONE_LOCKED", str(tmp_path / "locked.yaml"))
    return tmp_path


def test_registry_loads_the_proposed_rule_and_the_sealed_family(tmp_path, monkeypatch):
    import importlib
    synthetic_env(tmp_path, monkeypatch)
    import sim.registry as reg; importlib.reload(reg)
    assert reg.proposed_available() and reg.available_rules() == ["B1", "B2", "B3", "proposed"]
    rule = reg.make_rule("proposed", reg.proposed_params()["best_params"])
    assert rule.tol == 0.1 and rule.L == 5                       # the describe() record is checked in Task 3's tests
    fams = reg.available_families()
    assert set(fams) == {"D1", "D2", "D2+H3", "H2"} and fams["H2"].name == "H2" and len(fams["H2"].corners()) != len(fams["D2"].corners())
    from sim.schedule import cell_runs, budget_from_locked
    lk = load_locked(); b = budget_from_locked(lk); assert cell_runs("H2", b)["corners"] == len(fams["H2"].corners()) * b.n_train
    from sim.tuning import rule_from_params
    assert rule_from_params("proposed", {"P1": 0.25, "P2": 0.4, "P3": 0.55, "tol": 0.1, "L": 5}).name == rule.name


def test_registry_applies_a_logged_family_repair(tmp_path, monkeypatch):
    import hashlib, importlib
    synthetic_env(tmp_path, monkeypatch)
    s = tmp_path / "sealed"; (s / "patches").mkdir()
    fixed = H2_SRC.replace('"H2"', '"H2fixed"'); (s / "patches" / "family.py").write_text(fixed)
    (s / "patches" / "log.json").write_text(json.dumps({"family.py": {"sha256": hashlib.sha256(fixed.encode()).hexdigest(), "replaces": "h2/family.py", "demotes": []}}))
    import sim.registry as reg; importlib.reload(reg)
    assert reg.available_families()["H2"].name == "H2fixed"                                  # the overlay is read, the original file untouched
    assert (s / "h2" / "family.py").read_text() == H2_SRC


def test_registry_without_the_files_has_only_baselines(tmp_path, monkeypatch):
    import importlib
    monkeypatch.setenv("TOUCHSTONE_PROPOSED_MODULE", str(tmp_path / "nope.py")); monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(tmp_path / "nosealed"))
    import sim.registry as reg; importlib.reload(reg)
    assert not reg.proposed_available() and reg.available_rules() == ["B1", "B2", "B3"] and "H2" not in reg.available_families()
    with pytest.raises(ValueError):
        reg.make_rule("proposed", {})


def test_manifest_lists_heldout_cells_only_when_h2_is_registered(tmp_path, monkeypatch):
    import importlib
    from sim.manifest import enumerate_manifest, totals
    lk = load_locked()
    monkeypatch.setenv("TOUCHSTONE_SEALED_DIR", str(tmp_path / "nosealed")); import sim.registry as reg; importlib.reload(reg)
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    assert not any(c.section == "heldout" for c in cells)
    synthetic_env(tmp_path, monkeypatch); importlib.reload(reg)
    cells = enumerate_manifest(lk, ["B1", "B2", "B3", "proposed"])            # proposed in --rules never reaches the tuning grids or the bank
    held = [c for c in cells if c.section == "heldout"]
    n_betas = len(lk["beta_grid"]); n_pos = len(lk["positions"])
    h2 = [c for c in held if c.family == "H2"]; h3 = [c for c in held if c.family == "D2+H3"]
    assert len(h2) == 4 * (n_betas - 1 + n_pos) and all(c.post_lock for c in held) and {c.rule for c in held} == {"B1", "B2", "B3", "proposed"}
    assert len(h3) == 4 and all(c.position == "median" and float(c.beta) == float(lk["beta_headline"]) for c in h3)     # amendment 1: the final H3 stress-test cells
    held = h2
    assert len({c.name for c in held}) == len(held) and not any(c.rule == "proposed" and c.section != "heldout" for c in cells if not c.post_lock)
    t = totals(cells)
    assert t["heldout"] > 0 and t["pre_lock"] == totals([c for c in cells if c.section != "heldout"])["pre_lock"]
    from sim.schedule import budget_from_locked
    lk20 = dict(lk, coverage_consequences={"final_eval_n": 20, "h1": "confirmatory", "parametrized": "percentile_n20"})
    lk40 = dict(lk, coverage_consequences={"final_eval_n": 40, "h1": "confirmatory", "parametrized": "studentized_n40"})
    held20 = [c for c in enumerate_manifest(lk20, ["B2"]) if c.section == "heldout" and c.family == "H2"]
    held40 = [c for c in enumerate_manifest(lk40, ["B2"]) if c.section == "heldout" and c.family == "H2"]
    assert held40[0].runs - held20[0].runs == 4 * (40 - 20)                                   # the final-eval sample size enters only the evaluation runs


def test_sweep_smoke_runs_the_proposed_rule_and_h2_through_every_stage(tmp_path, monkeypatch):
    # The documented post-lock command on the locked market with a smoke budget: every stage, a baseline and the proposed
    # rule, the synthetic H2 whose corner count differs from D2's, the bundle hash in the records, and the H2 headline.
    import os
    from sim.calibrate import calibrate, save_calibration
    from sim.locked import market_config_from_locked
    synthetic_env(tmp_path, monkeypatch)
    lk = load_locked(); save_calibration(calibrate(market_config_from_locked(lk), [4000, 4001]), tmp_path / "cal.json")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "sweep.py"), "--stage", "all", "--sections", "heldout", "--rules", "B2,proposed",
                        "--calibration", str(tmp_path / "cal.json"), "--smoke", "--select", "beta0.05", "--out", str(tmp_path / "out")],
                       capture_output=True, text=True, cwd=ROOT, env=dict(os.environ))
    assert r.returncode == 0, r.stderr
    evals = {p.stem: json.loads(p.read_text()) for p in (tmp_path / "out" / "evaluate").glob("*.json")}
    assert {v["spec"]["rule"] for v in evals.values()} == {"B2", "proposed"} and {v["spec"]["family"] for v in evals.values()} == {"H2", "D2+H3"}
    assert all(v.get("bundle_hash") for v in evals.values() if v["spec"]["family"] == "H2")
    h3 = [v for v in evals.values() if v["spec"]["family"] == "D2+H3"]                                  # amendment 1: the final H3 stress-test cells, one per rule at the median
    assert {v["spec"]["rule"] for v in h3} == {"B2", "proposed"} and all(v["spec"]["position"] == "median" for v in h3)
    head = json.loads((tmp_path / "out" / "headline.json").read_text())
    assert "B2/H2" in head and "proposed/H2" in head and head["B2/H2"]["headline"] in ("low", "median", "high")
