"""The churn block of the post-hoc analysis (docs/revision/churn/churn-plan.md, draft 6, sections 2, 4, 5 and 6).

g_p(r, m) = mean over the evaluation seeds of the normalised gain of the D2+H3 winner selected under churn p, against
the rule's frozen truthful reference played under the same churn; p = 0 is the registered no-churn record on the same
seeds. Rules: R3 = F111, C*, B3 = F000. Contrasts d = g(C*) - g(R3), q = g(B3) - g(R3), and their changes from no churn,
paired by seed (base with base, doubled with doubled). Intervals: paired seed bootstrap, 9,999 resamples, percentile 95%;
one resampled index vector per market and replicate, shared by every rule, rate, version and the no-churn records;
pooled = equal-weight mean of the six market means, seeds resampled within each market. The intervals condition on the
markets and the selected policies. Exploratory follow-up: no test, no multiplicity family, no registered decision changes.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

RULES = ("F111", "C*", "F000")
RATES = (0.01, 0.05)
CONDS = ("0",) + tuple(f"{p:g}" for p in RATES)
VERS = ("base", "doubled")
B = 9999
SEED = 20261110                       # fixed bootstrap seed (the plan's date of specification)
TOL = 1e-9
LABEL = "exploratory follow-up (churn plan draft 6); no confirmatory test, no multiplicity family, no registered decision changes"


def safe(rid: str) -> str:
    return rid.replace("|", "__").replace("/", "~").replace("*", "star")      # revision_v2._safe


def _read(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def _arrays(src: dict, what: str, n_seeds: int) -> dict:
    """One-dimensional finite gains and profit terms, one per seed, unique seeds, the expected seed count."""
    seeds = list(src["seeds"])
    if len(seeds) != n_seeds:
        raise ValueError(f"{what}: {len(seeds)} seeds (expected {n_seeds})")
    if len(set(seeds)) != len(seeds):
        raise ValueError(f"{what}: duplicate seed identifiers")
    out = {}
    for k in ("gain", "profit_attack", "profit_ref"):
        a = np.asarray(src[k], dtype=float)
        if a.ndim != 1 or a.size != n_seeds:
            raise ValueError(f"{what}: {a.size} values of {k} for {n_seeds} seeds (expected {n_seeds})")
        if not np.all(np.isfinite(a)):
            raise ValueError(f"{what}: non-finite {k}")
        out[k] = a
    return out


def load(eval_all, churn_dir, report_path, markets, n_seeds: int = 200) -> dict:
    """Per-seed arrays {ver: {cond: {market: {rule: {gain, profit_attack, profit_ref}}}}}, the doubling flags of the churn
    cells, and the missing cells. Refuses if a market's seed lists differ between any rule, rate, version or no churn."""
    report = json.loads(Path(report_path).read_text())
    cells = {v: {c: {m: {} for m in markets} for c in CONDS} for v in VERS}
    flags, missing = {}, []
    for m in markets:
        seeds = None
        for r in RULES:
            rid = f"{m}@rho0.2|{r}|D2+H3|profit"
            srcs = {("base", "0"): _read(Path(eval_all) / "evaluate" / (safe(rid) + ".json")),
                    ("doubled", "0"): (report.get("doubling", {}).get(rid) or {}).get("heldout")}
            for p in RATES:
                c = f"{p:g}"; cid = f"{rid}|churn{c}"; d = Path(churn_dir) / f"p{c}"
                srcs[("base", c)] = _read(d / "evaluate" / (safe(cid) + ".json"))
                dbl = _read(d / "doubling" / (safe(cid) + ".json"))
                srcs[("doubled", c)] = (dbl or {}).get("heldout")
                if dbl is not None:
                    flags[f"{c}|{m}|{r}"] = {k: dbl[k] for k in ("attack_change", "reference_change", "incomplete")}
            for (v, c), src in srcs.items():
                if src is None and c == "0":      # registered records all exist: a gap means a wrong input directory
                    raise ValueError(f"registered no-churn record missing: {rid} ({v})")
                if src is None:
                    missing.append(f"{v}|{c}|{m}|{r}"); continue
                if seeds is None:
                    seeds = list(src["seeds"])
                elif list(src["seeds"]) != seeds:
                    raise ValueError(f"seeds of {rid} ({v}, p = {c}) differ from the market's seed list")
                cells[v][c][m][r] = _arrays(src, f"{rid} ({v}, p = {c})", n_seeds)
    return {"cells": cells, "flags": flags, "missing": missing, "markets": tuple(markets)}


