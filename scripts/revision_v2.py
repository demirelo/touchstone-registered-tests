"""The protocol-v2 runner (design 5 to 9; plan docs/superpowers/plans/2026-10-22-revision-build.md Task 11). Stages, in
order: search (profit and W0 searches; X7-SC after the same rule's D2+H3 search, with its embedding as an incumbent),
reference (one menu per rule and context from its D2+H3 and X7-SC searches), dependent (W1 after the reference; the
coalition joint twin, joint reference, then the total and minimum searches), freeze (envelope choices and the fixed-attack
bank, then a complete freeze of the context), evaluate and cross (only after the freeze is accepted again), doubling
(continued searches, diagnostic only). Every record carries provenance and upstream hashes; outputs stay under --out.
Development markets (dev0, dev1) run the fresh0 template of the manifest."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sim import instances as INST  # noqa: E402
from sim import manifest_v2 as MAN  # noqa: E402
from sim.calibrate import cell_config, load_calibration  # noqa: E402
from sim.cell import Abstain, Cell, SeedCache, run_focal  # noqa: E402
from sim.h4_loader import Excluded, load as load_h4  # noqa: E402
from sim.locked import load_locked, market_config_from_locked  # noqa: E402
from sim.objectives_v2 import CoalitionObjective, WelfareObjective, gross_efficiency, joint_reference, select_w1, _member_rows  # noqa: E402
from sim.policies.families import D2, Family, exact_key  # noqa: E402
from sim.policies.honest import HonestMax  # noqa: E402
from sim.policies.identity import h3_family  # noqa: E402
from sim.policies.v2 import x5v2_family, x6v2_family, x6v2_member, x6v2_members  # noqa: E402
from sim.policies.x7 import corner_vectors, embed_h3, x7_family  # noqa: E402
from sim.positions import positions  # noqa: E402
from sim.records import cfg_to_dict, search_from_json, search_to_json  # noqa: E402
from sim.records_v2 import read, sha_file, validate, write  # noqa: E402
from sim.reference import Candidate, evaluate_gain, reference_candidates, select_reference, twin_search  # noqa: E402
from sim.rng import SALT_ENV, load_identity_salt  # noqa: E402
from sim.rules_v2 import CORE, MATCHED, make_rule, public_constants, registered_b2_params  # noqa: E402
from sim.search import Objective, SearchSettings, cma_search, settings_from_locked  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("search", "reference", "dependent", "freeze", "evaluate", "cross", "doubling")
CATEGORIES = ("abstain", "honest_max", "twin_search", "attack_projection", "archive_clip1", "archive_truthful_clip0", "bank")
MENU = ("D2+H3", "X7-SC")
SMOKE = (1, 16, 1, 2)
DEV_ROOT = INST.DEV_ROOT
THRESHOLD = 0.005


# ---- context ---------------------------------------------------------------------------------------------------------

def git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha_json(obj) -> str:
    return _sha(json.dumps(obj, sort_keys=True, default=float).encode())


def install_salt(root: str, out: Path) -> Path:
    """Write the fresh root's identity salt under --out and point the harness at it before any episode."""
    p = Path(out) / "salt.hex"; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(INST.identity_salt_hex(root))
    os.environ[SALT_ENV] = str(p)
    return p


@lru_cache(maxsize=4)
def _fresh(root: str) -> tuple:
    return tuple(m["cfg"] for m in INST.markets(root, 6))


@lru_cache(maxsize=32)
def _market_cfg(label: str, root: str, rho: float):
    if label == "headline":
        return cell_config(market_config_from_locked(load_locked()), load_calibration(ROOT / "experiments/calibration.json"), rho=rho, beta=0.05)
    if label.startswith("dev"):
        base = INST.dev_markets()[int(label[3:])]["cfg"]
    elif label.startswith("fresh"):
        base = _fresh(root)[int(label[5:])]
    else:
        raise ValueError(f"unknown market {label!r}")
    return INST.calibrated(base, rho=rho)


def market(label: str, root: str, rho: float = 0.2, dev: bool = False, smoke: bool = False) -> dict:
    cfg = _market_cfg(label, root, float(rho))
    train, val = list(range(1000, 1005)), list(range(2000, 2020))
    ev = val if dev else INST.eval_seeds(root, label)
    if smoke:
        train, ev = train[: SMOKE[2]], ev[: SMOKE[3]]
    return {"label": label, "root": root, "rho": float(rho), "dev": bool(dev), "smoke": bool(smoke), "cfg": cfg, "focal": int(positions(cfg)["median"]),
            "seeds_train": train, "seeds_val": val, "seeds_eval": list(ev), "context": MAN.context(label, float(rho))}


def manifest_ctx(ctx: str) -> str:
    """Development contexts run the fresh0 template of the manifest."""
    label, rest = ctx.split("@", 1)
    return f"fresh0@{rest}" if label.startswith("dev") else ctx


