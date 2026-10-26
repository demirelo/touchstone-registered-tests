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
Q1R = ("F111", "C*", "R4", "C*/S2")
CORE = ("F000", "F111", "C*", "R4")
N_SEEDS = 24


def _job(ctx, rule, family, objective="profit", c=None, schedule=None):
    from scripts.revision_v2 import cell_id
    return {"id": cell_id(ctx, rule, family, objective, c, schedule), "context": ctx, "rule": rule, "family": family, "objective": objective,
            "c": c, "schedule": schedule, "mkt": {"cfg": SimpleNamespace(N=10), "seeds_eval": list(range(N_SEEDS)), "label": ctx.split("@")[0]}}


def _profit(rng, mean_gain, eff=0.95):
    g = rng.normal(mean_gain, 0.05, N_SEEDS); sstar = np.full(N_SEEDS, 50.0); pref = rng.normal(5.0, 0.2, N_SEEDS)
    return {"seeds": list(range(N_SEEDS)), "gain": g.tolist(), "eff_attack": rng.normal(eff, 0.005, N_SEEDS).tolist(), "eff_ref": [0.97] * N_SEEDS,
            "net_eff_attack": [0.94] * N_SEEDS, "net_eff_ref": [0.96] * N_SEEDS, "profit_attack": (pref + g * 5).tolist(), "profit_ref": pref.tolist(),
            "audit_spend_attack": [0.1] * N_SEEDS, "sstar": sstar.tolist()}


def _world(tmp_path, seed=0, missing=(), gain=None, eff=None):
    """Every cell the questions read, on the six fresh markets and the headline market; returns (out, catalog)."""
    from scripts.revision_v2 import eval_path, path_of, write
    rng = np.random.default_rng(seed); out = tmp_path / "eval"; cat = []
    gain = gain or (lambda m, r: {"F000": 0.30, "F111": 0.02, "C*": 0.05, "R4": 0.03, "C*/S2": 0.04}.get(r, 0.1 + 0.01 * FACT.index(r) if r in FACT else 0.1))
    eff = eff or (lambda m, r: 0.95)
    for m in FRESH + ["headline"]:
        ctx = f"{m}@rho0.2"
        rules = sorted(set(FACT) | set(Q1R) | set(CORE))
        for r in rules:
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
            rows = {f"{a}>{r}": rng.normal(0.1 + 0.01 * FACT.index(r), 0.05, N_SEEDS).tolist() for a in FACT for r in FACT}
            p = out / "cross" / ctx / (fam.replace("+", "+") + ".json")
            from scripts.revision_v2 import _safe
            write(out / "cross" / ctx / (_safe(fam) + ".json"), {"stage": "cross", "context": ctx, "family": fam, "attacks": FACT, "rules": FACT,
                                                                 "matrix": [[float(np.mean(rows[f"{a}>{r}"])) for r in FACT] for a in FACT], "per_seed": rows})
    ctx = "headline@rho0.2"
    for r in CORE:
        for fam in ("D2+H3", "X7-SC"):
            for obj in ("W0", "W1"):
                j = _job(ctx, r, fam, obj); cat.append(j)
                if j["id"] in missing:
                    continue
                if obj == "W1" and r == "R4":
                    write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], "seeds": list(range(N_SEEDS)), "no_feasible_candidate": True})
                    continue
                rec = {"seeds": list(range(N_SEEDS)), "eff": rng.normal(0.80, 0.01, N_SEEDS).tolist(), "normalized": rng.normal(0.5, 0.02, N_SEEDS).tolist()}
                if obj == "W1":
                    rec["constraint"] = rng.normal(0.01, 0.005, N_SEEDS).tolist()
                write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], **rec})
        for c in (2, 5):
            for sch in ("synchronised", "staggered"):
                for obj in ("total", "min"):
                    j = _job(ctx, r, "X6-SE/v2", obj, c, sch); cat.append(j)
                    mg = rng.normal(0.05, 0.02, (c, N_SEEDS))
                    write(eval_path(out, j["id"]), {"stage": "evaluate", "id": j["id"], "seeds": list(range(N_SEEDS)), "member_gain": mg.tolist(),
                                                    "total": float(mg.mean(axis=1).sum()), "min": float(mg.mean(axis=1).min())})
    for r in ("B3-t", "R3-t", "R4-t", "C*-t"):
        for m in FRESH + ["headline"]:
            for fam in ("D2+H3", "X7-SC"):
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
    st = [_gain(out, f"{m}@rho0.2", "F111", "D2+H3") - _gain(out, f"{m}@rho0.2", "C*", "D2+H3") for m in FRESH]
    t = r["q1"]["tests"]["F111-C*|D2+H3"]; tail = 0.5 * 0.05 / 8
    assert t["estimate"] == pytest.approx(I.stratified_mean(st))
    assert t["interval"] == pytest.approx([I.stratified_at(st, "lower", tail), I.stratified_at(st, "upper", tail)])
    assert t["interval"][0] != pytest.approx(I.stratified_at(st, "lower", 0.05 / 8))          # kappa is used
    assert t["category"] in ("R lower", "C lower", "equivalent", "inconclusive") and set(r["q1"]["tests"]) == {f"{a}-{b}|{f}" for a, b in (("F111", "C*"), ("R4", "C*/S2")) for f in ("D2+H3", "X7-SC")}
    d = r["q1"]["descriptive"]["fresh0"]["F111-C*|D2+H3"]
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
    assert r["q3"]["welfare"]["R4"]["D2+H3"]["W1"] == "no feasible candidate found"
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
    t = r["q1"]["tests"]["R4-C*/S2|X7-SC"]
    assert t["category"] == "no confirmatory decision" and t["estimate"] is not None and t["interval_label"] == "nominal 95 percent, unadjusted"
    assert r["q4"]["decided"] is False and r["q4"]["wording"] == "no confirmatory decision" and r["q4"]["markets"]["fresh0"]["gain_diff_lower"] is not None


