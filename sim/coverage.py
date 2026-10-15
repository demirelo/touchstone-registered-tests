"""Coverage study (spec 8): the registered cell selection (ruling D12), fresh seed blocks, per-seed scalar observations
for the eight endpoints computed in chunks, conservative scoring against the reference-mean interval, the analytic
threshold with its registered simulation check, the joint fixture test and control power (scipy Hermite rule),
admission in the remedy order, and the report."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from scipy import stats
from scipy.special import roots_hermite

from .cell import Cell, SeedCache, run_focal
from .intervals import Bound, bound, t_interval
from .records import cfg_from_dict

STATISTICS = ("gain", "eff", "loss_diff")
ENDPOINTS = (("gain", "upper", 0.95), ("gain", "lower", 0.95), ("eff", "lower", 0.95), ("eff", "upper", 0.95),
             ("loss_diff", "lower", 0.9875), ("loss_diff", "upper", 0.9875), ("gain", "lower", 0.9875), ("gain", "upper", 0.9875))
LEVELS = (0.95, 0.9875)
PROCEDURES_AT_N = {10: ("t",), 20: ("percentile", "studentized"), 40: ("studentized",)}
BASE_N = (10, 20)
CONDITIONAL_N = (40,)


def endpoint_key(stat: str, side: str, level: float, n: int) -> str:
    return f"{stat}|{side}|{level}|{n}"


# ---- selection (ruling D12) -------------------------------------------------------------------------------------------

def skewness(x) -> float:
    x = np.asarray(x, dtype=float)
    return float("nan") if x.size < 3 or np.std(x) == 0.0 else float(stats.skew(x, bias=False))


def sarle_bimodality(x) -> float:
    x = np.asarray(x, dtype=float); n = x.size
    if n < 4 or np.std(x) == 0.0:
        return float("nan")
    g = float(stats.skew(x, bias=False)); k = float(stats.kurtosis(x, bias=False))
    return (g * g + 1.0) / (k + 3.0 * (n - 1) ** 2 / ((n - 2) * (n - 3)))


def select_cells(stats_by_cell: dict, k: int = 3) -> list:
    """Top k by gain skewness and top k by the Sarle coefficient of ban counts (finite values, descending, name as the
    tie-break); their union in order (skewness picks, then Sarle picks); while fewer than 2k, the next unused entry of
    the ranking that has contributed fewer distinct cells (ties to skewness); an exhausted ranking yields to the other."""
    def ranking(key):
        valid = [(float(v[key]), name) for name, v in stats_by_cell.items() if math.isfinite(float(v[key]))]
        return [name for _, name in sorted(valid, key=lambda p: (-p[0], p[1]))]
    ranks = [ranking("skew_gain"), ranking("sarle_bans")]
    chosen: list = []; contributed = [0, 0]; cursor = [0, 0]

    def take(i) -> bool:
        while cursor[i] < len(ranks[i]):
            name = ranks[i][cursor[i]]; cursor[i] += 1
            if name not in chosen:
                chosen.append(name); contributed[i] += 1
                return True
        return False

    for i in (0, 1):
        for _ in range(k):
            take(i)
    while len(chosen) < 2 * k:
        first = 1 if contributed[1] < contributed[0] else 0
        if not take(first) and not take(1 - first):
            break
    return chosen


# ---- seeds and observations ------------------------------------------------------------------------------------------

def seed_blocks(locked: dict, cell_index: int, pool_factor: int = 1, rep_factor: int = 1, n_list=None):
    """Fixed layout per cell: the pool range is reserved at 2 x pool and each n's replication range at 2 x R_n x n,
    whatever factors another n uses, so a doubled pool is the base pool plus the next `pool` seeds, a doubled R is the
    base rows plus the next R_n rows, and no seed is shared between the pool and any n or between two n's."""
    cov = locked["seeds"]["coverage"]
    start = int(cov["start"]) + int(cell_index) * int(cov["block"])
    pool_n = int(cov["pool"]) * int(pool_factor)
    pool = np.arange(start, start + pool_n, dtype=np.int64)
    nxt = start + 2 * int(cov["pool"]); reps = {}
    wanted = {int(n) for n in (n_list if n_list is not None else cov["n_grid"])}
    for n in cov["n_grid"]:
        R0 = int(cov["replications"][str(n)]); R = R0 * int(rep_factor)
        if int(n) in wanted:
            reps[int(n)] = np.arange(nxt, nxt + R * int(n), dtype=np.int64).reshape(R, int(n))
        nxt += 2 * R0 * int(n)
    if nxt > start + int(cov["block"]):
        raise ValueError(f"coverage block of {cov['block']} seeds is too small for the reserved layout ({nxt - start} seeds)")
    return pool, reps


