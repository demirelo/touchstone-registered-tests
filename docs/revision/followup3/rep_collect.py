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


def _num(x) -> bool:
    """A finite number: not a boolean, and an int too large for a float is not (review rep-impl-r5: 10**400)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        return False
    try:
        return math.isfinite(float(x))
    except OverflowError:
        return False


def _finite(xs) -> bool:
    """A nonempty list of finite numbers; any other type is not (reviews rep-impl-r4, r5)."""
    return isinstance(xs, (list, tuple)) and bool(xs) and all(_num(x) for x in xs)


def _same(a, b) -> bool:
    """Equality that does not let True stand for 1 or 1.0 for 1 (review rep-impl-r5): the canonical JSON texts agree."""
    try:
        return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    except (TypeError, ValueError):
        return False


def _d(x):
    """A record is a JSON object; any other root (a list, a number) counts as no valid record (review rep-impl-r5)."""
    return x if isinstance(x, dict) else None


def _checked(fn):
    """A record check never raises on a malformed record: a wrong type anywhere is a problem, not an error (review
    rep-impl-r4). The explicit type checks come first; this is the last line."""
    import functools

    @functools.wraps(fn)
    def run(*a, **k):
        try:
            return fn(*a, **k)
        except (TypeError, ValueError, KeyError, AttributeError, IndexError, OverflowError, ZeroDivisionError) as e:
            return f"malformed record ({type(e).__name__})"
    return run


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
    rec = _d(rec)
    """Round 1 equals this run's doubling record exactly (plan section 5: "required identical"); Run B's comparison
    allowed 1e-9 on the continuous values, so its pass alone is not enough."""
    g = (rec or {}).get("round1_gate")
    return isinstance(g, dict) and g.get("pass") is True and g.get("problems") == [] and \
        all(g.get(k) == 0.0 and not isinstance(g.get(k), bool) for k in ("max_knob_rel", "max_change_abs", "max_gain_abs"))


def cost_stopped(rec) -> bool:
    return str((_d(rec) or {}).get("status", "")) == "stopped at the cost cap"


STATUSES = ("passed", "not passed at the cap", "stopped at the cost cap", "stopped: round 1 differs from the registered doubling")
SMOKE_GATE = "not compared (smoke)"


def _knobs_ok(k) -> bool:
    return isinstance(k, dict) and bool(k) and all(isinstance(x, str) for x in k) and _finite(list(k.values()))


def _rounds_problem(rec: dict, max_rounds: int) -> str | None:
    """Run B's rounds (convergence_v2.run_cell; review rep-impl-r3): numbered 1..k with k <= max_rounds, finite search and
    reference values with finite knobs; "passed" exactly when the last round is the first that passes the doubling
    threshold, "not passed at the cap" when k equals the cap and no round passes; the held-out winner is the last round's."""
    from convergence_v2 import _passes
    rounds = rec.get("rounds")
    if not isinstance(rounds, list) or not 1 <= len(rounds) <= max_rounds:
        return "rounds missing or beyond the cap"
    for i, r in enumerate(rounds):
        if not isinstance(r, dict) or type(r.get("round")) is not int or r["round"] != i + 1 or not _finite([r.get(k) for k in ("attack_f", "attack_change", "reference_f", "reference_change")]) \
                or not _knobs_ok(r.get("best_knobs")):
            return f"round {i + 1} malformed or nonfinite"
    ok = [_passes(r) for r in rounds]
    if rec["status"] == "passed" and not (ok[-1] and not any(ok[:-1])):
        return "status passed without a final passing round"
    if rec["status"] == STATUSES[1] and (len(rounds) != max_rounds or any(ok)):
        return "status at the cap without the capped, unpassed rounds"
    if not _same((rec.get("heldout") or {}).get("knobs"), rounds[-1]["best_knobs"]):
        return "held-out winner differs from the last round's winner"
    return None


