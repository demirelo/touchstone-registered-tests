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


def test_dropped_reasons_name_sites_that_exist_where_stated():
    """A reason that names a replacement site must name one present in the WEIS version (lesson 2026-11-24)."""
    import re
    weis, dropped = _load(HERE / "sites.json"), _load(HERE / "dropped.json")
    for k, why in dropped.items():
        for name in re.findall(r"site ([a-z0-9_]+)", why):
            assert name in weis, f"{k}: reason names {name}, which is not in the WEIS version"
            sec = weis[name]["section"]
            if "Appendix" in why or "appendix" in why:
                assert sec.startswith("app"), f"{k}: reason says appendix, but {name} is in {sec}"
            if "Section" in why:
                assert not sec.startswith("app"), f"{k}: reason says a body section, but {name} is in {sec}"


def _title(tex: str) -> str:
    import re
    return re.search(r"\\title\{(.*)\}", tex).group(1)


def test_weis_title_differs_from_the_public_title():
    # The public release carries the full paper's title; a search for it would find the author (review, 2026-11-24).
    full, weis = (_title((d / "main.tex").read_text()) for d in (FULL, HERE))
    norm = lambda s: " ".join(s.replace("\\\\", " ").lower().split())
    assert norm(full) != norm(weis)
    assert "identities are free" not in norm(weis) and "checking newcomers when" not in norm(weis)


def test_both_versions_state_ai_use():
    for d in (FULL, HERE):
        assert "\\section*{Use of AI tools}" in (d / "main.tex").read_text(), d
