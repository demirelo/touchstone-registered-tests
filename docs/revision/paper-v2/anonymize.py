"""Build the double-anonymous submission source from main.tex and refuse it if an identifying string remains.
Usage: anonymize.py main.tex out.tex   (exit 1 and a list of findings if the output still identifies the author)"""
import re
import sys
from pathlib import Path

# Strings that identify the author or let a reviewer find the repository. Checked case-insensitively.
FORBIDDEN = [r"ömer", r"demirel", r"progfi", r"house\.markets", r"oemer", r"cba512aa",
             r"\bthe author\b", r"\\author\{(?!Anonymous submission\})", r"zenodo\.\d", r"github\.com/",
             # searchable identifiers of the public release (WEIS review, 2026-11-24): block heights, tags, branch, dates
             r"\b97\d{4}\b", r"protocol-v2", r"two20k", r"17 October 2026", r"published erratum", r"release v\d"]
SUBS = [
    (r"\\author\{[^}]*\}", r"\\author{Anonymous submission}"),
    (r"\\texttt\{cba512aa\\ldots\}", "[hash withheld for review]"),
    (r"\\url\{https://(github\.com|doi\.org)/[^}]*\}", "[withheld for review]"),   # the release repository and its Zenodo records
    (r"\\const\{97\d{4}\}", r"\\text{[withheld for review]}"),     # Bitcoin block heights of the draw; \text keeps the spaces in math mode
    (r"\\texttt\{protocol-v2\}", "[tag withheld for review]"),
    (r"\\texttt\{two20k\}", "[branch withheld for review]"),
    (r"release v\d+\.\d+", "the release"),
    (r"17 October 2026", "[date withheld for review]"),
    (r"\(published erratum\)", "(erratum)"),
    (r"timestamped with OpenTimestamps, and published,", "timestamped with OpenTimestamps,"),
    (r"\bthe author's\b", "the authors'"),
    (r"\bthe author\b", "the authors"),
]


def anonymize(tex: str) -> str:
    for pat, rep in SUBS:
        tex = re.sub(pat, rep, tex)
    return tex


def problems(tex: str) -> list:
    return [f"{p}: {m.group(0)!r}" for p in FORBIDDEN for m in re.finditer(p, tex, re.I)]


def main(argv) -> int:
    out = anonymize(Path(argv[0]).read_text())
    bad = problems(out)
    if bad:
        print("\n".join(bad)); return 1
    Path(argv[1]).write_text(out); print("anonymized ok"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
