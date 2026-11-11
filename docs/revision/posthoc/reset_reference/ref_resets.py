"""Fable r3 problem 2: do the 18 frozen truthful references replace their identity on the evaluation seeds?
For each (market, rule): the chosen reference candidate, its family and knobs, reset counts, and (if it resets) the
reference's mean normalised profit with replacement disabled. Validation: reference normalised profit per seed must equal
the D2 winner's normalised profit (Mac diagnostics) minus the stored D2 gain."""
import json, sys
from pathlib import Path
import numpy as np

T0 = Path(sys.argv[1]); B = Path(sys.argv[2]); POD = Path(sys.argv[3]); DIAG = Path(sys.argv[4]); OUT = Path(sys.argv[5]); ONLY = sys.argv[6] if len(sys.argv) > 6 else None
sys.path.insert(0, str(T0 / "docs/revision/followup"))
import reset_followup_v2 as F  # noqa: E402
R = F.R
from sim.cell import SeedCache, run_focal  # noqa: E402
from sim.records_v2 import read  # noqa: E402
from sim.records import cfg_from_dict  # noqa: E402

root = json.loads((B / "draw/draw.json").read_text())["hash"]
salt = json.loads((B / "draw/instances.json").read_text())["salt_sha256"]
cfgs = {k: cfg_from_dict(v) for k, v in json.loads((B / "deviation/cfg_linux.json").read_text()).items()}
params = json.loads((T0 / "experiments/v2/params.json").read_text())
jobs = F.build_jobs(root, cfgs, params, salt)
diag = json.loads(DIAG.read_text())


def no_replace(family, knobs, T):
    if family == "X7-SC":
        return {**knobs, "h_R": float(T), "lambda": 1.0}
    if "x" in knobs:
        return {**knobs, "x": 0}
    return None


res = {}
for j in jobs:
    ctx, rule = j["context"], j["rule"]
    if ONLY and not ctx.startswith(ONLY + "@"):
        continue
    ref = read(B / "eval-all" / "reference" / ctx / (rule.replace("*", "star") + ".json"))
    cand = ref["candidates"][ref["choice"]]
    T, L = R.constants(j); cell = R.eval_cell(j); cache = SeedCache()
    fam = R.family_for(cand["family"], T, L) if cand.get("family") else None
    row = {"name": cand["name"], "family": cand.get("family"), "knobs": cand.get("knobs")}
    if fam is None:
        row["note"] = "no family (abstain or honest policy)"; res[f"{ctx}|{rule}"] = row; continue
    run = run_focal(cell, lambda: fam.make(dict(cand["knobs"])), cache)
    st = F.reset_stats(run.results, cell.focal)
    norm = np.asarray(run.normalized, float)
    d2 = np.asarray(diag[f"{ctx}|{rule}"]["d2_base"]["normalized"], float)
    gain = np.asarray(json.loads((POD / "evaluate" / (j["id"].replace("|", "__").replace("*", "star") + ".json")).read_text())["gain"], float)
    row.update({k: st[k] for k in ("mean_resets", "p_any_reset", "mean_ban_rounds")})
    row["ref_mean_normalized"] = float(norm.mean())
    ev = json.loads((POD / "evaluate" / (j["id"].replace("|", "__").replace("*", "star") + ".json")).read_text())
    scale = np.asarray(ev["sstar"], float) / cell.cfg.N; pr = np.asarray(ev["profit_ref"], float) / scale
    row["validation_mean_diff"] = float(np.mean(norm - pr)); row["validation_seeds_differing"] = int((np.abs(norm - pr) > 1e-9).sum())
    row["validation_max_abs_diff"] = float(np.max(np.abs(norm - pr)))
    if st["mean_resets"] > 0:
        k0 = no_replace(cand["family"], cand["knobs"], T)
        off = run_focal(cell, lambda: fam.make(dict(k0)), cache)
        row["ref_no_replace_mean_normalized"] = float(np.mean(off.normalized))
        row["replacement_value_to_reference"] = float(norm.mean() - np.mean(off.normalized))
    res[f"{ctx}|{rule}"] = row
    print(ctx, rule, row["name"], row["family"], "clip", (cand.get("knobs") or {}).get("clip"), "resets", row["mean_resets"],
          "valid_mean", f"{row['validation_mean_diff']:.1e}", "n_diff", row["validation_seeds_differing"], "repl_value", row.get("replacement_value_to_reference"), flush=True)
OUT.write_text(json.dumps(res, indent=1) + "\n")