def rule_spec(rule: str, params: dict | None) -> dict:
    p = params or {}
    if rule in MATCHED:
        spec = {"tol": 0.16, "L": 10}
    elif rule == "B2":
        b2 = registered_b2_params(); spec = {"tol": float(b2["tol"]), "L": int(b2["L"]), "b2": b2}
    else:
        t = (p.get("tuned") or {}).get(rule)
        if t is None:
            raise SystemExit(f"{rule}: no tuned parameters in --params")
        spec = {"tol": float(t["tol"]), "L": int(t["L"])}
    if rule.startswith("C*"):
        if not p.get("cred"):
            raise SystemExit(f"{rule}: no comparator (cred) in --params")
        spec["cred"] = dict(p["cred"])
    return spec


def rule_factory(job: dict):
    s = job["spec"]
    return lambda: make_rule(job["rule"], s["tol"], s["L"], cred=s.get("cred"), b2_params=s.get("b2"))


def constants(job: dict) -> tuple[int, int]:
    rule = rule_factory(job)()
    pc = public_constants(rule, job["mkt"]["cfg"])
    return pc["T"], pc["L"]


@lru_cache(maxsize=8)
def _h4(path: str, sha: str):
    return load_h4(Path(path), sha)


def family_for(name: str, T: int, L: int, h4: dict | None = None) -> Family:
    if name == "D2":
        return D2
    if name == "D2+H3":
        return h3_family(D2)
    if name == "X7-SC":
        return x7_family(T, L)
    if name == "X5-AG/v2":
        return x5v2_family(T, L)
    if name == "X6-SE/v2":
        return x6v2_family(T, L)
    if name == "H4":
        src = _h4(h4["dir"], h4["sha"]) if h4 else Excluded("no bundle")
        if isinstance(src, Excluded):
            raise SystemExit(f"H4 excluded: {src.reason}")
        return src.family(T, L)
    raise ValueError(f"unknown family {name!r}")


def cell_id(ctx: str, rule: str, family: str, objective: str, c=None, schedule=None) -> str:
    return f"{ctx}|{rule}|{family}|{objective}" + (f"|c{c}_{schedule}" if c is not None else "")


def job(mkt: dict, rule: str, family: str, objective: str = "profit", c: int | None = None, schedule: str | None = None,
        smoke: bool = False, params: dict | None = None, h4: dict | None = None) -> dict:
    lk = load_locked(); s = lk["search"]
    R, E, n_train, n_eval = SMOKE if (smoke or mkt["smoke"]) else (int(s["restarts"]), int(s["evals_per_restart"]), len(mkt["seeds_train"]), len(mkt["seeds_eval"]))
    if family == "X7-SC":
        E *= 2
    spec = rule_spec(rule, params)
    salt = _sha(load_identity_salt())
    j = {"id": cell_id(mkt["context"], rule, family, objective, c, schedule), "context": mkt["context"], "rule": rule, "family": family,
         "objective": objective, "c": c, "schedule": schedule, "budget": [R, E, n_train, n_eval], "spec": spec, "mkt": mkt,
         "h4": h4 if family == "H4" else None}
    j["provenance"] = context_provenance(mkt) | {"budget": j["budget"], "rule_params_sha256": _sha_json(spec), "id": j["id"]}
    j["provenance"]["salt_sha256"] = salt
    return j


def context_provenance(mkt: dict) -> dict:
    return {"git_commit": git_commit(), "runner_sha256": _sha(Path(__file__).read_bytes()), "cfg_sha256": _sha_json(cfg_to_dict(mkt["cfg"])),
            "salt_sha256": _sha(load_identity_salt()), "root": mkt["root"], "seeds_train": mkt["seeds_train"], "seeds_val": mkt["seeds_val"],
            "seeds_eval": mkt["seeds_eval"], "context": mkt["context"]}


def settings(job: dict) -> SearchSettings:
    R, E, _, _ = job["budget"]
    return replace(settings_from_locked(load_locked()), restarts=int(R), evals_per_restart=int(E))


def train_cell(job: dict, others: tuple = ()) -> Cell:
    m = job["mkt"]
    return Cell(cfg=m["cfg"], rule_factory=rule_factory(job), focal=m["focal"], seeds=tuple(m["seeds_train"]), name=job["id"], others=others)


def eval_cell(job: dict) -> Cell:
    return replace(train_cell(job), seeds=tuple(job["mkt"]["seeds_eval"]))


# ---- record paths ------------------------------------------------------------------------------------------------------

def _safe(s: str) -> str:
    return s.replace("|", "__").replace("/", "~").replace("*", "star")


def path_of(out: Path, rid: str) -> Path:
    if "|" in rid:
        objective = rid.split("|")[3]
        return Path(out) / ("dependent" if objective in ("W1", "total", "min") else "search") / (_safe(rid) + ".json")
    kind, ctx, rest = rid.split("/", 2)
    return Path(out) / kind / ctx / (_safe(rest) + ".json")


