"""Exploratory attackers: the registered per-cell pipeline (twin search, attack search with the registered incumbents,
exact corners, a cross-rule bank pass, reference selection in registered order, dev-val evaluation, budget doubling)
for the six post-verdict families of sim/policies/exploratory.py. Plan: docs/superpowers/plans/2026-10-20-exploratory-attackers.md.
Exploratory only: no registered artifact is read for a claim or changed; the final-evaluation seeds are never used.

X6 (simultaneous entrants) is a joint deviation: its searches use CoalitionObjective (every member takes the candidate's
knobs; the twin clips every member); its references are re-scored with honest opponents (coalition-cached scores never
rank a unilateral reference); its gain is focal profit in the coalition minus the best unilateral reference."""
from __future__ import annotations

import argparse, csv, hashlib, json, os, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.calibrate import cell_config, load_calibration
from sim.cell import Cell, SeedCache, run_focal
from sim.intervals import bound
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash
from sim.metrics import harm
from sim.policies.exploratory import (EXPLORATORY_FAMILIES, T_PUBLIC, W_PUBLIC, X6Policy, coalition_members, reset_overlap,
                                      scheduled_resets)
from sim.policies.families import exact_key
from sim.policies.honest import HonestMax
from sim.positions import positions
from sim.records import candidate_from_record, candidate_to_json, cfg_from_dict, cfg_to_dict, search_from_json, search_to_json
from sim.reference import (GainResult, attack_search, participant_diagnostics, reference_candidates, seed_rows, select_reference,
                           twin_search, _gross, _net)
from sim.registry import make_rule
from sim.rng import load_identity_salt
from sim.schedule import SMOKE_BUDGET, Budget, budget_from_locked
from sim.search import ArchiveEntry, Objective, SearchSettings, cma_search, corner_controls, settings_from_locked, best_archived
from sim.search_checks import DoublingCheck, FixedClipObjective, doubling_check, restart_spread, twin_vs_honest

ROOT = Path(__file__).resolve().parents[1]
RULES = ("B1", "B2", "B3", "proposed")
X6 = "X6-SE"
X6_SIZES = (1, 2, 5)
BETA, RHO, POSITION = 0.05, 0.2, "median"
DEV_SALT_PREFIX = "3b0350f7"           # the development salt of the registered dev-val records (matched controls)
X3_DIAGNOSTICS = (("diag_10_190", {"t0": 0.05, "span": 0.9, "z": 0}, [10, 190]), ("diag_190_200", {"t0": 0.95, "span": 0.05, "z": 0}, [190, 200]))
PREDICTION_ITEM = {"X1-AH": 2, "X2-TD": 2, "X3-HS": 3, "X4-RO": 4, "X5-AG": 4, "X6-SE": 5}
STAGES = ("search", "bank", "reference", "evaluate", "doubling", "report")


# ---- jobs and provenance ----------------------------------------------------------------------------------------------

def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_json(obj) -> str:
    return _sha(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode())


def git_commit() -> str:
    env = os.environ.get("TOUCHSTONE_GIT_COMMIT")
    if env:
        return env
    f = ROOT / "COMMIT"
    if f.exists():
        return f.read_text().strip()
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def rule_params(rule: str) -> dict:
    from scripts.sweep import load_params
    lk = load_locked(); cal = load_calibration(ROOT / "experiments/calibration.json")
    return load_params(rule, ROOT / "experiments/tuned", False, cal.market_key, settings_hash(lk), cal.seeds)


def cell_name(rule: str, family: str, c: int | None = None) -> str:
    return f"{rule}_{family}" + (f"_c{c}" if c is not None else "")


def job_for_x(rule: str, family: str, c: int | None = None, smoke: bool = False) -> dict:
    if (family == X6) != (c is not None):
        raise SystemExit(f"{family}: the coalition size c is required for X6 and only for X6")
    lk = load_locked(); cal = load_calibration(ROOT / "experiments/calibration.json")
    cfg = cell_config(market_config_from_locked(lk), cal, rho=RHO, beta=BETA)
    if cfg.T != T_PUBLIC:
        raise SystemExit(f"the gates assume T = {T_PUBLIC}; this market has T = {cfg.T}")
    b = SMOKE_BUDGET if smoke else budget_from_locked(lk)
    params = rule_params(rule)
    focal = positions(cfg)[POSITION]
    members = list(coalition_members(cfg, focal, c)) if family == X6 else [focal]
    salt = _sha(load_identity_salt())
    if not salt.startswith(DEV_SALT_PREFIX):
        raise SystemExit("the exploratory runs use the development salt of the registered dev-val records (unset TOUCHSTONE_IDENTITY_SALT)")
    s = settings_from_locked(lk)
    job = {"name": cell_name(rule, family, c), "rule": rule, "family": family, "c": c, "cfg": cfg_to_dict(cfg), "params": params,
           "budget": [b.restarts, b.evals, b.n_train, b.n_val], "smoke": bool(smoke), "focal": focal, "members": members,
           "seeds_train": [int(x) for x in locked_seeds(lk, "dev_train")[: b.n_train]], "seeds_val": [int(x) for x in locked_seeds(lk, "dev_val")[: b.n_val]],
           "search": {"popsize": s.popsize, "sigma0": s.sigma0, "reeval_every": s.reeval_every, "near_corner": s.near_corner, "sobol_seed": s.sobol_seed},
           "reference_order": list(lk["reference_order"]), "intervals": dict(lk["intervals"])}
    job["provenance"] = {"git_commit": git_commit(), "runner_sha256": _sha(Path(__file__).read_bytes()),
                         "policy_sha256": _sha((ROOT / "sim/policies/exploratory.py").read_bytes()), "params_sha256": _sha_json(params),
                         "cfg_sha256": _sha_json(job["cfg"]), "calibration_sha256": _sha((ROOT / "experiments/calibration.json").read_bytes()),
                         "salt_sha256": salt, "seeds_train": job["seeds_train"], "seeds_val": job["seeds_val"], "members": members,
                         "smoke": bool(smoke), "budget": job["budget"], "search": job["search"], "reference_order": job["reference_order"],
                         "intervals": job["intervals"]}
    check_job_seeds(job)
    return job


