import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sim.calibrate import calibrate, save_calibration
from sim.config import MarketConfig
from sim.locked import load_locked

ROOT = Path(__file__).resolve().parents[1]


def smoke_cal(tmp_path):
    c = MarketConfig.default()
    cfg = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)
    p = tmp_path / "cal.json"; save_calibration(calibrate(cfg, [4000, 4001]), p)
    return p


def run(*args):
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "h1.py"), *args], capture_output=True, text=True, cwd=ROOT)


def base_args(cal, out):
    return ["--smoke", "--out", str(out)]                      # a smoke run calibrates its own small market and needs no calibration files


def test_h1_smoke_writes_rows_and_summary_and_replays(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-cheat", "--rules", "B1,B2", *base_args(cal, out))
    assert r.returncode == 0, r.stderr
    rows = list(csv.DictReader((out / "h1_rows.csv").open()))
    assert len(rows) == 2 * 1 * 2 and {"rule", "beta", "budget", "rep", "eval_seed", "reference", "profit_attack", "profit_ref", "gain", "gain_vs_twin", "invalid", "backend"} <= set(rows[0])
    s = json.loads((out / "h1_summary.json").read_text())
    assert set(s["cells"]) == {"B1|0.05", "B2|0.05"} and all(c["inconclusive"] is False for c in s["cells"].values()) and s["partial"] == []
    assert s["comprehension"]["B1"] >= 0 and s["calls_cap"] == load_locked()["h1"]["calls_cap"] and s["calls"] > 0 and len(s["instructions_sha256"]) == 64
    r2 = run("--backend", "fake-cheat", "--rules", "B1,B2", *base_args(cal, out))
    assert r2.returncode == 0 and json.loads((out / "h1_summary.json").read_text())["calls"] == 0
    assert len(list(csv.DictReader((out / "h1_rows.csv").open()))) == 4                      # rewritten, not appended


def test_h1_stops_before_the_call_that_exceeds_the_cap(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--max-calls", "10")
    assert r.returncode == 3 and "calls cap" in (r.stderr + r.stdout)
    s = json.loads((out / "h1_summary.json").read_text())
    assert s["calls"] == 10 and s["partial"] == ["B1|0.05"] and s["stopped_by"].startswith("calls cap")
    assert not (out / "h1_rows.csv").exists() or list(csv.DictReader((out / "h1_rows.csv").open())) == []    # the partial cell is not written as rows


def test_h1_pilot_stops_at_the_target_and_reports_cost_per_call(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--pilot", "--pilot-calls", "17")
    assert r.returncode == 0, r.stderr
    p = json.loads((out / "pilot_fake.json").read_text())
    assert p["calls"] == 17 and p["complete"] is True and p["mean_input_tokens"] > 0 and p["mean_latency_s"] >= 0
    assert p["projected_cost_usd"] == pytest.approx(p["cost_per_call_usd"] * load_locked()["h1"]["calls_cap"])
    r2 = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, tmp_path / "out2"), "--pilot", "--pilot-calls", "100000")
    assert r2.returncode == 4 and json.loads((tmp_path / "out2" / "pilot_fake.json").read_text())["complete"] is False


def test_h1_prompt_goes_through_the_repair_overlay(tmp_path, monkeypatch):
    import hashlib
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    s = tmp_path / "sealed"; (s / "patches").mkdir(parents=True); (s / "h1_prompt.txt").write_text("original prompt")
    (s / "patches" / "h1_prompt.txt").write_text("repaired prompt")
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": hashlib.sha256(b"repaired prompt").hexdigest(), "replaces": "h1_prompt.txt", "demotes": []}}))
    env = dict(__import__("os").environ, TOUCHSTONE_SEALED_DIR=str(s))
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "h1.py"), "--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--prompt", str(s / "h1_prompt.txt")],
                       capture_output=True, text=True, cwd=ROOT, env=env)
    assert r.returncode == 0, r.stderr
    assert json.loads((out / "h1_summary.json").read_text())["instructions_sha256"] == hashlib.sha256(b"repaired prompt").hexdigest()


def test_h1_final_eval_namespace_refused_before_the_unseal(tmp_path):
    cal = smoke_cal(tmp_path); out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", *base_args(cal, out), "--eval-namespace", "final_eval")
    assert r.returncode != 0 and "final_eval" in (r.stderr + r.stdout)


def test_h1_verifies_tuned_files_against_the_t200_calibration(tmp_path):
    """Ruling D9: a non-smoke run takes the T = 200 calibration for the tuned-file check and the T = 100 one for the market."""
    import hashlib
    from sim.locked import market_config_from_locked, settings_hash
    from sim.cell import market_key
    import dataclasses
    lk = load_locked(); base = market_config_from_locked(lk)
    c = MarketConfig.default()
    small = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=0.0, budget=0.0)
    save_calibration(calibrate(small, [4000]), tmp_path / "cal200.json")            # stands in for the T = 200 calibration
    save_calibration(calibrate(dataclasses.replace(small, T=5), [4000]), tmp_path / "cal100.json")
    tuned = tmp_path / "tuned"; tuned.mkdir()
    (tuned / "tuned_B1.json").write_text(json.dumps({"rule": "B1", "best_params": {"P1": 0.2, "P2": 0.35, "P3": 0.5}, "market_key": market_key(small),
                                                     "settings_hash": settings_hash(lk), "calibration_seeds": [4000], "quick": False}))
    out = tmp_path / "out"
    r = run("--backend", "fake-honest", "--rules", "B1", "--calibration", str(tmp_path / "cal200.json"), "--calibration-t100", str(tmp_path / "cal100.json"),
            "--tuned-dir", str(tuned), "--out", str(out), "--max-calls", "5", "--smoke")      # --smoke keeps the small market; the tuned file is still verified
    assert "tuned on another market" not in (r.stderr + r.stdout)                 # the T = 200 key verified the tuned file
    assert r.returncode == 3 and json.loads((out / "h1_summary.json").read_text())["T"] == 6    # the smoke market; the cap stopped it
    r2 = run("--backend", "fake-honest", "--rules", "B1", "--tuned-dir", str(tuned), "--out", str(tmp_path / "o2"), "--smoke")
    assert r2.returncode != 0 and "--calibration" in (r2.stderr + r2.stdout)       # tuned files cannot be verified without the T = 200 calibration
