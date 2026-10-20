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


# ---- gated policies ----------------------------------------------------------------------------------------------------

def _check_cheat_knobs(u, m, s, w, clip) -> None:
    if not (0.0 <= u <= 1.0 and 0.0 <= m <= 1.0 and 0.0 <= s <= 0.3 and 0.0 <= w <= 2.0):
        raise ValueError("cheat knob outside its domain")
    _check_binary(clip, "clip")


def _check_binary(v, name) -> None:
    if isinstance(v, bool) or v not in (0, 1) or int(v) != v:
        raise ValueError(f"{name} must be exactly 0 or 1")


def _failed_last(view: ProviderView) -> bool:
    return bool(view.history.failed) and view.history.failed[-1] > 0


class _Gated:
    """One instance per entity per episode. Each round: apply last round's observation once, learn, decide an exit,
    then choose the honest or the cheat action under the (possibly new) identity's phase."""
    name = "gated"
    exit_knob = False

    def __init__(self, u: float, m: float, s: float, w: float, clip: int) -> None:
        _check_cheat_knobs(u, m, s, w, clip)
        self.u, self.m, self.s, self.w, self.clip = float(u), float(m), float(s), float(w), int(clip)
        self.state = IdentityState()
        self._last_t: int | None = None
        self._last: Action | None = None
        self._seen = 0

    # hooks
    def learn(self, o: dict) -> None: ...
    def on_exit(self, t: int) -> None: ...
    def want_exit(self, view: ProviderView) -> bool:
        return False
    def want_cheat(self, view: ProviderView, phase: str) -> bool:
        return True

    def act(self, view: ProviderView) -> Action:
        if self._last_t == view.t and self._last is not None:
            return self._last
        st = self.state
        st.begin_round(view)
        while self._seen < len(st.obs):
            self.learn(st.obs[self._seen]); self._seen += 1
        ex = view.t > 0 and self.want_exit(view)
        if ex:
            st.note_exit(view.t); self.on_exit(view.t)
        banned = (not ex) and bool(view.history.banned_until) and view.history.banned_until[-1] > view.t
        a = (cheat_action(view, self.u, self.m, self.s, self.w, self.clip) if self.want_cheat(view, st.phase(view.t))
             else honest_action(view, self.w))
        st.record_action(view.t, a.effort, eligible=not banned)
        self._last_t, self._last = view.t, Action(effort=a.effort, offer=a.offer, exit=ex)
        return self._last


class X1Policy(_Gated):
    """Audit hazard: per-phase audited-per-served estimate shrunk toward the pooled rate; cheat below theta."""
    name = "x1_audit_hazard"

    def __init__(self, u, m, s, w, theta, kappa, x, clip):
        super().__init__(u, m, s, w, clip); _check_binary(x, "x")
        self.theta, self.kappa, self.x = float(theta), float(kappa), int(x)
        self.n = {FRESH: [0, 0], ESTABLISHED: [0, 0], TERMINAL: [0, 0]}     # phase -> [served, audited]

    def learn(self, o):
        self.n[o["phase"]][0] += o["served"]; self.n[o["phase"]][1] += o["audited"]

    def hazard(self, phase: str) -> float:
        sv = sum(v[0] for v in self.n.values()); au = sum(v[1] for v in self.n.values())
        pool = (au + 1.0) / (sv + 1.0)
        sb, ab = self.n[phase]
        if sb + self.kappa == 0:
            return pool
        return (ab + self.kappa * pool) / (sb + self.kappa)

    def want_exit(self, view):
        return bool(self.x) and _failed_last(view)

    def want_cheat(self, view, phase):
        return self.hazard(phase) < self.theta


