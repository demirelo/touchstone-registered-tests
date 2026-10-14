import numpy as np
import pytest
from sim.config import MarketConfig, ProviderParams
from sim.firstbest import first_best_round, first_best_episode
from sim.rng import make_draws


def one_provider(q_max=0.8, a=0.1, b=0.5, k=1, J=1, v=1.0):
    return MarketConfig(N=1, J=J, T=1, sigma=0.0, e=0.0, v_min=v, v_max=v,
                        providers=(ProviderParams(q_max=q_max, a=a, b=b, k=k),), alpha=0.0, budget=0.0)


def test_one_provider_one_job_closed_form():
    assert first_best_round(one_provider(), np.array([1.0])) == pytest.approx(0.3)


def test_capacity_exceeds_jobs():
    assert first_best_round(one_provider(k=7, J=2), np.array([1.0, 1.0])) == pytest.approx(0.6)


def test_jobs_exceed_capacity_picks_highest_values():
    cfg = MarketConfig(N=1, J=3, T=1, sigma=0.0, e=0.0, v_min=0.6, v_max=2.0,
                       providers=(ProviderParams(q_max=1.0, a=0.0, b=0.5, k=2),), alpha=0.0, budget=0.0)
    assert first_best_round(cfg, np.array([2.0, 1.0, 0.6])) == pytest.approx(2.0)


def test_episode_sums_rounds_and_is_positive():
    cfg = MarketConfig.default()
    d = make_draws(cfg, seed=1)
    total = first_best_episode(cfg, d)
    assert total == pytest.approx(sum(first_best_round(cfg, d.values[t]) for t in range(cfg.T)))
    assert total > 0
