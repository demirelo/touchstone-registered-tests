"""Factorial rules F000-F111 and R4 (design 3.2, 3.4): regression oracles B3, R3, and the 46694cb predecessor; pacing,
selection, and admissibility properties."""
import itertools

import numpy as np
import pytest

from sim.mechanisms import proposed
from sim.mechanisms.audit_random import spread_audit_count
from sim.mechanisms.second_score import SecondScore
from tests._v2_profiles import CFG, COMMON_GRID, PROFILE_NAMES, market, run_full, fingerprint
from tests.oracles import predecessor_46694cb as pred

SEEDS = [pytest.param(2000)] + [pytest.param(s, marks=pytest.mark.slow) for s in (2001, 2002, 2003, 2004)]
CELLS = ["F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111", "R4"]


def make(name, tol=0.16, L=10):
    from sim.mechanisms.factorial import make_factorial
    return make_factorial(name, tol, L)


@pytest.mark.parametrize("tol,L", COMMON_GRID)
@pytest.mark.parametrize("profile", PROFILE_NAMES)
@pytest.mark.parametrize("seed", SEEDS)
def test_f000_equals_b3(tol, L, profile, seed):
    assert fingerprint(run_full(CFG, make("F000", tol, L), profile, seed)) == fingerprint(run_full(CFG, SecondScore(tol, L), profile, seed))


@pytest.mark.parametrize("tol,L", COMMON_GRID)
@pytest.mark.parametrize("profile", PROFILE_NAMES)
@pytest.mark.parametrize("seed", SEEDS)
def test_f111_equals_r3(tol, L, profile, seed):
    assert fingerprint(run_full(CFG, make("F111", tol, L), profile, seed)) == fingerprint(run_full(CFG, proposed.Proposed("A", "T1", tol, L), profile, seed))


@pytest.mark.parametrize("tol,L", COMMON_GRID)
@pytest.mark.parametrize("profile", PROFILE_NAMES)
@pytest.mark.parametrize("seed", SEEDS)
def test_f011_equals_predecessor(tol, L, profile, seed):
    assert fingerprint(run_full(CFG, make("F011", tol, L), profile, seed)) == fingerprint(run_full(CFG, pred.Proposed("A", "T1", tol, L), profile, seed))


def test_names():
    assert [make(n).name for n in CELLS] == CELLS
    with pytest.raises(ValueError):
        make("F112")


def _round(first_round, by_identity, keys, t=30, L=10):
    return dict(jobs_by_identity=by_identity, audit_key=np.asarray(keys, dtype=float), first_round=first_round, t=t, L=L)


def test_p1_g0_residual_is_uniform():
    from sim.mechanisms.factorial import select
    # identity 7 is fresh (born 25); identities 1 and 2 are established, 2 newer than 1
    r = _round({7: 25, 1: 0, 2: 10}, {7: [0], 1: [1, 2], 2: [3, 4]}, [0.9, 0.5, 0.1, 0.2, 0.3])
    assert select(**r, k=3, P=1, G=0) == [0, 2, 3]            # priority job 0, then uniform by key: 2 (0.1), 3 (0.2)
    assert select(**r, k=3, P=1, G=1) == [0, 3, 2]            # T1 takes the newest established identity's lowest key first
    assert select(**r, k=3, P=0, G=0) == [2, 3, 4]


def test_select_matches_proposed_when_p1_g1():
    from sim.mechanisms.factorial import select
    rng = np.random.default_rng(1)
    for _ in range(200):
        n_id = int(rng.integers(1, 6)); jobs = list(range(int(rng.integers(1, 15))))
        owners = rng.integers(0, n_id, size=len(jobs))
        by = {}
        for j, i in zip(jobs, owners):
            by.setdefault(int(i), []).append(j)
        fr = {i: int(rng.integers(0, 40)) for i in by}; keys = rng.random(len(jobs)); k = int(rng.integers(0, len(jobs) + 2))
        want = proposed.select_audits(by, keys, fr, {}, {}, "T1", k, 40, 10)
        assert select(by, keys, fr, 40, 10, k=k, P=1, G=1) == want