def test_missing_cells_make_dependent_questions_unanswered(tmp_path, monkeypatch):
    from scripts.revision_v2 import cell_id
    gone = cell_id("fresh2@rho0.2", "F111", "D2+H3", "profit")
    out, cat = _world(tmp_path, missing=(gone,))
    r = _run(monkeypatch, out, cat, verify={"ok": True, "h4": None, "contexts": {"fresh2@rho0.2": {"status": "ok", "missing": [gone]}}})
    assert r["q1"] == "unanswered" and r["q2"] == "unanswered" and r["q3"] == "unanswered"
    assert r["q4"]["markets"]["fresh2"] == "not decided" and "generalisation not established" in r["q4"]["wording"] and r["q4"]["k"] is not None
    assert r["secondary"] != "unanswered" and gone in r["missing"] and set(r["unanswered"]) == {"Q1", "Q2", "Q3"}


def test_unavailable_context_is_unanswered_not_an_error(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    ids = [j["id"] for j in cat if j["context"] == "fresh3@rho0.2"]
    r = _run(monkeypatch, out, cat, verify={"ok": True, "h4": None, "contexts": {"fresh3@rho0.2": {"status": "unavailable", "missing": ids}}})
    assert r["q1"] == "unanswered" and r["q4"]["markets"]["fresh3"] == "not decided" and set(ids) <= set(r["missing"])


def test_q3_unanswered_without_h4(tmp_path, monkeypatch):
    out, cat = _world(tmp_path)
    r = _run(monkeypatch, out, cat, h4_loaded=False)
    assert r["q3"]["independent"] == "unanswered" and r["q3"]["envelope"]["F111"]["fresh0"]["family"] == "X7-SC"


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
    assert ra["q1"] == rb["q1"] and ra["q4"] == rb["q4"] and ra["q2"] == rb["q2"]
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
    for needle in ("## Q2", "## Q3", "## Secondary", "## Doubling", f"{p:.4f}", f"{env:.4f}", "independently authored family (H4): unanswered",
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