def _market_stats(data: dict, m: str, idx=None) -> dict:
    """Per-market means for one market, optionally on resampled seed indices: keys 'ver|cond|kind|name'."""
    out = {}
    pick = (lambda a: a) if idx is None else (lambda a: a[idx])
    for v in VERS:
        for c in CONDS:
            x = data["cells"][v][c][m]
            for r, a in x.items():
                out[f"{v}|{c}|g|{r}"] = float(np.mean(pick(a["gain"])))
                out[f"{v}|{c}|pa|{r}"] = float(np.mean(pick(a["profit_attack"])))
                out[f"{v}|{c}|pr|{r}"] = float(np.mean(pick(a["profit_ref"])))
            for name, (a, b) in (("d", ("C*", "F111")), ("q", ("F000", "F111"))):
                if a in x and b in x:
                    out[f"{v}|{c}|{name}|"] = float(np.mean(pick(x[a]["gain"]) - pick(x[b]["gain"])))
            if c == "0":
                continue
            for k in [k for k in list(out) if k.startswith(f"{v}|{c}|") and k.split("|")[2] in ("g", "d", "q", "pa", "pr")]:
                k0 = k.replace(f"{v}|{c}|", f"{v}|0|", 1)
                if k0 in out:
                    out[k.replace(f"{v}|{c}|", f"{v}|{c}|c", 1)] = out[k] - out[k0]
    return out


def _pool(pm: dict, key: str, markets) -> float | None:
    xs = [pm[m][key] for m in markets if key in pm[m]]
    return float(np.mean(xs)) if markets and len(xs) == len(markets) else None


def _ci(xs):
    xs = np.asarray([x for x in xs if x is not None], dtype=float)
    if xs.size == 0:
        return None
    return [float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))]


def _signs(vals) -> dict:
    vals = list(vals)
    return {"positive": sum(x > 0 for x in vals), "negative": sum(x < 0 for x in vals), "zero": sum(x == 0 for x in vals)}


def _build(data: dict, reps=None) -> dict:
    ms = data["markets"]; pm = {m: _market_stats(data, m) for m in ms}

    def entry(key, signs=False):
        e = {"markets": {m: pm[m][key] for m in ms if key in pm[m]}}
        est = _pool(pm, key, ms)
        if reps is None:
            e["pooled"] = est
        else:
            e["pooled"] = {"estimate": est, "ci95": _ci([_pool(rp, key, ms) for rp in reps]) if est is not None else None}
            e["ci95_markets"] = {m: _ci([rp[m].get(key) for rp in reps]) for m in e["markets"]}
        if signs:
            e["signs"] = _signs(e["markets"].values())
        return e

    res = {}
    for v in VERS:
        res[v] = {}
        for c in CONDS:
            b = {"g": {r: entry(f"{v}|{c}|g|{r}") for r in RULES}, "d": entry(f"{v}|{c}|d|", True),
                 "q": entry(f"{v}|{c}|q|", True),
                 "profit": {r: {"attack": entry(f"{v}|{c}|pa|{r}"), "reference": entry(f"{v}|{c}|pr|{r}")} for r in RULES}}
            if c != "0":
                b["change"] = {"g": {r: entry(f"{v}|{c}|cg|{r}", True) for r in RULES}, "d": entry(f"{v}|{c}|cd|", True),
                               "q": entry(f"{v}|{c}|cq|", True),
                               "profit": {r: {"attack": entry(f"{v}|{c}|cpa|{r}"), "reference": entry(f"{v}|{c}|cpr|{r}")}
                                          for r in RULES}}
            res[v][c] = b
    return res


