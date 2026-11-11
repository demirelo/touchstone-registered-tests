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


def _eval_set(out, src, ru, cs, r3, ru_d=None, cs_d=None, r3_d=None, markets=("fresh0", "fresh1")):
    rep = {"doubling": {}}
    for m in markets:
        for base, rule, g, gd in ((out, "C*", ru, ru_d), (src, "F111", r3, r3_d), (src, "C*", cs, cs_d)):
            rid = f"{m}@rho0.2|{rule}|D2+H3|profit"; write(A.R.eval_path(base, rid), {"seeds": [1, 2], "gain": g})
            held = {"seeds": [1, 2], "gain": gd if gd is not None else g, "knobs": {}}
            if base == out:
                write(out / "doubling" / (A.R._safe(rid) + ".json"), {"heldout": held, "attack_change": 0.001, "reference_change": 0.0, "incomplete": False})
            else:
                rep["doubling"][rid] = {"heldout": held}
    return rep


def test_analysis_has_base_and_doubled_contrasts_and_scores_the_expectation(tmp_path):
    out, src = tmp_path / "out", tmp_path / "src"
    rep = _eval_set(out, src, ru=[0.10, 0.12], cs=[0.15, 0.15], r3=[0.08, 0.08], ru_d=[0.11, 0.13], cs_d=[0.16, 0.16])
    got = A.analysis(out, src, rep, ("fresh0", "fresh1"), fams=("D2+H3",), resamples=199)["D2+H3"]
    assert got["base"]["runner_up_minus_r3"]["estimate"] == pytest.approx(0.03) and got["base"]["cstar_minus_runner_up"]["estimate"] == pytest.approx(0.04)
    assert got["base"]["cstar_minus_r3"]["estimate"] == pytest.approx(0.07) and got["doubled"]["cstar_minus_runner_up"]["estimate"] == pytest.approx(0.04)
    assert got["base"]["runner_up_minus_r3"]["category"] == A.C.q1_category(got["base"]["runner_up_minus_r3"]["interval"])
    assert got["expectation"] == {"statement": A.EXPECTATION, "base": 0.04 > 0, "doubled": True, "score": "met"} or got["expectation"]["score"] == "met"
    assert set(got["flags"]["fresh0"]) == {"attack_change", "reference_change", "incomplete"} and got["label"].startswith("exploratory")


@pytest.mark.parametrize("ru,ru_d,score", [([0.10, 0.12], [0.20, 0.20], "not established"), ([0.20, 0.20], [0.20, 0.20], "failed"),
                                           ([0.15, 0.15], [0.10, 0.10], "not established")])
def test_expectation_scores_ties_as_not_met(tmp_path, ru, ru_d, score):
    out, src = tmp_path / "out", tmp_path / "src"
    rep = _eval_set(out, src, ru=ru, cs=[0.15, 0.15], r3=[0.08, 0.08], ru_d=ru_d)
    assert A.analysis(out, src, rep, ("fresh0", "fresh1"), fams=("D2+H3",), resamples=99)["D2+H3"]["expectation"]["score"] == score


def test_missing_or_nonfinite_values_are_not_failures(tmp_path):
    out, src = tmp_path / "out", tmp_path / "src"
    rep = _eval_set(out, src, ru=[0.10, float("nan")], cs=[0.15, 0.15], r3=[0.08, 0.08])
    assert A.analysis(out, src, rep, ("fresh0", "fresh1"), fams=("D2+H3",), resamples=99)["D2+H3"]["expectation"]["score"] == "not available"
    rep["doubling"].pop("fresh1@rho0.2|C*|D2+H3|profit")
    ok = _eval_set(out, src, ru=[0.10, 0.12], cs=[0.15, 0.15], r3=[0.08, 0.08]); ok["doubling"].pop("fresh1@rho0.2|C*|D2+H3|profit")
    got = A.analysis(out, src, ok, ("fresh0", "fresh1"), fams=("D2+H3",), resamples=99)["D2+H3"]
    assert got["doubled"] == "not available" and got["expectation"]["score"] == "not available"


def test_the_exact_runner_up_specification_is_enforced():
    good = {"id": "x", "spec": {"tol": 0.16, "L": 10, "cred": {"variant": "thr", "K": 12, "M": None}}}
    A.check_spec([good])
    for bad in ({**good["spec"], "tol": 0.14}, {**good["spec"], "cred": {"variant": "thr", "K": 6, "M": None}}, {**good["spec"], "L": 3}):
        with pytest.raises(SystemExit, match="specification"):
            A.check_spec([{"id": "x", "spec": bad}])


