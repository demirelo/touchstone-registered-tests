import numpy as np
import pytest
from sim.config import MarketConfig
from sim.policies.families import D1, D2, FAMILIES, embed_d1_in_d2, knob_key, exact_key
from sim.policies.adaptive import AdaptiveCheat
from sim.policies.base import ProviderView, ProviderHistory
from sim.policies.honest import HonestMax
from sim.policies.identity import h3_family, IdentityReplacement


def view(i=0, t=0, failed=None, banned=None):
    cfg = MarketConfig.default()
    h = ProviderHistory()
    for k, f in enumerate(failed or []):
        h.append(1, 0.5, 1, f, 0.0, (banned or [0] * len(failed))[k])
    return ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=None, history=h, policy_seed=0, identity=i)


def test_transform_maps_into_bounds_and_clip_thresholds():
    x = np.zeros(D2.dim)
    k = D2.transform(x)
    assert k["u0"] == pytest.approx(0.5) and k["s"] == pytest.approx(0.15) and k["w"] == pytest.approx(1.0)
    assert k["clip"] == 1          # sigmoid(0) = 0.5 >= 0.5
    k2 = D2.transform(np.full(D2.dim, -0.1))
    assert k2["clip"] == 0
    big = D2.transform(np.full(D2.dim, 50.0))
    assert big["u0"] == pytest.approx(1.0) and big["r"] == pytest.approx(0.2)


def test_inverse_round_trips_and_registered_starts():
    k = {"u0": 0.3, "m0": 0.7, "s": 0.1, "d": 0.2, "r": 0.05, "w": 1.5, "clip": 1}
    x = D2.inverse(k, near=0.02)
    back = D2.transform(x)
    for name in ("u0", "m0", "s", "d", "r", "w"):
        assert back[name] == pytest.approx(k[name], abs=1e-9)
    assert back["clip"] == 1
    settings = {"near_corner": 0.02, "sobol_seed": 7}
    starts = D2.registered_starts(settings)
    assert len(starts) == 5
    cheat = D2.transform(starts[0]); honest = D2.transform(starts[1])      # near-full-cheat first: a one-restart attack search can cheat
    tw = D2.registered_starts(settings, twin=True)
    assert np.array_equal(tw[0], starts[1]) and np.array_equal(tw[1], starts[0]) and all(np.array_equal(a, b) for a, b in zip(tw[2:], starts[2:]))
    assert honest["u0"] == pytest.approx(0.02) and honest["clip"] == 1
    assert cheat["u0"] == pytest.approx(0.98) and cheat["s"] == pytest.approx(0.3 * 0.02) and cheat["clip"] == 0


