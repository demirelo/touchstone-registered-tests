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


# ---- Task 2: the six families ------------------------------------------------------------------------------------------

FAMS = ("X1-AH", "X2-TD", "X3-HS", "X4-RO", "X5-AG", "X6-SE")
KNOBS = {"X1-AH": ("u", "m", "s", "w", "theta", "kappa", "x", "clip"), "X2-TD": ("u", "m", "s", "w", "theta", "h", "x", "clip"),
         "X3-HS": ("u", "m", "s", "w", "t0", "span", "z", "clip"), "X4-RO": ("u", "m", "s", "w", "lambda", "n_age", "x", "clip"),
         "X5-AG": ("u", "m", "s", "w", "n_age", "x", "clip"), "X6-SE": ("u", "m", "s", "w", "P", "x", "y", "clip")}
BINARY = {"X1-AH": {"x", "clip"}, "X2-TD": {"x", "clip"}, "X3-HS": {"z", "clip"}, "X4-RO": {"x", "clip"}, "X5-AG": {"x", "clip"},
          "X6-SE": {"x", "y", "clip"}}


def fam(name):
    from sim.policies.exploratory import EXPLORATORY_FAMILIES
    return EXPLORATORY_FAMILIES[name]


def b3_noisy():
    return make_rule("B3", {"tol": 0.01, "L": 10})            # honest delivery fails about 4 in 10 audits: false failures and bans


def _episode(focal_policy, rule, seed, focal=4, others=None):
    cfg = headline_cfg(); pols = [HonestMax() for _ in range(cfg.N)]
    for e, p in (others or {}).items():
        pols[e] = p
    pols[focal] = focal_policy
    return run_episode(cfg, rule, pols, seed)


def _same(a, b):
    return (np.array_equal(a.profit, b.profit) and np.array_equal(np.nan_to_num(a.claims, nan=-1), np.nan_to_num(b.claims, nan=-1))
            and np.array_equal(a.efforts, b.efforts) and np.array_equal(a.served, b.served) and a.n_identities == b.n_identities)


@pytest.mark.parametrize("name", FAMS)
def test_domain_and_order(name):
    f = fam(name)
    assert f.knobs == KNOBS[name] and f.dim <= 8 and f.knobs[-1] == "clip"
    assert {k for k in f.knobs if f.is_binary(k)} == BINARY[name]


@pytest.mark.parametrize("name", FAMS)
@pytest.mark.parametrize("rule", ["b3_noisy", "r3"])
def test_honest_point_equals_honest_max_over_episodes(name, rule):
    f = fam(name); mk = {"b3_noisy": b3_noisy, "r3": r3}[rule]
    for seed in (1000, 1001, 1002):
        hon = _episode(HonestMax(), mk(), seed)
        got = _episode(f.make(f.honest_point()), mk(), seed)
        assert _same(hon, got), f"{name} honest point differs from honest-max on seed {seed}"
    if rule == "b3_noisy":
        assert int(hon.failures[:, 4].sum()) > 0          # false failures and bans were exercised


def _cheating_knobs(name, rng):
    f = fam(name); k = f.transform(rng.normal(0, 1.5, f.dim)); k["clip"] = 0
    k.update({"u": 0.4, "m": 0.3, "s": 0.0})
    for b in BINARY[name] - {"clip"}:
        k[b] = 1
    if name == "X1-AH": k["theta"] = 0.5
    if name == "X2-TD": k["theta"] = 0.5
    if name == "X3-HS": k.update({"t0": 0.1, "span": 0.6})
    if name in ("X4-RO", "X5-AG"): k["n_age"] = 5.0
    if name == "X6-SE": k["P"] = 25.0
    return k


@pytest.mark.parametrize("name", FAMS)
def test_twin_trajectory_equals_projected_family(name):
    from sim.policies.twin import Twin
    f = fam(name); rng = np.random.default_rng(7)
    for seed in (1000, 1001):
        k = _cheating_knobs(name, rng)
        a = _episode(Twin(f.make(k)), b3(), seed)
        b = _episode(f.make(f.project(k)), b3(), seed)
        assert _same(a, b)


# synthetic driver: one round at a time, history appended after each action, a new identity after each exit
def drive(policy, outcomes, params=None, T=200):
    params = params or headline_cfg().providers[4]
    h = ProviderHistory(); ident = 0; acts = []
    for t in range(len(outcomes)):
        a = policy.act(view_at(t, params, h, identity=ident))
        acts.append(a)
        if a.exit:
            ident += 1
        o = outcomes[t]
        h.append(o.get("served", 6), o.get("payment", 6 * 0.5), o.get("audited", 0), o.get("failed", 0), o.get("refunded", 0.0),
                 o.get("banned_until", 0))
    return acts


