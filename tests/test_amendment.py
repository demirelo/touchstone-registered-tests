import numpy as np
import pytest
import yaml

from sim.amendment import (AMEND_ENDPOINTS, AMEND_STATISTICS, LIMITATION, REGISTRATION_FIELDS, CoverageExtSpec, admission_ext, amendment_hash,
                           fixture_and_power_ext, load_amendment, measure_ext, observe_ext, seed_blocks_ext, trajectory_keys_ext)
from sim.config import MarketConfig
from sim.coverage import joint_fixture, thresholds
from sim.locked import load_locked
from sim.records import cfg_to_dict

SEEDS_EXT = {"start": 6_600_000, "block": 400_000, "pool": 35_000, "replications": {"40": 4000}}
SMOKE_AMEND = {"seeds_ext": dict(SEEDS_EXT)}


def small_ext_spec(ref_b2=True, ref_b3=True):
    c = MarketConfig.default()
    cfg = MarketConfig(N=4, J=30, T=6, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4, providers=c.providers[6:10], alpha=c.alpha, budget=0.3)
    params = {"B1": {"P1": 0.2, "P2": 0.35, "P3": 0.5}, "B2": {"P1": 0.2, "P2": 0.35, "P3": 0.5, "tol": 0.12, "L": 3}, "B3": {"tol": 0.12, "L": 3}}
    cheat = {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0.0}
    hon = {"name": "honest_max", "knobs": None}
    return CoverageExtSpec(name="x_B1", cfg=cfg_to_dict(cfg), focal=3, family="D1", params_by_rule=params,
                           attack_knobs_by_rule={r: dict(cheat) for r in params},
                           ref_candidate_by_rule={"B2": dict(hon) if ref_b2 else None, "B3": dict(hon) if ref_b3 else None})


def test_seed_layout_keeps_prefixes_under_both_remedies_and_refuses_overlap(tmp_path):
    am = {"seeds_ext": dict(SEEDS_EXT)}
    p1, r1 = seed_blocks_ext(am, 2); p2, r2 = seed_blocks_ext(am, 2, pool_factor=2); p3, r3 = seed_blocks_ext(am, 2, rep_factor=2)
    assert p1[0] == 6_600_000 + 800_000 and p1.size == 35_000 and np.array_equal(p2[:35_000], p1) and p2.size == 70_000
    assert r1.shape == (4000, 40) and r1[0, 0] == p1[0] + 70_000 and np.array_equal(r3[:4000], r1) and r3.shape == (8000, 40)
    assert r3.max() < 6_600_000 + 3 * 400_000 and not (set(p2.tolist()) & set(r3.ravel().tolist()))
    f = tmp_path / "a.yaml"
    for start in (3_000_000, 5_000_000, 9_900_000, 2_000):
        f.write_text(yaml.safe_dump({"seeds_ext": {"start": start, "block": 400_000, "pool": 35_000, "replications": {"40": 4000}}}))
        with pytest.raises(ValueError, match="overlap"):
            load_amendment(f, load_locked())
    f.write_text(yaml.safe_dump({"seeds_ext": {"start": 6_600_000, "block": 200_000, "pool": 35_000, "replications": {"40": 4000}}}))
    with pytest.raises(ValueError, match="block"):
        load_amendment(f, load_locked())
    f.write_text(yaml.safe_dump({"seeds_ext": dict(SEEDS_EXT)}))
    assert load_amendment(f, load_locked())["seeds_ext"]["block"] == 400_000


def test_amendment_hash_ignores_registration_fields_only():
    doc = {"clause": {"n": 40}, "coverage_report_amendment_sha256": None, "coverage_consequences": None}
    h = amendment_hash(doc)
    assert REGISTRATION_FIELDS == ("coverage_report_amendment_sha256", "coverage_consequences")
    assert amendment_hash({**doc, "coverage_report_amendment_sha256": "ab" * 32, "coverage_consequences": {"h3_comparative": "confirmatory"}}) == h
    assert amendment_hash({**doc, "clause": {"n": 20}}) != h and len(h) == 64


