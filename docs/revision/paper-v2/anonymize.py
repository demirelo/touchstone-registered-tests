"""Build the double-anonymous submission source from main.tex and refuse it if an identifying string remains.
Usage: anonymize.py main.tex out.tex   (exit 1 and a list of findings if the output still identifies the author)"""
import re
import sys
from pathlib import Path

# Strings that identify the author or let a reviewer find the repository. Checked case-insensitively.
FORBIDDEN = [r"ömer", r"demirel", r"progfi", r"house\.markets", r"oemer", r"cba512aa",
             r"\bthe author\b", r"\\author\{(?!Anonymous submission\})"]
SUBS = [
    (r"\\author\{[^}]*\}", r"\\author{Anonymous submission}"),
    (r"\\texttt\{cba512aa\\ldots\}", "[hash withheld for review]"),
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
