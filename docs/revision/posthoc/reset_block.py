"""The reset block of the post-hoc analysis (docs/revision/reset-experiment-plan.md, draft 5, sections 5 and 6).

I(r, m) = mean over the evaluation seeds of g(D2+H3 winner) - g(D2 winner), both against the frozen reference of (r, m).
Rules: B3 = F000, R3 = F111, C*. Gaps G(fam) = g_B3 - g_R3 under one family. Share S = 1 - G(D2) / G(D2+H3), pooled,
reported only if the lower bound of pooled G(D2+H3) exceeds 0.05. Intervals: paired seed bootstrap, percentile 95%,
the same resampled seed indices for every rule and family of a market; pooled = equal-weight mean of the market means,
seeds resampled independently within each market. Descriptive; no test, no registered decision changes.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RULES = ("F000", "F111", "C*")
FAMS = ("D2+H3", "D2")
B = 9999
SEED = 20261109                       # fixed bootstrap seed (the plan's date of specification)
GATE = 0.05
CONTRASTS = {"B3-R3": ("F000", "F111"), "C*-R3": ("C*", "F111")}


def safe(rid: str) -> str:
    return rid.replace("|", "__").replace("/", "~").replace("*", "star")      # revision_v2._safe


def _read(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def load(eval_all, reset_dir, report: dict, markets) -> dict:
    """Base and doubled per-seed gains, {version: {market: {family: {rule: array}}}}, plus the D2 doubling flags.
    Refuses if the seeds of a market differ between any rule, family or version (the pairing needs one seed list)."""
    base, dbl, flags = {}, {}, {}
    for m in markets:
        seeds = None
        for fam in FAMS:
            for rule in RULES:
                rid = f"{m}@rho0.2|{rule}|{fam}|profit"
                root = Path(eval_all) if fam == "D2+H3" else Path(reset_dir)
                r = _read(root / "evaluate" / (safe(rid) + ".json"))
                if fam == "D2+H3":
                    h = report.get("doubling", {}).get(rid)
                else:
                    d = _read(Path(reset_dir) / "doubling" / (safe(rid) + ".json")); h = d
                    if d is not None:
                        flags[f"{m}|{rule}|D2"] = {k: d[k] for k in ("attack_change", "reference_change", "incomplete")}
                for ver, src, store in (("base", r, base), ("doubled", (h or {}).get("heldout"), dbl)):
                    if src is None:
                        continue
                    if seeds is None:
                        seeds = list(src["seeds"])
                    elif list(src["seeds"]) != seeds:
                        raise ValueError(f"seeds of {rid} ({ver}) differ from the market's seed list")
                    store.setdefault(m, {}).setdefault(fam, {})[rule] = np.asarray(src["gain"], dtype=float)
    return {"base": base, "doubled": dbl, "flags": flags}


def _complete(cells: dict) -> tuple[dict, list]:
    """Markets with every rule and family, and the list of missing cells (reported, never imputed)."""
    ok, missing = {}, []
    for m, v in cells.items():
        miss = [f"{m}|{r}|{f}" for f in FAMS for r in RULES if r not in v.get(f, {})]
        missing += miss
        ok[m] = v
    return ok, missing


def _market_stats(v: dict, idx=None) -> dict:
    """Per-market means of the statistics for one market (optionally on resampled seed indices)."""
    g = {f: {r: (a if idx is None else a[idx]) for r, a in v.get(f, {}).items()} for f in FAMS}
    out = {}
    for r in RULES:
        if r in g["D2+H3"] and r in g["D2"]:
            out[("I", r)] = float(np.mean(g["D2+H3"][r] - g["D2"][r]))
    for name, (a, b) in CONTRASTS.items():
        if ("I", a) in out and ("I", b) in out:
            out[("C", name)] = out[("I", a)] - out[("I", b)]
    for f in FAMS:
        if "F000" in g[f] and "F111" in g[f]:
            out[("G", f)] = float(np.mean(g[f]["F000"] - g[f]["F111"]))
    return out


def _pool(per_market: dict, key, markets) -> float | None:
    xs = [per_market[m][key] for m in markets if key in per_market[m]]
    return float(np.mean(xs)) if xs and len(xs) == len(markets) else None


def _share(gd2, gd2h3):
    return None if gd2 is None or gd2h3 is None or gd2h3 == 0 else 1 - gd2 / gd2h3


def statistics(cells: dict) -> dict:
    """Point estimates: per market and pooled (pooled only over markets where the statistic exists in all of them)."""
    pm = {m: _market_stats(v) for m, v in cells.items()}; ms = tuple(cells)
    res = {"I": {}, "contrast": {}, "G": {}}
    for r in RULES:
        res["I"][r] = {"markets": {m: pm[m][("I", r)] for m in ms if ("I", r) in pm[m]}, "pooled": _pool(pm, ("I", r), _have(pm, ("I", r)))}
    for c in CONTRASTS:
        res["contrast"][c] = {"markets": {m: pm[m][("C", c)] for m in ms if ("C", c) in pm[m]}, "pooled": _pool(pm, ("C", c), _have(pm, ("C", c)))}
    for f in FAMS:
        res["G"][f] = {"markets": {m: pm[m][("G", f)] for m in ms if ("G", f) in pm[m]}, "pooled": _pool(pm, ("G", f), _have(pm, ("G", f)))}
    res["S"] = {"pooled": _share(res["G"]["D2"]["pooled"], res["G"]["D2+H3"]["pooled"])}
    return res


def _have(pm, key):
    return tuple(m for m in pm if key in pm[m])


def _boot(cells: dict, markets, b: int, rng) -> list[dict]:
    """b replicates; each replicate draws one index vector per market, shared by every rule and family of that market."""
    reps = []
    n = {m: len(next(iter(next(iter(cells[m].values())).values()))) for m in markets}
    for _ in range(b):
        reps.append({m: _market_stats(cells[m], rng.integers(0, n[m], n[m])) for m in markets})
    return reps


def _ci(xs):
    xs = np.asarray([x for x in xs if x is not None], dtype=float)
    return [float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))] if xs.size else None


def _gated_share(pm_point, reps, markets) -> dict:
    """S over `markets` with its denominator gate (lower bound of pooled G(D2+H3) over the same markets above 0.05)."""
    g1 = _pool(pm_point, ("G", "D2+H3"), markets); g0 = _pool(pm_point, ("G", "D2"), markets)
    lb = _ci([_pool(r, ("G", "D2+H3"), markets) for r in reps])
    if g1 is None or g0 is None or lb is None:
        return {"value": None, "reason": "not defined: a cell is missing", "ci95": None}
    if not lb[0] > GATE:
        return {"value": None, "reason": f"not defined: lower bound of pooled G(D2+H3) {lb[0]:.4f} <= {GATE}", "ci95": None}
    return {"value": _share(g0, g1), "reason": "defined", "ci95": _ci([_share(_pool(r, ("G", "D2"), markets), _pool(r, ("G", "D2+H3"), markets)) for r in reps]),
            "denominator_lower_bound": lb[0]}


def analyse(cells: dict, b: int = B, seed: int = SEED) -> dict:
    """Point estimates with paired percentile intervals, the gated share, market sensitivity and expectation inputs."""
    cells, missing = _complete(cells); ms = tuple(cells)
    pm = {m: _market_stats(cells[m]) for m in ms}
    reps = _boot(cells, ms, b, np.random.default_rng(seed))
    res = {"missing": missing, "bootstrap": {"resamples": b, "seed": seed, "interval": "percentile 95%"}}

    def block(kind, key_of, names):
        out = {}
        for nm in names:
            k = key_of(nm); have = _have(pm, k)
            out[nm] = {"markets": {m: {"estimate": pm[m][k], "ci95": _ci([r[m].get(k) for r in reps])} for m in have},
                       "pooled": {"estimate": _pool(pm, k, have) if len(have) == len(ms) else None,
                                  "ci95": _ci([_pool(r, k, have) for r in reps]) if len(have) == len(ms) else None}}
        return out
    res["I"] = block("I", lambda r: ("I", r), RULES)
    res["contrast"] = block("C", lambda c: ("C", c), tuple(CONTRASTS))
    res["G"] = block("G", lambda f: ("G", f), FAMS)
    res["S"] = {"pooled": _gated_share(pm, reps, ms)}
    signs = {c: {"positive": int(sum(1 for m in ms if pm[m].get(("C", c), 0) > 0)), "n": int(sum(1 for m in ms if ("C", c) in pm[m]))} for c in CONTRASTS}
    loo = {m: _gated_share(pm, reps, tuple(x for x in ms if x != m)) for m in ms} if len(ms) > 1 else {}
    res["sensitivity"] = {"signs": signs, "S_leave_one_out": loo}
    six = len(ms) == 6
    res["expectation_inputs"] = {"all_markets": {c: (signs[c]["positive"] == 6 if six and signs[c]["n"] == 6 else None) for c in CONTRASTS},
                                 "S": res["S"]["pooled"]["value"]}
    return res


def score(base: dict, dbl: dict) -> dict:
    """Plan section 6: met if it holds under both the base and the doubled searches, failed if under neither,
    not established (search-sensitive) if they disagree; undefined S and missing cells are reported as such."""
    def one(a, b):
        if a is None or b is None:
            return "missing cell"
        return "met" if a and b else "failed" if not a and not b else "not established (search-sensitive)"
    out = {f"{c} on all six": one(base["all_markets"][c], dbl["all_markets"][c]) for c in CONTRASTS}
    sb, sd = base["S"], dbl["S"]
    out["pooled S > 0.5"] = "S not defined" if sb is None or sd is None else one(sb > 0.5, sd > 0.5)
    return out


def reset_block(eval_all, reset_dir, report: dict, markets, b: int = B, seed: int = SEED) -> dict:
    L = load(eval_all, reset_dir, report, markets)
    base, dbl = analyse(L["base"], b, seed), analyse(L["doubled"], b, seed)
    return {"label": "exploratory follow-up (reset experiment plan draft 5); descriptive, not registered",
            "base": base, "doubled": dbl, "doubling_flags": L["flags"],
            "expectations": score(base["expectation_inputs"], dbl["expectation_inputs"])}


def switch_summary(diag: dict, markets=tuple(f"fresh{i}" for i in range(6))) -> dict:
    """Plan section 4, per rule pooled over the markets with equal weights: the fixed-policy switch g(winner) - g(winner,
    x = 0) of the D2+H3 winners (frozen and doubled), the reverse switch of the D2 winners (x = 1), and the reset counts.
    Refuses if any D2 winner has a reset (the plan's stop rule)."""
    out = {}
    for r in RULES:
        cells = [diag[f"{m}@rho0.2|{r}"] for m in markets]
        bad = [m for m, c in zip(markets, cells) if c["d2_base"]["mean_resets"] != 0]
        if bad:
            raise ValueError(f"D2 winner of {r} has a reset at {bad}")
        def pooled(f):
            xs = {m: f(c) for m, c in zip(markets, cells)}
            return {"markets": xs, "pooled": float(np.mean(list(xs.values())))}
        out[r] = {"fixed_policy_x0": pooled(lambda c: c["d2h3_base"]["switch_x0"]["effect"]),
                  "fixed_policy_x0_doubled": pooled(lambda c: c["d2h3_doubled"]["switch_x0"]["effect"]),
                  "reverse_x1": pooled(lambda c: c["d2_base"]["switch_x1"]["effect"]),
                  "d2h3_mean_resets": pooled(lambda c: c["d2h3_base"]["mean_resets"]),
                  "d2h3_p_any_reset": pooled(lambda c: c["d2h3_base"]["p_any_reset"]),
                  "d2_mean_resets_max": float(max(c["d2_base"]["mean_resets"] for c in cells))}
    return out


def headline(eval_all) -> dict:
    """Plan section 1 (exploratory): at headline@rho0.2, I per rule with its paired standard error, and the B3 - R3 gaps
    under D2+H3 and D2, from the registered evaluation records (same seeds and frozen reference per rule)."""
    g = {}
    for r in RULES:
        for f in FAMS:
            rid = f"headline@rho0.2|{r}|{f}|profit"; rec = _read(Path(eval_all) / "evaluate" / (safe(rid) + ".json"))
            if rec is None:
                raise ValueError(f"missing {rid}")
            g[(r, f)] = (list(rec["seeds"]), np.asarray(rec["gain"], dtype=float))
    seeds = g[(RULES[0], FAMS[0])][0]
    if any(v[0] != seeds for v in g.values()):
        raise ValueError("headline seeds differ between records")
    out = {"I": {}, "G": {}}
    for r in RULES:
        d = g[(r, "D2+H3")][1] - g[(r, "D2")][1]
        out["I"][r] = {"estimate": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(d.size))}
    for f in FAMS:
        out["G"][f] = {"estimate": float(np.mean(g[("F000", f)][1] - g[("F111", f)][1]))}   # leaf name fits the paper's gain kind
    return out


