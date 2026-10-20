"""The exploratory cell runner (scripts/explore_attackers.py), smoke budget on B3. Plan Task 3 and Task 4."""
from __future__ import annotations

import json
import numpy as np
import pytest

import scripts.explore_attackers as X
from sim.cell import SeedCache, run_focal
from sim.policies.exploratory import EXPLORATORY_FAMILIES
from sim.policies.families import exact_key
from sim.policies.honest import HonestMax


@pytest.fixture(scope="module")
def x1():
    job = X.job_for_x("B3", "X1-AH", smoke=True)
    return job, X.x_search(job)


@pytest.fixture(scope="module")
def x6c2():
    job = X.job_for_x("B3", "X6-SE", c=2, smoke=True)
    return job, X.x_search(job)


def test_search_record_contents_and_hashes(x1):
    job, rec = x1
    for k in ("twin", "attack", "corners", "restart_spread", "twin_vs_honest", "provenance", "runs"):
        assert k in rec
    prov = rec["provenance"]
    for k in ("git_commit", "runner_sha256", "policy_sha256", "params_sha256", "cfg_sha256", "calibration_sha256", "salt_sha256",
              "seeds_train", "seeds_val", "members", "smoke"):
        assert k in prov
    assert prov == job["provenance"] and len(rec["corners"]) == 2 ** EXPLORATORY_FAMILIES["X1-AH"].dim


def test_salt_is_the_development_salt_of_the_registered_dev_val_records():
    job = X.job_for_x("B3", "X5-AG", smoke=True)
    assert job["provenance"]["salt_sha256"].startswith("3b0350f7")


def test_x3_diagnostic_incumbents_counted():
    job = X.job_for_x("B3", "X3-HS", smoke=True); rec = X.x_search(job)
    d = rec["diagnostics"]
    assert [x["window"] for x in d] == [[10, 190], [190, 200]]
    best = rec["attack"]["best_knobs"]
    for x in d:
        assert x["knobs"]["z"] == 0 and all(x["knobs"][k] == best[k] for k in ("u", "m", "s", "w", "clip"))
        assert any(e["source"] == x["source"] for e in rec["attack"]["evaluations"])
    assert rec["runs"] == rec["scheduled_runs"]


def test_bank_parity_with_frozen_bank():
    from sim.bank import Bank
    from sim.calibrate import cell_config, load_calibration
    from sim.cell import Cell
    from sim.locked import load_locked, market_config_from_locked
    from sim.policies.families import D2
    from sim.positions import positions
    from sim.registry import make_rule
    lk = load_locked(); cfg = cell_config(market_config_from_locked(lk), load_calibration("experiments/calibration.json"), 0.2, 0.05)
    cell = Cell(cfg=cfg, rule_factory=lambda: make_rule("B3", {"tol": 0.16, "L": 10}), focal=positions(cfg)["median"], seeds=(1000,), name="parity")
    bank = Bank()
    bank.add("D2", {"u0": 0.3, "m0": 0.2, "s": 0.0, "d": 0.1, "r": 0.05, "w": 0.1, "clip": 0}, "a")
    bank.add("D2", {"u0": 0.0, "m0": 0.0, "s": 0.0, "d": 0.0, "r": 0.0, "w": 0.0, "clip": 1}, "b")
    members = bank._compatible("D2")
    known = {exact_key(m): 0.25 for m, _ in members[5:9]}                  # equal known values: ties keep the earlier member
    frozen = bank.bank_pass(cell, D2, SeedCache(), incumbent_f=0.3, known=known)
    local = X.bank_pass_local(members, lambda m: float(run_focal(cell, lambda: D2.make(m), SeedCache()).normalized.mean()), 0.3, known)
    assert [(exact_key(m), f, o) for m, f, o in frozen.ranked] == [(exact_key(m), f, o) for m, f, o in local["ranked"]]
    assert frozen.improved == local["improved"] and (frozen.best_knobs or {}) == (local["best_knobs"] or {})


def test_bank_requires_complete_manifest(x1):
    job, rec = x1
    with pytest.raises(SystemExit):
        X.build_bank_doc("X1-AH", {job["name"]: rec}, rules=["B2", "B3"], sizes=None)


def test_bank_replaces_only_when_strictly_better():
    members = [({"a": 1}, "m1"), ({"a": 2}, "m2")]
    vals = {exact_key({"a": 1}): 0.5, exact_key({"a": 2}): 0.5}
    out = X.bank_pass_local(members, lambda m: vals[exact_key(m)], 0.5, {})
    assert not out["improved"]
    out2 = X.bank_pass_local(members, lambda m: vals[exact_key(m)], 0.4999, {})
    assert out2["improved"] and out2["best_knobs"] == {"a": 1}             # tie: the earlier member


