"""Benchmark v2 (design 8.2): the cost table from measured timings, caps, approval, and the pod command line."""
import json

import pytest

UNIT = 1500.0
DESIGN = {"d2h3_cell": UNIT, "x7_cell": 2.5 * UNIT, "inner": 0.04 * UNIT, "inner_x7": 0.1 * UNIT, "doubling": UNIT, "doubling_x7": 2.5 * UNIT,
          "episode": UNIT / 18000, "bootstrap_batch": 10 * UNIT, "eval200_extra_fraction": 0.16,
          "cross_row": 140 * UNIT / 18000}                    # 14 x 8 rows x 10 = 156,800 / 18,000 units: design 8.2's cross row


def test_cost_table_reproduces_design_units():
    from scripts.benchmark_v2 import cost_table
    t = cost_table(DESIGN, usd_per_core_hour=0.108)                     # design draft 7, 8.2: about 177.3 and 696 units, about 39.3 USD
    assert t["development_units"] == pytest.approx(177.3, abs=0.5) and t["evaluation_units"] == pytest.approx(696.0, abs=1.5)
    assert t["rows"]["comparator_selection"] == pytest.approx(33.48, abs=0.01) and t["rows"]["tuning"] == pytest.approx(106.92, abs=0.01)
    assert t["rows"]["doublings"] == pytest.approx(149.0) and t["rows"]["cells"] == pytest.approx(446.0) and "fixtures" not in t["rows"]
    assert t["rows"]["coalition_extras"] == pytest.approx(18.0) and t["total_usd"] == pytest.approx(873.0 * 0.045, rel=0.01)


def test_flags_caps_and_approval():
    from scripts.benchmark_v2 import cost_table
    t = cost_table(DESIGN, usd_per_core_hour=0.108)
    assert t["flags"] == {"development_over_cap": False, "evaluation_over_cap": False, "approval_required": False}
    assert cost_table(DESIGN, usd_per_core_hour=0.12)["flags"]["approval_required"] is True
    dear = cost_table({**DESIGN, "inner": 0.3 * UNIT}, usd_per_core_hour=0.108)
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
    assert json.loads(capsys.readouterr().out)["flags"]["approval_required"] is False


def test_measure_covers_every_kind_on_development_seeds(tmp_path):
    from scripts.benchmark_v2 import EPISODE_SEEDS, KINDS, WORKLOADS, measure
    calls = []
    stubs = {k: (lambda k=k: calls.append(k)) for k in WORKLOADS}
    t = measure(tmp_path, 1, fns=stubs)
    assert set(calls) == set(WORKLOADS) and set(t) >= set(KINDS) - {"coverage_batch", "inner", "inner_x7"} | {"doubling_x7", "episode", "bootstrap_batch", "eval160", "reference", "dev_inner_config", "dev_recheck_config"}
    assert all(s < 30_000_000 for s in EPISODE_SEEDS)
    with pytest.raises(SystemExit):
        measure(tmp_path, 1, fns={k: v for k, v in stubs.items() if k != "w1_search"})


def test_cost_table_uses_measured_welfare_and_coalition():
    from scripts.benchmark_v2 import cost_table
    base = cost_table(DESIGN, 0.108)["rows"]["cells"]
    more = cost_table({**DESIGN, "w1": 2 * UNIT, "coalition_total": 3 * UNIT}, 0.108)["rows"]["cells"]
    assert more == pytest.approx(base + 6 * 1 + 6 * 2.5 + 30 * 2)


# ---- fix-pass re-review (round 1) --------------------------------------------------------------------------------------

