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


SITES = {"q4-count": {"path": "q4.k", "kind": "count", "section": "results"},
         "q1-d2h3-d": {"path": "q1.tests.C*-F111|D2+H3.estimate", "kind": "gain", "section": "results"},
         "abs-q4-count": {"path": "q4.k", "kind": "count", "section": "abstract"}}
TEX3 = r"""\begin{abstract}
% BEGIN-EV2
Replicated on \site{abs-q4-count} of six markets.
% END-EV2
\end{abstract}
\section{Introduction}\label{sec:intro}
Intro.
\section{Model}\label{sec:model}
Ten providers at \const{0.050} noise; evaluation 1 gave \evone{0.353}.
\section{The second test: results}\label{sec:results}
% BEGIN-EV2
Replicated on \site{q4-count} of six markets; d is \site{q1-d2h3-d}.
% END-EV2
\section{Discussion}\label{sec:discussion}
\section{Conclusion}\label{sec:conclusion}
"""


def _setup3(tmp_path, tex, sites=SITES, extra=None):
    (tmp_path / "sites.json").write_text(json.dumps(sites))
    return _setup2(tmp_path, tex, extra)


def _v3(old, new):
    assert old in TEX3, old
    return TEX3.replace(old, new)


def test_sites_pass_when_consistent(tmp_path):
    assert _setup3(tmp_path, TEX3) == []


def test_site_in_the_wrong_section_fails(tmp_path):
    bad = _v3(r"Replicated on \site{q4-count} of six markets; d is \site{q1-d2h3-d}.", r"d is \site{q1-d2h3-d}.").replace(
        r"Replicated on \site{abs-q4-count} of six markets.", r"Replicated on \site{q4-count} and \site{abs-q4-count}.")
    assert any("section" in p for p in _setup3(tmp_path, bad))


def test_site_used_twice_or_unused_fails(tmp_path):
    bad = _v3(r"d is \site{q1-d2h3-d}.", r"d is \site{q4-count}.")
    probs = _setup3(tmp_path, bad)
    assert any("twice" in p for p in probs) and any("unused" in p for p in probs)


def test_raw_path_macros_refused_in_regions(tmp_path):
    bad = _v3(r"d is \site{q1-d2h3-d}.", r"d is \site{q1-d2h3-d}, bound \rvk{gain}{q4.markets.fresh0.gain_diff}.")
    assert any("\\site" in p for p in _setup3(tmp_path, bad))


def test_results_section_must_be_fully_marked(tmp_path):
    bad = _v3("% END-EV2\n\\section{Discussion}", "% END-EV2\nReplicated on 4 of six markets.\n\\section{Discussion}")
    assert any("outside a result region" in p for p in _setup3(tmp_path, bad))


def test_unmarked_decimal_outside_regions_fails_even_if_not_a_report_value(tmp_path):
    bad = _v3("\\label{sec:discussion}", "\\label{sec:discussion}\nThe gap was 0.999.")
    assert any("0.999" in p for p in _setup3(tmp_path, bad))


def test_unmarked_decimal_in_included_caption_fails(tmp_path):
    bad = _v3("\\label{sec:discussion}", "\\label{sec:discussion}\n\\input{cap}")
    assert any("0.999" in p for p in _setup3(tmp_path, bad, extra={"cap.tex": "Caption: gain 0.999.\n"}))


def test_unknown_site_and_bad_manifest_path_fail(tmp_path):
    sites = dict(SITES, extra={"path": "q9.x", "kind": "gain", "section": "results"})
    probs = _setup3(tmp_path, _v3(r"d is \site{q1-d2h3-d}.", r"d is \site{q1-d2h3-d} \site{extra} \site{nope}."), sites)
    assert any("q9.x" in p for p in probs) and any("nope" in p for p in probs)


def test_results_label_on_its_own_line_and_missing_results_section(tmp_path):
    ok = _v3("\\section{The second test: results}\\label{sec:results}", "\\section{The second test: results}\n\\label{sec:results}")
    assert _setup3(tmp_path, ok) == []
    bad = _v3("\\label{sec:results}", "")
    assert any("required section results" in p for p in _setup3(tmp_path, bad))


