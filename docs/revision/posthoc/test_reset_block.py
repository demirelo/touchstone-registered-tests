"""Tests of the reset block (docs/revision/reset-experiment-plan.md, draft 5, sections 5 and 6), written before the code."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reset_block as RB  # noqa: E402

M6 = tuple(f"fresh{i}" for i in range(6))


def _cells(i_b3=0.3, i_r3=0.01, i_c=0.05, g_r3_d2h3=0.05, g_r3_d2=0.03, n=40, noise=0.0, seed=0):
    """Synthetic per-seed gains: D2+H3 gains are D2 gains plus I; B3-R3 gap under D2 is 0.01 by construction."""
    rng = np.random.default_rng(seed); cells = {}
    for m in M6:
        e = rng.normal(0, noise, n) if noise else np.zeros(n)
        d2 = {"F111": g_r3_d2 + e, "F000": g_r3_d2 + 0.01 + e, "C*": g_r3_d2 + 0.005 + e}
        d2h3 = {"F111": d2["F111"] + i_r3, "F000": d2["F000"] + i_b3, "C*": d2["C*"] + i_c}
        cells[m] = {"D2+H3": d2h3, "D2": d2}
    return cells


def test_point_estimates_of_i_contrasts_gaps_and_share():
    s = RB.statistics(_cells())
    assert s["I"]["F000"]["pooled"] == pytest.approx(0.3) and s["I"]["F111"]["pooled"] == pytest.approx(0.01)
    assert s["contrast"]["B3-R3"]["pooled"] == pytest.approx(0.29) and s["contrast"]["C*-R3"]["pooled"] == pytest.approx(0.04)
    assert s["G"]["D2"]["pooled"] == pytest.approx(0.01) and s["G"]["D2+H3"]["pooled"] == pytest.approx(0.30)
    assert s["S"]["pooled"] == pytest.approx(1 - 0.01 / 0.30)


def test_pooled_is_the_equal_weight_mean_of_market_means():
    c = _cells(); c["fresh0"]["D2+H3"]["F000"] = c["fresh0"]["D2+H3"]["F000"] + 0.6   # I(B3) = 0.9 at fresh0 only
    s = RB.statistics(c)
    assert s["I"]["F000"]["markets"]["fresh0"] == pytest.approx(0.9)
    assert s["I"]["F000"]["pooled"] == pytest.approx((0.9 + 5 * 0.3) / 6)


def test_share_undefined_when_the_denominator_lower_bound_is_at_or_below_005():
    c = _cells(i_b3=0.04, i_r3=0.01, noise=0.02)          # pooled G(D2+H3) = 0.04: lower bound below 0.05
    r = RB.analyse(c, b=999, seed=1)
    assert r["S"]["pooled"]["value"] is None and r["S"]["pooled"]["reason"].startswith("not defined")
    assert r["G"]["D2+H3"]["pooled"]["estimate"] == pytest.approx(0.04)  # the gaps are reported anyway


def test_share_defined_and_not_clipped():
    c = _cells(i_b3=0.3, i_r3=0.01)
    for m in M6:                                           # G(D2) negative, so S > 1
        c[m]["D2"]["F000"] = c[m]["D2"]["F111"] - 0.05; c[m]["D2+H3"]["F000"] = c[m]["D2"]["F000"] + 0.3
    r = RB.analyse(c, b=199, seed=1)
    assert r["S"]["pooled"]["value"] > 1


def test_bootstrap_uses_the_same_seed_indices_for_every_rule_and_family_of_a_market():
    c = _cells(noise=0.05, seed=3)                         # identical noise in every rule and family of a market
    r = RB.analyse(c, b=499, seed=2)
    lo, hi = r["G"]["D2"]["pooled"]["ci95"]               # the shared noise cancels in a paired contrast
    assert hi - lo == pytest.approx(0.0, abs=1e-12)
    lo, hi = r["I"]["F000"]["pooled"]["ci95"]
    assert hi - lo == pytest.approx(0.0, abs=1e-12)


def test_bootstrap_is_reproducible_and_has_9999_resamples_by_default():
    assert RB.B == 9999
    c = _cells(noise=0.05, seed=4)
    for m in M6:                                           # break the pairing so intervals have width
        c[m]["D2"]["F111"] = c[m]["D2"]["F111"] + np.random.default_rng(9).normal(0, 0.05, 40)
    a, b = RB.analyse(c, b=299, seed=5), RB.analyse(c, b=299, seed=5)
    assert a["G"]["D2"]["pooled"]["ci95"] == b["G"]["D2"]["pooled"]["ci95"]
    lo, hi = a["G"]["D2"]["pooled"]["ci95"]
    assert lo < a["G"]["D2"]["pooled"]["estimate"] < hi


def test_market_sensitivity_sign_counts_and_leave_one_out_share():
    c = _cells(); c["fresh2"]["D2+H3"]["F000"] = c["fresh2"]["D2"]["F000"] - 0.02     # I(B3) < I(R3) at fresh2
    r = RB.analyse(c, b=199, seed=1)
    assert r["sensitivity"]["signs"]["B3-R3"] == {"positive": 5, "n": 6}
    assert r["sensitivity"]["signs"]["C*-R3"] == {"positive": 6, "n": 6}
    loo = r["sensitivity"]["S_leave_one_out"]
    assert set(loo) == set(M6) and all(v["value"] is not None for v in loo.values())


def test_leave_one_out_has_its_own_five_market_gate():
    c = _cells(i_b3=0.3)
    for m in M6[1:]:                                       # only fresh0 carries a B3 - R3 gap under D2+H3
        c[m]["D2+H3"]["F000"] = c[m]["D2+H3"]["F111"] + 0.0
    r = RB.analyse(c, b=199, seed=1)
    assert r["sensitivity"]["S_leave_one_out"]["fresh0"]["value"] is None     # five markets left: no gap
    assert r["sensitivity"]["S_leave_one_out"]["fresh1"]["value"] is not None  # fresh0 kept: 0.30 / 5 = 0.06 > 0.05


def test_missing_cell_is_reported_not_imputed():
    c = _cells(); del c["fresh3"]["D2"]["C*"]
    r = RB.analyse(c, b=99, seed=1)
    assert "fresh3|C*|D2" in r["missing"]
    assert "fresh3" not in r["I"]["C*"]["markets"]


def test_seed_mismatch_refused(tmp_path):
    ev, rs = _write(tmp_path, seeds_d2=list(range(1, 41)))
    with pytest.raises(ValueError, match="seeds"):
        RB.load(ev, rs, _report(tmp_path, ev), M6, n_seeds=40)


def test_expectation_scoring_met_failed_not_established():
    base = {"all_markets": {"B3-R3": True, "C*-R3": True}, "S": 0.8}
    dbl = {"all_markets": {"B3-R3": True, "C*-R3": False}, "S": 0.4}
    e = RB.score(base, dbl)
    assert e["B3-R3 on all six"] == "met"
    assert e["C*-R3 on all six"] == "not established (search-sensitive)"
    assert e["pooled S > 0.5"] == "not established (search-sensitive)"
    e = RB.score({"all_markets": {"B3-R3": False, "C*-R3": False}, "S": None}, {"all_markets": {"B3-R3": False, "C*-R3": False}, "S": None})
    assert e["B3-R3 on all six"] == "failed" and e["pooled S > 0.5"] == "S not defined"


def test_expectations_need_all_six_markets():
    c = _cells(); del c["fresh1"]["D2"]["F000"]
    r = RB.analyse(c, b=99, seed=1)
    assert r["expectation_inputs"]["all_markets"]["B3-R3"] is None    # a missing cell is not a pass


# ---- loading from records ----

def _write(tmp, seeds_d2=None, n=40):
    ev, rs = tmp / "eval", tmp / "reset"
    for d in (ev / "evaluate", rs / "evaluate", rs / "doubling"):
        d.mkdir(parents=True, exist_ok=True)
    seeds = list(range(n))
    for m in M6:
        for rule in RB.RULES:
            for fam, root, s in (("D2+H3", ev, seeds), ("D2", rs, seeds_d2 or seeds)):
                rid = f"{m}@rho0.2|{rule}|{fam}|profit"
                (root / "evaluate" / (RB.safe(rid) + ".json")).write_text(json.dumps({"id": rid, "seeds": s, "gain": [0.1] * n}))
            rid = f"{m}@rho0.2|{rule}|D2|profit"
            (rs / "doubling" / (RB.safe(rid) + ".json")).write_text(json.dumps({"id": rid, "attack_change": 0.01, "reference_change": 0.0,
                                                                                "incomplete": False, "heldout": {"seeds": seeds_d2 or seeds, "gain": [0.2] * n}}))
    return ev, rs


def _report(tmp, ev, n=40):
    return {"doubling": {f"{m}@rho0.2|{r}|D2+H3|profit": {"attack_change": 0.0, "reference_change": 0.0, "incomplete": False,
                                                          "heldout": {"seeds": list(range(n)), "gain": [0.3] * n}} for m in M6 for r in RB.RULES}}


def test_load_reads_base_and_doubled_and_flags(tmp_path):
    ev, rs = _write(tmp_path)
    L = RB.load(ev, rs, _report(tmp_path, ev), M6, n_seeds=40)
    assert np.allclose(L["base"]["fresh0"]["D2"]["F000"], 0.1) and np.allclose(L["doubled"]["fresh0"]["D2"]["F000"], 0.2)
    assert np.allclose(L["doubled"]["fresh0"]["D2+H3"]["C*"], 0.3)
    f = L["flags"]["fresh0|F000|D2"]
    assert f == {"attack_change": 0.01, "reference_change": 0.0, "incomplete": False}


def test_doubled_d2h3_seeds_must_match(tmp_path):
    ev, rs = _write(tmp_path); rep = _report(tmp_path, ev)
    rep["doubling"]["fresh4@rho0.2|F111|D2+H3|profit"]["heldout"]["seeds"] = list(range(1, 41))
    with pytest.raises(ValueError, match="seeds"):
        RB.load(ev, rs, rep, M6, n_seeds=40)


# ---- table and command line ----

def test_table_lists_base_and_doubled_rows_with_intervals():
    c = _cells(noise=0.02, seed=7)
    r = {"base": RB.analyse(c, b=99, seed=1), "doubled": RB.analyse(c, b=99, seed=1), "expectations": {}}
    t = RB.table(r)
    assert "\\begin{tabular}" in t and "I(B3)" in t and "G(D2+H3)" in t and "S" in t
    assert t.count("frozen") >= 1 and t.count("doubled") >= 1
    assert "0.300" in t                                   # pooled I(B3) to three decimals


def test_table_prints_not_defined_for_an_undefined_share():
    c = _cells(i_b3=0.04, noise=0.02)
    r = {"base": RB.analyse(c, b=99, seed=1), "doubled": RB.analyse(c, b=99, seed=1), "expectations": {}}
    assert "not defined" in RB.table(r)


def test_main_writes_json_and_table(tmp_path):
    ev, rs = _write(tmp_path); rep = tmp_path / "report.json"; rep.write_text(json.dumps(_report(tmp_path, ev)))
    out, tab = tmp_path / "reset.json", tmp_path / "tables"
    assert RB.main(["--records", str(ev), "--reset", str(rs), "--report", str(rep), "--out", str(out), "--tables", str(tab), "--resamples", "49", "--n-seeds", "40"]) == 0
    d = json.loads(out.read_text())
    assert set(d) >= {"base", "doubled", "doubling_flags", "expectations", "label", "inputs"}
    assert (tab / "posthoc_reset.tex").exists()


# ---- diagnostics summary (plan section 4) ----

def _diag(eff0, eff1, resets_d2=0.0, mr=50.0):
    cell = lambda e, key: {"mean_resets": mr if key == "switch_x0" else resets_d2, "p_any_reset": 1.0 if key == "switch_x0" else 0.0,
                           "mean_ban_rounds": 3.0, key: {"effect": e, "per_seed": [e] * 4, **({"identical": False} if key == "switch_x0" else {})}}
    return {f"{m}@rho0.2|{r}": {"d2h3_base": cell(eff0, "switch_x0"), "d2h3_doubled": cell(eff0 / 2, "switch_x0"), "d2_base": cell(eff1, "switch_x1")}
            for m in M6 for r in RB.RULES}


def test_switch_summary_pools_by_rule_with_equal_market_weights():
    d = _diag(0.2, -0.01); d["fresh0@rho0.2|F000"]["d2h3_base"]["switch_x0"]["effect"] = 0.8
    s = RB.switch_summary(d)
    assert s["F000"]["fixed_policy_x0"]["pooled"] == pytest.approx((0.8 + 5 * 0.2) / 6)
    assert s["F111"]["reverse_x1"]["pooled"] == pytest.approx(-0.01)
    assert s["F111"]["fixed_policy_x0_doubled"]["pooled"] == pytest.approx(0.1)
    assert s["F000"]["d2_mean_resets_max"] == 0.0 and s["F000"]["d2h3_mean_resets"]["pooled"] == pytest.approx(50.0)


def test_switch_summary_refuses_a_d2_winner_with_resets():
    d = _diag(0.2, -0.01); d["fresh2@rho0.2|C*"]["d2_base"]["mean_resets"] = 0.01
    with pytest.raises(ValueError, match="reset"):
        RB.switch_summary(d)


# ---- headline market (plan section 1, exploratory) ----

def test_headline_i_and_gaps(tmp_path):
    ev = tmp_path / "eval"; (ev / "evaluate").mkdir(parents=True)
    gains = {("F000", "D2+H3"): [0.4, 0.3], ("F000", "D2"): [0.1, 0.0], ("F111", "D2+H3"): [0.05, 0.05], ("F111", "D2"): [0.04, 0.02],
             ("C*", "D2+H3"): [0.1, 0.1], ("C*", "D2"): [0.05, 0.03]}
    for (r, f), g in gains.items():
        rid = f"headline@rho0.2|{r}|{f}|profit"
        (ev / "evaluate" / (RB.safe(rid) + ".json")).write_text(json.dumps({"id": rid, "seeds": [1, 2], "gain": g}))
    h = RB.headline(ev, n_seeds=2)
    assert h["I"]["F000"]["estimate"] == pytest.approx(0.3) and h["I"]["F111"]["estimate"] == pytest.approx(0.02)
    assert h["I"]["F000"]["se"] == pytest.approx(0.0)                       # paired differences 0.3, 0.3
    assert h["G"]["D2+H3"]["estimate"] == pytest.approx(0.30) and h["G"]["D2"]["estimate"] == pytest.approx(0.02)


# ---- internal review r1 (Sol 1-2, Astra 1-2) ----

def test_a_wholly_missing_market_is_reported_and_withholds_pooled_results():
    c = _cells(); del c["fresh5"]
    r = RB.analyse(c, b=99, seed=1, markets=M6)
    assert {f"fresh5|{x}|{f}" for x in RB.RULES for f in RB.FAMS} <= set(r["missing"])
    assert r["S"]["pooled"]["value"] is None and r["G"]["D2+H3"]["pooled"]["estimate"] is None
    assert r["expectation_inputs"]["all_markets"]["B3-R3"] is None and r["expectation_inputs"]["S"] is None


def test_load_keeps_a_market_with_no_records(tmp_path):
    ev, rs = _write(tmp_path)
    for p in list((ev / "evaluate").glob("fresh2*")) + list((rs / "evaluate").glob("fresh2*")):
        p.unlink()
    L = RB.load(ev, rs, _report(tmp_path, ev), M6, n_seeds=40)
    assert "fresh2" in L["base"] and L["base"]["fresh2"] == {}


@pytest.mark.parametrize("bad", ["short", "dupe", "nan", "count"])
def test_load_rejects_malformed_records(tmp_path, bad):
    ev, rs = _write(tmp_path); p = rs / "evaluate" / (RB.safe("fresh1@rho0.2|F111|D2|profit") + ".json"); d = json.loads(p.read_text())
    if bad == "short":
        d["gain"] = d["gain"][:-1]
    elif bad == "dupe":
        for root in (ev, rs):                              # same duplicated seed list everywhere, so only uniqueness fails
            for q in (root / "evaluate").glob("fresh1*"):
                e = json.loads(q.read_text()); e["seeds"] = [1] + e["seeds"][1:]; q.write_text(json.dumps(e))
        d = json.loads(p.read_text())
    elif bad == "nan":
        d["gain"][3] = float("nan")
    p.write_text(json.dumps(d))
    with pytest.raises(ValueError):
        RB.load(ev, rs, _report(tmp_path, ev), M6, n_seeds=(41 if bad == "count" else 40))


def test_valid_names_each_defect():
    ok = {"seeds": [1, 2, 3], "gain": [0.1, 0.2, 0.3]}
    assert RB._valid(ok, "x", 3).shape == (3,)
    for src, msg in (({"seeds": [1, 1, 3], "gain": [0.1, 0.2, 0.3]}, "duplicate"), ({"seeds": [1, 2, 3], "gain": [0.1, 0.2]}, "gains for"),
                     ({"seeds": [1, 2, 3], "gain": [0.1, float("inf"), 0.3]}, "non-finite"), (ok, "expected 4")):
        with pytest.raises(ValueError, match=msg):
            RB._valid(src, "x", 4 if msg == "expected 4" else 3)
