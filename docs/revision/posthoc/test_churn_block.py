"""Tests of the churn block (docs/revision/churn/churn-plan.md, draft 6, sections 5 and 6), written before the code."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import churn_block as CB  # noqa: E402

M6 = tuple(f"fresh{i}" for i in range(6))
RATES = (0.01, 0.05)


def _rec(gain, seeds, pa=None, pr=None, eff=None):
    g = np.asarray(gain, float)
    pa = g + 1.0 if pa is None else np.asarray(pa, float)
    pr = pa - g if pr is None else np.asarray(pr, float)
    return {"seeds": list(seeds), "gain": g.tolist(), "profit_attack": pa.tolist(), "profit_ref": pr.tolist(),
            "eff_attack": (np.full(g.size, 0.9) if eff is None else np.asarray(eff, float)).tolist()}


def _write(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(obj))


def _gains(n=40, noise=0.0, seed=0, base=None, shift=None, rates=RATES):
    """Per-seed gains {cond: {ver: {m: {rule: array}}}}; cond 0 is no churn. Shared noise per market and seed."""
    base = base or {"F111": 0.06, "C*": 0.08, "F000": 0.23}
    shift = shift or {}
    rng = np.random.default_rng(seed); out = {}
    e = {m: (rng.normal(0, noise, n) if noise else np.zeros(n)) for m in M6}
    for c in (0,) + tuple(rates):
        out[c] = {}
        for v in ("base", "doubled"):
            out[c][v] = {m: {r: base[r] + shift.get((c, v, r), 0.0) + e[m] for r in CB.RULES} for m in M6}
    return out


def _tree(tmp: Path, gains: dict, n=40, seeds=None, flags=None, rates=RATES):
    """Writes the registered no-churn records (eval-all/evaluate and report.json doubling) and the churn records."""
    seeds = list(range(1000, 1000 + n)) if seeds is None else seeds
    ea, ch = tmp / "eval-all", tmp / "churn"; report = {"doubling": {}}
    for m in M6:
        for r in CB.RULES:
            rid = f"{m}@rho0.2|{r}|D2+H3|profit"
            _write(ea / "evaluate" / (CB.safe(rid) + ".json"), _rec(gains[0]["base"][m][r], seeds))
            report["doubling"][rid] = {"attack_change": 0.0, "reference_change": 0.0, "incomplete": False, "kind": "x",
                                       "heldout": _rec(gains[0]["doubled"][m][r], seeds)}
            for p in rates:
                cid = f"{rid}|churn{p:g}"; d = ch / f"p{p:g}"
                _write(d / "evaluate" / (CB.safe(cid) + ".json"), _rec(gains[p]["base"][m][r], seeds))
                fl = (flags or {}).get((p, m, r), {"attack_change": 0.0, "reference_change": 0.0, "incomplete": False})
                _write(d / "doubling" / (CB.safe(cid) + ".json"), dict(fl, kind="x", heldout=_rec(gains[p]["doubled"][m][r], seeds)))
    _write(tmp / "report.json", report)
    return ea, ch, tmp / "report.json"


def test_safe_matches_the_driver_names():
    assert CB.safe("fresh0@rho0.2|C*|D2+H3|profit|churn0.05") == "fresh0@rho0.2__Cstar__D2+H3__profit__churn0.05"


def test_point_estimates_contrasts_and_changes(tmp_path):
    g = _gains(shift={(0.05, "base", "F111"): 0.02, (0.05, "doubled", "F111"): 0.03})
    data = CB.load(*_tree(tmp_path, g), markets=M6, n_seeds=40)
    s = CB.statistics(data)
    assert s["base"]["0"]["g"]["F111"]["pooled"] == pytest.approx(0.06)
    assert s["base"]["0.05"]["g"]["F111"]["pooled"] == pytest.approx(0.08)
    assert s["base"]["0.05"]["d"]["pooled"] == pytest.approx(0.0)              # C* - R3 = 0.08 - 0.08
    assert s["base"]["0.05"]["q"]["pooled"] == pytest.approx(0.15)             # B3 - R3 = 0.23 - 0.08
    assert s["base"]["0.05"]["change"]["d"]["pooled"] == pytest.approx(-0.02)
    assert s["doubled"]["0.05"]["change"]["g"]["F111"]["pooled"] == pytest.approx(0.03)
    assert s["base"]["0.01"]["change"]["q"]["pooled"] == pytest.approx(0.0)


def test_pooled_is_the_equal_weight_mean_of_market_means(tmp_path):
    g = _gains(); g[0.05]["base"]["fresh0"]["F111"] = g[0.05]["base"]["fresh0"]["F111"] + 0.6
    s = CB.statistics(CB.load(*_tree(tmp_path, g), markets=M6, n_seeds=40))
    assert s["base"]["0.05"]["g"]["F111"]["markets"]["fresh0"] == pytest.approx(0.66)
    assert s["base"]["0.05"]["g"]["F111"]["pooled"] == pytest.approx((0.66 + 5 * 0.06) / 6)


def test_profit_terms_are_reported_separately(tmp_path):
    s = CB.statistics(CB.load(*_tree(tmp_path, _gains()), markets=M6, n_seeds=40))
    t = s["base"]["0.05"]["profit"]["F111"]
    assert t["attack"]["pooled"] == pytest.approx(1.06) and t["reference"]["pooled"] == pytest.approx(1.0)


def test_bootstrap_is_paired_across_rules_rates_versions_and_no_churn(tmp_path):
    g = _gains(noise=0.05, seed=3, shift={(0.05, "base", "C*"): 0.01})
    r = CB.analyse(CB.load(*_tree(tmp_path, g), markets=M6, n_seeds=40), b=499, seed=2)
    lo, hi = r["base"]["0.05"]["d"]["pooled"]["ci95"]            # shared noise cancels in a paired contrast
    assert hi - lo == pytest.approx(0.0, abs=1e-12)
    lo, hi = r["base"]["0.05"]["change"]["g"]["F111"]["pooled"]["ci95"]   # and in the change from no churn
    assert hi - lo == pytest.approx(0.0, abs=1e-12)
    lo, hi = r["base"]["0.05"]["g"]["F111"]["pooled"]["ci95"]    # a level keeps its seed noise
    assert hi - lo > 0.005


def test_bootstrap_is_reproducible_with_the_fixed_seed(tmp_path):
    data = CB.load(*_tree(tmp_path, _gains(noise=0.05, seed=4)), markets=M6, n_seeds=40)
    a = CB.analyse(data, b=199, seed=7); b = CB.analyse(data, b=199, seed=7)
    assert a["base"]["0.05"]["g"]["C*"]["pooled"]["ci95"] == b["base"]["0.05"]["g"]["C*"]["pooled"]["ci95"]
    assert CB.B == 9999


def test_sign_counts_over_markets(tmp_path):
    g = _gains()
    for m in M6[:4]:
        g[0.01]["base"][m]["F000"] = g[0.01]["base"][m]["F000"] * 0 + 0.0     # B3 - R3 = -0.06 on four markets
    r = CB.analyse(CB.load(*_tree(tmp_path, g), markets=M6, n_seeds=40), b=99, seed=1)
    assert r["base"]["0.01"]["q"]["signs"] == {"positive": 2, "negative": 4, "zero": 0}


def test_load_refuses_seed_lists_that_differ_between_churn_and_no_churn(tmp_path):
    ea, ch, rep = _tree(tmp_path, _gains())
    f = ch / "p0.05" / "evaluate" / (CB.safe("fresh2@rho0.2|C*|D2+H3|profit|churn0.05") + ".json")
    r = json.loads(f.read_text()); r["seeds"] = list(reversed(r["seeds"])); f.write_text(json.dumps(r))
    with pytest.raises(ValueError, match="seeds"):
        CB.load(ea, ch, rep, markets=M6, n_seeds=40)


def test_load_refuses_a_wrong_seed_count_or_a_non_finite_gain(tmp_path):
    ea, ch, rep = _tree(tmp_path, _gains())
    with pytest.raises(ValueError, match="expected 50"):
        CB.load(ea, ch, rep, markets=M6, n_seeds=50)
    f = ch / "p0.01" / "doubling" / (CB.safe("fresh1@rho0.2|F000|D2+H3|profit|churn0.01") + ".json")
    r = json.loads(f.read_text()); r["heldout"]["gain"][3] = float("nan"); f.write_text(json.dumps(r))
    with pytest.raises(ValueError, match="non-finite"):
        CB.load(ea, ch, rep, markets=M6, n_seeds=40)


def test_a_missing_cell_is_reported_and_its_market_drops_from_the_pool(tmp_path):
    ea, ch, rep = _tree(tmp_path, _gains())
    f = ch / "p0.05" / "evaluate" / (CB.safe("fresh3@rho0.2|F111|D2+H3|profit|churn0.05") + ".json")
    f.rename(f.with_suffix(".gone"))
    data = CB.load(ea, ch, rep, markets=M6, n_seeds=40)
    r = CB.analyse(data, b=99, seed=1)
    assert "base|0.05|fresh3|F111" in r["missing"]
    assert r["base"]["0.05"]["g"]["F111"]["pooled"]["estimate"] is None      # pooled only over all six markets
    assert "fresh3" not in r["base"]["0.05"]["g"]["F111"]["markets"]


def test_load_refuses_a_missing_registered_no_churn_record(tmp_path):
    """The registered records all exist; a missing one means a wrong input directory (lesson 2026-11-12: the churn bundle
    holds only the gate cell), so loading refuses instead of reporting it as a missing cell."""
    ea, ch, rep = _tree(tmp_path, _gains())
    f = ea / "evaluate" / (CB.safe("fresh4@rho0.2|C*|D2+H3|profit") + ".json"); f.rename(f.with_suffix(".gone"))
    with pytest.raises(ValueError, match="registered no-churn record missing"):
        CB.load(ea, ch, rep, markets=M6, n_seeds=40)


def test_reselection_flags_per_cell(tmp_path):
    fl = {(0.05, "fresh0", "F111"): {"attack_change": 0.012, "reference_change": -0.003, "incomplete": True}}
    data = CB.load(*_tree(tmp_path, _gains(), flags=fl), markets=M6, n_seeds=40)
    f = data["flags"]["0.05|fresh0|F111"]
    assert f == {"attack_change": 0.012, "reference_change": -0.003, "incomplete": True}
    assert CB.flag_summary(data["flags"])["incomplete"] == ["0.05|fresh0|F111"]
    assert CB.flag_summary(data["flags"])["incomplete_n"] == 1


def _scores(tmp_path, shift, b=99):
    r = CB.analyse(CB.load(*_tree(tmp_path, _gains(shift=shift)), markets=M6, n_seeds=40), b=b, seed=1)
    return CB.expectations(r, diagnostics=None)


def test_expectation_1_met_failed_and_not_established(tmp_path):
    up = {(0.05, v, "F111"): 0.01 for v in ("base", "doubled")}
    assert _scores(tmp_path / "a", up)["1"]["verdict"] == "met"
    down = {(0.05, v, "F111"): -0.01 for v in ("base", "doubled")}
    assert _scores(tmp_path / "b", down)["1"]["verdict"] == "failed"
    mixed = {(0.05, "base", "F111"): 0.01, (0.05, "doubled", "F111"): -0.01}
    assert _scores(tmp_path / "c", mixed)["1"]["verdict"] == "not established"
    assert _scores(tmp_path / "d", {})["1"]["verdict"] == "failed"          # equal is not "exceeds"


def test_expectation_2_compares_d_with_its_own_no_churn_value(tmp_path):
    lower = {(0.05, "base", "C*"): -0.01, (0.05, "doubled", "C*"): -0.005}
    s = _scores(tmp_path / "a", lower)["2"]
    assert s["verdict"] == "met" and s["base"]["churn"] == pytest.approx(0.01) and s["base"]["no_churn"] == pytest.approx(0.02)
    assert _scores(tmp_path / "b", {(0.05, "base", "C*"): -0.01})["2"]["verdict"] == "not established"


def test_expectation_3_needs_all_six_markets(tmp_path):
    assert _scores(tmp_path / "a", {})["3"]["verdict"] == "met"
    g = _gains(); g[0.01]["base"]["fresh5"]["F000"] = g[0.01]["base"]["fresh5"]["F111"] - 0.001
    r = CB.analyse(CB.load(*_tree(tmp_path / "b", g), markets=M6, n_seeds=40), b=99, seed=1)
    s = CB.expectations(r, diagnostics=None)["3"]
    assert s["verdict"] == "not established" and s["base"]["positive"] == 5 and s["doubled"]["positive"] == 6


def _diag(sh):
    """Driver-shaped pooled diagnostics: sh[(rule, winner)] is the first-bin honest-replacement share."""
    pooled = {}
    for (rule, w), v in sh.items():
        bins = [{"share": v, "markets": 6 if v is not None else 0}] + [{"share": 0.1, "markets": 6}] * 3
        pooled[f"{rule}|{w}"] = {"honest_replacement": bins, "honest_initial": bins, "focal": bins}
    return {"cells": {}, "pooled": pooled}


def test_expectation_4_reads_the_first_bin_at_p005(tmp_path):
    r = CB.analyse(CB.load(*_tree(tmp_path, _gains()), markets=M6, n_seeds=40), b=99, seed=1)
    hi = {("F111", w): 0.9 for w in ("base", "doubled")} | {(x, w): 0.3 for x in ("C*", "F000") for w in ("base", "doubled")}
    assert CB.expectations(r, diagnostics=_diag(hi))["4"]["verdict"] == "met"
    one = dict(hi); one[("F000", "doubled")] = 0.95                        # R3 not above B3 for the doubled winner
    assert CB.expectations(r, diagnostics=_diag(one))["4"]["verdict"] == "not established"
    low = {k: (0.1 if k[0] == "F111" else 0.5) for k in hi}
    assert CB.expectations(r, diagnostics=_diag(low))["4"]["verdict"] == "failed"
    na = dict(hi); na[("C*", "base")] = None
    assert CB.expectations(r, diagnostics=_diag(na))["4"]["verdict"] == "unavailable"
    assert CB.expectations(r, diagnostics=None)["4"]["verdict"] == "unavailable"


def _full_diag(n=4, share_r3=0.6, markets=M6, seeds=None):
    """Consistent driver-shaped diagnostics: per-episode [served, audited] counts, bin totals, and the market-pooled shares."""
    cells, pooled = {}, {}
    for r in CB.RULES:
        for w in ("base", "doubled"):
            bins_by_m = {}
            for i, m in enumerate(markets):
                au = {"F111": round(10 * share_r3), "C*": 4, "F000": 2}[r] + (i % 2)
                per = [{c: [[10, au], [5, 1], [0, 0], [3, 0]] for c in ("honest_replacement", "honest_initial", "focal")} for _ in range(n)]
                sh = {}
                for c in ("honest_replacement", "honest_initial", "focal"):
                    rows = []
                    for b in range(4):
                        sv = sum(e[c][b][0] for e in per); a = sum(e[c][b][1] for e in per)
                        rows.append({"age": list(CB.AGE_BINS[b]), "served": sv, "audited": a, "share": (a / sv if sv else None)})
                    sh[c] = rows
                sh.update(per_episode=per, honest_replacements_per_episode=18.0, focal_newest_by_creation=[0.5] * n,
                          focal_newest_by_first_offer_assigned=[0.25] * n)
                cells.setdefault(f"{m}@rho0.2|{r}", {})[w] = {"seeds": list(range(n)) if seeds is None else list(seeds), "shares": sh,
                                                             "knobs": {"x": i % 2}}
                bins_by_m[m] = sh
            pooled[f"{r}|{w}"] = {}
            for c in ("honest_replacement", "honest_initial", "focal"):
                res = []
                for b in range(4):
                    v = [bins_by_m[m][c][b]["share"] for m in markets if bins_by_m[m][c][b]["share"] is not None]
                    res.append({"share": (sum(v) / len(v) if v else None), "markets": len(v)})
                pooled[f"{r}|{w}"][c] = res
    return {"cells": cells, "pooled": pooled}


def test_validate_diagnostics_accepts_a_consistent_summary():
    CB.validate_diagnostics(_full_diag(), M6, n_seeds=4)


def test_validate_diagnostics_rejects_a_conflicting_pooled_share():
    d = _full_diag(); d["pooled"]["F111|base"]["honest_replacement"][0]["share"] += 0.01
    with pytest.raises(ValueError, match="pooled"):
        CB.validate_diagnostics(d, M6, n_seeds=4)


def test_validate_diagnostics_rejects_bin_totals_that_differ_from_the_episode_counts():
    d = _full_diag(); d["cells"]["fresh2@rho0.2|C*"]["doubled"]["shares"]["honest_replacement"][0]["audited"] += 1
    with pytest.raises(ValueError, match="per-episode"):
        CB.validate_diagnostics(d, M6, n_seeds=4)


def test_validate_diagnostics_rejects_a_missing_cell_or_episode():
    d = _full_diag(); del d["cells"]["fresh5@rho0.2|F000"]
    with pytest.raises(ValueError, match="missing"):
        CB.validate_diagnostics(d, M6, n_seeds=4)
    with pytest.raises(ValueError, match="seed|episodes"):
        CB.validate_diagnostics(_full_diag(), M6, n_seeds=5)


def test_validate_diagnostics_rejects_swapped_relabelled_or_missing_bins():
    """Sol and Astra r2: the four age bins in order; a consistent swap of the first two bins or an empty bin list fails."""
    d = _full_diag(); sh = d["cells"]["fresh1@rho0.2|F111"]["base"]["shares"]
    sh["honest_replacement"][0]["age"], sh["honest_replacement"][1]["age"] = [10, 20], [0, 10]
    with pytest.raises(ValueError, match="age bins"):
        CB.validate_diagnostics(d, M6, n_seeds=4)
    d = _full_diag(); d["cells"]["fresh1@rho0.2|F111"]["base"]["shares"]["focal"] = []
    with pytest.raises(ValueError, match="age bins"):
        CB.validate_diagnostics(d, M6, n_seeds=4)
    d = _full_diag(); d["pooled"]["C*|doubled"]["honest_initial"] = d["pooled"]["C*|doubled"]["honest_initial"][:3]
    with pytest.raises(ValueError, match="age bins"):
        CB.validate_diagnostics(d, M6, n_seeds=4)


def test_validate_diagnostics_rejects_non_finite_shares_at_both_levels():
    d = _full_diag(); d["cells"]["fresh3@rho0.2|F000"]["base"]["shares"]["honest_replacement"][0]["share"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        CB.validate_diagnostics(d, M6, n_seeds=4)
    d = _full_diag(); d["pooled"]["F111|base"]["honest_replacement"][0]["share"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        CB.validate_diagnostics(d, M6, n_seeds=4)


def test_validate_diagnostics_checks_the_seed_identifiers():
    d = _full_diag(); d["cells"]["fresh0@rho0.2|C*"]["base"]["seeds"] = [7, 7, 7, 7]
    with pytest.raises(ValueError, match="seed"):
        CB.validate_diagnostics(d, M6, n_seeds=4)
    seeds = {m: list(range(4)) for m in M6}; CB.validate_diagnostics(_full_diag(), M6, n_seeds=4, seeds=seeds)
    seeds["fresh4"] = [0, 1, 3, 2]
    with pytest.raises(ValueError, match="seed"):
        CB.validate_diagnostics(_full_diag(), M6, n_seeds=4, seeds=seeds)


def test_newest_share_averages_episode_shares_within_a_market_then_across_markets():
    """Sol r1: not one pooled fraction of rounds. Market fresh0 has episode shares 1, 0, 0 (one third), the others 1."""
    d = _full_diag(n=3)
    for m in M6:
        d["cells"][f"{m}@rho0.2|F111"]["base"]["shares"]["focal_newest_by_first_offer_assigned"] = [1.0, 1.0, 1.0]
    d["cells"]["fresh0@rho0.2|F111"]["base"]["shares"]["focal_newest_by_first_offer_assigned"] = [1.0, 0.0, None]
    s = CB.diag_summary(d)["F111|base"]
    assert s["focal_newest_first_offer"] == pytest.approx((0.5 + 5 * 1.0) / 6)       # None episodes are left out


def test_registered_values_are_reproduced_from_the_no_churn_records(tmp_path):
    """posthoc.json doubled.D2+H3: q1 = C* - R3, q4 = B3 - R3 (frozen = base, doubled); absolute mean gains of C* and R3."""
    r = CB.analyse(CB.load(*_tree(tmp_path, _gains()), markets=M6, n_seeds=40), b=99, seed=1)
    reg = {"pooled": {"q1_frozen": 0.02, "q1_doubled": 0.02, "q4_frozen": 0.17, "q4_doubled": 0.17},
           "absolute": {"C*": {"mean_gain": 0.08}, "F111": {"mean_gain": 0.06}}}
    chk = CB.registered_check(r, reg)
    assert chk["ok"] is True and chk["absolute_matches"] == ["base", "doubled"]
    bad = json.loads(json.dumps(reg)); bad["pooled"]["q4_doubled"] = 0.18
    assert CB.registered_check(r, bad)["ok"] is False


def test_cli_writes_the_result_with_input_hashes_and_a_table(tmp_path):
    ea, ch, rep = _tree(tmp_path, _gains(noise=0.01))
    for c in ("0.01", "0.05"):
        _write(ch / f"p{c}" / "diagnostics.json", _full_diag(n=40, seeds=range(1000, 1040)))
    out, tab = tmp_path / "churn.json", tmp_path / "tables"
    rc = CB.main(["--records", str(ea), "--churn", str(ch), "--report", str(rep), "--out", str(out), "--tables", str(tab),
                  "--n-seeds", "40", "--resamples", "99"])
    assert rc == 0
    res = json.loads(out.read_text())
    assert res["label"].startswith("exploratory follow-up") and len(res["inputs"]["report_sha256"]) == 64
    assert set(res["expectations"]) == {"1", "2", "3", "4"}
    t = (tab / "posthoc_churn.tex").read_text()
    assert t.count("\\\\") >= 6 and "C$^*$" in t and "C*" not in t.replace("C$^*$", "")


# Amendment 1 (rates 0.02 and 0.03) and the round-4 review block (post hoc, labelled), written before the code.
MID = (0.02, 0.03)


def test_rates_option_reads_the_amendment_rates(tmp_path):
    g = _gains(rates=MID, shift={(0.03, "base", "F111"): 0.05})
    data = CB.load(*_tree(tmp_path, g, rates=MID), markets=M6, n_seeds=40, rates=MID)
    s = CB.statistics(data)
    assert set(s["base"]) == {"0", "0.02", "0.03"}
    assert s["base"]["0.03"]["change"]["g"]["F111"]["pooled"] == pytest.approx(0.05)
    r = CB.analyse(data, b=99, seed=1)
    assert "0.05" not in r["base"] and r["base"]["0.02"]["d"]["pooled"]["ci95"] is not None


def test_review_r4_market_t_interval_of_the_contrasts(tmp_path):
    g = _gains()
    for i, m in enumerate(M6):
        g[0.05]["base"][m]["C*"] = g[0.05]["base"][m]["C*"] + 0.01 * i          # d_0.05(m) = 0.02 + 0.01 i
    r = CB.analyse(CB.load(*_tree(tmp_path, g), markets=M6, n_seeds=40), b=99, seed=1)
    t = CB.review_r4(r, data=None, diags={})["t95"]["base"]["0.05"]["d"]
    xs = np.array([0.02 + 0.01 * i for i in range(6)])
    half = 2.5705818366147395 * xs.std(ddof=1) / np.sqrt(6)
    assert t["mean"] == pytest.approx(xs.mean()) and t["ci"] == pytest.approx([xs.mean() - half, xs.mean() + half])


def test_review_r4_efficiency_under_attack(tmp_path):
    ea, ch, rep_ = _tree(tmp_path, _gains())
    data = CB.load(ea, ch, rep_, markets=M6, n_seeds=40)
    r = CB.analyse(data, b=99, seed=1)
    e = CB.review_r4(r, data=data, diags={})["eff_attack"]
    assert e["base"]["0.05"]["F111"] == pytest.approx(0.9) and e["doubled"]["0"]["C*"] == pytest.approx(0.9)


def test_review_r4_audit_allocation_from_the_episode_counts():
    d = _full_diag(n=4)
    a = CB.audit_allocation(d)["F111|base"]
    aus = [6 + (i % 2) for i in range(6)]
    assert a["young_honest_job_share"] == pytest.approx(20 / 54)
    assert a["young_honest_audit_share"] == pytest.approx(np.mean([2 * x / (3 * (x + 1)) for x in aus]))
    assert a["established_honest_audit_rate"] == pytest.approx(1 / 8)
    assert a["focal_job_share"] == pytest.approx(1 / 3)
    assert a["focal_audit_rate"] == pytest.approx(np.mean([(x + 1) / 18 for x in aus]))
    assert a["x_by_market"] == {m: i % 2 for i, m in enumerate(M6)}


def _first(r_first, s01=0.88, s05=0.57):
    """A churn.json-shaped first arm: statistics and the R3 first-bin shares at 0.01 and 0.05."""
    pb = lambda v: {"honest_replacement": [{"share": v, "markets": 6}] * 4}
    return {"statistics": r_first, "diagnostics": {c: {f"F111|{w}": {"pooled_bins": pb(v)} for w in ("base", "doubled")}
                                                   for c, v in (("0.01", s01), ("0.05", s05))}}


def _mid_diag(s02, s03):
    return {"0.02": {"pooled": {f"F111|{w}": {"honest_replacement": [{"share": s02, "markets": 6}] * 4} for w in ("base", "doubled")}},
            "0.03": {"pooled": {f"F111|{w}": {"honest_replacement": [{"share": s03, "markets": 6}] * 4} for w in ("base", "doubled")}}}


def test_expectations_5_to_8(tmp_path):
    r1 = CB.analyse(CB.load(*_tree(tmp_path / "a", _gains(shift={(0.05, v, "F111"): 0.2 for v in ("base", "doubled")})),
                            markets=M6, n_seeds=40), b=99, seed=1)                         # g_0.05(R3) = 0.26
    g = _gains(rates=MID, shift={(0.03, v, "F111"): 0.01 for v in ("base", "doubled")})   # d_0.03 < d_0.02
    rm = CB.analyse(CB.load(*_tree(tmp_path / "b", g, rates=MID), markets=M6, n_seeds=40, rates=MID), b=99, seed=1)
    e = CB.expectations_mid(rm, _mid_diag(0.8, 0.7), _first(r1))
    assert [e[k]["verdict"] for k in ("5", "6", "7", "8")] == ["met", "met", "met", "met"]
    assert CB.expectations_mid(rm, _mid_diag(0.7, 0.8), _first(r1))["5"]["verdict"] == "failed"     # not lower at 0.03
    assert CB.expectations_mid(rm, _mid_diag(0.9, 0.7), _first(r1))["5"]["verdict"] == "failed"     # above the 0.01 value
    g2 = _gains(rates=MID, shift={(0.02, "base", "F111"): 0.2})                                     # frozen g_0.02 = 0.26 > midpoint 0.16
    rm2 = CB.analyse(CB.load(*_tree(tmp_path / "c", g2, rates=MID), markets=M6, n_seeds=40, rates=MID), b=99, seed=1)
    e2 = CB.expectations_mid(rm2, _mid_diag(0.8, 0.7), _first(r1))
    assert e2["7"]["verdict"] == "not established" and e2["7"]["base"]["midpoint"] == pytest.approx(0.16)
    assert e2["6"]["verdict"] == "failed"                                # d_0.03 above (frozen) or equal to (doubled) d_0.02
    assert e2["8"]["base"]["positive"] == 0 and e2["8"]["verdict"] == "not established"


def test_cli_with_amendment_rates_scores_5_to_8(tmp_path):
    r1dir = tmp_path / "first"; ea, ch, rep_ = _tree(r1dir, _gains(noise=0.01))
    for c in ("0.01", "0.05"):
        _write(ch / f"p{c}" / "diagnostics.json", _full_diag(n=40, seeds=range(1000, 1040)))
    first = tmp_path / "churn.json"
    assert CB.main(["--records", str(ea), "--churn", str(ch), "--report", str(rep_), "--out", str(first), "--tables", str(tmp_path / "t1"),
                    "--n-seeds", "40", "--resamples", "99"]) == 0
    g = _gains(rates=MID, noise=0.01); ea2, ch2, rep2 = _tree(tmp_path / "mid", g, rates=MID)
    for c in ("0.02", "0.03"):
        _write(ch2 / f"p{c}" / "diagnostics.json", _full_diag(n=40, seeds=range(1000, 1040)))
    out = tmp_path / "churn_mid.json"
    assert CB.main(["--records", str(ea2), "--churn", str(ch2), "--report", str(rep2), "--out", str(out), "--tables", str(tmp_path / "t2"),
                    "--n-seeds", "40", "--resamples", "99", "--rates", "0.02,0.03", "--first", str(first)]) == 0
    res = json.loads(out.read_text())
    assert set(res["expectations"]) == {"5", "6", "7", "8"} and "review_r4" in res and res["review_r4"]["label"].startswith("post hoc")
    assert set(res["statistics"]["base"]) == {"0", "0.02", "0.03"}
    assert (tmp_path / "t2" / "posthoc_churn_mid.tex").exists()
    with pytest.raises(SystemExit):
        CB.main(["--records", str(ea2), "--churn", str(ch2), "--report", str(rep2), "--out", str(out), "--tables", str(tmp_path / "t3"),
                 "--rates", "0.02,0.04"])


# Review churn-mid-r1 caveats (Sol and Astra): --first required for the amendment rates, rate order irrelevant, and the
# combined five-condition table promised in amendment section 3.
def _first_and_mid(tmp_path):
    r1dir = tmp_path / "first"; ea, ch, rep_ = _tree(r1dir, _gains(noise=0.01))
    for c in ("0.01", "0.05"):
        _write(ch / f"p{c}" / "diagnostics.json", _full_diag(n=40, seeds=range(1000, 1040)))
    first = tmp_path / "churn.json"
    assert CB.main(["--records", str(ea), "--churn", str(ch), "--report", str(rep_), "--out", str(first), "--tables", str(tmp_path / "t1"),
                    "--n-seeds", "40", "--resamples", "99"]) == 0
    ea2, ch2, rep2 = _tree(tmp_path / "mid", _gains(rates=MID, noise=0.01), rates=MID)
    for c in ("0.02", "0.03"):
        _write(ch2 / f"p{c}" / "diagnostics.json", _full_diag(n=40, seeds=range(1000, 1040)))
    return first, ["--records", str(ea2), "--churn", str(ch2), "--report", str(rep2), "--n-seeds", "40", "--resamples", "99"], (ea, ch, rep_)


def test_amendment_rates_require_first(tmp_path):
    first, mid, _ = _first_and_mid(tmp_path)
    with pytest.raises(SystemExit):
        CB.main(mid + ["--out", str(tmp_path / "x.json"), "--tables", str(tmp_path / "tx"), "--rates", "0.02,0.03"])
    assert not (tmp_path / "x.json").exists()


def test_rate_order_does_not_change_the_expectations(tmp_path):
    first, mid, (ea, ch, rep_) = _first_and_mid(tmp_path)
    out = tmp_path / "rev.json"
    assert CB.main(["--records", str(ea), "--churn", str(ch), "--report", str(rep_), "--out", str(out), "--tables", str(tmp_path / "tr"),
                    "--n-seeds", "40", "--resamples", "99", "--rates", "0.05,0.01"]) == 0
    assert set(json.loads(out.read_text())["expectations"]) == {"1", "2", "3", "4"}
    assert (tmp_path / "tr" / "posthoc_churn.tex").exists()
    out2 = tmp_path / "mid_rev.json"
    assert CB.main(mid + ["--out", str(out2), "--tables", str(tmp_path / "tm"), "--rates", "0.03,0.02", "--first", str(first)]) == 0
    assert set(json.loads(out2.read_text())["expectations"]) == {"5", "6", "7", "8"}


def test_other_rate_sets_are_refused(tmp_path):
    first, mid, _ = _first_and_mid(tmp_path)
    for r in ("0.02", "0.01,0.02", "0.01,0.02,0.03,0.05"):
        with pytest.raises(SystemExit):
            CB.main(mid + ["--out", str(tmp_path / "y.json"), "--tables", str(tmp_path / "ty"), "--rates", r, "--first", str(first)])


def test_combined_table_lists_all_five_conditions_for_both_versions(tmp_path):
    first, mid, _ = _first_and_mid(tmp_path)
    out = tmp_path / "churn_mid.json"
    assert CB.main(mid + ["--out", str(out), "--tables", str(tmp_path / "tc"), "--rates", "0.02,0.03", "--first", str(first)]) == 0
    t = (tmp_path / "tc" / "posthoc_churn_all.tex").read_text()
    rows = [l for l in t.splitlines() if l.startswith(("frozen", "doubled"))]
    assert len(rows) == 10
    for v in ("frozen", "doubled"):
        assert [l.split(" & ")[1] for l in rows if l.startswith(v)] == ["0 (registered)", "0.01", "0.02", "0.03", "0.05"]
    assert json.loads(out.read_text())["combined_no_churn_check"] == "ok"


def test_combined_table_refuses_a_first_arm_whose_no_churn_values_differ(tmp_path):
    first, mid, _ = _first_and_mid(tmp_path)
    f = json.loads(first.read_text())
    f["statistics"]["base"]["0"]["g"]["F111"]["pooled"]["estimate"] += 0.01
    bad = tmp_path / "bad_first.json"; bad.write_text(json.dumps(f))
    with pytest.raises(ValueError, match="no-churn"):
        CB.main(mid + ["--out", str(tmp_path / "z.json"), "--tables", str(tmp_path / "tz"), "--rates", "0.02,0.03", "--first", str(bad)])
    assert not (tmp_path / "z.json").exists()


def test_review_r5_per_market_values(tmp_path):
    # Fable round 5, problems 5 and 8: per-market efficiency under attack and the attacker's audited rate per market
    ea, ch, rep_ = _tree(tmp_path, _gains())
    data = CB.load(ea, ch, rep_, markets=M6, n_seeds=40)
    r5 = CB.review_r5(data=data, diags={"0.05": _full_diag(n=4)})
    e = r5["eff_by_market"]["base"]["0.05"]["F111"]
    assert set(e) == set(M6) and all(v == pytest.approx(0.9) for v in e.values())
    fa = r5["focal_audit_rate_by_market"]["0.05"]["F111|base"]
    aus = [6 + (i % 2) for i in range(6)]
    assert [fa[m] for m in M6] == pytest.approx([(x + 1) / 18 for x in aus])
    assert np.mean(list(fa.values())) == pytest.approx(CB.audit_allocation(_full_diag(n=4))["F111|base"]["focal_audit_rate"])


def test_review_r5_newest_by_market():
    # External review d10 (Astra Pro), problem 7: the focal provider's newest-identity frequency per market
    r5 = CB.review_r5(data=None, diags={"0.05": _full_diag(n=4)})
    nb = r5["focal_newest_by_market"]["0.05"]["F111|base"]
    assert set(nb) == set(M6) and all(v == pytest.approx(0.25) for v in nb.values())
