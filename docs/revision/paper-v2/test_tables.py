"""Tests for tables_v2.py on the report built by the code's own synthetic world (tests/test_report_v2.py), so the
schema is the real one. Row labels are the keys that fetch the values; these tests check that, and the status rows."""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import tables_v2 as T  # noqa: E402
from tests import test_report_v2 as W  # noqa: E402


@pytest.fixture
def report(tmp_path, monkeypatch):
    out, cat = W._world(tmp_path)
    return W._run(monkeypatch, out, cat)


def _row(tex: str, label: str) -> str:
    rows = [r for r in tex.split("\\\\") if r.strip().startswith(label + " &") or ("\n" + label + " &") in r]
    assert len(rows) == 1, (label, rows)
    return rows[0]


def test_q4_rows_carry_their_own_market_values(report):
    for i, m in enumerate(W.FRESH):
        if isinstance(report["q4"]["markets"][m], dict):
            report["q4"]["markets"][m]["gain_diff"] = 0.101 + i / 10
    tex = T.q4(report)
    for i, m in enumerate(W.FRESH):
        assert f"{0.101 + i / 10:.3f}" in _row(tex, m)


def test_q4_status_row_for_an_undecided_market(report):
    report["q4"]["markets"]["fresh2"] = "not decided"
    assert "not decided" in _row(T.q4(report), "fresh2")


def test_q1_rows_by_family_with_category_and_side_evidence(report):
    tex = T.q1(report); side = T.q1_side(report)
    for fam in ("D2+H3", "X7-SC"):
        t = report["q1"]["tests"][f"C*-F111|{fam}"]
        assert T.esc(t["category"]) in _row(tex, fam)
        assert f"{t['side']['gross_eff_diff']:.3f}".lstrip("-") in _row(side, fam)


def test_q2_contrast_rows_match_their_contrast(report):
    tex = T.q2(report, "D2+H3")
    for c, v in report["q2"]["searched"]["D2+H3"].items():
        assert f"{v['estimate']:.3f}".lstrip("-") in _row(tex, c)


def test_coalition_and_welfare_tables_render(report):
    assert "c5\\_staggered" in T.coalitions(report)
    assert "W1" in T.welfare(report)


def test_nonfinite_value_refused(report):
    report["q4"]["markets"]["fresh0"]["gain_diff"] = math.nan
    with pytest.raises(ValueError):
        T.q4(report)


def test_all_tables_compile(report, tmp_path):
    tex = "\n".join(T.all_tables(report).values())
    (tmp_path / "t.tex").write_text("\\documentclass{article}\\usepackage{booktabs}\\begin{document}\n" + tex + "\n\\end{document}\n")
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "t.tex"], cwd=tmp_path, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-1500:]


def test_small_p_values_keep_digits_in_tables(report):
    report["q1"]["tests"]["C*-F111|D2+H3"]["p"] = 0.0001
    for m in W.FRESH:
        if isinstance(report["q4"]["markets"][m], dict):
            report["q4"]["markets"][m]["p_gain"] = 0.00003
    assert "0.0001" in _row(T.q1(report), "D2+H3")
    assert "3\\times10^{-5}" in _row(T.q4(report), "fresh0")
