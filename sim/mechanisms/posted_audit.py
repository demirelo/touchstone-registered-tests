from __future__ import annotations

from .audit_random import RandomAuditMixin
from .posted import PostedPrices


class PostedRandomAudit(RandomAuditMixin, PostedPrices):
    """B2 (spec 4.1)."""
    name = "B2_posted_random_audit"

    def __init__(self, P1: float, P2: float, P3: float, tol: float, L: int) -> None:
        PostedPrices.__init__(self, P1, P2, P3)
        self.tol = float(tol)
        self.L = int(L)

    def describe(self) -> dict:
        d = PostedPrices.describe(self)
        d.update({"audit_selection": "uniform random among served jobs, spread evenly over rounds", "audit_tolerance": "number",
                  "failed_audit": "full refund of the audited job", "ban_length": "number" if self.L > 0 else "none", "holdback": "none",
                  "parameters": {"audit_tolerance": float(self.tol), **({"ban_length": int(self.L)} if self.L > 0 else {})}})
        return d

