"""X8-DB (design draft 7, 5.2): a role-asymmetric coalition at c = 2. Member 0 (the focal provider) is the beneficiary,
member 1 the decoy. The decoy replaces its identity when it failed an audit in the previous round or when its identity's
integer age reaches the real threshold n_D (no rounding); the schedule clock restarts after every replacement. The
beneficiary never replaces its identity; if g_B = 1 it shades only while the decoy identity that offers in the round is
younger than L, and plays honest-max otherwise. Both members share one coordinator, which computes round t once from the
members' own histories, so the result does not depend on which member the harness asks first."""
from __future__ import annotations

from .base import Action, Offer, ProviderView
from .families import Family
from .honest import HonestMax

X8_KNOBS = ("n_D", "u_D", "w_D", "u_B", "m_B", "s_B", "w_B", "g_B", "clip")


class X8Pair:
    """The shared coordinator: the decoy's identity state and the round's gate, computed once per round."""

    def __init__(self, knobs: dict, T: int, L: int) -> None:
        k = dict(knobs); self.T, self.L = int(T), int(L)
        for name, (lo, hi) in x8_bounds(self.L).items():
            if not (lo <= float(k[name]) <= hi):
                raise ValueError(f"X8-DB knob {name} outside its domain")
        for name in ("g_B", "clip"):
            if isinstance(k[name], bool) or k[name] not in (0, 1) or int(k[name]) != k[name]:
                raise ValueError(f"{name} must be exactly 0 or 1")
        self.k = k
        self.c_D = 0                                  # creation round of the decoy's current identity
        self.histories: dict[str, object] = {}        # each member's own (live) history, by role
        self.seen: set[int] = set()                   # provider indices whose views the coordinator received
        self._round: int | None = None
        self.decoy_exit = False; self.shade = True; self.replacements = 0

    def observe(self, role: str, view: ProviderView) -> None:
        self.histories[role] = view.history; self.seen.add(int(view.i))
        t = int(view.t)
        if self._round == t:
            return
        self._round = t
        hd = self.histories.get("decoy")
        failed = hd is not None and bool(hd.failed) and len(hd.failed) == t and hd.failed[-1] > 0
        self.decoy_exit = t > 0 and (failed or (t - self.c_D) >= float(self.k["n_D"]))
        if self.decoy_exit:
            self.c_D = t; self.replacements += 1
        self.shade = (not int(self.k["g_B"])) or (t - self.c_D) < self.L


class X8Member:
    name = "x8_decoy_beneficiary"

    def __init__(self, pair: X8Pair, role: str) -> None:
        if role not in ("beneficiary", "decoy"):
            raise ValueError(role)
        self.pair, self.role = pair, role

    def act(self, view: ProviderView) -> Action:
        self.pair.observe(self.role, view)
        k, p = self.pair.k, view.params
        if self.role == "decoy":
            effort = p.q_max * (1.0 - float(k["u_D"]))
            return Action(effort=effort, offer=Offer(claim=effort, bid=(1.0 + float(k["w_D"])) * (p.a + p.b * effort)), exit=self.pair.decoy_exit)
        if not self.pair.shade:
            return HonestMax().act(view)
        effort = p.q_max * (1.0 - min(1.0, float(k["u_B"])))
        claim = min(1.0, max(0.0, effort + float(k["m_B"]) - float(k["s_B"])))
        if int(k["clip"]):
            claim = min(claim, effort)
        return Action(effort=effort, offer=Offer(claim=claim, bid=(1.0 + float(k["w_B"])) * (p.a + p.b * effort)))


def x8_bounds(L: int) -> dict:
    return {"n_D": (1.0, 2.0 * float(L)), "u_D": (0.0, 1.0), "w_D": (0.0, 2.0), "u_B": (0.0, 1.0), "m_B": (0.0, 1.0), "s_B": (0.0, 0.3),
            "w_B": (0.0, 2.0)}


def x8_members(knobs: dict, T: int, L: int) -> tuple[X8Member, X8Member]:
    """(beneficiary, decoy) sharing one coordinator."""
    pair = X8Pair(knobs, T, L)
    return X8Member(pair, "beneficiary"), X8Member(pair, "decoy")


def _no_single(**_):
    raise TypeError("X8-DB members are built in pairs (sim.policies.x8.x8_members, sim.objectives_v2.member_factories)")


def x8_family(T: int, L: int) -> Family:
    return Family("X8-DB", X8_KNOBS, x8_bounds(L), _no_single)
