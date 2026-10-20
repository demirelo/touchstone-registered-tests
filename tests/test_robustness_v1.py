"""Robustness v1 (plan docs/superpowers/plans/2026-10-21-theorem-and-robustness.md Task 3)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
import yaml

import scripts.explore_attackers as X
import scripts.robustness_v1 as R
from sim.cell import SeedCache, run_focal

ROOT = Path(__file__).resolve().parents[1]
DOC = yaml.safe_load((ROOT / "experiments/robustness-v1.yaml").read_text())


def test_family_of_covers_registered_and_exploratory_without_sealed_discovery(monkeypatch):
    import sim.registry as reg
    monkeypatch.setattr(reg, "available_families", lambda *a, **k: (_ for _ in ()).throw(AssertionError("sealed discovery")))
    for n in ("D2", "D2+H3", "X1-AH", "X6-SE"):
        assert X.family_of(n).name == n
    assert X.family_of("D2+H3").knobs[-2:] == ("x", "clip")


def test_manifest_exact_membership_292():
    specs = R.manifest_specs()
    ids = [s["id"] for s in specs]
    assert len(ids) == len(set(ids)) == 292
    by_axis = {}
    for s in specs:
        by_axis[s["axis"]] = by_axis.get(s["axis"], 0) + 1
    assert by_axis == {k: v for k, v in DOC["expected_counts"].items() if k != "total"}
    assert "headline_proposed_X6-SE_c5_staggered_median" in ids and "T400_B3_D2+H3_median" in ids and "beta0.02_B1_X4-RO_low" in ids
    assert not any("T100" in i and "X4-RO" in i for i in ids)


def test_diagnostics_exact_membership_72():
    from scripts.check_reset_theory import configurations
    d = DOC["diagnostics"]; conf = configurations()
    assert len(conf) == d["total"] == 72
    assert {(c["beta"], c["rule"], c["delta"], "reset" if c["reset"] else "wait") for c in conf} == \
        {(b, r, dl, p) for b in d["betas"] for r in d["rules"] for dl in d["deltas"] for p in d["plans"]}


def test_interpolated_provider_arrays_valid_and_frozen():
    for N in (5, 20):
        cfg = R.build_market(R.variant("N5J25" if N == 5 else "N20J100"))
        cfg.validate()
        assert [p.q_max for p in cfg.providers] == pytest.approx(DOC["provider_arrays"][N]["q_max"], abs=1e-9)
        assert [p.b for p in cfg.providers] == pytest.approx(DOC["provider_arrays"][N]["b"], abs=1e-9)
        assert all(p.a == 0.02 and p.k == 6 for p in cfg.providers)


def test_calibration_bound_to_variant_and_entry_ratio(tmp_path):
    from sim.cell import market_key
    v = R.variant("eta1")
    cfg = R.build_market(v); m = R.headline_m()
    assert cfg.e == pytest.approx(1.0 * m)
    cal = R.calibrate_market(v, out_dir=tmp_path, seeds=[4000])
    assert cal["market_key"] == market_key(cfg)
    assert R.calibrate_market(R.variant("headline"), out_dir=tmp_path) == "experiments/calibration.json"


def test_transfer_params_validated_and_labelled(tmp_path):
    job = X.job_for_x("B3", "D2", smoke=True, variant=R.variant("sigma0.10", position="median"))
    prov = job["provenance"]
    assert prov["param_transfer"] is True and prov["param_source_sha256"] and prov["variant"]["sigma"] == 0.10
    head = X.job_for_x("B3", "D2", smoke=True, variant=R.variant("headline", position="median"))
    assert head["provenance"]["param_transfer"] is False
    bad = tmp_path / "tuned"; bad.mkdir()
    d = json.loads((ROOT / "experiments/tuned/tuned_B3.json").read_text()); d["market_key"] = "deadbeef"
    (bad / "tuned_B3.json").write_text(json.dumps(d))
    with pytest.raises(SystemExit):
        R.load_transfer_params("B3", tuned_dir=bad)


def test_robust_cell_names_and_meta_from_job():
    job = X.job_for_x("proposed", "X6-SE", c=2, smoke=True, schedule="staggered", variant=R.variant("headline", position="median"))
    assert job["name"] == "headline_proposed_X6-SE_c2_staggered_median" and job["schedule"] == "staggered"
    j2 = X.job_for_x("B3", "D2+H3", smoke=True, variant=R.variant("beta0.02", position="low"))
    assert j2["name"] == "beta0.02_B3_D2+H3_low" and j2["beta"] == 0.02 and j2["position"] == "low"


def test_exploratory_family_refused_at_T_not_200():
    with pytest.raises(SystemExit):
        X.job_for_x("B3", "X4-RO", smoke=True, variant=R.variant("T100", position="median"))


def test_x6_staggered_profile_installs_staggered_members(monkeypatch):
    from sim.policies.exploratory import scheduled_resets
    job = X.job_for_x("B3", "X6-SE", c=2, smoke=True, schedule="staggered", variant=R.variant("headline", position="median"))
    seen = []
    orig = X.run_focal
    def spy(cell, factory, cache):
        if cell.others:
            focal = factory(); partners = [f() for _, f in cell.others]
            P = focal.P
            want = scheduled_resets(P, 2, 200, staggered=True)
            if focal.y:
                assert focal.sched == set(want[0]) and partners[0].sched == set(want[1])
            seen.append(1)
        return orig(cell, factory, cache)
    monkeypatch.setattr(X, "run_focal", spy)
    X.x_search(job)
    assert seen


def test_bank_embeds_d2_sources_for_h3_cells_and_refuses_foreign_groups():
    from sim.policies.families import embed_d2_in_h3, embed_d2_in_h3_exit, exact_key
    v = R.variant("headline", position="median")
    jd = X.job_for_x("B3", "D2", smoke=True, variant=v); jh = X.job_for_x("B3", "D2+H3", smoke=True, variant=v)
    rd = X.x_search(jd); rh = X.x_search(jh)
    doc = X.build_bank_doc("D2+H3", {jh["name"]: rh}, rules=["B3"], sizes=None, names=[jh["name"]], embed={jd["name"]: rd})
    keys = [exact_key(m["knobs"]) for m in doc["members"]]
    k0 = exact_key(embed_d2_in_h3(rd["attack"]["best_knobs"])); k1 = exact_key(embed_d2_in_h3_exit(rd["attack"]["best_knobs"]))
    assert k0 in keys and k1 in keys and keys.index(k0) < keys.index(k1)
    assert any(m["origin"].endswith("|x=0") for m in doc["members"]) and doc["embed_sources"][jd["name"]]
    doc2 = X.build_bank_doc("D2+H3", {jh["name"]: rh}, rules=["B3"], sizes=None, names=[jh["name"]])
    assert doc2["bank_hash"] != doc["bank_hash"]
    brec = X.x_bank(jh, rh, doc); ref = X.x_reference(jh, rh, brec)
    proj = [X.family_of("D2+H3").project(embed_d2_in_h3_exit(rd["attack"]["best_knobs"]))]
    assert any(exact_key(c["knobs"]) == exact_key(proj[0]) for c in ref["candidates"] if c["knobs"] is not None)
    other = X.job_for_x("B3", "D2", smoke=True, variant=R.variant("beta0.02", position="median"))
    with pytest.raises(SystemExit):
        X.build_bank_doc("D2+H3", {jh["name"]: rh}, rules=["B3"], sizes=None, names=[jh["name"]], embed={other["name"]: {**rd, "name": other["name"], "provenance": other["provenance"]}},
                         group=jh["bank_group"])


def test_entry_cost_charged_on_replacement():
    from sim.market import run_episode
    from sim.policies.honest import HonestMax
    from sim.calibrate import cell_config, load_calibration
    from tests.test_identity import ExitAt
    v = R.variant("eta1"); cfg = R.build_market(v)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[4] = ExitAt(30)
    res = run_episode(cfg, X.make_rule("B3", {"tol": 0.16, "L": 10}), pols, 2000)
    assert float(res.ledger.entry.sum()) == pytest.approx(cfg.e)


def test_doubling_cells_fixed_by_manifest():
    specs = R.manifest_specs()
    dbl = sorted(s["id"] for s in specs if s["doubling"])
    want = sorted(f"{v}_{r}_D2+H3_median" for v in DOC["doubling"]["variants"] for r in DOC["doubling"]["rules"])
    assert dbl == want


FROZEN = ["sim/market.py", "sim/search.py", "sim/reference.py", "sim/cell.py", "sim/registry.py", "sim/bank.py", "sim/ledger.py",
          "sim/mechanisms/proposed.py", "sim/mechanisms/second_score.py", "sim/mechanisms/posted.py", "sim/mechanisms/posted_audit.py",
          "sim/mechanisms/audit_random.py", "sim/mechanisms/base.py", "sim/policies/families.py", "sim/policies/identity.py",
          "scripts/sweep.py", "scripts/check_claim.py", "experiments/locked.yaml", "experiments/proposed.yaml",
          "experiments/tuned/tuned_B1.json", "experiments/tuned/tuned_B2.json", "experiments/tuned/tuned_B3.json"]


def test_frozen_files_unchanged():
    for p in FROZEN:
        tagged = subprocess.run(["git", "-C", str(ROOT), "show", f"final-eval-2026-10-20:{p}"], capture_output=True, check=True).stdout
        assert hashlib.sha256(tagged).hexdigest() == hashlib.sha256((ROOT / p).read_bytes()).hexdigest(), p


def test_smoke_end_to_end_changed_market(tmp_path):
    o = {"stage": "all", "variants": "N5J25", "rules": "B3", "families": "D2,D2+H3", "workers": 1, "out": str(tmp_path), "smoke": True}
    t = R.run(o)
    assert t["search"] > 0 and (tmp_path / "evaluate").exists()
    rep = json.loads((tmp_path / "report.json").read_text())
    assert {c["family"] for c in rep["cells"]} == {"D2", "D2+H3"} and all(c["variant"] == "N5J25" for c in rep["cells"])


# ---- final-review fixes ------------------------------------------------------------------------------------------------

def _staged(tmp_path, fams, stage):
    return {"stage": stage, "variants": "headline", "rules": "B3", "families": fams, "workers": 1, "out": str(tmp_path), "smoke": True}


def test_family_filtered_bank_uses_manifest_dependency_jobs_and_report_needs_doubling(tmp_path):
    R.run(_staged(tmp_path, "D2", "search"))
    R.run(_staged(tmp_path, "D2+H3", "search,bank"))                # D2 sources outside the family selection are found and valid
    bank = json.loads((tmp_path / "bank_headline_D2+H3_median.json").read_text())
    assert bank["embed_sources"] and bank["embedding_sha256"]


def test_changed_group_member_invalidates_bank_consumers(tmp_path):
    o = {"stage": "search,bank,reference", "variants": "headline", "rules": "B3", "families": "D2,D2+H3", "workers": 1, "out": str(tmp_path), "smoke": True}
    R.run(o)
    p = tmp_path / "search" / "headline_B3_D2_median.json"; d = json.loads(p.read_text())
    d["attack"]["best_f"] += 1.0; p.write_text(json.dumps(d))       # a D2 source of the D2+H3 bank changes; the D2+H3 search does not
    jobs = R.jobs_for([s for s in R.manifest_specs() if s["id"] == "headline_B3_D2+H3_median"], True)
    R.assign_banks(jobs, R.manifest_specs(), True, selected=jobs)
    with pytest.raises(SystemExit):
        X.verify_bank_group(tmp_path, jobs[0])


def test_report_requires_validated_doubling_records(tmp_path):
    specs = [s for s in R.manifest_specs() if s["id"] == "beta0.02_B3_D2+H3_median"]
    assert specs[0]["doubling"]
    o = {"stage": "search,bank,reference,evaluate", "variants": "beta0.02", "rules": "B3", "families": "D2,D2+H3", "workers": 1, "out": str(tmp_path), "smoke": True}
    R.run(o)
    with pytest.raises(SystemExit):
        R.run({**o, "stage": "report"})                              # the manifest-selected doubling record is missing
    R.run({**o, "stage": "doubling,report"})
    rep = json.loads((tmp_path / "report.json").read_text())
    assert any(c["doubling_delta"] is not None for c in rep["cells"] if c["cell"] == "beta0.02_B3_D2+H3_median")


def test_robust_x6_cells_keep_matched_timing_controls():
    job = X.job_for_x("B3", "X6-SE", c=2, smoke=True, schedule="synchronised", variant=R.variant("headline", position="median"))
    rec = X.x_search(job); ref = X.x_reference(job, rec, None); ev = X.x_evaluate(job, ref)
    k = ref["attack_knobs"]
    if k.get("y"):
        assert {"x1_synchronised", "x1_staggered", "x0_synchronised", "x0_staggered"} & set(ev["controls"])
    else:
        assert "note" in ev["controls"]