def check_job_seeds(job: dict) -> None:
    lk = load_locked(); allowed = set(int(x) for x in locked_seeds(lk, "dev_train")) | set(int(x) for x in locked_seeds(lk, "dev_val"))
    used = set(job["seeds_train"]) | set(job["seeds_val"])
    if not used <= allowed or not set(job["seeds_train"]) <= set(locked_seeds(lk, "dev_train")):
        raise SystemExit(f"{job['name']}: seeds outside the dev-train and dev-val allow-list: {sorted(used - allowed)}")


def check_inputs(job: dict, *recs) -> None:
    for rec in recs:
        if rec is None:
            continue
        if rec.get("provenance") != job["provenance"]:
            diff = sorted(k for k in set(rec.get("provenance", {})) | set(job["provenance"]) if rec.get("provenance", {}).get(k) != job["provenance"].get(k))
            raise SystemExit(f"{job['name']}: a stored record differs from this run in {diff}; rerun from the search stage")
        if rec.get("name") != job["name"]:
            raise SystemExit(f"{job['name']}: record belongs to another cell")


REQUIRED = {"search": ("twin", "attack", "corners", "restart_spread", "twin_vs_honest", "runs", "scheduled_runs"),
            "bank": ("attack", "bank_hash", "projected_members", "transfer", "inputs", "runs"),
            "reference": ("candidate", "candidates", "scores", "attack_knobs", "attack_f", "gain_train", "inputs", "runs"),
            "evaluate": ("rows", "controls", "reference_candidate", "inputs", "runs"),
            "doubling": ("doubling", "inputs", "runs")}


def validate_record(job: dict, stage: str, rec: dict | None, upstream: dict) -> None:
    """A stored record is consumed or skipped only if it is complete for its stage, belongs to this run (provenance,
    name), and was built from exactly the current upstream records (their hashes in its `inputs`)."""
    if rec is None:
        raise SystemExit(f"{job['name']}: no {stage} record; run the {stage} stage first")
    check_inputs(job, rec)
    missing = [k for k in REQUIRED[stage] if k not in rec]
    if rec.get("stage") != stage or missing:
        raise SystemExit(f"{job['name']}: the {stage} record is incomplete (missing {missing}); remove it and rerun")
    for key, up in upstream.items():
        want = _sha_json(up) if isinstance(up, dict) else up
        if rec["inputs"].get(key) != want:
            raise SystemExit(f"{job['name']}: the {stage} record was built from another {key} record; remove it and its downstream records")


def bank_source_cells(family: str, smoke: bool, rules, sizes) -> list[str]:
    """A real bank always draws on all four rules (and every X6 size), whatever cells are targeted; a smoke bank on the
    selected ones."""
    if smoke:
        return expected_cells(family, [r for r in RULES if r in rules], sorted(sizes) if family == X6 else None)
    return expected_cells(family, list(RULES), list(X6_SIZES) if family == X6 else None)


def upper_bound(gains, intervals: dict) -> tuple[float, bool]:
    b = bound("studentized", np.asarray(gains, dtype=float), "upper", 0.95, intervals)
    return float(b.value), bool(b.degenerate)


def settings_of(job: dict) -> SearchSettings:
    s = job["search"]; r, e, _, _ = job["budget"]
    return SearchSettings(popsize=s["popsize"], sigma0=s["sigma0"], restarts=r, evals_per_restart=e, reeval_every=s["reeval_every"],
                          near_corner=s["near_corner"], sobol_seed=s["sobol_seed"])


def _rule_factory(job):
    rule, params = job["rule"], job["params"]
    return lambda: make_rule(rule, params)


def make_unilateral_cell(job: dict, seeds: tuple) -> Cell:
    return Cell(cfg=cfg_from_dict(job["cfg"]), rule_factory=_rule_factory(job), focal=int(job["focal"]), seeds=tuple(seeds), name=job["name"])


def _member_factory(knobs: dict, j: int, c: int, staggered: bool, sink: list | None = None):
    def f():
        p = X6Policy(**knobs, member=j, c=c, staggered=staggered)
        if sink is not None:
            sink.append((j, p))
        return p
    return f


def coalition_cell(job: dict, seeds: tuple, knobs: dict, staggered: bool = False, sink: list | None = None) -> tuple[Cell, object]:
    """The cell with the c - 1 partners playing `knobs` (each its own instance) and the focal member's factory."""
    c = int(job["c"]); mem = job["members"]
    others = tuple((int(e), _member_factory(knobs, j, c, staggered, sink)) for j, e in enumerate(mem) if j > 0)
    cell = Cell(cfg=cfg_from_dict(job["cfg"]), rule_factory=_rule_factory(job), focal=int(job["focal"]), seeds=tuple(seeds), name=job["name"], others=others)
    return cell, _member_factory(knobs, 0, c, staggered, sink)


class UnilateralObjective(Objective):
    """The frozen Objective, named so X6 code paths that score unilaterally are distinguishable from frozen calls."""


class CoalitionObjective(Objective):
    """Focal normalized profit under the coordinated profile: every member plays the evaluated knobs (projected for
    every member when force_clip)."""

    def __init__(self, job: dict, seeds: tuple, cache: SeedCache, force_clip: bool = False) -> None:
        super().__init__(make_unilateral_cell(job, seeds), EXPLORATORY_FAMILIES[X6], cache, force_clip)
        self.job, self.seeds = job, tuple(seeds)

    def member_policies(self, knobs: dict) -> list:
        c = int(self.job["c"])
        return [X6Policy(**knobs, member=j, c=c, staggered=False) for j in range(c)]

    def eval_knobs(self, knobs: dict, source: str = "search") -> float:
        knobs = self.family.project(knobs) if self.force_clip else dict(knobs)
        cell, focal = coalition_cell(self.job, self.seeds, knobs)
        fr = run_focal(cell, focal, self.cache)
        f = float(fr.normalized.mean()); key = exact_key(knobs)
        if key not in self.archive:
            self.archive[key] = ArchiveEntry(knobs=dict(knobs), f=f, per_seed_profit=fr.profit, per_seed_normalized=fr.normalized,
                                             inflated=fr.inflated, source=source)
        self.log.append({"knobs": dict(knobs), "f": f, "source": source, "per_seed_normalized": [float(v) for v in fr.normalized]})
        self.evals += 1
        return f


