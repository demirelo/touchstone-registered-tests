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
        N = view.N
        cap = np.array(view.capacity, dtype=np.int64)
        tier = np.full(N, -1, dtype=np.int64)
        claim = np.zeros(N)
        for i, off in offers.items():
            if view.is_active(i):
                tier[i] = self.tier_of(off.claim)
                claim[i] = off.claim
        price = np.where(tier >= 0, np.array(self.prices)[np.clip(tier, 0, 2)], np.inf)
        tie = view.memory["tie_key"]
        out: dict[int, int] = {}
        for j in np.argsort(-values_t, kind="stable"):
            v = float(values_t[j])
            mask = (cap > 0) & (tier >= 0) & (v * claim >= price)
            if not mask.any():
                continue
            best = tier[mask].max()
            cands = np.flatnonzero(mask & (tier == best))
            chosen = int(cands[np.argmin(tie[j, cands])])
            out[int(j)] = chosen
            cap[chosen] -= 1
        return out

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        return {j: self.prices[self.tier_of(offers[i].claim)] for j, i in assignment.items()}

    def audit(self, assignment, view) -> list[int]:
        return []

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        return Consequences()

    def describe(self) -> dict[str, str]:
        return {"allocation": "descending value; highest accepted tier; random within tier",
                "pricing": "posted tier price", "audit_selection": "none", "audit_tolerance": "none",
                "failed_audit": "none", "ban_length": "0", "holdback": "none"}
