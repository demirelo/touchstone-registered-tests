"""Driver of the churn replication (docs/revision/followup3/replication-plan.md, draft 3 with the review r3 caveats).
It calls the frozen functions directly (no change under sim/ or scripts/) and reuses the churn arm's and Run A's helpers.
Stages, in order (each checks the commitment manifest and the frozen code first, plan section 5):
  instances    the draw record and stamped manifest -> the six markets, their seeds and salt (no calibration)
  calibrate    the six calibrated configurations, once, on this machine; their hashes and the container record
  menu         the matched rules' D2+H3 searches, then their X7-SC searches; references of R3, C*, B3; the follow-up freeze
  cthr         the runner-up C-thr(12) under the C* label in its own directory: bank copies, searches, reference, freeze
  gate0        the churn-zero gate: one p = 0 cell through the churn path against the ordinary menu search (all stages)
  rates        p = 0 evaluation and doubling of the menu winners; p = 0.03, 0.05 churn search, evaluation, doubling, diagnostics
  continue     the ordered continuation queue of flagged cells (churn-aware adapter; round 1 against this run's doubling)
  inventory    one inventory.json at the output root (last on each pod; the launcher verifies against it)
The market labels stay fresh0..fresh5 (the frozen code requires them); every output lives under --out, never under the
registered results. Usage: rep_v2.py --stage <stage> --out <dir> --manifest <file> [stage options]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for p in (HERE, HERE.parent / "churn", HERE.parent / "followup2", HERE.parent / "followup", ROOT, ROOT / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import commitment as K  # noqa: E402

MARKETS = tuple(f"fresh{i}" for i in range(6))
TARGETS = ("F111", "C*", "F000")                     # R3, C*, B3
RATES = (0.03, 0.05)
FAMS = ("D2+H3", "X7-SC")
CONT_RATE_ORDER = (0.05, 0.03, 0.0)                  # plan section 4: the continuation queue order
CONT_RULE_ORDER = ("F111", "C*", "Cthr", "F000")


def _refuse(msg: str):
    raise SystemExit(f"replication refused: {msg}")


# ---- pure helpers (tested) ------------------------------------------------------------------------------------------

def continuation_queue(flagged: list[dict]) -> list[dict]:
    """The flagged cells in the fixed order: rate 0.05, 0.03, 0; markets fresh0..5; rules R3, C*, C-thr, B3.
    Each item: {"rate": float, "market": str, "rule": "F111" | "C*" | "Cthr" | "F000", ...}."""
    rk = {r: i for i, r in enumerate(CONT_RATE_ORDER)}; uk = {r: i for i, r in enumerate(CONT_RULE_ORDER)}
    bad = [c for c in flagged if c["rate"] not in rk or c["rule"] not in uk or c["market"] not in MARKETS]
    if bad:
        _refuse(f"unknown cells in the flag list: {bad[:3]}")
    return sorted(flagged, key=lambda c: (rk[c["rate"]], MARKETS.index(c["market"]), uk[c["rule"]]))


def resume_point(queue: list[dict], passed: set) -> int:
    """A resume continues the same queue from the first cell without a passing record (plan section 4)."""
    for i, c in enumerate(queue):
        if c["id"] not in passed:
            return i
    return len(queue)


def admit_workers(requested: int, limit_bytes: int | None, peak_bytes: float, parent_bytes: float = 2e9, headroom: float = 1.25) -> int:
    """Pod-memory admission (plan section 5): the largest worker count whose measured peak with 25 percent headroom,
    plus the parent, fits the pod's cgroup limit; at least 1 only if one task fits, else refuse."""
    if limit_bytes is None:
        return requested
    fit = int((limit_bytes - parent_bytes) // (peak_bytes * headroom))
    if fit < 1:
        _refuse(f"one task needs {peak_bytes * headroom / 1e9:.1f} GB with headroom; the limit is {limit_bytes / 1e9:.1f} GB")
    return min(requested, fit)


def check_cfg_reuse(cfgs_path: Path, calibration_record: dict) -> None:
    """The saved configurations are reused on a later pod only if their hash equals the calibrating pod's record."""
    if K._sha(Path(cfgs_path)) != calibration_record.get("cfgs_sha256"):
        _refuse("the saved configurations differ from the calibration record")


# ---- stages (run on the Mac in smoke mode and on the pod) ---------------------------------------------------------

def _require(a) -> None:
    K.require(ROOT, a.manifest)
    pin_commit(a.manifest)


def pin_commit(manifest) -> None:
    """Every job built in this process records the manifest's commit, not the current HEAD, so a docs-only commit
    between stages or pods cannot change a provenance. Truthful because require() has just checked that sim/ and
    scripts/ equal that commit. Jobs are built in the parent, so the workers inherit the provenance with each job."""
    import revision_v2 as R
    commit = json.loads(Path(manifest).read_text())["commit"]
    R.git_commit = lambda: commit


def stage_instances(a) -> None:
    from scripts import draw_v2
    draw = json.loads(Path(a.draw).read_text())
    proto = Path(a.protocol or a.manifest).read_bytes()      # production: the stamped manifest's bytes (plan section 5)
    if a.protocol and not a.smoke:
        _refuse("--protocol other than the manifest is for smoke runs only")
    inst = draw_v2.instances(draw, proto, Path(a.proof).read_bytes(), a.published_height, calibrate=False)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "instances.json").write_text(json.dumps(inst, indent=1, sort_keys=True) + "\n")