def test_project_corners_keys_and_honest_point():
    assert D1.project({"u": 0.2, "m": 0.9, "s": 0.0, "w": 0.0, "clip": 0})["clip"] == 1
    corners = D1.corners()
    assert len(corners) == 2 ** 5 and len({knob_key(c) for c in corners}) == len(corners)
    assert len(D2.corners()) == 2 ** 7
    assert knob_key({"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}) == knob_key({"u": 0.5000000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0})
    assert exact_key({"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}) != exact_key({"u": 0.5000000000001, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0})
    assert D1.honest_point() == {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}
    assert D2.honest_point() == {"u0": 0.0, "m0": 0.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "clip": 1}


def test_honest_point_of_each_family_reproduces_honest_max():
    for fam in (D1, D2):
        p = fam.make(fam.honest_point())
        for i in range(10):
            for t, failed in enumerate(([], [1], [1, 0])):
                assert p.act(view(i=i, t=t, failed=failed)) == HonestMax().act(view(i=i, t=t, failed=failed))


def test_d2_recurrence_and_containment_of_d1():
    p = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.0, w=0.0, clip=0)
    a0 = p.act(view(i=0, failed=[]))                    # m_1 = 0.6 -> claim min(1, 0.3 + 0.6 - 0.2) = 0.7
    assert a0.offer.claim == pytest.approx(0.7)
    a1 = p.act(view(i=0, t=1, failed=[1]))              # failed last round -> m = 0.3 -> claim 0.4
    assert a1.offer.claim == pytest.approx(0.4)
    a2 = p.act(view(i=0, t=2, failed=[1, 0]))           # no failure, r = 0 -> stays 0.3
    assert a2.offer.claim == pytest.approx(0.4)
    q = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.2, w=0.0, clip=0)
    q.act(view(i=0, failed=[])); q.act(view(i=0, t=1, failed=[1]))
    a = q.act(view(i=0, t=2, failed=[1, 0]))            # recovery: min(0.6, 0.3 + 0.2 * 0.6) = 0.42 -> claim 0.52
    assert a.offer.claim == pytest.approx(0.52)
    with pytest.raises(ValueError):
        AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.5, w=0.0, clip=0)   # r outside [0, 0.2]
    # ban branch: banned last round and not audited -> state unchanged
    b = AdaptiveCheat(u0=0.5, m0=0.6, s=0.2, d=0.5, r=0.2, w=0.0, clip=0)
    b.act(view(i=0, failed=[])); b.act(view(i=0, t=1, failed=[1]))          # m = 0.3
    a_b = b.act(view(i=0, t=2, failed=[1, 0], banned=[0, 5]))              # banned in round 1 -> m stays 0.3
    assert a_b.offer.claim == pytest.approx(0.4)
    # containment: D1 point embedded at d = r = 0 behaves like D1 every round
    k1 = {"u": 0.4, "m": 0.5, "s": 0.1, "w": 0.3, "clip": 0}
    d2 = D2.make(embed_d1_in_d2(k1)); d1 = D1.make(k1)
    for t, failed in enumerate(([], [1], [1, 1], [1, 1, 0])):
        assert d2.act(view(i=1, t=t, failed=failed)) == d1.act(view(i=1, t=t, failed=failed))


def test_make_returns_fresh_instances():
    k = {"u0": 0.5, "m0": 0.6, "s": 0.2, "d": 0.5, "r": 0.0, "w": 0.0, "clip": 0}
    a, b = D2.make(k), D2.make(k)
    a.act(view(i=0)); a.act(view(i=0, t=1, failed=[1]))
    assert b.act(view(i=0)).offer.claim == pytest.approx(0.7)    # b's state untouched
    assert set(FAMILIES) == {"D1", "D2"}


def test_h3_family_adds_the_exit_knob_and_keeps_honest_max_inside():
    h3 = h3_family(D2)
    assert h3.name == "D2+H3" and h3.knobs == D2.knobs[:-1] + ("x", "clip") and h3.dim == D2.dim + 1
    assert h3.honest_point() == dict(D2.honest_point(), x=0) and len(h3.corners()) == 2 ** 8
    k = {"u0": 0.5, "m0": 0.6, "s": 0.2, "d": 0.5, "r": 0.0, "w": 0.0, "clip": 0}
    wrapped = h3.make(dict(k, x=1)); plain = h3.make(dict(k, x=0))
    assert isinstance(wrapped, IdentityReplacement) and isinstance(plain, AdaptiveCheat)
    assert wrapped.act(view(i=0, t=1, failed=[1])).exit is True and plain.act(view(i=0, t=1, failed=[1])).exit is False
    honest = h3.make(h3.honest_point())
    for t, failed in enumerate(([], [1], [1, 0])):
        assert honest.act(view(i=0, t=t, failed=failed)) == HonestMax().act(view(i=0, t=t, failed=failed))
    starts = h3.registered_starts({"near_corner": 0.02, "sobol_seed": 7})
    assert h3.transform(starts[0])["x"] == 1 and h3.transform(starts[0])["clip"] == 0 and h3.transform(starts[1])["x"] == 0
    assert h3.project(dict(k, x=1))["x"] == 1 and h3.project(dict(k, x=1))["clip"] == 1