def cheats(a, params=None):
    params = params or headline_cfg().providers[4]
    return a.effort < params.q_max - 1e-12


BASE = {"u": 0.5, "m": 0.2, "s": 0.0, "w": 0.0, "clip": 0}


def test_x1_bucket_arithmetic_with_empty_buckets_and_kappa0():
    f = fam("X1-AH")
    # kappa = 0 and an empty fresh bucket at t = 0: the pooled rate (0 + 1) / (0 + 1) = 1 applies, so theta 0.9 does not cheat
    p = f.make({**BASE, "theta": 0.9, "kappa": 0.0, "x": 0})
    acts = drive(p, [{"served": 6, "audited": 0}] * 12)
    assert not cheats(acts[0])
    # rounds 0..9 are fresh with 0 of 6 audited each: fresh rate 0 at kappa 0, so from round 1 it cheats
    assert all(cheats(a) for a in acts[1:10])
    # kappa = 6 shrinks toward the pool (audited_all + 1) / (served_all + 1): after round 0, p = (0 + 6 * 1/7) / (6 + 6) = 1/14
    p2 = f.make({**BASE, "theta": 1 / 14 + 1e-9, "kappa": 6.0, "x": 0}); a2 = drive(p2, [{"served": 6, "audited": 0}] * 2)
    assert cheats(a2[1])
    p3 = f.make({**BASE, "theta": 1 / 14 - 1e-9, "kappa": 6.0, "x": 0}); a3 = drive(p3, [{"served": 6, "audited": 0}] * 2)
    assert not cheats(a3[1])


def test_x1_exit_after_failed_audit_only_when_x1():
    f = fam("X1-AH"); out = [{"served": 6, "audited": 2, "failed": 1, "banned_until": 16}] + [{"served": 0}] * 3
    assert drive(f.make({**BASE, "theta": 0.5, "kappa": 1.0, "x": 1}), out)[1].exit
    assert not drive(f.make({**BASE, "theta": 0.5, "kappa": 1.0, "x": 0}), out)[1].exit


def test_x2_per_phase_ewma_and_reset_on_exit():
    f = fam("X2-TD"); h = 1.0; lam = 0.5 ** (1 / h)
    # fresh phase: audited fractions 0.5, 0.0 -> EWMA 1 -> lam*1 + (1-lam)*0.5 = 0.75 -> lam*0.75 + 0 = 0.375
    p = f.make({**BASE, "theta": 0.5, "h": h, "x": 1})
    acts = drive(p, [{"served": 6, "audited": 3}, {"served": 6, "audited": 0}, {"served": 6, "audited": 6, "failed": 1, "banned_until": 0},
                     {"served": 6, "audited": 0}])
    assert not cheats(acts[1]) and cheats(acts[2])                 # 0.75 then 0.375 < 0.5
    assert acts[3].exit and not cheats(acts[3])                    # exit after the failure: the fresh EWMA resets to 1


def test_x3_window_edges_and_terminal_switch():
    f = fam("X3-HS"); k = {**BASE, "t0": 0.25, "span": 0.25, "z": 0}
    acts = drive(f.make(k), [{}] * 200)
    on = [t for t, a in enumerate(acts) if cheats(a)]
    assert on == list(range(50, 100))
    acts_z = drive(f.make({**k, "z": 1}), [{}] * 200)
    assert [t for t, a in enumerate(acts_z) if cheats(a)] == list(range(50, 100)) + list(range(190, 200))
    assert not any(a.exit for a in acts_z)


def _ro(lam, n_age=0.0, x=1):
    return fam("X4-RO").make({**BASE, "lambda": lam, "n_age": n_age, "x": x})


def test_x4_lambda0_always_resets_after_failure_and_x0_never():
    out = [{"served": 6, "payment": 3.0}] * 15 + [{"served": 6, "failed": 1, "audited": 1, "banned_until": 26}] + [{"served": 0, "banned_until": 26}] * 3
    assert drive(_ro(0.0), out)[16].exit
    assert not any(a.exit for a in drive(_ro(0.0, x=0), out))