def eval_path(out: Path, rid: str) -> Path:
    return Path(out) / "evaluate" / (_safe(rid) + ".json")


# ---- search adapters ---------------------------------------------------------------------------------------------------

def search_family(cell: Cell, family: Family, cache: SeedCache, st: SearchSettings, twin, extra_incumbents: dict | None = None):
    inc = {"twin_best": twin.best_knobs, "honest_point": family.honest_point(), **(extra_incumbents or {})}
    return cma_search(Objective(cell, family, cache), family, st, 1, incumbents=inc)


def controls(objective, family: Family) -> list:
    vecs = corner_vectors(family) if family.name == "X7-SC" else family.corners()
    return [(k, float(objective.eval_knobs(k, source="corner"))) for k in vecs]


def continue_search(objective, family: Family, st: SearchSettings, original, seed: int = 1):
    """Doubling (design 6.5): as many new restarts as registered, with restart seeds after the registered ones, on the
    merged archive (old entries kept), the previous best as an incumbent."""
    objective.archive.update(original.archive)
    return cma_search(objective, family, st, int(seed) + int(st.restarts), incumbents={"previous_best": dict(original.best_knobs)})


# ---- stages ------------------------------------------------------------------------------------------------------------

def _menu_id(ctx, rule, fam):
    return cell_id(ctx, rule, fam, "profit")


def stage_search(job: dict, out: Path) -> dict:
    T, L = constants(job); fam = family_for(job["family"], T, L, job.get("h4")); cache = SeedCache(); st = settings(job); cell = train_cell(job)
    upstream = {}
    if job["objective"] == "W0":
        obj = WelfareObjective(cell, fam, cache)
        res = cma_search(obj, fam, st, 1, incumbents={"honest_point": fam.honest_point()})
        return {"welfare": search_to_json(res), "selected": dict(res.best_knobs),
                "extras": [{"knobs": obj.archive[k].knobs, **v} for k, v in obj.extra.items()], "upstream": upstream, "T": T, "L": L}
    tw = twin_search(cell, fam, cache, st, seed=0)
    extra = {}
    if job["family"] == "X7-SC":
        rid = _menu_id(job["context"], job["rule"], "D2+H3"); rec = read(path_of(out, rid))
        if rec is None:
            raise SystemExit(f"{job['id']}: needs {rid} first")
        extra["embedded_h3"] = embed_h3(rec["attack"]["best_knobs"], T); upstream[rid] = sha_file(path_of(out, rid))
    at = search_family(cell, fam, cache, st, tw, extra)
    obj = Objective(cell, fam, cache); obj.archive.update(at.archive)
    ctrl = controls(obj, fam)
    best_ctrl = max(ctrl, key=lambda kf: kf[1]) if ctrl else None
    at.archive.update(obj.archive)
    rec = {"twin": search_to_json(tw), "attack": search_to_json(at), "controls": [{"knobs": k, "f": f} for k, f in ctrl],
           "upstream": upstream, "T": T, "L": L, "runs": cache.runs}
    if best_ctrl is not None and best_ctrl[1] > at.best_f:
        rec["attack"]["best_knobs"], rec["attack"]["best_f"], rec["attack"]["best_source"] = dict(best_ctrl[0]), float(best_ctrl[1]), "control"
    return rec


def cand_to_json(c: Candidate, family: str | None, T: int, L: int) -> dict:
    return {"name": c.name, "family": family, "T": T, "L": L, "knobs": c.knobs}


def cand_from_json(d: dict, h4: dict | None = None) -> Candidate:
    if d["knobs"] is None:
        return Candidate(d["name"], Abstain if d["name"] == "abstain" else HonestMax, None)
    fam = family_for(d["family"], int(d["T"]), int(d["L"]), h4); k = dict(d["knobs"])
    return Candidate(d["name"], lambda: fam.make(k), k)


def menu(job: dict, out: Path, cuts: int = 0, h4_excluded: bool = False) -> tuple[list, list, dict]:
    """The reference menu of the job's rule in its context (design 6.4): candidates, their family names, upstream hashes."""
    ctx, rule = job["context"], job["rule"]; T, L = constants(job); cell = train_cell(job)
    groups: dict[tuple, list] = {}; upstream = {}
    for fname in MENU:
        rid = _menu_id(ctx, rule, fname); rec = read(path_of(out, rid))
        if rec is None:
            raise SystemExit(f"reference {ctx}/{rule}: needs {rid}")
        upstream[rid] = sha_file(path_of(out, rid))
        fam = family_for(fname, T, L)
        bank = []
        if rule in MATCHED:
            for other in MAN.bank_rules(manifest_ctx(ctx), fname, cuts, h4_excluded):
                if other == rule:
                    continue
                orid = _menu_id(ctx, other, fname); orec = read(path_of(out, orid))
                if orec is None:
                    raise SystemExit(f"reference {ctx}/{rule}: needs bank source {orid}")
                upstream[orid] = sha_file(path_of(out, orid)); bank.append(fam.project(orec["attack"]["best_knobs"]))
        lk = load_locked()
        cands = reference_candidates(cell, fam, search_from_json(rec["attack"]), search_from_json(rec["twin"]), bank, tuple(lk["reference_order"]))
        for c in cands:
            cat = "bank" if c.name.startswith("bank_") else c.name
            groups.setdefault((cat, fname), []).append(c)
    out_c, fams = merge_menu(groups, MENU)
    return out_c, fams, upstream


