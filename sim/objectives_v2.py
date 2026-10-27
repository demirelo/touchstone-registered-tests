"""Welfare and coalition objectives of the revision program (design 6.2, 6.3). W0 maximises -E[gross efficiency]; W1 does
the same and records, per evaluated point, the constraint mean E[(pi - pi_ref) / (S*/N)] on the training seeds against a
frozen reference; its selection is feasibility-first and may find no feasible candidate. Coalitions: members play shared
X6-SE/v2 knobs with member schedules, non-members honest-max; member gain g_j = (pi_j - pi_j^0) / (S*/N) against the
frozen joint truthful reference; objectives total = sum_j E[g_j] and min = min_j E[g_j]; the joint twin maximises the
members' total normalised profit with clip forced. Design draft 7 adds X8-DB (decoy and beneficiary, c = 2): members are
built per episode through `member_factories`, and every stored coalition profile is a `ProfileDescriptor` that
`profile_factories` rebuilds after the records are read back."""
from __future__ import annotations

import numpy as np

from .cell import Abstain, Cell, SeedCache, run_focal, run_profile
from .policies.families import Family, exact_key
from .policies.honest import HonestMax
from .policies.v2 import x6v2_member
from .policies.x8 import x8_members
from .search import ArchiveEntry, Objective

JOINT_ORDER = ("honest_max", "abstain", "joint_twin")
COALITION_FAMILIES = ("X6-SE/v2", "X8-DB")


class _PairSource:
    """Binds the two X8-DB member factories of one episode to one coordinator, in whichever order they are called."""

    def __init__(self, knobs: dict, T: int, L: int) -> None:
        self.knobs, self.T, self.L = dict(knobs), int(T), int(L); self.pending: dict | None = None

    def make(self, role: str):
        if self.pending is None or role not in self.pending:
            ben, dec = x8_members(self.knobs, self.T, self.L)
            self.pending = {"beneficiary": ben, "decoy": dec}
        m = self.pending.pop(role)
        if not self.pending:
            self.pending = None
        return m


def member_factories(family_name: str, knobs: dict, members, staggered: bool | None, T: int, L: int) -> list:
    """Per-member policy factories of a coalition profile (design 6.3): X6-SE/v2 shared knobs with member schedules, or
    X8-DB with member 0 the beneficiary and member 1 the decoy."""
    c = len(members); k = dict(knobs)
    if family_name == "X6-SE/v2":
        return [lambda j=j: x6v2_member(k, j, c, bool(staggered), T, L) for j in range(c)]
    if family_name == "X8-DB":
        if c != 2:
            raise ValueError("X8-DB needs exactly two members")
        src = _PairSource(k, T, L)
        return [lambda: src.make("beneficiary"), lambda: src.make("decoy")]
    raise ValueError(f"unknown coalition family {family_name!r}")


def profile_descriptor(kind: str, family: str | None = None, schedule: str | None = None, knobs: dict | None = None) -> dict:
    """A JSON-serialisable coalition profile: all honest-max, all abstain, or a family's knobs with its schedule."""
    if kind not in ("honest_max", "abstain", "knobs"):
        raise ValueError(kind)
    if (kind == "knobs") != (family is not None and knobs is not None):
        raise ValueError("a knobs profile needs its family and knobs, and only it")
    return {"kind": kind, "family": family, "schedule": schedule, "knobs": None if knobs is None else dict(knobs)}


def profile_factories(desc: dict, members, T: int, L: int) -> list:
    c = len(members)
    if desc["kind"] == "honest_max":
        return [HonestMax] * c
    if desc["kind"] == "abstain":
        return [Abstain] * c
    return member_factories(desc["family"], desc["knobs"], members, desc["schedule"] == "staggered", T, L)


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
                 staggered: bool = False, T: int = 200, L: int = 10, family_name: str = "X6-SE/v2") -> None:
        if kind not in ("total", "min", "joint_twin"):
            raise ValueError(kind)
        if family_name not in COALITION_FAMILIES:
            raise ValueError(f"unknown coalition family {family_name!r}")
        if family_name == "X8-DB" and len(members) != 2:
            raise ValueError("X8-DB needs exactly two members")
        self.family_name = family_name
        if kind != "joint_twin" and joint_ref is None:
            raise ValueError("total and min need the frozen joint reference")
        cell = Cell(cfg=cfg, rule_factory=rule_factory, focal=int(members[0]), seeds=tuple(seeds), name="coalition")
        super().__init__(cell, family, cache, force_clip=(kind == "joint_twin"))
        self.members, self.kind, self.staggered, self.T, self.L = tuple(int(m) for m in members), kind, bool(staggered), int(T), int(L)
        self.ref = None if joint_ref is None else np.asarray(joint_ref, dtype=float)
        self.extra: dict[tuple, dict] = {}

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        knobs = self.family.project(knobs) if self.force_clip else dict(knobs)
        facs = member_factories(self.family_name, knobs, self.members, self.staggered, self.T, self.L)
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


def select_welfare(records_by_family: dict) -> dict:
    """Design 6.2 (draft 7): per rule and objective, the family whose training-selected winner has the lower training
    efficiency, among families with a candidate (a W1 search may find none); ties D2+H3 first."""
    best = None
    for fam in ("D2+H3", "X7-SC"):
        r = records_by_family.get(fam)
        if r is None or r.get("selected") is None:
            continue
        if best is None or float(r["train_eff"]) < best[1]:
            best = (fam, float(r["train_eff"]))
    if best is None:
        return {"family": None, "status": "no feasible candidate found", "train_eff": None}
    return {"family": best[0], "status": "selected", "train_eff": best[1]}

