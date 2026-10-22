"""X5-AG/v2 and X6-SE/v2 (design 5.2): the exploratory families with the rule's public T and L injected."""
from dataclasses import replace

import pytest

from sim.config import ProviderParams
from sim.policies.base import ProviderHistory, ProviderView
from sim.policies.exploratory import EXPLORATORY_FAMILIES, X6Policy, coalition_members
from sim.policies.honest import HonestMax
from sim.rules_v2 import make_rule
from tests._v2_profiles import CFG, count_exits, fingerprint, run_full

P = ProviderParams(q_max=0.8, a=0.02, b=0.3, k=6)
X5K = {"u": 0.6, "m": 0.5, "s": 0.0, "w": 0.0, "n_age": 3.0, "x": 1, "clip": 0}
X6K = {"u": 0.4, "m": 0.3, "s": 0.0, "w": 0.0, "P": 25.0, "x": 1, "y": 1, "clip": 0}


def focal(f, N=10):
    return [f] + [HonestMax for _ in range(N - 1)]


def pview(t, rows):
    h = ProviderHistory()
    for s, a, f, b in rows:
        h.append(s, 0.0, a, f, 0.0, b)
    return ProviderView(i=0, params=P, t=t, posted_prices=None, history=h, policy_seed=1, identity=0)


@pytest.mark.parametrize("rule", ["F000", "F111", "R4"])
def test_v2_families_match_v1_at_headline_constants(rule):
    from sim.policies.v2 import x5v2_family, x6v2_member
    v1 = EXPLORATORY_FAMILIES["X5-AG"]
    a = run_full(CFG, make_rule(rule), focal(lambda: v1.make(X5K)), 2000)
    b = run_full(CFG, make_rule(rule), focal(lambda: x5v2_family(200, 10).make(X5K)), 2000)
    assert fingerprint(a) == fingerprint(b) and count_exits(a) > 0
    a = run_full(CFG, make_rule(rule), focal(lambda: X6Policy(**X6K, member=0, c=1, staggered=False)), 2000)
    b = run_full(CFG, make_rule(rule), focal(lambda: x6v2_member(X6K, 0, 1, False, 200, 10)), 2000)
    assert fingerprint(a) == fingerprint(b) and count_exits(a) > 0


def test_x5v2_exit_round_action_nondefault():
    from sim.policies.v2 import x5v2_family
    p = x5v2_family(100, 20).make({**X5K, "n_age": 10.0})
    rows = [(2, 0, 0, 0)] * 29 + [(2, 1, 1, 0)]
    for t in range(30):
        p.act(pview(t, rows[:t]))
    a = p.act(pview(30, rows))
    assert a.exit and a.effort == pytest.approx(P.q_max) and a.offer.claim == pytest.approx(P.q_max)   # the replacement (age 0 < 10) is honest


def test_x6v2_schedule_uses_injected_T():
    from sim.policies.v2 import x6v2_member
    p = x6v2_member({**X6K, "P": 30.0, "x": 0}, 0, 1, False, 100, 20)
    exits = [t for t in range(100) if p.act(pview(t, [(1, 0, 0, 0)] * t)).exit]
    assert exits == [30, 60, 90]


def test_x5v2_age_bound_60():
    from sim.policies.v2 import x5v2_family
    f = x5v2_family(200, 50)
    assert f.name == "X5-AG/v2" and f.bounds["n_age"] == (0.0, 60.0) and f.knobs == EXPLORATORY_FAMILIES["X5-AG"].knobs


def test_x6v2_family_shape():
    from sim.policies.v2 import x6v2_family
    f = x6v2_family(200, 10)
    assert f.name == "X6-SE/v2" and f.knobs == EXPLORATORY_FAMILIES["X6-SE"].knobs and f.bounds == EXPLORATORY_FAMILIES["X6-SE"].bounds


def test_members_order():
    from sim.policies.v2 import x6v2_members
    other = replace(CFG, providers=tuple(reversed(CFG.providers)))
    for cfg in (CFG, other):
        for c in (2, 5):
            assert x6v2_members(cfg, 4, c) == coalition_members(cfg, 4, c)
