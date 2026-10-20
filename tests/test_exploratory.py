"""Exploratory attackers (plan docs/superpowers/plans/2026-10-20-exploratory-attackers.md): shared actions, identity
state, the six families, honest points, twins, and information limits. Exploratory only; no registered artifact."""
from __future__ import annotations

import numpy as np
import pytest

from sim.calibrate import cell_config, load_calibration
from sim.locked import load_locked, market_config_from_locked
from sim.market import run_episode
from sim.policies.base import Action, ProviderHistory, ProviderView
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.honest import HonestMax
from sim.registry import make_rule, proposed_params


def headline_cfg():
    lk = load_locked()
    return cell_config(market_config_from_locked(lk), load_calibration("experiments/calibration.json"), rho=0.2, beta=0.05)


def b3():
    return make_rule("B3", {"tol": 0.16, "L": 10})


def r3():
    return make_rule("proposed", proposed_params()["best_params"] if "best_params" in proposed_params() else proposed_params())


def view_at(t, params, history=None, identity=0, seed=0):
    return ProviderView(i=0, params=params, t=t, posted_prices=None, history=history or ProviderHistory(), policy_seed=seed, identity=identity)


# ---- Task 1: shared actions ------------------------------------------------------------------------------------------

def test_cheat_action_matches_fixed_cheat():
    from sim.policies.exploratory import cheat_action
    rng = np.random.default_rng(0); cfg = headline_cfg()
    for n in range(50):
        p = cfg.providers[n % cfg.N]
        u, m, s, w = rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0, 0.3), rng.uniform(0, 2); clip = int(rng.integers(0, 2))
        v = view_at(n, p)
        assert cheat_action(v, u, m, s, w, clip) == FixedCheat(u, m, s, w, clip).act(v)


def test_honest_action_at_w0_is_honest_max():
    from sim.policies.exploratory import honest_action
    cfg = headline_cfg()
    for p in cfg.providers:
        v = view_at(3, p)
        assert honest_action(v, 0.0) == HonestMax().act(v)


# ---- Task 1: identity state through real episodes ---------------------------------------------------------------------

class Scripted:
    """Honest-max that exits in the listed rounds and records, per round, the IdentityState's age and the last
    observation it attributed (which identity served, its profit proxy)."""
    name = "scripted"

    def __init__(self, exits=(), T=200, calls_per_round=1):
        from sim.policies.exploratory import IdentityState
        self.exits, self.state, self.log, self.calls = set(exits), IdentityState(T=T), [], calls_per_round

    def act(self, view):
        for _ in range(self.calls):
            self.state.begin_round(view)
        ex = view.t in self.exits
        if ex:
            self.state.note_exit(view.t)
        a = self.base_action(view)
        banned = (not ex) and bool(view.history.banned_until) and view.history.banned_until[-1] > view.t
        self.state.record_action(view.t, a.effort, eligible=not banned)
        self.log.append({"t": view.t, "age": self.state.age(view.t), "identity": view.identity, "n_obs": len(self.state.obs),
                         "last": dict(self.state.obs[-1]) if self.state.obs else None})
        return Action(effort=a.effort, offer=a.offer, exit=ex)

    def base_action(self, view):
        return HonestMax().act(view)


def _run(policy, rule=None, seed=1000, focal=4):
    cfg = headline_cfg(); pols = [HonestMax() for _ in range(cfg.N)]; pols[focal] = policy
    return run_episode(cfg, rule or b3(), pols, seed)


def test_age_zero_in_exit_round_one_next():
    p = Scripted(exits=(30,)); _run(p)
    by_t = {r["t"]: r for r in p.log}
    assert by_t[29]["age"] == 29 and by_t[30]["age"] == 0 and by_t[31]["age"] == 1
    assert by_t[31]["identity"] != by_t[29]["identity"]


def test_consecutive_exits():
    p = Scripted(exits=(30, 31, 32)); _run(p)
    by_t = {r["t"]: r for r in p.log}
    assert [by_t[t]["age"] for t in (30, 31, 32, 33)] == [0, 0, 0, 1]
    assert len({by_t[t]["identity"] for t in (30, 31, 32, 33)}) == 4          # each view after an exit shows a new identity


class FailThenBanned(Scripted):
    """Claims above effort from round 20 so an audit fails (B3 audits at random); used to obtain bans."""
    def base_action(self, view):
        a = HonestMax().act(view)
        if 20 <= view.t < 120:
            return Action(effort=a.effort * 0.3, offer=type(a.offer)(claim=1.0, bid=a.offer.bid))
        return a


def test_ban_return_keeps_age():
    p = FailThenBanned(); r = _run(p)
    assert all(x["age"] == x["t"] for x in p.log)           # no exits: age is the round, ban or no ban
    assert int(r.failures[:, 4].sum()) > 0                    # the fixture did produce failures and bans


def test_exit_during_ban():
    base = FailThenBanned(); rb = _run(base)
    banned = [t for t in range(21, 119) if base.log[t - 1]["last"] is not None and rb.history and t < 119
              and base.log[t]["t"] == t and _banned_at(base, t)]
    assert banned, "the fixture must produce a banned round"
    t_ex = banned[0]
    p = FailThenBanned(exits=(t_ex,)); _run(p)
    by_t = {r["t"]: r for r in p.log}
    assert by_t[t_ex]["age"] == 0 and by_t[t_ex + 1]["age"] == 1


def _banned_at(policy, t):
    o = policy.log[t]["last"]                 # the observation of round t - 1, made at round t
    return o is not None and o["banned_until"] > t


def test_repeated_call_same_round_is_idempotent():
    a = Scripted(exits=(30,)); _run(a)
    b = Scripted(exits=(30,), calls_per_round=3); _run(b)
    assert [(x["age"], x["n_obs"], x["last"]) for x in a.log] == [(x["age"], x["n_obs"], x["last"]) for x in b.log]


def test_history_entry_attributed_to_serving_identity():
    p = Scripted(exits=(30,)); r = _run(p)
    by_t = {x["t"]: x for x in p.log}
    # the observation of round 30 (made at round 31) belongs to the identity created at round 30
    o = by_t[31]["last"]
    assert o["t"] == 30 and o["creation"] == 30 and o["age"] == 0
    o29 = by_t[30]["last"]
    assert o29["t"] == 29 and o29["creation"] == 0


def test_profit_proxy_uses_refunds_and_remembered_effort():
    p = FailThenBanned(); r = _run(p)
    cfg = headline_cfg(); pp = cfg.providers[4]
    for x in p.log[1:]:
        o = x["last"]
        want = o["payment"] - o["refunded"] - o["served"] * (pp.a + pp.b * o["effort"])
        assert o["profit"] == pytest.approx(want)
    assert any(x["last"]["refunded"] > 0 for x in p.log[1:])   # a refunded round was exercised
