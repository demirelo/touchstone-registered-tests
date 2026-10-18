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


# ----------------------------------------------------------------------------------------------------------------- selection (amendment 3)
# select_audits(jobs_by_identity, audit_key, first_round, audits, served, targeting, k, t, L): the priority phase (served jobs of
# identities with 0 <= t - first_round < L, newest first, then audit key, then job index, up to k), then the residual r = k - q
# split ceil(r/2) targeted (T1 / T2 one job at a time) and floor(r/2) uniform by (audit_key, job index); pure.
def zero(ids):
    return {i: 0 for i in ids}


def test_t1_residual_orders_the_newest_identities_first_then_by_audit_key_when_nobody_is_fresh():
    jobs = {0: [0], 1: [1], 2: [2], 3: [3]}; key = np.array([0.1, 0.4, 0.3, 0.2]); fr = {0: 0, 1: 0, 2: 5, 3: 5}; one = {i: 1 for i in jobs}
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T1", 4, 20, 10) == [3, 2, 0, 1]      # k_t = 2 by (newest, key), k_u = 2 by key
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T1", 2, 20, 10) == [3, 0]            # one targeted (newest, lowest key), one uniform (lowest key among the rest)
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T1", 3, 20, 10) == [3, 2, 0]


def test_priority_phase_takes_fresh_identities_newest_first_before_the_split():
    jobs = {0: [0], 1: [1], 2: [2], 3: [3]}; key = np.array([0.1, 0.4, 0.3, 0.2]); fr = {0: 0, 1: 0, 2: 5, 3: 5}; one = {i: 1 for i in jobs}
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T1", 4, 7, 10) == [3, 2, 0, 1]       # all four fresh at t = 7: priority order (newest, key)
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T2", 2, 7, 10) == [3, 2]             # priority is targeting-independent
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T1", 3, 12, 10) == [3, 2, 0]         # 2 and 3 fresh (age 7), 0 and 1 not (age 12): priority then one targeted
    assert proposed.select_audits(jobs, key, fr, zero(jobs), one, "T2", 3, 12, 10) == [3, 2, 0]


@pytest.mark.parametrize("L", [3, 10, 20])
def test_freshness_ages_zero_one_l_minus_one_are_fresh_and_age_l_is_not(L):
    t = 30; fr = {0: t, 1: t - 1, 2: t - (L - 1), 3: t - L}; jobs = {i: [i] for i in fr}; key = np.array([0.4, 0.3, 0.2, 0.1]); one = {i: 1 for i in fr}
    assert proposed.select_audits(jobs, key, fr, zero(fr), one, "T1", 4, t, L) == [0, 1, 2, 3]          # ages 0, 1, L-1 by recency, then age L in the residual
    assert proposed.select_audits(jobs, key, fr, zero(fr), one, "T1", 3, t, L) == [0, 1, 2]
    assert proposed.select_audits(jobs, key, fr, zero(fr), one, "T2", 1, t, L) == [0]


def test_round_zero_priority_takes_the_whole_quota_among_all_served_jobs_by_key():
    rng = np.random.default_rng(0); key = rng.random(50); jobs = {i: [j for j in range(50) if j % 10 == i] for i in range(10)}
    chosen = proposed.select_audits(jobs, key, zero(range(10)), zero(range(10)), {i: 5 for i in range(10)}, "T1", 10, 0, 10)
    assert chosen == sorted(range(50), key=lambda j: (float(key[j]), j))[:10]


def test_a_six_job_newest_entrant_is_fully_audited_before_older_fresh_identities():
    rng = np.random.default_rng(1); key = rng.random(56)
    jobs = {i: [j for j in range(50) if j % 10 == i] for i in range(10)}; jobs[10] = list(range(50, 56))          # the entrant's six jobs
    fr = {**zero(range(10)), 10: 1}; served = {**{i: 5 for i in range(10)}, 10: 6}
    for targeting in ("T1", "T2"):
        chosen = proposed.select_audits(jobs, key, fr, zero(fr), served, targeting, 10, 1, 10)
        assert chosen[:6] == sorted(range(50, 56), key=lambda j: (float(key[j]), j)) and len(chosen) == 10 and len(set(chosen)) == 10
        assert chosen[6:] == sorted(range(50), key=lambda j: (float(key[j]), j))[:4]                              # the older fresh identities follow, by key


def test_simultaneous_entrants_share_the_quota_by_key_then_job_index():
    key = np.array([0.5] * 12); jobs = {10: list(range(0, 6)), 11: list(range(6, 12))}; fr = {10: 4, 11: 4}; served = {10: 6, 11: 6}
    assert proposed.select_audits(jobs, key, fr, zero(fr), served, "T1", 10, 4, 10) == list(range(10))           # equal keys: job index decides
    assert proposed.select_audits(jobs, key, fr, zero(fr), served, "T2", 12, 4, 10) == list(range(12))
    assert proposed.select_audits(jobs, key, fr, zero(fr), served, "T1", 13, 4, 10) == list(range(12))           # never more than the served jobs


def test_priority_set_below_equal_above_quota_and_empty_and_zero_quota():
    key = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6]); jobs = {0: [0, 1], 1: [2, 3], 2: [4, 5]}; served = {i: 2 for i in jobs}
    fr = {0: 9, 1: 0, 2: 0}                                                                                   # identity 0 fresh at t = 9, L = 10
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T1", 4, 9, 10) == [0, 1, 2, 3]        # below: q = 2, residual r = 2 (one targeted by key, one uniform)
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T1", 2, 9, 10) == [0, 1]              # equal: no residual
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T1", 1, 9, 10) == [0]                 # above: truncated by key
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T1", 3, 30, 10) == [0, 1, 2]          # empty: pure residual (k_t 2 by key with equal ages, k_u 1)
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T2", 0, 9, 10) == []


