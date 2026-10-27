"""The v2 manifest (design 8.1, 8.2, 6.5, 6.6): cells, doublings, cross-evaluations, priority, cuts, freeze requirements."""
from collections import Counter

import pytest

FRESH = [f"fresh{i}" for i in range(6)]


def _search_cells():
    from sim.manifest_v2 import cells
    return [c for c in cells() if c["block"] != "diagnostic"]


def test_counts_draft7():
    from sim.manifest_v2 import cells, cross_evaluations, doublings
    cs = _search_cells()
    assert len(cs) == 287 and len({c["id"] for c in cells()}) == 290
    assert sum(c["family"] == "X7-SC" for c in cs) == 85 and sum(c["family"] == "H4" for c in cs) == 21
    assert sum(c["block"] == "diagnostic" for c in cells()) == 3
    assert len(doublings()) == 98 and set(doublings()) <= {c["id"] for c in cs}
    assert len(cross_evaluations()) == 14


def test_block_counts():
    from sim.manifest_v2 import cells
    assert Counter(c["block"] for c in cells()) == {"matched": 140, "extras": 63, "tuned": 24, "reference": 3, "welfare": 12, "coalition": 24,
                                                    "coalition_roles": 6, "repair": 15, "diagnostic": 3}


def test_every_rule_has_menu_searches():
    from sim.manifest_v2 import menu_families
    cs = _search_cells(); prof = {(c["context"], c["rule"], c["family"]) for c in cs if c["objective"] == "profit"}
    for c in cs:
        if c["objective"] not in ("total", "min"):
            assert all((c["context"], c["rule"], f) in prof for f in menu_families(c["context"], c["rule"]))


def test_no_r4_or_cstar_s2_at_rho02():
    cs = _search_cells()
    assert not any(c["rule"] in ("R4", "C*/S2") and c["rho"] == 0.2 for c in cs)
    assert {c["rule"] for c in cs if c["rho"] == 1.0} == {"F000", "F111", "R4", "C*", "C*/S2"}


def test_no_r4t():
    from sim.rules_v2 import make_rule
    assert not any(c["rule"] == "R4-t" for c in _search_cells())
    with pytest.raises(ValueError):
        make_rule("R4-t")


def test_tuned_fresh_d2h3_only():
    cs = [c for c in _search_cells() if c["block"] == "tuned"]
    assert {c["family"] for c in cs if c["market"].startswith("fresh")} == {"D2+H3"}
    assert {c["family"] for c in cs if c["market"] == "headline"} == {"D2+H3", "X7-SC"}
    assert {c["rule"] for c in cs} == {"B3-t", "R3-t", "C*-t"}


def _a_tot(K: int, rho: float) -> int:
    return int((0.05 / rho) * 200 * min(50, K))


def test_distinct_rule_bound_at_generator_ends():
    from sim.manifest_v2 import distinct_rule_problems
    for K in (40, 80):
        assert _a_tot(K, 0.2) in (2000, 2500)
        bad = [{"block": "matched", "context": "m@rho0.2", "rule": r} for r in ("F111", "R4")]
        assert distinct_rule_problems(bad, {"m@rho0.2": _a_tot(K, 0.2)})
        bad2 = [{"block": "matched", "context": "m@rho0.2", "rule": r} for r in ("C*", "C*/S2")]
        assert distinct_rule_problems(bad2, {"m@rho0.2": _a_tot(K, 0.2)})
        ok = [{"block": "repair", "context": "m@rho1", "rule": r} for r in ("F111", "R4", "C*", "C*/S2")]
        assert _a_tot(K, 1.0) in (400, 500) and distinct_rule_problems(ok, {"m@rho1": _a_tot(K, 1.0)}) == []


def test_manifest_passes_distinct_rule_check():
    from sim.manifest_v2 import cells, distinct_rule_problems, headline_a_tot
    assert headline_a_tot(0.2) == 2500 and headline_a_tot(1.0) == 500
    cs = _search_cells()
    assert distinct_rule_problems(cs, {c["context"]: headline_a_tot(c["rho"]) for c in cs}) == []


def test_draft6_cell_ids_are_foreign(tmp_path):
    import scripts.revision_v2 as RV
    ids = {c["id"] for c in _search_cells()}
    for rid in ("headline@rho0.2|R4|D2+H3|profit", "headline@rho0.2|C*/S2|X7-SC|profit"):
        assert rid not in ids
        with pytest.raises(ValueError):
            RV.check_record(rid, {"stage": "search"}, [], tmp_path)


