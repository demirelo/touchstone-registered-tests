"""The replication's continuation stage and record loader (replication-plan.md, sections 2 and 4).
continue: the flagged cells of every rate directory, in the fixed queue order; the first cell runs alone as the
  nonzero-churn continuation gate (round 1 against this run's own doubling record); the rest run in workers that each
  install the churn-aware adapter and save their own record.
collect: per winner set (frozen, primary), gains[rate][market][rule] for replication_analysis, R3's audited share of the
  attacker's jobs per market from the diagnostics (frozen winners), and the counts of continued, unresolved, stopped and
  not-continued cells. A round-1 mismatch anywhere makes the primary set unavailable (plan section 4)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (HERE, HERE.parent / "churn", HERE.parent / "followup2", HERE.parent / "followup"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

RATE_DIRS = (0.0, 0.03, 0.05)


class Round1Mismatch(Exception):
    """Round 1 of a continuation differs from this run's doubling record: an environment or code fault."""


def analysis_rule(kind: str, rule: str) -> str:
    if kind == "cthr":
        return "C-thr"
    return {"F111": "R3", "C*": "C*", "F000": "B3"}[rule]


def _finite(xs) -> bool:
    return bool(xs) and all(isinstance(x, (int, float)) and math.isfinite(x) for x in xs)


def select_winner(frozen: list, rec: dict | None) -> tuple:
    """(gains, kind) for one flagged cell: a passed cell uses its continued winner ("continued"); a cell at the round cap
    uses its last winner ("unresolved"); a cost-stopped cell keeps the frozen winner and drops its partial rounds
    ("stopped"); a missing or nonfinite continuation keeps the frozen winner ("not continued"); a round-1 mismatch raises."""
    if rec is None:
        return frozen, "frozen"
    st = str(rec.get("status", ""))
    if st.startswith("stopped: round 1"):
        raise Round1Mismatch(rec.get("id", "?"))
    if st == "stopped at the cost cap":
        return frozen, "stopped"
    g = (rec.get("heldout") or {}).get("gain")
    if not _finite(g):
        return frozen, "not continued"
    return list(g), ("continued" if st == "passed" else "unresolved")


def _key(kind: str, p: float, jid: str) -> str:
    return f"{kind}-p{p:g}|{jid}"


def flagged_cells(base: Path, jobs_by_dir: dict) -> list:
    """Every cell whose doubling record says incomplete, as queue items (rate, market, rule, id, job, dir)."""
    import revision_v2 as R
    from sim.records_v2 import read
    out = []
    for (kind, p), jobs in jobs_by_dir.items():
        d = Path(base) / f"{kind}-p{p:g}"
        for j in jobs:
            rec = read(d / "doubling" / (R._safe(j["id"]) + ".json"))
            if rec is not None and rec.get("incomplete"):
                out.append({"rate": p, "market": j["mkt"]["label"], "rule": "Cthr" if kind == "cthr" else j["rule"],
                            "id": _key(kind, p, j["id"]), "job": j, "dir": str(d)})
    return out


def round_hours(job: dict) -> float:
    """One continuation round's admission estimate (Run B's rule): a doubling-size search and its 200-seed evaluation from
    the benchmark, times the churn slowdown (1.33 at p > 0, the churn arm's rate stages), plus 0.1 h shutdown."""
    import json as _j
    from convergence_v2 import ROOT as _ROOT
    t = _j.loads((_ROOT / "experiments/v2/benchmark/timings.json").read_text())["timings"]
    base = (t["doubling_x7"] if job.get("family") == "X7-SC" else t["doubling"]) + t["eval160"]["profit"] * 200 / 160
    return base * (1.33 if float(job.get("churn") or 0) > 0 else 1.0) / 3600 + 0.1


def run_cells(*args):
    """Run B's worker pool (each worker saves its own record); a module-level name so tests can replace it."""
    from convergence_v2 import run_cells as rc
    return rc(*args)


def write_record(dest, rec: dict) -> None:
    from sim.records_v2 import write
    write(dest, rec)


