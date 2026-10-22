"""Interval and test primitives of protocol v2 (design 9.2): arbitrary tails, bootstrap p-values, Holm, calibration,
stratified pooled bounds, simultaneous member bounds, Clopper-Pearson."""
import numpy as np
import pytest

from sim import intervals as I

X = np.random.default_rng(0).normal(0.1, 1.0, 60)


def test_studentized_at_matches_existing_at_registered_level():
    for side in ("lower", "upper"):
        assert I.studentized_at(X, side, 0.0125, 999, 5) == pytest.approx(I.studentized_bootstrap(X, side, 0.9875, 999, 5).value)


def test_pvalue_inverts_bound():
    B = 1999
    for side, null in (("lower", -0.15), ("upper", 0.4)):
        p = I.bootstrap_pvalue(X, null, side, B, 3)
        for a in np.linspace(0.002, 0.5, 60):
            if abs(a - p) <= 3.0 / (B + 1):
                continue
            b = I.studentized_at(X, side, a, B, 3)
            assert (b > null if side == "lower" else b < null) == (p <= a)


def test_pvalue_constant_and_unattainable():
    c = np.full(10, 0.3)
    assert I.bootstrap_pvalue(c, 0.0, "lower") == 0.0 and I.bootstrap_pvalue(c, 1.0, "lower") == 1.0
    assert I.bootstrap_pvalue(c, 1.0, "upper") == 0.0 and I.bootstrap_pvalue(c, 0.0, "upper") == 1.0
    assert I.bootstrap_pvalue(X, 100.0, "lower", 999, 1) == 1.0


def test_two_sided_pvalue():
    pl = I.bootstrap_pvalue(X, 0.0, "lower", 999, 2); pu = I.bootstrap_pvalue(X, 0.0, "upper", 999, 2)
    assert I.two_sided_pvalue(X, 0.0, 999, 2) == pytest.approx(min(1.0, 2 * min(pl, pu)))


def test_holm_known_example():
    assert I.holm([0.001, 0.04]) == [True, True]
    assert [p <= 0.025 for p in (0.001, 0.04)] == [True, False]
    assert I.holm([0.04, 0.001, 0.03]) == [False, True, False]      # 0.001 <= 0.05/3; then 0.03 > 0.05/2 stops


def test_calibrated_monotone():
    assert I.calibrated(0.01, 0.5) == 0.02 and I.calibrated(0.8, 0.25) == 1.0 and I.calibrated(0.01, 1.0) == 0.01


def test_stratified_se_formula_and_independent_streams():
    rng = np.random.default_rng(4); st = [rng.normal(k, 1 + k, 30 + 5 * k) for k in range(3)]
    m, se, t = I.stratified_tstats(st, 499, 11)
    assert m == pytest.approx(np.mean([s.mean() for s in st]))
    assert se == pytest.approx(np.sqrt(sum(s.var(ddof=1) / s.size for s in st)) / 3)
    kids = np.random.SeedSequence(11).spawn(3)
    ms = []; ses = []
    for s, kid in zip(st, kids):
        idx = np.random.default_rng(kid).integers(0, s.size, size=(499, s.size)); r = s[idx]
        ms.append(r.mean(axis=1)); ses.append(r.var(axis=1, ddof=1) / s.size)
    ref = (np.mean(ms, axis=0) - m) / (np.sqrt(np.sum(ses, axis=0)) / 3)
    assert np.allclose(t, ref)
    shared = np.random.default_rng(11).integers(0, 30, size=(499, 30))
    assert not np.allclose(t[:5], ((st[0][shared].mean(axis=1) - st[0].mean()))[:5])


def test_stratified_bounds_and_pvalue():
    rng = np.random.default_rng(5); st = [rng.normal(0.2, 1, 200) for _ in range(6)]
    lo = I.stratified_at(st, "lower", 0.025, 999, 1); hi = I.stratified_at(st, "upper", 0.025, 999, 1)
    assert lo < np.mean([s.mean() for s in st]) < hi
    assert I.stratified_pvalue(st, 0.0, "lower", 999, 1) < 0.05


def test_gmin_bounds_are_member_minima():
    rng = np.random.default_rng(6); rows = [rng.normal(m, 1, 100) for m in (0.5, 0.1, 0.3)]
    lo, hi = I.gmin_bounds(rows, 0.05, 999, 2)
    assert lo == pytest.approx(min(I.studentized_at(r, "lower", 0.05 / 3, 999, 2) for r in rows))
    assert hi == pytest.approx(min(I.studentized_at(r, "upper", 0.05 / 3, 999, 2) for r in rows))


def test_clopper_pearson_known_values():
    conf = 1 - 0.01 / 32
    assert I.clopper_pearson_upper(88, 20000, conf) == pytest.approx(0.006238, abs=2e-6)
    assert I.clopper_pearson_upper(89, 20000, conf) > 0.00625
    assert I.clopper_pearson_upper(5, 5, 0.99) == 1.0