@dataclass
class CoverageCellSpec:
    name: str
    cfg: dict
    focal: int
    rule: str
    family: str
    params_by_rule: dict
    attack_knobs_by_rule: dict
    ref_candidate: dict | None
    pair: tuple = ("B2", "B3")


def trajectory_keys(spec: CoverageCellSpec) -> list:
    keys = [(spec.rule, "attack"), (spec.rule, "clip")] + ([(spec.rule, "ref")] if spec.ref_candidate is not None else [])
    for p in spec.pair:
        if p != spec.rule:
            keys += [(p, "attack"), (p, "clip")]
    return keys


def runs_per_seed(spec: CoverageCellSpec) -> int:
    return len(trajectory_keys(spec))


def _factory(spec: CoverageCellSpec, rule: str, kind: str, families: dict):
    from .records import candidate_from_record
    fam = families[spec.family]; knobs = spec.attack_knobs_by_rule[rule]
    if kind == "attack":
        return lambda: fam.make(dict(knobs))
    if kind == "clip":
        return lambda: fam.make(fam.project(dict(knobs)))
    return candidate_from_record(fam, spec.ref_candidate).policy_factory


def observe_chunk(spec: CoverageCellSpec, seeds, families: dict) -> dict:
    """Scalars per seed for one chunk: profit of the focal entity, gross efficiency, S*; episode results are dropped."""
    from .registry import make_rule
    seeds = tuple(int(s) for s in seeds); cfg = cfg_from_dict(spec.cfg); N = cfg.N; f = spec.focal; cache = SeedCache()
    scal: dict = {}
    for rule, kind in trajectory_keys(spec):
        cell = Cell(cfg=cfg, rule_factory=(lambda r=rule: make_rule(r, spec.params_by_rule[r])), focal=f, seeds=seeds, name=f"{spec.name}/{rule}/{kind}")
        res = run_focal(cell, _factory(spec, rule, kind, families), cache).results
        scal[(rule, kind)] = {"profit": np.array([r.profit[f] for r in res]), "eff": np.array([(r.W + r.audit_cost) / r.sstar for r in res]),
                              "sstar": np.array([r.sstar for r in res])}
        del res
    own = scal[(spec.rule, "attack")]; scale = own["sstar"] / N
    p_ref = scal[(spec.rule, "ref")]["profit"] if (spec.rule, "ref") in scal else np.zeros_like(own["profit"])
    a, b = spec.pair
    return {"gain": (own["profit"] - p_ref) / scale, "eff": own["eff"],
            "loss_diff": (scal[(a, "clip")]["eff"] - scal[(a, "attack")]["eff"]) - (scal[(b, "clip")]["eff"] - scal[(b, "attack")]["eff"])}


def _chunk_job(args):
    spec, seeds = args
    from .registry import available_families
    return observe_chunk(spec, seeds, available_families())


def observe(spec: CoverageCellSpec, seeds, chunk: int = 500, families: dict | None = None, workers: int = 1) -> dict:
    """Scalar observations in chunks; with workers > 1 the chunks run in a process pool (one cell can use a whole machine)."""
    from concurrent.futures import ProcessPoolExecutor
    from .registry import available_families
    seeds = np.asarray(seeds, dtype=np.int64).ravel(); chunks = [seeds[i:i + chunk] for i in range(0, len(seeds), chunk)]
    if workers > 1 and len(chunks) > 1:
        with ProcessPoolExecutor(int(workers)) as ex:
            parts = list(ex.map(_chunk_job, [(spec, c) for c in chunks]))
    else:
        families = families or available_families(); parts = [observe_chunk(spec, c, families) for c in chunks]
    return {s: np.concatenate([p[s] for p in parts]) if parts else np.zeros(0) for s in STATISTICS}


# ---- scoring ---------------------------------------------------------------------------------------------------------

