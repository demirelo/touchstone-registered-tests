import pytest
from sim.config import MarketConfig, ProviderParams


def with_last_provider(base, p):
    return MarketConfig(N=base.N, J=base.J, T=base.T, sigma=base.sigma, e=base.e,
                        v_min=base.v_min, v_max=base.v_max,
                        providers=base.providers[:-1] + (p,), alpha=base.alpha, budget=base.budget)


def test_default_config_is_valid():
    cfg = MarketConfig.default()
    cfg.validate()
    assert cfg.N == 10 and cfg.J == 50 and cfg.T == 200
    assert len(cfg.providers) == cfg.N


def test_validity_rejects_unprofitable_provider():
    cfg = with_last_provider(MarketConfig.default(), ProviderParams(q_max=0.5, a=0.5, b=0.5, k=5))
    with pytest.raises(ValueError, match="first-best weight"):
        cfg.validate()


def test_validity_rejects_zero_capacity():
    cfg = with_last_provider(MarketConfig.default(), ProviderParams(q_max=0.9, a=0.02, b=0.3, k=0))
    with pytest.raises(ValueError, match="capacity"):
        cfg.validate()


def test_validity_rejects_price_grid_condition():
    cfg = MarketConfig(N=1, J=5, T=2, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0,
                       providers=(ProviderParams(q_max=1.0, a=0.94, b=0.01, k=5),),
                       alpha=0.05, budget=0.0)
    with pytest.raises(ValueError, match="price grid"):
        cfg.validate()


def test_validity_price_grid_boundary_is_strict():
    cfg = MarketConfig(N=1, J=5, T=2, sigma=0.05, e=0.0, v_min=1.0, v_max=1.0,
                       providers=(ProviderParams(q_max=1.0, a=0.89, b=0.01, k=5),),
                       alpha=0.05, budget=0.0)
    with pytest.raises(ValueError, match="price grid"):
        cfg.validate()
