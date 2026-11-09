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


def test_training_feasible_weight_meets_both_empirical_checks():
    # external review round 6: the largest grid weight at which the evaluation lower bound and the training mean gain are
    # both non-negative (C* with D2+H3: training break-even 0.47676, so 0.4765 on the 0.0005 grid)
    rng = np.random.default_rng(3)
    gw0, gp = -0.1 + 0.001 * rng.standard_normal(200), 0.11 + 0.001 * rng.standard_normal(200)
    ew0, ep = np.full(200, 0.84), np.full(200, 1.0)
    g0_tr, gp_tr = -0.0937682027, 0.0854403021
    m = P.feasible_mixture(gw0, ew0, gp, ep, g0_tr, gp_tr)
    assert m["weight"] == pytest.approx(0.4765)
    assert P.train_mix(g0_tr, gp_tr, m["weight"]) >= 0 > P.train_mix(g0_tr, gp_tr, m["weight"] + 0.0005)
    assert m["train_mix"] == pytest.approx(P.train_mix(g0_tr, gp_tr, 0.4765))
    g = 0.4765 * gw0 + (1 - 0.4765) * gp
    assert m["lower"] == pytest.approx(g.mean() - 1.645 * g.std(ddof=1) / np.sqrt(200)) and m["lower"] >= 0


def test_w0_gain_refuses_a_w1_record_with_another_seed_order(tmp_path):
    ctx = "headline@rho0.2"
    _rec(tmp_path, f"{ctx}|C*|D2+H3|W0", seeds=[1, 2], normalized=[0.1, 0.2], eff=[0.8, 0.8])
    _rec(tmp_path, f"{ctx}|C*|D2+H3|W1", seeds=[2, 1], normalized=[0.3, 0.3], constraint=[0.0, 0.0], eff=[1.0, 1.0])
    with pytest.raises(ValueError, match="seed order"):
        P._w0_gain(tmp_path, "C*")


def test_training_rows_export_seeds_policies_and_reference(tmp_path):
    ctx = "headline@rho0.2"; seeds = [11, 12, 13, 14, 15]
    ref = {"per_seed_normalized": [0.5] * 5, "choice": 1, "candidates": [{"name": "a"}, {"name": "ref-b"}],
           "provenance": {"seeds_train": seeds}}
    p = tmp_path / "reference" / ctx / "Cstar.json"; p.parent.mkdir(parents=True); p.write_text(json.dumps(ref))
    k0, kp = {"x": 0}, {"x": 1}
    for rid, body in ((f"{ctx}|C*|D2+H3|W0", {"selected": k0, "welfare": {"archive": [{"knobs": k0, "per_seed_normalized": [0.4] * 5}]},
                                               "provenance": {"seeds_train": seeds}}),
                      (f"{ctx}|C*|H4|profit", {"attack": {"best_knobs": kp, "archive": [{"knobs": kp, "per_seed_normalized": [0.7] * 5}]},
                                               "provenance": {"seeds_train": seeds}})):
        q = tmp_path / "search" / (P.safe(rid) + ".json"); q.parent.mkdir(parents=True, exist_ok=True); q.write_text(json.dumps(body))
    rows = P.train_rows(tmp_path, "C*", ["H4"])
    assert [r["seed"] for r in rows if r["component"] == "W0"] == seeds
    r = next(r for r in rows if r["component"] == "H4" and r["seed"] == 13)
    assert r["reference"] == "ref-b" and r["normalized"] == pytest.approx(0.7) and r["reference_normalized"] == pytest.approx(0.5)
    assert r["gain"] == pytest.approx(0.2) and json.loads(r["policy_knobs"]) == kp


def test_welfare_table_adds_the_training_feasible_row_beside_the_failed_one():
    fm = {"weight": 0.4765, "estimate": 0.00093096, "lower": 0.00069945, "efficiency": 0.922401, "train_mix": 0.00004745}
    mx = {"weight": 0.48, "estimate": 0.00029715, "lower": 0.0000668, "efficiency": 0.921852, "train_mix": -0.00057978,
          "train_feasible_mixture": fm}
    res = {"q1_split": {}, "q4_diag": {}, "stability": {"q1": {}},
           "welfare": {"C*": {"w1": {"efficiency": 0.997}, "w0": {"efficiency": 0.840}, "mixtures": {"D2+H3": mx}}}}
    t = P.tables(res)["welfare_mix"]
    assert "D2+H3 & 0.4800" in t and "D2+H3, training-feasible & 0.4765" in t       # the failed row stays
    assert "0.0000475" in t and "0.000931" in t and "0.9224" in t


