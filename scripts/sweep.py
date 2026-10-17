from __future__ import annotations

import argparse, csv, hashlib, json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim.all_deviators import iterated_best_response
from sim.bank import Bank
from sim.calibrate import cell_config, load_calibration
from sim.cell import Cell, SeedCache
from sim.locked import load_locked, market_config_from_locked, seeds as locked_seeds, settings_hash
from sim.manifest import CellSpec, cell_name, enumerate_manifest
from sim.rng import load_identity_salt
from sim.policies.families import D2, FAMILIES, exact_key
from sim.registry import SEALED_DIR, available_families, make_rule, proposed_params
from sim.sealed import bundle_hash
from sim.positions import headline_position, positions
from sim.records import candidate_from_record, candidate_to_json, cfg_from_dict, cfg_to_dict, search_from_json, search_to_json
from sim.reference import ROW_FIELDS, attack_search, evaluate_gain, reference_candidates, seed_rows, select_reference, twin_search
from sim.schedule import SMOKE_BUDGET, Budget, all_deviators_runs, bank_stage_bound, budget_from_locked, doubling_bound, reference_bound, stage_runs
from sim.search import Objective, SearchSettings, corner_controls, settings_from_locked
from sim.search_checks import doubling_check, restart_spread, twin_vs_honest

DEFAULT_PARAMS = {"B1": {"P1": 0.25, "P2": 0.40, "P3": 0.55},
                  "B2": {"P1": 0.25, "P2": 0.40, "P3": 0.55, "tol": 0.12, "L": 10},
                  "B3": {"tol": 0.12, "L": 10}}
DEFAULT_PARAMS["proposed"] = dict(DEFAULT_PARAMS["B2"])          # smoke runs of a synthetic proposed module that wraps B2
STAGES = ("search", "bank", "reference", "evaluate", "checks", "all_deviators")
META_FIELDS = ["cell", "section", "rule", "family", "beta", "rho", "position", "smoke", "reference", "budget"]


def family_of(name: str):
    """The registry re-reads the sealed path on every call, so a bundle unsealed later is seen without a restart; after the
    lock the bundle must match its commitment before H2 is used."""
    lk = load_locked()
    return available_families(lk if lk.get("sealed_bundle_sha256") else None)[name]


def load_params(rule: str, tuned_dir: Path | None, smoke: bool, market_key: str, shash: str, cal_seeds) -> dict:
    if tuned_dir is None:
        if not smoke:
            raise SystemExit("refusing to run without tuned parameters: pass --tuned-dir, or --smoke for a smoke run")
        return dict(DEFAULT_PARAMS[rule])
    if rule == "proposed":
        d = proposed_params(); p = Path("experiments/proposed.yaml")             # the allow-listed parameter file of the proposed rule
    else:
        p = tuned_dir / f"tuned_{rule}.json"
        if not p.exists():
            raise SystemExit(f"tuned parameters for {rule} not found at {p}")
        d = json.loads(p.read_text())
    if d.get("rule") != rule:
        raise SystemExit(f"{p} is a tuning result for rule {d.get('rule')!r}, not {rule}")
    if d.get("market_key") != market_key:
        raise SystemExit(f"{p} was tuned on another market (market_key mismatch)")
    if d.get("settings_hash") != shash:
        raise SystemExit(f"{p} was tuned under other locked settings (settings_hash mismatch)")
    if d.get("quick"):
        raise SystemExit(f"{p} is a quick tuning result and cannot be used for a real run")
    if list(d.get("calibration_seeds", [])) != list(cal_seeds):
        raise SystemExit(f"{p} was tuned with another calibration (calibration seeds differ)")
    return dict(d["best_params"])


def settings_for(locked: dict, budget: Budget) -> SearchSettings:
    s = settings_from_locked(locked)
    return SearchSettings(popsize=s.popsize, sigma0=s.sigma0, restarts=budget.restarts, evals_per_restart=budget.evals,
                          reeval_every=s.reeval_every, near_corner=s.near_corner, sobol_seed=s.sobol_seed)


