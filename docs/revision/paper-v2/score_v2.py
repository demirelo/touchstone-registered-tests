"""Scores the hashed predictions (docs/revision/predictions-v2.md, scoring table) from report.json and cells.json.
A prediction over several cells is scored cell by cell: failed if any assessed cell fails; fulfilled only if every
required cell is assessed and fulfilled; otherwise not assessed. A cell is not assessed when its value is missing,
cut, refused, or a status string. Descriptive only: predictions change no decision."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FRESH = tuple(f"fresh{i}" for i in range(6))
MARKETS = FRESH + ("headline",)
NA = "not assessed"
KAPPA_Q4 = 0.25                       # experiments/protocol-v2.yaml, admitted Q4 multiplier


def _cal(p, kappa: float = KAPPA_Q4):
    """p' = min(1, p / kappa) (design 9.2): Q4-b is registered on the calibrated component p-values."""
    return None if _num(p) is None else min(1.0, float(p) / kappa)


def _num(x):
    return float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def _cell(name, value, test) -> dict:
    v = _num(value) if not isinstance(value, (tuple, list)) else value
    if v is None or (isinstance(v, (tuple, list)) and any(_num(z) is None for z in v)):
        return {"cell": name, "value": None, "status": NA}
    return {"cell": name, "value": v, "status": "fulfilled" if test(v) else "failed"}


def _combine(cells: list) -> dict:
    st = [c["status"] for c in cells]
    status = "failed" if "failed" in st else "fulfilled" if st and all(s == "fulfilled" for s in st) else NA
    return {"status": status, "cells": cells}


def _get(d, *path):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def _gain(cells, m, rule, fam):
    return _get(cells, f"{m}@rho0.2|{rule}|{fam}|profit", "gain")


