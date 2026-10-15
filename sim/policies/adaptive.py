from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class AdaptiveCheat:
    """D2 (spec 5.3). Markup state m_t: m_1 = m0; after a failed audit
    m <- m (1 - d); otherwise m <- min(m0, m + r m0); unchanged during a ban.
    One instance per entity per episode."""
    name = "adaptive_cheat"

    def __init__(self, u0: float, m0: float, s: float, d: float, r: float, w: float, clip: int) -> None:
        if not (0.0 <= u0 <= 1.0 and 0.0 <= m0 <= 1.0 and 0.0 <= s <= 0.3 and 0.0 <= d <= 1.0
                and 0.0 <= r <= 0.2 and 0.0 <= w <= 2.0):
            raise ValueError("D2 knob outside its domain")
        if isinstance(clip, bool) or clip not in (0, 1) or int(clip) != clip:
            raise ValueError("clip must be exactly 0 or 1")
        self.u0, self.m0, self.s, self.d, self.r, self.w, self.clip = float(u0), float(m0), float(s), float(d), float(r), float(w), int(clip)
        self.m = float(m0)
        self._last_t: int | None = None

    def _update_state(self, view: ProviderView) -> None:
        # Apply the recurrence once per round, using what happened last round.
        if self._last_t is not None and view.t > self._last_t and view.history.failed:
            banned_last = bool(view.history.banned_until) and view.history.banned_until[-1] > view.t - 1
            if view.history.failed[-1] > 0:
                self.m *= (1.0 - self.d)
            elif banned_last:
                pass   # banned and not audited last round: state unchanged
            else:
                self.m = min(self.m0, self.m + self.r * self.m0)
        self._last_t = view.t

    def act(self, view: ProviderView) -> Action:
        self._update_state(view)
        p = view.params
        effort = p.q_max * (1.0 - self.u0)
        claim = min(1.0, max(0.0, effort + self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + self.w) * (p.a + p.b * effort)))
