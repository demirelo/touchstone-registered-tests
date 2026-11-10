"""Exploratory analyses on the second test's evaluation records, after the report (external review round 4, 2026-11-05).
None of them is registered; none changes a registered estimate or decision. Gains follow the records' definition,
g = (attacked profit - truthful reference profit) / (S*/N) with N = 10 (checked against the stored gain).

1. Q1 split: the pooled d = g_C* - g_F111 as an attacked-profit term plus a reference-profit term, equal market weights.
2. Welfare mixtures: an episode-level lottery between the selected W0 attack and a profitable attack of the same rule at
   the headline market (same frozen reference), with the largest W0 weight whose mean gain keeps a nonnegative one-sided
   95 percent lower bound on the evaluation seeds. This shows whether the prescribed W1 search missed episode-level mixtures with lower efficiency;
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


def feasible_mixture(gw0, ew0, gp, ep, g0_train: float, gp_train: float, grid: int = 2001) -> dict:
    """The largest W0 weight on the grid at which both empirical checks hold: the evaluation lower bound and the training
    mean gain (W1's registered constraint) are non-negative (external review round 6)."""
    gw0, ew0, gp, ep = (np.asarray(x, dtype=float) for x in (gw0, ew0, gp, ep))
    best = None
    for w in np.linspace(0.0, 1.0, grid):
        g = w * gw0 + (1 - w) * gp
        if g.mean() - Z * g.std(ddof=1) / np.sqrt(len(g)) >= 0 and train_mix(g0_train, gp_train, w) >= 0:
            best = float(w)
    if best is None:
        return {"weight": None}
    g, e = best * gw0 + (1 - best) * gp, best * ew0 + (1 - best) * ep
    return {"weight": best, "estimate": float(g.mean()), "lower": float(g.mean() - Z * g.std(ddof=1) / np.sqrt(len(g))),
            "efficiency": float(e.mean()), "train_mix": train_mix(g0_train, gp_train, best)}


def sensitivity(gw0, ew0, gp, ep, weights) -> list:
    """Mean gain, its nominal one-sided 95 percent lower bound, and mean efficiency of the lottery at each W0 weight."""
    gw0, ew0, gp, ep = (np.asarray(x, dtype=float) for x in (gw0, ew0, gp, ep)); rows = []
    for w in weights:
        g, e = w * gw0 + (1 - w) * gp, w * ew0 + (1 - w) * ep
        rows.append({"weight": float(w), "estimate": float(g.mean()), "lower": float(g.mean() - Z * g.std(ddof=1) / np.sqrt(len(g))),
                     "efficiency": float(e.mean())})
    return rows


SENS_WEIGHTS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)


def weight_label(w: float) -> str:
    """Two decimals in percent: the bound is near zero at the selected weight, and rounding can flip its sign."""
    return f"{100 * w:.2f} percent"


def _ref_train(out, rule: str):
    fn = rule.replace("*", "star")
    return np.asarray(json.loads((Path(out) / "reference" / "headline@rho0.2" / f"{fn}.json").read_text())["per_seed_normalized"], dtype=float)


def _search_rec(out, rid):
    return json.loads((Path(out) / "search" / (safe(rid) + ".json")).read_text())


def _archive_entry(archive: list, knobs: dict) -> dict:
    hits = [a for a in archive if a["knobs"] == knobs]
    if len(hits) != 1:
        raise ValueError(f"{len(hits)} archive entries match the evaluated policy")
    return hits[0]


def train_gain_w0(out, rule: str) -> float:
    """Training mean gain of the selected W0 attack: its archive entry's per-seed normalised profit on the dev-train seeds
    minus the frozen reference's (design 6.2: W1's constraint is this mean >= 0)."""
    s = _search_rec(out, f"headline@rho0.2|{rule}|D2+H3|W0"); e = _archive_entry(s["welfare"]["archive"], s["selected"])
    return float(np.mean(np.asarray(e["per_seed_normalized"], dtype=float) - _ref_train(out, rule)))


def train_gain_profit(out, rule: str, fam: str) -> float:
    """Training mean gain of the evaluated profit attack (attack.best_knobs, as stage_evaluate uses it)."""
    a = _search_rec(out, f"headline@rho0.2|{rule}|{fam}|profit")["attack"]; e = _archive_entry(a["archive"], a["best_knobs"])
    return float(np.mean(np.asarray(e["per_seed_normalized"], dtype=float) - _ref_train(out, rule)))


