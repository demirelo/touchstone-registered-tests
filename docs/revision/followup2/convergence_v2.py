"""Run B (docs/revision/followup2/convergence-plan.md): the 14 search-flagged profit cells of the report searched further,
one doubling round at a time, until a round's doubling check passes or the cap is reached.

Round k continues the search from the best result so far with as many new restarts as registered (revision_v2
`continue_search`, restart seeds after every earlier round's), then reselects the reference from the frozen menu plus
the new candidates as the registered doubling stage does. A round passes when both changes against the previous round,
attacker and reference normalised profit on the training seeds, are below the registered threshold 0.005. Round 1
recomputes the registered doubling check (its changes are compared with the report's). The cap is three rounds, four
times the registered restarts in all. The final winner (best training value over all rounds) is evaluated on the
evaluation seeds against the unchanged frozen reference. The frozen estimates stay primary; these are a sensitivity.
The 7 flagged coalition cells are not in this run (plan, section 3)."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE.parent / "followup")); sys.path.insert(0, str(HERE))

import common as C  # noqa: E402
import reset_followup_v2 as F  # noqa: E402
import revision_v2 as R  # noqa: E402
from sim.records_v2 import read, sha_file, write  # noqa: E402

THRESHOLD = R.THRESHOLD                            # 0.005, the registered doubling threshold (design 6.5)
MAX_ROUNDS = 3
CUTS, H4_EXCLUDED = F.CUTS, F.H4_EXCLUDED
FRESH = tuple(f"fresh{i}" for i in range(6))


def _refuse(msg: str):
    raise SystemExit(f"convergence follow-up refused: {msg}")


def flagged(report: dict) -> dict:
    d = report["doubling"]; f = [k for k, v in d.items() if v.get("incomplete")]
    return {"profit": [k for k in f if d[k].get("kind") == "profit"], "coalition": [k for k in f if d[k].get("kind") != "profit"]}


def round_seed(k: int, restarts: int) -> int:
    """`continue_search` seed of round k; round 1 is the registered doubling's seed 1."""
    return 1 + (k - 1) * restarts


def cma_seeds(k: int, restarts: int) -> set:
    s = round_seed(k, restarts) + restarts                     # continue_search passes seed + restarts to cma_search
    return set(range(s + 1, s + 1 + restarts))                 # cma_search uses seed + 1 + r


def _passes(r: dict) -> bool:
    return r["attack_change"] < THRESHOLD - 1e-12 and r["reference_change"] < THRESHOLD - 1e-12


def passed_round(rounds: list) -> int | None:
    return next((r["round"] for r in rounds if _passes(r)), None)


def round1_agrees(r1: dict, registered: dict, tol: float = 1e-9) -> bool:
    return all(abs(r1[k] - registered[k]) <= tol for k in ("attack_change", "reference_change"))


def job_for(rid: str, root: str, cfgs: dict, params: dict, salt: str, smoke: bool) -> dict:
    ctx, rule, fam, _ = rid.split("|"); label = ctx.split("@")[0]
    mkt = R.market(label, root, 0.2, smoke=smoke, cfg=cfgs.get(label), salt_sha256=salt)
    return R.job(mkt, rule, fam, "profit", smoke=smoke, params=params)


def cell_inputs(src, job: dict) -> dict:
    need = F.inputs(src, [job]); p = R.path_of(src, job["id"])
    fr = read(R.path_of(src, f"freeze/{job['context']}"))
    if job["id"] not in fr["records"] or fr["records"][job["id"]] != sha_file(p):
        _refuse(f"{job['id']}: its search record differs from the original freeze")
    need[job["id"]] = fr["records"][job["id"]]
    for u, s in (read(p).get("upstream") or {}).items():
        if need.setdefault(u, s) != s:
            _refuse(f"{u}: two original records hold different hashes")
    return need


def run_cell(job: dict, out, max_rounds: int = MAX_ROUNDS) -> dict:
    from sim.cell import SeedCache
    from sim.locked import load_locked
    from sim.records import search_from_json
    from sim.reference import reference_candidates, select_reference
    from sim.search import Objective
    T, L = R.constants(job); fam = R.family_for(job["family"], T, L); cell = R.train_cell(job); st = R.settings(job); cache = SeedCache()
    rec = read(R.path_of(out, job["id"])); prev = search_from_json(rec["attack"]); twin = search_from_json(rec["twin"])
    frozen_ref, rrec, _ = R.reference_of(job, out); prev_ref = float(np.mean(rrec["per_seed_normalized"]))
    cands, _, _ = R.menu(job, out, CUTS, H4_EXCLUDED); order = tuple(load_locked()["reference_order"])
    rounds = []
    for k in range(1, max_rounds + 1):
        new = R.continue_search(Objective(cell, fam, cache), fam, st, prev, seed=round_seed(k, st.restarts))
        best = new if new.best_f > prev.best_f else replace(new, best_x=prev.best_x, best_knobs=prev.best_knobs, best_f=prev.best_f, best_source=prev.best_source)
        extra = reference_candidates(cell, fam, best, twin, [], order)
        ref = select_reference(cell, cands + [c for c in extra if c.knobs is not None], cache); ref_f = float(np.mean(ref.per_seed_normalized))
        rounds.append({"round": k, "restarts_total": st.restarts * (k + 1), "cma_seeds": sorted(cma_seeds(k, st.restarts)), "attack_f": float(best.best_f),
                       "attack_change": float(best.best_f - prev.best_f), "reference_f": ref_f, "reference_change": ref_f - prev_ref,
                       "best_knobs": dict(best.best_knobs), "best_source": best.best_source})
        prev, prev_ref = best, ref_f
        if _passes(rounds[-1]):
            break
    held = R.gain_fields(R.eval_cell(job), fam, prev.best_knobs, frozen_ref, SeedCache())
    return {"stage": "convergence", "id": job["id"], "provenance": job["provenance"], "restarts": st.restarts, "rounds": rounds,
            "status": "passed" if passed_round(rounds) else "not passed at the cap", "passed_round": passed_round(rounds),
            "frozen_best_f": float(rec["attack"]["best_f"]), "heldout": {"knobs": dict(prev.best_knobs), "seeds": list(R.eval_cell(job).seeds), **held}}


