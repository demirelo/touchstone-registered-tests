import numpy as np
import pytest
from sim.mechanisms.base import Offer, StateView, Consequences, AuditRecord, L_MAX, H_MAX


def test_offer_rejects_effort_and_bad_ranges():
    with pytest.raises(TypeError):
        Offer(claim=0.8, bid=0.3, effort=0.7)  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        Offer(claim=1.2, bid=0.3)
    with pytest.raises(ValueError):
        Offer(claim=0.5, bid=-0.1)
    with pytest.raises(ValueError):
        Offer(claim=float("nan"), bid=0.0)


def mkview(t=0, banned=(0, 0), caps=(1, 1)):
    return StateView(t=t, T=5, N=2, audits_left=0, audit_u=0.5, audit_key=np.zeros(1),
                     banned_until=np.array(banned, dtype=np.int64), bond=np.zeros(2),
                     capacity=np.array(caps), escrow={}, history=(), memory={})


def test_state_view_arrays_are_read_only():
    v = mkview()
    with pytest.raises(ValueError):
        v.banned_until[0] = 9
    with pytest.raises(ValueError):
        v.bond[0] = 1.0
    with pytest.raises(ValueError):
        v.capacity[0] = 0
    v.memory["x"] = 1


def test_state_view_is_active():
    assert not mkview(t=3, banned=(4, 0)).is_active(0)
    assert mkview(t=4, banned=(4, 0)).is_active(0)


def test_constants_and_defaults():
    assert L_MAX == 50 and H_MAX == 3
    c = Consequences()
    assert c.refunds == {} and c.bans == {} and c.holdbacks == {} and c.forfeits == {} and c.releases == {}
    assert AuditRecord(job=1, provider=2, delivered=0.7, claim=0.9, failed=True).failed