def reference_interval(obs, level: float):
    obs = np.asarray(obs, dtype=float); lo, hi = t_interval(obs, level)
    return lo, hi, float(obs.std(ddof=1) / np.sqrt(obs.size))


def covered(b: Bound, lo: float, hi: float) -> bool:
    return bool(b.value >= hi) if b.side == "upper" else bool(b.value <= lo)


def measure(samples: dict, refs: dict, n: int, procedures, settings: dict) -> dict:
    out = {}
    for stat in STATISTICS:
        X = np.asarray(samples[stat], dtype=float); lo, hi = refs[stat]
        eps = [(side, lv) for s, side, lv in ENDPOINTS if s == stat]
        for proc in procedures:
            hits = {e: 0 for e in eps}
            for row in X:
                for side, lv in eps:
                    if covered(bound(proc, row, side, lv, settings), lo, hi):
                        hits[(side, lv)] += 1
            for (side, lv), h in hits.items():
                out[f"{endpoint_key(stat, side, lv, n)}|{proc}"] = h / X.shape[0]
    return out


# ---- thresholds, fixture, power --------------------------------------------------------------------------------------

def analytic_conservative_coverage(n: int, critical: float, M: int, ref_level: float = 0.95) -> float:
    """Expected conservative coverage of x_bar + c s / sqrt(n) scored against pool_mean + z sigma / sqrt(M) for normal data
    with known sigma: the pool-mean error and the sample mean combine into one normal, so the statistic is noncentral t
    with df n - 1. The reference interval's t quantile and the pool's sample variance add O(1/M) terms (below 1e-6 at
    M = 35,000); the registered cross-check is `threshold_check` (spec 8)."""
    z = stats.norm.ppf(0.5 + ref_level / 2.0)
    nc = -z * math.sqrt(n / (M + n))
    return float(1.0 - stats.nct.cdf(-critical / math.sqrt(1.0 + n / M), n - 1, nc))


def simulated_conservative_coverage(n: int, level: float, M: int, pools: int, reps: int, rng) -> float:
    crit = stats.t.ppf(level, n - 1); hits = 0; total = 0
    for _ in range(pools):
        pool = rng.normal(size=M); _, hi = t_interval(pool, 0.95)
        X = rng.normal(size=(reps, n)); U = X.mean(axis=1) + crit * X.std(axis=1, ddof=1) / math.sqrt(n)
        hits += int((U >= hi).sum()); total += reps
    return hits / total


def thresholds(locked: dict, M: int) -> dict:
    iv = locked["intervals"]; out = {}
    for n in locked["seeds"]["coverage"]["n_grid"]:
        for lv in LEVELS:
            exact = analytic_conservative_coverage(int(n), float(stats.t.ppf(lv, int(n) - 1)), int(M), float(iv["reference_level"]))
            margin = float(iv["margins"][str(lv)])
            out[f"{n}|{lv}"] = {"n": int(n), "level": lv, "exact": exact, "margin": margin, "threshold": exact - margin / 100.0}
    return out


def _pool_coverages(n: int, level: float, M: int, pools: int, reps: int, rng) -> np.ndarray:
    crit = stats.t.ppf(level, n - 1); out = np.empty(pools)
    for k in range(pools):
        pool = rng.normal(size=M); _, hi = t_interval(pool, 0.95)
        X = rng.normal(size=(reps, n)); U = X.mean(axis=1) + crit * X.std(axis=1, ddof=1) / math.sqrt(n)
        out[k] = float((U >= hi).mean())
    return out


def threshold_check(locked: dict, M: int, pools: int, reps: int, rng) -> dict:
    """The registered cross-check of the analytic threshold: 200 pools of size M, 20,000 replications each (spec 8). The
    replications in one pool share its mean error, so the standard error is the between-pool one: sd(per-pool coverage) / sqrt(pools)."""
    out = {}
    for key, t in thresholds(locked, M).items():
        cov = _pool_coverages(t["n"], t["level"], M, pools, reps, rng); sim = float(cov.mean())
        se = float(cov.std(ddof=1) / math.sqrt(pools)) if pools > 1 else float("inf")
        out[key] = {"analytic": t["exact"], "simulated": sim, "gap": t["exact"] - sim, "se": se, "pools": pools, "reps": reps, "pass_": bool(abs(t["exact"] - sim) <= 3 * se + 1e-4)}
    return out


