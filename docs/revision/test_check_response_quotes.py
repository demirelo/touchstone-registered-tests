import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_response_quotes as C  # noqa: E402


def test_a_quote_absent_from_the_paper_is_reported():
    # the round-3 mistake: the note quoted "inside search error", which the paper never said
    assert C.missing('The text says "inside search error".', ["the window changes the gain, which is within search error"]) == ["inside search error"]


def test_line_breaks_and_the_section_reference_do_not_count_as_misses():
    src = "Section~\\ref{sec:results} reports an exploratory matched comparison"
    assert C.missing('"Section 9\n   reports an exploratory matched comparison"', [src]) == []