def _round1_ready(rec, doubling, search) -> bool:
    """Round 1 was measured and both records it is compared with are well-formed: then any disagreement below is a
    round-1 mismatch, not a malformed record."""
    rec, doubling, search = _d(rec), _d(doubling), _d(search)
    if rec is None or doubling is None or search is None or not isinstance(rec.get("round1_gate"), dict):
        return False
    rounds, h, g = rec.get("rounds"), doubling.get("heldout"), rec["round1_gate"]
    if not (isinstance(rounds, list) and rounds and isinstance(rounds[0], dict) and isinstance(h, dict) and
            _finite(h.get("gain")) and _knobs_ok(h.get("knobs")) and isinstance(search.get("attack"), dict) and
            _knobs_ok(search["attack"].get("best_knobs"))):
        return False
    r1, fh = rounds[0], rec.get("heldout")                  # the measured values themselves must be well-formed
    if not (_finite([r1.get("attack_change"), r1.get("reference_change"), g.get("heldout_mean")]) and
            _knobs_ok(r1.get("best_knobs")) and _knobs_ok(g.get("heldout_knobs"))):
        return False
    return not (isinstance(fh, dict) and _same(fh.get("knobs"), h["knobs"])) or _finite(fh.get("gain"))


def _round1_problem(rec: dict, doubling, search=None) -> str | None:
    """Round 1 against this cell's own doubling record and frozen search (reviews rep-impl-r4, r5): with zero
    differences, the comparison's round-1 winner equals the doubling's held-out knobs, its held-out mean equals the mean
    of the doubling's held-out gains (the same np.mean of the same values), and round 1's two changes equal the
    doubling's; round 1's best knobs are the doubling's winner or the frozen search winner (the better of the two); and a
    final winner equal to the doubling's winner has the doubling's held-out gains exactly. All five hold on every Run B
    record with an identical round 1 (76 records; 48 with that final winner)."""
    import numpy as np
    if not _round1_ready(rec, doubling, search):
        return "no valid doubling or search record to check round 1 against"
    g, r1, h = rec["round1_gate"], rec["rounds"][0], doubling["heldout"]
    if not _same(g.get("heldout_knobs"), h["knobs"]):
        return "round-1 winner differs from the doubling record's held-out winner"
    if not _same(g.get("heldout_mean"), float(np.mean(h["gain"]))):
        return "round-1 held-out mean differs from the doubling record's"
    if not (_same(r1.get("attack_change"), doubling.get("attack_change")) and _same(r1.get("reference_change"), doubling.get("reference_change"))):
        return "round-1 changes differ from the doubling record's"
    if not any(_same(r1.get("best_knobs"), k) for k in (h["knobs"], search["attack"]["best_knobs"])):
        return "round-1 best knobs are neither the doubling winner nor the frozen winner"
    fh = rec.get("heldout")
    if isinstance(fh, dict) and _same(fh.get("knobs"), h["knobs"]) and not _same(fh.get("gain"), h["gain"]):
        return "the doubling winner's held-out gains differ from the doubling record's"
    return None


def doubling_of(d, jid: str):
    import revision_v2 as R
    return _d(read_record(Path(d) / "doubling" / (R._safe(jid) + ".json")))


def search_of(d, jid: str):
    import revision_v2 as R
    try:
        return _d(read_record(R.path_of(d, jid)))
    except ValueError:                                   # not a cell id: no search record
        return None


@_checked
def cont_problem(rec, key: str, job: dict, smoke: bool = False, max_rounds: int = 3, doubling=None, search=None) -> str | None:
    """A continuation record (reviews rep-impl-r2, r3): stage, id, provenance, a known status; a winner it supplies
    ("passed" or "not passed at the cap") needs its own identical round-1 comparison with a finite round-1 winner (smoke:
    not compared), well-formed rounds (_rounds_problem) and a finite held-out result with positive normalizers on the
    job's ordered evaluation seeds; a measured round 1 must agree with this cell's doubling record (`doubling`;
    _round1_problem). The job must carry its evaluation seeds: no check is skipped."""
    seeds = (job.get("mkt") or {}).get("seeds_eval")
    if not seeds:
        return "the job has no evaluation seeds to check against"
    if not isinstance(rec, dict) or rec.get("stage") != "convergence" or not _same(rec.get("id"), key):
        return "not a continuation record of this cell"
    if not _same(rec.get("provenance"), job.get("provenance")):
        return "continuation record of another job or run"
    st = rec.get("status")
    if st not in STATUSES:
        return f"unknown continuation status {st!r}"
    if st in STATUSES[:2]:
        g = rec.get("round1_gate")
        if not (identical(rec) or (smoke and g == SMOKE_GATE)):
            return "a continued winner without its own identical round-1 comparison"
        if isinstance(g, dict) and not (_knobs_ok(g.get("heldout_knobs")) and _finite([g.get("heldout_mean")])):
            return "round-1 comparison without a finite round-1 winner"
        h = rec.get("heldout")
        if not (_valid_held(h, seeds) and _knobs_ok(h.get("knobs"))):
            return "held-out result missing, nonfinite, on other seeds or with a zero normalizer"
        if x := _rounds_problem(rec, max_rounds):
            return x
        if isinstance(g, dict) and (x := _round1_problem(rec, doubling, search)):
            return x
    return None


