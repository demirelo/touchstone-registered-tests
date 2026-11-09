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


def test_predictions_rows_carry_their_own_status_and_cells():
    sc = {"Q1-a": {"status": "fulfilled", "cells": [{"cell": "D2+H3", "status": "fulfilled", "value": "equivalent"}]},
          "Q2-a": {"status": "failed", "cells": [{"cell": "G", "status": "fulfilled", "value": -0.0952},
                                                 {"cell": "S", "status": "failed", "value": 0.0039}]},
          "Q4-b": {"status": "not assessed", "cells": []}}
    tex = T.predictions(sc)
    assert "fulfilled" in _row(tex, "Q1-a") and "equivalent" in _row(tex, "Q1-a")
    r = _row(tex, "Q2-a")
    assert r.split("&")[2].strip() == "failed" and "S 0.0039 failed" in r and "-0.0952" in r.replace("\\ensuremath{", "").replace("}", "")
    assert "not assessed" in _row(tex, "Q4-b")


def test_prediction_pairs_are_labelled_and_rounded():
    sc = {"Q2-d": {"status": "failed", "cells": [{"cell": "P D2+H3", "status": "failed", "value": [-0.08739750289482723, -0.0831087194]}]},
          "Q3-d": {"status": "fulfilled", "cells": [{"cell": "F111 c2_staggered", "status": "fulfilled", "value": [-0.0019989738, 0.07708038]}]}}
    tex = T.predictions(sc).replace("\\ensuremath{", "").replace("}", "")
    assert "fixed -0.08740, searched -0.08311" in _row(tex, "Q2-d")
    assert "G_min -0.00200, G_tot 0.07708" in _row(tex, "Q3-d").replace("\\_", "_")
    assert "0.08739" not in tex and "[" not in tex.split("midrule")[1]


def test_prediction_statements_come_from_the_registered_table():
    md = "| ID | Quantity | Where | Condition |\n|---|---|---|---|\n| Q1-a | category, D2+H3 | pooled fresh | \\| x \\| < 0.05 |\n"
    st = T.statements(md)
    assert st == {"Q1-a": "category, D2+H3 (pooled fresh): | x | < 0.05"}
    tex = T.predictions({"Q1-a": {"status": "fulfilled", "cells": []}}, st)
    assert "category, D2+H3" in _row(tex, "Q1-a")


def test_all_prediction_pairs_are_named_and_precise():
    sc = {"Q3-e": {"status": "fulfilled", "cells": [{"cell": "headline", "status": "fulfilled", "value": [0.04312, 0.04301]}]},
          "Q4-b": {"status": "fulfilled", "cells": [{"cell": "fresh0", "status": "fulfilled", "value": [1.0, 0.0001]}]}}
    tex = T.predictions(sc).replace("\\ensuremath{", "").replace("}", "")
    assert "F111 0.04312, C* 0.04301" in _row(tex, "Q3-e").replace("C$^*$", "C*")
    assert "value 1" not in tex and "p'" in _row(tex, "Q4-b")


def test_predictions_split_into_two_tables_by_question():
    sc = {k: {"status": "fulfilled", "cells": []} for k in ("Q1-a", "Q2-a", "Q3-a", "Q4-a")}
    a, b = T.predictions(sc, ids=("Q1", "Q2")), T.predictions(sc, ids=("Q3", "Q4"))
    assert "Q1-a" in a and "Q3-a" not in a and "Q4-a" in b and "Q2-a" not in b


def test_close_values_stay_distinguishable_and_q3f_pairs_are_named():
    sc = {"Q3-e": {"status": "fulfilled", "cells": [{"cell": "headline", "status": "fulfilled", "value": [0.0426027286, 0.0425939768]}]},
          "Q3-c": {"status": "fulfilled", "cells": [{"cell": "fresh2 C*", "status": "fulfilled", "value": -0.00041}]},
          "Q3-f": {"status": "failed", "cells": [{"cell": "F000<F111 W0", "status": "fulfilled", "value": [0.8387, 0.8403]}]}}
    tex = T.predictions(sc).replace("\\ensuremath{", "").replace("}", "")
    assert "0.04260" in tex and "0.04259" in tex
    assert "-0.0004" in _row(tex, "Q3-c")
    assert "F000 efficiency" in _row(tex, "Q3-f") and "value 1" not in tex