def clopper_pearson_lower(k: int, n: int, conf: float) -> float:
    return 0.0 if k == 0 else float(stats.beta.ppf(1.0 - conf, k, n - k + 1))


def joint_fixture(locked: dict, n: int, M: int, R: int, thr: dict, trials: int, rng, cells: int = 6) -> dict:
    """One trial: for each cell and each statistic an independent normal pool and (R, n) sample; the sides and levels of
    one statistic share its sample; admitted when all 6 x 8 endpoints are at or above threshold."""
    iv = locked["intervals"]; conf = 1.0 - 0.05 / 3.0; admitted = 0
    crit = {lv: float(stats.t.ppf(lv, n - 1)) for lv in LEVELS}
    for _ in range(trials):
        ok = True
        for _c in range(cells):
            for stat in STATISTICS:
                pool = rng.normal(size=M); lo, hi = t_interval(pool, float(iv["reference_level"]))
                X = rng.normal(size=(R, n)); m = X.mean(axis=1); se = X.std(axis=1, ddof=1) / math.sqrt(n)
                for s, side, lv in ENDPOINTS:
                    if s != stat:
                        continue
                    cov = float(((m + crit[lv] * se) >= hi).mean()) if side == "upper" else float(((m - crit[lv] * se) <= lo).mean())
                    if cov < thr[f"{n}|{lv}"]["threshold"]:
                        ok = False; break
                if not ok:
                    break
            if not ok:
                break
        admitted += int(ok)
    ll = clopper_pearson_lower(admitted, trials, conf)
    return {"n": n, "M": M, "R": R, "trials": trials, "cells": cells, "endpoints_per_cell": len(ENDPOINTS), "admitted": admitted, "conf": conf,
            "lower_limit": ll, "pass_": bool(ll >= 0.9)}


def _tail_fill(p: np.ndarray, nc: np.ndarray) -> np.ndarray:
    """scipy's nct.cdf returns NaN for |nc| above about 9. For p = 1 - cdf(-c; nc): as nc -> +inf (the pool mean far below
    the truth) the cdf -> 0 and the coverage -> 1; as nc -> -inf the coverage -> 0."""
    return np.where(np.isfinite(p), p, (nc > 0).astype(float))


def control_power(n: int, level: float, deficit_points: float, M: int, R: int, threshold: float, nodes: int, ref_level: float = 0.95) -> float:
    """Expected binomial rejection probability of the negative control (a t bound whose true coverage is the nominal level
    minus the deficit), integrated over the pool-mean error with the Gauss-Hermite rule (spec 8, power)."""
    c = float(stats.t.ppf(level - deficit_points / 100.0, n - 1))
    z = stats.norm.ppf(0.5 + ref_level / 2.0); delta = z / math.sqrt(M)
    x, w = roots_hermite(int(nodes))
    eps = math.sqrt(2.0) / math.sqrt(M) * x                       # pool-mean error in units of sigma
    nc = -(eps + delta) * math.sqrt(n)
    p = _tail_fill(1.0 - stats.nct.cdf(-c, n - 1, nc), nc)
    need = int(math.ceil(R * threshold))                         # admitted iff hits >= need; rejected iff hits <= need - 1
    rej = stats.binom.cdf(need - 1, R, p)
    total = float((w * rej).sum() / math.sqrt(math.pi))
    if not (np.all(np.isfinite(x)) and np.all(np.isfinite(w)) and math.isfinite(total)):
        raise FloatingPointError("non-finite quadrature in control_power")
    return total


def power_check(locked: dict, M: int, R_by_n: dict, thr: dict) -> dict:
    iv = locked["intervals"]; out = {}
    for key, t in thr.items():
        n, lv = t["n"], t["level"]
        if int(n) not in R_by_n:
            continue
        d = float(iv["deficits"][str(lv)]); R = int(R_by_n[int(n)])
        p200 = control_power(n, lv, d, M, R, t["threshold"], int(iv["quadrature_nodes"]), float(iv["reference_level"]))
        p400 = control_power(n, lv, d, M, R, t["threshold"], 2 * int(iv["quadrature_nodes"]), float(iv["reference_level"]))
        conv = abs(p200 - p400) <= 0.001
        out[key] = {"deficit": d, "power_200": p200, "power_400": p400, "converged": bool(conv), "pass_": bool(conv and p200 >= 0.8)}
    return out


