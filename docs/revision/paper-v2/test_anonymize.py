import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import anonymize as A  # noqa: E402

SRC = r"""\title{T}
\author{Ömer Demirel}
\begin{document}
at the author's request; started by the author, wrote; bundle SHA-256 \texttt{cba512aa\ldots}).
"""


def test_anonymize_removes_identifying_strings():
    out = A.anonymize(SRC)
    assert A.problems(out) == []
    assert "\\author{Anonymous submission}" in out and "the authors'" in out and "by the authors," in out


def test_check_finds_each_identifying_string():
    for bad in ("Ömer", "Demirel", "progfi", "house.markets", "oemer", "cba512aa", "the author's", "\\author{X}"):
        assert A.problems("\\author{Anonymous submission}\n" + bad), bad


def test_real_paper_anonymizes_cleanly():
    out = A.anonymize((Path(__file__).resolve().parent / "main.tex").read_text())
    assert A.problems(out) == []


def test_release_links_are_withheld():
    tex = r"public at \url{https://github.com/demirelo/touchstone-registered-tests} (archived at \url{https://doi.org/10.5281/zenodo.24498973})"
    out = A.anonymize(tex)
    assert A.problems(out) == [] and out.count("[withheld for review]") == 2
    assert A.problems(tex)                                    # the raw links are refused


def test_release_identifiers_are_masked():
    tex = (r"block \const{974379}; $H = \const{974451}$; tag \texttt{protocol-v2}; branch \texttt{two20k}; "
           r"(release v2.1, x); locked on 17 October 2026; (published erratum); committed, timestamped with OpenTimestamps, and published, and")
    out = A.anonymize(tex)
    assert A.problems(out) == [] and "[withheld for review]" in out and "protocol-v2" not in out
    assert len(A.problems(tex)) >= 6                          # each raw identifier is refused


def test_pdf_check_flags_identifiers_and_allows_third_party_github():
    import check_anon_pdf as C
    assert C.findings("see https://github.com/BOINC/boinc/wiki and block 123") == []
    assert len(C.findings("Demirel, block 974451, tag protocol-v2, zenodo.24499068")) == 4


def test_dates_paths_model_and_timestamps_are_masked():
    tex = ("\\documentclass[11pt]{article}\n\\date{November 2026}\n\\section{The first test (October 2026)}\n"
           "locked on 17 October 2026; approved 12 November 2026; in October~\\const{2026}; \\texttt{docs/revision/audit}; "
           "\\texttt{sealed2/h4/}; wrote H4 (gpt-6.1-sol)")
    out = A.anonymize(tex)
    assert A.problems(out) == [], A.problems(out)
    assert "\\pdfinfoomitdate=1" in out and "\\date{}" in out and "\\section{The first test}" in out
    assert len(A.problems(tex)) >= 6
