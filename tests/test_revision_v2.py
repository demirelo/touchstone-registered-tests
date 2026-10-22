"""The v2 runner (plan Task 11): contexts, the common reference menu, dependency and freeze order, acceptance, resume,
doubling, cross-evaluation, the in-process salt, and the CLI. Smoke budgets on dev0; the freeze requirements of the
template context are narrowed to one rule's two menu searches and its reference so a complete context is cheap."""
import json
import os
from pathlib import Path

import numpy as np
import pytest

import sim.manifest_v2 as MAN
from sim.cell import SeedCache, run_focal
from sim.policies.x7 import corner_vectors as _cv
from sim.search import ArchiveEntry, SearchResult

CTX = "dev0@rho0.2"
TEMPLATE = "fresh0@rho0.2"
CRED = {"cred": {"variant": "thr", "K": 6, "M": None}}


def _required(ctx, cuts=0, h4_excluded=False):
    if ctx == TEMPLATE:
        return [f"{TEMPLATE}|F111|D2+H3|profit", f"{TEMPLATE}|F111|X7-SC|profit", f"reference/{TEMPLATE}/F111"]
    return MAN.__dict__["_real_required"](ctx, cuts, h4_excluded)


MAN._real_required = MAN.required


def _patch(mp):
    import scripts.revision_v2 as RV
    mp.setattr(MAN, "required", _required)
    mp.setattr(MAN, "bank_rules", lambda ctx, fam, cuts=0, h4_excluded=False: [])
    mp.setattr(RV, "corner_vectors", lambda fam: _cv(fam)[:8])
    return RV


@pytest.fixture(autouse=True)
def patched(monkeypatch):
    return _patch(monkeypatch)


@pytest.fixture(scope="module")
def ctx_dir(tmp_path_factory):
    with pytest.MonkeyPatch.context() as mp:
        RV = _patch(mp)
        out = tmp_path_factory.mktemp("rv2")
        mkt = RV.market("dev0", RV.DEV_ROOT, 0.2, dev=True, smoke=True)
        jobs = [RV.job(mkt, "F111", f, smoke=True) for f in ("D2+H3", "X7-SC")]
        RV.run("search", jobs, out); RV.run("reference", jobs, out); RV.run("freeze", jobs, out)
        return out, jobs


def _jobs(RV):
    mkt = RV.market("dev0", RV.DEV_ROOT, 0.2, dev=True, smoke=True)
    return [RV.job(mkt, "F111", f, smoke=True) for f in ("D2+H3", "X7-SC")]


def _hashes(out):
    from sim.records_v2 import sha_file
    return {str(p): sha_file(p) for p in Path(out).rglob("*.json") if "doubling" not in p.parts and "evaluate" not in p.parts}


def test_job_provenance_and_context(patched):
    RV = patched
    a = RV.market("dev0", RV.DEV_ROOT, 0.2, dev=True, smoke=True); b = RV.market("dev0", RV.DEV_ROOT, 1.0, dev=True, smoke=True)
    assert (a["context"], b["context"]) == ("dev0@rho0.2", "dev0@rho1")
    assert RV.path_of(Path("o"), f"reference/{a['context']}/F111") != RV.path_of(Path("o"), f"reference/{b['context']}/F111")
    j = RV.job(a, "F111", "D2+H3", smoke=True)
    assert set(j["provenance"]) >= {"git_commit", "runner_sha256", "cfg_sha256", "salt_sha256", "root", "seeds_train", "seeds_eval", "budget", "rule_params_sha256"}
    assert j["budget"] == [1, 16, 1, 2] and RV.job(a, "F111", "X7-SC", smoke=True)["budget"] == [1, 32, 1, 2]


