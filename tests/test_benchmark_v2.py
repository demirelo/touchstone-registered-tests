"""Benchmark v2 (design 8.2): the cost table from measured timings, caps, approval, and the pod command line."""
import json

import pytest

UNIT = 1500.0
DESIGN = {"d2h3_cell": UNIT, "x7_cell": 2.5 * UNIT, "inner": 0.04 * UNIT, "inner_x7": 0.1 * UNIT, "doubling": UNIT, "doubling_x7": 2.5 * UNIT,
          "episode": UNIT / 18000, "bootstrap_batch": 10 * UNIT, "eval200_extra_fraction": 0.16,
          "cross_row": 140 * UNIT / 18000}                    # 14 x 8 rows x 10 = 156,800 / 18,000 units: design 8.2's cross row


def test_cost_table_reproduces_design_units():
    from scripts.benchmark_v2 import cost_table
    t = cost_table(DESIGN, usd_per_core_hour=0.108)
    assert t["development_units"] == pytest.approx(233.25, abs=0.5) and t["evaluation_units"] == pytest.approx(868.8, abs=0.5)
    assert t["rows"]["comparator_selection"] == pytest.approx(33.48, abs=0.01) and t["rows"]["tuning"] == pytest.approx(142.56, abs=0.01)
    assert t["rows"]["doublings"] == pytest.approx(207.0) and t["rows"]["cells"] == pytest.approx(563.0)
    assert t["total_usd"] == pytest.approx(1102.0 * 0.045, rel=0.01)


def test_flags_caps_and_approval():
    from scripts.benchmark_v2 import cost_table
    t = cost_table(DESIGN, usd_per_core_hour=0.108)
    assert t["flags"] == {"development_over_cap": False, "evaluation_over_cap": False, "approval_required": True}
    cheap = cost_table(DESIGN, usd_per_core_hour=0.05)
    assert cheap["flags"]["approval_required"] is False
    dear = cost_table({**DESIGN, "inner": 0.2 * UNIT}, usd_per_core_hour=0.108)
    assert dear["flags"]["development_over_cap"] is True


def test_cli_accepts_pod_arguments(tmp_path):
    from scripts.benchmark_v2 import main
    assert main(["--run", "--dry-run", "--workers", "2", "--out", str(tmp_path)]) == 0
    plan = json.loads((tmp_path / "benchmark_plan.json").read_text())
    assert [k["kind"] for k in plan["kinds"]] == ["d2h3_cell", "x7_cell", "w1", "coalition_total", "inner", "inner_x7", "coverage_batch", "cross_row", "doubling"]


def test_cli_table(tmp_path, capsys):
    from scripts.benchmark_v2 import main
    p = tmp_path / "timings.json"; p.write_text(json.dumps({"timings": DESIGN, "usd_per_core_hour": 0.108}))
    assert main(["--table", str(p)]) == 0
    assert json.loads(capsys.readouterr().out)["flags"]["approval_required"] is True


def test_measure_covers_every_kind_on_development_seeds(tmp_path):
    from scripts.benchmark_v2 import EPISODE_SEEDS, KINDS, WORKLOADS, measure
    calls = []
    stubs = {k: (lambda k=k: calls.append(k)) for k in WORKLOADS}
    t = measure(tmp_path, 1, fns=stubs)
    assert set(calls) == set(WORKLOADS) and set(t) >= set(KINDS) - {"coverage_batch"} | {"doubling_x7", "episode", "bootstrap_batch", "eval160", "reference", "inner_d2"}
    assert all(s < 30_000_000 for s in EPISODE_SEEDS)
    with pytest.raises(SystemExit):
        measure(tmp_path, 1, fns={k: v for k, v in stubs.items() if k != "w1_search"})


def test_cost_table_uses_measured_welfare_and_coalition():
    from scripts.benchmark_v2 import cost_table
    base = cost_table(DESIGN, 0.108)["rows"]["cells"]
    more = cost_table({**DESIGN, "w1": 2 * UNIT, "coalition_total": 3 * UNIT}, 0.108)["rows"]["cells"]
    assert more == pytest.approx(base + 8 * 1 + 8 * 2.5 + 32 * 2)


# ---- fix-pass re-review (round 1) --------------------------------------------------------------------------------------

def test_g6_components_run_in_dependency_order(tmp_path):
    from scripts.benchmark_v2 import WORKLOADS, measure
    calls = []
    measure(tmp_path, 1, fns={k: (lambda k=k: calls.append(k)) for k in WORKLOADS})
    i = calls.index
    assert calls == list(WORKLOADS) and i("search_d2h3") < i("reference") and i("search_x7") < i("reference")
    assert all(i("reference") < i(k) for k in ("eval_d2h3", "eval_x7", "w1_search", "cross_row", "doubling", "doubling_x7"))
    assert i("w1_search") < i("w1_eval") and i("coalition_prereqs") < i("coalition_search") < i("coalition_eval")


