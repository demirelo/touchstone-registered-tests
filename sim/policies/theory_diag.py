"""Fixed diagnostic policy for the reset-deterrence checks (docs/theory/reset-deterrence.md section 8). Exploratory."""
from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView
from .exploratory import W_PUBLIC, IdentityState


class FixedShade:
    """Claim q_max and bid a + b q_max always; honest effort while the identity is younger than W (the replacement
    round included); effort q_max - delta once established; after a failed audit, replace the identity in the next
    round if `reset`, otherwise wait out the ban."""
    name = "fixed_shade"

    def __init__(self, delta: float, reset: bool) -> None:
        self.delta, self.reset = float(delta), bool(reset)
        self.state = IdentityState()
        self._last_t = None; self._last = None

    def act(self, view: ProviderView) -> Action:
        if self._last_t == view.t and self._last is not None:
            return self._last
        st = self.state; st.begin_round(view)
        ex = self.reset and view.t > 0 and bool(view.history.failed) and view.history.failed[-1] > 0
        if ex:
            st.note_exit(view.t)
        p = view.params
        effort = p.q_max if st.age(view.t) < W_PUBLIC else max(0.0, p.q_max - self.delta)
        a = Action(effort=effort, offer=Offer(claim=p.q_max, bid=p.a + p.b * p.q_max), exit=ex)
        st.record_action(view.t, effort, eligible=True)
        self._last_t, self._last = view.t, a
        return a