def statistics(data: dict) -> dict:
    """Point estimates per market and pooled (pooled only when the statistic exists in every market)."""
    return _build(data)


def analyse(data: dict, b: int = B, seed: int = SEED) -> dict:
    """Point estimates with paired percentile intervals and sign counts over the markets."""
    rng = np.random.default_rng(seed); ms = data["markets"]
    n = {m: next((len(a["gain"]) for v in VERS for c in CONDS for a in data["cells"][v][c][m].values()), 0) for m in ms}
    reps = [{m: (_market_stats(data, m, rng.integers(0, n[m], n[m])) if n[m] else {}) for m in ms} for _ in range(b)]
    res = _build(data, reps)
    res["missing"] = list(data["missing"])
    res["bootstrap"] = {"resamples": b, "seed": seed, "interval": "percentile 95%", "paired": "rules, rates, versions, no churn"}
    return res


def flag_summary(flags: dict) -> dict:
    inc = sorted(k for k, f in flags.items() if f.get("incomplete"))
    return {"cells": len(flags), "incomplete_n": len(inc), "incomplete": sorted(k for k, f in flags.items() if f.get("incomplete")),
            "attack_changed": sorted(k for k, f in flags.items() if f.get("attack_change")),
            "reference_changed": sorted(k for k, f in flags.items() if f.get("reference_change"))}


def _est(e):
    p = e["pooled"]
    return p["estimate"] if isinstance(p, dict) else p


def _verdict(holds: dict) -> str:
    if any(h is None for h in holds.values()):
        return "unavailable"
    return "met" if all(holds.values()) else ("failed" if not any(holds.values()) else "not established")


def expectations(res: dict, diagnostics: dict | None) -> dict:
    """Section 6, scored on point estimates: met (both versions), failed (neither), not established (they disagree)."""
    out = {}
    e1, e2, e3 = {}, {}, {}
    for v in VERS:
        ch, nc = _est(res[v]["0.05"]["g"]["F111"]), _est(res[v]["0"]["g"]["F111"])
        e1[v] = {"churn": ch, "no_churn": nc, "holds": None if ch is None or nc is None else ch > nc}
        ch, nc = _est(res[v]["0.05"]["d"]), _est(res[v]["0"]["d"])
        e2[v] = {"churn": ch, "no_churn": nc, "holds": None if ch is None or nc is None else ch < nc}
        mk = res[v]["0.01"]["q"]["markets"]; pos = sum(x > 0 for x in mk.values())
        e3[v] = {"positive": pos, "markets": len(mk), "holds": None if len(mk) < 6 else pos == 6}
    out["1"] = {"text": "pooled g_0.05(R3) exceeds pooled no-churn g(R3)", **e1, "verdict": _verdict({v: e1[v]["holds"] for v in VERS})}
    out["2"] = {"text": "pooled d_0.05 = C* - R3 below its no-churn value", **e2, "verdict": _verdict({v: e2[v]["holds"] for v in VERS})}
    out["3"] = {"text": "q_0.01 = B3 - R3 positive on all six markets", **e3, "verdict": _verdict({v: e3[v]["holds"] for v in VERS})}
    e4 = {}
    for w in VERS:
        try:
            sh = {r: diagnostics["pooled"][f"{r}|{w}"]["honest_replacement"][0]["share"] for r in RULES}
        except (TypeError, KeyError, IndexError):
            sh = {r: None for r in RULES}
        ok = None if any(x is None for x in sh.values()) else (sh["F111"] > sh["C*"] and sh["F111"] > sh["F000"])
        e4[w] = {"first_bin_share": sh, "holds": ok}
    out["4"] = {"text": "p = 0.05: pooled audited share of honest replacements aged [0, 10) higher under R3 than C* and B3",
                **e4, "verdict": _verdict({w: e4[w]["holds"] for w in VERS})}
    return out


