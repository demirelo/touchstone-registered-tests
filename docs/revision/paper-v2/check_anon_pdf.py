"""Refuse an anonymized PDF that still shows an identifying or searchable string (WEIS double-anonymous review).
Checks the extracted text (pdftotext) and the document information. Usage: check_anon_pdf.py PDF"""
import re
import subprocess
import sys

# Specific literals (case-insensitive). Third-party URLs (for example the BOINC wiki on github.com) stay allowed.
PDF_FORBIDDEN = [r"ömer", r"demirel", r"oemer", r"progfi", r"house\.markets", r"7556489", r"touchstone-registered",
                 r"zenodo\.2449", r"\b97\d{4}\b", r"protocol-v2", r"two20k", r"17 October 2026", r"cba512aa"]


def findings(text: str) -> list:
    return [f"{p}: {m.group(0)!r}" for p in PDF_FORBIDDEN for m in re.finditer(p, text, re.I)]


def main(argv) -> int:
    pdf = argv[0]
    text = subprocess.run(["pdftotext", "-q", pdf, "-"], capture_output=True, text=True, check=True).stdout
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    bad = findings(text) + [f"metadata {f}" for f in findings(info)]
    print("\n".join(bad) if bad else "anonymous pdf ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