def test_reference_menu_is_union_of_two_searches(ctx_dir):
    out, jobs = ctx_dir
    rec = json.loads((Path(out) / "reference" / CTX / "F111.json").read_text())
    fams = [c["family"] for c in rec["candidates"]]
    assert set(fams) <= {None, "D2+H3", "X7-SC"} and "X7-SC" in fams and "D2+H3" in fams
    cats = [("bank" if c["name"].startswith("bank_") else c["name"]) for c in rec["candidates"]]
    order = {n: i for i, n in enumerate(("abstain", "honest_max", "twin_search", "attack_projection", "archive_clip1", "archive_truthful_clip0", "bank"))}
    keys = [(order[c], 0 if f in (None, "D2+H3") else 1) for c, f in zip(cats, fams)]
    assert keys == sorted(keys)


def test_reference_survives_resume(ctx_dir, patched):
    RV = patched; out, jobs = ctx_dir
    rec = json.loads((Path(out) / "reference" / CTX / "F111.json").read_text())
    cand = RV.cand_from_json(rec["candidates"][rec["choice"]])
    fr = run_focal(RV.train_cell(jobs[0]), cand.policy_factory, SeedCache())
    assert np.allclose(fr.normalized, rec["per_seed_normalized"])


def test_bank_group_follows_effective_manifest(monkeypatch):
    import scripts.revision_v2 as RV
    monkeypatch.setattr(MAN, "bank_rules", MAN.__dict__["bank_rules"])
    from importlib import reload
    M = reload(MAN)
    assert len(M.bank_rules(RV.manifest_ctx("headline@rho1"), "D2+H3")) == 5
    assert len(M.bank_rules(RV.manifest_ctx("fresh3@rho0.2"), "X7-SC", cuts=4)) == 11
    assert len(M.bank_rules(RV.manifest_ctx("dev0@rho0.2"), "D2+H3")) == 12


def test_x7_uses_769_controls_and_embedded_incumbent(monkeypatch):
    import scripts.revision_v2 as RV
    from sim.policies.x7 import corner_vectors, x7_family
    monkeypatch.setattr(RV, "corner_vectors", corner_vectors)
    calls = []

    class Stub:
        def eval_knobs(self, k, source="search"):
            calls.append(k); return 0.0
    fam = x7_family(200, 10)
    assert len(RV.controls(Stub(), fam)) == 769 and len(calls) == 769
    seen = {}
    monkeypatch.setattr(RV, "cma_search", lambda obj, fam, st, seed, incumbents=None, starts=None: seen.update(incumbents or {}) or "res")
    tw = type("T", (), {"best_knobs": {"a": 1}})()
    RV.search_family(None, fam, None, None, tw, {"embedded_h3": {"b": 2}})
    assert set(seen) == {"twin_best", "honest_point", "embedded_h3"}


def test_x7_search_needs_d2h3_first(tmp_path, patched):
    RV = patched; jobs = _jobs(RV)
    with pytest.raises(SystemExit):
        RV.run("search", [jobs[1]], tmp_path)


def test_dependent_stage_requires_reference(tmp_path, patched):
    RV = patched
    mkt = RV.market("dev0", RV.DEV_ROOT, 0.2, dev=True, smoke=True)
    with pytest.raises(SystemExit):
        RV.run("dependent", [RV.job(mkt, "F111", "D2+H3", "W1", smoke=True)], tmp_path)


def test_freeze_refuses_incomplete_manifest(tmp_path, patched):
    RV = patched; jobs = _jobs(RV)
    RV.run("search", jobs[:1], tmp_path)
    with pytest.raises(SystemExit):
        RV.run("freeze", jobs, tmp_path)
    assert not (tmp_path / "freeze" / f"{CTX}.json").exists()


def test_evaluate_refuses_before_final_freeze(tmp_path, patched, monkeypatch):
    RV = patched; jobs = _jobs(RV)
    monkeypatch.setattr(RV, "evaluate_gain", lambda *a, **k: pytest.fail("an episode ran"))
    with pytest.raises(SystemExit):
        RV.run("evaluate", jobs, tmp_path)


