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


def test_reproduction_compares_knobs_and_per_seed_gains_exactly(tmp_path):
    rid = "headline@rho0.2|F111|D2|profit"
    def put(base, knobs, gain):
        write(F.R.path_of(base, rid), {"stage": "search", "attack": {"best_knobs": knobs, "best_f": 0.1}})
        write(F.R.eval_path(base, rid), {"stage": "evaluate", "seeds": [1, 2], "gain": gain})
    put(tmp_path / "a", {"u0": 0.5, "clip": 0}, [0.1, 0.2]); put(tmp_path / "b", {"u0": 0.5, "clip": 0}, [0.1, 0.2])
    assert F.compare(tmp_path / "a", tmp_path / "b", rid) == []
    put(tmp_path / "c", {"u0": 0.5 + 1e-16, "clip": 0}, [0.1, 0.2 + 1e-16])
    assert F.compare(tmp_path / "a", tmp_path / "c", rid) == ["selected knobs differ", "per-seed gains differ"]


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