def _set_aside(cdir: Path, dest: Path) -> None:
    """Move a record that will be rerun out of the way (no deletion), so that a lost worker shows as a missing record and
    is never masked by the old one (review rep-impl-r2)."""
    if dest.exists():
        sup = cdir / "superseded"; sup.mkdir(parents=True, exist_ok=True)
        n = len(list(sup.glob(dest.stem + ".*.json")))
        dest.rename(sup / f"{dest.stem}.{n}.json")


def _mismatch(rec, doubling=None, search=None) -> bool:
    """A measured round 1 that differs from the doubling record at all: the recorded status, a comparison that is not
    identical, or (with the cell's doubling and search records) any recorded round-1 value that disagrees with them
    (_round1_problem; review rep-impl-r5). A cell refused before round 1 ("not run") or a smoke run ("not compared")
    measured nothing."""
    rec = _d(rec)
    if rec is None:
        return False
    if str(rec.get("status", "")).startswith("stopped: round 1"):
        return True
    if not isinstance(rec.get("round1_gate"), dict):
        return False
    if not identical(rec):
        return True
    return _round1_ready(rec, doubling, search) and _round1_problem(rec, doubling, search) is not None


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
    saved = {d: _d(read_record(d)) for _, d in items}                   # a non-object root counts as no record
    dbl = {d: doubling_of(c["dir"], c["job"]["id"]) for c, d in items}; srch = {d: search_of(c["dir"], c["job"]["id"]) for c, d in items}
    other = [c["id"] for c, d in items if saved[d] is not None and not _same(saved[d].get("provenance"), c["job"].get("provenance"))]
    if other:                                                            # plan section 5: reuse only this run's records
        raise SystemExit(f"replication refused: saved continuation records of another job or run: {other[:3]}")
    if any(_mismatch(saved[d], dbl[d], srch[d]) for _, d in items):     # a measured disagreement included (review rep-impl-r5)
        return {"run": 0, "exit": 4, "gate": "round-1 mismatch on record: continuation stays stopped"}   # also on resume (plan section 4)
    hours = {c["id"]: round_hours(c["job"]) for c, _ in items}
    # review rep-impl-r3: a saved record is reused only if it passes the same checks collect applies; any other record
    # (incomplete, malformed, nonfinite) means "no passing record" and its cell is rerun (plan section 4: a resume
    # continues from the first cell without a passing record); the old record is set aside, never deleted
    # (an unknown status included: review rep-impl-r4; a measured round-1 mismatch stopped above and is never rerun)
    invalid = lambda c, d, mr: saved[d] is not None and not cost_stopped(saved[d]) and \
        cont_problem(saved[d], c["id"], c["job"], smoke, mr, dbl[d], srch[d]) is not None
    rerun = lambda c, d, mr: saved[d] is None or cost_stopped(saved[d]) or invalid(c, d, mr)
    run = 0
    if rerun(gate, gdest, 1):
        _set_aside(cdir, gdest)
        lost, failed = run_cells(_cont_one, [gate], [(gate["job"], gate["dir"], 1, cost, hours[gate["id"]])], 1, [gdest],
                                 [{"id": gate["id"], "gate": True}])
        run += 1
        if failed:
            return {"run": run, "failed": failed, "exit": 6, "gate": "the gate cell raised an error"}
        if lost:
            _lost(cdir, lost, hours, 1)
            return {"run": run, "lost": lost, "exit": 5, "gate": "the gate cell's worker was lost"}
    g = _d(read_record(gdest))
    if _mismatch(g, dbl[gdest], srch[gdest]):
        return {"run": run, "exit": 4, "gate": "round-1 mismatch at the gate: continuation stopped"}
    if cost_stopped(g):
        return {"run": run, "exit": 3, "gate": "the gate cell was refused at the cost cap: no further cell started"}
    if not smoke and not identical(g):                                   # the gate must prove identity, not just not fail
        return {"run": run, "exit": 4, "gate": "the gate has no identical round-1 comparison: continuation stopped"}
    if (why := cont_problem(g, gate["id"], gate["job"], smoke, max_rounds=1, doubling=dbl[gdest], search=srch[gdest])) is not None:
        return {"run": run, "exit": 6, "gate": f"the gate record fails its checks: {why}"}
    todo = [c for c in queue if rerun(c, dest(c), max_rounds)]          # same order; completed, valid cells reused
    for c in todo:
        _set_aside(cdir, dest(c))
    lost, failed = ([], {}) if not todo else run_cells(
        _cont_one, todo, [(c["job"], c["dir"], max_rounds, cost, hours[c["id"]]) for c in todo], workers,   # module-level fn
        [dest(c) for c in todo], [{"id": c["id"]} for c in todo])
    recs = [_d(read_record(dest(c))) for c in todo]
    mismatch = [c["id"] for c, r in zip(todo, recs) if _mismatch(r, dbl[dest(c)], srch[dest(c)])]
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
    """Finite per-seed values on the ordered seeds, and a positive normalizer S* on every seed (terms_of divides by it;
    review rep-impl-r3)."""
    return isinstance(h, dict) and isinstance(h.get("seeds"), list) and _same(h["seeds"], list(seeds)) and \
        all(_finite(h.get(f)) and len(h[f]) == len(seeds) for f in FIELDS) and all(x > 0 for x in h["sstar"])


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