def test_unmarked_integer_in_a_caption_or_discussion_fails(tmp_path):
    for add in ("\\caption{Replicated on 4 of six markets.}", "Replicated on 4 of six markets."):
        bad = _v3("\\label{sec:discussion}", "\\label{sec:discussion}\n" + add)
        assert any("unmarked number" in p for p in _setup3(tmp_path, bad)), add
    cap = _v3("\\label{sec:model}", "\\label{sec:model}\n\\input{cap}")
    assert any("caption outside a result region" in p for p in _setup3(tmp_path, cap, extra={"cap.tex": "\\caption{Replicated on 4 of six markets.}\n"}))


def test_model_section_integers_are_allowed(tmp_path):
    assert _setup3(tmp_path, _v3("Ten providers", "There are 10 providers and 50 jobs;")) == []


def test_site_only_in_a_comment_is_unused(tmp_path):
    bad = _v3(r"Replicated on \site{q4-count} of six markets; d is \site{q1-d2h3-d}.",
              r"% Replicated on \site{q4-count} of six markets; d is \site{q1-d2h3-d}." + "\nNothing here.")
    assert any("unused" in p for p in _setup3(tmp_path, bad))


def test_documented_limit_swap_of_two_sites_within_one_section_passes(tmp_path):
    """Stated limit (outline, Result sites): a swap of any two sites inside one section is not detected; the final read
    of the PDF against report.md covers it. This test pins the limit so a change to it is visible."""
    sw = _v3(r"Replicated on \site{q4-count} of six markets; d is \site{q1-d2h3-d}.",
             r"Replicated on \site{q1-d2h3-d} of six markets; d is \site{q4-count}.")
    assert _setup3(tmp_path, sw) == []


TEX4 = TEX3


def _v4(old, new):
    assert old in TEX4, old
    return TEX4.replace(old, new)


def test_full_labelled_paper_passes(tmp_path):
    assert _setup3(tmp_path, TEX4) == []


def test_unlabelled_section_fails(tmp_path):
    assert any("label" in p for p in _setup3(tmp_path, _v4("\\section{Model}\\label{sec:model}", "\\section{Model}")))


def test_subsection_sec_label_fails_and_keeps_parent(tmp_path):
    bad = _v4("% END-EV2\n\\section{Discussion}", "% END-EV2\n\\subsection{More}\\label{sec:more}\nReplicated on 4 of six markets.\n\\section{Discussion}")
    probs = _setup3(tmp_path, bad)
    assert any("sec: label" in p for p in probs) and any("results" in p and "4" in p for p in probs)


def test_introduction_count_fails(tmp_path):
    assert any("intro" in p for p in _setup3(tmp_path, _v4("Intro.", "Replicated on 4 of six markets.")))


def test_multiline_caption_and_macro_caption_outside_regions_fail(tmp_path):
    for cap in ("\\caption{\nReplicated on 4 of six markets.\n}\n", "\\caption{Count \\rvk{count}{q4.k}.}\n"):
        probs = _setup3(tmp_path, _v4("\\section{Model}\\label{sec:model}", "\\section{Model}\\label{sec:model}\n\\input{cap}"), extra={"cap.tex": cap})
        assert any("caption" in p for p in probs), cap


def test_escaped_backslash_percent_and_commented_input_hide_sites(tmp_path):
    sentence = r"Replicated on \site{q4-count} of six markets; d is \site{q1-d2h3-d}."
    probs = _setup3(tmp_path, _v4(sentence, r"Line break \\% " + sentence[13:]))
    assert any("unused" in p for p in probs)
    probs = _setup3(tmp_path, _v4(sentence, "% \\input{res}\nNothing."), extra={"res.tex": sentence + "\n"})
    assert any("unused" in p for p in probs)


