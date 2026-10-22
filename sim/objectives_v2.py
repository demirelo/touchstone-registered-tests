"""Welfare and coalition objectives of the revision program (design 6.2, 6.3). W0 maximises -E[gross efficiency]; W1 does
the same and records, per evaluated point, the constraint mean E[(pi - pi_ref) / (S*/N)] on the training seeds against a
frozen reference; its selection is feasibility-first and may find no feasible candidate. Coalitions: members play shared
X6-SE/v2 knobs with member schedules, non-members honest-max; member gain g_j = (pi_j - pi_j^0) / (S*/N) against the
frozen joint truthful reference; objectives total = sum_j E[g_j] and min = min_j E[g_j]; the joint twin maximises the
members' total normalised profit with clip forced."""
from __future__ import annotations

import numpy as np

from .cell import Abstain, Cell, SeedCache, run_focal, run_profile
from .policies.families import Family, exact_key
from .policies.honest import HonestMax
from .policies.v2 import x6v2_member
from .search import ArchiveEntry, Objective

JOINT_ORDER = ("honest_max", "abstain", "joint_twin")


def gross_efficiency(results) -> np.ndarray:
    return np.array([(r.W + r.audit_cost) / r.sstar for r in results])


class WelfareObjective(Objective):
    def __init__(self, cell: Cell, family: Family, cache: SeedCache, ref_normalized=None) -> None:
        super().__init__(cell, family, cache)
        self.ref = None if ref_normalized is None else np.asarray(ref_normalized, dtype=float)
        self.extra: dict[tuple, dict] = {}

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        knobs = dict(knobs)
        fr = run_focal(self.cell, lambda: self.family.make(knobs), self.cache)
        eff = gross_efficiency(fr.results); f = -float(eff.mean()); key = exact_key(knobs)
        if key not in self.archive:
            self.archive[key] = ArchiveEntry(knobs=dict(knobs), f=f, per_seed_profit=fr.profit, per_seed_normalized=fr.normalized,
                                             inflated=fr.inflated, source=source)
            self.extra[key] = {"eff": float(eff.mean()), "per_seed_eff": eff.tolist(),
                               "constraint": None if self.ref is None else float((fr.normalized - self.ref).mean())}
        self.log.append({"knobs": dict(knobs), "f": f, "source": source})
        self.evals += 1
        return f


def select_w1(objective) -> dict | None:
    """Among evaluated points with a non-negative training constraint mean, the lowest training efficiency (highest f),
    ties to the earlier point; None reports "no feasible candidate found"."""
    best = None
    for key, e in objective.archive.items():
        c = objective.extra[key]["constraint"]
        if c is not None and c >= 0 and (best is None or e.f > best.f):
            best = e
    return None if best is None else dict(best.knobs)


def coalition_score(member_g, kind: str) -> float:
    means = [float(np.mean(g)) for g in member_g]
    if kind == "total":
        return float(sum(means))
    if kind == "min":
        return float(min(means))
    raise ValueError(kind)


def pick_joint(scores: list[tuple[str, float]]) -> str:
    best = None
    for name, s in scores:
        if best is None or s > best[1]:
            best = (name, s)
    return best[0]


def _member_rows(cfg, rule_factory, members, seeds, cache, member_factories) -> np.ndarray:
    fs = [HonestMax for _ in range(cfg.N)]
    for e, f in zip(members, member_factories):
        fs[int(e)] = f
    res = run_profile(cfg, rule_factory, fs, seeds, cache)
    return np.array([[float(r.profit[e] / (r.sstar / cfg.N)) for r in res] for e in members])


class CoalitionObjective(Objective):
    def __init__(self, cfg, rule_factory, members, family: Family, seeds, cache: SeedCache, kind: str, joint_ref=None,
                 staggered: bool = False, T: int = 200, L: int = 10) -> None:
        if kind not in ("total", "min", "joint_twin"):
            raise ValueError(kind)
        if kind != "joint_twin" and joint_ref is None:
            raise ValueError("total and min need the frozen joint reference")
        cell = Cell(cfg=cfg, rule_factory=rule_factory, focal=int(members[0]), seeds=tuple(seeds), name="coalition")
        super().__init__(cell, family, cache, force_clip=(kind == "joint_twin"))
        self.members, self.kind, self.staggered, self.T, self.L = tuple(int(m) for m in members), kind, bool(staggered), int(T), int(L)
        self.ref = None if joint_ref is None else np.asarray(joint_ref, dtype=float)
        self.extra: dict[tuple, dict] = {}

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        knobs = self.family.project(knobs) if self.force_clip else dict(knobs)
        c = len(self.members)
        facs = [lambda j=j: x6v2_member(knobs, j, c, self.staggered, self.T, self.L) for j in range(c)]
        rows = _member_rows(self.cell.cfg, self.cell.rule_factory, self.members, self.cell.seeds, self.cache, facs)
        if self.kind == "joint_twin":
            f = float(rows.sum(axis=0).mean()); g = rows
        else:
            g = rows - self.ref; f = coalition_score(list(g), self.kind)
        key = exact_key(knobs)
        if key not in self.archive:
            self.archive[key] = ArchiveEntry(knobs=dict(knobs), f=f, per_seed_profit=rows[0], per_seed_normalized=rows[0], inflated=False, source=source)
            self.extra[key] = {"member_means": [float(v) for v in g.mean(axis=1)], "total": float(g.mean(axis=1).sum()),
                               "min": float(g.mean(axis=1).min()), "member_rows": rows.tolist()}
        self.log.append({"knobs": dict(knobs), "f": f, "source": source})
        self.evals += 1
        return f


def joint_reference(cfg, rule_factory, members, seeds, cache: SeedCache, twin_knobs: dict, staggered: bool, T: int, L: int) -> dict:
    """The frozen joint truthful reference (design 6.3): the candidate with the highest training mean of the members'
    total normalised profit among all honest-max, all abstain, and all playing the projected joint twin, in that tie order."""
    c = len(members); tw = dict(twin_knobs); tw["clip"] = 1
    cands = {"honest_max": [HonestMax] * c, "abstain": [Abstain] * c,
             "joint_twin": [lambda j=j: x6v2_member(tw, j, c, staggered, T, L) for j in range(c)]}
    rows = {n: _member_rows(cfg, rule_factory, members, seeds, cache, cands[n]) for n in JOINT_ORDER}
    name = pick_joint([(n, float(rows[n].sum(axis=0).mean())) for n in JOINT_ORDER])
    return {"name": name, "scores": {n: float(rows[n].sum(axis=0).mean()) for n in JOINT_ORDER}, "member_normalized": rows[name], "twin_knobs": tw}
