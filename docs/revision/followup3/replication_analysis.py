"""Analysis of the churn replication (docs/revision/followup3/replication-plan.md, sections 2 and 3), fixed before the
draw. Input per winner set: recs[rate][market][rule] = per-seed lists {"gain", "attack", "reference", "eff_attack",
"seeds"} for markets rep0..rep5, rules R3, C*, C-thr, B3 and rates "0", "0.03", "0.05"; audit[rate][market] =
(audited jobs, served jobs) of the attacker under R3. Output: the paired changes from each market's own no-churn value,
the descriptive support criterion and its material companion, the five expectations, the absolute contrasts, the attack
and reference terms and efficiency under attack, and the seed-bootstrap intervals with one index vector per market
shared by every rule, rate and winner set. A missing cell makes what needs it "not scorable"; a malformed cell (nonfinite
values, unequal seed vectors within a market) is refused. Exploratory; intervals omit search uncertainty."""
import math

import numpy as np

MARKETS = tuple(f"rep{i}" for i in range(6))
RULES = ("R3", "C*", "C-thr", "B3")
CONTRASTS = {"d": "C*", "q": "B3", "u": "C-thr"}   # x = g(comparator) - g(R3)
RATES = ("0.03", "0.05")
ALL_RATES = ("0",) + RATES
T5 = 2.570581835636314                             # 0.975 quantile of Student's t, 5 degrees of freedom
MATERIAL = -0.05                                   # the registered Q1 margin
RESAMPLES, SEED = 9999, 0
FIELDS = ("gain", "attack", "reference", "eff_attack")


def _mean(xs):
    return sum(xs) / len(xs)


def _finite(xs) -> bool:
    return bool(xs) and all(isinstance(x, (int, float)) and math.isfinite(x) for x in xs)


def _check(gains: dict) -> None:
    """Every present cell finite; within a market every rule and rate has the same number of seeds."""
    for m in MARKETS:
        lens = set()
        for p in ALL_RATES:
            for r, xs in (gains.get(p, {}).get(m) or {}).items():
                if not _finite(xs):
                    raise ValueError(f"{p} {m} {r}: missing or nonfinite gains")
                lens.add(len(xs))
        if len(lens) > 1:
            raise ValueError(f"{m}: unequal seed vectors {sorted(lens)}")


def _check_recs(recs: dict) -> None:
    for m in MARKETS:
        seeds = None
        for p in ALL_RATES:
            for r, c in (recs.get(p, {}).get(m) or {}).items():
                for f in FIELDS:
                    if not _finite(c.get(f)):
                        raise ValueError(f"{p} {m} {r}: missing or nonfinite {f}")
                if len({len(c[f]) for f in FIELDS} | {len(c["seeds"])}) != 1:
                    raise ValueError(f"{p} {m} {r}: fields of unequal length")
                if seeds is None:
                    seeds = list(c["seeds"])
                elif list(c["seeds"]) != seeds:
                    raise ValueError(f"{p} {m} {r}: seeds differ from the market's other cells")


def gains_of(recs: dict) -> dict:
    return {p: {m: {r: list(c["gain"]) for r, c in rs.items()} for m, rs in ms.items()} for p, ms in recs.items()}


def _t95(xs: list) -> list:
    n = len(xs); m = _mean(xs); sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    half = T5 * sd / math.sqrt(n)
    return [m - half, m + half]


def contrast(cell: dict, comparator: str):
    """Mean of g(comparator) - g(R3) over the seeds of one market, or None if a rule is missing."""
    if comparator not in cell or "R3" not in cell:
        return None
    return _mean(cell[comparator]) - _mean(cell["R3"])


def _cell(gains, p, m):
    return gains.get(p, {}).get(m) or {}