def test_reference_order_registered_without_h2(x1):
    job, rec = x1
    doc = X.build_bank_doc("X1-AH", {job["name"]: rec}, rules=["B3"], sizes=None)
    brec = X.x_bank(job, rec, doc); ref = X.x_reference(job, rec, brec)
    groups = [n.split("_")[0] if n.startswith("bank_") else n for n in ref["scores"]]
    order = ["abstain", "honest_max", "twin_search", "attack_projection", "archive_clip1", "archive_truthful_clip0", "bank"]
    seen = [g for g in order if g in groups]
    assert [g for g in dict.fromkeys(groups)] == seen and "H2" not in json.dumps(ref)


def test_x6_reference_rescored_with_honest_opponents(x6c2):
    job, rec = x6c2
    poisoned = json.loads(json.dumps(rec))
    for e in poisoned["attack"]["archive"]:
        e["f"] = 99.0 if e["knobs"]["clip"] == 1 else e["f"]                 # misleading cached coalition scores
        e["per_seed_normalized"] = [99.0 for _ in e["per_seed_normalized"]]
    ref = X.x_reference(job, poisoned, None)
    cell = X.make_unilateral_cell(job, tuple(job["seeds_train"]))
    fam = EXPLORATORY_FAMILIES["X6-SE"]
    for name, score in ref["scores"].items():
        assert score < 50.0                                                  # no cached coalition score survived
    chosen = ref["candidate"]
    if chosen["knobs"] is not None:
        k = dict(chosen["knobs"]); want = float(run_focal(cell, lambda: fam.make(k), SeedCache()).normalized.mean())
        assert ref["scores"][chosen["name"]] == pytest.approx(want)


def test_x6_twin_clips_every_member(x6c2):
    job, rec = x6c2
    assert all(e["knobs"]["clip"] == 1 for e in rec["twin"]["evaluations"])
    obj = X.CoalitionObjective(job, tuple(job["seeds_train"]), SeedCache(), force_clip=True)
    k = dict(rec["attack"]["best_knobs"]); k["clip"] = 0
    pols = obj.member_policies(obj.family.project(k) if obj.force_clip else k)
    assert len(pols) == 2 and all(p.clip == 1 for p in pols)


def test_x6_c1_equals_unilateral():
    job = X.job_for_x("B3", "X6-SE", c=1, smoke=True)
    k = {"u": 0.4, "m": 0.3, "s": 0.0, "w": 0.1, "P": 12.0, "x": 1, "y": 1, "clip": 0}
    co = X.CoalitionObjective(job, tuple(job["seeds_train"]), SeedCache()).eval_knobs(k)
    from sim.search import Objective
    uni = Objective(X.make_unilateral_cell(job, tuple(job["seeds_train"])), EXPLORATORY_FAMILIES["X6-SE"], SeedCache()).eval_knobs(k)
    assert co == pytest.approx(uni)


def test_evaluate_rows_and_local_diagnostics(x6c2):
    from sim.reference import ROW_FIELDS
    job, rec = x6c2
    doc = X.build_bank_doc("X6-SE", {job["name"]: rec}, rules=["B3"], sizes=[2])
    brec = X.x_bank(job, rec, doc); ref = X.x_reference(job, rec, brec); ev = X.x_evaluate(job, ref)
    assert len(ev["rows"]) == len(job["seeds_val"])
    for r in ev["rows"]:
        assert set(ROW_FIELDS) <= set(r)
        for k in ("focal_identities", "fresh_served_focal", "fresh_audited_focal", "fresh_served_market", "rounds_fresh_exceeds_audits",
                  "member_bans", "outsider_bans", "outsider_lost_capacity", "harm_outsiders", "member_gain_vs_honest"):
            assert k in r
        assert r["focal_identities"] >= 1


def test_stale_or_smoke_record_refused(x1):
    job, rec = x1
    stale = json.loads(json.dumps(rec)); stale["provenance"]["policy_sha256"] = "0" * 64
    with pytest.raises(SystemExit):
        X.check_inputs(job, stale)
    real = dict(job); real["provenance"] = {**job["provenance"], "smoke": False}
    with pytest.raises(SystemExit):
        X.check_inputs(real, rec)


def test_seed_allow_list():
    job = X.job_for_x("B3", "X5-AG", smoke=True)
    X.check_job_seeds(job)
    bad = dict(job); bad["seeds_val"] = list(job["seeds_val"]) + [10_000_123]
    with pytest.raises(SystemExit):
        X.check_job_seeds(bad)


