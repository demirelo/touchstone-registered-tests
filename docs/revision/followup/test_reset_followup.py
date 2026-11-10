"""The reset follow-up driver (docs/revision/reset-experiment-plan.md, draft 4, section 3): the 18 restored cells, the
copied inputs with their hash checks, the refusals, the follow-up freeze and its acceptance check, and the inventory."""
import json
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reset_followup_v2 as F  # noqa: E402
from sim.records_v2 import read, sha_file, write

CTX = "fresh0@rho0.2"


def test_the_18_cells_are_exactly_the_cut_d2_cells():
    cs = F.restored_cells()
    assert len(cs) == 18 and {c["family"] for c in cs} == {"D2"} and {c["rule"] for c in cs} == {"F000", "F111", "C*"}
    assert {c["market"] for c in cs} == {f"fresh{i}" for i in range(6)} and {c["rho"] for c in cs} == {0.2}
    from sim import manifest_v2 as MAN
    kept = {c["id"] for c in MAN.effective(F.CUTS, F.H4_EXCLUDED)}
    assert not kept & {c["id"] for c in cs}                                   # every one was removed by cut 3


def test_an_output_inside_eval_all_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "EVAL_ALL", tmp_path / "eval" / "all")
    for bad in (tmp_path / "eval" / "all", tmp_path / "eval" / "all" / "followup"):
        with pytest.raises(SystemExit):
            F.check_out(bad)
    F.check_out(tmp_path / "followup-reset")


def _src(tmp_path) -> Path:
    """A minimal original output: two menu searches, one bank source, the reference, and the context's freeze."""
    src = tmp_path / "src"
    ids = [f"{CTX}|F111|D2+H3|profit", f"{CTX}|F111|X7-SC|profit", f"{CTX}|F000|D2+H3|profit"]
    for i in ids:
        write(F.R.path_of(src, i), {"stage": "search", "id": i, "upstream": {}})
    x7 = F.R.path_of(src, ids[1]); write(x7, {"stage": "search", "id": ids[1], "upstream": {ids[0]: sha_file(F.R.path_of(src, ids[0]))}})
    ref = f"reference/{CTX}/F111"
    write(F.R.path_of(src, ref), {"stage": "reference", "upstream": {i: sha_file(F.R.path_of(src, i)) for i in ids}})
    write(F.R.path_of(src, f"freeze/{CTX}"), {"stage": "freeze", "records": {ref: sha_file(F.R.path_of(src, ref)), **{i: sha_file(F.R.path_of(src, i)) for i in ids}}})
    return src


def _job(rule="F111", cfg="c0", salt="s0"):
    return {"id": f"{CTX}|{rule}|D2|profit", "context": CTX, "rule": rule, "family": "D2", "objective": "profit", "mkt": {"label": "fresh0"},
            "provenance": {"cfg_sha256": cfg, "salt_sha256": salt}}


@pytest.fixture
def no_expected_check(monkeypatch):
    """The miniature source has no full menu; the expected-dependency check gets its own test below."""
    monkeypatch.setattr(F, "_expected_reference_upstream", lambda rid: None)


def test_inputs_come_from_the_original_records_hashes(tmp_path, no_expected_check):
    src = _src(tmp_path); need = F.inputs(src, [_job()])
    assert set(need) == {f"reference/{CTX}/F111", f"{CTX}|F111|D2+H3|profit", f"{CTX}|F111|X7-SC|profit", f"{CTX}|F000|D2+H3|profit"}
    out = tmp_path / "out"; F.copy_inputs(src, out, need)
    assert all(sha_file(F.R.path_of(out, r)) == s for r, s in need.items()) and read(out / "inputs.json") == need
    F.copy_inputs(src, out, need)                                             # a second call reuses identical copies


def test_a_changed_reference_is_refused(tmp_path, no_expected_check):
    src = _src(tmp_path); p = F.R.path_of(src, f"reference/{CTX}/F111"); d = read(p); d["choice"] = 3; write(p, d)
    with pytest.raises(SystemExit, match="differs"):
        F.copy_inputs(src, tmp_path / "out", F.inputs(src, [_job()]))


