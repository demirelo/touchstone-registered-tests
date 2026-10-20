"""Exploratory attackers (post-verdict, exploratory only; plan docs/superpowers/plans/2026-10-20-exploratory-attackers.md).

Six searchable families built from one two-mode action (an honest round or a D1-shaped cheat round) and a per-family
gate that decides when to cheat and when to replace the identity. Gates read only the ProviderView (the entity's own
history across identities, the round, its parameters, the identity id compared for equality) and two public constants:
the horizon T and the common ban length W = 10 of B2, B3, and R3. Nothing here is a registered family."""
from __future__ import annotations

from ..mechanisms.base import Offer
from .base import Action, ProviderView

T_PUBLIC = 200          # the locked market's horizon
W_PUBLIC = 10           # the ban length shared by the tuned B2, B3, and the frozen R3
FRESH, ESTABLISHED, TERMINAL = "fresh", "established", "terminal"


def cheat_action(view: ProviderView, u: float, m: float, s: float, w: float, clip: int) -> Action:
    """D1's FixedCheat arithmetic: effort q_max (1 - u), claim effort + m - s in [0, 1], clipped to effort if clip."""
    p = view.params
    effort = p.q_max * (1.0 - u)
    claim = min(1.0, max(0.0, effort + m - s))
    if clip:
        claim = min(claim, effort)
    return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + w) * (p.a + p.b * effort)))


def honest_action(view: ProviderView, w: float) -> Action:
    p = view.params
    return Action(effort=p.q_max, offer=Offer(claim=p.q_max, bid=(1.0 + w) * (p.a + p.b * p.q_max)))


def phase_of(age: int, t: int, T: int = T_PUBLIC, W: int = W_PUBLIC) -> str:
    if T - t <= W:
        return TERMINAL
    return FRESH if age < W else ESTABLISHED


class IdentityState:
    """The entity's own record of its identities. The harness asks for an action before it creates a replacement, so
    an exit noted in round t makes t the new identity's first round (age 0); the next view shows the new id (age 1).
    A ban return never resets age. Each history entry is applied once, to the identity that served in that round,
    with the effort and eligibility recorded when the action was chosen (before enforcement)."""

    def __init__(self, T: int = T_PUBLIC, W: int = W_PUBLIC) -> None:
        self.T, self.W = int(T), int(W)
        self.creation = 0
        self.ident: int | None = None
        self.t: int | None = None
        self.obs: list[dict] = []
        self._acted: dict[int, dict] = {}       # round -> {"effort", "eligible", "creation", "phase"}

    def begin_round(self, view: ProviderView) -> None:
        if self.t == view.t:
            return                               # idempotent within a round
        h = view.history
        while len(self.obs) < len(h.served):
            k = len(self.obs)
            a = self._acted.get(k, {"effort": view.params.q_max, "eligible": True, "creation": self.creation, "phase": phase_of(k - self.creation, k, self.T, self.W)})
            p = view.params
            served, payment, refunded = int(h.served[k]), float(h.payment[k]), float(h.refunded[k])
            self.obs.append({"t": k, "creation": a["creation"], "age": k - a["creation"], "phase": a["phase"],
                             "served": served, "audited": int(h.audited[k]), "failed": int(h.failed[k]),
                             "payment": payment, "refunded": refunded, "banned_until": int(h.banned_until[k]),
                             "effort": float(a["effort"]), "eligible": bool(a["eligible"]),
                             "profit": payment - refunded - served * (p.a + p.b * float(a["effort"]))})
        if self.ident is None:
            self.ident = view.identity
        elif view.identity != self.ident:
            self.ident = view.identity           # the creation round was set by note_exit in the exit round
        self.t = view.t

    def note_exit(self, t: int) -> None:
        self.creation = int(t)

    def age(self, t: int) -> int:
        return int(t) - self.creation

    def phase(self, t: int) -> str:
        return phase_of(self.age(t), t, self.T, self.W)

    def record_action(self, t: int, effort: float, eligible: bool) -> None:
        self._acted[int(t)] = {"effort": float(effort), "eligible": bool(eligible), "creation": self.creation, "phase": self.phase(t)}
