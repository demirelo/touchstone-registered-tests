"""Tuning v2 (design 4, 3.3): every whole system and the comparator selection are scored by one objective,
J = min over tuning markets of min(m_D2, m_H3, m_X7), m = min((eff - 0.90) / 0.90, (0.30 - gain) / 0.30), with gain against
the rule's development reference (design 6.4: one menu from its D2, D2+H3, and X7-SC searches). The registered inner
search scores every configuration in-sample on the dev-train seeds; the top 2 are rechecked at the full budget on dev-train
and scored on dev-val; ties by grid order. As in the registered tuning, no corner controls run inside tuning. The C*/S2
fixture searches supply the coverage fixtures (design 9.5). With --workers N every (configuration, market) pair is one task
in a process pool; the parent alone writes the logs, one per configuration and stage with every market. All outputs stay
under --out."""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from sim.cell import Cell, SeedCache  # noqa: E402
from sim.locked import load_locked  # noqa: E402
from sim.mechanisms.credibility import SELECTION_GRID  # noqa: E402
from sim.policies.x7 import embed_h3  # noqa: E402
from sim.records import search_to_json  # noqa: E402
from sim.reference import evaluate_gain, reference_candidates, select_reference, twin_search  # noqa: E402
from sim.rules_v2 import make_rule, public_constants  # noqa: E402
from sim.search import settings_from_locked  # noqa: E402

FAMILIES = ("D2", "D2+H3", "X7-SC")
SYSTEMS = ("B3-t", "R3-t", "C*-t")                  # design draft 7, 3.5: R4-t is dropped; no C*/S2 fixture searches
COMMON_GRID = [(t, L) for t in (0.08, 0.12, 0.14, 0.16) for L in (3, 10, 20, 50)]
FIXED = {"tol": 0.16, "L": 10}
TOP = 2
INNER = (1, 100, 3)                 # restarts, evaluations, dev-train seeds (X7-SC doubles the evaluations)
SMOKE_INNER, SMOKE_FULL = (1, 16, 1), (1, 16, 1, 2)


def margin(eff: float, gain: float) -> float:
    return min((float(eff) - 0.90) / 0.90, (0.30 - float(gain)) / 0.30)


def objective(margins_by_market: dict) -> float:
    return min(v for fam in margins_by_market.values() for v in fam.values())


def comparator_grid() -> list[dict]:
    return [dict(g) for g in SELECTION_GRID]


def rank(scores: list[dict]) -> list[dict]:
    """Highest objective first; ties by the original grid index (kept in "grid"), else by list order."""
    order = {id(s): i for i, s in enumerate(scores)}
    return sorted(scores, key=lambda s: (-s["objective"], s.get("grid", order[id(s)])))


def _market(label: str, smoke: bool) -> dict:
    return RV.market(label, RV.DEV_ROOT, 0.2, dev=True, smoke=False)


def _settings(budget, family):
    R, E = budget[0], budget[1] * (2 if family == "X7-SC" else 1)
    return replace(settings_from_locked(load_locked()), restarts=int(R), evals_per_restart=int(E))


def market_searches(rule: str, spec: dict, mkt: dict, budget: tuple, cache: SeedCache) -> dict:
    """Twin and attack searches of D2, D2+H3, X7-SC on budget[2] dev-train seeds, and the development reference."""
    rf = lambda: make_rule(rule, spec["tol"], spec["L"], cred=spec.get("cred"))
    T = int(mkt["cfg"].T); L = public_constants(rf(), mkt["cfg"])["L"]
    cell = Cell(cfg=mkt["cfg"], rule_factory=rf, focal=mkt["focal"], seeds=tuple(mkt["seeds_train"][: budget[2]]), name=f"tune/{rule}")
    lk = load_locked(); groups, attacks, fams = {}, {}, {}
    for fname in FAMILIES:
        fam = RV.family_for(fname, T, L); st = _settings(budget, fname); fams[fname] = fam
        tw = twin_search(cell, fam, cache, st, seed=0)
        extra = {"embedded_h3": embed_h3(attacks["D2+H3"].best_knobs, T)} if fname == "X7-SC" else {}
        at = RV.search_family(cell, fam, cache, st, tw, extra); attacks[fname] = at
        for c in reference_candidates(cell, fam, at, tw, [], tuple(lk["reference_order"])):
            groups.setdefault(("bank" if c.name.startswith("bank_") else c.name, fname), []).append(c)
    cands, cfams = RV.merge_menu(groups, FAMILIES)
    ref = select_reference(cell, cands, cache)
    idx = next(i for i, c in enumerate(cands) if c is ref.candidate)
    return {"cell": cell, "families": fams, "attacks": attacks, "reference": ref, "reference_json": RV.cand_to_json(cands[idx], cfams[idx], T, L), "T": T, "L": L}


def _score_market(rule: str, spec: dict, label: str, budget: tuple, recheck: bool) -> dict:
    """One configuration on one market: its searches, development reference, and three evaluations (a pool task)."""
    cache = SeedCache(); mkt = _market(label, False); s = market_searches(rule, spec, mkt, budget, cache)
    score_cell = s["cell"] if not recheck else replace(s["cell"], seeds=tuple(mkt["seeds_val"][: budget[3]]))
    margins, detail = {}, {}
    for fname in FAMILIES:
        g = evaluate_gain(score_cell, s["families"][fname], s["attacks"][fname].best_knobs, s["reference"].candidate, cache)
        eff, gain = float(g.eff_attack.mean()), float(g.gain.mean())
        margins[fname] = margin(eff, gain); detail[fname] = {"eff": eff, "gain": gain, "attack": s["attacks"][fname].best_knobs}
    detail["reference"] = s["reference_json"]
    return {"label": label, "margins": margins, "detail": detail, "episodes": cache.runs}


