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