def test_a_changed_menu_search_is_refused(tmp_path, no_expected_check):
    src = _src(tmp_path); p = F.R.path_of(src, f"{CTX}|F000|D2+H3|profit"); d = read(p); d["runs"] = 1; write(p, d)
    with pytest.raises(SystemExit, match="differs"):
        F.copy_inputs(src, tmp_path / "out", F.inputs(src, [_job()]))


def test_a_missing_input_is_refused(tmp_path, no_expected_check):
    src = _src(tmp_path); F.R.path_of(src, f"{CTX}|F111|X7-SC|profit").unlink()
    with pytest.raises(SystemExit, match="missing"):
        F.copy_inputs(src, tmp_path / "out", F.inputs(src, [_job()]))
    src2 = _src(tmp_path / "b"); F.R.path_of(src2, f"reference/{CTX}/F111").unlink()
    with pytest.raises(SystemExit, match="missing"):
        F.inputs(src2, [_job()])


def test_a_reference_whose_dependencies_are_not_the_registered_menu_is_refused(tmp_path):
    src = _src(tmp_path)                                                       # the miniature menu lacks the full cuts-3 bank
    with pytest.raises(SystemExit, match="registered menu"):
        F.inputs(src, [_job()])


def test_a_wrong_configuration_hash_is_refused():
    container = {"fresh0": {"container_hash": "c0"}}
    F.check_configs([_job(cfg="c0")], container)
    with pytest.raises(SystemExit, match="configuration"):
        F.check_configs([_job(cfg="c1")], container)


def _frozen(tmp_path, monkeypatch, no_check=True):
    src = _src(tmp_path); out = tmp_path / "out"
    need = F.inputs(src, [_job()]); F.copy_inputs(src, out, need)
    j = _job(salt=F.R._sha(b"\x01" * 32))
    (out / "salt.hex").write_text((b"\x01" * 32).hex())
    write(F.R.path_of(out, j["id"]), {"stage": "search", "id": j["id"], "provenance": j["provenance"], "upstream": {}})
    F.prefreeze(out, [j])
    return out, j


def test_acceptance_admits_the_follow_up_freeze(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch)
    fr = read(F.R.path_of(out, f"freeze/{CTX}"))
    assert fr["followup"] is True and len(fr["deviations"]) == 3 and j["id"] in fr["records"] and f"reference/{CTX}/F111" in fr["records"]
    F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}})


def test_acceptance_refuses_a_missing_freeze(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch); F.R.path_of(out, f"freeze/{CTX}").unlink()
    with pytest.raises(SystemExit, match="freeze"):
        F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}})


def test_acceptance_refuses_a_changed_search_record(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch); p = F.R.path_of(out, j["id"]); d = read(p); d["attack"] = {"best_knobs": {"u0": 1}}; write(p, d)
    with pytest.raises(SystemExit, match="differs"):
        F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}})


def test_acceptance_refuses_a_changed_copied_input(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch); p = F.R.path_of(out, f"{CTX}|F000|D2+H3|profit"); p.chmod(0o644); d = read(p); d["runs"] = 2; write(p, d)
    with pytest.raises(SystemExit, match="differs"):
        F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}})


def test_acceptance_refuses_a_changed_salt(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch)
    with pytest.raises(SystemExit, match="salt"):
        F.accept(out, [j], F.R._sha(b"\x02" * 32), {"fresh0": {"container_hash": "c0"}})
    (out / "salt.hex").write_text((b"\x02" * 32).hex())
    with pytest.raises(SystemExit, match="salt"):
        F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}})


def test_the_inventory_lists_every_output_but_itself(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch); inv = F.inventory(out)
    assert "inventory.json" not in inv["records"] and f"freeze/{CTX}.json" in inv["records"] and "inputs.json" in inv["records"]
    assert inv["records"]["salt.hex"] == sha_file(out / "salt.hex") and read(out / "inventory.json") == inv