def test_x4_inequality_both_sides_and_ban_capped_at_T():
    from sim.policies.exploratory import W_PUBLIC
    pp = headline_cfg().providers[4]
    # fresh rounds 0..9 earn 1.0 per round, established rounds 10..14 earn 2.0: V_f = 1, V_e = 2 (constant streams)
    def pay(profit, served=6, effort=None):
        e = pp.q_max * 0.5                           # the cheat effort at u = 0.5 (n_age 0: cheats from round 0)
        return {"served": served, "payment": profit + served * (pp.a + pp.b * e)}
    out = [pay(1.0)] * 10 + [pay(2.0)] * 5 + [{**pay(2.0), "failed": 1, "audited": 1, "banned_until": 26}] + [{"served": 0, "banned_until": 26}] * 2
    # round 16: remaining ban 26 - 16 = 10 rounds; lhs = 10 * V_e = 10 * V_e_hat; rhs = lambda * W * (V_e - V_f)
    p = _ro(1.0); acts = drive(p, out)
    ve, vf = p.V_e, p.V_f
    lhs = (26 - 16) * max(ve, 0); rhs_unit = W_PUBLIC * max(ve - vf, 0)
    assert acts[16].exit == (lhs > 1.0 * rhs_unit)
    lam_hi = lhs / rhs_unit + 0.01; lam_lo = lhs / rhs_unit - 0.01
    assert not drive(_ro(lam_hi), out)[16].exit and drive(_ro(lam_lo), out)[16].exit
    # a ban beyond the horizon counts only to T
    late = [pay(1.0)] * 10 + [pay(2.0)] * 179 + [{**pay(2.0), "failed": 1, "audited": 1, "banned_until": 400}] + [{"served": 0}] * 2
    p2 = _ro(1.0); a2 = drive(p2, late)
    assert a2[190].exit == ((200 - 190) * max(p2.V_e, 0) > W_PUBLIC * max(p2.V_e - p2.V_f, 0))


def test_x4_undefined_vf_exits():
    out = [{"served": 6, "failed": 1, "audited": 1, "banned_until": 11}] + [{"served": 0}] * 2
    p = _ro(2.0, n_age=0.0); acts = drive(p, out)   # round 0 is fresh, so V_f exists but V_e does not: undefined -> exit
    assert acts[1].exit


def test_x4_failed_banned_established_round_updates_ve_once():
    pp = headline_cfg().providers[4]; e = pp.q_max * 0.5
    out = [{"served": 6, "payment": 6 * (pp.a + pp.b * e) + 1.0}] * 12
    out[11] = {"served": 6, "payment": 6 * (pp.a + pp.b * e) + 1.0, "audited": 1, "failed": 1, "refunded": 3.0, "banned_until": 22}
    p = _ro(5.0, x=0); drive(p, out + [{"served": 0, "banned_until": 22}])
    lam = 0.5 ** (1 / 10)
    want = lam * 1.0 + (1 - lam) * (1.0 - 3.0)       # V_e initialised at round 10's 1.0, then round 11's refunded profit -2.0 once
    assert p.V_e == pytest.approx(want) and p.n_updates_e == 2


def test_x5_honest_for_exactly_n_age_rounds_per_identity():
    f = fam("X5-AG")
    out = [{"served": 6}] * 20 + [{"served": 6, "audited": 1, "failed": 1, "banned_until": 31}] + [{"served": 6}] * 15
    acts = drive(f.make({**BASE, "n_age": 7.4, "x": 1}), out)
    assert [cheats(a) for a in acts[:8]] == [False] * 7 + [True]
    assert acts[21].exit and [cheats(a) for a in acts[21:29]] == [False] * 7 + [True]


def test_x5_ban_does_not_restart_aging():
    f = fam("X5-AG")
    out = [{"served": 6}] * 9 + [{"served": 6, "audited": 1, "failed": 1, "banned_until": 20}] + [{"served": 0, "banned_until": 20}] * 12
    acts = drive(f.make({**BASE, "n_age": 5.0, "x": 0}), out)
    assert all(cheats(a) for a in acts[20:22])


def test_x6_scheduled_resets_and_switches():
    f = fam("X6-SE")
    acts = drive(f.make({**BASE, "P": 10.0, "x": 0, "y": 1}), [{}] * 200)
    assert [t for t, a in enumerate(acts) if a.exit] == list(range(10, 200, 10))
    assert not any(a.exit for a in drive(f.make({**BASE, "P": 10.0, "x": 0, "y": 0}), [{}] * 200))


