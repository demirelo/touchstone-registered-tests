"""Tuning v2 (design 4, 3.3): the common objective, comparator selection, whole-system tuning, and C*/S2 fixture searches."""
import json

import pytest


def test_margin_and_objective_min_over_markets_and_families():
    from scripts.tune_v2 import margin, objective
    assert margin(0.99, 0.0) == pytest.approx(0.1) and margin(0.95, 0.27) == pytest.approx(0.05 / 0.9) and margin(1.0, 0.27) == pytest.approx(0.1)
    m = {"headline": {"D2": 0.5, "D2+H3": 0.2, "X7-SC": 0.3}, "dev0": {"D2": 0.4, "D2+H3": -0.1, "X7-SC": 0.6}}
    assert objective(m) == -0.1


def test_grid_sizes():
    from scripts.tune_v2 import COMMON_GRID, comparator_grid
    assert len(comparator_grid()) == 12 and len(COMMON_GRID) == 16
    assert (0.14, 3) in COMMON_GRID and (0.08, 50) in COMMON_GRID


def test_ties_by_grid_order():
    from scripts.tune_v2 import rank
    scores = [{"tag": "a", "objective": 0.1}, {"tag": "b", "objective": 0.3}, {"tag": "c", "objective": 0.3}, {"tag": "d", "objective": 0.2}]
    assert [s["tag"] for s in rank(scores)] == ["b", "c", "d", "a"]


def _fake_score(calls):
    """A per-(configuration, market) scorer: the objective of a configuration is the minimum of its markets' margins."""
    def f(rule, spec, label, budget, recheck):
        calls.append((rule, json.dumps(spec, sort_keys=True), recheck))
        tol, L = spec["tol"], spec["L"]
        v = -abs(tol - 0.12) - abs(L - 10) / 100 + (0.001 if spec.get("cred", {}).get("variant") == "mem" else 0)
        return {"label": label, "margins": {"D2": v}, "detail": {}, "episodes": 1}
    return f