def _cont_one(job: dict, rate_dir: str, max_rounds: int, cost, hours: float) -> dict:
    """In a worker: install the churn-aware adapter, then continue one cell; round 1 is compared with this run's
    doubling record in the same rate directory. Every round is admitted with `hours` against the cost stop."""
    from continuation import install_continuation
    install_continuation()
    import convergence_v2 as B
    return B.run_cell(job, rate_dir, max_rounds=max_rounds, src=rate_dir, cost=cost, round_hours=hours)


def read_record(path):
    from sim.records_v2 import read
    return read(path)


def identical(rec) -> bool:
    """Round 1 equals this run's doubling record exactly (plan section 5: "required identical"); Run B's comparison
    allowed 1e-9 on the continuous values, so its pass alone is not enough."""
    g = (rec or {}).get("round1_gate")
    return isinstance(g, dict) and g.get("pass") is True and all(g.get(k) == 0.0 for k in ("max_knob_rel", "max_change_abs", "max_gain_abs"))


def cost_stopped(rec) -> bool:
    return str((rec or {}).get("status", "")) == "stopped at the cost cap"


STATUSES = ("passed", "not passed at the cap", "stopped at the cost cap", "stopped: round 1 differs from the registered doubling")
SMOKE_GATE = "not compared (smoke)"


def _knobs_ok(k) -> bool:
    return isinstance(k, dict) and bool(k) and _finite(list(k.values()))


def cont_problem(rec, key: str, job: dict, smoke: bool = False, max_rounds: int = 3) -> str | None:
    """A continuation record (review rep-impl-r2): stage, id, provenance, a known status; a winner it supplies ("passed"
    or "not passed at the cap") needs its own identical round-1 comparison (smoke: not compared), one to max_rounds
    rounds and a finite held-out result on the job's ordered evaluation seeds with finite knobs."""
    if not isinstance(rec, dict) or rec.get("stage") != "convergence" or rec.get("id") != key:
        return "not a continuation record of this cell"
    if rec.get("provenance") != job.get("provenance"):
        return "continuation record of another job or run"
    st = rec.get("status")
    if st not in STATUSES:
        return f"unknown continuation status {st!r}"
    if st in STATUSES[:2]:
        if not (identical(rec) or (smoke and rec.get("round1_gate") == SMOKE_GATE)):
            return "a continued winner without its own identical round-1 comparison"
        rounds = rec.get("rounds")
        if not isinstance(rounds, list) or not 1 <= len(rounds) <= max_rounds:
            return "rounds missing or beyond the cap"
        h = rec.get("heldout")
        seeds = (job.get("mkt") or {}).get("seeds_eval")
        if seeds is not None and not (_valid_held(h, seeds) and _knobs_ok(h.get("knobs"))):
            return "held-out result missing, nonfinite or on other seeds"
    return None


def _set_aside(cdir: Path, dest: Path) -> None:
    """Move a record that will be rerun out of the way (no deletion), so that a lost worker shows as a missing record and
    is never masked by the old one (review rep-impl-r2)."""
    if dest.exists():
        sup = cdir / "superseded"; sup.mkdir(parents=True, exist_ok=True)
        n = len(list(sup.glob(dest.stem + ".*.json")))
        dest.rename(sup / f"{dest.stem}.{n}.json")


def _mismatch(rec) -> bool:
    """A measured round 1 that differs from the doubling record at all. A cell refused before round 1 ("not run") or a
    smoke run ("not compared") measured nothing."""
    if rec is None:
        return False
    if str(rec.get("status", "")).startswith("stopped: round 1"):
        return True
    return isinstance(rec.get("round1_gate"), dict) and not identical(rec)


DIAG_HOURS = 60.0 * 1.33 / 3600     # one continued winner's diagnostics (stage_continue's admission: 60 s per cell at p > 0)


def _lost(cdir: Path, ids: list, hours: dict, max_rounds: int) -> None:
    from convergence_v2 import restart_hours
    write_record(cdir / "lost_cells.json", {"lost": ids, "restart_hours": restart_hours([hours[k] * max_rounds for k in ids])})