def merge_menu(groups: dict, family_order) -> tuple[list, list]:
    """Candidates in the registered category order, families in the given order within a category, de-duplicated by
    (family, exact key); abstain and honest-max once."""
    out_c, fams, seen = [], [], set()
    for cat in CATEGORIES:
        for fname in family_order:
            for c in groups.get((cat, fname), []):
                key = ("name", c.name) if c.knobs is None else (fname, exact_key(c.knobs))
                if key in seen:
                    continue
                seen.add(key); out_c.append(c); fams.append(None if c.knobs is None else fname)
    return out_c, fams


def stage_reference(job: dict, out: Path, cuts: int = 0, h4_excluded: bool = False) -> dict:
    T, L = constants(job); cands, fams, upstream = menu(job, out, cuts, h4_excluded)
    choice = select_reference(train_cell(job), cands, SeedCache())
    idx = next(i for i, c in enumerate(cands) if c is choice.candidate)
    return {"candidates": [cand_to_json(c, f, T, L) for c, f in zip(cands, fams)], "choice": idx, "scores": choice.scores,
            "per_seed_normalized": [float(v) for v in choice.per_seed_normalized], "upstream": upstream, "T": T, "L": L}


def reference_of(job: dict, out: Path) -> tuple[Candidate, dict, Path]:
    p = path_of(out, f"reference/{job['context']}/{job['rule']}"); rec = read(p)
    if rec is None:
        raise SystemExit(f"{job['id']}: needs the rule's reference")
    return cand_from_json(rec["candidates"][rec["choice"]]), rec, p


def _coalition_tag(job):
    return f"{job['rule']}_c{job['c']}_{job['schedule']}"


def stage_dependent(job: dict, out: Path) -> dict:
    T, L = constants(job); cache = SeedCache(); st = settings(job); m = job["mkt"]
    if job["objective"] == "W1":
        cand, rrec, rp = reference_of(job, out); fam = family_for(job["family"], T, L)
        obj = WelfareObjective(train_cell(job), fam, cache, ref_normalized=np.asarray(rrec["per_seed_normalized"]))
        res = cma_search(obj, fam, st, 1, incumbents={"honest_point": fam.honest_point()})
        return {"welfare": search_to_json(res), "selected": select_w1(obj), "extras": [{"knobs": obj.archive[k].knobs, **v} for k, v in obj.extra.items()],
                "upstream": {f"reference/{job['context']}/{job['rule']}": sha_file(rp)}, "T": T, "L": L}
    fam = x6v2_family(T, L); members = x6v2_members(m["cfg"], m["focal"], int(job["c"])); stag = job["schedule"] == "staggered"
    tag = _coalition_tag(job); tid, rid = f"joint_twin/{job['context']}/{tag}", f"joint_reference/{job['context']}/{tag}"
    if read(path_of(out, tid)) is None:
        tobj = CoalitionObjective(m["cfg"], rule_factory(job), members, fam, m["seeds_train"], cache, "joint_twin", staggered=stag, T=T, L=L)
        tw = cma_search(tobj, fam, st, 0, starts=fam.registered_starts({"near_corner": st.near_corner, "sobol_seed": st.sobol_seed}, twin=True))
        write(path_of(out, tid), {"stage": "joint_twin", "provenance": job["provenance"], "twin": search_to_json(tw), "upstream": {}})
    trec = read(path_of(out, tid))
    if read(path_of(out, rid)) is None:
        jr = joint_reference(m["cfg"], rule_factory(job), members, m["seeds_train"], cache, trec["twin"]["best_knobs"], stag, T, L)
        write(path_of(out, rid), {"stage": "joint_reference", "provenance": job["provenance"], "name": jr["name"], "scores": jr["scores"],
                                  "member_normalized": jr["member_normalized"].tolist(), "twin_knobs": jr["twin_knobs"],
                                  "upstream": {tid: sha_file(path_of(out, tid))}})
    jrec = read(path_of(out, rid))
    obj = CoalitionObjective(m["cfg"], rule_factory(job), members, fam, m["seeds_train"], cache, job["objective"],
                             joint_ref=np.asarray(jrec["member_normalized"]), staggered=stag, T=T, L=L)
    res = cma_search(obj, fam, st, 1, incumbents={"joint_twin": jrec["twin_knobs"], "honest_point": fam.honest_point()})
    best = obj.extra[exact_key(res.best_knobs)] if exact_key(res.best_knobs) in obj.extra else None
    return {"coalition": search_to_json(res), "selected": dict(res.best_knobs), "selected_extra": best, "members": list(members),
            "upstream": {rid: sha_file(path_of(out, rid))}, "T": T, "L": L}


