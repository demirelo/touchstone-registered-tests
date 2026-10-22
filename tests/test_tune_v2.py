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
    def f(rule, spec, markets, budget, recheck, log):
        calls.append((rule, json.dumps(spec, sort_keys=True), recheck))
        tol, L = spec["tol"], spec["L"]
        v = -abs(tol - 0.12) - abs(L - 10) / 100 + (0.001 if spec.get("cred", {}).get("variant") == "mem" else 0)
        return {"objective": v, "margins": {}, "episodes": 1}
    return f


def test_recheck_top2_on_dev_val(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []
    monkeypatch.setattr(TV, "score_config", _fake_score(calls))
    res = TV.tune_system("B3-t", ["headline"], tmp_path, smoke=True)
    rechecks = [c for c in calls if c[2]]
    assert len([c for c in calls if not c[2]]) == 16 and len(rechecks) == 2
    assert res["best_params"] == {"tol": 0.12, "L": 10} and (tmp_path / "tuned_B3-t.json").exists()


def test_c_t_keeps_comparator_variant(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []
    monkeypatch.setattr(TV, "score_config", _fake_score(calls))
    cred = {"variant": "mem", "K": 6, "M": 50}
    res = TV.tune_system("C*-t", ["headline"], tmp_path, cred=cred, smoke=True)
    assert all(json.loads(c[1])["cred"] == cred for c in calls) and set(res["best_params"]) == {"tol", "L"} and res["cred"] == cred


def test_select_comparator(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    calls = []
    monkeypatch.setattr(TV, "score_config", _fake_score(calls))
    res = TV.select_comparator(["headline"], tmp_path, smoke=True)
    assert len([c for c in calls if not c[2]]) == 12 and len([c for c in calls if c[2]]) == 2
    assert res["cred"]["variant"] == "mem" and json.loads((tmp_path / "comparator.json").read_text())["cred"] == res["cred"]


def test_fixture_searches_count(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    seen = []
    monkeypatch.setattr(TV, "market_searches", lambda rule, spec, mkt, budget, cache: seen.append((rule, mkt["label"])) or {"attacks": {"D2": {}, "D2+H3": {}, "X7-SC": {}}, "reference": {"name": "honest_max"}, "episodes": 0})
    monkeypatch.setattr(TV, "_market", lambda label, smoke: {"label": label})
    res = TV.fixture_searches(["headline", "dev0", "dev1"], tmp_path, cred={"variant": "thr", "K": 6, "M": None}, smoke=True)
    assert seen == [("C*/S2", m) for m in ("headline", "dev0", "dev1")]
    assert sum(len(v["attacks"]) for v in res["markets"].values()) == 9 and (tmp_path / "fixture_cstar_s2.json").exists()


@pytest.mark.slow
def test_smoke_run_writes_logs(tmp_path):
    import scripts.tune_v2 as TV
    res = TV.tune_system("B3-t", ["dev0"], tmp_path, smoke=True, grid_limit=1)
    assert res["episodes"] > 0 and (tmp_path / "tuned_B3-t.json").exists() and any((tmp_path / "log").iterdir())


def test_cli_accepts_pod_arguments(tmp_path, monkeypatch):
    import scripts.tune_v2 as TV
    monkeypatch.setattr(TV, "score_config", _fake_score([]))
    assert TV.main(["--select", "comparator", "--markets", "dev0", "--smoke", "--workers", "2", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "comparator.json").exists()


def test_recheck_ties_keep_grid_order(monkeypatch, tmp_path):
    import scripts.tune_v2 as TV
    def f(rule, spec, markets, budget, recheck, log):
        if not recheck:                                       # inner prefers L = 10 over L = 3
            return {"objective": {3: 0.1, 10: 0.2}.get(spec["L"], -1.0), "margins": {}, "episodes": 1}
        return {"objective": 0.5 if spec["L"] in (3, 10) else -1.0, "margins": {}, "episodes": 1}
    monkeypatch.setattr(TV, "score_config", f)
    monkeypatch.setattr(TV, "COMMON_GRID", [(0.08, 3), (0.08, 10), (0.08, 20)])
    assert TV.tune_system("B3-t", ["headline"], tmp_path, smoke=True)["best_params"] == {"tol": 0.08, "L": 3}
