"""Welfare (W0, W1) and coalition (total, worst member, joint reference) objectives (design 6.2, 6.3)."""
import numpy as np
import pytest

from sim.cell import Cell, SeedCache
from sim.policies.families import D2
from sim.positions import positions
from sim.rules_v2 import make_rule
from tests._v2_profiles import CFG

FOCAL = positions(CFG)["median"]
SEEDS = (2000, 2001)
HONEST_D2 = {"u0": 0.0, "m0": 0.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "clip": 1}
SABOTAGE = {"u0": 1.0, "m0": 1.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "clip": 0}


def cell():
    return Cell(cfg=CFG, rule_factory=lambda: make_rule("F000"), focal=FOCAL, seeds=SEEDS, name="t")


def test_w0_prefers_lower_efficiency():
    from sim.objectives_v2 import WelfareObjective
    o = WelfareObjective(cell(), D2, SeedCache())
    f_h = o.eval_knobs(HONEST_D2); f_s = o.eval_knobs(SABOTAGE)
    assert f_s > f_h
    assert o.extra[next(iter(o.extra))]["eff"] == pytest.approx(-f_h)


def test_w1_records_constraint():
    from sim.objectives_v2 import WelfareObjective
    o = WelfareObjective(cell(), D2, SeedCache(), ref_normalized=np.zeros(len(SEEDS)))
    o.eval_knobs(HONEST_D2)
    e = next(iter(o.extra.values()))
    assert e["constraint"] == pytest.approx(float(np.mean(next(iter(o.archive.values())).per_seed_normalized)))


def _fake(entries):
    from sim.objectives_v2 import WelfareObjective
    o = WelfareObjective.__new__(WelfareObjective)
    o.archive, o.extra = {}, {}
    for n, (f, c) in enumerate(entries):
        key = (("k", float(n)),)
        o.archive[key] = type("E", (), {"knobs": {"k": n}, "f": f})(); o.extra[key] = {"eff": -f, "constraint": c}
    return o


def test_w1_feasibility_first():
    from sim.objectives_v2 import select_w1
    o = _fake([(-0.5, 0.1), (-0.2, -0.01), (-0.4, 0.0), (-0.4, 0.3)])   # the lowest efficiency (-0.2) is infeasible
    assert select_w1(o) == {"k": 2}                                      # best feasible f = -0.4; ties to the earlier point


def test_w1_none_when_no_feasible():
    from sim.objectives_v2 import select_w1
    assert select_w1(_fake([(-0.5, -0.1), (-0.2, -0.01)])) is None


def test_coalition_total_vs_min():
    from sim.objectives_v2 import coalition_score
    g = [np.array([1.0, -1.0]), np.array([-0.5, 0.9])]                 # member means 0.0 and 0.2
    assert coalition_score(g, "total") == pytest.approx(0.2)
    assert coalition_score(g, "min") == pytest.approx(0.0)
    assert coalition_score(g, "min") != pytest.approx(np.mean(np.minimum(*g)))   # not the mean of per-seed minima


def test_joint_reference_tie_order():
    from sim.objectives_v2 import pick_joint
    assert pick_joint([("honest_max", 0.3), ("abstain", 0.3), ("joint_twin", 0.3)]) == "honest_max"
    assert pick_joint([("honest_max", 0.1), ("abstain", 0.0), ("joint_twin", 0.2)]) == "joint_twin"


def test_joint_twin_forces_clip():
    from sim.objectives_v2 import CoalitionObjective
    from sim.policies.v2 import x6v2_family, x6v2_members
    fam = x6v2_family(200, 10); mem = x6v2_members(CFG, FOCAL, 2)
    o = CoalitionObjective(CFG, lambda: make_rule("F111"), mem, fam, SEEDS, SeedCache(), "joint_twin", staggered=False, T=200, L=10)
    k = {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "P": 20.0, "x": 1, "y": 1, "clip": 0}
    o.eval_knobs(k)
    assert all(e.knobs["clip"] == 1 for e in o.archive.values())
    assert o.knobs_of(np.zeros(fam.dim))["clip"] == 1


def test_coalition_objective_total_and_joint_reference():
    from sim.objectives_v2 import CoalitionObjective, joint_reference
    from sim.policies.v2 import x6v2_family, x6v2_members
    fam = x6v2_family(200, 10); mem = x6v2_members(CFG, FOCAL, 2); rf = lambda: make_rule("F111")
    twin = {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "P": 50.0, "x": 0, "y": 0, "clip": 1}
    ref = joint_reference(CFG, rf, mem, SEEDS, SeedCache(), twin, False, 200, 10)
    assert ref["name"] in ("honest_max", "abstain", "joint_twin") and ref["member_normalized"].shape == (2, len(SEEDS))
    o = CoalitionObjective(CFG, rf, mem, fam, SEEDS, SeedCache(), "total", joint_ref=ref["member_normalized"], staggered=False, T=200, L=10)
    f = o.eval_knobs({**twin, "clip": 0})
    assert np.isfinite(f) and set(o.extra[next(iter(o.extra))]) >= {"member_means", "total", "min"}
