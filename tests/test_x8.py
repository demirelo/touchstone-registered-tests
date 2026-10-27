"""X8-DB (design draft 7, 5.2): a decoy and a beneficiary at c = 2 sharing one coordinator; real n_D schedule restarted
after every replacement, the gate from the identity that offers in the round, independence from the policy-call order,
a projection that clips only the beneficiary, and members that read only member histories."""
import numpy as np
import pytest

from sim.config import ProviderParams
from sim.policies.base import ProviderHistory, ProviderView

P = ProviderParams(q_max=0.8, a=0.02, b=0.3, k=6)
K = {"n_D": 2.5, "u_D": 0.0, "w_D": 0.0, "u_B": 0.4, "m_B": 0.3, "s_B": 0.0, "w_B": 0.1, "g_B": 1, "clip": 0}


def hist(rows):
    h = ProviderHistory()
    for s, a, f in rows:
        h.append(s, 0.0, a, f, 0.0, 0)
    return h


def view(i, t, h):
    return ProviderView(i=i, params=P, t=t, posted_prices=None, history=h, policy_seed=1, identity=i)


def pair(**kw):
    from sim.policies.x8 import x8_members
    return x8_members({**K, **kw}, 200, 10)


def run_rounds(ben, dec, decoy_rows, rounds, decoy_first=True):
    hb, hd = ProviderHistory(), ProviderHistory()
    out = []
    for t in range(rounds):
        calls = [(dec, 1, hd), (ben, 0, hb)] if decoy_first else [(ben, 0, hb), (dec, 1, hd)]
        acts = {i: p.act(view(i, t, h)) for p, i, h in calls}
        out.append((acts[1].exit, acts[0].effort, acts[0].offer.claim))
        hb.append(1, 0.0, 0, 0, 0.0, 0)
        s, a, f = decoy_rows[t] if t < len(decoy_rows) else (1, 0, 0)
        hd.append(s, 0.0, a, f, 0.0, 0)
    return out


def test_x8_schedule_real_nd():
    ben, dec = pair(n_D=2.5)
    exits = [e for e, _, _ in run_rounds(ben, dec, [], 10)]
    assert [t for t, e in enumerate(exits) if e] == [3, 6, 9]            # ages 0, 1, 2, then 3 >= 2.5
    ben, dec = pair(n_D=2.5)
    rows = [(1, 0, 0), (1, 1, 1)]                                        # failure in round 1 (age 1)
    exits = [e for e, _, _ in run_rounds(ben, dec, rows, 8)]
    assert [t for t, e in enumerate(exits) if e] == [2, 5]               # replaced at age 2 by the failure, clock restarts


def test_x8_gate_at_replacement_boundary():
    ben, dec = pair(n_D=12.0, g_B=1)
    out = run_rounds(ben, dec, [], 14)
    assert out[9][1] < P.q_max and out[10][1] == pytest.approx(P.q_max)  # decoy age 9 < L: shade; age 10: honest-max
    assert out[12][0] and out[12][1] < P.q_max                           # decoy replaced in round 12: the offering identity is age 0
    ben, dec = pair(n_D=20.0, g_B=0)
    assert all(e < P.q_max for _, e, _ in run_rounds(ben, dec, [], 15))  # g_B = 0: always shades


def test_x8_call_order_independent():
    rows = [(1, 0, 0), (1, 1, 1), (1, 0, 0), (1, 1, 0)]
    a = run_rounds(*pair(n_D=3.0), rows, 12, decoy_first=True)
    b = run_rounds(*pair(n_D=3.0), rows, 12, decoy_first=False)
    assert a == b


def test_x8_projection_keeps_decoy():
    from sim.policies.x8 import x8_family
    fam = x8_family(200, 10)
    k = {**K, "u_D": 0.7, "clip": 0}
    assert fam.project(k) == {**k, "clip": 1}
    assert fam.knobs == ("n_D", "u_D", "w_D", "u_B", "m_B", "s_B", "w_B", "g_B", "clip") and fam.bounds["n_D"] == (1.0, 20.0)


def test_x8_members_read_only_member_histories():
    ben, dec = pair()
    run_rounds(ben, dec, [], 3)
    assert ben.pair.seen == {0, 1} and dec.pair is ben.pair


def test_x8_pair_source_binds_each_episode():
    from sim.objectives_v2 import member_factories
    fs = member_factories("X8-DB", K, (4, 2), None, 200, 10)
    for order in ((0, 1), (1, 0)):
        made = [None, None]
        for j in order:
            made[j] = fs[j]()
        assert made[0].pair is made[1].pair and made[0].role == "beneficiary" and made[1].role == "decoy"


def test_coalition_objective_x8():
    from sim.cell import SeedCache
    from sim.objectives_v2 import CoalitionObjective
    from sim.policies.v2 import x6v2_members
    from sim.policies.x8 import x8_family
    from sim.rules_v2 import make_rule
    from tests._v2_profiles import CFG
    mem = x6v2_members(CFG, 4, 2); ref = np.zeros((2, 2))
    o = CoalitionObjective(CFG, lambda: make_rule("F111"), mem, x8_family(200, 10), [2000, 2001], SeedCache(), "total",
                           joint_ref=ref, T=200, L=10, family_name="X8-DB")
    f = o.eval_knobs(K)
    ex = o.extra[next(iter(o.extra))]
    assert np.isfinite(f) and f == pytest.approx(ex["total"]) and len(ex["member_means"]) == 2
    with pytest.raises(ValueError):
        CoalitionObjective(CFG, lambda: make_rule("F111"), x6v2_members(CFG, 4, 5), x8_family(200, 10), [2000], SeedCache(), "total",
                           joint_ref=np.zeros((5, 1)), T=200, L=10, family_name="X8-DB")