def stage_calibrate(a) -> None:
    import platform

    import revision_v2 as R
    from sim import instances as INST
    from sim.records import cfg_from_dict, cfg_to_dict
    out = Path(a.out); inst = json.loads((out / "instances.json").read_text())
    cfgs = {m: cfg_to_dict(INST.calibrated(cfg_from_dict(inst["markets"][m]["cfg"]))) for m in MARKETS}
    p = out / "cfgs.json"; p.write_text(json.dumps(cfgs, indent=1, sort_keys=True) + "\n")
    params = json.loads(Path(a.params).read_text())
    container = {}
    for m in MARKETS:
        mkt = R.market(m, inst["root"], 0.2, cfg=cfg_from_dict(cfgs[m]), salt_sha256=inst["salt_sha256"])
        container[m] = {"container_hash": R.job(mkt, "F111", "D2+H3", "profit", params=params)["provenance"]["cfg_sha256"]}
    rec = {"cfgs_sha256": K._sha(p), "container": container, "machine": platform.machine(), "system": platform.system(),
           "python": platform.python_version()}
    (out / "calibration.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")


def install_checked_salt(root: str, out, salt_sha256: str) -> None:
    """Install the draw's identity salt for this process (and its workers) and check its hash. Every stage needs it:
    under churn new identities appear mid-episode, and their draws depend on the salt (smoke run 2026-11-19)."""
    import revision_v2 as R
    p = R.install_salt(root, Path(out))
    if K._sha(p) is None or R._sha(bytes.fromhex(p.read_text().strip())) != salt_sha256:
        _refuse("the installed identity salt is not the draw's salt")


def _context(a):
    """The draw root, salt, configurations, container and parameters, with the configuration reuse check."""
    from sim.records import cfg_from_dict
    out = Path(a.out); inst = json.loads((out / "instances.json").read_text())
    cal = json.loads((out / "calibration.json").read_text())
    check_cfg_reuse(out / "cfgs.json", cal)
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads((out / "cfgs.json").read_text()).items()}
    install_checked_salt(inst["root"], out, inst["salt_sha256"])
    return SimpleNamespace(root=inst["root"], salt=inst["salt_sha256"], cfgs=cfgs, container=cal["container"],
                           params=json.loads(Path(a.params).read_text()), confirmatory=inst["confirmatory"])


def menu_rules(ctx: str, family: str) -> list[str]:
    """The registered menu's rules for one context and family (the frozen manifest at cuts 3, H4 loaded): the bank rules,
    which include the targets."""
    import revision_v2 as R
    from sim import manifest_v2 as MAN
    from reset_followup_v2 import CUTS, H4_EXCLUDED
    return MAN.bank_rules(R.manifest_ctx(ctx), family, CUTS, H4_EXCLUDED)


