"""The protocol-v2 runner (design 5 to 9; plan docs/superpowers/plans/2026-10-22-revision-build.md Task 11). Stages, in
order: search (profit and W0 searches; X7-SC after the same rule's D2+H3 search, with its embedding as an incumbent),
reference (one menu per rule and context from its D2+H3 and X7-SC searches), dependent (W1 after the reference; the
coalition joint twin, joint reference, then the total and minimum searches), freeze (envelope choices and the fixed-attack
bank, then a complete freeze of the context), then evaluate, cross, and doubling (continued searches, diagnostic only),
each only after the freeze is accepted again. Every record carries provenance and upstream hashes; outputs stay under
--out. Development markets (dev0, dev1) run the fresh0 template of the manifest."""
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
from sim import families_v2 as FV2  # noqa: E402
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
    if name == "H4":
        src = _h4(h4["dir"], h4["sha"]) if h4 else Excluded("no bundle")
        if isinstance(src, Excluded):
            raise SystemExit(f"H4 excluded: {src.reason}")
        return FV2.family_for(name, T, L, src)
    return FV2.family_for(name, T, L)


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
    if family == "H4" and h4:
        j["provenance"]["h4_sha256"] = str(h4["sha"])
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
    if rid.startswith("freeze/"):
        return Path(out) / "freeze" / (rid.split("/", 1)[1] + ".json")
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


def aux_provenance(mkt: dict, **extra) -> dict:
    return context_provenance(mkt) | extra


def group_provenance(job: dict) -> dict:
    return {**job["provenance"], "id": f"coalition/{job['context']}/{_coalition_tag(job)}"}


def reusable(p: Path, rec: dict | None, prov: dict, check) -> bool:
    """The resume rule for every record (plan Review Focus 5): a missing, damaged, or stale record under the current
    provenance is recomputed (False); one that passes `check` is reused (True); a record with another provenance is
    refused, never overwritten."""
    if rec is None:
        return False
    if rec.get("provenance") != prov:
        raise SystemExit(f"{p}: a record with another provenance exists; refusing to overwrite")
    try:
        check()
        return True
    except (ValueError, KeyError, StopIteration, TypeError):
        return False


def _welfare_extra(job: dict, out: Path, T: int) -> tuple[dict, dict]:
    """X7-SC welfare searches start from the embedding of the same rule's D2+H3 welfare selection (design 5.2)."""
    if job["family"] != "X7-SC":
        return {}, {}
    rid = cell_id(job["context"], job["rule"], "D2+H3", job["objective"]); rec = read(path_of(out, rid))
    if rec is None:
        raise SystemExit(f"{job['id']}: needs {rid} first")
    up = {rid: sha_file(path_of(out, rid))}
    return ({"embedded_h3": embed_h3(rec["selected"], T)} if rec.get("selected") else {}), up


def _welfare_record(obj, res, selected, up, T, L) -> dict:
    return {"welfare": search_to_json(res), "selected": selected, "extras": [{"knobs": obj.archive[k].knobs, **v} for k, v in obj.extra.items()],
            "upstream": up, "T": T, "L": L}


def stage_search(job: dict, out: Path) -> dict:
    T, L = constants(job); fam = family_for(job["family"], T, L, job.get("h4")); cache = SeedCache(); st = settings(job); cell = train_cell(job)
    upstream = {}
    if job["objective"] == "W0":
        extra, upstream = _welfare_extra(job, out, T)
        obj = WelfareObjective(cell, fam, cache)
        res = cma_search(obj, fam, st, 1, incumbents={"honest_point": fam.honest_point(), **extra})
        controls(obj, fam)
        best = max(obj.archive.values(), key=lambda e: e.f)
        return _welfare_record(obj, res, dict(best.knobs), upstream, T, L)
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
    if d.get("family") == "H4":
        return FV2.cand_from_json(d, _h4(h4["dir"], h4["sha"]))
    return FV2.cand_from_json(d)


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


def reference_provenance(job: dict) -> dict:
    return aux_provenance(job["mkt"], rule=job["rule"], rule_params_sha256=_sha_json(job["spec"]))


def reference_of(job: dict, out: Path) -> tuple[Candidate, dict, Path]:
    p = path_of(out, f"reference/{job['context']}/{job['rule']}"); rec = read(p)
    if rec is None:
        raise SystemExit(f"{job['id']}: needs the rule's reference")
    return cand_from_json(rec["candidates"][rec["choice"]]), rec, p