def test_p_value_columns_say_what_they_print(report):
    """Round-5 review: the report stores raw Q4 component p-values and the calibrated Q1 value that enters Holm; each column
    label must name that quantity, and the Holm-adjusted values are printed beside them."""
    q4 = T.q4(report); hdr = q4.split("\\midrule")[0]
    assert "Raw $p_{\\mathrm{gain}}$" in hdr and "Raw $p_{\\mathrm{eff}}$" in hdr and "Holm-adj." in hdr and "p'_{\\mathrm{gain}}" not in hdr
    q = report["q4"]; adj = T.holm_adjusted(q["p"])
    for i, m in enumerate(W.FRESH):
        if isinstance(q["markets"][m], dict):
            assert T._fmt_p(adj[i]) in _row(q4, m)
    q1 = T.q1(report); hdr = q1.split("\\midrule")[0]
    assert "$p'$ to Holm" in hdr and "Holm-adj." in hdr


def test_side_table_names_false_failure_refunds_and_the_service_fraction(report):
    # external review round 6: the refund fields count refunds on failed audits of honest play, not all refunds
    side = T.q1_side(report)
    assert "False-fail refunds (focal)" in side and "Service fraction" in side and "Served share" not in side


def _elig():
    st = lambda n, q, d: {"numerical": n, "q3": q, "descriptive": d}
    return {"tally": {"numerical": {"fulfilled": 10, "failed": 8, "not assessed": 0},
                      "q3": {"fulfilled": 7, "failed": 8, "not assessed": 3},
                      "descriptive": {"fulfilled": 6, "failed": 5, "not assessed": 7}},
            "targets": {"Q3-b": {"decision": False, "status": st("fulfilled", "not assessed", "not assessed")},
                        "Q2-b": {"decision": False, "status": st("failed", "failed", "not assessed")},
                        "Q3-c": {"decision": False, "status": st("failed", "failed", "failed")}}}


def test_prediction_rows_mark_the_targets_a_stricter_eligibility_reading_changes():
    # external review round 7: Q3-b is not assessed under both stricter readings, Q2-b only under the broader one
    sc = {k: {"status": v["status"]["numerical"], "cells": []} for k, v in _elig()["targets"].items()}
    a, b = T.predictions(sc, ids=("Q2",), elig=_elig()), T.predictions(sc, ids=("Q3",), elig=_elig())
    assert _row(b, "Q3-b").split("&")[2].strip() == "fulfilled$^{\\dagger}$"
    assert _row(a, "Q2-b").split("&")[2].strip() == "failed$^{\\ddagger}$"
    assert _row(b, "Q3-c").split("&")[2].strip() == "failed"
    assert T.predictions(sc, ids=("Q3",)) == T.predictions(sc, ids=("Q3",), elig=None)      # no map, no marks


def test_eligibility_table_gives_each_reading_its_tally_and_changed_predictions():
    tex = T.eligibility(_elig())
    assert "Numerical (as scored) & 10 & 8 & 0" in tex and "& 7 & 8 & 3 &" in tex and "& 6 & 5 & 7 &" in tex
    assert "Q3-b" in _row(tex, "Flagged inputs, Q3") and "Q2-b" not in _row(tex, "Flagged inputs, Q3")
    assert "Q2-b" in _row(tex, "Flagged inputs, all non-exempt cells")


def test_eligibility_table_adds_the_direct_input_tallies_when_the_map_has_them():
    # external review round 8: Table 21 should carry both direct-input tallies (7/8/3 and 6/5/7 in the real map)
    e = _elig()
    assert "direct inputs" not in T.eligibility(e)                # an old map without them: no extra rows
    e["tally_direct_inputs"] = {"q3": {"fulfilled": 7, "failed": 8, "not assessed": 3},
                                "descriptive": {"fulfilled": 6, "failed": 5, "not assessed": 7}}
    tex = T.eligibility(e)
    assert _row(tex, "Flagged direct inputs only, Q3").split("&")[1:4] == [" 7 ", " 8 ", " 3 "]
    assert _row(tex, "Flagged direct inputs only, all non-exempt cells").split("&")[1:4] == [" 6 ", " 5 ", " 7 "]
