"""Amendment 1 to the lock of 2026-10-17: the paired H3 statistic gain_diff, its fresh seed layout with remedy factors, its
12-endpoint gate at n = 40 (6 cells x 2 sides), its strict admission, and the canonical hash of the amendment file.
Nothing here edits experiments/locked.yaml or any registered artifact (consensus of Sol high and Astra high, 2026-10-17)."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from .cell import Cell, SeedCache, run_focal
from .coverage import (LEVELS, covered, endpoint_key, joint_fixture, power_check, reference_interval, threshold_check, thresholds)
from .intervals import bound
from .records import cfg_from_dict

AMEND_STATISTICS = ("gain_diff",)
AMEND_ENDPOINTS = (("gain_diff", "lower", 0.9875), ("gain_diff", "upper", 0.9875))
AMEND_N = 40
AMEND_PROCEDURES = ("studentized",)
AMEND_LEVEL = 0.9875
LIMITATION = ("Proxy admission on development distributions with B3 standing in for R*; this is not nominal coverage for "
              "comparisons involving the selected R*.")
REGISTRATION_FIELDS = ("coverage_report_amendment_sha256", "coverage_consequences")
FINAL_EVAL_RANGE = (10_000_000, 20_000_000)
CELLS = 6


# ---- the amendment file ------------------------------------------------------------------------------------------------

def _registered_ranges(locked: dict) -> list:
    """Every seed range the lock already uses: the listed namespaces, the base coverage block, and the final-eval range."""
    seeds = locked.get("seeds", {}); ranges = []
    for key in ("dev_train", "dev_val", "calibration"):
        vals = seeds.get(key)
        if isinstance(vals, list) and vals:
            ranges.append((key, int(min(vals)), int(max(vals)) + 1))
    cov = seeds.get("coverage")
    if isinstance(cov, dict):
        start = int(cov["start"]); ranges.append(("coverage", start, start + CELLS * int(cov["block"])))
    ranges.append(("final_eval", *FINAL_EVAL_RANGE))
    return ranges


def load_amendment(path, locked: dict) -> dict:
    """The amendment document; refuses a seed block that overlaps a registered range or is too small for both remedies."""
    doc = yaml.safe_load(Path(path).read_text()) or {}
    se = doc.get("seeds_ext") or {}
    start, block, pool = int(se["start"]), int(se["block"]), int(se["pool"]); R = int(se["replications"][str(AMEND_N)])
    need = 2 * pool + 2 * R * AMEND_N
    if block < need:
        raise ValueError(f"seeds_ext block {block} is smaller than the reserved layout of {need} seeds (2 x pool + 2 x R x n)")
    lo, hi = start, start + CELLS * block
    for name, a, b in _registered_ranges(locked):
        if lo < b and a < hi:
            raise ValueError(f"seeds_ext [{lo}, {hi}) overlaps the registered {name} range [{a}, {b})")
    return doc


def amendment_hash(doc: dict) -> str:
    """Canonical hash: the document with the registration fields set to null, so the hash is the same before and after
    scripts/amend.py records the extension report."""
    bound_doc = {**doc, **{k: None for k in REGISTRATION_FIELDS}}
    return hashlib.sha256(json.dumps(bound_doc, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


# ---- seeds -----------------------------------------------------------------------------------------------------------

def seed_blocks_ext(amend: dict, cell_index: int, pool_factor: int = 1, rep_factor: int = 1):
    """Fixed layout per cell: the pool range is reserved at 2 x pool (positions 0 to 2 pool - 1) and the n = 40 replication
    range at 2 x R x 40 after it, so a doubled pool or a doubled R extends the base seeds and never moves them."""
    se = amend["seeds_ext"]; start = int(se["start"]) + int(cell_index) * int(se["block"])
    pool_n = int(se["pool"]); R0 = int(se["replications"][str(AMEND_N)])
    pool = np.arange(start, start + pool_n * int(pool_factor), dtype=np.int64)
    rs = start + 2 * pool_n; R = R0 * int(rep_factor)
    reps = np.arange(rs, rs + R * AMEND_N, dtype=np.int64).reshape(R, AMEND_N)
    if rs + 2 * R0 * AMEND_N > start + int(se["block"]):
        raise ValueError("seeds_ext block is too small for the reserved layout")
    return pool, reps


# ---- observations -------------------------------------------------------------------------------------------------------

@dataclass
class CoverageExtSpec:
    name: str
    cfg: dict
    focal: int
    family: str
    params_by_rule: dict
    attack_knobs_by_rule: dict
    ref_candidate_by_rule: dict
    pair: tuple = ("B2", "B3")


def trajectory_keys_ext(spec: CoverageExtSpec) -> list:
    keys = []
    for rule in spec.pair:
        keys.append((rule, "attack"))
        if spec.ref_candidate_by_rule.get(rule) is not None:
            keys.append((rule, "ref"))
    return keys


def runs_per_seed_ext(spec: CoverageExtSpec) -> int:
    return len(trajectory_keys_ext(spec))


def _factory_ext(spec: CoverageExtSpec, rule: str, kind: str, families: dict):
    from .records import candidate_from_record
    fam = families[spec.family]
    if kind == "attack":
        knobs = spec.attack_knobs_by_rule[rule]
        return lambda: fam.make(dict(knobs))
    return candidate_from_record(fam, spec.ref_candidate_by_rule[rule]).policy_factory


def observe_chunk_ext(spec: CoverageExtSpec, seeds, families: dict) -> dict:
    """Per seed: [(pi_B2,attack - pi_B2,ref) - (pi_B3,attack - pi_B3,ref)] / (S* / N), with reference profit 0 for a rule
    whose selected reference is abstain (no ref key)."""
    from .registry import make_rule
    seeds = tuple(int(s) for s in seeds); cfg = cfg_from_dict(spec.cfg); N = cfg.N; f = spec.focal; cache = SeedCache()
    prof: dict = {}; sstar = None
    for rule, kind in trajectory_keys_ext(spec):
        cell = Cell(cfg=cfg, rule_factory=(lambda r=rule: make_rule(r, spec.params_by_rule[r])), focal=f, seeds=seeds, name=f"{spec.name}/{rule}/{kind}")
        res = run_focal(cell, _factory_ext(spec, rule, kind, families), cache).results
        prof[(rule, kind)] = np.array([r.profit[f] for r in res])
        if sstar is None:
            sstar = np.array([r.sstar for r in res])
        del res
    a, b = spec.pair; zero = np.zeros(len(seeds))
    ga = prof[(a, "attack")] - prof.get((a, "ref"), zero); gb = prof[(b, "attack")] - prof.get((b, "ref"), zero)
    return {"gain_diff": (ga - gb) / (sstar / N)}


def _chunk_job_ext(args):
    spec, seeds = args
    from .registry import available_families
    return observe_chunk_ext(spec, seeds, available_families())


def observe_ext(spec: CoverageExtSpec, seeds, chunk: int = 500, families: dict | None = None, workers: int = 1) -> dict:
    from concurrent.futures import ProcessPoolExecutor
    from .registry import available_families
    seeds = np.asarray(seeds, dtype=np.int64).ravel(); chunks = [seeds[i:i + chunk] for i in range(0, len(seeds), chunk)]
    if workers > 1 and len(chunks) > 1:
        with ProcessPoolExecutor(int(workers)) as ex:
            parts = list(ex.map(_chunk_job_ext, [(spec, c) for c in chunks]))
    else:
        families = families or available_families(); parts = [observe_chunk_ext(spec, c, families) for c in chunks]
    return {s: np.concatenate([p[s] for p in parts]) if parts else np.zeros(0) for s in AMEND_STATISTICS}


# ---- scoring -----------------------------------------------------------------------------------------------------------

def measure_ext(samples: dict, refs: dict, n: int, settings: dict) -> dict:
    out = {}
    for stat in AMEND_STATISTICS:
        X = np.asarray(samples[stat], dtype=float); lo, hi = refs[stat]
        eps = [(side, lv) for s, side, lv in AMEND_ENDPOINTS if s == stat]
        for proc in AMEND_PROCEDURES:
            hits = {e: 0 for e in eps}
            for row in X:
                for side, lv in eps:
                    if covered(bound(proc, row, side, lv, settings), lo, hi):
                        hits[(side, lv)] += 1
            for (side, lv), h in hits.items():
                out[f"{endpoint_key(stat, side, lv, n)}|{proc}"] = h / X.shape[0]
    return out


# ---- gate ----------------------------------------------------------------------------------------------------------------

def fixture_and_power_ext(locked: dict, amend: dict, smoke: bool, rng) -> dict:
    """The gate for the 12 extension endpoints at n = 40 only: thresholds, the registered threshold check at every M used,
    the joint fixture over 6 cells x 2 endpoints, and the power check at 40|0.9875, in the remedy order (1,1), (2,1), (2,2)."""
    se = amend["seeds_ext"]; iv = locked["intervals"]; n = AMEND_N
    base_M = 200 if smoke else int(se["pool"]); trials = 10 if smoke else int(iv["joint_trials"])
    base_R = 20 if smoke else int(se["replications"][str(n)])
    pools_c, reps_c = (5, 500) if smoke else (int(iv.get("threshold_check_pools", 200)), int(iv.get("threshold_check_reps", 20000)))
    key = f"{n}|{AMEND_LEVEL}"; checks = {}; attempts = []
    for pf, rf in ((1, 1), (2, 1), (2, 2)):
        M = base_M * pf; R = base_R * rf; thr_all = thresholds(locked, M); thr = {key: thr_all[key]}
        if str(M) not in checks:
            full = threshold_check(locked, M, pools_c, reps_c, rng); checks[str(M)] = {key: full[key]}
        chk_ok = bool(checks[str(M)][key]["pass_"])
        fx = joint_fixture(locked, n, M, R, thr_all, trials, rng, cells=CELLS, statistics=AMEND_STATISTICS, endpoints=AMEND_ENDPOINTS)
        pw = power_check(locked, M, {n: R}, thr)
        ok = fx["pass_"] and all(v["pass_"] for v in pw.values()) and chk_ok
        attempts.append({"pool_factor": pf, "rep_factor": rf, "M": M, "R": R, "fixture": fx, "power": pw, "threshold_check_pass": chk_ok, "pass_": bool(ok)})
        if ok:
            break
    last = attempts[-1]
    return {"per_n": {str(n): attempts}, "admissible_n": {str(n): bool(last["pass_"])},
            "remedies": {str(n): {"pool_factor": last["pool_factor"], "rep_factor": last["rep_factor"], "admissible": bool(last["pass_"])}},
            "base_M": base_M, "base_R": {str(n): base_R}, "threshold_check": checks, "smoke": bool(smoke)}


# ---- admission -------------------------------------------------------------------------------------------------------------

def admission_ext(measured: dict, thr_by_n: dict, locked: dict, admissible_n: dict, selection_names: list) -> dict:
    """Strict: exactly the six registered cells, both endpoint measurements finite in [0, 1] and at or above the threshold,
    and the gate admissible at n = 40; otherwise the H3 comparative clause is exploratory."""
    n = AMEND_N; thr = thr_by_n.get(n) or thr_by_n.get(str(n)) or {}
    names = list(selection_names or [])
    ok = len(names) == CELLS and len(set(names)) == CELLS and set(measured) == set(names) and bool((admissible_n or {}).get(str(n), False)) and bool(thr)
    for proc in AMEND_PROCEDURES:
        for cell in names:
            cov = measured.get(cell) or {}
            for stat, side, lv in AMEND_ENDPOINTS:
                v = cov.get(f"{endpoint_key(stat, side, lv, n)}|{proc}")
                t = (thr.get(f"{n}|{lv}") or {}).get("threshold")
                if not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or not (0.0 <= v <= 1.0) or t is None or v < t:
                    ok = False
    procedure_admitted = {f"{p}|{n}": bool(ok) for p in AMEND_PROCEDURES}
    method = AMEND_PROCEDURES[0] if ok else None
    admitted_sides = {endpoint_key(s, side, lv, n): method for s, side, lv in AMEND_ENDPOINTS}
    return {"procedure_admitted": procedure_admitted, "method_at_n": {str(n): method}, "admitted_sides": admitted_sides,
            "consequences": {"h3_comparative": "confirmatory" if ok else "exploratory"}}
