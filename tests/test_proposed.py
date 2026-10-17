"""The proposed rule's contract (amendment 2, task A5), written against the registered design before the module
exists; collected and skipped until Phase B creates sim/mechanisms/proposed.py."""
import math
from pathlib import Path

import numpy as np
import pytest

proposed = pytest.importorskip("sim.mechanisms.proposed")

from sim.config import MarketConfig, ProviderParams  # noqa: E402
from sim.describe import NOT_EXPRESSIBLE, describe_record, uses_not_expressible  # noqa: E402
from sim.market import run_episode  # noqa: E402
from sim.mechanisms.base import AuditRecord  # noqa: E402
from sim.mechanisms.posted_audit import PostedRandomAudit  # noqa: E402
from sim.mechanisms.second_score import SecondScore  # noqa: E402
from sim.policies.fixed_cheat import FixedCheat  # noqa: E402
from sim.policies.honest import HonestMax  # noqa: E402
from sim.policies.identity import IdentityReplacement  # noqa: E402
from tests._proposed_fixtures import RecordingView, offers_for, run_with_memory  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PRICES = {"P1": 0.25, "P2": 0.40, "P3": 0.55}
A_TOT, J, T = 2500, 50, 200


def make(allocation="A", targeting="T1", tol=0.12, L=10, prices=True):
    p = {"allocation": allocation, "targeting": targeting, "tol": tol, "L": L}
    if allocation == "B" and prices:
        p.update(PRICES)
    return proposed.make(p)


def locked_like(budget=125.0, T=200, N=10, J=50):
    c = MarketConfig.default()
    return MarketConfig(N=N, J=J, T=T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max, providers=c.providers[:N], alpha=0.05, budget=budget)


def tiny(budget=0.5, T=20):
    return locked_like(budget=budget, T=T)


# ----------------------------------------------------------------------------------------------------------------- schedule
@pytest.mark.parametrize("L, reserve, early, lo, hi", [(10, 500, 2000, 10, 11), (3, 150, 2350, 11, 12), (20, 1000, 1500, 8, 9)])
def test_schedule_arithmetic_at_the_locked_market(L, reserve, early, lo, hi):
    quotas = [proposed.audit_quota(t, T, L, J, A_TOT, 0) for t in range(T - L)]
    assert set(quotas) <= {lo, hi} and sum(quotas) == early == A_TOT - reserve
    assert all(proposed.terminal(t, T, L) == (t >= T - L) for t in range(T))
    assert proposed.audit_quota(T - L, T, L, J, A_TOT, 7) >= J           # terminal rounds: every served job, capped by the caller


def test_carry_adds_to_the_next_available_quota():
    q0 = proposed.audit_quota(0, T, 10, J, A_TOT, 0)
    assert proposed.audit_quota(1, T, 10, J, A_TOT, 7) == proposed.audit_quota(1, T, 10, J, A_TOT, 0) + 7 and q0 == 10


def test_split_counts():
    assert proposed.split_counts(13) == (7, 6) and proposed.split_counts(1) == (1, 0) and proposed.split_counts(0) == (0, 0)


# ----------------------------------------------------------------------------------------------------------------- selection
def test_t1_orders_the_newest_identities_first_then_by_audit_key():
    jobs = {0: [0], 1: [1], 2: [2], 3: [3]}; key = np.array([0.1, 0.4, 0.3, 0.2])
    first_round = {0: 0, 1: 0, 2: 5, 3: 5}
    chosen = proposed.select_audits(jobs, key, first_round, {i: 0 for i in jobs}, {i: 1 for i in jobs}, "T1", 4, 0)
    assert chosen == [3, 2, 0, 1]
    assert proposed.select_audits(jobs, key, first_round, {i: 0 for i in jobs}, {i: 1 for i in jobs}, "T1", 2, 0) == [3, 2]
    assert proposed.select_audits(jobs, key, first_round, {i: 0 for i in jobs}, {i: 1 for i in jobs}, "T1", 1, 1) == [3, 0]   # the uniform half by key among the rest


def test_t2_recomputes_the_ratio_after_every_selection_and_breaks_zero_history_ties_by_key():
    jobs = {0: [0, 2], 1: [1, 3]}; key = np.array([0.1, 0.2, 0.3, 0.4])
    audits = {0: 0, 1: 0}; served = {0: 2, 1: 2}
    assert proposed.select_audits(jobs, key, {0: 0, 1: 0}, audits, served, "T2", 2, 0) == [0, 1]
    assert proposed.select_audits(jobs, key, {0: 0, 1: 0}, audits, served, "T2", 2, 1) == [0, 1, 2]
    assert audits == {0: 0, 1: 0}                                                       # pure: the caller's counts are untouched
    assert proposed.select_audits(jobs, key, {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 0, 1: 2}, "T2", 1, 0) == [0]   # served 0 gives ratio 0; ties by key
    key2 = np.array([0.1, 0.3, 0.2, 0.4])                                                   # identity 0 owns the two smallest keys: a static order would pick [0, 2]
    assert proposed.select_audits(jobs, key2, {0: 0, 1: 0}, audits, served, "T2", 2, 0) == [0, 1]
    assert proposed.select_audits({0: [0, 1, 2], 1: [3]}, np.array([0.1, 0.2, 0.3, 0.9]), {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 3, 1: 1}, "T2", 3, 0) == [0, 3, 1]


