"""Amendment 2 (task A4): the five registered falsification tests of the proposed rule (amendment 1, falsification
block; made precise in docs/amendments/2026-10-17-amendment-2.md), run from the allow-listed module, the dev seeds, and
the proposed rule's records in the amended sweep directory. Writes report.json and the falsification note; exit 1 on
any kill. No gate is weakened and no registered choice changed to obtain a pass."""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

H3_CORNER = {"u0": 1.0, "m0": 1.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "x": 1, "clip": 0}     # the literal full-cheat corner with replacement
EFF_MIN, GAIN_MAX, REDUCTION_MIN, DOUBLING_TOL, REDUCTION_LEVEL = 0.90, 0.30, 0.10, 0.005, 0.9875


# ----------------------------------------------------------------------------------------------------------------- helpers
def f2_corner_rounds(res, k_by_round) -> list:
    """Per round in which exactly one replacement identity (generation >= 1) served jobs: its served count s, the round's
    audit count k (after the served-jobs and audits_left caps: the audits the rule made), its audited count, whether the
    allowance permitted full coverage (k >= s), and the pass verdict (None when not applicable)."""
    ks = [len(r.audits) for r in res.history] if k_by_round is None else [int(k) for k in k_by_round]
    rows = []
    for t, rec in enumerate(res.history):
        served: dict[int, int] = {}
        for j, i in rec.assignment.items():
            if res.identity_generation[i] >= 1:
                served[i] = served.get(i, 0) + 1
        if len(served) != 1:
            continue
        (i, s), = served.items()
        audited = sum(1 for a in rec.audits if a.provider == i)
        applicable = ks[t] >= s
        rows.append({"round": t, "identity": int(i), "served": int(s), "k": int(ks[t]), "audited": int(audited), "applicable": bool(applicable),
                     "pass": (audited == s) if applicable else None})
    return rows


def f3_expected_failures_and_bans(res, tol: float, sigma: float, L: int | None = None, capacity=None) -> dict:
    """All-honest expectations under independent Gaussian job noise: p = Phi(-tol / sigma) per audited job; a ban event
    is one identity-round with any failed audit, expected 1 - (1 - p)^a with a the identity's audits that round; lost
    rounds are the actual banned rounds clipped at the episode end (expected with L when given); lost capacity sums the
    identity's capacity over those rounds when `capacity` (per identity) is given."""
    p = float(norm.cdf(-tol / sigma)); T = len(res.history)
    audited = observed_failures = observed_bans = 0; expected_bans = expected_lost = 0.0; observed_lost = 0; observed_lost_cap = 0.0
    for t, rec in enumerate(res.history):
        per_identity: dict[int, int] = {}; failed_identities = set()
        for a in rec.audits:
            audited += 1; per_identity[a.provider] = per_identity.get(a.provider, 0) + 1
            if a.failed:
                observed_failures += 1; failed_identities.add(a.provider)
        observed_bans += len(failed_identities)
        remaining = T - t - 1
        for i, a in per_identity.items():
            pb = 1.0 - (1.0 - p) ** a
            expected_bans += pb
            if L is not None:
                expected_lost += pb * min(int(L), remaining)
        for i, rounds in rec.consequences.bans.items():
            lost = min(int(rounds), remaining); observed_lost += lost
            if capacity is not None:
                observed_lost_cap += lost * float(capacity[i])
    out = {"p": p, "audited": audited, "observed_failures": observed_failures, "expected_failures": p * audited,
           "observed_ban_events": observed_bans, "expected_ban_events": expected_bans, "observed_lost_rounds": observed_lost}
    if L is not None:
        out["expected_lost_rounds"] = expected_lost
    if capacity is not None:
        out["observed_lost_capacity"] = observed_lost_cap
    return out


