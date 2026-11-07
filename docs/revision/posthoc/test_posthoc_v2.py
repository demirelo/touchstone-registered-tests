"""Tests for posthoc_v2.py (exploratory analyses after the report; external review round 4): the Q1 split into attacked and
reference terms, the episode-mixture welfare frontier, and the per-market Q4 diagnostics."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import posthoc_v2 as P  # noqa: E402


def _rec(out, rid, **f):
    p = out / "evaluate" / (P.safe(rid) + ".json"); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(f))


def test_split_terms_add_up_to_the_gain_difference(tmp_path):
    s = [10.0, 10.0]
    _rec(tmp_path, "m0@rho0.2|C*|D2+H3|profit", profit_attack=[3.0, 5.0], profit_ref=[1.0, 1.0], sstar=s)
    _rec(tmp_path, "m0@rho0.2|F111|D2+H3|profit", profit_attack=[2.0, 2.0], profit_ref=[0.5, 0.5], sstar=s)
    got = P.split(tmp_path, ["m0"], "C*", "F111", "D2+H3", n=10)
    # g_C = (2, 4), g_F = (1.5, 1.5): d mean = 1.5; attacked term = (1, 3) mean 2; reference term = -(0.5, 0.5) mean -0.5
    assert got["pooled"]["estimate"] == pytest.approx(1.5)
    assert got["pooled"]["attacked"] == pytest.approx(2.0) and got["pooled"]["reference"] == pytest.approx(-0.5)


def test_mixture_weight_is_the_largest_with_a_nonnegative_lower_bound():
    rng = np.random.default_rng(0)
    gw0, gp = -0.1 + 0.001 * rng.standard_normal(200), 0.06 + 0.001 * rng.standard_normal(200)
    ew0, ep = np.full(200, 0.84), np.full(200, 1.0)
    m = P.mixture(gw0, ew0, gp, ep)
    assert 0.0 < m["weight"] < 0.375                          # 0.375 is where the mean gain reaches zero
    g = m["weight"] * gw0 + (1 - m["weight"]) * gp
    assert g.mean() - 1.645 * g.std(ddof=1) / np.sqrt(len(g)) >= 0
    assert m["efficiency"] == pytest.approx(m["weight"] * 0.84 + (1 - m["weight"]) * 1.0)


def test_no_mixture_when_the_profitable_policy_is_not_profitable():
    z = np.zeros(200)
    assert P.mixture(z - 0.1, z + 0.84, z - 0.01, z + 1.0)["weight"] == 0.0


def test_weight_label_and_stability_table_keep_the_needed_precision():
    assert P.weight_label(0.4195) == "41.95 percent"            # a rounded 0.42 flips the sign of the lower bound
    res = {"q1_split": {}, "welfare": {}, "q4_diag": {},
           "stability": {"q1": {"C*-F111|D2+H3": {"estimate_report": 0.020720, "estimate_registered_cfg": 0.020917, "category_registered_cfg": "eq"}}}}
    assert "0.0207" in P.tables(res)["stability"] and "0.0209" in P.tables(res)["stability"]


def test_sensitivity_is_linear_in_the_weight_with_its_own_bound():
    rng = np.random.default_rng(2)
    gw0, gp = -0.1 + 0.01 * rng.standard_normal(200), 0.06 + 0.01 * rng.standard_normal(200)
    ew0, ep = np.full(200, 0.84), np.full(200, 1.0)
    rows = P.sensitivity(gw0, ew0, gp, ep, (0.0, 0.25, 0.5))
    assert [r["weight"] for r in rows] == [0.0, 0.25, 0.5]
    g = 0.25 * gw0 + 0.75 * gp
    assert rows[1]["estimate"] == pytest.approx(g.mean()) and rows[1]["efficiency"] == pytest.approx(0.25 * 0.84 + 0.75)
    assert rows[1]["lower"] == pytest.approx(g.mean() - 1.645 * g.std(ddof=1) / np.sqrt(200))


def test_welfare_table_prints_small_gains_with_their_bound_and_every_companion():
    res = {"q1_split": {}, "q4_diag": {}, "stability": {"q1": {}},
           "welfare": {"F111": {"w1": {"efficiency": 0.997}, "w0": {"efficiency": 0.840},
                                "mixtures": {"H4": {"weight": 0.4195, "weight_label": "41.95 percent", "estimate": 0.000374263, "lower": 0.0000279, "efficiency": 0.931956},
                                             "D2+H3": {"weight": 0.339, "weight_label": "33.90 percent", "estimate": 0.000252853, "lower": 0.0000101, "efficiency": 0.944510,
                                                       "train_mix": -0.00057978}}}}}
    t = P.tables(res)["welfare_mix"]
    assert "\\ensuremath{-0.000580}" in t and "Train gain" in t
    assert "0.000374" in t and "0.0000279" in t and "0.000253" in t and "D2+H3" in t and "H4" in t


def test_a_profitable_w0_attack_is_one_row_without_a_companion():
    mx = {"weight": 1.0, "weight_label": "100.00 percent", "estimate": 0.254, "lower": 0.253, "efficiency": 0.8387, "train_mix": 0.2}
    res = {"q1_split": {}, "q4_diag": {}, "stability": {"q1": {}},
           "welfare": {"F000": {"w1": {"efficiency": 0.839}, "w0": {"efficiency": 0.839}, "mixtures": {"H4": mx, "D2+H3": dict(mx)}}}}
    t = P.tables(res)["welfare_mix"]
    assert t.count("F000 &") == 1 and "none (W0 estimated gain positive)" in t


def test_mixture_labels_keep_three_significant_digits():
    assert P.label3(0.000374263) == "0.000374" and P.label3(0.0000279) == "0.0000279" and P.label3(None) == "n/a"


def _search(out, rid, **rec):
    p = out / "search" / (P.safe(rid) + ".json"); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(rec))


def test_training_gain_reads_the_archive_entry_of_the_evaluated_policy(tmp_path):
    ref = [0.05, 0.06]
    p = tmp_path / "reference" / "headline@rho0.2" / "F111.json"; p.parent.mkdir(parents=True); p.write_text(json.dumps({"per_seed_normalized": ref}))
    _search(tmp_path, "headline@rho0.2|F111|D2+H3|W0", selected={"a": 1},
            welfare={"archive": [{"knobs": {"a": 0}, "per_seed_normalized": [9, 9]}, {"knobs": {"a": 1}, "per_seed_normalized": [0.0, 0.0]}]})
    _search(tmp_path, "headline@rho0.2|F111|H4|profit", attack={"best_knobs": {"b": 2}, "best_f": 99.0,
            "archive": [{"knobs": {"b": 2}, "per_seed_normalized": [0.15, 0.16]}]})
    assert P.train_gain_w0(tmp_path, "F111") == pytest.approx(-0.055)            # mean of (0 - 0.05, 0 - 0.06)
    assert P.train_gain_profit(tmp_path, "F111", "H4") == pytest.approx(0.10)       # archive, not best_f
    assert P.train_mix(-0.055, 0.10, 0.4) == pytest.approx(0.4 * -0.055 + 0.6 * 0.10)
