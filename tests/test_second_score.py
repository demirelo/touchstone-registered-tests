import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.base import Offer, StateView
from sim.mechanisms.second_score import SecondScore
from sim.policies.honest import HonestMax


def view(N, caps, J=1, tie=None):
    tie = np.zeros((J, N)) if tie is None else tie
    return StateView(t=0, T=1, N=N, audits_left=0, audit_u=0.5, audit_key=np.zeros(J),
                     banned_until=np.zeros(N, dtype=np.int64), bond=np.zeros(N), capacity=np.array(caps),
                     escrow={}, history=(), memory={"tie_key": tie})


def test_worked_example_payment_is_three():
    r = SecondScore(tol=0.12, L=10)
    offers = {0: Offer(1.0, 1.0), 1: Offer(1.0, 3.0)}
    v = view(2, (1, 1))
    asg = r.allocate(np.array([10.0]), offers, v)
    assert asg == {0: 0}
    assert r.price(asg, np.array([10.0]), offers, v)[0] == pytest.approx(3.0)


def test_single_bidder_pays_value_times_claim():
    r = SecondScore(tol=0.12, L=10)
    offers = {0: Offer(0.9, 0.5)}
    v = view(1, (1,))
    asg = r.allocate(np.array([2.0]), offers, v)
    assert r.price(asg, np.array([2.0]), offers, v)[0] == pytest.approx(1.8)


def test_negative_score_not_eligible_and_capacity_respected():
    r = SecondScore(tol=0.12, L=10)
    assert r.allocate(np.array([0.6]), {0: Offer(0.5, 1.0)}, view(1, (1,))) == {}
    offers = {0: Offer(1.0, 0.1), 1: Offer(1.0, 0.5)}
    asg = r.allocate(np.array([1.0, 1.0, 1.0]), offers, view(2, (1, 5), J=3))
    assert list(asg.values()).count(0) == 1 and list(asg.values()).count(1) == 2


def test_tie_broken_by_key():
    offers = {0: Offer(1.0, 0.5), 1: Offer(1.0, 0.5)}
    assert SecondScore(tol=0.12, L=10).allocate(np.array([1.0]), offers, view(2, (1, 1), tie=np.array([[0.9, 0.1]]))) == {0: 1}


def test_full_episode_audits_and_runs():
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=50, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                       providers=c.providers, alpha=c.alpha, budget=2.0)
    res = run_episode(cfg, SecondScore(tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    assert res.audits.sum() == 40 and res.W > 0
