"""The reset follow-up (docs/revision/reset-experiment-plan.md, draft 4, section 3): the 18 D2 cells that cut 3 removed
(F000, F111, C* x fresh0..fresh5 at rho 0.2), run with the frozen stage functions of scripts/revision_v2.py.

Three things of the frozen runner are bypassed, each a recorded deviation (DEVIATIONS): the manifest's cut list, the
hard-coded doubling eligibility, and the original freeze. Everything else is the frozen code: `job`, `stage_search`,
`stage_evaluate`, `stage_doubling`, reached through `revision_v2._run_one`, so the record format and the dependency sets
are the registered ones.

Order: copy the inputs (the frozen references, the menu searches and bank sources they list, each checked against the
hash the original records hold), search, the follow-up freeze, acceptance, evaluation, acceptance, doubling, inventory.
The output directory is never results/v2/eval/all."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # docs/revision/followup/ (code after the freeze lives under docs/)
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT))

import revision_v2 as R  # noqa: E402
from sim import manifest_v2 as MAN  # noqa: E402
from sim.records_v2 import read, sha_file, write  # noqa: E402

RULES = ("F000", "F111", "C*")
MARKETS = tuple(f"fresh{i}" for i in range(6))
CUTS, H4_EXCLUDED = 3, False                        # the registered evaluation: cuts 3, H4 loaded (results/v2/draw/h4.json)
EVAL_ALL = ROOT / "results" / "v2" / "eval" / "all"
DEVIATIONS = (
    "manifest cut list bypassed: the 18 D2 cells (F000, F111, C* x fresh0..fresh5, rho 0.2) that cut 3 removed are run",
    "doubling eligibility bypassed: each of the 18 cells gets a doubling check with its held-out evaluation",
    "original freeze bypassed: this script's follow-up freeze and acceptance check replace revision_v2.accept",
)


def _refuse(msg: str):
    raise SystemExit(f"reset follow-up refused: {msg}")


def cell_ids(markets=MARKETS) -> list[str]:
    return [R.cell_id(MAN.context(m), r, "D2", "profit") for m in markets for r in RULES]


def restored_cells(markets=MARKETS) -> list[dict]:
    uncut = {c["id"]: c for c in MAN.cells()}; kept = {c["id"] for c in MAN.effective(CUTS, H4_EXCLUDED)}; ids = cell_ids(markets)
    if missing := [i for i in ids if i not in uncut]:
        _refuse(f"not design cells: {missing}")
    if present := [i for i in ids if i in kept]:
        _refuse(f"not removed by cut {CUTS}: {present}")
    return [uncut[i] for i in ids]


def check_out(out, src=None) -> None:
    o = Path(out).resolve()
    for e in {Path(EVAL_ALL).resolve()} | ({Path(src).resolve()} if src else set()):
        if o == e or e in o.parents:
            _refuse(f"the output {o} is inside {e}")


PAIRED_KEYS = ("runner_sha256", "salt_sha256", "cfg_sha256", "root", "seeds_train", "seeds_val", "seeds_eval", "rule_params_sha256", "context")


def check_pairing(src, jobs: list[dict]) -> None:
    """Each job's provenance equals its frozen reference's provenance on every key the pairing depends on (the commit may
    differ): runner, salt, configuration, root, seeds, rule parameters, context (Fable 5.2 driver review, finding 1)."""
    for j in jobs:
        ref = read(R.path_of(src, f"reference/{j['context']}/{j['rule']}"))
        if ref is None:
            _refuse(f"{j['id']}: no reference record to pair with")
        if bad := [k for k in PAIRED_KEYS if j["provenance"].get(k) != ref["provenance"].get(k)]:
            _refuse(f"{j['id']}: provenance differs from its reference in {bad}")


def check_commit(jobs: list[dict]) -> None:
    if bad := [j["id"] for j in jobs if j["provenance"].get("git_commit") in (None, "", "unknown")]:
        _refuse(f"no git commit recorded for {bad[:3]}")


def check_code() -> None:
    """The frozen runner and simulator are byte-identical to the protocol-v2 tag."""
    import subprocess
    r = subprocess.run(["git", "diff", "--quiet", "protocol-v2", "--", "scripts/revision_v2.py", "sim/"], cwd=ROOT)
    if r.returncode != 0:
        _refuse("scripts/revision_v2.py or sim/ differs from protocol-v2 (or the tag is missing)")


def check_salt(out, salt_sha256: str, jobs: list[dict]) -> None:
    salt = Path(out) / "salt.hex"
    if not salt.exists() or R._sha(bytes.fromhex(salt.read_text().strip())) != salt_sha256:
        _refuse("the identity salt under the output is not the recorded salt")
    if bad := [j["id"] for j in jobs if j["provenance"]["salt_sha256"] != salt_sha256]:
        _refuse(f"jobs carry another salt hash: {bad}")


def build_jobs(root: str, cfgs: dict, params: dict, salt_sha256: str, markets=MARKETS, smoke: bool = False) -> list[dict]:
    """The frozen `job` for each restored cell, on the recorded (container) configuration of its market."""
    jobs = []
    for m in markets:
        mkt = R.market(m, root, 0.2, smoke=smoke, cfg=cfgs[m], salt_sha256=salt_sha256)
        jobs += [R.job(mkt, c["rule"], "D2", "profit", smoke=smoke, params=params, block=c["block"]) for c in restored_cells((m,))]
    return jobs


def _expected_reference_upstream(rid: str) -> set:
    """The registered menu and cuts-3 bank of a reference (revision_v2.expected_upstream)."""
    return R.expected_upstream(rid, [], CUTS, H4_EXCLUDED)


def inputs(src, jobs: list[dict]) -> dict[str, str]:
    """Every record the frozen evaluation and doubling stages read for `jobs`, with the hash the original records hold:
    the reference from the context's original freeze, its menu and bank records from the reference's `upstream`, and
    (recursively) the `upstream` of each copied search record."""
    need: dict[str, str] = {}
    for j in jobs:
        ctx = j["context"]; fr = read(R.path_of(src, f"freeze/{ctx}"))
        if fr is None:
            _refuse(f"the original freeze of {ctx} is missing")
        if fr.get("cuts", CUTS) != CUTS or fr.get("h4_excluded", H4_EXCLUDED) != H4_EXCLUDED:
            _refuse(f"the original freeze of {ctx} is not cuts {CUTS} with H4 loaded")
        rid = f"reference/{ctx}/{j['rule']}"
        if rid not in fr["records"]:
            _refuse(f"{rid} is not in the original freeze of {ctx}")
        ref = read(R.path_of(src, rid))
        if ref is None:
            _refuse(f"{rid} is missing in {src}")
        want = _expected_reference_upstream(rid)
        if want is not None and set(ref.get("upstream") or {}) != want:
            _refuse(f"{rid}: its dependencies are not the registered menu and cuts-{CUTS} bank")
        need[rid] = fr["records"][rid]; todo = dict(ref["upstream"])
        while todo:
            u, s = todo.popitem()
            if need.setdefault(u, s) != s:
                _refuse(f"{u}: two original records hold different hashes")
            for k, v in ((read(R.path_of(src, u)) or {}).get("upstream") or {}).items():
                if need.get(k, v) != v or todo.get(k, v) != v:
                    _refuse(f"{k}: two original records hold different hashes")
                if k not in need:
                    todo[k] = v
    return need


def copy_inputs(src, out, need: dict[str, str]) -> None:
    """Copy each input read-only, checked against its recorded hash; an existing identical copy is kept."""
    for rid, sha in sorted(need.items()):
        p, q = R.path_of(src, rid), R.path_of(out, rid)
        if not p.exists():
            _refuse(f"input {rid} is missing in {src}")
        if sha_file(p) != sha:
            _refuse(f"input {rid} differs from the hash in the original records")
        if q.exists():
            if sha_file(q) != sha:
                _refuse(f"{q} exists and differs from the original {rid}")
            continue
        q.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(p, q); q.chmod(0o444)
    prev = read(Path(out) / "inputs.json")
    if prev is not None and prev != {**prev, **need}:
        _refuse("inputs.json lists other hashes for the same records")
    write(Path(out) / "inputs.json", {**(prev or {}), **need})


def check_configs(jobs: list[dict], container: dict) -> None:
    """Each job's configuration hash equals the recorded container hash (addendum.json deviations.configs)."""
    for j in jobs:
        label = j["mkt"]["label"]; want = (container.get(label) or {}).get("container_hash")
        if j["provenance"]["cfg_sha256"] != want:
            _refuse(f"{j['id']}: configuration hash {j['provenance']['cfg_sha256']} is not the container hash {want}")


