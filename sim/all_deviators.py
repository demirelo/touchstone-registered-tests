from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .cell import Cell, SeedCache, run_profile
from .policies.families import Family
from .search import Objective, SearchSettings, cma_search


@dataclass
class AllDeviatorsResult:
    profiles: list
    values: list
    final_profile: list
    final_gross_eff: float
    final_normalized_profit: list
    eval_seeds: tuple


def iterated_best_response(cfg, rule_factory, family: Family, cache: SeedCache, settings: SearchSettings, seeds,
                           sweeps: int, seed: int = 0, force_clip: bool = False, eval_seeds=None) -> AllDeviatorsResult:
    """Spec 5.3 all-deviators table: iterated best response, every provider on `family`;
    with force_clip the matched truthful (twin) procedure. The frozen final profile is
    evaluated on eval_seeds (dev-val in the sweep)."""
    N = cfg.N
    profile: list[dict] = [family.honest_point() for _ in range(N)]
    profiles, values = [], []
    for s in range(sweeps):
        row = []
        for i in range(N):
            others = tuple((j, (lambda k=profile[j]: family.make(k))) for j in range(N) if j != i)
            cell = Cell(cfg=cfg, rule_factory=rule_factory, focal=i, seeds=tuple(seeds), name=f"all_deviators/{i}", others=others)
            obj = Objective(cell, family, cache, force_clip=force_clip)
            current = obj.eval_knobs(profile[i], source="current")
            starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed}, twin=force_clip)
            res = cma_search(obj, family, settings, seed=seed + s * N + i, starts=starts)
            if res.best_f > current:
                profile[i] = dict(res.best_knobs); row.append(float(res.best_f))
            else:
                row.append(float(current))
        profiles.append([dict(k) for k in profile]); values.append(row)
    ev = tuple(seeds) if eval_seeds is None else tuple(eval_seeds)
    results = run_profile(cfg, rule_factory, [(lambda k=k: family.make(k)) for k in profile], ev, cache)
    eff = float(np.mean([(r.W + r.audit_cost) / r.sstar for r in results]))
    norm = [float(np.mean([r.profit[i] / (r.sstar / N) for r in results])) for i in range(N)]
    return AllDeviatorsResult(profiles=profiles, values=values, final_profile=[dict(k) for k in profile],
                              final_gross_eff=eff, final_normalized_profit=norm, eval_seeds=ev)
