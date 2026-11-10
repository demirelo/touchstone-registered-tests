"""Run A (docs/revision/followup2/runner-up-plan.md): the full-budget runner-up comparator C-thr(K=12) on the fresh markets."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import runnerup_v2 as A  # noqa: E402
from sim.records_v2 import read, sha_file, write  # noqa: E402

MAIN = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")
CTX = "fresh0@rho0.2"


def test_the_runner_up_is_c_thr_12_from_the_recheck_log():
    assert A.runner_up_cred() == {"variant": "thr", "K": 12, "M": None}
    p = A.runner_up_params({"cred": {"variant": "mem", "K": 6, "M": 20}, "tuned": {}})
    assert p["cred"] == {"variant": "thr", "K": 12, "M": None} and p["tuned"] == {}


def _src(tmp_path, rules=("F000", "F111", "C*", "C*/S0")):
    src = tmp_path / "src"; recs = {}
    for fam in ("D2+H3", "X7-SC"):
        for r in rules:
            rid = A.R.cell_id(CTX, r, fam, "profit"); write(A.R.path_of(src, rid), {"stage": "search", "attack": {"best_knobs": {}}}); recs[rid] = sha_file(A.R.path_of(src, rid))
    write(A.R.path_of(src, f"freeze/{CTX}"), {"stage": "freeze", "cuts": 3, "h4_excluded": False, "records": recs})
    return src


def test_bank_inputs_are_the_other_rules_winners_never_the_registered_cstar(tmp_path, monkeypatch):
    monkeypatch.setattr(A.MAN, "bank_rules", lambda ctx, fam, cuts, h4: ["F000", "F111", "C*", "C*/S0"])
    src = _src(tmp_path); need = A.bank_inputs(src, [CTX])
    assert len(need) == 6 and not any("|C*|" in r for r in need) and all(need[r] == sha_file(A.R.path_of(src, r)) for r in need)


def test_bank_inputs_refuse_a_record_missing_from_the_original_freeze(tmp_path, monkeypatch):
    monkeypatch.setattr(A.MAN, "bank_rules", lambda ctx, fam, cuts, h4: ["F000", "F010"])
    with pytest.raises(SystemExit, match="freeze"):
        A.bank_inputs(_src(tmp_path), [CTX])


def test_a_copy_of_a_registered_cstar_record_in_the_output_is_refused(tmp_path, monkeypatch):
    src = _src(tmp_path); out = tmp_path / "out"; rid = A.R.cell_id(CTX, "C*", "D2+H3", "profit")
    A.check_no_registered_cstar(src, out)
    s0 = A.R.cell_id(CTX, "C*/S0", "D2+H3", "profit"); q0 = A.R.path_of(out, s0); q0.parent.mkdir(parents=True)
    q0.write_bytes(A.R.path_of(src, s0).read_bytes()); A.check_no_registered_cstar(src, out)           # a C*/S0 bank copy is allowed
    q = A.R.path_of(out, rid); q.write_bytes(A.R.path_of(src, rid).read_bytes())
    with pytest.raises(SystemExit, match="registered C"):
        A.check_no_registered_cstar(src, out)


def test_pairing_with_the_registered_cstar_reference_except_the_rule_parameters(tmp_path):
    prov = {"runner_sha256": "r", "salt_sha256": "s", "cfg_sha256": "c", "root": "h", "seeds_train": [1], "seeds_val": [2], "seeds_eval": [3],
            "rule_params_sha256": "registered", "context": CTX, "rule": "C*"}
    src = tmp_path / "src"; write(A.R.path_of(src, f"reference/{CTX}/C*"), {"provenance": prov})
    job = {"id": f"{CTX}|C*|D2+H3|profit", "context": CTX, "provenance": {**prov, "rule_params_sha256": "runner-up"}}
    A.check_pairing_rule(src, [job])
    with pytest.raises(SystemExit, match="registered C"):
        A.check_pairing_rule(src, [{**job, "provenance": prov}])                  # same parameters: this would be C* itself
    with pytest.raises(SystemExit, match="root"):
        A.check_pairing_rule(src, [{**job, "provenance": {**job["provenance"], "root": "x"}}])


def test_analysis_pairs_the_runner_up_with_r3_and_cstar(tmp_path):
    out, src = tmp_path / "out", tmp_path / "src"
    for m in ("fresh0", "fresh1"):
        for base, rule, g in ((out, "C*", [0.10, 0.12]), (src, "F111", [0.08, 0.08]), (src, "C*", [0.15, 0.15])):
            write(A.R.eval_path(base, f"{m}@rho0.2|{rule}|D2+H3|profit"), {"seeds": [1, 2], "gain": g})
    got = A.analysis(out, src, ("fresh0", "fresh1"), fams=("D2+H3",), resamples=199)["D2+H3"]
    assert got["runner_up_minus_r3"]["estimate"] == pytest.approx(0.03) and got["cstar_minus_runner_up"]["estimate"] == pytest.approx(0.04)
    assert got["runner_up_minus_r3"]["category"] == A.C.q1_category(got["runner_up_minus_r3"]["interval"]) and got["label"].startswith("exploratory")


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_smoke_path_for_one_fresh_market(tmp_path):
    out = tmp_path / "runnerup"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--markets", "fresh0", "--smoke"]
    assert A.main(args) == 0
    for fam in ("D2+H3", "X7-SC"):
        rid = A.R.cell_id(CTX, "C*", fam, "profit")
        ev = read(A.R.eval_path(out, rid)); db = read(out / "doubling" / (A.R._safe(rid) + ".json"))
        assert len(ev["gain"]) == 2 and f"reference/{CTX}/C*" in ev["upstream"] and "heldout" in db
    ref = read(A.R.path_of(out, f"reference/{CTX}/C*")); assert ref["provenance"]["rule_params_sha256"] != read(A.R.path_of(MAIN / "eval/all", f"reference/{CTX}/C*"))["provenance"]["rule_params_sha256"]
    inv = read(out / "inventory.json"); assert "environment" in inv and (out / "label.json").exists()