def _ctx_inputs(out, ctx: str) -> dict[str, str]:
    return {r: s for r, s in (read(Path(out) / "inputs.json") or {}).items() if ctx in r}


def prefreeze(out, jobs: list[dict]) -> None:
    """The pre-evaluation freeze of each context: its copied inputs and its new search records, with their hashes."""
    for ctx in sorted({j["context"] for j in jobs}):
        recs = dict(_ctx_inputs(out, ctx))
        for j in (j for j in jobs if j["context"] == ctx):
            p = R.path_of(out, j["id"]); rec = read(p)
            if rec is None or rec.get("stage") != "search" or rec.get("provenance") != j["provenance"]:
                _refuse(f"{j['id']}: no current search record to freeze")
            recs[j["id"]] = sha_file(p)
        body = {"stage": "freeze", "context": ctx, "followup": True, "deviations": list(DEVIATIONS), "cuts": CUTS, "h4_excluded": H4_EXCLUDED, "records": recs}
        p = R.path_of(out, f"freeze/{ctx}"); old = read(p)
        if old is not None and old != body:
            _refuse(f"{p} exists with other records")
        if old is None:
            write(p, body)


def accept(out, jobs: list[dict], salt_sha256: str, container: dict, src=None) -> None:
    """Run before evaluation and before doubling: the freeze exists and every record in it, and every copied input,
    still has its hash; the identity salt and the configurations are the recorded ones; with `src`, inputs.json holds
    every input recomputed from the original records."""
    check_salt(out, salt_sha256, jobs)
    check_configs(jobs, container)
    if src is not None:
        have = read(Path(out) / "inputs.json") or {}
        if bad := sorted(r for r, s in inputs(src, jobs).items() if have.get(r) != s):
            _refuse(f"inputs.json lacks or differs on {bad[:3]}")
    for ctx in sorted({j["context"] for j in jobs}):
        fr = read(R.path_of(out, f"freeze/{ctx}"))
        if fr is None or not fr.get("followup"):
            _refuse(f"{ctx}: no follow-up freeze")
        want = {**_ctx_inputs(out, ctx), **{j["id"]: None for j in jobs if j["context"] == ctx}}
        if missing := sorted(set(want) - set(fr["records"])):
            _refuse(f"{ctx}: the freeze lacks {missing}")
        for r, sha in fr["records"].items():
            p = R.path_of(out, r)
            if not p.exists() or sha_file(p) != sha or (want.get(r) not in (None, sha)):
                _refuse(f"{ctx}: {r} differs from the freeze")