def test_atomic_write_and_resume(tmp_path):
    o = {"stage": "all", "rules": "B3", "families": "X5-AG", "sizes": "1", "workers": 1, "out": str(tmp_path), "smoke": True}
    t1 = X.run(o)
    assert t1["search"] > 0 and (tmp_path / "evaluate").exists() and not list(tmp_path.rglob("*.tmp"))
    t2 = X.run(o)
    assert sum(t2.values()) == 0                                             # every stage skipped on resume
    rep = json.loads((tmp_path / "report.json").read_text())
    assert rep["cells"] and rep["cells"][0]["family"] == "X5-AG"


def test_pilot_refuses_missing_bank_sources(tmp_path):
    o = {"stage": "bank", "rules": "B2,B3", "families": "X5-AG", "sizes": "1", "workers": 1, "out": str(tmp_path), "smoke": True}
    X.run({**o, "stage": "search", "rules": "B3"})
    with pytest.raises(SystemExit):
        X.run(o)


def test_episode_manifest_counts():
    m = X.episode_manifest(smoke=False, rules=["B1", "B2", "B3", "proposed"], families=list(EXPLORATORY_FAMILIES), sizes=[1, 2, 5])
    assert m["cells"] == 5 * 4 + 3 * 4 and m["search_episodes"] > 400_000


def test_x6_doubling_moves_all_members_and_ignores_coalition_scores(x6c2, monkeypatch):
    from sim import search as S
    job, rec = x6c2
    calls = {"frozen": 0}
    orig = S.Objective.eval_knobs
    def spy(self, knobs, source="search"):
        if not isinstance(self, X.CoalitionObjective) and not isinstance(self, X.UnilateralObjective):
            calls["frozen"] += 1
        return orig(self, knobs, source)
    monkeypatch.setattr(S.Objective, "eval_knobs", spy)
    d = X.x_doubling(job, rec, None)
    assert calls["frozen"] == 0 and d["doubling"]["ref_base_name"] and "delta_gain" in d["doubling"]


def test_x6_doubling_c1_parity():
    from sim.search_checks import doubling_check
    from sim.search import SearchResult
    from sim.records import search_from_json
    job = X.job_for_x("B3", "X6-SE", c=1, smoke=True); rec = X.x_search(job)
    loc = X.x_doubling(job, rec, None)["doubling"]
    cell = X.make_unilateral_cell(job, tuple(job["seeds_train"]))
    fz = doubling_check(cell, EXPLORATORY_FAMILIES["X6-SE"], SeedCache(), X.settings_of(job), seed=0, base_attack=search_from_json(rec["attack"]),
                        base_twin=search_from_json(rec["twin"]), bank_members=[], order=tuple(job["reference_order"]))
    assert loc["delta_gain"] == pytest.approx(fz.delta_gain) and loc["ref_base_name"] == fz.ref_base_name


def test_assemble_gain_matches_frozen_evaluate_gain():
    from sim.reference import Candidate, evaluate_gain, METRIC_FIELDS
    job = X.job_for_x("B3", "X5-AG", smoke=True); fam = EXPLORATORY_FAMILIES["X5-AG"]
    cell = X.make_unilateral_cell(job, tuple(job["seeds_val"]))
    k = {"u": 0.4, "m": 0.3, "s": 0.0, "w": 0.1, "n_age": 5.0, "x": 1, "clip": 0}
    ref = Candidate("honest_max", HonestMax, None)
    frozen = evaluate_gain(cell, fam, k, ref, SeedCache())
    c = SeedCache()
    loc = X.assemble_gain(cell, run_focal(cell, lambda: fam.make(k), c), run_focal(cell, lambda: fam.make(fam.project(k)), c),
                          run_focal(cell, HonestMax, c), run_focal(cell, HonestMax, c))
    for name in METRIC_FIELDS[1:]:
        assert np.allclose(getattr(frozen, name), getattr(loc, name)), name


def test_report_has_every_cell_prediction_and_control(tmp_path):
    o = {"stage": "all", "rules": "B3", "families": "X5-AG", "sizes": "1", "workers": 1, "out": str(tmp_path), "smoke": True,
         "registered_sweep": str(tmp_path / "reg")}
    reg = tmp_path / "reg" / "evaluate"; reg.mkdir(parents=True)
    (reg / "B3_D2+H3_beta0.05_rho0.2_median_h3.json").write_text(json.dumps({"rows": [{"gain": 0.3}, {"gain": 0.4}]}))
    X.run(o)
    rep = json.loads((tmp_path / "report.json").read_text())
    (c,) = rep["cells"]
    assert c["cell"] == "B3_X5-AG" and c["prediction_item"] == 4 and c["control_d2h3_devval_gain"] == pytest.approx(0.35)
    assert c["final40_d2h3_gain"] is not None and "exploratory" in rep["status"]
    for k in ("gain_mean", "inflation_term", "selection_term", "eff_attack", "eff_clip", "eff_ref", "eff_honest", "net_eff_attack", "harm",
              "audit_spend", "focal_failures", "focal_bans", "focal_identities", "knobs", "source", "reference", "restart_gain_spread",
              "twin_vs_honest_passed", "bank_improved"):
        assert k in c