@_checked
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
    if ev.get("stage") != "evaluate" or not _same(ev.get("id"), job["id"]) or not _same(ev.get("provenance"), job["provenance"]):
        return "evaluation record of another stage, cell or run"
    if not _valid_held(ev, seeds):
        return "evaluation values nonfinite or on other seeds"
    if x := _deps_problem(d, ev, {fz, rid, job["id"]}):
        return "evaluation: " + x
    if db is None:
        return "no doubling record"
    if db.get("stage") != "doubling" or not _same(db.get("id"), job["id"]) or not _same(db.get("provenance"), job["provenance"]) or db.get("kind") != "profit":
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


def _n_bins() -> int:
    from churn_v2 import AGE_EDGES
    return len(AGE_EDGES) - 1


def _shares_ok(sh, n_episodes: int) -> bool:
    """Newcomer audit counts (churn_v2.newcomer_shares): one episode per evaluation seed, each with the prescribed number
    of age bins of [served, audited], finite and nonnegative, audited at most served (review rep-impl-r3)."""
    per = (sh or {}).get("per_episode") if isinstance(sh, dict) else None
    if not isinstance(per, list) or len(per) != n_episodes:
        return False
    nb = _n_bins()
    for e in per:
        f = e.get("focal") if isinstance(e, dict) else None
        if not isinstance(f, list) or len(f) != nb:
            return False
        for b in f:
            if not (isinstance(b, list) and len(b) == 2 and _finite(b) and 0 <= b[1] <= b[0]):
                return False
    return True


def diag_ok(row, seeds, knobs) -> bool:
    """A diagnostics row (frozen: diagnostics.json cells[...]["base"]; continued: its own record) for this winner: its
    knobs, the job's ordered evaluation seeds, finite per-seed profits and well-formed audit counts (review rep-impl-r2)."""
    return isinstance(row, dict) and _same(row.get("knobs"), knobs) and isinstance(row.get("seeds"), list) and \
        _same(row["seeds"], list(seeds)) and _finite(row.get("normalized")) and len(row["normalized"]) == len(seeds) and \
        _shares_ok(row.get("shares"), len(seeds))


BINDING = "diagnostics_binding.json"


def diagnostics_binding(d: Path, kind: str, p: float, jobs: list) -> dict:
    """Written by rep_v2's rate stage right after the diagnostics step and before the inventory (review rep-impl-r3): the
    sha256 of diagnostics.json, the rate, and per cell the job id, its provenance (this run's commit, draw and salt) and
    the hashes of the search and doubling records whose winners the diagnostics reran."""
    import revision_v2 as R
    from sim.records_v2 import sha_file
    d = Path(d); h = lambda q: sha_file(q) if q.is_file() else None
    return {"stage": "diagnostics binding", "kind": kind, "rate": float(p), "diagnostics": h(d / "diagnostics.json"),
            "cells": {f"{j['context']}|{j['rule']}": {"id": j["id"], "provenance": j["provenance"], "search": h(R.path_of(d, j["id"])),
                                                       "doubling": h(d / "doubling" / (R._safe(j["id"]) + ".json"))} for j in jobs}}


