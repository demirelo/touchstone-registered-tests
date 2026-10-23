"""The locked interval algorithms of spec 8. Every function is a pure function of its inputs and the seed."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

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


# ---- protocol v2 (design 9.2): arbitrary tails, bootstrap p-values, Holm, calibration, stratified and member bounds ----

V2_RESAMPLE_SEED = 20261022


@lru_cache(maxsize=16)
def _boot_idx(n: int, resamples: int, seed: int) -> np.ndarray:
    """The resample index matrix of a fixed seed (the same matrix studentized_bootstrap draws); cached for calibration."""
    idx = np.random.default_rng(int(seed)).integers(0, int(n), size=(int(resamples), int(n)))
    idx.setflags(write=False)
    return idx


@lru_cache(maxsize=16)
def _strat_idx(sizes: tuple, resamples: int, seed: int) -> tuple:
    out = []
    for n, kid in zip(sizes, np.random.SeedSequence(int(seed)).spawn(len(sizes))):
        idx = np.random.default_rng(kid).integers(0, int(n), size=(int(resamples), int(n))); idx.setflags(write=False); out.append(idx)
    return tuple(out)


def sample(x, what: str = "sample") -> np.ndarray:
    """A finite sample of at least two values; anything else is an error, never a decision."""
    x = np.asarray(x, dtype=float).ravel()
    if x.size < 2:
        raise ValueError(f"{what} has {x.size} value(s); at least two are needed")
    if not np.all(np.isfinite(x)):
        raise ValueError(f"{what} has nonfinite values")
    return x


def _mean_var(x: np.ndarray) -> tuple[float, float]:
    """Exact for a constant sample (its value, variance 0), so every path treats constant data alike."""
    if np.all(x == x[0]):
        return float(x[0]), 0.0
    return float(x.mean()), float(x.var(ddof=1))


def sample_mean(x) -> float:
    return _mean_var(sample(x))[0]


def _combine(means: list) -> float:
    """The equal-weight mean of stratum means, exact when they are all equal (the constant rule across strata)."""
    return float(means[0]) if all(m == means[0] for m in means) else float(np.mean(means))


def stratified_mean(strata) -> float:
    """The equal-weight mean of the stratum means (design 9.2)."""
    st = [sample(s, f"stratum {k}") for k, s in enumerate(strata)]
    if not st:
        raise ValueError("no strata")
    return _combine([_mean_var(s)[0] for s in st])


def studentized_tstats(x, resamples: int, seed: int) -> tuple[float, float, np.ndarray]:
    """Mean, standard error, and bootstrap-t statistics with studentized_bootstrap's resampling and zero-se rule; a
    constant sample returns its value, se 0, and all-zero statistics."""
    x = sample(x); n = x.size
    mean, var = _mean_var(x)
    if var == 0:
        return mean, 0.0, np.zeros(int(resamples))
    se = float(np.sqrt(var) / np.sqrt(n))
    samples = x[_boot_idx(n, int(resamples), int(seed))]
    m = samples.mean(axis=1); s = samples.std(axis=1, ddof=1) / np.sqrt(n)
    s = np.where(s > 0, s, se)
    return mean, se, ((m - mean) / s if se > 0 else np.zeros_like(m))


def _bound_from(mean: float, se: float, t: np.ndarray, side: str, tail: float) -> float:
    if se == 0:                                  # constant sample (or constant strata): the bound is the mean
        if side not in ("lower", "upper"):
            raise ValueError("side must be 'upper' or 'lower'")
        return float(mean)
    if side == "lower":
        return float(mean - np.quantile(t, 1.0 - tail) * se)
    if side == "upper":
        return float(mean - np.quantile(t, tail) * se)
    raise ValueError("side must be 'upper' or 'lower'")


def studentized_at(x, side: str, tail: float, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float:
    return _bound_from(*studentized_tstats(x, resamples, seed), side, tail)


def _pvalue_from(mean: float, se: float, t: np.ndarray, null: float, side: str) -> float:
    """Smallest tail at which the one-sided bound crosses `null`, at resolution 1 / (B + 1)."""
    if se == 0:
        above = mean > null if side == "lower" else mean < null
        return 0.0 if above else 1.0
    t_obs = (mean - float(null)) / se
    B = t.size
    count = int(np.sum(t >= t_obs)) if side == "lower" else int(np.sum(t <= t_obs))
    return min(1.0, (count + 1) / (B + 1)) if count < B else 1.0


def bootstrap_pvalue(x, null: float, side: str, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float:
    """side 'lower': H0 mean <= null (rejected when the lower bound exceeds null); 'upper': H0 mean >= null."""
    return _pvalue_from(*studentized_tstats(x, resamples, seed), null, side)


def two_sided_pvalue(x, null: float, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float:
    return min(1.0, 2.0 * min(bootstrap_pvalue(x, null, "lower", resamples, seed), bootstrap_pvalue(x, null, "upper", resamples, seed)))


def _p(p) -> float:
    p = float(p)
    if not (np.isfinite(p) and 0.0 <= p <= 1.0):
        raise ValueError(f"p-value {p} is not in [0, 1]")
    return p


def calibrated(p: float, kappa: float) -> float:
    if not (np.isfinite(float(kappa)) and 0.0 < float(kappa) <= 1.0):
        raise ValueError(f"kappa {kappa} is not in (0, 1]")
    return min(1.0, _p(p) / float(kappa))


def holm(pvalues, alpha: float = 0.05) -> list[bool]:
    pvalues = [_p(p) for p in pvalues]; m = len(pvalues); order = sorted(range(m), key=lambda i: pvalues[i]); out = [False] * m
    for rank, i in enumerate(order):
        if pvalues[i] <= alpha / (m - rank):
            out[i] = True
        else:
            break
    return out


def stratified_tstats(strata, resamples: int, seed: int) -> tuple[float, float, np.ndarray]:
    """Equal-weight mean of stratum means; stratum k resampled with its own child stream of SeedSequence(seed);
    se^2 = sum_k s_k^2 / n_k / K^2; bootstrap-t statistics with the zero-se rule (all-zero t when se is zero). Strata
    must be finite with at least two values each."""
    st = [sample(s, f"stratum {k}") for k, s in enumerate(strata)]; K = len(st)
    if not K:
        raise ValueError("no strata")
    mv = [_mean_var(s) for s in st]
    mean = _combine([m for m, _ in mv])
    se = float(np.sqrt(sum(v / s.size for (_, v), s in zip(mv, st))) / K)
    if se == 0:
        return mean, se, np.zeros(int(resamples))
    ms, vs = [], []
    for s, idx in zip(st, _strat_idx(tuple(s.size for s in st), int(resamples), int(seed))):
        r = s[idx]
        ms.append(r.mean(axis=1)); vs.append(r.var(axis=1, ddof=1) / s.size)
    se_b = np.sqrt(np.sum(vs, axis=0)) / K
    se_b = np.where(se_b > 0, se_b, se)
    return mean, se, (np.mean(ms, axis=0) - mean) / se_b


def stratified_at(strata, side: str, tail: float, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float:
    return _bound_from(*stratified_tstats(strata, resamples, seed), side, tail)


def stratified_pvalue(strata, null: float, side: str, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float:
    return _pvalue_from(*stratified_tstats(strata, resamples, seed), null, side)


def stratified_two_sided(strata, null: float, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> float:
    m, se, t = stratified_tstats(strata, resamples, seed)
    return min(1.0, 2.0 * min(_pvalue_from(m, se, t, null, "lower"), _pvalue_from(m, se, t, null, "upper")))


def gmin_bounds(member_rows, tail: float, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> tuple[float, float]:
    """Bounds of min_j E[g_j]: the minimum over members of the members' bounds at tail / c (simultaneous)."""
    c = len(member_rows)
    return (min(studentized_at(r, "lower", tail / c, resamples, seed) for r in member_rows),
            min(studentized_at(r, "upper", tail / c, resamples, seed) for r in member_rows))


def clopper_pearson_upper(x: int, n: int, confidence: float) -> float:
    return 1.0 if int(x) >= int(n) else float(stats.beta.ppf(float(confidence), int(x) + 1, int(n) - int(x)))
