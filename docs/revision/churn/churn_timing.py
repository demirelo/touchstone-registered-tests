import json, sys, time
from pathlib import Path
sys.path.insert(0, "docs/revision/churn")
import churn_v2 as C
from sim.cell import SeedCache, run_focal
from sim.records import cfg_from_dict
R = C.R; M = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")
root = json.loads((M / "draw/draw.json").read_text())["hash"]; salt = json.loads((M / "draw/instances.json").read_text())["salt_sha256"]
R.install_salt(root, Path("/private/tmp"))
cfgs = {k: cfg_from_dict(v) for k, v in json.loads((M / "deviation/cfg_linux.json").read_text()).items()}
params = json.loads(Path("experiments/v2/params.json").read_text())
C.install()
mkt = R.market("fresh0", root, 0.2, cfg=cfgs["fresh0"], salt_sha256=salt)
base = R.job(mkt, "F111", "D2+H3", "profit", params=params)
T, L = R.constants(base); fam = R.family_for("D2+H3", T, L)
knobs = json.loads(R.path_of(M / "eval/all", base["id"]).read_text())["attack"]["best_knobs"]
for p in (None, 0.01, 0.05):
    j = base if p is None else C.churn_job(base, p)
    cell = R.eval_cell(j); cell = type(cell)(**{**cell.__dict__, "seeds": cell.seeds[:40]})
    t0 = time.perf_counter(); fr = run_focal(cell, lambda: fam.make(dict(knobs)), SeedCache()); dt = time.perf_counter() - t0
    sh = C.newcomer_shares(fr.results, cell.focal)
    print(json.dumps({"p": p, "seconds_40_episodes": round(dt, 2), "mean_norm": round(float(fr.normalized.mean()), 5),
                      "honest_reps_per_ep": sh["honest_replacements_per_episode"], "focal_identities_per_ep": round(sum(sum(1 for e in r.entity_of if e == cell.focal) for r in fr.results) / 40, 2)}))
