"""Run A (docs/revision/followup2/runner-up-plan.md): the full-budget runner-up comparator C-thr(K=12) on the six fresh
markets at rho 0.2, under D2+H3 and X7-SC, with the frozen stage functions of scripts/revision_v2.py.

The frozen code identifies a rule by its label and reads its parameters from `params["cred"]`. The runner-up therefore
runs under the label "C*" with the runner-up's credibility parameters, in its own output directory; its records differ
from the registered C* records by `rule_params_sha256`, and `label.json` names the rule. The driver refuses an output
that contains a copy of a registered C* record. Its reference is selected by the frozen reference stage from the
registered C* menu construction: its own D2+H3 and X7-SC searches plus the cuts-3 bank of the other rules' registered
winners (the registered C* winner is excluded, as C* excluded itself).

Order: bank inputs (hash-checked against the original freeze), preflight, searches (D2+H3, then X7-SC), references,
the follow-up freeze, acceptance, evaluation, acceptance, doubling, analysis, inventory. Exploratory; no registered
estimate or decision changes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE.parent / "followup")); sys.path.insert(0, str(HERE))

import common as C  # noqa: E402
import reset_followup_v2 as F  # noqa: E402
import revision_v2 as R  # noqa: E402
from sim import manifest_v2 as MAN  # noqa: E402
from sim.records_v2 import read, sha_file, write  # noqa: E402

LABEL = "C*"
FAMS = ("D2+H3", "X7-SC")
MARKETS = tuple(f"fresh{i}" for i in range(6))
CUTS, H4_EXCLUDED = F.CUTS, F.H4_EXCLUDED
LOG = ROOT / "experiments" / "v2" / "log" / 'Cstar__{"L":10,"cred":{"K":12,"M":null,"variant":"thr"},"tol":0.16}__recheck.json'
DEVIATIONS = ("a rule outside the registered manifest: the full-budget development runner-up C-thr(K=12), run under the label C* in its own output",
              "its reference menu: its own searches plus the cuts-3 bank of the other rules' registered winners, without the registered C* winner",
              "follow-up freeze and acceptance of this script replace revision_v2.accept; exploratory, after the report")


def _refuse(msg: str):
    raise SystemExit(f"runner-up follow-up refused: {msg}")


def runner_up_cred() -> dict:
    rec = read(LOG)
    if rec is None or not rec.get("recheck"):
        _refuse(f"no full-budget recheck record at {LOG}")
    return dict(rec["spec"]["cred"])


def runner_up_params(base: dict) -> dict:
    return {**base, "cred": runner_up_cred()}


def build_jobs(root: str, cfgs: dict, params: dict, salt_sha256: str, markets=MARKETS, smoke: bool = False) -> list[dict]:
    jobs = []
    for m in markets:
        mkt = R.market(m, root, 0.2, smoke=smoke, cfg=cfgs[m], salt_sha256=salt_sha256)
        jobs += [R.job(mkt, LABEL, fam, "profit", smoke=smoke, params=params) for fam in FAMS]
    return jobs


def bank_inputs(src, contexts) -> dict[str, str]:
    """The other rules' registered winners that the frozen menu reads for a C*-labelled rule, with their original freeze hashes."""
    need = {}
    for ctx in sorted(set(contexts)):
        fr = read(R.path_of(src, f"freeze/{ctx}"))
        if fr is None or fr.get("cuts") != CUTS or fr.get("h4_excluded") != H4_EXCLUDED:
            _refuse(f"the original freeze of {ctx} is missing or not cuts {CUTS} with H4 loaded")
        for fam in MAN.menu_families(R.manifest_ctx(ctx), LABEL):
            for other in MAN.bank_rules(R.manifest_ctx(ctx), fam, CUTS, H4_EXCLUDED):
                if other == LABEL:
                    continue
                rid = R.cell_id(ctx, other, fam, "profit")
                if rid not in fr["records"]:
                    _refuse(f"{rid} is not in the original freeze of {ctx}")
                need[rid] = fr["records"][rid]
    return need


