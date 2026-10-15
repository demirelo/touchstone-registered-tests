import pytest
from sim.locked import load_locked, seeds, sha256_file, settings_hash, market_config_from_locked
from sim.mechanisms.base import L_MAX, H_MAX


def test_locked_loads_and_namespaces_are_disjoint():
    lk = load_locked()
    tr, va, ca = seeds(lk, "dev_train"), seeds(lk, "dev_val"), seeds(lk, "calibration")
    assert len(tr) == 5 and len(va) == 20 and len(ca) == 20
    assert not (set(tr) & set(va)) and not (set(tr) & set(ca)) and not (set(va) & set(ca))
    assert lk["seeds"]["final_eval"] is None     # custodian-held until the unseal
    with pytest.raises(ValueError):
        seeds(lk, "final_eval")
    assert lk["beta_grid"] == [0.0, 0.01, 0.02, 0.05, 0.10, 0.20]
    assert lk["rho"]["default"] == 0.2 and lk["rho"]["sweep"] == [0.05, 0.2, 1.0]
    assert lk["search"]["popsize"] == 8 and lk["search"]["restarts"] == 5 and lk["search"]["evals_per_restart"] == 300
    assert lk["admissible"]["L_max"] == L_MAX and lk["admissible"]["H_max"] == H_MAX
    assert lk["reference_order"][0] == "abstain"
    assert lk["tuning"]["recheck_namespace"] == "dev_val"


def test_market_config_comes_from_the_yaml_alone():
    lk = load_locked()
    cfg = market_config_from_locked(lk)
    cfg.validate()
    assert cfg.N == 10 and cfg.J == 50 and cfg.T == 200 and cfg.alpha == 0.0 and cfg.budget == 0.0
    assert [p.q_max for p in cfg.providers] == lk["market"]["providers"]["q_max"]
    assert cfg.v_min == lk["market"]["v_min"]


def test_sha256_is_stable(tmp_path):
    p = tmp_path / "x.txt"; p.write_text("abc")
    assert sha256_file(p) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_settings_hash_covers_every_experimental_setting():
    lk = load_locked()
    h = settings_hash(lk)
    assert len(h) == 64
    for key, value in (("tuning", dict(lk["tuning"], inner_evals=101)), ("beta_headline", 0.1), ("rho", dict(lk["rho"], default=0.5)),
                       ("seeds", dict(lk["seeds"], calibration=[4000]))):
        other = dict(lk); other[key] = value
        assert settings_hash(other) != h
    same = dict(lk); same["version"] = "something-else"; same["tuned"] = {"B1": "x"}; same["identity_salt_sha256"] = "ab" * 32
    assert settings_hash(same) == h          # the blocks written at the lock do not invalidate the artifacts the lock lists


def test_locked_has_plan_2b_blocks_and_coverage_range_is_disjoint():
    lk = load_locked()
    cov = lk["seeds"]["coverage"]
    assert cov["start"] == 3_000_000 and cov["pool"] == 35_000 and cov["replications"] == {"10": 2000, "20": 2000, "40": 4000} and cov["n_grid"] == [10, 20, 40]
    assert cov["block"] >= 2 * cov["pool"] + 2 * sum(int(r) * int(n) for n, r in cov["replications"].items())   # room for both doublings
    lo, hi = cov["start"], cov["start"] + 6 * cov["block"]
    for ns in ("dev_train", "dev_val", "calibration"):
        assert all(not (lo <= s < hi) for s in seeds(lk, ns))
    assert lk["intervals"]["bootstrap_resamples"] == 10_000 and lk["intervals"]["margins"] == {"0.95": 2.0, "0.9875": 1.0}
    assert lk["h1"]["model"] == "claude-opus-5-5" and lk["h1"]["jev_model"] == "jev-1.14.0" and lk["h1"]["T"] == 100
    assert lk["claim"]["eff_min"] == 0.90 and lk["claim"]["gain_max"] == 0.30 and lk["claim"]["baseline_level"] == 0.9875
    assert "sim/mechanisms/proposed.py" in lk["allow_list"] and "sealed/" in lk["allow_list"]
    assert lk["calibration"] is None and lk["sealed_bundle_sha256"] is None
    h = settings_hash(lk)
    filled = dict(lk); filled["calibration"] = {"S_hat": 1.0}; filled["sealed_bundle_sha256"] = "ab" * 32
    filled["coverage_report_sha256"] = "cd" * 32; filled["comprehension_fixture_sha256"] = "ef" * 32; filled["coverage_consequences"] = {"final_eval_n": 20}
    filled["h1"] = dict(lk["h1"], cost_cap_usd=120.0)
    assert settings_hash(filled) == h          # lock-time blocks never invalidate pre-lock artifacts
