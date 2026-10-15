from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .cell import Abstain, Cell, SeedCache, run_focal
from .metrics import harm
from .policies.families import Family, exact_key
from .policies.honest import HonestMax
from .search import Objective, SearchResult, SearchSettings, best_archived, cma_search

REFERENCE_ORDER = ("abstain", "honest_max", "twin_search", "attack_projection", "archive_clip1", "archive_truthful_clip0", "bank")


@dataclass(frozen=True)
class Candidate:
    name: str
    policy_factory: Callable
    knobs: dict | None
    known_profit: np.ndarray | None = None
    known_normalized: np.ndarray | None = None


@dataclass
class ReferenceChoice:
    candidate: Candidate
    per_seed_profit: np.ndarray
    per_seed_normalized: np.ndarray
    scores: dict


def twin_search(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int) -> SearchResult:
    starts = family.registered_starts({"near_corner": settings.near_corner, "sobol_seed": settings.sobol_seed}, twin=True)
    return cma_search(Objective(cell, family, cache, force_clip=True), family, settings, seed, starts=starts)


def attack_search(cell: Cell, family: Family, cache: SeedCache, settings: SearchSettings, seed: int, twin: SearchResult) -> SearchResult:
    """Attack search with the twin best and the honest-max point as registered incumbents (spec 5.2)."""
    return cma_search(Objective(cell, family, cache), family, settings, seed,
                      incumbents={"twin_best": twin.best_knobs, "honest_point": family.honest_point()})


def _factory(family: Family, knobs: dict) -> Callable:
    return lambda: family.make(knobs)


def _known(entry) -> dict:
    return {} if entry is None else {"known_profit": entry.per_seed_profit, "known_normalized": entry.per_seed_normalized}


def reference_candidates(cell: Cell, family: Family, attack: SearchResult, twin: SearchResult,
                         bank_members: list[dict], order=REFERENCE_ORDER) -> list[Candidate]:
    """Every reference candidate in projected form, in registered tie order (spec 5.2); de-duplicated by exact key."""
    n = len(cell.seeds)
    groups: dict[str, list[Candidate]] = {}
    groups["abstain"] = [Candidate("abstain", Abstain, None, np.zeros(n), np.zeros(n))]
    groups["honest_max"] = [Candidate("honest_max", HonestMax, None)]
    tw = family.project(twin.best_knobs)
    groups["twin_search"] = [Candidate("twin_search", _factory(family, tw), tw, **_known(twin.archive.get(exact_key(tw))))]
    proj = family.project(attack.best_knobs)
    groups["attack_projection"] = [Candidate("attack_projection", _factory(family, proj), proj, **_known(attack.archive.get(exact_key(proj))))]
    e1 = best_archived(attack.archive, clip=1)
    groups["archive_clip1"] = [] if e1 is None else [Candidate("archive_clip1", _factory(family, e1.knobs), dict(e1.knobs), **_known(e1))]
    e0 = best_archived(attack.archive, clip=0, truthful_only=True)
    if e0 is None:
        groups["archive_truthful_clip0"] = []
    else:   # never inflated on dev-train: its projection has the same trajectory, so its observed values are its projected values
        p0 = family.project(e0.knobs)
        groups["archive_truthful_clip0"] = [Candidate("archive_truthful_clip0", _factory(family, p0), p0, **_known(e0))]
    groups["bank"] = [Candidate(f"bank_{i}", _factory(family, family.project(m)), family.project(m)) for i, m in enumerate(bank_members)]
    out, seen = [], set()
    for g in order:
        for c in groups.get(g, []):
            key = exact_key(c.knobs) if c.knobs is not None else ("name", c.name)
            if key in seen:
                continue
            seen.add(key); out.append(c)
    return out


def select_reference(cell: Cell, candidates: list[Candidate], cache: SeedCache) -> ReferenceChoice:
    """Highest mean normalized profit on the cell's seeds; ties to the earlier candidate; known values need no run."""
    best, scores = None, {}
    for c in candidates:
        if c.known_normalized is not None and len(c.known_normalized) == len(cell.seeds):
            profit, norm = c.known_profit, c.known_normalized
        else:
            fr = run_focal(cell, c.policy_factory, cache)
            profit, norm = fr.profit, fr.normalized
        score = float(norm.mean())
        scores[c.name] = score
        if best is None or score > best[0]:
            best = (score, c, profit, norm)
    _, c, profit, norm = best
    return ReferenceChoice(candidate=c, per_seed_profit=np.asarray(profit, dtype=float), per_seed_normalized=np.asarray(norm, dtype=float), scores=scores)