# ---- freeze ------------------------------------------------------------------------------------------------------------

def derived_records(ctx: str, jobs: list[dict], out: Path, cuts: int, h4_excluded: bool) -> None:
    """Envelope family choices (design 9.3 Q3, on training gains) and the fixed-attack bank (design 6.6)."""
    by_id = {j["id"]: j for j in jobs}
    req = [r.replace(manifest_ctx(ctx), ctx, 1) for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded)]
    prov = None
    for r in req:
        kind = r.split("/", 1)[0]
        if kind == "envelope":
            rule = r.split("/", 2)[2]; _, rrec, rp = reference_of({"context": ctx, "rule": rule, "id": r}, out)
            ref_score = float(np.mean(rrec["per_seed_normalized"])); gains = {}; up = {f"reference/{ctx}/{rule}": sha_file(rp)}
            for fname in MAN.doc()["envelope_families"]:
                rid = cell_id(ctx, rule, fname, "profit")
                if rid in by_id and read(path_of(out, rid)) is not None:
                    gains[fname] = float(read(path_of(out, rid))["attack"]["best_f"]) - ref_score; up[rid] = sha_file(path_of(out, rid))
                    prov = prov or by_id[rid]["provenance"]
            write(path_of(out, r), {"stage": "envelope", "provenance": context_provenance(next(iter(by_id.values()))["mkt"]),
                                   "choice": max(gains, key=gains.get) if gains else None, "training_gains": gains, "upstream": up})
        elif kind == "bank":
            fname = r.split("/", 2)[2]; attacks, up = {}, {}
            for rule in MAN.FACTORIAL:
                rid = cell_id(ctx, rule, fname, "profit"); rec = read(path_of(out, rid))
                if rec is not None:
                    attacks[rule] = rec["attack"]["best_knobs"]; up[rid] = sha_file(path_of(out, rid))
            write(path_of(out, r), {"stage": "bank", "provenance": context_provenance(next(iter(by_id.values()))["mkt"]), "attacks": attacks,
                                   "upstream": up})


def _upstream_paths(rec: dict, out: Path) -> dict:
    return {rid: path_of(out, rid) for rid in (rec.get("upstream") or {})}


def check_complete(ctx: str, jobs: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    by_id = {j["id"]: j for j in jobs}; problems = []
    any_job = next((j for j in jobs if j["context"] == ctx), None)
    cprov = context_provenance(any_job["mkt"]) if any_job else None
    for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded):
        r = r.replace(manifest_ctx(ctx), ctx, 1)
        rec = read(path_of(out, r))
        if rec is None:
            problems.append(f"missing {r}"); continue
        try:
            if "|" in r:
                j = by_id.get(r)
                if j is None:
                    problems.append(f"no job for {r}"); continue
                validate(j, "dependent" if j["objective"] in ("W1", "total", "min") else "search", rec, _upstream_paths(rec, out))
            else:
                kind = r.split("/", 1)[0]
                ok_prov = rec.get("provenance", {}).get("git_commit") == cprov["git_commit"] and rec.get("provenance", {}).get("salt_sha256") == cprov["salt_sha256"]
                if rec.get("stage") != kind or not ok_prov:
                    raise ValueError(f"{r}: stage or provenance")
                validate({"provenance": rec.get("provenance")}, kind, rec, _upstream_paths(rec, out))
        except ValueError as e:
            problems.append(f"{r}: {e}")
    return problems


def stage_freeze(ctx: str, jobs: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> dict:
    derived_records(ctx, jobs, out, cuts, h4_excluded)
    problems = check_complete(ctx, jobs, out, cuts, h4_excluded)
    if problems:
        raise SystemExit(f"freeze {ctx} refused: {problems[:5]}{' ...' if len(problems) > 5 else ''}")
    recs = {r.replace(manifest_ctx(ctx), ctx, 1): None for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded)}
    rec = {"stage": "freeze", "context": ctx, "cuts": cuts, "h4_excluded": h4_excluded, "records": {r: sha_file(path_of(out, r)) for r in recs}}
    write(Path(out) / "freeze" / f"{ctx}.json", rec)
    return rec


def accept(ctx: str, jobs: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> dict:
    fr = read(Path(out) / "freeze" / f"{ctx}.json")
    if fr is None:
        raise SystemExit(f"{ctx}: no freeze; evaluation refused")
    for r, sha in fr["records"].items():
        p = path_of(out, r)
        if not p.exists() or sha_file(p) != sha:
            raise SystemExit(f"{ctx}: {r} differs from the freeze; evaluation refused")
    problems = check_complete(ctx, jobs, out, cuts, h4_excluded)
    missing = [r.replace(manifest_ctx(ctx), ctx, 1) for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded)
               if r.replace(manifest_ctx(ctx), ctx, 1) not in fr["records"]]
    if problems or missing:
        raise SystemExit(f"{ctx}: freeze incomplete or stale; evaluation refused: {(problems + missing)[:5]}")
    return fr


