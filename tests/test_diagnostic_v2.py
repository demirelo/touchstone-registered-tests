"""Draft-7 evaluation helpers (design 6.2, 6.6, 6.7, 9.3): false-failure refunds, served share, the fixed-attack
decomposition, training-selected envelopes and welfare winners, the W1 classification, and the honest-replacement
diagnostic."""
from types import SimpleNamespace

import numpy as np
import pytest


def _result(failures, claims, efforts, refunds, sstar=10.0, served=None):
    T, N = np.asarray(failures).shape
    return SimpleNamespace(failures=np.asarray(failures), claims=np.asarray(claims, dtype=float), efforts=np.asarray(efforts, dtype=float),
                           ledger=SimpleNamespace(refunds=np.asarray(refunds, dtype=float)), sstar=sstar,
                           served=np.asarray(served if served is not None else np.ones((T, N), dtype=int)))


def test_false_refund_definition():
    from sim.diagnostic_v2 import false_refunds
    # round 0: entity 0 truthful (claim = effort) and fails by noise: counts; round 1: entity 0 shades and fails: does not
    r = _result([[1, 0], [1, 1]], [[0.5, 0.6], [0.7, 0.4]], [[0.5, 0.6], [0.5, 0.4]], [[0.2, 0.0], [0.3, 0.1]])
    focal, others = false_refunds(r, focal=0, N=2)
    assert focal == pytest.approx(0.2 / 5.0) and others == pytest.approx(0.1 / 5.0)


def test_served_share():
    from sim.diagnostic_v2 import served_share
    cfg = SimpleNamespace(T=2, J=3, providers=[SimpleNamespace(k=1), SimpleNamespace(k=1)])
    r = _result([[0, 0], [0, 0]], [[0, 0], [0, 0]], [[0, 0], [0, 0]], [[0, 0], [0, 0]], served=[[1, 1], [1, 0]])
    assert served_share(r, cfg) == pytest.approx(3 / 4)                     # n_FB = T min(J, sum k) = 2 x 2


def test_cross_decomposition_sums():
    from sim.diagnostic_v2 import decompose
    row = {"F111": {"profit_attack": [1.0, 2.0], "profit_ref": [0.5, 0.5]}, "F000": {"profit_attack": [3.0, 1.0], "profit_ref": [0.2, 0.4]}}
    d = decompose(row, "F111", "F000")
    gR = np.subtract(row["F111"]["profit_attack"], row["F111"]["profit_ref"]); gC = np.subtract(row["F000"]["profit_attack"], row["F000"]["profit_ref"])
    assert np.allclose(gR - gC, np.subtract(d["attack_term"], d["reference_term"]), atol=1e-12)


def test_envelope_uses_training():
    from sim.diagnostic_v2 import envelope_rule
    train = {"attacks": ["F000", "F111", "F010"], "rules": ["F111"], "matrix": [[0.1], [0.3], [0.3]]}
    assert envelope_rule(train, "F111") == "F111"                           # highest training gain, ties by bank order


def test_select_welfare_training():
    from sim.objectives_v2 import select_welfare
    recs = {"D2+H3": {"selected": {"a": 1}, "train_eff": 0.8}, "X7-SC": {"selected": {"b": 1}, "train_eff": 0.7}}
    assert select_welfare(recs) == {"family": "X7-SC", "status": "selected", "train_eff": 0.7}
    recs["X7-SC"]["train_eff"] = 0.8
    assert select_welfare(recs)["family"] == "D2+H3"                       # ties: D2+H3 first


def test_select_welfare_one_family_infeasible():
    from sim.objectives_v2 import select_welfare
    recs = {"D2+H3": {"selected": None, "train_eff": None}, "X7-SC": {"selected": {"b": 1}, "train_eff": 0.9}}
    assert select_welfare(recs)["family"] == "X7-SC"


def test_select_welfare_both_infeasible():
    from sim.objectives_v2 import select_welfare
    recs = {"D2+H3": {"selected": None, "train_eff": None}, "X7-SC": {"selected": None, "train_eff": None}}
    assert select_welfare(recs) == {"family": None, "status": "no feasible candidate found", "train_eff": None}


def test_w1_class():
    from sim.decisions_v2 import w1_class
    assert w1_class(0.0, 0.2) == "supported" and w1_class(-0.3, -0.01) == "contradicted" and w1_class(-0.1, 0.1) == "unresolved"


def test_honest_replacement_bins():
    from sim.cell import SeedCache
    from sim.diagnostic_v2 import honest_replacement
    from sim.positions import positions
    from sim.rules_v2 import make_rule
    from tests._v2_profiles import CFG
    seeds = list(range(2000, 2020)); focal = positions(CFG)["median"]
    a = honest_replacement(CFG, lambda: make_rule("F000"), focal, seeds, SeedCache())
    b = honest_replacement(CFG, lambda: make_rule("F111"), focal, seeds, SeedCache())
    assert a["bins"][0]["age"] == [0, 10] and len(a["bins"]) == len(b["bins"]) and a["replace_at"] == 50
    assert b["bins"][0]["audited_share"] > a["bins"][0]["audited_share"]   # newest-first targeting audits the replacement more (direction)
    assert all(np.isfinite(x["profit_per_round"]) and x["false_refund"] >= 0 for x in a["bins"])
