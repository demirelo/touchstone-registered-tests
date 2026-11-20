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
    res = D.run_queue(q, tmp_path, workers=1, gate={"id": "g", "job": {}, "dir": "x"})
    assert calls == [] and "mismatch" in res["gate"]


def _queue(n, churn=0.05):
    return [{"id": f"c{i}", "job": {"id": f"j{i}", "churn": churn, "family": "D2+H3", "provenance": {"id": f"j{i}"}}, "dir": "x"}
            for i in range(n)]


def test_every_continuation_round_is_admitted_with_a_nonzero_estimate(tmp_path, monkeypatch):
    # review gap 2026-11-19: run_cell's round admission used round_hours = 0, so the cost stop could never refuse a round
    seen = []
    monkeypatch.setattr(D, "_cont_one", lambda job, d, mr, cost, hours: seen.append(hours) or {"status": "passed", "provenance": job["provenance"], "round1_gate": EXACT})
    monkeypatch.setattr(D, "run_cells", lambda fn, todo, args, w, dests, extras: (
        [D.write_record(d, {**fn(*a), **e}) for a, d, e in zip(args, dests, extras)], ([], {}))[1])
    D.run_queue(_queue(3), tmp_path, workers=2, gate=_gate())
    assert len(seen) == 4 and all(h > 0.3 for h in seen)
    assert D.round_hours({"churn": 0.05, "family": "D2+H3"}) > D.round_hours({"family": "D2+H3"})


def test_end_codes_mismatch_lost_and_failed(tmp_path, monkeypatch):
    # Run B's codes: 4 a measured round-1 mismatch (outranks the rest), 5 a lost worker (restart estimate saved), 6 a cell error
    ok = lambda job, *a: {"status": "passed", "provenance": job["provenance"], "round1_gate": EXACT}
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
        res = D.run_queue(_queue(3), d, workers=2, gate=_gate())
        assert res["exit"] == code, (outcome, res)
    import json
    assert json.loads((tmp_path / "5" / "continuation" / "lost_cells.json").read_text())["restart_hours"]["1"] > 0


