"""Evaluate the claim predicate (spec 8). Confirmatory mode verifies the lock and freeze tags, the proposed module, the
coverage report, every record, and the H1 summary before reading a number (spec 6); --verify-only stops after the
tree, module, and report checks. Synthetic mode (--synthetic, CSV inputs) runs the predicate alone for tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.sweep import read_dir  # noqa: E402
from sim.amendment import LIMITATION, REGISTRATION_FIELDS, load_amendment  # noqa: E402
from sim.claimcheck import (INCONCLUSIVE, check_proposed_module_isolated, evaluate_amendment, evaluate_claim, verdict_json, verify_amendment_report, verify_coverage_report,  # noqa: E402
                            verify_describe_record, verify_freeze, verify_h3_records,
                            verify_h1_summary, verify_lock, verify_records)
from sim.coverage import load_report  # noqa: E402
from sim.locked import load_locked, settings_hash  # noqa: E402
from sim.registry import PROPOSED_MODULE, SEALED_DIR, make_rule, proposed_params  # noqa: E402
from sim.sealed import demoted_cells, effective_path, final_eval_seeds  # noqa: E402


def h2_from_sweep(sweep_out: Path, locked: dict, jobs: dict) -> tuple[pd.DataFrame, list, dict, list]:
    """The H2 evaluate records and the headline position per rule, recomputed from the checked reference records
    (the dev-train gains), never read from headline.json."""
    from scripts.sweep import check_record
    from sim.positions import headline_position
    recs = read_dir(sweep_out / "evaluate"); rows = []; records = []; problems = []
    for rec in recs.values():
        if rec["spec"]["section"] == "heldout" and rec["spec"]["family"] == "H2":
            records.append(rec); rows += rec["rows"]
    refs = read_dir(sweep_out / "reference"); gains: dict = {}
    for rec in refs.values():
        s = rec["spec"]
        if s["section"] == "heldout" and s["family"] == "H2" and float(s["beta"]) == float(locked["beta_headline"]):
            job = jobs.get(s["name"])
            if job is None:
                problems.append(f"{s['name']}: no job for this reference record"); continue
            try:
                check_record(job, rec)
            except SystemExit as e:
                problems.append(f"{s['name']}: {e}"); continue
            gains.setdefault(s["rule"], {})[s["position"]] = float(rec["gain_train"])
    headline = {}
    for rule in sorted({r["spec"]["rule"] for r in records} | {"B2", "B3"}):
        g = gains.get(rule, {})
        if set(g) != set(locked["positions"]):
            problems.append(f"{rule}/H2: checked reference records are missing at some position at the headline beta; the headline position cannot be selected"); continue
        headline[rule] = headline_position(g)
    return pd.DataFrame(rows), records, headline, problems


def h3_from_sweep(sweep_out: Path, locked: dict, jobs: dict) -> tuple[pd.DataFrame, list, list]:
    """The final H3 evaluate records (section heldout, family D2+H3, median position): the public identity-replacement
    stress test on fresh final-evaluation seeds, never a held-out family."""
    recs = read_dir(sweep_out / "evaluate"); rows = []; records = []
    for rec in recs.values():
        s = rec["spec"]
        if s["section"] == "heldout" and s["family"] == "D2+H3" and s["position"] == "median":
            records.append(rec); rows += rec["rows"]
    return pd.DataFrame(rows), records, []


def refuse(problems: list) -> None:
    for p in problems:
        print("REFUSED: " + p, file=sys.stderr)
    sys.exit(2)


def heldout_jobs(locked: dict, calibration: str, tuned_dir: Path) -> dict:
    """The jobs of every held-out cell, rebuilt from the lock exactly as the sweep builds them (the record check compares
    params, cfg, settings hash, budget, smoke flag, and salt hash against these)."""
    from scripts.sweep import job_for, load_params
    from sim.calibrate import load_calibration
    from sim.locked import market_config_from_locked
    from sim.manifest import enumerate_manifest
    from sim.registry import available_rules
    from sim.schedule import budget_from_locked
    import hashlib as _h
    want_cal = (locked.get("calibration") or {}).get("sha256")
    if _h.sha256(Path(calibration).read_bytes()).hexdigest() != want_cal:
        refuse([f"--calibration {calibration}: hash differs from the lock"])
    for r, hsh in (locked.get("tuned") or {}).items():
        p = Path(tuned_dir) / f"tuned_{r}.json"
        if not p.exists() or _h.sha256(p.read_bytes()).hexdigest() != hsh:
            refuse([f"tuned file for {r}: missing or its hash differs from the lock"])
    cal = load_calibration(calibration); base = market_config_from_locked(locked); b = budget_from_locked(locked); rules = available_rules()
    params = {r: load_params(r, tuned_dir, False, cal.market_key, settings_hash(locked), cal.seeds) for r in rules}
    jobs = {}
    for spec in enumerate_manifest(locked, rules, budget=b):
        if spec.section == "heldout":
            jobs[spec.name] = dict(job_for(spec, locked, cal, base, params[spec.rule], b, False), eval_namespace="final_eval")
    return jobs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true"); ap.add_argument("--verify-only", dest="verify_only", action="store_true")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--sweep-out", dest="sweep_out", default=None); ap.add_argument("--h2-rows", dest="h2_rows", default=None)
    ap.add_argument("--h1-dir", dest="h1_dir", default=None); ap.add_argument("--h1-rows", dest="h1_rows", default=None); ap.add_argument("--h1-summary", dest="h1_summary", default=None)
    ap.add_argument("--coverage-report", dest="coverage_report", default=None, help="default: experiments/coverage_report.json under --repo")
    ap.add_argument("--amendment", default=None, help="default: experiments/amendment-2026-10-17.yaml under --repo; absent file = no amendment")
    ap.add_argument("--coverage-ext", dest="coverage_ext", default=None, help="default: experiments/coverage_report_amendment.json under --repo")
    ap.add_argument("--h3-rows", dest="h3_rows", default=None, help="synthetic only: H3 rows CSV")
    ap.add_argument("--proposed", required=True); ap.add_argument("--proposed-describe", dest="proposed_describe", default=None)
    ap.add_argument("--verify-lock", dest="verify_lock", default=None); ap.add_argument("--verify-freeze", dest="verify_freeze", default=None)
    ap.add_argument("--tuned-dir", dest="tuned_dir", default=None); ap.add_argument("--calibration", default=None)
    ap.add_argument("--out", default="results/verdict.json")
    a = ap.parse_args()
    lk = load_locked(); repo = Path(a.repo); problems = []
    a.coverage_report = a.coverage_report or str(repo / "experiments" / "coverage_report.json")   # resolved under --repo, never the caller's cwd
    a.amendment = a.amendment or str(repo / "experiments" / "amendment-2026-10-17.yaml"); a.coverage_ext = a.coverage_ext or str(repo / "experiments" / "coverage_report_amendment.json")
    amend = load_amendment(a.amendment, lk) if Path(a.amendment).exists() else None
    registered = amend is not None and all(amend.get(k) is not None for k in REGISTRATION_FIELDS)
    if not a.synthetic:
        if not a.verify_lock or (not a.verify_only and not a.verify_freeze):
            refuse(["confirmatory mode needs --verify-lock TAG and --verify-freeze TAG (or --verify-only with --verify-lock); pass --synthetic for CSV inputs"])
        problems += verify_lock(repo, a.verify_lock, lk["allow_list"])
        if a.verify_freeze:
            problems += verify_freeze(repo, a.verify_freeze, lk, lk["allow_list"])
        if PROPOSED_MODULE.exists():
            problems += check_proposed_module_isolated(PROPOSED_MODULE, repo, params=proposed_params().get("best_params") if a.verify_freeze else None)
        if Path(a.coverage_report).exists():
            problems += verify_coverage_report(a.coverage_report, lk)
        elif not a.verify_only:
            problems.append(f"coverage report {a.coverage_report} not found")
        if amend is not None:
            if registered:
                problems += verify_amendment_report(a.coverage_ext, amend) if Path(a.coverage_ext).exists() else [f"amendment report {a.coverage_ext} not found"]
            elif not a.verify_only:
                problems.append("amendment not registered: coverage_report_amendment_sha256 and coverage_consequences are null (run scripts/amend.py first)")
        if problems:
            refuse(problems)
        if a.verify_only:
            print("verified: tree, proposed module, coverage report")
            if amend is not None:
                print("amendment report verified" if registered else "amendment: unregistered (draft)")
            return
        if a.h2_rows or a.h1_rows:
            refuse(["CSV inputs are for synthetic tests; pass --synthetic"])
        if not (a.sweep_out and a.calibration and a.tuned_dir and a.proposed_describe):
            refuse(["confirmatory mode needs --sweep-out DIR --calibration PATH --tuned-dir DIR --proposed-describe PATH"])
    h2 = h1 = h3 = None; h1_summary = None; headline = {}; demoted = set()
    if a.sweep_out:
        from sim.rng import load_identity_salt
        if hashlib.sha256(load_identity_salt()).hexdigest() != lk.get("identity_salt_sha256"):
            refuse(["the identity salt in this environment is not the one committed at the lock (export TOUCHSTONE_IDENTITY_SALT from the released sealed/identity_salt.hex)"])
        jobs = heldout_jobs(lk, a.calibration, Path(a.tuned_dir))
        h2, records, headline, hp = h2_from_sweep(Path(a.sweep_out), lk, jobs); problems += hp
        expected = final_eval_seeds(SEALED_DIR)
        problems += verify_records(records, lk, jobs, expected)
        if amend is not None:
            h3, h3_records, hp3 = h3_from_sweep(Path(a.sweep_out), lk, jobs); problems += hp3
            problems += verify_h3_records(h3_records, lk, jobs, expected, a.proposed)
        demoted = demoted_cells(SEALED_DIR)
        if a.proposed_describe and Path(a.proposed_describe).resolve() != (repo / "experiments" / "proposed_describe.yaml").resolve():
            refuse(["--proposed-describe must be the frozen experiments/proposed_describe.yaml (checked against the freeze tag)"])
    elif a.h2_rows:
        h2 = pd.read_csv(a.h2_rows)
    if a.synthetic and a.h3_rows:
        h3 = pd.read_csv(a.h3_rows)
    if a.h1_dir:
        d = Path(a.h1_dir); h1 = pd.read_csv(d / "h1_rows.csv"); h1_summary = json.loads((d / "h1_summary.json").read_text())
        problems += verify_h1_summary(h1_summary, h1, lk, effective_path(SEALED_DIR, "h1_prompt.txt"), final_eval_seeds(SEALED_DIR))
    elif a.h1_rows:
        h1 = pd.read_csv(a.h1_rows); h1_summary = json.loads(Path(a.h1_summary).read_text()) if a.h1_summary else None
    if problems:
        refuse(problems)
    cov = load_report(a.coverage_report)
    rec = yaml.safe_load(Path(a.proposed_describe).read_text()) if a.proposed_describe else None
    if rec is not None and not a.synthetic:
        rule = make_rule("proposed", proposed_params()["best_params"])
        dp = verify_describe_record(rec, rule)
        if dp:
            refuse(dp)
        rec = rule.describe()                                      # the record the actor saw, validated against the vocabulary
    res = evaluate_claim(h2, h1, cov, lk, a.proposed, h1_summary=h1_summary, describe_record=rec, h2_headline=headline, demoted=demoted)
    out = verdict_json(res); out["synthetic"] = bool(a.synthetic)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(json.dumps(out, indent=1, default=float))
    print(("SYNTHETIC " if a.synthetic else "") + f"claim: {res['claim']}   confirmatory families: {res['confirmatory']}")
    for fam, r in res["rule_clause"].items():
        print(f"  rule clause {fam}: {r['status']}  eff {r['eff'].status} ({r['eff'].bound})  gain {r['gain'].status} ({r['gain'].bound})  audit {r['audit']}")
    for B, r in res["baseline_clause"].items():
        print(f"  baseline clause {B}: {r['status']}  " + "  ".join(f"{k} {v.status} ({v.bound})" for k, v in r["pairs"].items()))
    if res["h1_note"]:
        print(f"  H1 note: {res['h1_note']}")
    if amend is not None and (registered or a.synthetic):
        cov_ext = load_report(a.coverage_ext) if Path(a.coverage_ext).exists() else None
        h2_status = (res["rule_clause"].get("H2") or {}).get("status", INCONCLUSIVE)
        am = evaluate_amendment(h3, cov, cov_ext, lk, amend, a.proposed, h2_status, demoted=demoted)
        out["amendment"] = verdict_json(am); Path(a.out).write_text(json.dumps(out, indent=1, default=float))
        print(f"amended claim: {am['amended']}   (H3: public identity-replacement stress test on fresh final-evaluation seeds)")
        print(f"  H2 rule clause gate: {am['h2_rule_status']}   gain_diff sides admitted: {am['admitted']}")
        ab = am.get("absolute") or {}
        if ab:
            print(f"  H3 absolute: {ab['status']}  eff {ab['eff'].status} ({ab['eff'].bound})  gain {ab['gain'].status} ({ab['gain'].bound})  audit {ab['audit']}")
        cp = am.get("comparative") or {}
        for B in amend["clause"]["baselines"]:
            if B in cp:
                print(f"  gain reduction vs {B}: {cp[B].status} ({cp[B].bound})")
        if am.get("reason"):
            print(f"  reason: {am['reason']}")
        print("  " + LIMITATION)


if __name__ == "__main__":
    main()
