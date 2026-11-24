"""Paper summary and tables for the churn replication, built from the committed analysis (replication-analysis.json) and
the post-analysis extract (replication-extract.json); not part of the stamped manifest.

Refusals: the analysis must be confirmatory and report no problem, unscorable cell, round-1 mismatch or failed gate; the
extract must be bound to this analysis file (sha256; the extract recomputed it from the collected records) and to the
committed draw and manifest (experiments/v2/replication-draw.json, replication-manifest.json), carry the same collector
status and counts, and list unique continued cells of the run's shapes whose number equals the continued plus
unresolved counts and whose (rate, market, rule) set equals the cells where the primary and frozen terms differ. Audit
counts must be integers with 0 <= audited <= served, the allocation shares must lie in [0, 1] with the attacker's
audited rate equal to audited over served and x in {0, 1}; the frozen set must cover every rate and market, and the
primary set may miss exactly the continued R3 cells at a rate where the run code computed no continued diagnostics
(p = 0.03). Expectation 5 must agree with the audit counts (lower on at least five of six markets).

The summary holds the derived values the analysis file does not store, per winner set: R3's audited share of the
attacker's jobs (min, max, markets with a count, markets lower at p = 0.05 than at p = 0, a zero denominator at either
rate counted as not lower), R3's audit allocation (the draft-10 statistics, equal-weight means over the markets with
diagnostics), mean and lowest efficiency under attack per rule, the markets with a negative absolute contrast, the two
most negative paired changes per contrast and rate with the range of the other four, the number of contrast-rate pairs
meeting the support criterion and the material companion, and the expectation tally; across sets, the primary minus
all-frozen difference of each pooled absolute contrast; and the continued cells by rate and rule.

Usage: replication_paper.py --analysis A --extract E --summary S --table T (--write | --check); the appendix tables are
written next to T (replication_markets.tex, replication_absolute.tex, replication_terms.tex, replication_alloc.tex)."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from replication_extract import parse_cell  # noqa: E402

RATES = ("0", "0.03", "0.05")
MARKETS = tuple(f"rep{i}" for i in range(6))
RULES = ("R3", "C*", "C-thr", "B3")
POLICY = {"F111": "R3", "Cstar": "C*", "F000": "B3"}   # menu policies; every cthr-directory cell is C-thr
SETS = (("primary", "Primary"), ("frozen", "All-frozen"))
X = (("d", "$d$ (C$^*$)"), ("q", "$q$ (B3)"), ("u", "$u$ (C-thr)"))
ALLOC = ("young_honest_job_share", "young_honest_audit_share", "established_honest_audit_rate", "focal_job_share", "focal_audit_rate")
STATUS = ("problems", "unscorable", "round1_mismatch", "gate_ok")
ROOT = Path(__file__).resolve().parents[3]
COMMITTED = {"draw": ROOT / "experiments/v2/replication-draw.json", "manifest": ROOT / "experiments/v2/replication-manifest.json"}
CONT_DIAG_RATES = ("0", "0.05")       # rep_collect.run_diagnostics: continued R3 winners get diagnostics only at these rates
APPENDIX = ("markets", "absolute", "terms", "alloc")


def sha_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


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


def _alloc(al: dict) -> dict:
    out = {}
    for p in RATES:
        rows = list(al.get(p, {}).values())
        mean = lambda k: (sum(r[k] for r in rows if r[k] is not None) / sum(r[k] is not None for r in rows)
                          if any(r[k] is not None for r in rows) else None)
        out[p] = {k: mean(k) for k in ALLOC}
        out[p]["markets"] = len(rows)
        out[p]["replacing_markets"] = sum(r["x"] == 1 for r in rows)
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


def _spread(pc: dict) -> dict:
    """The two most negative market changes, their markets, and the range of the other four."""
    v = sorted(pc["markets"].items(), key=lambda kv: kv[1])
    rest = [x for _, x in v[2:]]
    return {"top": {"0": v[0][1], "1": v[1][1]}, "top_markets": sorted(m for m, _ in v[:2]), "rest": {"min": min(rest), "max": max(rest)}}


def _continued(cells: list) -> dict:
    out = {"all": {"cells": len(cells)}, "rules": {r: {"cells": sum(_rule(c) == r for c in cells)} for r in RULES}}
    out.update({p: {"cells": sum(c["rate"] == p for c in cells)} for p in RATES})
    return out


def _rule(c: dict) -> str:
    return "C-thr" if c["kind"] == "cthr" else POLICY[c["policy"]]


def _validate_counts(extract: dict) -> None:
    for s, _ in SETS:
        for p, ms in extract["audit"][s].items():
            for m, c in ms.items():
                if not (isinstance(c, list) and len(c) == 2 and all(isinstance(v, int) and not isinstance(v, bool) for v in c)
                        and 0 <= c[0] <= c[1]):
                    raise ValueError(f"impossible audit count {s} {p} {m}: {c}")
                al = extract["alloc"][s][p][m]
                if any(al[k] is not None and not 0 <= al[k] <= 1 for k in ALLOC) or al.get("x") not in (0, 1):
                    raise ValueError(f"allocation out of range {s} {p} {m}")
                want = c[0] / c[1] if c[1] else None
                if (want is None) != (al["focal_audit_rate"] is None) or (want is not None and abs(want - al["focal_audit_rate"]) > 1e-12):
                    raise ValueError(f"the attacker's audited rate disagrees with its counts {s} {p} {m}")


def _validate_coverage(analysis: dict, extract: dict) -> None:
    full = {(p, m) for p in RATES for m in MARKETS}
    have = lambda s: {(p, m) for p, ms in extract["audit"][s].items() for m in ms}
    if have("frozen") != full:
        raise ValueError("the frozen audit counts do not cover every rate and market")
    gaps = {(c["rate"], c["market"]) for c in extract["continued"] if _rule(c) == "R3" and c["rate"] not in CONT_DIAG_RATES}
    if have("primary") != full - gaps:
        raise ValueError("the primary audit counts miss cells other than continued R3 cells without diagnostics")
    differ = {(p, m, r) for p in RATES for m in MARKETS for r in RULES
              if analysis["primary"]["terms"][p][m][r] != analysis["frozen"]["terms"][p][m][r]}
    if differ != {(c["rate"], c["market"], _rule(c)) for c in extract["continued"]}:
        raise ValueError("the continued cells are not the cells whose primary and frozen terms differ")


def _validate(analysis: dict, extract: dict, analysis_sha: str) -> None:
    if analysis.get("problems") or analysis.get("unscorable") or analysis.get("round1_mismatch") or not analysis.get("gate_ok"):
        raise ValueError("the analysis reports problems, unscorable cells, a round-1 mismatch or a failed gate")
    if analysis.get("confirmatory") is not True:
        raise ValueError("the analysis is not the confirmatory run")
    b = extract.get("binding") or {}
    if b.get("analysis") != analysis_sha or b.get("recomputed") is not True:
        raise ValueError("the extract is not bound to this analysis file")
    for k, path in COMMITTED.items():
        if b.get(k) != sha_file(path):
            raise ValueError(f"the extract's {k} is not the committed {path.name}")
    if extract.get("status") != {k: analysis.get(k) for k in STATUS}:
        raise ValueError("the extract's collector status differs from the analysis")
    if analysis["counts"] != extract["counts"]:
        raise ValueError("the extract's counts differ from the analysis")
    stems = [c["stem"] for c in extract["continued"]]
    if len(set(stems)) != len(stems):
        raise ValueError("duplicate continued cell")
    for c in extract["continued"]:
        if dict(parse_cell(c["stem"]), stem=c["stem"]) != c:
            raise ValueError(f"continued cell fields disagree with its identity: {c['stem']}")
    if len(stems) != analysis["counts"]["continued"] + analysis["counts"].get("unresolved", 0):
        raise ValueError("the continued-cell list does not match the continued count")
    for s, _ in SETS:
        for part in ("audit", "alloc"):
            for p, ms in extract[part][s].items():
                if p not in RATES or not set(ms) <= set(MARKETS):
                    raise ValueError(f"unexpected rate or market in the extract's {part} ({s}, {p})")
        if {p: set(ms) for p, ms in extract["audit"][s].items()} != {p: set(ms) for p, ms in extract["alloc"][s].items()}:
            raise ValueError(f"audit counts and allocation cover different cells ({s})")
    _validate_counts(extract)
    _validate_coverage(analysis, extract)


def summary(analysis: dict, extract: dict, analysis_sha: str) -> dict:
    _validate(analysis, extract, analysis_sha)
    res = {"continued": _continued(extract["continued"])}
    for s, _ in SETS:
        if isinstance(analysis[s], str):
            raise ValueError(f"winner set {s} not available")
        a = analysis[s]
        res[s] = {"audit": _audit(extract["audit"][s]), "alloc": _alloc(extract["alloc"][s]), "eff": _eff(a["terms"]),
                  "absneg": {p: {x: {"negative": sum(v["estimate"] < 0 for v in a["absolute"][p][x]["markets"].values())}
                                 for x, _ in X} for p in RATES},
                  "spread": {p: {x: _spread(a["paired_changes"][p][x]) for x, _ in X} for p in ("0.03", "0.05")},
                  "criteria": {k: {"cells": sum(c[k] for p in a["criteria"] for c in a["criteria"][p].values())}
                               for k in ("support", "material")}}
        v = [e["verdict"] for e in a["expectations"].values()]
        if any(x not in ("met", "not met") for x in v):
            raise ValueError(f"expectation not scorable in {s}")
        res[s]["exp"] = {"fulfilled": v.count("met"), "failed": v.count("not met")}
        if (res[s]["audit"]["below"]["markets"] >= 5) != (a["expectations"]["5"]["verdict"] == "met"):
            raise ValueError(f"the audit counts disagree with expectation 5 ({s})")
    res["setdiff"] = {p: {x: {"difference": analysis["primary"]["absolute"][p][x]["mean"] - analysis["frozen"]["absolute"][p][x]["mean"]}
                          for x, _ in X} for p in RATES}
    return res


def _f(v) -> str:
    """Three decimals; four where a nonzero value would print as 0.000, so that a bound's sign stays visible."""
    if v is None:
        return "--"
    s = f"{v:.3f}" if v == 0 or abs(v) >= 0.0005 else f"{v:.4f}"
    return s.replace("-", "$-$")