def test_a_gate_mismatch_exits_4(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_cont_one", lambda job, *a: {"status": "stopped: round 1 differs", "provenance": job["provenance"]})
    monkeypatch.setattr(D, "run_cells", _pool([]))
    assert D.run_queue(_queue(2), tmp_path, workers=1, gate=_gate())["exit"] == 4


def test_resume_refuses_a_saved_record_of_another_job(tmp_path, monkeypatch):
    # plan section 5: a resume reuses only records with this run's binding (here the job's provenance)
    import json
    monkeypatch.setattr(D, "_cont_one", lambda job, *a: {"status": "passed", "provenance": job["provenance"]})
    (tmp_path / "continuation").mkdir()
    (tmp_path / "continuation" / "c0.json").write_text(json.dumps({"id": "c0", "status": "passed", "provenance": {"id": "other"}}))
    with pytest.raises(SystemExit):
        D.run_queue(_queue(2), tmp_path, workers=1, gate=_gate())


# ---- review rep-impl-r1 (Sol 3, 4, 5, 6; Astra 4, 7, 8): the gate, exact identity, failure paths, validation -----------

EXACT = {"pass": True, "max_knob_rel": 0.0, "max_change_abs": 0.0, "max_gain_abs": 0.0, "problems": []}


def _gate():
    return {"id": "menu-p0.05|g", "job": {"id": "g", "churn": 0.05, "family": "D2+H3", "provenance": {"id": "g"}}, "dir": "x"}


def _pool(calls, outcome=None):
    """A fake Run B pool: records every call; outcome maps an id to "lost", "fail" or a record override."""
    outcome = outcome or {}
    def f(fn, todo, args, w, dests, extras):
        calls.append([c["id"] for c in todo]); lost, failed = [], {}
        for c, a, d, e in zip(todo, args, dests, extras):
            o = outcome.get(c["id"])
            if o == "lost":
                lost.append(c["id"])
            elif o == "fail":
                failed[c["id"]] = "ValueError: x"
            else:
                D.write_record(d, {**fn(*a), **e, **(o or {})})
        return lost, failed
    return f


def _ok(job, d, mr, cost, hours):
    return {"status": "passed", "provenance": job["provenance"], "round1_gate": EXACT, "max_rounds": mr}


def test_the_gate_runs_in_a_child_even_when_no_cell_is_flagged(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(D, "_cont_one", _ok); monkeypatch.setattr(D, "run_cells", _pool(calls))
    res = D.run_queue([], tmp_path, workers=2, gate=_gate())
    assert calls == [["menu-p0.05|g"]] and res["exit"] == 0
    rec = D.read_record(tmp_path / "continuation" / "gate" / "menu-p0.05_g.json") or D.read_record(next((tmp_path / "continuation" / "gate").iterdir()))
    assert rec["max_rounds"] == 1 and rec["gate"] is True


def test_a_gate_round1_that_is_not_identical_is_a_mismatch(tmp_path, monkeypatch):
    calls = []
    near = {**EXACT, "max_gain_abs": 1e-12}                    # inside Run B's 1e-9 tolerance, but not identical
    monkeypatch.setattr(D, "_cont_one", _ok)
    monkeypatch.setattr(D, "run_cells", _pool(calls, {"menu-p0.05|g": {"round1_gate": near}}))
    res = D.run_queue(_queue(2), tmp_path, workers=2, gate=_gate())
    assert res["exit"] == 4 and calls == [["menu-p0.05|g"]]


def test_a_cost_refused_gate_stops_before_the_queue_with_exit_3(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(D, "_cont_one", _ok)
    monkeypatch.setattr(D, "run_cells", _pool(calls, {"menu-p0.05|g": {"status": "stopped at the cost cap", "round1_gate": "not run"}}))
    res = D.run_queue(_queue(2), tmp_path, workers=2, gate=_gate())
    assert res["exit"] == 3 and calls == [["menu-p0.05|g"]]


def test_a_gate_error_exits_6_and_a_lost_gate_exits_5(tmp_path, monkeypatch):
    import json
    monkeypatch.setattr(D, "_cont_one", _ok)
    monkeypatch.setattr(D, "run_cells", _pool([], {"menu-p0.05|g": "fail"}))
    assert D.run_queue(_queue(2), tmp_path / "f", workers=2, gate=_gate())["exit"] == 6
    monkeypatch.setattr(D, "run_cells", _pool([], {"menu-p0.05|g": "lost"}))
    assert D.run_queue(_queue(2), tmp_path / "l", workers=2, gate=_gate())["exit"] == 5
    assert json.loads((tmp_path / "l" / "continuation" / "lost_cells.json").read_text())["lost"] == ["menu-p0.05|g"]


def test_a_queue_cell_that_is_not_identical_is_a_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_cont_one", _ok)
    monkeypatch.setattr(D, "run_cells", _pool([], {"c1": {"round1_gate": {**EXACT, "max_knob_rel": 2e-16}}}))
    assert D.run_queue(_queue(3), tmp_path, workers=2, gate=_gate())["exit"] == 4


def test_a_cost_stop_in_the_queue_exits_3_and_a_resume_reruns_only_cost_stopped_cells(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(D, "_cont_one", _ok)
    monkeypatch.setattr(D, "run_cells", _pool(calls, {"c2": {"status": "stopped at the cost cap", "round1_gate": "not run"}}))
    assert D.run_queue(_queue(3), tmp_path, workers=2, gate=_gate())["exit"] == 3
    calls.clear(); monkeypatch.setattr(D, "run_cells", _pool(calls))
    assert D.run_queue(_queue(3), tmp_path, workers=2, gate=_gate())["exit"] == 0
    assert calls == [["c2"]]                                   # the gate and the completed cells are reused


def test_a_gate_without_a_measured_comparison_does_not_pass_outside_smoke(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "_cont_one", lambda job, *a: {"status": "passed", "provenance": job["provenance"], "round1_gate": "not compared (smoke)"})
    monkeypatch.setattr(D, "run_cells", _pool([]))
    assert D.run_queue(_queue(1), tmp_path / "p", workers=1, gate=_gate())["exit"] == 4
    assert D.run_queue(_queue(1), tmp_path / "s", workers=1, gate=_gate(), smoke=True)["exit"] == 0


# ---- collect: validation before scoring (Sol 6, 9; Astra 4, 6) --------------------------------------------------------

def _job(m="fresh0", rule="F111", p=0.0):
    jid = f"{m}@rho0.2|{rule}|D2+H3|profit" + (f"|churn{p:g}" if p else "")
    return {"id": jid, "rule": rule, "context": f"{m}@rho0.2", "mkt": {"label": m, "seeds_eval": [11, 12], "cfg": {"N": 4}},
            "provenance": {"id": jid, "b": 1}}


KNOBS = {"u0": 1.0, "x": 0}


def _deps(d, job):
    """The records an evaluation and a doubling record depend on (freeze, reference with its menu, the cell's search),
    written once; returns the evaluation and the doubling dependency hashes."""
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    from sim.records_v2 import sha_file
    ctx = job["context"]; menu = f"{ctx}|F000|D2+H3|profit"; fz, rid = f"freeze/{ctx}", f"reference/{ctx}/{job['rule']}"
    for k, obj in ((fz, {"stage": "freeze"}), (menu, {"stage": "search", "attack": {"best_knobs": {"u0": 2.0, "x": 1}}}),
                   (job["id"], {"stage": "search", "attack": {"best_knobs": KNOBS}})):
        if not R.path_of(d, k).exists():
            _w(R.path_of(d, k), obj)
    if not R.path_of(d, rid).exists():
        _w(R.path_of(d, rid), {"stage": "reference", "upstream": {menu: sha_file(R.path_of(d, menu))}})
    h = lambda ks: {k: sha_file(R.path_of(d, k)) for k in ks}
    return h([fz, rid, job["id"]]), h([fz, rid, job["id"], menu])


def _cell(base, job, p, kind="menu", gain=(0.1, 0.3), incomplete=False, ev_prov=None, seeds=None, doubling=True, ev=True):
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    d = base / f"{kind}-p{p:g}"
    h = {"seeds": list(seeds or job["mkt"]["seeds_eval"]), "gain": list(gain), "profit_attack": [g + 1 for g in gain],
         "profit_ref": [1.0] * len(gain), "sstar": [4.0] * len(gain), "eff_attack": [0.9] * len(gain)}
    eup, dup = _deps(d, job)
    if ev:
        _w(R.eval_path(d, job["id"]), {"stage": "evaluate", "id": job["id"], "provenance": ev_prov or job["provenance"], **h,
                                       "upstream": eup})
    if doubling:
        _w(d / "doubling" / (R._safe(job["id"]) + ".json"), {"stage": "doubling", "id": job["id"], "provenance": job["provenance"],
                                                             "kind": "profit", "attack_change": 0.01 if incomplete else 0.0,
                                                             "reference_change": 0.0, "incomplete": incomplete,
                                                             "heldout": {"knobs": dict(KNOBS), **h}, "upstream": dup})
    return d


def _cont(base, kind, p, job, status="passed", gain=(0.5, 0.7), gate=EXACT, sub=""):
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    key = D._key(kind, p, job["id"])
    h = {"knobs": {"u0": 3.0, "x": 2}, "seeds": job["mkt"]["seeds_eval"], "gain": list(gain), "profit_attack": [g + 1 for g in gain],
         "profit_ref": [1.0] * len(gain), "sstar": [4.0] * len(gain), "eff_attack": [0.8] * len(gain)}
    _w(base / "continuation" / sub / (R._safe(key) + ".json"), {"stage": "convergence", "id": key, "status": status,
                                                               "provenance": job["provenance"], "round1_gate": gate,
                                                               "rounds": [{"round": 1}], "heldout": h})
    return key


def _gi(job, p=0.05):
    """The gate item collect needs (rep_v2.gate_item's shape)."""
    return {"id": D._key("menu", p, job["id"]), "job": job}


def test_collect_skips_invalid_base_records(tmp_path):
    a, b, c = _job("fresh0"), _job("fresh1"), _job("fresh2")
    _cell(tmp_path, a, 0, ev_prov={"id": "other"}); _cell(tmp_path, b, 0, seeds=[12, 11]); _cell(tmp_path, c, 0, doubling=False)
    col = D.collect(tmp_path, {("menu", 0.0): [a, b, c]}, gate=None)
    assert col["frozen"].get("0", {}) == {} and len(col["unscorable"]) == 3


def test_continuation_applies_only_to_flagged_cells(tmp_path):
    a, b = _job("fresh0"), _job("fresh1")
    _cell(tmp_path, a, 0, incomplete=False); _cell(tmp_path, b, 0, incomplete=True)
    _cont(tmp_path, "menu", 0.0, a)                                  # an unflagged cell's record (e.g. the gate's) is ignored
    gj = _job("fresh0", p=0.05); _cont(tmp_path, "menu", 0.05, gj, sub="gate")
    col = D.collect(tmp_path, {("menu", 0.0): [a, b]}, gate=_gi(gj))
    assert col["primary"]["0"]["rep0"]["R3"]["gain"] == [0.1, 0.3]
    assert col["primary"]["0"]["rep1"]["R3"]["gain"] == [0.1, 0.3] and col["counts"]["not continued"] == 1


def test_a_mismatch_record_is_seen_even_when_the_evaluation_is_missing(tmp_path):
    a = _job("fresh0")
    _cell(tmp_path, a, 0, incomplete=True, ev=False)
    _cont(tmp_path, "menu", 0.0, a, status="stopped: round 1 differs from the registered doubling")
    assert D.collect(tmp_path, {("menu", 0.0): [a]}, gate=None)["primary"] is None


def test_continued_winners_need_an_identical_gate(tmp_path):
    a = _job("fresh0"); gj = {**_job("fresh0", p=0.05)}
    _cell(tmp_path, a, 0, incomplete=True); _cont(tmp_path, "menu", 0.0, a)
    assert D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))["primary"] is None      # no gate record
    _cont(tmp_path, "menu", 0.05, gj, sub="gate")
    col = D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))
    assert col["primary"]["0"]["rep0"]["R3"]["gain"] == [0.5, 0.7] and col["counts"]["continued"] == 1
    t = col["primary"]["0"]["rep0"]["R3"]
    assert all(abs((x - y) - g) < 1e-12 for x, y, g in zip(t["attack"], t["reference"], t["gain"]))


