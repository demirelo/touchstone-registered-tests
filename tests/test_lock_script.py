import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from sim.locked import load_locked, settings_hash

ROOT = Path(__file__).resolve().parents[1]


def setup(tmp_path):
    exp = tmp_path / "experiments"; exp.mkdir(); shutil.copy(ROOT / "experiments" / "locked.yaml", exp / "locked.yaml")
    shutil.copy(ROOT / "experiments" / "comprehension_fixture.yaml", exp / "comprehension_fixture.yaml")
    tuned = tmp_path / "tuned"; tuned.mkdir()
    for r in ("B1", "B2", "B3"):
        (tuned / f"tuned_{r}.json").write_text(json.dumps({"rule": r}))
    lk = load_locked(); T = lk["market"]["T"]; T100 = lk["h1"]["T"]
    cal = {"S_hat": 1.0, "n_FB": 2.0, "m": 0.5, "market_key": "k", "T": T, "seeds": [1]}
    (tmp_path / "cal.json").write_text(json.dumps(cal)); (tmp_path / "cal100.json").write_text(json.dumps(dict(cal, T=T100))); (tmp_path / "calbad.json").write_text(json.dumps(dict(cal, T=7)))
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{} for _ in range(6)],
           "fixture_and_power": {"per_n": {"10": [{"fixture": {"trials": lk["intervals"]["joint_trials"]}}], "20": [{"fixture": {"trials": lk["intervals"]["joint_trials"]}}]}},
           "consequences": {"h1": "confirmatory", "parametrized": "percentile_n20", "final_eval_n": 20}}
    from sim.coverage import ENDPOINTS, PROCEDURES_AT_N, endpoint_key, thresholds, admission
    thr = {n: thresholds(lk, 35000) for n in (10, 20)}
    measured = {f"{endpoint_key(st, side, lv, n)}|{proc}": 0.999 for n in (10, 20) for proc in PROCEDURES_AT_N[n] for st, side, lv in ENDPOINTS}
    pn = {n: {"pool_size": 35000, "replications": {n: 2000}, "pool_factor": 1, "rep_factor": 1} for n in ("10", "20")}
    rep["cells"] = {f"c{i}": {"per_n": json.loads(json.dumps(pn)), "measured": dict(measured)} for i in range(6)}
    rep["selection"] = [{"name": f"c{i}"} for i in range(6)]; rep["thresholds"] = {str(n): t for n, t in thr.items()}
    rep["M"] = 35000; rep["fixture_and_power"]["base_M"] = 35000; rep["fixture_and_power"]["base_R"] = {"10": 2000, "20": 2000, "40": 4000}
    from sim.coverage import clopper_pearson_lower
    rep["fixture_and_power"]["per_n"]["40"] = [{"fixture": {"trials": lk["intervals"]["joint_trials"]}}]
    for n, R in (("10", 2000), ("20", 2000), ("40", 4000)):
        att = rep["fixture_and_power"]["per_n"][n][0]; T = lk["intervals"]["joint_trials"]
        att.update({"M": 35000, "R": R, "pool_factor": 1, "rep_factor": 1, "threshold_check_pass": True, "pass_": True,
                    "power": {f"{n}|{lv}": {"power_200": 0.95, "power_400": 0.95, "converged": True, "pass_": True} for lv in (0.95, 0.9875)}})
        att["fixture"].update({"M": 35000, "R": R, "cells": 6, "endpoints_per_cell": 8, "admitted": T, "lower_limit": clopper_pearson_lower(T, T, 1 - 0.05 / 3), "pass_": True})
    rep["fixture_and_power"]["threshold_check"] = {"35000": {k: {"gap": 0.0, "se": 1e-4, "pass_": True} for n in (10, 20, 40) for k in (f"{n}|0.95", f"{n}|0.9875")}}
    rep["fixture_and_power"]["admissible_n"] = {"10": True, "20": True, "40": True}            # gates computed for every n; thresholds and cells only for the measured 10 and 20
    import hashlib, sys as _sys
    _sys.path.insert(0, str(ROOT)); from scripts.coverage_study import provenance_hash
    rep["provenance"] = {"settings_hash": settings_hash(lk), "salt_hash": "cd" * 32, "calibration_sha256": hashlib.sha256((tmp_path / "cal.json").read_bytes()).hexdigest(),
                         "tuned_sha256": {r: hashlib.sha256((tuned / f"tuned_{r}.json").read_bytes()).hexdigest() for r in ("B1", "B2", "B3")}, "reference_records_sha256": {}, "sweep_out": "x"}
    rep["provenance_hash"] = provenance_hash(rep["provenance"])
    for i, c in enumerate(rep["cells"].values()):
        c["input_hash"] = f"{i:02d}" * 32; c["provenance_hash"] = rep["provenance_hash"]
    adm = admission({k: v["measured"] for k, v in rep["cells"].items()}, thr, lk, rep["fixture_and_power"]["admissible_n"]); rep.update(adm)
    (tmp_path / "cov.json").write_text(json.dumps(rep)); (tmp_path / "pilot.json").write_text(json.dumps({"projected_cost_usd": 118.4, "complete": True, "calls": 200, "backend": "anthropic"}))
    return exp, tuned


