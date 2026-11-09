"""Evaluation-2 result tables for the paper, generated whole from report.json (paper draft 9 outline, "Rules for the
text"). Each row's label is the key that fetched its values, so a label cannot sit beside another row's numbers. A
string in the report (a status such as "not decided" or "unanswered: missing cell") is printed across the row. Captions
live in main.tex; these files hold only the tabular. --write writes tables/<name>.tex; --check compares them."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numbers_v2 import _fmt, _fmt_p  # noqa: E402

FRESH = tuple(f"fresh{i}" for i in range(6))
FAMS = ("D2+H3", "X7-SC")
CORE = ("F000", "F111", "C*")
SIDE = ("gross_eff_diff", "net_eff_diff", "ref_profit_diff", "audit_spend_diff", "false_refund_focal_diff", "false_refund_others_diff",
        "served_share_diff")


def holm_adjusted(p: list) -> list:
    """Holm step-down adjusted p-values: sorted ascending, adj_(i) = max_{j<=i} min(1, (m - j + 1) p_(j))."""
    m = len(p); order = sorted(range(m), key=lambda i: p[i]); out = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * float(p[i]))); out[i] = run
    return out


def esc(s) -> str:
    return _fmt(str(s))


def num(v) -> str:
    return _fmt(v) if not isinstance(v, str) else esc(v)


def iv(x) -> str:
    return "n/a" if not x or None in x else f"[{num(float(x[0]))}, {num(float(x[1]))}]"


def tabular(cols: str, header: list[str], rows: list[tuple[str, object]]) -> str:
    """rows: (label, list of cells) or (label, status string); a status spans the remaining columns."""
    n = len(header); out = [f"\\begin{{tabular}}{{@{{}}{cols}@{{}}}}\\toprule", " & ".join(header) + " \\\\\\midrule"]
    for label, cells in rows:
        if isinstance(cells, str):
            out.append(f"{esc(label)} & \\multicolumn{{{n - 1}}}{{l}}{{{esc(cells)}}} \\\\")
        else:
            out.append(" & ".join([esc(label)] + list(cells)) + " \\\\")
    out.append("\\bottomrule\\end{tabular}")
    return "\n".join(out) + "\n"


def q1(r: dict) -> str:
    """The stored "p" is the calibrated two-sided p-value that enters Holm over the two fixed slots (sim.decisions_v2.q1_family);
    the Holm-adjusted value is computed beside it."""
    rows = []; tests = [r["q1"]["tests"][f"C*-F111|{f}"] for f in FAMS]
    ps = [t.get("p") for t in tests]; adj = holm_adjusted([1.0 if p is None else p for p in ps]) if any(p is not None for p in ps) else [None] * len(ps)
    for f, t, a in zip(FAMS, tests, adj):
        rows.append((f, [num(t.get("estimate")), iv(t.get("interval")), esc(t.get("category")), _fmt_p(t.get("p")),
                         _fmt_p(a if t.get("p") is not None else None), esc(t.get("efficiency") or "n/a"), esc(t.get("better") or "none")]))
    return tabular("lrllrrll", ["Family", "$d$", "Interval", "Category", "$p'$ to Holm", "Holm-adj.", "Efficiency", "Better"], rows)


def q1_side(r: dict) -> str:
    rows = []
    for f in FAMS:
        s = r["q1"]["tests"][f"C*-F111|{f}"].get("side")
        rows.append((f, "not available") if not s else (f, [num(s[k]) for k in SIDE]))
    return tabular("l" + "r" * len(SIDE), ["Family", "Gross eff.", "Net eff.", "Ref.\\ profit", "Audit spend", "False-fail refunds (focal)",
                                           "False-fail refunds (others)", "Service fraction"], rows)


def q4(r: dict) -> str:
    """The stored p_gain and p_eff are the raw one-sided bootstrap p-values; q4.p holds the calibrated market maxima that
    enter Holm over six slots (sim.decisions_v2.q4_markets). Printed: raw values, the market maximum, and its Holm-adjusted value."""
    q = r["q4"]; rows = []; adj = holm_adjusted(q["p"]) if q.get("p") else [None] * len(FRESH)
    for i, m in enumerate(FRESH):
        x = q["markets"][m]
        if isinstance(x, str):
            rows.append((m, x)); continue
        dec = "pass" if m in q.get("passing", []) else "fail" if m in q.get("failing", []) else "not decided"
        rows.append((m, [num(x["gain_diff"]), num(x["gain_diff_lower"]), num(x["eff"]), num(x["eff_lower"]), _fmt_p(x["p_gain"]),
                         _fmt_p(x["p_eff"]), _fmt_p(q["p"][i] if q.get("p") else None), _fmt_p(adj[i]),
                         dec + (" (search flagged)" if x.get("search") else "")]))
    return tabular("lrrrrrrrrl", ["Market", "F000$-$F111", "Lower", "F111 eff.", "Lower", "Raw $p_{\\mathrm{gain}}$", "Raw $p_{\\mathrm{eff}}$",
                                  "Market $p'$", "Holm-adj.", "Decision"], rows)


def q2(r: dict, fam: str) -> str:
    q = r["q2"]; s = q["searched"][fam]
    if isinstance(s, str):
        return tabular("ll", ["Contrast", "Status"], [("all", s)])
    rows = []
    for c in s:
        def cell(kind):
            v = q[kind][fam]
            return "n/a" if isinstance(v, str) or c not in v else num(v[c]["estimate"])
        rows.append((c, [num(s[c]["estimate"]), iv(s[c]["interval"]), cell("fixed"), cell("fixed_attack_term"), cell("fixed_reference_term"),
                         cell("searched_eff"), cell("searched_net_eff")]))
    return tabular("lrlrrrrr", ["Contrast", "Searched", "Interval", "Fixed", "Attack term", "Ref.\\ term", "Gross eff.", "Net eff."], rows)


def envelope(r: dict) -> str:
    rows = []
    for rule in CORE:
        for m in FRESH + ("headline",):
            x = r["q3"]["envelope"][rule][m]
            rows.append((f"{rule} {m}", x if isinstance(x, str) else [esc(x["family"]), num(x["estimate"]), iv(x["interval"])]))
    return tabular("llrl", ["Rule, market", "Family", "Gain", "Interval"], rows)


def welfare(r: dict) -> str:
    rows = []
    for rule in CORE:
        for obj in ("W0", "W1"):
            x = r["q3"]["welfare_selected"][rule][obj]
            if x.get("family") is None:
                rows.append((f"{rule} {obj}", x.get("status") or "n/a")); continue
            res, oth = x["result"], x["other_result"]
            if isinstance(res, str):
                rows.append((f"{rule} {obj}", f"{x['family']}: {res}")); continue
            other = esc(oth) if isinstance(oth, str) else num(oth["efficiency"])
            rows.append((f"{rule} {obj}", [esc(x["family"]), num(res["efficiency"]), iv(res["interval"]), num(res["attacker_gain"]),
                                           esc(res.get("w1_class") or "n/a"), esc(x["other_family"]), other]))
    return tabular("llrlrlll", ["Rule, objective", "Selected", "Gross eff.", "Interval", "Attacker gain", "W1 class", "Other", "Other eff."], rows)


def coalitions(r: dict) -> str:
    rows = []
    for rule in CORE:
        for g, x in r["q3"]["coalition"][rule].items():
            if isinstance(x, str):
                rows.append((f"{rule} {g}", x)); continue
            st = x.get("search") or x["G_min"].get("status") or ""
            rows.append((f"{rule} {g}", [num(x["G_tot"]["estimate"]), num(x["G_min"]["estimate"]), iv(x["G_min"]["bounds"]), esc(st or "answered")]))
    return tabular("lrrll", ["Rule, group", "$G_{\\mathrm{tot}}$", "$G_{\\min}$", "$G_{\\min}$ bounds", "Status"], rows)


def repair(r: dict) -> str:
    rows = []
    for rule, fams in r["secondary"]["repair_rho1"].items():
        for f, x in fams.items():
            rows.append((f"{rule} {f}", [num(x["estimate"]), iv(x["interval"])]))
    return tabular("lrl", ["Rule, family ($\\rho = 1$)", "Gain", "Interval"], rows or [("all", "no records")])


PAIR_LABELS = {"Q2-d": ("fixed", "searched"), "Q3-d": ("G_min", "G_tot"), "Q3-e": ("F111", "C*"), "Q3-f": ("F000 efficiency", "F111 efficiency"), "Q3-g": ("R3", "R4"),
               "Q4-b": ("p'_gain", "p'_eff")}     # score_v2.py's pair order


def _p4(x) -> str:
    """Paired values at five decimals, so that close pairs stay distinguishable (Q3-e differs in the sixth digit)."""
    if x is None:
        return "n/a"
    t = f"{float(x):.5f}"
    return f"\\ensuremath{{{t}}}" if t.startswith("-") else t


def _pval(pid: str, v) -> str:
    if isinstance(v, (list, tuple)):
        labels = PAIR_LABELS.get(pid, tuple(f"value {i + 1}" for i in range(len(v))))
        return ", ".join(f"{esc(lab)} {_p4(x)}" for lab, x in zip(labels, v))
    if isinstance(v, str):
        return esc(v)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        t = f"{float(v):.4f}"                                      # four decimals: a value near zero keeps its sign
        return f"\\ensuremath{{{t}}}" if t.startswith("-") else t
    return num(v)


def statements(md: str) -> dict:
    """Prediction id -> 'statistic (scope): fulfilled if', from the registered scoring table of predictions-v2.md."""
    out = {}
    for line in md.splitlines():
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        if len(cells) == 4 and re.fullmatch(r"Q\d-[a-z](-alt)?", cells[0]):
            out[cells[0]] = f"{cells[1]} ({cells[2]}): {cells[3]}".replace("\\|", "|")
    alt = re.search(r"\*\*Q1-a,[^\n]*\n\s*Alternative: ([^.]*)\.", md)          # the alternative is registered in the prose list
    if alt and "Q1-a" in out:
        out["Q1-a-alt"] = f"Q1 category, D2+H3 (pooled fresh), alternative to Q1-a: {alt.group(1)}"
    return out


def _mark(pid: str, elig: dict | None) -> str:
    """Dagger: not assessed under both stricter eligibility readings; double dagger: only under the descriptive one."""
    s = ((elig or {}).get("targets", {}).get(pid) or {}).get("status")
    if not s or s["numerical"] == "not assessed":
        return ""
    return "$^{\\dagger}$" if s["q3"] == "not assessed" else "$^{\\ddagger}$" if s["descriptive"] == "not assessed" else ""


READINGS = (("numerical", "Numerical (as scored)"), ("q3", "Flagged inputs, Q3"), ("descriptive", "Flagged inputs, all non-exempt cells"))


def eligibility(elig: dict) -> str:
    """The prediction tally under the scorer's numerical reading and the two stricter eligibility readings (score_v2.py),
    with the predictions each stricter reading leaves not assessed."""
    rows = []
    for key, label in READINGS:
        t = elig["tally"][key]
        ch = [pid for pid, v in sorted(elig["targets"].items()) if v["status"][key] == "not assessed" != v["status"]["numerical"]]
        rows.append((label, [str(t["fulfilled"]), str(t["failed"]), str(t["not assessed"]), ", ".join(ch) or "none"]))
    for key, label in READINGS[1:]:                       # the same filters on the listed inputs only, without tracing
        t = elig.get("tally_direct_inputs", {}).get(key)
        if t:
            rows.append((label.replace("Flagged inputs", "Flagged direct inputs only"),
                         [str(t["fulfilled"]), str(t["failed"]), str(t["not assessed"]), "--"]))
    return tabular("lrrrl", ["Reading", "Fulfilled", "Failed", "Not assessed", "Not assessed under this reading"], rows)


def predictions(sc: dict, st: dict | None = None, ids: tuple | None = None, elig: dict | None = None) -> str:
    """The prediction scoring table (score_v2.py): the registered statement, the overall status, then each scored cell with
    its value and status; paired values carry their labels (they are two statistics, not an interval). With an eligibility
    map, a status a stricter reading changes carries a mark (_mark)."""
    rows = []
    for pid in sorted(sc):
        if ids and not pid.startswith(tuple(f"{q}-" for q in ids)):
            continue
        v = sc[pid]
        cells = "; ".join(f"{esc(c['cell'])} {_pval(pid, c['value'])} {esc(c['status'])}" for c in v.get("cells", [])) or "none scored"
        rows.append((pid, [esc((st or {}).get(pid, "")), esc(v["status"]) + _mark(pid, elig), cells]))
    return tabular("lp{0.36\\linewidth}lp{0.34\\linewidth}", ["Prediction", "Registered statement", "Status", "Scored cells"], rows)


def all_tables(r: dict) -> dict:
    return {"q1": q1(r), "q1_side": q1_side(r), "q4": q4(r), "q2_d2h3": q2(r, "D2+H3"), "q2_x7sc": q2(r, "X7-SC"), "envelope": envelope(r),
            "welfare": welfare(r), "coalitions": coalitions(r), "repair": repair(r)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True); ap.add_argument("--dir", required=True)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    ap.add_argument("--scoring", help="score_v2.py output; adds tables/predictions.tex")
    ap.add_argument("--eligibility", help="score_v2.py eligibility map; marks the prediction tables, adds tables/pred_eligibility.tex")
    a = ap.parse_args(argv); tabs = all_tables(json.loads(Path(a.report).read_text())); d = Path(a.dir)
    ap_md = Path(__file__).resolve().parent.parent / "predictions-v2.md"
    if a.scoring:
        sc, st = json.loads(Path(a.scoring).read_text()), (statements(ap_md.read_text()) if ap_md.exists() else None)
        el = json.loads(Path(a.eligibility).read_text()) if a.eligibility else None
        tabs["predictions"] = predictions(sc, st, ids=("Q1", "Q2"), elig=el)          # two tables: one does not fit a page
        tabs["predictions_b"] = predictions(sc, st, ids=("Q3", "Q4"), elig=el)
        if el:
            tabs["pred_eligibility"] = eligibility(el)
    if a.write:
        d.mkdir(parents=True, exist_ok=True)
        for k, v in tabs.items():
            (d / f"{k}.tex").write_text(v)
        return 0
    bad = [k for k, v in tabs.items() if not (d / f"{k}.tex").exists() or (d / f"{k}.tex").read_text() != v]
    print("\n".join(f"tables/{k}.tex: stale or missing" for k in bad) or "ok")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
