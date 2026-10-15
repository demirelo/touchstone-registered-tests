import subprocess, sys
import pytest
from sim.locked import load_locked
from sim.manifest import enumerate_manifest, totals
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
    assert m == {"D1": {"n_unknown": 24, "n_projected": 24 + 16}, "D2": {"n_unknown": 48, "n_projected": 48 + 64}}
    assert all_deviators_runs(lk, 10, SMOKE_BUDGET) == 2 * (3 * 10 * (16 + 2) * 1) + 2 * 2     # the smoke budget caps evaluations and seeds


def test_manifest_totals_follow_the_schedule():
    lk = load_locked()
    cells = enumerate_manifest(lk, ["B1", "B2", "B3"])
    t = totals(cells)
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
    assert t["bank"] == 24 * per_d1 + 32 * per_d2 == 24 * 330 + 32 * 810
    assert t["ablation"] == 3 * c1 + 3 * c2 and t["all_deviators_post_lock"] == all_deviators_runs(lk, 10, b)
    assert t["bank_post_lock"] > 0
    assert t["pre_lock"] == sum(t[k] for k in ("development", "rho_sweep", "no_ban", "h3", "controls", "all_deviators", "tuning", "bank"))
    assert t["pre_lock"] * 45.0 / 3.6e6 < 20.0                     # the gate at 45 ms per run
    assert t["pre_lock_exact"] + t["pre_lock_upper_bound"] == t["pre_lock"]
    assert {c.section for c in cells if c.post_lock} == {"bank_post_lock", "all_deviators_post_lock", "ablation"}
    assert all(not c.exact for c in cells if c.section in ("bank", "bank_post_lock", "controls"))
    names = [c.name for c in cells]
    assert len(names) == len(set(names))


def test_manifest_script_prints_totals():
    out = subprocess.run([sys.executable, "scripts/manifest.py", "--ms-per-run", "45"], check=True, capture_output=True, text=True).stdout
    assert "pre_lock" in out and "core-hours" in out and "upper bound" in out