# ---- evaluation --------------------------------------------------------------------------------------------------------

GAIN_FIELDS = ("gain", "eff_attack", "eff_ref", "net_eff_attack", "net_eff_ref", "profit_attack", "profit_ref", "audit_spend_attack", "sstar")


def stage_evaluate(job: dict, out: Path) -> dict:
    T, L = constants(job); cache = SeedCache(); m = job["mkt"]; cell = eval_cell(job)
    rec = read(path_of(out, job["id"]))
    if job["objective"] == "profit":
        fam = family_for(job["family"], T, L, job.get("h4")); cand, _, _ = reference_of(job, out)
        g = evaluate_gain(cell, fam, rec["attack"]["best_knobs"], cand, cache)
        return {"seeds": list(cell.seeds), **{k: [float(v) for v in getattr(g, k)] for k in GAIN_FIELDS}}
    if job["objective"] in ("W0", "W1"):
        if rec["selected"] is None:
            return {"seeds": list(cell.seeds), "no_feasible_candidate": True}
        fam = family_for(job["family"], T, L); fr = run_focal(cell, lambda: fam.make(dict(rec["selected"])), cache)
        out_ = {"seeds": list(cell.seeds), "eff": gross_efficiency(fr.results).tolist(), "normalized": fr.normalized.tolist()}
        if job["objective"] == "W1":
            cand, _, _ = reference_of(job, out); ref = run_focal(cell, cand.policy_factory, cache)
            out_["constraint"] = (fr.normalized - ref.normalized).tolist()
        return out_
    fam = x6v2_family(T, L); members = rec["members"]; c = len(members); stag = job["schedule"] == "staggered"; k = rec["selected"]
    jrec = read(path_of(out, f"joint_reference/{job['context']}/{_coalition_tag(job)}"))
    rows = _member_rows(m["cfg"], rule_factory(job), members, cell.seeds, cache, [lambda j=j: x6v2_member(k, j, c, stag, T, L) for j in range(c)])
    ref_f = {"honest_max": [HonestMax] * c, "abstain": [Abstain] * c,
             "joint_twin": [lambda j=j: x6v2_member(jrec["twin_knobs"], j, c, stag, T, L) for j in range(c)]}[jrec["name"]]
    ref_rows = _member_rows(m["cfg"], rule_factory(job), members, cell.seeds, cache, ref_f)
    g = rows - ref_rows
    return {"seeds": list(cell.seeds), "member_gain": g.tolist(), "total": float(g.mean(axis=1).sum()), "min": float(g.mean(axis=1).min())}


def stage_cross(ctx: str, family: str, jobs: list[dict], out: Path) -> dict:
    bank = read(path_of(out, f"bank/{ctx}/{family}"))
    by_rule = {j["rule"]: j for j in jobs if j["context"] == ctx and j["family"] == family and j["objective"] == "profit" and j["rule"] in MAN.FACTORIAL}
    rules = [r for r in MAN.FACTORIAL if r in by_rule]; cache = SeedCache(); mat, rows = [], {}
    for a in rules:
        row = []
        for r in rules:
            j = by_rule[r]; T, L = constants(j); fam = family_for(family, T, L); cell = eval_cell(j)
            cand, _, _ = reference_of(j, out)
            att = run_focal(cell, lambda: fam.make(dict(bank["attacks"][a])), cache); ref = run_focal(cell, cand.policy_factory, cache)
            gain = (att.profit - ref.profit) / (np.array([x.sstar for x in att.results]) / cell.cfg.N)
            rows[f"{a}>{r}"] = gain.tolist(); row.append(float(gain.mean()))
        mat.append(row)
    return {"stage": "cross", "context": ctx, "family": family, "attacks": rules, "rules": rules, "matrix": mat, "per_seed": rows}


# ---- doubling ----------------------------------------------------------------------------------------------------------

def doubling_report(kind: str, old: dict, new: dict) -> dict:
    """Changes in the objective's units (design 6.5): profit (attack and reference normalised profit), welfare (gross
    efficiency, lower is a better attack), w1 (efficiency and feasibility), coalition (objective)."""
    rep = {"kind": kind}
    if kind == "profit":
        rep["attack_change"] = float(new["attack_f"] - old["attack_f"]); rep["reference_change"] = float(new["ref_f"] - old["ref_f"])
        changes = [rep["attack_change"], rep["reference_change"]]
    elif kind in ("welfare", "w1"):
        rep["efficiency_change"] = float(old["eff"] - new["eff"]) if old.get("eff") is not None and new.get("eff") is not None else 0.0
        changes = [rep["efficiency_change"]]
        if kind == "w1":
            rep["feasibility_transition"] = bool(old.get("feasible") is False and new.get("feasible") is True)
    elif kind == "coalition":
        rep["objective_change"] = float(new["f"] - old["f"]); changes = [rep["objective_change"]]
    else:
        raise ValueError(kind)
    rep["incomplete"] = bool(any(c >= THRESHOLD - 1e-12 for c in changes) or rep.get("feasibility_transition", False))
    return rep