def _fmt(est, ci, d: int = 3) -> str:
    if est is None:
        return "--"
    return f"{est:.{d}f}" + (f" [{ci[0]:.{d}f}, {ci[1]:.{d}f}]" if ci else "")


ROWS = (("I(B3)", "I", "F000"), ("I(R3)", "I", "F111"), ("I(C*)", "I", "C*"), ("I(B3) - I(R3)", "contrast", "B3-R3"),
        ("I(C*) - I(R3)", "contrast", "C*-R3"), ("G(D2+H3)", "G", "D2+H3"), ("G(D2)", "G", "D2"))


def table(res: dict) -> str:
    """Pooled statistics (equal market weights) with 95% paired percentile intervals, frozen and doubled searches."""
    lines = ["\\begin{tabular}{lll}", "\\hline", "Statistic & frozen searches & doubled searches \\\\", "\\hline"]
    for label, kind, key in ROWS:
        cells = [_fmt(res[v][kind][key]["pooled"]["estimate"], res[v][kind][key]["pooled"]["ci95"]) for v in ("base", "doubled")]
        lines.append(f"{label} & {cells[0]} & {cells[1]} \\\\")
    s = [res[v]["S"]["pooled"] for v in ("base", "doubled")]
    lines.append("S & " + " & ".join(_fmt(x["value"], x["ci95"], 2) if x["value"] is not None else "not defined" for x in s) + " \\\\")
    for c in CONTRASTS:
        lines.append(f"markets with {c.replace('B3-R3', 'I(B3) > I(R3)').replace('C*-R3', 'I(C*) > I(R3)')} & "
                     + " & ".join(f"{res[v]['sensitivity']['signs'][c]['positive']} of {res[v]['sensitivity']['signs'][c]['n']}" for v in ("base", "doubled")) + " \\\\")
    lines += ["\\hline", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    import argparse
    import hashlib
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for k in ("--records", "--reset", "--report", "--out", "--tables"):
        ap.add_argument(k, required=True)
    ap.add_argument("--diagnostics", default=None, help="the Mac diagnostics.json (plan section 4)")
    ap.add_argument("--resamples", type=int, default=B); ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    markets = tuple(f"fresh{i}" for i in range(6))
    res = reset_block(a.records, a.reset, json.loads(Path(a.report).read_text()), markets, a.resamples, a.seed)
    res["inputs"] = {"records": str(a.records), "reset": str(a.reset), "report_sha256": hashlib.sha256(Path(a.report).read_bytes()).hexdigest(),
                     "reset_inventory_sha256": (hashlib.sha256((Path(a.reset) / "inventory.json").read_bytes()).hexdigest()
                                                if (Path(a.reset) / "inventory.json").exists() else None)}
    hl = Path(a.records) / "evaluate" / (safe("headline@rho0.2|F000|D2|profit") + ".json")
    res["headline"] = headline(a.records) if hl.exists() else None          # absent only in test fixtures
    if a.diagnostics:
        res["switches"] = switch_summary(json.loads(Path(a.diagnostics).read_text()))
        res["inputs"]["diagnostics_sha256"] = hashlib.sha256(Path(a.diagnostics).read_bytes()).hexdigest()
    Path(a.out).write_text(json.dumps(res, indent=1) + "\n")
    d = Path(a.tables); d.mkdir(parents=True, exist_ok=True)
    (d / "posthoc_reset.tex").write_text(table(res).replace("C*", "C$^*$"))
    print(json.dumps(res["expectations"], indent=1))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
