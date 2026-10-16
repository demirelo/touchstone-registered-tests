"""Write the lock-time blocks into experiments/locked.yaml (spec 6) after validating their inputs, and print the tag
commands; --check verifies every written value against its file."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sim.locked import settings_hash  # noqa: E402
from sim.rng import load_identity_salt  # noqa: E402

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(a, lk: dict, cal: dict, cal100: dict, cov: dict) -> list:
    problems = []
    if int(cal.get("T", -1)) != int(lk["market"]["T"]):
        problems.append(f"--calibration has T = {cal.get('T')}, the locked market T is {lk['market']['T']}")
    if int(cal100.get("T", -1)) != int(lk["h1"]["T"]):
        problems.append(f"--calibration-t100 has T = {cal100.get('T')}, locked h1.T is {lk['h1']['T']}")
    if cov.get("admission_basis") != "registered" or cov.get("smoke"):
        problems.append("coverage report: not a registered admission (smoke run?)")
    if len(cov.get("selection", [])) != 6:
        problems.append("coverage report: selection is not 6 cells")
    trials = int(lk["intervals"]["joint_trials"])
    for n, attempts in (cov.get("fixture_and_power", {}).get("per_n") or {}).items():
        if any(int(att.get("fixture", {}).get("trials", 0)) != trials for att in attempts):
            problems.append(f"coverage report: the joint fixture at n = {n} did not run {trials} trials")
    if "consequences" not in cov:
        problems.append("coverage report: no consequences")
    for name, v in (("--bundle-hash", a.bundle_hash), ("--salt-hash", a.salt_hash)):
        if v is None or not HEX64.match(v):
            problems.append(f"{name} is required and must be 64 hex characters")
    names = [c.get("name") for c in cov.get("selection", [])]
    if len(set(names)) != len(names) or not all(names):
        problems.append("coverage report: selection names must be present and distinct")
    cons = cov.get("consequences") or {}
    if not {"h1", "parametrized", "final_eval_n"} <= set(cons):
        problems.append("coverage report: consequences incomplete")
    per_n = (cov.get("fixture_and_power") or {}).get("per_n") or {}
    if not {"10", "20"} <= set(per_n) or any(not attempts for attempts in per_n.values()):
        problems.append("coverage report: fixture and power results missing for n = 10 or n = 20")
    cells = cov.get("cells") or {}
    need_n = {"10", "20"} | ({str(cons.get("final_eval_n"))} if cons.get("final_eval_n") else set())
    if set(cells) != set(names) or any(not need_n <= set(r.get("per_n") or {}) for r in cells.values()) or not need_n <= set(per_n):
        problems.append(f"coverage report: every selected cell must have results and gates at n in {sorted(need_n)}")
    fpw = cov.get("fixture_and_power") or {}; checks = fpw.get("threshold_check") or {}
    covs = lk["seeds"]["coverage"]; base_M = int(covs["pool"]); base_R = {str(n): int(r) for n, r in covs["replications"].items()}   # sizes come from the lock, never from the report
    conf = 1.0 - 0.05 / 3.0; levels = ("0.95", "0.9875")
    derived: dict = {}
    from sim.coverage import clopper_pearson_lower as _cp
    for n, attempts in per_n.items():
        ok_n = False
        for i, att in enumerate(attempts):
            fx = att.get("fixture") or {}; pw = att.get("power") or {}; M = int(att.get("M", 0)); chk = checks.get(str(M)) or {}
            expect = [(1, 1), (2, 1), (2, 2)][i] if i < 3 else None
            if (att.get("pool_factor"), att.get("rep_factor")) != expect or int(fx.get("trials", 0)) != trials or int(fx.get("cells", 0)) != 6 or int(fx.get("endpoints_per_cell", 0)) != 8:
                problems.append(f"coverage report: attempt {i} at n = {n} is not the registered attempt order or size")
            if M != base_M * (att.get("pool_factor") or 0) or int(att.get("R", 0)) != base_R.get(str(n), -1) * (att.get("rep_factor") or 0) or int(fx.get("M", -1)) != M or int(fx.get("R", -1)) != int(att.get("R", 0)):
                problems.append(f"coverage report: attempt {i} at n = {n} has an M or R that is not the locked size times the factor")
            fx_ll = _cp(int(fx.get("admitted", 0)), trials, conf) if trials else 0.0
            fx_ok = abs(float(fx.get("lower_limit", -1)) - fx_ll) < 1e-9 and bool(fx.get("pass_")) == (fx_ll >= 0.9)
            pw_keys = {f"{n}|{lv}" for lv in levels}; ck_keys = pw_keys
            pw_ok = set(pw) == pw_keys and all(isinstance(v.get("power_200"), (int, float)) and isinstance(v.get("power_400"), (int, float))
                                              and bool(v.get("converged")) == (abs(v["power_200"] - v["power_400"]) <= 0.001)
                                              and bool(v.get("pass_")) == (bool(v.get("converged")) and v["power_200"] >= 0.8) for v in pw.values())
            ck_ok = ck_keys <= set(chk) and all(isinstance(v.get("gap"), (int, float)) and isinstance(v.get("se"), (int, float)) and bool(v.get("pass_")) == (abs(v["gap"]) <= 3 * v["se"] + 1e-4)
                                             for k, v in chk.items() if k in ck_keys)
            att_ok = fx_ok and pw_ok and ck_ok
            if not (fx_ok and pw_ok and ck_ok):
                problems.append(f"coverage report: attempt {i} at n = {n} has incomplete evidence or pass flags that contradict their values")
            passed = bool(fx.get("pass_")) and all(v.get("pass_") for v in pw.values()) and all(v.get("pass_") for k, v in chk.items() if k in ck_keys) and bool(chk)
            if bool(att.get("pass_")) != passed or bool(att.get("threshold_check_pass")) != all(v.get("pass_") for k, v in chk.items() if k in ck_keys):
                problems.append(f"coverage report: attempt {i} at n = {n} has a pass flag that contradicts its fixture, power, or threshold check")
            ok_n = passed and att_ok
        derived[str(n)] = ok_n and bool(attempts) and attempts[-1].get("pass_") is True
    if derived != {k: bool(v) for k, v in (fpw.get("admissible_n") or {}).items()}:
        problems.append(f"coverage report: admissible_n {fpw.get('admissible_n')} does not follow from the fixture, power, and threshold evidence ({derived})")
    measured_n = {str(n) for r in cells.values() for n in (r.get("per_n") or {})}
    if set((cov.get("thresholds") or {}).keys()) != measured_n:
        problems.append(f"coverage report: thresholds must be recorded for exactly the measured sample sizes {sorted(measured_n)}")
    from sim.coverage import ENDPOINTS as _EP, PROCEDURES_AT_N as _PR, endpoint_key as _ek
    for cname, r in cells.items():
        for n, pn in (r.get("per_n") or {}).items():
            attempts = per_n.get(str(n)) or []; sel = attempts[-1] if attempts else {}
            if (pn.get("pool_factor"), pn.get("rep_factor")) != (sel.get("pool_factor"), sel.get("rep_factor")):
                problems.append(f"coverage report: cell {cname} at n = {n} ran with other factors than the selected attempt")
            if int(pn.get("pool_size", -1)) != base_M * (sel.get("pool_factor") or 0) or int((pn.get("replications") or {}).get(str(n), -1)) != base_R.get(str(n), -1) * (sel.get("rep_factor") or 0):
                problems.append(f"coverage report: cell {cname} at n = {n} has a pool size or replication count that is not the locked size times the factor")
            keys = [f"{_ek(st, side, lv, int(n))}|{proc}" for proc in _PR[int(n)] for st, side, lv in _EP]
            vals = [(r.get("measured") or {}).get(k) for k in keys]
            if any(v is None or not isinstance(v, (int, float)) or not math.isfinite(v) or not (0.0 <= v <= 1.0) for v in vals):
                problems.append(f"coverage report: cell {cname} at n = {n} lacks a finite coverage in [0, 1] for every endpoint and procedure")
    try:
        from sim.coverage import admission as _adm, thresholds as _thr
        thr = {int(k): v for k, v in (cov.get("thresholds") or {}).items()}
        for n in thr:                                              # measured sample sizes only; the gates at an unmeasured n are validated above
            attempts = per_n.get(str(n)) or []
            want = _thr(lk, int(attempts[-1]["M"])) if attempts else {}
            if not attempts or any(abs(float(thr[n].get(k, {}).get("threshold", -1)) - v["threshold"]) > 1e-12 for k, v in want.items() if v["n"] == int(n)):
                problems.append(f"coverage report: the thresholds at n = {n} are not thresholds(locked, M) of the last attempt at that n")
        recomputed = _adm({k: v["measured"] for k, v in cells.items()}, thr, lk, derived)
        if recomputed["consequences"] != cov.get("consequences") or recomputed["admitted_sides"] != cov.get("admitted_sides"):
            problems.append("coverage report: the recorded consequences or admitted sides do not follow from its measurements and gates")
    except Exception as e:
        problems.append(f"coverage report: admission could not be recomputed ({e!r})")
    if any(not v.get("input_hash") for v in cells.values()) or {v.get("provenance_hash") for v in cells.values()} != {cov.get("provenance_hash")} or not cov.get("provenance_hash"):
        problems.append("coverage report: every cell must carry its input hash and the report's provenance hash")
    prov = cov.get("provenance") or {}
    want_prov = {"settings_hash": settings_hash(lk), "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest(), "calibration_sha256": sha(a.calibration),   # the pre-lock runs used this environment's salt; --salt-hash is the sealed commitment
                 "tuned_sha256": {r: sha(Path(a.tuned_dir) / f"tuned_{r}.json") for r in ("B1", "B2", "B3")}}
    for k, v in want_prov.items():
        if prov.get(k) != v:
            problems.append(f"coverage report: provenance {k} differs from the input being locked")
    from scripts.coverage_study import provenance_hash as _ph
    if _ph(prov) != cov.get("provenance_hash"):
        problems.append("coverage report: provenance_hash does not match its provenance")
    if len({v.get("input_hash") for v in cells.values()}) != len(cells):
        problems.append("coverage report: two cells share one input hash (the cell specification is part of it)")
    if a.pilot is None and a.cost_cap_usd is None:
        problems.append("a cost cap is required: --pilot PILOT.json (ceil of projected_cost_usd) or --cost-cap-usd X")
    if a.cost_cap_usd is not None and not (math.isfinite(a.cost_cap_usd) and a.cost_cap_usd > 0):
        problems.append("--cost-cap-usd must be a finite positive number")
    if a.pilot is not None:
        pilot = json.loads(Path(a.pilot).read_text())
        if not pilot.get("complete") or int(pilot.get("calls", 0)) < 200 or pilot.get("backend") != "anthropic":
            problems.append("--pilot must be a complete Anthropic pilot of at least 200 calls")
        if not (isinstance(pilot.get("projected_cost_usd"), (int, float)) and math.isfinite(pilot["projected_cost_usd"]) and pilot["projected_cost_usd"] > 0):
            problems.append("--pilot has no finite positive projected cost")
        rate = pilot.get("fallback_rate")
        if not isinstance(rate, (int, float)) or "fallback_rounds" not in pilot:
            problems.append("--pilot carries no fallback figures (fallback_rounds, fallback_rate): rerun the pilot with the current scripts/h1.py")
        elif float(rate) > float(lk["h1"]["fallback_limit"]):
            problems.append(f"--pilot fallback rate {rate} exceeds h1.fallback_limit {lk['h1']['fallback_limit']}: the actor truncates or refuses too often to lock")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", default="experiments/locked.yaml"); ap.add_argument("--tuned-dir", dest="tuned_dir", required=True)
    ap.add_argument("--calibration", required=True); ap.add_argument("--calibration-t100", dest="calibration_t100", required=True)
    ap.add_argument("--coverage-report", dest="coverage_report", required=True); ap.add_argument("--fixture", default="experiments/comprehension_fixture.yaml")
    ap.add_argument("--bundle-hash", dest="bundle_hash", default=None); ap.add_argument("--salt-hash", dest="salt_hash", default=None)
    ap.add_argument("--pilot", default=None); ap.add_argument("--cost-cap-usd", dest="cost_cap_usd", type=float, default=None)
    ap.add_argument("--date", default="2026-10-17"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    path = Path(a.locked); lk = yaml.safe_load(path.read_text()); before = settings_hash(lk)
    tuned = {r: sha(Path(a.tuned_dir) / f"tuned_{r}.json") for r in ("B1", "B2", "B3")}
    cal = json.loads(Path(a.calibration).read_text()); cal100 = json.loads(Path(a.calibration_t100).read_text()); cov = json.loads(Path(a.coverage_report).read_text())
    new = {"version": f"locked-{a.date}", "tuned": tuned,
           "calibration": {**cal, "sha256": sha(a.calibration), "T100": {**cal100, "sha256": sha(a.calibration_t100)}},
           "coverage_report_sha256": sha(a.coverage_report), "coverage_consequences": cov.get("consequences"), "comprehension_fixture_sha256": sha(a.fixture)}
    if a.check:
        a.bundle_hash = a.bundle_hash or lk.get("sealed_bundle_sha256"); a.salt_hash = a.salt_hash or lk.get("identity_salt_sha256")
        a.cost_cap_usd = a.cost_cap_usd if (a.cost_cap_usd is not None or a.pilot) else lk.get("h1", {}).get("cost_cap_usd")
        problems = validate(a, lk, cal, cal100, cov)                   # the same validation as at write time
        problems += [f"{k}: {lk.get(k)!r} != {v!r}" for k, v in new.items() if k != "version" and lk.get(k) != v]
        problems += [f"tuned_{r}.json hash differs from the lock" for r in tuned if (lk.get("tuned") or {}).get(r) != tuned[r]]
        if lk.get("h1", {}).get("cost_cap_usd") is None:
            problems.append("h1.cost_cap_usd is not set")
        if a.bundle_hash != lk.get("sealed_bundle_sha256") or a.salt_hash != lk.get("identity_salt_sha256"):
            problems.append("the commitments passed differ from the stored ones")
        want_cap = float(math.ceil(float(json.loads(Path(a.pilot).read_text())["projected_cost_usd"]))) if a.pilot else a.cost_cap_usd
        if want_cap is not None and lk.get("h1", {}).get("cost_cap_usd") != want_cap:
            problems.append(f"h1.cost_cap_usd {lk.get('h1', {}).get('cost_cap_usd')} differs from the expected {want_cap}")
        if problems:
            print("\n".join(problems)); sys.exit(1)
        print("lock-time blocks match their files"); return
    problems = validate(a, lk, cal, cal100, cov)
    if problems:
        sys.exit("\n".join("REFUSED: " + p for p in problems))
    cap = a.cost_cap_usd
    if a.pilot is not None:
        pilot = json.loads(Path(a.pilot).read_text())
        cap = float(math.ceil(float(pilot["projected_cost_usd"])))
    lk.update(new); lk["h1"]["cost_cap_usd"] = cap; lk["sealed_bundle_sha256"] = a.bundle_hash; lk["identity_salt_sha256"] = a.salt_hash
    if settings_hash(lk) != before:
        sys.exit("REFUSED: the lock-time blocks changed the settings hash; nothing written")
    path.write_text(yaml.safe_dump(lk, sort_keys=False, default_flow_style=None, width=120))
    print(f"wrote {path}\n")
    print(f"git add {path} && git commit -S -m 'lock: {a.date}' && git tag -s lock-{a.date} -m 'Touchstone lock {a.date}' && git push origin main lock-{a.date}")
    print("then post the tag hash to the public timestamp (OSF or AsPredicted) the same day")


if __name__ == "__main__":
    main()
