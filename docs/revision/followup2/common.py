"""Shared descriptive analysis of the follow-up runs in docs/revision/followup2 (exploratory, after the report).

The registered Q1 machinery used studentized bootstrap intervals with calibrated tails and Holm; these follow-up runs
are not registered, so they use a nominal paired percentile bootstrap (seeds resampled within each market, the same
resampled indices for both rules, equal market weights) and apply the registered Q1 category rules to that nominal
interval, labelled exploratory. d = g(comparator) - g(R3); positive means R3 leaves the lower gain."""
from __future__ import annotations

import numpy as np

MARGIN = 0.05                                       # the registered Q1 margin (design 9.3)
RESAMPLES, SEED = 9999, 0
SCOPE = ("nominal paired percentile bootstrap over seeds, conditional on these markets and the selected policies and references; "
         "no search or market-sampling uncertainty; no registered calibration or Holm guarantee")


def pooled_paired(a: dict, b: dict, resamples: int = RESAMPLES, seed: int = SEED, level: float = 0.95) -> dict:
    """`a`, `b`: market -> per-seed gains on the same seeds in the same order. Pooled = mean of the market means."""
    markets = sorted(a)
    if sorted(b) != markets:
        raise ValueError("the two rules cover different markets")
    diffs = {}
    for m in markets:
        x, y = np.asarray(a[m], float), np.asarray(b[m], float)
        if x.shape != y.shape:
            raise ValueError(f"{m}: unequal seed counts")
        diffs[m] = x - y
    rng = np.random.default_rng(seed); per = {m: np.empty(resamples) for m in markets}
    for i in range(resamples):
        for m in markets:
            d = diffs[m]; per[m][i] = d[rng.integers(0, len(d), len(d))].mean()
    reps = np.mean([per[m] for m in markets], axis=0)
    q = (1 - level) / 2; iv = lambda r: [float(np.quantile(r, q)), float(np.quantile(r, 1 - q))]
    return {"markets": {m: float(diffs[m].mean()) for m in markets}, "market_intervals": {m: iv(per[m]) for m in markets},
            "estimate": float(np.mean([diffs[m].mean() for m in markets])), "interval": iv(reps), "resamples": resamples, "seed": seed, "level": level,
            "scope": SCOPE}


def q1_category(interval) -> str:
    """The registered Q1 categories (design 9.3), applied descriptively to a nominal interval."""
    lo, hi = interval
    if lo > MARGIN:
        return "materially lower (R3 lower)"
    if hi < -MARGIN:
        return "materially lower (comparator lower)"
    if -MARGIN <= lo and hi <= MARGIN:
        if lo > 0:
            return "equivalent, direction R3 lower"
        if hi < 0:
            return "equivalent, direction comparator lower"
        return "equivalent"
    if lo > 0 or hi < 0:
        return "ordered, size not established"
    return "inconclusive"