def _objective(job: dict, seeds: tuple, cache: SeedCache, force_clip: bool = False):
    if job["family"] == X6:
        return CoalitionObjective(job, seeds, cache, force_clip)
    return Objective(make_unilateral_cell(job, seeds), EXPLORATORY_FAMILIES[job["family"]], cache, force_clip)


# ---- records ------------------------------------------------------------------------------------------------------------

def write_record(path: Path, rec: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(rec, indent=1, sort_keys=True, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)) + "\n")
    os.replace(tmp, path)


def read_record(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def _base(job: dict, cache: SeedCache, stage: str, scheduled: int | None = None, inputs: dict | None = None) -> dict:
    return {"name": job["name"], "rule": job["rule"], "family": job["family"], "c": job["c"], "stage": stage, "provenance": job["provenance"],
            "runs": cache.runs, "scheduled_runs": scheduled, "inputs": inputs or {}}


# ---- search ---------------------------------------------------------------------------------------------------------------

def search_schedule(job: dict) -> int:
    r, e, n_train, _ = job["budget"]; dim = EXPLORATORY_FAMILIES[job["family"]].dim
    per_seed = (r * e + 1) + (r * e + 2 + 1) + 2 ** dim + (len(X3_DIAGNOSTICS) if job["family"] == "X3-HS" else 0)
    return per_seed * n_train


def x_search(job: dict) -> dict:
    fam = EXPLORATORY_FAMILIES[job["family"]]; cache = SeedCache(); seeds = tuple(job["seeds_train"]); st = settings_of(job)
    if job["family"] == X6:
        starts = fam.registered_starts({"near_corner": st.near_corner, "sobol_seed": st.sobol_seed}, twin=True)
        tw = cma_search(CoalitionObjective(job, seeds, cache, force_clip=True), fam, st, 0, starts=starts)
        at = cma_search(CoalitionObjective(job, seeds, cache), fam, st, 1, incumbents={"twin_best": tw.best_knobs, "honest_point": fam.honest_point()})
    else:
        cell = make_unilateral_cell(job, seeds)
        tw = twin_search(cell, fam, cache, st, seed=0)
        at = attack_search(cell, fam, cache, st, seed=1, twin=tw)
    obj = _objective(job, seeds, cache); obj.archive.update(at.archive)
    corners = corner_controls(obj, fam)
    extra = 0

    def replace_best(knobs, f, source):
        nonlocal extra
        proj = fam.project(knobs); key = exact_key(proj)
        if key in obj.archive:
            pf = obj.archive[key].f
        else:
            pf = obj.eval_knobs(proj, source="projection"); extra += 1
        at.best_knobs, at.best_f, at.best_source = (proj, pf, "projection") if pf > f else (dict(knobs), f, source)
        at.projection_f, at.replaced_by_projection = pf, pf > f
        at.best_x = fam.inverse(at.best_knobs, st.near_corner)

    best_corner, best_corner_f = max(corners, key=lambda kf: kf[1])
    if best_corner_f > at.best_f:
        replace_best(best_corner, best_corner_f, "corner")
    diagnostics = []
    if job["family"] == "X3-HS":
        base = dict(at.best_knobs)
        for name, window_knobs, window in X3_DIAGNOSTICS:
            k = {**base, **window_knobs}; f = obj.eval_knobs(k, source=f"incumbent:{name}")
            diagnostics.append({"name": name, "window": window, "knobs": k, "f": f, "source": f"incumbent:{name}"})
        for d in diagnostics:
            if d["f"] > at.best_f:
                replace_best(d["knobs"], d["f"], d["source"])
    at.archive = obj.archive; at.evaluations = list(getattr(at, "evaluations", [])) + list(obj.log)
    rec = _base(job, cache, "search", scheduled=search_schedule(job) + extra * len(seeds))
    if rec["runs"] != rec["scheduled_runs"]:
        raise AssertionError(f"{job['name']}: ran {rec['runs']} episodes, schedule says {rec['scheduled_runs']}")
    rec.update({"twin": search_to_json(tw), "attack": search_to_json(at), "corners": [{"knobs": k, "f": f} for k, f in corners],
                "diagnostics": diagnostics, "restart_spread": restart_spread(at, tw),
                "twin_vs_honest": twin_vs_honest(tw, at.incumbent_scores["honest_point"]).__dict__})
    return rec


# ---- bank -----------------------------------------------------------------------------------------------------------------

def expected_cells(family: str, rules, sizes) -> list[str]:
    if family == X6:
        return [cell_name(r, family, c) for r in rules for c in sizes]
    return [cell_name(r, family) for r in rules]


def build_bank_doc(family: str, search: dict, rules, sizes, sources: dict | None = None, names: list | None = None) -> dict:
    """Members from a complete, immutable source manifest: per source cell in canonical order (rules B1, B2, B3, proposed;
    coalition sizes ascending) the attack best then the twin best, then the family's exact corners; exact-key
    de-duplication keeps the first occurrence."""
    rules = [r for r in RULES if r in rules]; sizes = sorted(sizes) if sizes else None
    names = names or expected_cells(family, rules, sizes)
    missing = [n for n in names if n not in search]
    if missing:
        raise SystemExit(f"bank for {family}: missing source search records {missing}; run the search stage for every cell first")
    members, seen = [], set()

    def take(k, origin):
        key = exact_key(k)
        if key not in seen:
            seen.add(key); members.append({"knobs": dict(k), "origin": origin})
    for n in names:
        take(search[n]["attack"]["best_knobs"], f"{n}:attack"); take(search[n]["twin"]["best_knobs"], f"{n}:twin")
    for k in EXPLORATORY_FAMILIES[family].corners():
        take(k, "corner")
    doc = {"family": family, "sources": {n: (sources or {}).get(n) or _sha_json(search[n]) for n in names}, "members": members}
    doc["bank_hash"] = _sha_json({"sources": doc["sources"], "members": members})
    return doc


def bank_pass_local(members: list, evaluate, incumbent_f: float, known: dict) -> dict:
    """The frozen Bank.bank_pass logic: every member scored (a known exact key takes its value), ranked descending with ties
    to the earlier member; replaced only when the best is strictly higher than the incumbent."""
    scored = []
    for m, origin in members:
        key = exact_key(m)
        f = known[key] if key in known else float(evaluate(m))
        scored.append((m, f, origin))
    scored.sort(key=lambda t: -t[1])
    if not scored:
        return {"ranked": [], "best_knobs": None, "best_f": float(incumbent_f), "best_origin": None, "improved": False}
    m, f, origin = scored[0]; improved = f > incumbent_f
    return {"ranked": scored, "best_knobs": m if improved else None, "best_f": f if improved else float(incumbent_f),
            "best_origin": origin if improved else None, "improved": improved}


def project_members(fam, members: list) -> list[dict]:
    projected, seen = [], set()
    for m, _ in members:
        p = fam.project(m); key = exact_key(p)
        if key not in seen:
            seen.add(key); projected.append(p)
    return projected


def x_bank(job: dict, rec: dict, doc: dict) -> dict:
    validate_record(job, "search", rec, {})
    if doc["family"] != job["family"] or job["name"] not in doc["sources"]:
        raise SystemExit(f"{job['name']}: the bank document does not list this cell as a source")
    fam = EXPLORATORY_FAMILIES[job["family"]]; cache = SeedCache(); seeds = tuple(job["seeds_train"])
    attack = search_from_json(rec["attack"])
    obj = _objective(job, seeds, cache); obj.archive.update(attack.archive)
    known = {k: e.f for k, e in attack.archive.items()}
    members = [(m["knobs"], m["origin"]) for m in doc["members"]]
    bp = bank_pass_local(members, lambda m: obj.eval_knobs(m, source="bank"), attack.best_f, known)
    if bp["improved"]:
        f = obj.eval_knobs(bp["best_knobs"], source=f"bank:{bp['best_origin']}")
        proj = fam.project(bp["best_knobs"]); pf = obj.eval_knobs(proj, source="projection")
        best, best_f, src = (proj, pf, "projection") if pf > f else (bp["best_knobs"], f, f"bank:{bp['best_origin']}")
        attack.best_knobs, attack.best_f, attack.best_source, attack.archive = best, best_f, src, obj.archive
        attack.projection_f, attack.replaced_by_projection = pf, pf > f
        attack.best_x = fam.inverse(best, settings_of(job).near_corner)
    projected = project_members(fam, members)
    out = _base(job, cache, "bank", inputs={"search": _sha_json(rec), "bank_hash": doc["bank_hash"]})
    out.update({"attack": search_to_json(attack), "bank_hash": doc["bank_hash"], "projected_members": projected,
                "transfer": {"cell": job["name"], "incumbent": float(rec["attack"]["best_f"]), "best_bank": float(bp["ranked"][0][1]) if bp["ranked"] else None,
                             "best_origin": bp["ranked"][0][2] if bp["ranked"] else None, "improved": bool(bp["improved"])}})
    return out


# ---- reference ------------------------------------------------------------------------------------------------------------

def _rescore_unilateral(job: dict, cell: Cell, attack, cache: SeedCache):
    """X6: every eligible truthful archive entry (clip 1, or clip 0 never inflated in the coalition) re-scored with honest
    opponents; entries inflated unilaterally drop out of the truthful clip-0 group. Archive order is kept."""
    fam = EXPLORATORY_FAMILIES[job["family"]]; uo = UnilateralObjective(cell, fam, cache)
    new = {}
    for key, e in attack.archive.items():
        if e.knobs["clip"] == 1 or not e.inflated:
            uo.eval_knobs(e.knobs, source="rescore")
            ue = uo.archive[exact_key(e.knobs)]
            if e.knobs["clip"] == 0 and ue.inflated:
                continue
            new[key] = ue
    return replace(attack, archive=new)


def x6_select_reference(job: dict, cell: Cell, attack, twin, members: list, cache: SeedCache, with_candidates: bool = False):
    att = _rescore_unilateral(job, cell, attack, cache)
    tw = replace(twin, archive={})                                   # the twin best is run with honest opponents
    cands = reference_candidates(cell, EXPLORATORY_FAMILIES[job["family"]], att, tw, members, tuple(job["reference_order"]))
    cands = [replace(c, known_profit=None, known_normalized=None) if c.name not in ("abstain",) and c.knobs is not None and exact_key(c.knobs) not in att.archive else c
             for c in cands]
    ref = select_reference(cell, cands, cache)
    return (ref, cands) if with_candidates else ref


def _require_bank(job: dict, bank_rec) -> None:
    if bank_rec is None and not job["smoke"]:
        raise SystemExit(f"{job['name']}: a real run needs the cell's bank record; run the bank stage first")


def x_reference(job: dict, rec: dict, bank_rec: dict | None) -> dict:
    _require_bank(job, bank_rec)
    validate_record(job, "search", rec, {})
    if bank_rec is not None:
        validate_record(job, "bank", bank_rec, {"search": rec})
    fam = EXPLORATORY_FAMILIES[job["family"]]; cache = SeedCache(); cell = make_unilateral_cell(job, tuple(job["seeds_train"]))
    attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); twin = search_from_json(rec["twin"])
    members = bank_rec["projected_members"] if bank_rec else []
    if job["family"] == X6:
        ref, cands = x6_select_reference(job, cell, attack, twin, members, cache, with_candidates=True)
    else:
        cands = reference_candidates(cell, fam, attack, twin, members, tuple(job["reference_order"]))
        ref = select_reference(cell, cands, cache)
    out = _base(job, cache, "reference", inputs={"search": _sha_json(rec), "bank": _sha_json(bank_rec) if bank_rec else None})
    out.update({"candidate": candidate_to_json(ref.candidate), "candidates": [candidate_to_json(c) for c in cands], "scores": ref.scores, "attack_knobs": attack.best_knobs, "attack_f": attack.best_f,
                "attack_source": attack.best_source, "gain_train": attack.best_f - ref.scores[ref.candidate.name],
                "bank_hash": bank_rec["bank_hash"] if bank_rec else None})
    return out


