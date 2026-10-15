from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import cma
import numpy as np

from .cell import Cell, SeedCache, run_focal
from .policies.families import Family, exact_key


@dataclass(frozen=True)
class SearchSettings:
    popsize: int
    sigma0: float
    restarts: int
    evals_per_restart: int
    reeval_every: int
    near_corner: float
    sobol_seed: int


def settings_from_locked(locked: dict) -> SearchSettings:
    s = locked["search"]
    return SearchSettings(popsize=int(s["popsize"]), sigma0=float(s["sigma0"]), restarts=int(s["restarts"]),
                          evals_per_restart=int(s["evals_per_restart"]), reeval_every=int(s["reeval_every"]),
                          near_corner=float(s["near_corner"]), sobol_seed=int(s["sobol_seed"]))


@dataclass
class ArchiveEntry:
    knobs: dict
    f: float
    per_seed_profit: np.ndarray
    per_seed_normalized: np.ndarray
    inflated: bool
    source: str


class Objective:
    """Mean over the cell's seeds of per-seed normalized profit pi / (S* / N).
    The reference is subtracted after reference selection, never here. Every
    evaluated point goes to the archive with its per-seed values and whether
    the focal provider ever claimed above its effort (spec 5.2)."""

    def __init__(self, cell: Cell, family: Family, cache: SeedCache, force_clip: bool = False) -> None:
        self.cell, self.family, self.cache, self.force_clip = cell, family, cache, force_clip
        self.archive: dict[tuple, ArchiveEntry] = {}
        self.evals = 0

    def knobs_of(self, x: np.ndarray) -> dict:
        k = self.family.transform(x)
        return self.family.project(k) if self.force_clip else k

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        knobs = self.family.project(knobs) if self.force_clip else dict(knobs)
        fr = run_focal(self.cell, lambda: self.family.make(knobs), self.cache)
        f = float(fr.normalized.mean())
        key = exact_key(knobs)
        if key not in self.archive:
            self.archive[key] = ArchiveEntry(knobs=dict(knobs), f=f, per_seed_profit=fr.profit, per_seed_normalized=fr.normalized,
                                             inflated=fr.inflated, source=source)
        self.evals += 1
        return f

    def __call__(self, x: np.ndarray) -> float:
        return self.eval_knobs(self.knobs_of(x))


def best_archived(archive: dict, clip: int, truthful_only: bool = False) -> ArchiveEntry | None:
    best = None
    for e in archive.values():
        if e.knobs["clip"] != clip or (truthful_only and e.inflated):
            continue
        if best is None or e.f > best.f:
            best = e
    return best


@dataclass
class SearchResult:
    best_x: np.ndarray
    best_knobs: dict
    best_f: float
    best_source: str
    restart_bests: list
    evals: int
    trace: list
    incumbent_scores: dict
    projection_f: float
    replaced_by_projection: bool
    archive: dict = field(default_factory=dict)


def cma_search(objective, family: Family, settings: SearchSettings, seed: int,
               incumbents: dict[str, dict] | None = None, starts: list | None = None) -> SearchResult:
    """CMA-ES maximization with registered restarts and a fixed evaluation budget
    per restart (incumbent re-evaluations count). Registered incumbents and the
    projection of the best point are evaluated exactly, outside the budget."""
    if starts is None:
        starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed})
    best_x, best_knobs, best_f, best_source = None, None, -np.inf, ""
    restart_bests, trace, evals = [], [], 0
    for r in range(settings.restarts):
        x0 = starts[r % len(starts)]
        es = cma.CMAEvolutionStrategy(x0, settings.sigma0,
                                      {"popsize": settings.popsize, "seed": int(seed) + 1 + r, "verbose": -9, "verb_log": 0})
        used, it = 0, 0
        r_best_x, r_best_f = x0.copy(), objective(x0)
        used += 1; evals += 1
        while used < settings.evals_per_restart:
            X = es.ask()
            n = min(len(X), settings.evals_per_restart - used)
            X = X[:n]
            F = [objective(np.asarray(x)) for x in X]
            used += n; evals += n
            if n == settings.popsize:
                es.tell(X, [-f for f in F])
            for x, f in zip(X, F):
                if f > r_best_f:
                    r_best_x, r_best_f = np.asarray(x).copy(), f
            it += 1
            if it % settings.reeval_every == 0 and used < settings.evals_per_restart:
                f_re = objective(r_best_x)
                used += 1; evals += 1
                r_best_f = min(r_best_f, f_re)   # a deterministic objective returns the same value
            trace.append((evals, r_best_f))
        restart_bests.append(r_best_f)
        if r_best_f > best_f:
            best_x, best_knobs, best_f, best_source = r_best_x.copy(), objective.knobs_of(r_best_x), r_best_f, f"restart_{r}"
    incumbent_scores: dict[str, float] = {}
    for name, k in (incumbents or {}).items():
        f = objective.eval_knobs(k, source=f"incumbent:{name}")
        incumbent_scores[name] = float(f)
        if f > best_f:
            best_x, best_knobs, best_f, best_source = family.inverse(k, settings.near_corner), dict(k), float(f), f"incumbent:{name}"
    proj = family.project(best_knobs)
    projection_f = float(objective.eval_knobs(proj, source="projection"))
    replaced = projection_f > best_f
    if replaced:
        best_x, best_knobs, best_f, best_source = family.inverse(proj, settings.near_corner), proj, projection_f, "projection"
    return SearchResult(best_x=best_x, best_knobs=best_knobs, best_f=float(best_f), best_source=best_source,
                        restart_bests=restart_bests, evals=evals, trace=trace, incumbent_scores=incumbent_scores,
                        projection_f=projection_f, replaced_by_projection=replaced, archive=objective.archive)


def corner_controls(objective, family: Family) -> list[tuple[dict, float]]:
    """Exact corners (knobs at 0 or 1), one evaluation each, outside the search budget (spec 5.3)."""
    return [(k, float(objective.eval_knobs(k, source="corner"))) for k in family.corners()]
