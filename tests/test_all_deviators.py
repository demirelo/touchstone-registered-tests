import numpy as np
import pytest
from sim.all_deviators import iterated_best_response
from sim.cell import SeedCache
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D2
from sim.search import SearchSettings


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=8, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


def test_iterated_best_response_terminates_and_records_profiles():
    cache = SeedCache()
    settings = SearchSettings(popsize=8, sigma0=0.3, restarts=1, evals_per_restart=16, reeval_every=10, near_corner=0.02, sobol_seed=3)
    res = iterated_best_response(fixture_cfg(), lambda: PostedPrices(0.20, 0.35, 0.50), D2, cache, settings, seeds=(1,), sweeps=2, eval_seeds=(2, 3))
    assert len(res.profiles) == 2 and all(len(p) == 4 for p in res.profiles)
    assert all(set(k) == set(D2.knobs) for p in res.profiles for k in p)
    assert len(res.values) == 2 and all(np.isfinite(v) for row in res.values for v in row)
    assert res.final_profile == res.profiles[-1] and np.isfinite(res.final_gross_eff) and res.eval_seeds == (2, 3)
    # under B1 without audits every provider gains from cheating: every provider's policy inflates (clip = 0) after sweep 1
    assert all(k["clip"] == 0 for k in res.profiles[0])
    assert cache.runs == 2 * 4 * (16 + 1 + 1) + 2     # per provider and sweep: search, projection, current-value evaluation; final profile on two evaluation seeds


def test_twin_procedure_keeps_every_provider_truthful():
    cache = SeedCache()
    settings = SearchSettings(popsize=8, sigma0=0.3, restarts=1, evals_per_restart=16, reeval_every=10, near_corner=0.02, sobol_seed=3)
    res = iterated_best_response(fixture_cfg(), lambda: PostedPrices(0.20, 0.35, 0.50), D2, cache, settings, seeds=(1,), sweeps=1, force_clip=True)
    assert all(k["clip"] == 1 for k in res.final_profile) and res.eval_seeds == (1,)
    assert all(v > 0.0 for v in res.final_normalized_profit)          # the twin procedure starts near honest, so truthful profit stays positive