def _map(fn, items: list[tuple], workers: int) -> list:
    if workers <= 1 or len(items) <= 1:
        return [fn(*it) for it in items]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, *zip(*items)))


def _combine(rule: str, spec: dict, budget: tuple, recheck: bool, parts: list[dict], log: Path) -> dict:
    margins = {p["label"]: p["margins"] for p in parts}; detail = {p["label"]: p["detail"] for p in parts}
    episodes = int(sum(p["episodes"] for p in parts))
    tag = f"{rule}|{json.dumps(spec, sort_keys=True)}|{'recheck' if recheck else 'inner'}"
    Path(log).mkdir(parents=True, exist_ok=True)
    (Path(log) / (RV._safe(tag).replace(" ", "") + ".json")).write_text(json.dumps({"rule": rule, "spec": spec, "recheck": recheck, "budget": list(budget),
                                                                                     "margins": margins, "detail": detail, "episodes": episodes}, default=float))
    return {"objective": objective(margins), "margins": margins, "episodes": episodes}


def score_config(rule: str, spec: dict, markets: list[str], budget: tuple, recheck: bool, log: Path) -> dict:
    """Margins per market and family; inner scoring on the search seeds, recheck scoring on dev-val."""
    return _combine(rule, spec, budget, recheck, [_score_market(rule, spec, m, budget, recheck) for m in markets], log)


def _score_all(rule: str, specs: list[dict], markets: list[str], budget: tuple, recheck: bool, log: Path, workers: int) -> list[dict]:
    """Every (configuration, market) pair as one task; results recombined per configuration in grid order."""
    items = [(rule, spec, m, budget, recheck) for spec in specs for m in markets]
    parts = _map(_score_market, items, workers); k = len(markets)
    return [_combine(rule, spec, budget, recheck, parts[i * k:(i + 1) * k], log) for i, spec in enumerate(specs)]


def _budgets(smoke: bool) -> tuple[tuple, tuple]:
    lk = load_locked()
    full = (int(lk["search"]["restarts"]), int(lk["search"]["evals_per_restart"]), len(lk["seeds"]["dev_train"]), len(lk["seeds"]["dev_val"]))
    return ((*SMOKE_INNER, 2), SMOKE_FULL) if smoke else ((*INNER, 20), full)


def _tune(rule: str, specs: list[dict], markets: list[str], out: Path, smoke: bool, workers: int = 1) -> tuple[list, list]:
    inner, full = _budgets(smoke); log = Path(out) / "log"
    scores = [{"spec": spec, "grid": i, **r} for i, (spec, r) in enumerate(zip(specs, _score_all(rule, specs, markets, inner, False, log, workers)))]
    top = rank(scores)[:TOP]
    rechecked = [{"spec": s["spec"], "grid": s["grid"], **r} for s, r in zip(top, _score_all(rule, [s["spec"] for s in top], markets, full, True, log, workers))]
    return scores, rank(rechecked)


def _provenance(smoke: bool, markets: list[str]) -> dict:
    inner, full = _budgets(smoke)
    return {"smoke": smoke, "markets": list(markets), "budget_inner": list(inner), "budget_full": list(full), "commit": RV.git_commit()}


def select_comparator(markets: list[str], out: Path, smoke: bool = False, grid_limit: int | None = None, workers: int = 1) -> dict:
    grid = comparator_grid()[:grid_limit] if grid_limit else comparator_grid()
    specs = [{**FIXED, "cred": g} for g in grid]
    scores, rechecked = _tune("C*", specs, markets, out, smoke, workers)
    res = {"cred": rechecked[0]["spec"]["cred"], "scores": scores, "rechecked": rechecked,
           "episodes": int(sum(s["episodes"] for s in scores + rechecked)), **_provenance(smoke, markets)}
    Path(out).mkdir(parents=True, exist_ok=True); (Path(out) / "comparator.json").write_text(json.dumps(res, default=float))
    return res


def tune_system(name: str, markets: list[str], out: Path, cred: dict | None = None, smoke: bool = False, grid_limit: int | None = None,
                workers: int = 1) -> dict:
    grid = COMMON_GRID[:grid_limit] if grid_limit else COMMON_GRID
    specs = [{"tol": t, "L": L, **({"cred": cred} if cred else {})} for t, L in grid]
    if name not in SYSTEMS:
        raise SystemExit(f"unknown whole system {name!r} (design draft 7: {SYSTEMS})")
    rule = name
    scores, rechecked = _tune(rule, specs, markets, out, smoke, workers)
    best = rechecked[0]["spec"]
    res = {"rule": name, "best_params": {"tol": best["tol"], "L": best["L"]}, "cred": cred, "scores": scores, "rechecked": rechecked,
           "episodes": int(sum(s["episodes"] for s in scores + rechecked)), **_provenance(smoke, markets)}
    Path(out).mkdir(parents=True, exist_ok=True); (Path(out) / f"tuned_{name}.json").write_text(json.dumps(res, default=float))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", required=True, choices=["comparator", *SYSTEMS])
    ap.add_argument("--markets", default="headline,dev0,dev1"); ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true"); ap.add_argument("--comparator", default=None)
    a = ap.parse_args(argv)
    markets = a.markets.split(","); out = Path(a.out)
    cred = json.loads(Path(a.comparator).read_text())["cred"] if a.comparator else None
    if a.select == "comparator":
        select_comparator(markets, out, a.smoke, workers=a.workers)
    else:
        if a.select == "C*-t" and cred is None:
            raise SystemExit("C*-t needs --comparator")
        tune_system(a.select, markets, out, cred if a.select == "C*-t" else None, a.smoke, workers=a.workers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