def test_r4_reserve_is_half_allowance():
    cfg = market(rho=1.0)
    A = int(np.floor(cfg.budget / cfg.alpha + 1e-12)); L = 10
    early = lambda res: int(res.audits[: cfg.T - L].sum())
    r3 = run_full(cfg, make("F111"), "honest", 2000); r4 = run_full(cfg, make("R4"), "honest", 2000)
    assert early(r3) == max(0, A - min(cfg.J * L, A))
    assert early(r4) == A - min(cfg.J * L, A // 2)
    assert early(r4) > 0


class Spy:
    """Records (expected count, audits) per round: the expected count from the frozen schedule functions."""

    def __init__(self, rule):
        self.rule, self.rows = rule, []
        self.name, self.tol = rule.name, rule.tol

    def bind(self, cfg):
        self.rule.bind(cfg); self.cfg = cfg

    def allocate(self, v, o, view):
        return self.rule.allocate(v, o, view)

    def price(self, a, v, o, view):
        return self.rule.price(a, v, o, view)

    def audit(self, assignment, view):
        r, cfg = self.rule, self.cfg
        n = len(assignment); A = int(np.floor(cfg.budget / cfg.alpha + 1e-12))
        if r.S == 0:
            cap = max(1, int(np.floor(2.0 * cfg.budget / (cfg.T * cfg.alpha))))
            k = spread_audit_count(view.audits_left, view.t, cfg.T, n, cap, view.audit_u)
        else:
            carry = int(view.memory.get("quota_carry", 0)); res = min(cfg.J * r.L, A if r.reserve == "full" else A // 2)
            if view.t >= cfg.T - r.L:
                k_av = min(n, A)
            else:
                E = A - res; er = cfg.T - r.L; C = lambda t: 0 if t < 0 else (E * (t + 1)) // er
                k_av = C(view.t) - C(view.t - 1) + carry
            k = max(0, min(k_av, n, int(view.audits_left)))
        out = r.audit(assignment, view)
        self.rows.append((k, n, int(view.audits_left), out))
        return out

    def enforce(self, rec, view):
        return self.rule.enforce(rec, view)

    def describe(self):
        return self.rule.describe()


@pytest.mark.parametrize("name", CELLS)
@pytest.mark.parametrize("profile", ["honest", "replacement", "empty_rounds"])
def test_positive_quota_audits_every_cell(name, profile):
    spy = Spy(make(name)); run_full(CFG, spy, profile, 2000)
    assert any(k > 0 for k, *_ in spy.rows)
    for k, n, left, out in spy.rows:
        assert len(out) == k and len(set(out)) == len(out) and len(out) <= n


@pytest.mark.parametrize("name", CELLS)
def test_no_audit_when_budget_or_service_empty(name):
    from tests._proposed_fixtures import RecordingView
    rule = make(name); rule.bind(CFG)
    rv = RecordingView(CFG.N, CFG.J, CFG.T)
    assert rule.audit({}, rv.view(5, audits_left=100)) == []
    assert rule.audit({0: 1, 1: 2}, rv.view(5, audits_left=0)) == []


def test_relabelling_invariance():
    from sim.mechanisms.factorial import select
    rng = np.random.default_rng(7)
    for P, G in itertools.product((0, 1), (0, 1)):
        for _ in range(50):
            jobs = list(range(12)); owners = rng.integers(0, 4, size=12)
            by = {}
            for j, i in zip(jobs, owners):
                by.setdefault(int(i), []).append(j)
            fr = {i: int(rng.integers(0, 40)) for i in by}; keys = rng.random(12); k = int(rng.integers(0, 13))
            perm = {i: int(100 + p) for i, p in zip(by, rng.permutation(len(by)))}
            by2 = {perm[i]: js for i, js in by.items()}; fr2 = {perm[i]: v for i, v in fr.items()}
            assert select(by, keys, fr, 40, 10, k=k, P=P, G=G) == select(by2, keys, fr2, 40, 10, k=k, P=P, G=G)