def test_primary_audit_uses_the_continued_r3_winners_diagnostics(tmp_path):
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    a0, a5 = _job("fresh0"), _job("fresh0", p=0.05)
    d0 = _cell(tmp_path, a0, 0); d5 = _cell(tmp_path, a5, 0.05, incomplete=True)
    sh = lambda served, audited: {"per_episode": [{"focal": [[served, audited]]}]}
    for d, ck in ((d0, "fresh0@rho0.2|F111"), (d5, "fresh0@rho0.2|F111")):
        _w(d / "diagnostics.json", {"cells": {ck: {"base": {"knobs": KNOBS, "seeds": [11, 12], "normalized": [0.1, 0.2],
                                                             "shares": sh(100, 30)}}}})
    gj = _job("fresh1", p=0.05); _cont(tmp_path, "menu", 0.05, gj, sub="gate"); gid = _gi(gj)
    key = _cont(tmp_path, "menu", 0.05, a5)
    col = D.collect(tmp_path, {("menu", 0.0): [a0], ("menu", 0.05): [a5]}, gate=gid)
    assert col["audit"]["frozen"]["0.05"]["rep0"] == (30, 100) and "rep0" not in col["audit"]["primary"].get("0.05", {})
    _w(tmp_path / "continuation" / "diagnostics" / (R._safe(key) + ".json"),
       {"stage": "continued diagnostics", "id": key, "provenance": a5["provenance"], "knobs": {"u0": 3.0, "x": 2},
        "seeds": [11, 12], "normalized": [0.1, 0.2], "shares": sh(100, 5)})
    col = D.collect(tmp_path, {("menu", 0.0): [a0], ("menu", 0.05): [a5]}, gate=gid)
    assert col["audit"]["primary"]["0.05"]["rep0"] == (5, 100) and col["audit"]["primary"]["0"]["rep0"] == (30, 100)


