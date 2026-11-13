"""Run B (docs/revision/followup2/convergence-plan.md, draft 3): the 14 search-flagged profit cells of the report and the
X7-SC cells with a nesting shortfall of at least 0.005 (posthoc `nesting`) searched further, one round of R restarts at a
time, until a round's check passes or the cap is reached; nesting cells run at least two rounds and, from round 2, also
start from the doubled D2+H3 winner embedded in X7-SC.

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


def cells_for(report: dict, nesting: dict) -> dict:
    """The run's cells: the flagged profit cells, then every X7-SC cell whose nesting shortfall (posthoc `nesting`) is at
    least the doubling threshold (draft 3, Fable 5.2 r2 new problem 2)."""
    base = sorted(flagged(report)["profit"])
    nest = sorted(f"{k}|X7-SC|profit" for k, v in nesting["cells"].items() if v["shortfall"] >= THRESHOLD - 1e-12)
    return {"cells": base + [c for c in nest if c not in base], "nesting": nest}


def round_incumbents(k: int, prev_knobs: dict, embedded: dict | None) -> dict:
    """Round 1 keeps the registered doubling's incumbent; from round 2 a nesting cell also gets the doubled D2+H3 winner
    embedded in X7-SC (a deviation, so that the nesting gap can close)."""
    inc = {"previous_best": dict(prev_knobs)}
    if k >= 2 and embedded is not None:
        inc["embedded_doubled_d2h3"] = dict(embedded)
    return inc


def shortfall_report(nesting: dict, final_gains: dict) -> dict:
    res = {}
    for rid, g in final_gains.items():
        c = nesting["cells"][rid.rsplit("|", 2)[0]]
        res[rid] = {"before": c["shortfall"], "after": c["best_d2h3"] - float(np.mean(g)), "best_d2h3": c["best_d2h3"]}
    return res


def round_seed(k: int, restarts: int) -> int:
    """`continue_search` seed of round k; round 1 is the registered doubling's seed 1."""
    return 1 + (k - 1) * restarts


def cma_seeds(k: int, restarts: int) -> set:
    s = round_seed(k, restarts) + restarts                     # continue_search passes seed + restarts to cma_search
    return set(range(s + 1, s + 1 + restarts))                 # cma_search uses seed + 1 + r


def _passes(r: dict) -> bool:
    return r["attack_change"] < THRESHOLD - 1e-12 and r["reference_change"] < THRESHOLD - 1e-12


def passed_round(rounds: list, min_rounds: int = 1) -> int | None:
    """The first eligible passing round (from `min_rounds`)."""
    return next((r["round"] for r in rounds if r["round"] >= min_rounds and _passes(r)), None)


def final_status(rounds: list, outcome: str, min_rounds: int = 1) -> tuple:
    """The reported status and pass round agree with the final outcome."""
    status = {"passed": "passed", "round cap": "not passed at the cap", "cost cap": "stopped at the cost cap",
              "round-1 mismatch": "stopped: round 1 differs from the registered doubling"}[outcome]
    return status, (passed_round(rounds, min_rounds) if outcome == "passed" else None)


def place_heldout(status: str, held: dict) -> dict:
    """A cost-stopped cell keeps its frozen estimate as primary; its partial result goes to a separate field."""
    return {"partial": held} if status == "stopped at the cost cap" else {"heldout": held}


def check_rounds(max_rounds: int, gate: bool, nesting: list) -> None:
    if not gate and nesting and max_rounds < 2:
        _refuse("--max-rounds must be at least 2 for a continuation run with nesting cells")


