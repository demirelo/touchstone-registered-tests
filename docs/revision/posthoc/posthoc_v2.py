"""Exploratory analyses on the second test's evaluation records, after the report (external review round 4, 2026-11-05).
None of them is registered; none changes a registered estimate or decision. Gains follow the records' definition,
g = (attacked profit - truthful reference profit) / (S*/N) with N = 10 (checked against the stored gain).

1. Q1 split: the pooled d = g_C* - g_F111 as an attacked-profit term plus a reference-profit term, equal market weights.
2. Welfare mixtures: an episode-level lottery between the selected W0 attack and a profitable attack of the same rule at
   the headline market (same frozen reference), with the largest W0 weight whose mean gain keeps a nonnegative one-sided
   95 percent lower bound on the evaluation seeds. This checks whether the W1 policy class is closed under randomisation;
   the weight is chosen on the evaluation seeds, so it is not an out-of-sample estimate.
3. Q4 diagnostics per fresh market: the B3 - R3 gain difference split into its two terms, and R3's audit spending and
   served share under the selected attack.
4. Stability: the registered-configuration re-evaluation (deviation/stability-result.json) beside the report.

Usage: posthoc_v2.py --records EVAL/all --report report.json --stability stability-result.json --out posthoc.json --tables DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

FRESH = tuple(f"fresh{i}" for i in range(6))
N = 10
Z = 1.645
PROFIT_FAMS = ("D2+H3", "X7-SC", "X5-AG/v2", "H4", "D2")


def safe(rid: str) -> str:
    return rid.replace("|", "__").replace("/", "~").replace("*", "star")      # revision_v2._safe


def _rec(out, rid):
    p = Path(out) / "evaluate" / (safe(rid) + ".json")
    return json.loads(p.read_text()) if p.exists() else None


def _terms(r):
    s = np.asarray(r["sstar"], dtype=float) / N
    return np.asarray(r["profit_attack"], dtype=float) / s, np.asarray(r["profit_ref"], dtype=float) / s


def split(out, markets, a: str, b: str, fam: str, n: int = N) -> dict:
    """d = g_a - g_b per market and pooled with equal market weights, as attacked term + reference term."""
    rows = {}
    for m in markets:
        ra, rb = _rec(out, f"{m}@rho0.2|{a}|{fam}|profit"), _rec(out, f"{m}@rho0.2|{b}|{fam}|profit")
        if ra is None or rb is None:
            continue
        (pa, ta), (pb, tb) = _terms(ra), _terms(rb)
        att, ref = pa - pb, -(ta - tb)
        rows[m] = {"estimate": float(np.mean(att + ref)), "attacked": float(np.mean(att)), "reference": float(np.mean(ref))}
    pooled = {k: float(np.mean([v[k] for v in rows.values()])) for k in ("estimate", "attacked", "reference")} if rows else {}
    return {"markets": rows, "pooled": pooled}


def mixture(gw0, ew0, gp, ep, grid: int = 2001) -> dict:
    """The largest W0 weight w with mean(w gw0 + (1-w) gp) - Z se >= 0, and the mixture's mean gain and efficiency."""
    gw0, ew0, gp, ep = (np.asarray(x, dtype=float) for x in (gw0, ew0, gp, ep))
    best = 0.0
    for w in np.linspace(0.0, 1.0, grid):
        g = w * gw0 + (1 - w) * gp
        if g.mean() - Z * g.std(ddof=1) / np.sqrt(len(g)) >= 0:
            best = float(w)
    if best == 0.0 and not ((gp.mean() - Z * gp.std(ddof=1) / np.sqrt(len(gp))) >= 0):
        return {"weight": 0.0, "estimate": float(gp.mean()), "efficiency": float(ep.mean())}
    g, e = best * gw0 + (1 - best) * gp, best * ew0 + (1 - best) * ep
    return {"weight": best, "estimate": float(g.mean()), "lower": float(g.mean() - Z * g.std(ddof=1) / np.sqrt(len(g))),
            "efficiency": float(e.mean())}


def welfare_mixtures(out, rule: str) -> dict:
    ctx = "headline@rho0.2"; w0 = _rec(out, f"{ctx}|{rule}|D2+H3|W0"); w1 = _rec(out, f"{ctx}|{rule}|D2+H3|W1")
    ref = np.asarray(w1["normalized"]) - np.asarray(w1["constraint"]); gw0 = np.asarray(w0["normalized"]) - ref
    res = {"w0": {"estimate": float(gw0.mean()), "efficiency": float(np.mean(w0["eff"]))},
           "w1": {"estimate": float(np.mean(w1["constraint"])), "efficiency": float(np.mean(w1["eff"]))}, "mixtures": {}}
    for fam in PROFIT_FAMS:
        r = _rec(out, f"{ctx}|{rule}|{fam}|profit")
        if r is None or r["seeds"] != w0["seeds"]:
            continue
        mx = mixture(gw0, w0["eff"], r["gain"], r["eff_attack"])
        mx["weight_label"] = f"{round(100 * mx['weight'])} percent"
        res["mixtures"][fam] = mx
    feasible = {f: v for f, v in res["mixtures"].items() if v["weight"] > 0}
    if feasible:
        f = min(feasible, key=lambda k: feasible[k]["efficiency"]); res["best"] = {"family": f, **feasible[f]}
    return res


