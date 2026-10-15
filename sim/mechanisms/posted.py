from __future__ import annotations

import numpy as np

from .base import AuditRecord, Consequences, Mechanism, Offers, StateView

TIERS = ((0.0, 0.5), (0.5, 0.8), (0.8, 1.0001))


class PostedPrices(Mechanism):
    """B1 (spec 4.1). Tie-breaks use the precomputed key view.memory['tie_key'][j, i]."""
    name = "B1_posted"
    tol = None

    def __init__(self, P1: float, P2: float, P3: float) -> None:
        if not (0.0 < P1 < P2 < P3):
            raise ValueError("need 0 < P1 < P2 < P3")
        self.prices = (float(P1), float(P2), float(P3))

    @staticmethod
    def tier_of(claim: float) -> int:
        for k, (lo, hi) in enumerate(TIERS):
            if lo <= claim < hi:
                return k
        return 2

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        # Ten providers: plain Python per job beats NumPy small-array overhead.
        cap = view.capacity.tolist()
        tie = view.memory["tie_key"]
        by_tier: list[list[tuple[int, float]]] = [[], [], []]   # (provider, acceptance threshold v >= P/claim)
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

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        tier_price = {i: self.prices[self.tier_of(off.claim)] for i, off in offers.items()}
        return {j: tier_price[i] for j, i in assignment.items()}

    def audit(self, assignment, view) -> list[int]:
        return []

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        return Consequences()

    def describe(self) -> dict:
        return {"allocation_order": "jobs in descending value; each job goes to the highest posted tier that has an offer with capacity whose claim times the job value reaches the tier price, at random among those offers; tiers by claim: below 0.5, 0.5 to below 0.8, 0.8 and above",
                "eligibility": "active offers with capacity", "payment": "the posted price of the tier the job was allocated in",
                "audit_selection": "none", "audit_tolerance": "none", "failed_audit": "none", "ban_length": "none", "holdback": "none",
                "parameters": {}}

