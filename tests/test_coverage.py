import numpy as np
import pytest
from scipy import stats

from sim.coverage import (ENDPOINTS, PROCEDURES_AT_N, BASE_N, endpoint_key, skewness, sarle_bimodality, select_cells, seed_blocks, CoverageCellSpec,
                          trajectory_keys, runs_per_seed, observe, observe_chunk, reference_interval, covered, measure, analytic_conservative_coverage,
                          simulated_conservative_coverage, threshold_check, thresholds, clopper_pearson_lower, joint_fixture, control_power, power_check,
                          fixture_and_power, admission, write_report, load_report)
from sim.config import MarketConfig
from sim.intervals import Bound
from sim.locked import load_locked
from sim.records import cfg_to_dict
from sim.registry import available_families


def test_endpoints_and_moments():
    assert len(ENDPOINTS) == 8 and ENDPOINTS[0] == ("gain", "upper", 0.95) and ENDPOINTS[4] == ("loss_diff", "lower", 0.9875)
    assert PROCEDURES_AT_N == {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)} and BASE_N == (10, 20)
    assert endpoint_key("gain", "upper", 0.95, 20) == "gain|upper|0.95|20"
    x = np.array([1.0, 2.0, 3.0, 10.0])
    assert skewness(x) == pytest.approx(stats.skew(x, bias=False))
    g, k, n = stats.skew(x, bias=False), stats.kurtosis(x, bias=False), 4
    assert sarle_bimodality(x) == pytest.approx((g * g + 1) / (k + 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))))
    assert np.isnan(skewness(np.array([1.0, 1.0, 1.0]))) and np.isnan(sarle_bimodality(np.array([1.0, 2.0, 3.0])))


def test_cell_selection_handles_degenerate_rankings():
    nan = float("nan")
    st = {"a": {"skew_gain": 3.0, "sarle_bans": 0.9}, "b": {"skew_gain": 2.0, "sarle_bans": 0.1}, "c": {"skew_gain": 1.0, "sarle_bans": 0.5},
          "d": {"skew_gain": 0.5, "sarle_bans": 0.8}, "e": {"skew_gain": 0.1, "sarle_bans": nan}, "f": {"skew_gain": nan, "sarle_bans": 0.7},
          "g": {"skew_gain": -1.0, "sarle_bans": 0.0}}
    # skew ranking a b c d e g; sarle ranking a d f c b g; union of the top threes = a b c d f (5); skew contributed 3 distinct,
    # sarle 2 new (a overlapped) -> fill from sarle: c (used), b (used), g -> a b c d f g
    assert select_cells(st, k=3) == ["a", "b", "c", "d", "f", "g"]
    st2 = {"a": {"skew_gain": 1.0, "sarle_bans": 1.0}, "b": {"skew_gain": 0.0, "sarle_bans": nan}, "c": {"skew_gain": nan, "sarle_bans": nan}}
    assert select_cells(st2, k=3) == ["a", "b"]                   # both rankings exhausted: fewer than 6
    st3 = {n: {"skew_gain": v, "sarle_bans": nan} for n, v in zip("abcdefg", range(7, 0, -1))}
    assert select_cells(st3, k=3) == ["a", "b", "c", "d", "e", "f"]   # the Sarle ranking is empty: skewness fills


def test_seed_blocks_are_fresh_disjoint_and_bounded():
    lk = load_locked(); cov = lk["seeds"]["coverage"]
    pool, reps = seed_blocks(lk, 0)
    assert pool[0] == cov["start"] and len(pool) == cov["pool"]
    assert reps[10].shape == (2000, 10) and reps[20].shape == (2000, 20) and reps[40].shape == (4000, 40)
    allseeds = np.concatenate([pool] + [r.ravel() for r in reps.values()])
    assert len(np.unique(allseeds)) == len(allseeds) and allseeds.max() < cov["start"] + cov["block"]
    pool1, _ = seed_blocks(lk, 1); assert pool1[0] == cov["start"] + cov["block"]
    _, base = seed_blocks(lk, 0, n_list=BASE_N)
    assert set(base) == {10, 20} and np.array_equal(base[20], reps[20])       # a base-only run uses the same seeds as the full layout
    pool2, reps2 = seed_blocks(lk, 2, pool_factor=2, rep_factor=2); pool1b, reps1b = seed_blocks(lk, 2)
    assert len(pool2) == 2 * cov["pool"] and reps2[40].shape == (8000, 40)
    assert np.array_equal(pool2[:cov["pool"]], pool1b) and np.array_equal(reps2[40][:4000], reps1b[40])        # a doubling extends, it never moves
    mixed_pool, mixed_reps = seed_blocks(lk, 2, pool_factor=2, rep_factor=1, n_list=(20,))
    assert np.array_equal(mixed_reps[20], reps1b[20]) and not set(mixed_pool.tolist()) & set(mixed_reps[20].ravel().tolist())   # the layout does not depend on another n's factors
    with pytest.raises(ValueError):
        seed_blocks(dict(lk, seeds=dict(lk["seeds"], coverage=dict(cov, block=1000))), 0)


