# Independent oracle: verbatim copy of sim/mechanisms/proposed.py at commit 46694cb (the amendment-2 rule, killed at F2).
"""The proposed rule R*, exactly as the registered design block of experiments/amendment-2026-10-17.yaml prescribes
(amendment 1, design and tuning; the orchestration of amendment 2). Allocation A reimplements B3's descending-value
sequential second-score allocation and payment; allocation B reimplements B1's tier allocation at the locked B2 prices
(bids ignored). The audit count follows the registered schedule (terminal reserve of the last L rounds, cumulative
early quota with carry); the audit selection is half targeted (T1: newest identity first; T2: lowest audits per served
job, recomputed after every selection), half uniform by audit key; enforcement is a full refund of the failed job's
escrow and a ban of L rounds; no hold-back. The rule reads only offers, job values, purchased audit results, its own
memory, and the constants of bind(cfg). Its audit selection is not expressible in the locked vocabulary (the ruling of
both review seats), so the describe record says so."""
from __future__ import annotations

import math

import numpy as np

from sim.mechanisms.base import AuditRecord, Consequences, Mechanism, Offers, StateView

ALLOCATIONS = ("A", "B")
TARGETINGS = ("T1", "T2")
TOLS = (0.12, 0.14, 0.16)
BAN_LENGTHS = (3, 10, 20)
TIERS = ((0.0, 0.5), (0.5, 0.8), (0.8, 1.0001))          # B1's tiers by claim


# ------------------------------------------------------------------------------------------------ the registered schedule
def terminal(t: int, T: int, L: int) -> bool:
    """Rounds T - L .. T - 1 are terminal: every served job is audited while audits remain."""
    return int(t) >= int(T) - int(L)


def _reserve(J: int, L: int, A_tot: int) -> int:
    return min(int(J) * int(L), int(A_tot))


def _cumulative(t: int, E: int, early_rounds: int) -> int:
    """C(t) = floor(E (t + 1) / (T - L)); C(-1) = 0."""
    if t < 0:
        return 0
    return (int(E) * (int(t) + 1)) // int(early_rounds)


def audit_quota(t: int, T: int, L: int, J: int, A_tot: int, carry: int) -> int:
    """The available quota of round t before the served-jobs and audits-left caps: in an early round C(t) - C(t - 1)
    plus the carried unspent quota; in a terminal round the whole allowance (the caller caps it by the served jobs and
    by audits_left, so every served job is audited while audits remain)."""
    if terminal(t, T, L):
        return int(A_tot)
    early_rounds = int(T) - int(L)
    E = int(A_tot) - _reserve(J, L, A_tot)
    return _cumulative(t, E, early_rounds) - _cumulative(t - 1, E, early_rounds) + int(carry)


def split_counts(k: int) -> tuple[int, int]:
    """k_t = ceil(k / 2) targeted, the rest uniform."""
    k_t = (int(k) + 1) // 2
    return k_t, int(k) - k_t


def select_audits(jobs_by_identity: dict, audit_key, first_round: dict, audits: dict, served: dict, targeting: str, k_t: int, k_u: int) -> list:
    """Pure job-level selection in order: k_t targeted picks, one job at a time (T1 by descending first_round of the
    job's identity then ascending audit_key; T2 by ascending audits_i / served_i recomputed after every pick, served_i = 0
    giving 0, then ascending audit_key), then k_u uniform picks among the remaining jobs by ascending audit_key. The
    caller's counts are not changed."""
    remaining = {int(j): int(i) for i, jobs in jobs_by_identity.items() for j in jobs}
    counts = {int(i): int(a) for i, a in audits.items()}
    chosen: list = []

    def ratio(i: int) -> float:
        s = int(served.get(i, 0))
        return (counts.get(i, 0) / s) if s > 0 else 0.0

    for _ in range(int(k_t)):
        if not remaining:
            break
        if targeting == "T1":
            pick = min(remaining, key=lambda j: (-int(first_round.get(remaining[j], 0)), float(audit_key[j]), j))
        else:
            pick = min(remaining, key=lambda j: (ratio(remaining[j]), float(audit_key[j]), j))
        i = remaining.pop(pick)
        counts[i] = counts.get(i, 0) + 1
        chosen.append(pick)
    rest = sorted(remaining, key=lambda j: (float(audit_key[j]), j))
    chosen.extend(rest[: max(0, int(k_u))])
    return chosen


