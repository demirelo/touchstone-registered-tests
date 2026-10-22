"""Family names of protocol v2 and the candidate reconstruction shared by the runner, tuning, and coverage."""
from __future__ import annotations

from .cell import Abstain
from .policies.families import D2, Family
from .policies.honest import HonestMax
from .policies.identity import h3_family
from .policies.v2 import x5v2_family, x6v2_family
from .policies.x7 import x7_family
from .reference import Candidate


def family_for(name: str, T: int, L: int, h4_source=None) -> Family:
    if name == "D2":
        return D2
    if name == "D2+H3":
        return h3_family(D2)
    if name == "X7-SC":
        return x7_family(T, L)
    if name == "X5-AG/v2":
        return x5v2_family(T, L)
    if name == "X6-SE/v2":
        return x6v2_family(T, L)
    if name == "H4":
        if h4_source is None:
            raise ValueError("H4 is not loaded")
        return h4_source.family(T, L)
    raise ValueError(f"unknown family {name!r}")


def cand_from_json(d: dict, h4_source=None) -> Candidate:
    if d["knobs"] is None:
        return Candidate(d["name"], Abstain if d["name"] == "abstain" else HonestMax, None)
    fam = family_for(d["family"], int(d["T"]), int(d["L"]), h4_source); k = dict(d["knobs"])
    return Candidate(d["name"], lambda: fam.make(k), k)
