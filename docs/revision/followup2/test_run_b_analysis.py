import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import run_b_analysis as A  # noqa: E402

MARKETS = {"fresh0": 0.1, "fresh1": 0.2}


def _q(f, c):
    return {"frozen": {"markets": dict(f)}, "converged": {"markets": dict(c)}}


def _setup(tmp_path, pod_extra=None):
    (tmp_path / "convergence").mkdir()
    (tmp_path / "convergence" / "a.json").write_text(json.dumps({"id": "a", "binding": {"x": 1}, "heldout": {}, "status": "passed", "rounds": [1, 2]}))
    mac = {"label": "L", "q1": _q(MARKETS, {"fresh0": 0.1, "fresh1": 0.25}), "q1_x7": _q(MARKETS, MARKETS), "q4": _q(MARKETS, MARKETS), "substituted": ["a"]}
    pod = {**mac, **(pod_extra or {}), "nesting_shortfall": {}}
    (tmp_path / "recompute.json").write_text(json.dumps(pod))
    return mac


def test_equal_recompute_reports_items(tmp_path, monkeypatch):
    mac = _setup(tmp_path)
    monkeypatch.setattr(A.B, "recompute", lambda src, run, expected: mac)
    r = A.analyse(tmp_path, "src")
    assert r["mac_equals_pod"] and r["passed_within_three_rounds"] == 1
    assert r["largest_market_change"]["market"] == "fresh1" and abs(r["largest_market_change"]["change"] - 0.05) < 1e-12


def test_differing_recompute_is_refused(tmp_path, monkeypatch):
    mac = _setup(tmp_path, pod_extra={"substituted": []})
    monkeypatch.setattr(A.B, "recompute", lambda src, run, expected: mac)
    with pytest.raises(SystemExit):
        A.analyse(tmp_path, "src")


def test_selection_counts_come_from_the_report(tmp_path, monkeypatch):
    # External review d10 (Astra Pro), problem 2: Run B's cells are flagged cells plus unflagged nesting cells
    mac = _setup(tmp_path)
    monkeypatch.setattr(A.B, "recompute", lambda src, run, expected: mac)
    (tmp_path / "convergence" / "b.json").write_text(json.dumps({"id": "b", "binding": {"x": 2}, "heldout": {}, "status": "passed", "rounds": [1]}))
    report = {"doubling": {"a": {"incomplete": True}, "b": {"incomplete": False}}}
    r = A.analyse(tmp_path, "src", report=report)
    assert r["selection"] == {"flagged": 1, "unflagged": 1, "unflagged_cells": ["b"]}