def q4_diagnostics(out) -> dict:
    res = {}
    for m in FRESH:
        sp = split(out, [m], "F000", "F111", "D2+H3")["markets"].get(m)
        r = _rec(out, f"{m}@rho0.2|F111|D2+H3|profit")
        if sp is None or r is None:
            continue
        res[m] = {**sp, "audit_spend": float(np.mean(r["audit_spend_attack"])), "served_share": float(np.mean(r["served_share_attack"])),
                  "efficiency": float(np.mean(r["eff_attack"]))}
    return res


def stability(report: dict, stab: dict) -> dict:
    q1 = {k: {"estimate_report": report["q1"]["tests"][k]["estimate"], "estimate_registered_cfg": v["estimate"],
              "category_report": report["q1"]["tests"][k]["category"], "category_registered_cfg": v["category"]}
          for k, v in stab["q1_new"].items()}
    shifts = [abs(c["mean_new"] - c["mean_old"]) for c in stab["cells"].values()]
    return {"q1": q1, "q4_k_report": report["q4"]["k"], "q4_k_registered_cfg": stab["q4_new"]["k"],
            "cells": len(shifts), "max_mean_shift": float(max(shifts)), "decisions_unchanged": bool(stab["decisions_unchanged"])}


def _f(x):
    return "n/a" if x is None else (f"\\ensuremath{{{x:.3f}}}" if x < 0 else f"{x:.3f}")


def tables(res: dict) -> dict:
    t = {}
    rows = [f"{fam} & {_f(v['pooled']['estimate'])} & {_f(v['pooled']['attacked'])} & {_f(v['pooled']['reference'])} \\\\"
            for fam, v in res["q1_split"].items()]
    t["q1_split"] = ("\\begin{tabular}{@{}lrrr@{}}\\toprule\nFamily & $d$ & Attacked term & Reference term \\\\\\midrule\n"
                     + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = []
    for r, v in res["welfare"].items():
        b = v.get("best")
        rows.append(f"{r} & {_f(v['w1']['efficiency'])} & {_f(v['w0']['efficiency'])} & "
                    + (f"{b['family']} & {b['weight_label']} & {_f(b['estimate'])} & {_f(b['efficiency'])}" if b else "none & & &")
                    + " \\\\")
    t["welfare_mix"] = ("\\begin{tabular}{@{}lrrlrrr@{}}\\toprule\nRule & W1 eff. & W0 eff. & Mixed with & W0 weight & Mixed gain & Mixed eff. \\\\\\midrule\n"
                        + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = [f"{m} & {_f(v['estimate'])} & {_f(v['attacked'])} & {_f(v['reference'])} & {_f(v['audit_spend'])} & {_f(v['served_share'])} \\\\"
            for m, v in res["q4_diag"].items()]
    t["q4_diag"] = ("\\begin{tabular}{@{}lrrrrr@{}}\\toprule\nMarket & B3$-$R3 gain & Attacked term & Reference term & R3 audit spend & R3 served share \\\\\\midrule\n"
                    + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = [f"{k} & {_f(v['estimate_report'])} & {_f(v['estimate_registered_cfg'])} & {v['category_registered_cfg']} \\\\" for k, v in res["stability"]["q1"].items()]
    t["stability"] = ("\\begin{tabular}{@{}lrrl@{}}\\toprule\nQ1 test & $d$, report & $d$, registered configs & Category, registered configs \\\\\\midrule\n"
                      + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for k in ("--records", "--report", "--stability", "--out", "--tables"):
        ap.add_argument(k, required=True)
    a = ap.parse_args(argv)
    out = Path(a.records); report = json.loads(Path(a.report).read_text()); stab = json.loads(Path(a.stability).read_text())
    res = {"label": "exploratory, after the report; not registered",
           "q1_split": {f: split(out, FRESH, "C*", "F111", f) for f in ("D2+H3", "X7-SC")},
           "welfare": {r: welfare_mixtures(out, r) for r in ("F000", "F111", "C*")},
           "q4_diag": q4_diagnostics(out), "stability": stability(report, stab)}
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    d = Path(a.tables); d.mkdir(parents=True, exist_ok=True)
    for k, v in tables(res).items():
        (d / f"posthoc_{k}.tex").write_text(v.replace("C*", "C$^*$"))
    print(json.dumps({r: v.get("best") for r, v in res["welfare"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
