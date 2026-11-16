import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import churn_paper as P  # noqa: E402

HERE = Path(__file__).parent
FIRST = json.loads((HERE / "churn.json").read_text())
MID = json.loads((HERE / "churn_mid.json").read_text())


def test_curves_cover_five_rates_and_match_the_records():
    d = P.data(FIRST, MID)
    assert d["rates"] == [0.0, 0.01, 0.02, 0.03, 0.05]
    d05 = [p for p in d["curves"]["base"]["d"] if p["p"] == 0.05][0]
    assert d05["estimate"] == FIRST["statistics"]["base"]["0.05"]["d"]["pooled"]["estimate"]
    q03 = [p for p in d["curves"]["doubled"]["q"] if p["p"] == 0.03][0]
    assert q03["estimate"] == MID["statistics"]["doubled"]["0.03"]["q"]["pooled"]["estimate"]


def test_allocation_rows_come_from_review_r4():
    d = P.data(FIRST, MID)
    assert len(d["allocation"]) == 12
    r = [x for x in d["allocation"] if x["p"] == 0.02 and x["rule"] == "R3"][0]
    a = MID["review_r4"]["audit_allocation"]["0.02"]["F111|base"]
    assert r["focal_audit_rate"] == a["focal_audit_rate"] and r["x_off"] == sum(v == 0 for v in a["x_by_market"].values())
    assert r["eff_attack"] == MID["review_r4"]["eff_attack"]["base"]["0.02"]["F111"]


def test_check_refuses_stale_outputs(tmp_path):
    d = P.data(FIRST, MID)
    assert len(P.check(d, tmp_path, tmp_path)) == 2
    P.write(d, tmp_path, tmp_path)
    assert P.check(d, tmp_path, tmp_path) == []
    (tmp_path / "posthoc_churn_audit.tex").write_text("x")
    assert any("audit" in b for b in P.check(d, tmp_path, tmp_path))


def test_summary_aggregates_flags_reselection_and_rules():
    s = P.summary(FIRST, MID)
    cells = {**FIRST["flags"], **MID["flags"]}
    assert s["flags"]["cells"] == len(cells) == 72
    assert s["flags"]["max_attack_change"] == max(c["attack_change"] for c in cells.values())
    assert s["flags"]["reselected"] == sum(1 for c in cells.values() if c["reference_change"] != 0)
    assert s["flags"]["max_reference_change"] == max(abs(c["reference_change"]) for c in cells.values())
    r = s["rates"]["0.05"]["R3"]
    a = FIRST["review_r4"]["audit_allocation"]["0.05"]["F111|base"]
    assert r["x_off"] == sum(v == 0 for v in a["x_by_market"].values()) and r["focal_audit_rate"] == a["focal_audit_rate"]
    assert r["eff"] == FIRST["review_r4"]["eff_attack"]["base"]["0.05"]["F111"]
    assert set(s["rates"]) == {"0.01", "0.02", "0.03", "0.05"}


def test_check_refuses_a_stale_summary(tmp_path):
    d = P.data(FIRST, MID); s = P.summary(FIRST, MID); out = tmp_path / "churn_paper.json"
    P.write(d, tmp_path, tmp_path, summary_path=out, summary=s)
    assert P.check(d, tmp_path, tmp_path, summary_path=out, summary=s) == []
    out.write_text("{}")
    assert any("churn_paper.json" in b for b in P.check(d, tmp_path, tmp_path, summary_path=out, summary=s))


def test_check_refuses_a_replaced_figure(tmp_path):
    # Astra paper-d10-r1, correction 8: a PDF that no longer matches its data must be refused
    d = P.data(FIRST, MID)
    P.write(d, tmp_path, tmp_path)
    assert P.check(d, tmp_path, tmp_path) == []
    (tmp_path / "fig_churn.pdf").write_bytes(b"%PDF-1.4 not the figure")
    assert any("fig_churn" in b for b in P.check(d, tmp_path, tmp_path))