def test_question_map():
    from sim.manifest_v2 import QUESTIONS, question_cells
    q1 = question_cells("Q1")
    assert len(q1["cells"]) == 24 and set(q1["checks"]) == set(q1["cells"])
    assert {c.split("|")[1] for c in q1["cells"]} == {"F111", "C*"} and all(c.startswith("fresh") for c in q1["cells"])
    q4 = question_cells("Q4")
    assert len(q4["cells"]) == 12 and {c.split("|")[1] for c in q4["cells"]} == {"F000", "F111"} and all("|D2+H3|" in c for c in q4["cells"])
    q3 = question_cells("Q3")
    assert sum("|H4|" in c for c in q3["cells"]) == 21 and sum("|diagnostic" in c for c in q3["cells"]) == 3
    assert set(QUESTIONS) == {"Q1", "Q2", "Q3", "Q4", "repair", "whole"}
    assert not any("|H4|" in c for c in question_cells("Q3", h4_excluded=True)["cells"])


def test_diagnostic_not_required_before_freeze():
    from sim.manifest_v2 import bank_rules, doublings, required
    req = required("headline@rho0.2")
    assert not any("diagnostic" in r for r in req) and not any("diagnostic" in d for d in doublings())
    assert "HR1" not in str(bank_rules("headline@rho0.2", "D2+H3"))


def test_cuts_in_order():
    from sim.manifest_v2 import CUT_ORDER, effective
    base = {c["id"] for c in effective(0)}
    expect = [18, 18, 18, 12]
    prev = base
    for n, want in enumerate(expect, start=1):
        cur = {c["id"] for c in effective(n)}
        removed = prev - cur
        assert len(removed) == want and cur < prev
        assert all(r.startswith("fresh") for r in removed) and len(CUT_ORDER) == 4
        prev = cur
    rm1 = base - {c["id"] for c in effective(1)}
    assert all(r.split("|")[1] in ("B3-t", "R3-t", "C*-t") for r in rm1)
    rm4 = {c["id"] for c in effective(3)} - {c["id"] for c in effective(4)}
    assert all(r.split("|")[1] == "C*/S0" for r in rm4)


def test_priority():
    from sim.manifest_v2 import cells, priority
    by = {c["id"]: priority(c) for c in cells()}
    assert by["fresh0@rho0.2|F111|D2+H3|profit"] == 0 and by["fresh0@rho0.2|C*|X7-SC|profit"] == 0
    assert by["fresh0@rho0.2|F010|D2+H3|profit"] == 1
    assert by["headline@rho0.2|F111|X6-SE/v2|total|c2_synchronised"] == 2 and by["headline@rho0.2|C*|X5-AG/v2|profit"] == 2
    assert by["fresh0@rho0.2|B3-t|D2+H3|profit"] == 3


def test_effective_and_required():
    from sim.manifest_v2 import effective, required
    assert len(effective(0, h4_excluded=True)) == 290 - 21
    req = required("headline@rho0.2")
    assert "reference/headline@rho0.2/F111" in req and "reference/headline@rho0.2/B2" in req
    assert "joint_twin/headline@rho0.2/F111_c5_staggered" in req and "joint_reference/headline@rho0.2/F111_c5" in req
    assert "joint_reference_pre/headline@rho0.2/F111_c2" in req and "coalition_select/headline@rho0.2/C*_c2" in req
    assert "joint_reference/headline@rho0.2/F111_c5_staggered" not in req and "bank/headline@rho0.2/X7-SC" in req
    assert "envelope/headline@rho0.2/C*" in req
    req1 = required("headline@rho1")
    assert "reference/headline@rho1/R4" in req1 and not any(r.startswith("bank/headline@rho1") for r in req1)
    assert not any("|H4|" in r for r in required("fresh2@rho0.2", h4_excluded=True))


def test_bank_rules():
    from sim.manifest_v2 import bank_rules
    assert bank_rules("headline@rho1", "D2+H3") == ["F000", "F111", "C*", "C*/S2", "R4"]
    assert len(bank_rules("fresh3@rho0.2", "X7-SC", cuts=4)) == 9 and len(bank_rules("fresh3@rho0.2", "X7-SC")) == 10
