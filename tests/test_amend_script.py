import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

from tests.conftest import fabricate_ext_report

ROOT = Path(__file__).resolve().parents[1]


def cmd(inp, report=None, amendment=None, base=None, selection=None, locked=None, *extra):
    return [sys.executable, str(ROOT / "scripts" / "amend.py"), "--amendment", str(amendment or inp["amendment"]), "--report", str(report or inp["report"]),
            "--base-report", str(base or inp["base_report"]), "--selection", str(selection or inp["selection"]), "--calibration", str(inp["calibration"]),
            "--calibration-t100", str(inp["dir"] / "cal100.json"), "--tuned-dir", str(inp["tuned"]), "--locked", str(locked or inp["locked"]), *extra]


def run(c):
    return subprocess.run(c, capture_output=True, text=True, cwd=ROOT)


def rewrite(path: Path, fn):
    d = json.loads(path.read_text()); fn(d); path.write_text(json.dumps(d, sort_keys=True, indent=1))


def test_amend_script_records_fields_and_refuses_inconsistent_or_retuned_inputs(registered_inputs):
    inp = registered_inputs; am = Path(inp["amendment"])
    r = run(cmd(inp)); assert r.returncode == 0, r.stderr
    doc = yaml.safe_load(am.read_text())
    assert doc["coverage_report_amendment_sha256"] == hashlib.sha256(Path(inp["report"]).read_bytes()).hexdigest()
    assert doc["coverage_consequences"] == {"h3_comparative": "confirmatory"} and doc["clause"]["gain_reduction_min"] == 0.10      # other keys preserved
    assert run(cmd(inp, None, None, None, None, None, "--check")).returncode == 0
    rewrite(Path(inp["report"]), lambda d: d["consequences"].update(h3_comparative="exploratory"))
    r = run(cmd(inp, None, None, None, None, None, "--check")); assert r.returncode == 2 and "REFUSED" in r.stderr                   # the recorded hash no longer matches
    fabricate_ext_report(inp["lk"], Path(inp["base_report"]), yaml.safe_load(am.read_text()), Path(inp["report"]))                        # restore
    assert run(cmd(inp, None, None, None, None, None, "--check")).returncode == 0

    def flip_consequence(d): d["consequences"]["h3_comparative"] = "exploratory"
    def set_measured_1_5(d): next(iter(d["cells"].values()))["measured"]["gain_diff|lower|0.9875|40|studentized"] = 1.5
    def swap_selection(d): d["selection"][0], d["selection"][1] = d["selection"][1], d["selection"][0]
    def change_base_hash_field(d): d["base_report_sha256"] = "0" * 64; d["provenance"]["base_report_sha256"] = "0" * 64
    def halve_pool(d): next(iter(d["cells"].values()))["pool_size"] = 17500
    def rep_factor_2(d): next(iter(d["cells"].values()))["rep_factor"] = 2
    def drop_limitation(d): d["limitation"] = "none"
    def fixture_two_cells(d): d["fixture_and_power"]["per_n"]["40"][0]["fixture"]["cells"] = 2
    for i, mutate in enumerate((flip_consequence, set_measured_1_5, swap_selection, change_base_hash_field, halve_pool, rep_factor_2, drop_limitation, fixture_two_cells)):
        bad = inp["dir"] / f"bad{i}.json"; bad.write_text(Path(inp["report"]).read_text()); rewrite(bad, mutate)
        fresh = inp["dir"] / f"am{i}.yaml"; fresh.write_text(yaml.safe_dump({**yaml.safe_load(am.read_text()), "coverage_report_amendment_sha256": None, "coverage_consequences": None}))
        r = run(cmd(inp, bad, fresh)); assert r.returncode == 2 and "REFUSED" in r.stderr, (mutate.__name__, r.stderr[-600:])
        assert yaml.safe_load(fresh.read_text())["coverage_report_amendment_sha256"] is None                                           # nothing written on refusal
    # a consistently retuned B2: the extension's provenance is self-consistent but differs from the base report's and the lock's
    (Path(inp["tuned"]) / "tuned_B2.json").write_text(json.dumps({"rule": "B2", "changed": True}))
    retuned = inp["dir"] / "retuned.json"
    d = json.loads(Path(inp["report"]).read_text()); d["provenance"]["tuned_sha256"]["B2"] = hashlib.sha256((Path(inp["tuned"]) / "tuned_B2.json").read_bytes()).hexdigest()
    from scripts.coverage_study import provenance_hash
    d["provenance_hash"] = provenance_hash(d["provenance"])
    for c in d["cells"].values():
        c["provenance_hash"] = d["provenance_hash"]
    retuned.write_text(json.dumps(d, sort_keys=True, indent=1))
    fresh = inp["dir"] / "am_retuned.yaml"; fresh.write_text(yaml.safe_dump({**yaml.safe_load(am.read_text()), "coverage_report_amendment_sha256": None, "coverage_consequences": None}))
    r = run(cmd(inp, retuned, fresh)); assert r.returncode == 2 and "REFUSED" in r.stderr and "tuned" in r.stderr
    wrong_base = inp["dir"] / "wrong_base.json"; wrong_base.write_text("{}")
    r = run(cmd(inp, None, fresh, wrong_base)); assert r.returncode == 2 and "base report" in r.stderr


