"""Drift tests for the WEIS version: every number it shows comes from the same source path and kind as in the full
paper, and every result site of the full paper that the WEIS version leaves out is listed with a reason."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FULL = HERE.parent / "paper-v2"


def _load(p):
    return json.loads(Path(p).read_text())


def test_weis_sites_match_the_full_paper():
    full, weis = _load(FULL / "sites.json"), _load(HERE / "sites.json")
    bad = [k for k, v in weis.items() if k not in full or {x: v[x] for x in ("path", "kind")} != {x: full[k][x] for x in ("path", "kind")}]
    assert bad == [], f"WEIS sites not in the full paper, or with another path or kind: {bad}"


def test_dropped_sites_are_listed_with_reasons():
    full, weis, dropped = _load(FULL / "sites.json"), _load(HERE / "sites.json"), _load(HERE / "dropped.json")
    assert set(full) - set(weis) == set(dropped), "full-paper sites missing from the WEIS version must be listed in dropped.json"
    assert all(isinstance(r, str) and r.strip() for r in dropped.values()), "every dropped site needs a reason"
