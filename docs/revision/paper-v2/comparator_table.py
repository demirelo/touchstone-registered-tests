"""The development comparator table: each credibility configuration's stored attacker gains (D2+H3) and gross
efficiencies at the inner search budget, and the two configurations rechecked at full budget, from
experiments/v2/log/Cstar__*.json (development records, before the lock). Usage: comparator_table.py [LOGDIR] OUT.tex"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _name(c: dict) -> str:
    v = c["variant"]
    return "C-boinc" if v == "boinc" else f"C-mem({c['K']}, {c['M']})" if v == "mem" else f"C-{v}({c['K']})"


def rows(logdir) -> list:
    out = []
    for f in sorted(Path(logdir).glob("Cstar__*.json")):
        d = json.loads(f.read_text()); kind = f.stem.rsplit("__", 1)[1]
        out.append({"config": _name(d["spec"]["cred"]), "budget": "full" if kind == "recheck" else "inner",
                    "gain": {m: {fam: d["detail"][m][fam]["gain"] for fam in ("D2+H3", "X7-SC")} for m in ("headline", "dev0")},
                    "eff": {m: d["detail"][m]["D2+H3"]["eff"] for m in ("headline", "dev0")}})
    return sorted(out, key=lambda r: (r["config"], r["budget"] != "inner"))


def _f(x: float) -> str:
    return f"\\ensuremath{{{x:.3f}}}" if x < 0 else f"{x:.3f}"


def table(rs: list) -> str:
    body = "".join(f"{r['config']} & {r['budget']} & {_f(r['gain']['headline']['D2+H3'])} & {_f(r['gain']['dev0']['D2+H3'])} & "
                   f"{_f(r['eff']['headline'])} & {_f(r['eff']['dev0'])} \\\\\n" for r in rs)
    return ("\\begin{tabular}{@{}llrrrr@{}}\\toprule\n & & \\multicolumn{2}{c}{Gain, D2+H3} & \\multicolumn{2}{c}{Gross efficiency} \\\\\n"
            "Configuration & Budget & headline & dev0 & headline & dev0 \\\\\\midrule\n" + body + "\\bottomrule\\end{tabular}\n")


if __name__ == "__main__":
    a = sys.argv[1:]; logdir, out = (a[0], a[1]) if len(a) == 2 else (ROOT / "experiments/v2/log", a[0])
    Path(out).write_text(table(rows(logdir)).replace("C*", "C$^*$"))
