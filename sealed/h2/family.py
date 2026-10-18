"""Held-out family H2 (spec 6.1), written by the custodian session.

H2 "audit-aware adaptive cheat with demand-responsive pricing". It extends the
development family D2 with two channels that D2 never reads:

  * g, audit sensitivity: the policy estimates the audit frequency of its own
    served jobs, a_hat = (jobs audited so far) / (jobs served so far), from
    every audit, passed or failed (0 before any job is served), and scales its
    markup down to m_eff = m_t (1 - g a_hat).
  * h, demand response: the bid markup is a state w_t with w_1 = w. After a round
    in which the entity was not banned and served no job, w_{t+1} = w_t (1 - h);
    after a round in which it served its full capacity k,
    w_{t+1} = min(w, w_t + h w); otherwise w_t is unchanged.

Everything else is D2: effort q = q_max (1 - u0); markup state m_t with
m_1 = m0, m <- m (1 - d) after a round with a failed audit, unchanged after a
banned round without a failure, else m <- min(m0, m + r m0); claim
c = min(1, max(0, q + m_eff - s)), so the shading knob s permits claims below
effort; with clip = 1 the claim is min(c, q); bid = (1 + w_t)(a + b q). The
policy never abstains and never exits.

Knobs, in search order (bounded knobs, then the binary clip last):
  u0, m0 in [0, 1]; s in [0, 0.3]; d in [0, 1]; r in [0, 0.2]; w in [0, 2];
  g in [0, 1]; h in [0, 1]; clip in {0, 1}.

Containment: H2 contains D2 through embed_d2 (g = h = 0), and contains its
own twin (clip fixed at 1) by construction. The honest point (every bounded
knob at its lower bound, clip = 1) reproduces honest-max. Registered starts,
transform, projection, corners, and the exact and rounded keys are those of
sim.policies.families (experiments/families.md).
"""
from sim.mechanisms.base import Offer
from sim.policies.base import Action
from sim.policies.families import Family, exact_key, knob_key

__all__ = ["H2", "CONTAINMENT", "embed_d2", "AuditAwareCheat", "exact_key", "knob_key", "KNOBS", "BOUNDS"]

KNOBS = ("u0", "m0", "s", "d", "r", "w", "g", "h", "clip")
BOUNDS = {"u0": (0.0, 1.0), "m0": (0.0, 1.0), "s": (0.0, 0.3), "d": (0.0, 1.0), "r": (0.0, 0.2),
          "w": (0.0, 2.0), "g": (0.0, 1.0), "h": (0.0, 1.0)}


class AuditAwareCheat:
    """One instance per entity per episode (Family.make returns a fresh one)."""
    name = "audit_aware_cheat"

    def __init__(self, u0, m0, s, d, r, w, g, h, clip):
        vals = {"u0": u0, "m0": m0, "s": s, "d": d, "r": r, "w": w, "g": g, "h": h}
        for k, v in vals.items():
            lo, hi = BOUNDS[k]
            if isinstance(v, bool) or not (lo <= float(v) <= hi):
                raise ValueError(f"H2 knob {k}={v!r} outside its domain [{lo}, {hi}]")
        if isinstance(clip, bool) or clip not in (0, 1) or int(clip) != clip:
            raise ValueError("clip must be exactly 0 or 1")
        self.u0, self.m0, self.s, self.d, self.r = float(u0), float(m0), float(s), float(d), float(r)
        self.w, self.g, self.h, self.clip = float(w), float(g), float(h), int(clip)
        self.m = float(m0)
        self.w_t = float(w)
        self._last_t = None

    def _update_state(self, view) -> None:
        # Once per round, from what happened in the previous round (index -1 of the history).
        hist = view.history
        if self._last_t is not None and view.t > self._last_t and hist.failed:
            banned_last = bool(hist.banned_until) and hist.banned_until[-1] > view.t - 1
            if hist.failed[-1] > 0:
                self.m *= (1.0 - self.d)
            elif banned_last:
                pass
            else:
                self.m = min(self.m0, self.m + self.r * self.m0)
            banned_during_last = len(hist.banned_until) >= 2 and hist.banned_until[-2] > view.t - 1
            if not banned_during_last:
                if hist.served[-1] == 0:
                    self.w_t *= (1.0 - self.h)
                elif hist.served[-1] >= int(view.params.k):
                    self.w_t = min(self.w, self.w_t + self.h * self.w)
        self._last_t = view.t

    def _audit_rate(self, view) -> float:
        served = sum(view.history.served)
        if served <= 0:
            return 0.0
        return min(1.0, max(0.0, sum(view.history.audited) / served))

    def act(self, view) -> Action:
        self._update_state(view)
        p = view.params
        effort = p.q_max * (1.0 - self.u0)
        m_eff = self.m * (1.0 - self.g * self._audit_rate(view))
        claim = min(1.0, max(0.0, effort + m_eff - self.s))
        if self.clip:
            claim = min(claim, effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + self.w_t) * (p.a + p.b * effort)))


H2 = Family("H2", KNOBS, dict(BOUNDS), AuditAwareCheat)

CONTAINMENT = ("contains D2: embed_d2 sets g = h = 0 and copies u0, m0, s, d, r, w, clip, which reproduces D2 exactly; "
               "H2 also reads its passed audits and its served counts, and keeps a bid-markup state, which D2 cannot")


def embed_d2(knobs: dict) -> dict:
    """The H2 point that behaves exactly like the given D2 point in every round."""
    return {"u0": float(knobs["u0"]), "m0": float(knobs["m0"]), "s": float(knobs["s"]), "d": float(knobs["d"]),
            "r": float(knobs["r"]), "w": float(knobs["w"]), "g": 0.0, "h": 0.0, "clip": int(knobs["clip"])}