# ---- evaluate -------------------------------------------------------------------------------------------------------------

def assemble_gain(cell: Cell, attack, clipped, ref, honest) -> GainResult:
    """The frozen evaluate_gain arithmetic from four focal runs (the X6 attack and clipped runs use the coalition cell)."""
    N, f = cell.cfg.N, cell.focal
    sstar = np.array([r.sstar for r in attack.results]); scale = sstar / N
    inflation = (attack.profit - clipped.profit) / scale; selection = (clipped.profit - ref.profit) / scale
    hm = np.array([harm(a, r, f) for a, r in zip(attack.results, ref.results)])
    diag = [participant_diagnostics(r, cell.cfg, f) for r in attack.results]
    served = np.array([int(r.served[:, f].sum()) for r in attack.results])
    audited = np.array([int(r.audits.sum()) for r in attack.results]); total_served = np.array([int(r.served.sum()) for r in attack.results])
    return GainResult(
        gain=inflation + selection, inflation_term=inflation, selection_term=selection,
        profit_attack=attack.profit, profit_clip=clipped.profit, profit_ref=ref.profit, profit_honest=honest.profit, sstar=sstar,
        eff_attack=_gross(attack.results), eff_clip=_gross(clipped.results), eff_ref=_gross(ref.results), eff_honest=_gross(honest.results),
        net_eff_attack=_net(attack.results), net_eff_ref=_net(ref.results),
        audit_cost_attack=np.array([r.audit_cost for r in attack.results]), audit_spend_attack=np.array([r.audit_cost / r.sstar for r in attack.results]),
        audited_fraction_attack=np.where(total_served > 0, audited / np.maximum(total_served, 1), 0.0),
        harm_accounting=hm[:, 0], harm_direct=hm[:, 1], served_focal_attack=served,
        failures_focal_attack=np.array([int(r.failures[:, f].sum()) for r in attack.results]),
        entry_attack=np.array([r.entry for r in attack.results]), n_identities_attack=np.array([r.n_identities for r in attack.results]),
        others_profit_attack=np.array([float(r.profit.sum() - r.profit[f]) for r in attack.results]),
        refunds_attack=np.array([float(r.ledger.refunds.sum()) for r in attack.results]), forfeits_attack=np.array([float(r.ledger.forfeits.sum()) for r in attack.results]),
        holdback_in_attack=np.array([float(r.ledger.holdback_in.sum()) for r in attack.results]),
        refunds_focal_attack=np.array([d["refunds_focal"] for d in diag]), forfeits_focal_attack=np.array([d["forfeits_focal"] for d in diag]),
        focal_bans_attack=np.array([d["focal_bans"] for d in diag]), focal_audited_attack=np.array([d["focal_audited"] for d in diag]),
        focal_banned_rounds_attack=np.array([d["focal_banned_rounds"] for d in diag]), others_audited_attack=np.array([d["others_audited"] for d in diag]),
        others_bans_attack=np.array([d["others_bans"] for d in diag]), others_lost_capacity_attack=np.array([d["others_lost_capacity"] for d in diag]),
        seeds=tuple(cell.seeds))


