from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView


class Twin:
    """Truthful twin: same policy, market-facing claim clipped to <= effort."""

    def __init__(self, policy) -> None:
        self.policy = policy
        self.name = f"twin({getattr(policy, 'name', 'policy')})"

    def act(self, view: ProviderView) -> Action:
        a = self.policy.act(view)
        if a.offer is None:
            return a
        return Action(effort=a.effort, offer=Offer(claim=min(a.offer.claim, a.effort), bid=a.offer.bid), exit=a.exit)