def _ci(c) -> str:
    return f"[{_f(c[0])}, {_f(c[1])}]"


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
                cells += [f"{_f(c['mean'])} {_ci(c['t95'])}", f"{c['lower']}/6"]
            lines.append(" & ".join([lab, p] + cells) + " \\\\")
    lines += ["\\midrule", f"\\multicolumn{{{len(cols)}}}{{l}}{{\\emph{{Absolute contrast: mean [market $t$ interval]}}}} \\\\"]
    for s, lab in SETS:
        for p in RATES:
            cells = []
            for x, _ in X:
                c = analysis[s]["absolute"][p][x]
                cells += [f"\\multicolumn{{2}}{{r}}{{{_f(c['mean'])} {_ci(c['t95'])}}}"]
            lines.append(" & ".join([lab, p] + cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def table_markets(analysis: dict) -> str:
    """Per-market paired changes with their seed-bootstrap intervals (second line), and the equal-weight mean with its
    pooled seed-bootstrap interval; both sets, both churn rates, all three contrasts."""
    lines = ["\\begin{tabular}{lll" + "r" * (len(MARKETS) + 1) + "}", "\\toprule",
             " & ".join(["Winners", "$p$", "Contrast"] + list(MARKETS) + ["Mean"]) + " \\\\", "\\midrule"]
    for s, lab in SETS:
        for p in ("0.03", "0.05"):
            for x, xl in X:
                c, b = analysis[s]["paired_changes"][p][x], analysis[s]["bootstrap"][p][x]
                lines.append(" & ".join([lab, p, xl] + [_f(c["markets"][m]) for m in MARKETS] + [_f(c["mean"])]) + " \\\\")
                lines.append(" & ".join(["", "", ""] + [f"{{\\scriptsize {_ci(b['markets'][m]['ci95'])}}}" for m in MARKETS]
                                        + [f"{{\\scriptsize {_ci(b['pooled']['ci95'])}}}"]) + " \\\\")
    return "\n".join(lines + ["\\bottomrule", "\\end{tabular}", ""])


def table_absolute(analysis: dict) -> str:
    """Per-market absolute contrasts with their seed-bootstrap intervals (second line), and the pooled mean with its
    pooled seed-bootstrap interval."""
    lines = ["\\begin{tabular}{lll" + "r" * (len(MARKETS) + 1) + "}", "\\toprule",
             " & ".join(["Winners", "$p$", "Contrast"] + list(MARKETS) + ["Pooled"]) + " \\\\", "\\midrule"]
    for s, lab in SETS:
        for p in RATES:
            for x, xl in X:
                c = analysis[s]["absolute"][p][x]
                lines.append(" & ".join([lab, p, xl] + [_f(c["markets"][m]["estimate"]) for m in MARKETS] + [_f(c["mean"])]) + " \\\\")
                lines.append(" & ".join(["", "", ""] + [f"{{\\scriptsize {_ci(c['markets'][m]['ci95'])}}}" for m in MARKETS]
                                        + [f"{{\\scriptsize {_ci(c['pooled_ci95'])}}}"]) + " \\\\")
    return "\n".join(lines + ["\\bottomrule", "\\end{tabular}", ""])


def table_terms(analysis: dict) -> str:
    """Equal-weight means over the six markets of each rule's normalised attacked profit, reference profit and gain, and
    its gross efficiency under the selected attack (mean and lowest market)."""
    lines = ["\\begin{tabular}{lllrrrrr}", "\\toprule",
             "Winners & $p$ & Rule & Attack & Reference & Gain & Efficiency & Lowest \\\\", "\\midrule"]
    for s, lab in SETS:
        for p in RATES:
            t = analysis[s]["terms"][p]
            for r in RULES:
                v = {k: [t[m][r][k] for m in MARKETS] for k in ("attack", "reference", "gain", "eff_attack")}
                mean = lambda k: sum(v[k]) / len(v[k])
                lines.append(" & ".join([lab, p, r.replace("C*", "C$^*$"), _f(mean("attack")), _f(mean("reference")), _f(mean("gain")),
                                         _f(mean("eff_attack")), _f(min(v["eff_attack"]))]) + " \\\\")
    return "\n".join(lines + ["\\bottomrule", "\\end{tabular}", ""])


def table_alloc(summ: dict) -> str:
    """R3's audit allocation per set and rate: equal-weight means over the markets with diagnostics, and the range of
    the audited share of the attacker's jobs over those markets."""
    lines = ["\\begin{tabular}{llrrrrrrrr}", "\\toprule",
             "Winners & $p$ & Markets & Young honest jobs & Young honest audits & Established honest rate & Attacker jobs & "
             "Attacker rate & Attacker range & Replacing \\\\", "\\midrule"]
    for s, lab in SETS:
        for p in RATES:
            a, au = summ[s]["alloc"][p], summ[s]["audit"][p]
            lines.append(" & ".join([lab, p, f"{a['markets']}/6"] + [_f(a[k]) for k in ALLOC]
                                    + [f"{_f(au['focal_audit_min'])}--{_f(au['focal_audit_max'])}", f"{a['replacing_markets']}/{a['markets']}"]) + " \\\\")
    return "\n".join(lines + ["\\bottomrule", "\\end{tabular}", ""])


def _dump(d: dict) -> str:
    return json.dumps(d, indent=1, sort_keys=True) + "\n"


def outputs(analysis, extract, analysis_sha, summary_path, table_path) -> dict:
    s = summary(analysis, extract, analysis_sha)
    d = Path(table_path).parent
    return {Path(summary_path): _dump(s), Path(table_path): table(analysis),
            d / "replication_markets.tex": table_markets(analysis), d / "replication_absolute.tex": table_absolute(analysis),
            d / "replication_terms.tex": table_terms(analysis), d / "replication_alloc.tex": table_alloc(s)}


def write(analysis, extract, analysis_sha, summary_path, table_path) -> None:
    for path, text in outputs(analysis, extract, analysis_sha, summary_path, table_path).items():
        path.write_text(text)


def check(analysis, extract, analysis_sha, summary_path, table_path) -> list:
    return [f"stale: {p} (run replication_paper.py --write)"
            for p, want in outputs(analysis, extract, analysis_sha, summary_path, table_path).items()
            if not p.exists() or p.read_text() != want]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for k in ("analysis", "extract", "summary", "table"):
        ap.add_argument(f"--{k}", required=True)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    an, ex = (json.loads(Path(p).read_text()) for p in (a.analysis, a.extract))
    sha = sha_file(a.analysis)
    if a.write:
        write(an, ex, sha, a.summary, a.table); return 0
    probs = check(an, ex, sha, a.summary, a.table)
    print("\n".join(probs) or "ok")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