def deps_for(report, posthoc, registered_doubling, embedded) -> dict:
    """What a result depends on besides its inputs and driver: helpers, plan, report, posthoc, the registered doubling
    record of the cell, and the embedded doubled D2+H3 incumbent (nesting cells)."""
    h = lambda p: sha_file(p) if p is not None and Path(p).exists() else None
    return {"reset_followup_v2.py": h(HERE.parent / "followup" / "reset_followup_v2.py"), "guards.py": h(HERE / "guards.py"), "common.py": h(HERE / "common.py"),
            "plan": h(HERE / "convergence-plan.md"), "report": h(report), "posthoc": h(posthoc), "registered_doubling": h(registered_doubling),
            "embedded_incumbent": G.sha_json(embedded) if embedded is not None else None}


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
DEVIATIONS = ("continued searches of the 14 flagged profit cells and of the X7-SC cells with a nesting shortfall of at least 0.005, "
              "beyond the registered doubling, up to three rounds of R restarts",
              "from round 2 a nesting cell's X7-SC search also starts from the doubled D2+H3 winner embedded in X7-SC, and such a cell runs at least two rounds",
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


def decide(k: int, last: dict, gate: dict | None, cost_ok: bool, max_rounds: int = MAX_ROUNDS, min_rounds: int = 1) -> str:
    """After round k: stop on a round-1 mismatch, on a pass (from round `min_rounds`), at the round cap, or (before the
    next round) at the cost cap."""
    if k == 1 and gate is not None and not gate["pass"]:
        return "round-1 mismatch"
    if k >= min_rounds and _passes(last):
        return "passed"
    if k >= max_rounds:
        return "round cap"
    return "continue" if cost_ok else "cost cap"


GATE_CELLS = ("headline@rho0.2|F111|X7-SC|profit", "fresh1@rho0.2|F111|D2+H3|profit")


def check_run_evidence(paths, smoke: bool, gate: bool, cells: dict) -> None:
    """A full run needs, for each gate cell, a passing full-budget gate record from the Mac and one from this machine,
    bound to the cell's current inputs and this driver."""
    if smoke or gate:
        return
    if not paths:
        _refuse("no reproduction evidence given for a full run")
    G.check_gate_evidence(paths, cells)


def merge_inputs(needs: list[dict]) -> dict:
    merged = {}
    for n in needs:
        for k, v in n.items():
            if merged.setdefault(k, v) != v:
                _refuse(f"{k}: two cells list different hashes")
    return merged


def worker_cost_args(stop) -> tuple:
    """The arguments a worker uses to rebuild the validated cost stop: the same cap, rate, accounting start (the recorded
    open event), prior spend, STOP file and soft deadline."""
    import time as _t
    return (stop.cap, stop.rate, stop.started, _t.time, stop.prior, str(stop.stop_file) if stop.stop_file else None, stop.soft)


def run_cell(job: dict, out, max_rounds: int = MAX_ROUNDS, src=None, cost: tuple | None = None, round_hours: float = 0.0,
             embedded: dict | None = None, min_rounds: int = 1, reference=None) -> dict:
    from sim.cell import SeedCache
    from sim.locked import load_locked
    from sim.records import search_from_json
    from sim.reference import reference_candidates, select_reference
    from sim.search import Objective, cma_search
    T, L = R.constants(job); fam = R.family_for(job["family"], T, L); cell = R.train_cell(job); st = R.settings(job); cache = SeedCache()
    rec = read(R.path_of(out, job["id"])); prev = search_from_json(rec["attack"]); twin = search_from_json(rec["twin"])
    frozen_ref, rrec, _ = R.reference_of(job, out); prev_ref = float(np.mean(rrec["per_seed_normalized"]))
    cands, _, _ = R.menu(job, out, CUTS, H4_EXCLUDED); order = tuple(load_locked()["reference_order"])
    stopper = G.CostStop(*cost) if cost else None
    emb = R.embed_h3(embedded, T) if embedded is not None else None
    rounds, gate, outcome = [], None, "round cap"
    if stopper and not stopper.allow("round 1", round_hours):           # admission before the cell's first round
        return {"stage": "convergence", "id": job["id"], "provenance": job["provenance"], "restarts": st.restarts, "rounds": [],
                "status": "stopped at the cost cap", "passed_round": None, "round1_gate": "not run", "claim": CLAIM, "cost": stopper.report()}
    for k in range(1, max_rounds + 1):
        obj = Objective(cell, fam, cache); obj.archive.update(prev.archive)     # revision_v2.continue_search, with the round's incumbents
        new = cma_search(obj, fam, st, round_seed(k, st.restarts) + st.restarts, incumbents=round_incumbents(k, prev.best_knobs, emb))
        best = new if new.best_f > prev.best_f else replace(new, best_x=prev.best_x, best_knobs=prev.best_knobs, best_f=prev.best_f, best_source=prev.best_source)
        extra = reference_candidates(cell, fam, best, twin, [], order)
        ref = select_reference(cell, cands + [c for c in extra if c.knobs is not None], cache); ref_f = float(np.mean(ref.per_seed_normalized))
        rounds.append({"round": k, "restarts_total": st.restarts * (k + 1), "cma_seeds": sorted(cma_seeds(k, st.restarts)), "attack_f": float(best.best_f),
                       "attack_change": float(best.best_f - prev.best_f), "reference_f": ref_f, "reference_change": ref_f - prev_ref,
                       "best_knobs": dict(best.best_knobs), "best_source": best.best_source})
        if k == 1 and src is not None:                          # the registered doubling's held-out winner is round 1's search winner
            reg = read(reference) if reference is not None else read(Path(src) / "doubling" / (R._safe(job["id"]) + ".json"))
            h1 = R.gain_fields(R.eval_cell(job), fam, new.best_knobs, frozen_ref, SeedCache())
            r1 = {**rounds[0], "heldout": {"knobs": dict(new.best_knobs), "seeds": list(R.eval_cell(job).seeds), "gain": h1["gain"]}}
            gate = compare_round1(reg, r1) if reg is not None else {"pass": False, "problems": ["no registered doubling record"]}
            gate["heldout_knobs"], gate["heldout_mean"] = dict(new.best_knobs), float(np.mean(h1["gain"]))
        prev, prev_ref = best, ref_f
        outcome = decide(k, rounds[-1], gate, stopper.allow(f"round {k + 1}", round_hours) if stopper else True, max_rounds, min_rounds)
        if outcome != "continue":
            break
    status, passed = final_status(rounds, outcome, min_rounds)
    res = {"stage": "convergence", "id": job["id"], "provenance": job["provenance"], "restarts": st.restarts, "rounds": rounds, "status": status,
           "passed_round": passed, "round1_gate": gate if gate is not None else "not compared (smoke)", "claim": CLAIM,
           "frozen_best_f": float(rec["attack"]["best_f"]), "embedded_doubled_d2h3": emb is not None, "min_rounds": min_rounds,
           "cost": stopper.report() if stopper else None}
    if outcome != "round-1 mismatch":
        held = R.gain_fields(R.eval_cell(job), fam, prev.best_knobs, frozen_ref, SeedCache())
        res.update(place_heldout(status, {"knobs": dict(prev.best_knobs), "seeds": list(R.eval_cell(job).seeds), **held}))
    return res


def frozen_doubling(job: dict, out) -> Path:
    """The frozen doubling stage (revision_v2.stage_doubling) for this cell on this machine, saved as a reference record."""
    p = Path(out) / "gate" / "frozen" / (R._safe(job["id"]) + ".json")
    if read(p) is None:
        write(p, {"stage": "doubling", "id": job["id"], **R.stage_doubling(job, Path(out), CUTS, H4_EXCLUDED)})
    return p


def gate_cell(job: dict, out, src, site: str, bind: dict, cost: tuple | None = None, round_hours: float = 0.0) -> dict:
    """Gate mode: round 1 only. On the Mac it is compared with the frozen doubling stage run on the same machine (flagged
    cells diverge across platforms); on the pod, with the registered doubling record. Saved full-budget evidence bound to
    the cell's inputs, this driver, the site, and the environment."""
    ref = frozen_doubling(job, out) if site == "mac" else None
    r = run_cell(job, out, max_rounds=1, src=src, cost=cost, round_hours=round_hours, reference=ref)
    ok = isinstance(r["round1_gate"], dict) and r["round1_gate"]["pass"] is True
    stopped = r.get("round1_gate") == "not run"        # refused by the cell's own admission before round 1: a cost stop, not a mismatch
    return {"stage": "convergence gate", "cell": job["id"], "pass": bool(ok), "cost_stopped": stopped, "cost": r.get("cost") if stopped else None, "site": site, "compared_with": "frozen stage, same machine" if ref else "registered record",
            "comparison": r["round1_gate"],
            "round1": (r.get("rounds") or [None])[0],
            "binding": bind, "environment": G.environment()}


def _cell_gains(src, conv, rid: str, expected: dict):
    f = read(R.eval_path(src, rid))
    if rid not in expected:
        return f["gain"], f["gain"], False
    c = read(Path(conv) / "convergence" / (R._safe(rid) + ".json"))
    if c is None or c.get("id") != rid or c.get("binding") != expected[rid] or "heldout" not in c:
        raise ValueError(f"{rid}: no validated result of this run (binding)")
    g = c["heldout"]["gain"]
    if c["heldout"]["seeds"] != f["seeds"] or len(g) != len(f["gain"]) or not G.finite(g):
        raise ValueError(f"{rid}: held-out seeds, length or values invalid")
    return f["gain"], g, True


def recompute(src, conv, markets=FRESH, resamples: int = C.RESAMPLES, expected: dict | None = None) -> dict:
    """Q1 (C* - R3; D2+H3 and X7-SC) and Q4 (B3 - R3, D2+H3) per market and pooled, with this run's validated final
    winners (`expected`: cell id -> binding) substituted and the frozen winners elsewhere; descriptive."""
    expected = expected or {}
    for rid in expected:
        if not (Path(conv) / "convergence" / (R._safe(rid) + ".json")).exists():
            raise ValueError(f"{rid}: the run's result is missing")
    sub, out = [], {}
    for q, (a, b, fam) in {"q1": ("C*", "F111", "D2+H3"), "q1_x7": ("C*", "F111", "X7-SC"), "q4": ("F000", "F111", "D2+H3")}.items():
        fz_a, fz_b, cv_a, cv_b = {}, {}, {}, {}
        for m in markets:
            ra, rb = (f"{m}@rho0.2|{r}|{fam}|profit" for r in (a, b))
            if read(R.eval_path(src, ra)) is None or read(R.eval_path(src, rb)) is None:
                continue
            (fa, ca, sa), (fb, cb, sb) = _cell_gains(src, conv, ra, expected), _cell_gains(src, conv, rb, expected)
            fz_a[m], fz_b[m], cv_a[m], cv_b[m] = fa, fb, ca, cb
            sub += [r for r, s_ in ((ra, sa), (rb, sb)) if s_ and r not in sub]
        if fz_a:
            out[q] = {"frozen": C.pooled_paired(fz_a, fz_b, resamples), "converged": C.pooled_paired(cv_a, cv_b, resamples)}
    return {"label": "exploratory sensitivity; the frozen estimates stay primary; " + C.SCOPE, **out, "substituted": sub}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True); ap.add_argument("--report", required=True)
    ap.add_argument("--posthoc", default=str(HERE.parent / "posthoc" / "posthoc.json"), help="its `nesting` block adds X7-SC cells")
    ap.add_argument("--draw", required=True); ap.add_argument("--instances", required=True); ap.add_argument("--cfgs", required=True); ap.add_argument("--addendum", required=True)
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json")); ap.add_argument("--cells", default=None, help="comma list; default the whole run")
    ap.add_argument("--max-rounds", dest="max_rounds", type=int, default=MAX_ROUNDS); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--gate", action="store_true", help="round 1 only, compared with the registered doubling")
    ap.add_argument("--site", choices=("mac", "pod"), default="pod", help="where this runs; a pod run is paid and needs --started-at")
    ap.add_argument("--evidence", action="append", default=[], help="gate records (Mac and pod) for the gate cells (full runs)")
    ap.add_argument("--cap-usd", dest="cap", type=float, default=4.25); ap.add_argument("--usd-per-hour", dest="rate", type=float, default=0.56)
    ap.add_argument("--started-at", dest="started", type=float, default=None)
    ap.add_argument("--attempts", default=None, help="the launcher's attempts file (closed attempts count toward the cap); required for a paid run")
    ap.add_argument("--ledger", default=str(ROOT / "docs/revision/budget-ledger.json"), help="recorded spend of earlier launches")
    ap.add_argument("--run-tag", dest="run_tag", default=None, help="ledger tag prefix of this run's launches (e.g. convergence); required for a paid run")
    ap.add_argument("--stop-file", dest="stop_file", default=None, help="the launcher's STOP file, checked before each stage or round")
    ap.add_argument("--soft-deadline", dest="soft", type=float, default=None, help="the launcher's soft deadline (epoch seconds)")
    a = ap.parse_args(argv)
    G.pin_settings(); out = Path(a.out); F.check_out(out, a.src)
    if not 1 <= a.max_rounds <= MAX_ROUNDS:
        _refuse(f"--max-rounds must be 1 to {MAX_ROUNDS}")
    from sim.records import cfg_from_dict
    report = json.loads(Path(a.report).read_text()); nesting = json.loads(Path(a.posthoc).read_text())["nesting"]
    root = json.loads(Path(a.draw).read_text())["hash"]; salt = json.loads(Path(a.instances).read_text())["salt_sha256"]
    params = json.loads(Path(a.params).read_text()); cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    plan = cells_for(report, nesting); check_rounds(a.max_rounds, a.gate, plan["nesting"])
    cells = a.cells.split(",") if a.cells else plan["cells"]
    if bad := [c for c in cells if c not in plan["cells"]]:
        _refuse(f"not cells of this run: {bad}")
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
    needs = {j["id"]: cell_inputs(a.src, j) for j in jobs}
    F.copy_inputs(a.src, out, merge_inputs(list(needs.values())))     # one call: the helper refuses added keys
    drv = sha_file(Path(__file__))
    emb = lambda j: (report["doubling"].get(R.cell_id(j["context"], j["rule"], "D2+H3", "profit")) or {}).get("heldout", {}).get("knobs") if j["id"] in plan["nesting"] else None
    dbl_rec = lambda j: Path(a.src) / "doubling" / (R._safe(j["id"]) + ".json")
    def bind_for(j, inputs, smoke, gate):
        st = {"max_rounds": 1 if gate else a.max_rounds, "threshold": THRESHOLD, "seeds": "1+(k-1)R", "gate": gate,
              "nesting": (j["id"] in plan["nesting"]) and not gate}
        return G.binding(inputs_sha=G.sha_json(inputs), provenance=j["provenance"], smoke=smoke, settings=st, driver_sha=drv,
                         deps=deps_for(a.report, a.posthoc, dbl_rec(j), None if gate else emb(j)))
    bind = lambda j: bind_for(j, needs[j["id"]], a.smoke, a.gate)
    if not a.smoke and not a.gate:
        gj = {c: job_for(c, root, cfgs, params, salt, False) for c in GATE_CELLS}
        check_run_evidence(a.evidence, a.smoke, a.gate, {c: bind_for(j, cell_inputs(a.src, j), False, True) for c, j in gj.items()})
    t = json.loads((ROOT / "experiments/v2/benchmark/timings.json").read_text())["timings"]; ev = t["eval160"]["profit"] * 200 / 160
    hours = lambda j: ((t["doubling_x7"] if j["family"] == "X7-SC" else t["doubling"]) + ev) / 3600 + 0.1     # a round, its evaluation, shutdown
    paid = a.site == "pod" and not a.smoke
    stop = G.paid_cost_stop(a.cap, a.rate, a.started, a.attempts, a.ledger, a.run_tag, stop_file=a.stop_file, soft_deadline=a.soft) if paid else None
    cargs = worker_cost_args(stop) if paid else None
    files = {"driver": Path(__file__), "plan": HERE / "convergence-plan.md", "report": Path(a.report), "posthoc": Path(a.posthoc)}
    if a.gate:
        res = {}
        for j in jobs:                                           # serial; admission before each gate cell
            if stop and not stop.allow(f"gate {j['id']}", hours(j)):
                write(out / "cost_stop.json", stop.report()); G.inventory(out, DEVIATIONS, files, argv); return 3
            res[j["id"]] = gate_cell(j, out, a.src, a.site, bind(j), cargs, hours(j))
            if res[j["id"]]["cost_stopped"]:                     # shared launcher review r1: exit 3 (a stop), and no gate record
                write(out / "cost_stop.json", {**(stop.report() if stop else {}), "inner": res[j["id"]]["cost"], "cell": j["id"]})
                G.inventory(out, DEVIATIONS, files, argv); return 3
            write(out / "gate" / (R._safe(j["id"]) + f"__{a.site}.json"), res[j["id"]])
            if not res[j["id"]]["pass"]:                         # review r2: a measured mismatch ends the gate at once (exit 4);
                G.inventory(out, DEVIATIONS, files, argv); return 4   # no later cell starts, so no later stop can mask it
        G.inventory(out, DEVIATIONS, files, argv)
        return 0 if all(r["pass"] for r in res.values()) else 4
    path = lambda j: out / "convergence" / (R._safe(j["id"]) + ".json")
    todo = sorted((j for j in jobs if not G.reusable(path(j), bind(j))), key=lambda j: j["family"] != "X7-SC")   # longest first
    minr = lambda j: 2 if j["id"] in plan["nesting"] else 1
    args = [(j, out, a.max_rounds, None if a.smoke else a.src, cargs, hours(j), emb(j), minr(j)) for j in todo]
    from concurrent.futures import ProcessPoolExecutor
    if a.workers > 1 and len(todo) > 1:
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            res = list(ex.map(run_cell, *zip(*args)))
    else:
        res = [run_cell(*x) for x in args]
    for j, rec in zip(todo, res):
        write(path(j), {**rec, "binding": bind(j)})
    status = {j["id"]: read(path(j))["status"] for j in jobs}
    mismatch = [k for k, v in status.items() if v.startswith("stopped: round 1")]
    if not a.smoke and not mismatch:
        done = {j["id"]: bind(j) for j in jobs if "heldout" in read(path(j))}           # cost-stopped cells keep their frozen estimates
        nest_done = {k: read(out / "convergence" / (R._safe(k) + ".json"))["heldout"]["gain"] for k in plan["nesting"] if k in done}
        write(out / "recompute.json", {**recompute(a.src, out, expected=done), "nesting_shortfall": shortfall_report(nesting, nest_done)})
    G.inventory(out, DEVIATIONS, files, argv)
    print(json.dumps({"cells": len(jobs), "status": status}))
    return 4 if mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