def stage_doubling(job: dict, out: Path, cuts: int = 0, h4_excluded: bool = False) -> dict:
    T, L = constants(job); cache = SeedCache(); st = settings(job); cell = train_cell(job); rec = read(path_of(out, job["id"]))
    if job["objective"] == "profit":
        fam = family_for(job["family"], T, L); orig = search_from_json(rec["attack"])
        new = continue_search(Objective(cell, fam, cache), fam, st, orig)
        _, rrec, _ = reference_of(job, out)
        cands, fams, _ = menu(job, out, cuts, h4_excluded)
        lk = load_locked(); extra = reference_candidates(cell, fam, new, search_from_json(rec["twin"]), [], tuple(lk["reference_order"]))
        newref = select_reference(cell, cands + [c for c in extra if c.knobs is not None], cache)
        return doubling_report("profit", {"attack_f": orig.best_f, "ref_f": float(np.mean(rrec["per_seed_normalized"]))},
                               {"attack_f": max(new.best_f, orig.best_f), "ref_f": float(np.mean(newref.per_seed_normalized))})
    if job["objective"] in ("W0", "W1"):
        fam = family_for(job["family"], T, L); orig = search_from_json(rec["welfare"])
        ref = np.asarray(reference_of(job, out)[1]["per_seed_normalized"]) if job["objective"] == "W1" else None
        obj = WelfareObjective(cell, fam, cache, ref_normalized=ref); continue_search(obj, fam, st, orig)
        old_eff = min(e["eff"] for e in rec["extras"] if job["objective"] == "W0" or (e["constraint"] is not None and e["constraint"] >= 0)) if rec["selected"] else None
        sel = select_w1(obj) if job["objective"] == "W1" else dict(max(obj.archive.values(), key=lambda e: e.f).knobs)
        new_eff = obj.extra[exact_key(sel)]["eff"] if sel is not None and exact_key(sel) in obj.extra else None
        return doubling_report("w1" if job["objective"] == "W1" else "welfare", {"eff": old_eff, "feasible": rec["selected"] is not None},
                               {"eff": new_eff, "feasible": sel is not None})
    m = job["mkt"]; fam = x6v2_family(T, L); orig = search_from_json(rec["coalition"])
    jrec = read(path_of(out, f"joint_reference/{job['context']}/{_coalition_tag(job)}"))
    obj = CoalitionObjective(m["cfg"], rule_factory(job), rec["members"], fam, m["seeds_train"], cache, job["objective"],
                             joint_ref=np.asarray(jrec["member_normalized"]), staggered=job["schedule"] == "staggered", T=T, L=L)
    new = continue_search(obj, fam, st, orig)
    return doubling_report("coalition", {"f": orig.best_f}, {"f": max(new.best_f, orig.best_f)})


# ---- orchestration -----------------------------------------------------------------------------------------------------

def _stage_record_path(stage: str, job: dict, out: Path) -> Path:
    if stage in ("search", "dependent"):
        return path_of(out, job["id"])
    if stage == "evaluate":
        return eval_path(out, job["id"])
    return Path(out) / "doubling" / (_safe(job["id"]) + ".json")


def _run_one(stage: str, job: dict, out: str, cuts: int, h4_excluded: bool) -> str:
    out = Path(out); p = _stage_record_path(stage, job, out); rec = read(p)
    if rec is not None:
        if rec.get("provenance") != job["provenance"]:
            raise SystemExit(f"{p}: a record with another provenance exists; refusing to overwrite")
        return "skipped"
    body = {"search": stage_search, "dependent": stage_dependent, "evaluate": stage_evaluate}.get(stage)
    rec = body(job, out) if body else stage_doubling(job, out, cuts, h4_excluded)
    upstream = rec.pop("upstream", {})
    write(p, {"stage": stage, "id": job["id"], "provenance": job["provenance"], "upstream": upstream, **rec})
    return "done"


def _pool(stage, jobs, out, workers, cuts, h4_excluded) -> list:
    if workers <= 1 or len(jobs) <= 1:
        return [_run_one(stage, j, str(out), cuts, h4_excluded) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_run_one, [stage] * len(jobs), jobs, [str(out)] * len(jobs), [cuts] * len(jobs), [h4_excluded] * len(jobs)))


