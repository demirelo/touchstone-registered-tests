import json, subprocess, sys
import pytest
from sim.cell import SeedCache
from sim.config import MarketConfig
from sim.locked import load_locked
from sim.tuning import price_grid, tuning_grid, rule_from_params, score_point, tune


def test_price_grid_is_27_ordered_positive_triples():
    cfg = MarketConfig.default()
    g = price_grid(cfg, [0.5, 0.7, 0.9])
    assert len(g) == 27
    for p1, p2, p3 in g:
        assert 0 < p1 < p2 < p3
    assert max(t[2] for t in g) == pytest.approx(0.9 * cfg.q90)
    assert min(t[2] for t in g) == pytest.approx(float(cfg.cost_full.min()))


def test_tuning_grids_sizes_and_rule_construction():
    lk = load_locked(); cfg = MarketConfig.default()
    assert len(tuning_grid("B1", cfg, lk)) == 27
    assert len(tuning_grid("B2", cfg, lk)) == 27 * 3 * 3
    assert len(tuning_grid("B3", cfg, lk)) == 9
    r = rule_from_params("B2", tuning_grid("B2", cfg, lk)[0])
    assert r.name == "B2_posted_random_audit" and r.L in (10, 20, 50)


def small_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers[6:10], alpha=0.05, budget=0.3)


QUICK = {"inner_evals": 16, "inner_seeds": 1, "recheck_top": 1, "recheck_evals": 16, "recheck_restarts": 1, "recheck_val_seeds": 2}


def test_inner_score_is_in_sample_and_recheck_scores_on_dev_val():
    lk = load_locked(); cfg = small_cfg(); cache = SeedCache()
    params = {"P1": 0.9, "P2": 1.0, "P3": 1.2, "tol": 0.12, "L": 10}   # tier 3 unaffordable for most jobs
    sc = score_point("B2", params, cfg, lk, cache, inner_override=QUICK)
    assert sc.namespace == "dev_train" and sc.margin <= 0.0 and sc.eff < 0.9
    rc = score_point("B2", params, cfg, lk, cache, inner_override=QUICK, recheck=True)
    assert rc.namespace == "dev_val" and rc.margin == pytest.approx(min((rc.eff - 0.90) / 0.90, (0.30 - rc.gain) / 0.30))
    b1 = score_point("B1", {"P1": 0.20, "P2": 0.35, "P3": 0.50}, cfg, lk, cache, inner_override=QUICK)
    assert b1.gain > 0.0                       # a one-restart inner search starts near full cheat, so B1's manipulability is measured


def test_quick_tune_terminates_and_picks_by_recheck():
    lk = load_locked(); cache = SeedCache()
    res = tune("B2", small_cfg(), lk, cache, inner_override=QUICK, grid_limit=3)
    assert res.best_params in [s["params"] for s in res.scores] and len(res.rechecked) == 1
    assert res.rechecked[0]["namespace"] == "dev_val" and res.best_params == res.rechecked[0]["params"]


def test_tune_script_quick(tmp_path):
    cal = {"S_hat": 1.0, "n_FB": 1.0, "m": 1.0, "market_key": "x", "T": 200, "seeds": [4000]}
    # a foreign calibration must be refused
    calp = tmp_path / "cal.json"; calp.write_text(json.dumps(cal))
    r = subprocess.run([sys.executable, "scripts/tune_baselines.py", "--calibration", str(calp), "--rule", "B3",
                        "--out", str(tmp_path / "t.json"), "--quick"], capture_output=True, text=True)
    assert r.returncode != 0 and "calibration" in (r.stderr + r.stdout)