def train_mix(g0: float, gp: float, w: float) -> float:
    return float(w * g0 + (1 - w) * gp)


def _w0_gain(out, rule: str):
    """W0's per-seed gain against the frozen reference: the W1 record's normalized profit minus its constraint (the gain)
    gives the reference term, which W0 shares (same rule, market, and reference)."""
    ctx = "headline@rho0.2"; w0 = _rec(out, f"{ctx}|{rule}|D2+H3|W0"); w1 = _rec(out, f"{ctx}|{rule}|D2+H3|W1")
    if w1["seeds"] != w0["seeds"]:
        raise ValueError(f"{rule}: the W1 record's seed order differs from W0's")
    ref = np.asarray(w1["normalized"]) - np.asarray(w1["constraint"])
    return w0, w1, np.asarray(w0["normalized"]) - ref


def train_rows(out, rule: str, fams=PROFIT_FAMS) -> list:
    """The training observations behind the lottery's training gains (external review round 6): per dev-train seed, the
    normalised profit of the selected W0 policy and of each evaluated profit attack (archive entries, matched by knobs),
    the frozen reference's, and the reference candidate's name."""
    ctx = "headline@rho0.2"; ref = json.loads((Path(out) / "reference" / ctx / f"{rule.replace('*', 'star')}.json").read_text())
    rn, rname, seeds = ref["per_seed_normalized"], ref["candidates"][ref["choice"]]["name"], ref["provenance"]["seeds_train"]
    comps = []
    s = _search_rec(out, f"{ctx}|{rule}|D2+H3|W0"); comps.append(("W0", f"{ctx}|{rule}|D2+H3|W0", s, _archive_entry(s["welfare"]["archive"], s["selected"])))
    for fam in fams:
        try:
            s = _search_rec(out, f"{ctx}|{rule}|{fam}|profit")
        except FileNotFoundError:
            continue
        comps.append((fam, f"{ctx}|{rule}|{fam}|profit", s, _archive_entry(s["attack"]["archive"], s["attack"]["best_knobs"])))
    rows = []
    for name, rid, s, e in comps:
        if s["provenance"]["seeds_train"] != seeds or len(e["per_seed_normalized"]) != len(seeds):
            raise ValueError(f"{rid}: training seeds differ from the reference's")
        for sd, x, r in zip(seeds, e["per_seed_normalized"], rn):
            rows.append({"rule": rule, "component": name, "search_record": rid, "policy_knobs": json.dumps(e["knobs"], sort_keys=True),
                         "seed": sd, "normalized": float(x), "reference": rname, "reference_normalized": float(r), "gain": float(x) - float(r)})
    return rows


def seed_rows(out, rule: str) -> list:
    """Per-seed component values for the lottery analysis, one row per seed and companion family (CSV export)."""
    ctx = "headline@rho0.2"; w0, _, gw0 = _w0_gain(out, rule); rows = []
    for fam in PROFIT_FAMS:
        r = _rec(out, f"{ctx}|{rule}|{fam}|profit")
        if r is None or r["seeds"] != w0["seeds"]:
            continue
        for s, a, b, c, d in zip(w0["seeds"], gw0, w0["eff"], r["gain"], r["eff_attack"]):
            rows.append({"rule": rule, "companion": fam, "seed": s, "gain_w0": float(a), "eff_w0": float(b), "gain_companion": float(c), "eff_companion": float(d)})
    return rows