def run_queue(queue: list, base: Path, workers: int, cost=None, max_rounds: int = 3, gate: dict | None = None,
              smoke: bool = False) -> dict:
    """The nonzero-churn gate first, then the flagged cells, every cell in a child process that saves its own record
    (Run B's pool). The gate is the first p = 0.05 cell whether flagged or not (plan section 5); it runs round 1 only and
    its record (continuation/gate/) never enters a result. Exit codes: 4 a round-1 mismatch anywhere, measured or saved
    (no restart); 6 a cell error; 5 a lost worker (lost_cells.json holds the restart estimate); 3 a cost stop (a
    cost-refused gate stops before the queue); 0 otherwise. A resume reuses this run's completed records and reruns only
    cost-stopped ones."""
    import convergence_v2  # noqa: F401  (first: it puts scripts/ on the path)
    import revision_v2 as R
    if gate is None:
        raise SystemExit("replication refused: the continuation needs its gate cell (the first p = 0.05 cell)")
    cdir = Path(base) / "continuation"; cdir.mkdir(parents=True, exist_ok=True)
    gdest = cdir / "gate" / (R._safe(gate["id"]) + ".json")
    dest = lambda c: cdir / (R._safe(c["id"]) + ".json")
    items = [(gate, gdest)] + [(c, dest(c)) for c in queue]
    saved = {d: read_record(d) for _, d in items}
    other = [c["id"] for c, d in items if saved[d] is not None and saved[d].get("provenance") != c["job"].get("provenance")]
    if other:                                                            # plan section 5: reuse only this run's records
        raise SystemExit(f"replication refused: saved continuation records of another job or run: {other[:3]}")
    if any(_mismatch(r) for r in saved.values()):
        return {"run": 0, "exit": 4, "gate": "round-1 mismatch on record: continuation stays stopped"}   # also on resume (plan section 4)
    bad = [(c["id"], saved[d].get("status")) for c, d in items if saved[d] is not None and saved[d].get("status") not in STATUSES]
    if bad:                                                              # review rep-impl-r2: no reuse of an unknown record
        raise SystemExit(f"replication refused: saved continuation records with an unknown status: {bad[:3]}")
    hours = {c["id"]: round_hours(c["job"]) for c, _ in items}
    run = 0
    if saved[gdest] is None or cost_stopped(saved[gdest]):
        _set_aside(cdir, gdest)
        lost, failed = run_cells(_cont_one, [gate], [(gate["job"], gate["dir"], 1, cost, hours[gate["id"]])], 1, [gdest],
                                 [{"id": gate["id"], "gate": True}])
        run += 1
        if failed:
            return {"run": run, "failed": failed, "exit": 6, "gate": "the gate cell raised an error"}
        if lost:
            _lost(cdir, lost, hours, 1)
            return {"run": run, "lost": lost, "exit": 5, "gate": "the gate cell's worker was lost"}
    g = read_record(gdest)
    if _mismatch(g):
        return {"run": run, "exit": 4, "gate": "round-1 mismatch at the gate: continuation stopped"}
    if cost_stopped(g):
        return {"run": run, "exit": 3, "gate": "the gate cell was refused at the cost cap: no further cell started"}
    if not smoke and not identical(g):                                   # the gate must prove identity, not just not fail
        return {"run": run, "exit": 4, "gate": "the gate has no identical round-1 comparison: continuation stopped"}
    todo = [c for c in queue if saved[dest(c)] is None or cost_stopped(saved[dest(c)])]   # same order; completed cells reused
    for c in todo:
        _set_aside(cdir, dest(c))
    lost, failed = ([], {}) if not todo else run_cells(
        _cont_one, todo, [(c["job"], c["dir"], max_rounds, cost, hours[c["id"]]) for c in todo], workers,   # module-level fn
        [dest(c) for c in todo], [{"id": c["id"]} for c in todo])
    recs = [read_record(dest(c)) for c in todo]
    mismatch = [c["id"] for c, r in zip(todo, recs) if _mismatch(r)]
    stopped = [c["id"] for c, r in zip(todo, recs) if cost_stopped(r)]
    if lost and not mismatch and not failed:
        _lost(cdir, lost, hours, max_rounds)
    code = 4 if mismatch else 6 if failed else 5 if lost else 3 if stopped else 0
    return {"run": run + len(todo), "lost": lost, "failed": failed, "mismatch": mismatch, "stopped": stopped, "exit": code}


FIELDS = ("gain", "profit_attack", "profit_ref", "sstar", "eff_attack")


def _n_agents(job: dict) -> int:
    cfg = job["mkt"]["cfg"]
    return int(cfg["N"] if isinstance(cfg, dict) else cfg.N)


