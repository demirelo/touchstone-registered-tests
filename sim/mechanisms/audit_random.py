from __future__ import annotations

import numpy as np

from .base import AuditRecord, Consequences, StateView


def spread_audit_count(allowance_left: int, t: int, T: int, served_count: int, cap_per_round: int, audit_u: float) -> int:
    """Spec 4.1 spread schedule on an integer allowance; t is zero-based."""
    if allowance_left <= 0:
        return 0
    target = allowance_left / (T - t)
    base = int(np.floor(target))
    n = base + (1 if audit_u < target - base else 0)
    return max(0, min(n, int(served_count), int(cap_per_round), int(allowance_left)))


class RandomAuditMixin:
    tol: float
    L: int
    cap_per_round: int = 1
    T: int = 1

    def bind(self, cfg) -> None:
        self.T = int(cfg.T)
        self.cap_per_round = max(1, int(np.floor(2.0 * cfg.budget / (cfg.T * cfg.alpha)))) if cfg.alpha > 0 else 0

    def audit(self, assignment: dict[int, int], view: StateView) -> list[int]:
        jobs = np.fromiter(assignment.keys(), dtype=np.int64, count=len(assignment))
        n = spread_audit_count(view.audits_left, view.t, self.T, len(jobs), self.cap_per_round, view.audit_u)
        if n == 0:
            return []
        order = np.argsort(view.audit_key[jobs], kind="stable")
        return jobs[order[:n]].tolist()

    def enforce(self, records: tuple[AuditRecord, ...], view: StateView) -> Consequences:
        cons = Consequences()
        for r in records:
            if r.failed:
                cons.refunds[r.job] = float(view.escrow[r.job])
                if self.L > 0:
                    cons.bans[r.provider] = max(cons.bans.get(r.provider, 0), int(self.L))
        return cons