def _fake_diag(job, knobs):
    return {"stage": "continued diagnostics", "provenance": job["provenance"], "knobs": dict(knobs), "seeds": [11, 12],
            "normalized": [0.1, 0.2], "shares": {"per_episode": [{"focal": [[10, 1]]}]}}


def test_continued_diagnostics_run_only_for_continued_r3_menu_cells_at_p0_and_p005(tmp_path, monkeypatch):
    calls = []
    a0, a3, a5, c5 = _job("fresh0"), _job("fresh0", p=0.03), _job("fresh0", p=0.05), _job("fresh0", rule="C*", p=0.05)
    for j, p in ((a0, 0), (a3, 0.03), (a5, 0.05), (c5, 0.05)):
        _cell(tmp_path, j, p, incomplete=True); _cont(tmp_path, "menu", p, j)
    _cont(tmp_path, "menu", 0.0, a0)                                   # passed: continued
    _cont(tmp_path, "menu", 0.05, a5, status="stopped at the cost cap")   # cost-stopped: keeps the frozen winner, no run
    monkeypatch.setattr(D, "run_cells", _pool(calls))
    monkeypatch.setattr(D, "_diag_cont", _fake_diag)
    jobs = {("menu", 0.0): [a0], ("menu", 0.03): [a3], ("menu", 0.05): [a5, c5]}
    res = D.run_diagnostics(tmp_path, jobs, workers=2)
    assert calls == [[D._key("menu", 0.0, a0["id"])]] and res["exit"] == 0
    calls.clear(); D.run_diagnostics(tmp_path, jobs, workers=2)
    assert calls == []                                                 # saved records with this binding are reused