def _cell_gains(src, conv, rid: str):
    c = read(Path(conv) / "convergence" / (R._safe(rid) + ".json"))
    f = read(R.eval_path(src, rid))
    if c is not None and c["heldout"]["seeds"] != f["seeds"]:
        raise ValueError(f"{rid}: held-out seeds differ from the evaluation seeds")
    return f["gain"], (c["heldout"]["gain"] if c else f["gain"]), c is not None


def recompute(src, conv, markets=FRESH, resamples: int = C.RESAMPLES) -> dict:
    """Q1 (C* - R3, D2+H3) and Q4 (B3 - R3, D2+H3) per market and pooled, with the final winners substituted for the
    re-searched cells; descriptive, nominal paired bootstrap."""
    sub, out = [], {}
    for q, (a, b) in {"q1": ("C*", "F111"), "q4": ("F000", "F111")}.items():
        fz_a, fz_b, cv_a, cv_b = {}, {}, {}, {}
        for m in markets:
            ra, rb = (f"{m}@rho0.2|{r}|D2+H3|profit" for r in (a, b))
            (fa, ca, sa), (fb, cb, sb) = _cell_gains(src, conv, ra), _cell_gains(src, conv, rb)
            fz_a[m], fz_b[m], cv_a[m], cv_b[m] = fa, fb, ca, cb
            sub += [r for r, s in ((ra, sa), (rb, sb)) if s and r not in sub]
        out[q] = {"frozen": C.pooled_paired(fz_a, fz_b, resamples), "converged": C.pooled_paired(cv_a, cv_b, resamples)}
    return {"label": "exploratory sensitivity; the frozen estimates stay primary", **out, "substituted": sub}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True); ap.add_argument("--report", required=True)
    ap.add_argument("--draw", required=True); ap.add_argument("--instances", required=True); ap.add_argument("--cfgs", required=True); ap.add_argument("--addendum", required=True)
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json")); ap.add_argument("--cells", default=None, help="comma list; default all 14")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=MAX_ROUNDS); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv); out = Path(a.out); F.check_out(out, a.src)
    if not 1 <= a.max_rounds <= MAX_ROUNDS:
        _refuse(f"--max-rounds must be 1 to {MAX_ROUNDS}")
    from sim.records import cfg_from_dict
    report = json.loads(Path(a.report).read_text()); root = json.loads(Path(a.draw).read_text())["hash"]
    salt = json.loads(Path(a.instances).read_text())["salt_sha256"]; params = json.loads(Path(a.params).read_text())
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    cells = a.cells.split(",") if a.cells else flagged(report)["profit"]
    if bad := [c for c in cells if c not in flagged(report)["profit"]]:
        _refuse(f"not flagged profit cells: {bad}")
    out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
    jobs = [job_for(c, root, cfgs, params, salt, a.smoke) for c in cells]
    container = dict(json.loads(Path(a.addendum).read_text())["deviations"]["configs"])
    for j in jobs:                                               # headline: the registered record's configuration hash
        if j["mkt"]["label"] == "headline":
            container["headline"] = {"container_hash": read(R.path_of(a.src, j["id"]))["provenance"]["cfg_sha256"]}
    F.check_salt(out, salt, jobs); F.check_commit(jobs); F.check_code(); F.check_configs(jobs, container)
    if not a.smoke:
        F.check_pairing(a.src, jobs)
    for j in jobs:
        F.copy_inputs(a.src, out, cell_inputs(a.src, j))
    from concurrent.futures import ProcessPoolExecutor
    def done(j, rec):
        write(out / "convergence" / (R._safe(j["id"]) + ".json"), rec)
        if not a.smoke:
            r1 = rec["rounds"][0]; rec["round1_agrees_with_report"] = round1_agrees(r1, report["doubling"][j["id"]])
            write(out / "convergence" / (R._safe(j["id"]) + ".json"), rec)
    todo = [j for j in jobs if not (out / "convergence" / (R._safe(j["id"]) + ".json")).exists()]
    if a.workers > 1 and len(todo) > 1:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for j, rec in zip(todo, ex.map(run_cell, todo, [out] * len(todo), [a.max_rounds] * len(todo))):
                done(j, rec)
    else:
        for j in todo:
            done(j, run_cell(j, out, a.max_rounds))
    if not a.smoke:
        write(out / "recompute.json", recompute(a.src, out))
    F.inventory(out)
    print(json.dumps({"cells": len(jobs), "status": {j["id"]: read(out / "convergence" / (R._safe(j["id"]) + ".json"))["status"] for j in jobs}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
