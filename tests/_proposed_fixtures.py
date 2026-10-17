"""Fixtures for the proposed rule's contract tests (amendment 2, task A5): explicit StateViews and a tiny episode runner
that captures the rule's memory. Test-only code; the rule module never imports this."""
from __future__ import annotations

import numpy as np

from sim.mechanisms.base import Consequences, Mechanism, Offer, StateView


class RecordingView:
    """Builds StateViews with explicit audit_key, capacity, banned_until, escrow, tie_key, and memory."""

    def __init__(self, N: int, J: int, T: int, seed: int = 0) -> None:
        self.N, self.J, self.T = int(N), int(J), int(T)
        self.rng = np.random.default_rng(seed)

    def view(self, t: int, *, audits_left: int, memory: dict | None = None, audit_key=None, capacity=None, banned_until=None, escrow=None,
             tie_key=None, audit_u: float = 0.5, N: int | None = None, history=()) -> StateView:
        N = self.N if N is None else int(N)
        mem = {} if memory is None else memory
        tk = self.rng.random((self.J, N)) if tie_key is None else np.asarray(tie_key, dtype=float)
        mem["tie_key"] = tk
        return StateView(t=int(t), T=self.T, N=N, audits_left=int(audits_left), audit_u=float(audit_u),
                         audit_key=self.rng.random(self.J) if audit_key is None else np.asarray(audit_key, dtype=float),
                         banned_until=np.zeros(N, dtype=np.int64) if banned_until is None else np.asarray(banned_until, dtype=np.int64),
                         bond=np.zeros(N), capacity=np.full(N, 6, dtype=np.int64) if capacity is None else np.asarray(capacity, dtype=np.int64),
                         escrow={} if escrow is None else dict(escrow), history=tuple(history), memory=mem)


def offers_for(claims: dict[int, float], bids: dict[int, float] | None = None) -> dict[int, Offer]:
    return {i: Offer(claim=float(c), bid=float((bids or {}).get(i, 0.0))) for i, c in claims.items()}


class MemorySpy(Mechanism):
    """Delegates every call to the wrapped rule and keeps a reference to the episode's memory dict."""

    def __init__(self, rule) -> None:
        self.rule = rule; self.name = rule.name; self.tol = rule.tol; self.memory = None
        self.prices = getattr(rule, "prices", None)

    def bind(self, cfg) -> None:
        self.rule.bind(cfg)

    def allocate(self, values_t, offers, view):
        self.memory = view.memory
        return self.rule.allocate(values_t, offers, view)

    def price(self, assignment, values_t, offers, view):
        return self.rule.price(assignment, values_t, offers, view)

    def audit(self, assignment, view):
        return self.rule.audit(assignment, view)

    def enforce(self, records, view) -> Consequences:
        return self.rule.enforce(records, view)

    def describe(self):
        return self.rule.describe()


def run_with_memory(cfg, rule, policies, seed: int):
    from sim.market import run_episode
    spy = MemorySpy(rule)
    res = run_episode(cfg, spy, policies, seed)
    return res, spy.memory
