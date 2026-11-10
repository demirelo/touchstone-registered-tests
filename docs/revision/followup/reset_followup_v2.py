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


REPRO = "headline@rho0.2|F111|D2|profit"


def compare(src, out, rid: str = REPRO) -> list[str]:
    """Validation (a): the selected knobs and the per-seed gains must be identical, not close."""
    problems = []
    a, b = read(R.path_of(src, rid)), read(R.path_of(out, rid))
    if a is None or b is None or a["attack"]["best_knobs"] != b["attack"]["best_knobs"]:
        problems.append("selected knobs differ")
    ea, eb = read(R.eval_path(src, rid)), read(R.eval_path(out, rid))
    if ea is None or eb is None or ea["seeds"] != eb["seeds"] or ea["gain"] != eb["gain"]:
        problems.append("per-seed gains differ")
    return problems


def reproduce(src, out, root: str, params: dict, salt_sha256: str, workers: int = 1) -> list[str]:
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
    ap.add_argument("--stage", default="all", choices=("inputs", "search", "freeze", "evaluate", "doubling", "inventory", "all"))
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--reproduce", action="store_true", help=f"validation (a): rerun {REPRO} and compare exactly")
    a = ap.parse_args(argv); out = Path(a.out); check_out(out, a.src)
    from sim.records import cfg_from_dict
    root = json.loads(Path(a.draw).read_text())["hash"]; salt_sha = json.loads(Path(a.instances).read_text())["salt_sha256"]
    container = json.loads(Path(a.addendum).read_text())["deviations"]["configs"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
    if a.reproduce:
        problems = reproduce(a.src, out, root, json.loads(Path(a.params).read_text()), salt_sha, a.workers)
        print(json.dumps({"reproduce": REPRO, "identical": not problems, "problems": problems}))
        return 0 if not problems else 1
    jobs = build_jobs(root, cfgs, json.loads(Path(a.params).read_text()), salt_sha, tuple(a.markets.split(",")), a.smoke)
    check_configs(jobs, container); check_salt(out, salt_sha, jobs); check_commit(jobs); check_code()
    if not a.smoke:
        check_pairing(a.src, jobs)
    steps = ("inputs", "search", "freeze", "evaluate", "doubling", "inventory") if a.stage == "all" else (a.stage,)
    for st in steps:
        if st == "inputs":
            copy_inputs(a.src, out, inputs(a.src, jobs))
        elif st == "search":
            run_stage("search", jobs, out, a.workers)
        elif st == "freeze":
            prefreeze(out, jobs)
        elif st in ("evaluate", "doubling"):
            accept(out, jobs, salt_sha, container, src=a.src); run_stage(st, jobs, out, a.workers)
        else:
            inventory(out)
        print(json.dumps({"stage": st, "jobs": len(jobs)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
