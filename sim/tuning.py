from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import product

import numpy as np

from .cell import Cell, SeedCache
from .config import MarketConfig
from .locked import seeds as locked_seeds
from .mechanisms.posted import PostedPrices
from .mechanisms.posted_audit import PostedRandomAudit
from .mechanisms.second_score import SecondScore
from .policies.families import D2, Family
from .positions import positions
from .reference import attack_search, evaluate_gain, reference_candidates, select_reference, twin_search
from .search import SearchSettings, settings_from_locked


def price_grid(cfg: MarketConfig, f_values) -> list[tuple[float, float, float]]:
    c_min = float(cfg.cost_full.min()); p_top = 0.9 * cfg.q90
    p3s = np.geomspace(c_min, p_top, 3)
    out = []
    for p3 in p3s:
        for f2 in f_values:
            for f1 in f_values:
                p2 = f2 * p3; p1 = f1 * p2
                out.append((float(p1), float(p2), float(p3)))
    return out


def tuning_grid(rule_name: str, cfg: MarketConfig, locked: dict) -> list[dict]:
    tg = locked["tuning"]
    prices = price_grid(cfg, tg["price_f"])
    if rule_name == "B1":
        return [{"P1": a, "P2": b, "P3": c} for a, b, c in prices]
    if rule_name == "B2":
        return [{"P1": a, "P2": b, "P3": c, "tol": float(t), "L": int(L)}
                for (a, b, c), t, L in product(prices, tg["tol"], tg["L"])]
    if rule_name == "B3":
        return [{"tol": float(t), "L": int(L)} for t, L in product(tg["tol"], tg["L"])]
    raise ValueError(rule_name)


def rule_from_params(rule_name: str, params: dict):
    if rule_name == "B1":
        return PostedPrices(params["P1"], params["P2"], params["P3"])
    if rule_name == "B2":
        return PostedRandomAudit(params["P1"], params["P2"], params["P3"], tol=params["tol"], L=params["L"])
    if rule_name == "B3":
        return SecondScore(tol=params["tol"], L=params["L"])
    raise ValueError(rule_name)


@dataclass
class TuningScore:
    eff: float
    gain: float
    margin: float
    namespace: str


def _margin(eff: float, gain: float) -> float:
    return min((eff - 0.90) / 0.90, (0.30 - gain) / 0.30)


def _settings_and_seeds(locked: dict, override: dict | None, recheck: bool) -> tuple[SearchSettings, list[int], list[int] | None]:
    tg = dict(locked["tuning"]); tg.update(override or {})
    base = settings_from_locked(locked)
    tr = locked_seeds(locked, "dev_train")
    if recheck:
        evals = int(tg.get("recheck_evals", base.evals_per_restart)); restarts = int(tg.get("recheck_restarts", base.restarts))
        val = locked_seeds(locked, tg["recheck_namespace"])[: int(tg.get("recheck_val_seeds", 10**9))]
        return replace(base, evals_per_restart=evals, restarts=restarts), tr, val
    return replace(base, restarts=int(tg["inner_restarts"]), evals_per_restart=int(tg["inner_evals"])), tr[: int(tg["inner_seeds"])], None


def score_point(rule_name: str, params: dict, cfg: MarketConfig, locked: dict, cache: SeedCache,
                family: Family = D2, inner_override: dict | None = None, recheck: bool = False) -> TuningScore:
    """Inner scoring is in-sample on the inner dev-train seeds (spec 4.2); the recheck searches on all dev-train
    seeds at the full budget and scores on the recheck namespace (dev-val, spec 6)."""
    settings, train, val = _settings_and_seeds(locked, inner_override, recheck)
    focal = positions(cfg)["median"]
    cell = Cell(cfg=cfg, rule_factory=lambda: rule_from_params(rule_name, params), focal=focal, seeds=tuple(train), name=f"tune/{rule_name}")
    tw = twin_search(cell, family, cache, settings, seed=0)
    at = attack_search(cell, family, cache, settings, seed=1, twin=tw)
    ref = select_reference(cell, reference_candidates(cell, family, at, tw, [], tuple(locked["reference_order"])), cache)
    score_cell = cell if val is None else Cell(cfg=cfg, rule_factory=cell.rule_factory, focal=focal, seeds=tuple(val), name=cell.name + "/val")
    g = evaluate_gain(score_cell, family, at.best_knobs, ref.candidate, cache)
    eff, gain = float(g.eff_attack.mean()), float(g.gain.mean())
    return TuningScore(eff=eff, gain=gain, margin=_margin(eff, gain), namespace="dev_train" if val is None else str(locked["tuning"]["recheck_namespace"]))


@dataclass
class TuningResult:
    best_params: dict
    scores: list
    rechecked: list


def tune(rule_name: str, cfg: MarketConfig, locked: dict, cache: SeedCache, inner_override: dict | None = None,
         grid_limit: int | None = None) -> TuningResult:
    grid = tuning_grid(rule_name, cfg, locked)
    if grid_limit is not None:
        grid = grid[:grid_limit]
    scores = []
    for params in grid:
        sc = score_point(rule_name, params, cfg, locked, cache, inner_override=inner_override)
        scores.append({"params": params, "eff": sc.eff, "gain": sc.gain, "margin": sc.margin, "namespace": sc.namespace})
    scores.sort(key=lambda s: -s["margin"])
    top = int((inner_override or {}).get("recheck_top", locked["tuning"]["recheck_top"]))
    rechecked = []
    for s in scores[:top]:
        sc = score_point(rule_name, s["params"], cfg, locked, cache, inner_override=inner_override, recheck=True)
        rechecked.append({"params": s["params"], "eff": sc.eff, "gain": sc.gain, "margin": sc.margin, "namespace": sc.namespace})
    rechecked.sort(key=lambda s: -s["margin"])
    return TuningResult(best_params=rechecked[0]["params"], scores=scores, rechecked=rechecked)