def test_select_audits_never_returns_more_than_the_served_jobs():
    jobs = {0: [0], 1: [1]}; key = np.array([0.5, 0.4])
    assert sorted(proposed.select_audits(jobs, key, {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 1, 1: 1}, "T1", 3, 3)) == [0, 1]


# ----------------------------------------------------------------------------------------------------------------- the rule in a round
def served_memory(served: dict, first_round: dict | None = None, audits: dict | None = None, carry: int = 0) -> dict:
    return {"first_round": dict(first_round or {i: 0 for i in served}), "audits": dict(audits or {i: 0 for i in served}), "served": dict(served),
            "quota_carry": int(carry)}


def test_undersubscribed_round_carries_and_the_next_full_round_spends_it():
    cfg = locked_like(); r = make("A", "T1", 0.12, 10); r.bind(cfg)
    rv = RecordingView(cfg.N, cfg.J, cfg.T)
    mem = served_memory({0: 3})
    v0 = rv.view(0, audits_left=A_TOT, memory=mem)
    chosen = r.audit({0: 0, 1: 0, 2: 0}, v0)
    assert len(chosen) == 3 and mem["quota_carry"] == 10 - 3 and mem["audits"][0] == 3
    mem["served"] = {i: 5 for i in range(10)}; mem["first_round"] = {i: 0 for i in range(10)}; mem["audits"] = {i: 0 for i in range(10)}
    assignment = {j: j % 10 for j in range(50)}
    v1 = rv.view(1, audits_left=A_TOT - 3, memory=mem)
    chosen = r.audit(assignment, v1)
    assert len(chosen) == (21 - 10) + 7 and mem["quota_carry"] == 0 and len(set(chosen)) == len(chosen)


def test_terminal_rounds_audit_every_served_job_up_to_audits_left_and_carry_nothing():
    cfg = locked_like(); r = make("A", "T2", 0.12, 10); r.bind(cfg)
    rv = RecordingView(cfg.N, cfg.J, cfg.T)
    assignment = {j: j % 10 for j in range(50)}
    mem = served_memory({i: 5 for i in range(10)}, carry=7)
    assert len(r.audit(assignment, rv.view(190, audits_left=30, memory=mem))) == 30 and mem["quota_carry"] == 0
    mem = served_memory({i: 5 for i in range(10)}, carry=7)
    assert sorted(r.audit(assignment, rv.view(199, audits_left=600, memory=mem))) == list(range(50)) and mem["quota_carry"] == 0


def test_audits_never_exceed_audits_left_in_an_early_round():
    cfg = locked_like(); r = make("A", "T1", 0.12, 3); r.bind(cfg)
    rv = RecordingView(cfg.N, cfg.J, cfg.T)
    mem = served_memory({i: 5 for i in range(10)})
    assert len(r.audit({j: j % 10 for j in range(50)}, rv.view(0, audits_left=4, memory=mem))) == 4


def test_allocation_updates_served_and_sets_first_round_once():
    cfg = locked_like(); r = make("A", "T1", 0.12, 10); r.bind(cfg)
    rv = RecordingView(cfg.N, cfg.J, cfg.T); mem = {}
    values = np.linspace(1.4, 0.6, cfg.J)
    offers = offers_for({i: 0.9 for i in range(10)}, {i: 0.1 * (i + 1) for i in range(10)})
    v3 = rv.view(3, audits_left=A_TOT, memory=mem)
    a = r.allocate(values, offers, v3)
    assert mem["first_round"] == {i: 3 for i in range(10)} and sum(mem["served"].values()) == len(a) and all(mem["served"][i] <= 6 for i in range(10))
    v7 = rv.view(7, audits_left=A_TOT, memory=mem)
    r.allocate(values, offers_for({i: 0.9 for i in range(10)}, {i: 0.1 * (i + 1) for i in range(10)}), v7)
    assert mem["first_round"] == {i: 3 for i in range(10)}                               # never reset


def test_first_round_of_a_replacement_identity_is_the_round_of_its_first_offer():
    cfg = tiny(budget=2.0, T=20); r = make("A", "T1", 0.12, 3)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[4] = IdentityReplacement(FixedCheat(u=0.0, m=1.0, s=0.0, w=0.0, clip=0))
    res, mem = run_with_memory(cfg, r, pols, 0)
    assert res.n_identities > cfg.N, "the fixture must produce at least one replacement"
    for i in range(cfg.N, res.n_identities):
        assert mem["first_round"][i] == res.identity_round[i]


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_allocation_a_equals_b3_and_b_equals_b2_with_zero_audit_budget(seed):
    cfg = tiny(budget=0.0)
    pols = [HonestMax() for _ in range(cfg.N)]
    for mine, theirs in ((make("A", "T1", 0.12, 10), SecondScore(tol=0.12, L=10)), (make("B", "T1", 0.12, 10), PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10))):
        a, b = run_episode(cfg, mine, pols, seed), run_episode(cfg, theirs, pols, seed)
        for ra, rb in zip(a.history, b.history):
            assert dict(ra.assignment) == dict(rb.assignment)
            assert all(math.isclose(ra.payments[j], rb.payments[j], rel_tol=0, abs_tol=1e-12) for j in ra.assignment)
            assert ra.audits == () and rb.audits == ()