def run_stage(stage: str, jobs: list[dict], out, workers: int = 1) -> list[str]:
    return R._pool(stage, jobs, Path(out), workers, CUTS, H4_EXCLUDED, jobs)


def inventory(out) -> dict:
    """Every output file with its hash, written after the outputs, so no record lists itself."""
    out = Path(out)
    recs = {str(p.relative_to(out)): sha_file(p) for p in sorted(out.rglob("*"))
            if p.is_file() and p.name != "inventory.json" and not p.name.endswith((".lock", ".tmp"))}
    import platform
    import numpy
    env = {"python": platform.python_version(), "numpy": numpy.__version__, "machine": platform.machine(), "platform": platform.platform(),
           "processor": platform.processor(), "driver_sha256": sha_file(Path(__file__))}
    inv = {"stage": "inventory", "deviations": list(DEVIATIONS), "environment": env, "records": recs}
    write(out / "inventory.json", inv)
    return inv


def reset_stats(results, focal: int) -> dict:
    """Plan section 4: per episode, the focal provider's identity replacements, the rounds they were created, the rounds
    without a focal offer (banned or waiting), and the ban rounds imposed on its identities."""
    import numpy as np
    resets, rounds, no_offer, bans = [], [], [], []
    for r in results:
        mine = [i for i, e in enumerate(r.entity_of) if e == focal]
        new = [i for i in mine if r.identity_generation[i] > 0]
        resets.append(len(new)); rounds.append([int(r.identity_round[i]) for i in new])
        no_offer.append(int(np.isnan(r.claims[:, focal]).sum()))
        bans.append(int(sum(v for h in r.history for i, v in h.consequences.bans.items() if i in mine)))
    return {"resets": resets, "reset_rounds": rounds, "no_offer_rounds": no_offer, "ban_rounds": bans,
            "mean_resets": float(np.mean(resets)), "p_any_reset": float(np.mean([x > 0 for x in resets])),
            "mean_no_offer_rounds": float(np.mean(no_offer)), "mean_ban_rounds": float(np.mean(bans))}


