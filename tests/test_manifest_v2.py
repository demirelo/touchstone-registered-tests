"""The v2 manifest (design 8.1, 8.2, 6.5, 6.6): cells, doublings, cross-evaluations, priority, cuts, freeze requirements."""
from collections import Counter

import pytest

FRESH = [f"fresh{i}" for i in range(6)]


def test_counts():
    from sim.manifest_v2 import cells, cross_evaluations, doublings
    cs = cells()
    assert len(cs) == 374 and len({c["id"] for c in cs}) == 374
    assert sum(c["family"] == "X7-SC" for c in cs) == 126
    assert len(doublings()) == 132 and set(doublings()) <= {c["id"] for c in cs}
    assert len(cross_evaluations()) == 14


def test_block_counts():
    from sim.manifest_v2 import cells
    assert Counter(c["block"] for c in cells()) == {"matched": 168, "extras": 84, "tuned": 56, "reference": 3, "welfare": 16, "coalition": 32, "repair": 15}


def test_every_rule_has_menu_searches():
    from sim.manifest_v2 import cells
    cs = cells(); prof = {(c["context"], c["rule"], c["family"]) for c in cs if c["objective"] == "profit"}
    for c in cs:
        if c["objective"] != "coalition":
            assert (c["context"], c["rule"], "D2+H3") in prof and (c["context"], c["rule"], "X7-SC") in prof


def test_cuts_in_order():
    from sim.manifest_v2 import CUT_ORDER, effective
    base = {c["id"] for c in effective(0)}
    expect = [48, 24, 24, 12]
    prev = base
    for n, want in enumerate(expect, start=1):
        cur = {c["id"] for c in effective(n)}
        removed = prev - cur
        assert len(removed) == want and cur < prev
        assert all(r.startswith("fresh") for r in removed) and len(CUT_ORDER) == 4
        prev = cur
    rm1 = base - {c["id"] for c in effective(1)}
    assert all(r.split("|")[1] in ("B3-t", "R3-t", "R4-t", "C*-t") for r in rm1)
    rm4 = {c["id"] for c in effective(3)} - {c["id"] for c in effective(4)}
    assert all(r.split("|")[1] == "C*/S0" for r in rm4)


def test_priority():
    from sim.manifest_v2 import cells, priority
    by = {c["id"]: priority(c) for c in cells()}
    assert by["fresh0@rho0.2|F111|D2+H3|profit"] == 0 and by["fresh0@rho0.2|C*/S2|X7-SC|profit"] == 0
    assert by["fresh0@rho0.2|F010|D2+H3|profit"] == 1
    assert by["headline@rho0.2|F111|X6-SE/v2|total|c2_synchronised"] == 2 and by["headline@rho0.2|C*|X5-AG/v2|profit"] == 2
    assert by["fresh0@rho0.2|B3-t|D2+H3|profit"] == 3


def test_effective_and_required():
    from sim.manifest_v2 import effective, required
    assert len(effective(0, h4_excluded=True)) == 374 - 28
    req = required("headline@rho0.2")
    assert "reference/headline@rho0.2/F111" in req and "reference/headline@rho0.2/B2" in req
    assert "joint_reference/headline@rho0.2/F111_c5_staggered" in req and "bank/headline@rho0.2/X7-SC" in req
    assert "envelope/headline@rho0.2/C*" in req
    req1 = required("headline@rho1")
    assert "reference/headline@rho1/R4" in req1 and not any(r.startswith("bank/headline@rho1") for r in req1)
    assert not any("|H4|" in r for r in required("fresh2@rho0.2", h4_excluded=True))


def test_bank_rules():
    from sim.manifest_v2 import bank_rules
    assert bank_rules("headline@rho1", "D2+H3") == ["F000", "F111", "C*", "C*/S2", "R4"]
    assert len(bank_rules("fresh3@rho0.2", "X7-SC", cuts=4)) == 11 and len(bank_rules("fresh3@rho0.2", "X7-SC")) == 12
