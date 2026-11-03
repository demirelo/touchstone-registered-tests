"""Tests for figures_v2.py: each figure's data file holds exactly the plotted values, each with its report path, and
check mode detects a stale figure. Synthetic report from the code's own world."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import figures_v2 as F  # noqa: E402
import numbers_v2 as N  # noqa: E402
from tests import test_report_v2 as W  # noqa: E402


@pytest.fixture
def report(tmp_path, monkeypatch):
    out, cat = W._world(tmp_path)
    return W._run(monkeypatch, out, cat)


def test_figures_written_with_data_matching_report_paths(report, tmp_path):
    d = tmp_path / "figs"; F.write(report, d)
    raw = N.flat(report)
    for name in ("fig_q1", "fig_q4", "fig_q2"):
        assert (d / f"{name}.pdf").stat().st_size > 1000
        data = json.loads((d / f"{name}.data.json").read_text())
        assert data["points"], name
        for pt in data["points"]:
            for key, path in pt["paths"].items():
                assert raw[path] == pt[key], (name, key, path)


def test_check_detects_a_stale_figure(report, tmp_path):
    d = tmp_path / "figs"; F.write(report, d)
    assert F.check(report, d) == []
    report["q4"]["markets"]["fresh0"]["gain_diff"] += 0.05
    assert any("fig_q4" in p for p in F.check(report, d))


def test_status_strings_are_skipped_and_listed(report, tmp_path):
    report["q4"]["markets"]["fresh2"] = "not decided"
    d = tmp_path / "figs"; F.write(report, d)
    data = json.loads((d / "fig_q4.data.json").read_text())
    assert "fresh2" in data["skipped"] and all(p["market"] != "fresh2" for p in data["points"])
