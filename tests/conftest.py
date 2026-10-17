import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reload_registry_after_each_test():
    """sim.registry reads its paths from the environment at import time; tests that monkeypatch them reload it, so
    reload it again after every test (the environment is restored by then) so no test order sees a stale path."""
    yield
    try:
        import sim.registry as reg
        importlib.reload(reg)
    except Exception:
        pass


@pytest.fixture(scope="session")
def cal_path_session(tmp_path_factory):
    """The smoke calibration, built once per session (tests/test_sweep.py keeps its own module-scoped copy)."""
    from sim.calibrate import calibrate, save_calibration
    from sim.locked import load_locked, market_config_from_locked
    p = tmp_path_factory.mktemp("cal_session") / "cal.json"
    save_calibration(calibrate(market_config_from_locked(load_locked()), seeds=[4000]), p)
    return p


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False, help="run the tests marked slow (end-to-end smoke paths)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        return
    skip = pytest.mark.skip(reason="slow end-to-end smoke path; pass --runslow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)


SEEDS_EXT = {"start": 6_600_000, "block": 400_000, "pool": 35_000, "replications": {"40": 4000}}


def amendment_doc() -> dict:
    return {"amendment": {"id": 1, "date": "2026-10-17", "lock_tag": "lock-2026-10-17"},
            "clause": {"family": "D2+H3", "position": "median", "beta": 0.05, "eff_min": 0.90, "gain_max": 0.30, "gain_reduction_min": 0.10,
                       "level_rule": 0.95, "level_comparative": 0.9875, "baselines": ["B2", "B3"], "n": 40, "requires_h2_rule_clause": True},
            "extension": {"statistic": "gain_diff", "stand_in": {"r_star": "B3", "baseline": "B2"}, "procedures": ["studentized"], "sides": ["lower", "upper"]},
            "seeds_ext": dict(SEEDS_EXT), "coverage_report_amendment_sha256": None, "coverage_consequences": None}


def _run(args, cwd=ROOT):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=cwd, env={**__import__("os").environ, "OMP_NUM_THREADS": "1"})
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(str(a) for a in args[:3])} failed:\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r