def test_enforcement_refunds_the_escrow_and_bans_l_rounds():
    cfg = locked_like(); r = make("A", "T1", 0.12, 20); r.bind(cfg)
    rv = RecordingView(cfg.N, cfg.J, cfg.T)
    v = rv.view(5, audits_left=A_TOT, escrow={0: 0.7, 1: 0.6}, memory=served_memory({0: 1, 1: 1}))
    recs = (AuditRecord(job=0, provider=0, delivered=0.5, claim=0.9, failed=True), AuditRecord(job=1, provider=1, delivered=0.9, claim=0.9, failed=False))
    cons = r.enforce(recs, v)
    assert cons.refunds == {0: 0.7} and cons.bans == {0: 20} and not cons.holdbacks and not cons.forfeits


def test_describe_record_and_module_rules():
    from sim.claimcheck import check_proposed_module, verify_describe_record
    for r in (make("A", "T1", 0.14, 3), make("B", "T2", 0.16, 20)):
        rec = describe_record(r)
        assert rec["audit_selection"] == NOT_EXPRESSIBLE and uses_not_expressible(rec)
        assert rec["parameters"]["audit_tolerance"] == r.tol and rec["parameters"]["ban_length"] == r.L
        assert verify_describe_record(rec, r) == []
    assert check_proposed_module(ROOT / "sim" / "mechanisms" / "proposed.py", ROOT, params={"allocation": "A", "targeting": "T1", "tol": 0.12, "L": 10}) == []


@pytest.mark.parametrize("bad", [{"allocation": "B", "targeting": "T1", "tol": 0.12, "L": 10}, {"allocation": "A", "targeting": "T1", "tol": 0.13, "L": 10},
                                 {"allocation": "A", "targeting": "T1", "tol": 0.12, "L": 7}, {"allocation": "C", "targeting": "T1", "tol": 0.12, "L": 10},
                                 {"allocation": "A", "targeting": "T3", "tol": 0.12, "L": 10}, {"allocation": "A", "targeting": "T1", "tol": 0.12}])
def test_make_refuses_parameters_outside_the_registered_grid(bad):
    with pytest.raises(ValueError):
        proposed.make(bad)


def test_name_and_attributes():
    r = make("B", "T2", 0.16, 20)
    assert proposed.Proposed.name == "proposed" and r.name == "proposed" and r.tol == 0.16 and r.L == 20
    assert r.allocation == "B" and r.targeting == "T2" and r.prices == (0.25, 0.40, 0.55) and make("A").prices is None


def test_relabeling_a_permutation_of_identities_permutes_the_allocation_and_the_audit_choice():
    cfg = locked_like(); rng = np.random.default_rng(3)
    perm = rng.permutation(cfg.N); inv = np.argsort(perm)
    values = rng.uniform(0.6, 1.4, cfg.J); claims = rng.uniform(0.5, 1.0, cfg.N); bids = rng.uniform(0.0, 0.3, cfg.N)
    tie = rng.random((cfg.J, cfg.N)); key = rng.random(cfg.J); cap = rng.integers(1, 7, cfg.N)
    first_round = {i: int(rng.integers(0, 5)) for i in range(cfg.N)}; audits = {i: int(rng.integers(0, 3)) for i in range(cfg.N)}
    for targeting in ("T1", "T2"):
        for alloc in ("A", "B"):
            r, rp = make(alloc, targeting, 0.12, 10), make(alloc, targeting, 0.12, 10); r.bind(cfg); rp.bind(cfg)
            rv = RecordingView(cfg.N, cfg.J, cfg.T)
            mem = {"first_round": dict(first_round), "audits": dict(audits), "served": {i: 0 for i in range(cfg.N)}, "quota_carry": 0}
            memp = {"first_round": {int(perm[i]): first_round[i] for i in range(cfg.N)}, "audits": {int(perm[i]): audits[i] for i in range(cfg.N)},
                    "served": {i: 0 for i in range(cfg.N)}, "quota_carry": 0}
            v = rv.view(5, audits_left=A_TOT, memory=mem, audit_key=key, capacity=cap, tie_key=tie)
            vp = rv.view(5, audits_left=A_TOT, memory=memp, audit_key=key, capacity=cap[inv], tie_key=tie[:, inv])
            a = r.allocate(values, offers_for({i: claims[i] for i in range(cfg.N)}, {i: bids[i] for i in range(cfg.N)}), v)
            ap = rp.allocate(values, offers_for({int(perm[i]): claims[i] for i in range(cfg.N)}, {int(perm[i]): bids[i] for i in range(cfg.N)}), vp)
            assert {j: int(perm[i]) for j, i in a.items()} == ap
            assert r.audit(a, v) == rp.audit(ap, vp)
