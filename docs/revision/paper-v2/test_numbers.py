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
Replicated on \rvk{count}{q4.k} of six markets; d is \rvk{gain}{q1.tests.C*-F111|D2+H3.estimate}.
% END-EV2
Evaluation 1 gains were 0.570 and 0.353.
"""


def _v(old, new):
    """Edit the fixture; fail if the target text is absent (a silent no-op would make the test pass vacuously)."""
    assert old in TEX, old
    return TEX.replace(old, new)


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
    d = _setup(tmp_path, tex=_v(r"\rvk{count}{q4.k}", r"\rvk{count}{q4.kk}"))
    assert any("q4.kk" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))


def test_check_fails_on_bare_number_in_ev2_block(tmp_path):
    d = _setup(tmp_path, tex=_v(r"\rvk{count}{q4.k} of six", r"\rvk{count}{q4.k} of six, gap 0.271"))
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
    d = _setup(tmp_path, tex=_v("% END-EV2\n", ""))
    assert any("unclosed" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex"))


def test_check_fails_on_bare_integer_and_percentage(tmp_path):
    for bad in ("replicated on 5 of the markets", "a 27% reduction"):
        d = _setup(tmp_path, tex=_v(r"Replicated on \rvk{count}{q4.k} of six markets", bad))
        assert any("bare number" in p for p in N.check(d / "report.json", d / "numbers.tex", d / "main.tex")), bad


def test_check_ignores_identifiers_constants_and_references(tmp_path):
    ok = (r"F111 and X7-SC and D2+H3 under H4, Q1, W0, C-mem at \const{$\rho = 1$} (Table~\ref{tab:q4}, \cite{holm1979}, "
          r"\label{sec:r2}) with \includegraphics[width=0.8\linewidth]{f1.png} of six markets")
    d = _setup(tmp_path, tex=_v(r"Replicated on \rvk{count}{q4.k} of six markets", r"Replicated on \rvk{count}{q4.k}; " + ok))
    assert N.check(d / "report.json", d / "numbers.tex", d / "main.tex") == []


def test_render_refuses_nonfinite_values():
    import pytest
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError):
            N.render({"q4": {"x": bad}})


R2 = {"q4": {"k": 5, "p": [0.0001, 0.2], "markets": {"fresh0": {"gain_diff": 0.27149, "p_gain": 0.00003}}},
      "q1": {"tests": {"C*-F111|D2+H3": {"estimate": -0.0123, "p": 0.0004, "category": "equivalent"}}}}
TEX2 = r"""% BEGIN-EV2
Replicated on \rvk{count}{q4.k} of six markets; d is \rvk{gain}{q1.tests.C*-F111|D2+H3.estimate} (\rvk{label}{q1.tests.C*-F111|D2+H3.category}).
% END-EV2
"""


def _setup2(tmp_path, tex, extra=None):
    (tmp_path / "report.json").write_text(json.dumps(R2)); (tmp_path / "main.tex").write_text(tex)
    for name, body in (extra or {}).items():
        (tmp_path / name).write_text(body)
    N.write(tmp_path / "report.json", tmp_path / "numbers.tex")
    return N.check(tmp_path / "report.json", tmp_path / "numbers.tex", tmp_path / "main.tex")


def test_kinds_pass_when_matching(tmp_path):
    assert _setup2(tmp_path, TEX2) == []


def test_kind_mismatch_fails_a_gain_used_as_count(tmp_path):
    bad = TEX2.replace(r"\rvk{count}{q4.k}", r"\rvk{count}{q1.tests.C*-F111|D2+H3.estimate}")
    assert bad != TEX2 and any("kind" in p for p in _setup2(tmp_path, bad))


def test_plain_rv_not_allowed_in_ev2_region(tmp_path):
    bad = TEX2.replace(r"\rvk{count}{q4.k}", r"\rv{q4.k}")
    assert bad != TEX2 and any("\\rvk" in p for p in _setup2(tmp_path, bad))


def test_report_value_outside_regions_is_flagged(tmp_path):
    bad = TEX2 + "In the discussion, the gap was 0.271.\n"
    assert any("0.271" in p for p in _setup2(tmp_path, bad))


def test_included_file_is_scanned(tmp_path):
    tex = TEX2 + "\\input{cap.tex}\n"
    assert any("0.271" in p for p in _setup2(tmp_path, tex, {"cap.tex": "% BEGIN-EV2\nCaption: gap 0.271.\n% END-EV2\n"}))


def test_small_p_values_keep_four_significant_digits():
    m = N.macros(R2)
    assert m["q4.p.0"] == "0.0001" and m["q4.markets.fresh0.p_gain"] == r"\ensuremath{3\times10^{-5}}"
    assert m["q1.tests.C*-F111|D2+H3.p"] == "0.0004" and m["q4.p.1"] == "0.2"
