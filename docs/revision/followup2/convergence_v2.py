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
import guards as G  # noqa: E402
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


CLAIM = ("a cell that passes 'passed the registered incremental check within three rounds' (a capped search extension "
         "of R restarts per round); this is not convergence, not optimality, and not a bound on the remaining search error")
DEVIATIONS = ("continued searches of the 14 flagged profit cells beyond the registered doubling, up to three rounds of R restarts",
              "the final winner is evaluated against the unchanged frozen reference; reselected references are diagnostics only",
              "unflagged cells, frozen banks and X7-SC's original D2+H3 incumbents are unchanged; the 7 flagged coalition cells and "
              "the unchecked fresh factorial cells are not in this run", "exploratory sensitivity after the report; the frozen estimates stay primary")
KNOB_TOL, VAL_TOL = 1e-9, 1e-9


def compare_round1(registered: dict, r1: dict) -> dict:
    """Round 1 against the registered doubling record: exact on the seeds and discrete held-out knobs; 1e-9 on the
    continuous knobs, both changes and the held-out gains; every value finite."""
    problems = []
    ha, hb = registered["heldout"], r1["heldout"]
    if not G.finite(ha["gain"], hb["gain"], hb["knobs"], [r1["attack_change"], r1["reference_change"]]):
        problems.append("nonfinite value")
    if ha["seeds"] != hb["seeds"]:
        problems.append("seeds differ")
    ka, kb = ha["knobs"], hb["knobs"]; disc = [k for k in ka if isinstance(ka[k], int) and not isinstance(ka[k], bool)]
    if set(ka) != set(kb) or any(ka[k] != kb[k] for k in disc):
        problems.append("discrete knob differs")
    rel = max((abs(ka[k] - kb[k]) / max(abs(ka[k]), 1e-300) for k in ka if k not in disc and k in kb), default=0.0)
    chg = max(abs(registered[k] - r1[k]) for k in ("attack_change", "reference_change"))
    gd = max((abs(x - y) for x, y in zip(ha["gain"], hb["gain"])), default=0.0) if len(ha["gain"]) == len(hb["gain"]) else float("inf")
    if not (rel <= KNOB_TOL and chg <= VAL_TOL and gd <= VAL_TOL):
        problems.append(f"tolerance exceeded (knobs {rel:.3g}, changes {chg:.3g}, gains {gd:.3g})")
    return {"pass": not problems, "max_knob_rel": rel, "max_change_abs": chg, "max_gain_abs": gd, "problems": problems}


def decide(k: int, last: dict, gate: dict | None, cost_ok: bool, max_rounds: int = MAX_ROUNDS) -> str:
    """After round k: stop on a round-1 mismatch, on a pass, at the round cap, or (before the next round) at the cost cap."""
    if k == 1 and gate is not None and not gate["pass"]:
        return "round-1 mismatch"
    if _passes(last):
        return "passed"
    if k >= max_rounds:
        return "round cap"
    return "continue" if cost_ok else "cost cap"


def check_run_evidence(paths, smoke: bool, gate: bool) -> None:
    if smoke or gate:
        return
    if not paths:
        _refuse("no reproduction evidence given for a full run")
    G.check_evidence(paths)


def merge_inputs(needs: list[dict]) -> dict:
    merged = {}
    for n in needs:
        for k, v in n.items():
            if merged.setdefault(k, v) != v:
                _refuse(f"{k}: two cells list different hashes")
    return merged