def _valid_held(h, seeds) -> bool:
    return isinstance(h, dict) and list(h.get("seeds") or []) == list(seeds) and \
        all(_finite(h.get(f)) and len(h[f]) == len(seeds) for f in FIELDS)


def _deps_problem(d: Path, rec: dict, want: set) -> str | None:
    import revision_v2 as R
    from sim.records_v2 import sha_file
    up = rec.get("upstream")
    if not isinstance(up, dict) or set(up) != set(want):
        return "dependency set differs"
    for u, h in up.items():
        q = R.path_of(d, u)
        if not q.is_file() or sha_file(q) != h:
            return f"dependency hash differs: {u}"
    return None


def base_problem(d: Path, job: dict, ev, db) -> str | None:
    """The evaluation and doubling records of one cell (plan section 4; review rep-impl-r2): stage, id, provenance, finite
    values on the job's ordered evaluation seeds; the evaluation depends exactly on the context's freeze, the rule's
    reference and the cell's search, the doubling on those and the reference's menu, every hash equal to the file in
    the rate directory; the doubling is a profit record with finite changes, a held-out winner with finite knobs, and
    its flag equals the frozen rule (revision_v2.doubling_report)."""
    import revision_v2 as R
    seeds = job["mkt"]["seeds_eval"]; ctx = job["context"]
    fz, rid = f"freeze/{ctx}", f"reference/{ctx}/{job['rule']}"
    if ev is None:
        return "no evaluation record"
    if ev.get("stage") != "evaluate" or ev.get("id") != job["id"] or ev.get("provenance") != job["provenance"]:
        return "evaluation record of another stage, cell or run"
    if not _valid_held(ev, seeds):
        return "evaluation values nonfinite or on other seeds"
    if x := _deps_problem(d, ev, {fz, rid, job["id"]}):
        return "evaluation: " + x
    if db is None:
        return "no doubling record"
    if db.get("stage") != "doubling" or db.get("id") != job["id"] or db.get("provenance") != job["provenance"] or db.get("kind") != "profit":
        return "doubling record of another stage, cell, run or kind"
    ch = [db.get("attack_change"), db.get("reference_change")]
    if not _finite(ch) or not isinstance(db.get("incomplete"), bool):
        return "doubling changes nonfinite or flag missing"
    if db["incomplete"] != any(c >= R.THRESHOLD - 1e-12 for c in ch):
        return "doubling flag differs from its changes"
    h = db.get("heldout")
    if not _valid_held(h, seeds) or not _knobs_ok(h.get("knobs")):
        return "doubling held-out result missing, nonfinite or on other seeds"
    ref = read_record(R.path_of(d, rid))
    if ref is None or not isinstance(ref.get("upstream"), dict):
        return "no reference record"
    if x := _deps_problem(d, db, set(ref["upstream"]) | {fz, rid, job["id"]}):
        return "doubling: " + x
    return None


def _shares_ok(sh) -> bool:
    """Newcomer audit counts: per episode a list of [served, audited] bins, the same number of bins in every episode,
    finite and nonnegative, audited at most served."""
    per = (sh or {}).get("per_episode") if isinstance(sh, dict) else None
    if not isinstance(per, list) or not per:
        return False
    nb = None
    for e in per:
        f = e.get("focal") if isinstance(e, dict) else None
        if not isinstance(f, list) or not f or (nb is not None and len(f) != nb):
            return False
        nb = len(f)
        for b in f:
            if not (isinstance(b, list) and len(b) == 2 and _finite(b) and 0 <= b[1] <= b[0]):
                return False
    return True


def diag_ok(row, seeds, knobs) -> bool:
    """A diagnostics row (frozen: diagnostics.json cells[...]["base"]; continued: its own record) for this winner: its
    knobs, the job's ordered evaluation seeds, finite per-seed profits and well-formed audit counts (review rep-impl-r2)."""
    return isinstance(row, dict) and row.get("knobs") == knobs and list(row.get("seeds") or []) == list(seeds) and \
        _finite(row.get("normalized")) and len(row["normalized"]) == len(seeds) and _shares_ok(row.get("shares"))


