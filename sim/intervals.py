"""The locked interval algorithms of spec 8. Every function is a pure function of its inputs and the seed."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass(frozen=True)
class Bound:
    value: float
    side: str
    level: float
    method: str
    degenerate: bool
    n: int


def _check(x: np.ndarray, side: str, level: float) -> np.ndarray:
    x = np.asarray(x, dtype=float).ravel()
    if x.size < 2 or not np.all(np.isfinite(x)):
        raise ValueError("need at least two finite per-seed values")
    if side not in ("upper", "lower"):
        raise ValueError("side must be 'upper' or 'lower'")
    if not (0.5 < level < 1.0):
        raise ValueError("level must be in (0.5, 1)")
    return x


def percentile_bootstrap(x, side: str, level: float, resamples: int, seed: int) -> Bound:
    """One-sided percentile bootstrap of the mean; the seed is the resampling unit (spec 8)."""
    x = _check(x, side, level); n = x.size
    if np.all(x == x[0]):
        return Bound(float(x[0]), side, level, "percentile", True, n)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, n, size=(int(resamples), n))
    means = x[idx].mean(axis=1)
    q = level if side == "upper" else 1.0 - level
    return Bound(float(np.quantile(means, q)), side, level, "percentile", False, n)


def studentized_bootstrap(x, side: str, level: float, resamples: int, seed: int) -> Bound:
    """Bootstrap-t: each resample studentized by its own standard error; a zero-standard-error resample
    uses the full-sample standard error (spec 8)."""
    x = _check(x, side, level); n = x.size
    mean = x.mean(); se = x.std(ddof=1) / np.sqrt(n)
    if np.all(x == x[0]):                                        # exact constancy, not std == 0: ten copies of 1/3 have a nonzero float std
        return Bound(float(x[0]), side, level, "studentized", True, n)
    rng = np.random.default_rng(int(seed))
    idx = rng.integers(0, n, size=(int(resamples), n))
    samples = x[idx]
    m = samples.mean(axis=1); s = samples.std(axis=1, ddof=1) / np.sqrt(n)
    s = np.where(s > 0, s, se)
    tstat = (m - mean) / s
    if side == "upper":
        return Bound(float(mean - np.quantile(tstat, 1.0 - level) * se), side, level, "studentized", False, n)
    return Bound(float(mean - np.quantile(tstat, level) * se), side, level, "studentized", False, n)


def t_bound(x, side: str, level: float) -> Bound:
    """One-sided Student t bound on the mean (H1's 10 repetitions, spec 8)."""
    x = _check(x, side, level); n = x.size
    se = x.std(ddof=1) / np.sqrt(n)
    crit = stats.t.ppf(level, n - 1)
    degenerate = bool(np.all(x == x[0]))
    value = float(x[0]) if degenerate else (x.mean() + crit * se if side == "upper" else x.mean() - crit * se)
    return Bound(float(value), side, level, "t", degenerate, n)


def exact_t_bound_with_critical(x, side: str, critical: float) -> float:
    """A one-sided t-type bound at an arbitrary critical value (the coverage study's negative control)."""
    x = np.asarray(x, dtype=float).ravel(); n = x.size
    se = x.std(ddof=1) / np.sqrt(n)
    return float(x.mean() + critical * se if side == "upper" else x.mean() - critical * se)


def t_interval(x, level: float = 0.95) -> tuple[float, float]:
    """Two-sided t interval on the mean (the reference-mean interval of the coverage study)."""
    x = np.asarray(x, dtype=float).ravel(); n = x.size
    se = x.std(ddof=1) / np.sqrt(n)
    h = stats.t.ppf(0.5 + level / 2.0, n - 1) * se
    return float(x.mean() - h), float(x.mean() + h)


def bound(method: str, x, side: str, level: float, settings: dict) -> Bound:
    if method == "percentile":
        return percentile_bootstrap(x, side, level, int(settings["bootstrap_resamples"]), int(settings["bootstrap_seed"]))
    if method == "studentized":
        return studentized_bootstrap(x, side, level, int(settings["bootstrap_resamples"]), int(settings["bootstrap_seed"]))
    if method == "t":
        return t_bound(x, side, level)
    raise ValueError(f"unknown interval method {method!r}")