def _coalition_tag(job):
    return f"{job['rule']}_c{job['c']}_{job['schedule']}"


def coalition_prereqs(job: dict, out: Path, catalog: list | None = None) -> None:
    """The coalition group's joint twin and joint reference (design 6.3), created once per group before the objective
    searches run, with the group's provenance; existing records are reused only if they pass the full record check."""
    T, L = constants(job); cache = SeedCache(); st = settings(job); m = job["mkt"]; prov = group_provenance(job); catalog = catalog or [job]
    fam = x6v2_family(T, L); members = x6v2_members(m["cfg"], m["focal"], int(job["c"])); stag = job["schedule"] == "staggered"
    tag = _coalition_tag(job); tid, rid = f"joint_twin/{job['context']}/{tag}", f"joint_reference/{job['context']}/{tag}"
    trec = read(path_of(out, tid))
    if not reusable(path_of(out, tid), trec, prov, lambda: check_record(tid, trec, catalog, out)):
        tobj = CoalitionObjective(m["cfg"], rule_factory(job), members, fam, m["seeds_train"], cache, "joint_twin", staggered=stag, T=T, L=L)
        tw = cma_search(tobj, fam, st, 0, starts=fam.registered_starts({"near_corner": st.near_corner, "sobol_seed": st.sobol_seed}, twin=True))
        write(path_of(out, tid), {"stage": "joint_twin", "provenance": prov, "twin": search_to_json(tw), "upstream": {}})
        trec = read(path_of(out, tid))
    jrec = read(path_of(out, rid))
    if not reusable(path_of(out, rid), jrec, prov, lambda: check_record(rid, jrec, catalog, out)):
        jr = joint_reference(m["cfg"], rule_factory(job), members, m["seeds_train"], cache, trec["twin"]["best_knobs"], stag, T, L)
        write(path_of(out, rid), {"stage": "joint_reference", "provenance": prov, "name": jr["name"], "scores": jr["scores"],
                                  "member_normalized": jr["member_normalized"].tolist(), "twin_knobs": jr["twin_knobs"],
                                  "upstream": {tid: sha_file(path_of(out, tid))}})


def stage_dependent(job: dict, out: Path) -> dict:
    T, L = constants(job); cache = SeedCache(); st = settings(job); m = job["mkt"]
    if job["objective"] == "W1":
        cand, rrec, rp = reference_of(job, out); fam = family_for(job["family"], T, L)
        extra, up = _welfare_extra(job, out, T)
        obj = WelfareObjective(train_cell(job), fam, cache, ref_normalized=np.asarray(rrec["per_seed_normalized"]))
        res = cma_search(obj, fam, st, 1, incumbents={"honest_point": fam.honest_point(), **extra})
        controls(obj, fam)
        return _welfare_record(obj, res, select_w1(obj), {f"reference/{job['context']}/{job['rule']}": sha_file(rp), **up}, T, L)
    fam = x6v2_family(T, L); members = x6v2_members(m["cfg"], m["focal"], int(job["c"])); stag = job["schedule"] == "staggered"
    rid = f"joint_reference/{job['context']}/{_coalition_tag(job)}"; jrec = read(path_of(out, rid))
    if jrec is None:
        raise SystemExit(f"{job['id']}: needs {rid} (run the coalition prerequisites first)")
    obj = CoalitionObjective(m["cfg"], rule_factory(job), members, fam, m["seeds_train"], cache, job["objective"],
                             joint_ref=np.asarray(jrec["member_normalized"]), staggered=stag, T=T, L=L)
    res = cma_search(obj, fam, st, 1, incumbents={"joint_twin": jrec["twin_knobs"], "honest_point": fam.honest_point()})
    best = obj.extra[exact_key(res.best_knobs)] if exact_key(res.best_knobs) in obj.extra else None
    return {"coalition": search_to_json(res), "selected": dict(res.best_knobs), "selected_extra": best, "members": list(members),
            "upstream": {rid: sha_file(path_of(out, rid))}, "T": T, "L": L}


# ---- freeze ------------------------------------------------------------------------------------------------------------

def _by_id(catalog: list[dict]) -> dict:
    return {j["id"]: j for j in catalog}


def _first(catalog, **kw):
    return next((j for j in catalog if all(j.get(k) == v for k, v in kw.items())), None)