def cont_diag_ok(rec, key: str, job: dict, knobs) -> bool:
    return isinstance(rec, dict) and rec.get("stage") == "continued diagnostics" and rec.get("id") == key and \
        rec.get("provenance") == job["provenance"] and diag_ok(rec, job["mkt"]["seeds_eval"], knobs)


def terms_of(h: dict, n: int) -> dict:
    """Per seed: gain = attack term - reference term, each normalised by S*/N (sim/reference.evaluate_gain)."""
    sc = [x / n for x in h["sstar"]]
    return {"gain": list(h["gain"]), "attack": [a / s for a, s in zip(h["profit_attack"], sc)],
            "reference": [r / s for r, s in zip(h["profit_ref"], sc)], "eff_attack": list(h["eff_attack"]), "seeds": list(h["seeds"])}


def _audit_of(shares: dict) -> tuple:
    per = shares["per_episode"]
    fo = [sum(e["focal"][b][i] for e in per for b in range(len(e["focal"]))) for i in (0, 1)]
    return fo[1], fo[0]                                                   # (audited, served)


def collect(base: Path, jobs_by_dir: dict, gate: dict | None, smoke: bool = False) -> dict:
    """Records for both winner sets (recs[rate][market][rule] with gains, attack and reference terms, efficiency and
    seeds), R3's audit counts for both sets, and the winner counts. Every record is checked before use (review
    rep-impl-r2): a cell whose evaluation or doubling record fails base_problem is unscorable (plan section 4); a frozen
    diagnostics row that fails diag_ok gives no audit count. Only flagged cells look at a continuation record; a flagged
    cell without one is "not continued". The primary set is unavailable after a round-1 mismatch in any continuation
    record, without this run's identical gate record (also when no cell is flagged), or when a flagged cell's
    continuation record fails cont_problem. A continued R3 winner's audit count needs its checked continued diagnostics."""
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    base = Path(base); cdir = base / "continuation"
    allrec = [read_record(q) for q in sorted(cdir.glob("*.json")) + sorted((cdir / "gate").glob("*.json")) if q.name != "lost_cells.json"]
    mismatch = any(_mismatch(r) for r in allrec)
    g = read_record(cdir / "gate" / (R._safe(gate["id"]) + ".json")) if gate else None
    gjob = {**(gate or {}).get("job", {}), "mkt": None}
    gate_ok = g is not None and cont_problem(g, gate["id"], gjob, smoke, max_rounds=1) is None and \
        g.get("status") in STATUSES[:2] and (identical(g) or (smoke and g.get("round1_gate") == SMOKE_GATE))
    frozen, primary, problems, unscorable = {}, {}, [], []
    counts = {"frozen": 0, "continued": 0, "unresolved": 0, "stopped": 0, "not continued": 0}
    audit = {"frozen": {}, "primary": {}}
    bad_cont = False
    for (kind, p), jobs in jobs_by_dir.items():
        rk = "0" if p == 0 else f"{p:g}"; d = base / f"{kind}-p{p:g}"
        diag = (read_record(d / "diagnostics.json") or {}).get("cells") or {} if kind == "menu" else {}
        for j in jobs:
            m, r = j["mkt"]["label"].replace("fresh", "rep"), analysis_rule(kind, j["rule"])
            ev = read_record(R.eval_path(d, j["id"])); db = read_record(d / "doubling" / (R._safe(j["id"]) + ".json"))
            seeds = j["mkt"]["seeds_eval"]
            if (why := base_problem(d, j, ev, db)) is not None:
                unscorable.append(f"{kind}-p{p:g}|{j['id']}: {why}"); continue
            n = _n_agents(j); fz = terms_of(ev, n)
            frozen.setdefault(rk, {}).setdefault(m, {})[r] = fz
            fa = None
            if r == "R3" and kind == "menu":
                ck = f"{j['context']}|{j['rule']}"
                row = (diag.get(ck) or {}).get("base")
                sr = read_record(R.path_of(d, j["id"])) or {}
                if diag_ok(row, seeds, (sr.get("attack") or {}).get("best_knobs")):
                    fa = _audit_of(row["shares"]); audit["frozen"].setdefault(rk, {})[m] = fa
                elif ck in diag:
                    problems.append(f"{kind}-p{p:g}|{j['id']}: frozen diagnostics fail their checks")
            win, kw, crec = fz, "frozen", None
            key = _key(kind, p, j["id"])
            if db["incomplete"]:
                crec = read_record(cdir / (R._safe(key) + ".json"))
                if crec is None:
                    kw = "not continued"
                elif (why := cont_problem(crec, key, j, smoke)) is not None:
                    problems.append(f"{key}: {why}"); bad_cont = True; kw = "not continued"
                else:
                    try:
                        _, kw = select_winner(fz["gain"], crec)
                    except Round1Mismatch:
                        kw = "frozen"
                    if kw in ("continued", "unresolved"):
                        win = terms_of(crec["heldout"], n)
            counts[kw] += 1
            primary.setdefault(rk, {}).setdefault(m, {})[r] = win
            if r == "R3" and kind == "menu" and fa is not None:
                if kw in ("continued", "unresolved"):
                    cd = read_record(cdir / "diagnostics" / (R._safe(key) + ".json"))
                    if cont_diag_ok(cd, key, j, crec["heldout"]["knobs"]):
                        audit["primary"].setdefault(rk, {})[m] = _audit_of(cd["shares"])
                    elif cd is not None:
                        problems.append(f"{key}: continued diagnostics fail their checks")
                else:
                    audit["primary"].setdefault(rk, {})[m] = fa
    if not gate_ok:
        problems.append("no identical gate record of this run's gate cell")
    bad = mismatch or not gate_ok or bad_cont
    return {"frozen": frozen, "primary": None if bad else primary, "audit": audit, "counts": counts,
            "round1_mismatch": mismatch, "gate_ok": gate_ok, "problems": problems, "unscorable": unscorable}