def test_g6_components_run_in_dependency_order(tmp_path):
    from scripts.benchmark_v2 import WORKLOADS, measure
    calls = []
    measure(tmp_path, 1, fns={k: (lambda k=k: calls.append(k)) for k in WORKLOADS})
    i = calls.index
    assert calls == list(WORKLOADS) and i("search_d2h3") < i("reference") and i("search_x7") < i("reference")
    assert all(i("reference") < i(k) for k in ("eval_d2h3", "eval_x7", "w1_search", "cross_row", "doubling", "doubling_x7"))
    assert i("w1_search") < i("w1_eval") and i("coalition_prereqs") < i("coalition_search") < i("coalition_reference") < i("coalition_final") \
        < i("coalition_select") < i("coalition_eval")


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
    assert t["cross_row"] == r["cross_row"] and t["episode"] == r["episode"] / 20 and t["dev_inner_config"] == r["dev_inner_config"]
    assert t["dev_recheck_config"] == 2 * r["search_d2h3"] + r["search_x7"] + r["reference"] + 3 * r["eval_d2h3"]


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
    assert want == 9 and t["bank_sizes"] == {"D2+H3": want, "X7-SC": want}           # the matched rule's menu holds the 9 other matched rules' attacks
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
    assert extra_s(base) == pytest.approx(8 * 10.0 * (145 + 79 + 21 + 6 + 6 + 30))
    for comp, cells in (("eval_d2h3", 145), ("eval_x7", 100), ("w1_eval", 12), ("coalition_eval", 30)):     # each kind from its own evaluation (H4 as X7-SC)
        more = B.cost_table(_composed(B, monkeypatch, tmp_path, **{comp: 20.0}), 0.108)
        assert extra_s(more) - extra_s(base) == pytest.approx(cells * 8 * 10.0), comp


def test_h3_references_priced_once_per_menu(tmp_path, monkeypatch):
    import scripts.benchmark_v2 as B
    import sim.manifest_v2 as MAN
    menus = {(c["context"], c["rule"]) for c in MAN.effective(0, False) if c["objective"] == "profit" and c["family"] in ("D2+H3", "X7-SC")}
    full = {m for m in menus if all((m[0], m[1], f) in {(c["context"], c["rule"], c["family"]) for c in MAN.effective(0, False)} for f in ("D2+H3", "X7-SC"))}
    assert B.REFERENCE_MENUS == len(full) == 79 and B.REDUCED_MENUS == len(menus) - len(full) == 18
    a = B.cost_table(_composed(B, monkeypatch, tmp_path), 0.108); b = B.cost_table(_composed(B, monkeypatch, tmp_path, reference=11.0), 0.108)
    sec = lambda tb, row: tb["rows"][row] * tb["unit_core_hours"] * 3600
    assert sec(b, "references") - sec(a, "references") == pytest.approx(97.0) and sec(b, "cells") == pytest.approx(sec(a, "cells"))
    usd = 0.108 / 3600
    assert b["evaluation_usd"] - a["evaluation_usd"] == pytest.approx(97.0 * usd) and b["total_usd"] - a["total_usd"] == pytest.approx((97.0 + 24.0) * usd)


def test_i1_development_prices_its_reference_menus(tmp_path, monkeypatch):
    """180 inner configuration-markets measured whole (three searches, the development reference, three evaluations);
    24 rechecks composed of full-budget searches, a reference, and three 20-seed evaluations (three tuned systems, no fixtures)."""
    import scripts.benchmark_v2 as B
    assert B.CONFIG_MARKETS == {"comparator_inner": 36, "comparator_recheck": 6, "tuning_inner": 144, "tuning_recheck": 18}
    dev_s = lambda tb: tb["development_usd"] / 0.108 * 3600
    a = B.cost_table(_composed(B, monkeypatch, tmp_path), 0.108)
    assert dev_s(B.cost_table(_composed(B, monkeypatch, tmp_path, reference=11.0), 0.108)) - dev_s(a) == pytest.approx(24.0)
    assert dev_s(B.cost_table(_composed(B, monkeypatch, tmp_path, dev_inner_config=11.0), 0.108)) - dev_s(a) == pytest.approx(180.0)
    assert dev_s(B.cost_table(_composed(B, monkeypatch, tmp_path, eval_d2h3=11.0), 0.108)) - dev_s(a) == pytest.approx(24 * 3.0)
    assert dev_s(B.cost_table(_composed(B, monkeypatch, tmp_path, search_x7=11.0), 0.108)) - dev_s(a) == pytest.approx(24.0)
    assert dev_s(B.cost_table(_composed(B, monkeypatch, tmp_path, search_d2h3=11.0), 0.108)) - dev_s(a) == pytest.approx(48.0)


