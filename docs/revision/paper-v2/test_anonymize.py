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
