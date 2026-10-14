from __future__ import annotations

import numpy as np

from .mechanisms.base import Consequences, H_MAX


class Ledger:
    """Owns every money flow. Conservation after every settlement:
    funding = released + refunds + holdback_out + forfeits + bond + escrow."""

    def __init__(self, N: int, T: int) -> None:
        self.N, self.T = N, T
        self.funding = np.zeros((T, N)); self.refunds = np.zeros((T, N)); self.released = np.zeros((T, N))
        self.holdback_in = np.zeros((T, N)); self.holdback_out = np.zeros((T, N)); self.forfeits = np.zeros((T, N))
        self.cost = np.zeros((T, N)); self.entry = np.zeros((T, N))
        self.audit_cost = np.zeros(T)
        self.bond = np.zeros(N)
        self._settled = 0

    def fund(self, t: int, job: int, provider: int, amount: float, escrow: dict, owner: dict) -> None:
        if not np.isfinite(amount) or amount < 0:
            raise ValueError("payment must be finite and non-negative")
        escrow[job] = escrow.get(job, 0.0) + amount
        owner[job] = provider
        self.funding[t, provider] += amount

    def charge_cost(self, t: int, provider: int, amount: float) -> None:
        self.cost[t, provider] += amount

    def charge_entry(self, t: int, provider: int, amount: float) -> None:
        self.entry[t, provider] += amount

    def charge_audit(self, t: int, amount: float) -> None:
        self.audit_cost[t] += amount

    def recent_receipts(self) -> np.ndarray:
        if self._settled == 0:
            return np.zeros(self.N)
        lo = max(0, self._settled - H_MAX)
        return self.released[lo:self._settled].sum(axis=0)

    def settle(self, t: int, escrow: dict, owner: dict, cons: Consequences, failed_jobs_of: dict) -> None:
        released = np.zeros(self.N)
        for job, amount in escrow.items():
            p = owner[job]
            refund = min(cons.refunds.get(job, 0.0), amount)
            self.refunds[t, p] += refund
            released[p] += amount - refund
        for ident, amount in cons.forfeits.items():
            self.bond[ident] -= amount
            self.forfeits[t, ident] += amount
        for ident, amount in cons.releases.items():
            self.bond[ident] -= amount
            self.holdback_out[t, ident] += amount
        for ident, amount in cons.holdbacks.items():
            if amount > released[ident] + 1e-12:
                raise ValueError(f"hold-back for identity {ident} exceeds its release this round")
            released[ident] -= amount
            self.holdback_in[t, ident] += amount
            self.bond[ident] += amount
        self.released[t] += released
        self._settled = t + 1
        excess = np.maximum(self.bond - self.recent_receipts(), 0.0)
        self.bond -= excess
        self.holdback_out[t] += excess
        escrow.clear()
        owner.clear()

    def terminal_settlement(self) -> None:
        t = max(self._settled - 1, 0)
        self.holdback_out[t] += self.bond
        self.bond[:] = 0.0

    def profit(self) -> np.ndarray:
        return (self.released + self.holdback_out - self.cost - self.entry).sum(axis=0)

    def buyer_credit(self) -> float:
        return float(self.refunds.sum() + self.forfeits.sum())

    def check_conservation(self, escrow_outstanding: float) -> None:
        lhs = self.funding.sum()
        rhs = (self.released.sum() + self.refunds.sum() + self.holdback_out.sum()
               + self.forfeits.sum() + self.bond.sum() + escrow_outstanding)
        if not (np.isfinite(lhs) and np.isfinite(rhs)):
            raise AssertionError("non-finite ledger totals")
        if abs(lhs - rhs) > 1e-9:
            raise AssertionError(f"cash not conserved: funding {lhs:.9f} vs {rhs:.9f}")