def _others_outside(res, members: set) -> float:
    return res.buyer_surplus + float(sum(res.profit[e] for e in range(len(res.profit)) if e not in members)) - res.audit_cost


def local_diagnostics(res, cfg, focal: int, members: list, ref_res, honest_res) -> dict:
    """Focal identities; fresh (younger than W) served jobs and their audits for the focal entity and the market; rounds
    after the initial window whose fresh served jobs exceed the round's audits; bans on members' and outsiders' identities;
    capacity lost while an entity's active identity is banned, for members and outsiders separately (a ban on a retired
    identity excludes nothing); outsider harm as the registered direct harm with every member's profit removed from the
    others' welfare (equal to the registered harm_direct for a single member); members' mean profit change against
    all-honest-max. Outsiders play honest-max, so their bans are false bans."""
    mem = set(members); ent = res.entity_of; born = res.identity_round; gen = res.identity_generation
    out = {"focal_identities": sum(1 for e in ent if e == focal), "fresh_served_focal": 0, "fresh_audited_focal": 0, "fresh_served_market": 0,
           "rounds_fresh_exceeds_audits": 0, "member_bans": 0, "outsider_bans": 0, "outsider_false_bans": 0,
           "member_lost_capacity": 0, "outsider_lost_capacity": 0}
    by_entity: dict[int, list] = {}
    for i, e in enumerate(ent):
        by_entity.setdefault(e, []).append(i)
    banned_until: dict[int, int] = {}
    for rec in res.history:
        t = rec.t; audited = {a.job for a in rec.audits}; fresh_round = 0
        for j, i in rec.assignment.items():
            if t - born[i] < W_PUBLIC:
                fresh_round += 1
                if ent[i] == focal:
                    out["fresh_served_focal"] += 1; out["fresh_audited_focal"] += int(j in audited)
        out["fresh_served_market"] += fresh_round
        if t >= W_PUBLIC and fresh_round > len(rec.audits):
            out["rounds_fresh_exceeds_audits"] += 1
        for e, ids in by_entity.items():
            active = max((i for i in ids if born[i] <= t), key=lambda i: (born[i], gen[i]))
            if t < banned_until.get(active, 0):
                out["member_lost_capacity" if e in mem else "outsider_lost_capacity"] += cfg.providers[e].k
        for i, rounds in rec.consequences.bans.items():
            if ent[i] in mem:
                out["member_bans"] += 1
            else:
                out["outsider_bans"] += 1; out["outsider_false_bans"] += 1
            banned_until[i] = max(banned_until.get(i, 0), t + int(rounds) + 1)
    out["harm_outsiders"] = float((_others_outside(ref_res, mem) - _others_outside(res, mem)) / res.sstar)
    scale = res.sstar / cfg.N
    out["member_gain_vs_honest"] = float(np.mean([(res.profit[e] - honest_res.profit[e]) / scale for e in members]))
    return out