def _paired(rows_a: list, rows_b: list, key: str) -> np.ndarray:
    a = {int(r["seed"]): float(r[key]) for r in rows_a}; b = {int(r["seed"]): float(r[key]) for r in rows_b}
    if sorted(a) != sorted(b) or len(a) != len(rows_a) or len(b) != len(rows_b):
        raise ValueError("the rows are not paired by seed")
    return np.array([a[s] - b[s] for s in sorted(a)])


def _se(x: np.ndarray) -> float:
    return float(x.std(ddof=1) / math.sqrt(x.size)) if x.size > 1 else float("nan")


def f4_cell_gate(rows_proposed: list, rows_b3: list) -> dict:
    """One D2 cell: kill when the proposed rule's mean dev-val gain exceeds 0.30 or its mean efficiency falls below 0.90;
    the comparative claim fails when B3's paired gain is lower, or its efficiency higher, by more than two standard errors
    of the paired per-seed difference."""
    g = np.array([float(r["gain"]) for r in rows_proposed]); e = np.array([float(r["eff_attack"]) for r in rows_proposed])
    dg = _paired(rows_b3, rows_proposed, "gain"); de = _paired(rows_b3, rows_proposed, "eff_attack")
    mean_gain, mean_eff = float(g.mean()), float(e.mean())
    kill = bool(mean_gain > GAIN_MAX or mean_eff < EFF_MIN)
    gain_worse = bool(dg.mean() < -2 * _se(dg)); eff_worse = bool(de.mean() > 2 * _se(de))
    return {"n": int(g.size), "mean_gain": mean_gain, "mean_eff": mean_eff, "kill": kill,
            "diff_gain_mean": float(dg.mean()), "diff_gain_se": _se(dg), "diff_eff_mean": float(de.mean()), "diff_eff_se": _se(de),
            "b3_gain_lower": gain_worse, "b3_eff_higher": eff_worse, "comparative_fails": bool(gain_worse or eff_worse)}


def f5_gain_reduction(rows_h3: dict, checks_h3: dict | None, settings: dict) -> dict:
    """The H3 cell: paired dev-val gain reductions against B2 and B3 must have lower 98.75 percent studentized bounds of
    at least 0.10, and the H3 doubling check must report |delta_gain| < 0.005. A missing doubling record is refused."""
    from sim.intervals import bound
    if not checks_h3 or "doubling" not in checks_h3:
        raise ValueError("F5 needs the proposed rule's H3 doubling record (the checks stage on the h3 control cell)")
    reductions = {}
    for b in ("B2", "B3"):
        x = _paired(rows_h3[b], rows_h3["proposed"], "gain")
        bd = bound("studentized", x, "lower", REDUCTION_LEVEL, settings)
        reductions[b] = {"n": int(x.size), "mean": float(x.mean()), "lower_bound": float(bd.value), "level": REDUCTION_LEVEL, "method": bd.method,
                         "degenerate": bool(bd.degenerate), "pass": bool(bd.value >= REDUCTION_MIN)}
    delta = float(checks_h3["doubling"]["delta_gain"]); doubling_pass = bool(abs(delta) < DOUBLING_TOL)
    ok = doubling_pass and all(v["pass"] for v in reductions.values())
    return {"reductions": reductions, "delta_gain": delta, "doubling_pass": doubling_pass, "pass": ok, "kill": not ok}


# ----------------------------------------------------------------------------------------------------------------- harness
def _read(path: Path) -> dict:
    return json.loads(path.read_text())


RULES = ("B1", "B2", "B3", "proposed")
SECTIONS = ("development", "rho_sweep", "h3", "ablation")            # the full cells of the documented sweep; all_deviators is a stage with one aggregate file


