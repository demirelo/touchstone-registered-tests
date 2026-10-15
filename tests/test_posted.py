import numpy as np
import pytest
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.base import Offer, StateView


def view(N, caps, t=0, banned=None, tie=None, J=1):
    tie = np.zeros((J, N)) if tie is None else tie
    return StateView(t=t, T=5, N=N, audits_left=0, audit_u=0.5, audit_key=np.zeros(J),
                     banned_until=np.zeros(N, dtype=np.int64) if banned is None else np.array(banned),
                     bond=np.zeros(N), capacity=np.array(caps), escrow={}, history=(), memory={"tie_key": tie})


def test_tier_boundaries():
    r = PostedPrices(0.2, 0.4, 0.6)
    assert r.tier_of(0.0) == 0 and r.tier_of(0.49) == 0
    assert r.tier_of(0.5) == 1 and r.tier_of(0.79) == 1
    assert r.tier_of(0.8) == 2 and r.tier_of(1.0) == 2


def test_prefers_highest_tier_and_respects_acceptance():
    r = PostedPrices(0.2, 0.4, 0.6)
    offers = {0: Offer(0.4, 0.0), 1: Offer(0.9, 0.0)}
    asg = r.allocate(np.array([0.7]), offers, view(2, (1, 1)))
    assert asg == {0: 1}
    assert r.price(asg, np.array([0.7]), offers, view(2, (1, 1))) == {0: pytest.approx(0.6)}


def test_no_acceptable_tier_leaves_job_unserved():
    assert PostedPrices(0.5, 0.7, 0.9).allocate(np.array([0.6]), {0: Offer(0.6, 0.0)}, view(1, (1,))) == {}


def test_banned_provider_not_eligible():
    assert PostedPrices(0.2, 0.4, 0.6).allocate(np.array([1.0]), {0: Offer(0.9, 0.0)}, view(1, (1,), t=2, banned=[4])) == {}


def test_tie_break_uses_smallest_key():
    offers = {0: Offer(0.9, 0.0), 1: Offer(0.9, 0.0)}
    assert PostedPrices(0.2, 0.4, 0.6).allocate(np.array([1.0]), offers, view(2, (1, 1), tie=np.array([[0.7, 0.2]]))) == {0: 1}


def test_describe_fields():
    d = PostedPrices(0.2, 0.4, 0.6).describe()
    assert set(d) >= {"allocation_order", "eligibility", "payment", "audit_selection", "audit_tolerance", "failed_audit", "ban_length", "holdback", "parameters"}