class X2Policy(_Gated):
    """Tranche signal: one EWMA per phase of the per-round audited fraction; cheat below theta."""
    name = "x2_tranche_signal"

    def __init__(self, u, m, s, w, theta, h, x, clip):
        super().__init__(u, m, s, w, clip); _check_binary(x, "x")
        self.theta, self.h, self.x = float(theta), float(h), int(x)
        self.lam = 0.5 ** (1.0 / self.h)
        self.ewma = {FRESH: 1.0, ESTABLISHED: 1.0, TERMINAL: 1.0}

    def learn(self, o):
        if o["served"] > 0:
            ph = o["phase"]; self.ewma[ph] = self.lam * self.ewma[ph] + (1 - self.lam) * (o["audited"] / o["served"])

    def on_exit(self, t):
        self.ewma[FRESH] = 1.0

    def want_exit(self, view):
        return bool(self.x) and _failed_last(view)

    def want_cheat(self, view, phase):
        return self.ewma[phase] < self.theta


class X3Policy(_Gated):
    """Horizon timing: cheat inside [t0 T, (t0 + span) T), and in the last W rounds if z; never exits."""
    name = "x3_horizon_timing"

    def __init__(self, u, m, s, w, t0, span, z, clip):
        super().__init__(u, m, s, w, clip); _check_binary(z, "z")
        self.t0, self.span, self.z = float(t0), float(span), int(z)

    def in_window(self, t: int) -> bool:
        T = T_PUBLIC
        return self.t0 * T <= t < min(T, (self.t0 + self.span) * T) or (bool(self.z) and t >= T - W_PUBLIC)

    def want_cheat(self, view, phase):
        return self.in_window(view.t)


class X4Policy(_Gated):
    """Reset option: honest while younger than n_age, cheat afterwards; after a failed audit that bans until B, exit
    if x and (lambda = 0, or a proxy value is undefined, or (min(B, T) - t) V_e > lambda W (V_e - V_f))."""
    name = "x4_reset_option"
    HALF_LIFE = 10.0

    def __init__(self, u, m, s, w, clip, n_age, x, **kw):
        lam = kw.pop("lambda")
        if kw:
            raise TypeError(f"unexpected knobs {sorted(kw)}")
        super().__init__(u, m, s, w, clip); _check_binary(x, "x")
        self.lam_knob, self.n_age, self.x = float(lam), int(round(float(n_age))), int(x)
        self.decay = 0.5 ** (1.0 / self.HALF_LIFE)
        self.V_e = self.V_f = None
        self.n_updates_e = self.n_updates_f = 0

    def learn(self, o):
        if o["served"] <= 0 or o["phase"] == TERMINAL:
            return
        if o["phase"] == ESTABLISHED:
            self.V_e = o["profit"] if self.V_e is None else self.decay * self.V_e + (1 - self.decay) * o["profit"]; self.n_updates_e += 1
        else:
            self.V_f = o["profit"] if self.V_f is None else self.decay * self.V_f + (1 - self.decay) * o["profit"]; self.n_updates_f += 1

    def want_exit(self, view):
        if not (self.x and _failed_last(view)):
            return False
        if self.lam_knob == 0.0 or self.V_e is None or self.V_f is None:
            return True
        B = int(view.history.banned_until[-1])
        remaining = max(0, min(B, T_PUBLIC) - view.t)
        return remaining * max(self.V_e, 0.0) > self.lam_knob * W_PUBLIC * max(self.V_e - self.V_f, 0.0)

    def want_cheat(self, view, phase):
        return self.state.age(view.t) >= self.n_age


def _x4_factory(**k):
    return X4Policy(**k)


class X5Policy(_Gated):
    """Aging: honest while younger than n_age, cheat afterwards; exit after a failed audit if x."""
    name = "x5_aging"

    def __init__(self, u, m, s, w, n_age, x, clip):
        super().__init__(u, m, s, w, clip); _check_binary(x, "x")
        self.n_age, self.x = int(round(float(n_age))), int(x)

    def want_exit(self, view):
        return bool(self.x) and _failed_last(view)

    def want_cheat(self, view, phase):
        return self.state.age(view.t) >= self.n_age