def welfare_mixtures(out, rule: str) -> dict:
    ctx = "headline@rho0.2"; w0, w1, gw0 = _w0_gain(out, rule)
    res = {"w0": {"estimate": float(gw0.mean()), "efficiency": float(np.mean(w0["eff"]))},
           "w1": {"estimate": float(np.mean(w1["constraint"])), "efficiency": float(np.mean(w1["eff"]))}, "mixtures": {}}
    for fam in PROFIT_FAMS:
        r = _rec(out, f"{ctx}|{rule}|{fam}|profit")
        if r is None or r["seeds"] != w0["seeds"]:
            continue
        mx = mixture(gw0, w0["eff"], r["gain"], r["eff_attack"])
        mx["weight_label"] = weight_label(mx["weight"]); mx["estimate_label"] = label3(mx["estimate"]); mx["lower_label"] = label3(mx.get("lower"))
        mx["sensitivity"] = sensitivity(gw0, w0["eff"], r["gain"], r["eff_attack"], SENS_WEIGHTS)
        try:
            g0, gp = train_gain_w0(out, rule), train_gain_profit(out, rule, fam)
            mx.update(train_w0=g0, train_companion=gp, train_mix=train_mix(g0, gp, mx["weight"]))
            mx["train_feasible"] = mx["train_mix"] >= 0; mx["train_label"] = label3(mx["train_mix"])
            if not mx["train_feasible"]:
                fm = feasible_mixture(gw0, w0["eff"], r["gain"], r["eff_attack"], g0, gp)
                if fm["weight"] is not None:
                    fm.update(weight_label=weight_label(fm["weight"]), estimate_label=label3(fm["estimate"]), lower_label=label3(fm["lower"]),
                              train_label=label3(fm["train_mix"]), efficiency_label=f"{fm['efficiency']:.4f}", break_even=float(gp / (gp - g0)) if gp != g0 else None)
                mx["train_feasible_mixture"] = fm
        except (FileNotFoundError, ValueError, KeyError):
            mx["train_mix"] = None
        res["mixtures"][fam] = mx
    feasible = {f: v for f, v in res["mixtures"].items() if v["weight"] > 0}
    if feasible:
        f = min(feasible, key=lambda k: feasible[k]["efficiency"]); res["best"] = {"family": f, **feasible[f]}
    return res


def doubled(out, report: dict, markets, fams=("D2+H3", "X7-SC")) -> dict:
    """External review round 9: per market, C* - F111 (Q1) and F000 - F111 (Q4, D2+H3 only) with the frozen search winners
    and with the doubled-search winners (report doubling[...].heldout), both evaluated on the same seeds against the same
    frozen reference; plus the frozen pooled absolute gains. Descriptive; no decision changes."""
    res = {}
    for fam in fams:
        rows, absg = {}, {"C*": [], "F111": []}
        for m in markets:
            fz, db = {}, {}
            for rule in ("C*", "F111", "F000"):
                rid = f"{m}@rho0.2|{rule}|{fam}|profit"; r = _rec(out, rid); h = report.get("doubling", {}).get(rid)
                if r is None or h is None:
                    continue
                if list(h["heldout"]["seeds"]) != list(r["seeds"]):
                    raise ValueError(f"doubled winner of {rid} evaluated on other seeds")
                fz[rule], db[rule] = float(np.mean(r["gain"])), float(np.mean(h["heldout"]["gain"]))
            if "C*" not in fz or "F111" not in fz:
                continue
            row = {"q1_frozen": fz["C*"] - fz["F111"], "q1_doubled": db["C*"] - db["F111"]}
            if fam == "D2+H3" and "F000" in fz:
                row.update(q4_frozen=fz["F000"] - fz["F111"], q4_doubled=db["F000"] - db["F111"])
            rows[m] = row; absg["C*"].append(fz["C*"]); absg["F111"].append(fz["F111"])
        keys = sorted({k for v in rows.values() for k in v})
        res[fam] = {"markets": rows, "pooled": {k: float(np.mean([v[k] for v in rows.values() if k in v])) for k in keys},
                    "absolute": {k: {"mean_gain": float(np.mean(v))} for k, v in absg.items()}}
    return res


def honest(report: dict) -> dict:
    """Design 6.7 honest-replacement profile (report q3.diagnostic), unrounded: per age bin of an honest provider's replacement
    identity, the audited share of its served jobs, its profit per round and its false-failure refunds (both / (S*/N))."""
    d = report["q3"]["diagnostic"]
    res = {r: {"bins": v["bins"], "mean_profit_per_round": float(np.mean([b["profit_per_round"] for b in v["bins"]])),
               "mean_false_refund": float(np.mean([b["false_refund"] for b in v["bins"]]))} for r, v in d.items()}
    res["r3_minus_cstar_profit_per_round"] = res["F111"]["mean_profit_per_round"] - res["C*"]["mean_profit_per_round"]
    return res


def market_level(dbl: dict) -> dict:
    """Fable 5.2 review: the six per-market Q1 differences treated as a sample of markets (t interval, n - 1 degrees of
    freedom, and the count of positive markets), for the frozen and the doubled winners; plus the relative difference of
    the pooled absolute gains, C*/R3 - 1. The registered intervals hold the six markets fixed; this one does not."""
    from scipy import stats
    res = {}
    for fam, v in dbl.items():
        out = {}
        for k in ("frozen", "doubled"):
            x = np.array([row[f"q1_{k}"] for row in v["markets"].values()]); n = len(x)
            h = float(stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n))
            out[k] = {"mean": float(x.mean()), "t95": [float(x.mean()) - h, float(x.mean()) + h], "positive": int((x > 0).sum()), "n": n}
        out["relative"] = v["absolute"]["C*"]["mean_gain"] / v["absolute"]["F111"]["mean_gain"] - 1
        res[fam] = out
    return res