def test_recheck_top2_on_dev_val(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []
    monkeypatch.setattr(TV, "_score_market", _fake_score(calls))
    res = TV.tune_system("B3-t", ["headline"], tmp_path, smoke=True)
    rechecks = [c for c in calls if c[2]]
    assert len([c for c in calls if not c[2]]) == 16 and len(rechecks) == 2
    assert res["best_params"] == {"tol": 0.12, "L": 10} and (tmp_path / "tuned_B3-t.json").exists()


def test_c_t_keeps_comparator_variant(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []
    monkeypatch.setattr(TV, "_score_market", _fake_score(calls))
    cred = {"variant": "mem", "K": 6, "M": 50}
    res = TV.tune_system("C*-t", ["headline"], tmp_path, cred=cred, smoke=True)
    assert all(json.loads(c[1])["cred"] == cred for c in calls) and set(res["best_params"]) == {"tol", "L"} and res["cred"] == cred


def test_select_comparator(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []
    monkeypatch.setattr(TV, "_score_market", _fake_score(calls))
    res = TV.select_comparator(["headline"], tmp_path, smoke=True)
    assert len([c for c in calls if not c[2]]) == 12 and len([c for c in calls if c[2]]) == 2
    assert res["cred"]["variant"] == "mem" and json.loads((tmp_path / "comparator.json").read_text())["cred"] == res["cred"]


def test_tune_three_systems_and_no_fixture_searches():
    import scripts.tune_v2 as TV
    assert TV.SYSTEMS == ("B3-t", "R3-t", "C*-t") and not hasattr(TV, "fixture_searches")
    with pytest.raises(SystemExit):
        TV.main(["--select", "fixtures", "--markets", "headline", "--out", "x"])
    with pytest.raises(SystemExit):
        TV.main(["--select", "R4-t", "--markets", "headline", "--out", "x"])


@pytest.mark.slow
def test_smoke_run_writes_logs(tmp_path):
    import scripts.tune_v2 as TV
    res = TV.tune_system("B3-t", ["dev0"], tmp_path, smoke=True, grid_limit=1)
    assert res["episodes"] > 0 and (tmp_path / "tuned_B3-t.json").exists() and any((tmp_path / "log").iterdir())


def test_cli_accepts_pod_arguments(tmp_path, monkeypatch):
    import scripts.tune_v2 as TV
    monkeypatch.setattr(TV, "_score_market", _fake_score([])); monkeypatch.setattr(TV, "ProcessPoolExecutor", _Recorder)
    assert TV.main(["--select", "comparator", "--markets", "dev0", "--smoke", "--workers", "2", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "comparator.json").exists()


def test_recheck_ties_keep_grid_order(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    def f(rule, spec, label, budget, recheck):
        if not recheck:                                       # inner prefers L = 10 over L = 3
            return {"label": label, "margins": {"D2": {3: 0.1, 10: 0.2}.get(spec["L"], -1.0)}, "detail": {}, "episodes": 1}
        return {"label": label, "margins": {"D2": 0.5 if spec["L"] in (3, 10) else -1.0}, "detail": {}, "episodes": 1}
    monkeypatch.setattr(TV, "_score_market", f)
    monkeypatch.setattr(TV, "COMMON_GRID", [(0.08, 3), (0.08, 10), (0.08, 20)])
    assert TV.tune_system("B3-t", ["headline"], tmp_path, smoke=True)["best_params"] == {"tol": 0.08, "L": 3}


# ---- operations plan Task 2: many cores, fixture provenance ---------------------------------------------------------------

class _Recorder:
    """Stands in for ProcessPoolExecutor: runs inline and records max_workers and every submitted call."""
    seen = []

    def __init__(self, max_workers=None):
        _Recorder.seen.append(("pool", max_workers))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def map(self, fn, *its):
        out = []
        for args in zip(*its):
            _Recorder.seen.append(("call", args[2] if len(args) > 2 else args)); out.append(fn(*args))
        return iter(out)


def test_workers_submit_one_task_per_configuration_and_market(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []; _Recorder.seen = []
    monkeypatch.setattr(TV, "_score_market", _fake_score(calls)); monkeypatch.setattr(TV, "ProcessPoolExecutor", _Recorder)
    monkeypatch.setattr(TV, "COMMON_GRID", [(0.08, 3), (0.12, 10), (0.16, 20)])
    TV.tune_system("B3-t", ["headline", "dev0"], tmp_path, smoke=True, workers=2)
    pools = [x for x in _Recorder.seen if x[0] == "pool"]; submitted = [x for x in _Recorder.seen if x[0] == "call"]
    assert pools == [("pool", 2), ("pool", 2)]                      # inner, then rechecks
    assert len(submitted) == 3 * 2 + 2 * 2 and {x[1] for x in submitted} == {"headline", "dev0"}


def test_parallel_logs_hold_every_market(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    def f(rule, spec, label, budget, recheck):
        return {"label": label, "margins": {"D2": 0.1}, "detail": {"D2": {"eff": 0.95, "gain": 0.0, "attack": {"u0": 0.1}}, "reference": {"name": "honest_max"}}, "episodes": 2}
    monkeypatch.setattr(TV, "_score_market", f); monkeypatch.setattr(TV, "ProcessPoolExecutor", _Recorder)
    monkeypatch.setattr(TV, "COMMON_GRID", [(0.16, 10)])
    res = TV.tune_system("R3-t", ["headline", "dev0", "dev1"], tmp_path, smoke=True, workers=3)
    logs = [json.loads(p.read_text()) for p in (tmp_path / "log").glob("*.json")]
    assert logs and all(set(d["detail"]) == {"headline", "dev0", "dev1"} for d in logs) and res["episodes"] == 2 * 3 * 2
    assert {"budget_inner", "budget_full", "commit", "smoke", "markets"} <= set(res)


@pytest.mark.slow
def test_parallel_tuning_equals_serial(tmp_path):
    import scripts.tune_v2 as TV
    a = TV.tune_system("B3-t", ["dev0"], tmp_path / "a", smoke=True, grid_limit=2, workers=1)
    b = TV.tune_system("B3-t", ["dev0"], tmp_path / "b", smoke=True, grid_limit=2, workers=2)
    strip = lambda r: [{k: v for k, v in s.items()} for s in r]
    assert strip(a["scores"]) == strip(b["scores"]) and strip(a["rechecked"]) == strip(b["rechecked"]) and a["best_params"] == b["best_params"]
    for p in (tmp_path / "b" / "log").glob("*.json"):
        assert set(json.loads(p.read_text())["detail"]) == {"dev0"}