def job_for(spec: CellSpec, locked: dict, cal, base, params: dict, budget: Budget, smoke: bool, eval_namespace: str = "dev_val") -> dict:
    cfg = cell_config(base, cal, rho=spec.rho, beta=spec.beta)
    p = dict(params); p.update(spec.params_override or {})
    return {"spec": {"name": spec.name, "section": spec.section, "rule": spec.rule, "family": spec.family, "beta": spec.beta,
                     "rho": spec.rho, "position": spec.position}, "cfg": cfg_to_dict(cfg), "params": p, "locked": locked,
            "budget": [budget.restarts, budget.evals, budget.n_train, budget.n_val], "smoke": smoke, "settings_hash": settings_hash(locked),
            "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest(), "eval_namespace": eval_namespace}


def check_record(job: dict, rec: dict) -> None:
    """A later stage refuses a record from another configuration or mode (stale tuned parameters, calibration,
    settings, budget, or a smoke record under a real run)."""
    for key in ("params", "cfg", "settings_hash", "budget", "smoke", "salt_hash", "eval_namespace"):
        if rec.get(key) != job[key]:
            raise SystemExit(f"{job['spec']['name']}: stored {key} differs from the current run; rerun from the search stage")
    if rec.get("spec", {}).get("name") != job["spec"]["name"]:
        raise SystemExit(f"{job['spec']['name']}: record belongs to another cell")


def make_cell(job: dict, seeds: tuple[int, ...], suffix: str = "") -> Cell:
    cfg = cfg_from_dict(job["cfg"]); params = job["params"]; rule = job["spec"]["rule"]
    return Cell(cfg=cfg, rule_factory=lambda: make_rule(rule, params), focal=positions(cfg)[job["spec"]["position"]],
                seeds=seeds, name=job["spec"]["name"] + suffix)


def train_val(job: dict) -> tuple[tuple[int, ...], tuple[int, ...], Budget]:
    """Dev-train seeds, the evaluation seeds of the job's namespace, and the budget whose n_val is the evaluation size:
    under final_eval the registered size is coverage_consequences.final_eval_n (20 or 40), so the evaluate stage's exact
    run count follows it."""
    b = Budget(*job["budget"]); lk = job["locked"]; ns = job.get("eval_namespace", "dev_val")
    n_eval = int((lk.get("coverage_consequences") or {}).get("final_eval_n") or b.n_val) if ns == "final_eval" else b.n_val
    b_eval = Budget(b.restarts, b.evals, b.n_train, n_eval)
    return tuple(locked_seeds(lk, "dev_train")[: b.n_train]), tuple(locked_seeds(lk, ns)[: n_eval]), b_eval


def base_record(job: dict, cache: SeedCache, scheduled: int, exact: bool) -> dict:
    if exact and cache.runs != scheduled:
        raise AssertionError(f"{job['spec']['name']}: ran {cache.runs} episodes, schedule says {scheduled}")
    if not exact and cache.runs > scheduled:
        raise AssertionError(f"{job['spec']['name']}: ran {cache.runs} episodes, schedule bound is {scheduled}")
    return {"spec": job["spec"], "cfg": job["cfg"], "params": job["params"], "settings_hash": job["settings_hash"], "smoke": job["smoke"],
            "budget": job["budget"], "salt_hash": job["salt_hash"], "eval_namespace": job["eval_namespace"], "runs": cache.runs, "scheduled": scheduled,
            "bundle_hash": bundle_hash(SEALED_DIR) if job["spec"]["family"] == "H2" else None}


def stage_search(job: dict) -> dict:
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    settings = settings_for(job["locked"], b)
    tw = twin_search(cell, fam, cache, settings, seed=0)
    at = attack_search(cell, fam, cache, settings, seed=1, twin=tw)
    obj = Objective(cell, fam, cache); obj.archive.update(at.archive)
    corners = corner_controls(obj, fam)
    best_corner, best_corner_f = max(corners, key=lambda kf: kf[1])
    if best_corner_f > at.best_f:     # an exact corner control replaces the incumbent when it scores higher (spec 8); its projection is a corner, already evaluated
        proj = fam.project(best_corner); pf = obj.archive[exact_key(proj)].f
        at.best_knobs, at.best_f, at.best_source = (proj, pf, "projection") if pf > best_corner_f else (best_corner, best_corner_f, "corner")
        at.projection_f, at.replaced_by_projection = pf, pf > best_corner_f
        at.best_x = fam.inverse(at.best_knobs, settings.near_corner)      # coordinates follow the selected point (approximate, as for incumbents)
    at.archive = obj.archive
    rec = base_record(job, cache, stage_runs(job["spec"]["family"], "search", b), exact=True)
    rec.update({"twin": search_to_json(tw), "attack": search_to_json(at), "corners": [{"knobs": k, "f": f} for k, f in corners],
                "restart_spread": restart_spread(at, tw), "twin_vs_honest": twin_vs_honest(tw, at.incumbent_scores["honest_point"]).__dict__})
    return rec


def record_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_bank(out: Path, search: dict, jobs: dict) -> dict:
    """Every source record is validated before any member enters the bank; the bank document lists its sources with
    their hashes and carries a hash of members and sources, which every bank record and every later stage checks."""
    for name, rec in search.items():
        check_record(jobs[name], rec)
    bank = Bank(); sources = {}
    for name, rec in search.items():
        if rec["spec"]["section"] == "development":
            bank.add(rec["spec"]["family"], rec["attack"]["best_knobs"], origin=name)
            sources[name] = record_hash(out / "search" / f"{name}.json")
    members = json.loads(bank.to_json())
    from sim.policies.families import H3_EMBEDDINGS
    embeddings = {"D2+H3": list(H3_EMBEDDINGS)}                                   # amendment 2: the registered transfer into the H3 cells, inside the hash
    bank_hash = hashlib.sha256(json.dumps({"members": members, "sources": sources, "embeddings": embeddings}, sort_keys=True).encode()).hexdigest()
    return {"members": members, "sources": sources, "embeddings": embeddings, "bank_hash": bank_hash}


def load_bank_doc(out: Path) -> dict:
    """The current bank document, refused when a source record changed or disappeared since the bank was built, or when
    its embeddings entry is not the registered one (amendment 2)."""
    doc = json.loads((out / "bank.json").read_text())
    from sim.policies.families import H3_EMBEDDINGS
    if doc.get("embeddings") != {"D2+H3": list(H3_EMBEDDINGS)}:
        raise SystemExit("bank.json: the embeddings entry is not the registered D2-to-H3 transfer; rebuild the bank")
    want = hashlib.sha256(json.dumps({"members": doc["members"], "sources": doc["sources"], "embeddings": doc["embeddings"]}, sort_keys=True).encode()).hexdigest()
    if doc.get("bank_hash") != want:
        raise SystemExit("bank.json: bank_hash does not cover its members, sources, and embeddings; rebuild the bank")
    for name, h in doc["sources"].items():
        path = out / "search" / f"{name}.json"
        if not path.exists() or record_hash(path) != h:
            raise SystemExit(f"bank source {name} changed or disappeared since the bank was built; rerun the bank stage")
    return doc


def check_bank_record(rec: dict | None, doc: dict | None, stage: str) -> None:
    """A bank or reference record of a D1, D2, or (amendment 2) D2+H3 cell must come from the current bank (its hash)."""
    if rec is None:
        return
    needs_bank = rec["spec"]["family"] in FAMILIES or rec["spec"]["family"] == "D2+H3"
    if rec.get("bank_hash") is None:
        if needs_bank:
            raise SystemExit(f"{rec['spec']['name']}: record carries no bank hash; rerun the bank and reference stages before {stage}")
        return
    if doc is None or rec["bank_hash"] != doc["bank_hash"]:
        raise SystemExit(f"{rec['spec']['name']}: record belongs to another bank; rerun the bank and reference stages before {stage}")


def stage_bank(job: dict, rec: dict, bank_doc: dict) -> dict:
    check_record(job, rec)
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    bank = Bank.from_json(json.dumps(bank_doc["members"]))
    attack = search_from_json(rec["attack"])
    known = {exact_key(c["knobs"]): float(c["f"]) for c in rec["corners"]}          # corner controls were evaluated in the search stage
    n_unknown = sum(1 for m in bank.members_for(fam.name) if exact_key(m) not in known)
    bp = bank.bank_pass(cell, fam, cache, incumbent_f=attack.best_f, known=known)
    if bp.improved:
        obj = Objective(cell, fam, cache); obj.archive.update(attack.archive)
        f = obj.eval_knobs(bp.best_knobs, source=f"bank:{bp.best_origin}")
        proj = fam.project(bp.best_knobs); pf = obj.eval_knobs(proj, source="projection")
        best, best_f, src = (proj, pf, "projection") if pf > f else (bp.best_knobs, f, f"bank:{bp.best_origin}")
        attack.best_knobs, attack.best_f, attack.best_source, attack.archive = best, best_f, src, obj.archive
        attack.projection_f, attack.replaced_by_projection = pf, pf > f
        attack.best_x = fam.inverse(best, settings_for(job["locked"], b).near_corner)
    out = base_record(job, cache, bank_stage_bound(n_unknown, b), exact=False)
    out.update({"bank_hash": bank_doc["bank_hash"], "transfer": Bank.transfer_rows(cell.name, float(rec["attack"]["best_f"]), bp),
                "ranked_top": bp.ranked[:10], "attack": search_to_json(attack), "projected_members": bank.projected_members_for(fam.name)})
    return out


def stage_reference(job: dict, rec: dict, bank_rec: dict | None) -> dict:
    check_record(job, rec)
    if bank_rec is not None:
        check_record(job, bank_rec)
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); twin = search_from_json(rec["twin"])
    members = bank_rec["projected_members"] if bank_rec else []
    cands = reference_candidates(cell, fam, attack, twin, members, tuple(job["locked"]["reference_order"]))
    ref = select_reference(cell, cands, cache)
    out = base_record(job, cache, reference_bound(len(members), b), exact=False)
    out.update({"candidate": candidate_to_json(ref.candidate), "scores": ref.scores, "attack_knobs": attack.best_knobs,
                "attack_f": attack.best_f, "attack_source": attack.best_source, "gain_train": attack.best_f - ref.scores[ref.candidate.name],
                "bank_hash": bank_rec["bank_hash"] if bank_rec else None,
                "attack_per_seed_normalized": [float(v) for v in attack.archive[exact_key(attack.best_knobs)].per_seed_normalized],
                "reference_per_seed_normalized": [float(v) for v in ref.per_seed_normalized],
                "reference_per_seed_profit": [float(v) for v in ref.per_seed_profit]})
    return out


