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
import guards as G  # noqa: E402
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


def _expected(rid: str, jobs: list[dict]) -> set:
    return R.expected_upstream(rid, jobs, CUTS, H4_EXCLUDED)


def _ref_provenance(jobs: list[dict], ctx: str) -> dict:
    return R.reference_provenance(next(j for j in jobs if j["context"] == ctx))


def _validate_new(out, rid: str, stage: str, prov: dict, jobs: list[dict]) -> str:
    """A new record of this run: its stage, its current provenance, its dependency ids, and each dependency's current hash."""
    p = R.path_of(out, rid); rec = read(p)
    if rec is None or rec.get("stage") != stage:
        _refuse(f"{rid}: no {stage} record")
    if rec.get("provenance") != prov:
        _refuse(f"{rid}: provenance is not the current job's")
    up = rec.get("upstream") or {}
    if set(up) != _expected(rid, jobs):
        _refuse(f"{rid}: dependency set {sorted(up)} is not the expected one")
    for u, h in up.items():
        q = R.path_of(out, u)
        if not q.exists() or sha_file(q) != h:
            _refuse(f"{rid}: dependency {u} differs from its recorded hash")
    return sha_file(p)


def check_bank_copies(out, src, contexts) -> dict:
    """Exactly the bank inputs, each copy's actual hash equal to the original freeze's."""
    need = bank_inputs(src, contexts)
    for r, h in need.items():
        q = R.path_of(out, r)
        if not q.exists() or sha_file(q) != h:
            _refuse(f"{r}: the copy differs from the original freeze")
    return need


def reference_stage(jobs, out, src) -> None:
    """Reference construction, after the bank copies are checked (also when resumed at --stage reference)."""
    check_bank_copies(out, src, [j["context"] for j in jobs]); run_references(jobs, out)


def _required(out, jobs: list[dict], ctx: str, src) -> dict:
    """Every record the context's freeze must hold: exactly its bank inputs, each copy's actual hash equal to the original
    freeze's, both searches, and its reference, each new record validated with current hashes."""
    recs = dict(check_bank_copies(out, src, [ctx]))
    for j in (j for j in jobs if j["context"] == ctx):
        recs[j["id"]] = _validate_new(out, j["id"], "search", j["provenance"], jobs)
    rid = f"reference/{ctx}/{LABEL}"; recs[rid] = _validate_new(out, rid, "reference", _ref_provenance(jobs, ctx), jobs)
    return recs


def prefreeze(out, jobs, src) -> None:
    for ctx in sorted({j["context"] for j in jobs}):
        body = {"stage": "freeze", "context": ctx, "followup": True, "deviations": list(DEVIATIONS), "cuts": CUTS, "h4_excluded": H4_EXCLUDED,
                "records": _required(out, jobs, ctx, src)}
        p = R.path_of(out, f"freeze/{ctx}"); old = read(p)
        if old is not None and old != body:
            _refuse(f"{p} exists with other records")
        if old is None:
            write(p, body)


def check_freeze(out, jobs, src) -> None:
    """The freeze holds exactly the required records (bank copies checked against the original freeze) with their current
    hashes and the expected metadata."""
    for ctx in sorted({j["context"] for j in jobs}):
        fr = read(R.path_of(out, f"freeze/{ctx}"))
        if fr is None or fr.get("followup") is not True or "cuts" not in fr or "h4_excluded" not in fr or fr["cuts"] != CUTS or fr["h4_excluded"] != H4_EXCLUDED:
            _refuse(f"{ctx}: no follow-up freeze with cuts {CUTS} and H4 loaded")
        if not fr.get("records") or fr["records"] != _required(out, jobs, ctx, src):
            _refuse(f"{ctx}: the freeze is empty, incomplete, or stale")


def accept(out, jobs, salt_sha256: str, container: dict, src) -> None:
    F.check_salt(out, salt_sha256, jobs); F.check_configs(jobs, container); check_no_registered_cstar(src, out)
    check_freeze(out, jobs, src)


EXPECTED_SPEC = {"tol": 0.16, "L": 10, "cred": {"variant": "thr", "K": 12, "M": None}}