def test_gain_diff_uses_each_rules_reference_and_abstain_is_zero_profit():
    both = small_ext_spec(ref_b2=True, ref_b3=True); one = small_ext_spec(ref_b2=True, ref_b3=False)
    assert trajectory_keys_ext(both) == [("B2", "attack"), ("B2", "ref"), ("B3", "attack"), ("B3", "ref")]
    assert trajectory_keys_ext(one) == [("B2", "attack"), ("B2", "ref"), ("B3", "attack")]
    o1 = observe_ext(both, np.arange(4), chunk=2); o2 = observe_ext(one, np.arange(4), chunk=2); par = observe_ext(both, np.arange(4), chunk=2, workers=2)
    assert set(o1) == set(AMEND_STATISTICS) == {"gain_diff"} and o1["gain_diff"].shape == (4,) and np.all(np.isfinite(o1["gain_diff"]))
    assert np.array_equal(par["gain_diff"], o1["gain_diff"])
    assert not np.array_equal(o1["gain_diff"], o2["gain_diff"])                      # B3's reference changes the statistic


def test_measure_ext_has_two_sides_and_admission_is_strict():
    rng = np.random.default_rng(0)
    m = measure_ext({"gain_diff": rng.normal(size=(50, 40))}, {"gain_diff": (-0.05, 0.05)}, 40, {"bootstrap_resamples": 200, "bootstrap_seed": 1})
    assert set(m) == {"gain_diff|lower|0.9875|40|studentized", "gain_diff|upper|0.9875|40|studentized"} and all(0.0 <= v <= 1.0 for v in m.values())
    thr = {40: {"40|0.9875": {"threshold": 0.9}}}; names = [f"c{i}" for i in range(6)]; lk = load_locked()
    good = {c: {k: 0.99 for k in m} for c in names}
    adm = admission_ext(good, thr, lk, {"40": True}, names)
    assert adm["consequences"] == {"h3_comparative": "confirmatory"} and adm["procedure_admitted"] == {"studentized|40": True}
    assert adm["admitted_sides"] == {"gain_diff|lower|0.9875|40": "studentized", "gain_diff|upper|0.9875|40": "studentized"}
    assert admission_ext(good, thr, lk, {"40": False}, names)["admitted_sides"]["gain_diff|lower|0.9875|40"] is None
    assert admission_ext({k: v for k, v in good.items() if k != "c5"}, thr, lk, {"40": True}, names)["consequences"]["h3_comparative"] == "exploratory"
    assert admission_ext({**good, "c6": good["c0"]}, thr, lk, {"40": True}, names)["consequences"]["h3_comparative"] == "exploratory"
    half = dict(good); half["c0"] = {"gain_diff|lower|0.9875|40|studentized": 0.99}
    assert admission_ext(half, thr, lk, {"40": True}, names)["consequences"]["h3_comparative"] == "exploratory"
    nan = dict(good); nan["c1"] = {**good["c1"], "gain_diff|upper|0.9875|40|studentized": float("nan")}
    assert admission_ext(nan, thr, lk, {"40": True}, names)["consequences"]["h3_comparative"] == "exploratory"
    low = dict(good); low["c2"] = {**good["c2"], "gain_diff|upper|0.9875|40|studentized": 0.85}
    assert admission_ext(low, thr, lk, {"40": True}, names)["consequences"]["h3_comparative"] == "exploratory"


def test_joint_fixture_accepts_a_custom_endpoint_set_and_defaults_are_unchanged():
    lk = load_locked(); thr = thresholds(lk, 200)
    base = joint_fixture(lk, 10, 200, 20, thr, 3, np.random.default_rng(1))
    ext = joint_fixture(lk, 40, 200, 20, thr, 3, np.random.default_rng(1), statistics=AMEND_STATISTICS, endpoints=AMEND_ENDPOINTS)
    assert base["endpoints_per_cell"] == 8 and ext["endpoints_per_cell"] == 2 and ext["n"] == 40 and ext["cells"] == 6


def test_fixture_and_power_ext_smoke_shape():
    fp = fixture_and_power_ext(load_locked(), SMOKE_AMEND, True, np.random.default_rng(0))
    assert set(fp["per_n"]) == {"40"} and fp["per_n"]["40"][0]["fixture"]["endpoints_per_cell"] == 2 and set(fp["admissible_n"]) == {"40"}
    assert set(fp["per_n"]["40"][0]["power"]) == {"40|0.9875"} and fp["base_M"] == 200 and fp["base_R"] == {"40": 20}
    assert "proxy" in LIMITATION.lower()