def test_g7_cells_are_composed_from_their_components(tmp_path, monkeypatch):
    import scripts.benchmark_v2 as B
    secs = {k: float(n + 1) for n, k in enumerate(B.WORKLOADS)}
    monkeypatch.setattr(B, "_timed", lambda f: secs[f()])
    fns = {k: (lambda k=k: k) for k in B.WORKLOADS}; fns["_meta"] = {"eval_seeds": 20, "episodes": 20, "coverage_replications": 100}
    t = B.measure(tmp_path, 1, fns=fns); r = secs
    assert t["d2h3_cell"] == r["search_d2h3"] + 2 * r["eval_d2h3"] and t["x7_cell"] == r["search_x7"] + 2 * r["eval_x7"]          # references apart
    assert t["reference"] == r["reference"] and t["w1"] == r["w1_search"] + 2 * r["w1_eval"]
    assert t["coalition_total"] == r["coalition_prereqs"] / 2 + r["coalition_search"] + 2 * r["coalition_eval"]
    assert t["eval160"] == {"profit": 8 * r["eval_d2h3"], "x7": 8 * r["eval_x7"], "welfare": 8 * r["w1_eval"], "coalition": 8 * r["coalition_eval"]}
    assert t["cross_row"] == r["cross_row"] and t["episode"] == r["episode"] / 20 and t["inner_d2"] == r["inner_d2"]


def test_g7_cost_table_prices_the_measured_cross_row_and_inner_d2():
    from scripts.benchmark_v2 import cost_table
    base = cost_table(DESIGN, 0.108)["rows"]
    assert base["cross"] == pytest.approx(156_800 / 18_000)
    more = cost_table({**DESIGN, "cross_row": 2 * DESIGN["cross_row"], "inner_d2": 3 * DESIGN["inner"]}, 0.108)["rows"]
    assert more["cross"] == pytest.approx(2 * base["cross"])
    assert more["comparator_selection"] == pytest.approx(base["comparator_selection"] + 72 * DESIGN["inner"] / UNIT)        # 72 x (1 + 3) / 2 - 72


def test_g6_default_workloads_run_at_smoke_budget_on_development_seeds(tmp_path, monkeypatch):
    """The real default wiring (not stubs) at the smoke budget; X7-SC controls sliced to 8; the fresh-seed generator is
    disabled, so any reserved evaluation seed would raise."""
    import math
    import scripts.benchmark_v2 as B
    import scripts.revision_v2 as RV
    import sim.manifest_v2 as MAN
    from sim.policies.x7 import corner_vectors as cv
    monkeypatch.setattr(RV, "corner_vectors", lambda fam: cv(fam)[:8])
    monkeypatch.setattr(RV.INST, "eval_seeds", lambda *a, **k: (_ for _ in ()).throw(AssertionError("reserved evaluation seeds")))
    t = B.measure(tmp_path, 1, smoke=True)
    assert set(t["components"]) == set(B.WORKLOADS) and all(v > 0 for v in t["components"].values())
    want = len([o for o in MAN.bank_rules("headline@rho0.2", "D2+H3") if o != "F111"])
    assert want == 11 and t["bank_sizes"] == {"D2+H3": want, "X7-SC": want}          # the matched rule's menu holds the 11 other matched rules' attacks
    table = B.cost_table(t, 0.108)
    assert all(math.isfinite(v) for v in table["rows"].values()) and table["total_usd"] > 0


def _composed(B, monkeypatch, tmp_path, **override):
    secs = {k: 10.0 for k in B.WORKLOADS} | override
    monkeypatch.setattr(B, "_timed", lambda f: secs[f()])
    fns = {k: (lambda k=k: k) for k in B.WORKLOADS}; fns["_meta"] = {"eval_seeds": 20, "episodes": 20, "coverage_replications": 100}
    return B.measure(tmp_path, 1, fns=fns)


def test_h2_extra_evaluation_follows_evaluation_components_only(tmp_path, monkeypatch):
    import scripts.benchmark_v2 as B
    base = B.cost_table(_composed(B, monkeypatch, tmp_path), 0.108); u = base["unit_core_hours"] * 3600
    slow = B.cost_table(_composed(B, monkeypatch, tmp_path, coalition_search=20.0, search_d2h3=30.0, w1_search=40.0), 0.108)
    extra_s = lambda tb: tb["rows"]["eval200_extra"] * tb["unit_core_hours"] * 3600
    assert extra_s(slow) == pytest.approx(extra_s(base))                                # slower searches, same evaluations: same extra
    assert extra_s(base) == pytest.approx(8 * 10.0 * (208 + 118 + 8 + 8 + 32))
    more = B.cost_table(_composed(B, monkeypatch, tmp_path, coalition_eval=20.0), 0.108)
    assert extra_s(more) - extra_s(base) == pytest.approx(32 * 8 * 10.0)


def test_h3_references_priced_once_per_menu(tmp_path, monkeypatch):
    import scripts.benchmark_v2 as B
    import sim.manifest_v2 as MAN
    menus = {(c["context"], c["rule"]) for c in MAN.effective(0, False) if c["objective"] == "profit" and c["family"] in ("D2+H3", "X7-SC")}
    assert B.REFERENCE_MENUS == len(menus) == 118
    a = B.cost_table(_composed(B, monkeypatch, tmp_path), 0.108); b = B.cost_table(_composed(B, monkeypatch, tmp_path, reference=11.0), 0.108)
    sec = lambda tb, row: tb["rows"][row] * tb["unit_core_hours"] * 3600
    assert sec(b, "references") - sec(a, "references") == pytest.approx(118.0) and sec(b, "cells") == pytest.approx(sec(a, "cells"))