def meta_of(job: dict, reference_name: str) -> dict:
    s = job["spec"]
    return {"cell": s["name"], "section": s["section"], "rule": s["rule"], "family": s["family"], "beta": s["beta"], "rho": s["rho"],
            "position": s["position"], "smoke": bool(job["smoke"]), "reference": reference_name, "budget": float(job["cfg"]["budget"])}


def stage_evaluate(job: dict, ref_rec: dict) -> dict:
    check_record(job, ref_rec)
    _, val, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, val, suffix="/val")
    cand = candidate_from_record(fam, ref_rec["candidate"])
    g = evaluate_gain(cell, fam, ref_rec["attack_knobs"], cand, cache)
    out = base_record(job, cache, stage_runs(job["spec"]["family"], "evaluate", b), exact=True)
    out["rows"] = seed_rows(cell, g, meta_of(job, ref_rec["candidate"]["name"]))
    return out


def stage_checks(job: dict, rec: dict, bank_rec: dict | None, ref_rec: dict) -> dict:
    check_record(job, rec); check_record(job, ref_rec)
    if bank_rec is not None:
        check_record(job, bank_rec)
    train, _, b = train_val(job)
    fam = family_of(job["spec"]["family"]); cache = SeedCache()
    cell = make_cell(job, train)
    attack = search_from_json(bank_rec["attack"] if bank_rec else rec["attack"]); twin = search_from_json(rec["twin"])   # bank-finalized base
    members = bank_rec["projected_members"] if bank_rec else []
    dc = doubling_check(cell, fam, cache, settings_for(job["locked"], b), seed=0, base_attack=attack, base_twin=twin,
                        bank_members=members, order=tuple(job["locked"]["reference_order"]))
    if abs(dc.gain_base - ref_rec["gain_train"]) > 1e-9 or dc.ref_base_name != ref_rec["candidate"]["name"]:
        raise AssertionError(f"{cell.name}: the doubling check's base does not reproduce the reference-stage record")
    out = base_record(job, cache, doubling_bound(len(members), b), exact=False)
    out.update({"doubling": dc.__dict__, "restart_spread": rec["restart_spread"], "twin_vs_honest": rec["twin_vs_honest"]})
    return out