def check_spec(jobs: list[dict]) -> None:
    """Each job runs exactly the runner-up of the development recheck: C-thr(K = 12) at tolerance 0.16 and L = 10."""
    for j in jobs:
        if j["spec"] != EXPECTED_SPEC:
            _refuse(f"{j['id']}: the rule specification {j['spec']} is not the runner-up's {EXPECTED_SPEC}")


def check_run_evidence(reset_mac, reset_pod, doubling, smoke: bool, want: dict) -> None:
    """A full run needs the reset driver's headline F111 D2 reproduction gate from the Mac and, bit-identical, from this
    machine, and its fresh0 F111 D2+H3 doubling gate, each verified (guards.check_reset_evidence)."""
    if smoke:
        return
    if not (reset_mac and reset_pod and doubling):
        _refuse("a full run needs the evidence directories --reset-mac, --reset-pod and --doubling-evidence")
    G.check_reset_evidence(reset_mac, reset_pod, doubling, want)


def evidence_want(src, root: str, cfgs: dict, params: dict, salt: str) -> dict:
    """The inputs and budget the reset driver's two reproductions must have used, recomputed from the original records."""
    rj = R.job(R.market("headline", root, 0.2, salt_sha256=salt), "F111", "D2", "profit", params=params)
    dj = R.job(R.market("fresh0", root, 0.2, cfg=cfgs["fresh0"], salt_sha256=salt), "F111", "D2+H3", "profit", params=params)
    dbl = F.inputs(src, [dj]); dbl[dj["id"]] = sha_file(R.path_of(src, dj["id"]))
    return {"repro_inputs": F.inputs(src, [rj]), "dbl_inputs": dbl, "budget": list(rj["budget"]), "src": src}


def run_stage(stage: str, jobs, out, workers: int = 1) -> None:
    """Evaluation and doubling of every runner-up cell (the registered doubling list does not name this rule)."""
    R._pool(stage, jobs, Path(out), workers, CUTS, H4_EXCLUDED, jobs)


EXPECTATION = "pooled g(C*) - g(runner-up) > 0 under D2+H3 (the runner-up leaves the lower gain), base and doubled"


def _base(base, rule: str, fam: str, markets) -> dict | None:
    res = {}
    for m in markets:
        rec = read(R.eval_path(base, R.cell_id(MAN.context(m), rule, fam, "profit")))
        if rec is None:
            return None
        res[m] = (rec["seeds"], rec["gain"])
    return res


def _doubled_out(out, fam: str, markets) -> dict | None:
    res = {}
    for m in markets:
        rec = read(Path(out) / "doubling" / (R._safe(R.cell_id(MAN.context(m), LABEL, fam, "profit")) + ".json"))
        if rec is None or "heldout" not in rec:
            return None
        res[m] = (rec["heldout"]["seeds"], rec["heldout"]["gain"])
    return res


def _doubled_report(report: dict, rule: str, fam: str, markets) -> dict | None:
    res = {}
    for m in markets:
        h = (report.get("doubling", {}).get(R.cell_id(MAN.context(m), rule, fam, "profit")) or {}).get("heldout")
        if h is None:
            return None
        res[m] = (h["seeds"], h["gain"])
    return res


def _contrasts(ru, r3, cs, markets, resamples) -> dict | str:
    if None in (ru, r3, cs):
        return "not available"
    for m in markets:
        if not (ru[m][0] == r3[m][0] == cs[m][0]):
            raise ValueError(f"{m}: evaluation seeds differ")
    if not G.finite([ru[m][1] for m in markets], [r3[m][1] for m in markets], [cs[m][1] for m in markets]):
        return "not available"
    g = lambda d: {m: d[m][1] for m in markets}
    a, b, c = C.pooled_paired(g(ru), g(r3), resamples), C.pooled_paired(g(cs), g(ru), resamples), C.pooled_paired(g(cs), g(r3), resamples)
    return {"runner_up_minus_r3": {**a, "category": C.q1_category(a["interval"])}, "cstar_minus_runner_up": b,
            "cstar_minus_r3": {**c, "category": C.q1_category(c["interval"])}}


