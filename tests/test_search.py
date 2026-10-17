import numpy as np
import pytest
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig, ProviderParams
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2, knob_key, exact_key
from sim.search import SearchSettings, Objective, cma_search, corner_controls, best_archived


def fixture_cfg(J=30):
    # every job accepts tier 3 at P3 = 0.5 (v_min 0.6 >= 0.5), P3 > a; 30 jobs so the focal serves at every tier
    c = MarketConfig.default()
    return MarketConfig(N=4, J=J, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=60, reeval_every=10,
                       near_corner=0.02, sobol_seed=3)
FULL = SearchSettings(popsize=8, sigma0=0.3, restarts=5, evals_per_restart=300, reeval_every=10, near_corner=0.02, sobol_seed=3)


class Flat:
    """Objective protocol stub: every point scores the same."""
    def __init__(self, family, value=0.0): self.family, self.value, self.evals, self.archive = family, value, 0, {}
    def knobs_of(self, x): return self.family.transform(x)
    def eval_knobs(self, knobs, source="search"): self.evals += 1; return self.value
    def __call__(self, x): return self.eval_knobs(self.knobs_of(x))


class PrefersIncumbent:
    """Stub: only the exact honest point (unreachable through the sigmoid) scores 2.0."""
    def __init__(self, family): self.family, self.evals, self.archive = family, 0, {}
    def knobs_of(self, x): return self.family.transform(x)
    def eval_knobs(self, knobs, source="search"):
        self.evals += 1
        return 2.0 if knobs == self.family.honest_point() else 1.0 - knobs["u"] * 0.1
    def __call__(self, x): return self.eval_knobs(self.knobs_of(x))


class PrefersProjection:
    """Stub: the evaluation made at the projection step scores highest."""
    def __init__(self, family): self.family, self.evals, self.archive = family, 0, {}
    def knobs_of(self, x): return self.family.transform(x)
    def eval_knobs(self, knobs, source="search"):
        self.evals += 1
        return 3.0 if source == "projection" else 1.0 - knobs["u"] * 0.1
    def __call__(self, x): return self.eval_knobs(self.knobs_of(x))


def test_search_recovers_b1_analytic_best_response_within_one_percent():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1, 2), name="b1fix")
    obj = Objective(cell, D1, cache)
    analytic = obj.eval_knobs({"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, source="analytic")
    res = cma_search(obj, D1, FULL, seed=0)
    assert res.best_f >= analytic * 0.99
    k = res.best_knobs
    assert k["clip"] == 0 and k["u"] > 0.99 and k["m"] - k["s"] >= 0.8
    assert res.evals == 5 * 300 and len(res.restart_bests) == 5
    # the optimizer, not only the registered near-full-cheat start (restart 0), reaches the optimum: a Sobol restart gets there
    assert max(res.restart_bests[2:]) >= analytic * 0.99
    assert res.replaced_by_projection is False and res.projection_f < res.best_f


def test_search_respects_budget_and_is_deterministic():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="b1fix")
    a = cma_search(Objective(cell, D2, cache), D2, SMALL, seed=1); b = cma_search(Objective(cell, D2, cache), D2, SMALL, seed=1)
    assert a.evals == 2 * 60 and a.best_f == b.best_f and np.array_equal(a.best_x, b.best_x)
    assert np.isfinite(a.best_f)
    assert len(a.archive) >= 100 and all(e.per_seed_profit.shape == (1,) for e in a.archive.values())


def test_flat_objective_terminates_and_counts():
    obj = Flat(D1)
    res = cma_search(obj, D1, SMALL, seed=0)
    assert res.evals == 120 and res.best_f == 0.0 and obj.evals == 120 + 1   # + the projection evaluation


def test_incumbents_and_projection_replace_the_best_when_higher():
    obj = PrefersIncumbent(D1)
    res = cma_search(obj, D1, SMALL, seed=0, incumbents={"honest_point": D1.honest_point()})
    assert res.incumbent_scores == {"honest_point": 2.0}
    assert res.best_f == 2.0 and res.best_knobs == D1.honest_point() and res.best_source == "incumbent:honest_point"
    assert res.projection_f == 2.0 and res.replaced_by_projection is False     # projection of a clip = 1 point is itself; not strictly higher
    res2 = cma_search(PrefersProjection(D1), D1, SMALL, seed=0)
    assert res2.replaced_by_projection is True and res2.best_knobs["clip"] == 1 and res2.best_source == "projection" and res2.best_f == 3.0


def test_force_clip_objective_never_inflates_and_archive_flags_inflation():
    cache = SeedCache()
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="b1fix")
    obj_t = Objective(cell, D1, cache, force_clip=True)
    k = {"u": 0.5, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}
    obj_t.eval_knobs(k)
    entry = next(iter(obj_t.archive.values()))
    assert entry.knobs["clip"] == 1 and entry.inflated is False
    obj = Objective(cell, D1, cache)
    obj.eval_knobs(k)
    e2 = next(iter(obj.archive.values()))
    assert e2.inflated is True and e2.knobs["clip"] == 0
    assert best_archived(obj.archive, clip=0, truthful_only=True) is None
    assert best_archived(obj.archive, clip=0) is e2
    # the archive never merges distinct policies: one ulp of u is a different entry with its own value
    obj.eval_knobs(dict(k, u=0.5 + 1e-12))
    assert len(obj.archive) == 2 and exact_key(dict(k, u=0.5 + 1e-12)) in obj.archive