@pytest.mark.parametrize("P,c", [(10, 2), (5, 2), (3, 5), (1, 5)])
def test_scheduled_resets_counts_and_distinctness(P, c):
    from sim.policies.exploratory import reset_overlap, scheduled_resets
    sync = scheduled_resets(P, c, 200, staggered=False); stag = scheduled_resets(P, c, 200, staggered=True)
    K = (200 - 1) // P
    assert all(len(r) == K for r in sync + stag) and all(1 <= t <= 199 for r in stag for t in r)
    assert all(r == list(range(P, K * P + 1, P)) for r in sync)
    if P >= c:
        assert reset_overlap(stag) == 0
    else:
        assert reset_overlap(stag) > 0
    assert reset_overlap(sync) == K if c > 1 else True


def test_x6_staggered_member_follows_its_schedule_and_failure_resets_counted():
    from sim.policies.exploratory import X6Policy, scheduled_resets
    k = {**BASE, "P": 10.0, "x": 1, "y": 1}
    m1 = X6Policy(**k, member=1, c=2, staggered=True)
    out = [{}] * 200; out[33] = {"failed": 1, "audited": 1}
    acts = drive(m1, out)
    sched = scheduled_resets(10, 2, 200, staggered=True)[1]
    exits = [t for t, a in enumerate(acts) if a.exit]
    assert set(sched) <= set(exits) and 34 in exits
    assert m1.resets_scheduled == len(sched) and m1.resets_failure == 1


def test_coalition_members():
    from sim.policies.exploratory import coalition_members
    from sim.positions import positions
    cfg = headline_cfg(); f = positions(cfg)["median"]
    score = [p.b * p.q_max for p in cfg.providers]; order = sorted(range(cfg.N), key=lambda i: (score[i], i)); r = order.index(f)
    assert coalition_members(cfg, f, 1) == (f,)
    m2 = coalition_members(cfg, f, 2); m5 = coalition_members(cfg, f, 5)
    assert m2[0] == f and len(m2) == 2 and abs(order.index(m2[1]) - r) == 1
    assert len(set(m5)) == 5 and m5[0] == f and max(abs(order.index(e) - r) for e in m5) <= 3


def test_x6_c1_equals_unilateral_member():
    from sim.policies.exploratory import X6Policy
    f = fam("X6-SE"); k = {**BASE, "P": 12.0, "x": 1, "y": 1}
    a = _episode(f.make(k), b3(), 1000); b = _episode(X6Policy(**k, member=0, c=1, staggered=False), b3(), 1000)
    assert _same(a, b)


class _Guard:
    ALLOWED = {"i", "params", "t", "posted_prices", "history", "policy_seed", "identity", "rng"}

    def __init__(self, v):
        object.__setattr__(self, "_v", v)

    def __getattr__(self, name):
        if name not in self.ALLOWED:
            raise AssertionError(f"gate read {name}")
        val = getattr(self._v, name)
        return _HGuard(val) if name == "history" else val


class _HGuard:
    ALLOWED = {"served", "payment", "audited", "failed", "refunded", "banned_until"}

    def __init__(self, h):
        object.__setattr__(self, "_h", h)

    def __getattr__(self, name):
        if name not in self.ALLOWED:
            raise AssertionError(f"gate read history.{name}")
        return getattr(self._h, name)


@pytest.mark.parametrize("name", FAMS)
def test_gates_read_only_provider_view(name):
    f = fam(name); p = f.make(_cheating_knobs(name, np.random.default_rng(3))); params = headline_cfg().providers[4]
    h = ProviderHistory(); ident = 0
    for t in range(200):
        a = p.act(_Guard(view_at(t, params, h, identity=ident)))
        ident += int(a.exit)
        h.append(6, 3.0, int(t % 7 == 0), int(t % 21 == 0), 0.0, t + 11 if t % 21 == 0 else 0)


def test_x3_diagnostic_windows_are_exact_knob_points():
    f = fam("X3-HS")
    a = drive(f.make({**BASE, "t0": 0.05, "span": 0.9, "z": 0}), [{}] * 200)
    assert [t for t, x in enumerate(a) if cheats(x)] == list(range(10, 190))
    b = drive(f.make({**BASE, "t0": 0.95, "span": 0.05, "z": 0}), [{}] * 200)
    assert [t for t, x in enumerate(b) if cheats(x)] == list(range(190, 200))


def test_x6_coincident_scheduled_and_failure_reset_counts_both_triggers_one_exit():
    from sim.policies.exploratory import X6Policy
    p = X6Policy(**{**BASE, "P": 20.0, "x": 1, "y": 1})
    out = [{}] * 30; out[19] = {"failed": 1, "audited": 1}
    acts = drive(p, out)
    assert [t for t, a in enumerate(acts) if a.exit] == [20]
    assert (p.resets_scheduled, p.resets_failure, p.resets_coincident) == (1, 1, 1)
