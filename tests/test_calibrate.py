import json, subprocess, sys
import numpy as np
import pytest
from sim.calibrate import calibrate, cell_config, first_best_served, load_calibration, save_calibration
from sim.cell import market_key
from sim.config import MarketConfig, ProviderParams
from sim.locked import load_locked, market_config_from_locked


def test_first_best_served_counts_positive_pairs():
    cfg = MarketConfig(N=1, J=3, T=1, sigma=0.0, e=0.0, v_min=0.6, v_max=2.0,
                       providers=(ProviderParams(q_max=1.0, a=0.0, b=0.5, k=2),), alpha=0.0, budget=0.0)
    assert first_best_served(cfg, np.array([2.0, 1.0, 0.6])) == 2


def test_calibration_binds_to_the_market_and_cells_derive_alpha_and_budget():
    cfg = market_config_from_locked(load_locked())
    cal = calibrate(cfg, seeds=[4000, 4001])
    assert cal.S_hat > 0 and cal.n_FB > 0 and cal.m == pytest.approx(cal.S_hat / cal.n_FB)
    assert cal.market_key == market_key(cfg) and cal.T == cfg.T
    c = cell_config(cfg, cal, rho=0.2, beta=0.05)
    c.validate()
    assert c.alpha == pytest.approx(0.2 * cal.m) and c.budget == pytest.approx(0.05 * cal.S_hat)
    assert cell_config(cfg, cal, rho=1.0, beta=0.0).budget == 0.0


def test_calibrate_refuses_invalid_config_and_empty_seeds():
    c = MarketConfig.default()
    bad = MarketConfig(N=c.N, J=c.J, T=c.T, sigma=c.sigma, e=c.e, v_min=0.1, v_max=c.v_max, providers=c.providers, alpha=0.0, budget=0.0)
    with pytest.raises(ValueError):
        calibrate(bad, seeds=[4000])
    with pytest.raises(ValueError):
        calibrate(c, seeds=[])


def test_cell_config_refuses_foreign_calibration(tmp_path):
    cfg = market_config_from_locked(load_locked())
    cal = calibrate(cfg, seeds=[4000])
    other = MarketConfig(N=cfg.N, J=cfg.J, T=cfg.T + 1, sigma=cfg.sigma, e=cfg.e, v_min=cfg.v_min, v_max=cfg.v_max,
                         providers=cfg.providers, alpha=0.0, budget=0.0)
    with pytest.raises(ValueError, match="calibration"):
        cell_config(other, cal, rho=0.2, beta=0.05)
    p = tmp_path / "cal.json"; save_calibration(cal, p)
    assert load_calibration(p) == cal


def test_calibrate_script_writes_json(tmp_path):
    out = tmp_path / "cal.json"
    subprocess.run([sys.executable, "scripts/calibrate.py", "--seeds", "2", "--out", str(out)], check=True)
    cal = json.loads(out.read_text())
    assert set(cal) == {"S_hat", "n_FB", "m", "market_key", "T", "seeds"} and cal["seeds"] == [4000, 4001]
