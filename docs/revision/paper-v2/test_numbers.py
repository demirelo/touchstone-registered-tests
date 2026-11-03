"""Tests for numbers.py: the paper's evaluation-2 numbers come only from report.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numbers_v2 as N  # noqa: E402

REPORT = {"q4": {"k": 5, "passing": ["fresh0", "fresh1"], "markets": {"fresh0": {"gain_diff": 0.27149, "eff_lower": 0.99512}}},
          "q1": {"tests": {"C*-F111|D2+H3": {"estimate": -0.0123, "interval": [-0.031, 0.0069], "category": "equivalent, direction R3 lower",
                                             "better": None}}},
          "confirmatory": True}
TEX = r"""\section{Results}
% BEGIN-EV2
Replicated on \rv{q4.k} of 6 markets; d is \rv{q1.tests.C*-F111|D2+H3.estimate}.
% END-EV2
Evaluation 1 gains were 0.570 and 0.353.
"""


def _setup(tmp_path, tex=TEX, report=REPORT):
    (tmp_path / "report.json").write_text(json.dumps(report)); (tmp_path / "main.tex").write_text(tex)
    N.write(tmp_path / "report.json", tmp_path / "numbers.tex")
    return tmp_path


def test_flatten_formats_numbers_and_escapes_text():
    m = N.macros(REPORT)
    assert m["q4.k"] == "5"
    assert m["q4.markets.fresh0.gain_diff"] == "0.271"
    assert m["q1.tests.C*-F111|D2+H3.estimate"] == r"\ensuremath{-0.012}"
    assert m["q1.tests.C*-F111|D2+H3.interval.1"] == "0.007"
    assert m["q1.tests.C*-F111|D2+H3.better"] == "n/a"
    assert m["confirmatory"] == "yes"
    assert m["q4.passing.0"] == "fresh0"


def test_check_passes_on_consistent_files(tmp_path):
    d = _setup(tmp_path)
    assert N.check(d / "report.json", d / "numbers.tex", d / "main.tex") == []


def test_check_fails_on_unknown_path(tmp_path):
    d = _setup(tmp_path, tex=TEX.replace(r"\rv{q4.k}", r"\rv{q4.kk}"))
    assert any("q4.kk" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))


def test_check_fails_on_bare_number_in_ev2_block(tmp_path):
    d = _setup(tmp_path, tex=TEX.replace(r"\rv{q4.k} of 6", r"\rv{q4.k} of 6, gap 0.271"))
    assert any("0.271" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))


def test_check_ignores_numbers_outside_ev2_blocks(tmp_path):
    d = _setup(tmp_path)
    assert not any("0.570" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))


def test_check_fails_on_stale_numbers_file(tmp_path):
    d = _setup(tmp_path)
    changed = json.loads(json.dumps(REPORT)); changed["q4"]["k"] = 4
    (d / "report.json").write_text(json.dumps(changed))
    assert any("stale" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))


def test_check_fails_on_unclosed_block(tmp_path):
    d = _setup(tmp_path, tex=TEX.replace("% END-EV2\n", ""))
    assert any("unclosed" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))
