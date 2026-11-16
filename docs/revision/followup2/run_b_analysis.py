"""Run B analysis on the Mac (convergence-plan.md, sections 3, 4 and 7 step 3): recompute Q1 and Q4 from the pulled
records with each validated record's own binding, check that the result equals the pod's recompute.json, and write the
items that section 4 reports (cells passing within three rounds, the nesting shortfalls, the largest market change).
Descriptive and exploratory; the frozen estimates stay primary.
Usage: run_b_analysis.py <run_dir> <eval_all> <out_json> [report.json]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import convergence_v2 as B  # noqa: E402


def analyse(run_dir: Path, src: str, report: dict | None = None) -> dict:
    recs = {}
    for p in sorted((run_dir / "convergence").glob("*.json")):
        r = json.loads(p.read_text())
        recs[r["id"]] = r
    exp = {k: r["binding"] for k, r in recs.items() if "heldout" in r}
    mac = B.recompute(src, run_dir, expected=exp)
    pod = json.loads((run_dir / "recompute.json").read_text())
    same = {k: v for k, v in pod.items() if k != "nesting_shortfall"} == mac
    if not same:
        raise SystemExit("the Mac recompute differs from the pod's recompute.json")
    change = {q: {m: mac[q]["converged"]["markets"][m] - mac[q]["frozen"]["markets"][m] for m in mac[q]["frozen"]["markets"]}
              for q in ("q1", "q1_x7", "q4")}
    big = max(((q, m, d) for q, ms in change.items() for m, d in ms.items()), key=lambda t: abs(t[2]))
    return {"label": mac["label"], "cells": len(recs), "with_heldout": len(exp),
            "status": {k: r["status"] for k, r in recs.items()},
            "rounds": {k: len(r.get("rounds", [])) for k, r in recs.items()},
            "passed_within_three_rounds": sum(r["status"] == "passed" and len(r.get("rounds", [])) <= 3 for r in recs.values()),
            "mac_equals_pod": same, "recompute": mac, "market_change": change,
            "largest_market_change": {"q": big[0], "market": big[1], "change": big[2]},
            "nesting_shortfall": pod["nesting_shortfall"],
            **({"selection": _selection(recs, report)} if report is not None else {})}


def _selection(recs: dict, report: dict) -> dict:
    """External review d10 (Astra Pro): which run cells the registered doubling check flagged, and which were added
    unflagged (the X7-SC nesting cells of convergence-plan.md)."""
    dbl = report.get("doubling", {})
    un = sorted(k for k in recs if not (dbl.get(k) or {}).get("incomplete"))
    return {"flagged": len(recs) - len(un), "unflagged": len(un), "unflagged_cells": un}


if __name__ == "__main__":
    rep = json.loads(Path(sys.argv[4]).read_text()) if len(sys.argv) > 4 else None
    res = analyse(Path(sys.argv[1]), sys.argv[2], report=rep)
    Path(sys.argv[3]).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("cells", "passed_within_three_rounds", "mac_equals_pod", "largest_market_change")}))