def run(stage: str, jobs: list[dict], out: Path, workers: int = 1, cuts: int = 0, h4_excluded: bool = False) -> dict:
    out = Path(out); res = {}
    if stage == "search":
        first = [j for j in jobs if j["objective"] in ("profit", "W0") and j["family"] != "X7-SC"]
        second = [j for j in jobs if j["objective"] in ("profit", "W0") and j["family"] == "X7-SC"]
        for wave in (first, second):
            for j, r in zip(wave, _pool(stage, wave, out, workers, cuts, h4_excluded)):
                res[j["id"]] = r
    elif stage == "reference":
        seen = set()
        for j in jobs:
            key = (j["context"], j["rule"])
            if j["objective"] == "profit" and j["family"] in MENU and key not in seen:
                seen.add(key); p = path_of(out, f"reference/{key[0]}/{key[1]}")
                if read(p) is None:
                    rec = stage_reference(j, out, cuts, h4_excluded); up = rec.pop("upstream")
                    write(p, {"stage": "reference", "provenance": context_provenance(j["mkt"]), "upstream": up, **rec})
                res[f"reference/{key[0]}/{key[1]}"] = "done"
    elif stage == "dependent":
        dep = [j for j in jobs if j["objective"] in ("W1", "total", "min")]
        for j, r in zip(dep, _pool(stage, dep, out, workers, cuts, h4_excluded)):
            res[j["id"]] = r
    elif stage == "freeze":
        for ctx in sorted({j["context"] for j in jobs}):
            stage_freeze(ctx, jobs, out, cuts, h4_excluded); res[ctx] = "frozen"
    elif stage == "evaluate":
        for ctx in sorted({j["context"] for j in jobs}):
            accept(ctx, jobs, out, cuts, h4_excluded)
        for j, r in zip(jobs, _pool(stage, jobs, out, workers, cuts, h4_excluded)):
            res[j["id"]] = r
    elif stage == "cross":
        for ctx, fam in MAN.cross_evaluations() + [(c, f) for c in sorted({j["context"] for j in jobs}) if c.startswith("dev") for f in MENU]:
            if not any(j["context"] == ctx for j in jobs):
                continue
            accept(ctx, jobs, out, cuts, h4_excluded)
            p = Path(out) / "cross" / ctx / (_safe(fam) + ".json")
            if read(p) is None:
                write(p, stage_cross(ctx, fam, jobs, out))
            res[f"cross/{ctx}/{fam}"] = "done"
    elif stage == "doubling":
        dbl = set(MAN.doublings())
        sel = [j for j in jobs if j["id"].replace(j["context"], manifest_ctx(j["context"]), 1) in dbl]
        for j, r in zip(sel, _pool(stage, sel, out, workers, cuts, h4_excluded)):
            res[j["id"]] = r
    else:
        raise SystemExit(f"unknown stage {stage!r}")
    return res


def build_jobs(markets: list[str], root: str, dev: bool, smoke: bool, params: dict | None, cuts: int, h4: dict | None, h4_excluded: bool) -> list[dict]:
    jobs = []
    for label in markets:
        for rho in sorted({c["rho"] for c in MAN.effective(cuts, h4_excluded)}):
            mctx = MAN.context("fresh0" if label.startswith("dev") else label, rho)
            cs = [c for c in MAN.effective(cuts, h4_excluded) if c["context"] == mctx]
            if not cs:
                continue
            mkt = market(label, root, rho, dev=dev, smoke=smoke)
            for c in cs:
                jobs.append(job(mkt, c["rule"], c["family"], c["objective"], c["c"], c["schedule"], smoke, params, h4))
    return jobs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=STAGES); ap.add_argument("--select", default="*"); ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--dev", action="store_true"); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--root", default=None); ap.add_argument("--h4", default=None); ap.add_argument("--h4-sha", dest="h4_sha", default=None)
    ap.add_argument("--params", default=None); ap.add_argument("--cuts", type=int, default=0); ap.add_argument("--markets", default=None)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if a.dev:
        root = DEV_ROOT; markets = (a.markets or "dev0,dev1").split(",")
    else:
        if not a.root:
            raise SystemExit("a fresh run needs --root (the block hash); use --dev for development markets")
        root = a.root; install_salt(root, out); markets = (a.markets or ",".join(MAN.doc()["markets"])).split(",")
    params = json.loads(Path(a.params).read_text()) if a.params else None
    h4 = {"dir": a.h4, "sha": a.h4_sha} if a.h4 else None
    h4_excluded = h4 is None or isinstance(_h4(a.h4, a.h4_sha), Excluded)
    if h4 is not None and h4_excluded:
        write(out / "h4_excluded.json", {"reason": _h4(a.h4, a.h4_sha).reason})
    patterns = a.select.split(",")
    try:
        jobs = build_jobs(markets, root, a.dev, a.smoke, params, a.cuts, h4, h4_excluded)
    except SystemExit as e:
        if a.select == "*":
            raise
        print(f"note: {e}", file=sys.stderr); jobs = []
    jobs = [j for j in jobs if any(fnmatch.fnmatchcase(j["id"], p) for p in patterns)] if a.select != "*" else jobs
    res = run(a.stage, jobs, out, a.workers, a.cuts, h4_excluded) if jobs else {}
    print(json.dumps({"stage": a.stage, "jobs": len(jobs), "results": res}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
