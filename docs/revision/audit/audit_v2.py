"""Inference and numerical audit of the second test's report (external review round 5, 2026-11-07). Changes no registered
estimate or decision; it reads the report, the evaluation records, and the stability re-evaluation records.

1. Inference audit. The report stores, for Q1, the calibrated two-sided p-value that enters Holm (field "p"), and for Q4
   the raw one-sided bootstrap p-values per market (fields "p_gain", "p_eff") and the calibrated market maxima that enter
   Holm (field "q4.p"). This prints raw, calibrated, and Holm-adjusted values beside each decision and checks them against
   the registered rule (design 9.2, 9.3): p' = min(1, p / kappa); Q4 market value max(p'_gain, p'_eff); Holm at 0.05.
2. Q4 per market from records (frozen functions), for the report's records and for the registered-configuration
   re-evaluation, so the stability table can print every Q4 quantity old and new.
3. Extreme descriptive intervals: every interval in the report with a bound beyond a limit, and a studentization
   diagnostic (sample standard error, smallest resample standard error, near-constant resamples) for each.

Usage: audit_v2.py --report report.json --records EVAL/all --stability-work DIR --out audit.json --tables DIR
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sim.decisions_v2 import ALPHA, Q1_SLOTS, q1_family, q4_markets  # noqa: E402
from sim.intervals import V2_RESAMPLE_SEED, _boot_idx, bootstrap_pvalue, studentized_tstats, calibrated, stratified_two_sided, studentized_at  # noqa: E402

FRESH = tuple(f"fresh{i}" for i in range(6))
FAMS = ("D2+H3", "X7-SC")
KAPPA = {"Q1": 0.5, "Q4": 0.25}                                   # protocol-v2.yaml, admitted multipliers


def safe(rid: str) -> str:
    return rid.replace("|", "__").replace("/", "~").replace("*", "star")      # revision_v2._safe


def holm_adjusted(p: list) -> list:
    """Holm step-down adjusted p-values: sorted ascending, adj_(i) = max_{j<=i} min(1, (m - j + 1) p_(j))."""
    m = len(p); order = sorted(range(m), key=lambda i: p[i]); out = [0.0] * m; run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (m - rank) * float(p[i]))); out[i] = run
    return out


def q1_audit(report: dict, kappa: float, raw: dict, categories: dict | None = None) -> tuple[dict, list]:
    """raw: the recomputed two-sided raw p-value per test; the stored value must equal calibrated(raw). categories: the
    category recomputed by the frozen q1_family from the records; it must equal the report's."""
    tests = report["q1"]["tests"]; names = list(tests); problems = []
    stored = [float(tests[n]["p"]) for n in names]
    slots = stored + [1.0] * max(0, Q1_SLOTS - len(stored)); adj = holm_adjusted(slots)
    rows = {}
    for i, n in enumerate(names):
        cal = calibrated(raw[n], kappa)
        if not np.isclose(cal, stored[i], rtol=0, atol=1e-12):
            problems.append(f"q1 {n}: stored p {stored[i]} differs from calibrated raw {cal}")
        reject = adj[i] <= ALPHA
        if reject != bool(tests[n]["reject"]):
            problems.append(f"q1 {n}: Holm decision {reject} differs from the report's {tests[n]['reject']}")
        if categories is not None and categories[n] != tests[n].get("category"):
            problems.append(f"q1 {n}: category {tests[n].get('category')!r} differs from the recomputed {categories[n]!r}")
        rows[n] = {"raw": float(raw[n]), "calibrated": cal, "holm_adjusted": adj[i], "reject": bool(tests[n]["reject"])}
    return rows, problems


