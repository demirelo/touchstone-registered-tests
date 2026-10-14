from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class HonestMax:
    name = "honest_max"

    def act(self, view: ProviderView) -> Action:
        p = view.params
        return Action(effort=p.q_max, offer=Offer(claim=p.q_max, bid=p.a + p.b * p.q_max))