def _score(base, doubled) -> dict:
    vals = [None if isinstance(x, str) else x["cstar_minus_runner_up"]["estimate"] > 0 for x in (base, doubled)]   # a tie is not met
    score = "not available" if None in vals else ("met" if all(vals) else ("failed" if not any(vals) else "not established"))
    return {"statement": EXPECTATION, "base": vals[0], "doubled": vals[1], "score": score}


def analysis(out, src, report: dict, markets=MARKETS, fams=FAMS, resamples: int = C.RESAMPLES) -> dict:
    """Per family: runner-up minus R3, C* minus runner-up and C* minus R3, base and doubled, each rule against its own
    unchanged frozen reference, paired on the evaluation seeds, from unrounded values; exploratory."""
    res = {}
    for fam in fams:
        base = _contrasts(_base(out, LABEL, fam, markets), _base(src, "F111", fam, markets), _base(src, "C*", fam, markets), markets, resamples)
        dbl = _contrasts(_doubled_out(out, fam, markets), _doubled_report(report, "F111", fam, markets), _doubled_report(report, "C*", fam, markets), markets, resamples)
        flags = {}
        for m in markets:
            rec = read(Path(out) / "doubling" / (R._safe(R.cell_id(MAN.context(m), LABEL, fam, "profit")) + ".json")) or {}
            flags[m] = {k: rec.get(k) for k in ("attack_change", "reference_change", "incomplete")}
        row = {"label": "exploratory, after the report; " + C.SCOPE, "base": base, "doubled": dbl, "flags": flags}
        if fam == "D2+H3":
            row["expectation"] = _score(base, dbl)
        res[fam] = row
    return res