def test_caveat_stand_in_bank_is_distinct_excludes_the_best_and_refuses_shortage(tmp_path, monkeypatch):
    from types import SimpleNamespace as E
    import scripts.benchmark_v2 as B
    import scripts.revision_v2 as RV
    from sim.policies.families import exact_key
    fam = RV.family_for("D2+H3", 200, 10); h = fam.honest_point()
    pts = [dict(h, u0=i / 20, clip=c) for i in range(8) for c in (0, 1)]            # 16 entries, 8 distinct after projection
    entries = [E(knobs=k, f=float(n)) for n, k in enumerate(pts)]; best = pts[-1]
    b = B.stand_in_bank(entries, best, fam, 5)
    keys = [exact_key(k) for k in b]
    assert len(b) == 5 and len(set(keys)) == 5 and exact_key(fam.project(best)) not in keys
    assert [k["u0"] for k in b] == [6 / 20, 5 / 20, 4 / 20, 3 / 20, 2 / 20]              # by training value, best excluded
    assert len(B.stand_in_bank(entries, best, fam, 7)) == 7
    with pytest.raises(SystemExit):
        B.stand_in_bank(entries, best, fam, 8)
    assert B._default_fns(tmp_path, smoke=True)["_meta"]["n_bank"] == {"D2+H3": 9, "X7-SC": 9}
    import sim.manifest_v2 as MAN
    monkeypatch.setattr(MAN, "bank_rules", lambda ctx, f, cuts=0, h4_excluded=False: ["F000", "F111", "R4", "C*", "F010"])       # the size follows the manifest
    assert B._default_fns(tmp_path, smoke=True)["_meta"]["n_bank"] == {"D2+H3": 4, "X7-SC": 4}


# ---- operations plan Task 4: cuts, branches, wave billing, the cost decision ----------------------------------------------

POD = {"d2h3_cell": 1200.0, "x7_cell": 3000.0, "reference": 300.0, "w1": 1500.0, "coalition_total": 1500.0,
       "eval160": {"profit": 240.0, "x7": 240.0, "welfare": 240.0, "coalition": 240.0}, "cross_row": 12.0, "doubling": 1200.0, "doubling_x7": 3000.0,
       "episode": 1500.0 / 18000, "bootstrap_batch": 3000.0, "dev_inner_config": 200.0, "dev_recheck_config": 6000.0, "usd_per_pod_hour": 0.56,
       "task_seconds": {"search": {"profit": 1000.0, "x7": 2500.0, "W0": 1000.0, "W0_x7": 2500.0}, "reference": 300.0, "W1": 1000.0, "W1_x7": 2500.0,
                        "prereqs": 400.0, "coalition": 800.0, "coalition_reference": 300.0, "coalition_final": 350.0, "coalition_select": 10.0,
                        "evaluate": {"profit": 240.0, "x7": 400.0, "welfare": 240.0, "coalition": 240.0, "diagnostic": 20.0},
                        "cross_item": 960.0, "doubling": 1200.0, "doubling_x7": 3000.0}}


def test_defaults_reproduce_the_current_table():
    import sim.manifest_v2 as MAN
    from scripts.benchmark_v2 import counts
    c = counts()
    assert c["cells"] == {"plain": 145, "x7": 79, "h4": 21, "welfare_h3": 6, "welfare_x7": 6, "coalition": 30} and c["reference_menus"] == 79
    assert c["reduced_menus"] == 18 and c["diagnostic"] == 3 and c["coalition_groups"] == 6 and c["bank_train_items"] == 14
    assert c["doublings"] == (64, 34) and c["cross_rows"] == 14 * 8 and sum(c["cells"].values()) == len(MAN.effective(0, False)) - 3 == 287
    assert c["config_markets"] == {"comparator_inner": 36, "comparator_recheck": 6, "tuning_inner": 144, "tuning_recheck": 18}
    assert c["coverage_episodes"] == 8 * 20_000 * 3