def test_amend_script_checks_gate_parameters_thresholds_and_the_t100_calibration(registered_inputs):
    import math
    inp = registered_inputs
    def one_pool(d): d["fixture_and_power"]["threshold_check"]["35000"]["40|0.9875"].update(pools=1, reps=1)
    def wrong_deficit(d): d["fixture_and_power"]["per_n"]["40"][0]["power"]["40|0.9875"]["deficit"] = 90.0
    def power_fifty(d): d["fixture_and_power"]["per_n"]["40"][0]["power"]["40|0.9875"].update(power_200=50.0, power_400=50.0)
    def gap_lie(d): d["fixture_and_power"]["threshold_check"]["35000"]["40|0.9875"].update(simulated=0.0, gap=0.0)
    def nan_threshold(d):
        d["thresholds"]["40"]["40|0.9875"]["threshold"] = float("nan")
        for c in d["cells"].values():
            for k in c["measured"]:
                c["measured"][k] = 0.0
    for i, mutate in enumerate((one_pool, wrong_deficit, power_fifty, gap_lie, nan_threshold)):
        bad = inp["dir"] / f"gate{i}.json"; bad.write_text(Path(inp["report"]).read_text()); rewrite(bad, mutate)
        fresh = inp["dir"] / f"amg{i}.yaml"; fresh.write_text(yaml.safe_dump({**yaml.safe_load(Path(inp["amendment"]).read_text()), "coverage_report_amendment_sha256": None, "coverage_consequences": None}))
        r = run(cmd(inp, bad, fresh)); assert r.returncode == 2 and "REFUSED" in r.stderr, (mutate.__name__, r.stderr[-500:])
    # the T = 100 calibration is a registered artifact: a changed file is refused when the lock names its hash
    lk = yaml.safe_load(Path(inp["locked"]).read_text()); lk["calibration"]["T100"] = {"sha256": "ab" * 32}
    locked2 = inp["dir"] / "locked_t100.yaml"; locked2.write_text(yaml.safe_dump(lk, sort_keys=False))
    fresh = inp["dir"] / "am_t100.yaml"; fresh.write_text(yaml.safe_dump({**yaml.safe_load(Path(inp["amendment"]).read_text()), "coverage_report_amendment_sha256": None, "coverage_consequences": None}))
    r = run(cmd(inp, None, fresh, None, None, locked2))
    assert r.returncode == 2 and "T100" in r.stderr
    assert run([*cmd(inp, None, fresh), "--repo", str(inp["dir"])]).returncode == 0                                       # --repo is accepted
