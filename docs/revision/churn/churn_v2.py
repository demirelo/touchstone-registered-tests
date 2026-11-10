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


def _uniquely_newest(r, focal: int) -> float:
    """Share of rounds in which the focal provider's current identity has the latest creation round among the current
    identities, strictly (initial identities tie at round 0)."""
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
    per, reps, newest = [], [], []
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
        per.append(cnt); newest.append(_uniquely_newest(r, focal))
    out = {}
    for c in cats:
        rows = []
        for b in range(nb):
            sv = sum(e[c][b][0] for e in per); au = sum(e[c][b][1] for e in per)
            rows.append({"age": [edges[b], edges[b + 1]], "served": sv, "audited": au, "share": (au / sv if sv else None)})
        out[c] = rows
    out["per_episode"] = per
    out["honest_replacements_per_episode"] = float(sum(reps) / len(reps)) if reps else 0.0
    out["focal_uniquely_newest"] = newest
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


def check_cap(started: float | None, need_s: float, cap: float = STOP_USD, usd_per_hour: float = POD_USD_PER_HOUR, now: float | None = None) -> None:
    """No running stage is ever killed (author, 2026-11-10). Between stages: refuse to dispatch the next stage if the pod
    time already billed since `started` plus the stage's estimate would pass the stop cap; the driver then stops and
    reports."""
    import time
    if started is None:
        return
    spent = ((now if now is not None else time.time()) - float(started)) / 3600 * usd_per_hour
    need = float(need_s) / 3600 * usd_per_hour
    if spent + need > cap:
        raise SystemExit(f"churn arm stopped between stages: {spent:.2f} USD billed + {need:.2f} USD for the next stage would pass the {cap:.2f} USD cap")


def inventory(out, p: float) -> dict:
    inv = F.inventory(out)
    inv["environment"]["churn_driver_sha256"] = sha_file(Path(__file__)); inv["churn"] = float(p); inv["deviations"] = list(DEVIATIONS)
    write(Path(out) / "inventory.json", inv)
    return inv


STAGE_SECONDS = {"search": 2084.3, "evaluate": 120.0, "doubling": 997.8, "diagnostics": 60.0}   # benchmark, per job (plan section 7)


def _run_rate(out, jobs, steps, a, salt_sha, container, p, started) -> None:
    F.check_configs(jobs, container); F.check_salt(out, salt_sha, jobs); F.check_commit(jobs); F.check_code()
    if not a.smoke:
        F.check_pairing(a.src, jobs)
    slow = 1.33 if p > 0 else 1.0
    for st in steps:
        w = a.workers_search if st == "search" else a.workers_eval
        if st in STAGE_SECONDS:
            check_cap(started, STAGE_SECONDS[st] * slow * -(-len(jobs) // max(1, w)), a.stop_usd, a.usd_per_hour)
        if st == "inputs":
            F.copy_inputs(a.src, out, F.inputs(a.src, jobs))
        elif st == "search":
            run_stage("search", jobs, out, w)
        elif st == "freeze":
            F.prefreeze(out, jobs)
        elif st in ("evaluate", "doubling"):
            F.accept(out, jobs, salt_sha, container, src=a.src); run_stage(st, jobs, out, w)
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
    ap.add_argument("--stop-usd", dest="stop_usd", type=float, default=STOP_USD); ap.add_argument("--usd-per-hour", dest="usd_per_hour", type=float, default=POD_USD_PER_HOUR)
    ap.add_argument("--gate", choices=("first", "only", "skip"), default="first", help="the p = 0 reproduction gate (plan section 3 c)")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv); base = Path(a.out); F.check_out(base, a.src)
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
    for p in (float(x) for x in a.rates.split(",")):
        out = base / f"p{p:g}"; out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
        jobs = build_jobs(root, cfgs, params, salt_sha, p, tuple(a.markets.split(",")), tuple(a.rules.split(",")), a.smoke)
        _run_rate(out, jobs, steps, a, salt_sha, container, p, a.started)
    return 0


if __name__ == "__main__":
    sys.exit(main())
