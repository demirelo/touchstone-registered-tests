import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from sim.locked import load_locked
from sim.reference import ROW_FIELDS

ROOT = Path(__file__).resolve().parents[1]


def fake_sweep(tmp_path):
    out = tmp_path / "sweep"; (out / "evaluate").mkdir(parents=True); rng = np.random.default_rng(0)
    for rule, tol in (("B1", None), ("B2", 0.12)):
        for fam in ("D1", "D2"):
            for beta in (0.02, 0.05):
                rows = []
                for k, seed in enumerate(range(2000, 2020)):
                    r = {f: float(rng.uniform(0, 1)) for f in ROW_FIELDS}
                    r.update({"seed": seed, "sstar": 10.0, "gain": 0.2 + beta + rng.normal(0, 0.05), "audit_spend_attack": beta * 0.9,
                              "eff_honest": 0.99, "eff_ref": 0.97, "eff_clip": 0.95, "eff_attack": 0.90,
                              "cell": f"{rule}_{fam}_{beta}", "section": "development", "rule": rule, "family": fam, "beta": beta, "rho": 0.5,
                              "position": "median", "smoke": False, "reference": "honest_max", "budget": beta * 10})
                    rows.append(r)
                params = {"P1": 0.25, "P2": 0.4, "P3": 0.55} | ({"tol": tol, "L": 10} if tol else {})
                (out / "evaluate" / f"{rule}_{fam}_beta{beta}_rho0.5_median_development.json").write_text(json.dumps(
                    {"spec": {"name": f"{rule}_{fam}_beta{beta}_rho0.5_median_development", "section": "development", "rule": rule, "family": fam,
                              "beta": beta, "rho": 0.5, "position": "median"}, "params": params, "rows": rows}))
    return out


def test_plot_writes_figures_and_data(tmp_path):
    from scripts.plot import figure_frames
    from sim.coverage import ENDPOINTS, endpoint_key
    out = fake_sweep(tmp_path); lk = load_locked()
    f1, f2 = figure_frames(out, lk)
    assert len(f1) == 8 and set(f1.rule) == {"B1", "B2"} and (f1.gain_upper >= f1.gain_mean).all() and (f1.n_seeds == 20).all() and (f1.bound_method == "percentile (nominal)").all()
    cov = {"method_at_n": {"10": "t", "20": "studentized", "40": None}, "admitted_sides": {endpoint_key(s, side, lv, 20): "studentized" for s, side, lv in ENDPOINTS}}
    g1, _ = figure_frames(out, lk, coverage=cov)
    assert (g1.bound_method == "studentized").all() and not np.allclose(g1.gain_upper, f1.gain_upper)
    none, _ = figure_frames(out, lk, coverage={"method_at_n": {"20": None}, "admitted_sides": {}})
    assert (none.bound_method == "none").all() and none.gain_upper.isna().all()
    (out / "headline.json").write_text(json.dumps({"B2/D1": {"gain_train": {}, "headline": "high"}}))
    (out / "evaluate" / "B2_D1_beta0.05_rho0.5_high_development.json").write_text(
        (out / "evaluate" / "B2_D1_beta0.05_rho0.5_median_development.json").read_text().replace('"position": "median"', '"position": "high"').replace("_median_", "_high_"))
    h1, _ = figure_frames(out, lk)
    row = h1[(h1.rule == "B2") & (h1.family == "D1")]
    assert set(row[row.beta == 0.05].position) == {"high"} and set(row[row.beta == 0.02].position) == {"median"}    # headline position only at the headline beta
    h1dir = tmp_path / "h1"; h1dir.mkdir()
    pd.DataFrame({"rule": ["B2"] * 10, "beta": 0.05, "rep": range(10), "eval_seed": range(10), "sstar": 5.0, "gain": 0.3, "eff_attack": 0.9, "eff_clip": 0.92,
                  "eff_ref": 0.95, "audit_cost_attack": 0.1, "budget": 0.25, "invalid": 0}).to_csv(h1dir / "h1_rows.csv", index=False)
    with_h1, f2h = figure_frames(out, lk, h1_dir=h1dir)
    h1row = with_h1[with_h1.family == "H1"].iloc[0]
    assert (with_h1.family == "H1").sum() == 1 and h1row.n_seeds == 10 and h1row.bound_method == "t (nominal)" and f2h[f2h.family == "H1"].eff_honest.isna().all()
    from sim.intervals import t_bound
    assert h1row.gain_upper == pytest_approx(t_bound(np.full(10, 0.3), "upper", 0.95).value)
    b2 = f1[f1.rule == "B2"].iloc[0]; assert b2.honest_failure_rate == pytest_approx(stats.norm.cdf(-0.12 / lk["market"]["sigma"]))
    assert f1[f1.rule == "B1"].honest_failure_rate.eq(0.0).all()
    assert len(f2) == 8 and {"eff_honest", "eff_ref", "eff_clip", "eff_attack", "audit_spend"} <= set(f2.columns)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "plot.py"), "--sweep-out", str(out), "--out", str(tmp_path / "figs"), "--h1-dir", str(h1dir)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "figs" / "figure1_gain_vs_audit.png").stat().st_size > 1000 and (tmp_path / "figs" / "figure2_efficiency_quadruple.png").exists()
    assert len(pd.read_csv(tmp_path / "figs" / "figure_data.csv")) == 9


def pytest_approx(x):
    import pytest
    return pytest.approx(x)