def x7_embedding(out, markets) -> dict:
    """Fable 5.2 review: Q1 cells where the X7-SC search winner is the embedded D2+H3 winner (design 5.2 incumbent) and its
    evaluated gains equal the D2+H3 cell's, so the second Q1 family adds no evidence there."""
    same, differs, n = 0, [], 0
    for m in markets:
        for rule in ("C*", "F111"):
            x, d = _rec(out, f"{m}@rho0.2|{rule}|X7-SC|profit"), _rec(out, f"{m}@rho0.2|{rule}|D2+H3|profit")
            if x is None or d is None:
                continue
            n += 1; src = _search_rec(out, f"{m}@rho0.2|{rule}|X7-SC|profit")["attack"].get("best_source", "")
            if src.startswith("incumbent:embedded") and list(x["gain"]) == list(d["gain"]):
                same += 1
            else:
                differs.append(f"{m}@rho0.2|{rule}")
    return {"embedded_identical": same, "cells": n, "differs": differs}


def envelope_difference(report: dict, markets) -> dict:
    """Fable 5.2 review: C* minus R3 with each rule's training-selected strongest family (report q3.envelope); descriptive."""
    e = report["q3"]["envelope"]; rows = {}
    for m in markets:
        if m in e.get("C*", {}) and m in e.get("F111", {}):
            rows[m] = {"difference": e["C*"][m]["estimate"] - e["F111"][m]["estimate"], "family_cstar": e["C*"][m]["family"], "family_r3": e["F111"][m]["family"]}
    return {"markets": rows, "pooled": float(np.mean([v["difference"] for v in rows.values()]))}


def doubling_flags(report: dict) -> dict:
    d = report["doubling"]
    return {"flagged": sum(1 for v in d.values() if v.get("incomplete")), "checks": len(d)}


def direct_priority(out, markets, fams=("D2+H3", "X7-SC")) -> dict:
    """Follow-up reviews: R3's own priority-phase comparison, F111 - F011 (G = 1 and S = 1), per market and pooled with equal
    weights, from the searched evaluation records (the registered Q2 contrast P|G=1 also averages over pacing)."""
    res = {}
    for fam in fams:
        rows = {}
        for m in markets:
            a, b = _rec(out, f"{m}@rho0.2|F111|{fam}|profit"), _rec(out, f"{m}@rho0.2|F011|{fam}|profit")
            if a is not None and b is not None:
                rows[m] = float(np.mean(a["gain"]) - np.mean(b["gain"]))
        if rows:
            res[fam] = {"markets": rows, "pooled": float(np.mean(list(rows.values())))}
    return res


def nesting(out, report: dict, markets, rules=("F000", "F111", "C*")) -> dict:
    """Follow-up reviews: X7-SC contains D2+H3, so an X7-SC cell's evaluated gain is compared with the better of the frozen
    and the doubled D2+H3 winners on the same seeds; a positive shortfall is an evaluation discrepancy
    that calls for further search checks, not a demonstrated search failure: winners are selected on training seeds
    and need not keep their order on evaluation seeds, and the better D2+H3 winner is picked on the evaluation seeds."""
    cells, fails = {}, []
    for m in markets:
        for r in rules:
            d, x = _rec(out, f"{m}@rho0.2|{r}|D2+H3|profit"), _rec(out, f"{m}@rho0.2|{r}|X7-SC|profit")
            if d is None or x is None:
                continue
            best = float(np.mean(d["gain"])); h = report.get("doubling", {}).get(f"{m}@rho0.2|{r}|D2+H3|profit")
            if h is not None and list(h["heldout"]["seeds"]) == list(x.get("seeds", h["heldout"]["seeds"])):
                best = max(best, float(np.mean(h["heldout"]["gain"])))
            sf = best - float(np.mean(x["gain"])); cells[f"{m}@rho0.2|{r}"] = {"best_d2h3": best, "x7": float(np.mean(x["gain"])), "shortfall": sf}
            if sf > 1e-12:
                fails.append(f"{m}@rho0.2|{r}")
    over = [c for c in fails if cells[c]["shortfall"] >= 0.005]                # the doubling check's threshold (design 6.5)
    return {"cells": cells, "failures": fails, "n": len(cells), "over_threshold": len(over),
            "max_shortfall": max((cells[c]["shortfall"] for c in fails), default=0.0)}


