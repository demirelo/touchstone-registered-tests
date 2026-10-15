import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1
from sim.positions import positions, headline_position
from sim.search import SearchSettings, Objective
from sim.search_checks import restart_spread, doubling_check, twin_vs_honest, FixedClipObjective
from sim.reference import twin_search, attack_search, REFERENCE_ORDER


def test_positions_by_b_times_qmax_and_headline():
    cfg = MarketConfig.default()
    pos = positions(cfg)
    score = [p.b * p.q_max for p in cfg.providers]
    order = sorted(range(cfg.N), key=lambda i: (score[i], i))
    assert pos == {"low": order[0], "median": order[cfg.N // 2], "high": order[-1]}
    assert headline_position({"low": 0.1, "median": 0.3, "high": 0.3}) == "median"
    assert headline_position({"low": 0.5, "median": 0.3, "high": 0.3}) == "low"


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=24, reeval_every=10, near_corner=0.02, sobol_seed=3)


def test_fixed_clip_objective_fixes_the_clip():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    f0 = FixedClipObjective(Objective(cell, D1, cache), clip=0); f1 = FixedClipObjective(Objective(cell, D1, cache), clip=1)
    x = np.full(D1.dim, 3.0)
    assert f0.knobs_of(x)["clip"] == 0 and f1.knobs_of(x)["clip"] == 1
    f0(x); f1(x)
    assert all(e.knobs["clip"] == 0 for e in f0.archive.values()) and all(e.knobs["clip"] == 1 for e in f1.archive.values())


def test_doubling_spread_and_twin_vs_honest():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    runs_before = cache.runs
    dc = doubling_check(cell, D1, cache, SMALL, seed=0, base_attack=at, base_twin=tw, bank_members=[], order=REFERENCE_ORDER)
    # two fixed-clip searches at half the budget each, plus two projections and one honest-max run for each reference selection
    assert cache.runs - runs_before == 2 * (2 * 12) + 2 * 1 + 2 * 1
    assert dc.attack_doubled_f >= dc.attack_base_f - 1e-12 and np.isfinite(dc.clip0_f) and np.isfinite(dc.clip1_f)
    assert dc.clip0_f >= dc.clip0_search_f and dc.clip1_f >= dc.clip1_search_f
    assert dc.delta_gain == pytest.approx(dc.gain_doubled - dc.gain_base) and isinstance(dc.passed, bool)
    assert dc.ref_base_name in REFERENCE_ORDER or dc.ref_base_name.startswith("bank_")
    sp = restart_spread(at, tw)
    assert sp["attack_spread"] >= 0.0 and sp["reference_spread"] >= 0.0 and len(sp["attack_bests"]) == 2
    assert sp["gain_bests"] == [a - r for a, r in zip(sp["attack_bests"], sp["reference_bests"])] and sp["gain_spread"] >= 0.0
    chk = twin_vs_honest(tw, honest_f=at.incumbent_scores["honest_point"])
    assert chk.passed is (chk.twin_f >= chk.honest_f - 0.01 * abs(chk.honest_f))