def run_cell(job: dict, out, max_rounds: int = MAX_ROUNDS, src=None, cost: tuple | None = None, round_hours: float = 0.0) -> dict:
    from sim.cell import SeedCache
    from sim.locked import load_locked
    from sim.records import search_from_json
    from sim.reference import reference_candidates, select_reference
    from sim.search import Objective
    T, L = R.constants(job); fam = R.family_for(job["family"], T, L); cell = R.train_cell(job); st = R.settings(job); cache = SeedCache()
    rec = read(R.path_of(out, job["id"])); prev = search_from_json(rec["attack"]); twin = search_from_json(rec["twin"])
    frozen_ref, rrec, _ = R.reference_of(job, out); prev_ref = float(np.mean(rrec["per_seed_normalized"]))
    cands, _, _ = R.menu(job, out, CUTS, H4_EXCLUDED); order = tuple(load_locked()["reference_order"])
    stopper = G.CostStop(*cost) if cost else None
    rounds, gate, outcome = [], None, "round cap"
    for k in range(1, max_rounds + 1):
        new = R.continue_search(Objective(cell, fam, cache), fam, st, prev, seed=round_seed(k, st.restarts))
        best = new if new.best_f > prev.best_f else replace(new, best_x=prev.best_x, best_knobs=prev.best_knobs, best_f=prev.best_f, best_source=prev.best_source)
        extra = reference_candidates(cell, fam, best, twin, [], order)
        ref = select_reference(cell, cands + [c for c in extra if c.knobs is not None], cache); ref_f = float(np.mean(ref.per_seed_normalized))
        rounds.append({"round": k, "restarts_total": st.restarts * (k + 1), "cma_seeds": sorted(cma_seeds(k, st.restarts)), "attack_f": float(best.best_f),
                       "attack_change": float(best.best_f - prev.best_f), "reference_f": ref_f, "reference_change": ref_f - prev_ref,
                       "best_knobs": dict(best.best_knobs), "best_source": best.best_source})
        if k == 1 and src is not None:                          # the registered doubling's held-out winner is round 1's search winner
            reg = read(Path(src) / "doubling" / (R._safe(job["id"]) + ".json"))
            h1 = R.gain_fields(R.eval_cell(job), fam, new.best_knobs, frozen_ref, SeedCache())
            r1 = {**rounds[0], "heldout": {"knobs": dict(new.best_knobs), "seeds": list(R.eval_cell(job).seeds), "gain": h1["gain"]}}
            gate = compare_round1(reg, r1) if reg is not None else {"pass": False, "problems": ["no registered doubling record"]}
        prev, prev_ref = best, ref_f
        outcome = decide(k, rounds[-1], gate, stopper.allow(f"round {k + 1}", round_hours) if stopper else True, max_rounds)
        if outcome != "continue":
            break
    status = {"passed": "passed", "round cap": "not passed at the cap", "cost cap": "stopped at the cost cap",
              "round-1 mismatch": "stopped: round 1 differs from the registered doubling"}[outcome]
    res = {"stage": "convergence", "id": job["id"], "provenance": job["provenance"], "restarts": st.restarts, "rounds": rounds, "status": status,
           "passed_round": passed_round(rounds), "round1_gate": gate if gate is not None else "not compared (smoke)", "claim": CLAIM,
           "frozen_best_f": float(rec["attack"]["best_f"])}
    if outcome != "round-1 mismatch":
        held = R.gain_fields(R.eval_cell(job), fam, prev.best_knobs, frozen_ref, SeedCache())
        res["heldout"] = {"knobs": dict(prev.best_knobs), "seeds": list(R.eval_cell(job).seeds), **held}
    return res


def gate_cell(job: dict, out, src) -> dict:
    """Gate mode: round 1 only, compared with the registered doubling record (saved full-budget evidence)."""
    r = run_cell(job, out, max_rounds=1, src=src)
    return {"stage": "convergence gate", "cell": job["id"], "pass": bool(r["round1_gate"] != "not compared (smoke)" and r["round1_gate"]["pass"]),
            "comparison": r["round1_gate"], "environment": G.environment()}


