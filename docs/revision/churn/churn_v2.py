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


_ORIG = None


def install() -> None:
    """Wrap revision_v2.train_cell so a job with a `churn` rate gets churning opponents (idempotent)."""
    global _ORIG
    if _ORIG is not None:
        return
    _ORIG = R.train_cell

    def train_cell(job, others=()):
        cell = _ORIG(job, others)
        p = job.get("churn")
        if p is None or others:
            return cell
        from dataclasses import replace
        return replace(cell, others=tuple((e, _churn_factory(p)) for e in range(cell.cfg.N) if e != cell.focal))
    R.train_cell = train_cell


def uninstall() -> None:
    global _ORIG
    if _ORIG is not None:
        R.train_cell = _ORIG; _ORIG = None


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


def newcomer_shares(results, focal: int, edges=AGE_EDGES) -> dict:
    """Audited share of served jobs by identity age (rounds since creation), for honest replacement identities, honest
    initial identities, and the focal provider's identities, pooled over episodes; plus honest replacements per episode."""
    cats = ("honest_replacement", "honest_initial", "focal")
    cnt = {c: [[0, 0] for _ in edges[:-1]] for c in cats}
    reps = []
    for r in results:
        reps.append(sum(1 for i, e in enumerate(r.entity_of) if e != focal and r.identity_generation[i] > 0))
        def cat(i):
            if r.entity_of[i] == focal:
                return "focal"
            return "honest_replacement" if r.identity_generation[i] > 0 else "honest_initial"
        for t, h in enumerate(r.history):
            def put(i, k):
                age = t - r.identity_round[i]
                for b in range(len(edges) - 1):
                    if edges[b] <= age < edges[b + 1]:
                        cnt[cat(i)][b][k] += 1; return
            for i in h.assignment.values():
                put(i, 0)
            for a in h.audits:
                put(a.provider, 1)
    out = {c: [{"age": [edges[b], edges[b + 1]], "served": s, "audited": a, "share": (a / s if s else 0.0)} for b, (s, a) in enumerate(cnt[c])] for c in cats}
    out["honest_replacements_per_episode"] = float(sum(reps) / len(reps)) if reps else 0.0
    return out


def diagnostics(out, jobs: list[dict]) -> dict:
    """The selected attack of each churn cell rerun on the evaluation seeds under churn, with the newcomer audit shares."""
    import numpy as np
    from sim.cell import SeedCache, run_focal
    install(); res = {}
    for j in jobs:
        T, L = R.constants(j); fam = R.family_for("D2+H3", T, L); cell = R.eval_cell(j)
        knobs = read(R.path_of(out, j["id"]))["attack"]["best_knobs"]
        fr = run_focal(cell, lambda: fam.make(dict(knobs)), SeedCache())
        res[f"{j['context']}|{j['rule']}"] = {"knobs": knobs, "mean_normalized": float(np.mean(fr.normalized)), "shares": newcomer_shares(fr.results, cell.focal)}
    return res


def inventory(out, p: float) -> dict:
    inv = F.inventory(out)
    inv["environment"]["churn_driver_sha256"] = sha_file(Path(__file__)); inv["churn"] = float(p); inv["deviations"] = list(DEVIATIONS)
    write(Path(out) / "inventory.json", inv)
    return inv


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True)
    ap.add_argument("--draw", default=str(F.ROOT / "results/v2/draw/draw.json")); ap.add_argument("--instances", default=str(F.ROOT / "results/v2/draw/instances.json"))
    ap.add_argument("--cfgs", default=str(F.ROOT / "results/v2/deviation/cfg_linux.json")); ap.add_argument("--addendum", default=str(F.ROOT / "results/v2/report/addendum.json"))
    ap.add_argument("--params", default=str(F.ROOT / "experiments/v2/params.json")); ap.add_argument("--markets", default=",".join(MARKETS))
    ap.add_argument("--rules", default=",".join(RULES)); ap.add_argument("--rates", default=",".join(f"{p:g}" for p in RATES))
    ap.add_argument("--stage", default="all", choices=("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory", "all"))
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv); base = Path(a.out); F.check_out(base, a.src)
    from sim.records import cfg_from_dict
    root = json.loads(Path(a.draw).read_text())["hash"]; salt_sha = json.loads(Path(a.instances).read_text())["salt_sha256"]
    container = json.loads(Path(a.addendum).read_text())["deviations"]["configs"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    params = json.loads(Path(a.params).read_text())
    steps = ("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory") if a.stage == "all" else (a.stage,)
    install()
    for p in (float(x) for x in a.rates.split(",")):
        out = base / f"p{p:g}"; out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
        jobs = build_jobs(root, cfgs, params, salt_sha, p, tuple(a.markets.split(",")), tuple(a.rules.split(",")), a.smoke)
        F.check_configs(jobs, container); F.check_salt(out, salt_sha, jobs); F.check_commit(jobs); F.check_code()
        if not a.smoke:
            F.check_pairing(a.src, jobs)
        for st in steps:
            if st == "inputs":
                F.copy_inputs(a.src, out, F.inputs(a.src, jobs))
            elif st == "search":
                run_stage("search", jobs, out, a.workers)
            elif st == "freeze":
                F.prefreeze(out, jobs)
            elif st in ("evaluate", "doubling"):
                F.accept(out, jobs, salt_sha, container, src=a.src); run_stage(st, jobs, out, a.workers)
            elif st == "diagnostics":
                write(out / "diagnostics.json", diagnostics(out, jobs))
            else:
                inventory(out, p)
            print(json.dumps({"churn": p, "stage": st, "jobs": len(jobs)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