def _diag_cont(job: dict, knobs: dict) -> dict:
    """In a worker: the churn arm's diagnostic run (churn_v2._diag_one) for a continued winner's knobs on the evaluation
    seeds under the cell's churn: per-seed normalised profits and newcomer audit counts (plan section 3, expectation 5
    on the primary winners)."""
    import churn_v2
    import numpy as np
    import revision_v2 as R
    from sim.cell import SeedCache, run_focal
    churn_v2.install()
    T, L = R.constants(job); fam = R.family_for("D2+H3", T, L); cell = R.eval_cell(job)
    fr = run_focal(cell, lambda: fam.make(dict(knobs)), SeedCache())
    return {"stage": "continued diagnostics", "provenance": job["provenance"], "knobs": dict(knobs),
            "seeds": [int(x) for x in cell.seeds], "normalized": [float(x) for x in fr.normalized],
            "mean_normalized": float(np.mean(fr.normalized)), "shares": churn_v2.newcomer_shares(fr.results, cell.focal)}


def run_diagnostics(base: Path, jobs_by_dir: dict, workers: int, smoke: bool = False) -> dict:
    """The diagnostics of R3's continued winners (menu cells at p = 0 and 0.05 whose continuation passed or reached the
    cap) in Run B's pool; records under continuation/diagnostics/, reused on resume when bound to the same job."""
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    cdir = Path(base) / "continuation"; todo, args, dests, extras = [], [], [], []
    for (kind, p), jobs in jobs_by_dir.items():
        if kind != "menu" or p not in (0.0, 0.05):
            continue
        for j in jobs:
            if j["rule"] != "F111":
                continue
            key = _key(kind, p, j["id"]); crec = read_record(cdir / (R._safe(key) + ".json"))
            if crec is None or cont_problem(crec, key, j, smoke) is not None or crec["status"] not in STATUSES[:2]:
                continue
            dest = cdir / "diagnostics" / (R._safe(key) + ".json"); old = read_record(dest)
            if cont_diag_ok(old, key, j, crec["heldout"]["knobs"]):
                continue
            _set_aside(cdir / "diagnostics", dest)              # a stale or foreign record is rerun, never reused
            todo.append({"id": key}); args.append((j, crec["heldout"]["knobs"])); dests.append(dest); extras.append({"id": key})
    lost, failed = ([], {}) if not todo else run_cells(_diag_cont, todo, args, workers, dests, extras)
    if lost and not failed:                                     # the launcher's restart reads this estimate (exit 5)
        _lost(cdir, lost, {k: DIAG_HOURS for k in lost}, 1)
    return {"run": len(todo), "lost": lost, "failed": failed, "exit": 6 if failed else 5 if lost else 0}