def x_evaluate(job: dict, ref_rec: dict) -> dict:
    validate_record(job, "reference", ref_rec, {})
    fam = EXPLORATORY_FAMILIES[job["family"]]; cache = SeedCache(); val = tuple(job["seeds_val"])
    uni = make_unilateral_cell(job, val)
    k = dict(ref_rec["attack_knobs"]); kp = fam.project(k)
    cand = candidate_from_record(fam, ref_rec["candidate"])
    if job["family"] == X6:
        ca, fa = coalition_cell(job, val, k); cc, fc = coalition_cell(job, val, kp)
        attack, clipped = run_focal(ca, fa, cache), run_focal(cc, fc, cache)
    else:
        attack, clipped = run_focal(uni, lambda: fam.make(k), cache), run_focal(uni, lambda: fam.make(kp), cache)
    ref = run_focal(uni, cand.policy_factory, cache); honest = run_focal(uni, HonestMax, cache)
    g = assemble_gain(uni, attack, clipped, ref, honest)
    meta = {"cell": job["name"], "rule": job["rule"], "family": job["family"], "c": job["c"], "beta": BETA, "rho": RHO, "position": POSITION,
            "smoke": job["smoke"], "reference": ref_rec["candidate"]["name"], "budget": float(job["cfg"]["budget"])}
    rows = seed_rows(uni, g, meta)
    for n, row in enumerate(rows):
        row.update(local_diagnostics(attack.results[n], uni.cfg, int(job["focal"]), job["members"], ref.results[n], honest.results[n]))
        if job["family"] == X6:          # the frozen others_* diagnostics treat partners as outsiders; the local fields replace them
            for f in ("others_bans_attack", "others_lost_capacity_attack", "others_audited_attack", "harm_accounting", "harm_direct"):
                row[f] = None
    controls = x6_controls(job, k, ref, honest, cache) if job["family"] == X6 and int(job["c"]) > 1 else {}
    out = _base(job, cache, "evaluate", inputs={"reference": _sha_json(ref_rec)})
    out.update({"rows": rows, "controls": controls, "reference_candidate": ref_rec["candidate"]["name"], "bank_hash": ref_rec.get("bank_hash")})
    return out


def x6_controls(job: dict, k: dict, ref, honest, cache: SeedCache) -> dict:
    """At the selected point: synchronised and staggered scheduled resets with x as selected, and the same pair with x = 0.
    Each control runs the coalition attack and its all-member projection with that schedule against the same unilateral
    reference and honest-max runs; scheduled, failure-triggered, and coincident resets are counted per member; a staggered
    schedule with P' < c is labelled partially staggered and its overlap reported."""
    if not k.get("y"):
        return {"note": "y = 0: no scheduled resets, no timing control"}
    val = tuple(job["seeds_val"]); c = int(job["c"]); uni = make_unilateral_cell(job, val); fam = EXPLORATORY_FAMILIES[X6]
    Pp = max(1, int(round(float(k["P"])))); out = {}
    for xv in sorted({int(k["x"]), 0}, reverse=True):
        for stag in (False, True):
            kk = {**k, "x": xv}; sink = []
            ca, fa = coalition_cell(job, val, kk, staggered=stag, sink=sink); cc, fc = coalition_cell(job, val, fam.project(kk), staggered=stag)
            att, clp = run_focal(ca, fa, cache), run_focal(cc, fc, cache)
            g = assemble_gain(uni, att, clp, ref, honest)
            diag = [local_diagnostics(att.results[n], uni.cfg, int(job["focal"]), job["members"], ref.results[n], honest.results[n]) for n in range(len(val))]
            resets = [{"scheduled": 0, "failure": 0, "coincident": 0} for _ in range(c)]
            for j, pol in sink:
                resets[j]["scheduled"] += pol.resets_scheduled; resets[j]["failure"] += pol.resets_failure; resets[j]["coincident"] += pol.resets_coincident
            ub, deg = upper_bound(g.gain, job["intervals"])
            out[f"x{xv}_{'staggered' if stag else 'synchronised'}"] = {
                "gain": [float(v) for v in g.gain], "gain_mean": float(np.mean(g.gain)), "gain_upper95": ub, "degenerate_bound": deg,
                "inflation_term": float(np.mean(g.inflation_term)), "selection_term": float(np.mean(g.selection_term)),
                "eff_attack": float(np.mean(g.eff_attack)), "eff_clip": float(np.mean(g.eff_clip)), "eff_ref": float(np.mean(g.eff_ref)),
                "eff_honest": float(np.mean(g.eff_honest)), "audit_spend": float(np.mean(g.audit_spend_attack)),
                "harm_outsiders": float(np.mean([d["harm_outsiders"] for d in diag])), "member_bans": float(np.mean([d["member_bans"] for d in diag])),
                "outsider_bans": float(np.mean([d["outsider_bans"] for d in diag])), "focal_identities": float(np.mean([d["focal_identities"] for d in diag])),
                "resets_by_member": resets, "overlap": reset_overlap(scheduled_resets(k["P"], c, T_PUBLIC, staggered=stag)),
                "partially_staggered": bool(stag and Pp < c)}
    return out


# ---- doubling ---------------------------------------------------------------------------------------------------------------

