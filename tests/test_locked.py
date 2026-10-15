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
