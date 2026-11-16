"""Draft 10 churn float data (outline-draft10.md, sections 4 and 5): the C* - R3 and B3 - R3 curves against the churn
rate (figure) and the audit allocation per rate (table), from churn.json (p = 0, 0.01, 0.05) and churn_mid.json
(p = 0.02, 0.03). Exploratory, after the report; descriptive. --write regenerates, --check refuses stale outputs.
Usage: churn_paper.py --first churn.json --mid churn_mid.json --figdir <dir> --tabdir <dir> [--summary churn_paper.json --runnerup runnerup_analysis.json] (--write | --check)"""
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
            a, ad = alloc[_key(p)][f"{rule}|base"], alloc[_key(p)][f"{rule}|doubled"]
            rows.append({"p": p, "rule": name, "focal_audit_rate": a["focal_audit_rate"], "focal_audit_rate_doubled": ad["focal_audit_rate"],
                         "x_off_doubled": sum(1 for x in ad["x_by_market"].values() if x == 0), "eff_doubled": eff["doubled"][_key(p)][rule],
                         "young_honest_job_share": a["young_honest_job_share"], "young_honest_job_share_doubled": ad["young_honest_job_share"],
                         "young_honest_audit_share": a["young_honest_audit_share"], "young_honest_audit_share_doubled": ad["young_honest_audit_share"],
                         "established_honest_audit_rate": a["established_honest_audit_rate"],
                         "established_honest_audit_rate_doubled": ad["established_honest_audit_rate"],
                         "x_off": sum(1 for x in a["x_by_market"].values() if x == 0), "markets": a["markets"],
                         "eff_attack": eff["base"][_key(p)][rule]})
    return {"label": "exploratory, after the report; frozen searches unless stated", "rates": rates, "curves": curves, "allocation": rows}


def summary(first: dict, mid: dict, runnerup: dict | None = None) -> dict:
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
            ad = rows.get(f"{rule}|doubled")
            if ad:   # Fable round 5, problem 4 and 5: the doubled winners beside the frozen ones
                rates[p][name.replace("$^*$", "*")].update(focal_audit_rate_doubled=ad["focal_audit_rate"],
                    x_off_doubled=sum(1 for x in ad["x_by_market"].values() if x == 0), eff_doubled=eff["doubled"][p][rule])
    r5 = first.get("review_r5", {})
    r3 = {}
    if r5:   # Fable round 5, problems 5 and 8: R3 at p = 0.05 per market (frozen searches)
        fa = r5["focal_audit_rate_by_market"]["0.05"]["F111|base"]; xs = alloc["0.05"]["F111|base"]["x_by_market"]
        rep = [fa[m] for m in fa if xs.get(m) == 1]
        e = r5["eff_by_market"]["base"]["0.05"]["F111"]
        keep = [fa[m] for m in fa if xs.get(m) == 0]
        r3 = {"replacing_audit_min": min(rep), "replacing_audit_max": max(rep), "replacing_markets": len(rep),
              "staying_audit_min": min(keep), "staying_audit_max": max(keep), "staying_markets": len(keep),
              "eff_min": min(e.values()), "eff_min_market": min(e, key=e.get)}
        fad = r5["focal_audit_rate_by_market"]["0.05"].get("F111|doubled"); xd = alloc["0.05"]["F111|doubled"]["x_by_market"]
        if fad:   # Astra d10-r2, correction 5: the same range for the doubled winners
            repd = [fad[m] for m in fad if xd.get(m) == 1]
            keepd = [fad[m] for m in fad if xd.get(m) == 0]
            r3.update(replacing_audit_min_doubled=min(repd), replacing_audit_max_doubled=max(repd), replacing_markets_doubled=len(repd),
                      staying_audit_min_doubled=min(keepd), staying_audit_max_doubled=max(keepd), staying_markets_doubled=len(keepd))
    ru = {}
    for fam, vers in (runnerup or {}).items():
        if not isinstance(vers, dict):
            continue
        for v in ("base", "doubled"):
            ms = (vers.get(v) or {}).get("runner_up_minus_r3", {}).get("markets")
            if ms:   # Fable round 5, problem 1: runner-up minus R3 per market (positive: R3 lower)
                ru[f"{fam}|{v}"] = {"positive": sum(1 for g in ms.values() if g > 0), "negative": sum(1 for g in ms.values() if g < 0),
                                    "min": min(ms.values()), "min_market": min(ms, key=ms.get),
                                    "cstar_minus_runner_up": vers[v]["cstar_minus_runner_up"]["estimate"]}
    ruf = {}
    for fam, vers in (runnerup or {}).items():
        fl = vers.get("flags") if isinstance(vers, dict) else None
        if fl:   # Astra d10-r3: flags per family
            ruf[fam] = {"incomplete": sum(1 for v in fl.values() if v.get("incomplete")), "markets": len(fl)}
    return {"label": "exploratory, after the report; aggregates of churn.json and churn_mid.json", "r3_p05": r3, "runner_up": ru,
            "runner_up_flags": ruf,
            "flags": {"cells": len(cells), "max_attack_change": cells[top]["attack_change"], "max_attack_cell": top,
                      "reselected": sum(1 for c in cells.values() if c["reference_change"] != 0),
                      "max_reference_change": max(abs(c["reference_change"]) for c in cells.values()),
                      "incomplete_n": first["flag_summary"]["incomplete_n"] + mid["flag_summary"]["incomplete_n"]},
            "rates": rates}


def _key(p: float) -> str:
    return "0" if p == 0 else f"{p:g}"


def _f(x: float) -> str:
    s = f"{x:.3f}"
    return s.replace("-", "$-$")