def score(rep: dict, cells: dict) -> dict:
    out = {}
    q1 = lambda f: _get(rep, "q1", "tests", f"C*-F111|{f}") or {}
    cat = lambda f: q1(f).get("category") if isinstance(q1(f).get("category"), str) else None
    c = cat("D2+H3")
    out["Q1-a"] = _combine([{"cell": "D2+H3", "value": c, "status": NA if c is None or c.startswith("not decided") or c == "refused"
                             else "fulfilled" if c == "equivalent, direction R3 lower" else "failed"}])
    est = _num(q1("D2+H3").get("estimate"))
    out["Q1-a-alt"] = _combine([{"cell": "D2+H3", "value": c, "status": NA if c is None or est is None or c.startswith("not decided")
                                 else "fulfilled" if (c == "ordered, size not established" and est > 0) else "failed"}])
    c = cat("X7-SC")
    out["Q1-b"] = _combine([{"cell": "X7-SC", "value": c, "status": NA if c is None or c.startswith("not decided") or c == "refused"
                             else "fulfilled" if c in ("equivalent", "equivalent, direction R3 lower") else "failed"}])
    neg = lambda v: None if v is None else -v                     # the report's side fields are F111 minus C*; Q1-c is C* minus F111
    out["Q1-c"] = _combine([_cell(f, neg(_get(q1(f), "side", "gross_eff_diff")), lambda v: -0.01 <= v <= 0.01) for f in ("D2+H3", "X7-SC")])
    out["Q1-d"] = _combine([{"cell": f, "value": q1(f).get("better"), "status": NA if cat(f) is None or "efficiency" not in q1(f)
                             else "fulfilled" if q1(f).get("better") is None else "failed"} for f in ("D2+H3", "X7-SC")])
    s = lambda kind, f, k: _get(rep, "q2", kind, f, k, "estimate")
    out["Q2-a"] = _combine([_cell(k, s("searched", "D2+H3", k), lambda v: v <= -0.05) for k in ("G", "S")])
    out["Q2-b"] = _combine([_cell("P", s("searched", "D2+H3", "P"), lambda v: abs(v) < 0.03)])
    out["Q2-c"] = _combine([_cell("PG", s("searched", "D2+H3", "PG"), lambda v: abs(v) < 0.03),
                            _cell("PS", s("searched", "D2+H3", "PS"), lambda v: abs(v) < 0.03),
                            _cell("GS", s("searched", "D2+H3", "GS"), lambda v: v <= 0)])
    out["Q2-d"] = _combine([_cell(f"{k} {f}", (s("fixed", f, k), s("searched", f, k)), lambda v: abs(v[0]) < abs(v[1]))
                            for f in ("D2+H3", "X7-SC") for k in ("P", "G", "S")])
    diff = lambda m, r, a, b: (None if _gain(cells, m, r, a) is None or _gain(cells, m, r, b) is None
                               else _gain(cells, m, r, a) - _gain(cells, m, r, b))
    out["Q3-a"] = _combine([_cell(f"{m} {r}", diff(m, r, "X7-SC", "D2+H3"), lambda v: v < 0.05) for m in MARKETS for r in ("F111", "C*")])
    out["Q3-b"] = _combine([_cell("headline F111", diff("headline", "F111", "H4", "X7-SC"), lambda v: v <= 0.05)])
    out["Q3-c"] = _combine([_cell(f"{m} {r}", diff(m, r, "X5-AG/v2", "D2+H3"), lambda v: v < 0) for m in MARKETS for r in ("F111", "C*")])
    groups = ["c2_synchronised", "c2_staggered", "c5_synchronised", "c5_staggered", "c2_roles"]
    co = lambda r, g: _get(rep, "q3", "coalition", r, g)
    out["Q3-d"] = _combine([_cell(f"{r} {g}", (_get(co(r, g), "G_min", "estimate"), _get(co(r, g), "G_tot", "estimate")),
                                  lambda v: v[0] - 0.5 * v[1] <= 0) for r in ("F111", "C*") for g in groups])
    ben = lambda r: (_get(cells, f"headline@rho0.2|{r}|X8-DB|total|c2_roles", "member_gain") or [None])[0]
    out["Q3-e"] = _combine([_cell("headline", (ben("F111"), ben("C*")), lambda v: v[0] > v[1])])
    eff = lambda r, o: _get(rep, "q3", "welfare_selected", r, o, "result", "efficiency")
    out["Q3-f"] = _combine([_cell(f"{r} {o}", eff(r, o), lambda v: v >= 0.90) for o in ("W0", "W1") for r in ("F111", "C*")]
                           + [_cell(f"F000<F111 {o}", (eff("F000", o), eff("F111", o)), lambda v: v[0] < v[1]) for o in ("W0", "W1")])
    rp = lambda r: _get(rep, "secondary", "repair_rho1", r, "D2", "estimate")
    out["Q3-g"] = _combine([_cell("headline rho1", (rp("F111"), rp("R4")), lambda v: v[0] - v[1] >= 0.10)])
    k = _get(rep, "q4", "k")
    out["Q4-a"] = _combine([_cell("k", k, lambda v: v >= 5)])
    mk = _get(rep, "q4", "markets") or {}
    elig = [m for m in (_get(rep, "q4", "failing") or []) if isinstance(mk.get(m), dict)]
    out["Q4-b"] = _combine([_cell(m, (_cal(mk[m].get("p_gain")), _cal(mk[m].get("p_eff"))), lambda v: v[0] > v[1]) for m in elig])
    return out


# Eligibility (external review round 7). predictions-v2.md: a target that is "incomplete (design 6.5)" is not assessed;
# design 6.5 calls a search-flagged cell "incomplete" and keeps its estimate for the prescribed search procedure, and keeps
# every confirmatory decision that uses it. score() above reads the numbers only; the map below names each cell's
# required searches and rescored the predictions under two stricter readings. Descriptive only.
RULES8 = tuple(f"F{a}{b}{c}" for a in "01" for b in "01" for c in "01")
DECISIONS = frozenset({"Q1-a", "Q1-a-alt", "Q1-b", "Q1-d", "Q4-a", "Q4-b"})   # score a confirmatory decision or its label
SCOPES = ("numerical", "q3", "descriptive")
COALITION_FAMILY = {"c2_roles": "X8-DB"}                                   # the other coalition groups are X6-SE/v2


def _sid(m, r, fam, obj="profit", grp=None, rho="0.2"):
    return f"{m}@rho{rho}|{r}|{fam}|{obj}" + (f"|{grp}" if grp else "")


