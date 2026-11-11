"""Guard (lesson 2026-11-11): every "quoted" phrase in a review package's response note must occur in the paper source
or the operations ledger (whitespace-normalised; Section~\\ref{sec:results} read as "Section 9"). Exit 1 on any miss.
Usage: check_response_quotes.py RESPONSE.md [SOURCE ...]"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT = (HERE / "paper-v2" / "main.tex", HERE / "operations-ledger.md")


def _n(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("Section~\\ref{sec:results}", "Section 9"))


def missing(response: str, sources: list[str]) -> list[str]:
    text = " ".join(_n(s) for s in sources)
    return [q for q in re.findall(r'"([^"]+)"', response) if _n(q) not in text]


def main(argv) -> int:
    srcs = [Path(p).read_text() for p in (argv[1:] or DEFAULT)]
    bad = missing(Path(argv[0]).read_text(), srcs)
    for q in bad:
        print("MISSING:", q)
    print("quotes ok" if not bad else f"{len(bad)} quotes not in the sources")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