def scheduled_resets(P, c: int, T: int = T_PUBLIC, staggered: bool = False) -> list[list[int]]:
    """Per member, the scheduled reset rounds: K = floor((T - 1) / P') with P' = round(P); synchronised members reset at
    k P', staggered member j at k P' - floor(j P' / c), k = 1..K (equal counts; distinct across members iff P' >= c)."""
    Pp = max(1, int(round(float(P)))); K = (int(T) - 1) // Pp
    return [[k * Pp - ((j * Pp) // c if staggered else 0) for k in range(1, K + 1)] for j in range(int(c))]


def reset_overlap(schedules: list[list[int]]) -> int:
    from collections import Counter
    cnt = Counter(t for s in schedules for t in set(s))
    return sum(1 for v in cnt.values() if v >= 2)


class X6Policy(_Gated):
    """Simultaneous entrants (one coalition member): cheat when not banned; if y, exit at the member's scheduled reset
    rounds; if x, also after its own failed audit. Counts scheduled and failure-triggered resets separately."""
    name = "x6_simultaneous_entrants"

    def __init__(self, u, m, s, w, P, x, y, clip, member: int = 0, c: int = 1, staggered: bool = False):
        super().__init__(u, m, s, w, clip); _check_binary(x, "x"); _check_binary(y, "y")
        if not (1.0 <= float(P) <= 50.0):
            raise ValueError("P outside [1, 50]")
        self.P, self.x, self.y = float(P), int(x), int(y)
        self.sched = set(scheduled_resets(P, c, T_PUBLIC, staggered)[member]) if self.y else set()
        self.resets_scheduled = self.resets_failure = 0

    def want_exit(self, view):
        if view.t in self.sched:
            self.resets_scheduled += 1; return True
        if self.x and _failed_last(view):
            self.resets_failure += 1; return True
        return False


def coalition_members(cfg, focal: int, c: int) -> tuple[int, ...]:
    """The focal entity and the c - 1 entities nearest to it in the positions score order, ties to the lower index."""
    score = [p.b * p.q_max for p in cfg.providers]
    order = sorted(range(cfg.N), key=lambda i: (score[i], i)); r = order.index(focal)
    others = sorted((e for e in range(cfg.N) if e != focal), key=lambda e: (abs(order.index(e) - r), e))
    return (focal,) + tuple(others[: int(c) - 1])


from .families import Family    # noqa: E402

_CHEAT = {"u": (0.0, 1.0), "m": (0.0, 1.0), "s": (0.0, 0.3), "w": (0.0, 2.0)}
EXPLORATORY_FAMILIES = {
    "X1-AH": Family("X1-AH", ("u", "m", "s", "w", "theta", "kappa", "x", "clip"), {**_CHEAT, "theta": (0.0, 1.0), "kappa": (0.0, 50.0)}, X1Policy),
    "X2-TD": Family("X2-TD", ("u", "m", "s", "w", "theta", "h", "x", "clip"), {**_CHEAT, "theta": (0.0, 0.6), "h": (1.0, 30.0)}, X2Policy),
    "X3-HS": Family("X3-HS", ("u", "m", "s", "w", "t0", "span", "z", "clip"), {**_CHEAT, "t0": (0.0, 1.0), "span": (0.0, 1.0)}, X3Policy),
    "X4-RO": Family("X4-RO", ("u", "m", "s", "w", "lambda", "n_age", "x", "clip"), {**_CHEAT, "lambda": (0.0, 3.0), "n_age": (0.0, 40.0)}, _x4_factory),
    "X5-AG": Family("X5-AG", ("u", "m", "s", "w", "n_age", "x", "clip"), {**_CHEAT, "n_age": (0.0, 40.0)}, X5Policy),
    "X6-SE": Family("X6-SE", ("u", "m", "s", "w", "P", "x", "y", "clip"), {**_CHEAT, "P": (1.0, 50.0)}, X6Policy),
}