def _report_doubling(cells):
    return {"doubling": {rid: {"heldout": {"gain": g, "seeds": [1, 2]}} for rid, g in cells.items()}}


def test_doubled_winners_pair_the_heldout_gains_against_the_frozen_search(tmp_path):
    # external review round 9: the doubled-search winners, evaluated on the same seeds, beside the frozen searches
    for rule, g in (("C*", [0.10, 0.12]), ("F111", [0.14, 0.16]), ("F000", [0.40, 0.42])):
        _rec(tmp_path, f"m0@rho0.2|{rule}|D2+H3|profit", gain=g, seeds=[1, 2])
    rep = _report_doubling({"m0@rho0.2|C*|D2+H3|profit": [0.20, 0.22], "m0@rho0.2|F111|D2+H3|profit": [0.14, 0.16],
                            "m0@rho0.2|F000|D2+H3|profit": [0.40, 0.42]})
    got = P.doubled(tmp_path, rep, ["m0"], fams=("D2+H3",))
    row = got["D2+H3"]["markets"]["m0"]
    assert row["q1_frozen"] == pytest.approx(-0.04) and row["q1_doubled"] == pytest.approx(0.06)       # C* - F111 changes sign
    assert row["q4_frozen"] == pytest.approx(0.26) and row["q4_doubled"] == pytest.approx(0.26)         # F000 - F111
    assert got["D2+H3"]["pooled"]["q1_doubled"] == pytest.approx(0.06)
    assert got["D2+H3"]["absolute"] == {"C*": {"mean_gain": pytest.approx(0.11)}, "F111": {"mean_gain": pytest.approx(0.15)}}


def test_doubled_refuses_a_heldout_evaluation_on_other_seeds(tmp_path):
    for rule in ("C*", "F111", "F000"):
        _rec(tmp_path, f"m0@rho0.2|{rule}|D2+H3|profit", gain=[0.1, 0.1], seeds=[1, 2])
    rep = _report_doubling({f"m0@rho0.2|{r}|D2+H3|profit": [0.1, 0.1] for r in ("C*", "F111", "F000")})
    rep["doubling"]["m0@rho0.2|C*|D2+H3|profit"]["heldout"]["seeds"] = [3, 4]
    with pytest.raises(ValueError):
        P.doubled(tmp_path, rep, ["m0"], fams=("D2+H3",))


def test_honest_profile_keeps_unrounded_values_and_the_r3_minus_cstar_difference():
    bins = lambda a, p: [{"age": [0, 10], "audited_share": a, "profit_per_round": p, "false_refund": 1e-5},
                         {"age": [10, 20], "audited_share": a / 2, "profit_per_round": p, "false_refund": 1e-5}]
    rep = {"q3": {"diagnostic": {"F111": {"replace_at": 50, "bins": bins(1.0, 0.000280)},
                                 "C*": {"replace_at": 50, "bins": bins(0.4, 0.000286)},
                                 "F000": {"replace_at": 50, "bins": bins(0.25, 0.000287)}}}}
    got = P.honest(rep)
    assert got["F111"]["bins"][0]["audited_share"] == 1.0 and got["F111"]["mean_profit_per_round"] == pytest.approx(0.000280)
    assert got["r3_minus_cstar_profit_per_round"] == pytest.approx(-0.000006)


def test_tables_show_doubled_winners_and_the_honest_profile():
    res = {"q1_split": {}, "welfare": {}, "q4_diag": {}, "stability": {"q1": {}},
           "doubled": {"D2+H3": {"markets": {"fresh3": {"q1_frozen": -0.0382, "q1_doubled": 0.0149, "q4_frozen": 0.2626, "q4_doubled": 0.2600}}},
                       "X7-SC": {"markets": {"fresh3": {"q1_frozen": 0.01, "q1_doubled": 0.01}}}},
           "honest": {r: {"bins": [{"age": [0, 10], "audited_share": a, "profit_per_round": 0.00028, "false_refund": 2e-5}] * 3,
                          "mean_profit_per_round": 0.00028, "mean_false_refund": 2e-5} for r, a in (("F000", 0.25), ("F111", 1.0), ("C*", 0.428))}}
    t = P.tables(res)
    assert "fresh3 & $-0.038$ & $0.015$ & $0.010$ & $0.010$ & $0.263$ & $0.260$" in t["doubled"]
    assert "C* & 0.428" in t["honest"] and "R3 (F111) & 1.000" in t["honest"] and "2.80" in t["honest"] and "2.00" in t["honest"]
