"""Tests for audit_v2.py (external review round 5): the inference audit (raw, calibrated, and Holm-adjusted p-values of Q1
and Q4 beside the report's decisions), the Q4 per-market recomputation used for the stability table, and the scan for
numerically extreme descriptive intervals."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_v2 as A  # noqa: E402


def test_holm_adjusted_is_the_step_down_maximum():
    # sorted 0.01, 0.02, 0.04 with m = 3: 0.03, max(0.03, 0.04) = 0.04, max(0.04, 0.04) = 0.04
    assert A.holm_adjusted([0.04, 0.01, 0.02]) == pytest.approx([0.04, 0.03, 0.04])
    assert A.holm_adjusted([0.0004, 0.0004]) == pytest.approx([0.0008, 0.0008])
    assert A.holm_adjusted([0.6, 0.9]) == pytest.approx([1.0, 1.0])            # capped at one


def _q4_report(raw, kappa=0.25):
    from sim.decisions_v2 import q4_markets
    pa, pb = [r[0] for r in raw], [r[1] for r in raw]; d = q4_markets(pa, pb, kappa)
    mk = {f"fresh{i}": {"p_gain": a, "p_eff": b} for i, (a, b) in enumerate(raw)}
    return {"q4": {"markets": mk, "p": d["p"], "passing": [f"fresh{i}" for i, ok in enumerate(d["pass"]) if ok]}}


def test_q4_audit_reads_the_stored_p_values_as_raw_and_reproduces_the_decisions():
    raw = [(1.0, 0.0001), (0.0001, 0.0001), (1.0, 0.0001), (0.0001, 0.0001), (0.0001, 0.0001), (1.0, 0.0001)]
    rows, problems = A.q4_audit(_q4_report(raw), kappa=0.25)
    assert problems == []
    assert rows["fresh1"]["calibrated_gain"] == pytest.approx(0.0004) and rows["fresh1"]["holm_adjusted"] == pytest.approx(0.0024)
    assert rows["fresh1"]["decision"] == "pass" and rows["fresh0"]["decision"] == "fail"


def test_q4_audit_reports_a_report_that_disagrees_with_the_rule():
    raw = [(1.0, 0.0001), (0.0001, 0.0001), (1.0, 0.0001), (0.0001, 0.0001), (0.0001, 0.0001), (1.0, 0.0001)]
    rep = _q4_report(raw); rep["q4"]["p"][1] = 0.0001                           # as if calibration had been skipped
    _, problems = A.q4_audit(rep, kappa=0.25)
    assert any("fresh1" in p for p in problems)


def test_q1_audit_recovers_the_raw_value_and_adjusts_over_both_slots():
    rep = {"q1": {"tests": {"a": {"p": 0.0004, "reject": True}, "b": {"p": 0.0004, "reject": True}}}}
    rows, problems = A.q1_audit(rep, kappa=0.5, raw={"a": 0.0002, "b": 0.0002})
    assert problems == [] and rows["a"]["raw"] == pytest.approx(0.0002) and rows["a"]["holm_adjusted"] == pytest.approx(0.0008)
    _, problems = A.q1_audit(rep, kappa=0.5, raw={"a": 0.0004, "b": 0.0002})
    assert problems                                                              # stored value is not calibrated(raw)


def test_q4_market_recomputes_the_registered_quantities():
    rng = np.random.default_rng(1)
    f0, f1 = {"gain": 0.5 + 0.01 * rng.standard_normal(400)}, {"gain": 0.1 + 0.01 * rng.standard_normal(400),
                                                               "eff_attack": 0.95 + 0.001 * rng.standard_normal(400)}
    row = A.q4_market(f0, f1, kappa=0.25)
    assert row["gain_diff"] == pytest.approx(np.mean(f0["gain"] - f1["gain"]))
    assert row["p_gain"] == pytest.approx(0.0001) and row["gain_diff_lower"] > 0.10 and row["eff_lower"] > 0.90


def test_extreme_scan_finds_huge_finite_bounds_and_nothing_else():
    rep = {"q2": {"per_market": {"D2+H3": {"fresh1": {"fixed_reference_term": {"P": {"estimate": 0.0, "interval": [-7.2e5, -0.0]},
                                                                               "G": {"estimate": 0.1, "interval": [0.0, 0.2]}}}}}}}
    hits = A.extreme_intervals(rep, limit=1e3)
    assert hits == ["q2/per_market/D2+H3/fresh1/fixed_reference_term/P"]


def test_studentization_diagnostic_reports_the_frozen_bootstrap_t_statistics():
    from sim.intervals import studentized_tstats
    x = np.zeros(400); x[:3] = [1.0, 1.0 + 1e-13, 1.0 - 1e-13]                 # three near-equal outliers among zeros
    d = A.studentization(x)
    _, se, t = studentized_tstats(x, 9999, A.V2_RESAMPLE_SEED)
    assert d["se"] == pytest.approx(se) and d["max_abs_t"] == pytest.approx(float(np.max(np.abs(t))))
    assert d["seeds_above_1e-9"] == 3 and d["share_resamples_without_them"] == pytest.approx((1 - 3 / 400) ** 400)
    assert d["share_zero"] == pytest.approx(397 / 400) and d["resamples_abs_t_over_100"] == int(np.sum(np.abs(t) > 100))
