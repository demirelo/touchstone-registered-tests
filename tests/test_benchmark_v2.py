"""Benchmark v2 (design 8.2): the cost table from measured timings, caps, approval, and the pod command line."""
import json

import pytest

UNIT = 1500.0
DESIGN = {"d2h3_cell": UNIT, "x7_cell": 2.5 * UNIT, "inner": 0.04 * UNIT, "inner_x7": 0.1 * UNIT, "doubling": UNIT, "doubling_x7": 2.5 * UNIT,
          "episode": UNIT / 18000, "bootstrap_batch": 10 * UNIT, "eval200_extra_fraction": 0.16}


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