def with_x(knobs: dict, x: int) -> dict:
    """The same policy in the D2+H3 family with the replacement switch set to x (D2 is D2+H3 with x = 0)."""
    return {**knobs, "x": int(x)}


def diagnostics(src, out, jobs: list[dict], report: dict) -> dict:
    """Plan section 4 (draft 5), evaluation only: for each D2 job's (context, rule), the base and doubled D2+H3 winners and
    the base D2 winner on the evaluation seeds with reset instrumentation; the switch g(winner) - g(winner with x = 0) for
    the D2+H3 winners and the reverse switch g(D2 winner with x = 1) - g(D2 winner). The reference cancels in each switch,
    so it is a difference of normalised profits."""
    import numpy as np
    from sim.cell import SeedCache, run_focal
    res = {}
    for j in jobs:
        T, L = R.constants(j); fam = R.family_for("D2+H3", T, L); cell = R.eval_cell(j); cache = SeedCache()
        h3 = R.cell_id(j["context"], j["rule"], "D2+H3", "profit")
        pols = {"d2h3_base": read(R.path_of(src, h3))["attack"]["best_knobs"], "d2h3_doubled": report["doubling"][h3]["heldout"]["knobs"],
                "d2_base": with_x(read(R.path_of(out, j["id"]))["attack"]["best_knobs"], 0)}
        runs = {k: run_focal(cell, lambda k=k: fam.make(dict(pols[k])), cache) for k in pols}
        row = {k: {"knobs": pols[k], **reset_stats(runs[k].results, cell.focal), "mean_normalized": float(np.mean(runs[k].normalized))} for k in pols}
        for k in ("d2h3_base", "d2h3_doubled"):
            if int(pols[k].get("x", 0)) == 0:
                row[k]["switch_x0"] = {"identical": True, "effect": 0.0}
            else:
                off = run_focal(cell, lambda k=k: fam.make(with_x(pols[k], 0)), cache)
                row[k]["switch_x0"] = {"identical": False, "effect": float(np.mean(runs[k].normalized - off.normalized))}
        on = run_focal(cell, lambda: fam.make(with_x(pols["d2_base"], 1)), cache)
        row["d2_base"]["switch_x1"] = {"effect": float(np.mean(on.normalized - runs["d2_base"].normalized))}
        res[f"{j['context']}|{j['rule']}"] = row
    return res


REPRO = "headline@rho0.2|F111|D2|profit"


KNOB_TOL, GAIN_TOL = 1e-9, 1e-9                      # plan draft 5, section 3 (a)


