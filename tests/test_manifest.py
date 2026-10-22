import subprocess, sys
import pytest
from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals, manifest_weights
from sim.schedule import (Budget, SMOKE_BUDGET, budget_from_locked, cell_runs, search_runs, stage_runs, bank_stage_bound,
                          reference_bound, doubling_bound, tuning_point_runs, tuning_recheck_runs, all_deviators_runs, bank_members)


def test_schedule_arithmetic_is_explicit():
    lk = load_locked(); b = budget_from_locked(lk)
    assert b == Budget(restarts=5, evals=300, n_train=5, n_val=20) and search_runs(b) == 7500
    d1, d2, h3 = cell_runs("D1", b), cell_runs("D2", b), cell_runs("D2+H3", b)
    assert d1 == {"twin": 7500, "twin_projection": 5, "attack": 7500, "incumbents": 10, "attack_projection": 5,
                  "reference": 5, "corners": 32 * 5, "evaluation": 4 * 20}
    assert sum(d1.values()) == 15265 and sum(d2.values()) == 15265 - 160 + 640 and sum(h3.values()) == 15265 - 160 + 1280
    assert stage_runs("D1", "search", b) == 7500 + 5 + 7500 + 10 + 5 + 160 and stage_runs("D1", "evaluate", b) == 80
    assert bank_stage_bound(24, b) == (24 + 2) * 5 and reference_bound(40, b) == 41 * 5
    assert doubling_bound(40, b) == 2 * (5 * 150 * 5 + 5) + 2 * 41 * 5
    assert tuning_point_runs(lk) == 2 * (1 * 100 * 3) + 3 + 6 + 3 + 3 + 4 * 3
    assert tuning_recheck_runs(b) == 2 * 7500 + 5 + 10 + 5 + 5 + 4 * 20
    assert all_deviators_runs(lk, 10, b) == 2 * (3 * 10 * (100 + 2) * 3) + 2 * 20
    m = bank_members(24)
    assert m == {"D1": {"n_unknown": 24, "n_projected": 24 + 16}, "D2": {"n_unknown": 48, "n_projected": 48 + 64},
                 "D2+H3": {"n_unknown": 2 * (24 + 48), "n_projected": 2 * (24 + 48) + 128}}     # amendment 2: both embeddings of every D2-compatible member
    assert all_deviators_runs(lk, 10, SMOKE_BUDGET) == 2 * (3 * 10 * (16 + 2) * 1) + 2 * 2     # the smoke budget caps evaluations and seeds


def test_manifest_totals_follow_the_schedule():
    lk = load_locked()
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    t_all = totals(cells); t = totals([c for c in cells if not c.post_lock])          # the section sums below are the registered pre-lock entries
    b = budget_from_locked(lk)
    c1, c2, c3 = (sum(cell_runs(f, b).values()) for f in ("D1", "D2", "D2+H3"))
    assert t["development"] == 24 * c1 + 24 * c2                   # 3 rules x 2 families x (5 + 3) cells
    assert t["rho_sweep"] == 2 * 3 * c2 and t["no_ban"] == 2 * c2 and t["h3"] == 3 * c3
    m = bank_members(24)
    assert t["controls"] == 3 * (doubling_bound(m["D1"]["n_projected"], b) + doubling_bound(m["D2"]["n_projected"], b))
    assert t["all_deviators"] == 3 * all_deviators_runs(lk, 10, b)
    assert t["tuning"] == (27 + 243 + 9) * tuning_point_runs(lk) + 9 * tuning_recheck_runs(b)
    # bank: every pre-lock D1 and D2 full cell is a target (24 D1; 24 + 6 + 2 = 32 D2); bank stage plus the extra reference candidates
    per_d1 = bank_stage_bound(m["D1"]["n_unknown"], b) + m["D1"]["n_projected"] * 5
    per_d2 = bank_stage_bound(m["D2"]["n_unknown"], b) + m["D2"]["n_projected"] * 5
    per_h3 = bank_stage_bound(m["D2+H3"]["n_unknown"], b) + m["D2+H3"]["n_projected"] * 5          # amendment 2: the three pre-lock H3 cells take the bank
    assert per_d1 == 330 and per_d2 == 810 and per_h3 == 2090
    assert t["bank"] == 24 * per_d1 + 32 * per_d2 + 3 * per_h3
    assert t_all["ablation"] == 3 * c1 + 3 * c2 and t_all["all_deviators_post_lock"] == all_deviators_runs(lk, 10, b)
    assert t_all["bank_post_lock"] > 0 and t_all["pre_lock"] == t["pre_lock"]
    assert t["pre_lock"] == sum(t[k] for k in ("development", "rho_sweep", "no_ban", "h3", "controls", "all_deviators", "tuning", "bank"))
    assert t["pre_lock"] * 45.0 / 3.6e6 < 20.0                     # the gate at 45 ms per run
    assert t["pre_lock_exact"] + t["pre_lock_upper_bound"] == t["pre_lock"]
    t = t_all
    assert {c.section for c in cells if c.post_lock} == {"bank_post_lock", "all_deviators_post_lock", "ablation", "development", "rho_sweep", "h3", "controls",   # amendment 2: the proposed rule's post-lock cells and the H3 controls
                                                         "heldout"}                                                                                           # the final cells: the bundle is in the repository since the unseal
    assert all(not c.exact for c in cells if c.section in ("bank", "bank_post_lock", "controls"))
    names = [c.name for c in cells]
    assert len(names) == len(set(names))