def stage_all_deviators(job: dict) -> dict:
    _, val, b = train_val(job)
    lk = job["locked"]; ad = lk["all_deviators"]; cfg = cfg_from_dict(job["cfg"]); params = job["params"]; rule = job["spec"]["rule"]
    s = settings_from_locked(lk)
    settings = SearchSettings(popsize=s.popsize, sigma0=s.sigma0, restarts=int(ad["restarts"]), evals_per_restart=min(int(ad["evals"]), b.evals),
                              reeval_every=s.reeval_every, near_corner=s.near_corner, sobol_seed=s.sobol_seed)
    seeds = tuple(locked_seeds(lk, "dev_train")[: min(int(ad["seeds"]), b.n_train)])
    cache = SeedCache()
    att = iterated_best_response(cfg, lambda: make_rule(rule, params), D2, cache, settings, seeds, sweeps=int(ad["sweeps"]), eval_seeds=val)
    tw = iterated_best_response(cfg, lambda: make_rule(rule, params), D2, cache, settings, seeds, sweeps=int(ad["sweeps"]), force_clip=True, eval_seeds=val)
    out = base_record(job, cache, all_deviators_runs(lk, cfg.N, b), exact=True)
    out.update({"attack": att.__dict__, "twin": tw.__dict__,
                "gain_dev_val": [a - t for a, t in zip(att.final_normalized_profit, tw.final_normalized_profit)]})
    return out


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float) + "\n")