def test_corner_controls_use_exact_knobs_at_tier_boundaries():
    c = MarketConfig.default()
    providers = (ProviderParams(q_max=0.8, a=0.02, b=0.32, k=6),) + c.providers[6:9]
    cfg = MarketConfig(N=4, J=30, T=5, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=providers, alpha=c.alpha, budget=0.0)
    cache = SeedCache()
    cell = Cell(cfg=cfg, rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=0, seeds=(1,), name="tier")
    obj = Objective(cell, D1, cache)
    ctrl = dict((exact_key(k), f) for k, f in corner_controls(obj, D1))
    honest = D1.honest_point()
    exact = ctrl[exact_key(honest)]
    via_inverse = obj(D1.inverse(honest, near=1e-9))
    assert exact > via_inverse            # claim 0.8 is tier 3 at P3; one ulp below is tier 2 at P2
    assert len(ctrl) == 32 and all(np.isfinite(f) for f in ctrl.values())


def test_objective_log_records_every_evaluation_including_repeats_and_survives_the_record_roundtrip():
    from sim.records import search_from_json, search_to_json
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    obj = Objective(cell, D1, SeedCache())
    k = {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}
    obj.eval_knobs(k, source="a"); obj.eval_knobs(k, source="b"); obj.eval_knobs({**k, "u": 0.6}, source="c")
    assert len(obj.archive) == 2 and len(obj.log) == 3 and [e["source"] for e in obj.log] == ["a", "b", "c"]       # the archive de-duplicates, the log does not
    assert all({"knobs", "f", "source", "per_seed_normalized"} <= set(e) for e in obj.log)
    res = cma_search(Objective(cell, D1, SeedCache()), D1, SMALL, seed=1)
    assert len(res.evaluations) == res.evals + 1 and len(res.trace) > 0                                             # every budgeted evaluation plus the projection
    back = search_from_json(search_to_json(res))
    assert back.trace == [list(t) if isinstance(t, tuple) else t for t in res.trace] or len(back.trace) == len(res.trace)
    assert len(back.evaluations) == len(res.evaluations) and back.evaluations[0]["source"] == res.evaluations[0]["source"]
    old = search_to_json(res); old.pop("trace"); old.pop("evaluations")
    assert search_from_json(old).evaluations == [] and search_from_json(old).trace == []                              # older records still load