def test_residual_split_odd_and_even_under_both_variants():
    key = np.array([0.6, 0.5, 0.4, 0.3, 0.2, 0.1]); jobs = {0: [0, 1, 2], 1: [3, 4, 5]}; served = {0: 3, 1: 3}; fr = {0: 0, 1: 0}
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T1", 3, 30, 10) == [5, 4, 3]           # r = 3: two targeted by key, one uniform by key
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T1", 4, 30, 10) == [5, 4, 3, 2]
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T2", 3, 30, 10) == [5, 2, 4]           # T2: 5 (id 1), then id 0 has ratio 0 -> its lowest key 2, then uniform 4
    assert proposed.select_audits(jobs, key, fr, zero(jobs), served, "T2", 4, 30, 10) == [5, 2, 4, 3]


def test_t2_recomputes_the_ratio_after_every_selection_and_counts_the_priority_picks():
    jobs = {0: [0, 2], 1: [1, 3]}; key = np.array([0.1, 0.2, 0.3, 0.4]); audits = {0: 0, 1: 0}; served = {0: 2, 1: 2}
    assert proposed.select_audits(jobs, key, {0: 0, 1: 0}, audits, served, "T2", 3, 30, 10) == [0, 1, 2]
    assert audits == {0: 0, 1: 0}                                                                             # pure: the caller's counts are untouched
    key2 = np.array([0.1, 0.3, 0.2, 0.4])                                                                     # identity 0 owns the two smallest keys: a static order would pick [0, 2]
    assert proposed.select_audits(jobs, key2, {0: 0, 1: 0}, audits, served, "T2", 3, 30, 10) == [0, 1, 2]
    assert proposed.select_audits({0: [0, 1, 2], 1: [3]}, np.array([0.1, 0.2, 0.3, 0.9]), {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 3, 1: 1}, "T2", 4, 30, 10) == [0, 3, 1, 2]
    assert proposed.select_audits(jobs, key, {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 0, 1: 2}, "T2", 1, 30, 10) == [0]   # served 0 gives ratio 0; ties by key
    # the priority picks count: identity 0 fresh with two jobs audited in the priority phase, then T2 prefers identity 1 although identity 0 holds the lowest remaining key
    jobs3 = {0: [0, 1, 2], 1: [3]}; key3 = np.array([0.1, 0.2, 0.25, 0.9]); fr3 = {0: 29, 1: 0}; served3 = {0: 3, 1: 1}
    assert proposed.select_audits(jobs3, key3, fr3, zero(fr3), served3, "T2", 4, 30, 10) == [0, 1, 2, 3]        # q = 3 (all of identity 0), r = 1 targeted: only 3 remains
    assert proposed.select_audits({0: [0, 1, 2, 4], 1: [3]}, np.array([0.1, 0.2, 0.25, 0.9, 0.95]), {0: 29, 1: 0}, {0: 0, 1: 0}, {0: 4, 1: 1}, "T2", 5, 30, 10)[:4] == [0, 1, 2, 4]
    sel = proposed.select_audits({0: [0, 1, 4], 1: [3], 2: [2]}, np.array([0.1, 0.2, 0.25, 0.9, 0.95]), {0: 29, 1: 0, 2: 0}, {0: 0, 1: 0, 2: 0}, {0: 3, 1: 1, 2: 1}, "T2", 4, 30, 10)
    assert sel == [0, 1, 4, 2]                                                                                # after 3 priority audits on identity 0, T2 picks the lowest-key job among ratio-0 identities (job 2 of identity 2)


def test_select_audits_never_returns_more_than_the_served_jobs_or_a_duplicate():
    jobs = {0: [0], 1: [1]}; key = np.array([0.5, 0.4])
    for t in (0, 30):
        out = proposed.select_audits(jobs, key, {0: 0, 1: 0}, {0: 0, 1: 0}, {0: 1, 1: 1}, "T1", 6, t, 10)
        assert sorted(out) == [0, 1] and len(out) == 2


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


def test_rule_audits_a_sole_fresh_entrants_jobs_first_in_an_early_round_under_both_variants():
    cfg = locked_like(); rv = RecordingView(cfg.N, cfg.J, cfg.T)
    assignment = {j: j % 10 for j in range(44)}; assignment.update({j: 10 for j in range(44, 50)})          # identity 10: a six-job entrant
    for targeting in ("T1", "T2"):
        r = make("A", targeting, 0.16, 10); r.bind(cfg)
        mem = served_memory({**{i: 5 for i in range(10)}, 10: 6}, first_round={**{i: 0 for i in range(10)}, 10: 2})
        v = rv.view(2, audits_left=2480, memory=mem, N=11)
        chosen = r.audit(assignment, v)
        assert len(chosen) == 10 and set(range(44, 50)) <= set(chosen[:6]) and mem["audits"][10] == 6     # k = 10 at t = 2 under L = 10: all six jobs, first
    r = make("A", "T1", 0.16, 10); r.bind(cfg)
    mem = served_memory({**{i: 5 for i in range(10)}, 10: 6}, first_round={**{i: 0 for i in range(10)}, 10: 2})
    v = rv.view(12, audits_left=2380, memory=mem, N=11)                                                     # the entrant is 10 rounds old: no longer fresh
    chosen = r.audit(assignment, v)
    assert len(chosen) == 10 and len(set(chosen)) == 10


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
    first_round[3] = 5; first_round[7] = 5                                                              # two identities born in this round (t = 5): fresh, tied arrival
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