def small_spec(rule="B1", ref=True):
    c = MarketConfig.default()
    cfg = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=c.alpha, budget=0.3)
    params = {"B1": {"P1": 0.2, "P2": 0.35, "P3": 0.5}, "B2": {"P1": 0.2, "P2": 0.35, "P3": 0.5, "tol": 0.12, "L": 3}, "B3": {"tol": 0.12, "L": 3}}
    cheat = {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0.0}
    return CoverageCellSpec(name=f"x_{rule}", cfg=cfg_to_dict(cfg), focal=3, rule=rule, family="D1", params_by_rule=params,
                            attack_knobs_by_rule={r: dict(cheat) for r in params}, ref_candidate={"name": "honest_max", "knobs": None} if ref else None)


def test_observe_is_chunked_scalar_and_pair_invariant():
    fams = available_families()
    s1 = small_spec("B1"); s2 = small_spec("B2", ref=False)
    assert runs_per_seed(s1) == 7 and runs_per_seed(s2) == 4 and ("B2", "clip") in trajectory_keys(s2) and ("B2", "ref") not in trajectory_keys(s2)
    seeds = np.arange(6)
    obs = observe(s1, seeds, chunk=2); whole = observe_chunk(s1, seeds, fams); par = observe(s1, seeds, chunk=2, workers=2)
    assert set(obs) == {"gain", "eff", "loss_diff"} and all(v.shape == (6,) and np.all(np.isfinite(v)) for v in obs.values())
    for k in obs:
        assert np.array_equal(obs[k], whole[k]) and np.array_equal(par[k], whole[k])   # chunking and the process pool do not change the observations
    obs2 = observe(s2, seeds, chunk=4)
    assert np.array_equal(obs["loss_diff"], obs2["loss_diff"])                # the pair statistic does not depend on the cell's rule


def test_pool_cache_extends_returns_prefixes_and_refuses_other_inputs(tmp_path):
    from scripts.coverage_study import input_hash, pool_observations
    s1 = small_spec("B1"); prov = {"settings_hash": "x"}; key = input_hash(s1, prov)
    base = np.arange(4); doubled = np.arange(8)
    o1, n1 = pool_observations(s1, base, tmp_path, 0, 1, key); assert n1 == 4 and o1["gain"].shape == (4,)
    o2, n2 = pool_observations(s1, doubled, tmp_path, 0, 1, key); assert n2 == 4 and np.array_equal(o2["gain"][:4], o1["gain"])   # extended with the missing seeds only
    o3, n3 = pool_observations(s1, base, tmp_path, 0, 1, key); assert n3 == 0 and np.array_equal(o3["gain"], o1["gain"])        # a shorter request is a prefix, never a refusal
    assert input_hash(small_spec("B2", ref=False), prov) != key
    import pytest as _pt
    with _pt.raises(SystemExit, match="input hash"):
        pool_observations(s1, base, tmp_path, 0, 1, input_hash(s1, {"settings_hash": "y"}))                                      # other inputs never reuse the cache