def inputs(pid: str, cell: str) -> list:
    """The searches a prediction cell needs (ids as in the report's search_flagged list)."""
    q1 = lambda fam: [_sid(m, r, fam) for m in FRESH for r in ("C*", "F111")]
    q2 = lambda fam: [_sid(m, r, fam) for m in FRESH for r in RULES8]          # searched cells and the fixed-attack bank
    if pid in ("Q1-a", "Q1-a-alt"):
        return q1("D2+H3")
    if pid in ("Q1-b", "Q1-c", "Q1-d"):
        return q1(cell)
    if pid in ("Q2-a", "Q2-b", "Q2-c"):
        return q2("D2+H3")
    if pid == "Q2-d":
        return q2(cell.split()[1])
    if pid in ("Q3-a", "Q3-b", "Q3-c"):
        m, r = cell.split()
        a, b = {"Q3-a": ("X7-SC", "D2+H3"), "Q3-b": ("H4", "X7-SC"), "Q3-c": ("X5-AG/v2", "D2+H3")}[pid]
        return [_sid(m, r, a), _sid(m, r, b)]
    if pid == "Q3-d":
        r, g = cell.split()
        fam = COALITION_FAMILY.get(g, "X6-SE/v2")
        return [_sid("headline", r, fam, "min", g), _sid("headline", r, fam, "total", g)]
    if pid == "Q3-e":
        return [_sid("headline", r, "X8-DB", "total", "c2_roles") for r in ("F111", "C*")]
    if pid == "Q3-f":
        rules, o = (("F000", "F111"), cell.split()[1]) if cell.startswith("F000<") else ((cell.split()[0],), cell.split()[1])
        return [_sid("headline", r, f, o) for r in rules for f in ("D2+H3", "X7-SC")]
    if pid == "Q3-g":
        return [_sid("headline", r, "D2", rho="1") for r in ("F111", "R4")]
    if pid == "Q4-a":
        return [_sid(m, r, "D2+H3") for m in FRESH for r in ("F000", "F111")]
    if pid == "Q4-b":
        return [_sid(cell, r, "D2+H3") for r in ("F000", "F111")]
    raise ValueError(f"no input map for {pid}")


def eligibility(sc: dict, flagged, scope: str) -> dict:
    """Each cell lists its flagged required searches. Under 'q3' (the reviewer's reading) a Q3 cell with a flagged input is
    not assessed; under 'descriptive' every cell outside DECISIONS is; 'numerical' keeps the scorer's statuses."""
    if scope not in SCOPES:
        raise ValueError(f"unknown scope {scope}")
    fl, out = set(flagged), {}
    for pid, v in sc.items():
        hit = scope == "descriptive" and pid not in DECISIONS or scope == "q3" and pid.startswith("Q3-")
        cells = []
        for c in v.get("cells", []):
            f = [x for x in inputs(pid, c["cell"]) if x in fl]
            cells.append({**c, "flagged": f, "status": NA if (hit and f) else c["status"]})
        out[pid] = {**_combine(cells), "cells": cells} if cells else dict(v)
    return out


def tally(sc: dict) -> dict:
    st = [v["status"] for v in sc.values()]
    return {s: st.count(s) for s in ("fulfilled", "failed", NA)}


def eligibility_map(sc: dict, flagged) -> dict:
    by = {s: eligibility(sc, flagged, s) for s in SCOPES}
    return {"flagged": sorted(set(flagged)), "tally": {s: tally(by[s]) for s in SCOPES},
            "targets": {pid: {"decision": pid in DECISIONS, "status": {s: by[s][pid]["status"] for s in SCOPES},
                              "flagged": sorted({x for c in by["numerical"][pid].get("cells", []) for x in c["flagged"]}),
                              "cells": {c["cell"]: c["flagged"] for c in by["numerical"][pid].get("cells", []) if c["flagged"]}}
                        for pid in sorted(sc)}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--report", required=True); ap.add_argument("--cells", required=True)
    ap.add_argument("--write", required=True)
    ap.add_argument("--eligibility", help="also write the eligibility map (flagged inputs, three readings) here")
    a = ap.parse_args(argv); rep = json.loads(Path(a.report).read_text())
    sc = score(rep, json.loads(Path(a.cells).read_text()))
    Path(a.write).write_text(json.dumps(sc, indent=1, sort_keys=True))
    if a.eligibility:
        Path(a.eligibility).write_text(json.dumps(eligibility_map(sc, rep.get("search_flagged") or []), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