def test_freeze_hash_mismatch_refuses(ctx_dir, patched, tmp_path):
    import shutil
    RV = patched; out, jobs = ctx_dir
    d = tmp_path / "copy"; shutil.copytree(out, d)
    fr = json.loads((d / "freeze" / f"{CTX}.json").read_text()); r = next(iter(fr["records"])); fr["records"][r] = "0" * 64
    (d / "freeze" / f"{CTX}.json").write_text(json.dumps(fr))
    with pytest.raises(SystemExit):
        RV.accept(CTX, jobs, d)


def test_accept_refuses_supplied_incomplete_freeze(ctx_dir, patched, tmp_path, monkeypatch):
    import shutil
    RV = patched; out, jobs = ctx_dir
    d = tmp_path / "copy"; shutil.copytree(out, d)
    fr = json.loads((d / "freeze" / f"{CTX}.json").read_text()); fr["records"].pop(f"reference/{CTX}/F111")
    (d / "freeze" / f"{CTX}.json").write_text(json.dumps(fr))
    monkeypatch.setattr(RV, "evaluate_gain", lambda *a, **k: pytest.fail("an episode ran"))
    with pytest.raises(SystemExit):
        RV.run("evaluate", jobs, d)


def test_accept_refuses_stale_upstream(ctx_dir, patched, tmp_path):
    import shutil
    from sim.records_v2 import sha_file, write
    RV = patched; out, jobs = ctx_dir
    d = tmp_path / "copy"; shutil.copytree(out, d)
    p = RV.path_of(d, jobs[0]["id"]); rec = json.loads(p.read_text()); rec["attack"]["best_f"] += 1.0; write(p, rec)
    fr = json.loads((d / "freeze" / f"{CTX}.json").read_text()); fr["records"][jobs[0]["id"]] = sha_file(p)     # a freeze updated to the new file
    (d / "freeze" / f"{CTX}.json").write_text(json.dumps(fr))
    with pytest.raises(SystemExit):
        RV.accept(CTX, jobs, d)                                # the reference's upstream hash no longer matches


def test_accept_and_evaluate_on_complete_context(ctx_dir, patched):
    RV = patched; out, jobs = ctx_dir
    RV.accept(CTX, jobs, out)
    res = RV.run("evaluate", jobs, out)
    rec = json.loads(RV.eval_path(out, jobs[0]["id"]).read_text())
    assert set(res.values()) <= {"done", "skipped"} and len(rec["gain"]) == 2


def test_truncated_record_is_rerun(tmp_path, patched):
    RV = patched; jobs = _jobs(RV)
    RV.run("search", jobs[:1], tmp_path)
    p = RV.path_of(tmp_path, jobs[0]["id"]); p.write_text(p.read_text()[:50])
    assert RV.run("search", jobs[:1], tmp_path)[jobs[0]["id"]] == "done" and json.loads(p.read_text())["stage"] == "search"


def test_doubling_reports_and_labels(patched):
    RV = patched
    assert RV.doubling_report("profit", {"attack_f": 0.1, "ref_f": 0.0}, {"attack_f": 0.105, "ref_f": 0.0})["incomplete"] is True
    assert RV.doubling_report("profit", {"attack_f": 0.1, "ref_f": 0.0}, {"attack_f": 0.1049, "ref_f": 0.0})["incomplete"] is False
    r = RV.doubling_report("w1", {"eff": None, "feasible": False}, {"eff": 0.8, "feasible": True})
    assert r["feasibility_transition"] and r["incomplete"]
    assert RV.doubling_report("welfare", {"eff": 0.9}, {"eff": 0.894})["incomplete"] is True
    assert RV.doubling_report("coalition", {"f": 0.3}, {"f": 0.302})["incomplete"] is False


