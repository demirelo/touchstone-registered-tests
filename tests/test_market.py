import numpy as np
import pytest
from sim.config import MarketConfig, ProviderParams
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.rng import make_draws


def b1():
    return PostedPrices(0.25, 0.40, 0.55)


def honest(n):
    return [HonestMax() for _ in range(n)]


def test_same_seed_same_result():
    cfg = MarketConfig.default()
    a, b = run_episode(cfg, b1(), honest(cfg.N), 5), run_episode(cfg, b1(), honest(cfg.N), 5)
    assert a.W == b.W and np.array_equal(a.profit, b.profit)
    assert np.array_equal(a.claims, b.claims, equal_nan=True)


def test_deviation_does_not_change_draw_contents():
    cfg = MarketConfig.default()
    d = make_draws(cfg, 9)
    snap = {k: getattr(d, k).copy() for k in ("values", "noise", "tie_key", "audit_u", "audit_key", "policy_seed")}
    dev = honest(cfg.N); dev[0] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    a = run_episode(cfg, b1(), honest(cfg.N), 9, draws=d)
    b = run_episode(cfg, b1(), dev, 9, draws=d)
    for k, arr in snap.items():
        assert np.array_equal(arr, getattr(d, k))
    assert not np.array_equal(a.profit, b.profit)


def test_capacity_above_jobs_runs():
    c0 = MarketConfig.default()
    big = tuple(ProviderParams(p.q_max, p.a, p.b, k=80) for p in c0.providers)
    cfg = MarketConfig(N=10, J=50, T=3, sigma=0.05, e=0.0, v_min=0.6, v_max=1.4, providers=big, alpha=0.05, budget=0.0)
    assert run_episode(cfg, b1(), honest(10), 1).served.sum() <= 150


def test_tied_values_deterministic():
    c0 = MarketConfig.default()
    cfg = MarketConfig(N=10, J=50, T=5, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0, providers=c0.providers, alpha=0.05, budget=0.0)
    a, b = run_episode(cfg, b1(), honest(10), 2), run_episode(cfg, b1(), honest(10), 2)
    assert np.array_equal(a.served, b.served)


def test_history_records_every_round():
    cfg = MarketConfig.default()
    res = run_episode(cfg, b1(), honest(cfg.N), 0)
    assert len(res.history) == cfg.T and res.history[0].t == 0 and res.history[-1].t == cfg.T - 1
    assert all(len(rec.audits) == 0 for rec in res.history)


def test_invalid_rule_output_is_rejected_before_money_moves():
    class BadRule(PostedPrices):
        def allocate(self, values_t, offers, view):
            return {j: 0 for j in range(7)}   # capacity is 6
    cfg = MarketConfig.default()
    with pytest.raises(ValueError, match="capacity"):
        run_episode(cfg, BadRule(0.25, 0.40, 0.55), honest(cfg.N), 0)


def test_rule_cannot_mutate_economic_state():
    class Sneaky(PostedPrices):
        def allocate(self, values_t, offers, view):
            view.banned_until[:] = 999
            return super().allocate(values_t, offers, view)
    cfg = MarketConfig.default()
    with pytest.raises(ValueError, match="read-only"):
        run_episode(cfg, Sneaky(0.25, 0.40, 0.55), honest(cfg.N), 0)
