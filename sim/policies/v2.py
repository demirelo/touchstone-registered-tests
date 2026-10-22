"""X5-AG/v2 and X6-SE/v2 (design 5.2): the exploratory aging and coalition families with the rule's public horizon T
and ban length L injected, where `sim/policies/exploratory.py` (frozen) assumes T = 200 and W = 10. X5-AG/v2 widens
n_age to [0, 60] so it covers L = 50. Behaviour at T = 200, L = 10 equals the exploratory families (tested)."""
from __future__ import annotations

from dataclasses import replace

from .exploratory import EXPLORATORY_FAMILIES, IdentityState, X5Policy, X6Policy, coalition_members, scheduled_resets
from .families import Family


class X5v2(X5Policy):
    def __init__(self, u, m, s, w, n_age, x, clip, T: int = 200, L: int = 10):
        super().__init__(u, m, s, w, n_age, x, clip)
        self.state = IdentityState(T, L)


class X6v2(X6Policy):
    def __init__(self, u, m, s, w, P, x, y, clip, member: int = 0, c: int = 1, staggered: bool = False, T: int = 200, L: int = 10):
        super().__init__(u, m, s, w, P, x, y, clip, member=member, c=c, staggered=staggered)
        self.state = IdentityState(T, L)
        self.sched = set(scheduled_resets(P, c, T, staggered)[member]) if self.y else set()


def x5v2_family(T: int, L: int) -> Family:
    base = EXPLORATORY_FAMILIES["X5-AG"]
    return replace(base, name="X5-AG/v2", bounds={**base.bounds, "n_age": (0.0, 60.0)}, factory=lambda **k: X5v2(**k, T=T, L=L))


def x6v2_family(T: int, L: int) -> Family:
    base = EXPLORATORY_FAMILIES["X6-SE"]
    return replace(base, name="X6-SE/v2", factory=lambda **k: X6v2(**k, T=T, L=L))


def x6v2_member(knobs: dict, member: int, c: int, staggered: bool, T: int, L: int) -> X6v2:
    return X6v2(**knobs, member=member, c=c, staggered=staggered, T=T, L=L)


def x6v2_members(cfg, focal: int, c: int) -> tuple[int, ...]:
    return coalition_members(cfg, focal, c)