def menu_jobs(c, smoke: bool) -> list[dict]:
    import revision_v2 as R
    jobs = []
    for m in MARKETS:
        mkt = R.market(m, c.root, 0.2, smoke=smoke, cfg=c.cfgs[m], salt_sha256=c.salt)
        for fam in FAMS:
            jobs += [R.job(mkt, r, fam, "profit", smoke=smoke, params=c.params) for r in menu_rules(mkt["context"], fam)]
    if missing := [(m, t) for m in MARKETS for t in TARGETS if not any(j["mkt"]["label"] == m and j["rule"] == t for j in jobs)]:
        _refuse(f"a target rule is not in the menu: {missing[:3]}")
    return jobs


def stage_menu(a) -> None:
    import revision_v2 as R
    from reset_followup_v2 import CUTS, H4_EXCLUDED
    c = _context(a); out = Path(a.out) / "menu"; out.mkdir(parents=True, exist_ok=True); R.install_salt(c.root, out)
    jobs = menu_jobs(c, a.smoke)
    lim = None if a.smoke else _memory_limit()
    w = admit_workers(a.workers_search, lim, a.peak_search)
    for fam in FAMS:                                    # D2+H3 first: the X7-SC search embeds the D2+H3 winner
        R._pool("search", [j for j in jobs if j["family"] == fam], out, w, CUTS, H4_EXCLUDED, jobs)
    for item in [i for i in R._menu_items(jobs) if i["rule"] in TARGETS]:
        R._run_reference(item, out, CUTS, H4_EXCLUDED, jobs)
    _menu_freeze(out, jobs)


def _menu_freeze(out: Path, jobs: list[dict]) -> None:
    """A follow-up freeze per context: every search record and the targets' references, each validated (stage,
    provenance, dependency set and hashes), so the reset driver's input and pairing checks can read this directory."""
    import revision_v2 as R
    from reset_followup_v2 import CUTS, DEVIATIONS, H4_EXCLUDED
    from runnerup_v2 import _validate_new
    from sim.records_v2 import read, write
    for ctx in sorted({j["context"] for j in jobs}):
        cj = [j for j in jobs if j["context"] == ctx]
        recs = {j["id"]: _validate_new(out, j["id"], "search", j["provenance"], jobs) for j in cj}
        for t in TARGETS:
            rid = f"reference/{ctx}/{t}"
            recs[rid] = _validate_new(out, rid, "reference", R.reference_provenance(next(j for j in cj if j["rule"] == t)), jobs)
        body = {"stage": "freeze", "context": ctx, "followup": True, "deviations": list(DEVIATIONS), "cuts": CUTS,
                "h4_excluded": H4_EXCLUDED, "records": recs}
        p = R.path_of(out, f"freeze/{ctx}"); old = read(p)
        if old is not None and old != body:
            _refuse(f"{p} exists with other records")
        if old is None:
            write(p, body)


def stage_cthr(a) -> None:
    import revision_v2 as R
    import runnerup_v2 as U
    from reset_followup_v2 import copy_inputs
    c = _context(a); src = Path(a.out) / "menu"; out = Path(a.out) / "cthr"; out.mkdir(parents=True, exist_ok=True)
    R.install_salt(c.root, out)
    jobs = U.build_jobs(c.root, c.cfgs, U.runner_up_params(c.params), c.salt, MARKETS, a.smoke)
    U.check_spec(jobs)
    copy_inputs(src, out, U.bank_inputs(src, [j["context"] for j in jobs]))
    w = admit_workers(a.workers_search, None if a.smoke else _memory_limit(), a.peak_search)
    U.run_searches(jobs, out, w); U.reference_stage(jobs, out, src); U.prefreeze(out, jobs, src)


def _memory_limit():
    import churn_v2
    return churn_v2.memory_limit()


def _rate_args(a, src: Path) -> SimpleNamespace:
    return SimpleNamespace(src=str(src), smoke=a.smoke, workers_search=a.workers_search, workers_eval=a.workers_eval,
                           stop_usd=a.stop_usd, usd_per_hour=a.usd_per_hour, prior_usd=a.prior_usd)


