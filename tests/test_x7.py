"""X7-SC (design 5.2): transition order, exact D2+H3 embedding, injected constants, Sobol corner controls."""
from dataclasses import replace

import numpy as np
import pytest

from sim.config import ProviderParams
from sim.policies.base import ProviderHistory, ProviderView
from sim.policies.families import D2
from sim.policies.honest import HonestMax
from sim.policies.identity import h3_family
from tests._v2_profiles import CFG, COMMON_GRID, FAILING_D2, count_exits, fingerprint, run_full

CRED = {"variant": "thr", "K": 6, "M": None}
SEEDS = [pytest.param(2000)] + [pytest.param(s, marks=pytest.mark.slow) for s in (2001, 2002, 2003, 2004)]
GRID = [pytest.param(0.16, 10)] + [pytest.param(t, L, marks=pytest.mark.slow) for t, L in COMMON_GRID if (t, L) != (0.16, 10)]
P = ProviderParams(q_max=0.8, a=0.02, b=0.3, k=6)
BASE = dict(u0=0.3, m0=0.4, s=0.05, d=0.5, r=0.0, w=0.2, k_F=1.0, k_T=1.0, a_F=0.0, n_P=0.0, h_R=0.0, a_R=200.0, e_P=1.0, lam=1.0, clip=0)


def pol(T=200, L=10, **kw):
    from sim.policies.x7 import X7Policy
    return X7Policy(**{**BASE, **kw}, T=T, L=L)


def hist(rows):
    """rows: list of (served, audited, failed, banned_until) for rounds 0..t-1."""
    h = ProviderHistory()
    for s, a, f, b in rows:
        h.append(s, 0.0, a, f, 0.0, b)
    return h


def pview(t, rows, ident=0):
    return ProviderView(i=0, params=P, t=t, posted_prices=None, history=hist(rows), policy_seed=1, identity=ident)


def focal(policy_factory, N=10):
    return [policy_factory] + [HonestMax for _ in range(N - 1)]


@pytest.mark.parametrize("x", [0, 1])
@pytest.mark.parametrize("rule_name", ["F000", "F111", "C*", "R4", "C*/S2"])
@pytest.mark.parametrize("tol,L", GRID)
@pytest.mark.parametrize("seed", SEEDS)
def test_embedding_equals_d2h3(x, rule_name, tol, L, seed):
    from sim.policies.x7 import embed_h3, x7_family
    from sim.rules_v2 import make_rule
    k = {**FAILING_D2, "x": x}
    a = run_full(CFG, make_rule(rule_name, tol, L, cred=CRED), focal(lambda: h3_family(D2).make(k)), seed)
    b = run_full(CFG, make_rule(rule_name, tol, L, cred=CRED), focal(lambda: x7_family(200, L).make(embed_h3(k, 200))), seed)
    assert fingerprint(a) == fingerprint(b)
    assert (count_exits(a) > 0) == (x == 1)


def test_transition_order():
    p = pol(d=0.5, m0=0.4, h_R=0.0, lam=0.0)
    p.act(pview(0, []))
    a1 = p.act(pview(1, [(2, 2, 1, 0)]))
    assert p.m == pytest.approx(0.2)                          # updated once from round 0's failure
    assert a1.exit and p.resets_failure == 1 and p.resets_voluntary == 0
    p.act(pview(1, [(2, 2, 1, 0)]))                           # same round again: no second update, no second count
    assert p.m == pytest.approx(0.2) and p.resets_failure == 1


def test_x7_exit_round_phase_is_replacement():
    p = pol(k_F=0.0, a_F=5.0, h_R=0.0)
    rows = [(2, 0, 0, 0)] * 19 + [(2, 1, 1, 0)]
    for t in range(20):
        p.act(pview(t, rows[:t]))
    assert p.last_phase == "established"
    a = p.act(pview(20, rows))
    assert a.exit and p.last_phase == "fresh"
    assert a.effort == pytest.approx(P.q_max)
    assert a.offer.claim == pytest.approx(min(1.0, max(0.0, P.q_max - BASE["s"])))
    assert a.offer.bid == pytest.approx((1 + BASE["w"]) * (P.a + P.b * P.q_max))


def test_voluntary_reset_window_and_zero_service():
    rows = [(2, 0, 0, 0)] * 15 + [(2, 2, 0, 0)] * 5
    p = pol(lam=0.4, L=10)                                    # window rounds 10..19: served 20, audited 10 -> 0.5 > 0.4
    for t in range(20):
        p.act(pview(t, rows[:t]))
    assert p.act(pview(20, rows)).exit and p.resets_voluntary == 1
    q = pol(lam=0.6, L=10)                                    # 0.5 <= 0.6: no reset
    for t in range(21):
        a = q.act(pview(t, rows[:t]))
    assert not a.exit
    z = pol(lam=0.0, L=10); rows0 = [(0, 0, 0, 0)] * 20
    for t in range(21):
        a = z.act(pview(t, rows0[:t]))
    assert not a.exit                                         # no service in the window: no reset
    n = pol(lam=1.0, L=10); rows1 = [(2, 2, 0, 0)] * 20
    for t in range(21):
        a = n.act(pview(t, rows1[:t]))
    assert not a.exit                                         # lambda = 1 never resets


