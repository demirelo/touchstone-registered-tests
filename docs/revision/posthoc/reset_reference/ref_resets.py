"""External review r3 (Fable 5.2), problem 2: do the 18 frozen truthful references replace their identity on the
evaluation seeds, and how much is that worth to them? Exploratory, run on the Mac.

`run`: for each (market, rule), the chosen reference candidate, its family and knobs, reset counts, the reference's mean
normalised profit, and (if it resets) the same policy's mean normalised profit with replacement disabled (X7-SC: h_R = T
and lambda = 1; D2+H3: x = 0). It records, without requiring equality, how far the Mac run is from the stored Linux
reference profits (`validation_*`): the Mac and Linux differ on some seeds (lesson in commit 9c13b88).

`summarize`: combines the per-market cell files with reset.json. A reference without replacement earns less by its
replacement value, so every gain against it rises by that value; G = g(B3) - g(R3) under either family shifts by
value(B3) - value(R3), the same for D2+H3 and D2. This is a sensitivity calculation on the stored gains, not a
re-evaluation.

Usage:
  ref_resets.py run CODE_ROOT BUNDLE POD_RECORDS OUT.json [MARKET]
  ref_resets.py summarize RESET_JSON OUT.json CELLS.json [CELLS.json ...]"""
import json
import sys
from pathlib import Path

import numpy as np

MARKETS = tuple(f"fresh{i}@rho0.2" for i in range(6))


def no_replace(family, knobs, T):
    if family == "X7-SC":
        return {**knobs, "h_R": float(T), "lambda": 1.0}
    if "x" in knobs:
        return {**knobs, "x": 0}
    return None


def summarize(cells: dict, reset: dict) -> dict:
    rv = lambda k: cells[k].get("replacement_value_to_reference") or 0.0   # noqa: E731 (no reset: no value)
    dG = {m.split("@")[0]: rv(f"{m}|F000") - rv(f"{m}|F111") for m in MARKETS}
    dC = {m.split("@")[0]: rv(f"{m}|C*") - rv(f"{m}|F111") for m in MARKETS}
    g1 = reset["base"]["G"]["D2+H3"]["pooled"]["estimate"]; g0 = reset["base"]["G"]["D2"]["pooled"]["estimate"]
    dp = sum(dG.values()) / len(MARKETS)
    return {"n": len(cells), "refs_with_any_reset": sum(1 for v in cells.values() if v.get("mean_resets", 0) > 0),
            "max_abs_replacement_value": max(abs(rv(k)) for k in cells),
            "G_shift_per_market": dG, "G_shift_pooled": dp, "Cstar_minus_R3_shift_pooled": sum(dC.values()) / len(MARKETS),
            "S_with_non_replacing_references": 1 - (g0 + dp) / (g1 + dp),
            "max_abs_validation_mean_diff": max(abs(v["validation_mean_diff"]) for v in cells.values())}


def run(T0: Path, B: Path, POD: Path, OUT: Path, only=None) -> None:
    sys.path.insert(0, str(T0 / "docs/revision/followup"))
    import reset_followup_v2 as F
    R = F.R
    from sim.cell import SeedCache, run_focal
    from sim.records import cfg_from_dict
    from sim.records_v2 import read
    root = json.loads((B / "draw/draw.json").read_text())["hash"]
    salt = json.loads((B / "draw/instances.json").read_text())["salt_sha256"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads((B / "deviation/cfg_linux.json").read_text()).items()}
    jobs = F.build_jobs(root, cfgs, json.loads((T0 / "experiments/v2/params.json").read_text()), salt)
    res = {}
    for j in jobs:
        ctx, rule = j["context"], j["rule"]
        if only and not ctx.startswith(only + "@"):
            continue
        ref = read(B / "eval-all" / "reference" / ctx / (rule.replace("*", "star") + ".json"))
        cand = ref["candidates"][ref["choice"]]
        T, L = R.constants(j); cell = R.eval_cell(j); cache = SeedCache()
        row = {"name": cand["name"], "family": cand.get("family"), "knobs": cand.get("knobs")}
        if not cand.get("family"):
            row["note"] = "no family (abstain or honest policy)"; res[f"{ctx}|{rule}"] = row; continue
        fam = R.family_for(cand["family"], T, L)
        out = run_focal(cell, lambda: fam.make(dict(cand["knobs"])), cache)
        st = F.reset_stats(out.results, cell.focal); norm = np.asarray(out.normalized, float)
        ev = json.loads((POD / "evaluate" / (j["id"].replace("|", "__").replace("*", "star") + ".json")).read_text())
        pr = np.asarray(ev["profit_ref"], float) / (np.asarray(ev["sstar"], float) / cell.cfg.N)
        row.update({k: st[k] for k in ("mean_resets", "p_any_reset", "mean_ban_rounds")})
        row.update({"ref_mean_normalized": float(norm.mean()), "validation_mean_diff": float(np.mean(norm - pr)),
                    "validation_seeds_differing": int((np.abs(norm - pr) > 1e-9).sum()), "validation_max_abs_diff": float(np.max(np.abs(norm - pr)))})
        if st["mean_resets"] > 0:
            k0 = no_replace(cand["family"], cand["knobs"], T)
            off = run_focal(cell, lambda: fam.make(dict(k0)), cache)
            row["ref_no_replace_mean_normalized"] = float(np.mean(off.normalized))
            row["replacement_value_to_reference"] = float(norm.mean() - np.mean(off.normalized))
        res[f"{ctx}|{rule}"] = row
        print(ctx, rule, row["name"], row["family"], "resets", row["mean_resets"], "repl_value", row.get("replacement_value_to_reference"), flush=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")


LABEL = ("external review r3 problem 2 (exploratory, Mac): the 18 frozen truthful references on the evaluation seeds; "
         "replacement_value_to_reference = reference normalised profit minus the same policy with replacement disabled "
         "(X7-SC: h_R = T, lambda = 1; D2+H3: x = 0). The summary adds these Mac values to the stored Linux gains (a "
         "sensitivity calculation, not a re-evaluation). The Mac reproduces the stored reference profits on average "
         "(validation_mean_diff) but not seed for seed (Mac vs Linux; commit 9c13b88).")


def main(argv):
    if argv[0] == "run":
        run(Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4]), argv[5] if len(argv) > 5 else None)
    elif argv[0] == "summarize":
        cells = {}
        for f in argv[3:]:
            cells.update(json.loads(Path(f).read_text()))
        cells = dict(sorted(cells.items()))
        out = {"label": LABEL, "cells": cells, "summary": summarize(cells, json.loads(Path(argv[1]).read_text()))}
        Path(argv[2]).write_text(json.dumps(out, indent=1) + "\n")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