def rate_jobs(c, rules_kind: str, p: float, smoke: bool) -> list[dict]:
    """The evaluation jobs of one branch (targets in menu/, or C-thr in cthr/) at one rate; p = 0 jobs are ordinary jobs
    (their search record is the menu record), p > 0 jobs carry churn."""
    import churn_v2
    import revision_v2 as R
    import runnerup_v2 as U
    params = U.runner_up_params(c.params) if rules_kind == "cthr" else c.params
    rules = ("C*",) if rules_kind == "cthr" else TARGETS
    if p == 0:
        jobs = []
        for m in MARKETS:
            mkt = R.market(m, c.root, 0.2, smoke=smoke, cfg=c.cfgs[m], salt_sha256=c.salt)
            jobs += [R.job(mkt, r, "D2+H3", "profit", smoke=smoke, params=params) for r in rules]
        return jobs
    return churn_v2.build_jobs(c.root, c.cfgs, params, c.salt, p, MARKETS, rules, smoke)


def stage_rates(a) -> None:
    import churn_v2
    import revision_v2 as R
    c = _context(a); churn_v2.install()
    rates = {"p0": (0.0,), "churn": RATES, "all": (0.0,) + RATES}[a.rates]   # p0, then gate0, then churn (plan section 5)
    for kind in ("menu", "cthr"):
        src = Path(a.out) / kind
        for p in rates:
            out = Path(a.out) / f"{kind}-p{p:g}"; out.mkdir(parents=True, exist_ok=True); R.install_salt(c.root, out)
            steps = ("inputs", "freeze", "evaluate", "doubling", "diagnostics", "inventory") if p == 0 else \
                    ("inputs", "search", "freeze", "evaluate", "doubling", "diagnostics", "inventory")
            churn_v2._run_rate(out, rate_jobs(c, kind, p, a.smoke), steps, _rate_args(a, src), c.salt, c.container, p, a.started)


def stage_gate0(a) -> None:
    """The churn-zero gate: fresh0 R3 at p = 0 through the churn path (search, evaluation, doubling) against the ordinary
    menu search and its p = 0 evaluation and doubling, required bit-identical (run after stage rates' p = 0 branch)."""
    import churn_v2
    import revision_v2 as R
    c = _context(a); churn_v2.install()
    out = Path(a.out) / "gate0"; out.mkdir(parents=True, exist_ok=True); R.install_salt(c.root, out)
    jobs = churn_v2.build_jobs(c.root, c.cfgs, c.params, c.salt, 0.0, ("fresh0",), ("F111",), a.smoke)
    churn_v2._run_rate(out, jobs, ("inputs", "search", "freeze", "evaluate", "doubling"), _rate_args(a, Path(a.out) / "menu"),
                       c.salt, c.container, 0.0, a.started)
    ref = Path(a.out) / "menu-p0"
    rid = R.cell_id("fresh0@rho0.2", "F111", "D2+H3", "profit")
    g = churn_v2.gate_compare(ref, out, rid, jobs[0]["id"], require_identical=not a.smoke)
    if not g["gate_ok"] and not a.smoke:
        _refuse("the churn-zero gate failed")


def _jobs_by_dir(c, smoke: bool) -> dict:
    return {(kind, p): rate_jobs(c, kind, p, smoke) for kind in ("menu", "cthr") for p in (0.0,) + RATES}


def stage_continue(a) -> None:
    """The ordered continuation queue (plan section 4); cost admission per round through the frozen CostStop."""
    import churn_v2
    import rep_collect as C
    from convergence_v2 import worker_cost_args
    from guards import CostStop
    c = _context(a); churn_v2.install()
    queue = continuation_queue(C.flagged_cells(Path(a.out), _jobs_by_dir(c, a.smoke)))
    cost = None if a.smoke else worker_cost_args(CostStop(a.stop_usd, a.usd_per_hour, a.started, prior_usd=a.prior_usd))
    w = admit_workers(a.workers_cont, None if a.smoke else _memory_limit(), a.peak_cont)
    res = C.run_queue(queue, Path(a.out), w, cost)
    print(json.dumps({"stage": "continue", "queued": len(queue), **{k: v for k, v in res.items()}}), flush=True)
    return res["exit"]                                   # Run B's codes: 4 round-1 mismatch, 5 lost worker, 6 cell error