def x_doubling(job: dict, rec: dict, bank_rec: dict | None) -> dict:
    _require_bank(job, bank_rec)
    validate_record(job, "search", rec, {})
    if bank_rec is not None:
        validate_record(job, "bank", bank_rec, {"search": rec})
    fam = EXPLORATORY_FAMILIES[job["family"]]; cache = SeedCache(); seeds = tuple(job["seeds_train"]); st = settings_of(job)
    base_attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); base_twin = search_from_json(rec["twin"])
    members = bank_rec["projected_members"] if bank_rec else []; order = tuple(job["reference_order"])
    cell = make_unilateral_cell(job, seeds)
    if job["family"] != X6:
        dc = doubling_check(cell, fam, cache, st, seed=0, base_attack=base_attack, base_twin=base_twin, bank_members=members, order=order)
    else:
        half = replace(st, evals_per_restart=max(1, st.evals_per_restart // 2))
        c0 = cma_search(FixedClipObjective(CoalitionObjective(job, seeds, cache), 0), fam, half, 100)
        c1 = cma_search(FixedClipObjective(CoalitionObjective(job, seeds, cache), 1), fam, half, 200)
        doubled = max((base_attack, c0, c1), key=lambda r: r.best_f)
        merged = replace(doubled, archive={**base_attack.archive, **c0.archive, **c1.archive})
        rb_ = x6_select_reference(job, cell, base_attack, base_twin, members, cache)
        rd_ = x6_select_reference(job, cell, merged, base_twin, members, cache)
        rb, rd = rb_.scores[rb_.candidate.name], rd_.scores[rd_.candidate.name]
        gb, gd = base_attack.best_f - rb, merged.best_f - rd
        dc = DoublingCheck(attack_base_f=base_attack.best_f, attack_doubled_f=merged.best_f, clip0_f=c0.best_f, clip1_f=c1.best_f,
                           clip0_search_f=float(max(c0.restart_bests)), clip1_search_f=float(max(c1.restart_bests)), ref_base_f=rb, ref_doubled_f=rd,
                           ref_base_name=rb_.candidate.name, ref_doubled_name=rd_.candidate.name, gain_base=gb, gain_doubled=gd,
                           delta_gain=gd - gb, passed=bool(abs(gd - gb) < 0.005))
    out = _base(job, cache, "doubling", inputs={"search": _sha_json(rec), "bank": _sha_json(bank_rec) if bank_rec else None})
    out["doubling"] = {k: (float(v) if isinstance(v, (float, np.floating)) else v) for k, v in dc.__dict__.items()}
    return out


# ---- manifest, report, orchestration ----------------------------------------------------------------------------------

def all_jobs(rules, families, sizes, smoke) -> list[dict]:
    out = []
    for f in families:
        for r in [r for r in RULES if r in rules]:
            for c in (sorted(sizes) if f == X6 else [None]):
                out.append(job_for_x(r, f, c, smoke))
    return out


def episode_manifest(smoke: bool, rules, families, sizes) -> dict:
    lk = load_locked(); b = SMOKE_BUDGET if smoke else budget_from_locked(lk)
    n = 0; eps = 0
    for f in families:
        for _ in rules:
            for _c in (sizes if f == X6 else [None]):
                dim = EXPLORATORY_FAMILIES[f].dim
                eps += ((b.restarts * b.evals + 1) + (b.restarts * b.evals + 3) + 2 ** dim + (2 if f == "X3-HS" else 0)) * b.n_train; n += 1
    return {"cells": n, "search_episodes": eps, "budget": [b.restarts, b.evals, b.n_train, b.n_val]}


def _mean(rows, k):
    return float(np.mean([r[k] for r in rows]))


def prediction_text(item: int) -> str:
    text = (ROOT / "docs/exploratory/2026-10-20-predictions.md").read_text()
    sec = text.split("## Predictions", 1)[1].split("\n## ", 1)[0]
    for line in sec.splitlines():
        if line.strip().startswith(f"{item}. "):
            return " ".join(line.split())
    raise SystemExit(f"prediction item {item} not found")


def report(out: Path, jobs: list[dict], registered_sweep: Path | None = None) -> dict:
    """Every expected cell's evaluation must exist, belong to this run, rest on its current reference record, and carry
    exactly the job's evaluation seeds; a real report needs the matched registered D2+H3 dev-val control for every rule."""
    final_rows = {}
    fd = ROOT / "docs/final-evaluation-2026-10-20/figures/figure_data.csv"
    for r in csv.DictReader(open(fd)):
        if r["family"] == "D2+H3":
            final_rows[r["rule"]] = float(r["gain_mean"])
    smoke = {j["smoke"] for j in jobs}
    if len(smoke) != 1:
        raise SystemExit("a report mixes smoke and real cells")
    smoke = smoke.pop(); cells, sources = [], {}
    for job in jobs:
        name = job["name"]
        se = read_record(out / "search" / f"{name}.json"); bk = read_record(out / "bank" / f"{name}.json")
        ref = read_record(out / "reference" / f"{name}.json"); ev = read_record(out / "evaluate" / f"{name}.json")
        dbl = read_record(out / "doubling" / f"{name}.json")
        validate_record(job, "search", se, {})
        if bk is not None or not smoke:
            validate_record(job, "bank", bk, {"search": se})
        validate_record(job, "reference", ref, {"search": se, **({"bank": bk} if bk is not None else {})})
        validate_record(job, "evaluate", ev, {"reference": ref})
        rows = ev["rows"]
        if [int(r["seed"]) for r in rows] != list(job["seeds_val"]):
            raise SystemExit(f"{name}: the evaluation rows do not carry exactly the job's evaluation seeds")
        sources[name] = _sha_json(ev)
        gains = [r["gain"] for r in rows]; ub, deg = upper_bound(gains, job["intervals"])
        ctrl = None
        p = (registered_sweep / "evaluate" / f"{job['rule']}_D2+H3_beta0.05_rho0.2_median_h3.json") if registered_sweep else None
        if p is not None and p.exists():
            ctrl = float(np.mean([x["gain"] for x in json.loads(p.read_text())["rows"]]))
        elif not smoke:
            raise SystemExit(f"{name}: the matched registered D2+H3 dev-val control is missing (pass --registered-sweep)")
        item = 1 if job["rule"] == "B1" else PREDICTION_ITEM[job["family"]]
        x6 = job["family"] == X6
        cells.append({"cell": name, "rule": job["rule"], "family": job["family"], "c": job["c"], "n": len(rows),
                      "gain_mean": float(np.mean(gains)), "gain_upper95_studentized": ub, "degenerate_bound": deg,
                      "inflation_term": _mean(rows, "inflation_term"), "selection_term": _mean(rows, "selection_term"),
                      "eff_attack": _mean(rows, "eff_attack"), "eff_clip": _mean(rows, "eff_clip"), "eff_ref": _mean(rows, "eff_ref"),
                      "eff_honest": _mean(rows, "eff_honest"), "net_eff_attack": _mean(rows, "net_eff_attack"),
                      "harm": _mean(rows, "harm_outsiders" if x6 else "harm_direct"), "harm_definition": "outsiders, direct" if x6 else "registered harm_direct",
                      "audit_spend": _mean(rows, "audit_spend_attack"), "focal_failures": _mean(rows, "failures_focal_attack"),
                      "focal_bans": _mean(rows, "focal_bans_attack"), "focal_identities": _mean(rows, "focal_identities"),
                      "member_bans": _mean(rows, "member_bans"), "outsider_false_bans": _mean(rows, "outsider_false_bans"),
                      "outsider_lost_capacity": _mean(rows, "outsider_lost_capacity"), "member_gain_vs_honest": _mean(rows, "member_gain_vs_honest"),
                      "fresh_audit_coverage_focal": sum(r["fresh_audited_focal"] for r in rows) / max(1, sum(r["fresh_served_focal"] for r in rows)),
                      "rounds_fresh_exceeds_audits": _mean(rows, "rounds_fresh_exceeds_audits"),
                      "knobs": ref["attack_knobs"], "source": ref["attack_source"], "reference": ev["reference_candidate"],
                      "restart_gain_spread": se["restart_spread"]["gain_spread"], "twin_vs_honest_passed": se["twin_vs_honest"]["passed"],
                      "bank_improved": bk["transfer"]["improved"] if bk else None, "doubling_delta": dbl["doubling"]["delta_gain"] if dbl else None,
                      "controls": ev.get("controls") or None, "control_d2h3_devval_gain": ctrl, "final40_d2h3_gain": final_rows.get(job["rule"]),
                      "prediction_item": item, "prediction": prediction_text(item)})
    doc = {"status": "exploratory; descriptive bounds at n = 20 (no coverage admission); dev-val informed earlier development",
           "smoke": smoke, "git_commit": git_commit(), "sources": sources, "cells": cells}
    write_record(out / "report.json", doc)
    return doc


def upstream_of(out: Path, job: dict, stage: str) -> dict:
    name = job["name"]; se = read_record(out / "search" / f"{name}.json"); bk = read_record(out / "bank" / f"{name}.json")
    if stage == "search":
        return {}
    if stage == "bank":
        doc = read_record(out / f"bank_{job['family']}.json")
        return {"search": se, "bank_hash": doc["bank_hash"] if doc else None}
    if stage in ("reference", "doubling"):
        return {"search": se, **({"bank": bk} if bk is not None else {})}
    if stage == "evaluate":
        return {"reference": read_record(out / "reference" / f"{name}.json")}
    raise ValueError(stage)


def _stage_job(stage, job, out_s):
    out = Path(out_s); name = job["name"]
    src = read_record(out / "search" / f"{name}.json")
    if stage == "search":
        return x_search(job)
    if stage == "bank":
        return x_bank(job, src, read_record(out / f"bank_{job['family']}.json"))
    bk = read_record(out / "bank" / f"{name}.json")
    if stage == "reference":
        return x_reference(job, src, bk)
    if stage == "evaluate":
        return x_evaluate(job, read_record(out / "reference" / f"{name}.json"))
    if stage == "doubling":
        return x_doubling(job, src, bk)
    raise ValueError(stage)


def run(o: dict) -> dict:
    out = Path(o["out"]); out.mkdir(parents=True, exist_ok=True)
    rules = o["rules"].split(","); fams = o["families"].split(","); sizes = [int(c) for c in str(o.get("sizes", "1,2,5")).split(",")]
    smoke = bool(o.get("smoke")); jobs = all_jobs(rules, fams, sizes, smoke)
    wanted = set(STAGES) if o["stage"] == "all" else set(str(o["stage"]).split(","))
    if not wanted <= set(STAGES):
        raise SystemExit(f"unknown stages {sorted(wanted - set(STAGES))}")
    stages = [s for s in STAGES if s in wanted]
    counted = {s: 0 for s in stages}
    pool = ProcessPoolExecutor(max_workers=int(o.get("workers", 1))) if int(o.get("workers", 1)) > 1 else None
    timings = {}
    for stage in stages:
        t0 = time.time()
        if stage == "report":
            report(out, jobs, Path(o["registered_sweep"]) if o.get("registered_sweep") else None); timings[stage] = time.time() - t0
            continue
        if stage == "bank":
            for f in fams:
                fj = [j for j in jobs if j["family"] == f]
                src_names = bank_source_cells(f, smoke, rules, sizes)
                search = {n: read_record(out / "search" / f"{n}.json") for n in src_names}
                search = {k: v for k, v in search.items() if v is not None}
                for n, v in search.items():
                    jb = next((j for j in jobs if j["name"] == n), None) or job_for_x(v["rule"], f, v.get("c"), smoke)
                    validate_record(jb, "search", v, {})
                doc = build_bank_doc(f, search, rules, sizes if f == X6 else None, names=bank_source_cells(f, smoke, rules, sizes))
                old = read_record(out / f"bank_{f}.json")
                if old is not None and old["bank_hash"] != doc["bank_hash"]:
                    raise SystemExit(f"bank_{f}.json was built from other sources; remove the stale bank and its downstream records")
                write_record(out / f"bank_{f}.json", doc)
        todo = jobs
        if stage == "doubling":
            todo = []
            for r in rules:
                evs = [(j, read_record(out / "evaluate" / f"{j['name']}.json")) for j in jobs if j["rule"] == r]
                evs = [(j, e) for j, e in evs if e is not None]
                evs.sort(key=lambda je: -np.mean([x["gain"] for x in je[1]["rows"]]))
                todo += [j for j, _ in evs[:2]]
        pending = []
        for j in todo:
            p = out / stage / f"{j['name']}.json"; existing = read_record(p)
            if existing is not None:
                validate_record(j, stage, existing, upstream_of(out, j, stage)); continue      # resume: a complete, current stage is skipped
            pending.append(j)
        res = pool.map(_stage_job, [stage] * len(pending), pending, [str(out)] * len(pending)) if pool else map(lambda j: _stage_job(stage, j, str(out)), pending)
        for j, rec in zip(pending, res):
            write_record(out / stage / f"{j['name']}.json", rec); counted[stage] += int(rec["runs"])
        timings[stage] = time.time() - t0
    if pool:
        pool.shutdown()
    if o.get("pilot"):
        print(json.dumps({"manifest": episode_manifest(smoke, rules, fams, sizes), "timings_s": timings, "runs": counted}, indent=1))
    return counted


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all", help="all, or a comma-separated list of " + ",".join(STAGES)); ap.add_argument("--rules", default=",".join(RULES))
    ap.add_argument("--families", default=",".join(EXPLORATORY_FAMILIES)); ap.add_argument("--sizes", default="1,2,5")
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--out", default="results/exploratory")
    ap.add_argument("--smoke", action="store_true"); ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--registered-sweep", dest="registered_sweep", default=None)
    a = ap.parse_args()
    print(json.dumps(run(vars(a))))


if __name__ == "__main__":
    main()
