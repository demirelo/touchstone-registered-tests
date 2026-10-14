import numpy as np
import pytest
from scipy import stats
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.audit_random import spread_audit_count
from sim.mechanisms.base import Consequences
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.rng import make_draws


def b2(tol=0.12, L=10):
    return PostedRandomAudit(0.25, 0.40, 0.55, tol=tol, L=L)


def cfgb(budget, T=200, sigma=0.05):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def honest(n):
    return [HonestMax() for _ in range(n)]


def test_spread_count_exact_rounding_and_caps():
    assert spread_audit_count(100, 0, 8, 1000, 25, audit_u=0.49) == 13   # target 12.5
    assert spread_audit_count(100, 0, 8, 1000, 25, audit_u=0.51) == 12
    assert spread_audit_count(0, 5, 10, 50, 10, 0.3) == 0
    assert spread_audit_count(1, 9, 10, 50, 10, 0.99) == 1
    assert spread_audit_count(1000, 0, 10, 50, 1, 0.0) == 1
    assert spread_audit_count(1000, 0, 1, 3, 1000, 0.0) == 3


def test_integer_allowance_is_fully_spent_when_affordable():
    cfg = cfgb(budget=2.0)   # floor(2.0 / 0.05) = 40 audits
    for seed in range(5):
        res = run_episode(cfg, b2(L=0), honest(cfg.N), seed)
        assert res.audits.sum() == 40
        assert res.audit_cost == pytest.approx(40 * cfg.alpha)
        assert res.audits.max() <= 1


def test_budget_never_exceeded_and_cap_holds():
    cfg = cfgb(budget=3.0)
    for seed in range(5):
        res = run_episode(cfg, b2(), honest(cfg.N), seed)
        assert res.audits.sum() <= int(np.floor(cfg.budget / cfg.alpha + 1e-12))
        assert res.audits.max() <= max(1, int(np.floor(2 * cfg.budget / (cfg.T * cfg.alpha))))


def test_audit_count_in_round_is_action_independent():
    cfg = cfgb(budget=20.0, T=50)
    d = make_draws(cfg, 3)
    dev = honest(cfg.N); dev[0] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    a = run_episode(cfg, b2(L=0), honest(cfg.N), 3, draws=d)
    b = run_episode(cfg, b2(L=0), dev, 3, draws=d)
    assert np.array_equal(a.audits, b.audits)


def test_honest_failure_rate_matches_formula():
    cfg = cfgb(budget=40.0, T=100)
    tol = 0.08
    fails = auds = 0
    for seed in range(6):
        res = run_episode(cfg, b2(tol=tol, L=0), honest(cfg.N), seed)
        fails += res.failures.sum(); auds += res.audits.sum()
    p = stats.norm.cdf(-tol / cfg.sigma)
    assert abs(fails / auds - p) < 4 * np.sqrt(p * (1 - p) / auds) + 0.005


def test_spread_halves_hypergeometric_criterion():
    cfg = cfgb(budget=2.0)
    diffs = []
    for seed in range(200):
        res = run_episode(cfg, b2(L=0), honest(cfg.N), seed)
        diffs.append(abs(int(res.audits[:100].sum()) - int(res.audits[100:].sum())))
    hg = stats.hypergeom(200, 100, 40)
    k = np.arange(0, 41)
    expected = float((hg.pmf(k) * np.abs(2 * k - 40)).sum())
    sd = float(np.sqrt((hg.pmf(k) * (np.abs(2 * k - 40) - expected) ** 2).sum()))
    assert abs(np.mean(diffs) - expected) <= 2 * sd / np.sqrt(200) + 0.5


def test_all_providers_banned_round_is_fine():
    cfg = cfgb(budget=50.0, T=30)
    res = run_episode(cfg, b2(tol=-10.0, L=20), honest(cfg.N), 0)
    assert np.isfinite(res.W) and (res.served.sum(axis=1) == 0).any()


def test_negative_delivery_exact_contribution_and_failure():
    c = MarketConfig.default()
    cfg = MarketConfig(N=1, J=1, T=1, sigma=2.0, e=0.0, v_min=1.0, v_max=1.0,
                       providers=(c.providers[9],), alpha=0.05, budget=0.05)
    seed = next(s for s in range(50) if 1.0 + make_draws(cfg, s).noise[0, 0, 0] < 0.0)
    d = make_draws(cfg, seed)
    res = run_episode(cfg, b2(tol=0.0, L=0), honest(1), seed, draws=d)
    y = 1.0 + d.noise[0, 0, 0]
    assert y < 0.0
    assert res.value == pytest.approx(1.0 * y)
    assert res.failures.sum() == 1


def test_failed_audit_without_refund_still_counts_as_failure():
    class NoRefund(PostedRandomAudit):
        def enforce(self, records, view):
            return Consequences()
    cfg = cfgb(budget=40.0, T=50)
    res = run_episode(cfg, NoRefund(0.25, 0.40, 0.55, tol=0.0, L=0), honest(cfg.N), 0)
    assert res.failures.sum() > 0 and res.ledger.refunds.sum() == 0.0


def test_realized_audit_cost_never_exceeds_budget_by_rounding():
    for budget in (0.15, 0.3, 3.0):
        cfg = cfgb(budget=budget, T=20)
        res = run_episode(cfg, b2(L=0), honest(cfg.N), 0)
        assert res.audit_cost <= cfg.budget
        assert res.audits.sum() == int(np.floor(cfg.budget / cfg.alpha + 1e-12))