def test_terminal_phase_uses_injected_L():
    p = pol(T=200, L=20)
    p.act(pview(179, [(1, 0, 0, 0)] * 179)); assert p.last_phase != "terminal"
    p.act(pview(180, [(1, 0, 0, 0)] * 180)); assert p.last_phase == "terminal"


def test_lambda_knob_maps_to_lam():
    from sim.policies.x7 import x7_family
    fam = x7_family(200, 10)
    k = {**{n: v for n, v in BASE.items() if n != "lam"}, "lambda": 0.3}
    assert fam.knobs[-2:] == ("lambda", "clip") and fam.make(k).lam == 0.3 and fam.bounds["h_R"] == (0.0, 200.0)


def test_corners_construction():
    from sim.policies.x7 import corner_vectors, x7_corners, x7_family
    fam = x7_family(200, 10)
    c = x7_corners(fam)
    low = {n: (0 if fam.is_binary(n) else fam.bounds[n][0]) for n in fam.knobs}
    high = {n: (1 if fam.is_binary(n) else fam.bounds[n][1]) for n in fam.knobs}
    assert c[-2:] == [low, high] and low not in c[:-2] and high not in c[:-2] and len(c) <= 514


def test_x7_knobs_15():
    from sim.policies.x7 import KNOBS, x7_family
    assert KNOBS == ("u0", "m0", "s", "d", "r", "w", "k_F", "k_T", "a_F", "n_P", "h_R", "a_R", "e_P", "lambda", "clip")
    fam = x7_family(200, 10)
    assert fam.bounds["a_R"] == (0.0, 200.0) and fam.bounds["e_P"] == (0.0, 1.0)


def test_corner_count_recorded():
    from sim.policies.x7 import X7_CORNER_COUNT, corner_vectors, x7_family
    assert len(corner_vectors(x7_family(200, 10))) == X7_CORNER_COUNT


def test_age_gate_waits():
    p = pol(a_R=5.0, h_R=0.0, lam=0.1, L=10)
    rows = [(2, 0, 0, 0)] * 8 + [(2, 2, 1, 12)]               # identity aged 8 fails in round 8, banned until round 12
    for t in range(9):
        p.act(pview(t, rows[:t]))
    a = p.act(pview(9, rows))
    assert not a.exit and p.resets_failure == 0 and p.resets_voluntary == 0      # waits; audited/served 2/18 > 0.1 ignored
    banned = rows + [(0, 0, 0, 12)] * 3
    for t in range(10, 13):
        assert not p.act(pview(t, banned[:t])).exit                               # no voluntary reset while waiting out the ban
    served = banned + [(2, 2, 0, 0)]
    assert p.act(pview(13, served)).exit and p.resets_voluntary == 1              # served again: the voluntary trigger is back
    young = pol(a_R=50.0, h_R=0.0)
    for t in range(9):
        young.act(pview(t, rows[:t]))
    assert young.act(pview(9, rows)).exit and young.resets_failure == 1           # age 8 < a_R: resets


def test_p_own_batch_update():
    p = pol(L=10)
    rows = [(3, 3, 0, 0), (3, 2, 1, 0), (3, 3, 0, 0)]
    p.act(pview(0, [])); p.act(pview(1, rows[:1]))
    assert p.p_own == 3
    p.act(pview(2, rows[:2]))
    assert p.p_own == 0                                       # passes and one failure in one round: zero
    p.act(pview(3, rows))
    assert p.p_own == 3


def test_exposure_gate():
    rows = [(2, 0, 0, 0)] * 15 + [(2, 2, 0, 0)] * 5           # window 10..19: audited/served 0.5
    hi = pol(e_P=0.4, k_F=0.0, L=10)
    for t in range(21):
        hi.act(pview(t, rows[:t]))
    assert hi.last_phase == "fresh"
    lo = pol(e_P=0.6, k_F=0.0, L=10)
    for t in range(21):
        lo.act(pview(t, rows[:t]))
    assert lo.last_phase == "established"
    off = pol(e_P=1.0, k_F=0.0, L=10); rows1 = [(2, 2, 0, 0)] * 20
    for t in range(21):
        off.act(pview(t, rows1[:t]))
    assert off.last_phase == "established"                    # e_P = 1 never forces the fresh phase


def test_x7_contains_its_twin():
    from sim.policies.x7 import x7_family
    fam = x7_family(200, 10)
    k = fam.project({**{n: v for n, v in BASE.items() if n != "lam"}, "lambda": 0.5, "m0": 1.0})
    res = run_full(CFG, __import__("sim.rules_v2", fromlist=["make_rule"]).make_rule("F111"), focal(lambda: fam.make(k)), 2000)
    c, e = res.claims[:, 0], res.efforts[:, 0]
    ok = ~np.isnan(c)
    assert (c[ok] <= e[ok] + 1e-12).all()


def test_x7_observations_only_view():
    seen = set()

    class Spy:
        def __init__(self, v):
            object.__setattr__(self, "_v", v)

        def __getattr__(self, name):
            seen.add(name); return getattr(self._v, name)
    p = pol()
    for t in range(3):
        p.act(Spy(pview(t, [(1, 1, 0, 0)] * t)))
    assert seen <= {"t", "params", "history", "identity"}
