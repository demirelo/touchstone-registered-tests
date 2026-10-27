"""The sealed session's check of its H4 bundle (design draft 7, 5.3). The load check imports h4/family.py by path and
checks make_family(T, L) at the loader's constant pairs and the resource envelope (sim/h4_loader.py); the smoke evaluation
searches the family against F000, F111, and the frozen C* on the development instances (dev-train seeds) and scores the
attack against honest-max on dev-val seeds; the timing payload measures one full-budget H4 search and one full-budget
X7-SC search, each with its bounded controls, against F111 on the headline market, in one process. h4/check.json (with the
payload) is written first; then the bundle hash is computed over the finished bundle, and the printed line is the export
record {"bundle_sha256", "commit", **payload}. The payload never contains the bundle hash."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from scripts.tune_v2 import INNER  # noqa: E402
from sim.cell import SeedCache  # noqa: E402
from sim.h4_loader import CHECK_CONSTANTS, _check, bundle_sha  # noqa: E402
from sim.policies.honest import HonestMax  # noqa: E402
from sim.reference import Candidate, evaluate_gain, twin_search  # noqa: E402
from sim.search import Objective  # noqa: E402
from sim.policies.x7 import x7_family  # noqa: E402

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


def smoke(bundle: Path, rules=("F000", "F111", "C*"), markets=("dev0", "dev1"), budget=SMOKE, cred: dict | None = None) -> dict:
    mod = _module(bundle); R, E, n_train, n_eval = budget; out = {}
    for label in markets:
        mkt = RV.market(label, RV.DEV_ROOT, 0.2, dev=True)
        for rule in rules:
            j = RV.job(mkt, rule, "D2+H3", params={"cred": cred} if rule.startswith("C*") else None)   # the family is H4's
            T, L = RV.constants(j); fam = mod.make_family(T, L); cache = SeedCache()
            st = replace(RV.settings(j), restarts=int(R), evals_per_restart=int(E))
            cell = replace(RV.train_cell(j), seeds=tuple(mkt["seeds_train"][: int(n_train)]))
            at = RV.search_family(cell, fam, cache, st, twin_search(cell, fam, cache, st, seed=0))
            ev = replace(RV.eval_cell(j), seeds=tuple(mkt["seeds_val"][: int(n_eval)]))
            g = evaluate_gain(ev, fam, at.best_knobs, Candidate("honest_max", HonestMax, None), cache)
            out[f"{rule}|{label}"] = {"train_seeds": list(cell.seeds), "eval_seeds": list(ev.seeds), "attack": dict(at.best_knobs),
                                      "gain": float(g.gain.mean())}
    return out


def _timed_search(j: dict, fam, budget) -> tuple[float, int, int]:
    """One search at `budget` with its bounded controls (the runner's procedure); seconds, episodes, control vectors."""
    R, E, n_train, _ = budget; cache = SeedCache(); t0 = time.perf_counter()
    st = replace(RV.settings(j), restarts=int(R), evals_per_restart=int(E))
    cell = replace(RV.train_cell(j), seeds=tuple(j["mkt"]["seeds_train"][: int(n_train)]))
    RV.search_family(cell, fam, cache, st, twin_search(cell, fam, cache, st, seed=0))
    n = len(RV.controls(Objective(cell, fam, cache), fam))
    return time.perf_counter() - t0, int(cache.runs), n


def timing(bundle: Path, defender_commit: str, market: str = "headline", budget=None) -> dict:
    """The timing payload (design draft 7, 5.3): H4 and X7-SC at the X7-SC budget, both against F111, one process."""
    mod = _module(bundle); mkt = RV.market(market, RV.DEV_ROOT, 0.2, dev=True)
    j = RV.job(mkt, "F111", "X7-SC"); T, L = RV.constants(j)
    b = tuple(budget) if budget is not None else tuple(j["budget"])
    h4 = mod.make_family(T, L)
    hs, he, hc = _timed_search(j, h4, b); xs, xe, _ = _timed_search(j, x7_family(T, L), b)
    return {"defender_commit": str(defender_commit), "h4_seconds": hs, "x7_seconds": xs, "h4_episodes": he, "x7_episodes": xe,
            "knobs": len(h4.knobs), "controls": hc}


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=RV.ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True); ap.add_argument("--smoke", action="store_true", help="smoke budget instead of the registered inner search")
    ap.add_argument("--comparator", default=str(RV.ROOT / "experiments/v2/comparator.json"), help="the promoted comparator (frozen C*)")
    ap.add_argument("--defender-commit", default=None, help="the defender-freeze commit (default: HEAD)")
    a = ap.parse_args(argv); d = Path(a.bundle)
    import scipy
    commit = _commit(); defender = a.defender_commit or commit
    chk = {"load": load_check(d), "smoke": None, "timing": None, "scipy": scipy.__version__, "commit": commit}
    if chk["load"]["ok"]:
        cred = json.loads(Path(a.comparator).read_text())["cred"]
        chk["smoke"] = smoke(d, budget=SMOKE if a.smoke else REGISTERED, cred=cred)
        chk["timing"] = timing(d, defender, budget=SMOKE if a.smoke else None)
    (d / "h4" / "check.json").write_text(json.dumps(chk, indent=1, default=float))      # first: the hash covers it
    print(json.dumps({"bundle_sha256": bundle_sha(d), "commit": commit, **(chk["timing"] or {})}, default=float))
    return 0 if chk["load"]["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
