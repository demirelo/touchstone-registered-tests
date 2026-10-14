import numpy as np
import pytest
from sim.config import MarketConfig
from sim.policies.base import ProviderView, ProviderHistory, Action, validate_action
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.twin import Twin
from sim.mechanisms.base import Offer


def view(i=0, t=0, seed=0):
    cfg = MarketConfig.default()
    return ProviderView(i=i, params=cfg.providers[i], t=t, posted_prices=None, history=ProviderHistory(), policy_seed=seed)


def test_honest_max_claims_effort_bids_cost():
    p = MarketConfig.default().providers[3]
    a = HonestMax().act(view(i=3))
    assert a.effort == pytest.approx(p.q_max) and a.offer.claim == pytest.approx(p.q_max)
    assert a.offer.bid == pytest.approx(p.a + p.b * p.q_max) and a.exit is False


def test_fixed_cheat_knobs_and_domains():
    p = MarketConfig.default().providers[0]   # q_max 0.6
    a = FixedCheat(u=0.5, m=0.4, s=0.1, w=0.5, clip=0).act(view(i=0))
    assert a.effort == pytest.approx(0.3) and a.offer.claim == pytest.approx(0.6)
    assert a.offer.bid == pytest.approx(1.5 * (p.a + p.b * 0.3))
    for bad in (dict(u=-0.1, m=0, s=0, w=0, clip=0), dict(u=0, m=1.1, s=0, w=0, clip=0),
                dict(u=0, m=0, s=0.4, w=0, clip=0), dict(u=0, m=0, s=0, w=2.5, clip=0),
                dict(u=0, m=0, s=0, w=0, clip=2), dict(u=0, m=0, s=0, w=0, clip=0.5)):
        with pytest.raises(ValueError):
            FixedCheat(**bad)


def test_clip_knob_and_twin_never_inflate():
    a = FixedCheat(u=0.5, m=0.9, s=0.0, w=0.0, clip=1).act(view(i=0))
    assert a.offer.claim <= a.effort + 1e-12
    base = FixedCheat(u=0.0, m=1.0, s=0.0, w=0.0, clip=0)
    raw, tw = base.act(view(i=0)), Twin(base).act(view(i=0))
    assert raw.offer.claim > raw.effort
    assert tw.effort == pytest.approx(raw.effort) and tw.offer.claim == pytest.approx(raw.effort)
    assert tw.offer.bid == pytest.approx(raw.offer.bid)


def test_honest_max_equals_its_twin():
    for i in range(10):
        assert HonestMax().act(view(i=i)) == Twin(HonestMax()).act(view(i=i))


def test_validate_action():
    p = MarketConfig.default().providers[0]
    validate_action(Action(effort=0.6, offer=Offer(0.5, 0.1)), p)
    for bad in (Action(effort=0.61, offer=Offer(0.5, 0.1)), Action(effort=-0.01, offer=None), Action(effort=float("nan"), offer=None)):
        with pytest.raises(ValueError):
            validate_action(bad, p)
    with pytest.raises(NotImplementedError):
        validate_action(Action(effort=0.5, offer=None, exit=True), p)


def test_view_rng_is_cached_and_seeded():
    v = view(seed=5)
    x1, x2 = v.rng.random(), v.rng.random()
    ref = np.random.default_rng(5)
    assert x1 == ref.random() and x2 == ref.random()
