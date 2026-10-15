import numpy as np
import pytest
from sim.cell import SeedCache, Cell, run_focal, run_profile, Abstain, market_key
from sim.config import MarketConfig, ProviderParams
from sim.mechanisms.posted import PostedPrices
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat


def tiny(budget=0.0, T=10, alpha=None):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=12, T=T, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers[6:10], alpha=c.alpha if alpha is None else alpha, budget=budget)


def test_cache_keys_on_market_not_on_budget():
    cache = SeedCache()
    cfg = tiny()
    d1, s1 = cache.get(cfg, 1); d2, s2 = cache.get(tiny(budget=3.0, alpha=0.1), 1)
    assert d1 is d2 and s1 == s2 and cache.hits == 1 and cache.misses == 1
    assert market_key(tiny(T=11)) != market_key(cfg)
    cache.get(tiny(T=11), 1)
    assert cache.misses == 2


def test_run_focal_normalizes_by_sstar_over_n_and_counts_runs():
    cache = SeedCache()
    cell = Cell(cfg=tiny(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=3, seeds=(1, 2, 3), name="t")
    fr = run_focal(cell, lambda: HonestMax(), cache)
    assert fr.profit.shape == (3,) and fr.normalized.shape == (3,) and cache.runs == 3
    for k, res in enumerate(fr.results):
        assert fr.normalized[k] == pytest.approx(fr.profit[k] / (res.sstar / 4))
    assert fr.inflated is False and not fr.inflated_per_seed.any()


def test_inflation_flag_and_others():
    cache = SeedCache()
    cell = Cell(cfg=tiny(), rule_factory=lambda: PostedPrices(0.25, 0.40, 0.55), focal=3, seeds=(1,), name="t",
                others=((0, lambda: FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)),))
    fr = run_focal(cell, lambda: FixedCheat(u=0.5, m=1.0, s=0.0, w=0.0, clip=0), cache)
    assert fr.inflated is True
    assert fr.results[0].efforts[0, 0] == 0.0                 # entity 0 played the cheat named in `others`
    fr2 = run_focal(cell, lambda: FixedCheat(u=0.5, m=1.0, s=0.0, w=0.0, clip=1), cache)
    assert fr2.inflated is False
    fr3 = run_focal(cell, lambda: FixedCheat(u=0.5, m=0.2, s=0.2, w=0.0, clip=0), cache)   # claim == effort exactly: truthful
    assert fr3.inflated is False
    fr4 = run_focal(cell, lambda: FixedCheat(u=0.5, m=0.2 + 1e-13, s=0.2, w=0.0, clip=0), cache)   # any positive excess inflates
    assert fr4.inflated is True


def test_run_profile_and_abstain():
    cache = SeedCache()
    cfg = tiny()
    res = run_profile(cfg, lambda: PostedPrices(0.25, 0.40, 0.55), [Abstain, HonestMax, HonestMax, HonestMax], (1,), cache)
    assert res[0].profit[0] == 0.0 and res[0].served[:, 0].sum() == 0 and cache.runs == 1
