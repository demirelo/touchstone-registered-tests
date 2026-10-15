import numpy as np
import pytest
from scipy import stats
from sim.intervals import percentile_bootstrap, studentized_bootstrap, t_bound, t_interval, bound, exact_t_bound_with_critical


def test_percentile_bootstrap_degenerate_when_all_values_equal():
    b = percentile_bootstrap(np.full(20, 0.37), "upper", 0.95, resamples=1000, seed=1)
    assert b.value == 0.37 and b.degenerate is True and np.isfinite(b.value)
    b2 = percentile_bootstrap(np.full(20, 0.37), "lower", 0.9875, resamples=1000, seed=1)
    assert b2.value == 0.37 and b2.degenerate is True


def test_percentile_bootstrap_is_one_sided_seeded_and_brackets_the_mean():
    rng = np.random.default_rng(0); x = rng.normal(1.0, 0.5, size=20)
    up = percentile_bootstrap(x, "upper", 0.95, resamples=2000, seed=7)
    lo = percentile_bootstrap(x, "lower", 0.95, resamples=2000, seed=7)
    assert lo.value < x.mean() < up.value and up.side == "upper" and up.level == 0.95 and up.n == 20 and up.degenerate is False
    assert percentile_bootstrap(x, "upper", 0.95, resamples=2000, seed=7).value == up.value       # seeded: byte-identical
    assert percentile_bootstrap(x, "upper", 0.95, resamples=2000, seed=8).value != up.value
    tighter = percentile_bootstrap(x, "upper", 0.9875, resamples=2000, seed=7)
    assert tighter.value > up.value


def test_studentized_bootstrap_zero_se_resample_uses_full_sample_se():
    x = np.array([0.0] * 9 + [1.0])          # a resample of ten zeros has zero standard error
    b = studentized_bootstrap(x, "upper", 0.95, resamples=500, seed=3)
    assert np.isfinite(b.value) and b.degenerate is False and b.value >= x.mean()
    d = studentized_bootstrap(np.full(10, 2.0), "lower", 0.95, resamples=500, seed=3)
    assert d.degenerate is True and d.value == 2.0


def test_t_bound_and_interval_match_scipy():
    x = np.array([0.2, 0.5, 0.1, 0.9, 0.4, 0.6, 0.3, 0.8, 0.7, 0.35])
    n = len(x); se = x.std(ddof=1) / np.sqrt(n)
    assert t_bound(x, "upper", 0.95).value == pytest.approx(x.mean() + stats.t.ppf(0.95, n - 1) * se)
    assert t_bound(x, "lower", 0.9875).value == pytest.approx(x.mean() - stats.t.ppf(0.9875, n - 1) * se)
    lo, hi = t_interval(x, 0.95)
    assert (lo, hi) == pytest.approx((x.mean() - stats.t.ppf(0.975, n - 1) * se, x.mean() + stats.t.ppf(0.975, n - 1) * se))
    assert exact_t_bound_with_critical(x, "upper", 1.0) == pytest.approx(x.mean() + se)


def test_dispatch_reads_settings():
    settings = {"bootstrap_resamples": 300, "bootstrap_seed": 5}
    x = np.linspace(0, 1, 20)
    assert bound("percentile", x, "upper", 0.95, settings).method == "percentile"
    assert bound("studentized", x, "lower", 0.95, settings).method == "studentized"
    assert bound("t", x, "upper", 0.95, settings).method == "t"
    with pytest.raises(ValueError):
        bound("other", x, "upper", 0.95, settings)


def test_constant_inputs_with_inexact_means_are_degenerate():
    """Final review F9: ten copies of 1/3 have a floating-point std above zero; the degenerate test is x == x[0]."""
    import numpy as np
    from sim.intervals import studentized_bootstrap, t_bound
    x = np.full(10, 1 / 3)
    assert studentized_bootstrap(x, "upper", 0.95, 200, 1).degenerate and t_bound(x, "upper", 0.95).degenerate
    assert studentized_bootstrap(x, "upper", 0.95, 200, 1).value == 1 / 3
