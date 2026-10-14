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

    def describe(self) -> dict[str, str]:
        d = PostedPrices.describe(self)
        d.update({"audit_selection": "uniform random among served jobs, spread schedule",
                  "audit_tolerance": f"{self.tol}", "failed_audit": "full refund",
                  "ban_length": f"{self.L}", "holdback": "none"})
        return d
