"""The honest-churn arm (docs/revision/churn/churn-plan.md, draft 1): the nine honest opponents also retire their identity
and re-enter under a fresh one with probability p per round, so the newest identity no longer marks the deviating
provider. D2+H3 attacks against R3 (F111), C* and B3 (F000) on the six fresh markets at rho 0.2, for each churn rate,
searched, evaluated and doubled with the frozen stage functions of scripts/revision_v2.py.

The frozen code is not edited (code freeze 627a2de). Churn enters through `Cell.others`: `install()` wraps
`revision_v2.train_cell`, which `eval_cell` also calls, so every stage that builds a cell for a churn job (search, twin
search, reference menu in the doubling diagnostic, evaluation) runs with churning opponents. Process pools install the
wrapper in their initialiser. A churn decision is drawn from the episode's per-round, per-entity policy seed, so it is
deterministic and identical across the three rules on the same seed.

Churn job ids carry the suffix `|churn<p>`, so they never collide with the registered D2+H3 records that the frozen
reference menus read. The frozen truthful reference of each (market, rule) is reused, not reselected, and every
reference episode runs under the same churn (see the plan, section 3). Each churn rate writes to its own directory."""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "followup"))

import reset_followup_v2 as F  # noqa: E402  (also puts the repository and scripts/ on the path)
from sim.mechanisms.base import Offer  # noqa: E402
from sim.policies.base import Action  # noqa: E402
from sim.records_v2 import read, sha_file, write  # noqa: E402

R = F.R
RULES = ("F111", "C*", "F000")
MARKETS = F.MARKETS
RATES = (0.01, 0.05)
AGE_EDGES = (0, 10, 20, 50, 200)
DEVIATIONS = (
    "follow-up beyond the registered manifest: honest opponents churn with probability p per round (not in the protocol)",
    "the frozen truthful reference of each (market, rule) is reused and re-evaluated under churn, not reselected",
    "doubling checks for every churn cell; the original freeze is replaced by this script's freeze and acceptance check",
)


class HonestChurn:
    """Honest-max delivery and offer; retires its identity and re-enters under a fresh one with probability p per round."""

    def __init__(self, p: float) -> None:
        self.p = float(p); self.name = f"honest_churn({self.p:g})"

    def act(self, view) -> Action:
        q = view.params.q_max
        return Action(effort=q, offer=Offer(claim=q, bid=view.params.a + view.params.b * q), exit=bool(self.p > 0 and view.rng.random() < self.p))


def _churn_factory(p: float):
    return lambda: HonestChurn(p)


_ORIG: dict = {}
_REF_CACHE: dict = {}


def install() -> None:
    """Wrap three revision_v2 names (idempotent): `train_cell`, so a job with a `churn` rate gets churning opponents in
    every cell built from it; `select_reference`, so a cell with churning opponents never reuses a candidate's stored
    no-churn training profits (internal review r1, blocker 1); and `reference_of`, so a churn job's frozen reference
    carries its training-seed score evaluated under the same churn, which the doubling stage's reference_change subtracts."""
    if _ORIG:
        return
    _ORIG.update(train_cell=R.train_cell, select_reference=R.select_reference, reference_of=R.reference_of)

    def train_cell(job, others=()):
        cell = _ORIG["train_cell"](job, others)
        p = job.get("churn")
        if p is None or others:
            return cell
        from dataclasses import replace
        return replace(cell, others=tuple((e, _churn_factory(p)) for e in range(cell.cfg.N) if e != cell.focal))

    def select_reference(cell, candidates, cache):
        if cell.others:
            from dataclasses import replace
            candidates = [c if c.name == "abstain" else replace(c, known_profit=None, known_normalized=None) for c in candidates]
        return _ORIG["select_reference"](cell, candidates, cache)

    def reference_of(job, out):
        cand, rrec, path = _ORIG["reference_of"](job, out)
        if job.get("churn") is None:
            return cand, rrec, path
        key = (job["id"], str(path))
        if key not in _REF_CACHE:
            from sim.cell import SeedCache, run_focal
            fr = run_focal(R.train_cell(job), cand.policy_factory, SeedCache())
            _REF_CACHE[key] = [float(x) for x in fr.normalized]
        return cand, {**rrec, "per_seed_normalized": list(_REF_CACHE[key]), "churn_reevaluated": True}, path

    R.train_cell, R.select_reference, R.reference_of = train_cell, select_reference, reference_of


