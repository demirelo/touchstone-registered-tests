"""Tests for cells_v2.py (per-cell means from the verified evaluation records) and score_v2.py (the hashed prediction
scoring table, cell by cell). The world is the code's own synthetic world (tests/test_report_v2.py)."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import cells_v2 as C  # noqa: E402
import score_v2 as S  # noqa: E402
from tests import test_report_v2 as W  # noqa: E402


@pytest.fixture
def world(tmp_path, monkeypatch):
    out, cat = W._world(tmp_path)
    return out, W._run(monkeypatch, out, cat)


def test_cells_reads_means_and_hashes(world):
    out, _ = world
    cells = C.extract(out)
    rid = "headline@rho0.2|F111|X7-SC|profit"
    gains = json.loads((out / "evaluate" / (C.safe(rid) + ".json")).read_text())["gain"]
    assert abs(cells[rid]["gain"] - sum(gains) / len(gains)) < 1e-12
    assert len(cells[rid]["sha256"]) == 64
    x8 = cells["headline@rho0.2|F111|X8-DB|total|c2_roles"]
    assert len(x8["member_gain"]) == 2


def test_every_prediction_scored_with_a_valid_status(world):
    out, rep = world
    sc = S.score(rep, C.extract(out))
    ids = {"Q1-a", "Q1-a-alt", "Q1-b", "Q1-c", "Q1-d", "Q2-a", "Q2-b", "Q2-c", "Q2-d", "Q3-a", "Q3-b", "Q3-c", "Q3-d", "Q3-e",
           "Q3-f", "Q3-g", "Q4-a", "Q4-b"}
    assert set(sc) == ids
    assert all(v["status"] in ("fulfilled", "failed", "not assessed") for v in sc.values())


def test_q1a_follows_the_category(world):
    out, rep = world
    rep["q1"]["tests"]["C*-F111|D2+H3"]["category"] = "equivalent, direction R3 lower"
    assert S.score(rep, C.extract(out))["Q1-a"]["status"] == "fulfilled"
    rep["q1"]["tests"]["C*-F111|D2+H3"]["category"] = "C* materially lower"
    assert S.score(rep, C.extract(out))["Q1-a"]["status"] == "failed"


def test_q1b_excludes_the_c_star_lower_direction(world):
    out, rep = world
    rep["q1"]["tests"]["C*-F111|X7-SC"]["category"] = "equivalent, direction C* lower"
    assert S.score(rep, C.extract(out))["Q1-b"]["status"] == "failed"


def test_cell_aggregation_missing_cell_is_not_assessed_but_a_failed_cell_fails(world):
    out, rep = world
    cells = C.extract(out)
    del cells["fresh3@rho0.2|C*|X7-SC|profit"]
    st = S.score(rep, cells)["Q3-a"]
    assert st["status"] in ("not assessed", "failed")
    if st["status"] == "not assessed":
        assert any(c["status"] == "not assessed" for c in st["cells"])
    cells["fresh0@rho0.2|F111|X7-SC|profit"]["gain"] = cells["fresh0@rho0.2|F111|D2+H3|profit"]["gain"] + 0.2
    assert S.score(rep, cells)["Q3-a"]["status"] == "failed"


def test_q3d_uses_the_difference_also_for_nonpositive_totals(world):
    out, rep = world
    for r in ("F111", "C*"):
        for g in rep["q3"]["coalition"][r]:
            rep["q3"]["coalition"][r][g] = {"G_tot": {"estimate": -0.2}, "G_min": {"estimate": -0.05, "bounds": [None, None]}}   # -0.05 > 0.5 x -0.2
    assert S.score(rep, C.extract(out))["Q3-d"]["status"] == "failed"
    for r in ("F111", "C*"):
        for g in rep["q3"]["coalition"][r]:
            rep["q3"]["coalition"][r][g] = {"G_tot": {"estimate": -0.2}, "G_min": {"estimate": -0.15, "bounds": [None, None]}}   # -0.15 <= 0.5 x -0.2
    assert S.score(rep, C.extract(out))["Q3-d"]["status"] == "fulfilled"


def test_q4b_strict_tie_fails_and_no_eligible_market_is_not_assessed(world):
    out, rep = world
    rep["q4"]["failing"] = []
    assert S.score(rep, C.extract(out))["Q4-b"]["status"] == "not assessed"
    m = "fresh1"
    rep["q4"]["failing"] = [m]; rep["q4"]["markets"][m]["p_gain"] = rep["q4"]["markets"][m]["p_eff"] = 0.5
    assert S.score(rep, C.extract(out))["Q4-b"]["status"] == "failed"


def test_q4a_needs_a_decision(world):
    out, rep = world
    rep["q4"]["k"] = None
    assert S.score(rep, C.extract(out))["Q4-a"]["status"] == "not assessed"
    rep["q4"]["k"] = 5
    assert S.score(rep, C.extract(out))["Q4-a"]["status"] == "fulfilled"


def test_q1c_reports_c_star_minus_f111_as_registered(world):
    out, rep = world
    rep["q1"]["tests"]["C*-F111|D2+H3"]["side"]["gross_eff_diff"] = 0.004          # the report's side fields are F111 minus C*
    cell = [c for c in S.score(rep, C.extract(out))["Q1-c"]["cells"] if c["cell"] == "D2+H3"][0]
    assert cell["value"] == -0.004


def test_q4b_compares_calibrated_p_values_as_registered(world):
    """Raw 0.30 > 0.26, but calibrated with kappa 0.25 both cap at 1: a tie, which fails (predictions-v2.md, Q4-b)."""
    out, rep = world
    m = "fresh1"; rep["q4"]["failing"] = [m]
    rep["q4"]["markets"][m]["p_gain"], rep["q4"]["markets"][m]["p_eff"] = 0.30, 0.26
    sc = S.score(rep, C.extract(out))["Q4-b"]
    assert sc["status"] == "failed" and sc["cells"][0]["value"] == pytest.approx((1.0, 1.0))


# External review round 7: the rubric (predictions-v2.md) makes a target "incomplete (design 6.5)" not assessed, and design
# 6.5 calls a search-flagged cell "incomplete". The numerical scorer ignored the flags; the eligibility map makes each
# prediction cell's required searches explicit and rescored the predictions under two stricter readings.
FLAG_Q3B = "headline@rho0.2|F111|X7-SC|profit"


def test_inputs_name_the_required_searches_of_each_prediction_cell():
    assert S.inputs("Q3-a", "fresh1 C*") == ["fresh1@rho0.2|C*|X7-SC|profit", "fresh1@rho0.2|C*|D2+H3|profit"]
    assert S.inputs("Q3-b", "headline F111") == ["headline@rho0.2|F111|H4|profit", FLAG_Q3B]
    assert S.inputs("Q3-d", "C* c2_roles") == ["headline@rho0.2|C*|X8-DB|min|c2_roles", "headline@rho0.2|C*|X8-DB|total|c2_roles"]
    assert S.inputs("Q3-d", "F111 c2_staggered")[0] == "headline@rho0.2|F111|X6-SE/v2|min|c2_staggered"
    assert S.inputs("Q3-e", "headline") == ["headline@rho0.2|F111|X8-DB|total|c2_roles", "headline@rho0.2|C*|X8-DB|total|c2_roles"]
    q2 = S.inputs("Q2-a", "G")
    assert len(q2) == 48 and "fresh4@rho0.2|F111|D2+H3|profit" in q2 and all("|D2+H3|" in x for x in q2)
    assert all("|X7-SC|" in x for x in S.inputs("Q2-d", "P X7-SC"))
    assert "fresh0@rho0.2|C*|D2+H3|profit" in S.inputs("Q1-c", "D2+H3")
    assert S.inputs("Q3-g", "headline rho1") == ["headline@rho1|F111|D2|profit", "headline@rho1|R4|D2|profit"]


def _sc():
    f = lambda c, s: {"cell": c, "status": s, "value": 0.0}
    return {"Q1-a": {"status": "fulfilled", "cells": [f("D2+H3", "fulfilled")]},
            "Q1-c": {"status": "fulfilled", "cells": [f("D2+H3", "fulfilled"), f("X7-SC", "fulfilled")]},
            "Q2-a": {"status": "failed", "cells": [f("G", "fulfilled"), f("S", "failed")]},
            "Q3-b": {"status": "fulfilled", "cells": [f("headline F111", "fulfilled")]},
            "Q3-c": {"status": "failed", "cells": [f("fresh1 C*", "failed"), f("fresh2 F111", "failed")]},
            "Q3-e": {"status": "fulfilled", "cells": [f("headline", "fulfilled")]}}


def test_a_flagged_required_search_makes_the_q3_cell_not_assessed():
    flagged = [FLAG_Q3B, "fresh1@rho0.2|C*|D2+H3|profit", "headline@rho0.2|C*|X8-DB|min|c2_roles", "fresh4@rho0.2|F111|D2+H3|profit"]
    e = S.eligibility(_sc(), flagged, "q3")
    assert e["Q3-b"]["status"] == "not assessed" and e["Q3-b"]["cells"][0]["flagged"] == [FLAG_Q3B]
    assert e["Q3-c"]["status"] == "failed"                  # fresh2 F111 fails without a flagged input
    assert e["Q3-e"]["status"] == "fulfilled"              # the C* flag is on the minimum objective, Q3-e uses the total
    assert e["Q2-a"]["status"] == "failed" and e["Q1-c"]["status"] == "fulfilled"      # outside the Q3 scope


def test_the_descriptive_reading_also_covers_q1c_and_q2_but_never_a_decision():
    flagged = ["fresh1@rho0.2|C*|D2+H3|profit", "fresh4@rho0.2|F111|D2+H3|profit"]
    e = S.eligibility(_sc(), flagged, "descriptive")
    assert e["Q2-a"]["status"] == "not assessed" and e["Q1-c"]["status"] == "not assessed"
    assert e["Q1-a"]["status"] == "fulfilled"              # a confirmatory decision is kept (design 6.5)
    num = S.eligibility(_sc(), flagged, "numerical")                   # flags are listed, statuses unchanged
    assert {k: v["status"] for k, v in num.items()} == {k: v["status"] for k, v in _sc().items()}
    assert num["Q2-a"]["cells"][0]["flagged"] == ["fresh4@rho0.2|F111|D2+H3|profit"]
    with pytest.raises(ValueError):
        S.eligibility(_sc(), flagged, "other")


def test_eligibility_map_tallies_each_reading():
    m = S.eligibility_map(_sc(), [FLAG_Q3B, "fresh4@rho0.2|F111|D2+H3|profit"])
    assert m["tally"]["numerical"] == {"fulfilled": 4, "failed": 2, "not assessed": 0}
    assert m["tally"]["q3"] == {"fulfilled": 3, "failed": 2, "not assessed": 1}
    assert m["tally"]["descriptive"] == {"fulfilled": 2, "failed": 1, "not assessed": 3}
    assert m["targets"]["Q3-b"]["status"] == {"numerical": "fulfilled", "q3": "not assessed", "descriptive": "not assessed"}
    assert m["targets"]["Q1-a"]["decision"] is True and m["targets"]["Q3-b"]["flagged"] == [FLAG_Q3B]