RUNNERUP = json.loads((HERE.parent / "followup2" / "runnerup_analysis.json").read_text())


def test_summary_round5_fields():
    # Fable round 5: doubled values beside frozen, the R3 per-market values at p = 0.05, Run A's market signs
    s = P.summary(FIRST, MID, RUNNERUP)
    r = s["rates"]["0.01"]["R3"]
    a = FIRST["review_r4"]["audit_allocation"]["0.01"]["F111|doubled"]
    assert r["focal_audit_rate_doubled"] == a["focal_audit_rate"]
    assert r["x_off_doubled"] == sum(v == 0 for v in a["x_by_market"].values())
    assert s["rates"]["0.05"]["R3"]["eff_doubled"] == FIRST["review_r4"]["eff_attack"]["doubled"]["0.05"]["F111"]
    r5 = FIRST["review_r5"]
    fa, x = r5["focal_audit_rate_by_market"]["0.05"]["F111|base"], FIRST["review_r4"]["audit_allocation"]["0.05"]["F111|base"]["x_by_market"]
    rep = [fa[m] for m in fa if x[m] == 1]
    assert s["r3_p05"]["replacing_audit_min"] == min(rep) and s["r3_p05"]["replacing_audit_max"] == max(rep)
    e = r5["eff_by_market"]["base"]["0.05"]["F111"]
    assert s["r3_p05"]["eff_min"] == min(e.values()) and s["r3_p05"]["eff_min_market"] == min(e, key=e.get)
    ru = RUNNERUP["D2+H3"]["base"]["runner_up_minus_r3"]["markets"]
    assert s["runner_up"]["D2+H3|base"]["positive"] == sum(v > 0 for v in ru.values())
    assert s["runner_up"]["D2+H3|base"]["min_market"] == min(ru, key=ru.get) and s["runner_up"]["D2+H3|base"]["min"] == min(ru.values())
    assert s["flags"]["incomplete_n"] == FIRST["flag_summary"]["incomplete_n"] + MID["flag_summary"]["incomplete_n"]


def test_summary_round6_fields():
    # Astra paper-d10-r2: the doubled replacing-winner range at p = 0.05 and Run A's flag count
    s = P.summary(FIRST, MID, RUNNERUP)
    r5 = FIRST["review_r5"]
    fa = r5["focal_audit_rate_by_market"]["0.05"]["F111|doubled"]
    x = FIRST["review_r4"]["audit_allocation"]["0.05"]["F111|doubled"]["x_by_market"]
    rep = [fa[m] for m in fa if x[m] == 1]
    assert s["r3_p05"]["replacing_audit_min_doubled"] == min(rep) and s["r3_p05"]["replacing_markets_doubled"] == len(rep)
    fl = RUNNERUP["D2+H3"]["flags"]
    assert s["runner_up_flags"]["D2+H3"]["incomplete"] == sum(1 for v in fl.values() if v["incomplete"])


