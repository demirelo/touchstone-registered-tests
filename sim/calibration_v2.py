"""Coverage check and calibration of protocol v2 (design 9.5). Pools: 14 profiles run on the same seeds (common random
numbers), so per-seed differences keep their dependence. Fixtures: Q1 pools six equal-weight strata; Q4 checks each market.
Endpoints: Q1, both sides of the four pooled differences at the Holm tails 0.05/8, 0.05/6, 0.05/4, 0.05/2 (32); Q4, the
one-sided lower bounds of the gain difference and of the efficiency at 0.05/6 .. 0.05/1 per market (36 with three markets).
Selection: the largest kappa in (1, 1/2, 1/4) whose every endpoint misses at most alpha_e of 10,000 replications.
Validation: 20,000 independent replications; admitted if every endpoint's Clopper-Pearson upper bound at 1 - 0.01 / m_F
(m_F = 32 or 36 in every branch) is at most alpha_e. Admission is conditional on the empirical fixtures."""
from __future__ import annotations

import numpy as np

from .cell import Cell, SeedCache, run_focal
from .families_v2 import cand_from_json, family_for
from .intervals import clopper_pearson_upper
from .objectives_v2 import gross_efficiency
from .rules_v2 import make_rule, public_constants

PROFILES = ([("attack", "F000", "D2+H3")] + [("attack", r, f) for r in ("F111", "C*", "R4", "C*/S2") for f in ("D2+H3", "X7-SC")]
            + [("ref", r) for r in ("F000", "F111", "C*", "R4", "C*/S2")])
Q1_STATS = tuple(f"{a}-{b}|{f}" for a, b in (("F111", "C*"), ("R4", "C*/S2")) for f in ("D2+H3", "X7-SC"))
Q4_STATS = ("gain_diff", "eff")
Q1_TAILS = tuple(0.05 / (2 * m) for m in (4, 3, 2, 1))
Q4_TAILS = tuple(0.05 / m for m in (6, 5, 4, 3, 2, 1))
KAPPAS = (1.0, 0.5, 0.25)
BRANCHES = {"three20k": (("headline", "dev0", "dev1"), 20_000, 2), "two20k": (("headline", "dev0"), 20_000, 3), "two10k": (("headline", "dev0"), 10_000, 3)}
VALIDATION_OFFSET = 1_000_003


def key(p) -> str:
    return "|".join(p)


def build_pool(mkt: dict, attacks: dict, refs: dict, seeds: list[int], cred: dict) -> dict:
    """Every profile on the same seeds: row i of every profile comes from seed i."""
    cache = SeedCache(); out = {"seeds": list(seeds), "normalized": {}, "eff": {}}
    for p in PROFILES:
        rule = p[1]; rf = lambda rule=rule: make_rule(rule, 0.16, 10, cred=cred)
        cell = Cell(cfg=mkt["cfg"], rule_factory=rf, focal=mkt["focal"], seeds=tuple(seeds), name=key(p))
        if p[0] == "attack":
            T, L = int(mkt["cfg"].T), public_constants(rf(), mkt["cfg"])["L"]
            fam = family_for(p[2], T, L); k = dict(attacks[(rule, p[2])])
            fr = run_focal(cell, lambda: fam.make(k), cache)
        else:
            fr = run_focal(cell, cand_from_json(refs[rule]).policy_factory, cache)
        out["normalized"][key(p)] = [float(v) for v in fr.normalized]; out["eff"][key(p)] = gross_efficiency(fr.results).tolist()
    return out


def q1_stats(pool: dict) -> dict:
    n = {k: np.asarray(v) for k, v in pool["normalized"].items()}
    g = lambda r, f: n[f"attack|{r}|{f}"] - n[f"ref|{r}"]
    return {f"{a}-{b}|{f}": g(a, f) - g(b, f) for a, b in (("F111", "C*"), ("R4", "C*/S2")) for f in ("D2+H3", "X7-SC")}


def q4_stats(pool: dict) -> dict:
    n = {k: np.asarray(v) for k, v in pool["normalized"].items()}
    gain = lambda r: n[f"attack|{r}|D2+H3"] - n[f"ref|{r}"]
    return {"gain_diff": gain("F000") - gain("F111"), "eff": np.asarray(pool["eff"]["attack|F111|D2+H3"])}


def strata(pools: dict, branch: str, M: int | None = None) -> list[list]:
    markets, M0, k = BRANCHES[branch]; M = int(M or M0); size = M // k
    return [list(pools[m][:M])[s * size:(s + 1) * size] for m in markets for s in range(k)]


def endpoints(family: str, branch: str) -> list[dict]:
    if family == "Q1":
        return [{"fixture": "pooled", "stat": s, "side": side, "alpha_e": t} for s in Q1_STATS for side in ("lower", "upper") for t in Q1_TAILS]
    if family == "Q4":
        return [{"fixture": m, "stat": s, "side": "lower", "alpha_e": t} for m in BRANCHES[branch][0] for s in Q4_STATS for t in Q4_TAILS]
    raise ValueError(family)