def paired_changes(gains: dict) -> dict:
    """Delta_x(m, p) = x(m, p) - x(m, 0) per contrast and positive rate over the six named markets; mean, market t interval
    and markets lower. A market missing a needed rule at either rate leaves that contrast incomplete."""
    _check(gains)
    out = {}
    for p in RATES:
        out[p] = {}
        for x, comp in CONTRASTS.items():
            ms = {}
            for m in MARKETS:
                a, b = contrast(_cell(gains, p, m), comp), contrast(_cell(gains, "0", m), comp)
                if a is not None and b is not None:
                    ms[m] = a - b
            vals = list(ms.values())
            out[p][x] = {"markets": ms, "complete": len(ms) == len(MARKETS),
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
    s = lambda p, x: None if crit.get(p, {}).get(x) is None else crit[p][x]["support"]
    below = None
    if all(m in audit.get("0", {}) and m in audit.get("0.05", {}) for m in MARKETS):
        n = 0
        for m in MARKETS:
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


def boot_indices(n_by_market: dict, resamples: int = RESAMPLES, seed: int = SEED) -> dict:
    """One (resamples x n) index array per market, drawn in market order from one generator seeded with `seed`; the
    same arrays serve every rule, rate and winner set (the churn arm's pairing)."""
    rng = np.random.default_rng(seed)
    return {m: rng.integers(0, n_by_market[m], size=(resamples, n_by_market[m])) for m in MARKETS if m in n_by_market}


def _ci(boots) -> list:
    b = np.sort(np.asarray(boots)); k = len(b)
    return [float(b[int(0.025 * (k + 1)) - 1]), float(b[int(0.975 * (k + 1)) - 1])]


def bootstrap(gains: dict, idx: dict) -> dict:
    """Per contrast and rate: per-market and equal-weight pooled percentile intervals of the absolute contrast x at every
    rate (its own cells only), and of the paired change Delta_x at the positive rates (it also needs the p = 0 cells),
    from the shared index arrays. A missing cell gives no market entry; a pooled interval needs all six markets."""
    bm = {}                                                  # bm[m][p][r] = resampled means (resamples,)
    for m, ix in idx.items():
        bm[m] = {p: {r: np.asarray(xs)[ix].mean(axis=1) for r, xs in _cell(gains, p, m).items()} for p in ALL_RATES}
    out = {}
    for p in ALL_RATES:
        out[p] = {}
        for x, comp in CONTRASTS.items():
            delta, absolute = {}, {}
            for m in MARKETS:
                b = bm.get(m, {})
                if all(r in b.get(p, {}) for r in (comp, "R3")):
                    absolute[m] = b[p][comp] - b[p]["R3"]
                    if p != "0" and all(r in b.get("0", {}) for r in (comp, "R3")):
                        delta[m] = absolute[m] - (b["0"][comp] - b["0"]["R3"])
            row = {"absolute_markets": {m: {"ci95": _ci(v)} for m, v in absolute.items()},
                   "absolute_pooled": {"ci95": _ci(sum(absolute.values()) / len(MARKETS))} if len(absolute) == len(MARKETS) else None}
            if p != "0":
                row.update({"markets": {m: {"ci95": _ci(v)} for m, v in delta.items()},
                            "pooled": {"ci95": _ci(sum(delta.values()) / len(MARKETS))} if len(delta) == len(MARKETS) else None})
            out[p][x] = row
    return out


def absolute(gains: dict, boot: dict) -> dict:
    """The absolute contrasts x(m, p) at every rate (secondary, descriptive): per market with its seed interval, mean,
    market t interval (all six markets only) and the pooled seed interval (all six markets only)."""
    out = {}
    for p in ALL_RATES:
        out[p] = {}
        for x, comp in CONTRASTS.items():
            ms = {m: contrast(_cell(gains, p, m), comp) for m in MARKETS}
            ms = {m: v for m, v in ms.items() if v is not None}
            b = boot.get(p, {}).get(x, {})
            vals = list(ms.values())
            out[p][x] = {"markets": {m: {"estimate": v, "ci95": (b.get("absolute_markets", {}).get(m) or {}).get("ci95")}
                                     for m, v in ms.items()},
                         "complete": len(ms) == len(MARKETS), "mean": _mean(vals) if vals else None,
                         "t95": _t95(vals) if len(ms) == len(MARKETS) else None,
                         "pooled_ci95": (b.get("absolute_pooled") or {}).get("ci95")}
    return out


def terms(recs: dict) -> dict:
    """Per cell: the mean gain, attack term and reference term (gain = attack - reference) and efficiency under attack."""
    return {p: {m: {r: {f: _mean(c[f]) for f in FIELDS} for r, c in (recs.get(p, {}).get(m) or {}).items()}
                for m in MARKETS} for p in ALL_RATES}


def analyse(recs: dict, audit: dict, resamples: int = RESAMPLES, seed: int = SEED) -> dict:
    """Everything the plan reports for one winner set."""
    _check_recs(recs)
    g = gains_of(recs)
    pc = paired_changes(g); cr = criteria(pc)
    n = {}
    for p in ALL_RATES:
        for m, rs in (g.get(p) or {}).items():
            for xs in rs.values():
                n[m] = len(xs)
    boot = bootstrap(g, boot_indices(n, resamples, seed))
    return {"paired_changes": pc, "criteria": cr, "expectations": expectations(cr, audit), "absolute": absolute(g, boot),
            "terms": terms(recs), "bootstrap": boot, "resamples": resamples, "seed": seed}
