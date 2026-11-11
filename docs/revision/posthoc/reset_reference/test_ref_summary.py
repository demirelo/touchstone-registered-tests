"""Test of the reference-check aggregation (external review r3, problem 2), written before the code."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ref_resets as RR  # noqa: E402


def _cells():
    c = {}
    for i in range(6):
        m = f"fresh{i}@rho0.2"
        c[f"{m}|F000"] = {"mean_resets": 5.0, "replacement_value_to_reference": 0.004, "validation_mean_diff": 1e-4}
        c[f"{m}|F111"] = {"mean_resets": 1.0, "replacement_value_to_reference": 0.001, "validation_mean_diff": -2e-4}
        c[f"{m}|C*"] = {"mean_resets": 0.0, "validation_mean_diff": 0.0}          # no reset: no replacement value
    return c


def test_summary_shifts_both_gaps_by_the_b3_minus_r3_replacement_value():
    reset = {"base": {"G": {"D2+H3": {"pooled": {"estimate": 0.2}}, "D2": {"pooled": {"estimate": -0.01}}}}}
    s = RR.summarize(_cells(), reset)
    assert s["n"] == 18 and s["refs_with_any_reset"] == 12
    assert s["G_shift_pooled"] == pytest.approx(0.003)
    assert s["Cstar_minus_R3_shift_pooled"] == pytest.approx(-0.001)
    assert s["S_with_non_replacing_references"] == pytest.approx(1 - (-0.01 + 0.003) / (0.2 + 0.003))
    assert s["max_abs_replacement_value"] == pytest.approx(0.004) and s["max_abs_validation_mean_diff"] == pytest.approx(2e-4)
