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


def test_pdf_check_flags_the_public_title():
    import check_anon_pdf as C
    assert C.findings("Checking Newcomers When\nIdentities Are Free: Registered Tests")
    assert C.findings("Checking newcomers is an old idea.") == []


def test_author_to_authors_keeps_verb_agreement():
    # "the author is" became "the authors is" in the AI-use statement (2026-11-24).
    import re
    for d in ("paper-v2", "paper-weis"):
        src = Path(__file__).resolve().parents[1] / d / "main.tex"
        if not src.exists():   # the WEIS copy lives only on the private branch weis-private
            continue
        out = A.anonymize(src.read_text())
        assert not re.search(r"\bthe authors (is|was|has|does)\b", out), d


def test_pdf_check_scans_compressed_streams_for_embedded_dates(tmp_path):
    # Figure PDFs carried their own creation dates inside compressed streams (round 2, 2026-11-25); pdftotext missed them.
    import zlib
    import check_anon_pdf as C
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.5\n1 0 obj<</Filter/FlateDecode>>stream\n" + zlib.compress(b"/CreationDate (D:20261104210106+02'00')")
                    + b"\nendstream endobj\n%%EOF")
    assert C.raw_findings(pdf.read_bytes())
    assert C.raw_findings(b"%PDF-1.5 plain /Producer (pdfTeX)") == []