def _frozen_out(tmp_path, monkeypatch):
    """A follow-up output with one market's bank input, two searches and a reference, and the matching jobs."""
    out = tmp_path / "out"; bank = A.R.cell_id(CTX, "F000", "D2+H3", "profit")
    write(A.R.path_of(out, bank), {"stage": "search"}); write(out / "inputs.json", {bank: sha_file(A.R.path_of(out, bank))})
    jobs = []
    for fam in ("D2+H3", "X7-SC"):
        rid = A.R.cell_id(CTX, "C*", fam, "profit"); prov = {"id": rid, "p": 1}
        up = {} if fam == "D2+H3" else {A.R.cell_id(CTX, "C*", "D2+H3", "profit"): sha_file(A.R.path_of(out, A.R.cell_id(CTX, "C*", "D2+H3", "profit")))}
        write(A.R.path_of(out, rid), {"stage": "search", "provenance": prov, "upstream": up}); jobs.append({"id": rid, "context": CTX, "family": fam, "provenance": prov})
    ref = f"reference/{CTX}/C*"; write(A.R.path_of(out, ref), {"stage": "reference", "provenance": {"ref": 1},
                                                                "upstream": {j["id"]: sha_file(A.R.path_of(out, j["id"])) for j in jobs} | {bank: sha_file(A.R.path_of(out, bank))}})
    monkeypatch.setattr(A, "_expected", lambda rid, jobs: set((read(A.R.path_of(out, rid)) or {}).get("upstream") or {}))
    monkeypatch.setattr(A, "_ref_provenance", lambda jobs, ctx: {"ref": 1})
    monkeypatch.setattr(A, "bank_inputs", lambda src, ctxs: {bank: sha_file(A.R.path_of(out, bank))})
    return out, jobs


def test_prefreeze_and_acceptance_validate_the_complete_freeze(tmp_path, monkeypatch):
    out, jobs = _frozen_out(tmp_path, monkeypatch)
    A.prefreeze(out, jobs, src="src"); fr = read(A.R.path_of(out, f"freeze/{CTX}"))
    assert len(fr["records"]) == 4 and fr["cuts"] == 3 and fr["h4_excluded"] is False and fr["followup"] is True
    A.check_freeze(out, jobs, src="src")


def test_acceptance_refuses_an_empty_or_incomplete_freeze(tmp_path, monkeypatch):
    out, jobs = _frozen_out(tmp_path, monkeypatch); A.prefreeze(out, jobs, src="src")
    p = A.R.path_of(out, f"freeze/{CTX}"); f = read(p)
    for change in ({"records": {}}, {"records": {k: v for k, v in f["records"].items() if not k.startswith("reference/")}}, {"cuts": 2}, {"h4_excluded": True}):
        write(p, {**f, **change})
        with pytest.raises(SystemExit):
            A.check_freeze(out, jobs, src="src")


def test_prefreeze_refuses_a_stale_or_wrongly_linked_record(tmp_path, monkeypatch):
    out, jobs = _frozen_out(tmp_path, monkeypatch)
    q = A.R.path_of(out, jobs[0]["id"]); d = read(q); d["provenance"] = {"id": "old"}; write(q, d)
    with pytest.raises(SystemExit, match="provenance"):
        A.prefreeze(out, jobs, src="src")
    out2, jobs2 = _frozen_out(tmp_path / "b", monkeypatch)
    q = A.R.path_of(out2, jobs2[1]["id"]); d = read(q); d["upstream"] = {jobs2[0]["id"]: "0" * 64}; write(q, d)
    with pytest.raises(SystemExit, match="hash"):
        A.prefreeze(out2, jobs2, src="src")