def uninstall() -> None:
    if _ORIG:
        R.train_cell, R.select_reference, R.reference_of = _ORIG["train_cell"], _ORIG["select_reference"], _ORIG["reference_of"]
        _ORIG.clear(); _REF_CACHE.clear()


def churn_job(job: dict, p: float) -> dict:
    rid = f"{job['id']}|churn{p:g}"
    return {**job, "id": rid, "churn": float(p), "provenance": {**job["provenance"], "id": rid, "churn": float(p)}}


def build_jobs(root: str, cfgs: dict, params: dict, salt_sha256: str, p: float, markets=MARKETS, rules=RULES, smoke: bool = False) -> list[dict]:
    jobs = []
    for m in markets:
        mkt = R.market(m, root, 0.2, smoke=smoke, cfg=cfgs[m], salt_sha256=salt_sha256)
        jobs += [churn_job(R.job(mkt, r, "D2+H3", "profit", smoke=smoke, params=params), p) for r in rules]
    return jobs


def _init_worker() -> None:
    install()


def run_stage(stage: str, jobs: list[dict], out, workers: int = 1) -> list[str]:
    install()
    if workers <= 1 or len(jobs) <= 1:
        return [R._run_one(stage, j, str(out), F.CUTS, F.H4_EXCLUDED, jobs) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as ex:
        n = len(jobs)
        return list(ex.map(R._run_one, [stage] * n, jobs, [str(out)] * n, [F.CUTS] * n, [F.H4_EXCLUDED] * n, [jobs] * n))


def _newest_by_first_offer(r, focal: int) -> float:
    """The mechanism-relevant statistic (sim/mechanisms/factorial.py: R3 ages an identity from its first offer and ranks
    the identities holding assigned jobs): over the rounds in which the focal identity holds assigned jobs, the share in
    which its first-offer round is strictly the latest among the identities holding assigned jobs."""
    first: dict = {}; hits = n = 0
    for t, h in enumerate(r.history):
        for i in getattr(h, "offers", {}) or {}:
            first.setdefault(int(i), t)
        holders = {int(i) for i in h.assignment.values()}
        mine = [i for i in holders if r.entity_of[i] == focal]
        if not mine:
            continue
        n += 1; f = first.get(mine[0], t); latest = max(first.get(i, t) for i in holders)
        hits += int(f == latest and sum(1 for i in holders if first.get(i, t) == latest) == 1)
    return hits / n if n else 0.0


def _uniquely_newest(r, focal: int) -> float:
    """Creation-time newest among the current identities: the share of rounds in which the focal provider's current
    identity has strictly the latest creation round (initial identities tie at round 0). Not the order R3 uses."""
    T = len(r.history); born = list(r.identity_round); ent = list(r.entity_of); hits = 0
    for t in range(T):
        cur = {}
        for i, (e, b) in enumerate(zip(ent, born)):
            if b <= t:
                cur[e] = i                                              # identities are numbered in creation order
        newest = max(born[i] for i in cur.values()); f = born[cur[focal]]
        hits += int(f == newest and sum(1 for i in cur.values() if born[i] == newest) == 1)
    return hits / T if T else 0.0


def newcomer_shares(results, focal: int, edges=AGE_EDGES) -> dict:
    """Audited share of served jobs by identity age (rounds since creation) for honest replacement identities, honest
    initial identities, and the focal provider's identities: per episode [served, audited] counts per age bin, and the
    pooled share per bin (None, "unavailable", when no job was served in the bin); honest replacements per episode; and
    per episode the share of rounds in which the focal identity is uniquely the newest."""
    cats = ("honest_replacement", "honest_initial", "focal"); nb = len(edges) - 1
    per, reps, newest, offer_newest = [], [], [], []
    for r in results:
        cnt = {c: [[0, 0] for _ in range(nb)] for c in cats}
        reps.append(sum(1 for i, e in enumerate(r.entity_of) if e != focal and r.identity_generation[i] > 0))
        cat = lambda i: "focal" if r.entity_of[i] == focal else ("honest_replacement" if r.identity_generation[i] > 0 else "honest_initial")
        for t, h in enumerate(r.history):
            def put(i, k):
                age = t - r.identity_round[i]
                for b in range(nb):
                    if edges[b] <= age < edges[b + 1]:
                        cnt[cat(i)][b][k] += 1; return
            for i in h.assignment.values():
                put(i, 0)
            for a in h.audits:
                put(a.provider, 1)
        per.append(cnt); newest.append(_uniquely_newest(r, focal)); offer_newest.append(_newest_by_first_offer(r, focal))
    out = {}
    for c in cats:
        rows = []
        for b in range(nb):
            sv = sum(e[c][b][0] for e in per); au = sum(e[c][b][1] for e in per)
            rows.append({"age": [edges[b], edges[b + 1]], "served": sv, "audited": au, "share": (au / sv if sv else None)})
        out[c] = rows
    out["per_episode"] = per
    out["honest_replacements_per_episode"] = float(sum(reps) / len(reps)) if reps else 0.0
    out["focal_newest_by_creation"] = newest
    out["focal_newest_by_first_offer_assigned"] = offer_newest
    return out


def pool_markets(by_market: dict, cat: str) -> list:
    """Equal market weights: per age bin, the mean of the market shares over the markets where the share is available."""
    nb = len(next(iter(by_market.values()))[cat]); res = []
    for b in range(nb):
        v = [m[cat][b]["share"] for m in by_market.values() if m[cat][b]["share"] is not None]
        res.append({"share": (sum(v) / len(v) if v else None), "markets": len(v)})
    return res


def _diag_one(job: dict, out: str) -> tuple:
    import numpy as np
    from sim.cell import SeedCache, run_focal
    install(); j = job
    T, L = R.constants(j); fam = R.family_for("D2+H3", T, L); cell = R.eval_cell(j)
    pols = {"base": read(R.path_of(out, j["id"]))["attack"]["best_knobs"],
            "doubled": read(Path(out) / "doubling" / (R._safe(j["id"]) + ".json"))["heldout"]["knobs"]}
    row = {}
    for k, knobs in pols.items():
        fr = run_focal(cell, lambda knobs=knobs: fam.make(dict(knobs)), SeedCache())
        row[k] = {"knobs": knobs, "seeds": [int(x) for x in cell.seeds], "normalized": [float(x) for x in fr.normalized],
                  "mean_normalized": float(np.mean(fr.normalized)), "shares": newcomer_shares(fr.results, cell.focal)}
    return f"{j['context']}|{j['rule']}", row


def diagnostics(out, jobs: list[dict], workers: int = 1) -> dict:
    """Plan section 4 (draft 2): the base and the doubled winner of each churn cell rerun on the evaluation seeds under
    churn, with per-seed normalised profits and newcomer audit counts; and, per rule and winner, the age-bin shares pooled
    over markets with equal weights."""
    install()
    if workers <= 1 or len(jobs) <= 1:
        rows = [_diag_one(j, str(out)) for j in jobs]
    else:
        with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as ex:
            rows = list(ex.map(_diag_one, jobs, [str(out)] * len(jobs)))
    res = dict(rows); pooled = {}
    for rule in sorted({k.split("|")[1] for k in res}):
        for w in ("base", "doubled"):
            bm = {k.split("|")[0]: v[w]["shares"] for k, v in res.items() if k.split("|")[1] == rule}
            pooled[f"{rule}|{w}"] = {c: pool_markets(bm, c) for c in ("honest_replacement", "honest_initial", "focal")}
    return {"cells": res, "pooled": pooled}


GATE_CELL = ("fresh0", "F111")


def _mapped_view(out, view, cid: str, rid: str) -> None:
    """Copies of a churn cell's search, evaluation, and doubling records under the registered id, so the reset driver's
    comparators read both sides by one id; only the id fields and the cell's own upstream key are renamed."""
    sr = read(R.path_of(out, cid)); ev = read(R.eval_path(out, cid)); db = read(Path(out) / "doubling" / (R._safe(cid) + ".json"))
    if sr is not None:
        write(R.path_of(view, rid), {**sr, "id": rid, "provenance": {**sr["provenance"], "id": rid}})
    if ev is not None:
        up = {(rid if k == cid else k): v for k, v in (ev.get("upstream") or {}).items()}
        write(R.eval_path(view, rid), {**ev, "id": rid, "upstream": up})
    if db is not None:
        write(Path(view) / "doubling" / (R._safe(rid) + ".json"), {**db, "id": rid})


def gate_compare(src, out, rid: str, cid: str) -> dict:
    """The p = 0 gate (plan draft 2, section 3 c): the churn cell `cid` at p = 0 against the registered cell `rid`, by the
    reset driver's draft-5 criteria for the search and evaluation (`compare`) and the doubling check (`compare_doubling`)."""
    view = Path(out) / "gate_view"; _mapped_view(out, view, cid, rid)
    s, d = F.compare(src, view, rid), F.compare_doubling(src, view, rid)
    res = {"stage": "churn p=0 gate", "registered": rid, "churn": cid, "pass": bool(s["pass"] and d["pass"]), "search": s, "doubling": d}
    write(Path(out) / "gate.json", res)
    return res


STOP_USD, POD_USD_PER_HOUR = 8.00, 0.56            # author, 2026-11-10: stop cap 8 USD for this arm (category followup)


def check_started(started, now: float | None = None) -> None:
    """Production runs need the pod's allocation time (epoch seconds, in the past)."""
    import math
    import time
    now = time.time() if now is None else now
    if started is None or not isinstance(started, (int, float)) or not math.isfinite(started) or not (1.6e9 < float(started) <= now):
        raise SystemExit(f"churn arm refused: --started must be the pod's allocation time in epoch seconds, got {started!r}")


def check_cap(started: float | None, need_s: float, cap: float = STOP_USD, usd_per_hour: float = POD_USD_PER_HOUR, now: float | None = None,
              prior_usd: float = 0.0) -> None:
    """An estimate-based stage-admission limit. No running stage is ever killed (author, 2026-11-10): before each stage,
    the pod time billed since `started`, plus the charges of earlier failed attempts (`prior_usd`), plus the stage's
    estimate, is compared with the cap, and the driver stops between stages if it would be passed. A stage that overruns
    its estimate can therefore end above the cap; pod deletion on completion or failure is the launcher's job."""
    import time
    if started is None:
        return
    spent = float(prior_usd) + ((now if now is not None else time.time()) - float(started)) / 3600 * usd_per_hour
    need = float(need_s) / 3600 * usd_per_hour
    if spent + need > cap:
        raise SystemExit(f"churn arm stopped between stages: {spent:.2f} USD billed + {need:.2f} USD for the next stage would pass the {cap:.2f} USD cap")


def inventory(out, p: float) -> dict:
    inv = F.inventory(out)
    inv["environment"]["churn_driver_sha256"] = sha_file(Path(__file__)); inv["churn"] = float(p); inv["deviations"] = list(DEVIATIONS)
    write(Path(out) / "inventory.json", inv)
    return inv


def require_gate(base) -> dict:
    """Every production churn stage needs a saved, passing p = 0 gate run by this driver version (plan section 3 c)."""
    g = read(Path(base) / "gate-p0" / "gate.json"); inv = read(Path(base) / "gate-p0" / "inventory.json")
    want = R.cell_id(f"{GATE_CELL[0]}@rho0.2", GATE_CELL[1], "D2+H3", "profit")
    if not g or not g.get("pass") or g.get("registered") != want or g.get("churn") != f"{want}|churn0":
        raise SystemExit("churn arm refused: no saved passing p = 0 gate for this cell")
    if not inv or inv.get("environment", {}).get("churn_driver_sha256") != sha_file(Path(__file__)):
        raise SystemExit("churn arm refused: the saved gate was run by another driver version")
    return g


def plan_workers(limit: int, task_peak: int, parent: int, requested: int, headroom: float = 0.9) -> int:
    """Workers for the four-profile stages that fit the memory limit: floor((headroom x limit - parent) / task peak)."""
    n = int((headroom * limit - parent) // task_peak)
    if n < 1:
        raise SystemExit(f"churn arm refused: memory limit {limit} bytes holds no {task_peak}-byte task")
    return min(int(requested), n)


def memory_limit() -> int:
    """The cgroup memory limit (v2 or v1), else the physical memory."""
    import os
    for f in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            v = Path(f).read_text().strip()
            if v.isdigit() and int(v) < 2 ** 60:
                return int(v)
        except OSError:
            pass
    return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")


def memory_preflight(job: dict, out, requested: int) -> dict:
    """Pod-side, before the nine-worker stages: one full evaluate task (four 200-seed profiles) for `job`, in a child
    process, measured by its peak RSS; the parent's own RSS; the limit; and the workers that fit."""
    import resource
    import subprocess
    import pickle
    jp = Path(out) / "memory_preflight_job.pkl"; jp.write_bytes(pickle.dumps(job))
    r = subprocess.run([sys.executable, str(HERE / "churn_memory.py"), "--task", str(jp), str(out)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"churn arm refused: memory preflight failed: {r.stderr[-300:]}")
    peak = int(json.loads(r.stdout.strip().splitlines()[-1])["peak_rss_bytes"])
    parent = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)   # bytes on macOS, KiB on Linux
    limit = memory_limit(); w = plan_workers(limit, peak, parent, requested)
    rec = {"limit_bytes": limit, "task_peak_bytes": peak, "parent_bytes": parent, "requested": requested, "workers": w}
    write(Path(out) / "memory_preflight.json", rec)
    return rec


STAGE_SECONDS = {"search": 2084.3, "evaluate": 120.0, "doubling": 997.8, "diagnostics": 60.0}   # benchmark, per job (plan section 7)


def _run_rate(out, jobs, steps, a, salt_sha, container, p, started) -> None:
    F.check_configs(jobs, container); F.check_salt(out, salt_sha, jobs); F.check_commit(jobs); F.check_code()
    if not a.smoke:
        F.check_pairing(a.src, jobs)
    slow = 1.33 if p > 0 else 1.0
    for st in steps:
        w = a.workers_search if st == "search" else a.workers_eval
        if st in STAGE_SECONDS:
            check_cap(started, STAGE_SECONDS[st] * slow * -(-len(jobs) // max(1, w)), a.stop_usd, a.usd_per_hour, prior_usd=a.prior_usd)
        if st == "inputs":
            F.copy_inputs(a.src, out, F.inputs(a.src, jobs))
        elif st == "search":
            run_stage("search", jobs, out, w)
        elif st == "freeze":
            F.prefreeze(out, jobs)
        elif st in ("evaluate", "doubling"):
            F.accept(out, jobs, salt_sha, container, src=a.src)
            if not a.smoke and len(jobs) > 1:
                w = memory_preflight(jobs[0], out, w)["workers"]
            run_stage(st, jobs, out, w)
        elif st == "diagnostics":
            write(Path(out) / "diagnostics.json", diagnostics(out, jobs, w))
        else:
            inventory(out, p)
        print(json.dumps({"churn": p, "stage": st, "jobs": len(jobs)}), flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True)
    ap.add_argument("--draw", default=str(F.ROOT / "results/v2/draw/draw.json")); ap.add_argument("--instances", default=str(F.ROOT / "results/v2/draw/instances.json"))
    ap.add_argument("--cfgs", default=str(F.ROOT / "results/v2/deviation/cfg_linux.json")); ap.add_argument("--addendum", default=str(F.ROOT / "results/v2/report/addendum.json"))
    ap.add_argument("--params", default=str(F.ROOT / "experiments/v2/params.json")); ap.add_argument("--markets", default=",".join(MARKETS))
    ap.add_argument("--rules", default=",".join(RULES)); ap.add_argument("--rates", default=",".join(f"{p:g}" for p in RATES))
    ap.add_argument("--stage", default="all", choices=("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory", "all"))
    ap.add_argument("--workers-search", dest="workers_search", type=int, default=16); ap.add_argument("--workers-eval", dest="workers_eval", type=int, default=9)
    ap.add_argument("--started", type=float, default=None, help="epoch seconds of pod allocation; spend is billed from it")
    ap.add_argument("--stop-usd", dest="stop_usd", type=float, default=STOP_USD)
    ap.add_argument("--usd-per-hour", dest="usd_per_hour", type=float, default=None, help="the pod's actual hourly price (required in production)")
    ap.add_argument("--prior-usd", dest="prior_usd", type=float, default=0.0, help="charges of earlier failed attempts of this arm")
    ap.add_argument("--gate", choices=("first", "only", "skip"), default="first", help="the p = 0 reproduction gate (plan section 3 c)")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv); base = Path(a.out); F.check_out(base, a.src)
    if not a.smoke:
        check_started(a.started)
        if a.usd_per_hour is None or not a.usd_per_hour > 0:
            raise SystemExit("churn arm refused: --usd-per-hour must be the pod's actual hourly price")
        if a.gate == "skip":
            raise SystemExit("churn arm refused: production runs cannot skip the gate")
        if a.stage != "all":
            require_gate(base)
        base.mkdir(parents=True, exist_ok=True)
        write(base / "run.json", {"started": a.started, "usd_per_hour": a.usd_per_hour, "prior_usd": a.prior_usd, "stop_usd": a.stop_usd})
    if a.usd_per_hour is None:
        a.usd_per_hour = POD_USD_PER_HOUR
    from sim.records import cfg_from_dict
    root = json.loads(Path(a.draw).read_text())["hash"]; salt_sha = json.loads(Path(a.instances).read_text())["salt_sha256"]
    container = json.loads(Path(a.addendum).read_text())["deviations"]["configs"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    params = json.loads(Path(a.params).read_text())
    steps = ("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory") if a.stage == "all" else (a.stage,)
    install()
    if a.gate != "skip" and a.stage == "all":
        out = base / "gate-p0"; out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
        jobs = build_jobs(root, cfgs, params, salt_sha, 0.0, (GATE_CELL[0],), (GATE_CELL[1],), a.smoke)
        _run_rate(out, jobs, ("inputs", "search", "freeze", "evaluate", "doubling", "inventory"), a, salt_sha, container, 0.0, a.started)
        rid = R.cell_id(f"{GATE_CELL[0]}@rho0.2", GATE_CELL[1], "D2+H3", "profit")
        g = gate_compare(a.src, out, rid, jobs[0]["id"]); inventory(out, 0.0)
        print(json.dumps({"gate": g["pass"], "search": g["search"].get("problems"), "doubling": g["doubling"].get("problems")}), flush=True)
        if not g["pass"] and not a.smoke:
            print("churn arm stopped: the p = 0 gate failed", file=sys.stderr)
            return 1
        if a.gate == "only":
            return 0 if g["pass"] else 1
    if not a.smoke:
        require_gate(base)
    for p in (float(x) for x in a.rates.split(",")):
        out = base / f"p{p:g}"; out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
        jobs = build_jobs(root, cfgs, params, salt_sha, p, tuple(a.markets.split(",")), tuple(a.rules.split(",")), a.smoke)
        _run_rate(out, jobs, steps, a, salt_sha, container, p, a.started)
    return 0


if __name__ == "__main__":
    sys.exit(main())