# ---- review rep-impl-r2 (Sol 2, 3, 4, 6; Astra 2, 3, 4, 6): every record collect reads is checked before use ----------

def _rw(path, **change):
    """Rewrite one record with fields changed (None removes the field)."""
    import json
    r = json.loads(path.read_text())
    for k, v in change.items():
        if v is None:
            r.pop(k, None)
        else:
            r[k] = v
    path.write_text(json.dumps(r))


def _paths(base, job, p=0.0, kind="menu"):
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    d = base / f"{kind}-p{p:g}"
    return R.eval_path(d, job["id"]), d / "doubling" / (R._safe(job["id"]) + ".json")


@pytest.mark.parametrize("which,change", [
    ("ev", {"stage": "doubling"}), ("ev", {"id": "x"}), ("ev", {"upstream": {}}), ("ev", {"upstream": "drop-one"}),
    ("ev", {"upstream": "wrong-hash"}),
    ("db", {"stage": "evaluate"}), ("db", {"kind": "welfare"}), ("db", {"heldout": None}), ("db", {"upstream": {}}),
    ("db", {"upstream": "wrong-hash"}), ("db", {"attack_change": float("nan")}), ("db", {"incomplete": True}),
    ("db", {"heldout": "no-knobs"})])
def test_collect_checks_stage_id_dependencies_hashes_values_and_the_flag(tmp_path, which, change):
    a = _job("fresh0"); _cell(tmp_path, a, 0)
    ev, db = _paths(tmp_path, a)
    path = ev if which == "ev" else db
    import json
    r = json.loads(path.read_text())
    if change.get("upstream") == "drop-one":
        change = {"upstream": dict(list(r["upstream"].items())[1:])}
    elif change.get("upstream") == "wrong-hash":
        change = {"upstream": {k: "0" * 64 for k in r["upstream"]}}
    elif change.get("heldout") == "no-knobs":
        change = {"heldout": {k: v for k, v in r["heldout"].items() if k != "knobs"}}
    _rw(path, **change)
    col = D.collect(tmp_path, {("menu", 0.0): [a]}, gate=None)
    assert len(col["unscorable"]) == 1 and col["frozen"].get("0", {}) == {}