def cmd(tmp_path, exp, tuned, *extra):
    return [sys.executable, str(ROOT / "scripts" / "lock.py"), "--locked", str(exp / "locked.yaml"), "--tuned-dir", str(tuned), "--calibration", str(tmp_path / "cal.json"),
            "--calibration-t100", str(tmp_path / "cal100.json"), "--coverage-report", str(tmp_path / "cov.json"), "--fixture", str(exp / "comprehension_fixture.yaml"), *extra]


def test_lock_script_writes_lock_time_blocks_validates_inputs_and_check_passes(tmp_path):
    exp, tuned = setup(tmp_path); before = settings_hash(load_locked(exp / "locked.yaml"))
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32, "--pilot", str(tmp_path / "pilot.json")), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    lk = yaml.safe_load((exp / "locked.yaml").read_text())
    assert lk["version"] == "locked-2026-10-28" and set(lk["tuned"]) == {"B1", "B2", "B3"} and lk["calibration"]["T100"]["T"] == lk["h1"]["T"]
    assert lk["sealed_bundle_sha256"] == "ab" * 32 and lk["identity_salt_sha256"] == "cd" * 32 and lk["h1"]["cost_cap_usd"] == 119 and lk["coverage_consequences"]["final_eval_n"] == 20
    assert len(lk["coverage_report_sha256"]) == 64 and len(lk["comprehension_fixture_sha256"]) == 64
    assert settings_hash(lk) == before and "git tag -s lock-2026-10-28" in r.stdout
    chk = subprocess.run(cmd(tmp_path, exp, tuned, "--check", "--pilot", str(tmp_path / "pilot.json")), capture_output=True, text=True, cwd=ROOT)
    assert chk.returncode == 0, chk.stderr
    (tuned / "tuned_B2.json").write_text("{}")
    chk2 = subprocess.run(cmd(tmp_path, exp, tuned, "--check", "--pilot", str(tmp_path / "pilot.json")), capture_output=True, text=True, cwd=ROOT)
    assert chk2.returncode == 1 and "tuned_B2" in (chk2.stdout + chk2.stderr)


