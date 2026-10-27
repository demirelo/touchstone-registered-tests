"""Coverage check and calibration of protocol v2 (design draft 7, 9.5). Pools: 8 profiles run on the same seeds (common
random numbers), so per-seed differences keep their dependence. Fixtures: Q1 pools six equal-weight strata; Q4 checks each
market. Endpoints: Q1, both sides of the two pooled differences d = g_C* - g_F111 at the Holm tails 0.05/4 and 0.05/2 (8);
Q4, the one-sided lower bounds of the gain difference and of the efficiency at 0.05/6 .. 0.05/1 per market (36 with three
markets). Selection: the largest kappa in (1, 1/2, 1/4) whose every endpoint has a Clopper-Pearson upper bound, at
1 - 0.01 / m_F, at most alpha_e on 10,000 replications (the validation criterion). Validation: 20,000 independent
replications, the same criterion (m_F = 8 or 36 in every branch); no fallback after a failed validation. Admission is
conditional on the empirical fixtures."""
from __future__ import annotations

import numpy as np

from .cell import Cell, SeedCache, run_focal
from .families_v2 import cand_from_json, family_for
from .intervals import (V2_RESAMPLE_SEED, _bound_from, clopper_pearson_upper, sample, sample_mean, stratified_at, stratified_mean,
                        stratified_tstats, studentized_at, studentized_tstats)
from .objectives_v2 import gross_efficiency
from .rules_v2 import make_rule, public_constants

PROFILES = ([("attack", "F000", "D2+H3")] + [("attack", r, f) for r in ("F111", "C*") for f in ("D2+H3", "X7-SC")]
            + [("ref", r) for r in ("F000", "F111", "C*")])
Q1_STATS = tuple(f"C*-F111|{f}" for f in ("D2+H3", "X7-SC"))
Q4_STATS = ("gain_diff", "eff")
Q1_TAILS = tuple(0.05 / (2 * m) for m in (2, 1))
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
    return {f"C*-F111|{f}": g("C*", f) - g("F111", f) for f in ("D2+H3", "X7-SC")}


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
    return {"Q1": 8, "Q4": 36}[family]


def bound_single(x, side: str, tail: float, resamples: int = 9999) -> float:
    """The production bound (fixed bootstrap seed) for one sample."""
    return studentized_at(x, side, tail, resamples, V2_RESAMPLE_SEED)


def bound_pooled(strata, side: str, tail: float, resamples: int = 9999) -> float:
    return stratified_at(strata, side, tail, resamples, V2_RESAMPLE_SEED)


def miss_counts(rows, kind: str, tails, kappas, replications: int, resamples: int, seed: int, n: int = 200, trace: list | None = None) -> dict:
    """Misses per (stat, side, tail, kappa): `rows` maps stat to a per-seed pool ("single") or is a list of stratum dicts
    ("pooled", equal weights). Replication r draws n seeds with replacement per pool or stratum from SeedSequence([seed, r]);
    the bounds are the production bounds (the fixed bootstrap streams of design 9.2, the same tstats and bound functions,
    so constant data give the same exact bound). The truth is the pool's mean by the production mean rule. Nonfinite
    pools or bounds are an error. `trace`, if given, receives (r, stat, side, tail, kappa, bound) for every bound."""
    out = {}
    if kind == "single":
        rows = {s: sample(v, f"pool {s}") for s, v in rows.items()}
        stats = list(rows); truth = {s: sample_mean(rows[s]) for s in stats}; M = len(next(iter(rows.values())))
    else:
        rows = [{s: sample(v, f"stratum {k} pool {s}") for s, v in st.items()} for k, st in enumerate(rows)]
        stats = list(rows[0]); truth = {s: stratified_mean([st[s] for st in rows]) for s in stats}
    for s in stats:
        for side in ("lower", "upper"):
            for t in tails:
                for kp in kappas:
                    out[(s, side, t, kp)] = 0
    for r in range(int(replications)):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), r]))
        if kind == "single":
            idx = rng.integers(0, M, n)
            per = {s: studentized_tstats(rows[s][idx], resamples, V2_RESAMPLE_SEED) for s in stats}
        else:
            draws = [rng.integers(0, len(next(iter(st.values()))), n) for st in rows]
            per = {s: stratified_tstats([st[s][i] for st, i in zip(rows, draws)], resamples, V2_RESAMPLE_SEED) for s in stats}
        for s, (mean, se, t) in per.items():
            for tail in tails:
                for kp in kappas:
                    lo, hi = _bound_from(mean, se, t, "lower", tail * kp), _bound_from(mean, se, t, "upper", tail * kp)
                    if not (np.isfinite(lo) and np.isfinite(hi)):
                        raise ValueError(f"nonfinite bound for {s}")
                    if trace is not None:
                        trace += [(r, s, "lower", tail, kp, lo), (r, s, "upper", tail, kp, hi)]
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
    eps = endpoints(family, branch); conf = 1.0 - 0.01 / denominator(family)
    for kp in KAPPAS:
        m = endpoint_misses(family, fixtures, branch, kp, replications, seed, resamples)
        if all(clopper_pearson_upper(int(m[i]), int(replications), conf) <= e["alpha_e"] for i, e in enumerate(eps)):
            return kp
    return None


def validate(family: str, kappa: float, fixtures, branch: str, seed: int, replications: int = 20_000, resamples: int = 9999) -> dict:
    eps = endpoints(family, branch); conf = 1.0 - 0.01 / denominator(family)
    m = endpoint_misses(family, fixtures, branch, kappa, replications, int(seed) + VALIDATION_OFFSET, resamples)
    rows = [{**e, "misses": int(m[i]), "upper": clopper_pearson_upper(int(m[i]), int(replications), conf),
             "pass": clopper_pearson_upper(int(m[i]), int(replications), conf) <= e["alpha_e"]} for i, e in enumerate(eps)]
    return {"family": family, "kappa": kappa, "branch": branch, "replications": int(replications), "confidence": conf,
            "admitted": all(r["pass"] for r in rows), "endpoints": rows}