def expected_upstream(rid: str, catalog: list[dict], cuts: int = 0, h4_excluded: bool = False) -> set:
    """The dependency ids a record must list (design 6.4 order), derived independently of the record."""
    by = _by_id(catalog)
    if "|" in rid:
        j = by[rid]; ctx, rule, fam, obj = j["context"], j["rule"], j["family"], j["objective"]
        if obj == "profit":
            return {_menu_id(ctx, rule, "D2+H3")} if fam == "X7-SC" else set()
        if obj == "W0":
            return {cell_id(ctx, rule, "D2+H3", "W0")} if fam == "X7-SC" else set()
        if obj == "W1":
            return {f"reference/{ctx}/{rule}"} | ({cell_id(ctx, rule, "D2+H3", "W1")} if fam == "X7-SC" else set())
        return {f"joint_reference/{ctx}/{_coalition_tag(j)}"}
    kind, ctx, rest = rid.split("/", 2)
    if kind == "reference":
        ids = {_menu_id(ctx, rest, f) for f in MENU}
        if rest in MATCHED:
            ids |= {_menu_id(ctx, o, f) for f in MENU for o in MAN.bank_rules(manifest_ctx(ctx), f, cuts, h4_excluded) if o != rest}
        return ids
    if kind == "envelope":
        return {f"reference/{ctx}/{rest}"} | {cell_id(ctx, rest, f, "profit") for f in MAN.doc()["envelope_families"] if cell_id(ctx, rest, f, "profit") in by}
    if kind == "bank":
        return {cell_id(ctx, r, rest, "profit") for r in MAN.FACTORIAL if cell_id(ctx, r, rest, "profit") in by}
    if kind == "joint_twin":
        return set()
    if kind == "joint_reference":
        return {f"joint_twin/{ctx}/{rest}"}
    raise ValueError(rid)


def expected_provenance(rid: str, catalog: list[dict]) -> dict:
    by = _by_id(catalog)
    if "|" in rid:
        return by[rid]["provenance"]
    kind, ctx, rest = rid.split("/", 2)
    if kind == "reference":
        return reference_provenance(_first(catalog, context=ctx, rule=rest, objective="profit"))
    any_job = _first(catalog, context=ctx)
    if kind == "envelope":
        return aux_provenance(any_job["mkt"], rule=rest)
    if kind == "bank":
        return aux_provenance(any_job["mkt"], family=rest)
    j = next(j for j in catalog if j["context"] == ctx and j["objective"] in ("total", "min") and _coalition_tag(j) == rest)
    return group_provenance(j)


def check_record(rid: str, rec: dict | None, catalog: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> None:
    if rec is None:
        raise ValueError("missing or unreadable")
    by = _by_id(catalog)
    if "|" in rid and rid not in by:
        raise ValueError("no job in the catalog")
    stage = ("dependent" if by[rid]["objective"] in ("W1", "total", "min") else "search") if "|" in rid else rid.split("/", 1)[0]
    if rec.get("stage") != stage:
        raise ValueError(f"stage {rec.get('stage')!r} is not {stage!r}")
    exp = expected_provenance(rid, catalog); got = rec.get("provenance") or {}
    if got != exp:
        keys = sorted(k for k in set(exp) | set(got) if exp.get(k) != got.get(k))
        raise ValueError(f"provenance differs from the expected provenance in {keys}")
    want = expected_upstream(rid, catalog, cuts, h4_excluded)
    if set(rec.get("upstream") or {}) != want:
        raise ValueError(f"dependencies {sorted(rec.get('upstream') or {})} are not {sorted(want)}")
    validate({"provenance": rec["provenance"]}, stage, rec, {u: path_of(out, u) for u in want})


def derived_records(ctx: str, catalog: list[dict], out: Path, cuts: int, h4_excluded: bool) -> None:
    """Envelope family choices (design 9.3 Q3, on training gains) and the fixed-attack bank (design 6.6)."""
    req = [r.replace(manifest_ctx(ctx), ctx, 1) for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded)]
    any_job = _first(catalog, context=ctx)
    for r in req:
        kind = r.split("/", 1)[0]
        if kind == "envelope":
            rule = r.split("/", 2)[2]; _, rrec, _ = reference_of({"context": ctx, "rule": rule, "id": r}, out)
            ref_score = float(np.mean(rrec["per_seed_normalized"])); gains, up = {}, {}
            for u in sorted(expected_upstream(r, catalog, cuts, h4_excluded)):
                if read(path_of(out, u)) is None:
                    continue
                up[u] = sha_file(path_of(out, u))
                if "|" in u:
                    gains[u.split("|")[2]] = float(read(path_of(out, u))["attack"]["best_f"]) - ref_score
            reusable(path_of(out, r), read(path_of(out, r)), aux_provenance(any_job["mkt"], rule=rule), lambda: None)      # refuses a foreign record
            write(path_of(out, r), {"stage": "envelope", "provenance": aux_provenance(any_job["mkt"], rule=rule),
                                   "choice": max(gains, key=gains.get) if gains else None, "training_gains": gains, "upstream": up})
        elif kind == "bank":
            fname = r.split("/", 2)[2]; attacks, up = {}, {}
            for u in sorted(expected_upstream(r, catalog, cuts, h4_excluded)):
                rec = read(path_of(out, u))
                if rec is not None:
                    attacks[u.split("|")[1]] = rec["attack"]["best_knobs"]; up[u] = sha_file(path_of(out, u))
            reusable(path_of(out, r), read(path_of(out, r)), aux_provenance(any_job["mkt"], family=fname), lambda: None)
            write(path_of(out, r), {"stage": "bank", "provenance": aux_provenance(any_job["mkt"], family=fname), "attacks": attacks, "upstream": up})