def test_main_refuses_a_summary_without_runnerup(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        P.main(["--first", str(HERE / "churn.json"), "--mid", str(HERE / "churn_mid.json"), "--figdir", str(tmp_path),
                "--tabdir", str(tmp_path), "--summary", str(tmp_path / "s.json"), "--write"])


def test_t_table_lists_every_rate_and_version(tmp_path):
    # Astra d10-r2, correction 2: the market-level t intervals at every rate, for both search versions
    t = P.t_table(FIRST, MID)
    ci = MID["review_r4"]["t95"]["doubled"]["0.03"]["d"]["ci"]
    assert P._f(ci[0]) in t and P._f(ci[1]) in t and t.count("\\\\\n") == 4 * 2 + 1
    d = P.data(FIRST, MID); s = P.summary(FIRST, MID, RUNNERUP)
    P.write(d, tmp_path, tmp_path, summary_path=tmp_path / "s.json", summary=s, ttable=t)
    assert P.check(d, tmp_path, tmp_path, summary_path=tmp_path / "s.json", summary=s, ttable=t) == []
    (tmp_path / "posthoc_churn_t.tex").write_text("x")
    assert any("posthoc_churn_t" in b for b in P.check(d, tmp_path, tmp_path, summary_path=tmp_path / "s.json", summary=s, ttable=t))


def test_runner_up_table_and_flags_per_family():
    # Astra d10-r3, correction 2: four rows (family x version) with market t interval and sign counts; flags per family
    t = P.runner_up_table(RUNNERUP)
    assert t.count("\\\\\n") == 4 + 1
    ms = list(RUNNERUP["X7-SC"]["doubled"]["runner_up_minus_r3"]["markets"].values())
    lo, hi = P._t95(ms)
    assert P._f(lo) in t and P._f(hi) in t
    s = P.summary(FIRST, MID, RUNNERUP)
    for fam in ("D2+H3", "X7-SC"):
        fl = RUNNERUP[fam]["flags"]
        assert s["runner_up_flags"][fam]["incomplete"] == sum(1 for v in fl.values() if v["incomplete"])
    assert s["runner_up"]["D2+H3|doubled"]["cstar_minus_runner_up"] == RUNNERUP["D2+H3"]["doubled"]["cstar_minus_runner_up"]["estimate"]
    r = s["r3_p05"]
    fa = FIRST["review_r5"]["focal_audit_rate_by_market"]["0.05"]["F111|base"]; x = FIRST["review_r4"]["audit_allocation"]["0.05"]["F111|base"]["x_by_market"]
    keep = [fa[m] for m in fa if x[m] == 0]
    assert r["staying_audit_min"] == min(keep) and r["staying_audit_max"] == max(keep)


def test_summary_staying_range_doubled():
    # Astra d10-r4, correction 3: the non-replacing range for the doubled winners at p = 0.05
    s = P.summary(FIRST, MID, RUNNERUP)
    fa = FIRST["review_r5"]["focal_audit_rate_by_market"]["0.05"]["F111|doubled"]
    x = FIRST["review_r4"]["audit_allocation"]["0.05"]["F111|doubled"]["x_by_market"]
    keep = [fa[m] for m in fa if x[m] == 0]
    assert s["r3_p05"]["staying_audit_min_doubled"] == min(keep) and s["r3_p05"]["staying_markets_doubled"] == len(keep)


FIRST = json.loads((HERE / "churn.json").read_text()); MID = json.loads((HERE / "churn_mid.json").read_text())


def test_delta_table_pairs_each_market_with_its_own_no_churn_value():
    # External review d10 (Astra Pro): change of each market's contrast from its own no-churn value, per version
    dl = P.deltas(FIRST, MID)
    m0 = FIRST["statistics"]["doubled"]["0"]["q"]["markets"]; m3 = MID["statistics"]["doubled"]["0.03"]["q"]["markets"]
    ch = [m3[k] - m0[k] for k in m0]
    row = dl["doubled"]["0.03"]["q"]
    assert row["mean"] == sum(ch) / 6 and row["negative"] == sum(1 for x in ch if x < 0)
    lo, hi = P._t95(ch)
    assert row["ci"] == [lo, hi]
    t = P.delta_table(dl)
    assert t.count("\\\\\n") == 8 + 1 and P._f(row["mean"]) in t


def test_summary_newest_range_for_replacing_markets():
    s = P.summary(FIRST, MID, RUNNERUP)
    nb = FIRST["review_r5"]["focal_newest_by_market"]["0.05"]["F111|base"]
    x = FIRST["review_r4"]["audit_allocation"]["0.05"]["F111|base"]["x_by_market"]
    rep = [nb[m] for m in nb if x[m] == 1]
    assert s["r3_p05"]["replacing_newest_min"] == min(rep) and s["r3_p05"]["replacing_newest_max"] == max(rep)
    assert s["deltas_all_negative"]["0.05"] == {"base": [6, 6], "doubled": [6, 6]}
