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