def check_complete(ctx: str, catalog: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> list[str]:
    problems = []
    for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded):
        r = r.replace(manifest_ctx(ctx), ctx, 1)
        try:
            check_record(r, read(path_of(out, r)), catalog, out, cuts, h4_excluded)
        except (ValueError, KeyError, StopIteration, TypeError) as e:
            problems.append(f"{r}: {e}")
    return problems


def stage_freeze(ctx: str, catalog: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> dict:
    derived_records(ctx, catalog, out, cuts, h4_excluded)
    problems = check_complete(ctx, catalog, out, cuts, h4_excluded)
    if problems:
        raise SystemExit(f"freeze {ctx} refused: {problems[:5]}{' ...' if len(problems) > 5 else ''}")
    recs = [r.replace(manifest_ctx(ctx), ctx, 1) for r in MAN.required(manifest_ctx(ctx), cuts, h4_excluded)]
    rec = {"stage": "freeze", "context": ctx, "cuts": cuts, "h4_excluded": h4_excluded, "records": {r: sha_file(path_of(out, r)) for r in recs}}
    write(path_of(out, f"freeze/{ctx}"), rec)
    return rec


def accept(ctx: str, catalog: list[dict], out: Path, cuts: int = 0, h4_excluded: bool = False) -> dict:
    fr = read(path_of(out, f"freeze/{ctx}"))
    if fr is None:
        raise SystemExit(f"{ctx}: no freeze; evaluation refused")
    for r, sha in fr["records"].items():
        p = path_of(out, r)
        if not p.exists() or sha_file(p) != sha:
            raise SystemExit(f"{ctx}: {r} differs from the freeze; evaluation refused")
    problems = check_complete(ctx, catalog, out, cuts, h4_excluded)
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


def _cross_rules(ctx: str, family: str, catalog: list[dict], bank: dict) -> tuple[dict, list]:
    by_rule = {j["rule"]: j for j in catalog if j["context"] == ctx and j["family"] == family and j["objective"] == "profit" and j["rule"] in MAN.FACTORIAL}
    return by_rule, [r for r in MAN.FACTORIAL if r in by_rule and r in bank["attacks"]]


def cross_expected(ctx: str, family: str, catalog: list[dict], out: Path) -> tuple[dict, set]:
    """The provenance and dependency ids of a cross record, derived independently of any stored record."""
    bank = read(path_of(out, f"bank/{ctx}/{family}"))
    if bank is None:
        raise SystemExit(f"cross {ctx}/{family}: no fixed-attack bank")
    _, rules = _cross_rules(ctx, family, catalog, bank)
    ids = {f"freeze/{ctx}", f"bank/{ctx}/{family}"} | {f"reference/{ctx}/{r}" for r in rules}
    return aux_provenance(_first(catalog, context=ctx)["mkt"], family=family), ids


def stage_cross(ctx: str, family: str, catalog: list[dict], out: Path) -> dict:
    bank = read(path_of(out, f"bank/{ctx}/{family}")); by_rule, rules = _cross_rules(ctx, family, catalog, bank); cache = SeedCache(); mat, rows = [], {}
    prov, ids = cross_expected(ctx, family, catalog, out)
    up = {u: sha_file(path_of(out, u)) for u in sorted(ids)}
    for a in rules:
        row = []
        for r in rules:
            j = by_rule[r]; T, L = constants(j); fam = family_for(family, T, L); cell = eval_cell(j)
            cand, _, _ = reference_of(j, out)
            att = run_focal(cell, lambda: fam.make(dict(bank["attacks"][a])), cache); ref = run_focal(cell, cand.policy_factory, cache)
            gain = (att.profit - ref.profit) / (np.array([x.sstar for x in att.results]) / cell.cfg.N)
            rows[f"{a}>{r}"] = gain.tolist(); row.append(float(gain.mean()))
        mat.append(row)
    return {"stage": "cross", "provenance": prov, "upstream": up,
            "context": ctx, "family": family, "attacks": rules, "rules": rules, "matrix": mat, "per_seed": rows}


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
        fam = family_for(job["family"], T, L, job.get("h4")); orig = search_from_json(rec["attack"])
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
        obj = WelfareObjective(cell, fam, cache, ref_normalized=ref)
        obj.extra.update({exact_key(e["knobs"]): {k: v for k, v in e.items() if k != "knobs"} for e in rec["extras"]})
        continue_search(obj, fam, st, orig)
        sel_old = rec["selected"]
        old_eff = obj.extra[exact_key(sel_old)]["eff"] if sel_old is not None else None
        sel = select_w1(obj) if job["objective"] == "W1" else dict(max(obj.archive.values(), key=lambda e: e.f).knobs)
        new_eff = obj.extra[exact_key(sel)]["eff"] if sel is not None else None
        return doubling_report("w1" if job["objective"] == "W1" else "welfare", {"eff": old_eff, "feasible": sel_old is not None},
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


def _inputs(job: dict) -> set:
    """The records an evaluation or a doubling check depends on."""
    ids = {job["id"]}
    if job["objective"] in ("profit", "W1"):
        ids.add(f"reference/{job['context']}/{job['rule']}")
    if job["objective"] in ("total", "min"):
        ids.add(f"joint_reference/{job['context']}/{_coalition_tag(job)}")
    return ids


def stage_upstream(stage: str, job: dict, catalog: list[dict], cuts: int, h4_excluded: bool) -> set:
    if stage in ("search", "dependent"):
        return expected_upstream(job["id"], catalog, cuts, h4_excluded)
    ids = _inputs(job) | {f"freeze/{job['context']}"}
    if stage == "doubling" and job["objective"] == "profit":                  # the profit check reselects from the rule's menu
        ids |= expected_upstream(f"reference/{job['context']}/{job['rule']}", catalog, cuts, h4_excluded)
    return ids


def _run_one(stage: str, job: dict, out: str, cuts: int, h4_excluded: bool, catalog: list | None = None) -> str:
    out = Path(out); p = _stage_record_path(stage, job, out); rec = read(p); catalog = catalog or [job]
    want = stage_upstream(stage, job, catalog, cuts, h4_excluded)
    def check():
        if set(rec.get("upstream") or {}) != want:
            raise ValueError("dependency set")
        validate(job, stage, rec, {u: path_of(out, u) for u in want})
    if reusable(p, rec, job["provenance"], check):
        return "skipped"
    body = {"search": stage_search, "dependent": stage_dependent, "evaluate": stage_evaluate}.get(stage)
    rec = body(job, out) if body else stage_doubling(job, out, cuts, h4_excluded)
    upstream = rec.pop("upstream", None)
    if stage in ("evaluate", "doubling") or upstream is None:
        upstream = {u: sha_file(path_of(out, u)) for u in sorted(want)}
    write(p, {"stage": stage, "id": job["id"], "provenance": job["provenance"], "upstream": upstream, **rec})
    return "done"


def _pool(stage, jobs, out, workers, cuts, h4_excluded, catalog=None) -> list:
    if workers <= 1 or len(jobs) <= 1:
        return [_run_one(stage, j, str(out), cuts, h4_excluded, catalog) for j in jobs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        n = len(jobs)
        return list(ex.map(_run_one, [stage] * n, jobs, [str(out)] * n, [cuts] * n, [h4_excluded] * n, [catalog] * n))


def run(stage: str, jobs: list[dict], out: Path, workers: int = 1, cuts: int = 0, h4_excluded: bool = False, catalog: list | None = None) -> dict:
    """`jobs` is the execution subset; `catalog` (default: `jobs`) is the full job list that freeze checks and
    acceptance validate against."""
    out = Path(out); res = {}; catalog = catalog if catalog is not None else jobs
    pool = lambda st_, js: _pool(st_, js, out, workers, cuts, h4_excluded, catalog) if js else []
    if stage == "search":
        first = [j for j in jobs if j["objective"] in ("profit", "W0") and j["family"] != "X7-SC"]
        second = [j for j in jobs if j["objective"] in ("profit", "W0") and j["family"] == "X7-SC"]
        for wave in (first, second):
            for j, r in zip(wave, pool(stage, wave)):
                res[j["id"]] = r
    elif stage == "reference":
        seen = set()
        for j in jobs:
            key = (j["context"], j["rule"])
            if j["objective"] == "profit" and j["family"] in MENU and key not in seen:
                seen.add(key); rid = f"reference/{key[0]}/{key[1]}"; p = path_of(out, rid); old = read(p)
                if reusable(p, old, reference_provenance(j), lambda: check_record(rid, old, catalog, out, cuts, h4_excluded)):
                    res[rid] = "skipped"; continue
                rec = stage_reference(j, out, cuts, h4_excluded); up = rec.pop("upstream")
                write(p, {"stage": "reference", "provenance": reference_provenance(j), "upstream": up, **rec})
                res[rid] = "done"
    elif stage == "dependent":
        w1 = [j for j in jobs if j["objective"] == "W1"]
        for wave in ([j for j in w1 if j["family"] != "X7-SC"], [j for j in w1 if j["family"] == "X7-SC"]):
            for j, r in zip(wave, pool(stage, wave)):
                res[j["id"]] = r
        coal = [j for j in jobs if j["objective"] in ("total", "min")]
        done = set()
        for j in coal:
            g = (j["context"], _coalition_tag(j))
            if g not in done:
                done.add(g); coalition_prereqs(j, out, catalog)
        for j, r in zip(coal, pool(stage, coal)):
            res[j["id"]] = r
    elif stage == "freeze":
        for ctx in sorted({j["context"] for j in jobs}):
            stage_freeze(ctx, catalog, out, cuts, h4_excluded); res[ctx] = "frozen"
    elif stage == "evaluate":
        for ctx in sorted({j["context"] for j in jobs}):
            accept(ctx, catalog, out, cuts, h4_excluded)
        for j, r in zip(jobs, pool(stage, jobs)):
            res[j["id"]] = r
    elif stage == "cross":
        ctxs = sorted({j["context"] for j in jobs})
        for ctx in ctxs:
            if not (ctx in {c for c, _ in MAN.cross_evaluations()} or ctx.startswith("dev")):
                continue
            accept(ctx, catalog, out, cuts, h4_excluded)
            for fam in MENU:
                p = Path(out) / "cross" / ctx / (_safe(fam) + ".json"); old = read(p); prov, ids = cross_expected(ctx, fam, catalog, out)

                def check(old=old, ids=ids, prov=prov):
                    if set(old.get("upstream") or {}) != ids:
                        raise ValueError("dependency set")
                    validate({"provenance": prov}, "cross", old, {u: path_of(out, u) for u in ids})
                if reusable(p, old, prov, check):
                    res[f"cross/{ctx}/{fam}"] = "skipped"; continue
                write(p, stage_cross(ctx, fam, catalog, out)); res[f"cross/{ctx}/{fam}"] = "done"
    elif stage == "doubling":
        dbl = set(MAN.doublings())
        sel = [j for j in jobs if j["id"].replace(j["context"], manifest_ctx(j["context"]), 1) in dbl]
        for ctx in sorted({j["context"] for j in sel}):
            accept(ctx, catalog, out, cuts, h4_excluded)                      # a diagnostic of the accepted freeze only
        for j, r in zip(sel, pool(stage, sel)):
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
    catalog = jobs
    jobs = [j for j in jobs if any(fnmatch.fnmatchcase(j["id"], p) for p in patterns)] if a.select != "*" else jobs
    res = run(a.stage, jobs, out, a.workers, a.cuts, h4_excluded, catalog=catalog) if jobs else {}
    print(json.dumps({"stage": a.stage, "jobs": len(jobs), "results": res}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