def test_reference_interval_and_conservative_scoring():
    rng = np.random.default_rng(1); pool = rng.normal(0.0, 1.0, size=5000)
    lo, hi, se = reference_interval(pool, 0.95)
    assert lo < pool.mean() < hi and se == pytest.approx(pool.std(ddof=1) / np.sqrt(5000)) and hi - lo == pytest.approx(2 * stats.t.ppf(0.975, 4999) * se)
    assert covered(Bound(hi + 0.01, "upper", 0.95, "t", False, 10), lo, hi) and not covered(Bound(hi - 0.01, "upper", 0.95, "t", False, 10), lo, hi)
    assert covered(Bound(lo - 0.01, "lower", 0.95, "t", False, 10), lo, hi) and not covered(Bound(lo + 0.01, "lower", 0.95, "t", False, 10), lo, hi)


def test_measure_runs_every_endpoint_and_procedure():
    rng = np.random.default_rng(2)
    samples = {s: rng.normal(size=(50, 20)) for s in ("gain", "eff", "loss_diff")}
    out = measure(samples, {s: (-0.05, 0.05) for s in samples}, 20, ("percentile", "studentized"), {"bootstrap_resamples": 200, "bootstrap_seed": 3})
    assert len(out) == 16 and all(0.0 <= v <= 1.0 for v in out.values())
    assert "gain|upper|0.95|20|percentile" in out and "loss_diff|lower|0.9875|20|studentized" in out


def test_analytic_threshold_matches_simulation_and_nominal_limit():
    assert analytic_conservative_coverage(20, stats.t.ppf(0.95, 19), 10**9) == pytest.approx(0.95, abs=1e-4)
    a = analytic_conservative_coverage(20, stats.t.ppf(0.95, 19), 2000)
    s = simulated_conservative_coverage(20, 0.95, 2000, pools=40, reps=4000, rng=np.random.default_rng(4))
    assert a < 0.95 and abs(a - s) < 0.01
    lk = load_locked(); thr = thresholds(lk, 35000)
    assert set(thr) == {f"{n}|{lv}" for n in (10, 20, 40) for lv in (0.95, 0.9875)}
    assert thr["20|0.95"]["threshold"] == pytest.approx(thr["20|0.95"]["exact"] - 0.02) and thr["40|0.9875"]["margin"] == 1.0
    chk = threshold_check(lk, 2000, pools=20, reps=2000, rng=np.random.default_rng(5))
    assert set(chk) == set(thr) and all(abs(v["gap"]) < 0.02 and v["se"] > 0 for v in chk.values())


def test_clopper_pearson_and_joint_fixture_small():
    assert clopper_pearson_lower(190, 200, 1 - 0.05 / 3) == pytest.approx(0.9063, abs=5e-4)
    assert clopper_pearson_lower(189, 200, 1 - 0.05 / 3) < 0.9 and clopper_pearson_lower(0, 10, 0.95) == 0.0
    lk = load_locked(); thr = thresholds(lk, 500)
    res = joint_fixture(lk, 20, 500, 60, thr, trials=8, rng=np.random.default_rng(5), cells=2)
    assert res["trials"] == 8 and 0 <= res["admitted"] <= 8 and 0.0 <= res["lower_limit"] <= 1.0 and isinstance(res["pass_"], bool) and res["endpoints_per_cell"] == 8


def test_control_power_is_high_for_a_3_point_deficit_and_quadrature_converges():
    lk = load_locked(); thr = thresholds(lk, 35000)
    p200 = control_power(20, 0.95, 3.0, 35000, 2000, thr["20|0.95"]["threshold"], nodes=200)
    p400 = control_power(20, 0.95, 3.0, 35000, 2000, thr["20|0.95"]["threshold"], nodes=400)
    assert np.isfinite(p200) and np.isfinite(p400) and p200 > 0.8 and abs(p200 - p400) <= 0.001
    pc = power_check(lk, 35000, {10: 2000, 20: 2000, 40: 4000}, thr)
    assert set(pc) == set(thr) and all(v["converged"] and np.isfinite(v["power_400"]) for v in pc.values())
    assert min(v["power_200"] for v in pc.values()) > 0.9                     # spec 8 reports a minimum of about 0.938