def registered_check(res: dict, reg: dict) -> dict:
    """The no-churn records reproduce posthoc.json doubled.D2+H3 (q1 = C* - R3, q4 = B3 - R3; frozen = base)."""
    pairs = {"q1_frozen": ("base", "d"), "q1_doubled": ("doubled", "d"), "q4_frozen": ("base", "q"), "q4_doubled": ("doubled", "q")}
    rows = {}
    for k, (v, s) in pairs.items():
        got = _est(res[v]["0"][s]); want = reg["pooled"][k]
        rows[k] = {"registered": want, "computed": got, "ok": got is not None and abs(got - want) <= TOL}
    absm = [v for v in VERS if all(_est(res[v]["0"]["g"][r]) is not None
                                   and abs(_est(res[v]["0"]["g"][r]) - reg["absolute"][r]["mean_gain"]) <= TOL for r in ("C*", "F111"))]
    return {"pooled": rows, "absolute_matches": absm, "ok": all(x["ok"] for x in rows.values()) and bool(absm)}


CATS = ("honest_replacement", "honest_initial", "focal")


def validate_diagnostics(diag: dict, markets, n_seeds: int = 200) -> None:
    """Astra r1: before scoring, check the driver's summaries against their own counts. Every (market, rule, winner) cell
    exists with one episode per seed; each bin's served and audited totals equal the sums of the per-episode counts and
    its share is audited / served (None when nothing was served); the market-pooled share per bin is the mean of the
    available market shares, with that count; the newest shares are in [0, 1] or None."""
    for r in RULES:
        for w in VERS:
            by_m = {}
            for m in markets:
                cell = (diag.get("cells", {}).get(f"{m}@rho0.2|{r}") or {}).get(w)
                if cell is None:
                    raise ValueError(f"diagnostics cell missing: {m}|{r}|{w}")
                sh = cell["shares"]; per = sh["per_episode"]
                if len(per) != n_seeds or len(sh["focal_newest_by_first_offer_assigned"]) != n_seeds:
                    raise ValueError(f"{m}|{r}|{w}: {len(per)} episodes (expected {n_seeds})")
                for x in sh["focal_newest_by_first_offer_assigned"] + sh["focal_newest_by_creation"]:
                    if x is not None and not (math.isfinite(x) and 0 <= x <= 1):
                        raise ValueError(f"{m}|{r}|{w}: newest share {x} outside [0, 1]")
                for c in CATS:
                    for b, row in enumerate(sh[c]):
                        sv = sum(e[c][b][0] for e in per); au = sum(e[c][b][1] for e in per)
                        if (row["served"], row["audited"]) != (sv, au):
                            raise ValueError(f"{m}|{r}|{w}|{c} bin {b}: totals differ from the per-episode counts")
                        want = au / sv if sv else None
                        if (want is None) != (row["share"] is None) or (want is not None and abs(row["share"] - want) > TOL):
                            raise ValueError(f"{m}|{r}|{w}|{c} bin {b}: share is not audited / served")
                by_m[m] = sh
            pooled = (diag.get("pooled") or {}).get(f"{r}|{w}")
            if pooled is None:
                raise ValueError(f"pooled diagnostics missing: {r}|{w}")
            for c in CATS:
                for b, row in enumerate(pooled[c]):
                    v = [by_m[m][c][b]["share"] for m in markets if by_m[m][c][b]["share"] is not None]
                    want = sum(v) / len(v) if v else None
                    if row["markets"] != len(v) or (want is None) != (row["share"] is None) or (want is not None and abs(row["share"] - want) > TOL):
                        raise ValueError(f"pooled share {r}|{w}|{c} bin {b} differs from the market shares")


