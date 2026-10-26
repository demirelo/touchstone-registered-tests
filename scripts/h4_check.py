"""The sealed session's check of its H4 bundle (design 5.3; operations plan Task 1). The load check imports h4/family.py by
path and checks make_family(T, L) at the loader's constant pairs (sim/h4_loader.py); the smoke evaluation searches the
family against F000 and F111 on the development instances (dev-train seeds) and scores the attack against honest-max on
dev-val seeds. h4/check.json is written last, because the bundle hash covers it; the printed line is the bundle hash."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from scripts.tune_v2 import INNER  # noqa: E402
from sim.cell import SeedCache  # noqa: E402
from sim.h4_loader import CHECK_CONSTANTS, _check, bundle_sha  # noqa: E402
from sim.policies.honest import HonestMax  # noqa: E402
from sim.reference import Candidate, evaluate_gain, twin_search  # noqa: E402

SMOKE = RV.SMOKE                                      # restarts, evaluations, train seeds, eval seeds
REGISTERED = (*INNER, 20)                             # the registered inner search, scored on the 20 dev-val seeds


def _module(bundle: Path):
    spec = importlib.util.spec_from_file_location("touchstone_h4_check", Path(bundle) / "h4" / "family.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def load_check(bundle: Path) -> dict:
    out = {"ok": False, "problem": None, "constants": [list(c) for c in CHECK_CONSTANTS]}
    try:
        mod = _module(bundle)
        if not hasattr(mod, "BINARY"):
            out["problem"] = "the module defines no BINARY"; return out
        for T, L in CHECK_CONSTANTS:
            problem = _check(mod.make_family(T, L), tuple(mod.BINARY))
            if problem:
                out["problem"] = problem; return out
    except Exception as e:                          # the family is the session's own code: report, do not crash
        out["problem"] = f"load failed: {type(e).__name__}: {e}"; return out
    out["ok"] = True
    return out


def smoke(bundle: Path, rules=("F000", "F111"), markets=("dev0", "dev1"), budget=SMOKE) -> dict:
    mod = _module(bundle); R, E, n_train, n_eval = budget; out = {}
    for label in markets:
        mkt = RV.market(label, RV.DEV_ROOT, 0.2, dev=True)
        for rule in rules:
            j = RV.job(mkt, rule, "D2+H3")            # the cell, rule, and public constants; the family is H4's
            T, L = RV.constants(j); fam = mod.make_family(T, L); cache = SeedCache()
            st = replace(RV.settings(j), restarts=int(R), evals_per_restart=int(E))
            cell = replace(RV.train_cell(j), seeds=tuple(mkt["seeds_train"][: int(n_train)]))
            at = RV.search_family(cell, fam, cache, st, twin_search(cell, fam, cache, st, seed=0))
            ev = replace(RV.eval_cell(j), seeds=tuple(mkt["seeds_val"][: int(n_eval)]))
            g = evaluate_gain(ev, fam, at.best_knobs, Candidate("honest_max", HonestMax, None), cache)
            out[f"{rule}|{label}"] = {"train_seeds": list(cell.seeds), "eval_seeds": list(ev.seeds), "attack": dict(at.best_knobs),
                                      "gain": float(g.gain.mean())}
    return out


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=RV.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True); ap.add_argument("--smoke", action="store_true", help="smoke budget instead of the registered inner search")
    a = ap.parse_args(argv); d = Path(a.bundle)
    import scipy
    chk = {"load": load_check(d), "smoke": None, "scipy": scipy.__version__, "commit": _commit()}
    if chk["load"]["ok"]:
        chk["smoke"] = smoke(d, budget=SMOKE if a.smoke else REGISTERED)
    (d / "h4" / "check.json").write_text(json.dumps(chk, indent=1, default=float))
    print(bundle_sha(d))
    return 0 if chk["load"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