def test_fixture_and_power_smoke_shape():
    lk = load_locked()
    fp = fixture_and_power(lk, smoke=True, rng=np.random.default_rng(6), n_list=(10, 20))
    assert set(fp["per_n"]) == {"10", "20"} and set(fp["remedies"]) == {"10", "20"} and str(fp["base_M"]) in fp["threshold_check"]
    assert all(a["fixture"]["M"] == fp["base_M"] * a["pool_factor"] and a["fixture"]["R"] == int(fp["base_R"][n]) * a["rep_factor"]
               and str(a["M"]) in fp["threshold_check"] for n, atts in fp["per_n"].items() for a in atts)   # one coherent (M, R) per attempt, each M cross-checked
    assert np.isfinite(control_power(20, 0.9875, 1.5, 200, 20, 0.9, nodes=400))                     # the smoke M: NaN tails are filled, no FloatingPointError
    from sim.coverage import _tail_fill
    assert _tail_fill(np.array([np.nan, np.nan, 0.5]), np.array([50.0, -50.0, 0.0])).tolist() == [1.0, 0.0, 0.5]   # +inf nc -> coverage 1, -inf nc -> 0
    chk = threshold_check(lk, 2000, pools=6, reps=500, rng=np.random.default_rng(7))
    assert all(v["se"] > 0 for v in chk.values())


def test_admission_follows_the_remedy_order_and_sets_consequences():
    lk = load_locked(); thr = {n: {f"{n}|{lv}": {"threshold": 0.9} for lv in (0.95, 0.9875)} for n in (10, 20, 40)}
    def cellcov(fail: set):
        out = {}
        for n, procs in PROCEDURES_AT_N.items():
            for proc in procs:
                for st, side, lv in ENDPOINTS:
                    out[f"{endpoint_key(st, side, lv, n)}|{proc}"] = 0.5 if (proc, n) in fail else 0.95
        return out
    ok_n = {"10": True, "20": True, "40": True}
    a = admission({"c1": cellcov(set()), "c2": cellcov(set())}, thr, lk, ok_n)
    assert a["method_at_n"] == {"10": "t", "20": "percentile", "40": "studentized"}
    assert a["consequences"] == {"h1": "confirmatory", "parametrized": "percentile_n20", "final_eval_n": 20}
    assert a["admitted_sides"]["gain|upper|0.95|20"] == "percentile" and a["admitted_sides"]["eff|lower|0.95|10"] == "t"
    b = admission({"c1": cellcov({("percentile", 20)}), "c2": cellcov(set())}, thr, lk, ok_n)
    assert b["method_at_n"]["20"] == "studentized" and b["consequences"]["parametrized"] == "studentized_n20"
    c = admission({"c1": cellcov({("percentile", 20), ("studentized", 20)})}, thr, lk, ok_n)
    assert c["method_at_n"]["20"] is None and c["consequences"] == {"h1": "confirmatory", "parametrized": "studentized_n40", "final_eval_n": 40}
    d = admission({"c1": cellcov({("t", 10), ("percentile", 20), ("studentized", 20), ("studentized", 40)})}, thr, lk, ok_n)
    assert d["consequences"] == {"h1": "exploratory", "parametrized": "inconclusive", "final_eval_n": None} and d["admitted_sides"]["gain|upper|0.95|20"] is None
    e = admission({"c1": cellcov(set())}, thr, lk, admissible_n={"10": False, "20": True, "40": True})
    assert e["consequences"]["h1"] == "exploratory" and e["method_at_n"]["20"] == "percentile"           # a failed fixture at n strikes every procedure at n
    base_only = {k: v for k, v in cellcov(set()).items() if "|40|" not in k}
    f = admission({"c1": base_only}, thr, lk, admissible_n={"10": True, "20": True})
    assert f["method_at_n"]["40"] is None and f["consequences"]["parametrized"] == "percentile_n20"       # no n = 40 measurements: not admitted, not needed
    g = admission({"c1": cellcov(set())}, thr, lk, admissible_n={"10": True, "20": True})
    assert g["method_at_n"]["40"] is None                                                                 # measurements without fixture and power evidence are not admitted


def test_report_roundtrip_and_hash(tmp_path):
    rep = {"selection": ["a"], "admitted_sides": {"gain|upper|0.95|20": "percentile"}}
    h = write_report(tmp_path / "r.json", rep)
    assert len(h) == 64 and load_report(tmp_path / "r.json") == rep