def envelope_interval(env: dict) -> dict:
    from scipy import stats
    x = np.array([v["difference"] for v in env["markets"].values()]); n = len(x)
    h = float(stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n))
    return {"t95": [float(x.mean()) - h, float(x.mean()) + h], "positive": int((x > 0).sum()), "n": n}


def honest_relative(hon: dict) -> float:
    """R3's honest-replacement mean profit per round relative to C*'s, minus one (registered diagnostic; no interval)."""
    return hon["F111"]["mean_profit_per_round"] / hon["C*"]["mean_profit_per_round"] - 1


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


def _f(x, d: int = 3):
    return "n/a" if x is None else (f"\\ensuremath{{{x:.{d}f}}}" if x < 0 else f"{x:.{d}f}")


def label3(x) -> str:
    """A positive or negative value at three significant digits as plain text (for sites in the paper's prose)."""
    if x is None:
        return "n/a"
    if x == 0:
        return "0"
    d = max(0, 2 - int(np.floor(np.log10(abs(x))))); return f"{x:.{d}f}"


def _s3(x) -> str:
    """Three significant digits in fixed notation, so a small gain or bound never prints as 0.000."""
    if x is None:
        return "n/a"
    if x == 0:
        return "0"
    d = max(0, 2 - int(np.floor(np.log10(abs(x))))); t = f"{x:.{d}f}"
    return f"\\ensuremath{{{t}}}" if x < 0 else t


