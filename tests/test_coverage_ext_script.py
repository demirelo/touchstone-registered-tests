import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

from sim.amendment import LIMITATION
from sim.locked import load_locked
from tests.conftest import SEEDS_EXT
from tests.test_amendment import small_ext_spec

ROOT = Path(__file__).resolve().parents[1]
SMOKE_AMEND = {"seeds_ext": dict(SEEDS_EXT)}


def ext_cmd(inp: dict, out: Path, **over) -> list:
    v = {"sweep": inp["sweep"], "cal": inp["cal"], "amendment": inp["amendment"], "base_report": inp["base_report"], "selection": inp["selection"], "locked": inp["locked"], **over}
    return [sys.executable, str(ROOT / "scripts" / "coverage_ext.py"), "--sweep-out", str(v["sweep"]), "--calibration", str(v["cal"]), "--amendment", str(v["amendment"]),
            "--base-report", str(v["base_report"]), "--selection", str(v["selection"]), "--locked", str(v["locked"]), "--out", str(out)]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)


def test_run_cell_ext_and_pool_cache_on_a_small_spec(tmp_path):
    from scripts.coverage_ext import input_hash_ext, pool_observations_ext, run_cell_ext
    spec = small_ext_spec(ref_b2=True, ref_b3=True); prov = {"settings_hash": "x", "base_report_sha256": "y", "amendment_sha256": "z", "selection": ["x_B1"]}
    key = input_hash_ext(spec, prov)
    o1, n1 = pool_observations_ext(spec, np.arange(4), tmp_path, 0, 1, key); o2, n2 = pool_observations_ext(spec, np.arange(8), tmp_path, 0, 1, key)
    assert n1 == 4 and n2 == 4 and np.array_equal(o2["gain_diff"][:4], o1["gain_diff"])
    o3, n3 = pool_observations_ext(spec, np.arange(4), tmp_path, 0, 1, key); assert n3 == 0 and np.array_equal(o3["gain_diff"], o1["gain_diff"])
    with pytest.raises(SystemExit, match="input hash"):
        pool_observations_ext(spec, np.arange(4), tmp_path, 0, 1, input_hash_ext(spec, {**prov, "settings_hash": "q"}))
    cell_out = tmp_path / "cell"; cell_out.mkdir()
    name, r = run_cell_ext(("x", spec, load_locked(), 0, 1, 1, True, cell_out, 1, prov, SMOKE_AMEND))
    assert name == "x" and set(r["measured"]) == {"gain_diff|lower|0.9875|40|studentized", "gain_diff|upper|0.9875|40|studentized"}
    assert r["replications"] == {"40": 20} and r["pool_size"] == 200 and r["pool_factor"] == 1 and r["rep_factor"] == 1 and r["input_hash"] == key


@pytest.mark.slow
def test_coverage_ext_smoke_end_to_end_and_refusals(tmp_path, smoke_inputs):
    out = tmp_path / "ext"
    for i in range(6):
        r = run(ext_cmd(smoke_inputs, out) + ["--cell", str(i), "--smoke", "--workers", "2"]); assert r.returncode == 0, r.stderr[-1500:]
        assert (out / f"cellx_{i}.json").exists() and (out / f"poolx_{i}.npz").exists()
    r = run(ext_cmd(smoke_inputs, out) + ["--merge", "--smoke"]); assert r.returncode == 0, r.stderr[-1500:]
    rep = json.loads((out / "coverage_report_amendment.json").read_text())
    assert rep["smoke"] is True and rep["admission_basis"].startswith("smoke") and set(rep["cells"]) == {c["name"] for c in rep["selection"]} and rep["limitation"] == LIMITATION
    assert set(rep["admitted_sides"]) == {"gain_diff|lower|0.9875|40", "gain_diff|upper|0.9875|40"} and rep["consequences"]["h3_comparative"] in ("confirmatory", "exploratory")
    assert set(rep["thresholds"]) == {"40"} and rep["base_report_sha256"] and rep["amendment_sha256"] and all(c["pool_factor"] == 1 for c in rep["cells"].values())
    r2 = run(ext_cmd(smoke_inputs, out) + ["--cell", "0", "--smoke"]); assert r2.returncode == 0 and "0 new pool seeds" in r2.stdout      # rerun reuses the pool
    r3 = run(ext_cmd(smoke_inputs, out) + ["--cell", "7", "--smoke"]); assert r3.returncode == 2 and "--cell" in r3.stderr
    sel = json.loads(Path(smoke_inputs["selection"]).read_text()); sel[0], sel[1] = sel[1], sel[0]
    bad_sel = tmp_path / "sel.json"; bad_sel.write_text(json.dumps(sel))
    r4 = run(ext_cmd(smoke_inputs, tmp_path / "e4", selection=bad_sel) + ["--cell", "0", "--smoke"]); assert r4.returncode == 2 and "selection" in r4.stderr
    other = tmp_path / "base2.json"; other.write_text(Path(smoke_inputs["base_report"]).read_text() + " ")
    r5 = run(ext_cmd(smoke_inputs, tmp_path / "e5", base_report=other) + ["--cell", "0", "--smoke"]); assert r5.returncode == 2 and "base report" in r5.stderr
    r6 = run(ext_cmd(smoke_inputs, tmp_path / "e6") + ["--cell", "0"]); assert r6.returncode == 2 and "smoke" in r6.stderr                    # smoke artifacts without --smoke
    changed = tmp_path / "changed"; shutil.copytree(smoke_inputs["dir"], changed)
    ref_dir = changed / "sweep" / "reference"; b3 = sorted(p for p in ref_dir.glob("B3_*.json"))[0]; doc = json.loads(b3.read_text())
    doc["candidate"] = {"name": "abstain", "knobs": None} if doc["candidate"]["name"] != "abstain" else {"name": "honest_max", "knobs": None}; b3.write_text(json.dumps(doc))
    inp = {**smoke_inputs, "sweep": changed / "sweep"}
    r7 = run(ext_cmd(inp, tmp_path / "e7") + ["--cell", "0", "--smoke"]); assert r7.returncode == 2 and "reference records" in r7.stderr