def read_dir(path: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text()) for p in sorted(path.glob("*.json"))} if path.exists() else {}


def run_stages(o: dict) -> dict:
    """o: stage, sections, rules, calibration, tuned_dir, smoke, workers, select, limit, out. Returns the totals of recorded runs per stage."""
    lk = load_locked(); cal = load_calibration(o["calibration"]); base = market_config_from_locked(lk)
    budget = SMOKE_BUDGET if o["smoke"] else budget_from_locked(lk)
    rules = o["rules"].split(","); sections = o["sections"].split(",")
    ns = o.get("eval_namespace", "dev_val")
    try:
        locked_seeds(lk, ns)                                            # before any record is read: final_eval exists only after the unseal
    except ValueError as e:
        raise SystemExit(f"evaluation namespace {ns} is not available: {e}")
    tuned = Path(o["tuned_dir"]) if o.get("tuned_dir") else None
    params = {r: load_params(r, tuned, o["smoke"], cal.market_key, settings_hash(lk), cal.seeds) for r in rules}
    if not o["smoke"] and list(cal.seeds) != locked_seeds(lk, "calibration"):
        raise SystemExit("calibration must use the full calibration namespace for a real run (pass --smoke for a smoke run)")
    out = Path(o["out"]); out.mkdir(parents=True, exist_ok=True)
    if o["smoke"]:
        (out / "SMOKE").write_text("smoke run: DEFAULT_PARAMS and SMOKE_BUDGET; not a result\n")
    manifest = enumerate_manifest(lk, rules, budget=budget)
    stages = STAGES if o["stage"] == "all" else (o["stage"],)
    counted: dict[str, int] = {}
    pool = ProcessPoolExecutor(max_workers=int(o.get("workers", 1)))

    def record(stage: str, rec: dict) -> None:
        counted[stage] = counted.get(stage, 0) + int(rec["runs"])
        write_json(out / stage / f"{rec['spec']['name']}.json", rec)

    for stage in stages:
        if stage == "search":
            jobs = []
            for sec in sections:
                specs = [c for c in manifest if c.section == sec and c.kind == "full_cell" and c.rule in rules
                         and (not o.get("select") or o["select"] in c.name)]
                specs = specs[: o.get("limit")]                          # manifest order, as in plan 2A
                if o.get("shard"):
                    k, n = (int(x) for x in o["shard"].split("/"))    # --shard K/N: cells sorted by name, cell i runs when i % N == K; shards share --out
                    specs = [c for i, c in enumerate(sorted(specs, key=lambda c: c.name)) if i % n == k]
                jobs += [job_for(c, lk, cal, base, params[c.rule], budget, o["smoke"], ns) for c in specs]
            for rec in pool.map(stage_search, jobs):
                record("search", rec)
        search = read_dir(out / "search")
        for name, rec in search.items():
            if rec["spec"]["rule"] not in rules:
                raise SystemExit(f"record {name} belongs to rule {rec['spec']['rule']}, which is not in --rules; pass it or use another output directory")
        jobs = {name: job_for(next(c for c in manifest if c.name == name), lk, cal, base, params[rec["spec"]["rule"]], budget, o["smoke"], ns)
                for name, rec in search.items()}
        if stage == "bank":
            doc = build_bank(out, search, jobs)
            write_json(out / "bank.json", doc)
            targets = [n for n, r in search.items() if r["spec"]["family"] in FAMILIES or r["spec"]["family"] == "D2+H3"]   # amendment 2: H3 cells take the bank through the embeddings
            for rec in pool.map(stage_bank, [jobs[n] for n in targets], [search[n] for n in targets], [doc] * len(targets)):
                record("bank", rec)
            trows = [json.loads((out / "bank" / f"{n}.json").read_text())["transfer"] for n in targets]
            with open(out / "transfer.csv", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["cell", "incumbent", "best_bank", "best_origin", "improved"]); w.writeheader(); w.writerows(trows)
        bank_recs = read_dir(out / "bank")
        bank_doc = None
        if stage in ("reference", "evaluate", "checks"):
            bank_doc = load_bank_doc(out) if (out / "bank.json").exists() else None
            for n, r in search.items():
                if (r["spec"]["family"] in FAMILIES or r["spec"]["family"] == "D2+H3") and n not in bank_recs:
                    raise SystemExit(f"{n}: no bank record; run the bank stage before {stage}")
                check_bank_record(bank_recs.get(n), bank_doc, stage)
        refs = read_dir(out / "reference")
        if stage in ("evaluate", "checks"):
            for n, r in refs.items():
                check_bank_record(r, bank_doc, stage)
        if stage == "reference":
            names = list(search)
            for rec in pool.map(stage_reference, [jobs[n] for n in names], [search[n] for n in names], [bank_recs.get(n) for n in names]):
                record("reference", rec)
            refs = read_dir(out / "reference")
        if stage == "evaluate":
            names = list(refs)
            by_section: dict[str, list] = {}
            for rec in pool.map(stage_evaluate, [jobs[n] for n in names], [refs[n] for n in names]):
                record("evaluate", rec)
                by_section.setdefault(rec["spec"]["section"], []).extend(rec["rows"])
            for sec, rws in by_section.items():
                with open(out / f"{sec}.csv", "w", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=META_FIELDS + ROW_FIELDS); w.writeheader(); w.writerows(rws)
            headline = {}
            for name, r in refs.items():
                s = r["spec"]
                if s["section"] in ("development", "heldout") and float(s["beta"]) == float(lk["beta_headline"]):
                    headline.setdefault(f"{s['rule']}/{s['family']}", {})[s["position"]] = float(r["gain_train"])
            write_json(out / "headline.json", {k: {"gain_train": v, "headline": headline_position(v)} for k, v in headline.items()})
        if stage == "checks":
            names = []
            for c in [c for c in manifest if c.section == "controls" and c.rule in rules]:
                src_section = "h3" if c.family == "D2+H3" else "development"           # amendment 2: a control is in scope when its source section is selected
                src_name = cell_name(src_section, c.rule, c.family, c.beta, c.rho, c.position)
                if src_section not in sections or (o.get("select") and o["select"] not in src_name):
                    continue
                n = next((n for n, r in search.items() if r["spec"]["section"] == src_section and r["spec"]["rule"] == c.rule
                          and r["spec"]["family"] == c.family and r["spec"]["position"] == c.position
                          and float(r["spec"]["beta"]) == c.beta and float(r["spec"]["rho"]) == c.rho), None)
                if n is None or n not in refs or ((c.family in FAMILIES or c.family == "D2+H3") and n not in bank_recs):
                    raise SystemExit(f"{c.name}: control in scope but its search record, bank record, or checked reference is missing; rerun the earlier stages")
                names.append(n)
            results = list(pool.map(stage_checks, [jobs[n] for n in names], [search[n] for n in names], [bank_recs.get(n) for n in names], [refs[n] for n in names]))
            for rec in results:
                counted["checks"] = counted.get("checks", 0) + int(rec["runs"])
                write_json(out / "checks" / f"{rec['spec']['name']}.json", rec)
            write_json(out / "checks.json", results)
        if stage == "all_deviators" and (o["stage"] == "all_deviators" or "all_deviators" in sections):
            specs = [c for c in manifest if c.section in ("all_deviators", "all_deviators_post_lock") and c.rule in rules]   # amendment 2: the proposed rule's post-lock entry
            adj = [job_for(c, lk, cal, base, params[c.rule], budget, o["smoke"]) for c in specs]
            results = list(pool.map(stage_all_deviators, adj))
            for rec in results:
                counted["all_deviators"] = counted.get("all_deviators", 0) + int(rec["runs"])
            write_json(out / "all_deviators.json", results)
    pool.shutdown()
    return counted


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES + ("all",))
    ap.add_argument("--sections", default="development,rho_sweep,no_ban,h3,all_deviators",
                    help="cell sections for the search stage (development, rho_sweep, no_ban, h3, all_deviators, heldout); the all_deviators stage runs under --stage all only when listed here")
    ap.add_argument("--rules", default="B1,B2,B3")
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None)
    ap.add_argument("--smoke", action="store_true", help="DEFAULT_PARAMS and the smoke budget; output marked SMOKE")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--select", default=None, help="only cells whose name contains this substring (search stage)")
    ap.add_argument("--limit", type=int, default=None, help="at most this many cells per section (search stage)")
    ap.add_argument("--shard", default=None, help="K/N (search stage): run the cells whose sorted index i has i %% N == K; shards share --out")
    ap.add_argument("--eval-namespace", dest="eval_namespace", default="dev_val", choices=["dev_val", "final_eval"])
    ap.add_argument("--out", required=True)
    counted = run_stages(vars(ap.parse_args()))
    print("done: " + ", ".join(f"{k} {v} runs" for k, v in counted.items()))


if __name__ == "__main__":
    main()