def tables(res: dict) -> dict:
    t = {}
    rows = [f"{fam} & {_f(v['pooled']['estimate'])} & {_f(v['pooled']['attacked'])} & {_f(v['pooled']['reference'])} \\\\"
            for fam, v in res["q1_split"].items()]
    t["q1_split"] = ("\\begin{tabular}{@{}lrrr@{}}\\toprule\nFamily & $d$ & Attacked term & Reference term \\\\\\midrule\n"
                     + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = []
    for r, v in res["welfare"].items():
        mixes = v.get("mixtures", {})
        if any(m["weight"] >= 1.0 for m in mixes.values()):
            mx = next(m for m in mixes.values() if m["weight"] >= 1.0)
            rows.append(f"{r} & {_f(v['w1']['efficiency'])} & {_f(v['w0']['efficiency'])} & none (W0 estimated gain positive) & 1 & {_s3(mx['estimate'])} & "
                        f"{_s3(mx.get('lower'))} & {_s3(mx.get('train_mix'))} & {_f(mx['efficiency'], 4)} \\\\"); continue
        for fam in ("H4", "D2+H3"):
            mx = mixes.get(fam)
            if mx and mx["weight"] > 0:
                rows.append(f"{r} & {_f(v['w1']['efficiency'])} & {_f(v['w0']['efficiency'])} & {fam} & {mx['weight']:.4f} & {_s3(mx['estimate'])} & "
                            f"{_s3(mx.get('lower'))} & {_s3(mx.get('train_mix'))} & {_f(mx['efficiency'], 4)} \\\\")
                fm = mx.get("train_feasible_mixture") or {}
                if fm.get("weight"):
                    rows.append(f"{r} & {_f(v['w1']['efficiency'])} & {_f(v['w0']['efficiency'])} & {fam}, training-feasible & {fm['weight']:.4f} & "
                                f"{_s3(fm['estimate'])} & {_s3(fm['lower'])} & {_s3(fm['train_mix'])} & {_f(fm['efficiency'], 4)} \\\\")
    t["welfare_mix"] = ("\\begin{tabular}{@{}lrrlrrrrr@{}}\\toprule\nRule & W1 eff. & W0 eff. & Mixed with & W0 weight & Est.\\ gain & Unadj.\\ lower & Train gain & Mixed eff. \\\\\\midrule\n"
                        + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = []
    for r in ("F111", "C*"):
        for fam in ("H4", "D2+H3"):
            mx = res["welfare"].get(r, {}).get("mixtures", {}).get(fam)
            if mx and "sensitivity" in mx:
                rows.append(f"{r} & {fam} & " + " & ".join(f"{_s3(x['estimate'])} / {_f(x['efficiency'])}" for x in mx["sensitivity"]) + " \\\\")
    t["welfare_sens"] = ("\\begin{tabular}{@{}ll" + "r" * len(SENS_WEIGHTS) + "@{}}\\toprule\nRule & Mixed with & "
                         + " & ".join(f"$w={w:.1f}$" for w in SENS_WEIGHTS) + " \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = [f"{m} & {_f(v['estimate'])} & {_f(v['attacked'])} & {_f(v['reference'])} & {_f(v['audit_spend'])} & {_f(v['served_share'])} \\\\"
            for m, v in res["q4_diag"].items()]
    t["q4_diag"] = ("\\begin{tabular}{@{}lrrrrr@{}}\\toprule\nMarket & B3$-$R3 gain & Attacked term & Reference term & R3 audit spend & R3 service fraction \\\\\\midrule\n"
                    + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = [f"{k} & {_f(v['estimate_report'], 4)} & {_f(v['estimate_registered_cfg'], 4)} & {v['category_registered_cfg']} \\\\" for k, v in res["stability"]["q1"].items()]
    t["stability"] = ("\\begin{tabular}{@{}lrrl@{}}\\toprule\nQ1 test & $d$, report & $d$, registered configs & Category, registered configs \\\\\\midrule\n"
                      + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    if "doubled" in res:
        sg = lambda x: f"${x:.3f}$".replace("$-", "$-") if x is not None else "--"
        rows = []
        for m in res["doubled"]["D2+H3"]["markets"]:
            a, b = res["doubled"]["D2+H3"]["markets"][m], res["doubled"].get("X7-SC", {}).get("markets", {}).get(m, {})
            rows.append(f"{m} & {sg(a['q1_frozen'])} & {sg(a['q1_doubled'])} & {sg(b.get('q1_frozen'))} & {sg(b.get('q1_doubled'))} & "
                        f"{sg(a.get('q4_frozen'))} & {sg(a.get('q4_doubled'))} \\\\")
        t["doubled"] = ("\\begin{tabular}{@{}lrrrrrr@{}}\\toprule\n & \\multicolumn{2}{c}{C*$-$R3, D2+H3} & \\multicolumn{2}{c}{C*$-$R3, X7-SC} & \\multicolumn{2}{c}{B3$-$R3, D2+H3} \\\\\n"
                        "Market & Frozen & Doubled & Frozen & Doubled & Frozen & Doubled \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    if "honest" in res:
        rows = []
        for r in ("F000", "F111", "C*"):
            v = res["honest"][r]; b = v["bins"]
            rows.append(f"{ {"F000": "B3 (F000)", "F111": "R3 (F111)"}.get(r, r)} & " + " & ".join(f"{x["audited_share"]:.3f}" for x in b[:3]) + f" & {v['mean_profit_per_round'] * 1e4:.2f} & {v['mean_false_refund'] * 1e5:.2f} \\\\")
        t["honest"] = ("\\begin{tabular}{@{}lrrrrr@{}}\\toprule\n & \\multicolumn{3}{c}{Audited share, by age} & Profit per round & False refunds \\\\\n"
                       "Rule & 0--10 & 10--20 & 20--30 & ($\\times 10^{-4}$) & ($\\times 10^{-5}$) \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
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
           "q4_diag": q4_diagnostics(out), "stability": stability(report, stab),
           "doubled": doubled(out, report, FRESH), "honest": honest(report)}
    res["market_level"] = market_level(res["doubled"]); res["x7_embedding"] = x7_embedding(out, FRESH); res["x7_embedding_all"] = x7_embedding(out, FRESH + ("headline",))
    res["envelope"] = envelope_difference(report, FRESH); res["doubling_flags"] = doubling_flags(report)
    res["direct_priority"] = direct_priority(out, FRESH); res["nesting"] = nesting(out, report, FRESH + ("headline",))
    res["envelope_interval"] = envelope_interval(res["envelope"]); res["honest_cost"] = {"relative": honest_relative(res["honest"])}
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    import csv
    seeds = [row for r in ("F000", "F111", "C*") for row in seed_rows(out, r)]
    with open(Path(a.out).with_name("lottery_seeds.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(seeds[0])); w.writeheader(); w.writerows(seeds)
    train = [row for r in ("F000", "F111", "C*") for row in train_rows(out, r)]
    with open(Path(a.out).with_name("lottery_train.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(train[0])); w.writeheader(); w.writerows(train)
    d = Path(a.tables); d.mkdir(parents=True, exist_ok=True)
    for k, v in tables(res).items():
        (d / f"posthoc_{k}.tex").write_text(v.replace("C*", "C$^*$"))
    print(json.dumps({r: v.get("best") for r, v in res["welfare"].items()}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