def _put(base, rid, knobs, gain, runs=100, src="restart_1", arch=3):
    write(F.R.path_of(base, rid), {"stage": "search", "attack": {"best_knobs": knobs, "best_f": 0.1, "best_source": src, "archive": [0] * arch},
                                   "runs": runs, "upstream": {}, "provenance": {"cfg_sha256": "c", "budget": [5, 300, 5, 200]}})
    write(F.R.eval_path(base, rid), {"stage": "evaluate", "seeds": [1, 2], "gain": gain})


def test_reproduction_criterion_exact_parts_and_tolerances(tmp_path):
    """Plan draft 5, section 3 (a): exact on counts, sources, discrete knobs, hashes; 1e-9 on continuous knobs and gains."""
    rid = "headline@rho0.2|F111|D2|profit"
    _put(tmp_path / "a", rid, {"u0": 0.5, "clip": 0}, [0.1, 0.2])
    _put(tmp_path / "b", rid, {"u0": 0.5 * (1 + 2.6e-13), "clip": 0}, [0.1, 0.2 + 2e-14])
    rep = F.compare(tmp_path / "a", tmp_path / "b", rid)
    assert rep["pass"] and not rep["identical"] and rep["max_knob_rel"] == pytest.approx(2.6e-13, rel=1e-3)
    for name, kw in (("knob tolerance", dict(knobs={"u0": 0.5 * (1 + 2e-9), "clip": 0}, gain=[0.1, 0.2])),
                     ("gain tolerance", dict(knobs={"u0": 0.5, "clip": 0}, gain=[0.1, 0.2 + 2e-9])),
                     ("discrete knob", dict(knobs={"u0": 0.5, "clip": 1}, gain=[0.1, 0.2])),
                     ("episode count", dict(knobs={"u0": 0.5, "clip": 0}, gain=[0.1, 0.2], runs=99)),
                     ("best_source", dict(knobs={"u0": 0.5, "clip": 0}, gain=[0.1, 0.2], src="control")),
                     ("archive size", dict(knobs={"u0": 0.5, "clip": 0}, gain=[0.1, 0.2], arch=4))):
        _put(tmp_path / name, rid, **kw)
        r = F.compare(tmp_path / "a", tmp_path / name, rid)
        assert not r["pass"] and any(name in p for p in r["problems"]), name
    _put(tmp_path / "same", rid, {"u0": 0.5, "clip": 0}, [0.1, 0.2])
    assert F.compare(tmp_path / "a", tmp_path / "same", rid)["identical"]


MAIN = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")


@pytest.mark.slow
@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_smoke_path_for_one_fresh_cell(tmp_path):
    """Validation (b): the complete path for fresh0 F111 at smoke size: input copies, search, the follow-up freeze,
    acceptance, evaluation, doubling, inventory; every dependency of the frozen stages resolves."""
    out = tmp_path / "followup"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--markets", "fresh0", "--smoke"]
    FF = F
    real = FF.restored_cells
    FF.restored_cells = lambda markets=FF.MARKETS: [c for c in real(markets) if c["rule"] == "F111"]
    try:
        assert F.main(args) == 0
    finally:
        FF.restored_cells = real
    rid = "fresh0@rho0.2|F111|D2|profit"
    ev = read(F.R.eval_path(out, rid)); db = read(out / "doubling" / (F.R._safe(rid) + ".json")); inv = read(out / "inventory.json")
    assert ev["stage"] == "evaluate" and len(ev["gain"]) == 2 and f"freeze/{CTX}" in ev["upstream"]
    assert db["stage"] == "doubling" and len(db["heldout"]["gain"]) == 2 and f"reference/{CTX}/F111" in db["upstream"]
    assert inv["records"][f"evaluate/{F.R._safe(rid)}.json"] == sha_file(F.R.eval_path(out, rid))


# ---- Fable 5.2 driver review (2026-11-10) ----

