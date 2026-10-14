from __future__ import annotations

import numpy as np

from .audit_random import RandomAuditMixin
from .base import Mechanism, Offers, StateView


class SecondScore(RandomAuditMixin, Mechanism):
    """B3 (spec 4.1): sequential second-score auction with capacity; not truthful."""
    name = "B3_second_score"

    def __init__(self, tol: float, L: int) -> None:
        self.tol = float(tol)
        self.L = int(L)

    def allocate(self, values_t: np.ndarray, offers: Offers, view: StateView) -> dict[int, int]:
        N = view.N
        cap = np.array(view.capacity, dtype=np.int64)
        claim = np.zeros(N); bid = np.zeros(N); offered = np.zeros(N, dtype=bool)
        for i, off in offers.items():
            if view.is_active(i):
                claim[i], bid[i], offered[i] = off.claim, off.bid, True
        tie = view.memory["tie_key"]
        idx = np.arange(N)
        s2_map: dict[int, float] = {}
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
            s2_map[int(j)] = float(rest.max()) if rest.size else 0.0
            out[int(j)] = w
            cap[w] -= 1
        view.memory["second_scores"] = s2_map
        return out

    def price(self, assignment, values_t, offers, view) -> dict[int, float]:
        s2 = view.memory.get("second_scores", {})
        return {j: float(values_t[j] * offers[i].claim - s2.get(j, 0.0)) for j, i in assignment.items()}

    def describe(self) -> dict[str, str]:
        return {"allocation": "descending value; highest score v*claim - bid wins; capacity respected",
                "pricing": "second score: v*claim minus runner-up score",
                "audit_selection": "uniform random among served jobs, spread schedule",
                "audit_tolerance": f"{self.tol}", "failed_audit": "full refund",
                "ban_length": f"{self.L}", "holdback": "none"}
