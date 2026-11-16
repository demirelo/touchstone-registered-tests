"""Tests for the replication analysis (plan sections 2 and 3) on synthetic records."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replication_analysis as RA  # noqa: E402

MK = [f"rep{i}" for i in range(6)]
RATES = ("0", "0.03", "0.05")


def _gains(shift: dict, n: int = 20) -> dict:
    """gains[rate][market][rule] = per-seed list; R3's gain rises with churn by shift[rate] on every market."""
    out = {}
    for p in RATES:
        out[p] = {}
        for i, m in enumerate(MK):
            base = {"R3": 0.10, "C*": 0.12, "C-thr": 0.11, "B3": 0.30}
            g = {r: [v + 0.001 * ((s + i) % 5) for s in range(n)] for r, v in base.items()}
            g["R3"] = [x + shift[p] + 0.002 * i for x in g["R3"]]
            out[p][m] = g
    return out


def test_paired_change_uses_each_market_s_own_no_churn_value():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    d = RA.paired_changes(g)
    # d = C* - R3: R3 rises by 0.20 at 0.05, so the change in d is -0.20 on every market
    assert all(math.isclose(v, -0.20, abs_tol=1e-12) for v in d["0.05"]["d"]["markets"].values())
    assert d["0.05"]["d"]["lower"] == 6 and math.isclose(d["0.05"]["d"]["mean"], -0.20, abs_tol=1e-12)
    lo, hi = d["0.05"]["d"]["t95"]
    assert lo - 1e-12 <= -0.20 <= hi + 1e-12      # equal changes give a zero-width interval


def test_support_and_material_criteria():
    g = _gains({"0": 0.0, "0.03": 0.02, "0.05": 0.06})
    c = RA.criteria(RA.paired_changes(g))
    assert c["0.05"]["d"] == {"support": True, "material": True} and c["0.03"]["q"] == {"support": True, "material": False}
    g2 = _gains({"0": 0.0, "0.03": 0.0, "0.05": 0.0})
    c2 = RA.criteria(RA.paired_changes(g2))
    assert c2["0.05"]["d"]["support"] is False


def test_support_needs_five_of_six_markets():
    g = _gains({"0": 0.0, "0.03": 0.0, "0.05": 0.05})
    for m in MK[:2]:                                    # two markets where R3 does not get worse
        g["0.05"][m]["R3"] = list(g["0"][m]["R3"])
    assert RA.criteria(RA.paired_changes(g))["0.05"]["d"]["support"] is False


def test_expectations_scored_as_written_and_unscorable_when_a_cell_is_missing():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    audit = {p: {m: (5, 100) if p == "0.05" else (30, 100) for m in MK} for p in RATES}
    e = RA.expectations(RA.criteria(RA.paired_changes(g)), audit)
    assert [e[k]["verdict"] for k in "12345"] == ["met"] * 5
    g["0.05"]["rep3"].pop("C-thr")
    e2 = RA.expectations(RA.criteria(RA.paired_changes(g)), audit)
    assert e2["4"]["verdict"] == "not scorable" and e2["1"]["verdict"] == "met"


def test_expectation5_zero_denominator_counts_as_not_below():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    audit = {p: {m: (5, 100) if p == "0.05" else (30, 100) for m in MK} for p in RATES}
    for m in MK[:2]:
        audit["0.05"][m] = (0, 0)
    assert RA.expectations(RA.criteria(RA.paired_changes(g)), audit)["5"]["verdict"] == "not met"


def test_seed_bootstrap_is_paired_and_deterministic():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    a = RA.pooled_paired(g["0.05"], "C*", resamples=199, seed=0)
    b = RA.pooled_paired(g["0.05"], "C*", resamples=199, seed=0)
    assert a == b and a["ci95"][0] <= a["estimate"] <= a["ci95"][1]


def test_nonfinite_gain_is_refused():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    g["0.03"]["rep1"]["B3"][0] = float("nan")
    with pytest.raises(ValueError):
        RA.paired_changes(g)