def stage_hours() -> dict:
    """Billed wall time per stage on one pod (critical path), from the benchmark."""
    t = json.loads((ROOT / "experiments/v2/benchmark/timings.json").read_text())["timings"]; ev = lambda k: t["eval160"][k] * 200 / 160
    return {"inputs": 0.02, "search": (t["d2h3_cell"] + t["x7_cell"]) / 3600, "reference": 6 * t["reference"] / 3600, "freeze": 0.01,
            "evaluate": max(ev("profit"), ev("x7")) / 3600, "doubling": t["doubling_x7"] / 3600, "analysis": 0.05, "inventory": 0.01}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--src", default=str(F.EVAL_ALL)); ap.add_argument("--out", required=True); ap.add_argument("--report", default=str(ROOT / "results/v2/report/report.json"))
    ap.add_argument("--draw", required=True); ap.add_argument("--instances", required=True); ap.add_argument("--cfgs", required=True); ap.add_argument("--addendum", required=True)
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json")); ap.add_argument("--markets", default=",".join(MARKETS))
    ap.add_argument("--stage", default="all", choices=("inputs", "search", "reference", "freeze", "evaluate", "doubling", "analysis", "inventory", "all"))
    ap.add_argument("--workers", type=int, default=1); ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--reset-mac", default=None, help="the reset reproduction gate directory from the Mac (gate.json, inventory.json)")
    ap.add_argument("--reset-pod", default=None, help="the same gate run on this pod with --require-identical")
    ap.add_argument("--doubling-evidence", default=None, help="the reset driver's doubling gate directory (fresh0 F111 D2+H3)")
    ap.add_argument("--site", choices=("mac", "pod"), default="pod", help="a pod run is paid and needs --started-at")
    ap.add_argument("--cap-usd", dest="cap", type=float, default=3.00); ap.add_argument("--usd-per-hour", dest="rate", type=float, default=0.56)
    ap.add_argument("--started-at", dest="started", type=float, default=None, help="pod allocation time (epoch seconds)")
    ap.add_argument("--attempts", default=None, help="the launcher's attempts file (closed attempts count toward the cap); required for a paid run")
    ap.add_argument("--ledger", default=str(ROOT / "docs/revision/budget-ledger.json"), help="recorded spend of earlier launches")
    ap.add_argument("--run-tag", dest="run_tag", default=None, help="ledger tag prefix of this run's launches (e.g. runner-up); required for a paid run")
    ap.add_argument("--stop-file", dest="stop_file", default=None, help="the launcher's STOP file, checked before each stage or round")
    ap.add_argument("--soft-deadline", dest="soft", type=float, default=None, help="the launcher's soft deadline (epoch seconds)")
    a = ap.parse_args(argv); out = Path(a.out); F.check_out(out, a.src)
    G.pin_settings()
    from sim.records import cfg_from_dict
    root = json.loads(Path(a.draw).read_text())["hash"]; salt = json.loads(Path(a.instances).read_text())["salt_sha256"]
    container = json.loads(Path(a.addendum).read_text())["deviations"]["configs"]
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads(Path(a.cfgs).read_text()).items()}
    base_params = json.loads(Path(a.params).read_text())
    check_run_evidence(a.reset_mac, a.reset_pod, a.doubling_evidence, a.smoke,
                       {} if a.smoke else evidence_want(a.src, root, cfgs, base_params, salt))
    out.mkdir(parents=True, exist_ok=True); R.install_salt(root, out)
    markets = tuple(a.markets.split(","))
    jobs = build_jobs(root, cfgs, runner_up_params(base_params), salt, markets, a.smoke)
    check_spec(jobs)
    if not a.smoke:
        for j in jobs:
            G.check_budget(j, R.path_of(a.src, R.cell_id(j["context"], LABEL, j["family"], "profit")))
    preflight(out, a.src, jobs, salt, container, a.smoke)
    b = G.binding(inputs_sha=G.sha_json(bank_inputs(a.src, [j["context"] for j in jobs])), provenance={j["id"]: j["provenance"] for j in jobs},
                  smoke=a.smoke, settings={"markets": list(markets), "spec": EXPECTED_SPEC, "cuts": CUTS}, driver_sha=sha_file(Path(__file__)),
                  deps={"reset_followup_v2.py": sha_file(HERE.parent / "followup" / "reset_followup_v2.py"), "guards.py": sha_file(HERE / "guards.py"),
                        "common.py": sha_file(HERE / "common.py"), "plan": sha_file(HERE / "runner-up-plan.md"), "report": sha_file(Path(a.report))})
    if not G.reusable(out / "run.json", b):
        write(out / "run.json", {"binding": b, "label": "runner-up follow-up run"})
    write(out / "label.json", {"rule_label": LABEL, "rule": "C-thr", "cred": runner_up_cred(), "source": str(LOG.relative_to(ROOT)), "deviations": list(DEVIATIONS)})
    paid = a.site == "pod" and not a.smoke
    cost = (G.paid_cost_stop(a.cap, a.rate, a.started, a.attempts, a.ledger, a.run_tag, stop_file=a.stop_file, soft_deadline=a.soft) if paid else
            G.CostStop(a.cap, a.rate, a.started if a.started is not None else __import__("time").time(), stop_file=a.stop_file, soft_deadline=a.soft))
    hours = stage_hours()
    files = {"driver": Path(__file__), "plan": HERE / "runner-up-plan.md", "report": Path(a.report)}
    steps = ("inputs", "search", "reference", "freeze", "evaluate", "doubling", "analysis", "inventory") if a.stage == "all" else (a.stage,)
    for st in steps:
        if not cost.allow(st, hours[st]):
            write(out / "cost_stop.json", cost.report()); G.inventory(out, DEVIATIONS, files, argv)
            print(json.dumps({"stopped_before": st, "cap_usd": a.cap}), flush=True)
            return 3
        if st == "inputs":
            F.copy_inputs(a.src, out, bank_inputs(a.src, [j["context"] for j in jobs]))
        elif st == "search":
            run_searches(jobs, out, a.workers)
        elif st == "reference":
            reference_stage(jobs, out, a.src)
        elif st == "freeze":
            prefreeze(out, jobs, a.src)
        elif st in ("evaluate", "doubling"):
            accept(out, jobs, salt, container, a.src); run_stage(st, jobs, out, a.workers)
        elif st == "analysis":
            if not a.smoke:                                       # smoke evaluations use two seeds, not the registered 200
                write(out / "analysis.json", analysis(out, a.src, json.loads(Path(a.report).read_text()), markets))
        else:
            write(out / "cost.json", cost.report()); G.inventory(out, DEVIATIONS, files, argv)
        print(json.dumps({"stage": st, "jobs": len(jobs)}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
