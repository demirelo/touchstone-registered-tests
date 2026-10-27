"""The report (operations plan Task 9). Records are written in the evaluate stage's own shape (`revision_v2.stage_evaluate`'s
fields, through `revision_v2.write` at `eval_path`); the verify stage, which has its own guarded tests, is stubbed to report
what is missing. Oracles are computed here from the per-seed arrays."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from sim import intervals as I

FRESH = [f"fresh{i}" for i in range(6)]
FACT = [f"F{p}{g}{s}" for p in "01" for g in "01" for s in "01"]
Q1R = ("F111", "C*")
MATCHED = tuple(FACT) + ("C*", "C*/S0")
CORE = ("F000", "F111", "C*")
WHOLE = ("B3-t", "R3-t", "C*-t")
N_SEEDS = 24


def _job(ctx, rule, family, objective="profit", c=None, schedule=None):
    from scripts.revision_v2 import cell_id
    return {"id": cell_id(ctx, rule, family, objective, c, schedule), "context": ctx, "rule": rule, "family": family, "objective": objective,
            "c": c, "schedule": schedule, "mkt": {"cfg": SimpleNamespace(N=10), "seeds_eval": list(range(N_SEEDS)), "label": ctx.split("@")[0]}}


def _profit(rng, mean_gain, eff=0.95):
    g = rng.normal(mean_gain, 0.05, N_SEEDS); sstar = np.full(N_SEEDS, 50.0); pref = rng.normal(5.0, 0.2, N_SEEDS)
    return {"seeds": list(range(N_SEEDS)), "gain": g.tolist(), "eff_attack": rng.normal(eff, 0.005, N_SEEDS).tolist(), "eff_ref": [0.97] * N_SEEDS,
            "net_eff_attack": [0.94] * N_SEEDS, "net_eff_ref": [0.96] * N_SEEDS, "profit_attack": (pref + g * 5).tolist(), "profit_ref": pref.tolist(),
            "audit_spend_attack": [0.1] * N_SEEDS, "sstar": sstar.tolist(), "served_share_attack": [0.9] * N_SEEDS, "served_share_ref": [0.95] * N_SEEDS,
            "false_refund_focal_attack": [0.01] * N_SEEDS, "false_refund_others_attack": [0.02] * N_SEEDS,
            "false_refund_focal_ref": [0.01] * N_SEEDS, "false_refund_others_ref": [0.02] * N_SEEDS}


def _cross(rng, out, ctx, fam, envelope=None):
    from scripts.revision_v2 import _safe, write
    pa = {f"{a}>{r}": rng.normal(1.0 + 0.01 * FACT.index(r), 0.05, N_SEEDS) for a in FACT for r in FACT}
    pr = {k: rng.normal(0.9, 0.05, N_SEEDS) for k in pa}
    rows = {k: (pa[k] - pr[k]).tolist() for k in pa}
    prof = {k: {"profit_attack": pa[k].tolist(), "profit_ref": pr[k].tolist(), "eff_attack": [0.95] * N_SEEDS, "net_eff_attack": [0.9] * N_SEEDS} for k in pa}
    write(out / "cross" / ctx / (_safe(fam) + ".json"), {"stage": "cross", "context": ctx, "family": fam, "attacks": FACT, "rules": FACT,
                                                         "matrix": [[float(np.mean(rows[f"{a}>{r}"])) for r in FACT] for a in FACT], "per_seed": rows,
                                                         "profit_rows": prof, "envelope": envelope or {r: "F000" for r in FACT}})


def _world(tmp_path, seed=0, missing=(), gain=None, eff=None, w1=0.01, welfare_choice="X7-SC", envelope=None):
    """Every cell the draft-7 questions read, on the six fresh markets and the headline market; returns (out, catalog)."""
    from scripts.revision_v2 import eval_path, path_of, write
    rng = np.random.default_rng(seed); out = tmp_path / "eval"; cat = []
    gain = gain or (lambda m, r: {"F000": 0.30, "F111": 0.02, "C*": 0.05, "C*/S0": 0.06}.get(r, 0.1 + 0.01 * FACT.index(r) if r in FACT else 0.1))
    eff = eff or (lambda m, r: 0.95)
    for m in FRESH + ["headline"]:
        ctx = f"{m}@rho0.2"
        for r in MATCHED:
            for fam in ("D2+H3", "X7-SC"):
                j = _job(ctx, r, fam); cat.append(j)
                if j["id"] not in missing:
                    write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], **_profit(rng, gain(m, r), eff(m, r))})
        for r in CORE:
            for fam in ("D2", "X5-AG/v2", "H4"):
                j = _job(ctx, r, fam); cat.append(j)
                if j["id"] not in missing:
                    write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], **_profit(rng, gain(m, r) + 0.01)})
            write(path_of(out, f"envelope/{ctx}/{r}"), {"stage": "envelope", "choice": "X7-SC", "training_gains": {"D2+H3": 0.1, "X7-SC": 0.2}})
        for fam in ("D2+H3", "X7-SC"):
            _cross(rng, out, ctx, fam, envelope)
    ctx = "headline@rho0.2"
    for r in CORE:
        for obj in ("W0", "W1"):
            write(path_of(out, f"welfare_select/{ctx}/{r}/{obj}"), {"stage": "welfare_select", "family": welfare_choice, "status": "selected", "train_eff": 0.7}
                  if not (r == "C*" and obj == "W1") else {"stage": "welfare_select", "family": None, "status": "no feasible candidate found", "train_eff": None})
            for fam in ("D2+H3", "X7-SC"):
                j = _job(ctx, r, fam, obj); cat.append(j)
                if j["id"] in missing:
                    continue
                if obj == "W1" and r == "C*":
                    write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], "seeds": list(range(N_SEEDS)), "no_feasible_candidate": True})
                    continue
                rec = {"seeds": list(range(N_SEEDS)), "eff": rng.normal(0.80 if fam == "D2+H3" else 0.85, 0.01, N_SEEDS).tolist(),
                       "normalized": rng.normal(0.5, 0.02, N_SEEDS).tolist()}
                if obj == "W1":
                    rec["constraint"] = rng.normal(w1, 0.005, N_SEEDS).tolist()
                write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], **rec})
        groups = [(c, sch, "X6-SE/v2") for c in (2, 5) for sch in ("synchronised", "staggered")] + [(2, "roles", "X8-DB")]
        for c, sch, fam in groups:
            for obj in ("total", "min"):
                j = _job(ctx, r, fam, obj, c, sch); cat.append(j)
                mg = rng.normal(0.05, 0.02, (c, N_SEEDS))
                write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], "seeds": list(range(N_SEEDS)), "member_gain": mg.tolist(),
                                                "total": float(mg.mean(axis=1).sum()), "min": float(mg.mean(axis=1).min())})
        j = _job(ctx, r, "HR1", "diagnostic"); cat.append(j)
        write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], "seeds": list(range(N_SEEDS)), "replace_at": 50, "bin_width": 10,
                                        "bins": [{"age": [k * 10, k * 10 + 10], "audited_share": 0.9 if r == "F111" else 0.3, "profit_per_round": 0.1,
                                                  "false_refund": 0.0} for k in range(15)]})
    for r in WHOLE:
        for m in FRESH + ["headline"]:
            for fam in (("D2+H3", "X7-SC") if m == "headline" else ("D2+H3",)):
                j = _job(f"{m}@rho0.2", r, fam); cat.append(j); write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], **_profit(rng, 0.05)})
    for r in ("F000", "F111", "R4", "C*", "C*/S2"):
        j = _job("headline@rho1", r, "D2+H3"); cat.append(j); write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], **_profit(rng, 0.2)})
    from scripts.revision_v2 import _safe
    dj = cat[0]; write(out / "doubling" / (_safe(dj["id"]) + ".json"), {"stage": "doubling", "kind": "profit", "attack_change": 0.001, "reference_change": 0.0, "incomplete": False})
    return out, cat


def _run(monkeypatch, out, cat, kappa=(0.5, 0.5), confirmatory=True, h4_loaded=True, verify=None):
    import scripts.report_v2 as R
    rep = verify or {"ok": True, "h4": None, "contexts": {}}
    monkeypatch.setattr(R, "verify_records", lambda *a, **k: rep)
    proto = {"kappa": {"Q1": kappa[0], "Q4": kappa[1]}, "cuts": 0, "h4": {"commit": "a" * 40, "bundle_sha256": "b" * 64} if h4_loaded else None}
    inst = {"confirmatory": confirmatory, "seeds": {}}
    return R.build(out, proto, inst, {"loaded": h4_loaded}, cat)


def _gain(out, ctx, rule, fam):
    from scripts.revision_v2 import cell_id, eval_path
    return np.asarray(json.loads(eval_path(out, cell_id(ctx, rule, fam, "profit")).read_text())["gain"])


def test_q1_strata_tails_and_kappa(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat, kappa=(0.5, 0.5))
    st = [_gain(out, f"{m}@rho0.2", "C*", "D2+H3") - _gain(out, f"{m}@rho0.2", "F111", "D2+H3") for m in FRESH]
    t = r["q1"]["tests"]["C*-F111|D2+H3"]; tail = 0.5 * 0.05 / 4
    assert t["estimate"] == pytest.approx(I.stratified_mean(st))
    assert t["interval"] == pytest.approx([I.stratified_at(st, "lower", tail), I.stratified_at(st, "upper", tail)])
    assert t["interval"][0] != pytest.approx(I.stratified_at(st, "lower", 0.05 / 4))          # kappa is used
    assert set(r["q1"]["tests"]) == {f"C*-F111|{f}" for f in ("D2+H3", "X7-SC")}
    d = r["q1"]["descriptive"]["fresh0"]["C*-F111|D2+H3"]
    assert d["interval"] == pytest.approx([I.studentized_at(st[0], "lower", 0.025), I.studentized_at(st[0], "upper", 0.025)]) and "headline" in r["q1"]["descriptive"]


def test_q2_per_seed_contrasts_against_an_oracle(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat)
    per_market = []
    for m in FRESH:
        g = {f: _gain(out, f"{m}@rho0.2", f, "X7-SC") for f in FACT}
        p1 = np.mean([g[f] for f in FACT if f[1] == "1"], axis=0); p0 = np.mean([g[f] for f in FACT if f[1] == "0"], axis=0)
        per_market.append(p1 - p0)
    q = r["q2"]["searched"]["X7-SC"]["P"]
    assert q["estimate"] == pytest.approx(float(np.mean([x.mean() for x in per_market])))
    assert q["interval"] == pytest.approx([I.stratified_at(per_market, "lower", 0.025), I.stratified_at(per_market, "upper", 0.025)])
    assert set(r["q2"]["fixed"]["D2+H3"]) >= {"P", "G", "S", "PG", "PS", "GS", "PGS", "G|P=0", "G|P=1", "P|S=0", "P|S=1"}
    assert set(r["q2"]["envelope"]["D2+H3"]["fresh0"]) == set(FACT)


def test_q3_welfare_gain_and_no_feasible_case(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id, eval_path
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat)
    w0 = json.loads(eval_path(out, cell_id("headline@rho0.2", "F111", "D2+H3", "W0")).read_text())
    pr = json.loads(eval_path(out, cell_id("headline@rho0.2", "F111", "D2+H3", "profit")).read_text())
    gain = np.asarray(w0["normalized"]) - np.asarray(pr["profit_ref"]) / (np.asarray(pr["sstar"]) / 10)
    cell = r["q3"]["welfare"]["F111"]["D2+H3"]["W0"]
    assert cell["attacker_gain"] == pytest.approx(float(gain.mean())) and cell["efficiency"] == pytest.approx(float(np.mean(w0["eff"])))
    assert r["q3"]["welfare"]["C*"]["D2+H3"]["W1"] == "no feasible candidate found"
    assert "constraint_interval" in r["q3"]["welfare"]["F111"]["X7-SC"]["W1"]
    co = r["q3"]["coalition"]["F111"]["c2_synchronised"]
    mg = np.asarray(json.loads(eval_path(out, cell_id("headline@rho0.2", "F111", "X6-SE/v2", "min", 2, "synchronised")).read_text())["member_gain"])
    assert co["G_min"]["bounds"] == pytest.approx(list(I.gmin_bounds(list(mg), 0.05))) and r["q3"]["envelope"]["F111"]["fresh0"]["family"] == "X7-SC"


def test_q4_wording_bounds_and_named_failures(tmp_path, monkeypatch):
    out, cat = _world(tmp_path, gain=lambda m, r: {"F000": 0.30 if m != "fresh3" else 0.03, "F111": 0.02}.get(r, 0.1))
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0)); q = r["q4"]
    assert q["k"] == 5 and q["failing"] == ["fresh3"] and q["wording"] == "replicated on 5 of 6 sampled markets"
    d = _gain(out, "fresh0@rho0.2", "F000", "D2+H3") - _gain(out, "fresh0@rho0.2", "F111", "D2+H3")
    assert q["markets"]["fresh0"]["gain_diff_lower"] == pytest.approx(I.studentized_at(d, "lower", 0.05 / 6))
    assert "generalisation not established" not in q["wording"]


def test_q4_keeps_six_holm_slots():
    from scripts.report_v2 import q4_decide
    from sim.decisions_v2 import q4_markets
    six = q4_decide([0.009, 0.5, 0.5, 0.5, 0.5, None], [0.001] * 6, 1.0)
    assert six["k"] == 0 and six["undecided"] == [5]
    assert q4_markets([0.009, 0.5, 0.5, 0.5, 0.5], [0.001] * 5, 1.0)["k"] == 1        # five slots would reject


def test_no_kappa_no_decision_but_estimates(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat, kappa=(None, None))
    t = r["q1"]["tests"]["C*-F111|X7-SC"]
    assert t["category"] == "no confirmatory decision" and t["estimate"] is not None and t["interval_label"] == "nominal 95 percent, unadjusted"
    assert r["q4"]["decided"] is False and r["q4"]["wording"] == "no confirmatory decision" and r["q4"]["markets"]["fresh0"]["gain_diff_lower"] is not None


def test_missing_cells_make_dependent_questions_unanswered(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id
    gone = cell_id("fresh2@rho0.2", "F111", "D2+H3", "profit")
    out, cat = _world(tmp_path, missing=(gone,))
    r = _run(monkeypatch, out, cat, verify={"ok": True, "h4": None, "contexts": {"fresh2@rho0.2": {"status": "ok", "missing": [gone]}}})
    assert r["q1"]["tests"]["C*-F111|D2+H3"]["category"] == "not decided: missing cell" and r["q1"]["tests"]["C*-F111|X7-SC"]["p"] is not None
    assert r["q2"]["searched"]["D2+H3"] == "unanswered: missing cell" and r["q3"]["envelope"]["F111"]["fresh2"] == "unanswered: missing cell"
    assert r["q4"]["markets"]["fresh2"] == "not decided" and "generalisation not established" in r["q4"]["wording"] and r["q4"]["k"] is not None
    assert r["secondary"] != "unanswered" and gone in r["missing"] and set(r["unanswered"]) == {"Q1", "Q2", "Q3"}


def test_unavailable_context_is_unanswered_not_an_error(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    ids = [j["id"] for j in cat if j["context"] == "fresh3@rho0.2"]
    r = _run(monkeypatch, out, cat, verify={"ok": True, "h4": None, "contexts": {"fresh3@rho0.2": {"status": "unavailable", "missing": ids}}})
    assert all(t["category"] == "not decided: missing cell" for t in r["q1"]["tests"].values())
    assert r["q4"]["markets"]["fresh3"] == "not decided" and set(ids) <= set(r["missing"])


def test_q3_unanswered_without_h4(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat, h4_loaded=False)
    assert r["q3"]["independent"].startswith("not run (H4 excluded)") and r["q3"]["envelope"]["F111"]["fresh0"]["family"] == "X7-SC"


def test_nonconfirmatory_draw_has_no_confirmatory_claim(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat, confirmatory=False)
    assert r["confirmatory"] is False and r["q1"]["heading"] == r["q4"]["heading"] == "nonconfirmatory (late publication)"
    md = R.markdown(r)
    assert "nonconfirmatory (late publication)" in md and "confirmatory decision" not in md.replace("no confirmatory decision", "")


def test_report_refuses_foreign_or_stale_records(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    with pytest.raises(SystemExit):
        _run(monkeypatch, out, cat, verify={"ok": False, "h4": None, "contexts": {"fresh0@rho0.2": {"status": "error", "stale": ["x"]}}})


def test_doubling_label_does_not_change_decisions(tmp_path, monkeypatch):
    from scripts.revision_v2 import _safe, write
    a, cat = _world(tmp_path / "a", seed=3); b, _ = _world(tmp_path / "b", seed=3)
    p = b / "doubling" / (_safe(cat[0]["id"]) + ".json"); d = json.loads(p.read_text()); d["incomplete"] = True; write(p, d)
    ra, rb = _run(monkeypatch, a, cat), _run(monkeypatch, b, cat)
    assert ra["q1"] == rb["q1"] and ra["q2"] == rb["q2"]
    assert all(ra["q4"][k] == rb["q4"][k] for k in ("decided", "k", "passing", "failing", "p", "undecided"))   # the decision is unchanged
    assert "prescribed search procedure on fresh0" in rb["q4"]["wording"] and "prescribed" not in ra["q4"]["wording"]   # only its label
    assert ra["doubling"][cat[0]["id"]]["incomplete"] is False and rb["doubling"][cat[0]["id"]]["incomplete"] is True


def test_check_mode_detects_a_changed_record(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    from scripts.revision_v2 import cell_id, eval_path
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat); rep = tmp_path / "report"
    R.save(r, rep)
    assert R.check(_run(monkeypatch, out, cat), rep) == []
    p = eval_path(out, cell_id("fresh1@rho0.2", "F111", "X7-SC", "profit")); d = json.loads(p.read_text()); d["gain"][0] += 1.0; p.write_text(json.dumps(d))
    assert R.check(_run(monkeypatch, out, cat), rep)



# ---- final review K11: a complete report, Markdown included -----------------------------------------------------------------------

def test_k11_headline_whole_systems_are_reported(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat)
    assert set(r["secondary"]["whole_systems"]["B3-t"]) == set(FRESH) | {"headline"}


def test_k11_markdown_renders_every_section(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    out, cat = _world(tmp_path)
    miss = cat[1]["id"]
    r = _run(monkeypatch, out, cat, h4_loaded=False, verify={"ok": True, "h4": None, "contexts": {"x": {"status": "ok", "missing": [], "missing_doubling": [miss]}}})
    md = R.markdown(r)
    p = r["q2"]["searched"]["D2+H3"]["P"]["estimate"]; env = r["q3"]["envelope"]["F111"]["fresh0"]["estimate"]
    for needle in ("## Q2", "## Q3", "## Secondary", "## Doubling", f"{p:.4f}", f"{env:.4f}", "independently authored family (H4): not run (H4 excluded)",
                   "no feasible candidate found", "G_min", "B3-t", f"no doubling record: {miss}"):
        assert needle in md, needle
    assert r["doubling_missing"] == [miss]
    w1 = r["q3"]["welfare"]["F111"]["X7-SC"]["W1"]; w0 = r["q3"]["welfare"]["F111"]["D2+H3"]["W0"]
    for iv in (w1["constraint_interval"], w1["attacker_gain_interval"], w0["attacker_gain_interval"]):
        assert f"[{iv[0]:.4f}, {iv[1]:.4f}]" in md, iv                     # L8: the intervals are rendered with their bounds
    c = w1["constraint_interval"]; assert f"W1 constraint [{c[0]:.4f}, {c[1]:.4f}]" in md          # the W1 constraint is labelled


def test_k11_check_compares_the_markdown(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    out, cat = _world(tmp_path); r = _run(monkeypatch, out, cat); rep = tmp_path / "report"
    R.save(r, rep)
    assert R.check(r, rep) == []
    (rep / "report.md").write_text((rep / "report.md").read_text().replace("Q1", "Q one", 1))
    assert any("report.md" in d for d in R.check(r, rep))


# ---- design draft 7 (Part A2 Task 9): integration through build and markdown ----

def test_report_constants_draft7():
    import scripts.report_v2 as R
    assert R.PAIRS == (("F111", "C*"),) and R.CORE == ("F000", "F111", "C*") and R.WHOLE == ("B3-t", "R3-t", "C*-t")


@pytest.mark.parametrize("delta,label", [(0.15, "R3 materially lower"), (-0.15, "C* materially lower")])
def test_report_q1_sign_both_directions(tmp_path, monkeypatch, delta, label):
    out, cat = _world(tmp_path, gain=lambda m, r: {"F111": 0.2, "C*": 0.2 + delta}.get(r, 0.1))
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0))
    assert all(t["category"] == label for t in r["q1"]["tests"].values())


def test_report_q1_efficiency_and_tradeoff_fields(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    out, cat = _world(tmp_path, gain=lambda m, r: {"F111": 0.05, "C*": 0.25}.get(r, 0.1))
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0)); t = r["q1"]["tests"]["C*-F111|D2+H3"]
    assert t["efficiency"] in ("efficiency condition met", "efficiency loss", "efficiency non-inferiority unresolved")
    assert set(t["side"]) == {"gross_eff_diff", "net_eff_diff", "ref_profit_diff", "audit_spend_diff", "false_refund_focal_diff",
                              "false_refund_others_diff", "served_share_diff"}
    assert t["better"] in (None, "R3 better (efficiency evidence descriptive)")
    md = R.markdown(r)
    assert t["efficiency"] in md and "served_share_diff" in md


def test_report_q2_decomposition_per_market_and_headline(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat); q = r["q2"]
    assert set(q["per_market"]["D2+H3"]) == set(FRESH) | {"headline"}
    a, b, g = q["fixed_attack_term"]["X7-SC"]["P"], q["fixed_reference_term"]["X7-SC"]["P"], q["fixed"]["X7-SC"]["P"]
    assert a["estimate"] - b["estimate"] == pytest.approx(g["estimate"], abs=1e-9)
    assert set(q["fixed_eff"]["D2+H3"]) >= {"P", "G", "S"}


def test_report_envelope_and_welfare_training_selected(tmp_path, monkeypatch):
    from scripts.revision_v2 import _safe
    out, cat = _world(tmp_path, envelope={r: "F001" for r in FACT})
    r = _run(monkeypatch, out, cat)
    cr = json.loads((out / "cross" / "fresh0@rho0.2" / (_safe("D2+H3") + ".json")).read_text())
    want = float(np.mean(cr["per_seed"]["F001>F111"]))
    assert r["q2"]["envelope"]["D2+H3"]["fresh0"]["F111"]["attack"] == "F001"
    assert r["q2"]["envelope"]["D2+H3"]["fresh0"]["F111"]["estimate"] == pytest.approx(want)
    w = r["q3"]["welfare_selected"]["F111"]["W0"]
    assert w["family"] == "X7-SC" and w["other_family"] == "D2+H3"           # the training choice, although D2+H3 has the lower evaluation efficiency


def test_report_w1_contradicted(tmp_path, monkeypatch):
    out, cat = _world(tmp_path, w1=-0.2)
    r = _run(monkeypatch, out, cat)
    assert r["q3"]["welfare"]["F111"]["X7-SC"]["W1"]["w1_class"] == "contradicted"
    assert r["q3"]["welfare_selected"]["C*"]["W1"] == {"family": None, "status": "no feasible candidate found"}


def test_report_q3_reduced_after_h4_exclusion_and_diagnostic(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat, h4_loaded=False)
    assert r["q3"]["independent"] == "not run (H4 excluded); the independently authored part of Q3 is unanswered"
    assert set(r["q3"]["coalition"]["F111"]) == {"c2_synchronised", "c2_staggered", "c5_synchronised", "c5_staggered", "c2_roles"}
    assert r["q3"]["diagnostic"]["F111"]["bins"][0]["audited_share"] == pytest.approx(0.9)
    md = R.markdown(r)
    assert "c2_roles" in md and "honest replacement" in md and "reduced menu (D2+H3)" in md


def test_report_nonfinite_withholds_only_affected(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id, eval_path, write
    out, cat = _world(tmp_path)
    p = eval_path(out, cell_id("fresh1@rho0.2", "C*", "X7-SC", "profit")); d = json.loads(p.read_text())
    d["gain"] = [1e308 * (-1) ** k for k in range(N_SEEDS)]; write(p, d)                 # finite values whose variance overflows
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0))
    assert r["q1"]["tests"]["C*-F111|X7-SC"]["category"] == "not decided: numerical refusal"
    assert r["q1"]["tests"]["C*-F111|D2+H3"]["p"] is not None and r["q4"]["decided"] is True


def test_report_paired_overflow_refused(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id, eval_path, write
    out, cat = _world(tmp_path)
    for rule, v in (("C*", 1e308), ("F111", -1e308)):
        p = eval_path(out, cell_id("fresh2@rho0.2", rule, "D2+H3", "profit")); d = json.loads(p.read_text()); d["gain"] = [v] * N_SEEDS; write(p, d)
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0))
    assert r["q1"]["tests"]["C*-F111|D2+H3"]["category"] == "not decided: numerical refusal" and r["q1"]["tests"]["C*-F111|X7-SC"]["p"] is not None


def test_missing_vs_flagged_statuses(tmp_path, monkeypatch):
    from scripts.revision_v2 import _safe, cell_id, write
    out, cat = _world(tmp_path)
    fl = cell_id("fresh0@rho0.2", "F111", "X7-SC", "profit")
    write(out / "doubling" / (_safe(fl) + ".json"), {"stage": "doubling", "kind": "profit", "attack_change": 0.02, "reference_change": 0.0, "incomplete": True})
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0))
    t = r["q1"]["tests"]["C*-F111|X7-SC"]
    assert t["p"] is not None and t["search"] == "about the prescribed search procedure (search flagged)"
    assert r["q1"]["tests"]["C*-F111|D2+H3"]["search"] is None
    assert r["q3"]["robustness"]["F111"]["X7-SC"] == "unanswered (search flagged)" and fl in r["search_flagged"]


def test_multiplicity_statement(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    out, cat = _world(tmp_path)
    md = R.markdown(_run(monkeypatch, out, cat))
    assert "Multiplicity is controlled within Q1 and within Q4 only; there is no paper-wide familywise guarantee." in md



# ---- whole-branch review round 1 (Sol, Astra): statuses, refusals, and Q2 parts ----

FLAG = "about the prescribed search procedure (search flagged)"


def _flag(out, rid, incomplete=True):
    from scripts.revision_v2 import _safe, write
    write(out / "doubling" / (_safe(rid) + ".json"), {"stage": "doubling", "kind": "profit", "attack_change": 0.02, "reference_change": 0.0,
                                                      "incomplete": incomplete})


def test_complete_run_reports_no_missing_cell(tmp_path, monkeypatch):
    """A complete run lists no missing cell: cells the schedule does not contain (X7-SC for fresh-market whole systems, a cut
    family) are not looked up as missing."""
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat)
    assert r["missing"] == [] and "X7-SC" not in str(r["secondary"]["whole_systems"]["B3-t"]["fresh0"])
    cut = [j for j in cat if not (j["family"] == "H4" and j["context"] != "headline@rho0.2")]             # cut level 2: H4 on fresh markets
    r = _run(monkeypatch, out, cut)
    assert r["missing"] == [] and isinstance(r["q3"]["envelope"]["F111"]["fresh0"], dict)


def test_w1_and_coalition_refusals_are_withheld_and_rendered(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    from scripts.revision_v2 import cell_id, eval_path, write
    out, cat = _world(tmp_path)
    p = eval_path(out, cell_id("headline@rho0.2", "F111", "X7-SC", "W1")); d = json.loads(p.read_text())
    d["constraint"] = [1e308 * (-1) ** k for k in range(N_SEEDS)]; write(p, d)                      # finite values whose variance overflows
    p = eval_path(out, cell_id("headline@rho0.2", "F111", "X8-DB", "min", 2, "roles")); d = json.loads(p.read_text())
    d["member_gain"] = [[1e308 * (-1) ** k for k in range(N_SEEDS)]] * 2; write(p, d)
    r = _run(monkeypatch, out, cat)
    w = r["q3"]["welfare"]["F111"]["X7-SC"]["W1"]
    assert w["w1_class"] == "not decided: numerical refusal" and w["constraint_interval"] == [None, None]
    assert r["q3"]["welfare"]["F111"]["D2+H3"]["W1"]["w1_class"] in ("supported", "contradicted", "inconclusive")
    g = r["q3"]["coalition"]["F111"]["c2_roles"]["G_min"]
    assert g["bounds"] == [None, None] and g["status"] == "not decided: numerical refusal"
    assert isinstance(r["q3"]["coalition"]["F111"]["c2_synchronised"]["G_min"]["bounds"][0], float)
    md = R.markdown(r)
    assert "W1 constraint [withheld: numerical refusal]" in md and "G_min" in md and "Q3" in r["unanswered"]


def test_q2_keeps_available_parts_with_per_market_and_headline_results(tmp_path, monkeypatch):
    import scripts.report_v2 as R
    from scripts.revision_v2 import _safe, cell_id
    gone = cell_id("fresh2@rho0.2", "F111", "D2+H3", "profit")
    out, cat = _world(tmp_path, missing=(gone,))
    (out / "cross" / "fresh3@rho0.2" / (_safe("X7-SC") + ".json")).unlink()
    r = _run(monkeypatch, out, cat, verify={"ok": True, "h4": None, "contexts": {"fresh2@rho0.2": {"status": "ok", "missing": [gone]}}})
    q = r["q2"]
    assert q["searched"]["D2+H3"] == "unanswered: missing cell" and isinstance(q["searched"]["X7-SC"], dict)
    assert isinstance(q["fixed"]["D2+H3"], dict) and q["fixed"]["X7-SC"] == "unanswered: missing cross record"
    assert q["per_market"]["D2+H3"]["fresh2"]["searched"] == "unanswered: missing cell"
    assert q["per_market"]["X7-SC"]["fresh3"]["fixed"] == "unanswered: missing cross record" and q["envelope"]["X7-SC"]["fresh3"] == "unanswered: missing cross record"
    head = q["per_market"]["D2+H3"]["headline"]
    for kind in ("searched", "searched_eff", "searched_net_eff", "fixed", "fixed_attack_term", "fixed_reference_term", "fixed_eff", "fixed_net_eff"):
        assert head[kind]["P"]["estimate"] is not None and len(head[kind]["P"]["interval"]) == 2, kind
    assert set(q["envelope"]["D2+H3"]["headline"]) == set(FACT)
    a, b, g = head["fixed_attack_term"]["G"], head["fixed_reference_term"]["G"], head["fixed"]["G"]
    assert a["estimate"] - b["estimate"] == pytest.approx(g["estimate"], abs=1e-9)
    assert isinstance(q["fixed_net_eff"]["D2+H3"]["P"]["estimate"], float) and isinstance(q["searched_net_eff"]["X7-SC"]["P"]["estimate"], float)
    md = R.markdown(r)
    assert "fixed_net_eff" in md and "headline" in md and "unanswered: missing cross record" in md


def test_search_status_reaches_welfare_coalition_q4_and_missing_checks(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id
    out, cat = _world(tmp_path)
    w1 = cell_id("headline@rho0.2", "F111", "X7-SC", "W1"); co = cell_id("headline@rho0.2", "C*", "X8-DB", "min", 2, "roles")
    q4c = cell_id("fresh3@rho0.2", "F000", "D2+H3", "profit"); nochk = cell_id("fresh0@rho0.2", "F000", "X7-SC", "profit")
    w0nochk = cell_id("headline@rho0.2", "F000", "D2+H3", "W0")
    for rid in (w1, co, q4c):
        _flag(out, rid)
    r = _run(monkeypatch, out, cat, kappa=(1.0, 1.0), verify={"ok": True, "h4": None, "contexts": {"x": {"status": "ok", "missing": [], "missing_doubling": [nochk, w0nochk]}}})
    q3 = r["q3"]
    assert q3["welfare"]["F111"]["X7-SC"]["W1"]["search"] == FLAG and q3["welfare"]["F111"]["X7-SC"]["W1"]["robustness"] == "unanswered (search flagged)"
    assert q3["welfare"]["F111"]["D2+H3"]["W1"]["robustness"] == "answered"
    assert q3["welfare"]["F000"]["D2+H3"]["W0"]["robustness"] == "unanswered (scheduled check missing)"
    assert q3["coalition"]["C*"]["c2_roles"]["robustness"] == "unanswered (search flagged)" and q3["coalition"]["C*"]["c2_staggered"]["robustness"] == "answered"
    assert q3["robustness"]["F000"]["X7-SC"] == "unanswered (scheduled check missing)" and q3["robustness"]["F000"]["D2+H3"] == "unanswered (search flagged)"
    assert q3["robustness"]["F111"]["X5-AG/v2"] == "no search-quality claim (no scheduled check)" and q3["robustness"]["C*"]["X7-SC"] == "answered"
    assert r["q4"]["markets"]["fresh3"]["search"] == FLAG and r["q4"]["markets"]["fresh0"]["search"] is None
    assert "decisions about the prescribed search procedure on fresh3" in r["q4"]["wording"]


def test_missing_cell_makes_robustness_unanswered(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id
    gone = cell_id("fresh2@rho0.2", "F111", "D2+H3", "profit")
    out, cat = _world(tmp_path, missing=(gone,))
    r = _run(monkeypatch, out, cat, verify={"ok": True, "h4": None, "contexts": {"fresh2@rho0.2": {"status": "ok", "missing": [gone]}}})
    assert r["q3"]["robustness"]["F111"]["D2+H3"] == "unanswered (missing cell)" and r["q3"]["robustness"]["F111"]["X7-SC"] == "answered"
