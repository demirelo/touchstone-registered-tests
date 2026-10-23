"""Coverage and calibration v2 (design 9.5): aligned 14-profile pools, fixture branches, endpoints, kappa selection on
selection replications, validation on independent replications with Bonferroni Clopper-Pearson bounds."""
import numpy as np
import pytest


def test_profiles():
    from sim.calibration_v2 import PROFILES
    assert len(PROFILES) == 14 and ("attack", "F000", "D2+H3") in PROFILES and ("attack", "F000", "X7-SC") not in PROFILES
    assert sum(p[0] == "ref" for p in PROFILES) == 5


def test_pool_rows_align_by_seed():
    from sim.calibration_v2 import PROFILES, build_pool
    from sim.cell import Cell, SeedCache, run_focal
    from sim.policies.families import D2
    from sim.policies.identity import h3_family
    from sim.policies.x7 import x7_family
    from sim.rules_v2 import make_rule
    from tests._v2_profiles import CFG
    from sim.positions import positions
    honest_h3 = {"u0": 0.0, "m0": 0.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "x": 0, "clip": 1}
    honest_x7 = {"u0": 0.0, "m0": 0.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "k_F": 1.0, "k_T": 1.0, "a_F": 0.0, "n_P": 0.0, "h_R": 200.0, "lambda": 1.0, "clip": 1}
    attacks = {(r, f): (honest_h3 if f == "D2+H3" else honest_x7) for k, r, *f in PROFILES if k == "attack" for f in f}
    refs = {r: {"name": "honest_max", "family": None, "T": 200, "L": 10, "knobs": None} for k, r, *_ in PROFILES if k == "ref"}
    mkt = {"cfg": CFG, "focal": positions(CFG)["median"]}
    seeds = [2000, 2001, 2002]
    pool = build_pool(mkt, attacks, refs, seeds, cred={"variant": "thr", "K": 6, "M": None})
    assert pool["seeds"] == seeds and len(pool["normalized"]) == 14
    one = run_focal(Cell(cfg=CFG, rule_factory=lambda: make_rule("F111"), focal=mkt["focal"], seeds=(2001,), name="x"),
                    lambda: h3_family(D2).make(honest_h3), SeedCache())
    assert pool["normalized"]["attack|F111|D2+H3"][1] == pytest.approx(float(one.normalized[0]))


def test_strata_branches_sizes_and_remainders():
    from sim.calibration_v2 import strata
    pools = {m: list(range(20000)) for m in ("headline", "dev0", "dev1")}
    a = strata(pools, "three20k"); assert len(a) == 6 and all(len(s) == 10000 for s in a)
    b = strata(pools, "two20k"); assert len(b) == 6 and all(len(s) == 6666 for s in b) and b[0][0] == 0 and b[1][0] == 6666
    c = strata(pools, "two10k"); assert len(c) == 6 and all(len(s) == 3333 for s in c) and c[2][-1] == 9998


def test_endpoint_counts_by_branch():
    from sim.calibration_v2 import denominator, endpoints
    assert len(endpoints("Q1", "three20k")) == 32 and len(endpoints("Q1", "two10k")) == 32
    assert len(endpoints("Q4", "three20k")) == 36 and len(endpoints("Q4", "two20k")) == 24
    assert denominator("Q1") == 32 and denominator("Q4") == 36
    tails = sorted({e["alpha_e"] for e in endpoints("Q1", "three20k")})
    assert tails == pytest.approx(sorted([0.05 / 8, 0.05 / 6, 0.05 / 4, 0.05 / 2]))


def test_miss_rate_near_nominal_on_normal_data():
    from sim.calibration_v2 import miss_counts
    rng = np.random.default_rng(0); pool = rng.normal(0.3, 1.0, 20000)
    c = miss_counts({"x": pool}, "single", [0.05], [1.0], replications=400, resamples=199, seed=1, n=200)
    rate = c[("x", "lower", 0.05, 1.0)] / 400
    assert 0.01 <= rate <= 0.11


def _fake_misses(table):
    def f(family, fixtures, branch, kappa, replications, seed, resamples):
        return {i: int(table(kappa, e) * replications) for i, e in enumerate(__import__("sim.calibration_v2", fromlist=["x"]).endpoints(family, branch))}
    return f


def test_select_largest_passing_kappa(monkeypatch):
    import sim.calibration_v2 as C
    monkeypatch.setattr(C, "endpoint_misses", _fake_misses(lambda k, e: e["alpha_e"] * (1.5 if k == 1.0 else 0.5)))
    assert C.select_kappa("Q1", None, "three20k", seed=1, replications=1000) == 0.5


def test_select_none_when_all_fail(monkeypatch):
    import sim.calibration_v2 as C
    monkeypatch.setattr(C, "endpoint_misses", _fake_misses(lambda k, e: e["alpha_e"] * 3))
    assert C.select_kappa("Q4", None, "three20k", seed=1, replications=1000) is None


