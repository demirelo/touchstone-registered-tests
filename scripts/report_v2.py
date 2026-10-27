"""The protocol-v2 report (design draft 7, 6.5, 8.1a, 9.2, 9.3, 9.4). It first runs the read-only verify stage and refuses on
any stale, foreign, or erroneous record; missing cells and unavailable contexts count as missing. Two cell statuses (design
6.5): a missing cell withholds every confirmatory test that uses it ("not decided: missing cell") and makes that part of its
question unanswered; a search-flagged cell (its scheduled doubling check over the threshold) keeps its decision, labelled as
about the prescribed search procedure, and makes the Q3 robustness statement for that rule and family unanswered. Q1 and Q4
are confirmatory (calibrated, Holm with fixed slots) unless the family has no admitted kappa or the draw is nonconfirmatory;
a numerical refusal withholds only the affected test. Q2, Q3, the secondary comparisons, and the doubling diagnostics are
descriptive; every extremum is selected on training data (frozen selection records). Multiplicity is controlled within Q1
and within Q4 only."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from sim.decisions_v2 import ALPHA, MISSING, NO_DECISION, REFUSED, q1_better, q1_efficiency, q1_family, q2_contrasts, q4_markets, w1_class  # noqa: E402
from sim.diagnostic_v2 import decompose  # noqa: E402
from sim.intervals import (NumericalRefusal, bootstrap_pvalue, calibrated, gmin_bounds, stratified_at, stratified_mean,  # noqa: E402
                           studentized_at)
from sim.records_v2 import read  # noqa: E402

FRESH = tuple(f"fresh{i}" for i in range(6))
FACT = tuple(f"F{p}{g}{s}" for p in "01" for g in "01" for s in "01")
PAIRS = (("F111", "C*"),)
FAMS = ("D2+H3", "X7-SC")
CORE = ("F000", "F111", "C*")
WHOLE = ("B3-t", "R3-t", "C*-t")
FLAGGED = "about the prescribed search procedure (search flagged)"
MULTIPLICITY = "Multiplicity is controlled within Q1 and within Q4 only; there is no paper-wide familywise guarantee."
REDUCED = "reduced menu (D2+H3)"
SIDE = {"gross_eff_diff": "eff_attack", "net_eff_diff": "net_eff_attack", "ref_profit_diff": "profit_ref", "audit_spend_diff": "audit_spend_attack",
        "false_refund_focal_diff": "false_refund_focal_attack", "false_refund_others_diff": "false_refund_others_attack",
        "served_share_diff": "served_share_attack"}
REPAIR = ("F000", "F111", "R4", "C*", "C*/S2")
NOMINAL = 0.025
NOMINAL_LABEL = "nominal 95 percent, unadjusted"
NONCONF = "nonconfirmatory (late publication)"


def verify_records(out, catalog, instances, protocol, h4, cuts, h4_excluded) -> dict:
    return RV.verify(Path(out), catalog, catalog, instances, protocol, h4, cuts, h4_excluded)


def _f(x) -> float | None:
    return None if x is None else float(x)


def _interval(x, tail: float = NOMINAL) -> list:
    """A descriptive interval; a numerical refusal withholds it (design 9.2) instead of stopping the report."""
    try:
        return [float(studentized_at(x, "lower", tail)), float(studentized_at(x, "upper", tail))]
    except NumericalRefusal:
        return [None, None]


def _strat(st, tail: float = NOMINAL, strict: bool = False) -> dict:
    try:
        return {"estimate": float(stratified_mean(st)), "interval": [float(stratified_at(st, "lower", tail)), float(stratified_at(st, "upper", tail))]}
    except NumericalRefusal:
        if strict:
            raise
        return {"estimate": None, "interval": [None, None], "status": REFUSED}


def _est(x) -> float | None:
    with np.errstate(over="ignore", invalid="ignore"):
        v = float(np.mean(np.asarray(x, dtype=float)))
    return v if np.isfinite(v) else None


class Records:
    def __init__(self, out: Path, catalog: list[dict], missing: set, flagged: set = frozenset()):
        self.out, self.missing, self.flagged = Path(out), set(missing), set(flagged); self.jobs = {j["id"]: j for j in catalog}

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
    """d = g_C* - g_F111 per seed, pooled over the six fresh markets (design 9.3), two fixed Holm slots."""
    tests, effs, sides, flags = {}, {}, {}, {}
    for a, b in PAIRS:
        for f in FAMS:
            name = f"{b}-{a}|{f}"; st, ef, sd, miss = [], [], {k: [] for k in SIDE}, False
            for m in FRESH:
                ra, rb = R.get(m, a, f), R.get(m, b, f)
                if ra is None or rb is None:
                    miss = True; break
                with np.errstate(over="ignore", invalid="ignore"):
                    st.append(np.asarray(rb["gain"], dtype=float) - np.asarray(ra["gain"], dtype=float))
                ef.append((np.asarray(ra["eff_attack"]), np.asarray(rb["eff_attack"])))
                for k, fld in SIDE.items():
                    sd[k].append(np.asarray(ra[fld], dtype=float) - np.asarray(rb[fld], dtype=float))
            tests[name] = None if miss else st; effs[name] = ef; sides[name] = sd
            flags[name] = any(RV.cell_id(f"{m}@rho0.2", r, f, "profit") in R.flagged for m in FRESH for r in (a, b))
    fam = q1_family(tests, kappa); tail = kappa * ALPHA / (2 * len(tests)) if kappa else NOMINAL
    out = {"heading": NONCONF if not confirmatory else "Q1: Holm on calibrated two-sided p-values (two slots), pooled over the six fresh markets",
           "tests": {}, "descriptive": {}}
    for name, st in tests.items():
        cat = fam[name]["category"]; t = {"p": _f(fam[name]["p"]), "reject": fam[name]["reject"], "category": cat,
                                          "search": FLAGGED if flags[name] and st is not None else None}
        if st is not None:
            try:
                t.update(_strat(st, tail, strict=True), interval_label=f"calibrated simultaneous, one-sided tails {tail:.6g}" if kappa else NOMINAL_LABEL)
                favoured_r3 = cat.startswith("R3") or (cat not in ("C* materially lower",) and float(stratified_mean(st)) >= 0)
                eff = [(x - y) if favoured_r3 else (y - x) for x, y in effs[name]]
                t["efficiency"] = q1_efficiency(eff); t["better"] = q1_better(cat, t["efficiency"])
                t["side"] = {k: float(stratified_mean(v)) for k, v in sides[name].items()}
            except NumericalRefusal:
                t.update(category=REFUSED, p=None, reject=None, estimate=None, interval=None, interval_label=NOMINAL_LABEL)
        else:
            t.update(estimate=None, interval=None, interval_label=NOMINAL_LABEL)
        out["tests"][name] = t
    for m in FRESH + ("headline",):
        d = {}
        for a, b in PAIRS:
            for f in FAMS:
                ra, rb = R.get(m, a, f), R.get(m, b, f)
                if ra is not None and rb is not None:
                    with np.errstate(over="ignore", invalid="ignore"):
                        x = np.asarray(rb["gain"], dtype=float) - np.asarray(ra["gain"], dtype=float)
                    d[f"{b}-{a}|{f}"] = {"estimate": _est(x), "interval": _interval(x)}
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
        try:
            p_g, p_e = bootstrap_pvalue(d, 0.10, "lower"), bootstrap_pvalue(eff, 0.90, "lower")
            lo_g, lo_e = studentized_at(d, "lower", tail), studentized_at(eff, "lower", tail)
        except NumericalRefusal:
            pa.append(None); pb.append(None); markets[m] = "not decided: numerical refusal"; continue
        pa.append(p_g); pb.append(p_e)
        markets[m] = {"gain_diff": float(d.mean()), "gain_diff_lower": float(lo_g), "eff": float(eff.mean()),
                      "eff_lower": float(lo_e), "p_gain": float(pa[-1]), "p_eff": float(pb[-1]),
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


def _contrasts(arr: dict) -> dict:
    return _contrast_rows(arr)


def _contrast_rows(arr: dict) -> dict:
    n = len(next(iter(arr.values()))); rows = [q2_contrasts({r: arr[r][s] for r in FACT}) for s in range(n)]
    return {k: np.asarray([row[k] for row in rows]) for k in rows[0]}


def q2(R: Records):
    """Searched and fixed-attack contrasts pooled over the fresh markets, per market and headline estimates, the fixed-attack
    decomposition into attacker-profit and reference terms with efficiency (design 6.6), and the training-selected bank
    envelope (the frozen envelope choice, evaluated)."""
    out = {"searched": {}, "fixed": {}, "fixed_attack_term": {}, "fixed_reference_term": {}, "fixed_eff": {}, "per_market": {}, "envelope": {},
           "label": NOMINAL_LABEL}
    for f in FAMS:
        searched, fixed, at, rt, fe, env, per = {}, {}, {}, {}, {}, {}, {}
        for m in FRESH + ("headline",):
            recs = {r: R.get(m, r, f) for r in FACT}; cr = R.cross(m, f)
            if any(v is None for v in recs.values()) or cr is None:
                return "unanswered"
            s_rows = _contrast_rows({r: np.asarray(recs[r]["gain"]) for r in FACT})
            per[m] = {k: _est(v) for k, v in s_rows.items()}
            if m == "headline":
                continue
            for k, v in s_rows.items():
                searched.setdefault(k, []).append(v)
            rows, prof = cr["per_seed"], cr["profit_rows"]
            for store, src in ((fixed, lambda a, r: rows[f"{a}>{r}"]), (at, lambda a, r: prof[f"{a}>{r}"]["profit_attack"]),
                               (rt, lambda a, r: prof[f"{a}>{r}"]["profit_ref"]), (fe, lambda a, r: prof[f"{a}>{r}"]["eff_attack"])):
                per_attack = [_contrast_rows({r: np.asarray(src(a, r)) for r in FACT}) for a in FACT]
                for k in per_attack[0]:
                    store.setdefault(k, []).append(np.mean([pa[k] for pa in per_attack], axis=0))
            env[m] = {r: {"attack": cr["envelope"][r], "estimate": float(np.mean(rows[f"{cr['envelope'][r]}>{r}"])),
                          "interval": _interval(np.asarray(rows[f"{cr['envelope'][r]}>{r}"]))} for r in FACT}
        out["searched"][f] = {k: _strat(v) for k, v in searched.items()}
        out["fixed"][f] = {k: _strat(v) for k, v in fixed.items()}
        out["fixed_attack_term"][f] = {k: _strat(v) for k, v in at.items()}
        out["fixed_reference_term"][f] = {k: _strat(v) for k, v in rt.items()}
        out["fixed_eff"][f] = {k: _strat(v) for k, v in fe.items()}
        out["per_market"][f] = per; out["envelope"][f] = env
    return out


def q3(R: Records, h4_loaded: bool):
    fams = ("D2+H3", "X7-SC", "X5-AG/v2") + (("H4",) if h4_loaded else ())
    out = {"envelope": {}, "welfare": {}, "welfare_selected": {}, "coalition": {}, "diagnostic": {}, "robustness": {}, "label": NOMINAL_LABEL}
    for r in CORE:
        out["envelope"][r] = {}; out["robustness"][r] = {}
        for f in fams:
            hit = any(RV.cell_id(f"{m}@rho0.2", r, f, "profit") in R.flagged for m in FRESH + ("headline",))
            out["robustness"][r][f] = "unanswered (search flagged)" if hit else "answered"
        for m in FRESH + ("headline",):
            env = R.aux(f"envelope/{m}@rho0.2/{r}")
            if env is None or any(R.get(m, r, f) is None for f in fams):
                out["envelope"][r][m] = "unanswered: missing cell"; continue
            rec = R.get(m, r, env["choice"])
            if rec is None:
                out["envelope"][r][m] = "unanswered: missing cell"; continue
            g = np.asarray(rec["gain"]); out["envelope"][r][m] = {"family": env["choice"], "estimate": _est(g), "interval": _interval(g)}
    for r in CORE:
        out["welfare"][r] = {}; out["welfare_selected"][r] = {}
        for f in FAMS:
            out["welfare"][r][f] = {}
            for obj in ("W0", "W1"):
                rec = R.get("headline", r, f, obj)
                if rec is None:
                    out["welfare"][r][f][obj] = "unanswered: missing cell"; continue
                if rec.get("no_feasible_candidate"):
                    out["welfare"][r][f][obj] = "no feasible candidate found"; continue
                eff = np.asarray(rec["eff"]); cell = {"efficiency": float(eff.mean()), "interval": _interval(eff)}
                if obj == "W0":
                    pr = R.get("headline", r, "D2+H3")
                    if pr is None:
                        out["welfare"][r][f][obj] = "unanswered: missing cell"; continue
                    N = R.jobs[RV.cell_id("headline@rho0.2", r, f, obj)]["mkt"]["cfg"].N
                    gain = np.asarray(rec["normalized"]) - np.asarray(pr["profit_ref"]) / (np.asarray(pr["sstar"]) / N)
                else:
                    gain = np.asarray(rec["constraint"]); ci = _interval(gain); cell["constraint_interval"] = ci; cell["w1_class"] = w1_class(*ci)
                cell.update(attacker_gain=float(gain.mean()), attacker_gain_interval=_interval(gain)); out["welfare"][r][f][obj] = cell
        for obj in ("W0", "W1"):
            sel = R.aux(f"welfare_select/headline@rho0.2/{r}/{obj}") or {}
            if sel.get("family") is None:
                out["welfare_selected"][r][obj] = {"family": None, "status": sel.get("status", "unanswered: missing selection")}
            else:
                other = "X7-SC" if sel["family"] == "D2+H3" else "D2+H3"
                out["welfare_selected"][r][obj] = {"family": sel["family"], "other_family": other, "result": out["welfare"][r][sel["family"]][obj],
                                                   "other_result": out["welfare"][r][other][obj]}
        out["coalition"][r] = {}
        groups = [(c, sch, "X6-SE/v2") for c in (2, 5) for sch in ("synchronised", "staggered")] + [(2, "roles", "X8-DB")]
        for c, sch, fam in groups:
            tot, mn = R.get("headline", r, fam, "total", c, sch), R.get("headline", r, fam, "min", c, sch)
            if tot is None or mn is None:
                out["coalition"][r][f"c{c}_{sch}"] = "unanswered: missing cell"; continue
            out["coalition"][r][f"c{c}_{sch}"] = {"G_tot": {"estimate": float(tot["total"])},
                                                  "G_min": {"estimate": float(mn["min"]), "bounds": [float(x) for x in gmin_bounds([np.asarray(v) for v in mn["member_gain"]], 0.05)]}}
        dg = R.get("headline", r, "HR1", "diagnostic")
        out["diagnostic"][r] = "unanswered: missing cell" if dg is None else {"replace_at": dg["replace_at"], "bins": dg["bins"]}
    out["independent"] = ("not run (H4 excluded); the independently authored part of Q3 is unanswered" if not h4_loaded else
                          {r: {m: (float(np.mean(R.get(m, r, "H4")["gain"])) if R.get(m, r, "H4") is not None else "not run (cut or missing)")
                               for m in FRESH + ("headline",)} for r in CORE})
    return out


def secondary(R: Records) -> dict:
    out = {"whole_systems": {}, "repair_rho1": {}, "label": NOMINAL_LABEL}
    for r in WHOLE:
        for m in FRESH + ("headline",):
            for f in FAMS:
                rec = R.get(m, r, f)
                if rec is not None:
                    g = np.asarray(rec["gain"]); out["whole_systems"].setdefault(r, {}).setdefault(m, {})[f] = {"estimate": float(g.mean()), "interval": _interval(g),
                                                                                                            **({"menu": REDUCED} if m != "headline" else {})}
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
    missing, no_doubling = set(), set()
    for c in rep.get("contexts", {}).values():
        missing |= set(c.get("missing", [])); no_doubling |= set(c.get("missing_doubling", []))
    R = Records(out, catalog, missing, _flagged(out, catalog)); conf = bool((instances or {}).get("confirmatory")); kappa = protocol.get("kappa") or {}
    r = {"confirmatory": conf, "q1": q1(R, kappa.get("Q1"), conf), "q2": q2(R), "q3": q3(R, bool(h4.get("loaded"))), "q4": q4(R, kappa.get("Q4"), conf)}
    r["secondary"] = secondary(R); r["doubling"] = doubling(R); r["doubling_missing"] = sorted(no_doubling)
    for j in catalog:
        if read(RV.eval_path(R.out, j["id"])) is None:
            R.missing.add(j["id"])
    r["missing"] = sorted(R.missing); r["search_flagged"] = sorted(R.flagged); r["multiplicity"] = MULTIPLICITY
    r["unanswered"] = [q.upper() for q in ("q1", "q2", "q3") if _unanswered(r[q])] + (["Q4"] if r["q4"] == "unanswered" else [])
    return json.loads(json.dumps(r, default=float))


def _flagged(out, catalog: list[dict]) -> set:
    """Cells whose scheduled doubling check exceeded the threshold (design 6.5 'search-flagged')."""
    by = {RV._safe(j["id"]): j["id"] for j in catalog}; d = Path(out) / "doubling"; got = set()
    for p in sorted(d.glob("*.json")) if d.exists() else []:
        rec = read(p)
        if rec is not None and rec.get("incomplete") is True and p.stem in by:
            got.add(by[p.stem])
    return got


def _unanswered(q) -> bool:
    """A question with any unanswered or undecided part (design 8.1a)."""
    if q == "unanswered":
        return True
    text = json.dumps(q, default=float)
    return any(k in text for k in ("unanswered", MISSING, REFUSED, "not decided"))


def _iv(x: dict) -> str:
    if x.get("estimate") is None or None in (x.get("interval") or [None]):
        return f"{x.get('estimate') if x.get('estimate') is not None else '-'} (interval withheld: numerical refusal)"
    return f"{x['estimate']:.4f} [{x['interval'][0]:.4f}, {x['interval'][1]:.4f}]"


def markdown(r: dict) -> str:
    L = ["# Protocol v2 report", ""]
    if not r["confirmatory"]:
        L += [f"All Q1 and Q4 results are descriptive: {NONCONF}.", ""]
    L += [r.get("multiplicity", MULTIPLICITY), ""]
    L.append("## Q1 comparator (d = gain of C* minus gain of F111)")
    if r["q1"] == "unanswered":
        L.append("unanswered: a required cell is missing")
    else:
        L += [f"_{r['q1']['heading']}_", "| test | estimate [interval] | interval kind | category | efficiency | better | search |", "|---|---|---|---|---|---|---|"]
        for k, t in r["q1"]["tests"].items():
            iv = _iv(t) if t.get("estimate") is not None else "not available"
            L.append(f"| {k} | {iv} | {t['interval_label']} | {t['category']} | {t.get('efficiency', '-')} | {t.get('better') or '-'} | {t.get('search') or '-'} |")
            if t.get("side"):
                L.append(f"- {k} side fields (descriptive, F111 minus C*): " + "; ".join(f"{n} {v:.4f}" for n, v in t["side"].items()))
        for m, d in r["q1"]["descriptive"].items():
            L += [f"- {m} (descriptive, {NOMINAL_LABEL}): " + "; ".join(f"{k} {_iv(v) if isinstance(v, dict) else v}" for k, v in d.items())]
    L += ["", "## Q4 replication", f"_{r['q4']['heading']}_", r["q4"]["wording"] + (f"; failing: {', '.join(r['q4']['failing'])}" if r["q4"].get("failing") else "")]
    for m, v in r["q4"]["markets"].items():
        L.append(f"- {m}: {v}" if isinstance(v, str) else
                 f"- {m}: gain difference {v['gain_diff']:.4f} (lower {v['gain_diff_lower']:.4f}), efficiency {v['eff']:.4f} (lower {v['eff_lower']:.4f}); {v['bound_label']}")
    L += ["", "## Q2 attribution (descriptive)"]
    if r["q2"] == "unanswered":
        L.append("unanswered: a required cell or cross record is missing")
    else:
        for kind in ("searched", "fixed", "fixed_attack_term", "fixed_reference_term", "fixed_eff"):
            for f, cs in r["q2"][kind].items():
                L.append(f"- {kind}, {f}: " + "; ".join(f"{k} {_iv(v)}" for k, v in cs.items()))
        for f, ms in r["q2"]["per_market"].items():
            L.append(f"- searched per market, {f}: " + "; ".join(f"{m}: " + ", ".join(f"{k} {v:.4f}" for k, v in d.items()) for m, d in ms.items()))
        for f, ms in r["q2"]["envelope"].items():
            L.append(f"- bank envelope (training-selected), {f}: " + "; ".join(f"{m}: " + ", ".join(f"{k} {v['attack']} {_iv(v)}" for k, v in d.items())
                                                                               for m, d in ms.items()))
    L += ["", "## Q3 attack strength (descriptive)"]
    q3 = r["q3"]
    if q3 == "unanswered":
        L.append("unanswered: a required cell is missing")
    else:
        for rule, ms in q3["envelope"].items():
            L.append(f"- envelope {rule}: " + "; ".join(f"{m} {v['family']} {_iv(v)}" if isinstance(v, dict) else f"{m} {v}" for m, v in ms.items()))
        for rule, fs in q3["robustness"].items():
            L.append(f"- robustness {rule}: " + ", ".join(f"{f} {v}" for f, v in fs.items()))
        for rule, fs in q3["welfare"].items():
            for f, objs in fs.items():
                for obj, v in objs.items():
                    if isinstance(v, str):
                        L.append(f"- welfare {rule} {f} {obj}: {v}"); continue
                    g = v["attacker_gain_interval"]; c = v.get("constraint_interval")
                    L.append(f"- welfare {rule} {f} {obj}: efficiency {v['efficiency']:.4f} [{v['interval'][0]:.4f}, {v['interval'][1]:.4f}], "
                             f"attacker gain {v['attacker_gain']:.4f} [{g[0]:.4f}, {g[1]:.4f}]" + (f", W1 constraint [{c[0]:.4f}, {c[1]:.4f}], {v['w1_class']}" if c else ""))
        for rule, objs in q3["welfare_selected"].items():
            for obj, v in objs.items():
                L.append(f"- welfare selected on training, {rule} {obj}: " + (v["status"] if v.get("family") is None else f"{v['family']} (other: {v['other_family']})"))
        for rule, gs in q3["coalition"].items():
            L.append(f"- coalition {rule}: " + "; ".join(f"{g} G_tot {v['G_tot']['estimate']:.4f}, G_min {v['G_min']['estimate']:.4f} "
                                                        f"[{v['G_min']['bounds'][0]:.4f}, {v['G_min']['bounds'][1]:.4f}]" if isinstance(v, dict) else f"{g} {v}"
                                                        for g, v in gs.items()))
        for rule, v in q3["diagnostic"].items():
            L.append(f"- honest replacement {rule}: " + (v if isinstance(v, str) else
                     "; ".join(f"age {b['age'][0]}-{b['age'][1]} audited {b['audited_share']:.3f}" for b in v["bins"])))
        L.append("- independently authored family (H4): " + (q3["independent"] if isinstance(q3["independent"], str) else
                 "; ".join(f"{rule}: " + ", ".join(f"{m} {v:.4f}" if not isinstance(v, str) else f"{m} {v}" for m, v in ms.items())
                           for rule, ms in q3["independent"].items())))
    L += ["", f"## Secondary (descriptive, {NOMINAL_LABEL})"]
    for part in ("whole_systems", "repair_rho1"):
        for rule, d in r["secondary"][part].items():
            L.append(f"- {part} {rule}: " + "; ".join(f"{k}: " + ", ".join(f"{f} {_iv(x)}" + (f" {x['menu']}" if x.get("menu") else "") for f, x in v.items())
                                                 if isinstance(v, dict) and "estimate" not in v else f"{k} {_iv(v)}" for k, v in d.items()))
    L += ["", "## Doubling diagnostics (labels beside the estimates; they change no decision)"]
    L += [f"- {rid}: " + ", ".join(f"{k} {v}" for k, v in sorted(d.items())) for rid, d in r["doubling"].items()]
    L += [f"- no doubling record: {rid}" for rid in r.get("doubling_missing", [])]
    L += ["", "## Missing cells", ", ".join(r["missing"]) or "none", "", "## Search-flagged cells", ", ".join(r.get("search_flagged", [])) or "none", ""]
    return "\n".join(L)


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
    d = Path(report_dir); out = _diff(r, json.loads((d / "report.json").read_text()))
    if (d / "report.md").read_text() != markdown(r):
        out.append("report.md differs from the report rebuilt from the records")
    return out


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