def test_a_changed_bank_copy_is_refused_even_with_a_rebuilt_reference(tmp_path, monkeypatch):
    out, jobs = _frozen_out(tmp_path, monkeypatch); bank = A.R.cell_id(CTX, "F000", "D2+H3", "profit"); q = A.R.path_of(out, bank)
    orig = sha_file(q); monkeypatch.setattr(A, "bank_inputs", lambda src, ctxs: {bank: orig})          # the original freeze hash
    write(q, {"stage": "search", "changed": True}); w = read(out / "inputs.json"); w[bank] = sha_file(q); write(out / "inputs.json", w)
    ref = A.R.path_of(out, f"reference/{CTX}/C*"); r = read(ref); r["upstream"][bank] = sha_file(q); write(ref, r)       # rebuilt reference
    with pytest.raises(SystemExit, match="original freeze"):
        A.prefreeze(out, jobs, src="src")


def test_a_full_run_needs_the_verified_reset_evidence(tmp_path, monkeypatch):
    with pytest.raises(SystemExit, match="evidence"):
        A.check_run_evidence(None, None, None, smoke=False, want={})
    seen = []
    monkeypatch.setattr(A.G, "check_reset_evidence", lambda m, p, d, w: seen.append((m, p, d, w)))
    A.check_run_evidence(tmp_path / "m", tmp_path / "p", tmp_path / "d", smoke=False, want={"budget": [5]})
    assert seen == [(tmp_path / "m", tmp_path / "p", tmp_path / "d", {"budget": [5]})]
    A.check_run_evidence(None, None, None, smoke=True, want={})


def test_bank_copies_are_checked_before_reference_construction(tmp_path, monkeypatch):
    out, jobs = _frozen_out(tmp_path, monkeypatch); bank = A.R.cell_id(CTX, "F000", "D2+H3", "profit")
    built = []; monkeypatch.setattr(A, "run_references", lambda jobs, out: built.append(1))
    orig = sha_file(A.R.path_of(out, bank)); monkeypatch.setattr(A, "bank_inputs", lambda src, ctxs: {bank: orig})   # the original freeze hash
    A.reference_stage(jobs, out, "src"); assert built == [1]
    write(A.R.path_of(out, bank), {"stage": "search", "changed": True})          # a changed copy, resumed at --stage reference
    with pytest.raises(SystemExit, match="original freeze"):
        A.reference_stage(jobs, out, "src")
    assert built == [1]


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_smoke_path_for_one_fresh_market(tmp_path, monkeypatch):
    monkeypatch.setattr(A.R, "git_commit", lambda: "pinned-for-the-rerun-check")      # a commit elsewhere during the test must not change the binding
    out = tmp_path / "runnerup"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--report", str(MAIN / "report/report.json"), "--markets", "fresh0", "--smoke"]
    assert A.main(args) == 0
    for fam in ("D2+H3", "X7-SC"):
        rid = A.R.cell_id(CTX, "C*", fam, "profit")
        ev = read(A.R.eval_path(out, rid)); db = read(out / "doubling" / (A.R._safe(rid) + ".json"))
        assert len(ev["gain"]) == 2 and f"reference/{CTX}/C*" in ev["upstream"] and "heldout" in db
    ref = read(A.R.path_of(out, f"reference/{CTX}/C*")); assert ref["provenance"]["rule_params_sha256"] != read(A.R.path_of(MAIN / "eval/all", f"reference/{CTX}/C*"))["provenance"]["rule_params_sha256"]
    inv = read(out / "inventory.json"); assert "environment" in inv and (out / "label.json").exists()
    assert inv["files"]["driver"] == sha_file(Path(A.__file__)) and inv["files"]["common.py"] and inv["args"] == args
    assert read(out / "run.json")["binding"]["smoke"] is True and read(out / "cost.json")["stopped_before"] is None
    assert A.main(args) == 0                                                     # rerun under the same binding reuses every record


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_the_run_stops_between_stages_at_the_cost_cap(tmp_path):
    out = tmp_path / "runnerup"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--report", str(MAIN / "report/report.json"), "--markets", "fresh0", "--smoke",
            "--cap-usd", "0.5", "--started-at", "0"]                           # epoch 0: the cap is long spent
    assert A.main(args) == 3 and read(out / "cost_stop.json")["stopped_before"] == "inputs" and (out / "inventory.json").exists()


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_the_launchers_stop_file_stops_the_run_before_the_next_stage(tmp_path):
    out = tmp_path / "runnerup"; stop = tmp_path / "STOP"; stop.write_text("")
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--report", str(MAIN / "report/report.json"),
            "--markets", "fresh0", "--smoke", "--stop-file", str(stop)]
    assert A.main(args) == 3 and read(out / "cost_stop.json")["stopped_before"] == "inputs"