# ---- final-review fix pass ---------------------------------------------------------------------------------------------

def test_harm_outsiders_equals_registered_direct_harm_for_a_single_member():
    from sim.metrics import harm
    job = X.job_for_x("B3", "X5-AG", smoke=True); fam = EXPLORATORY_FAMILIES["X5-AG"]
    cell = X.make_unilateral_cell(job, tuple(job["seeds_val"])); c = SeedCache()
    k = {"u": 0.4, "m": 0.3, "s": 0.0, "w": 0.1, "n_age": 5.0, "x": 1, "clip": 0}
    a = run_focal(cell, lambda: fam.make(k), c); r = run_focal(cell, HonestMax, c)
    for ra, rr in zip(a.results, r.results):
        d = X.local_diagnostics(ra, cell.cfg, cell.focal, [cell.focal], rr, rr)
        assert d["harm_outsiders"] == pytest.approx(harm(ra, rr, cell.focal)[1])


def test_provenance_binds_search_settings_reference_order_and_intervals():
    job = X.job_for_x("B3", "X5-AG", smoke=True)
    for k in ("search", "reference_order", "intervals"):
        assert job["provenance"][k] == job[k]


def test_partial_record_refused(x1):
    job, rec = x1
    with pytest.raises(SystemExit):
        X.validate_record(job, "search", {"name": job["name"], "provenance": job["provenance"], "stage": "search"}, {})


def test_changed_upstream_refused(x1):
    job, rec = x1
    doc = X.build_bank_doc("X1-AH", {job["name"]: rec}, rules=["B3"], sizes=None)
    brec = X.x_bank(job, rec, doc)
    changed = json.loads(json.dumps(rec)); changed["attack"]["best_f"] += 1.0
    with pytest.raises(SystemExit):
        X.x_reference(job, changed, brec)                      # the bank record was built from the original search record


def test_real_run_requires_a_bank_record_and_all_bank_sources():
    job = X.job_for_x("proposed", "X5-AG", smoke=False)
    fake = {"name": job["name"], "provenance": job["provenance"], "stage": "search"}
    with pytest.raises(SystemExit):
        X.x_reference(job, fake, None)
    assert X.bank_source_cells("X5-AG", smoke=False, rules=["proposed"], sizes=[1]) == [f"{r}_X5-AG" for r in X.RULES]
    assert X.bank_source_cells("X6-SE", smoke=False, rules=["proposed"], sizes=[2]) == [f"{r}_X6-SE_c{c}" for r in X.RULES for c in X.X6_SIZES]


def test_report_refuses_missing_stale_or_wrong_seed_evaluations(tmp_path):
    o = {"stage": "all", "rules": "B3", "families": "X5-AG", "sizes": "1", "workers": 1, "out": str(tmp_path), "smoke": True}
    X.run(o)
    jobs = X.all_jobs(["B3"], ["X5-AG"], [1], True)
    ev = tmp_path / "evaluate" / "B3_X5-AG.json"; good = ev.read_text()
    d = json.loads(good); d["rows"] = d["rows"][:1]; ev.write_text(json.dumps(d))
    with pytest.raises(SystemExit):
        X.report(tmp_path, jobs)
    d = json.loads(good); d["provenance"]["policy_sha256"] = "0" * 64; ev.write_text(json.dumps(d))
    with pytest.raises(SystemExit):
        X.report(tmp_path, jobs)
    ev.unlink()
    with pytest.raises(SystemExit):
        X.report(tmp_path, jobs)


def test_report_binds_sources_and_carries_prediction_text(tmp_path):
    o = {"stage": "all", "rules": "B3", "families": "X5-AG", "sizes": "1", "workers": 1, "out": str(tmp_path), "smoke": True}
    X.run(o)
    rep = json.loads((tmp_path / "report.json").read_text())
    assert rep["sources"]["B3_X5-AG"] and "X5" in rep["cells"][0]["prediction"] and rep["smoke"] is True


