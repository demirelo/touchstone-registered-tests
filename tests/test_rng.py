import numpy as np
from sim.config import MarketConfig
from sim.rng import make_draws, draws_for_round


def test_draw_shapes_and_ranges():
    cfg = MarketConfig.default()
    d = make_draws(cfg, seed=7)
    assert d.values.shape == (cfg.T, cfg.J)
    assert d.noise.shape == (cfg.T, cfg.N, cfg.kmax)
    assert d.tie_key.shape == (cfg.T, cfg.J, cfg.N)
    assert d.audit_u.shape == (cfg.T,)
    assert d.audit_key.shape == (cfg.T, cfg.J)
    assert d.policy_seed.shape == (cfg.T, cfg.N)
    assert d.values.min() >= cfg.v_min and d.values.max() <= cfg.v_max
    assert abs(d.noise.std() - cfg.sigma) < 0.01
    assert 0.0 <= d.audit_u.min() and d.audit_u.max() < 1.0


def test_same_seed_same_draws_and_different_seed_differs():
    cfg = MarketConfig.default()
    a, b, c = make_draws(cfg, 3), make_draws(cfg, 3), make_draws(cfg, 4)
    for name in ("values", "noise", "tie_key", "audit_u", "audit_key", "policy_seed"):
        assert np.array_equal(getattr(a, name), getattr(b, name))
    assert not np.array_equal(a.values, c.values)


def test_round_draws_are_pure_function_of_seed_and_round():
    cfg = MarketConfig.default()
    full = make_draws(cfg, seed=11)
    for t in (0, 1, 57, cfg.T - 1):
        v, n, tk, au, ak, ps = draws_for_round(cfg, seed=11, t=t)
        assert np.array_equal(v, full.values[t])
        assert np.array_equal(n, full.noise[t])
        assert np.array_equal(tk, full.tie_key[t])
        assert au == full.audit_u[t]
        assert np.array_equal(ak, full.audit_key[t])
        assert np.array_equal(ps, full.policy_seed[t])
