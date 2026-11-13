"""Run B (docs/revision/followup2/convergence-plan.md): further doublings of the flagged profit cells until the doubling
check passes or the cap is reached."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convergence_v2 as B  # noqa: E402
from sim.records_v2 import read, write  # noqa: E402

MAIN = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")


def test_flagged_cells_split_into_profit_and_coalition():
    rep = {"doubling": {"a|F111|D2+H3|profit": {"kind": "profit", "incomplete": True}, "b|C*|X6-SE/v2|total|c2_s": {"kind": "coalition", "incomplete": True},
                        "c|F000|D2+H3|profit": {"kind": "profit", "incomplete": False}}}
    assert B.flagged(rep) == {"profit": ["a|F111|D2+H3|profit"], "coalition": ["b|C*|X6-SE/v2|total|c2_s"]}


@pytest.mark.skipif(not (MAIN / "report/report.json").is_file(), reason="needs the report")
def test_the_registered_report_has_14_flagged_profit_cells_and_7_coalition_cells():
    f = B.flagged(json.loads((MAIN / "report/report.json").read_text()))
    assert len(f["profit"]) == 14 and len(f["coalition"]) == 7


def test_round_seeds_never_repeat_a_cma_seed():
    R5 = 5
    used = set(range(2, R5 + 2))                                            # the registered search: cma_search(seed 1)
    for k in (1, 2, 3):
        s = B.cma_seeds(k, R5)
        assert len(s) == R5 and not (s & used); used |= s
    assert B.cma_seeds(1, R5) == set(range(R5 + 2, 2 * R5 + 2))             # round 1 = the registered doubling (seed 1)


@pytest.mark.parametrize("changes,stop", [([(0.01, 0.0), (0.004, 0.0)], 2), ([(0.001, 0.001)], 1), ([(0.01, 0.0), (0.006, 0.0), (0.02, 0.0)], None),
                                          ([(0.01, 0.0), (0.001, 0.005)], None)])
def test_stopping_rule_is_the_registered_doubling_threshold(changes, stop):
    rounds = [{"round": i + 1, "attack_change": a, "reference_change": r} for i, (a, r) in enumerate(changes)]
    assert B.passed_round(rounds) == stop


def test_round_one_is_checked_against_the_registered_doubling():
    reg = {"attack_change": 0.0175, "reference_change": 0.0}
    assert B.round1_agrees({"attack_change": 0.0175 + 1e-12, "reference_change": 0.0}, reg)
    assert not B.round1_agrees({"attack_change": 0.02, "reference_change": 0.0}, reg)


def test_recompute_substitutes_only_the_converged_cells(tmp_path):
    src, conv = tmp_path / "src", tmp_path / "conv"
    for m, gc, gr in (("fresh0", [0.2, 0.2], [0.1, 0.1]), ("fresh1", [0.3, 0.3], [0.1, 0.1])):
        write(B.R.eval_path(src, f"{m}@rho0.2|C*|D2+H3|profit"), {"seeds": [1, 2], "gain": gc})
        write(B.R.eval_path(src, f"{m}@rho0.2|F111|D2+H3|profit"), {"seeds": [1, 2], "gain": gr})
        write(B.R.eval_path(src, f"{m}@rho0.2|F000|D2+H3|profit"), {"seeds": [1, 2], "gain": [0.5, 0.5]})
    write(conv / "convergence" / (B.R._safe("fresh1@rho0.2|C*|D2+H3|profit") + ".json"),
          {"id": "fresh1@rho0.2|C*|D2+H3|profit", "heldout": {"seeds": [1, 2], "gain": [0.4, 0.4]}, "binding": {"smoke": False}})
    got = B.recompute(src, conv, ("fresh0", "fresh1"), resamples=99, expected={"fresh1@rho0.2|C*|D2+H3|profit": {"smoke": False}})
    assert got["q1"]["frozen"]["estimate"] == pytest.approx(0.15) and got["q1"]["converged"]["estimate"] == pytest.approx(0.2)
    assert got["q4"]["converged"]["markets"]["fresh0"] == pytest.approx(0.4) and got["substituted"] == ["fresh1@rho0.2|C*|D2+H3|profit"]


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_smoke_path_for_one_flagged_fresh_cell(tmp_path, monkeypatch):
    monkeypatch.setattr(B.R, "git_commit", lambda: "pinned-for-the-rerun-check")      # a commit elsewhere during the test must not change the binding
    out = tmp_path / "conv"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--report", str(MAIN / "report/report.json"), "--draw", str(MAIN / "draw/draw.json"),
            "--instances", str(MAIN / "draw/instances.json"), "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"),
            "--cells", "fresh1@rho0.2|F111|D2+H3|profit", "--max-rounds", "2", "--smoke"]
    assert B.main(args) == 0
    rec = read(out / "convergence" / (B.R._safe("fresh1@rho0.2|F111|D2+H3|profit") + ".json"))
    assert 1 <= len(rec["rounds"]) <= 2 and rec["status"] in ("passed", "not passed at the cap") and len(rec["heldout"]["gain"]) == 2
    assert rec["rounds"][0]["restarts_total"] == 2 * rec["restarts"] and (out / "inventory.json").exists()
    assert rec["binding"]["smoke"] is True and read(out / "inventory.json")["files"]["driver"]
    assert B.main(args) == 0                                                     # the saved result is reused under the same binding


# ---- internal review round 1 ----

REG = {"incomplete": True, "attack_change": 0.0175, "reference_change": 0.0,
       "heldout": {"knobs": {"u0": 0.5, "x": 1, "clip": 0}, "seeds": [1, 2], "gain": [0.1, 0.2]}}


def test_round_one_is_compared_with_the_registered_doubling_record():
    r1 = {"attack_change": 0.0175 + 1e-13, "reference_change": 0.0, "heldout": {"knobs": {"u0": 0.5 + 1e-14, "x": 1, "clip": 0}, "seeds": [1, 2], "gain": [0.1, 0.2 + 1e-15]}}
    assert B.compare_round1(REG, r1)["pass"]
    for bad in ({**r1, "attack_change": 0.02}, {**r1, "heldout": {**r1["heldout"], "gain": [0.1, float("nan")]}},
                {**r1, "heldout": {**r1["heldout"], "knobs": {"u0": 0.5, "x": 0, "clip": 0}}}, {**r1, "heldout": {**r1["heldout"], "seeds": [1, 3]}}):
        assert not B.compare_round1(REG, bad)["pass"]


@pytest.mark.parametrize("k,last,gate,cost_ok,want", [(1, {"attack_change": 0.01, "reference_change": 0}, {"pass": False}, True, "round-1 mismatch"),
                                                       (1, {"attack_change": 0.01, "reference_change": 0}, {"pass": True}, True, "continue"),
                                                       (2, {"attack_change": 0.001, "reference_change": 0}, None, True, "passed"),
                                                       (2, {"attack_change": 0.01, "reference_change": 0}, None, False, "cost cap"),
                                                       (3, {"attack_change": 0.01, "reference_change": 0}, None, True, "round cap")])
def test_the_round_decision(k, last, gate, cost_ok, want):
    assert B.decide(k, last, gate, cost_ok, max_rounds=3) == want


def test_settings_and_budgets_are_pinned(tmp_path, monkeypatch):
    monkeypatch.setenv("TOUCHSTONE_LOCKED", "/tmp/x.yaml")
    with pytest.raises(SystemExit, match="TOUCHSTONE_LOCKED"):
        B.main(["--out", str(tmp_path / "o"), "--report", "r", "--draw", "d", "--instances", "i", "--cfgs", "c", "--addendum", "a", "--src", str(tmp_path / "s")])


def test_a_full_run_needs_gate_evidence(tmp_path):
    with pytest.raises(SystemExit, match="evidence"):
        B.check_run_evidence([], smoke=False, gate=False, cells={"a": {"inputs_sha": "i", "driver_sha": "d"}})
    B.check_run_evidence([], smoke=False, gate=True, cells={}); B.check_run_evidence([], smoke=True, gate=False, cells={})


def test_the_claim_is_bounded():
    assert "within three rounds" in B.CLAIM and "not convergence" in B.CLAIM


def test_recompute_refuses_a_smoke_or_unbound_record(tmp_path):
    src, conv = tmp_path / "src", tmp_path / "conv"; rid = "fresh0@rho0.2|C*|D2+H3|profit"
    for r in ("C*", "F111", "F000"):
        write(B.R.eval_path(src, f"fresh0@rho0.2|{r}|D2+H3|profit"), {"seeds": [1, 2], "gain": [0.1, 0.1]})
    write(conv / "convergence" / (B.R._safe(rid) + ".json"), {"id": rid, "heldout": {"seeds": [1, 2], "gain": [0.4, 0.4]}, "binding": {"smoke": True}})
    with pytest.raises(ValueError, match="binding"):
        B.recompute(src, conv, ("fresh0",), resamples=9, expected={rid: {"smoke": False}})


def test_inputs_of_several_cells_are_merged_and_conflicts_refused():
    assert B.merge_inputs([{"a": "1", "b": "2"}, {"b": "2", "c": "3"}]) == {"a": "1", "b": "2", "c": "3"}
    with pytest.raises(SystemExit, match="different hashes"):
        B.merge_inputs([{"a": "1"}, {"a": "9"}])


# ---- draft 3: the nesting cells, embedded incumbent, round 2 corrections ----

NEST = {"cells": {"fresh0@rho0.2|C*": {"shortfall": 0.0061, "best_d2h3": 0.12, "x7": 0.11}, "fresh2@rho0.2|C*": {"shortfall": 0.0003},
                  "headline@rho0.2|F111": {"shortfall": 0.0211, "best_d2h3": 0.07, "x7": 0.05}}}


def test_the_cell_list_adds_x7_cells_with_a_nesting_shortfall_above_the_threshold():
    rep = {"doubling": {"headline@rho0.2|F111|X7-SC|profit": {"kind": "profit", "incomplete": True}, "a|F111|D2+H3|profit": {"kind": "profit", "incomplete": True}}}
    got = B.cells_for(rep, NEST)
    assert got["cells"] == ["a|F111|D2+H3|profit", "headline@rho0.2|F111|X7-SC|profit", "fresh0@rho0.2|C*|X7-SC|profit"]
    assert got["nesting"] == ["fresh0@rho0.2|C*|X7-SC|profit", "headline@rho0.2|F111|X7-SC|profit"]


def test_nesting_cells_run_at_least_two_rounds():
    assert B.decide(1, {"attack_change": 0.0, "reference_change": 0.0}, {"pass": True}, True, max_rounds=3, min_rounds=2) == "continue"
    assert B.decide(2, {"attack_change": 0.0, "reference_change": 0.0}, None, True, max_rounds=3, min_rounds=2) == "passed"


def test_round_incumbents_add_the_embedded_doubled_d2h3_winner_from_round_two_for_nesting_cells():
    prev = {"u0": 0.1}; emb = {"k_F": 1.0}
    assert B.round_incumbents(1, prev, emb) == {"previous_best": prev}                 # round 1 stays the registered doubling
    assert B.round_incumbents(2, prev, emb) == {"previous_best": prev, "embedded_doubled_d2h3": emb}
    assert B.round_incumbents(2, prev, None) == {"previous_best": prev}


def test_shortfall_before_and_after():
    got = B.shortfall_report(NEST, {"fresh0@rho0.2|C*|X7-SC|profit": [0.125, 0.125]})
    assert got["fresh0@rho0.2|C*|X7-SC|profit"] == {"before": 0.0061, "after": pytest.approx(0.12 - 0.125), "best_d2h3": 0.12}


def test_recompute_uses_only_this_runs_validated_cells(tmp_path):
    src, conv = tmp_path / "src", tmp_path / "conv"; rid = "fresh0@rho0.2|C*|D2+H3|profit"; other = "fresh0@rho0.2|F111|D2+H3|profit"
    for r in ("C*", "F111", "F000"):
        write(B.R.eval_path(src, f"fresh0@rho0.2|{r}|D2+H3|profit"), {"seeds": [1, 2], "gain": [0.1, 0.1]})
    good = {"smoke": False, "inputs_sha": "i"}
    write(conv / "convergence" / (B.R._safe(rid) + ".json"), {"id": rid, "heldout": {"seeds": [1, 2], "gain": [0.4, 0.4]}, "binding": good})
    write(conv / "convergence" / (B.R._safe(other) + ".json"), {"id": other, "heldout": {"seeds": [1, 2], "gain": [0.9, 0.9]}, "binding": good})
    got = B.recompute(src, conv, ("fresh0",), resamples=9, expected={rid: good})
    assert got["substituted"] == [rid] and got["q1"]["converged"]["estimate"] == pytest.approx(0.3)          # the stale F111 record is ignored
    for bad in ({"smoke": False, "inputs_sha": "j"}, None):
        with pytest.raises(ValueError):
            B.recompute(src, conv, ("fresh0",), resamples=9, expected={rid: bad} if bad else {rid: good, "x": good})
    write(conv / "convergence" / (B.R._safe(rid) + ".json"), {"id": rid, "heldout": {"seeds": [1, 2], "gain": [0.4, float("nan")]}, "binding": good})
    with pytest.raises(ValueError):
        B.recompute(src, conv, ("fresh0",), resamples=9, expected={rid: good})


def test_gate_records_keep_round_one_for_diagnosis(monkeypatch):
    r1 = {"round": 1, "attack_change": 0.01, "reference_change": 0.0, "best_knobs": {"u0": 0.1}}
    monkeypatch.setattr(B, "run_cell", lambda *a, **k: {"rounds": [r1], "round1_gate": {"pass": False, "problems": ["x"], "heldout_mean": 0.2}})
    monkeypatch.setattr(B, "frozen_doubling", lambda job, out: "local.json")
    got = B.gate_cell({"id": "c"}, "out", "src", "mac", {"smoke": False})
    assert got["round1"] == r1 and got["pass"] is False


def test_the_mac_gate_compares_with_the_frozen_stage_on_the_same_machine(monkeypatch, tmp_path):
    """Flagged cells diverge between the Mac and the pods (2026-11-11: the frozen doubling stage itself differs from the
    registered record on the Mac by the same amounts as round 1), so the Mac gate checks the driver against the frozen
    stage on the same machine, and the pod gate checks it against the registered record."""
    seen = {}
    def fake_run_cell(job, out, max_rounds=3, src=None, cost=None, round_hours=0.0, embedded=None, min_rounds=1, reference=None):
        seen["reference"] = reference; return {"rounds": [{"round": 1}], "round1_gate": {"pass": True}}
    monkeypatch.setattr(B, "run_cell", fake_run_cell)
    monkeypatch.setattr(B, "frozen_doubling", lambda job, out: tmp_path / "local.json")
    B.gate_cell({"id": "c"}, "out", "src", "mac", {"smoke": False}); assert seen["reference"] == tmp_path / "local.json"
    B.gate_cell({"id": "c"}, "out", "src", "pod", {"smoke": False}); assert seen["reference"] is None        # the registered record



# ---- round 3 ----

def _rounds(*changes):
    return [{"round": i + 1, "attack_change": a, "reference_change": 0.0} for i, a in enumerate(changes)]


def test_a_pass_counts_only_from_the_minimum_round_and_agrees_with_the_outcome():
    assert B.passed_round(_rounds(0.001, 0.01, 0.01), min_rounds=2) is None                 # a round-1 pass does not count for a nesting cell
    assert B.final_status(_rounds(0.001, 0.01, 0.01), "round cap", min_rounds=2) == ("not passed at the cap", None)
    assert B.final_status(_rounds(0.01, 0.001), "passed", min_rounds=2) == ("passed", 2)
    assert B.final_status(_rounds(0.01, 0.01), "cost cap", min_rounds=1) == ("stopped at the cost cap", None)


def test_a_cost_stopped_cell_keeps_its_frozen_estimate_and_files_the_partial_result():
    held = {"gain": [0.1, 0.2]}
    assert B.place_heldout("passed", held) == {"heldout": held}
    assert B.place_heldout("not passed at the cap", held) == {"heldout": held}
    assert B.place_heldout("stopped at the cost cap", held) == {"partial": held}


def test_one_round_is_refused_for_a_continuation_run_with_nesting_cells():
    with pytest.raises(SystemExit, match="max-rounds"):
        B.check_rounds(1, gate=False, nesting=["x"])
    B.check_rounds(1, gate=True, nesting=["x"]); B.check_rounds(1, gate=False, nesting=[]); B.check_rounds(2, gate=False, nesting=["x"])


def test_bindings_change_with_the_report_the_registered_doubling_and_the_embedded_incumbent(tmp_path):
    files = {k: tmp_path / k for k in ("report.json", "posthoc.json", "dbl.json")}
    for p in files.values():
        p.write_text("{}")
    d0 = B.deps_for(files["report.json"], files["posthoc.json"], files["dbl.json"], {"u0": 0.1})
    assert {"reset_followup_v2.py", "guards.py", "common.py", "plan", "report", "posthoc", "registered_doubling", "embedded_incumbent"} <= set(d0)
    files["report.json"].write_text('{"changed": 1}'); assert B.deps_for(files["report.json"], files["posthoc.json"], files["dbl.json"], {"u0": 0.1}) != d0
    files["report.json"].write_text("{}"); assert B.deps_for(files["report.json"], files["posthoc.json"], files["dbl.json"], {"u0": 0.2}) != d0
    files["dbl.json"].write_text('{"x": 1}'); assert B.deps_for(files["report.json"], files["posthoc.json"], files["dbl.json"], {"u0": 0.1}) != d0


def test_worker_cost_arguments_keep_the_recorded_accounting_start(tmp_path):
    """Internal review r7 (Astra): the workers rebuild the cost stop; they must count from the recorded open event."""
    f = tmp_path / "a.attempts"; f.write_text("p1 0 start\n"); led = tmp_path / "l.json"; write(led, {"spent": [{"op": "followup", "tag": "c-1", "usd": 2.0}]})
    stop = B.G.paid_cost_stop(4.25, 0.56, started=3600.0, attempts=f, ledger=led, tag="c", clock=lambda: 3600.0)
    args = B.worker_cost_args(stop)
    assert args[2] == 0.0 and args[4] == pytest.approx(2.0)
    w = B.G.CostStop(*args[:3], lambda: 3600.0, *args[4:])
    assert w.allow("round 2", 3.9) is False                                     # 2.00 + 0.56 + 2.18 > 4.25, as the validated stopper says


# ---- shared launcher review r1 (Sol and Astra) ----

def test_a_gate_cell_refused_by_the_inner_admission_is_a_cost_stop_not_a_gate_failure(monkeypatch):
    """A cost stop before round 1 (round1_gate "not run") must not read as a measured mismatch."""
    monkeypatch.setattr(B, "run_cell", lambda *a, **k: {"rounds": [], "status": "stopped at the cost cap", "round1_gate": "not run", "cost": {"stopped_before": "round 1"}})
    got = B.gate_cell({"id": "c"}, "out", "src", "pod", {"smoke": False})
    assert got["pass"] is False and got["cost_stopped"] is True
    monkeypatch.setattr(B, "run_cell", lambda *a, **k: {"rounds": [{"round": 1}], "round1_gate": {"pass": False, "problems": ["x"]}})
    assert B.gate_cell({"id": "c"}, "out", "src", "pod", {"smoke": False})["cost_stopped"] is False


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_the_pod_gate_exits_3_when_the_stop_file_appears_between_the_outer_and_inner_admission(tmp_path, monkeypatch):
    """Real driver path: the outer admission in main() passes; a STOP file then appears; the real run_cell's own admission
    refuses round 1. The gate must exit 3 (a stop), write cost_stop.json, and write no gate record (not exit 4)."""
    import time
    monkeypatch.setattr(B.R, "git_commit", lambda: "pinned-for-the-rerun-check")
    now = time.time(); att = tmp_path / "f2.attempts"; att.write_text(f"pod1 {int(now) - 60} start\n")
    led = tmp_path / "ledger.json"; write(led, {"spent": [{"op": "followup", "tag": "reset-pod", "usd": 1.65}], "reservations": []})
    stop = tmp_path / "STOP"; real = B.run_cell
    def run_cell_after_stop(*a, **k):
        stop.write_text("")                                                         # the launcher's soft deadline passed meanwhile
        return real(*a, **k)
    monkeypatch.setattr(B, "run_cell", run_cell_after_stop)
    out = tmp_path / "conv"; cell = "fresh1@rho0.2|F111|D2+H3|profit"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--report", str(MAIN / "report/report.json"), "--draw", str(MAIN / "draw/draw.json"),
            "--instances", str(MAIN / "draw/instances.json"), "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"),
            "--gate", "--site", "pod", "--cells", cell, "--cap-usd", "4.25", "--usd-per-hour", "0.70", "--started-at", str(int(now) - 60),
            "--attempts", str(att), "--ledger", str(led), "--run-tag", "convergence", "--stop-file", str(stop), "--soft-deadline", str(now + 3600)]
    assert B.main(args) == 3
    assert (out / "cost_stop.json").exists() and not (out / "gate" / (B.R._safe(cell) + "__pod.json")).exists()


# ---- shared launcher review r2 (Sol and Astra) ----

def _pod_gate_args(tmp_path, cells):
    import time
    now = time.time(); att = tmp_path / "f2.attempts"; att.write_text(f"pod1 {int(now) - 60} start\n")
    led = tmp_path / "ledger.json"; write(led, {"spent": [{"op": "followup", "tag": "reset-pod", "usd": 1.65}], "reservations": []})
    out = tmp_path / "conv"
    return out, tmp_path / "STOP", ["--src", str(MAIN / "eval/all"), "--out", str(out), "--report", str(MAIN / "report/report.json"), "--draw", str(MAIN / "draw/draw.json"),
            "--instances", str(MAIN / "draw/instances.json"), "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"),
            "--gate", "--site", "pod", "--cells", ",".join(cells), "--cap-usd", "4.25", "--usd-per-hour", "0.70", "--started-at", str(int(now) - 60),
            "--attempts", str(att), "--ledger", str(led), "--run-tag", "convergence", "--stop-file", str(tmp_path / "STOP"), "--soft-deadline", str(now + 3600)]


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
@pytest.mark.parametrize("second", ["outer", "inner"])
def test_a_measured_gate_mismatch_exits_4_at_once_and_no_later_cell_starts(tmp_path, monkeypatch, second):
    """r2: the first gate cell fails its measured comparison; the second cell would be refused by the outer admission (a
    STOP file appears) or by its own inner admission. Exit 4 with the failed record and the inventory; the second never starts."""
    monkeypatch.setattr(B.R, "git_commit", lambda: "pinned-for-the-rerun-check")
    cells = list(B.GATE_CELLS); calls = []
    out, stop, args = _pod_gate_args(tmp_path, cells)
    def fake_gate_cell(job, *a, **k):
        calls.append(job["id"])
        if len(calls) == 1:
            if second == "outer":
                stop.write_text("")
            return {"stage": "convergence gate", "cell": job["id"], "pass": False, "cost_stopped": False, "cost": None, "comparison": {"pass": False, "problems": ["knob"]}}
        return {"stage": "convergence gate", "cell": job["id"], "pass": False, "cost_stopped": True, "cost": {"stopped_before": "round 1"}}
    monkeypatch.setattr(B, "gate_cell", fake_gate_cell)
    assert B.main(args) == 4
    assert calls == [cells[0]]
    assert read(out / "gate" / (B.R._safe(cells[0]) + "__pod.json"))["pass"] is False and (out / "inventory.json").exists()
    assert not (out / "cost_stop.json").exists()


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_without_a_measured_mismatch_a_later_admission_refusal_still_exits_3(tmp_path, monkeypatch):
    monkeypatch.setattr(B.R, "git_commit", lambda: "pinned-for-the-rerun-check")
    cells = list(B.GATE_CELLS); calls = []
    out, stop, args = _pod_gate_args(tmp_path, cells)
    def fake_gate_cell(job, *a, **k):
        calls.append(job["id"])
        if len(calls) == 1:
            stop.write_text("")
            return {"stage": "convergence gate", "cell": job["id"], "pass": True, "cost_stopped": False, "cost": None, "comparison": {"pass": True}}
        raise AssertionError("the second cell must not start after the STOP file")
    monkeypatch.setattr(B, "gate_cell", fake_gate_cell)
    assert B.main(args) == 3 and calls == [cells[0]] and (out / "cost_stop.json").exists()
