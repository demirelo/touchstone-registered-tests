"""Rule registry v2 (design 3.5): matched, tuned, and reference rules, and their public constants (design 5.1)."""
from dataclasses import replace

import pytest

from sim.mechanisms.proposed import Proposed
from sim.mechanisms.second_score import SecondScore
from tests._v2_profiles import CFG, run_full

CRED = {"variant": "thr", "K": 6, "M": None}


def test_make_rule_names_and_types():
    from sim.rules_v2 import make_rule, MATCHED
    for name in MATCHED + ["R4", "C*/S2", "B3-t", "R3-t", "C*-t", "B2"]:
        r = make_rule(name, cred=CRED)
        assert r.describe()["parameters"]["audit_tolerance"] > 0
    f = make_rule("F111")
    assert (f.name, f.tol, f.L) == ("F111", 0.16, 10)
    assert isinstance(make_rule("B3-t", 0.12, 20), SecondScore) and isinstance(make_rule("R3-t", 0.12, 20), Proposed)
    assert make_rule("C*/S2", cred={"variant": "mem", "K": 2, "M": 50}).name == "C-mem/S2"


def test_public_constants_nondefault():
    from sim.rules_v2 import make_rule, public_constants
    cfg = replace(CFG, T=100)
    assert public_constants(make_rule("C*", L=20, cred=CRED), cfg) == {"T": 100, "L": 20}


def test_public_constants_frozen_rules():
    from sim.rules_v2 import public_constants
    assert public_constants(SecondScore(0.16, 10), CFG) == {"T": 200, "L": 10}
    assert public_constants(Proposed("A", "T1", 0.16, 10), CFG) == {"T": 200, "L": 10}


def test_b2_uses_registered_parameters():
    import json
    from sim.rules_v2 import make_rule, public_constants
    best = json.load(open("experiments/tuned/tuned_B2.json"))["best_params"]
    r = make_rule("B2")
    assert public_constants(r, CFG)["L"] == int(best["L"]) and r.tol == float(best["tol"])


def test_unknown_name_refuses():
    from sim.rules_v2 import make_rule
    with pytest.raises(ValueError):
        make_rule("F222")
    with pytest.raises(ValueError):
        make_rule("C*")                                       # the comparator needs cred


def test_matched_and_core_lists():
    from sim.rules_v2 import MATCHED, CORE
    from sim.rules_v2 import FIXED, TUNED
    assert MATCHED == ["F000", "F001", "F010", "F011", "F100", "F101", "F110", "F111", "C*", "C*/S0"]
    assert CORE == ["F000", "F111", "C*"] and TUNED == ["B3-t", "R3-t", "C*-t"]
    assert FIXED == MATCHED + ["C*/S2", "R4"]


def test_repair_rules_construct():
    import scripts.revision_v2 as RV
    from sim.rules_v2 import make_rule
    params = {"cred": CRED, "tuned": {s: {"tol": 0.12, "L": 20} for s in ("B3-t", "R3-t", "C*-t")}}
    for rule in ("F000", "F111", "R4", "C*", "C*/S2"):
        spec = RV.rule_spec(rule, params)
        assert (spec["tol"], spec["L"]) == (0.16, 10)
        assert make_rule(rule, spec["tol"], spec["L"], cred=spec.get("cred")) is not None


def test_admissibility_inputs():
    from sim.rules_v2 import make_rule, MATCHED
    for name in MATCHED:
        res = run_full(CFG, make_rule(name, cred=CRED), "replacement", 2001)
        assert res.audits.sum() > 0 and (res.audits <= res.served.sum(axis=1)).all()
