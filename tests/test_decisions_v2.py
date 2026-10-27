"""Decision rules of protocol v2 (design 9.3): Q1 categories on the pooled fresh markets, Q2 contrasts, Q4 market tests."""
import numpy as np
import pytest

from sim import decisions_v2 as D

CELLS = [f"F{p}{g}{s}" for p in (0, 1) for g in (0, 1) for s in (0, 1)]


def strata(mean, sd=0.05, n=200, k=6, seed=0):
    rng = np.random.default_rng(seed)
    return [rng.normal(mean, sd, n) for _ in range(k)]


def test_q1_categories():
    # d = g_C* - g_F111 per seed; I = the calibrated Bonferroni interval at one-sided tail 0.05 / (2 m) x kappa, m = 2
    assert D.q1_category(strata(0.15, 0.02), 1.0, holm_reject=True) == "R3 materially lower"
    assert D.q1_category(strata(-0.15, 0.02), 1.0, holm_reject=True) == "C* materially lower"
    assert D.q1_category(strata(0.0, 0.05), 1.0, holm_reject=False) == "equivalent"
    assert D.q1_category(strata(0.02, 0.01), 1.0, holm_reject=True) == "equivalent, direction R3 lower"
    assert D.q1_category(strata(-0.02, 0.01), 1.0, holm_reject=True) == "equivalent, direction C* lower"
    assert D.q1_category(strata(0.05, 0.05), 1.0, holm_reject=True) == "ordered, size not established"
    assert D.q1_category(strata(0.04, 0.6), 1.0, holm_reject=False) == "inconclusive"


def test_q1_family_fixed_slots_and_withholding():
    tests = {"a": strata(0.2, 0.05, seed=1), "b": strata(0.0, 0.05, seed=2)}
    out = D.q1_family(tests, 1.0)
    assert out["a"]["category"] == "R3 materially lower" and out["b"]["category"] == "equivalent"
    gone = D.q1_family({"a": None, "b": strata(0.2, 0.05, seed=1)}, 1.0)
    assert gone["a"]["category"] == "not decided: missing cell" and gone["a"]["p"] is None and gone["b"]["category"] == "R3 materially lower"


def test_fixed_slots_boundary(monkeypatch):
    # one test withheld: the other's calibrated p-value 0.03 is not rejected (Holm keeps two slots, first step 0.025)
    monkeypatch.setattr(D, "stratified_two_sided", lambda st, null: 0.03)
    out = D.q1_family({"a": None, "b": strata(0.0, 0.05)}, 1.0)
    assert out["b"]["reject"] is False
    assert D.holm([0.03], 0.05) == [True]                                       # one slot would reject


def test_q1_suppressed_without_kappa():
    assert D.q1_category(strata(-0.3), None, holm_reject=True) == "no confirmatory decision"
    assert all(v["category"] == "no confirmatory decision" for v in D.q1_family({"a": strata(-0.3)}, None).values())


def test_q1_efficiency():
    # eff strata: (the favoured rule minus the other) per seed; condition: nominal one-sided 97.5 percent lower bound >= -0.01
    assert D.q1_efficiency(strata(0.0, 0.001)) == "efficiency condition met"
    assert D.q1_efficiency(strata(-0.05, 0.001)) == "efficiency loss"
    assert D.q1_efficiency(strata(-0.01, 0.05)) == "efficiency non-inferiority unresolved"


def test_q1_better_needs_category1_and_condition():
    assert D.q1_better("R3 materially lower", "efficiency condition met") == "R3 better (efficiency evidence descriptive)"
    assert D.q1_better("C* materially lower", "efficiency condition met") == "C* better (efficiency evidence descriptive)"
    assert D.q1_better("R3 materially lower", "efficiency non-inferiority unresolved") is None
    assert D.q1_better("equivalent, direction R3 lower", "efficiency condition met") is None


def test_q2_conditional_contrasts():
    v = {c: float(int(c[1]) * 1.0 + int(c[2]) * 2.0 + int(c[3]) * 4.0 + int(c[1]) * int(c[2]) * 8.0) for c in CELLS}
    q = D.q2_contrasts(v)
    assert q["P|G=0"] == pytest.approx(1.0) and q["P|G=1"] == pytest.approx(9.0)
    assert q["G|S=0"] == pytest.approx(6.0) and q["G|S=1"] == pytest.approx(6.0)


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