PAIRED = {"runner_sha256": "r", "salt_sha256": "s", "cfg_sha256": "c", "root": "h", "seeds_train": [1], "seeds_val": [2], "seeds_eval": [3],
          "rule_params_sha256": "p", "context": CTX, "rule": "F111", "git_commit": "d5e602e"}


def _paired_src(tmp_path, **override):
    src = tmp_path / "src"; write(F.R.path_of(src, f"reference/{CTX}/F111"), {"stage": "reference", "provenance": {**PAIRED, **override}})
    return src


def test_f1_each_job_matches_its_reference_provenance(tmp_path):
    j = {**_job(), "provenance": {**PAIRED, "id": f"{CTX}|F111|D2|profit", "budget": [5, 300, 5, 200], "git_commit": "abc"}}
    F.check_pairing(_paired_src(tmp_path), [j])                             # the commit may differ; everything else may not
    for key, bad in (("rule_params_sha256", "p2"), ("runner_sha256", "r2"), ("root", "h2"), ("seeds_eval", [4])):
        with pytest.raises(SystemExit, match=key):
            F.check_pairing(_paired_src(tmp_path / key, **{key: bad}), [j])


def test_f2_an_unknown_commit_is_refused():
    with pytest.raises(SystemExit, match="commit"):
        F.check_commit([{**_job(), "provenance": {"git_commit": "unknown"}}])
    F.check_commit([{**_job(), "provenance": {"git_commit": "052538c"}}])


def test_f2_the_inventory_records_the_environment(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch); env = F.inventory(out)["environment"]
    assert {"python", "numpy", "machine", "platform", "driver_sha256"} <= set(env)


def test_f5_an_output_equal_to_or_inside_the_source_is_refused(tmp_path):
    src = tmp_path / "copy-of-eval"
    for bad in (src, src / "followup"):
        with pytest.raises(SystemExit, match="inside"):
            F.check_out(bad, src)
    F.check_out(tmp_path / "followup", src)


def test_f6_the_salt_is_checked_before_any_search(tmp_path):
    (tmp_path / "salt.hex").write_text((b"\x01" * 32).hex())
    with pytest.raises(SystemExit, match="salt"):
        F.check_salt(tmp_path, F.R._sha(b"\x02" * 32), [])


def test_f7_a_second_different_hash_for_a_known_record_is_refused(tmp_path, no_expected_check):
    src = _src(tmp_path)                                                      # the X7-SC search lists the D2+H3 search by its hash
    x7 = F.R.path_of(src, f"{CTX}|F111|X7-SC|profit"); d = read(x7); d["upstream"] = {f"{CTX}|F111|D2+H3|profit": "0" * 64}; write(x7, d)
    ref = F.R.path_of(src, f"reference/{CTX}/F111"); r = read(ref); r["upstream"][f"{CTX}|F111|X7-SC|profit"] = sha_file(x7); write(ref, r)
    fr = F.R.path_of(src, f"freeze/{CTX}"); f = read(fr); f["records"][f"reference/{CTX}/F111"] = sha_file(ref); write(fr, f)
    with pytest.raises(SystemExit, match="different hashes"):
        F.inputs(src, [_job()])


def test_f7_the_original_freeze_must_be_cuts_3_with_h4(tmp_path, no_expected_check):
    src = _src(tmp_path); fr = F.R.path_of(src, f"freeze/{CTX}"); f = read(fr); f["cuts"] = 2; write(fr, f)
    with pytest.raises(SystemExit, match="cuts"):
        F.inputs(src, [_job()])


def test_f8_acceptance_recomputes_the_inputs_from_the_source(tmp_path, monkeypatch, no_expected_check):
    out, j = _frozen(tmp_path, monkeypatch)
    F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}}, src=tmp_path / "src")
    p = out / "inputs.json"; d = read(p); d.pop(f"{CTX}|F000|D2+H3|profit"); write(p, d)
    with pytest.raises(SystemExit, match="inputs"):
        F.accept(out, [j], j["provenance"]["salt_sha256"], {"fresh0": {"container_hash": "c0"}}, src=tmp_path / "src")