def fixture_and_power(locked: dict, smoke: bool, rng, n_list) -> dict:
    cov = locked["seeds"]["coverage"]; iv = locked["intervals"]
    base_M = 200 if smoke else int(cov["pool"]); trials = 10 if smoke else int(iv["joint_trials"])
    base_R = {int(n): (20 if smoke else int(cov["replications"][str(n)])) for n in cov["n_grid"]}
    per_n = {}; admissible = {}; remedies = {}; checks = {}
    pools_c, reps_c = (5, 500) if smoke else (int(iv.get("threshold_check_pools", 200)), int(iv.get("threshold_check_reps", 20000)))
    for n in n_list:
        n = int(n); attempts = []
        for pf, rf in ((1, 1), (2, 1), (2, 2)):
            M = base_M * pf; R = base_R[n] * rf; thr = thresholds(locked, M)
            if str(M) not in checks:                                  # the analytic threshold is cross-checked at every M actually used
                checks[str(M)] = threshold_check(locked, M, pools_c, reps_c, rng)
            chk_ok = all(v["pass_"] for k, v in checks[str(M)].items() if v and int(k.split("|")[0]) == n)
            fx = joint_fixture(locked, n, M, R, thr, trials, rng)
            pw = power_check(locked, M, {n: R}, {k: v for k, v in thr.items() if v["n"] == n})
            ok = fx["pass_"] and all(v["pass_"] for v in pw.values()) and chk_ok
            attempts.append({"pool_factor": pf, "rep_factor": rf, "M": M, "R": R, "fixture": fx, "power": pw, "threshold_check_pass": bool(chk_ok), "pass_": bool(ok)})
            if ok:
                break
        per_n[str(n)] = attempts; admissible[str(n)] = bool(attempts[-1]["pass_"])
        remedies[str(n)] = {"pool_factor": attempts[-1]["pool_factor"], "rep_factor": attempts[-1]["rep_factor"], "admissible": admissible[str(n)]}
    return {"per_n": per_n, "admissible_n": admissible, "remedies": remedies, "base_M": base_M, "base_R": {str(k): v for k, v in base_R.items()},
            "threshold_check": checks, "smoke": bool(smoke)}


# ---- admission -------------------------------------------------------------------------------------------------------

def admission(measured: dict, thr_by_n: dict, locked: dict, admissible_n: dict | None = None) -> dict:
    admissible_n = admissible_n or {}
    procedure_admitted = {}
    for n, procs in PROCEDURES_AT_N.items():
        thr = thr_by_n.get(n) or thr_by_n.get(str(n)) or {}
        for proc in procs:
            ok = len(measured) > 0 and admissible_n.get(str(n), False) and bool(thr)      # an n without fixture and power evidence is not admitted
            for cell, cov in measured.items():
                for stat, side, lv in ENDPOINTS:
                    key = f"{endpoint_key(stat, side, lv, n)}|{proc}"
                    if key not in cov or cov[key] < thr[f"{n}|{lv}"]["threshold"]:
                        ok = False
            procedure_admitted[f"{proc}|{n}"] = bool(ok)
    method_at_n = {str(n): next((p for p in procs if procedure_admitted[f"{p}|{n}"]), None) for n, procs in PROCEDURES_AT_N.items()}
    admitted_sides = {endpoint_key(s, side, lv, n): method_at_n[str(n)] for n in PROCEDURES_AT_N for s, side, lv in ENDPOINTS}
    h1 = "confirmatory" if method_at_n["10"] == "t" else "exploratory"
    if method_at_n["20"] == "percentile":
        par, fe = "percentile_n20", 20
    elif method_at_n["20"] == "studentized":
        par, fe = "studentized_n20", 20
    elif method_at_n["40"] == "studentized":
        par, fe = "studentized_n40", 40
    else:
        par, fe = "inconclusive", None
    return {"procedure_admitted": procedure_admitted, "method_at_n": method_at_n, "admitted_sides": admitted_sides,
            "consequences": {"h1": h1, "parametrized": par, "final_eval_n": fe}}


def write_report(path, report: dict) -> str:
    data = json.dumps(report, sort_keys=True, indent=1, default=float).encode()
    Path(path).parent.mkdir(parents=True, exist_ok=True); Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def load_report(path) -> dict:
    return json.loads(Path(path).read_text())
