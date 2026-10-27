"""Decision rules of protocol v2 (design 9.3). Q1: four pooled tests on the six fresh markets (Holm on calibrated two-sided
p-values; categories ordered, equivalent, inconclusive, in that order). Q2: effect-coded factorial contrasts and
conditional effects (descriptive). Q4: per market, an intersection-union test (the larger calibrated component p-value),
then Holm across the six markets. A family without an admitted multiplier (kappa None) gets no confirmatory decision."""
from __future__ import annotations

import numpy as np

from .intervals import calibrated, holm, stratified_at, stratified_mean, stratified_two_sided

MARGIN = 0.05
ALPHA = 0.05
NO_DECISION = "no confirmatory decision"


def q1_category(strata_diffs, kappa: float | None, holm_reject: bool, m: int = 4) -> str:
    if kappa is None:
        return NO_DECISION
    mean = stratified_mean(strata_diffs)                       # refuses nonfinite or short strata
    if holm_reject:
        return "R lower" if mean < 0 else "C lower"
    tail = ALPHA / (2 * m) * kappa
    lo, hi = stratified_at(strata_diffs, "lower", tail), stratified_at(strata_diffs, "upper", tail)
    return "equivalent" if (lo >= -MARGIN and hi <= MARGIN) else "inconclusive"


def q1_family(tests: dict, kappa: float | None) -> dict:
    names = list(tests)
    if kappa is None:
        return {n: {"p": None, "reject": None, "category": NO_DECISION} for n in names}
    p = [calibrated(stratified_two_sided(tests[n], 0.0), kappa) for n in names]
    rej = holm(p, ALPHA)
    return {n: {"p": p[i], "reject": rej[i], "category": q1_category(tests[n], kappa, rej[i], m=len(names))} for i, n in enumerate(names)}


def q2_contrasts(cell_means: dict) -> dict:
    cells = {(int(c[1]), int(c[2]), int(c[3])): float(v) for c, v in cell_means.items()}
    mean = lambda pred: float(np.mean([v for k, v in cells.items() if pred(*k)]))
    diff = lambda a, b: mean(a) - mean(b)
    return {"P": diff(lambda p, g, s: p == 1, lambda p, g, s: p == 0), "G": diff(lambda p, g, s: g == 1, lambda p, g, s: g == 0),
            "S": diff(lambda p, g, s: s == 1, lambda p, g, s: s == 0),
            "PG": diff(lambda p, g, s: p == g, lambda p, g, s: p != g), "PS": diff(lambda p, g, s: p == s, lambda p, g, s: p != s),
            "GS": diff(lambda p, g, s: g == s, lambda p, g, s: g != s),
            "PGS": diff(lambda p, g, s: (p + g + s) % 2 == 1, lambda p, g, s: (p + g + s) % 2 == 0),
            "G|P=0": diff(lambda p, g, s: p == 0 and g == 1, lambda p, g, s: p == 0 and g == 0),
            "G|P=1": diff(lambda p, g, s: p == 1 and g == 1, lambda p, g, s: p == 1 and g == 0),
            "P|S=0": diff(lambda p, g, s: s == 0 and p == 1, lambda p, g, s: s == 0 and p == 0),
            "P|S=1": diff(lambda p, g, s: s == 1 and p == 1, lambda p, g, s: s == 1 and p == 0)}


def q4_markets(pa: list, pb: list, kappa: float | None) -> dict:
    if kappa is None:
        return {"decided": False, "p": None, "pass": None, "k": None}
    p = [max(calibrated(a, kappa), calibrated(b, kappa)) for a, b in zip(pa, pb)]
    rej = holm(p, ALPHA)
    return {"decided": True, "p": p, "pass": rej, "k": int(sum(rej))}


def w1_class(lower: float, upper: float) -> str:
    """Design 6.2 (draft 7): W1 profitability on evaluation seeds from the constraint mean's interval."""
    if float(lower) >= 0.0:
        return "supported"
    if float(upper) < 0.0:
        return "contradicted"
    return "unresolved"