def test_valid_fixture_cells_are_scorable(tmp_path):
    a = _job("fresh0"); _cell(tmp_path, a, 0); _cell(tmp_path, _job("fresh1"), 0, incomplete=True)
    assert D.collect(tmp_path, {("menu", 0.0): [a, _job("fresh1")]}, gate=None)["unscorable"] == []


def _flagged_with_gate(tmp_path, **cont):
    a = _job("fresh0"); gj = _job("fresh0", p=0.05)
    _cell(tmp_path, a, 0, incomplete=True); key = _cont(tmp_path, "menu", 0.0, a, **cont)
    _cont(tmp_path, "menu", 0.05, gj, sub="gate")
    return a, gj, key


@pytest.mark.parametrize("cont", [{"status": "something else"}, {"gate": "not compared (smoke)"},
                                  {"gate": {**EXACT, "max_gain_abs": 1e-15}}])
def test_a_continued_winner_needs_a_known_status_and_its_own_identical_comparison(tmp_path, cont):
    a, gj, _ = _flagged_with_gate(tmp_path, **cont)
    col = D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))
    assert col["primary"] is None and col["problems"]


def test_a_continuation_record_without_rounds_or_with_another_id_is_refused(tmp_path):
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    a, gj, key = _flagged_with_gate(tmp_path)
    p = tmp_path / "continuation" / (R._safe(key) + ".json")
    _rw(p, rounds=[]); assert D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))["primary"] is None
    _rw(p, rounds=[{"round": 1}], id="other"); assert D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))["primary"] is None


def test_a_gate_of_another_job_does_not_pass(tmp_path):
    a, gj, _ = _flagged_with_gate(tmp_path)
    other = {**gj, "provenance": {"id": "another run"}}
    col = D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(other))
    assert col["gate_ok"] is False and col["primary"] is None


def test_the_primary_set_needs_the_gate_even_when_no_cell_is_flagged(tmp_path):
    a = _job("fresh0"); gj = _job("fresh0", p=0.05); _cell(tmp_path, a, 0)
    assert D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))["primary"] is None
    _cont(tmp_path, "menu", 0.05, gj, sub="gate")
    assert D.collect(tmp_path, {("menu", 0.0): [a]}, gate=_gi(gj))["primary"] is not None


def _diag_setup(tmp_path, base=None):
    a0, a5 = _job("fresh0"), _job("fresh0", p=0.05)
    d0 = _cell(tmp_path, a0, 0); d5 = _cell(tmp_path, a5, 0.05, incomplete=True)
    sh = {"per_episode": [{"focal": [[100, 30]]}]}
    row = {"knobs": KNOBS, "seeds": [11, 12], "normalized": [0.1, 0.2], "shares": sh, **(base or {})}
    for d in (d0, d5):
        _w(d / "diagnostics.json", {"cells": {"fresh0@rho0.2|F111": {"base": row}}})
    gj = _job("fresh1", p=0.05); _cont(tmp_path, "menu", 0.05, gj, sub="gate")
    key = _cont(tmp_path, "menu", 0.05, a5)
    return {("menu", 0.0): [a0], ("menu", 0.05): [a5]}, _gi(gj), a5, key


@pytest.mark.parametrize("base", [{"seeds": [12, 11]}, {"knobs": {"u0": 9.0, "x": 0}}, {"normalized": [float("nan"), 0.2]},
                                  {"shares": {"per_episode": [{"focal": [[100]]}]}},
                                  {"shares": {"per_episode": [{"focal": [[100, 30]]}, {"focal": [[1, 0], [2, 0]]}]}}])
