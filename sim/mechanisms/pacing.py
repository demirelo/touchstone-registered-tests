"""Audit pacing shared by the revision-program rules (design 3.2, 3.4): B3's spread count (S = 0) and R3's
terminal-reserve schedule with carry (S = 1), with R3's reserve min(J L, A_tot) or R4's min(J L, floor(A_tot / 2))."""
from __future__ import annotations

import math

import numpy as np

from .audit_random import spread_audit_count
from .base import StateView

RESERVES = ("full", "half")


def spread_count(view: StateView, T: int, cap_per_round: int, n_served: int) -> int:
    return spread_audit_count(view.audits_left, view.t, T, n_served, cap_per_round, view.audit_u)


def spread_cap(cfg) -> int:
    return max(1, int(np.floor(2.0 * cfg.budget / (cfg.T * cfg.alpha)))) if cfg.alpha > 0 else 0


class ReservePacing:
    """R3's schedule exactly as `Proposed.audit` computes it: terminal rounds t >= T - L audit every served job while
    audits remain; earlier rounds get C(t) - C(t - 1) plus the carry, C(t) = floor(E (t + 1) / (T - L)), E = A_tot - reserve.
    `count` assumes the caller audits exactly the returned number and updates `quota_carry` accordingly."""

    def __init__(self, reserve: str, L: int) -> None:
        if reserve not in RESERVES:
            raise ValueError(f"reserve must be one of {RESERVES}")
        self.reserve, self.L = reserve, int(L)
        self.T, self.J, self.A_tot = 1, 1, 0

    def bind(self, cfg) -> None:
        self.T, self.J = int(cfg.T), int(cfg.J)
        self.A_tot = int(math.floor(cfg.budget / cfg.alpha + 1e-12)) if cfg.alpha > 0 else 0

    def reserve_size(self) -> int:
        cap = self.A_tot if self.reserve == "full" else self.A_tot // 2
        return min(self.J * self.L, cap)

    def terminal(self, t: int) -> bool:
        return int(t) >= self.T - self.L

    def count(self, view: StateView, n_served: int) -> int:
        t = int(view.t); carry = int(view.memory.get("quota_carry", 0))
        if self.terminal(t):
            k_avail = int(min(n_served, self.A_tot))
        else:
            E, er = self.A_tot - self.reserve_size(), self.T - self.L
            c = lambda u: 0 if u < 0 else (E * (u + 1)) // er
            k_avail = c(t) - c(t - 1) + carry
        k = max(0, min(k_avail, int(n_served), int(view.audits_left)))
        view.memory["quota_carry"] = 0 if self.terminal(t) else int(k_avail - k)
        return k