@dataclass
class GainResult:
    gain: np.ndarray
    inflation_term: np.ndarray
    selection_term: np.ndarray
    profit_attack: np.ndarray
    profit_clip: np.ndarray
    profit_ref: np.ndarray
    profit_honest: np.ndarray
    sstar: np.ndarray
    eff_attack: np.ndarray
    eff_clip: np.ndarray
    eff_ref: np.ndarray
    eff_honest: np.ndarray
    net_eff_attack: np.ndarray
    net_eff_ref: np.ndarray
    audit_cost_attack: np.ndarray
    audit_spend_attack: np.ndarray
    audited_fraction_attack: np.ndarray
    harm_accounting: np.ndarray
    harm_direct: np.ndarray
    served_focal_attack: np.ndarray
    failures_focal_attack: np.ndarray
    entry_attack: np.ndarray
    n_identities_attack: np.ndarray
    others_profit_attack: np.ndarray
    refunds_attack: np.ndarray
    forfeits_attack: np.ndarray
    holdback_in_attack: np.ndarray
    refunds_focal_attack: np.ndarray
    forfeits_focal_attack: np.ndarray
    focal_bans_attack: np.ndarray
    focal_audited_attack: np.ndarray
    focal_banned_rounds_attack: np.ndarray
    others_audited_attack: np.ndarray
    others_bans_attack: np.ndarray
    others_lost_capacity_attack: np.ndarray
    seeds: tuple


METRIC_FIELDS = ["seed", "sstar", "gain", "inflation_term", "selection_term", "profit_attack", "profit_clip", "profit_ref",
                 "profit_honest", "eff_attack", "eff_clip", "eff_ref", "eff_honest", "net_eff_attack", "net_eff_ref",
                 "audit_cost_attack", "audit_spend_attack", "audited_fraction_attack", "harm_accounting", "harm_direct",
                 "served_focal_attack", "failures_focal_attack", "entry_attack", "n_identities_attack", "others_profit_attack",
                 "refunds_attack", "forfeits_attack", "holdback_in_attack", "refunds_focal_attack", "forfeits_focal_attack",
                 "focal_bans_attack", "focal_audited_attack", "focal_banned_rounds_attack",
                 "others_audited_attack", "others_bans_attack", "others_lost_capacity_attack"]
ROW_FIELDS = METRIC_FIELDS


def participant_diagnostics(res, cfg, focal: int) -> dict:
    """Spec 7 scripted-participant diagnostics from one episode: audits on the focal entity's identities and on
    the others, bans on the others (false bans: the others are honest-max), rounds the focal entity spent banned,
    and the capacity the others lost while banned (sum over banned identity-rounds of k_i). A ban on a retired
    focal identity does not count: the entity acts through its current identity."""
    ids_f = {i for i, e in enumerate(res.entity_of) if e == focal}
    k_of = [cfg.providers[e].k for e in res.entity_of]
    created = sorted((r, i) for i, (e, r) in enumerate(zip(res.entity_of, res.identity_round)) if e == focal)
    banned_until: dict[int, int] = {}
    out = {"focal_audited": 0, "others_audited": 0, "others_bans": 0, "focal_bans": 0, "focal_banned_rounds": 0, "others_lost_capacity": 0,
           "refunds_focal": float(sum(res.ledger.refunds[:, i].sum() for i in ids_f)),
           "forfeits_focal": float(sum(res.ledger.forfeits[:, i].sum() for i in ids_f))}
    for rec in res.history:
        current = max((i for r, i in created if r <= rec.t), key=lambda i: (res.identity_round[i], res.identity_generation[i]))   # the entity's identity this round
        for i, until in banned_until.items():
            if rec.t < until:
                if i == current:
                    out["focal_banned_rounds"] += 1      # a ban on a retired identity excludes nothing
                elif i not in ids_f:
                    out["others_lost_capacity"] += k_of[i]
        for r in rec.audits:
            out["focal_audited" if r.provider in ids_f else "others_audited"] += 1
        for i, rounds in rec.consequences.bans.items():
            out["focal_bans" if i in ids_f else "others_bans"] += 1
            banned_until[i] = max(banned_until.get(i, 0), rec.t + int(rounds) + 1)
    return out


