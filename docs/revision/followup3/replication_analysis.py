"""Analysis of the churn replication (docs/revision/followup3/replication-plan.md, sections 2 and 3), fixed before the
draw. Input: gains[rate][market][rule] = per-seed normalised gains (one winner set), rules R3, C*, C-thr, B3, rates "0",
"0.03", "0.05"; audit[rate][market] = (audited jobs, served jobs) of the attacker under R3. Output: the paired changes
from each market's own no-churn value, the descriptive support criterion and its material companion, the five
expectations, and the seed-bootstrap pooled contrasts. Exploratory; no registered calibration; intervals omit search
uncertainty."""
import math
import random

CONTRASTS = {"d": "C*", "q": "B3", "u": "C-thr"}   # x = g(comparator) - g(R3)
RATES = ("0.03", "0.05")
T5 = 2.570581835636314                             # 0.975 quantile of Student's t, 5 degrees of freedom
MATERIAL = -0.05                                   # the registered Q1 margin
RESAMPLES, SEED = 9999, 0


def _mean(xs):
    return sum(xs) / len(xs)


def _check(gains: dict) -> None:
    for p, ms in gains.items():
        for m, rs in ms.items():
            for r, xs in rs.items():
                if not xs or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in xs):
                    raise ValueError(f"{p} {m} {r}: missing or nonfinite gains")


def _t95(xs: list) -> list:
    n = len(xs); m = _mean(xs); sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = T5 * sd / math.sqrt(n)
    return [m - half, m + half]


def contrast(cell: dict, comparator: str):
    """Mean of g(comparator) - g(R3) over the seeds of one market, or None if a rule is missing."""
    if comparator not in cell or "R3" not in cell:
        return None
    return _mean(cell[comparator]) - _mean(cell["R3"])


def paired_changes(gains: dict) -> dict:
    """Delta_x(m, p) = x(m, p) - x(m, 0) per contrast and positive rate; mean, market t interval and markets lower.
    A market missing a needed rule at either rate leaves that contrast incomplete (complete = False)."""
    _check(gains)
    out = {}
    for p in RATES:
        out[p] = {}
        for x, comp in CONTRASTS.items():
            ms, complete = {}, True
            for m in gains["0"]:
                a, b = contrast(gains[p].get(m, {}), comp), contrast(gains["0"][m], comp)
                if a is None or b is None:
                    complete = False; continue
                ms[m] = a - b
            vals = list(ms.values())
            out[p][x] = {"markets": ms, "complete": complete and len(vals) == len(gains["0"]),
                         "mean": _mean(vals) if vals else None, "t95": _t95(vals) if len(vals) > 1 else None,
                         "lower": sum(1 for v in vals if v < 0)}
    return out


def criteria(pc: dict) -> dict:
    """Support (descriptive): mean < 0 and at least 5 of 6 markets lower; material: mean <= -0.05. None if incomplete."""
    out = {}
    for p, xs in pc.items():
        out[p] = {}
        for x, r in xs.items():
            if not r["complete"]:
                out[p][x] = None; continue
            out[p][x] = {"support": r["mean"] < 0 and r["lower"] >= 5, "material": r["mean"] <= MATERIAL}
    return out


def _verdict(*conds):
    if any(c is None for c in conds):
        return "not scorable"
    return "met" if all(conds) else "not met"


def expectations(crit: dict, audit: dict) -> dict:
    s = lambda p, x: None if crit[p][x] is None else crit[p][x]["support"]
    below = None
    if all(m in audit.get("0", {}) and m in audit.get("0.05", {}) for m in audit.get("0", {})) and audit.get("0"):
        n = 0
        for m in audit["0"]:
            (a0, s0), (a5, s5) = audit["0"][m], audit["0.05"][m]
            if s0 and s5 and a5 / s5 < a0 / s0:             # a zero denominator at either rate counts as not below
                n += 1
        below = n >= 5
    return {"1": {"text": "support for d at p = 0.05", "verdict": _verdict(s("0.05", "d"))},
            "2": {"text": "support for q at p = 0.05", "verdict": _verdict(s("0.05", "q"))},
            "3": {"text": "support for d and q at p = 0.03", "verdict": _verdict(s("0.03", "d"), s("0.03", "q"))},
            "4": {"text": "support for u (runner-up) at p = 0.05; subjective prospective probability 0.5",
                  "verdict": _verdict(s("0.05", "u"))},
            "5": {"text": "R3's audited share of the attacker's jobs lower at p = 0.05 than at p = 0 on at least 5 of 6 markets",
                  "verdict": _verdict(below)}}


def pooled_paired(cells: dict, comparator: str, resamples: int = RESAMPLES, seed: int = SEED) -> dict:
    """Equal-weight pooled g(comparator) - g(R3) over markets with a 95 percent paired percentile bootstrap: seeds are
    resampled within each market with one index vector per market shared by both rules."""
    rng = random.Random(seed)
    ms = sorted(cells)
    diffs = {m: [c - r for c, r in zip(cells[m][comparator], cells[m]["R3"])] for m in ms}
    est = _mean([_mean(diffs[m]) for m in ms])
    boots = []
    for _ in range(resamples):
        tot = 0.0
        for m in ms:
            d = diffs[m]; n = len(d)
            tot += sum(d[rng.randrange(n)] for _ in range(n)) / n
        boots.append(tot / len(ms))
    boots.sort()
    lo, hi = boots[int(0.025 * (resamples + 1)) - 1], boots[int(0.975 * (resamples + 1)) - 1]
    return {"estimate": est, "ci95": [lo, hi], "resamples": resamples, "seed": seed}
