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