def _gross(results) -> np.ndarray:
    return np.array([(r.W + r.audit_cost) / r.sstar for r in results])


def _net(results) -> np.ndarray:
    return np.array([r.W / r.sstar for r in results])


def evaluate_gain(cell: Cell, family: Family, attack_knobs: dict, reference: Candidate, cache: SeedCache) -> GainResult:
    attack = run_focal(cell, _factory(family, dict(attack_knobs)), cache)
    clipped = run_focal(cell, _factory(family, family.project(attack_knobs)), cache)
    ref = run_focal(cell, reference.policy_factory, cache)
    honest = run_focal(cell, HonestMax, cache)
    N, f = cell.cfg.N, cell.focal
    sstar = np.array([r.sstar for r in attack.results])
    scale = sstar / N
    inflation = (attack.profit - clipped.profit) / scale
    selection = (clipped.profit - ref.profit) / scale
    hm = np.array([harm(a, r, f) for a, r in zip(attack.results, ref.results)])
    diag = [participant_diagnostics(r, cell.cfg, f) for r in attack.results]
    served = np.array([int(r.served[:, f].sum()) for r in attack.results])
    audited = np.array([int(r.audits.sum()) for r in attack.results])
    total_served = np.array([int(r.served.sum()) for r in attack.results])
    return GainResult(
        gain=inflation + selection, inflation_term=inflation, selection_term=selection,
        profit_attack=attack.profit, profit_clip=clipped.profit, profit_ref=ref.profit, profit_honest=honest.profit, sstar=sstar,
        eff_attack=_gross(attack.results), eff_clip=_gross(clipped.results), eff_ref=_gross(ref.results), eff_honest=_gross(honest.results),
        net_eff_attack=_net(attack.results), net_eff_ref=_net(ref.results),
        audit_cost_attack=np.array([r.audit_cost for r in attack.results]),
        audit_spend_attack=np.array([r.audit_cost / r.sstar for r in attack.results]),
        audited_fraction_attack=np.where(total_served > 0, audited / np.maximum(total_served, 1), 0.0),
        harm_accounting=hm[:, 0], harm_direct=hm[:, 1],
        served_focal_attack=served, failures_focal_attack=np.array([int(r.failures[:, f].sum()) for r in attack.results]),
        entry_attack=np.array([r.entry for r in attack.results]),
        n_identities_attack=np.array([r.n_identities for r in attack.results]),
        others_profit_attack=np.array([float(r.profit.sum() - r.profit[f]) for r in attack.results]),
        refunds_attack=np.array([float(r.ledger.refunds.sum()) for r in attack.results]),
        forfeits_attack=np.array([float(r.ledger.forfeits.sum()) for r in attack.results]),
        holdback_in_attack=np.array([float(r.ledger.holdback_in.sum()) for r in attack.results]),
        refunds_focal_attack=np.array([d["refunds_focal"] for d in diag]),
        forfeits_focal_attack=np.array([d["forfeits_focal"] for d in diag]),
        focal_bans_attack=np.array([d["focal_bans"] for d in diag]),
        focal_audited_attack=np.array([d["focal_audited"] for d in diag]),
        focal_banned_rounds_attack=np.array([d["focal_banned_rounds"] for d in diag]),
        others_audited_attack=np.array([d["others_audited"] for d in diag]),
        others_bans_attack=np.array([d["others_bans"] for d in diag]),
        others_lost_capacity_attack=np.array([d["others_lost_capacity"] for d in diag]),
        seeds=tuple(cell.seeds))


def seed_rows(cell: Cell, g: GainResult, meta: dict) -> list[dict]:
    rows = []
    for k, seed in enumerate(cell.seeds):
        row = dict(meta)
        for name in METRIC_FIELDS:
            if name == "seed":
                row["seed"] = int(seed)
            else:
                v = getattr(g, name)[k]
                row[name] = int(v) if isinstance(v, (np.integer, int)) else float(v)
        rows.append(row)
    return rows