def _cell_gains(src, conv, rid: str):
    c = read(Path(conv) / "convergence" / (R._safe(rid) + ".json"))
    f = read(R.eval_path(src, rid))
    if c is not None and ((c.get("binding") or {}).get("smoke") is not False or "heldout" not in c):
        raise ValueError(f"{rid}: not a validated full-run result (binding)")
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
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True); ap.add_argument("--report", required=True)
    ap.add_argument("--draw", required=True); ap.add_argument("--instances", required=True); ap.add_argument("--cfgs", required=True); ap.add_argument("--addendum", required=True)
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json")); ap.add_argument("--cells", default=None, help="comma list; default all 14")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=MAX_ROUNDS); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--gate", action="store_true", help="round 1 only, compared with the registered doubling")
    ap.add_argument("--evidence", action="append", default=[], help="saved gate files that must report a pass (full runs)")
    ap.add_argument("--cap-usd", dest="cap", type=float, default=3.00); ap.add_argument("--usd-per-hour", dest="rate", type=float, default=0.56)
    ap.add_argument("--started-at", dest="started", type=float, default=None)
    a = ap.parse_args(argv)
    G.pin_settings(); out = Path(a.out); F.check_out(out, a.src)
    if not 1 <= a.max_rounds <= MAX_ROUNDS:
        _refuse(f"--max-rounds must be 1 to {MAX_ROUNDS}")
    check_run_evidence(a.evidence, a.smoke, a.gate)
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
            G.check_budget(j, R.path_of(a.src, j["id"]))
    F.copy_inputs(a.src, out, merge_inputs([cell_inputs(a.src, j) for j in jobs]))     # one call: the helper refuses added keys
    files = {"driver": Path(__file__), "plan": HERE / "convergence-plan.md", "report": Path(a.report)}
    if a.gate:
        for j in jobs:
            write(out / "gate" / (R._safe(j["id"]) + ".json"), gate_cell(j, out, a.src))
        G.inventory(out, DEVIATIONS, files, argv)
        return 0 if all(read(out / "gate" / (R._safe(j["id"]) + ".json"))["pass"] for j in jobs) else 4
    t = json.loads((ROOT / "experiments/v2/benchmark/timings.json").read_text())["timings"]
    started = a.started if a.started is not None else __import__("time").time()
    path = lambda j: out / "convergence" / (R._safe(j["id"]) + ".json")
    bind = lambda j: G.binding(inputs_sha=G.sha_json(cell_inputs(a.src, j)), provenance=j["provenance"], smoke=a.smoke,
                               settings={"max_rounds": a.max_rounds, "threshold": THRESHOLD, "seeds": "1+(k-1)R"}, driver_sha=sha_file(Path(__file__)))
    todo = [j for j in jobs if not G.reusable(path(j), bind(j))]
    hours = lambda j: (t["doubling_x7"] if j["family"] == "X7-SC" else t["doubling"]) / 3600
    stop = G.CostStop(a.cap, a.rate, started)
    if todo and not stop.allow("cells", max(hours(j) for j in todo)):
        write(out / "cost_stop.json", stop.report()); G.inventory(out, DEVIATIONS, files, argv)
        return 3
    srcs = [None if a.smoke else a.src] * len(todo); costs = [(a.cap, a.rate, started)] * len(todo)
    from concurrent.futures import ProcessPoolExecutor
    if a.workers > 1 and len(todo) > 1:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            res = list(ex.map(run_cell, todo, [out] * len(todo), [a.max_rounds] * len(todo), srcs, costs, [hours(j) for j in todo]))
    else:
        res = [run_cell(j, out, a.max_rounds, s, c, hours(j)) for j, s, c in zip(todo, srcs, costs)]
    for j, rec in zip(todo, res):
        write(path(j), {**rec, "binding": bind(j)})
    status = {j["id"]: read(path(j))["status"] for j in jobs}
    mismatch = [k for k, v in status.items() if v.startswith("stopped: round 1")]
    if not a.smoke and not mismatch:
        write(out / "recompute.json", recompute(a.src, out))
    G.inventory(out, DEVIATIONS, files, argv)
    print(json.dumps({"cells": len(jobs), "status": status}))
    return 4 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
