from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .cell import Cell, SeedCache
from .policies.families import Family
from .reference import reference_candidates, select_reference
from .search import Objective, SearchResult, SearchSettings, cma_search


def restart_spread(attack: SearchResult, twin: SearchResult) -> dict:
    """Check (c): attack and reference objectives per restart, reported separately, and their difference
    (restart r of the attack paired with restart r of the twin search: the registered convention)."""
    a, r = list(attack.restart_bests), list(twin.restart_bests)
    g = [x - y for x, y in zip(a, r)]
    return {"attack_bests": a, "reference_bests": r, "gain_bests": g,
            "attack_spread": float(max(a) - min(a)), "reference_spread": float(max(r) - min(r)), "gain_spread": float(max(g) - min(g))}


class FixedClipObjective:
    """The wrapped objective with the clip coordinate fixed; exact-knob evaluations keep their own clip."""

    def __init__(self, objective: Objective, clip: int) -> None:
        self.inner, self.clip = objective, int(clip)
        self.family = objective.family

    @property
    def archive(self):
        return self.inner.archive

    @property
    def evals(self):
        return self.inner.evals

    def knobs_of(self, x: np.ndarray) -> dict:
        k = self.inner.knobs_of(x); k["clip"] = self.clip
        return k

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        return self.inner.eval_knobs(knobs, source)

    def __call__(self, x: np.ndarray) -> float:
        return self.eval_knobs(self.knobs_of(x))


@dataclass
class DoublingCheck:
    attack_base_f: float
    attack_doubled_f: float
    clip0_f: float
    clip1_f: float
    clip0_search_f: float
    clip1_search_f: float
    ref_base_f: float
    ref_doubled_f: float
    ref_base_name: str
    ref_doubled_name: str
    gain_base: float
    gain_doubled: float
    delta_gain: float
    passed: bool


def doubling_check(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int,
                   base_attack: SearchResult, base_twin: SearchResult, bank_members: list[dict], order) -> DoublingCheck:
    """Check (b): the extra budget (equal to the base search) is split between a clip = 0 and a clip = 1 search;
    the reference is re-selected from the merged archive; the change in finalized dev-train gain must be under 0.5 points."""
    half = replace(settings, evals_per_restart=max(1, settings.evals_per_restart // 2))
    c0 = cma_search(FixedClipObjective(Objective(cell, family, cache), 0), family, half, seed + 100)
    c1 = cma_search(FixedClipObjective(Objective(cell, family, cache), 1), family, half, seed + 200)
    doubled = max((base_attack, c0, c1), key=lambda r: r.best_f)
    merged = replace(doubled, archive={**base_attack.archive, **c0.archive, **c1.archive})
    ref_base = select_reference(cell, reference_candidates(cell, family, base_attack, base_twin, bank_members, order), cache)
    ref_doubled = select_reference(cell, reference_candidates(cell, family, merged, base_twin, bank_members, order), cache)
    rb, rd = ref_base.scores[ref_base.candidate.name], ref_doubled.scores[ref_doubled.candidate.name]
    gain_base = base_attack.best_f - rb; gain_doubled = merged.best_f - rd
    delta = gain_doubled - gain_base
    return DoublingCheck(attack_base_f=base_attack.best_f, attack_doubled_f=merged.best_f, clip0_f=c0.best_f, clip1_f=c1.best_f,
                         clip0_search_f=float(max(c0.restart_bests)), clip1_search_f=float(max(c1.restart_bests)), ref_base_f=rb, ref_doubled_f=rd, ref_base_name=ref_base.candidate.name, ref_doubled_name=ref_doubled.candidate.name,
                         gain_base=gain_base, gain_doubled=gain_doubled, delta_gain=delta, passed=bool(abs(delta) < 0.005))


@dataclass
class TwinCheck:
    twin_f: float
    honest_f: float
    passed: bool


def twin_vs_honest(twin: SearchResult, honest_f: float) -> TwinCheck:
    """Check (d): the twin's objective is never below honest-max's by more than 1% (relative)."""
    return TwinCheck(twin_f=float(twin.best_f), honest_f=float(honest_f), passed=bool(twin.best_f >= honest_f - 0.01 * abs(honest_f)))
