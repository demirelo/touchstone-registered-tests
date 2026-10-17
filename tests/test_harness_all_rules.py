import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.second_score import SecondScore
from sim.metrics import gain
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.twin import Twin
from sim.rng import make_draws

RULES = [PostedPrices(0.25, 0.40, 0.55), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), SecondScore(tol=0.12, L=10)]
try:                                                                   # amendment 2: the proposed rule's two allocations join the harness once the module exists
    from sim.mechanisms import proposed as _proposed
    RULES += [_proposed.make({"allocation": "A", "targeting": "T1", "tol": 0.12, "L": 10}),
              _proposed.make({"allocation": "B", "targeting": "T2", "tol": 0.12, "L": 10, "P1": 0.25, "P2": 0.40, "P3": 0.55})]
except ImportError:
    pass
IDS = [r.name + (f"_{r.allocation}_{r.targeting}" if r.name == "proposed" else "") for r in RULES]


def tiny(budget=0.5):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=20, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def honest(n):
    return [HonestMax() for _ in range(n)]


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_tiny_market_runs_and_conserves(rule):
    cfg = tiny()
    res = run_episode(cfg, rule, honest(cfg.N), 0)
    assert np.isfinite(res.W) and res.sstar > 0
    res.ledger.check_conservation(0.0)


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_all_honest_mean_gross_efficiency_at_most_one(rule):
    cfg = tiny()
    effs = np.array([(lambda r: (r.W + r.audit_cost) / r.sstar)(run_episode(cfg, rule, honest(cfg.N), s)) for s in range(20)])
    assert effs.mean() <= 1.0 + 2 * effs.std(ddof=1) / np.sqrt(20)
    assert effs.mean() > 0.4


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_honest_max_equals_its_twin_round_by_round(rule):
    cfg = tiny()
    d = make_draws(cfg, 3)
    twins = honest(cfg.N); twins[4] = Twin(HonestMax())
    a, b = run_episode(cfg, rule, honest(cfg.N), 3, draws=d), run_episode(cfg, rule, twins, 3, draws=d)
    assert np.array_equal(a.claims, b.claims, equal_nan=True) and np.array_equal(a.served, b.served)
    assert gain(a, b, focal=4) == 0.0


@pytest.mark.parametrize("rule", RULES, ids=IDS)
def test_twin_claim_never_exceeds_effort(rule):
    cfg = tiny()
    res = run_episode(cfg, rule, [Twin(FixedCheat(u=0.3, m=0.8, s=0.0, w=0.2, clip=0)) for _ in range(cfg.N)], 1)
    assert np.all(np.nan_to_num(res.claims, nan=-1.0) <= res.efforts + 1e-12)