def test_doubling_executes_full_budget_new_seeds(patched, monkeypatch):
    RV = patched
    from dataclasses import replace
    from sim.locked import load_locked
    from sim.search import settings_from_locked
    st = settings_from_locked(load_locked())
    seen = {}

    def fake(obj, fam, settings, seed, incumbents=None, starts=None):
        seen.update(seed=seed, restarts=settings.restarts, evals=settings.evals_per_restart, keys=set(obj.archive), inc=incumbents)
        return "new"
    monkeypatch.setattr(RV, "cma_search", fake)
    old = ArchiveEntry(knobs={"a": 1.0}, f=0.1, per_seed_profit=np.zeros(1), per_seed_normalized=np.zeros(1), inflated=False, source="x")
    orig = SearchResult(best_x=np.zeros(1), best_knobs={"a": 1.0}, best_f=0.1, best_source="r", restart_bests=[], evals=1, trace=[],
                        incumbent_scores={}, projection_f=0.0, replaced_by_projection=False, archive={(("a", 1.0),): old})
    obj = type("O", (), {"archive": {}})()
    assert RV.continue_search(obj, None, st, orig) == "new"
    assert seen["seed"] == 1 + st.restarts and seen["restarts"] == st.restarts and seen["evals"] == st.evals_per_restart
    assert (("a", 1.0),) in seen["keys"] and seen["inc"] == {"previous_best": {"a": 1.0}}


def test_doubling_reference_only_change(patched):
    r = patched.doubling_report("profit", {"attack_f": 0.1, "ref_f": 0.0}, {"attack_f": 0.1, "ref_f": 0.01})
    assert r["attack_change"] == 0.0 and r["reference_change"] == pytest.approx(0.01) and r["incomplete"]


def test_doubling_does_not_touch_frozen_records(ctx_dir, patched):
    RV = patched; out, jobs = ctx_dir
    before = _hashes(out)
    res = RV.run("doubling", jobs[:1], out)
    assert res[jobs[0]["id"]] in ("done", "skipped") and _hashes(out) == before
    rec = json.loads((Path(out) / "doubling" / (RV._safe(jobs[0]["id"]) + ".json")).read_text())
    assert {"attack_change", "reference_change", "incomplete"} <= set(rec)


def test_cross_evaluation_matrix_shape(ctx_dir, patched):
    from sim.records_v2 import write
    RV = patched; out, jobs = ctx_dir
    write(RV.path_of(out, f"bank/{CTX}/D2+H3"), {"stage": "bank", "attacks": {"F111": json.loads(RV.path_of(out, jobs[0]["id"]).read_text())["attack"]["best_knobs"]}})
    rec = RV.stage_cross(CTX, "D2+H3", jobs, out)
    n = len(rec["rules"])
    assert n == 1 and len(rec["matrix"]) == n and all(len(r) == n for r in rec["matrix"])


def test_resume_skips_valid_and_refuses_foreign(ctx_dir, patched):
    RV = patched; out, jobs = ctx_dir
    assert RV.run("search", jobs, out) == {j["id"]: "skipped" for j in jobs}
    foreign = dict(jobs[0]); foreign["provenance"] = {**jobs[0]["provenance"], "git_commit": "other"}
    with pytest.raises(SystemExit):
        RV.run("search", [foreign], out)


def test_fresh_root_installs_salt_in_process(tmp_path, monkeypatch, patched):
    RV = patched
    from tests._v2_profiles import CFG, fingerprint, run_full
    from sim.rules_v2 import make_rule
    monkeypatch.delenv("TOUCHSTONE_IDENTITY_SALT", raising=False)
    a = run_full(CFG, make_rule("F111"), "replacement", 2000)
    p = RV.install_salt("ab" * 32, tmp_path)
    try:
        assert os.environ["TOUCHSTONE_IDENTITY_SALT"] == str(p) and p.read_text() == __import__("sim.instances", fromlist=["x"]).identity_salt_hex("ab" * 32)
        b = run_full(CFG, make_rule("F111"), "replacement", 2000)
        assert fingerprint(a) != fingerprint(b)
    finally:
        monkeypatch.delenv("TOUCHSTONE_IDENTITY_SALT", raising=False)


def test_cli_accepts_pod_arguments(tmp_path, patched):
    assert patched.main(["--stage", "search", "--select", "x", "--workers", "2", "--out", str(tmp_path), "--dev", "--smoke"]) == 0