def check_no_registered_cstar(src, out) -> None:
    """No file under the output may be a byte copy of a registered C* record (the label is shared)."""
    out, src = Path(out), Path(src)
    if not out.exists():
        return
    for q in out.rglob("*.json"):
        if "__Cstar__" not in q.name and q.stem != "Cstar":       # the C* label exactly; C*/S0 (Cstar~S0) is a bank input
            continue
        p = src / q.relative_to(out)
        if p.exists() and sha_file(p) == sha_file(q):
            _refuse(f"{q} is a copy of a registered C* record")


def check_pairing_rule(src, jobs: list[dict]) -> None:
    """Each job matches the registered C* reference's provenance on every pairing key except the rule parameters, which
    must differ (otherwise the job is the registered C*)."""
    keys = [k for k in F.PAIRED_KEYS if k != "rule_params_sha256"]
    for j in jobs:
        ref = read(R.path_of(src, f"reference/{j['context']}/{LABEL}"))
        if ref is None:
            _refuse(f"{j['id']}: no registered C* reference to pair with")
        if bad := [k for k in keys if j["provenance"].get(k) != ref["provenance"].get(k)]:
            _refuse(f"{j['id']}: provenance differs from the registered C* reference in {bad}")
        if j["provenance"].get("rule_params_sha256") == ref["provenance"].get("rule_params_sha256"):
            _refuse(f"{j['id']}: rule parameters equal the registered C*'s")


def preflight(out, src, jobs, salt_sha256: str, container: dict, smoke: bool = False) -> None:
    F.check_salt(out, salt_sha256, jobs); F.check_commit(jobs); F.check_code(); F.check_configs(jobs, container)
    check_no_registered_cstar(src, out)
    if not smoke:
        check_pairing_rule(src, jobs)


def run_searches(jobs, out, workers: int = 1) -> None:
    for fam in FAMS:
        R._pool("search", [j for j in jobs if j["family"] == fam], Path(out), workers, CUTS, H4_EXCLUDED, jobs)


def run_references(jobs, out) -> None:
    for item in R._menu_items(jobs):
        R._run_reference(item, Path(out), CUTS, H4_EXCLUDED, jobs)


def prefreeze(out, jobs) -> None:
    inp = read(Path(out) / "inputs.json") or {}
    for ctx in sorted({j["context"] for j in jobs}):
        ids = [j["id"] for j in jobs if j["context"] == ctx] + [f"reference/{ctx}/{LABEL}"]
        recs = {r: s for r, s in inp.items() if ctx in r}
        for i in ids:
            p = R.path_of(out, i)
            if not p.exists():
                _refuse(f"{i}: missing before the freeze")
            recs[i] = sha_file(p)
        body = {"stage": "freeze", "context": ctx, "followup": True, "deviations": list(DEVIATIONS), "cuts": CUTS, "h4_excluded": H4_EXCLUDED, "records": recs}
        p = R.path_of(out, f"freeze/{ctx}"); old = read(p)
        if old is not None and old != body:
            _refuse(f"{p} exists with other records")
        if old is None:
            write(p, body)


def accept(out, jobs, salt_sha256: str, container: dict, src) -> None:
    F.check_salt(out, salt_sha256, jobs); F.check_configs(jobs, container); check_no_registered_cstar(src, out)
    have = read(Path(out) / "inputs.json") or {}
    if bad := sorted(r for r, s in bank_inputs(src, [j["context"] for j in jobs]).items() if have.get(r) != s):
        _refuse(f"inputs.json lacks or differs on {bad[:3]}")
    for ctx in sorted({j["context"] for j in jobs}):
        fr = read(R.path_of(out, f"freeze/{ctx}"))
        if fr is None or not fr.get("followup"):
            _refuse(f"{ctx}: no follow-up freeze")
        for r, sha in fr["records"].items():
            p = R.path_of(out, r)
            if not p.exists() or sha_file(p) != sha:
                _refuse(f"{ctx}: {r} differs from the freeze")