@pytest.fixture(scope="session")
def smoke_inputs(tmp_path_factory, cal_path_session):
    """A smoke sweep over the 18 development cells at the headline budget (search, bank, reference), the smoke base
    coverage report on it, a synthetic lock bound to that report, its selection file, and a draft amendment file."""
    d = tmp_path_factory.mktemp("smoke_inputs"); sweep = d / "sweep"; cov = d / "cov"
    common = ["--calibration", str(cal_path_session), "--out", str(sweep), "--rules", "B1,B2,B3", "--smoke", "--workers", "2"]
    _run(["scripts/sweep.py", "--stage", "search", "--sections", "development", "--select", "beta0.05_rho0.2", *common])
    _run(["scripts/sweep.py", "--stage", "bank", *common])
    _run(["scripts/sweep.py", "--stage", "reference", *common])
    _run(["scripts/coverage_study.py", "--sweep-out", str(sweep), "--calibration", str(cal_path_session), "--out", str(cov), "--smoke", "--workers", "2"])
    report = cov / "coverage_report.json"
    lk = yaml.safe_load((ROOT / "experiments" / "locked.yaml").read_text())
    lk["coverage_report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    locked = d / "locked.yaml"; locked.write_text(yaml.safe_dump(lk, sort_keys=False))
    amend = d / "amendment.yaml"; amend.write_text(yaml.safe_dump(amendment_doc(), sort_keys=False))
    return {"dir": d, "sweep": sweep, "cal": cal_path_session, "base_report": report, "selection": cov / "coverage_cells.json", "locked": locked, "amendment": amend}


def fabricate_ext_report(lk: dict, base_path: Path, amend_doc: dict, out_path: Path) -> dict:
    """A registered-shaped extension report consistent with a fabricated base report (tests/test_lock_script.py::setup):
    six cells with both endpoints at 0.999, base sizes, one passing attempt at n = 40, provenance measured as the base's."""
    from scripts.coverage_study import provenance_hash
    from sim.amendment import AMEND_ENDPOINTS, LIMITATION, admission_ext, amendment_hash, endpoint_key
    from sim.coverage import clopper_pearson_lower, thresholds, write_report
    base = json.loads(base_path.read_text()); names = [c["name"] for c in base["selection"]]
    prov = {k: base["provenance"][k] for k in ("settings_hash", "salt_hash", "calibration_sha256", "tuned_sha256", "reference_records_sha256")}
    prov.update({"base_report_sha256": hashlib.sha256(base_path.read_bytes()).hexdigest(), "amendment_sha256": amendment_hash(amend_doc), "selection": names})
    T = int(lk["intervals"]["joint_trials"]); conf = 1 - 0.05 / 3; thr = thresholds(lk, 35000); thr40 = {k: v for k, v in thr.items() if v["n"] == 40}
    attempt = {"pool_factor": 1, "rep_factor": 1, "M": 35000, "R": 4000, "threshold_check_pass": True, "pass_": True,
               "fixture": {"n": 40, "M": 35000, "R": 4000, "trials": T, "cells": 6, "endpoints_per_cell": 2, "admitted": T, "conf": conf, "lower_limit": clopper_pearson_lower(T, T, conf), "pass_": True},
               "power": {"40|0.9875": {"deficit": 1.5, "power_200": 0.95, "power_400": 0.95, "converged": True, "pass_": True}}}
    fp = {"per_n": {"40": [attempt]}, "admissible_n": {"40": True}, "remedies": {"40": {"pool_factor": 1, "rep_factor": 1, "admissible": True}}, "base_M": 35000, "base_R": {"40": 4000},
          "threshold_check": {"35000": {"40|0.9875": {"analytic": thr["40|0.9875"]["exact"], "simulated": thr["40|0.9875"]["exact"], "gap": 0.0, "se": 1e-4, "pools": 200, "reps": 20000, "pass_": True}}}, "smoke": False}
    measured = {f"{endpoint_key(s, side, lv, 40)}|studentized": 0.999 for s, side, lv in AMEND_ENDPOINTS}
    cells = {n: {"measured": dict(measured), "pool_size": 35000, "replications": {"40": 4000}, "pool_factor": 1, "rep_factor": 1, "input_hash": f"{i:02d}" * 32,
                 "provenance_hash": provenance_hash(prov), "runs": 0, "pool_runs": 0} for i, n in enumerate(names)}
    adm = admission_ext({n: c["measured"] for n, c in cells.items()}, {40: thr}, lk, {"40": True}, names)
    report = {"smoke": False, "admission_basis": "registered", "selection": base["selection"], "base_report_sha256": prov["base_report_sha256"], "amendment_sha256": prov["amendment_sha256"],
              "cells": cells, "thresholds": {"40": thr40}, "fixture_and_power": fp, **adm, "provenance": prov, "provenance_hash": provenance_hash(prov), "limitation": LIMITATION, "manifest_runs": 0}
    write_report(out_path, report)
    return report


@pytest.fixture
def registered_inputs(tmp_path):
    """Fabricated registered artifacts: the lock-test base report and its lock copy, a draft amendment, a consistent extension report."""
    from tests.test_lock_script import setup
    exp, tuned = setup(tmp_path)
    lk = yaml.safe_load((exp / "locked.yaml").read_text()); lk["coverage_report_sha256"] = hashlib.sha256((tmp_path / "cov.json").read_bytes()).hexdigest()
    lk["calibration"] = {**(lk.get("calibration") or {}), "sha256": hashlib.sha256((tmp_path / "cal.json").read_bytes()).hexdigest()}     # the lock copy binds the fabricated inputs
    lk["tuned"] = {r: hashlib.sha256((tuned / f"tuned_{r}.json").read_bytes()).hexdigest() for r in ("B1", "B2", "B3")}
    locked = tmp_path / "locked_reg.yaml"; locked.write_text(yaml.safe_dump(lk, sort_keys=False))
    doc = amendment_doc(); amend = tmp_path / "amendment.yaml"; amend.write_text(yaml.safe_dump(doc, sort_keys=False))
    base = json.loads((tmp_path / "cov.json").read_text()); sel = tmp_path / "selection.json"; sel.write_text(json.dumps(base["selection"]))
    report = tmp_path / "ext.json"; fabricate_ext_report(lk, tmp_path / "cov.json", doc, report)
    return {"dir": tmp_path, "locked": locked, "amendment": amend, "report": report, "base_report": tmp_path / "cov.json", "selection": sel,
            "calibration": tmp_path / "cal.json", "tuned": tuned, "lk": lk}