def test_round6_parser_cases(tmp_path):
    assert any("without a" in p for p in _setup3(tmp_path, _v4("\\section{Model}\\label{sec:model}", "\\section{Model}\n\nText.")))
    assert _setup3(tmp_path, _v4("\\section{Model}\\label{sec:model}", "\\section{Model} \\label{sec:model}")) == []
    cap = _v4("\\label{sec:model}", "\\label{sec:model}\n\\caption\n{Replicated on 4 of six markets.}")
    assert any("caption" in p for p in _setup3(tmp_path, cap))
    fig = _v4("\\label{sec:model}", "\\label{sec:model}\n\\begin{figure}\nNote: 4 of six markets.\n\\end{figure}")
    assert any("figure or table" in p for p in _setup3(tmp_path, fig))


def _setup5(tmp_path, tex, floats):
    (tmp_path / "floats.json").write_text(json.dumps(floats))
    return _setup3(tmp_path, tex)


RES_FLOAT = "\\begin{table}\n\\caption{Replicated on \\site{q4-count} of six markets.}\\label{tab:q4}\n\\end{table}\n"


def test_listed_float_must_lie_wholly_in_a_region(tmp_path):
    inside = _v4("d is \\site{q1-d2h3-d}.", "d is \\site{q1-d2h3-d}.\n" + RES_FLOAT).replace(
        "Replicated on \\site{q4-count} of six markets; d", "D")
    assert _setup5(tmp_path, inside, ["tab:q4"]) == []
    assert any("tab:q9" in p for p in _setup5(tmp_path, inside, ["tab:q4", "tab:q9"]))
    half = inside.replace("\\label{tab:q4}\n\\end{table}", "\\label{tab:q4}\n% END-EV2\nNote.\n% BEGIN-EV2\n\\end{table}")
    assert any("tab:q4" in p and "wholly" in p for p in _setup5(tmp_path, half, ["tab:q4"]))


def test_float_lines_after_a_region_end_and_one_line_floats_are_scanned(tmp_path):
    one = _v4("\\label{sec:model}", "\\label{sec:model}\n\\begin{figure}Note: 4 of six markets.\\end{figure}")
    assert any("figure or table" in p for p in _setup3(tmp_path, one))
    split = _v4("\\label{sec:model}", "\\label{sec:model}\n% BEGIN-EV2\n\\begin{figure}\n% END-EV2\nNote: 4 of six markets.\n\\end{figure}")
    assert any("figure or table" in p for p in _setup3(tmp_path, split))


def test_two_float_commands_on_one_line_refused(tmp_path):
    bad = _v4("\\label{sec:model}", "\\label{sec:model}\n\\begin{figure}\\end{figure}\\begin{figure}\nNote: 4 of six markets.\n\\end{figure}")
    assert any("one float command per line" in p for p in _setup3(tmp_path, bad))


def test_digit_subscripts_are_identifiers_not_numbers(tmp_path):
    ok = _v4("\\label{sec:model}", "\\label{sec:model}\n\\begin{table}\nRule $F_{111}$ and $g_{F_{000}}$ and $x_1$.\n\\end{table}")
    assert _setup3(tmp_path, ok) == []
    bad = _v4("\\label{sec:model}", "\\label{sec:model}\n\\begin{table}\nGap \\textbf{0.271}.\n\\end{table}")
    assert any("figure or table" in p for p in _setup3(tmp_path, bad))


def test_extra_sources_merge_under_their_names(tmp_path):
    (tmp_path / "scoring.json").write_text(json.dumps({"Q4-a": {"status": "fulfilled"}}))
    sites = dict(SITES, **{"q4-pred": {"path": "scoring.Q4-a.status", "kind": "label", "section": "results"}})
    tex = _v4(r"d is \site{q1-d2h3-d}.", r"d is \site{q1-d2h3-d}; prediction \site{q4-pred}.")
    (tmp_path / "sites.json").write_text(json.dumps(sites)); (tmp_path / "report.json").write_text(json.dumps(R2))
    (tmp_path / "main.tex").write_text(tex)
    extra = {"scoring": tmp_path / "scoring.json"}
    N.write(tmp_path / "report.json", tmp_path / "numbers.tex", extra)
    assert N.check(tmp_path / "report.json", tmp_path / "numbers.tex", tmp_path / "main.tex", extra) == []
    assert "fulfilled" in (tmp_path / "numbers.tex").read_text()
