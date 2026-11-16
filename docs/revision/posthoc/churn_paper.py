"""Draft 10 churn float data (outline-draft10.md, sections 4 and 5): the C* - R3 and B3 - R3 curves against the churn
rate (figure) and the audit allocation per rate (table), from churn.json (p = 0, 0.01, 0.05) and churn_mid.json
(p = 0.02, 0.03). Exploratory, after the report; descriptive. --write regenerates, --check refuses stale outputs.
Usage: churn_paper.py --first churn.json --mid churn_mid.json --figdir <dir> --tabdir <dir> [--summary churn_paper.json] (--write | --check)"""
import argparse
import json
import sys
from pathlib import Path

RULES = (("F111", "R3"), ("C*", "C$^*$"), ("F000", "B3"))
VERS = ("base", "doubled")


def _stats(first: dict, mid: dict, ver: str) -> dict:
    s = dict(first["statistics"][ver]); s.update({k: v for k, v in mid["statistics"][ver].items() if k != "0"})
    return s


def _r4(first: dict, mid: dict, key: str) -> dict:
    out = {}
    for src in (first, mid):
        for k, v in src["review_r4"][key].items():
            if isinstance(v, dict):
                out.setdefault(k, {}).update(v)
    return out


def data(first: dict, mid: dict) -> dict:
    rates = sorted({float(k) for v in VERS for k in _stats(first, mid, v)})
    curves = {}
    for ver in VERS:
        s = _stats(first, mid, ver)
        curves[ver] = {c: [{"p": p, "estimate": s[_key(p)][c]["pooled"]["estimate"], "lo": s[_key(p)][c]["pooled"]["ci95"][0],
                            "hi": s[_key(p)][c]["pooled"]["ci95"][1]} for p in rates] for c in ("d", "q")}
    alloc, eff = _r4(first, mid, "audit_allocation"), _r4(first, mid, "eff_attack")
    rows = []
    for p in [r for r in rates if r > 0]:
        for rule, name in RULES:
            a = alloc[_key(p)][f"{rule}|base"]
            rows.append({"p": p, "rule": name, "focal_audit_rate": a["focal_audit_rate"], "young_honest_job_share": a["young_honest_job_share"],
                         "young_honest_audit_share": a["young_honest_audit_share"], "established_honest_audit_rate": a["established_honest_audit_rate"],
                         "x_off": sum(1 for x in a["x_by_market"].values() if x == 0), "markets": a["markets"],
                         "eff_attack": eff["base"][_key(p)][rule]})
    return {"label": "exploratory, after the report; frozen searches unless stated", "rates": rates, "curves": curves, "allocation": rows}


def summary(first: dict, mid: dict) -> dict:
    """Aggregates that the paper cites and the records hold only per cell: the doubling flags' largest attack change,
    the reselection diagnostic (reference_change), and per rate and rule the audit allocation, the selected attacks
    without replacement (x_off) and the gross efficiency under attack (frozen searches)."""
    cells = {**first["flags"], **mid["flags"]}
    top = max(cells, key=lambda k: cells[k]["attack_change"])
    alloc, eff = _r4(first, mid, "audit_allocation"), _r4(first, mid, "eff_attack")
    rates = {}
    for p, rows in alloc.items():
        rates[p] = {}
        for rule, name in RULES:
            a = rows[f"{rule}|base"]
            rates[p][name.replace("$^*$", "*")] = {
                "focal_audit_rate": a["focal_audit_rate"], "young_honest_job_share": a["young_honest_job_share"],
                "young_honest_audit_share": a["young_honest_audit_share"], "established_honest_audit_rate": a["established_honest_audit_rate"],
                "x_off": sum(1 for x in a["x_by_market"].values() if x == 0), "markets": a["markets"], "eff": eff["base"][p][rule]}
    return {"label": "exploratory, after the report; aggregates of churn.json and churn_mid.json",
            "flags": {"cells": len(cells), "max_attack_change": cells[top]["attack_change"], "max_attack_cell": top,
                      "reselected": sum(1 for c in cells.values() if c["reference_change"] != 0),
                      "max_reference_change": max(abs(c["reference_change"]) for c in cells.values())},
            "rates": rates}


def _key(p: float) -> str:
    return "0" if p == 0 else f"{p:g}"