def test_lock_script_refuses_bad_inputs(tmp_path):
    import sys as _sys
    _sys.path.insert(0, str(ROOT))
    from scripts.coverage_study import provenance_hash
    from sim.coverage import admission, thresholds
    exp, tuned = setup(tmp_path); lk = load_locked(); thr = {n: thresholds(lk, 35000) for n in (10, 20)}
    base = cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32, "--cost-cap-usd", "120")
    bad_t = [a if a != str(tmp_path / "cal100.json") else str(tmp_path / "calbad.json") for a in base]
    r = subprocess.run(bad_t, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "T" in (r.stderr + r.stdout)
    smoke = json.loads((tmp_path / "cov.json").read_text()); smoke["admission_basis"] = "smoke (not an admission)"; (tmp_path / "cov_smoke.json").write_text(json.dumps(smoke))
    bad_c = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_smoke.json") for a in base]
    r = subprocess.run(bad_c, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "coverage" in (r.stderr + r.stdout).lower()
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "zz", "--salt-hash", "cd" * 32, "--cost-cap-usd", "1"), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "hex" in (r.stderr + r.stdout).lower()
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "cost cap" in (r.stderr + r.stdout).lower()                 # a cost cap is required (pilot or explicit)
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--salt-hash", "cd" * 32, "--cost-cap-usd", "120"), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "bundle-hash" in (r.stderr + r.stdout)                      # both commitments are required
    r = subprocess.run(cmd(tmp_path, exp, tuned, "--bundle-hash", "ab" * 32, "--salt-hash", "cd" * 32, "--cost-cap-usd", "-1"), capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "positive" in (r.stderr + r.stdout)
    short = json.loads((tmp_path / "cov.json").read_text()); short["fixture_and_power"]["threshold_check"]["35000"]["10|0.95"]["pass_"] = False
    nocell = json.loads((tmp_path / "cov.json").read_text()); nocell["cells"] = {}; (tmp_path / "cov_nocell.json").write_text(json.dumps(nocell))
    bad_n = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_nocell.json") for a in base]
    r = subprocess.run(bad_n, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "every selected cell" in (r.stderr + r.stdout)
    liar = json.loads((tmp_path / "cov.json").read_text()); liar["consequences"]["h1"] = "exploratory"; (tmp_path / "cov_liar.json").write_text(json.dumps(liar))
    bad_l = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_liar.json") for a in base]
    r = subprocess.run(bad_l, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "do not follow" in (r.stderr + r.stdout)
    zero = json.loads((tmp_path / "cov.json").read_text())
    for t in zero["thresholds"]["20"].values():
        t["threshold"] = 0.0
    (tmp_path / "cov_zero.json").write_text(json.dumps(zero))
    bad_z = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_zero.json") for a in base]
    r = subprocess.run(bad_z, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "thresholds(locked" in (r.stderr + r.stdout)
    small = json.loads((tmp_path / "cov.json").read_text()); small["fixture_and_power"]["per_n"]["10"][0].update({"M": 4, "R": 2}); small["fixture_and_power"]["per_n"]["10"][0]["fixture"].update({"M": 4, "R": 2})
    (tmp_path / "cov_small.json").write_text(json.dumps(small))
    bad_s = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_small.json") for a in base]
    r = subprocess.run(bad_s, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "locked size" in (r.stderr + r.stdout)
    onekey = json.loads((tmp_path / "cov.json").read_text()); onekey["fixture_and_power"]["per_n"]["20"][0]["power"].pop("20|0.9875"); (tmp_path / "cov_onekey.json").write_text(json.dumps(onekey))
    bad_o = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_onekey.json") for a in base]
    r = subprocess.run(bad_o, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "incomplete evidence" in (r.stderr + r.stdout)
    flag = json.loads((tmp_path / "cov.json").read_text()); flag["fixture_and_power"]["per_n"]["10"][0]["fixture"]["admitted"] = 0; (tmp_path / "cov_flag.json").write_text(json.dumps(flag))
    bad_f = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_flag.json") for a in base]
    r = subprocess.run(bad_f, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "contradict" in (r.stderr + r.stdout)   # pass_ True with 0 admitted
    tiny = json.loads((tmp_path / "cov.json").read_text()); tiny["cells"]["c0"]["per_n"]["10"].update({"pool_size": 4, "replications": {"10": 2}}); (tmp_path / "cov_tiny.json").write_text(json.dumps(tiny))
    bad_t = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_tiny.json") for a in base]
    r = subprocess.run(bad_t, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "pool size or replication count" in (r.stderr + r.stdout)
    nan = json.loads((tmp_path / "cov.json").read_text()); nan["cells"]["c1"]["measured"] = {k: 1.5 for k in nan["cells"]["c1"]["measured"]}; (tmp_path / "cov_nan.json").write_text(json.dumps(nan))
    bad_v = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_nan.json") for a in base]
    r = subprocess.run(bad_v, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "finite coverage" in (r.stderr + r.stdout)
    # a failed first attempt followed by a registered doubling that passes is a valid report
    rem = json.loads((tmp_path / "cov.json").read_text()); first = rem["fixture_and_power"]["per_n"]["10"][0]
    failed = json.loads(json.dumps(first)); failed["threshold_check_pass"] = False; failed["pass_"] = False
    second = json.loads(json.dumps(first)); second.update({"pool_factor": 2, "M": 70000}); second["fixture"].update({"M": 70000})
    rem["fixture_and_power"]["per_n"]["10"] = [failed, second]
    rem["fixture_and_power"]["threshold_check"]["35000"]["10|0.95"] = {"gap": 0.01, "se": 1e-4, "pass_": False}
    rem["fixture_and_power"]["threshold_check"]["70000"] = {k: {"gap": 0.0, "se": 1e-4, "pass_": True} for n in (10, 20, 40) for k in (f"{n}|0.95", f"{n}|0.9875")}
    rem["thresholds"]["10"] = {k: v for k, v in thresholds(lk, 70000).items()}
    for c in rem["cells"].values():
        c["per_n"]["10"].update({"pool_size": 70000, "pool_factor": 2})
    adm2 = admission({k: v["measured"] for k, v in rem["cells"].items()}, {10: rem["thresholds"]["10"], 20: thr[20]}, lk, rem["fixture_and_power"]["admissible_n"]); rem.update(adm2)
    (tmp_path / "cov_rem.json").write_text(json.dumps(rem))
    good_r = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_rem.json") for a in base]
    r = subprocess.run(good_r, capture_output=True, text=True, cwd=ROOT); assert r.returncode == 0, r.stderr + r.stdout
    other = json.loads((tmp_path / "cov.json").read_text()); other["provenance"]["tuned_sha256"]["B2"] = "00" * 32; other["provenance_hash"] = provenance_hash(other["provenance"])
    for c in other["cells"].values():
        c["provenance_hash"] = other["provenance_hash"]
    (tmp_path / "cov_other.json").write_text(json.dumps(other))
    bad_p = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_other.json") for a in base]
    r = subprocess.run(bad_p, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "provenance tuned_sha256" in (r.stderr + r.stdout)   # a report from other tuned files never locks
    gate = json.loads((tmp_path / "cov.json").read_text()); gate["fixture_and_power"]["per_n"]["10"][0]["fixture"].update({"pass_": False, "admitted": 0, "lower_limit": 0.0}); gate["fixture_and_power"]["per_n"]["10"][0]["pass_"] = False
    (tmp_path / "cov_gate.json").write_text(json.dumps(gate))                      # admissible_n still says True: the evidence must win
    bad_g = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_gate.json") for a in base]
    r = subprocess.run(bad_g, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "admissible_n" in (r.stderr + r.stdout)
    (tmp_path / "cov_chk.json").write_text(json.dumps(short))
    bad_k = [a if a != str(tmp_path / "cov.json") else str(tmp_path / "cov_chk.json") for a in base]
    r = subprocess.run(bad_k, capture_output=True, text=True, cwd=ROOT); assert r.returncode != 0 and "threshold check" in (r.stderr + r.stdout)   # a failed check with pass_ still True contradicts its values
