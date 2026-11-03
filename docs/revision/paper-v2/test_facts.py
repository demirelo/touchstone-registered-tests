"""Facts in the paper that the code determines are checked against the code (lesson 2026-11-03: knob counts written from
memory were wrong). The family table's knob column must equal the registered family's knob count."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
TEX = Path(__file__).resolve().parent / "main.tex"


def _table_counts() -> dict:
    body = TEX.read_text().split("\\label{tab:families}")[0].rsplit("\\begin{table}", 1)[1]
    out = {}
    for row in body.split("\\\\"):
        cells = [c.strip() for c in row.split("&")]
        if len(cells) == 4:
            m = re.fullmatch(r"(?:at most )?\\const\{(\d+)\}", cells[2])
            if m:
                out[cells[0].split("\\midrule")[-1].strip()] = int(m.group(1))
    return out


def test_family_table_knob_counts_match_the_code():
    from scripts import revision_v2 as RV
    counts = _table_counts()
    assert {"D2", "D2+H3", "X7-SC"} <= set(counts), counts
    for fam, n in counts.items():
        if fam in ("H4",) or "," in fam:
            continue
        f = RV.family_for(fam, 200, 10)
        k = getattr(f, "knobs", None) or getattr(f, "bounds", None) or getattr(f, "space", None)
        assert len(k) == n, (fam, n, len(k))


def test_every_bibliography_entry_has_a_doi_or_url():
    """Outline R2: every entry carries an identifier that the style prints."""
    t = (Path(__file__).resolve().parent / "refs.bib").read_text()
    starts = [m.start() for m in re.finditer(r"^@\w+\{", t, re.M)]
    ents = [t[a:b] for a, b in zip(starts, starts[1:] + [len(t)])]
    missing = [re.match(r"@\w+\{([^,]+)", e).group(1) for e in ents if not re.search(r"\b(doi|url)\s*=", e)]
    assert len(ents) >= 30 and not missing, missing
