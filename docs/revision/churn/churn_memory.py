"""Peak resident memory of one 200-seed evaluation profile on fresh0 under R3, with and without churn (plan section 7).
Usage: churn_memory.py P   (P = none, 0.01 or 0.05); prints the peak RSS in MB."""
import json, resource, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import churn_v2 as C
from sim.cell import SeedCache, run_focal
from sim.records import cfg_from_dict
R = C.R; M = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")
root = json.loads((M / "draw/draw.json").read_text())["hash"]; salt = json.loads((M / "draw/instances.json").read_text())["salt_sha256"]
R.install_salt(root, Path("/private/tmp"))
cfgs = {k: cfg_from_dict(v) for k, v in json.loads((M / "deviation/cfg_linux.json").read_text()).items()}
C.install(); p = None if sys.argv[1] == "none" else float(sys.argv[1])
base = R.job(R.market("fresh0", root, 0.2, cfg=cfgs["fresh0"], salt_sha256=salt), "F111", "D2+H3", "profit", params=json.loads((C.F.ROOT / "experiments/v2/params.json").read_text()))
j = base if p is None else C.churn_job(base, p); T, L = R.constants(j); fam = R.family_for("D2+H3", T, L)
knobs = json.loads(R.path_of(M / "eval/all", base["id"]).read_text())["attack"]["best_knobs"]
fr = run_focal(R.eval_cell(j), lambda: fam.make(dict(knobs)), SeedCache())
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({"p": p, "episodes": len(fr.results), "peak_rss_mb": round(rss / (1024 * 1024 if sys.platform == "darwin" else 1024), 1)}))
