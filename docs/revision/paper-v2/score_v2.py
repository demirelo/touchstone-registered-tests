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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--report", required=True); ap.add_argument("--cells", required=True)
    ap.add_argument("--write", required=True); a = ap.parse_args(argv)
    sc = score(json.loads(Path(a.report).read_text()), json.loads(Path(a.cells).read_text()))
    Path(a.write).write_text(json.dumps(sc, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
