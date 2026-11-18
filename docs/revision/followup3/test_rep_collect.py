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