def diag_summary(diag: dict) -> dict:
    """Per rule and winner: honest replacements per episode, and the share of rounds in which the focal identity's first-offer
    round is strictly the latest among identities holding assigned jobs (ties excluded), averaged over the episodes of a
    market (episodes without such rounds left out) and then over markets with equal weights; not one pooled fraction of
    rounds. The driver's market-pooled age-bin shares are copied (checked by validate_diagnostics)."""
    out = {}
    cells = diag.get("cells", {})
    for r in RULES:
        for w in VERS:
            reps, newest = [], []
            for k, cell in cells.items():
                if k.split("|")[-1] != r or w not in cell:
                    continue
                s = cell[w]["shares"]; reps.append(float(s["honest_replacements_per_episode"]))
                xs = [x for x in s["focal_newest_by_first_offer_assigned"] if x is not None and math.isfinite(x)]
                if xs:
                    newest.append(float(np.mean(xs)))
            out[f"{r}|{w}"] = {"honest_replacements_per_episode": float(np.mean(reps)) if reps else None,
                               "focal_newest_first_offer": float(np.mean(newest)) if newest else None,
                               "markets": len(reps), "pooled_bins": diag.get("pooled", {}).get(f"{r}|{w}")}
    return out


def _fmt(e, d: int = 3) -> str:
    p = e["pooled"]
    if p["estimate"] is None:
        return "--"
    lo, hi = p["ci95"] or (None, None)
    n = lambda x: f"{x:.{d}f}".replace("-", "$-$")          # a typeset minus, not a hyphen
    return n(p["estimate"]) + ("" if lo is None else f" [{n(lo)}, {n(hi)}]")


def table(res: dict) -> str:
    name = {"0": "0 (registered)", "0.01": "0.01", "0.05": "0.05"}
    lines = ["\\begin{tabular}{llccccc}", "\\toprule",
             "Winner & $p$ & $g$(R3) & $g$(C*) & $g$(B3) & $d$ = C*$-$R3 & $q$ = B3$-$R3 \\\\", "\\midrule"]
    for v in VERS:
        for c in CONDS:
            b = res[v][c]
            lines.append(f"{'frozen' if v == 'base' else v} & {name[c]} & " + " & ".join([_fmt(b["g"][r]) for r in RULES] + [_fmt(b["d"]), _fmt(b["q"])]) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def _sha(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--records", required=True, help="registered eval-all directory (no-churn base records)")
    ap.add_argument("--churn", required=True, help="the pod's followup-churn directory (p0.01, p0.05)")
    ap.add_argument("--report", required=True, help="registered report.json (no-churn doubled records)")
    ap.add_argument("--out", required=True); ap.add_argument("--tables", required=True)
    ap.add_argument("--posthoc", default=None, help="posthoc.json, to check the registered no-churn values")
    ap.add_argument("--n-seeds", dest="n_seeds", type=int, default=200)
    ap.add_argument("--resamples", type=int, default=B); ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    markets = tuple(f"fresh{i}" for i in range(6)); ch = Path(a.churn)
    data = load(a.records, ch, a.report, markets, a.n_seeds)
    res = analyse(data, a.resamples, a.seed)
    diags = {c: _read(ch / f"p{c}" / "diagnostics.json") for c in CONDS[1:]}
    for d in diags.values():
        if d is not None:
            validate_diagnostics(d, markets, a.n_seeds)
    out = {"label": LABEL, "statistics": res, "flags": data["flags"], "flag_summary": flag_summary(data["flags"]),
           "expectations": expectations(res, diags.get("0.05")),
           "diagnostics": {c: (diag_summary(d) if d else None) for c, d in diags.items()},
           "inputs": {"records": str(a.records), "churn": str(ch), "report_sha256": _sha(Path(a.report)),
                      "run_json_sha256": _sha(ch / "run.json"),
                      **{f"inventory_p{c}_sha256": _sha(ch / f"p{c}" / "inventory.json") for c in CONDS[1:]},
                      **{f"diagnostics_p{c}_sha256": _sha(ch / f"p{c}" / "diagnostics.json") for c in CONDS[1:]}}}
    if a.posthoc:
        out["registered_check"] = registered_check(res, json.loads(Path(a.posthoc).read_text())["doubled"]["D2+H3"])
        out["inputs"]["posthoc_sha256"] = _sha(Path(a.posthoc))
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    d = Path(a.tables); d.mkdir(parents=True, exist_ok=True)
    (d / "posthoc_churn.tex").write_text(table(res).replace("C*", "C$^*$"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
