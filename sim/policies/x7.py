"""X7-SC, the state-conditioned attack family (design 5.2). D2's markup recurrence, persisting across identities as in
D2+H3; phase multipliers for fresh, established, and terminal rounds, where a phase reads the identity's age and its own
passed audits; a reset after a failed audit unless the remaining horizon is at most h_R; a voluntary reset when the
identity's own audit rate over its last L rounds exceeds lambda. Reads only the provider view and the rule's public
constants T and L, injected at construction. Per round: (1) markup update from round t - 1, once; (2) failure trigger;
(3) voluntary trigger if no failure trigger; (4) exit and new creation round t; (5) phase of the identity that serves in
round t; (6) action. The harness asks for the action before it creates the replacement and applies the exit before the
offer, so the exit round's action is the replacement's."""
from __future__ import annotations

from scipy.stats import qmc

from ..mechanisms.base import Offer
from .base import Action, ProviderView
from .families import Family, exact_key

KNOBS = ("u0", "m0", "s", "d", "r", "w", "k_F", "k_T", "a_F", "n_P", "h_R", "a_R", "e_P", "lambda", "clip")
SOBOL_SEED = 20261028
X7_CORNER_COUNT = 771                                # distinct corners and projections for 15 knobs with scipy 1.18.1 (design 5.2)
FRESH, ESTABLISHED, TERMINAL = "fresh", "established", "terminal"


class X7Policy:
    name = "x7_state_conditioned"

    def __init__(self, u0, m0, s, d, r, w, k_F, k_T, a_F, n_P, h_R, a_R, e_P, lam, clip, T: int, L: int) -> None:
        self.T, self.L = int(T), int(L)
        vals = dict(u0=u0, m0=m0, s=s, d=d, r=r, w=w, k_F=k_F, k_T=k_T, a_F=a_F, n_P=n_P, h_R=h_R, a_R=a_R, e_P=e_P, lam=lam)
        dom = dict(u0=(0, 1), m0=(0, 1), s=(0, 0.3), d=(0, 1), r=(0, 0.2), w=(0, 2), k_F=(0, 1), k_T=(0, 2), a_F=(0, 60), n_P=(0, 30),
                   h_R=(0, self.T), a_R=(0, self.T), e_P=(0, 1), lam=(0, 1))
        for k, v in vals.items():
            if not (dom[k][0] <= float(v) <= dom[k][1]):
                raise ValueError(f"X7-SC knob {k} outside its domain")
        if isinstance(clip, bool) or clip not in (0, 1) or int(clip) != clip:
            raise ValueError("clip must be exactly 0 or 1")
        for k, v in vals.items():
            setattr(self, k, float(v))
        self.clip = int(clip)
        self.m = float(m0)
        self.c = 0                                   # creation round of the current identity
        self.p_own = 0                               # passes since the identity's last failure (design draft 7, 5.2)
        self._p_upto = 0                             # rounds of history already folded into p_own
        self.waiting = False                         # a failure was rejected by the age gate and the identity has not served since
        self._last_t: int | None = None
        self._last: Action | None = None
        self.resets_failure = self.resets_voluntary = 0
        self.last_phase: str | None = None

    def _update_markup(self, view: ProviderView) -> None:
        h = view.history
        if self._last_t is not None and view.t > self._last_t and h.failed:
            banned_last = bool(h.banned_until) and h.banned_until[-1] > view.t - 1
            if h.failed[-1] > 0:
                self.m *= (1.0 - self.d)
            elif not banned_last:
                self.m = min(self.m0, self.m + self.r * self.m0)

    def _window(self, view: ProviderView, lo: int) -> tuple[int, int, int]:
        h, t = view.history, view.t
        rng = range(max(lo, 0), t)
        return sum(h.served[k] for k in rng), sum(h.audited[k] for k in rng), sum(h.failed[k] for k in rng)

    def _update_p_own(self, view: ProviderView) -> None:
        """Batch update of the identity's pass count after each round's audit results, as C's credibility state."""
        h = view.history
        for k in range(max(self._p_upto, self.c), view.t):
            self.p_own = 0 if h.failed[k] > 0 else self.p_own + (h.audited[k] - h.failed[k])
        self._p_upto = max(self._p_upto, view.t)

    def act(self, view: ProviderView) -> Action:
        t = int(view.t)
        if self._last_t == t and self._last is not None:
            return self._last
        self._update_markup(view)
        self._update_p_own(view)
        h = view.history
        exit_ = False
        failed_last = bool(h.failed) and h.failed[-1] > 0
        if self.waiting and h.served and h.served[-1] >= 1 and not failed_last:
            self.waiting = False                     # the identity has served again after waiting out its ban
        banned_now = bool(h.banned_until) and h.banned_until[-1] > t
        if failed_last and self.T - t > self.h_R and (t - self.c) < self.a_R:
            exit_ = True; self.resets_failure += 1
        elif failed_last and self.T - t > self.h_R:
            self.waiting = True                      # the age gate rejected the reset: wait, keep age and pass history
        elif not self.waiting and not banned_now:
            served, audited, _ = self._window(view, max(self.c, t - self.L))
            if served >= 1 and audited / served > self.lam:
                exit_ = True; self.resets_voluntary += 1
        if exit_:
            self.c = t; self.p_own = 0; self._p_upto = t; self.waiting = False
        served_w, audited_w, _ = self._window(view, max(self.c, t - self.L))
        exposed = served_w >= 1 and audited_w / served_w > self.e_P
        if self.T - t <= self.L:
            phase = TERMINAL
        elif (t - self.c) < self.a_F or self.p_own < self.n_P or exposed:
            phase = FRESH
        else:
            phase = ESTABLISHED
        k = {FRESH: self.k_F, ESTABLISHED: 1.0, TERMINAL: self.k_T}[phase]
        p = view.params
        effort = p.q_max * (1.0 - min(1.0, k * self.u0))
        claim = min(1.0, max(0.0, effort + k * self.m - self.s))
        if self.clip:
            claim = min(claim, effort)
        self.last_phase, self._last_t = phase, t
        self._last = Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + self.w) * (p.a + p.b * effort)), exit=exit_)
        return self._last