# ------------------------------------------------------------------------------------------------ the rule
class Proposed(Mechanism):
    name = "proposed"

    def __init__(self, allocation: str, targeting: str, tol: float, L: int, prices: tuple | None = None) -> None:
        self.allocation, self.targeting = str(allocation), str(targeting)
        self.tol, self.L = float(tol), int(L)
        self.prices = None if prices is None else tuple(float(p) for p in prices)
        self.T, self.J, self.A_tot = 1, 1, 0

    def bind(self, cfg) -> None:
        self.T, self.J = int(cfg.T), int(cfg.J)
        self.A_tot = int(math.floor(cfg.budget / cfg.alpha + 1e-12)) if cfg.alpha > 0 else 0

    # ---- memory
    @staticmethod
    def _memory(view: StateView) -> tuple[dict, dict, dict]:
        m = view.memory
        return m.setdefault("first_round", {}), m.setdefault("audits", {}), m.setdefault("served", {})

    # ---- allocation
    @staticmethod
    def tier_of(claim: float) -> int:
        for k, (lo, hi) in enumerate(TIERS):
            if lo <= claim < hi:
                return k
        return 2

    def _allocate_a(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        """B3: jobs in descending value; each to the active offer with capacity and the highest score v * claim - bid
        (negative scores not eligible), ties by the smallest tie key; the second score is stored for the payment."""
        N = view.N
        cap = np.array(view.capacity, dtype=np.int64)
        claim = np.zeros(N); bid = np.zeros(N); offered = np.zeros(N, dtype=bool)
        for i, off in offers.items():
            if view.is_active(i):
                claim[i], bid[i], offered[i] = off.claim, off.bid, True
        tie = view.memory["tie_key"]
        idx = np.arange(N)
        s2: dict[int, float] = {}
        out: dict[int, int] = {}
        for j in np.argsort(-values_t, kind="stable"):
            v = float(values_t[j])
            score = v * claim - bid
            mask = offered & (cap > 0) & (score >= 0)
            if not mask.any():
                continue
            top = score[mask].max()
            winners = np.flatnonzero(mask & (score == top))
            w = int(winners[np.argmin(tie[j, winners])])
            rest = score[mask & (idx != w)]
            s2[int(j)] = float(rest.max()) if rest.size else 0.0
            out[int(j)] = w
            cap[w] -= 1
        view.memory["second_scores"] = s2
        return out

    def _allocate_b(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        """B1 at the locked B2 prices: jobs in descending value; each to the highest tier with an active offer with
        capacity whose claim times the value reaches the tier price, ties by the smallest tie key; bids ignored."""
        cap = view.capacity.tolist()
        tie = view.memory["tie_key"]
        by_tier: list[list[tuple[int, float]]] = [[], [], []]
        for i, off in offers.items():
            if view.is_active(i) and cap[i] > 0:
                k = self.tier_of(off.claim)
                thr = self.prices[k] / off.claim if off.claim > 0 else float("inf")
                by_tier[k].append((i, thr))
        out: dict[int, int] = {}
        for j in np.argsort(-values_t, kind="stable").tolist():
            v = float(values_t[j])
            row = tie[j]
            for k in (2, 1, 0):
                best = -1; best_key = 2.0
                for i, thr in by_tier[k]:
                    if cap[i] > 0 and v >= thr:
                        key = float(row[i])
                        if key < best_key:
                            best, best_key = i, key
                if best >= 0:
                    out[j] = best
                    cap[best] -= 1
                    break
        return out

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        first_round, _, served = self._memory(view)
        for i in offers:
            if view.is_active(i):
                first_round.setdefault(int(i), int(view.t))           # the round of the identity's first offer, never changed
                served.setdefault(int(i), 0)                           # an offering identity's served count starts at the offer
        out = self._allocate_a(values_t, offers, view) if self.allocation == "A" else self._allocate_b(values_t, offers, view)
        for i in out.values():
            served[int(i)] = served.get(int(i), 0) + 1
        return out

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        if self.allocation == "A":
            s2 = view.memory.get("second_scores", {})
            return {j: float(values_t[j] * offers[i].claim - s2.get(j, 0.0)) for j, i in assignment.items()}
        tier_price = {i: self.prices[self.tier_of(off.claim)] for i, off in offers.items()}
        return {j: tier_price[i] for j, i in assignment.items()}

    # ---- audits
    def audit(self, assignment: dict[int, int], view: StateView) -> list[int]:
        first_round, audits, served = self._memory(view)
        carry = int(view.memory.get("quota_carry", 0))
        t = int(view.t); n_served = len(assignment)
        is_terminal = terminal(t, self.T, self.L)
        k_avail = int(min(n_served, self.A_tot)) if is_terminal else audit_quota(t, self.T, self.L, self.J, self.A_tot, carry)
        k = max(0, min(k_avail, n_served, int(view.audits_left)))
        k_t, k_u = split_counts(k)
        by_identity: dict[int, list[int]] = {}
        for j, i in assignment.items():
            by_identity.setdefault(int(i), []).append(int(j))
        chosen = select_audits(by_identity, view.audit_key, first_round, audits, served, self.targeting, k_t, k_u) if k > 0 else []
        for j in chosen:
            i = int(assignment[j]); audits[i] = audits.get(i, 0) + 1
        view.memory["quota_carry"] = 0 if is_terminal else int(k_avail - len(chosen))
        return chosen

    # ---- enforcement
    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        cons = Consequences()
        for r in records:
            if r.failed:
                cons.refunds[r.job] = float(view.escrow[r.job])
                cons.bans[r.provider] = max(cons.bans.get(r.provider, 0), int(self.L))
        return cons

    # ---- description
    def describe(self) -> dict:
        if self.allocation == "A":
            alloc = {"allocation_order": "jobs in descending value; each job goes to the offer with capacity and the highest score, score = job value times claim minus bid, offers with a negative score are not eligible, at random among equal scores",
                     "eligibility": "active offers with capacity",
                     "payment": "second score: job value times claim minus the highest score among the other eligible offers for that job, zero when there is none"}
        else:
            alloc = {"allocation_order": "jobs in descending value; each job goes to the highest posted tier that has an offer with capacity whose claim times the job value reaches the tier price, at random among those offers; tiers by claim: below 0.5, 0.5 to below 0.8, 0.8 and above",
                     "eligibility": "active offers with capacity", "payment": "the posted price of the tier the job was allocated in"}
        return {**alloc, "audit_selection": "not expressible", "audit_tolerance": "number", "failed_audit": "full refund of the audited job",
                "ban_length": "number", "holdback": "none", "parameters": {"audit_tolerance": float(self.tol), "ban_length": int(self.L)}}


def make(params: dict) -> Proposed:
    """The registered grid only: allocation A or B, targeting T1 or T2, tol in {0.12, 0.14, 0.16}, L in {3, 10, 20};
    allocation B needs the locked B2 prices P1 < P2 < P3 and allocation A takes none; no other key."""
    p = dict(params)
    allowed = {"allocation", "targeting", "tol", "L", "P1", "P2", "P3"}
    extra = sorted(set(p) - allowed)
    if extra:
        raise ValueError(f"unknown parameter(s) {extra}")
    for k in ("allocation", "targeting", "tol", "L"):
        if k not in p:
            raise ValueError(f"missing parameter {k!r}")
    if p["allocation"] not in ALLOCATIONS:
        raise ValueError(f"allocation must be one of {ALLOCATIONS}")
    if p["targeting"] not in TARGETINGS:
        raise ValueError(f"targeting must be one of {TARGETINGS}")
    tol = float(p["tol"])
    if not any(math.isclose(tol, v, rel_tol=0.0, abs_tol=1e-12) for v in TOLS):
        raise ValueError(f"tol must be one of {TOLS}")
    L = p["L"]
    if isinstance(L, bool) or int(L) != L or int(L) not in BAN_LENGTHS:
        raise ValueError(f"L must be one of {BAN_LENGTHS}")
    has_prices = any(k in p for k in ("P1", "P2", "P3"))
    if p["allocation"] == "B":
        if not all(k in p for k in ("P1", "P2", "P3")):
            raise ValueError("allocation B needs the locked B2 prices P1, P2, P3")
        prices = (float(p["P1"]), float(p["P2"]), float(p["P3"]))
        if not (0.0 < prices[0] < prices[1] < prices[2]):
            raise ValueError("need 0 < P1 < P2 < P3")
        return Proposed("B", p["targeting"], tol, int(L), prices)
    if has_prices:
        raise ValueError("allocation A takes no prices")
    return Proposed("A", p["targeting"], tol, int(L), None)