def test_validation_rejects_if_any_endpoint_fails(monkeypatch):
    import sim.calibration_v2 as C
    monkeypatch.setattr(C, "endpoint_misses", _fake_misses(lambda k, e: 0.0 if e["alpha_e"] > 0.01 else e["alpha_e"] * 2))
    v = C.validate("Q1", 1.0, None, "three20k", seed=1, replications=20000)
    assert v["admitted"] is False and any(not r["pass"] for r in v["endpoints"])
    monkeypatch.setattr(C, "endpoint_misses", _fake_misses(lambda k, e: 0.0))
    assert C.validate("Q1", 1.0, None, "three20k", seed=1, replications=20000)["admitted"] is True


def test_validation_uses_independent_seeds(monkeypatch):
    import sim.calibration_v2 as C
    seen = []
    def f(family, fixtures, branch, kappa, replications, seed, resamples):
        seen.append(seed); return {i: 0 for i, _ in enumerate(C.endpoints(family, branch))}
    monkeypatch.setattr(C, "endpoint_misses", f)
    C.select_kappa("Q1", None, "three20k", seed=7, replications=10); C.validate("Q1", 1.0, None, "three20k", seed=7, replications=10)
    assert seen[0] == 7 and seen[-1] != 7 and seen[-1] not in seen[:-1]


def test_fixture_inputs_from_tuning_outputs(tmp_path):
    import json
    from scripts.coverage_v2 import fixture_inputs
    cred = {"variant": "thr", "K": 6, "M": None}; log = tmp_path / "log"; log.mkdir()
    att = {"D2+H3": {"attack": {"a": 1}}, "X7-SC": {"attack": {"b": 2}}, "D2": {"attack": {"c": 3}}}
    for n, (rule, spec) in enumerate([("B3-t", {"tol": 0.16, "L": 10}), ("R3-t", {"tol": 0.16, "L": 10}), ("R4-t", {"tol": 0.16, "L": 10}),
                                      ("C*", {"tol": 0.16, "L": 10, "cred": cred}), ("B3-t", {"tol": 0.12, "L": 10})]):
        (log / f"{n}.json").write_text(json.dumps({"rule": rule, "spec": spec, "recheck": False,
                                                    "detail": {"dev0": {**att, "reference": {"name": rule, "family": None, "T": 200, "L": 10, "knobs": None}}}}))
    (tmp_path / "comparator.json").write_text(json.dumps({"cred": cred}))
    (tmp_path / "fixture_cstar_s2.json").write_text(json.dumps({"markets": {"dev0": {"attacks": {"D2+H3": {"d": 4}, "X7-SC": {"e": 5}, "D2": {}},
                                                                                   "reference": {"name": "S2", "family": None, "T": 200, "L": 10, "knobs": None}}}}))
    attacks, refs = fixture_inputs(tmp_path, "dev0")
    assert attacks[("F000", "D2+H3")] == {"a": 1} and attacks[("C*/S2", "X7-SC")] == {"e": 5} and ("F000", "X7-SC") not in attacks
    assert refs["F111"]["name"] == "R3-t" and refs["C*"]["name"] == "C*" and refs["C*/S2"]["name"] == "S2" and len(attacks) == 9 and len(refs) == 5


def test_cli_select_and_validate_on_synthetic_pools(tmp_path):
    import json
    from scripts.coverage_v2 import main
    rng = np.random.default_rng(3); pools = tmp_path / "pools"; pools.mkdir()
    for m in ("headline", "dev0", "dev1"):
        norm = {key(p): rng.normal(0.1, 0.2, 400).tolist() for p in __import__("sim.calibration_v2", fromlist=["x"]).PROFILES}
        eff = {k: rng.normal(0.98, 0.01, 400).tolist() for k in norm}
        (pools / f"{m}.json").write_text(json.dumps({"seeds": list(range(400)), "normalized": norm, "eff": eff}))
    assert main(["--select", "--branch", "three20k", "--out", str(tmp_path), "--replications", "40", "--resamples", "99", "--pool-size", "400"]) == 0
    cov = json.loads((tmp_path / "coverage.json").read_text())
    assert set(cov) >= {"Q1", "Q4"} and "kappa" in cov["Q1"]
    assert main(["--validate", "--branch", "three20k", "--out", str(tmp_path), "--replications", "40", "--resamples", "99", "--pool-size", "400"]) == 0
    assert "validation" in json.loads((tmp_path / "coverage.json").read_text())["Q4"]


def key(p):
    return "|".join(p)


def test_calibration_counts_misses_on_near_constant_pool():
    from sim.calibration_v2 import miss_counts
    pool = np.zeros(20000); pool[0] = -1.0
    c = miss_counts({"x": pool}, "single", [0.05], [1.0], replications=100, resamples=99, seed=2)
    assert c[("x", "lower", 0.05, 1.0)] >= 90


