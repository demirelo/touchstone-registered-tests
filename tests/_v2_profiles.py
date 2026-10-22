"""Policy profiles and episode fingerprints shared by the v2 rule and family tests (plan
docs/superpowers/plans/2026-10-22-revision-build.md, Tasks 1, 2, 4, 5)."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from sim.calibrate import cell_config, load_calibration
from sim.cell import Abstain
from sim.locked import load_locked, market_config_from_locked
from sim.market import run_episode
from sim.policies.base import Action
from sim.policies.families import D2
from sim.policies.honest import HonestMax
from sim.policies.identity import h3_family
from sim.rng import make_draws

ROOT = Path(__file__).resolve().parents[1]
COMMON_GRID = [(t, L) for t in (0.08, 0.12, 0.14, 0.16) for L in (3, 10, 20, 50)]
FAILING_D2 = {"u0": 0.6, "m0": 0.5, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "clip": 0}


def market(rho: float = 0.2, beta: float = 0.05):
    return cell_config(market_config_from_locked(load_locked()), load_calibration(ROOT / "experiments/calibration.json"), rho=rho, beta=beta)


CFG = market()


class AbstainSome:
    """Honest-max, but no offer in rounds t % period == phase: rounds with less or no service."""
    name = "abstain_some"

    def __init__(self, period: int = 7, phase: int = 0) -> None:
        self.h, self.period, self.phase = HonestMax(), int(period), int(phase)

    def act(self, view):
        return Action(effort=0.0, offer=None) if view.t % self.period == self.phase else self.h.act(view)


def _cheaters(n: int, x: int | None):
    fam = h3_family(D2) if x is not None else D2
    k = dict(FAILING_D2, **({"x": x} if x is not None else {}))
    return [lambda: fam.make(k) for _ in range(n)]


def factories(profile: str, N: int) -> list:
    honest = [HonestMax for _ in range(N)]
    if profile == "honest":
        return honest
    if profile == "abstain_mix":
        return [Abstain] + [lambda j=j: AbstainSome(5, j % 5) for j in range(1, N)]
    if profile == "replacement":
        return _cheaters(3, 1) + honest[3:]
    if profile == "ban_return":
        return _cheaters(3, None) + honest[3:]
    if profile == "tied_keys":
        return _cheaters(2, 1) + _cheaters(1, None) + honest[3:]
    if profile == "empty_rounds":
        return [lambda: AbstainSome(4, 0) for _ in range(N)]
    raise KeyError(profile)


PROFILE_NAMES = ("honest", "abstain_mix", "replacement", "ban_return", "tied_keys", "empty_rounds")


def run_full(cfg, rule, profile, seed: int, policies=None):
    """One episode; `profile` is a profile name or a list of policy factories."""
    fs = factories(profile, cfg.N) if isinstance(profile, str) else profile
    d = make_draws(cfg, int(seed))
    if profile == "tied_keys":
        d = replace(d, audit_key=np.full_like(d.audit_key, 0.5))
    return run_episode(cfg, rule, [f() for f in fs], int(seed), draws=d)


def fingerprint(res) -> dict:
    return {"history": res.history, "profit": tuple(float(v) for v in res.profit), "cost": float(res.cost), "entry": float(res.entry),
            "audit_cost": float(res.audit_cost), "W": float(res.W), "buyer_surplus": float(res.buyer_surplus),
            "identity_profit": tuple(float(v) for v in res.identity_profit), "served": res.served.tolist(), "audits": res.audits.tolist()}


def count_exits(res) -> int:
    return int(res.n_identities - res.profit.size)
