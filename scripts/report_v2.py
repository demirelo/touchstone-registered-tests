"""The protocol-v2 report (design 9.2, 9.3; operations plan Task 9). It first runs the read-only verify stage and refuses on
any stale, foreign, or erroneous record; missing cells and unavailable contexts count as missing. Each question reads only
its own cells, and a missing cell makes that question unanswered (Q4: that market not decided) while the others stay
answered. Q1 and Q4 are confirmatory (calibrated, Holm), unless the family has no admitted kappa or the draw is
nonconfirmatory; Q2, Q3, the secondary comparisons, and the doubling diagnostics are descriptive. Doubling labels are
reported beside the estimates and never change a decision (design 6.4)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from sim.decisions_v2 import ALPHA, NO_DECISION, q1_family, q2_contrasts, q4_markets  # noqa: E402
from sim.intervals import bootstrap_pvalue, calibrated, gmin_bounds, stratified_at, stratified_mean, studentized_at  # noqa: E402
from sim.records_v2 import read  # noqa: E402

FRESH = tuple(f"fresh{i}" for i in range(6))
FACT = tuple(f"F{p}{g}{s}" for p in "01" for g in "01" for s in "01")
PAIRS = (("F111", "C*"), ("R4", "C*/S2"))
FAMS = ("D2+H3", "X7-SC")
CORE = ("F000", "F111", "C*", "R4")
WHOLE = ("B3-t", "R3-t", "R4-t", "C*-t")
REPAIR = ("F000", "F111", "R4", "C*", "C*/S2")
NOMINAL = 0.025
NOMINAL_LABEL = "nominal 95 percent, unadjusted"
NONCONF = "nonconfirmatory (late publication)"


def verify_records(out, catalog, instances, protocol, h4, cuts, h4_excluded) -> dict:
    return RV.verify(Path(out), catalog, catalog, instances, protocol, h4, cuts, h4_excluded)


def _f(x) -> float | None:
    return None if x is None else float(x)


def _interval(x, tail: float = NOMINAL) -> list[float]:
    return [float(studentized_at(x, "lower", tail)), float(studentized_at(x, "upper", tail))]


def _strat(st, tail: float = NOMINAL) -> dict:
    return {"estimate": float(stratified_mean(st)), "interval": [float(stratified_at(st, "lower", tail)), float(stratified_at(st, "upper", tail))]}


class Records:
    def __init__(self, out: Path, catalog: list[dict], missing: set):
        self.out, self.missing = Path(out), set(missing); self.jobs = {j["id"]: j for j in catalog}

    def get(self, market: str, rule: str, family: str, objective: str = "profit", c=None, schedule=None, rho: str = "rho0.2"):
        rid = RV.cell_id(f"{market}@{rho}", rule, family, objective, c, schedule)
        if rid in self.missing:
            return None
        rec = read(RV.eval_path(self.out, rid))
        if rec is None:
            self.missing.add(rid)
        return rec

    def aux(self, rid: str):
        return read(RV.path_of(self.out, rid))

    def cross(self, market: str, family: str):
        return read(self.out / "cross" / f"{market}@rho0.2" / (RV._safe(family) + ".json"))


def q1(R: Records, kappa, confirmatory: bool):
    tests = {}
    for a, b in PAIRS:
        for f in FAMS:
            st = []
            for m in FRESH:
                ra, rb = R.get(m, a, f), R.get(m, b, f)
                if ra is None or rb is None:
                    return "unanswered"
                st.append(np.asarray(ra["gain"]) - np.asarray(rb["gain"]))
            tests[f"{a}-{b}|{f}"] = st
    fam = q1_family(tests, kappa); tail = kappa * ALPHA / (2 * len(tests)) if kappa else NOMINAL
    out = {"heading": NONCONF if not confirmatory else "Q1: Holm on calibrated two-sided p-values, pooled over the six fresh markets", "tests": {}, "descriptive": {}}
    for name, st in tests.items():
        out["tests"][name] = {**_strat(st, tail), "interval_label": f"calibrated simultaneous, one-sided tails {tail:.6g}" if kappa else NOMINAL_LABEL,
                              "p": _f(fam[name]["p"]), "reject": fam[name]["reject"], "category": fam[name]["category"]}
    for m in FRESH + ("headline",):
        d = {}
        for a, b in PAIRS:
            for f in FAMS:
                ra, rb = R.get(m, a, f), R.get(m, b, f)
                if ra is not None and rb is not None:
                    x = np.asarray(ra["gain"]) - np.asarray(rb["gain"]); d[f"{a}-{b}|{f}"] = {"estimate": float(x.mean()), "interval": _interval(x)}
        out["descriptive"][m] = d
    return out


def q4_decide(pa: list, pb: list, kappa) -> dict:
    """Holm over all six market slots (design 9.3): a market with a missing cell enters with p = 1 and is not decided."""
    fa, fb = [1.0 if p is None else p for p in pa], [1.0 if p is None else p for p in pb]
    res = dict(q4_markets(fa, fb, kappa)); res["undecided"] = [i for i, p in enumerate(pa) if p is None]
    return res


def q4(R: Records, kappa, confirmatory: bool) -> dict:
    pa, pb, markets = [], [], {}; tail = kappa * ALPHA / len(FRESH) if kappa else NOMINAL
    for m in FRESH:
        f0, f1 = R.get(m, "F000", "D2+H3"), R.get(m, "F111", "D2+H3")
        if f0 is None or f1 is None:
            pa.append(None); pb.append(None); markets[m] = "not decided"; continue
        d = np.asarray(f0["gain"]) - np.asarray(f1["gain"]); eff = np.asarray(f1["eff_attack"])
        pa.append(bootstrap_pvalue(d, 0.10, "lower")); pb.append(bootstrap_pvalue(eff, 0.90, "lower"))
        markets[m] = {"gain_diff": float(d.mean()), "gain_diff_lower": float(studentized_at(d, "lower", tail)), "eff": float(eff.mean()),
                      "eff_lower": float(studentized_at(eff, "lower", tail)), "p_gain": float(pa[-1]), "p_eff": float(pb[-1]),
                      "bound_label": f"calibrated one-sided, tail {tail:.6g}" if kappa else NOMINAL_LABEL}
    dec = q4_decide(pa, pb, kappa); undecided = [FRESH[i] for i in dec["undecided"]]
    out = {"heading": NONCONF if not confirmatory else "Q4: intersection-union per market, Holm over six markets", "markets": markets, "undecided": undecided,
           "decided": bool(dec["decided"])}
    if not dec["decided"]:
        out.update(k=None, passing=[], failing=[], wording=NO_DECISION); return out
    passing = [m for m, ok in zip(FRESH, dec["pass"]) if ok and m not in undecided]
    failing = [m for m, ok in zip(FRESH, dec["pass"]) if not ok and m not in undecided]
    wording = f"replicated on {len(passing)} of 6 sampled markets" + ("; generalisation not established" if undecided else "")
    out.update(k=len(passing), passing=passing, failing=failing, p=[float(p) for p in dec["p"]], wording=wording)
    return out


def _contrast_rows(arr: dict) -> dict:
    n = len(next(iter(arr.values()))); rows = [q2_contrasts({r: arr[r][s] for r in FACT}) for s in range(n)]
    return {k: np.asarray([row[k] for row in rows]) for k in rows[0]}


def q2(R: Records):
    out = {"searched": {}, "fixed": {}, "envelope": {}, "label": NOMINAL_LABEL}
    for f in FAMS:
        searched, fixed, env = {}, {}, {}
        for m in FRESH:
            recs = {r: R.get(m, r, f) for r in FACT}; cr = R.cross(m, f)
            if any(v is None for v in recs.values()) or cr is None:
                return "unanswered"
            for k, v in _contrast_rows({r: np.asarray(recs[r]["gain"]) for r in FACT}).items():
                searched.setdefault(k, []).append(v)
            rows = cr["per_seed"]; per_attack = [_contrast_rows({r: np.asarray(rows[f"{a}>{r}"]) for r in FACT}) for a in FACT]
            for k in per_attack[0]:
                fixed.setdefault(k, []).append(np.mean([pa[k] for pa in per_attack], axis=0))
            env[m] = {r: float(max(np.mean(rows[f"{a}>{r}"]) for a in FACT)) for r in FACT}
        out["searched"][f] = {k: _strat(v) for k, v in searched.items()}
        out["fixed"][f] = {k: _strat(v) for k, v in fixed.items()}
        out["envelope"][f] = env
    return out


def q3(R: Records, h4_loaded: bool):
    fams = ("D2+H3", "X7-SC", "X5-AG/v2") + (("H4",) if h4_loaded else ())
    out = {"envelope": {}, "welfare": {}, "coalition": {}, "label": NOMINAL_LABEL}
    for r in CORE:
        out["envelope"][r] = {}
        for m in FRESH + ("headline",):
            env = R.aux(f"envelope/{m}@rho0.2/{r}")
            if env is None or any(R.get(m, r, f) is None for f in fams):
                return "unanswered"
            rec = R.get(m, r, env["choice"])
            if rec is None:
                return "unanswered"
            g = np.asarray(rec["gain"]); out["envelope"][r][m] = {"family": env["choice"], "estimate": float(g.mean()), "interval": _interval(g)}
    for r in CORE:
        out["welfare"][r] = {}
        for f in FAMS:
            out["welfare"][r][f] = {}
            for obj in ("W0", "W1"):
                rec = R.get("headline", r, f, obj)
                if rec is None:
                    return "unanswered"
                if rec.get("no_feasible_candidate"):
                    out["welfare"][r][f][obj] = "no feasible candidate found"; continue
                eff = np.asarray(rec["eff"]); cell = {"efficiency": float(eff.mean()), "interval": _interval(eff)}
                if obj == "W0":
                    pr = R.get("headline", r, "D2+H3")
                    if pr is None:
                        return "unanswered"
                    N = R.jobs[RV.cell_id("headline@rho0.2", r, f, obj)]["mkt"]["cfg"].N
                    gain = np.asarray(rec["normalized"]) - np.asarray(pr["profit_ref"]) / (np.asarray(pr["sstar"]) / N)
                else:
                    gain = np.asarray(rec["constraint"]); cell["constraint_interval"] = _interval(gain)
                cell.update(attacker_gain=float(gain.mean()), attacker_gain_interval=_interval(gain)); out["welfare"][r][f][obj] = cell
        out["coalition"][r] = {}
        for c in (2, 5):
            for sch in ("synchronised", "staggered"):
                tot, mn = R.get("headline", r, "X6-SE/v2", "total", c, sch), R.get("headline", r, "X6-SE/v2", "min", c, sch)
                if tot is None or mn is None:
                    return "unanswered"
                out["coalition"][r][f"c{c}_{sch}"] = {"G_tot": {"estimate": float(tot["total"])},
                                                      "G_min": {"estimate": float(mn["min"]), "bounds": [float(x) for x in gmin_bounds([np.asarray(v) for v in mn["member_gain"]], 0.05)]}}
    out["independent"] = "unanswered" if not h4_loaded else {r: {m: float(np.mean(R.get(m, r, "H4")["gain"])) for m in FRESH + ("headline",)} for r in CORE}
    return out


def secondary(R: Records) -> dict:
    out = {"whole_systems": {}, "repair_rho1": {}, "label": NOMINAL_LABEL}
    for r in WHOLE:
        for m in FRESH:
            for f in FAMS:
                rec = R.get(m, r, f)
                if rec is not None:
                    g = np.asarray(rec["gain"]); out["whole_systems"].setdefault(r, {}).setdefault(m, {})[f] = {"estimate": float(g.mean()), "interval": _interval(g)}
    for r in REPAIR:
        for f in ("D2", "D2+H3", "X7-SC"):
            rec = R.get("headline", r, f, rho="rho1")
            if rec is not None:
                g = np.asarray(rec["gain"]); out["repair_rho1"].setdefault(r, {})[f] = {"estimate": float(g.mean()), "interval": _interval(g)}
    return out


def doubling(R: Records) -> dict:
    by = {RV._safe(rid): rid for rid in R.jobs}; out = {}
    for p in sorted((R.out / "doubling").glob("*.json")) if (R.out / "doubling").exists() else []:
        rec = read(p)
        if rec is not None and p.stem in by:
            out[by[p.stem]] = {k: v for k, v in rec.items() if k not in ("provenance", "upstream", "stage", "id")}
    return out


def build(out, protocol: dict, instances: dict, h4: dict, catalog: list[dict], cuts: int | None = None) -> dict:
    h4 = h4 or {}; cuts = int(protocol.get("cuts", 0) if cuts is None else cuts)
    rep = verify_records(out, catalog, instances, protocol, h4, cuts, not h4.get("loaded"))
    if not rep.get("ok"):
        raise SystemExit(f"verify found stale, foreign, or erroneous records; the report is refused: {json.dumps(rep)[:600]}")
    missing = set()
    for c in rep.get("contexts", {}).values():
        missing |= set(c.get("missing", []))
    R = Records(out, catalog, missing); conf = bool((instances or {}).get("confirmatory")); kappa = protocol.get("kappa") or {}
    r = {"confirmatory": conf, "q1": q1(R, kappa.get("Q1"), conf), "q2": q2(R), "q3": q3(R, bool(h4.get("loaded"))), "q4": q4(R, kappa.get("Q4"), conf)}
    r["secondary"] = secondary(R); r["doubling"] = doubling(R)
    for j in catalog:
        if read(RV.eval_path(R.out, j["id"])) is None:
            R.missing.add(j["id"])
    r["missing"] = sorted(R.missing); r["unanswered"] = [q.upper() for q in ("q1", "q2", "q3", "q4") if r[q] == "unanswered"]
    return json.loads(json.dumps(r, default=float))


def markdown(r: dict) -> str:
    lines = ["# Protocol v2 report", ""]
    if not r["confirmatory"]:
        lines += [f"All Q1 and Q4 results are descriptive: {NONCONF}.", ""]
    for q, title in (("q1", "Q1 comparator"), ("q4", "Q4 replication"), ("q2", "Q2 attribution (descriptive)"), ("q3", "Q3 attack strength (descriptive)")):
        lines.append(f"## {title}")
        v = r[q]
        if v == "unanswered":
            lines += ["unanswered: a required cell is missing", ""]; continue
        if q in ("q1", "q4"):
            lines.append(f"_{v['heading']}_")
        if q == "q1":
            lines += ["| test | estimate | interval | category |", "|---|---|---|---|"]
            lines += [f"| {k} | {t['estimate']:.4f} | [{t['interval'][0]:.4f}, {t['interval'][1]:.4f}] ({t['interval_label']}) | {t['category']} |" for k, t in v["tests"].items()]
        elif q == "q4":
            lines.append(v["wording"] + (f"; failing: {', '.join(v['failing'])}" if v.get("failing") else ""))
        else:
            lines.append(f"intervals: {v['label']}")
        lines.append("")
    lines += ["## Missing cells", ", ".join(r["missing"]) or "none", ""]
    return "\n".join(lines)


def save(r: dict, report_dir) -> None:
    d = Path(report_dir); d.mkdir(parents=True, exist_ok=True)
    (d / "report.json").write_text(json.dumps(r, indent=1, sort_keys=True)); (d / "report.md").write_text(markdown(r))


def _diff(a, b, path="") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        return [x for k in sorted(set(a) | set(b)) for x in (_diff(a.get(k), b.get(k), f"{path}/{k}") if k in a and k in b else [f"{path}/{k}: present on one side"])]
    if isinstance(a, list) and isinstance(b, list):
        return [f"{path}: lengths differ"] if len(a) != len(b) else [x for i, (u, v) in enumerate(zip(a, b)) for x in _diff(u, v, f"{path}[{i}]")]
    if isinstance(a, float) or isinstance(b, float):
        try:
            return [] if abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(a))) else [f"{path}: {a} != {b}"]
        except (TypeError, ValueError):
            return [f"{path}: {a} != {b}"]
    return [] if a == b else [f"{path}: {a} != {b}"]


def check(r: dict, report_dir) -> list[str]:
    return _diff(r, json.loads((Path(report_dir) / "report.json").read_text()))


def main(argv=None) -> int:
    import yaml
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--protocol", required=True); ap.add_argument("--instances", required=True)
    ap.add_argument("--h4", required=True); ap.add_argument("--report", required=True); ap.add_argument("--check", action="store_true")
    ap.add_argument("--params", default=str(RV.ROOT / "experiments" / "v2" / "params.json")); ap.add_argument("--commit", default=None)
    ap.add_argument("--markets", default=None); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    protocol = yaml.safe_load(Path(a.protocol).read_text()); inst = json.loads(Path(a.instances).read_text()); h4 = json.loads(Path(a.h4).read_text())
    from sim.records import cfg_from_dict
    cfgs = {k: cfg_from_dict(v["calibrated_cfg"]) for k, v in inst.get("markets", {}).items()}
    h4job = {"dir": None, "sha": h4["bundle_sha256"]} if h4.get("loaded") else None
    markets = (a.markets or ",".join(RV.MAN.doc()["markets"])).split(",")
    catalog = RV.build_jobs(markets, inst["root"], False, a.smoke, json.loads(Path(a.params).read_text()), int(protocol.get("cuts", 0)), h4job,
                            not h4.get("loaded"), cfgs, a.commit or RV.git_commit(), inst["salt_sha256"])
    r = build(a.out, protocol, inst, h4, catalog)
    if a.check:
        diffs = check(r, a.report)
        print("\n".join(diffs[:50]) or "ok")
        return 1 if diffs else 0
    save(r, a.report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