def required_inventory(lk, budget) -> dict:
    """The complete output of the documented sweep (`--sections development,rho_sweep,h3,all_deviators,ablation --rules B1,B2,B3,proposed`,
    every stage): a search, reference, and evaluate record per full cell, a bank record per bank-family cell, a checks
    record per control (under its shared name), the bank document, and the all-deviators aggregate."""
    from sim.manifest import checks_record_name, enumerate_manifest
    cells = enumerate_manifest(lk, list(RULES), budget=budget)
    full = [c for c in cells if c.kind == "full_cell" and c.section in SECTIONS and c.rule in RULES]
    names = [c.name for c in full]
    return {"search": names, "reference": list(names), "evaluate": list(names), "bank": [c.name for c in full if c.family in ("D1", "D2", "D2+H3")],
            "checks": [checks_record_name(c) for c in cells if c.section == "controls" and c.rule in RULES], "files": ["bank.json", "all_deviators.json"]}


def validate_sweep(sweep: Path, lk: dict, cal_path, params: dict, quick: bool) -> dict:
    """Nothing is read for a verdict before the whole inventory exists and every record is bound: each record is checked
    by the sweep's own check_record against the job rebuilt from the lock (parameters, configuration, settings hash, budget,
    smoke flag, salt, namespace, enforcer), the bank document is loaded with its sources verified, every bank-family
    reference, evaluate, and checks record carries that bank's hash, every evaluate record holds exactly the dev-val seeds,
    and the all-deviators aggregate covers the four rules."""
    from scripts.sweep import SMOKE_BUDGET, check_record, job_for, load_bank_doc, train_val
    from sim.calibrate import load_calibration
    from sim.locked import market_config_from_locked
    from sim.manifest import checks_record_name, enumerate_manifest
    from sim.schedule import budget_from_locked
    sweep = Path(sweep); budget = SMOKE_BUDGET if quick else budget_from_locked(lk)
    cal = load_calibration(cal_path); base = market_config_from_locked(lk)
    inv = required_inventory(lk, budget); problems = []
    for stage, names in inv.items():
        for n in names:
            if not (sweep / (n if stage == "files" else f"{stage}/{n}.json")).exists():
                problems.append(f"missing {n if stage == 'files' else f'{stage}/{n}.json'}")
    if problems:
        return {"problems": problems, "bank": None, "evaluate": {}, "checks": {}}
    try:
        doc = load_bank_doc(sweep)
    except SystemExit as e:
        return {"problems": [f"bank.json: {e}"], "bank": None, "evaluate": {}, "checks": {}}
    cells = {c.name: c for c in enumerate_manifest(lk, list(RULES), budget=budget)}

    def job(c):
        enf = {"rule": "B2", "params": dict(params["B2"])} if c.section == "ablation" else None
        return job_for(c, lk, cal, base, dict(params[c.rule]), budget, quick, enforcer=enf)

    def checked(stage, name, j):
        rec = _read(sweep / stage / f"{name}.json")
        try:
            check_record(j, rec)
        except SystemExit as e:
            problems.append(f"{stage}/{name}: {e}"); return None
        if stage != "search" and j["spec"]["family"] in ("D1", "D2", "D2+H3") and rec.get("bank_hash") != doc["bank_hash"]:   # search precedes the bank
            problems.append(f"{stage}/{name}: record belongs to another bank than bank.json (bank_hash {rec.get('bank_hash')!r})"); return None
        return rec
    evaluate, checks = {}, {}
    for name in inv["evaluate"]:
        c = cells[name]; j = job(c)
        checked("search", name, j); checked("reference", name, j)
        rec = checked("evaluate", name, j)
        if rec is not None:
            want = [int(s) for s in train_val(j)[1]]
            if [int(r["seed"]) for r in rec.get("rows", [])] != want:
                problems.append(f"evaluate/{name}: rows do not hold exactly the dev-val seeds {want}")
            elif not all(math.isfinite(float(r["gain"])) and math.isfinite(float(r["eff_attack"])) for r in rec["rows"]):
                problems.append(f"evaluate/{name}: a row is not finite")
            else:
                evaluate[name] = rec
    for name in inv["checks"]:
        rec = checked("checks", name, job(cells[name]))
        if rec is not None:
            if not isinstance(rec.get("doubling"), dict) or "delta_gain" not in rec["doubling"]:
                problems.append(f"checks/{name}: no doubling result")
            else:
                checks[name] = rec
    ad = _read(sweep / "all_deviators.json")
    if {r.get("spec", {}).get("rule") for r in ad} < set(RULES):
        problems.append(f"all_deviators.json: rules {sorted(r.get('spec', {}).get('rule') for r in ad)} do not cover {list(RULES)}")
    return {"problems": problems, "bank": doc, "evaluate": evaluate, "checks": checks}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibration", required=True); ap.add_argument("--tuned-dir", dest="tuned_dir", required=True)
    ap.add_argument("--sweep-out", dest="sweep_out", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--params", default=str(ROOT / "experiments" / "proposed.yaml"))
    ap.add_argument("--quick", action="store_true", help="tiny seed counts for a smoke run; never for the freeze (no f5_bank is recorded)")
    a = ap.parse_args()
    os.environ["TOUCHSTONE_PROPOSED_PARAMS"] = str(Path(a.params).resolve())
    from scripts.sweep import SMOKE_BUDGET, load_params
    from sim.manifest import checks_record_name, enumerate_manifest
    from sim.calibrate import cell_config, load_calibration
    from sim.claimcheck import check_proposed_module_isolated
    from sim.locked import load_locked, market_config_from_locked, seeds, settings_hash
    from sim.market import run_episode
    from sim.policies.families import D2
    from sim.policies.honest import HonestMax
    from sim.policies.identity import h3_family
    from sim.positions import positions
    from sim.registry import PROPOSED_MODULE, make_rule, proposed_params
    from sim.schedule import budget_from_locked
    lk = load_locked(); cal = load_calibration(a.calibration); base = market_config_from_locked(lk)
    budget = SMOKE_BUDGET if a.quick else budget_from_locked(lk)
    tuned = None if a.quick else Path(a.tuned_dir)
    params_by_rule = {r: load_params(r, tuned, a.quick, cal.market_key, settings_hash(lk), cal.seeds) for r in RULES}   # quick: the smoke defaults the smoke sweep used
    params = dict(params_by_rule["proposed"])
    sweep = Path(a.sweep_out); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    # the complete inventory and every record's binding first: nothing is read for a verdict before that
    v = validate_sweep(sweep, lk, a.calibration, params_by_rule, a.quick)
    if v["problems"]:
        raise SystemExit("the sweep directory is not the complete, bound output of the documented run:\n  " + "\n  ".join(v["problems"]))
    report: dict = {}
    bh, rho0 = float(lk["beta_headline"]), float(lk["rho"]["default"])
    cfg = cell_config(base, cal, rho=rho0, beta=bh); focal = positions(cfg)["median"]
    train = seeds(lk, "dev_train"); val = seeds(lk, "dev_val")
    if a.quick:
        train, val = train[:1], val[:2]

    # F1: the contract fixtures and the isolated module check
    t = subprocess.run([sys.executable, "-m", "pytest", "tests/test_proposed.py", "-q", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True,
                       env={**os.environ, "OMP_NUM_THREADS": "1"})
    tail = (t.stdout + t.stderr).strip().splitlines()[-1] if (t.stdout + t.stderr).strip() else ""
    fixtures_pass = t.returncode == 0 and " passed" in tail and "skipped" not in tail.split(",")[0]
    module_problems = check_proposed_module_isolated(PROPOSED_MODULE, ROOT, params=params)
    report["F1"] = {"pass": bool(fixtures_pass and not module_problems), "kill": not bool(fixtures_pass and not module_problems),
                    "figures": {"pytest": tail, "module_check": [str(p) for p in module_problems]}}

    # F2: the H3 full-cheat corner under both targeting variants, the 5 dev-train seeds
    fam = h3_family(D2); f2 = {}
    for variant in ("T1", "T2"):
        p = dict(params, targeting=variant); per_seed = []
        for s in train:
            pols = [HonestMax() for _ in range(cfg.N)]; pols[focal] = fam.make(dict(H3_CORNER))
            res = run_episode(cfg, make_rule("proposed", p), pols, int(s))
            rows = f2_corner_rounds(res, None)
            per_seed.append({"seed": int(s), "profit": float(res.profit[focal]), "rows": rows,
                             "coverage_pass": all(r["pass"] for r in rows if r["applicable"]), "applicable_rounds": sum(r["applicable"] for r in rows),
                             "replacements": int(sum(1 for g in res.identity_generation if g >= 1))})
        ok = all(r["coverage_pass"] and r["profit"] <= 0.0 for r in per_seed)
        f2[variant] = {"pass": ok, "per_seed": per_seed}
    f2_pass = all(v["pass"] for v in f2.values())
    report["F2"] = {"pass": f2_pass, "kill": not f2_pass, "figures": f2}

    # F3: all-honest on the dev-val seeds
    effs, agg = [], {"audited": 0, "observed_failures": 0, "expected_failures": 0.0, "observed_ban_events": 0, "expected_ban_events": 0.0,
                     "observed_lost_rounds": 0, "expected_lost_rounds": 0.0, "observed_lost_capacity": 0.0}
    rule0 = make_rule("proposed", params); tol, L = float(rule0.tol), int(rule0.L)
    for s in val:
        res = run_episode(cfg, make_rule("proposed", params), [HonestMax() for _ in range(cfg.N)], int(s))
        effs.append((res.W + res.audit_cost) / res.sstar)
        cap = np.array([cfg.providers[e].k for e in res.entity_of], dtype=float)
        d = f3_expected_failures_and_bans(res, tol, float(cfg.sigma), L=L, capacity=cap)
        for k in agg:
            agg[k] += d[k]
    eff_mean = float(np.mean(effs))
    report["F3"] = {"pass": eff_mean >= EFF_MIN, "kill": eff_mean < EFF_MIN,
                    "figures": {"n": len(val), "mean_gross_efficiency": eff_mean, "forecast": 0.97, "p": float(norm.cdf(-tol / cfg.sigma)), **agg}}

    # F4: the proposed rule's post-lock D2 cells at the three positions, against B3's paired rows; D1 reported
    f4 = {"D2": {}, "D1": {}}
    for pos in lk["positions"]:
        rp = v["evaluate"][f"proposed_D2_beta{bh}_rho{rho0}_{pos}_development"]["rows"]
        rb = v["evaluate"][f"B3_D2_beta{bh}_rho{rho0}_{pos}_development"]["rows"]
        f4["D2"][pos] = f4_cell_gate(rp, rb)
        r1 = v["evaluate"][f"proposed_D1_beta{bh}_rho{rho0}_{pos}_development"]["rows"]
        f4["D1"][pos] = {"n": len(r1), "mean_gain": float(np.mean([r["gain"] for r in r1])), "mean_eff": float(np.mean([r["eff_attack"] for r in r1]))}
    kill4 = any(v["kill"] for v in f4["D2"].values()); comp = any(v["comparative_fails"] for v in f4["D2"].values())
    report["F4"] = {"pass": not kill4 and not comp, "kill": kill4, "comparative_claim_fails": comp, "figures": f4}

    # F5: the H3 cell against B2 and B3, the doubling check, and the bank identity
    rows_h3 = {r: v["evaluate"][f"{r}_D2+H3_beta{bh}_rho{rho0}_median_h3"]["rows"] for r in ("proposed", "B2", "B3")}
    h3_control = next(c for c in enumerate_manifest(lk, list(RULES), budget=budget) if c.section == "controls" and c.rule == "proposed" and c.family == "D2+H3")
    checks = v["checks"][checks_record_name(h3_control)]
    f5 = f5_gain_reduction(rows_h3, checks, dict(lk["intervals"]))
    bank_doc = v["bank"]                                                   # loaded with its sources verified; every H3 record above carries its hash
    f5_bank = {"bank_hash": bank_doc["bank_hash"], "sources_sha256": hashlib.sha256(json.dumps(bank_doc["sources"], sort_keys=True).encode()).hexdigest(),
               "embeddings": bank_doc["embeddings"]}
    f5["f5_bank"] = f5_bank
    report["F5"] = {"pass": f5["pass"], "kill": f5["kill"], "figures": f5}
    if not a.quick:                       # the bank F5 used, recorded into the allow-listed file the freeze tag commits
        pdoc = yaml.safe_load(Path(a.params).read_text()); pdoc["f5_bank"] = f5_bank
        Path(a.params).write_text(yaml.safe_dump(pdoc, sort_keys=False))

    (out / "report.json").write_text(json.dumps(report, indent=1, default=float) + "\n")
    note = _render_note(report, params, a)
    note_path = (ROOT / "docs" / "amendments" / f"falsification-{_dt.date.today().isoformat()}.md") if not a.quick else out / "falsification.md"
    note_path.parent.mkdir(parents=True, exist_ok=True); note_path.write_text(note)
    kills = [k for k, v in report.items() if v["kill"]]
    print(json.dumps({k: {"pass": v["pass"], "kill": v["kill"]} for k, v in report.items()}))
    if kills:
        raise SystemExit(f"KILL: {', '.join(kills)} (see {out / 'report.json'})")


def _render_note(report: dict, params: dict, a) -> str:
    lines = [f"# Falsification record of the proposed rule ({_dt.date.today().isoformat()})", "",
             f"Parameters: `{json.dumps(params, sort_keys=True)}`. Sweep records: `{a.sweep_out}`. Quick mode: {bool(a.quick)}.", ""]
    for k in ("F1", "F2", "F3", "F4", "F5"):
        v = report[k]; lines.append(f"## {k}: {'PASS' if v['pass'] else 'KILL' if v['kill'] else 'FAIL (no kill)'}"); lines.append("")
        fig = v["figures"]
        if k == "F2":
            for variant, d in fig.items():
                lines.append(f"- {variant}: {'pass' if d['pass'] else 'fail'}; per seed (profit, applicable rounds, covered): " +
                             ", ".join(f"{s['seed']}: ({s['profit']:.4f}, {s['applicable_rounds']}, {s['coverage_pass']})" for s in d["per_seed"]))
        elif k == "F4":
            for fam, cells in fig.items():
                for pos, d in cells.items():
                    extra = f", B3 - R* gain {d['diff_gain_mean']:+.4f} (se {d['diff_gain_se']:.4f}), eff {d['diff_eff_mean']:+.4f} (se {d['diff_eff_se']:.4f}), comparative fails: {d['comparative_fails']}" if fam == "D2" else ""
                    lines.append(f"- {fam} {pos}: mean gain {d['mean_gain']:.4f}, mean efficiency {d['mean_eff']:.4f}{extra}")
        elif k == "F5":
            for b, d in fig["reductions"].items():
                lines.append(f"- reduction against {b}: mean {d['mean']:.4f}, lower {d['level']} {d['method']} bound {d['lower_bound']:.4f} (needs {REDUCTION_MIN}): {'pass' if d['pass'] else 'fail'}")
            lines.append(f"- H3 doubling delta_gain {fig['delta_gain']:+.5f} (needs |delta| < {DOUBLING_TOL}): {'pass' if fig['doubling_pass'] else 'fail'}")
            lines.append(f"- f5_bank: `{json.dumps(fig['f5_bank'])}`")
        else:
            lines.append("```json"); lines.append(json.dumps(fig, indent=1, default=float)); lines.append("```")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
