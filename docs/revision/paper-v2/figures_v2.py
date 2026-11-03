"""Evaluation-2 figures for the paper, drawn from report.json. Beside each figure, <name>.data.json lists every plotted
value with its report path; --check recomputes the data and compares (the image itself is not compared)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FRESH = tuple(f"fresh{i}" for i in range(6))
FAMS = ("D2+H3", "X7-SC")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def data_q1(r: dict) -> dict:
    pts, skipped = [], []
    for f in FAMS:
        base = f"q1.tests.C*-F111|{f}"; t = r["q1"]["tests"][f"C*-F111|{f}"]; iv = t.get("interval")
        if _num(t.get("estimate")) and iv and all(_num(x) for x in iv):
            pts.append({"family": f, "estimate": t["estimate"], "lo": iv[0], "hi": iv[1],
                        "paths": {"estimate": f"{base}.estimate", "lo": f"{base}.interval.0", "hi": f"{base}.interval.1"}})
        else:
            skipped.append(f)
    return {"points": pts, "skipped": skipped, "margin": 0.05}


def data_q4(r: dict) -> dict:
    pts, skipped = [], []
    for m in FRESH:
        x = r["q4"]["markets"][m]
        if not isinstance(x, dict):
            skipped.append(m); continue
        b = f"q4.markets.{m}"
        pts.append({"market": m, "gain_diff": x["gain_diff"], "gain_diff_lower": x["gain_diff_lower"], "eff": x["eff"], "eff_lower": x["eff_lower"],
                    "paths": {k: f"{b}.{k}" for k in ("gain_diff", "gain_diff_lower", "eff", "eff_lower")}})
    return {"points": pts, "skipped": skipped, "thresholds": {"gain": 0.10, "eff": 0.90}}


def data_q2(r: dict) -> dict:
    pts, skipped = [], []
    for f in FAMS:
        s, fx = r["q2"]["searched"][f], r["q2"]["fixed"][f]
        if isinstance(s, str) or isinstance(fx, str):
            skipped.append(f); continue
        for c in ("P", "G", "S"):
            b, bf = f"q2.searched.{f}.{c}", f"q2.fixed.{f}.{c}"
            pts.append({"family": f, "contrast": c, "searched": s[c]["estimate"], "lo": s[c]["interval"][0], "hi": s[c]["interval"][1],
                        "fixed": fx[c]["estimate"], "paths": {"searched": f"{b}.estimate", "lo": f"{b}.interval.0", "hi": f"{b}.interval.1",
                                                              "fixed": f"{bf}.estimate"}})
    return {"points": pts, "skipped": skipped}


DATA = {"fig_q1": data_q1, "fig_q4": data_q4, "fig_q2": data_q2}


def _draw(name: str, d: dict, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pts = d["points"]
    if name == "fig_q1":
        fig, ax = plt.subplots(figsize=(5, 2.2))
        for i, p in enumerate(pts):
            ax.errorbar(p["estimate"], i, xerr=[[p["estimate"] - p["lo"]], [p["hi"] - p["estimate"]]], fmt="o", capsize=3, color="#20675a")
        for x in (-d["margin"], d["margin"]):
            ax.axvline(x, ls="--", color="#606d67", lw=0.8)
        ax.axvline(0, color="#1c2421", lw=0.6); ax.set_yticks(range(len(pts)), [p["family"] for p in pts])
        ax.set_xlabel(r"$d = g_{C^*} - g_{F_{111}}$ (positive: R3 lower gain)")
    elif name == "fig_q4":
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(7, 2.6), sharey=True)
        ys = range(len(pts))
        a1.plot([p["gain_diff"] for p in pts], ys, "o", color="#20675a", label="estimate")
        a1.plot([p["gain_diff_lower"] for p in pts], ys, "|", ms=12, color="#b0471b", label="calibrated lower bound")
        a1.axvline(d["thresholds"]["gain"], ls="--", color="#606d67", lw=0.8); a1.set_xlabel(r"$g_{F_{000}} - g_{F_{111}}$ (D2+H3)")
        a2.plot([p["eff"] for p in pts], ys, "o", color="#20675a"); a2.plot([p["eff_lower"] for p in pts], ys, "|", ms=12, color="#b0471b")
        a2.axvline(d["thresholds"]["eff"], ls="--", color="#606d67", lw=0.8); a2.set_xlabel(r"$F_{111}$ gross efficiency")
        a1.set_yticks(list(ys), [p["market"] for p in pts]); fig.legend(*a1.get_legend_handles_labels(), loc="upper center", ncol=2, fontsize=7, frameon=False)
    else:
        fig, ax = plt.subplots(figsize=(6, 2.8))
        for i, p in enumerate(pts):
            ax.errorbar(p["searched"], i, xerr=[[p["searched"] - p["lo"]], [p["hi"] - p["searched"]]], fmt="o", capsize=3, color="#20675a",
                        label="searched" if i == 0 else None)
            ax.plot(p["fixed"], i, "s", mfc="none", color="#2a5d8a", label="fixed attacks" if i == 0 else None)
        ax.axvline(0, color="#1c2421", lw=0.6); ax.set_yticks(range(len(pts)), [f"{p['contrast']} ({p['family']})" for p in pts])
        ax.set_xlabel("contrast in gain"); ax.legend(fontsize=7)
    fig.tight_layout(rect=(0, 0, 1, 0.9) if name == "fig_q4" else None); fig.savefig(path); plt.close(fig)


def write(r: dict, outdir) -> None:
    d = Path(outdir); d.mkdir(parents=True, exist_ok=True)
    for name, fn in DATA.items():
        data = fn(r)
        (d / f"{name}.data.json").write_text(json.dumps(data, indent=1, sort_keys=True))
        _draw(name, data, d / f"{name}.pdf")


def check(r: dict, outdir) -> list[str]:
    d = Path(outdir); bad = []
    for name, fn in DATA.items():
        f = d / f"{name}.data.json"
        if not f.exists() or json.loads(f.read_text()) != json.loads(json.dumps(fn(r), sort_keys=True)) or not (d / f"{name}.pdf").exists():
            bad.append(f"{name}: stale or missing; run --write")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--report", required=True); ap.add_argument("--dir", required=True)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv); r = json.loads(Path(a.report).read_text())
    if a.write:
        write(r, a.dir); return 0
    bad = check(r, a.dir); print("\n".join(bad) or "ok"); return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