def compare(src, out, rid: str = REPRO) -> dict:
    """Validation (a), plan draft 5: exact on the episode count, archive size, `best_source`, discrete knobs, budget,
    configuration hash, dependency set and seeds; continuous knobs within KNOB_TOL relative and per-seed gains within
    GAIN_TOL absolute. `identical` reports bit identity separately."""
    a, b = read(R.path_of(src, rid)), read(R.path_of(out, rid)); ea, eb = read(R.eval_path(src, rid)), read(R.eval_path(out, rid))
    if None in (a, b, ea, eb):
        return {"pass": False, "identical": False, "problems": ["a record is missing"]}
    problems = []
    ka, kb = a["attack"]["best_knobs"], b["attack"]["best_knobs"]
    if set(ka) != set(kb):
        problems.append("knob names differ")
    disc = [k for k in ka if isinstance(ka[k], int) and not isinstance(ka[k], bool)]
    if any(ka[k] != kb.get(k) for k in disc):
        problems.append("discrete knob differs")
    rel = max((abs(ka[k] - kb[k]) / max(abs(ka[k]), 1e-300) for k in ka if k not in disc and k in kb), default=0.0)
    if rel > KNOB_TOL:
        problems.append(f"knob tolerance exceeded ({rel:.3g})")
    for what, x, y in (("episode count", a.get("runs"), b.get("runs")), ("best_source", a["attack"].get("best_source"), b["attack"].get("best_source")),
                       ("archive size", len(a["attack"].get("archive", [])), len(b["attack"].get("archive", []))),
                       ("budget", a["provenance"].get("budget"), b["provenance"].get("budget")),
                       ("configuration hash", a["provenance"].get("cfg_sha256"), b["provenance"].get("cfg_sha256")),
                       ("dependency set", sorted(a.get("upstream") or {}), sorted(b.get("upstream") or {})), ("seeds", ea["seeds"], eb["seeds"])):
        if x != y:
            problems.append(f"{what} differs")
    gd = max((abs(x - y) for x, y in zip(ea["gain"], eb["gain"])), default=0.0) if len(ea["gain"]) == len(eb["gain"]) else float("inf")
    if gd > GAIN_TOL:
        problems.append(f"gain tolerance exceeded ({gd:.3g})")
    return {"pass": not problems, "identical": ka == kb and ea["gain"] == eb["gain"], "max_knob_rel": rel, "max_gain_abs": gd, "problems": problems}


def compare_doubling(src, out, rid: str) -> dict:
    """Validation (d), plan draft 5: a doubling record against the registered one; exact on the flag, the seeds, and the
    discrete knobs; 1e-9 on the continuous knobs, the changes, and the held-out per-seed gains."""
    p = lambda b: Path(b) / "doubling" / (R._safe(rid) + ".json")
    a, b = read(p(src)), read(p(out))
    if a is None or b is None:
        return {"pass": False, "problems": ["a record is missing"]}
    problems = []
    if bool(a.get("incomplete")) != bool(b.get("incomplete")):
        problems.append("flag differs")
    ha, hb = a["heldout"], b["heldout"]
    if ha["seeds"] != hb["seeds"]:
        problems.append("seeds differ")
    ka, kb = ha["knobs"], hb["knobs"]; disc = [k for k in ka if isinstance(ka[k], int) and not isinstance(ka[k], bool)]
    if set(ka) != set(kb) or any(ka[k] != kb[k] for k in disc):
        problems.append("discrete knob differs")
    rel = max((abs(ka[k] - kb[k]) / max(abs(ka[k]), 1e-300) for k in ka if k not in disc and k in kb), default=0.0)
    chg = max(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in ("attack_change", "reference_change"))
    gd = max((abs(x - y) for x, y in zip(ha["gain"], hb["gain"])), default=0.0) if len(ha["gain"]) == len(hb["gain"]) else float("inf")
    if rel > KNOB_TOL or chg > GAIN_TOL or gd > GAIN_TOL:
        problems.append(f"tolerance exceeded (knobs {rel:.3g}, changes {chg:.3g}, gains {gd:.3g})")
    return {"pass": not problems, "max_knob_rel": rel, "max_change_abs": chg, "max_gain_abs": gd, "problems": problems}


def reproduce_doubling(src, out, rid: str, root: str, cfgs: dict, params: dict, salt_sha256: str) -> dict:
    """Rerun the registered doubling check of one fresh-market D2+H3 cell with the frozen stage, against copies of its inputs."""
    label, rest = rid.split("@", 1); rule = rid.split("|")[1]
    j = R.job(R.market(label, root, 0.2, cfg=cfgs[label], salt_sha256=salt_sha256), rule, "D2+H3", "profit", params=params)
    need = inputs(src, [j]); need[j["id"]] = sha_file(R.path_of(src, j["id"]))
    copy_inputs(src, out, need)
    rec = R.stage_doubling(j, out, CUTS, H4_EXCLUDED)
    write(Path(out) / "doubling" / (R._safe(rid) + ".json"), {"stage": "doubling", "id": rid, **rec})
    return compare_doubling(src, out, rid)


