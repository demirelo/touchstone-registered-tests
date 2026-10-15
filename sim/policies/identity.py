from __future__ import annotations

from dataclasses import replace

from .base import Action, ProviderView


class IdentityReplacement:
    """H3 (spec 6.2): behave like the wrapped policy, and exit in the round
    after a failed audit so the entity re-enters under a fresh identity in that
    round (exits take effect when made, Task 2)."""

    def __init__(self, policy) -> None:
        self.policy = policy
        self.name = f"h3({getattr(policy, 'name', 'policy')})"

    def act(self, view: ProviderView) -> Action:
        a = self.policy.act(view)
        failed_last = bool(view.history.failed) and view.history.failed[-1] > 0
        return Action(effort=a.effort, offer=a.offer, exit=a.exit or failed_last)


def h3_family(family):
    """The family with one more binary knob x: x = 1 wraps the policy in IdentityReplacement,
    x = 0 leaves it unwrapped, so the honest point (x = 0, clip = 1) is honest-max."""
    base_factory = family.factory

    def factory(**k):
        k = dict(k); x = int(k.pop("x"))
        p = base_factory(**k)
        return IdentityReplacement(p) if x else p
    knobs = tuple(n for n in family.knobs if n != "clip") + ("x", "clip")
    return replace(family, name=f"{family.name}+H3", knobs=knobs, factory=factory)