def audit_table(d: dict) -> str:
    head = ("\\begin{tabular}{llcccccc}\n\\toprule\n$p$ & Rule & attacker's jobs audited & young honest jobs & "
            "audits to young honest & established honest audited & winners without replacement & efficiency \\\\\n\\midrule\n")
    body = "".join(f"{r['p']:g} & {r['rule']} & {_f(r['focal_audit_rate'])} / {_f(r['focal_audit_rate_doubled'])} & {_f(r['young_honest_job_share'])} / {_f(r['young_honest_job_share_doubled'])} & "
                   f"{_f(r['young_honest_audit_share'])} / {_f(r['young_honest_audit_share_doubled'])} & "
                   f"{_f(r['established_honest_audit_rate'])} / {_f(r['established_honest_audit_rate_doubled'])} & {r['x_off']} / {r['x_off_doubled']} of {r['markets']} & "
                   f"{_f(r['eff_attack'])} / {_f(r['eff_doubled'])} \\\\\n" for r in d["allocation"])
    return head + body + "\\bottomrule\n\\end{tabular}\n"


T5 = 2.570581835636314   # 0.975 quantile of Student's t with 5 degrees of freedom


def _t95(xs: list) -> tuple:
    import math
    n = len(xs); m = sum(xs) / n; sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    return m - T5 * sd / math.sqrt(n), m + T5 * sd / math.sqrt(n)


def runner_up_table(runnerup: dict) -> str:
    """Run A: runner-up minus R3 per family and search version, with the market-level t interval and the market signs
    (positive: R3 lower), and C* minus runner-up (Astra d10-r3, correction 2)."""
    rows = []
    for fam in ("D2+H3", "X7-SC"):
        for v, name in (("base", "frozen"), ("doubled", "doubled")):
            x = runnerup[fam][v]; ms = list(x["runner_up_minus_r3"]["markets"].values()); lo, hi = _t95(ms)
            rows.append(f"{fam} & {name} & {_f(x['runner_up_minus_r3']['estimate'])} & [{_f(lo)}, {_f(hi)}] & "
                        f"{sum(1 for g in ms if g > 0)} / {sum(1 for g in ms if g < 0)} & {_f(x['cstar_minus_runner_up']['estimate'])} \\\\\n")
    return ("\\begin{tabular}{llcccc}\n\\toprule\nFamily & Winner & runner-up $-$ R3 & market $t$ interval & markets R3 lower / higher & C$^*$ $-$ runner-up \\\\\n\\midrule\n"
            + "".join(rows) + "\\bottomrule\n\\end{tabular}\n")


def t_table(first: dict, mid: dict) -> str:
    """Market-level t intervals (5 degrees of freedom) over the six market differences, per rate and search version,
    from the review_r4 blocks (Astra d10-r2, correction 2)."""
    t = {v: {**first["review_r4"]["t95"][v], **mid["review_r4"]["t95"][v]} for v in VERS}
    rows = []
    for v, name in (("base", "frozen"), ("doubled", "doubled")):
        for p in sorted(t[v], key=float):
            d, q = t[v][p]["d"], t[v][p]["q"]
            rows.append(f"{name} & {p} & {_f(d['mean'])} [{_f(d['ci'][0])}, {_f(d['ci'][1])}] & {_f(q['mean'])} [{_f(q['ci'][0])}, {_f(q['ci'][1])}] \\\\\n")
    return ("\\begin{tabular}{llcc}\n\\toprule\nWinner & $p$ & $d$ = C$^*$$-$R3 & $q$ = B3$-$R3 \\\\\n\\midrule\n" + "".join(rows)
            + "\\bottomrule\n\\end{tabular}\n")


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


def write(d: dict, figdir, tabdir, summary_path=None, summary=None, ttable=None, rtable=None) -> None:
    fd, td = Path(figdir), Path(tabdir)
    if rtable is not None:
        (td / "posthoc_runnerup.tex").write_text(rtable)
    if ttable is not None:
        (td / "posthoc_churn_t.tex").write_text(ttable)
    if summary_path is not None:
        Path(summary_path).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    (fd / "fig_churn.data.json").write_text(json.dumps(d, indent=1, sort_keys=True))
    _draw(d, fd / "fig_churn.pdf")
    (td / "posthoc_churn_audit.tex").write_text(audit_table(d))


def check(d: dict, figdir, tabdir, summary_path=None, summary=None, ttable=None, rtable=None) -> list:
    fd, td = Path(figdir), Path(tabdir); bad = []
    if rtable is not None and (not (td / "posthoc_runnerup.tex").exists() or (td / "posthoc_runnerup.tex").read_text() != rtable):
        bad.append("posthoc_runnerup.tex: stale or missing; run --write")
    if ttable is not None and (not (td / "posthoc_churn_t.tex").exists() or (td / "posthoc_churn_t.tex").read_text() != ttable):
        bad.append("posthoc_churn_t.tex: stale or missing; run --write")
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
    ap.add_argument("--figdir", required=True); ap.add_argument("--tabdir", required=True); ap.add_argument("--summary", default=None); ap.add_argument("--runnerup", default=None)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.summary and not a.runnerup:   # Astra d10-r2, correction 9: a summary without Run A would silently lack runner_up
        ap.error("--summary requires --runnerup (followup2/runnerup_analysis.json)")
    first, mid = json.loads(Path(a.first).read_text()), json.loads(Path(a.mid).read_text())
    ru = json.loads(Path(a.runnerup).read_text()) if a.runnerup else None
    d, s, tt = data(first, mid), summary(first, mid, ru), t_table(first, mid)
    rt = runner_up_table(ru) if ru else None
    if a.write:
        write(d, a.figdir, a.tabdir, a.summary, s, tt, rt); return 0
    bad = check(d, a.figdir, a.tabdir, a.summary, s, tt, rt); print("\n".join(bad) or "ok"); return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
