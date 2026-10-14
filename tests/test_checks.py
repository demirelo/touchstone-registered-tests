import numpy as np
import pytest
from sim.checks import validate_assignment, validate_payments, validate_audits, validate_consequences
from sim.mechanisms.base import Offer, StateView, Consequences, AuditRecord


def view(N=3, caps=(1, 2, 1), banned=(0, 0, 0), t=0, audits_left=5):
    return StateView(t=t, T=10, N=N, audits_left=audits_left, audit_u=0.5, audit_key=np.zeros(4),
                     banned_until=np.array(banned), bond=np.zeros(N), capacity=np.array(caps),
                     escrow={}, history=(), memory={})


def test_assignment_rejects_abstainer_banned_capacity_and_bad_job():
    values = np.array([1.0, 1.0, 1.0, 1.0])
    offers = {0: Offer(0.9, 0.1), 1: Offer(0.9, 0.1)}
    validate_assignment({0: 0, 1: 1, 2: 1}, values, offers, view())
    with pytest.raises(ValueError, match="offer"):
        validate_assignment({0: 2}, values, offers, view())
    with pytest.raises(ValueError, match="banned"):
        validate_assignment({0: 0}, values, offers, view(banned=(5, 0, 0)))
    with pytest.raises(ValueError, match="capacity"):
        validate_assignment({0: 0, 1: 0}, values, offers, view())
    with pytest.raises(ValueError, match="job"):
        validate_assignment({7: 0}, values, offers, view())


def test_payments_cover_assignment_and_respect_acceptance():
    values = np.array([1.0, 0.5])
    offers = {0: Offer(0.8, 0.1)}
    validate_payments({0: 0.8}, {0: 0}, values, offers)
    with pytest.raises(ValueError, match="accept"):
        validate_payments({0: 0.81}, {0: 0}, values, offers)
    with pytest.raises(ValueError, match="payments"):
        validate_payments({}, {0: 0}, values, offers)
    with pytest.raises(ValueError, match="finite"):
        validate_payments({0: float("nan")}, {0: 0}, values, offers)


def test_audits_unique_served_within_allowance():
    validate_audits([0, 1], {0: 0, 1: 1}, view(audits_left=2))
    with pytest.raises(ValueError, match="unique"):
        validate_audits([0, 0], {0: 0, 1: 1}, view())
    with pytest.raises(ValueError, match="served"):
        validate_audits([3], {0: 0, 1: 1}, view())
    with pytest.raises(ValueError, match="allowance"):
        validate_audits([0, 1], {0: 0, 1: 1}, view(audits_left=1))


def test_consequences_require_failed_records_and_respect_caps():
    recs = (AuditRecord(job=0, provider=0, delivered=0.5, claim=0.9, failed=True),
            AuditRecord(job=1, provider=1, delivered=0.9, claim=0.9, failed=False))
    escrow, owner = {0: 0.8, 1: 0.8, 2: 0.8}, {0: 0, 1: 1, 2: 0}
    bond = np.array([0.5, 0.0, 0.0]); recent = np.array([1.0, 1.0, 0.0]); active = {0, 1}
    ok = lambda c: validate_consequences(c, recs, escrow, owner, bond, recent, active)
    ok(Consequences(refunds={0: 0.8}, bans={0: 10}, forfeits={0: 0.5}))
    for bad, msg in [
        (Consequences(refunds={1: 0.1}), "failed"), (Consequences(refunds={2: 0.1}), "failed"),
        (Consequences(bans={1: 5}), "failed"), (Consequences(bans={0: 51}), "ban"),
        (Consequences(bans={0: 2.5}), "integer"), (Consequences(holdbacks={0: 0.6}), "hold-back"),
        (Consequences(forfeits={0: 0.6}), "forfeit"), (Consequences(forfeits={1: 0.0001}), "forfeit"),
        (Consequences(forfeits={0: 0.3}, releases={0: 0.3}), "release"),
        (Consequences(refunds={0: float("nan")}), "finite"),
    ]:
        with pytest.raises(ValueError, match=msg):
            ok(bad)