@pytest.mark.parametrize("cuts", [1, 2, 3, 4])
def test_cuts_and_branches_change_counts(cuts):
    import sim.manifest_v2 as MAN
    from scripts.benchmark_v2 import counts
    c = counts(cuts=cuts)
    eff = [x for x in MAN.effective(cuts, False) if x["block"] != "diagnostic"]
    assert sum(c["cells"].values()) == len(eff) < 287
    menus = {(x["context"], x["rule"]) for x in eff if x["objective"] == "profit" and x["family"] in ("D2+H3", "X7-SC")}
    assert c["reference_menus"] + c["reduced_menus"] == len(menus)
    two = counts(markets=("headline", "dev0"), branch="two10k")
    assert two["coverage_episodes"] == 8 * 10_000 * 2 and two["config_markets"]["tuning_inner"] == 144 * 2 // 3


def _greedy(times, m):
    loads = [0.0] * m
    for t in times:
        i = loads.index(min(loads)); loads[i] += t
    return max(loads)


def test_wave_bound_covers_unequal_tasks():
    import numpy as np
    from scripts.benchmark_v2 import wave_bound
    assert wave_bound([1.0] * 15 + [100.0], 16) >= 100.0
    rng = np.random.default_rng(1)
    for _ in range(300):
        n, m = int(rng.integers(1, 60)), int(rng.choice([1, 4, 16]))
        times = list(rng.exponential(10.0, n) * rng.choice([1, 10], n))
        assert wave_bound(times, m) >= _greedy(times, m) - 1e-9 and wave_bound(times, m) >= sum(times) / m - 1e-9


def test_evaluation_bill_follows_the_dispatch_plan():
    from scripts.benchmark_v2 import cost_table, wave_bound
    plan = [[50.0], [1.0] * 15 + [100.0], [2.0] * 40]
    t = cost_table(POD, plan=plan, vcpu=16)
    assert t["evaluation_usd"] == pytest.approx(sum(wave_bound(w, 16) for w in plan) / 3600 * POD["usd_per_pod_hour"])


def _ledger(spent=()):
    return {"caps": {"development": 12.0, "evaluation": 40.0}, "reservations": [], "spent": [{"op": op, "tag": f"t{i}", "usd": u} for i, (op, u) in enumerate(spent)]}


def test_choose_follows_design_order():
    from scripts.benchmark_v2 import choose
    ok = choose(POD, _ledger())
    assert ok["branch"] == "three20k" and ok["cuts"] == 0 and ok["stop"] is None
    from scripts.benchmark_v2 import cost_table
    heavy = dict(POD, episode=1.0)                                                   # coverage pushes three markets over the development cap
    assert cost_table(heavy)["development_usd"] > 12.0
    d = choose(heavy, _ledger())
    assert d["branch"] in ("two20k", "two10k") and d["markets"] == ["headline", "dev0"] and d["development_usd"] <= 12.0
    assert choose(dict(POD, dev_recheck_config=1e7), _ledger())["stop"] == "development"
    scale = lambda v, f: {k: scale(x, f) for k, x in v.items()} if isinstance(v, dict) else v * f
    e = {c: cost_table(POD, cuts=c)["evaluation_usd"] for c in range(5)}
    f = 39.0 / ((e[0] + e[4]) / 2)                                                   # evaluation cost is linear in the task times
    ev = dict(POD, task_seconds=scale(POD["task_seconds"], f))
    want = next(c for c in range(5) if e[c] * f + 1.0 <= 40.0)
    got = choose(ev, _ledger())
    assert want >= 1 and got["cuts"] == want and got["evaluation_usd"] == pytest.approx(e[want] * f + 1.0)
    assert choose(dict(POD, task_seconds=dict(POD["task_seconds"], reference=1e7)), _ledger())["stop"] == "evaluation"


def test_benchmark_spend_decides_a_borderline_case():
    from scripts.benchmark_v2 import choose
    base = choose(POD, _ledger())
    assert base["branch"] == "three20k"
    margin = 12.0 - base["development_usd"]
    assert choose(POD, _ledger([("development", margin + 0.01)]))["branch"] != "three20k"