def _f(x: float) -> str:
    s = f"{x:.3f}"
    return s.replace("-", "$-$")


def audit_table(d: dict) -> str:
    head = ("\\begin{tabular}{llcccccc}\n\\toprule\n$p$ & Rule & attacker's jobs audited & young honest jobs & "
            "audits to young honest & established honest audited & winners without replacement & efficiency \\\\\n\\midrule\n")
    body = "".join(f"{r['p']:g} & {r['rule']} & {_f(r['focal_audit_rate'])} & {_f(r['young_honest_job_share'])} & "
                   f"{_f(r['young_honest_audit_share'])} & {_f(r['established_honest_audit_rate'])} & {r['x_off']} of {r['markets']} & "
                   f"{_f(r['eff_attack'])} \\\\\n" for r in d["allocation"])
    return head + body + "\\bottomrule\n\\end{tabular}\n"


def _draw(d: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(5.5, 2.8))
    style = {("d", "base"): ("o-", "#20675a", "C$^*$ $-$ R3"), ("q", "base"): ("s-", "#b0471b", "B3 $-$ R3"),
             ("d", "doubled"): ("o--", "#20675a", "C$^*$ $-$ R3, doubled"), ("q", "doubled"): ("s--", "#b0471b", "B3 $-$ R3, doubled")}
    for (c, ver), (fmt, col, lab) in style.items():
        pts = d["curves"][ver][c]
        ax.plot([p["p"] for p in pts], [p["estimate"] for p in pts], fmt, color=col, label=lab, ms=4, mfc="white" if ver == "doubled" else col)
    ax.axhline(0, color="#1c2421", lw=0.6)
    ax.set_xlabel("honest churn rate $p$ (per round)"); ax.set_ylabel("gain difference")
    ax.legend(fontsize=7, frameon=False); fig.tight_layout()
    fig.savefig(path, metadata={"CreationDate": None}); plt.close(fig)   # no timestamp: the bytes depend only on the data (Astra d10-r1, 8)


def _same_pdf(d: dict, path: Path) -> bool:
    """The PDF on disk equals a fresh rendering of the data, byte for byte."""
    import tempfile
    if not path.exists():
        return False
    with tempfile.TemporaryDirectory() as t:
        fresh = Path(t) / "fig.pdf"; _draw(d, fresh)
        return fresh.read_bytes() == path.read_bytes()


def write(d: dict, figdir, tabdir, summary_path=None, summary=None) -> None:
    fd, td = Path(figdir), Path(tabdir)
    if summary_path is not None:
        Path(summary_path).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    (fd / "fig_churn.data.json").write_text(json.dumps(d, indent=1, sort_keys=True))
    _draw(d, fd / "fig_churn.pdf")
    (td / "posthoc_churn_audit.tex").write_text(audit_table(d))


def check(d: dict, figdir, tabdir, summary_path=None, summary=None) -> list:
    fd, td = Path(figdir), Path(tabdir); bad = []
    if summary_path is not None:
        sp = Path(summary_path)
        if not sp.exists() or json.loads(sp.read_text()) != json.loads(json.dumps(summary, sort_keys=True)):
            bad.append(f"{sp.name}: stale or missing; run --write")
    f = fd / "fig_churn.data.json"
    if not f.exists() or json.loads(f.read_text()) != json.loads(json.dumps(d, sort_keys=True)) or not _same_pdf(d, fd / "fig_churn.pdf"):
        bad.append("fig_churn: stale or missing; run --write")
    t = td / "posthoc_churn_audit.tex"
    if not t.exists() or t.read_text() != audit_table(d):
        bad.append("posthoc_churn_audit.tex: stale or missing; run --write")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", required=True); ap.add_argument("--mid", required=True)
    ap.add_argument("--figdir", required=True); ap.add_argument("--tabdir", required=True); ap.add_argument("--summary", default=None)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    first, mid = json.loads(Path(a.first).read_text()), json.loads(Path(a.mid).read_text())
    d, s = data(first, mid), summary(first, mid)
    if a.write:
        write(d, a.figdir, a.tabdir, a.summary, s); return 0
    bad = check(d, a.figdir, a.tabdir, a.summary, s); print("\n".join(bad) or "ok"); return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