def x7_family(T: int, L: int) -> Family:
    bounds = {"u0": (0.0, 1.0), "m0": (0.0, 1.0), "s": (0.0, 0.3), "d": (0.0, 1.0), "r": (0.0, 0.2), "w": (0.0, 2.0), "k_F": (0.0, 1.0),
              "k_T": (0.0, 2.0), "a_F": (0.0, 60.0), "n_P": (0.0, 30.0), "h_R": (0.0, float(T)), "a_R": (0.0, float(T)), "e_P": (0.0, 1.0),
              "lambda": (0.0, 1.0)}

    def factory(**k):
        k = dict(k); k["lam"] = k.pop("lambda")
        return X7Policy(**k, T=T, L=L)
    return Family("X7-SC", KNOBS, bounds, factory)


def embed_h3(knobs: dict, T: int) -> dict:
    """D2+H3 knobs (with x) to the X7-SC point with identical behaviour."""
    return {"u0": knobs["u0"], "m0": knobs["m0"], "s": knobs["s"], "d": knobs["d"], "r": knobs["r"], "w": knobs["w"], "k_F": 1.0,
            "k_T": 1.0, "a_F": 0.0, "n_P": 0.0, "h_R": 0.0 if int(knobs["x"]) else float(T), "a_R": float(T), "e_P": 1.0, "lambda": 1.0,
            "clip": knobs["clip"]}


def _corner(fam: Family, bits) -> dict:
    return {n: (int(b) if fam.is_binary(n) else float(fam.bounds[n][int(b)])) for n, b in zip(fam.knobs, bits)}


def x7_corners(fam: Family) -> list[dict]:
    """For any family (X7-SC and H4, design draft 7): 512 scrambled-Sobol corners (bit 1 when a coordinate is >= 0.5), de-duplicated in order, then the all-low and
    all-high corners if absent (a bounded diagnostic, not exhaustive coverage)."""
    pts = qmc.Sobol(d=len(fam.knobs), scramble=True, seed=SOBOL_SEED).random_base2(9)
    out, seen = [], set()
    for row in pts:
        k = _corner(fam, row >= 0.5); key = exact_key(k)
        if key not in seen:
            seen.add(key); out.append(k)
    for bits in ([0] * len(fam.knobs), [1] * len(fam.knobs)):
        k = _corner(fam, bits); key = exact_key(k)
        if key not in seen:
            seen.add(key); out.append(k)
    return out


def corner_vectors(fam: Family) -> list[dict]:
    """The corners and their truthful projections, de-duplicated by exact key across both."""
    out, seen = [], set()
    for k in x7_corners(fam) + [fam.project(c) for c in x7_corners(fam)]:
        key = exact_key(k)
        if key not in seen:
            seen.add(key); out.append(k)
    return out