def test_manifest_script_prints_totals():
    out = subprocess.run([sys.executable, "scripts/manifest.py", "--ms-per-run", "45"], check=True, capture_output=True, text=True).stdout
    assert "pre_lock" in out and "core-hours" in out and "upper bound" in out


def test_manifest_weights_split_pre_lock_runs_by_rule_and_family():
    lk = load_locked(); b = budget_from_locked(lk)
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    w = manifest_weights(cells)
    assert set(w) == {(r, f) for r in ("B1", "B2", "B3") for f in ("D1", "D2", "D2+H3")}
    assert sum(w.values()) == pytest.approx(totals(cells)["pre_lock"])          # every pre-lock run is attributed once
    assert w[("B1", "D2+H3")] == sum(cell_runs("D2+H3", b).values())               # the H3 cell alone
    assert w[("B2", "D2")] > w[("B1", "D2")]                                       # B2 carries the largest tuning grid


def test_manifest_lists_the_coverage_study_outside_the_search_gate_and_the_weights():
    from sim.manifest import coverage_cells, enumerate_manifest, manifest_weights, totals
    lk = load_locked(); cov = lk["seeds"]["coverage"]
    base_seeds = cov["pool"] + sum(int(cov["replications"][str(n)]) * n for n in (10, 20))
    est = coverage_cells(lk, None)
    assert len(est) == 24 and all(c.section == "coverage" for c in est)
    assert sum(c.runs for c in est if c.kind == "coverage_base") == 6 * 5 * base_seeds
    sel = [{"name": "B2_D1_beta0.05_rho0.5_median_development", "rule": "B2", "family": "D1", "position": "median", "runs_per_seed": 4}]
    real = coverage_cells(lk, sel)
    kinds = {c.kind: c.runs for c in real}
    assert kinds["coverage_base"] == 4 * base_seeds and kinds["coverage_conditional"] > 0 and len(real) == 4
    assert [c for c in real if c.name.endswith("n40")][0].runs == 4 * int(cov["replications"]["40"]) * 40
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"]); t = totals(cells)
    no_cov = [c for c in cells if c.section != "coverage"]
    assert t["coverage_base"] > 0 and t["coverage_conditional"] > 0
    assert t["pre_lock"] == totals(no_cov)["pre_lock"] and t["pre_lock_exact"] == totals(no_cov)["pre_lock_exact"]
    assert manifest_weights(cells) == manifest_weights(no_cov)


def test_final_h3_cells_are_beta_headline_median_only(monkeypatch):
    import sim.manifest as m
    from sim.locked import load_locked
    from sim.schedule import Budget, budget_from_locked, cell_runs
    import sim.registry as reg
    real = reg.available_families(); fams = {**real, "H2": real["D2"]}                      # a stand-in sealed family with D2's corner count
    monkeypatch.setattr(reg, "available_families", lambda locked=None: fams)
    lk = load_locked(); b = budget_from_locked(lk); cells = m.enumerate_manifest(lk, ["B1", "B2", "B3"], budget=b)
    final_rules = {"B1", "B2", "B3"} | ({"proposed"} if reg.proposed_available() else set())          # the proposed rule joins the final cells once its module exists
    h3 = [c for c in cells if c.section == "heldout" and c.family == "D2+H3"]
    assert len(h3) == len(final_rules) and {c.rule for c in h3} == final_rules
    assert {c.position for c in h3} == {"median"} and {float(c.beta) for c in h3} == {0.05} and all(c.post_lock for c in h3)
    n_final = int(lk["coverage_consequences"]["final_eval_n"])
    assert all(c.runs == sum(cell_runs("D2+H3", Budget(b.restarts, b.evals, b.n_train, n_final)).values()) for c in h3)
    h2 = [c for c in cells if c.section == "heldout" and c.family == "H2"]
    assert len(h2) == len(final_rules) * (len(lk["beta_grid"]) - 1 + len(lk["positions"]))        # unchanged: every budget at the median plus the headline budget at every position, per rule


def test_amendment_2_lists_the_proposed_rules_post_lock_cells_and_the_h3_controls():
    lk = load_locked(); b = budget_from_locked(lk); cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    pre = [c for c in cells if not c.post_lock]
    assert totals(pre)["pre_lock"] == totals(cells)["pre_lock"]                                           # the registered pre-lock accounting is untouched
    prop = [c for c in cells if c.rule == "proposed" and c.post_lock]
    by = {}
    for c in prop:
        by.setdefault(c.section, []).append(c)
    assert len(by["development"]) == 16 and {c.family for c in by["development"]} == {"D1", "D2"}
    assert len(by["rho_sweep"]) == 2 and len(by["h3"]) == 1 and by["h3"][0].position == "median" and float(by["h3"][0].beta) == float(lk["beta_headline"])
    assert sorted((c.family, c.position) for c in by["controls"]) == [("D1", "median"), ("D2", "median"), ("D2+H3", "median")]
    assert len(by["all_deviators_post_lock"]) == 1 and len(by["ablation"]) == 6 and len(by["bank_post_lock"]) == 1
    assert "no_ban" not in by                                                                              # the no-ban diagnostic stays registered for B2 and B3 only
    h3_controls = [c for c in cells if c.section == "controls" and c.family == "D2+H3"]
    assert {c.rule for c in h3_controls} == {"B1", "B2", "B3", "proposed"} and all(c.post_lock and c.position == "median" for c in h3_controls)
    assert all(c.runs == sum(cell_runs(c.family, b).values()) for c in by["development"] + by["rho_sweep"] + by["h3"])
    names = [c.name for c in cells]; assert len(names) == len(set(names))
    assert totals(cells)["post_lock"] >= sum(c.runs for c in prop)
