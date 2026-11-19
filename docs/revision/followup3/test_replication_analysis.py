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
    a = RA.analyse(_recs(g), _audit(), resamples=199)
    b = RA.analyse(_recs(g), _audit(), resamples=199)
    lo, hi = a["bootstrap"]["0.05"]["d"]["pooled"]["ci95"]
    assert a == b and lo <= a["paired_changes"]["0.05"]["d"]["mean"] <= hi


def test_nonfinite_gain_is_refused():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    g["0.03"]["rep1"]["B3"][0] = float("nan")
    with pytest.raises(ValueError):
        RA.paired_changes(g)


# ---- review rep-impl-r1 (Sol 7, 8; Astra 5, 6): six named markets, matched seeds, no crash, secondary outputs ----------

def _recs(g: dict) -> dict:
    """Records per cell from gains: attack term = gain + 0.5, reference term 0.5, efficiency 0.9, seeds 0..n-1."""
    return {p: {m: {r: {"gain": xs, "attack": [x + 0.5 for x in xs], "reference": [0.5] * len(xs),
                        "eff_attack": [0.9] * len(xs), "seeds": list(range(len(xs)))} for r, xs in rs.items()}
                for m, rs in ms.items()} for p, ms in g.items()}


def _audit():
    return {p: {m: (5, 100) if p == "0.05" else (30, 100) for m in MK} for p in RATES}


def test_a_market_missing_everywhere_makes_the_contrast_incomplete():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    for p in RATES:
        g[p].pop("rep5")                                 # five markets, all lower: must not score "met"
    e = RA.expectations(RA.criteria(RA.paired_changes(g)), _audit())
    assert [e[k]["verdict"] for k in "1234"] == ["not scorable"] * 4


def test_unequal_seed_vectors_are_refused():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    g["0.05"]["rep2"]["R3"] = g["0.05"]["rep2"]["R3"][:-1]
    with pytest.raises(ValueError):
        RA.paired_changes(g)
    r = _recs(_gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20}))
    r["0.03"]["rep1"]["B3"]["seeds"] = list(range(1, 21))   # same length, other seeds
    with pytest.raises(ValueError):
        RA.analyse(r, _audit(), resamples=19)


def test_a_missing_rate_or_r3_cell_is_not_scorable_and_does_not_crash():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    g.pop("0.03"); g["0.05"]["rep0"].pop("R3")
    out = RA.analyse(_recs(g), _audit(), resamples=19)
    assert [out["expectations"][k]["verdict"] for k in "1234"] == ["not scorable"] * 4
    assert out["bootstrap"]["0.05"]["d"]["pooled"] is None and out["bootstrap"]["0.03"]["q"]["pooled"] is None


def test_expectation5_needs_all_six_markets():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    a = _audit()
    for p in RATES:
        a[p].pop("rep4")
    assert RA.expectations(RA.criteria(RA.paired_changes(g)), a)["5"]["verdict"] == "not scorable"


def test_bootstrap_uses_one_index_vector_per_market_shared_by_rules_and_rates():
    g = _gains({"0": 0.0, "0.03": 0.0, "0.05": 0.0})
    for m in MK:                                         # noisy, but identical at every rate: every paired change is 0
        for r in ("R3", "C*", "C-thr", "B3"):
            xs = [((s * 7919 + MK.index(m) * 31 + len(r)) % 97) / 97 for s in range(20)]
            for p in RATES:
                g[p][m][r] = list(xs)
    b = RA.analyse(_recs(g), _audit(), resamples=199)["bootstrap"]
    assert b["0.05"]["d"]["pooled"]["ci95"] == [0.0, 0.0]
    assert all(v["ci95"] == [0.0, 0.0] for v in b["0.03"]["q"]["markets"].values())
    b2 = RA.analyse(_recs(g), _audit(), resamples=199)["bootstrap"]
    assert b == b2                                       # deterministic (seed 0)


def test_secondary_outputs_absolute_contrasts_terms_and_efficiency():
    g = _gains({"0": 0.0, "0.03": 0.06, "0.05": 0.20})
    out = RA.analyse(_recs(g), _audit(), resamples=99)
    ab = out["absolute"]["0.05"]["d"]
    assert set(ab) >= {"markets", "mean", "t95", "pooled_ci95"} and all(set(v) >= {"estimate", "ci95"} for v in ab["markets"].values())
    t = out["terms"]["0.05"]["rep0"]["R3"]
    assert math.isclose(t["attack"] - t["reference"], t["gain"], abs_tol=1e-12) and math.isclose(t["eff_attack"], 0.9)
    assert set(out) >= {"paired_changes", "criteria", "expectations", "absolute", "terms", "bootstrap"}
