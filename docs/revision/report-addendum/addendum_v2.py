"""Operation 8 addendum beside the tagged report (review round 1, 2026-11-04). The report itself stays as `report_v2.py`
at tag protocol-v2 wrote it; this file adds what the reviewers asked to be stated: interval labels, the claim scope of
design 9.4, both deviations with their evidence, the search-flag dependencies traced through reference and bank records,
and per-market Q1 side fields. It changes no estimate and no decision.

Usage: addendum_v2.py --report R/report.json --cfg-ulp D/cfg_ulp_all.json --ledger budget-ledger.json --records EVAL/all
       --eval-checkout CHECKOUT --write R
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

FRESH = tuple(f"fresh{i}" for i in range(6))
FAMS = ("D2+H3", "X7-SC")
PAIR = ("F111", "C*")                 # Q1: d = gain of C* minus gain of F111
Q4_RULES = ("F000", "F111")           # Q4: B3 - R3 under D2+H3
OLD_CAP = 40.0
SCOPE = ("All claims are conditional on the six sampled markets, the stated neighbourhood, the fixed pair (Q1, Q2, Q4), "
         "the searched families, and the frozen searches. Q4 replicates the B3 - R3 comparison under D2+H3 and R3's "
         "efficiency condition, not the complete amended PASS predicate of the first evaluation. Multiplicity is controlled "
         "within Q1 and within Q4 separately; there is no paper-wide 5 percent familywise guarantee. \"Confirmatory\" means "
         "specified before the fresh draw; it does not mean exact nominal error control on the fresh, selected-policy "
         "distributions. Q4 is an internal replication on fresh instances, not an independent-team replication. (Design 9.4.)")
LABELS = [
    ("Q1 decisions", "Holm over the two tests on calibrated two-sided p-values."),
    ("Q1 intervals", "calibrated Bonferroni simultaneous intervals (one-sided tails kappa x 0.05 / 4), reported beside the "
                     "Holm decisions and separate from them."),
    ("Q1 efficiency condition", "descriptive: nominal one-sided 97.5 percent bounds on the paired gross-efficiency "
                                "difference against -0.01; not calibrated."),
    ("Q1 per-market and headline rows", "descriptive, nominal 95 percent, unadjusted."),
    ("Q2", "descriptive, nominal 95 percent, unadjusted."),
    ("Q3", "descriptive, nominal 95 percent, unadjusted; G_min bounds are simultaneous over the c members, each member "
           "bound at tail 0.05/c."),
    ("Q4", "intersection-union per market, Holm over six markets (a missing market counts p = 1); bounds are calibrated "
           "one-sided at tail kappa x 0.05 / 6."),
]


def safe(rid: str) -> str:
    return rid.replace("|", "__").replace("/", "~").replace("*", "star")      # revision_v2._safe


def _read(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def flag_dependencies(out: Path, cells, flagged: set, path_of) -> dict:
    """For each evaluated cell, the flagged cells it depends on: itself, and every record reached through the upstream
    links of its evaluate record (search, reference, bank and twin records). Freeze records list everything of a market
    as an integrity anchor, not as a computational input, so they are not followed."""
    memo: dict = {}

    def closure(rid: str) -> set:
        if rid in memo:
            return memo[rid]
        rec = _read(path_of(out, rid))
        if rec is None:
            raise SystemExit(f"addendum: unresolvable upstream record {rid}")
        memo[rid] = set()                                   # cycle guard
        acc = set()
        for u in rec.get("upstream") or {}:
            if not u.startswith("freeze/"):
                acc |= {u} | closure(u)
        memo[rid] = acc
        return acc

    got = {}
    for cell in cells:
        ev = _read(Path(out) / "evaluate" / (safe(cell) + ".json"))
        if ev is None:
            raise SystemExit(f"addendum: no evaluate record for {cell}")
        acc = {cell}
        for u in ev.get("upstream") or {}:
            if not u.startswith("freeze/"):
                acc |= {u} | closure(u)
        got[cell] = sorted(acc & set(flagged))
    return got


def side_fields(out: Path, markets, pair, fams, side: dict) -> dict:
    """Per-market means of the Q1 side fields, first rule minus second (the report's pooled convention)."""
    a, b = pair; res = {}
    for m in markets:
        row = {}
        for f in fams:
            ra = _read(Path(out) / "evaluate" / (safe(f"{m}@rho0.2|{a}|{f}|profit") + ".json"))
            rb = _read(Path(out) / "evaluate" / (safe(f"{m}@rho0.2|{b}|{f}|profit") + ".json"))
            if ra is None or rb is None:
                continue
            row[f"{b}-{a}|{f}"] = {k: float(np.mean(np.asarray(ra[fld], dtype=float) - np.asarray(rb[fld], dtype=float)))
                                   for k, fld in side.items()}
        res[m] = row
    return res


def _stability(stab):
    if stab is None:
        return "not verified"
    return "verified: every Q1 and Q4 decision unchanged" if stab["decisions_unchanged"] else "checked: decisions changed"


def _stab_detail(stab, sha):
    if stab is None:
        return None
    cells = stab.get("cells", {})
    return {"sha256": sha, "diffs": list(stab["decision_diffs"]), "cells": len(cells),
            "cells_with_seed_changes": sum(1 for c in cells.values() if c["seeds_changed"]),
            "max_mean_shift": max((abs(c["mean_new"] - c["mean_old"]) for c in cells.values()), default=0.0)}


def _stab_text(dev: dict) -> str:
    d = dev["stability"]
    if d is None:
        return "That the decisions would be unchanged under the registered configurations is not verified."
    head = (f"A re-evaluation of the frozen policies of the {d['cells']} fresh-market cells that Q1 and Q4 use, on the registration "
            f"platform with the registered configurations (`results/v2/deviation/stability.json`, sha256 {d['sha256']}), changes "
            f"per-seed gains in {d['cells_with_seed_changes']} cells and cell means by at most {d['max_mean_shift']:.3f}; ")
    if not d["diffs"]:
        return head + "every Q1 and Q4 decision is unchanged."
    return head + "these decisions changed: " + "; ".join(d["diffs"]) + "."


def build(report: dict, cfg: dict, cfg_sha: str, ledger: dict, deps: dict, sides: dict, stab: dict | None = None,
          stab_sha: str | None = None) -> dict:
    if not cfg.get("ok"):
        raise SystemExit("addendum: the deviation check (cfg_ulp_all.json) did not pass")
    conf = {}
    for m, v in sorted(cfg["markets"].items()):
        conf[m] = {"recorded_hash": v["recorded_hash"], "container_hash": v["container_hash"],
                   "pod_hashes_match": all(h == v["container_hash"] for h in v["pod_hashes"]),
                   "differing_values": len(v["differences"]), "max_ulps": max((d[3] for d in v["differences"]), default=0),
                   "verify_with_container_configs": "ok" if v["verify_exit"] == 0 else "failed"}
    spent = sum(s["usd"] for s in ledger["spent"] if s["op"] == "evaluation")
    sd = {"q1": {}, "q4": {}}
    for name, hit in deps["q1"].items():
        sd["q1"][name] = {"depends_on_flagged": hit, "new_qualification": bool(hit) and not report["q1"]["tests"][name].get("search")}
    for m, hit in deps["q4"].items():
        mk = report["q4"]["markets"].get(m)
        sd["q4"][m] = {"depends_on_flagged": hit, "new_qualification": bool(hit) and not (isinstance(mk, dict) and mk.get("search"))}
    return {"labels": LABELS, "scope": SCOPE,
            "deviations": {"configs": conf, "evidence_sha256": cfg_sha, "decision_stability": _stability(stab), "stability": _stab_detail(stab, stab_sha),
                           "cap": {"old": OLD_CAP, "new": ledger["caps"]["evaluation"], "approval": ledger["approval"]["text"],
                                   "evaluation_spent": round(spent, 3)}},
            "search_dependencies": sd, "q1_side_fields": sides}


def render(add: dict) -> str:
    L = ["# Protocol v2 report: addendum (Operation 8, review round 1)", "",
         "This addendum accompanies `report.md` and `report.json`, which `scripts/report_v2.py` at tag protocol-v2 wrote. "
         "It changes no estimate and no decision.", "", "## Interval and decision labels"]
    L += [f"- {k}: {v}" for k, v in add["labels"]]
    L += ["", "## Claim scope", add["scope"], "", "## Deviations from the protocol", "",
          "1. Fresh-market configurations. The pods (Linux x86) recalibrated each fresh market; `instances.json` holds the "
          "arm64 calibration. The report used the configurations a Linux container reproduces "
          "(`results/v2/deviation/instances_container_configs.json`); the headline market uses the registered ones.", "",
          "| market | registered config hash | reproduced config hash | pod hashes match | differing values | max ulps | verify |",
          "|---|---|---|---|---|---|---|"]
    for m, v in add["deviations"]["configs"].items():
        L.append(f"| {m} | {v['recorded_hash']} | {v['container_hash']} | {v['pod_hashes_match']} | {v['differing_values']} "
                 f"| {v['max_ulps']} | {v['verify_with_container_configs']} |")
    c = add["deviations"]["cap"]
    L += ["", f"Evidence: `results/v2/deviation/cfg_ulp_all.json` (sha256 {add['deviations']['evidence_sha256']}), written by "
          "`docs/revision/deviation/cfg_ulp.py`. These checks establish matching pod hashes, differences within one unit in the "
          "last place, and verification with the reproduced configurations; they do not show that the decisions are unchanged, "
          "since small input differences can change discrete simulation branches. " + _stab_text(add["deviations"]), "",
          f"2. Evaluation cap. The author raised the evaluation cap from {c['old']:g} to {c['new']:g} USD after the first fresh "
          f"pods cost about ten percent more than estimated (recorded approval: \"{c['approval']}\"). Evaluation spend: "
          f"{c['evaluation_spent']:g} USD. No analysis changed.", "",
          "## Search-flag dependencies", "",
          "Design 6.5 labels a confirmatory decision that uses a search-flagged cell as a decision about the prescribed search "
          "procedure. A cell's reference is built from the search records of every family on its menu and, for fixed rules, "
          "from other rules' searches (the bank), so a decision can use a flagged cell's search through its references. "
          "Traced through the upstream links of the evaluate, reference, search and bank records (freeze records excluded):", ""]
    for q, rows in (("Q1", add["search_dependencies"]["q1"]), ("Q4", add["search_dependencies"]["q4"])):
        for k, v in rows.items():
            tag = "newly qualified: about the prescribed search procedure" if v["new_qualification"] else (
                "already labelled in the report" if v["depends_on_flagged"] else "no flagged dependency")
            L.append(f"- {q} {k}: {tag}" + (f" (depends on {', '.join(v['depends_on_flagged'])})" if v["depends_on_flagged"] else ""))
    L += ["", "## Q1 side fields per market (descriptive, means, F111 minus C*)"]
    for m, row in add["q1_side_fields"].items():
        for t, flds in row.items():
            L.append(f"- {m} {t}: " + "; ".join(f"{k} {v:.4f}" for k, v in flds.items()))
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    for a in ("--report", "--cfg-ulp", "--ledger", "--records", "--eval-checkout", "--write"):
        ap.add_argument(a, required=True)
    ap.add_argument("--stability", help="stability.py output")
    a = ap.parse_args(argv)
    co = Path(a.eval_checkout).resolve(); sys.path[:0] = [str(co / "scripts"), str(co)]
    import report_v2 as RP  # noqa: E402  (the tagged report's own field map)
    import revision_v2 as RV  # noqa: E402
    report = json.loads(Path(a.report).read_text()); cfgp = Path(a.cfg_ulp); out = Path(a.records)
    flagged = set(report["search_flagged"])
    q1c = {f"{PAIR[1]}-{PAIR[0]}|{f}": [f"{m}@rho0.2|{r}|{f}|profit" for m in FRESH for r in PAIR] for f in FAMS}
    q4c = {m: [f"{m}@rho0.2|{r}|D2+H3|profit" for r in Q4_RULES] for m in FRESH}
    allc = sorted({c for v in list(q1c.values()) + list(q4c.values()) for c in v})
    per = flag_dependencies(out, allc, flagged, RV.path_of)
    deps = {"q1": {k: sorted({h for c in v for h in per[c]}) for k, v in q1c.items()},
            "q4": {k: sorted({h for c in v for h in per[c]}) for k, v in q4c.items()}}
    sides = side_fields(out, FRESH + ("headline",), PAIR, FAMS, RP.SIDE)
    add = build(report, json.loads(cfgp.read_text()), hashlib.sha256(cfgp.read_bytes()).hexdigest(),
                json.loads(Path(a.ledger).read_text()), deps, sides,
                json.loads(Path(a.stability).read_text()) if a.stability else None,
                hashlib.sha256(Path(a.stability).read_bytes()).hexdigest() if a.stability else None)
    w = Path(a.write); (w / "addendum.json").write_text(json.dumps(add, indent=1, default=float) + "\n")
    (w / "addendum.md").write_text(render(add))
    print(f"addendum written: {w / 'addendum.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