def test_measure_records_billing_metadata(tmp_path):
    from scripts.benchmark_v2 import WORKLOADS, measure
    t = measure(tmp_path, 16, fns={k: (lambda: None) for k in WORKLOADS}, usd_per_pod_hour=0.56)
    assert t["vcpu"] == 16 and t["usd_per_pod_hour"] == 0.56 and t["markets"] == ["headline", "dev0"] and len(t["commit"]) >= 7 and t["wall_seconds"] >= 0


def test_decide_writes_the_decision_once_with_a_ledger_snapshot(tmp_path):
    from scripts.benchmark_v2 import main
    tm = tmp_path / "timings.json"; tm.write_text(json.dumps({"timings": POD, "smoke": False}))
    lg = tmp_path / "ledger.json"; lg.write_text(json.dumps(_ledger([("development", 1.5)])))
    out = tmp_path / "decision.json"
    assert main(["--decide", str(tm), "--ledger", str(lg), "--out", str(out)]) == 0
    d = json.loads(out.read_text())
    assert d["decision"]["branch"] == "three20k" and d["decision"]["spent_usd"] == 1.5 and d["ledger"] == json.loads(lg.read_text())
    assert len(d["timings_sha256"]) == 64
    with pytest.raises(SystemExit):
        main(["--decide", str(tm), "--ledger", str(lg), "--out", str(out)])           # written once


def test_default_eval_plan_follows_the_runner_dispatch():
    """Operations plan Task 8 (pre-flight ruling): the evaluation bill uses the runner's own dispatch waves per pod."""
    import scripts.revision_v2 as RV
    from scripts.benchmark_v2 import STAGES_BILLED, eval_pods, pod_plan
    pods = eval_pods()
    assert set(pods) == {"headline@rho0.2", "headline@rho1"} | {f"fresh{i}" for i in range(6)}
    for name in ("fresh0", "headline@rho0.2"):
        jobs = pods[name]
        want = [len(ids) for st in STAGES_BILLED for ids in RV.dispatch_plan(st, jobs)]
        assert [len(w) for w in pod_plan(POD, jobs)] == want



def test_k10_waves_are_priced_with_their_measured_components():
    """Final review K10: prerequisites and evaluations are billed in their own dispatch waves, at their measured times."""
    import scripts.revision_v2 as RV
    from scripts.benchmark_v2 import eval_pods, pod_plan
    ts = dict(POD["task_seconds"], prereqs=100.0, coalition=0.001)
    jobs = eval_pods()["headline@rho0.2"]; plan = pod_plan(dict(POD, task_seconds=ts), jobs)
    calls = [(st, items) for stage in ("search", "reference", "dependent", "evaluate", "cross", "doubling") for st, items in RV._waves(stage, jobs, jobs)]
    assert len(plan) == len(calls)
    for (st, items), wave in zip(calls, plan):
        if st == "joint_twin":
            assert wave == [100.0] * len(items)
        if st == "dependent" and items[0]["objective"] in ("total", "min"):
            assert wave == [0.001] * len(items)
        if st == "evaluate":
            assert all(w in (240.0, 400.0, 20.0) for w in wave)
    assert any(st == "evaluate" for st, _ in calls) and any(st == "joint_twin" for st, _ in calls)


def test_k10_measure_records_task_seconds(tmp_path, monkeypatch):
    import scripts.benchmark_v2 as B
    secs = {k: float(n + 1) for n, k in enumerate(B.WORKLOADS)}
    monkeypatch.setattr(B, "_timed", lambda f: secs[f()])
    fns = {k: (lambda k=k: k) for k in B.WORKLOADS}; fns["_meta"] = {"eval_seeds": 20, "episodes": 20, "coverage_replications": 100}
    t = B.measure(tmp_path, 16, fns=fns)["task_seconds"]
    assert t["prereqs"] == secs["coalition_prereqs"] and t["coalition"] == secs["coalition_search"] and t["reference"] == secs["reference"]
    assert t["coalition_reference"] == secs["coalition_reference"] and t["coalition_final"] == secs["coalition_final"] and t["coalition_select"] == secs["coalition_select"]
    assert t["evaluate"]["profit"] == secs["eval_d2h3"] * 10 and t["search"]["x7"] == secs["search_x7"] and t["cross_item"] == secs["cross_row"] * 8 * 10