def q4_audit(report: dict, kappa: float) -> tuple[dict, list]:
    q = report["q4"]; mk = q["markets"]; problems = []; rows = {}
    pa = [mk[m]["p_gain"] if isinstance(mk[m], dict) else 1.0 for m in FRESH]
    pb = [mk[m]["p_eff"] if isinstance(mk[m], dict) else 1.0 for m in FRESH]
    cal_max = [max(calibrated(a, kappa), calibrated(b, kappa)) for a, b in zip(pa, pb)]
    adj = holm_adjusted(cal_max)
    for i, m in enumerate(FRESH):
        if not np.isclose(cal_max[i], float(q["p"][i]), rtol=0, atol=1e-12):
            problems.append(f"q4 {m}: stored market value {q['p'][i]} differs from max calibrated {cal_max[i]}")
        dec = "pass" if adj[i] <= ALPHA else "fail"
        if (dec == "pass") != (m in q["passing"]):
            problems.append(f"q4 {m}: Holm decision {dec} differs from the report")
        rows[m] = {"raw_gain": float(pa[i]), "raw_eff": float(pb[i]), "calibrated_gain": calibrated(pa[i], kappa),
                   "calibrated_eff": calibrated(pb[i], kappa), "market_value": cal_max[i], "holm_adjusted": adj[i], "decision": dec}
    return rows, problems


def q4_market(f0: dict, f1: dict, kappa: float) -> dict:
    """The report's Q4 per-market quantities (report_v2.q4) from two records."""
    d = np.asarray(f0["gain"], dtype=float) - np.asarray(f1["gain"], dtype=float); eff = np.asarray(f1["eff_attack"], dtype=float)
    tail = kappa * ALPHA / len(FRESH)
    return {"gain_diff": float(d.mean()), "gain_diff_lower": float(studentized_at(d, "lower", tail)), "eff": float(eff.mean()),
            "eff_lower": float(studentized_at(eff, "lower", tail)), "p_gain": bootstrap_pvalue(d, 0.10, "lower"),
            "p_eff": bootstrap_pvalue(eff, 0.90, "lower")}


def q4_table(load, kappa: float) -> dict:
    """load(market, rule) -> record. Per market quantities, calibrated market value, Holm-adjusted value, decision."""
    rows = {m: q4_market(load(m, "F000"), load(m, "F111"), kappa) for m in FRESH}
    dec = q4_markets([rows[m]["p_gain"] for m in FRESH], [rows[m]["p_eff"] for m in FRESH], kappa)
    adj = holm_adjusted(dec["p"])
    for i, m in enumerate(FRESH):
        rows[m].update(market_value=dec["p"][i], holm_adjusted=adj[i], decision="pass" if dec["pass"][i] else "fail")
    return rows


def extreme_intervals(obj, limit: float = 1e3, path: str = "") -> list:
    hits = []
    if isinstance(obj, dict):
        iv = obj.get("interval")
        if isinstance(iv, list) and len(iv) == 2 and all(isinstance(v, (int, float)) for v in iv) and max(abs(v) for v in iv) > limit:
            hits.append(path)
        for k, v in obj.items():
            if k != "interval":
                hits += extreme_intervals(v, limit, f"{path}/{k}" if path else k)
    return hits


def studentization(x, resamples: int = 9999, seed: int = V2_RESAMPLE_SEED) -> dict:
    """What the frozen studentized bootstrap sees (sim.intervals.studentized_tstats): the sample standard error and the
    bootstrap-t statistics. A resample whose standard error is tiny but positive gives a huge statistic; the frozen code
    replaces only an exactly zero resample standard error."""
    x = np.asarray(x, dtype=float); _, se, t = studentized_tstats(x, resamples, seed); a = np.abs(t)
    return {"n": int(x.size), "mean": float(x.mean()), "se": float(se), "share_zero": float(np.mean(x == 0)),
            "max_abs": float(np.max(np.abs(x))),
            "seeds_above_1e-9": int(np.sum(np.abs(x) > 1e-9)), "prob_resample_without_them": float((1 - np.mean(np.abs(x) > 1e-9)) ** x.size),
            "resamples_without_them": int(np.sum(~(np.abs(x) > 1e-9)[_boot_idx(x.size, resamples, seed)].any(axis=1))),
            "max_rounding_residual": float(np.max(np.abs(x[np.abs(x) <= 1e-9]))) if np.any(np.abs(x) <= 1e-9) else 0.0,
            "max_abs_t": float(a.max()), "resamples_abs_t_over_100": int(np.sum(a > 100)),
            "t_quantiles": [float(q) for q in np.quantile(t, [0.0005, 0.025, 0.975, 0.9995])]}


