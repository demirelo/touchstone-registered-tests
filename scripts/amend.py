"""Amendment 1: validate the coverage extension report against the lock, the base coverage report, and the amendment
file, then record its hash and consequences in the amendment file (never in experiments/locked.yaml). --check compares
the recorded fields with the files and writes nothing. Mirrors scripts/lock.py::validate for the 12 extension endpoints
at n = 40 (consensus of Sol high and Astra high, 2026-10-17)."""
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
from scripts.coverage_study import provenance_hash  # noqa: E402
from sim.amendment import AMEND_ENDPOINTS, AMEND_LEVEL, AMEND_N, AMEND_PROCEDURES, LIMITATION, REGISTRATION_FIELDS, admission_ext, amendment_hash, load_amendment  # noqa: E402
from sim.coverage import clopper_pearson_lower, endpoint_key, thresholds  # noqa: E402
from sim.locked import load_locked, settings_hash  # noqa: E402
from sim.rng import load_identity_salt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PROVENANCE_KEYS = ("settings_hash", "salt_hash", "calibration_sha256", "tuned_sha256", "reference_records_sha256")


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def validate_ext(a, lk: dict, amend: dict, rep: dict, base: dict, selection: list) -> list:
    """Every problem found; an empty list means the report follows from its inputs and the registered procedure."""
    p = []; n = AMEND_N; key = f"{n}|{AMEND_LEVEL}"
    if rep.get("admission_basis") != "registered" or rep.get("smoke"):
        p.append("extension report: not a registered admission (smoke run?)")
    base_sha = sha(a.base_report)
    if base_sha != lk.get("coverage_report_sha256"):
        p.append("base report: hash differs from the lock's coverage_report_sha256")
    if rep.get("base_report_sha256") != base_sha or (rep.get("provenance") or {}).get("base_report_sha256") != base_sha:
        p.append("extension report: base_report_sha256 differs from the base report")
    if rep.get("amendment_sha256") != amendment_hash(amend) or (rep.get("provenance") or {}).get("amendment_sha256") != amendment_hash(amend):
        p.append("extension report: amendment_sha256 differs from the amendment file (its registration fields excluded)")
    names = [c.get("name") for c in rep.get("selection", [])]; base_names = [c.get("name") for c in base.get("selection", [])]; sel_names = [c.get("name") for c in selection]
    if len(names) != 6 or len(set(names)) != 6 or not all(names) or names != base_names or names != sel_names or (rep.get("provenance") or {}).get("selection") != names:
        p.append("selection: the report, the base report, the selection file, and the provenance must name the same six registered cells in order")
    prov = rep.get("provenance") or {}; bp = base.get("provenance") or {}
    want = {"settings_hash": settings_hash(lk), "salt_hash": hashlib.sha256(load_identity_salt()).hexdigest(), "calibration_sha256": sha(a.calibration),
            "tuned_sha256": {r: sha(Path(a.tuned_dir) / f"tuned_{r}.json") for r in ("B1", "B2", "B3")}}
    for k in PROVENANCE_KEYS:
        if prov.get(k) != bp.get(k):
            p.append(f"provenance {k}: the extension differs from the base report")
        if k in want and prov.get(k) != want[k]:
            p.append(f"provenance {k}: the extension differs from this environment's inputs")
    if (lk.get("calibration") or {}).get("sha256") not in (None, want["calibration_sha256"]):
        p.append("calibration: hash differs from the lock")
    t100 = ((lk.get("calibration") or {}).get("T100") or {}).get("sha256")
    if t100:
        if not a.calibration_t100:
            p.append("--calibration-t100 is required: the lock names the T100 calibration hash")
        elif sha(a.calibration_t100) != t100:
            p.append("calibration T100: hash differs from the lock")
    for r, h in (lk.get("tuned") or {}).items():
        if want["tuned_sha256"].get(r) != h:
            p.append(f"tuned file for {r}: hash differs from the lock")
    if provenance_hash(prov) != rep.get("provenance_hash") or not rep.get("provenance_hash"):
        p.append("provenance_hash does not match the provenance")
    se = amend["seeds_ext"]; base_M = int(se["pool"]); base_R = int(se["replications"][str(n)]); trials = int(lk["intervals"]["joint_trials"]); conf = 1.0 - 0.05 / 3.0
    fpw = rep.get("fixture_and_power") or {}; per_n = fpw.get("per_n") or {}; checks = fpw.get("threshold_check") or {}
    attempts = per_n.get(str(n)) or []
    if set(per_n) != {str(n)} or not attempts:
        p.append(f"fixture and power: results must exist for n = {n} only")
    ok_n = False
    for i, att in enumerate(attempts):
        fx = att.get("fixture") or {}; pw = att.get("power") or {}; M = int(att.get("M", 0)); chk = checks.get(str(M)) or {}
        expect = [(1, 1), (2, 1), (2, 2)][i] if i < 3 else None
        if (att.get("pool_factor"), att.get("rep_factor")) != expect or int(fx.get("trials", 0)) != trials or int(fx.get("cells", 0)) != 6 or int(fx.get("endpoints_per_cell", 0)) != 2:
            p.append(f"attempt {i}: not the registered attempt order or size (6 cells x 2 endpoints, {trials} trials)")
        if M != base_M * (att.get("pool_factor") or 0) or int(att.get("R", 0)) != base_R * (att.get("rep_factor") or 0) or int(fx.get("M", -1)) != M or int(fx.get("R", -1)) != int(att.get("R", 0)):
            p.append(f"attempt {i}: M or R is not the seeds_ext size times the factor")
        fx_ll = clopper_pearson_lower(int(fx.get("admitted", 0)), trials, conf) if trials else 0.0
        fx_ok = abs(float(fx.get("lower_limit", -1)) - fx_ll) < 1e-9 and bool(fx.get("pass_")) == (fx_ll >= 0.9)
        iv = lk["intervals"]; want_deficit = float(iv["deficits"][str(AMEND_LEVEL)]); exact = thresholds(lk, M).get(key, {}).get("exact") if M else None
        pw_ok = set(pw) == {key} and all(_num(v.get("power_200")) and _num(v.get("power_400")) and 0.0 <= v["power_200"] <= 1.0 and 0.0 <= v["power_400"] <= 1.0
                                      and _num(v.get("deficit")) and abs(float(v["deficit"]) - want_deficit) < 1e-12
                                      and bool(v.get("converged")) == (abs(v["power_200"] - v["power_400"]) <= 0.001)
                                      and bool(v.get("pass_")) == (bool(v.get("converged")) and v["power_200"] >= 0.8) for v in pw.values())
        c0 = chk.get(key) or {}
        ck_ok = (key in chk and _num(c0.get("gap")) and _num(c0.get("se")) and _num(c0.get("analytic")) and _num(c0.get("simulated"))
                 and 0.0 <= c0["simulated"] <= 1.0 and exact is not None and abs(float(c0["analytic"]) - float(exact)) < 1e-12
                 and abs(float(c0["gap"]) - (float(c0["analytic"]) - float(c0["simulated"]))) < 1e-12
                 and int(c0.get("pools", 0)) == int(iv.get("threshold_check_pools", 200)) and int(c0.get("reps", 0)) == int(iv.get("threshold_check_reps", 20000))
                 and bool(c0.get("pass_")) == (abs(c0["gap"]) <= 3 * c0["se"] + 1e-4))
        if not (fx_ok and pw_ok and ck_ok):
            p.append(f"attempt {i}: incomplete evidence or pass flags that contradict their values")
        passed = bool(fx.get("pass_")) and all(v.get("pass_") for v in pw.values()) and bool(pw) and ck_ok and bool(chk[key].get("pass_")) if key in chk else False
        if bool(att.get("pass_")) != passed or bool(att.get("threshold_check_pass")) != (bool(chk.get(key, {}).get("pass_"))):
            p.append(f"attempt {i}: a pass flag contradicts its fixture, power, or threshold check")
        ok_n = passed and fx_ok and pw_ok and ck_ok
    derived = {str(n): bool(ok_n and attempts and attempts[-1].get("pass_") is True)}
    if derived != {k: bool(v) for k, v in (fpw.get("admissible_n") or {}).items()}:
        p.append(f"admissible_n {fpw.get('admissible_n')} does not follow from the evidence ({derived})")
    sel_att = attempts[-1] if attempts else {}
    thr_rep = rep.get("thresholds") or {}
    want_thr = thresholds(lk, int(sel_att.get("M", 0))) if sel_att else {}
    got_thr = (thr_rep.get(str(n)) or {}).get(key, {}).get("threshold")
    if set(thr_rep) != {str(n)} or not _num(got_thr) or not (0.0 <= got_thr <= 1.0) or abs(float(got_thr) - float(want_thr.get(key, {}).get("threshold", -2))) > 1e-12:
        p.append(f"thresholds at n = {n} are not finite thresholds(locked, M) of the selected attempt")
    cells = rep.get("cells") or {}
    if set(cells) != set(names):
        p.append("cells: not exactly the six selected cells")
    keys = [f"{endpoint_key(st, side, lv, n)}|{proc}" for proc in AMEND_PROCEDURES for st, side, lv in AMEND_ENDPOINTS]
    for cname, r in cells.items():
        vals = [(r.get("measured") or {}).get(k) for k in keys]
        if any(not _num(v) or not (0.0 <= v <= 1.0) for v in vals):
            p.append(f"cell {cname}: lacks a finite coverage in [0, 1] for both endpoints")
        if (r.get("pool_factor"), r.get("rep_factor")) != (sel_att.get("pool_factor"), sel_att.get("rep_factor")):
            p.append(f"cell {cname}: factors differ from the selected attempt")
        if int(r.get("pool_size", -1)) != base_M * (sel_att.get("pool_factor") or 0) or int((r.get("replications") or {}).get(str(n), -1)) != base_R * (sel_att.get("rep_factor") or 0):
            p.append(f"cell {cname}: pool size or replication count is not the seeds_ext size times the selected factor")
        if not r.get("input_hash") or r.get("provenance_hash") != rep.get("provenance_hash"):
            p.append(f"cell {cname}: missing input hash or a provenance hash that differs from the report's")
    if len({r.get("input_hash") for r in cells.values()}) != len(cells):
        p.append("cells: two cells share one input hash")
    try:
        thr_int = {int(k): v for k, v in thr_rep.items()}
        rec = admission_ext({k: v.get("measured") or {} for k, v in cells.items()}, thr_int, lk, derived, names)
        for k in ("procedure_admitted", "admitted_sides", "consequences"):
            if rec[k] != rep.get(k):
                p.append(f"{k}: the recorded value does not follow from the measurements and the gate")
    except Exception as e:  # pragma: no cover
        p.append(f"admission could not be recomputed ({e!r})")
    if rep.get("limitation") != LIMITATION:
        p.append("limitation: the proxy-admission sentence is missing or altered")
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amendment", required=True); ap.add_argument("--report", required=True); ap.add_argument("--base-report", dest="base_report", required=True)
    ap.add_argument("--selection", required=True); ap.add_argument("--calibration", required=True); ap.add_argument("--tuned-dir", dest="tuned_dir", required=True)
    ap.add_argument("--calibration-t100", dest="calibration_t100", default=None, help="the T = 100 calibration; required when the lock names its hash")
    ap.add_argument("--repo", default=str(REPO)); ap.add_argument("--locked", default=None, help="default: experiments/locked.yaml under --repo"); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    a.locked = a.locked or str(Path(a.repo) / "experiments" / "locked.yaml")
    lk = load_locked(a.locked)
    try:
        amend = load_amendment(a.amendment, lk)
    except (ValueError, KeyError) as e:
        print(f"REFUSED: amendment file: {e}", file=sys.stderr); sys.exit(2)
    try:
        base = json.loads(Path(a.base_report).read_text()); rep = json.loads(Path(a.report).read_text()); selection = json.loads(Path(a.selection).read_text())
    except (OSError, ValueError) as e:
        print(f"REFUSED: cannot read an input ({e})", file=sys.stderr); sys.exit(2)
    if not isinstance(base, dict) or "selection" not in base or "provenance" not in base:
        print("REFUSED: base report: not a coverage report", file=sys.stderr); sys.exit(2)
    problems = validate_ext(a, lk, amend, rep, base, selection)
    if a.check:
        if amend.get("coverage_report_amendment_sha256") != sha(a.report):
            problems.append("--check: the recorded coverage_report_amendment_sha256 differs from the report")
        if amend.get("coverage_consequences") != rep.get("consequences"):
            problems.append("--check: the recorded coverage_consequences differ from the report")
    if problems:
        for q in problems:
            print("REFUSED: " + q, file=sys.stderr)
        sys.exit(2)
    if a.check:
        print("amendment registration matches the report"); return
    doc = yaml.safe_load(Path(a.amendment).read_text())
    doc["coverage_report_amendment_sha256"] = sha(a.report); doc["coverage_consequences"] = rep.get("consequences")
    Path(a.amendment).write_text(yaml.safe_dump(doc, sort_keys=False))
    print(f"recorded {REGISTRATION_FIELDS} in {a.amendment}")
    print(f"\ncp {a.report} experiments/coverage_report_amendment.json && uv run python scripts/amend.py ... --check && git add experiments/amendment-2026-10-17.yaml "
          f"experiments/coverage_report_amendment.json && git commit -S -m 'amendment 1: registered' && git tag -s lock-2026-10-17-amendment-1 -m 'Touchstone amendment 1' && git push origin main lock-2026-10-17-amendment-1")


if __name__ == "__main__":
    main()
