import numpy as np
import pytest
from sim.ledger import Ledger
from sim.mechanisms.base import Consequences


def test_fund_settle_releases():
    led = Ledger(N=2, T=3)
    esc, own = {}, {}
    led.fund(0, job=0, provider=1, amount=0.7, escrow=esc, owner=own)
    led.settle(0, esc, own, Consequences(), failed_jobs_of={})
    assert led.released[0, 1] == pytest.approx(0.7)
    assert led.profit()[1] == pytest.approx(0.7)
    led.check_conservation(escrow_outstanding=0.0)


def test_refund_reduces_release_and_credits_buyer():
    led = Ledger(N=1, T=2)
    esc, own = {}, {}
    led.fund(0, 0, 0, 1.0, esc, own)
    led.settle(0, esc, own, Consequences(refunds={0: 1.0}), failed_jobs_of={0: [0]})
    assert led.refunds[0, 0] == pytest.approx(1.0) and led.released[0, 0] == pytest.approx(0.0)
    assert led.buyer_credit() == pytest.approx(1.0)
    led.check_conservation(0.0)


def test_holdback_then_forfeit_and_release_single_booking():
    led = Ledger(N=1, T=4)
    esc, own = {}, {}
    led.fund(0, 0, 0, 1.0, esc, own); led.settle(0, esc, own, Consequences(), {})
    led.fund(1, 1, 0, 1.0, esc, own)
    led.settle(1, esc, own, Consequences(holdbacks={0: 0.4}), {})
    assert led.bond[0] == pytest.approx(0.4)
    assert led.released[1, 0] == pytest.approx(0.6)
    led.fund(2, 2, 0, 1.0, esc, own)
    led.settle(2, esc, own, Consequences(refunds={2: 1.0}, forfeits={0: 0.3}, releases={0: 0.05}),
               failed_jobs_of={0: [2]})
    assert led.bond[0] == pytest.approx(0.05)
    assert led.forfeits[2, 0] == pytest.approx(0.3)
    assert led.holdback_out[2, 0] == pytest.approx(0.05)
    assert led.buyer_credit() == pytest.approx(1.3)
    led.check_conservation(0.0)
    led.terminal_settlement()
    assert led.bond[0] == pytest.approx(0.0)
    assert led.profit()[0] == pytest.approx(1.0 + 0.6 + 0.0 + 0.05 + 0.05)
    led.check_conservation(0.0)


def test_forced_release_when_cap_shrinks():
    led = Ledger(N=1, T=8)
    esc, own = {}, {}
    for t in range(8):
        led.fund(t, t, 0, 1.0, esc, own)
        led.settle(t, esc, own, Consequences(holdbacks={0: 0.5}) if t > 0 else Consequences(), {})
        assert led.bond[0] <= led.recent_receipts()[0] + 1e-9
        led.check_conservation(0.0)
    assert led.bond[0] == pytest.approx(1.5)


def test_conservation_rejects_nan():
    led = Ledger(N=1, T=1)
    esc, own = {}, {}
    led.fund(0, 0, 0, 1.0, esc, own)
    led.released[0, 0] = float("nan")
    with pytest.raises(AssertionError):
        led.check_conservation(0.0)
