"""Credibility comparator (design 3.3): threshold, finite-memory, and taper variants with S0, S1, S2 pacing."""
import itertools
import math

import numpy as np
import pytest

from sim.mechanisms.base import AuditRecord
from tests._proposed_fixtures import RecordingView
from tests._v2_profiles import CFG, run_full


def C(variant="thr", K=2, pacing="S1", M=None, tol=0.16, L=10):
    from sim.mechanisms.credibility import Credibility
    return Credibility(variant, K, tol, L, pacing, M)


def rec(job, provider, failed):
    return AuditRecord(job=job, provider=provider, delivered=0.5, claim=0.5, failed=failed)


def view(t, memory, escrow=None, audits_left=100):
    return RecordingView(CFG.N, CFG.J, CFG.T).view(t, audits_left=audits_left, memory=memory, escrow=escrow or {j: 1.0 for j in range(50)})


def test_batch_failure_resets_even_with_passes():
    from sim.mechanisms.credibility import passes_of
    r = C(); r.bind(CFG); mem = {}
    r.enforce((rec(0, 3, False), rec(1, 3, False)), view(4, mem))
    assert passes_of(mem, 3, 5, None) == 2
    r.enforce((rec(2, 3, False), rec(3, 3, True)), view(5, mem))
    assert passes_of(mem, 3, 6, None) == 0


def test_counts_from_start_of_round():
    from sim.mechanisms.credibility import passes_of
    r = C(); r.bind(CFG); mem = {}
    r.enforce((rec(0, 1, False),), view(2, mem))
    before = passes_of(mem, 1, 3, None)
    r.audit({0: 1, 1: 1, 2: 2}, view(3, mem))
    assert passes_of(mem, 1, 3, None) == before == 1


def test_ban_return_starts_at_zero():
    from sim.mechanisms.credibility import passes_of
    r = C(); r.bind(CFG); mem = {}
    for t in range(3):
        r.enforce((rec(t, 4, False),), view(t, mem))
    r.enforce((rec(9, 4, True),), view(3, mem))
    assert passes_of(mem, 4, 3 + 10 + 1, None) == 0          # the first round after the ban of L = 10


def test_thr_priority_then_residual_order():
    from sim.mechanisms.credibility import select_credibility
    # passes: identity 1 has 0, identity 2 has 1, identity 3 has 5 (proven at K = 2)
    p = {1: 0, 2: 1, 3: 5}
    by = {1: [0, 1], 2: [2], 3: [3, 4, 5]}
    keys = np.array([0.6, 0.2, 0.1, 0.9, 0.3, 0.4])
    # priority: unproven jobs by (p, key, job): 1 (p0, .2), 0 (p0, .6), 2 (p1, .1); residual r = 2: one targeted pick by (p + picks):
    # identities 1 and 2 have no jobs left, identity 3 (5 + 0) -> its lowest key job 4; then uniform: 5 (.4)
    assert select_credibility("thr", by, keys, p, k=5, K=2) == [1, 0, 2, 4, 5]
    # k = 2: only priority
    assert select_credibility("thr", by, keys, p, k=2, K=2) == [1, 0]


def test_residual_counts_picks_this_round():
    from sim.mechanisms.credibility import select_credibility
    p = {1: 3, 2: 4}                                          # both proven at K = 2; no priority phase
    by = {1: [0, 1, 2], 2: [3, 4]}
    keys = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    # r = 4: two targeted picks: (3 + 0) -> job 0; then identity 1 has 3 + 1 = 4 = identity 2's 4 + 0: tie broken by key -> job 1 (.2)
    # then two uniform: 2 (.3), 3 (.4)
    assert select_credibility("thr", by, keys, p, k=4, K=2) == [0, 1, 2, 3]
    # equal counts tell dynamic from static order: (3 + 0) vs (3 + 0) -> job 0 (.1); then identity 1 has 4 > 3 -> job 3 (.4);
    # then two uniform: 1 (.2), 2 (.3). An order that ignores this round's picks gives [0, 1, 2, 3]
    assert select_credibility("thr", by, keys, {1: 3, 2: 3}, k=4, K=2) == [0, 3, 1, 2]


