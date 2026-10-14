from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class FixedCheat:
    """D1 (spec 5.3). Knobs: u, m in [0,1]; s in [0,0.3]; w in [0,2]; clip in {0,1}."""
    name = "fixed_cheat"

    def __init__(self, u: float, m: float, s: float, w: float, clip: int) -> None:
        if not (0.0 <= u <= 1.0 and 0.0 <= m <= 1.0 and 0.0 <= s <= 0.3 and 0.0 <= w <= 2.0):
            raise ValueError("D1 knob outside its domain")
        if isinstance(clip, bool) or clip not in (0, 1) or int(clip) != clip:
            raise ValueError("clip must be exactly 0 or 1")
        self.u, self.m, self.s, self.w, self.clip = float(u), float(m), float(s), float(w), int(clip)

    def act(self, view: ProviderView) -> Action:
        p = view.params
        effort = p.q_max * (1.0 - self.u)
        claim = min(1.0, max(0.0, effort + self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + self.w) * (p.a + p.b * effort)))
