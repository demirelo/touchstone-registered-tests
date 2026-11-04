"""H4: state-conditioned inflation with an own-service bid controller.

Only ProviderView and the injected T and L enter an action. The controller
retains its bid adjustment across identities, skips banned rounds, and uses
only the preceding round's own served count. There is no simulator access.
"""
from __future__ import annotations

from sim.mechanisms.base import Offer
from sim.policies.base import Action
from sim.policies.families import Family

BINARY: tuple[str, ...] = ("x", "clip")
__all__ = ("make_family", "BINARY")
_KNOBS = ("u0", "m0", "s", "d", "r", "w", "k_F", "k_T", "a_F", "n_P", "e_P", "b_gain", "b_target", "x", "clip")


class _Policy:
    name = "h4_service_feedback"

    def __init__(self, *, T, L, u0, m0, s, d, r, w, k_F, k_T, a_F, n_P, e_P, b_gain, b_target, x, clip):
        self.T, self.L = int(T), int(L)
        self.u0, self.m0, self.s = float(u0), float(m0), float(s)
        self.d, self.r, self.w = float(d), float(r), float(w)
        self.k_F, self.k_T = float(k_F), float(k_T)
        self.a_F, self.n_P, self.e_P = float(a_F), float(n_P), float(e_P)
        self.b_gain, self.b_target = float(b_gain), float(b_target)
        self.x, self.clip = int(x), int(clip)
        self.m, self.bid_adjustment = self.m0, 0.0
        self.creation, self.passes, self.seen = 0, 0, 0
        self.last_t, self.last_action = None, None
        self.eligible = {}

    def act(self, view):
        t, h, p = int(view.t), view.history, view.params
        if self.last_t == t:
            return self.last_action
        # Each observed round is folded once. A batch with any failure clears
        # the pass count, in the same way as the frozen credibility rule.
        for j in range(self.seen, t):
            failed = h.failed[j] > 0
            banned = h.banned_until[j] > j
            if failed:
                self.m *= 1.0 - self.d
                self.passes = 0
            else:
                self.passes += h.audited[j]
                if self.last_t is not None and not banned:
                    self.m = min(self.m0, self.m + self.r * self.m0)
            # The failure round was eligible even though enforcement banned it.
            if self.eligible[j] and self.b_gain:
                self.bid_adjustment = min(2.0, max(-0.95, self.bid_adjustment + self.b_gain * (h.served[j] / p.k - self.b_target)))
        self.seen = t
        exit_ = bool(self.x and h.failed and h.failed[-1] > 0)
        if exit_:
            self.creation, self.passes = t, 0
        lo = max(self.creation, t - self.L)
        served = sum(h.served[lo:t])
        audited = sum(h.audited[lo:t])
        exposed = served > 0 and audited / served > self.e_P
        if self.T - t <= self.L:
            k = self.k_T
        elif t - self.creation < self.a_F or self.passes < self.n_P or exposed:
            k = self.k_F
        else:
            k = 1.0
        effort = p.q_max * (1.0 - min(1.0, k * self.u0))
        claim = min(1.0, max(0.0, effort + k * self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        multiplier = max(0.0, 1.0 + self.w + self.bid_adjustment)
        action = Action(effort, Offer(claim, multiplier * (p.a + p.b * effort)), exit_)
        self.eligible[t] = exit_ or not h.banned_until or h.banned_until[-1] <= t
        self.last_t, self.last_action = t, action
        return action


def make_family(T: int, L: int) -> Family:
    bounds = {
        "u0": (0.0, 1.0), "m0": (0.0, 1.0), "s": (0.0, 0.3),
        "d": (0.0, 1.0), "r": (0.0, 0.2), "w": (0.0, 2.0),
        "k_F": (0.0, 1.0), "k_T": (0.0, 2.0), "a_F": (0.0, 60.0),
        "n_P": (0.0, 30.0), "e_P": (0.0, 1.0),
        "b_gain": (0.0, 0.5), "b_target": (0.0, 1.0),
    }
    return Family("H4", _KNOBS, bounds, lambda **knobs: _Policy(T=T, L=L, **knobs))
