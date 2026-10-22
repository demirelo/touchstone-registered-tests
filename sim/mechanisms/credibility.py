"""The credibility comparator (design 3.3), a budget-constrained adaptation of Sarmenta's credibility-based spot-checking
and BOINC's adaptive replication. B3's allocation and payment, refund-and-ban enforcement, and the pacing of F000 (S0),
R3 (S1), or R4 (S2). Credibility p_i = passed audits of identity i since its creation or its last failed audit, updated
in `enforce` from the round's audit results (any failure in the batch resets it to zero); selection in round t reads the
counts at the start of round t. C-thr: identities with p_i < K are unproven and their jobs are audited first; C-mem: as
C-thr over the passes of the last M rounds; C-taper: no priority phase, weighted sampling without replacement with
weights K / (p_i + K) by the exponential race on the audit key (a relative weight, not a marginal audit probability)."""
from __future__ import annotations

import math

import numpy as np

from .base import AuditRecord, Consequences, Mechanism, Offers, StateView
from .pacing import ReservePacing, spread_cap, spread_count
from .second_score import SecondScore

VARIANTS = ("thr", "mem", "taper")
PACINGS = ("S0", "S1", "S2")
SELECTION_GRID = ([{"variant": "thr", "K": k, "M": None} for k in (2, 6, 12, 24)]
                  + [{"variant": "mem", "K": k, "M": m} for k, m in ((2, 20), (2, 50), (6, 20), (6, 50))]
                  + [{"variant": "taper", "K": k, "M": None} for k in (2, 6, 12, 24)])


def passes_of(memory: dict, i: int, t: int, M: int | None) -> int:
    """Passes of identity i in rounds before t (and at or after t - M when M is set) since its last failure."""
    rows = memory.get("passes", {}).get(int(i), [])
    lo = -math.inf if M is None else int(t) - int(M)
    return int(sum(n for r, n in rows if lo <= r < int(t)))


def taper_weight(p: int, K: int) -> float:
    return float(K) / (float(p) + float(K))


def select_credibility(variant: str, jobs_by_identity: dict, audit_key, p: dict, k: int, K: int) -> list:
    """k audited jobs in order (design 3.3). `p` maps identity to its credibility at the start of the round."""
    remaining = {int(j): int(i) for i, jobs in jobs_by_identity.items() for j in jobs}
    k = max(0, min(int(k), len(remaining)))
    key = lambda j: float(audit_key[j])
    if variant == "taper":
        race = lambda j: (-math.log(key(j)) / taper_weight(p.get(remaining[j], 0), K) if key(j) > 0 else math.inf, j)
        return sorted(remaining, key=race)[:k]
    chosen: list = []
    picks: dict[int, int] = {}
    unproven = sorted((j for j, i in remaining.items() if p.get(i, 0) < K), key=lambda j: (p.get(remaining[j], 0), key(j), j))
    for j in unproven[:k]:
        i = remaining.pop(j); picks[i] = picks.get(i, 0) + 1; chosen.append(j)
    r = k - len(chosen); k_t = (r + 1) // 2
    for _ in range(k_t):
        pick = min(remaining, key=lambda j: (p.get(remaining[j], 0) + picks.get(remaining[j], 0), key(j), j))
        i = remaining.pop(pick); picks[i] = picks.get(i, 0) + 1; chosen.append(pick)
    chosen.extend(sorted(remaining, key=lambda j: (key(j), j))[: r - k_t])
    return chosen


class Credibility(Mechanism):
    def __init__(self, variant: str, K: int, tol: float, L: int, pacing: str = "S1", M: int | None = None) -> None:
        if variant not in VARIANTS:
            raise ValueError(f"variant must be one of {VARIANTS}")
        if pacing not in PACINGS:
            raise ValueError(f"pacing must be one of {PACINGS}")
        if (variant == "mem") != (M is not None):
            raise ValueError("M is required for C-mem and only for C-mem")
        self.variant, self.K, self.M, self.tol, self.L, self.pacing = variant, int(K), None if M is None else int(M), float(tol), int(L), pacing
        self.name = f"C-{variant}" + ("" if pacing == "S1" else f"/{pacing}")
        self._b3 = SecondScore(self.tol, self.L)
        self._pacing = None if pacing == "S0" else ReservePacing("full" if pacing == "S1" else "half", self.L)
        self.T, self.cap = 1, 1

    def bind(self, cfg) -> None:
        self.T, self.cap = int(cfg.T), spread_cap(cfg)
        if self._pacing is not None:
            self._pacing.bind(cfg)

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        return self._b3.allocate(values_t, offers, view)

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return self._b3.price(assignment, values_t, offers, view)

    def audit(self, assignment: dict[int, int], view: StateView) -> list[int]:
        n = len(assignment)
        k = self._pacing.count(view, n) if self._pacing is not None else spread_count(view, self.T, self.cap, n)
        if k <= 0:
            return []
        by_identity: dict[int, list[int]] = {}
        for j, i in assignment.items():
            by_identity.setdefault(int(i), []).append(int(j))
        window = self.M if self.variant == "mem" else None
        p = {i: passes_of(view.memory, i, view.t, window) for i in by_identity}
        return select_credibility(self.variant, by_identity, view.audit_key, p, k, self.K)

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        cons = Consequences()
        passes = view.memory.setdefault("passes", {}); last_fail = view.memory.setdefault("last_fail", {})
        batch: dict[int, list[bool]] = {}
        for r in records:
            batch.setdefault(int(r.provider), []).append(bool(r.failed))
            if r.failed:
                cons.refunds[r.job] = float(view.escrow[r.job])
                cons.bans[r.provider] = max(cons.bans.get(r.provider, 0), int(self.L))
        for i, fails in batch.items():
            if any(fails):
                passes[i] = []; last_fail[i] = int(view.t)
            else:
                passes.setdefault(i, []).append((int(view.t), len(fails)))
        return cons

    def describe(self) -> dict:
        d = dict(self._b3.describe())
        d["audit_selection"] = "not expressible"
        d["parameters"] = {"audit_tolerance": float(self.tol), "ban_length": int(self.L)}
        return d


def make_credibility(params: dict) -> Credibility:
    p = dict(params)
    extra = sorted(set(p) - {"variant", "K", "M", "tol", "L", "pacing"})
    if extra:
        raise ValueError(f"unknown parameter(s) {extra}")
    return Credibility(p["variant"], int(p["K"]), float(p["tol"]), int(p["L"]), p.get("pacing", "S1"), p.get("M"))