def reproduce(src, out, root: str, params: dict, salt_sha256: str, workers: int = 1) -> dict:
    """Rerun the registered headline F111 D2 search and evaluation through this script's path (input copies, freeze,
    acceptance) and compare with the registered records."""
    mkt = R.market("headline", root, 0.2, salt_sha256=salt_sha256)
    j = R.job(mkt, "F111", "D2", "profit", params=params)
    reg = read(R.path_of(src, REPRO))
    if reg is None or reg["provenance"]["cfg_sha256"] != j["provenance"]["cfg_sha256"]:
        _refuse("the headline configuration on this machine is not the registered one")
    copy_inputs(src, out, inputs(src, [j]))
    run_stage("search", [j], out, workers); prefreeze(out, [j])
    accept(out, [j], salt_sha256, {"headline": {"container_hash": reg["provenance"]["cfg_sha256"]}})
    run_stage("evaluate", [j], out, workers)
    return compare(src, out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(EVAL_ALL)); ap.add_argument("--out", required=True)
    ap.add_argument("--draw", default=str(ROOT / "results/v2/draw/draw.json")); ap.add_argument("--instances", default=str(ROOT / "results/v2/draw/instances.json"))
    ap.add_argument("--cfgs", default=str(ROOT / "results/v2/deviation/cfg_linux.json")); ap.add_argument("--addendum", default=str(ROOT / "results/v2/report/addendum.json"))
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json")); ap.add_argument("--markets", default=",".join(MARKETS))
    ap.add_argument("--stage", default="all", choices=("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory", "all"))
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--reproduce", action="store_true", help=f"validation (a): rerun {REPRO} and compare (plan draft 5)")
    ap.add_argument("--reproduce-doubling", dest="repro_dbl", default=None, help="validation (d): a registered D2+H3 doubling cell id")
    ap.add_argument("--report", default=str(ROOT / "results/v2/report/report.json"), help="for the diagnostics stage")
    a = ap.parse_args(argv); out = Path(a.out); check_out(out, a.src)
    from sim.records import cfg_from_dict
    root = json.loads(Path(a.draw).read_text())["hash"]; salt_sha = json.loads(Path(a.instances).read_text())["salt_sha256"]
    container = json.loads(Path(a.addendum).read_text())["deviations"]["configs"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
    if a.repro_dbl:
        rep = reproduce_doubling(a.src, out, a.repro_dbl, root, cfgs, json.loads(Path(a.params).read_text()), salt_sha)
        print(json.dumps({"reproduce_doubling": a.repro_dbl, **rep}))
        return 0 if rep["pass"] else 1
    if a.reproduce:
        rep = reproduce(a.src, out, root, json.loads(Path(a.params).read_text()), salt_sha, a.workers)
        print(json.dumps({"reproduce": REPRO, **rep}))
        return 0 if rep["pass"] else 1
    jobs = build_jobs(root, cfgs, json.loads(Path(a.params).read_text()), salt_sha, tuple(a.markets.split(",")), a.smoke)
    check_configs(jobs, container); check_salt(out, salt_sha, jobs); check_commit(jobs); check_code()
    if not a.smoke:
        check_pairing(a.src, jobs)
    steps = ("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory") if a.stage == "all" else (a.stage,)
    for st in steps:
        if st == "inputs":
            copy_inputs(a.src, out, inputs(a.src, jobs))
        elif st == "search":
            run_stage("search", jobs, out, a.workers)
        elif st == "freeze":
            prefreeze(out, jobs)
        elif st == "diagnostics":
            write(out / "diagnostics.json", diagnostics(a.src, out, jobs, json.loads(Path(a.report).read_text())))
        elif st in ("evaluate", "doubling"):
            accept(out, jobs, salt_sha, container, src=a.src); run_stage(st, jobs, out, a.workers)
        else:
            inventory(out)
        print(json.dumps({"stage": st, "jobs": len(jobs)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
