"""Decision rules of protocol v2 (design draft 7, 9.3). Q1: two pooled tests (F111 vs C*, families D2+H3 and X7-SC) on
d = g_C* - g_F111 over the six fresh markets; Holm on calibrated two-sided p-values decides the direction and the calibrated
Bonferroni interval decides the size against the margin 0.05, in four exclusive categories; two fixed Holm slots (an
unavailable test enters with p = 1 and is not decided); a descriptive efficiency condition for the word "better". Q2:
effect-coded factorial contrasts and conditional effects (descriptive). Q4: per market, an intersection-union test (the
larger calibrated component p-value), then Holm across six fixed market slots. A family without an admitted multiplier
(kappa None) gets no confirmatory decision. A numerical refusal withholds only the affected test."""
from __future__ import annotations

import numpy as np

from .intervals import NumericalRefusal, calibrated, holm, stratified_at, stratified_mean, stratified_two_sided

MARGIN = 0.05
ALPHA = 0.05
NO_DECISION = "no confirmatory decision"
MISSING = "not decided: missing cell"
REFUSED = "not decided: numerical refusal"
Q1_SLOTS, Q4_SLOTS = 2, 6
EFF_MARGIN = 0.01


def q1_category(strata_diffs, kappa: float | None, holm_reject: bool, m: int = Q1_SLOTS) -> str:
    """d = g_C* - g_F111 (positive: R3 lower gain). Categories in order: materially lower, equivalent, ordered but size not
    established, inconclusive (design 9.3)."""
    if kappa is None:
        return NO_DECISION
    mean = stratified_mean(strata_diffs)                       # refuses nonfinite or short strata
    tail = ALPHA / (2 * m) * kappa
    lo, hi = stratified_at(strata_diffs, "lower", tail), stratified_at(strata_diffs, "upper", tail)
    if lo > MARGIN:
        return "R3 materially lower"
    if hi < -MARGIN:
        return "C* materially lower"
    if lo >= -MARGIN and hi <= MARGIN:
        return ("equivalent, direction R3 lower" if mean > 0 else "equivalent, direction C* lower") if holm_reject else "equivalent"
    return "ordered, size not established" if holm_reject else "inconclusive"


def q1_family(tests: dict, kappa: float | None, slots: int = Q1_SLOTS) -> dict:
    """Holm over the fixed slots; a test whose strata are None (a missing cell) or refused enters with p = 1, undecided."""
    names = list(tests)
    if kappa is None:
        return {n: {"p": None, "reject": None, "category": NO_DECISION} for n in names}
    p, why = [], {}
    for n in names:
        if tests[n] is None:
            p.append(1.0); why[n] = MISSING; continue
        try:
            p.append(calibrated(stratified_two_sided(tests[n], 0.0), kappa))
        except NumericalRefusal:
            p.append(1.0); why[n] = REFUSED
    p += [1.0] * max(0, int(slots) - len(p))
    rej = holm(p, ALPHA); out = {}
    for i, n in enumerate(names):
        if n in why:
            out[n] = {"p": None, "reject": None, "category": why[n]}; continue
        try:
            out[n] = {"p": p[i], "reject": rej[i], "category": q1_category(tests[n], kappa, rej[i], m=int(slots))}
        except NumericalRefusal:
            out[n] = {"p": None, "reject": None, "category": REFUSED}
    return out


def q1_efficiency(eff_strata, tail: float = 0.025) -> str:
    """The pooled paired gross-efficiency difference (the favoured rule minus the other): nominal one-sided 97.5 percent
    bounds against -0.01 (descriptive, not calibrated)."""
    lo, hi = stratified_at(eff_strata, "lower", tail), stratified_at(eff_strata, "upper", tail)
    if lo >= -EFF_MARGIN:
        return "efficiency condition met"
    if hi < -EFF_MARGIN:
        return "efficiency loss"
    return "efficiency non-inferiority unresolved"


def q1_better(category: str, efficiency: str) -> str | None:
    """'Better' needs category 1 in the rule's favour and the efficiency condition; labelled descriptive (design 9.3)."""
    if efficiency != "efficiency condition met":
        return None
    return {"R3 materially lower": "R3 better (efficiency evidence descriptive)",
            "C* materially lower": "C* better (efficiency evidence descriptive)"}.get(category)


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
            "P|S=1": diff(lambda p, g, s: s == 1 and p == 1, lambda p, g, s: s == 1 and p == 0),
            "P|G=0": diff(lambda p, g, s: g == 0 and p == 1, lambda p, g, s: g == 0 and p == 0),
            "P|G=1": diff(lambda p, g, s: g == 1 and p == 1, lambda p, g, s: g == 1 and p == 0),
            "G|S=0": diff(lambda p, g, s: s == 0 and g == 1, lambda p, g, s: s == 0 and g == 0),
            "G|S=1": diff(lambda p, g, s: s == 1 and g == 1, lambda p, g, s: s == 1 and g == 0)}


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

