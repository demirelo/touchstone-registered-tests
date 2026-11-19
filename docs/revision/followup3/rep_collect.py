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


def _mismatch(rec) -> bool:
    return str((rec or {}).get("status", "")).startswith("stopped: round 1")


def run_queue(queue: list, base: Path, workers: int, cost=None, max_rounds: int = 3) -> dict:
    """The gate cell alone, then the rest in workers, each saving its own record (Run B's pattern). The result's "exit"
    follows Run B: 4 a measured round-1 mismatch (it outranks the rest; no restart), 6 a cell error (never restarted),
    5 a lost worker (lost_cells.json holds the restart estimate; saved cells are skipped on restart), 0 otherwise."""
    from convergence_v2 import restart_hours                             # first: it puts scripts/ on the path
    import revision_v2 as R
    from sim.records_v2 import read
    cdir = Path(base) / "continuation"; cdir.mkdir(parents=True, exist_ok=True)
    dest = lambda c: cdir / (R._safe(c["id"]) + ".json")
    saved = {c["id"]: read(dest(c)) for c in queue}
    other = [c["id"] for c in queue if saved[c["id"]] is not None and saved[c["id"]].get("provenance") != c["job"].get("provenance")]
    if other:                                                            # plan section 5: reuse only this run's records
        raise SystemExit(f"replication refused: saved continuation records of another job or run: {other[:3]}")
    if any(_mismatch(r) for r in saved.values()):
        return {"run": 0, "exit": 4, "gate": "round-1 mismatch on record: continuation stays stopped"}   # also on resume (plan section 4)
    todo = [c for c in queue if saved[c["id"]] is None]                   # a resume keeps the order and skips saved cells
    if not todo:
        return {"run": 0, "exit": 0}
    hours = {c["id"]: round_hours(c["job"]) for c in todo}
    first, rest = todo[0], todo[1:]
    write_record(dest(first), {**_cont_one(first["job"], first["dir"], max_rounds, cost, hours[first["id"]]), "id": first["id"]})
    if _mismatch(read(dest(first))):
        return {"run": 1, "exit": 4, "gate": "round-1 mismatch: continuation stopped"}
    lost, failed = run_cells(_cont_one, rest,                         # a module-level function: workers must unpickle it
                             [(c["job"], c["dir"], max_rounds, cost, hours[c["id"]]) for c in rest], workers, [dest(c) for c in rest],
                             [{"id": c["id"]} for c in rest])
    mismatch = [c["id"] for c in rest if _mismatch(read(dest(c)))]
    if lost and not mismatch and not failed:
        write_record(cdir / "lost_cells.json", {"lost": lost, "restart_hours": restart_hours([hours[k] * max_rounds for k in lost])})
    code = 4 if mismatch else 6 if failed else 5 if lost else 0
    return {"run": len(todo), "lost": lost, "failed": failed, "mismatch": mismatch, "exit": code}


def collect(base: Path, jobs_by_dir: dict) -> dict:
    """gains for both winner sets, R3's audit counts, and the winner counts."""
    import revision_v2 as R
    from sim.records_v2 import read
    frozen, primary, counts, mismatch = {}, {}, {"frozen": 0, "continued": 0, "unresolved": 0, "stopped": 0, "not continued": 0}, False
    audit = {}
    for (kind, p), jobs in jobs_by_dir.items():
        rk = "0" if p == 0 else f"{p:g}"; d = Path(base) / f"{kind}-p{p:g}"
        for j in jobs:
            m, r = j["mkt"]["label"].replace("fresh", "rep"), analysis_rule(kind, j["rule"])
            ev = read(R.eval_path(d, j["id"]))
            if ev is None or not _finite(ev.get("gain")):
                continue                                                  # unscorable: the analysis reports it
            frozen.setdefault(rk, {}).setdefault(m, {})[r] = list(ev["gain"])
            crec = read(Path(base) / "continuation" / (R._safe(_key(kind, p, j["id"])) + ".json"))
            try:
                g, kind_w = select_winner(list(ev["gain"]), crec)
            except Round1Mismatch:
                mismatch = True; g, kind_w = list(ev["gain"]), "frozen"
            counts[kind_w] += 1
            primary.setdefault(rk, {}).setdefault(m, {})[r] = g
        if kind == "menu":
            diag = read(d / "diagnostics.json") or {}
            for ck, cell in (diag.get("cells") or {}).items():
                if ck.split("|")[-1] != "F111" or "base" not in cell:
                    continue
                per = cell["base"]["shares"]["per_episode"]
                fo = [sum(e["focal"][b][i] for e in per for b in range(len(e["focal"]))) for i in (0, 1)]
                audit.setdefault(rk, {})[ck.split("@")[0].replace("fresh", "rep")] = (fo[1], fo[0])   # (audited, served)
    return {"frozen": frozen, "primary": None if mismatch else primary, "audit": audit, "counts": counts,
            "round1_mismatch": mismatch}