def diag_bound(d: Path, kind: str, p: float, ck: str, job: dict) -> bool:
    """The frozen diagnostics of cell `ck` belong to this job, rate and run: the binding names this rate, the current
    diagnostics.json, this job's id and provenance, and the current search and doubling records."""
    import revision_v2 as R
    from sim.records_v2 import sha_file
    b = _d(read_record(Path(d) / BINDING)); c = (_d((b or {}).get("cells")) or {}).get(ck)
    q = Path(d) / "diagnostics.json"
    return isinstance(c, dict) and b.get("stage") == "diagnostics binding" and b.get("kind") == kind and _same(b.get("rate"), float(p)) and \
        q.is_file() and b.get("diagnostics") == sha_file(q) and _same(c.get("id"), job["id"]) and _same(c.get("provenance"), job["provenance"]) and \
        R.path_of(d, job["id"]).is_file() and c.get("search") == sha_file(R.path_of(d, job["id"])) and \
        c.get("doubling") == sha_file(Path(d) / "doubling" / (R._safe(job["id"]) + ".json"))


def cont_diag_ok(rec, key: str, job: dict, knobs) -> bool:
    return isinstance(rec, dict) and rec.get("stage") == "continued diagnostics" and _same(rec.get("id"), key) and \
        _same(rec.get("provenance"), job["provenance"]) and diag_ok(rec, job["mkt"]["seeds_eval"], knobs)