def root_inventory(out) -> dict:
    """One inventory at the output root, written last: every file with its hash except inventory files and *.lock, *.tmp
    (the launcher verifies every pulled directory against it, and that no file is outside it)."""
    import hashlib
    from sim.records_v2 import write
    out = Path(out)
    recs = {str(q.relative_to(out)): hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(out.rglob("*"))
            if q.is_file() and q.name != "inventory.json" and not q.name.endswith((".lock", ".tmp"))}
    inv = {"stage": "inventory", "records": recs}
    write(out / "inventory.json", inv)
    return inv


def stage_inventory(a) -> None:
    root_inventory(a.out)


def stage_analyse(a) -> None:
    """The committed analysis on the collected records, for both winner sets (plan sections 2 and 3)."""
    import rep_collect as C
    import replication_analysis as RA
    c = _context(a); col = C.collect(Path(a.out), _jobs_by_dir(c, a.smoke))
    res = {"confirmatory": c.confirmatory, "counts": col["counts"], "round1_mismatch": col["round1_mismatch"]}
    for name in ("primary", "frozen"):
        g = col[name]
        if g is None:
            res[name] = "not available (round-1 mismatch)"; continue
        pc = RA.paired_changes(g); cr = RA.criteria(pc)
        res[name] = {"paired_changes": pc, "criteria": cr, "expectations": RA.expectations(cr, col["audit"]),
                     "pooled": {p: {x: RA.pooled_paired(g[p], comp, resamples=a.resamples) for x, comp in RA.CONTRASTS.items()
                                    if all(comp in g[p][m] for m in g[p])} for p in g}}
    (Path(a.out) / "analysis.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")


STAGES = {"instances": stage_instances, "calibrate": stage_calibrate, "menu": stage_menu, "cthr": stage_cthr,
          "gate0": stage_gate0, "rates": stage_rates, "continue": stage_continue, "analyse": stage_analyse,
          "inventory": stage_inventory}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stage", required=True, choices=tuple(STAGES)); ap.add_argument("--out", required=True)
    ap.add_argument("--manifest", required=True); ap.add_argument("--draw"); ap.add_argument("--proof")
    ap.add_argument("--protocol", default=None, help="smoke runs only: the committed bytes of an earlier draw")
    ap.add_argument("--published-height", dest="published_height", type=int, default=None)
    ap.add_argument("--params", default=str(ROOT / "experiments/v2/params.json"))
    ap.add_argument("--workers-search", dest="workers_search", type=int, default=16)
    ap.add_argument("--workers-eval", dest="workers_eval", type=int, default=9)
    ap.add_argument("--peak-search", dest="peak_search", type=float, default=1.2e9, help="measured search peak, bytes")
    ap.add_argument("--workers-cont", dest="workers_cont", type=int, default=5)
    ap.add_argument("--peak-cont", dest="peak_cont", type=float, default=3.54e9, help="Run B's measured continuation peak, bytes")
    ap.add_argument("--resamples", type=int, default=9999)
    ap.add_argument("--started", type=float, default=None); ap.add_argument("--stop-usd", dest="stop_usd", type=float, default=None)
    ap.add_argument("--usd-per-hour", dest="usd_per_hour", type=float, default=None)
    ap.add_argument("--prior-usd", dest="prior_usd", type=float, default=0.0)
    ap.add_argument("--rates", choices=("p0", "churn", "all"), default="all", help="stage rates: p = 0 only, churn only, or both")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(argv)
    _require(a)
    if a.smoke and a.stop_usd is None:
        a.stop_usd = 1e9
    if not a.smoke and a.stage in ("menu", "cthr", "gate0", "rates", "continue") and (a.started is None or not a.usd_per_hour or a.stop_usd is None):
        _refuse("a paid stage needs --started, --usd-per-hour and --stop-usd")
    return int(STAGES[a.stage](a) or 0)


if __name__ == "__main__":
    sys.exit(main())