def test_mem_window_boundary():
    from sim.mechanisms.credibility import passes_of
    r = C("mem", K=2, M=5); r.bind(CFG); mem = {}
    for t in (1, 2, 3, 4):
        r.enforce((rec(t, 6, False),), view(t, mem))
    # at t = 7, M = 5: window [max(f + 1, 2), 7) = [2, 7): rounds 2, 3, 4 count, round 1 (= t - M - 1) does not
    assert passes_of(mem, 6, 7, 5) == 3
    r.enforce((rec(20, 6, True),), view(5, mem))             # failure at round 5
    r.enforce((rec(21, 6, False),), view(6, mem))
    assert passes_of(mem, 6, 7, 5) == 1                      # only round 6; rounds <= f = 5 excluded


def test_taper_weights_and_race():
    from sim.mechanisms.credibility import select_credibility
    p = {1: 0, 2: 6}
    by = {1: [0, 1], 2: [2, 3]}
    keys = np.array([0.5, 0.9, 0.2, 0.3])
    K = 6
    w = {0: 1.0, 1: 1.0, 2: 0.5, 3: 0.5}
    race = sorted(range(4), key=lambda j: (-math.log(keys[j]) / w[j], j))
    assert select_credibility("taper", by, keys, p, k=3, K=K) == race[:3]


def test_taper_new_identity_weight_one():
    from sim.mechanisms.credibility import taper_weight
    assert taper_weight(0, 6) == 1.0 and taper_weight(6, 6) == 0.5 and taper_weight(18, 6) == 0.25


@pytest.mark.parametrize("pacing,cell", [("S0", "F000"), ("S1", "F111"), ("S2", "R4")])
def test_pacing_variants_match_factorial_counts(pacing, cell):
    from sim.mechanisms.factorial import make_factorial
    a = run_full(CFG, C("thr", 6, pacing), "honest", 2000)
    b = run_full(CFG, make_factorial(cell, 0.16, 10), "honest", 2000)
    assert a.audits.tolist() == b.audits.tolist()


def test_names():
    assert C().name == "C-thr" and C(pacing="S0").name == "C-thr/S0" and C("taper", pacing="S2").name == "C-taper/S2"
    assert C("mem", M=20).name == "C-mem"
    with pytest.raises(ValueError):
        C("mem")                                              # M required
    with pytest.raises(ValueError):
        C("bogus")


def test_selection_grid_order_and_size():
    from sim.mechanisms.credibility import SELECTION_GRID
    assert SELECTION_GRID == ([{"variant": "thr", "K": k, "M": None} for k in (2, 6, 12, 24)]
                              + [{"variant": "mem", "K": k, "M": m} for k, m in ((2, 20), (2, 50), (6, 20), (6, 50))]
                              + [{"variant": "taper", "K": k, "M": None} for k in (2, 6, 12, 24)])


def test_make_credibility():
    from sim.mechanisms.credibility import make_credibility
    r = make_credibility({"variant": "mem", "K": 6, "M": 50, "tol": 0.16, "L": 10, "pacing": "S2"})
    assert (r.variant, r.K, r.M, r.L, r.name) == ("mem", 6, 50, 10, "C-mem/S2")
    assert r.describe()["parameters"] == {"audit_tolerance": 0.16, "ban_length": 10}


def test_relabelling_invariance_credibility():
    from sim.mechanisms.credibility import select_credibility
    rng = np.random.default_rng(3)
    for variant in ("thr", "taper"):
        for _ in range(50):
            owners = rng.integers(0, 4, size=12); by = {}
            for j, i in enumerate(owners):
                by.setdefault(int(i), []).append(j)
            p = {i: int(rng.integers(0, 8)) for i in by}; keys = rng.random(12); k = int(rng.integers(0, 13))
            perm = {i: 50 + q for i, q in zip(by, rng.permutation(len(by)))}
            assert select_credibility(variant, by, keys, p, k=k, K=6) == select_credibility(
                variant, {perm[i]: v for i, v in by.items()}, keys, {perm[i]: v for i, v in p.items()}, k=k, K=6)


@pytest.mark.parametrize("variant,M", [("thr", None), ("mem", 20), ("taper", None)])
@pytest.mark.parametrize("pacing", ["S0", "S1", "S2"])
def test_no_audit_when_budget_or_service_empty_credibility(variant, M, pacing):
    r = C(variant, 6, pacing, M); r.bind(CFG)
    assert r.audit({}, view(5, {})) == []
    assert r.audit({0: 1, 1: 2}, view(5, {}, audits_left=0)) == []


@pytest.mark.parametrize("variant,M", [("thr", None), ("mem", 20), ("taper", None)])
def test_runs_and_never_exceeds_served(variant, M):
    res = run_full(CFG, C(variant, 6, "S1", M), "replacement", 2000)
    assert (res.audits <= res.served.sum(axis=1)).all() and res.audits.sum() > 0
