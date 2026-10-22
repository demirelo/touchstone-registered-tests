"""Decision rules of protocol v2 (design 9.3): Q1 categories on the pooled fresh markets, Q2 contrasts, Q4 market tests."""
import numpy as np
import pytest

from sim import decisions_v2 as D

CELLS = [f"F{p}{g}{s}" for p in (0, 1) for g in (0, 1) for s in (0, 1)]


def strata(mean, sd=0.05, n=200, k=6, seed=0):
    rng = np.random.default_rng(seed)
    return [rng.normal(mean, sd, n) for _ in range(k)]


def test_q1_precedence():
    assert D.q1_category(strata(-0.03, 0.02), 1.0, holm_reject=True) == "R lower"
    assert D.q1_category(strata(0.03, 0.02), 1.0, holm_reject=True) == "C lower"
    assert D.q1_category(strata(0.0, 0.05), 1.0, holm_reject=False) == "equivalent"
    assert D.q1_category(strata(0.04, 0.6), 1.0, holm_reject=False) == "inconclusive"


def test_q1_family_holm_and_categories():
    tests = {"a": strata(-0.2, 0.05, seed=1), "b": strata(0.0, 0.05, seed=2), "c": strata(0.3, 0.05, seed=3), "d": strata(0.01, 2.0, seed=4)}
    out = D.q1_family(tests, 1.0)
    assert out["a"]["category"] == "R lower" and out["c"]["category"] == "C lower"
    assert out["b"]["category"] == "equivalent" and out["d"]["category"] == "inconclusive"


def test_q1_suppressed_without_kappa():
    assert D.q1_category(strata(-0.3), None, holm_reject=True) == "no confirmatory decision"
    assert all(v["category"] == "no confirmatory decision" for v in D.q1_family({"a": strata(-0.3)}, None).values())


def test_q2_contrast_coefficients():
    means = {c: float(c[1]) for c in CELLS}                   # the P bit
    out = D.q2_contrasts(means)
    assert out["P"] == 1.0 and out["P|S=0"] == 1.0 and out["P|S=1"] == 1.0
    assert all(out[k] == 0.0 for k in ("G", "S", "PG", "PS", "GS", "PGS", "G|P=0", "G|P=1"))
    parity = {c: float(sum(int(b) for b in c[1:]) % 2) for c in CELLS}
    assert D.q2_contrasts(parity)["PGS"] == 1.0


def test_q4_component_max_then_holm():
    pa = [0.001, 0.001, 0.2, 0.004, 0.001, 0.009]; pb = [0.002, 0.03, 0.001, 0.001, 0.001, 0.001]
    out = D.q4_markets(pa, pb, 1.0)
    assert out["p"] == [0.002, 0.03, 0.2, 0.004, 0.001, 0.009]
    assert out["pass"] == [True, False, False, True, True, True] and out["k"] == 4


def test_q4_suppressed_without_kappa():
    out = D.q4_markets([0.001] * 6, [0.001] * 6, None)
    assert out["decided"] is False and out["k"] is None