def test_frozen_diagnostics_are_checked_before_their_audit_counts_are_used(tmp_path, base):
    jobs, gate, _, _ = _diag_setup(tmp_path, base)
    col = D.collect(tmp_path, jobs, gate=gate)
    assert col["audit"]["frozen"].get("0", {}) == {} and col["audit"]["frozen"].get("0.05", {}) == {}


@pytest.mark.parametrize("change", [{"provenance": {"id": "other"}}, {"seeds": [12, 11]}, {"knobs": KNOBS}, {"id": "x"},
                                    {"stage": "diagnostics"}])
def test_continued_diagnostics_are_checked_before_use(tmp_path, change):
    import convergence_v2  # noqa: F401
    import revision_v2 as R
    jobs, gate, a5, key = _diag_setup(tmp_path)
    rec = {"stage": "continued diagnostics", "id": key, "provenance": a5["provenance"], "knobs": {"u0": 3.0, "x": 2},
           "seeds": [11, 12], "normalized": [0.1, 0.2], "shares": {"per_episode": [{"focal": [[100, 5]]}]}}
    p = tmp_path / "continuation" / "diagnostics" / (R._safe(key) + ".json")
    _w(p, rec); assert D.collect(tmp_path, jobs, gate=gate)["audit"]["primary"]["0.05"]["rep0"] == (5, 100)
    _w(p, {**rec, **change}); assert "rep0" not in D.collect(tmp_path, jobs, gate=gate)["audit"]["primary"].get("0.05", {})


def _disk_pool(calls, lose):
    """Like convergence_v2.run_cells: a lost worker saves nothing, and a cell is lost when no record is on disk."""
    def f(fn, todo, args, w, dests, extras):
        calls.append([c["id"] for c in todo])
        for c, a, d, e in zip(todo, args, dests, extras):
            if c["id"] not in lose:
                D.write_record(d, {**fn(*a), **e})
        return [c["id"] for c, d in zip(todo, dests) if D.read_record(d) is None], {}
    return f


def test_a_lost_worker_on_resume_is_seen_behind_a_saved_cost_stopped_record(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(D, "_cont_one", _ok)
    q = _queue(3)
    monkeypatch.setattr(D, "run_cells", _pool(calls, {"c2": {"status": "stopped at the cost cap", "round1_gate": "not run"}}))
    assert D.run_queue(q, tmp_path, 2, gate=_gate())["exit"] == 3
    monkeypatch.setattr(D, "run_cells", _disk_pool(calls, {"c2"}))
    res = D.run_queue(q, tmp_path, 2, gate=_gate())
    assert res["exit"] == 5 and res["lost"] == ["c2"]
    assert (tmp_path / "continuation" / "lost_cells.json").exists()


def test_a_saved_continuation_record_with_an_unknown_status_is_not_reused(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(D, "_cont_one", _ok)
    q = _queue(1)
    monkeypatch.setattr(D, "run_cells", _pool(calls, {"c0": {"status": "odd"}}))
    D.run_queue(q, tmp_path, 1, gate=_gate())
    monkeypatch.setattr(D, "run_cells", _pool(calls))
    with pytest.raises(SystemExit):
        D.run_queue(q, tmp_path, 1, gate=_gate())


def test_a_lost_diagnostics_worker_writes_the_restart_estimate(tmp_path, monkeypatch):
    import json
    a0 = _job("fresh0"); _cell(tmp_path, a0, 0, incomplete=True); key = _cont(tmp_path, "menu", 0.0, a0)
    monkeypatch.setattr(D, "run_cells", _disk_pool([], {key}))
    monkeypatch.setattr(D, "_diag_cont", _fake_diag)
    res = D.run_diagnostics(tmp_path, {("menu", 0.0): [a0]}, workers=2)
    lc = json.loads((tmp_path / "continuation" / "lost_cells.json").read_text())
    assert res["exit"] == 5 and lc["lost"] == [key] and lc["restart_hours"]["3"] > 0
