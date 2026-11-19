"""Tests for the replication's continuation stage and record loader (plan sections 2 and 4)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rep_collect as D  # noqa: E402


def _w(p, obj):
    import json
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj))


def test_winner_selection_rules(tmp_path):
    # plan section 4: passed and round-cap cells use their continued winner; cost-stopped or missing cells keep the frozen one
    frozen = [0.1, 0.2]
    rec = lambda status, **k: {"status": status, **k}
    assert D.select_winner(frozen, None) == (frozen, "frozen")
    assert D.select_winner(frozen, rec("passed", heldout={"gain": [0.3, 0.4]})) == ([0.3, 0.4], "continued")
    assert D.select_winner(frozen, rec("not passed at the cap", heldout={"gain": [0.5, 0.6]})) == ([0.5, 0.6], "unresolved")
    assert D.select_winner(frozen, rec("stopped at the cost cap", partial={"gain": [9, 9]})) == (frozen, "stopped")
    assert D.select_winner(frozen, rec("passed", heldout={"gain": [float("nan"), 0.1]})) == (frozen, "not continued")
    with pytest.raises(D.Round1Mismatch):
        D.select_winner(frozen, rec("stopped: round 1 differs from the registered doubling"))


def test_rule_names_map_to_the_analysis_labels():
    assert D.analysis_rule("menu", "F111") == "R3" and D.analysis_rule("menu", "F000") == "B3"
    assert D.analysis_rule("menu", "C*") == "C*" and D.analysis_rule("cthr", "C*") == "C-thr"


def test_the_worker_function_is_picklable():
    import pickle
    assert pickle.loads(pickle.dumps(D._cont_one)) is D._cont_one


def test_a_saved_round1_mismatch_stops_the_queue_on_resume(tmp_path, monkeypatch):
    import json
    calls = []
    monkeypatch.setattr(D, "_cont_one", lambda *a: calls.append(a) or {"status": "passed"})
    q = [{"id": "a", "job": {}, "dir": "x"}, {"id": "b", "job": {}, "dir": "x"}]
    (tmp_path / "continuation").mkdir()
    (tmp_path / "continuation" / "a.json").write_text(json.dumps({"id": "a", "status": "stopped: round 1 differs from the registered doubling"}))
    res = D.run_queue(q, tmp_path, workers=1)
    assert calls == [] and "mismatch" in res["gate"]


def _queue(n, churn=0.05):
    return [{"id": f"c{i}", "job": {"id": f"j{i}", "churn": churn, "family": "D2+H3", "provenance": {"id": f"j{i}"}}, "dir": "x"}
            for i in range(n)]


def test_every_continuation_round_is_admitted_with_a_nonzero_estimate(tmp_path, monkeypatch):
    # review gap 2026-11-19: run_cell's round admission used round_hours = 0, so the cost stop could never refuse a round
    seen = []
    monkeypatch.setattr(D, "_cont_one", lambda job, d, mr, cost, hours: seen.append(hours) or {"status": "passed", "provenance": job["provenance"]})
    monkeypatch.setattr(D, "run_cells", lambda fn, todo, args, w, dests, extras: (
        [D.write_record(d, {**fn(*a), **e}) for a, d, e in zip(args, dests, extras)], ([], {}))[1])
    D.run_queue(_queue(3), tmp_path, workers=2)
    assert len(seen) == 3 and all(h > 0.3 for h in seen)
    assert D.round_hours({"churn": 0.05, "family": "D2+H3"}) > D.round_hours({"family": "D2+H3"})


def test_end_codes_mismatch_lost_and_failed(tmp_path, monkeypatch):
    # Run B's codes: 4 a measured round-1 mismatch (outranks the rest), 5 a lost worker (restart estimate saved), 6 a cell error
    ok = lambda job, *a: {"status": "passed", "provenance": job["provenance"]}
    monkeypatch.setattr(D, "_cont_one", ok)
    def cells(outcome):
        def f(fn, todo, args, w, dests, extras):
            lost, failed = [], {}
            for c, a, d, e in zip(todo, args, dests, extras):
                o = outcome.get(c["id"], "ok")
                if o == "lost":
                    lost.append(c["id"])
                elif o == "fail":
                    failed[c["id"]] = "ValueError: x"
                else:
                    D.write_record(d, {**fn(*a), **e, **({"status": "stopped: round 1 differs"} if o == "mm" else {})})
            return lost, failed
        return f
    for outcome, code in (({}, 0), ({"c2": "lost"}, 5), ({"c2": "fail"}, 6), ({"c1": "mm", "c2": "lost"}, 4)):
        d = tmp_path / str(code); monkeypatch.setattr(D, "run_cells", cells(outcome))
        res = D.run_queue(_queue(3), d, workers=2)
        assert res["exit"] == code, (outcome, res)
    import json
    assert json.loads((tmp_path / "5" / "continuation" / "lost_cells.json").read_text())["restart_hours"]["1"] > 0


def test_a_gate_mismatch_exits_4(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_cont_one", lambda job, *a: {"status": "stopped: round 1 differs", "provenance": job["provenance"]})
    assert D.run_queue(_queue(2), tmp_path, workers=1)["exit"] == 4


def test_resume_refuses_a_saved_record_of_another_job(tmp_path, monkeypatch):
    # plan section 5: a resume reuses only records with this run's binding (here the job's provenance)
    import json
    monkeypatch.setattr(D, "_cont_one", lambda job, *a: {"status": "passed", "provenance": job["provenance"]})
    (tmp_path / "continuation").mkdir()
    (tmp_path / "continuation" / "c0.json").write_text(json.dumps({"id": "c0", "status": "passed", "provenance": {"id": "other"}}))
    with pytest.raises(SystemExit):
        D.run_queue(_queue(2), tmp_path, workers=1)
