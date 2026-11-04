"""Evaluation-2 result tables for the paper, generated whole from report.json (paper draft 9 outline, "Rules for the
text"). Each row's label is the key that fetched its values, so a label cannot sit beside another row's numbers. A
string in the report (a status such as "not decided" or "unanswered: missing cell") is printed across the row. Captions
live in main.tex; these files hold only the tabular. --write writes tables/<name>.tex; --check compares them."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from numbers_v2 import _fmt, _fmt_p  # noqa: E402

FRESH = tuple(f"fresh{i}" for i in range(6))
FAMS = ("D2+H3", "X7-SC")
CORE = ("F000", "F111", "C*")
SIDE = ("gross_eff_diff", "net_eff_diff", "ref_profit_diff", "audit_spend_diff", "false_refund_focal_diff", "false_refund_others_diff",
        "served_share_diff")


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
    rows = []
    for f in FAMS:
        t = r["q1"]["tests"][f"C*-F111|{f}"]
        rows.append((f, [num(t.get("estimate")), iv(t.get("interval")), esc(t.get("category")), _fmt_p(t.get("p")),
                         esc(t.get("efficiency") or "n/a"), esc(t.get("better") or "none")]))
    return tabular("lrllrll", ["Family", "$d$", "Interval", "Category", "$p$", "Efficiency", "Better"], rows)


def q1_side(r: dict) -> str:
    rows = []
    for f in FAMS:
        s = r["q1"]["tests"][f"C*-F111|{f}"].get("side")
        rows.append((f, "not available") if not s else (f, [num(s[k]) for k in SIDE]))
    return tabular("l" + "r" * len(SIDE), ["Family", "Gross eff.", "Net eff.", "Ref.\\ profit", "Audit spend", "Refunds (focal)",
                                           "Refunds (others)", "Served share"], rows)


def q4(r: dict) -> str:
    q = r["q4"]; rows = []
    for m in FRESH:
        x = q["markets"][m]
        if isinstance(x, str):
            rows.append((m, x)); continue
        dec = "pass" if m in q.get("passing", []) else "fail" if m in q.get("failing", []) else "not decided"
        rows.append((m, [num(x["gain_diff"]), num(x["gain_diff_lower"]), num(x["eff"]), num(x["eff_lower"]), _fmt_p(x["p_gain"]),
                         _fmt_p(x["p_eff"]), dec + (" (search flagged)" if x.get("search") else "")]))
    return tabular("lrrrrrrl", ["Market", "F000$-$F111", "Lower", "F111 eff.", "Lower", "$p'_{\\mathrm{gain}}$", "$p'_{\\mathrm{eff}}$",
                                "Holm"], rows)


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


PAIR_LABELS = {"Q2-d": ("fixed", "searched"), "Q3-d": ("G_min", "G_tot")}     # score_v2.py's pair order


def _pval(pid: str, v) -> str:
    if isinstance(v, (list, tuple)):
        labels = PAIR_LABELS.get(pid, tuple(f"value {i + 1}" for i in range(len(v))))
        return ", ".join(f"{esc(lab)} {num(float(x)) if x is not None else 'n/a'}" for lab, x in zip(labels, v))
    return esc(v) if isinstance(v, str) else num(v)


def predictions(sc: dict) -> str:
    """The prediction scoring table (score_v2.py): overall status, then each scored cell with its value and status; paired
    values carry their labels (they are two statistics, not an interval)."""
    rows = []
    for pid in sorted(sc):
        v = sc[pid]
        cells = "; ".join(f"{esc(c['cell'])} {_pval(pid, c['value'])} {esc(c['status'])}" for c in v.get("cells", [])) or "none scored"
        rows.append((pid, [esc(v["status"]), cells]))
    return tabular("llp{0.62\\linewidth}", ["Prediction", "Status", "Scored cells"], rows)


def all_tables(r: dict) -> dict:
    return {"q1": q1(r), "q1_side": q1_side(r), "q4": q4(r), "q2_d2h3": q2(r, "D2+H3"), "q2_x7sc": q2(r, "X7-SC"), "envelope": envelope(r),
            "welfare": welfare(r), "coalitions": coalitions(r), "repair": repair(r)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True); ap.add_argument("--dir", required=True)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    ap.add_argument("--scoring", help="score_v2.py output; adds tables/predictions.tex")
    a = ap.parse_args(argv); tabs = all_tables(json.loads(Path(a.report).read_text())); d = Path(a.dir)
    if a.scoring:
        tabs["predictions"] = predictions(json.loads(Path(a.scoring).read_text()))
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