def denominator(family: str) -> int:
    return {"Q1": 32, "Q4": 36}[family]


def _tstats(samples: np.ndarray, bidx: np.ndarray) -> tuple[float, float, np.ndarray]:
    n = samples.size; mean = samples.mean(); se = samples.std(ddof=1) / np.sqrt(n)
    r = samples[bidx]; m = r.mean(axis=1); s = r.std(axis=1, ddof=1) / np.sqrt(n); s = np.where(s > 0, s, se)
    return mean, se, (m - mean) / s


def miss_counts(rows, kind: str, tails, kappas, replications: int, resamples: int, seed: int, n: int = 200) -> dict:
    """Misses per (stat, side, tail, kappa): `rows` maps stat to a per-seed pool ("single") or is a list of stratum dicts
    ("pooled", equal weights); each replication draws n seeds with replacement per pool or stratum and shares the resample
    indices across statistics."""
    out = {}
    if kind == "single":
        stats = list(rows); truth = {s: float(np.mean(rows[s])) for s in stats}; M = len(next(iter(rows.values())))
    else:
        stats = list(rows[0]); truth = {s: float(np.mean([np.mean(st[s]) for st in rows])) for s in stats}
    for s in stats:
        for side in ("lower", "upper"):
            for t in tails:
                for kp in kappas:
                    out[(s, side, t, kp)] = 0
    for r in range(int(replications)):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), r]))
        if kind == "single":
            idx = rng.integers(0, M, n); bidx = rng.integers(0, n, (int(resamples), n))
            per = {s: _tstats(np.asarray(rows[s])[idx], bidx) for s in stats}
        else:
            draws = [(rng.integers(0, len(next(iter(st.values()))), n), rng.integers(0, n, (int(resamples), n))) for st in rows]
            per = {}
            for s in stats:
                K = len(rows); xs = [np.asarray(st[s])[i] for st, (i, _) in zip(rows, draws)]
                mean = float(np.mean([x.mean() for x in xs])); se = float(np.sqrt(sum(x.var(ddof=1) / n for x in xs)) / K)
                rs = [x[b] for x, (_, b) in zip(xs, draws)]
                mb = np.mean([q.mean(axis=1) for q in rs], axis=0); sb = np.sqrt(np.sum([q.var(axis=1, ddof=1) / n for q in rs], axis=0)) / K
                per[s] = (mean, se, (mb - mean) / np.where(sb > 0, sb, se))
        for s, (mean, se, t) in per.items():
            for tail in tails:
                for kp in kappas:
                    lo = mean - np.quantile(t, 1.0 - tail * kp) * se; hi = mean - np.quantile(t, tail * kp) * se
                    out[(s, "lower", tail, kp)] += int(lo > truth[s]); out[(s, "upper", tail, kp)] += int(hi < truth[s])
    return out


def endpoint_misses(family: str, fixtures, branch: str, kappa: float, replications: int, seed: int, resamples: int) -> dict:
    eps = endpoints(family, branch); out = {}
    if family == "Q1":
        c = miss_counts(fixtures["pooled"], "pooled", Q1_TAILS, [kappa], replications, resamples, seed)
        return {i: c[(e["stat"], e["side"], e["alpha_e"], kappa)] for i, e in enumerate(eps)}
    for m in BRANCHES[branch][0]:
        c = miss_counts(fixtures[m], "single", Q4_TAILS, [kappa], replications, resamples, seed)
        for i, e in enumerate(eps):
            if e["fixture"] == m:
                out[i] = c[(e["stat"], e["side"], e["alpha_e"], kappa)]
    return out


def select_kappa(family: str, fixtures, branch: str, seed: int, replications: int = 10_000, resamples: int = 9999) -> float | None:
    eps = endpoints(family, branch)
    for kp in KAPPAS:
        m = endpoint_misses(family, fixtures, branch, kp, replications, seed, resamples)
        if all(m[i] <= e["alpha_e"] * replications for i, e in enumerate(eps)):
            return kp
    return None


def validate(family: str, kappa: float, fixtures, branch: str, seed: int, replications: int = 20_000, resamples: int = 9999) -> dict:
    eps = endpoints(family, branch); conf = 1.0 - 0.01 / denominator(family)
    m = endpoint_misses(family, fixtures, branch, kappa, replications, int(seed) + VALIDATION_OFFSET, resamples)
    rows = [{**e, "misses": int(m[i]), "upper": clopper_pearson_upper(int(m[i]), int(replications), conf),
             "pass": clopper_pearson_upper(int(m[i]), int(replications), conf) <= e["alpha_e"]} for i, e in enumerate(eps)]
    return {"family": family, "kappa": kappa, "branch": branch, "replications": int(replications), "confidence": conf,
            "admitted": all(r["pass"] for r in rows), "endpoints": rows}