def test_degenerate_bound_uses_the_frozen_bound():
    lk_int = X.job_for_x("B3", "X5-AG", smoke=True)["intervals"]
    v, deg = X.upper_bound([1 / 3] * 20, lk_int)
    assert deg and v == pytest.approx(1 / 3)
    v0, deg0 = X.upper_bound([0.0] * 20, lk_int)
    assert deg0 and v0 == 0.0


def _knob_tuple(p):
    return (p.u, p.m, p.s, p.w, p.clip, getattr(p, "P", None), getattr(p, "x", None), getattr(p, "y", None))


@pytest.mark.parametrize("c", [2, 5])
def test_coalition_partners_follow_every_evaluated_candidate(c, monkeypatch):
    """Every run on the coalition path (search, evaluate, doubling) installs partners whose knobs equal the focal's,
    clipped together; reference and honest runs install no partners."""
    job = X.job_for_x("B3", "X6-SE", c=c, smoke=True)
    seen = {"coalition": 0, "unilateral": 0}
    orig = X.run_focal
    def spy(cell, factory, cache):
        if cell.others:
            focal = factory(); assert len(cell.others) == c - 1
            for _, f in cell.others:
                assert _knob_tuple(f()) == _knob_tuple(focal)
            seen["coalition"] += 1
        else:
            seen["unilateral"] += 1
        return orig(cell, factory, cache)
    monkeypatch.setattr(X, "run_focal", spy)
    rec = X.x_search(job)
    ref = X.x_reference(job, rec, None); X.x_evaluate(job, ref); X.x_doubling(job, rec, None)
    assert seen["coalition"] > 0 and seen["unilateral"] > 0


def test_x6_reference_reversed_rankings_choose_the_unilateral_best(x6c2):
    job, rec = x6c2
    rev = json.loads(json.dumps(rec))
    for e in rev["attack"]["archive"]:
        e["f"] = -e["f"]; e["per_seed_normalized"] = [-v for v in e["per_seed_normalized"]]   # coalition ranking reversed
    ref = X.x_reference(job, rev, None)
    cell = X.make_unilateral_cell(job, tuple(job["seeds_train"])); fam = EXPLORATORY_FAMILIES["X6-SE"]
    want = {}
    for cand in ref["candidates"]:
        if cand["knobs"] is None:
            continue
        k = dict(cand["knobs"]); want[cand["name"]] = float(run_focal(cell, lambda: fam.make(k), SeedCache()).normalized.mean())
    for name, v in want.items():
        assert ref["scores"][name] == pytest.approx(v)
    best = max(ref["scores"].items(), key=lambda kv: kv[1])[0]
    assert ref["candidate"]["name"] == best


def test_bank_projected_members_match_frozen():
    from sim.bank import Bank
    from sim.policies.families import D2
    bank = Bank(); bank.add("D2", {"u0": 0.3, "m0": 0.2, "s": 0.0, "d": 0.1, "r": 0.05, "w": 0.1, "clip": 0}, "a")
    assert X.project_members(D2, bank._compatible("D2")) == bank.projected_members_for("D2")


def test_x6_controls_have_full_metrics_and_per_member_resets(x6c2):
    job, rec = x6c2
    k = dict(rec["attack"]["best_knobs"]); k.update({"y": 1, "x": 1, "P": 3.0})
    from sim.reference import Candidate
    cell = X.make_unilateral_cell(job, tuple(job["seeds_val"])); c = SeedCache()
    ref = run_focal(cell, HonestMax, c); honest = run_focal(cell, HonestMax, c)
    ctr = X.x6_controls(job, k, ref, honest, c)
    assert set(ctr) == {"x1_synchronised", "x1_staggered", "x0_synchronised", "x0_staggered"}
    for v in ctr.values():
        for f in ("gain_mean", "gain_upper95", "inflation_term", "selection_term", "eff_attack", "eff_clip", "eff_ref", "eff_honest",
                  "harm_outsiders", "audit_spend", "member_bans", "outsider_bans", "focal_identities", "resets_by_member", "overlap", "partially_staggered"):
            assert f in v
        assert len(v["resets_by_member"]) == 2
    assert ctr["x1_staggered"]["partially_staggered"] is False and ctr["x1_staggered"]["overlap"] == 0


def test_stage_list_runs_only_the_listed_stages(tmp_path):
    o = {"stage": "search,bank", "rules": "B3", "families": "X5-AG", "sizes": "1", "workers": 1, "out": str(tmp_path), "smoke": True}
    t = X.run(o)
    assert set(t) == {"search", "bank"} and (tmp_path / "bank").exists() and not (tmp_path / "reference").exists()
