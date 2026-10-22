"""The 2 x 2 x 2 decomposition of R3 (design 3.2) and the repaired R3, R4 (design 3.4). Every cell is B3's allocation and
payment with refund-and-ban enforcement; cells differ in pacing (S: B3's spread count or R3's reserve schedule) and in
selection (P: the priority phase over identities younger than L rounds; G: the newest-first half of the residual). F000 is
B3, F111 is R3, F011 is the killed amendment-2 rule (tests/oracles). Ties: when P = G = 0 the uniform order is B3's (stable
order of the audit key over jobs in assignment order); otherwise R3's (audit key, then job)."""
from __future__ import annotations

import numpy as np

from .base import AuditRecord, Consequences, Mechanism, Offers, StateView
from .pacing import ReservePacing, spread_cap, spread_count
from .second_score import SecondScore

NAMES = tuple(f"F{p}{g}{s}" for p in (0, 1) for g in (0, 1) for s in (0, 1)) + ("R4",)


def select(jobs_by_identity: dict, audit_key, first_round: dict, t: int, L: int, k: int, P: int, G: int, order: list | None = None) -> list:
    """k audited jobs in order. Priority phase (P = 1): the jobs of identities with 0 <= t - first_round < L, by (-first_round,
    audit_key, job). Residual r: with G = 1, ceil(r / 2) picks by (-first_round, audit_key, job), then uniform by (audit_key, job);
    with G = 0, all uniform. With P = G = 0, uniform is B3's stable audit-key order over `order` (jobs in assignment order)."""
    remaining = {int(j): int(i) for i, jobs in jobs_by_identity.items() for j in jobs}
    k = max(0, min(int(k), len(remaining)))
    if not P and not G:
        jobs = np.asarray(order if order is not None else list(remaining), dtype=np.int64)
        idx = np.argsort(np.asarray(audit_key)[jobs], kind="stable")
        return jobs[idx[:k]].tolist()
    born = lambda i: int(first_round.get(i, t))
    newest = lambda j: (-born(remaining[j]), float(audit_key[j]), j)
    chosen: list = []
    if P:
        fresh = sorted((j for j, i in remaining.items() if 0 <= int(t) - born(i) < int(L)), key=newest)
        for j in fresh[:k]:
            remaining.pop(j); chosen.append(j)
    r = k - len(chosen)
    k_t = (r + 1) // 2 if G else 0
    for _ in range(k_t):
        pick = min(remaining, key=newest)
        remaining.pop(pick); chosen.append(pick)
    rest = sorted(remaining, key=lambda j: (float(audit_key[j]), j))
    chosen.extend(rest[: r - k_t])
    return chosen


class FactorialRule(Mechanism):
    def __init__(self, P: int, G: int, S: int, tol: float, L: int, reserve: str = "full") -> None:
        if any(v not in (0, 1) for v in (P, G, S)):
            raise ValueError("P, G, S must be 0 or 1")
        self.P, self.G, self.S, self.tol, self.L, self.reserve = int(P), int(G), int(S), float(tol), int(L), str(reserve)
        if self.reserve != "full" and not (self.P and self.G and self.S):
            raise ValueError("the half reserve is R4 only")
        self.name = "R4" if self.reserve == "half" else f"F{self.P}{self.G}{self.S}"
        self._b3 = SecondScore(self.tol, self.L)
        self._pacing = ReservePacing(self.reserve, self.L)
        self.T, self.cap = 1, 1

    def bind(self, cfg) -> None:
        self.T, self.cap = int(cfg.T), spread_cap(cfg)
        self._pacing.bind(cfg)

    @staticmethod
    def _memory(view: StateView) -> tuple[dict, dict, dict]:
        m = view.memory
        return m.setdefault("first_round", {}), m.setdefault("audits", {}), m.setdefault("served", {})

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        first_round, _, served = self._memory(view)
        for i in offers:
            if view.is_active(i):
                first_round.setdefault(int(i), int(view.t))
                served.setdefault(int(i), 0)
        out = self._b3.allocate(values_t, offers, view)
        for i in out.values():
            served[int(i)] = served.get(int(i), 0) + 1
        return out

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return self._b3.price(assignment, values_t, offers, view)

    def audit(self, assignment: dict[int, int], view: StateView) -> list[int]:
        first_round, audits, _ = self._memory(view)
        n = len(assignment)
        k = self._pacing.count(view, n) if self.S else spread_count(view, self.T, self.cap, n)
        if k <= 0:
            return []
        by_identity: dict[int, list[int]] = {}
        for j, i in assignment.items():
            by_identity.setdefault(int(i), []).append(int(j))
        chosen = select(by_identity, view.audit_key, first_round, view.t, self.L, k, self.P, self.G, order=[int(j) for j in assignment])
        for j in chosen:
            i = int(assignment[j]); audits[i] = audits.get(i, 0) + 1
        return chosen

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        cons = Consequences()
        for r in records:
            if r.failed:
                cons.refunds[r.job] = float(view.escrow[r.job])
                cons.bans[r.provider] = max(cons.bans.get(r.provider, 0), int(self.L))
        return cons

    def describe(self) -> dict:
        d = dict(self._b3.describe())
        if self.name != "F000":
            d["audit_selection"] = "not expressible"
        d["parameters"] = {"audit_tolerance": float(self.tol), "ban_length": int(self.L)}
        return d


def make_factorial(name: str, tol: float, L: int) -> FactorialRule:
    if name == "R4":
        return FactorialRule(1, 1, 1, tol, L, reserve="half")
    if name not in NAMES:
        raise ValueError(f"unknown factorial cell {name!r}")
    return FactorialRule(int(name[1]), int(name[2]), int(name[3]), tol, L)
