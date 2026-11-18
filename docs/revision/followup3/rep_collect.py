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


def _cont_one(job: dict, rate_dir: str, max_rounds: int, cost) -> dict:
    """In a worker: install the churn-aware adapter, then continue one cell; round 1 is compared with this run's
    doubling record in the same rate directory."""
    from continuation import install_continuation
    install_continuation()
    import convergence_v2 as B
    return B.run_cell(job, rate_dir, max_rounds=max_rounds, src=rate_dir, cost=cost)


def run_queue(queue: list, base: Path, workers: int, cost=None, max_rounds: int = 3) -> dict:
    """The gate cell alone, then the rest in workers, each saving its own record (Run B's pattern)."""
    import revision_v2 as R
    from convergence_v2 import run_cells
    from sim.records_v2 import read, write
    cdir = Path(base) / "continuation"; cdir.mkdir(parents=True, exist_ok=True)
    dest = lambda c: cdir / (R._safe(c["id"]) + ".json")
    if any(str((read(dest(c)) or {}).get("status", "")).startswith("stopped: round 1") for c in queue):
        return {"run": 0, "gate": "round-1 mismatch on record: continuation stays stopped"}   # also on resume (plan section 4)
    todo = [c for c in queue if read(dest(c)) is None]                   # a resume keeps the order and skips saved cells
    if not todo:
        return {"run": 0}
    first, rest = todo[0], todo[1:]
    write(dest(first), {**_cont_one(first["job"], first["dir"], max_rounds, cost), "id": first["id"]})
    if str(read(dest(first)).get("status", "")).startswith("stopped: round 1"):
        return {"run": 1, "gate": "round-1 mismatch: continuation stopped"}
    lost, failed = run_cells(_cont_one, rest,                         # a module-level function: workers must unpickle it
                             [(c["job"], c["dir"], max_rounds, cost) for c in rest], workers, [dest(c) for c in rest],
                             [{"id": c["id"]} for c in rest])
    return {"run": len(todo), "lost": lost, "failed": failed}


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