def safe_terms(h: dict, n: int):
    """terms_of, or None when a normalizer S*/N is not positive after the division or any term is not finite (review
    rep-impl-r5: S* = 5e-324 passed as positive, then became 0 after division by N)."""
    try:
        if not all(x / n > 0 for x in h["sstar"]):
            return None
        t = terms_of(h, n)
        return t if _finite(t["attack"]) and _finite(t["reference"]) and _finite(t["gain"]) else None
    except (ZeroDivisionError, OverflowError, TypeError, KeyError):
        return None


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
    record or without this run's identical gate record (also when no cell is flagged). A flagged cell whose continuation
    record fails cont_problem keeps its validated frozen winner and counts as not continued (plan section 4; review
    rep-impl-r3). A frozen R3 audit count needs diagnostics bound to this job, rate and run (diag_bound) and complete
    (diag_ok); a continued R3 winner's audit count needs its checked continued diagnostics."""
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    base = Path(base); cdir = base / "continuation"
    allrec = [_d(read_record(q)) for q in sorted(cdir.glob("*.json")) + sorted((cdir / "gate").glob("*.json")) if q.name != "lost_cells.json"]
    mismatch = any(_mismatch(r) for r in allrec)
    g = _d(read_record(cdir / "gate" / (R._safe(gate["id"]) + ".json"))) if gate else None
    gdir = (gate.get("dir") or base / "menu-p0.05") if gate else None
    gdb, gsr = (doubling_of(gdir, gate["job"]["id"]), search_of(gdir, gate["job"]["id"])) if gate else (None, None)
    mismatch = mismatch or _mismatch(g, gdb, gsr)                        # a measured disagreement at the gate (review r5)
    gate_ok = g is not None and cont_problem(g, gate["id"], gate["job"], smoke, max_rounds=1, doubling=gdb, search=gsr) is None and \
        g.get("status") in STATUSES[:2] and (identical(g) or (smoke and g.get("round1_gate") == SMOKE_GATE))
    frozen, primary, problems, unscorable = {}, {}, [], []
    counts = {"frozen": 0, "continued": 0, "unresolved": 0, "stopped": 0, "not continued": 0}
    audit = {"frozen": {}, "primary": {}}
    for (kind, p), jobs in jobs_by_dir.items():
        rk = "0" if p == 0 else f"{p:g}"; d = base / f"{kind}-p{p:g}"
        diag = (_d((_d(read_record(d / "diagnostics.json")) or {}).get("cells")) or {}) if kind == "menu" else {}
        for j in jobs:
            m, r = j["mkt"]["label"].replace("fresh", "rep"), analysis_rule(kind, j["rule"])
            ev = _d(read_record(R.eval_path(d, j["id"]))); db = doubling_of(d, j["id"]); sr = search_of(d, j["id"]) or {}
            seeds = j["mkt"]["seeds_eval"]
            if (why := base_problem(d, j, ev, db)) is not None:
                unscorable.append(f"{kind}-p{p:g}|{j['id']}: {why}"); continue
            n = _n_agents(j); fz = safe_terms(ev, n)
            if fz is None:
                unscorable.append(f"{kind}-p{p:g}|{j['id']}: a normalizer or term is not finite and positive"); continue
            frozen.setdefault(rk, {}).setdefault(m, {})[r] = fz
            fa = None
            if r == "R3" and kind == "menu":
                ck = f"{j['context']}|{j['rule']}"
                row = (_d(diag.get(ck)) or {}).get("base")
                if diag_bound(d, kind, p, ck, j) and diag_ok(row, seeds, (_d(sr.get("attack")) or {}).get("best_knobs")):
                    fa = _audit_of(row["shares"]); audit["frozen"].setdefault(rk, {})[m] = fa
                elif ck in diag:
                    problems.append(f"{kind}-p{p:g}|{j['id']}: frozen diagnostics fail their checks")
            win, kw, crec = fz, "frozen", None
            key = _key(kind, p, j["id"])
            if db["incomplete"]:
                crec = _d(read_record(cdir / (R._safe(key) + ".json")))
                if _mismatch(crec, db, sr):                                    # plan section 4: a round-1 mismatch stops
                    mismatch = True; problems.append(f"{key}: round 1 differs from the doubling record")   # everything
                if crec is None:
                    kw = "not continued"
                elif (why := cont_problem(crec, key, j, smoke, doubling=db, search=sr)) is not None:   # plan section 4: invalid output keeps
                    problems.append(f"{key}: {why}"); kw = "not continued"     # the validated frozen winner
                else:
                    try:
                        _, kw = select_winner(fz["gain"], crec)
                    except Round1Mismatch:
                        kw = "frozen"
                    if kw in ("continued", "unresolved"):
                        win = safe_terms(crec["heldout"], n)
                        if win is None:
                            problems.append(f"{key}: a continued normalizer or term is not finite and positive")
                            win, kw = fz, "not continued"
            counts[kw] += 1
            primary.setdefault(rk, {}).setdefault(m, {})[r] = win
            if r == "R3" and kind == "menu":                # review rep-impl-r4: the primary count comes from the primary
                if kw in ("continued", "unresolved"):           # winner's own diagnostics; frozen ones only for a frozen winner
                    cd = _d(read_record(cdir / "diagnostics" / (R._safe(key) + ".json")))
                    if cont_diag_ok(cd, key, j, crec["heldout"]["knobs"]):
                        audit["primary"].setdefault(rk, {})[m] = _audit_of(cd["shares"])
                    elif cd is not None:
                        problems.append(f"{key}: continued diagnostics fail their checks")
                elif fa is not None:
                    audit["primary"].setdefault(rk, {})[m] = fa
    if not gate_ok:
        problems.append("no identical gate record of this run's gate cell")
    bad = mismatch or not gate_ok
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
            key = _key(kind, p, j["id"]); crec = _d(read_record(cdir / (R._safe(key) + ".json")))
            d = Path(base) / f"{kind}-p{p:g}"
            if crec is None or cont_problem(crec, key, j, smoke, doubling=doubling_of(d, j["id"]), search=search_of(d, j["id"])) is not None or crec["status"] not in STATUSES[:2]:
                continue
            dest = cdir / "diagnostics" / (R._safe(key) + ".json"); old = _d(read_record(dest))
            if cont_diag_ok(old, key, j, crec["heldout"]["knobs"]):
                continue
            _set_aside(cdir / "diagnostics", dest)              # a stale or foreign record is rerun, never reused
            todo.append({"id": key}); args.append((j, crec["heldout"]["knobs"])); dests.append(dest); extras.append({"id": key})
    lost, failed = ([], {}) if not todo else run_cells(_diag_cont, todo, args, workers, dests, extras)
    if lost and not failed:                                     # the launcher's restart reads this estimate (exit 5)
        _lost(cdir, lost, {k: DIAG_HOURS for k in lost}, 1)
    return {"run": len(todo), "lost": lost, "failed": failed, "exit": 6 if failed else 5 if lost else 0}
