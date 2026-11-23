"""Paper summary and table for the churn replication, built from the committed analysis (replication-analysis.json) and
the post-analysis extract (replication-extract.json); not part of the stamped manifest. The summary holds the derived
values the analysis file does not store: R3's audited share of the attacker's jobs per winner set and rate (min, max,
the markets with a count, and the markets where p = 0.05 is below p = 0, with a zero denominator at either rate counted
as not below, as expectation 5 is scored), mean efficiency under attack per rule, and the continued cells by rate and
rule. Usage: replication_paper.py --analysis A --extract E --summary S --table T (--write | --check)"""
import argparse
import json
import math
import sys
from pathlib import Path

RATES = ("0", "0.03", "0.05")
RULES = ("R3", "C*", "C-thr", "B3")
POLICY = {"F111": "R3", "Cstar": "C*", "F000": "B3"}   # menu policies; every cthr-directory cell is C-thr
SETS = (("primary", "Primary winners"), ("frozen", "All-frozen winners"))
X = (("d", "$d$ (C$^*$)"), ("q", "$q$ (B3)"), ("u", "$u$ (C-thr)"))


def _share(c):
    return c[0] / c[1] if c and c[1] > 0 else None


def _audit(au: dict) -> dict:
    out = {}
    for p in RATES:
        sh = [s for s in (_share(c) for c in au.get(p, {}).values()) if s is not None]
        out[p] = {"markets": len(sh), "focal_audit_min": min(sh) if sh else None, "focal_audit_max": max(sh) if sh else None}
    below = 0
    for m, c5 in au.get("0.05", {}).items():
        s0, s5 = _share(au.get("0", {}).get(m)), _share(c5)
        below += int(s0 is not None and s5 is not None and s5 < s0)
    out["below"] = {"markets": below}
    return out


def _eff(terms: dict) -> dict:
    out = {}
    for p in RATES:
        out[p] = {}
        for r in RULES:
            v = [terms[p][m][r]["eff_attack"] for m in sorted(terms[p])]
            if not all(math.isfinite(x) for x in v):
                raise ValueError(f"nonfinite efficiency at {p} {r}")
            out[p][r] = {"eff": sum(v) / len(v), "eff_min": min(v)}
    return out


def _continued(cells: list) -> dict:
    rule = lambda c: "C-thr" if c["kind"] == "cthr" else POLICY[c["policy"]]
    out = {"all": {"cells": len(cells)}, "rules": {r: {"cells": sum(rule(c) == r for c in cells)} for r in RULES}}
    out.update({p: {"cells": sum(c["rate"] == p for c in cells)} for p in RATES})
    return out


def summary(analysis: dict, extract: dict) -> dict:
    if analysis.get("problems") or analysis.get("unscorable") or analysis.get("round1_mismatch") or not analysis.get("gate_ok"):
        raise ValueError("the analysis reports problems, unscorable cells, a round-1 mismatch or a failed gate")
    for k in ("continued", "frozen"):
        if analysis["counts"].get(k) != extract["counts"].get(k):
            raise ValueError(f"the extract's {k} count differs from the analysis")
    if len(extract["continued"]) != analysis["counts"]["continued"]:
        raise ValueError("the continued-cell list does not match the continued count")
    res = {"continued": _continued(extract["continued"])}
    for s, _ in SETS:
        if isinstance(analysis[s], str):
            raise ValueError(f"winner set {s} not available")
        res[s] = {"audit": _audit(extract["audit"][s]), "eff": _eff(analysis[s]["terms"])}
    return res


def _f(v: float) -> str:
    return f"{v:.3f}".replace("-", "$-$")


def table(analysis: dict) -> str:
    cols = "ll" + "rr" * len(X)
    head = " & ".join(["Winners", "$p$"] + [f"\\multicolumn{{2}}{{c}}{{{lab}}}" for _, lab in X])
    lines = [f"\\begin{{tabular}}{{{cols}}}", "\\toprule", head + " \\\\",
             "\\midrule", f"\\multicolumn{{{len(cols)}}}{{l}}{{\\emph{{Paired change from the market's no-churn value: mean [market $t$ interval], markets lower}}}} \\\\"]
    for s, lab in SETS:
        for p in ("0.03", "0.05"):
            cells = []
            for x, _ in X:
                c = analysis[s]["paired_changes"][p][x]
                cells += [f"{_f(c['mean'])} [{_f(c['t95'][0])}, {_f(c['t95'][1])}]", f"{c['lower']}/6"]
            lines.append(" & ".join([lab, p] + cells) + " \\\\")
    lines += ["\\midrule", f"\\multicolumn{{{len(cols)}}}{{l}}{{\\emph{{Absolute contrast: mean [market $t$ interval]}}}} \\\\"]
    for s, lab in SETS:
        for p in RATES:
            cells = []
            for x, _ in X:
                c = analysis[s]["absolute"][p][x]
                cells += [f"\\multicolumn{{2}}{{r}}{{{_f(c['mean'])} [{_f(c['t95'][0])}, {_f(c['t95'][1])}]}}"]
            lines.append(" & ".join([lab, p] + cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def _dump(d: dict) -> str:
    return json.dumps(d, indent=1, sort_keys=True) + "\n"


def write(analysis, extract, summary_path, table_path) -> None:
    Path(summary_path).write_text(_dump(summary(analysis, extract)))
    Path(table_path).write_text(table(analysis))


def check(analysis, extract, summary_path, table_path) -> list:
    probs = []
    for path, want in ((summary_path, _dump(summary(analysis, extract))), (table_path, table(analysis))):
        if not Path(path).exists() or Path(path).read_text() != want:
            probs.append(f"stale: {path} (run replication_paper.py --write)")
    return probs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for k in ("analysis", "extract", "summary", "table"):
        ap.add_argument(f"--{k}", required=True)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    an, ex = (json.loads(Path(p).read_text()) for p in (a.analysis, a.extract))
    if a.write:
        write(an, ex, a.summary, a.table); return 0
    probs = check(an, ex, a.summary, a.table)
    print("\n".join(probs) or "ok")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