# ---- design draft 7 (Part A2 Task 10) ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("h4_excluded", [False, True])
@pytest.mark.parametrize("cuts", [0, 1, 2, 3, 4])
def test_counts_live_match_manifest(cuts, h4_excluded):
    import sim.manifest_v2 as MAN
    from scripts.benchmark_v2 import counts
    eff = MAN.effective(cuts, h4_excluded); c = counts(cuts, h4_excluded)
    assert c["cells"]["h4"] == sum(x["family"] == "H4" for x in eff) and c["diagnostic"] == sum(x["block"] == "diagnostic" for x in eff)
    assert c["cells"]["coalition"] == sum(x["objective"] in ("total", "min") for x in eff)
    assert sum(c["cells"].values()) + c["diagnostic"] == len(eff)


def test_default_billing_path_draft7():
    import scripts.benchmark_v2 as B
    t = B.cost_table(POD, vcpu=16)
    rows = t["rows_seconds"]; m = 3; ic, rc = POD["dev_inner_config"], POD["dev_recheck_config"]
    stage = lambda n: B.wave_bound([ic] * n, 16) + B.wave_bound([rc] * (2 * m), 16)
    assert rows["tuning"] == pytest.approx(3 * stage(16 * m)) and "fixtures" not in rows and t["counts"]["coverage_episodes"] == 8 * 20_000 * 3
    plan = B.default_eval_plan(POD)
    assert all(isinstance(x, float) for w in plan for x in w)


def test_cost_table_prices_h4_from_timing():
    from scripts.benchmark_v2 import cost_table
    base = cost_table(DESIGN, 0.108)["rows"]["cells"]
    h4 = {"h4_seconds": 2.0, "x7_seconds": 1.0}
    assert cost_table(DESIGN, 0.108, h4_timing=h4)["rows"]["cells"] == pytest.approx(base + 21 * 2.5)          # twice an X7-SC cell
    assert cost_table(DESIGN, 0.108, h4_timing={"h4_seconds": 1.0, "x7_seconds": 2.0})["rows"]["cells"] == pytest.approx(base - 21 * 2.5 / 2)
    pod = cost_table(POD, vcpu=16, h4_timing=h4)["evaluation_usd"]
    assert pod > cost_table(POD, vcpu=16)["evaluation_usd"]


def test_choose_after_h4_keeps_branch_and_counts_once():
    from scripts.benchmark_v2 import H4_RESERVE_USD, choose, choose_after_h4, cost_table
    frozen = dict(choose(POD, _ledger()), branch="two20k", markets=["headline", "dev0"])
    led = _ledger([("development", 7.0)])
    d = choose_after_h4(POD, led, frozen, {"h4_seconds": 1.0, "x7_seconds": 1.0})
    cov = cost_table(POD, markets=("headline", "dev0"), branch="two20k")["rows_seconds"]["coverage"] / 3600 * POD["usd_per_pod_hour"]
    assert d["branch"] == "two20k" and d["markets"] == ["headline", "dev0"] and d["stop"] is None
    assert d["development_usd"] == pytest.approx(7.0 + cov)                      # spend once, plus only the remaining coverage
    assert d["evaluation_usd"] == pytest.approx(cost_table(POD, cuts=d["cuts"], h4_timing={"h4_seconds": 1.0, "x7_seconds": 1.0})["evaluation_usd"] + H4_RESERVE_USD)
    dear = choose_after_h4(POD, led, frozen, {"h4_seconds": 400.0, "x7_seconds": 1.0})
    assert dear["stop"] == "evaluation" or dear["cuts"] > d["cuts"]


def test_choose_after_h4_development_stop():
    from scripts.benchmark_v2 import choose, choose_after_h4
    frozen = choose(POD, _ledger())
    assert choose_after_h4(POD, _ledger([("development", 11.99)]), frozen, {"h4_seconds": 1.0, "x7_seconds": 1.0})["stop"] == "development"