def run_stage(stage: str, jobs, out, workers: int = 1) -> None:
    """Evaluation and doubling of every runner-up cell (the registered doubling list does not name this rule)."""
    R._pool(stage, jobs, Path(out), workers, CUTS, H4_EXCLUDED, jobs)


def _gains(base, rule: str, fam: str, markets) -> dict:
    res = {}
    for m in markets:
        rec = read(R.eval_path(base, R.cell_id(MAN.context(m), rule, fam, "profit")))
        if rec is None:
            raise ValueError(f"no evaluation of {m} {rule} {fam} in {base}")
        res[m] = (rec["seeds"], rec["gain"])
    return res


def analysis(out, src, markets=MARKETS, fams=FAMS, resamples: int = C.RESAMPLES) -> dict:
    """d' = g(runner-up) - g(R3) and g(C*) - g(runner-up) per family, paired on the evaluation seeds; exploratory."""
    res = {}
    for fam in fams:
        ru, r3, cs = _gains(out, LABEL, fam, markets), _gains(src, "F111", fam, markets), _gains(src, "C*", fam, markets)
        for m in markets:
            if not (ru[m][0] == r3[m][0] == cs[m][0]):
                raise ValueError(f"{m} {fam}: evaluation seeds differ")
        g = lambda d: {m: d[m][1] for m in markets}
        a = C.pooled_paired(g(ru), g(r3), resamples); b = C.pooled_paired(g(cs), g(ru), resamples)
        res[fam] = {"label": "exploratory, after the report; nominal paired percentile bootstrap; not registered",
                    "runner_up_minus_r3": {**a, "category": C.q1_category(a["interval"])}, "cstar_minus_runner_up": b}
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True)
    ap.add_argument("--draw", required=True); ap.add_argument("--instances", required=True); ap.add_argument("--cfgs", required=True); ap.add_argument("--addendum", required=True)
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json")); ap.add_argument("--markets", default=",".join(MARKETS))
    ap.add_argument("--stage", default="all", choices=("inputs", "search", "reference", "freeze", "evaluate", "doubling", "analysis", "inventory", "all"))
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv); out = Path(a.out); F.check_out(out, a.src)
    from sim.records import cfg_from_dict
    root = json.loads(Path(a.draw).read_text())["hash"]; salt = json.loads(Path(a.instances).read_text())["salt_sha256"]
    container = json.loads(Path(a.addendum).read_text())["deviations"]["configs"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
    write(out / "label.json", {"rule_label": LABEL, "rule": "C-thr", "cred": runner_up_cred(), "source": str(LOG.relative_to(ROOT)), "deviations": list(DEVIATIONS)})
    markets = tuple(a.markets.split(","))
    jobs = build_jobs(root, cfgs, runner_up_params(json.loads(Path(a.params).read_text())), salt, markets, a.smoke)
    preflight(out, a.src, jobs, salt, container, a.smoke)
    steps = ("inputs", "search", "reference", "freeze", "evaluate", "doubling", "analysis", "inventory") if a.stage == "all" else (a.stage,)
    for st in steps:
        if st == "inputs":
            F.copy_inputs(a.src, out, bank_inputs(a.src, [j["context"] for j in jobs]))
        elif st == "search":
            run_searches(jobs, out, a.workers)
        elif st == "reference":
            run_references(jobs, out)
        elif st == "freeze":
            prefreeze(out, jobs)
        elif st in ("evaluate", "doubling"):
            accept(out, jobs, salt, container, a.src); run_stage(st, jobs, out, a.workers)
        elif st == "analysis":
            if not a.smoke:                                       # smoke evaluations use two seeds, not the registered 200
                write(out / "analysis.json", analysis(out, a.src, markets))
        else:
            F.inventory(out)
        print(json.dumps({"stage": st, "jobs": len(jobs)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