def test_calibration_uses_production_bounds():
    from sim import intervals as I
    from sim.calibration_v2 import bound_single, bound_pooled
    rng = np.random.default_rng(9); x = rng.normal(0, 1, 200); st = [rng.normal(0, 1, 200) for _ in range(6)]
    for side in ("lower", "upper"):
        assert bound_single(x, side, 0.0125, 999) == pytest.approx(I.studentized_at(x, side, 0.0125, 999))
        assert bound_pooled(st, side, 0.0125, 999) == pytest.approx(I.stratified_at(st, side, 0.0125, 999))


def _reference_misses(pool, tails, kappas, R, resamples, seed, n):
    """The definition, through the production bound functions: replication r draws n rows from SeedSequence([seed, r])."""
    from sim import intervals as I
    truth = float(pool[0]) if np.all(pool == pool[0]) else float(np.mean(pool)); out = {}
    for r in range(R):
        idx = np.random.default_rng(np.random.SeedSequence([seed, r])).integers(0, pool.size, n); x = pool[idx]
        for t in tails:
            for kp in kappas:
                out[("lower", t, kp)] = out.get(("lower", t, kp), 0) + int(I.studentized_at(x, "lower", t * kp, resamples) > truth)
                out[("upper", t, kp)] = out.get(("upper", t, kp), 0) + int(I.studentized_at(x, "upper", t * kp, resamples) < truth)
    return out


def test_g5_miss_counts_equal_production_replications():
    from sim import intervals as I
    from sim.calibration_v2 import miss_counts
    rng = np.random.default_rng(4)
    pools = {"normal": rng.normal(0.01, 1.0, 2000), "skew": rng.exponential(1.0, 2000) - 1.0, "const": np.full(20000, 1.1)}
    c = miss_counts(pools, "single", [0.05, 0.2], [1.0, 0.5], replications=30, resamples=99, seed=5, n=50)
    for s, pool in pools.items():
        ref = _reference_misses(pool, [0.05, 0.2], [1.0, 0.5], 30, 99, 5, 50)
        assert {k: c[(s, *k)] for k in ref} == ref
    assert all(c[("const", side, t, kp)] == 0 for side in ("lower", "upper") for t in (0.05, 0.2) for kp in (1.0, 0.5))
    strata = [{"d": rng.normal(0.0, 1.0, 300)} for _ in range(6)]
    cp = miss_counts(strata, "pooled", [0.1], [1.0], replications=20, resamples=99, seed=6, n=40)
    truth = I.stratified_mean([st["d"] for st in strata]); want = {"lower": 0, "upper": 0}
    for r in range(20):
        g = np.random.default_rng(np.random.SeedSequence([6, r])); draws = [g.integers(0, 300, 40) for _ in strata]
        x = [st["d"][i] for st, i in zip(strata, draws)]
        want["lower"] += int(I.stratified_at(x, "lower", 0.1, 99) > truth); want["upper"] += int(I.stratified_at(x, "upper", 0.1, 99) < truth)
    assert {side: cp[("d", side, 0.1, 1.0)] for side in want} == want


def test_g4_nonfinite_pools_are_refused():
    from sim.calibration_v2 import miss_counts
    pool = np.zeros(20000); pool[7] = np.nan
    with pytest.raises(ValueError):
        miss_counts({"x": pool}, "single", [0.05], [1.0], replications=2, resamples=99, seed=1)
    with pytest.raises(ValueError):
        miss_counts([{"x": pool[:300]}, {"x": np.zeros(300)}], "pooled", [0.05], [1.0], replications=2, resamples=99, seed=1)


def test_h5_every_replication_bound_equals_production():
    from sim import intervals as I
    from sim.calibration_v2 import miss_counts
    rng = np.random.default_rng(8); pool = rng.normal(0, 1, 1000); strata = [{"d": rng.normal(0, 1, 200)} for _ in range(3)]
    tr = []
    miss_counts({"x": pool}, "single", [0.1], [0.5], replications=5, resamples=99, seed=3, n=30, trace=tr)
    assert sorted((r, side) for r, _, side, *_ in tr) == sorted((r, side) for r in range(5) for side in ("lower", "upper"))
    for r, s, side, tail, kp, b in tr:
        idx = np.random.default_rng(np.random.SeedSequence([3, r])).integers(0, pool.size, 30)
        assert b == I.studentized_at(pool[idx], side, tail * kp, 99)
    tr = []
    miss_counts(strata, "pooled", [0.1], [1.0], replications=4, resamples=99, seed=4, n=20, trace=tr)
    assert sorted((r, s, side) for r, s, side, *_ in tr) == sorted((r, "d", side) for r in range(4) for side in ("lower", "upper"))
    for r, s, side, tail, kp, b in tr:
        g = np.random.default_rng(np.random.SeedSequence([4, r])); draws = [g.integers(0, 200, 20) for _ in strata]
        assert b == I.stratified_at([st["d"][i] for st, i in zip(strata, draws)], side, tail * kp, 99)