def labels(paths: list, diag: dict, resamples: int = 9999) -> dict:
    """Text labels for the paper's prose: entries flagged, the seed pattern common to all diagnosed entries, the observed
    count of frozen resamples that omit the substantive seeds (beside the theoretical probability), and the largest
    rounding residual."""
    one = lambda k: {d[k] for d in diag.values()}
    seeds, n, cnt, prob = one("seeds_above_1e-9"), one("n"), one("resamples_without_them"), {round(d["prob_resample_without_them"], 3) for d in diag.values()}
    if max(len(seeds), len(n), len(cnt), len(prob)) != 1:
        raise ValueError("the diagnosed entries differ; the prose summary needs one pattern")
    c = cnt.pop()
    return {"extreme_entries": str(len(paths)), "seeds_nonzero": str(seeds.pop()), "seeds_total": str(n.pop()),
            "resamples_without": str(c), "resamples_total": f"{resamples:,}", "share_resamples": f"{100 * c / resamples:.1f} percent",
            "prob_resamples": f"{100 * prob.pop():.1f} percent", "max_rounding": f"{max(d['max_rounding_residual'] for d in diag.values()):.1e}"}


def _fixed_reference_rows(records: Path, market: str, fam: str) -> dict:
    """The per-seed fixed-reference-term contrasts of report_v2.q2 for one market and family."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from scripts import report_v2 as RP                                        # frozen code
    cr = json.loads((records / "cross" / f"{market}@rho0.2" / (safe(fam) + ".json")).read_text())
    per = [RP._contrast_rows({r: np.asarray(cr["profit_rows"][f"{a}>{r}"]["profit_ref"], dtype=float) for r in RP.FACT}) for a in RP.FACT]
    return {c: np.mean([p[c] for p in per], axis=0) for c in per[0]}


def _f(x, d=4):
    return f"{x:.{d}f}"


def _p(x):
    return "1" if x >= 1 else f"{x:.4f}"


def tables(res: dict) -> dict:
    t = {}
    rows = [f"{n.split('|')[1]} & {_p(v['raw'])} & {_p(v['calibrated'])} & {_p(v['holm_adjusted'])} & {'yes' if v['reject'] else 'no'} \\\\"
            for n, v in res["q1"].items()]
    t["q1_p"] = ("\\begin{tabular}{@{}lrrrl@{}}\\toprule\nFamily & Raw $p$ & Calibrated $p'$ & Holm-adjusted & Direction rejected \\\\\\midrule\n"
                 + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = [f"{m} & {_p(v['raw_gain'])} & {_p(v['raw_eff'])} & {_p(v['calibrated_gain'])} & {_p(v['calibrated_eff'])} & {_p(v['market_value'])} & "
            f"{_p(v['holm_adjusted'])} & {v['decision']} \\\\" for m, v in res["q4"].items()]
    t["q4_p"] = ("\\begin{tabular}{@{}lrrrrrrl@{}}\\toprule\nMarket & Raw $p_{\\mathrm{gain}}$ & Raw $p_{\\mathrm{eff}}$ & $p'_{\\mathrm{gain}}$ & "
                 "$p'_{\\mathrm{eff}}$ & Market $\\max$ & Holm-adjusted & Decision \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    rows = []
    for m in FRESH:
        o, n = res["q4_stability"]["report"][m], res["q4_stability"]["registered_cfg"][m]
        rows.append(f"{m} & {_f(o['gain_diff'])} & {_f(n['gain_diff'])} & {_f(o['gain_diff_lower'])} & {_f(n['gain_diff_lower'])} & "
                    f"{_f(o['eff'])} & {_f(n['eff'])} & {_f(o['eff_lower'])} & {_f(n['eff_lower'])} & {_p(n['holm_adjusted'])} & {o['decision']}/{n['decision']} \\\\")
    t["q4_stability"] = ("\\begin{tabular}{@{}lrrrrrrrrrl@{}}\\toprule\n & \\multicolumn{2}{c}{B3$-$R3 gain} & \\multicolumn{2}{c}{Lower} & "
                         "\\multicolumn{2}{c}{R3 eff.} & \\multicolumn{2}{c}{Lower} & & \\\\\nMarket & report & reg. & report & reg. & report & reg. & "
                         "report & reg. & Holm adj., reg. & Decision \\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
    return t


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for k in ("--report", "--records", "--stability-work", "--out", "--tables"):
        ap.add_argument(k, required=True)
    a = ap.parse_args(argv)
    report = json.loads(Path(a.report).read_text()); records = Path(a.records); work = Path(a.stability_work)
    load_old = lambda m, r, f="D2+H3": json.loads((records / "evaluate" / (safe(f"{m}@rho0.2|{r}|{f}|profit") + ".json")).read_text())
    load_new = lambda m, r, f="D2+H3": json.loads((work / (safe(f"{m}@rho0.2|{r}|{f}|profit") + ".json")).read_text())
    raw = {}
    for f in FAMS:
        st = [np.asarray(load_old(m, "C*", f)["gain"], dtype=float) - np.asarray(load_old(m, "F111", f)["gain"], dtype=float) for m in FRESH]
        raw[f"C*-F111|{f}"] = stratified_two_sided(st, 0.0)
    strata = {f"C*-F111|{f}": [np.asarray(load_old(m, "C*", f)["gain"], dtype=float) - np.asarray(load_old(m, "F111", f)["gain"], dtype=float) for m in FRESH] for f in FAMS}
    cats = {n: v["category"] for n, v in q1_family(strata, KAPPA["Q1"]).items()}
    q1, p1 = q1_audit(report, KAPPA["Q1"], raw, cats); q4, p4 = q4_audit(report, KAPPA["Q4"])
    old, new = q4_table(load_old, KAPPA["Q4"]), q4_table(load_new, KAPPA["Q4"])
    for m in FRESH:                                                            # the recomputation must match the report
        for k in ("gain_diff", "gain_diff_lower", "eff", "eff_lower", "p_gain", "p_eff"):
            if not np.isclose(old[m][k], report["q4"]["markets"][m][k], rtol=0, atol=1e-12):
                p4.append(f"q4 {m} {k}: recomputed {old[m][k]} differs from the report {report['q4']['markets'][m][k]}")
    hits = extreme_intervals(report); diag = {}
    for h in hits:
        parts = h.split("/")
        if parts[:2] == ["q2", "per_market"] and parts[4] == "fixed_reference_term":
            diag[h] = studentization(_fixed_reference_rows(records, parts[3], parts[2])[parts[5]])
    res = {"label": "audit after the report (external review round 5); changes no registered estimate or decision",
           "kappa": KAPPA, "q1": q1, "q4": q4, "problems": p1 + p4,
           "q4_stability": {"report": old, "registered_cfg": new,
                            "decisions_unchanged": all(old[m]["decision"] == new[m]["decision"] for m in FRESH),
                            "max_abs_change": {k: max(abs(old[m][k] - new[m][k]) for m in FRESH) for k in ("gain_diff", "gain_diff_lower", "eff", "eff_lower")}},
           "extreme_intervals": {"limit": 1e3, "paths": hits, "studentization": diag, "labels": labels(hits, diag)}}
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    d = Path(a.tables); d.mkdir(parents=True, exist_ok=True)
    for k, v in tables(res).items():
        (d / f"audit_{k}.tex").write_text(v)
    print(json.dumps({"problems": res["problems"], "extreme": len(hits), "q4_stability_unchanged": res["q4_stability"]["decisions_unchanged"]}, indent=1))
    return 1 if res["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
