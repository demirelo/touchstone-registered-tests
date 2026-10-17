import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from sim.claimcheck import (PASS, FAIL, INCONCLUSIVE, decide, combine_all, combine_any, h1_frame, h1_proposed_reason, required_families, evaluate_claim,
                            tree_changes, allowed, verify_lock, verify_freeze, verify_records, verify_h1_summary, verify_coverage_report, check_proposed_module)
from sim.coverage import ENDPOINTS, endpoint_key
from sim.locked import load_locked, settings_hash

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = {"bootstrap_resamples": 500, "bootstrap_seed": 1}


def coverage(method20="percentile", method10="t", h1="confirmatory", par="percentile_n20", n_final=20, drop=(), method40=None):
    sides = {endpoint_key(s, side, lv, n): m for n, m in ((10, method10), (20, method20), (40, method40)) for s, side, lv in ENDPOINTS}
    for k in drop:
        sides[k] = None
    return {"admitted_sides": sides, "consequences": {"h1": h1, "parametrized": par, "final_eval_n": n_final}}


def test_decide_pass_fail_inconclusive():
    rng = np.random.default_rng(0); cov = coverage()
    hi = rng.normal(0.97, 0.01, size=20); lo = rng.normal(0.5, 0.01, size=20); mid = rng.normal(0.90, 0.05, size=20)
    assert decide(hi, "eff", "lower", 0.95, 0.90, cov, SETTINGS).status == PASS
    assert decide(lo, "eff", "lower", 0.95, 0.90, cov, SETTINGS).status == FAIL
    assert decide(mid, "eff", "lower", 0.95, 0.90, cov, SETTINGS).status == INCONCLUSIVE
    assert decide(lo, "gain", "upper", 0.95, 0.30, cov, SETTINGS).status == FAIL and decide(lo * 0.1, "gain", "upper", 0.95, 0.30, cov, SETTINGS).status == PASS
    cov2 = coverage(drop=(endpoint_key("eff", "lower", 0.95, 20),))
    v = decide(hi, "eff", "lower", 0.95, 0.90, cov2, SETTINGS)
    assert v.status == INCONCLUSIVE and "not admitted" in v.note
    assert decide(lo, "eff", "lower", 0.95, 0.90, cov2, SETTINGS).status == FAIL          # the opposite side is still admitted
    assert decide(hi[:5], "eff", "lower", 0.95, 0.90, cov, SETTINGS, n=20).status == INCONCLUSIVE
    assert combine_all([PASS, PASS]) == PASS and combine_all([PASS, INCONCLUSIVE]) == INCONCLUSIVE and combine_all([FAIL, INCONCLUSIVE]) == FAIL
    assert combine_any([FAIL, PASS]) == PASS and combine_any([FAIL, FAIL]) == FAIL and combine_any([FAIL, INCONCLUSIVE]) == INCONCLUSIVE


def frame(rule, family, gain, eff, eff_clip, audit, budget=1.0, n=20, position="median"):
    rng = np.random.default_rng(abs(hash((rule, family))) % 2**32)
    return pd.DataFrame({"rule": rule, "family": family, "position": position, "seed": np.arange(n), "beta": 0.05, "sstar": 10.0,
                         "gain": gain + rng.normal(0, 0.01, n), "eff_attack": eff + rng.normal(0, 0.005, n), "eff_clip": eff_clip + rng.normal(0, 0.005, n),
                         "audit_cost_attack": audit, "budget": budget})


def good_h2():
    return pd.concat([frame("R", "H2", 0.05, 0.97, 0.98, 0.5), frame("B2", "H2", 1.5, 0.80, 0.95, 0.5), frame("B3", "H2", 0.2, 0.85, 0.97, 0.5)], ignore_index=True)


def good_h1():
    return pd.concat([pd.DataFrame({"rule": r, "beta": 0.05, "rep": range(10), "eval_seed": range(10), "sstar": 5.0, "reference": "honest_max", "gain": g,
                                    "eff_attack": e, "eff_clip": e + 0.01, "audit_cost_attack": 0.1, "budget": 0.25, "invalid": 0})
                      for r, g, e in (("R", 0.02, 0.96), ("B2", 1.4, 0.8), ("B3", 1.3, 0.8))], ignore_index=True)


def summary(inconclusive=(), comp=None):
    return {"cells": {f"{r}|0.05": {"inconclusive": r in inconclusive} for r in ("R", "B2", "B3")}, "comprehension": comp or {"R": 7, "B2": 7, "B3": 6}}


def test_required_families_come_from_the_lock_not_the_inputs():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    assert required_families(coverage()) == ["H2", "H1"] and required_families(coverage(h1="exploratory")) == ["H2"]
    r = evaluate_claim(good_h2(), None, coverage(), lk, "R")                      # H1 required but absent
    assert r["confirmatory"] == ["H2", "H1"] and r["rule_clause"]["H1"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE
    r = evaluate_claim(None, good_h1(), coverage(), lk, "R", h1_summary=summary())  # H2 absent
    assert r["rule_clause"]["H2"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE
    r = evaluate_claim(good_h2(), good_h1(), coverage(h1="exploratory"), lk, "R")
    assert r["confirmatory"] == ["H2"] and r["claim"] == PASS and "exploratory" in r["h1_note"]
    r = evaluate_claim(good_h2(), good_h1(), coverage(method20=None, par="inconclusive", n_final=None), lk, "R", h1_summary=summary())
    assert r["rule_clause"]["H2"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE   # a failed parametrized remedy never drops H2


def test_claim_pass_fail_and_baseline_alternatives():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary())
    assert r["claim"] == PASS and r["baseline_clause"]["B2"]["status"] == PASS and r["baseline_clause"]["B3"]["status"] == PASS and r["n"] == {"H2": 20, "H1": 10}
    bad = good_h2(); bad.loc[bad.rule == "R", "gain"] += 1.0
    assert evaluate_claim(bad, good_h1(), coverage(), lk, "R", h1_summary=summary())["claim"] == FAIL
    over = good_h2(); over.loc[(over.rule == "R") & (over.seed == 3), "audit_cost_attack"] = 2.0
    assert evaluate_claim(over, good_h1(), coverage(), lk, "R", h1_summary=summary())["rule_clause"]["H2"]["audit"] == FAIL
    weak = good_h2(); weak.loc[weak.rule == "B2", "gain"] = 0.2; weak.loc[weak.rule == "B2", "eff_clip"] = weak.loc[weak.rule == "B2", "eff_attack"] + 0.005
    weak_h1 = good_h1(); weak_h1.loc[weak_h1.rule == "B2", "gain"] = 0.1; weak_h1.loc[weak_h1.rule == "B2", "eff_clip"] = weak_h1.loc[weak_h1.rule == "B2", "eff_attack"]
    assert evaluate_claim(weak, weak_h1, coverage(), lk, "R", h1_summary=summary())["baseline_clause"]["B2"]["status"] == FAIL
    # headline position: only rows at the rule's headline position enter
    two = pd.concat([good_h2(), frame("R", "H2", 5.0, 0.5, 0.5, 0.5, position="high")], ignore_index=True)
    assert evaluate_claim(two, good_h1(), coverage(), lk, "R", h1_summary=summary(), h2_headline={"R": "median"})["claim"] == PASS
    assert evaluate_claim(two, good_h1(), coverage(), lk, "R", h1_summary=summary(), h2_headline={"R": "high"})["claim"] == FAIL


def test_h1_invalidity_demotion_and_not_expressible():
    lk = load_locked(); lk = dict(lk, intervals=dict(lk["intervals"], **SETTINGS))
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary(inconclusive=("R",)))
    assert r["rule_clause"]["H1"]["status"] == INCONCLUSIVE and r["claim"] == INCONCLUSIVE
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary(inconclusive=("B2",)))
    assert r["baseline_clause"]["B2"]["pairs"]["H1|gain"].status == INCONCLUSIVE and r["baseline_clause"]["B2"]["status"] == PASS   # B2 still passes through H2
    r = evaluate_claim(good_h2(), good_h1(), coverage(), lk, "R", h1_summary=summary(), demoted={"R|H2"})
    assert r["rule_clause"]["H2"]["status"] == INCONCLUSIVE and "demoted" in r["rule_clause"]["H2"]["eff"].note
    rec = {"allocation_order": "ascending bid", "eligibility": "not expressible", "payment": "the bid", "audit_selection": "none",
           "audit_tolerance": "none", "failed_audit": "none", "ban_length": "none", "holdback": "none"}
    assert h1_proposed_reason("R", summary(), rec, 0.05) == "not expressible"
    assert h1_proposed_reason("R", summary(comp={"R": 5, "B2": 7, "B3": 7, "B1": 3}), None, 0.05) == "comprehension"     # ruling D11: min of B2 and B3
    assert h1_proposed_reason("R", summary(comp={"R": 6, "B2": 7, "B3": 7}), None, 0.05) is None
    assert h1_proposed_reason("R", summary(inconclusive=("R",)), None, 0.05) == "invalid repetitions"
    assert h1_proposed_reason("R", {"cells": {}, "comprehension": {}}, None, 0.05) == "missing"
    f = h1_frame(good_h1()); assert set(f.family) == {"H1"} and "seed" in f


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "-c", "commit.gpgsign=false", "-c", "tag.gpgsign=false", *args],
                          cwd=repo, check=True, capture_output=True, text=True).stdout


def make_repo(tmp_path):
    repo = tmp_path / "repo"; (repo / "sim" / "mechanisms").mkdir(parents=True); (repo / "experiments").mkdir(); (repo / "docs").mkdir()
    git(repo, "init", "-q")
    (repo / "sim" / "market.py").write_text("frozen = 1\n"); (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 0\n")
    (repo / "experiments" / "proposed.yaml").write_text("a: 1\n"); (repo / "experiments" / "proposed_describe.yaml").write_text("b: 1\n")
    (repo / "docs" / "note.md").write_text("hi\n"); (repo / "docs" / "odd name.md").write_text("quoted path\n")
    git(repo, "add", "."); git(repo, "commit", "-q", "-m", "lock"); git(repo, "tag", "lock-test")
    return repo


ALLOW = ["sim/mechanisms/proposed.py", "experiments/proposed.yaml", "experiments/proposed_describe.yaml", "experiments/cache/h1/", "scripts/plot.py", "docs/", "sealed/", "sealed/patches/"]


def test_check_claim_refuses_modified_frozen_file(tmp_path):
    repo = make_repo(tmp_path)
    assert verify_lock(repo, "lock-test", ALLOW) == []
    assert tree_changes(repo, "lock-test") == {}
    (repo / "docs" / "odd name.md").write_text("edited\n")
    assert tree_changes(repo, "lock-test") == {"docs/odd name.md": "M"} and verify_lock(repo, "lock-test", ALLOW) == []   # quoted path parsed; docs/ is allow-listed
    (repo / "experiments" / "cache" / "h1" / "anthropic").mkdir(parents=True); (repo / "experiments" / "cache" / "h1" / "anthropic" / "x.json").write_text("{}")
    git(repo, "add", "experiments/cache/h1"); assert verify_lock(repo, "lock-test", ALLOW) == []                        # the post-lock H1 cache is allow-listed
    assert allowed("docs/x/y.md", ALLOW) and allowed("sim/mechanisms/proposed.py", ALLOW) and not allowed("sim/market.py", ALLOW)
    (repo / "sim" / "market.py").write_text("frozen = 2\n")
    probs = verify_lock(repo, "lock-test", ALLOW)
    assert len(probs) == 1 and "sim/market.py" in probs[0] and "changed" in probs[0]
    (repo / "sim" / "market.py").write_text("frozen = 1\n")
    (repo / "sim" / "new.py").write_text("n = 1\n"); git(repo, "add", "sim/new.py")
    assert any("sim/new.py" in p and "new" in p for p in verify_lock(repo, "lock-test", ALLOW))
    git(repo, "rm", "-q", "--cached", "sim/new.py"); (repo / "sim" / "new.py").unlink()
    (repo / "sim" / "market.py").unlink()
    assert any("sim/market.py" in p and "deleted" in p for p in verify_lock(repo, "lock-test", ALLOW))


def test_check_claim_accepts_allow_listed_changes_after_freeze(tmp_path):
    from sim.sealed import bundle_hash
    repo = make_repo(tmp_path)
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 1\n"); (repo / "docs" / "note.md").write_text("changed\n")
    (repo / "scripts").mkdir(); (repo / "scripts" / "plot.py").write_text("p = 1\n")
    sealed = repo / "sealed"; sealed.mkdir(); (sealed / "h1_prompt.txt").write_text("prompt\n"); (sealed / "patches").mkdir()
    git(repo, "add", "."); git(repo, "commit", "-q", "-m", "freeze"); git(repo, "tag", "freeze-test")
    assert verify_lock(repo, "lock-test", ALLOW) == []
    lk = {"sealed_bundle_sha256": bundle_hash(sealed), "allow_list": ALLOW}
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 2\n")
    assert any("proposed.py" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))
    (repo / "sim" / "mechanisms" / "proposed.py").write_text("x = 1\n")
    (sealed / "__pycache__").mkdir(); (sealed / "__pycache__" / "x.pyc").write_bytes(b"\x00")
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []                              # import artifacts never change the bundle hash
    (sealed / "h1_prompt.txt").write_text("tampered\n")
    assert any("bundle" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))
    (sealed / "h1_prompt.txt").write_text("prompt\n")
    (sealed / "patches" / "fix.diff").write_text("--- a\n+++ b\n")
    assert any("patches" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))        # unlogged patch
    (sealed / "patches" / "log.json").write_text(json.dumps({"fix.diff": {"sha256": hashlib.sha256(b"--- a\n+++ b\n").hexdigest(), "replaces": "h1_prompt.txt", "demotes": ["R|H2"]},
                                                              "gone.diff": {"sha256": "00" * 32, "replaces": "h1_prompt.txt", "demotes": []}}))
    assert any("gone.diff" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))      # a logged patch must exist
    (sealed / "patches" / "log.json").write_text(json.dumps({"fix.diff": {"sha256": hashlib.sha256(b"--- a\n+++ b\n").hexdigest(), "replaces": "h1_prompt.txt", "demotes": ["R|H2"]}}))
    assert verify_freeze(repo, "freeze-test", lk, ALLOW) == []
    from sim.sealed import demoted_cells
    assert demoted_cells(sealed) == {"R|H2"}
    (repo / "experiments" / "proposed_describe.yaml").unlink()
    assert any("proposed_describe.yaml" in p for p in verify_freeze(repo, "freeze-test", lk, ALLOW))   # frozen files must exist


def test_verify_records_summary_and_coverage_report(tmp_path):
    from scripts.sweep import check_record
    lk = load_locked(); lk = dict(lk, identity_salt_sha256="ab" * 32, sealed_bundle_sha256="ee" * 32,
                                  calibration={"T100": {"sha256": "cc" * 32}}, coverage_consequences={"final_eval_n": 3, "h1": "confirmatory", "parametrized": "percentile_n20"})
    job = {"spec": {"name": "c", "rule": "B2", "family": "H2", "beta": 0.05, "position": "median"}, "params": {"tol": 0.1}, "cfg": {"T": 200, "budget": 0.5}, "settings_hash": settings_hash(lk),
           "budget": [1, 2, 3, 4], "smoke": False, "salt_hash": "ab" * 32, "eval_namespace": "final_eval"}
    meta = {"rule": "B2", "family": "H2", "beta": 0.05, "position": "median", "budget": 0.5}
    good = {**{k: job[k] for k in ("spec", "params", "cfg", "settings_hash", "budget", "smoke", "salt_hash")}, "eval_namespace": "final_eval", "bundle_hash": "ee" * 32,
            "rows": [dict(meta, seed=s) for s in (7, 8, 9)]}
    seeds = [7, 8, 9, 10]
    assert verify_records([good], lk, {"c": job}, seeds) == []
    for bad in (dict(good, settings_hash="x"), dict(good, salt_hash="y"), dict(good, params={"tol": 0.2}), dict(good, cfg={"T": 100}), dict(good, eval_namespace="dev_val"),
                dict(good, smoke=True), dict(good, bundle_hash="00" * 32), dict(good, rows=[dict(meta, seed=s) for s in (8, 7, 9)]), dict(good, rows=[dict(meta, seed=s) for s in (7, 8)]),
                dict(good, rows=[dict(meta, seed=s) for s in (7, 8, 10)]), dict(good, rows=[dict(meta, seed=s, rule="proposed") for s in (7, 8, 9)]),
                dict(good, rows=[dict(meta, seed=s, budget=999.0) for s in (7, 8, 9)])):
        assert verify_records([bad], lk, {"c": job}, seeds) != []
    assert any("salt" in p for p in verify_records([dict(good, salt_hash="cd" * 32)], lk, {"c": dict(job, salt_hash="cd" * 32)}, seeds))   # the lock commitment, not only the job, binds the salt
    assert any("no job" in p for p in verify_records([dict(good, spec=dict(job["spec"], name="zz"))], lk, {"c": job}, seeds))
    prompt = tmp_path / "h1_prompt.txt"; prompt.write_text("sealed prompt")
    lk = dict(lk, tuned={"B2": "b2" * 32, "B3": "b3" * 32})
    summ = {"model": lk["h1"]["model"], "T": lk["h1"]["T"], "eval_namespace": "final_eval", "instructions_sha256": hashlib.sha256(b"sealed prompt").hexdigest(),
            "calibration_t100_sha256": "cc" * 32, "smoke": False, "partial": [], "comprehension": {"R": 7, "B2": 7, "B3": 7}, "tuned_sha256": {"B2": "b2" * 32, "B3": "b3" * 32},
            "cells": {f"{r}|0.05": {"inconclusive": False, "invalid_count": 0} for r in ("R", "B2", "B3")}}
    rows = pd.concat([pd.DataFrame({"rule": r, "beta": 0.05, "rep": range(10), "eval_seed": list(range(100, 110)), "invalid": 0, "T": lk["h1"]["T"], "model": lk["h1"]["model"]})
                      for r in ("R", "B2", "B3")], ignore_index=True)
    sealed_seeds = list(range(100, 140))
    assert verify_h1_summary(summ, rows, lk, prompt, sealed_seeds) == []
    for bad in (dict(summ, model=lk["h1"]["jev_model"]), dict(summ, T=5), dict(summ, eval_namespace="dev_val"), dict(summ, instructions_sha256="00" * 32),
                dict(summ, calibration_t100_sha256="dd" * 32), dict(summ, smoke=True), dict(summ, partial=["B2|0.05"]), dict(summ, comprehension={"R": 7, "B2": 7}),
                dict(summ, tuned_sha256={"B2": "00" * 32, "B3": "b3" * 32})):
        assert verify_h1_summary(bad, rows, lk, prompt, sealed_seeds) != []
    wrong_seeds = rows.copy(); wrong_seeds.loc[wrong_seeds.rule == "R", "eval_seed"] = 0
    assert verify_h1_summary(summ, wrong_seeds, lk, prompt, sealed_seeds) != []
    wrong_invalid = rows.copy(); wrong_invalid.loc[wrong_invalid.rule == "B2", "invalid"] = 1
    assert verify_h1_summary(summ, wrong_invalid, lk, prompt, sealed_seeds) != []
    lying = dict(summ, cells=dict(summ["cells"], **{"B2|0.05": {"inconclusive": False, "invalid_count": 10}}))
    assert any("contradicts" in p for p in verify_h1_summary(lying, wrong_invalid, lk, prompt, sealed_seeds))          # inconclusive must follow the count
    frac = rows.copy(); frac["invalid"] = 0.05
    assert any("binary" in p for p in verify_h1_summary(summ, frac, lk, prompt, sealed_seeds))
    assert any("column" in p for p in verify_h1_summary(summ, rows.drop(columns=["model"]), lk, prompt, sealed_seeds))
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{"name": f"c{i}"} for i in range(6)], "consequences": lk["coverage_consequences"]}
    data = json.dumps(rep, sort_keys=True, indent=1).encode(); (tmp_path / "cov.json").write_bytes(data)
    lk2 = dict(lk, coverage_report_sha256=hashlib.sha256(data).hexdigest())
    assert verify_coverage_report(tmp_path / "cov.json", lk2) == []
    assert verify_coverage_report(tmp_path / "cov.json", dict(lk2, coverage_report_sha256="00" * 32)) != []
    for bad in (dict(rep, admission_basis="smoke (not an admission)"), dict(rep, selection=[{"name": "c0"}] * 6)):
        (tmp_path / "bad.json").write_text(json.dumps(bad, sort_keys=True, indent=1))
        assert verify_coverage_report(tmp_path / "bad.json", dict(lk2, coverage_report_sha256=hashlib.sha256((tmp_path / "bad.json").read_bytes()).hexdigest())) != []


def test_patch_overlay_applies_logged_repairs_without_touching_the_bundle(tmp_path):
    from sim.sealed import bundle_hash, effective_path, verify_patches
    s = tmp_path / "sealed"; (s / "h2").mkdir(parents=True); (s / "patches").mkdir()
    (s / "h1_prompt.txt").write_text("original\n"); (s / "h2" / "family.py").write_text("ORIG = 1\n"); h = bundle_hash(s)
    assert effective_path(s, "h1_prompt.txt") == s / "h1_prompt.txt"
    (s / "patches" / "h1_prompt.txt").write_text("repaired\n")
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": hashlib.sha256(b"repaired\n").hexdigest(), "replaces": "h1_prompt.txt", "demotes": []}}))
    assert verify_patches(s) == [] and effective_path(s, "h1_prompt.txt") == s / "patches" / "h1_prompt.txt" and bundle_hash(s) == h
    assert effective_path(s, "h1_prompt.txt").read_text() == "repaired\n" and (s / "h1_prompt.txt").read_text() == "original\n"
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": "00" * 32, "replaces": "h1_prompt.txt", "demotes": []}}))
    assert verify_patches(s) != [] and effective_path(s, "h1_prompt.txt") == s / "h1_prompt.txt"            # an unverified patch is not applied
    (s / "patches" / "log.json").write_text(json.dumps({"h1_prompt.txt": {"sha256": hashlib.sha256(b"repaired\n").hexdigest(), "replaces": "nope.txt", "demotes": []}}))
    assert any("replaces" in p for p in verify_patches(s))
    (s / "final_eval_seeds.json").write_text("[1, 2, 3]"); (s / "patches" / "seeds.json").write_text("[9]")
    (s / "patches" / "log.json").write_text(json.dumps({"seeds.json": {"sha256": hashlib.sha256(b"[9]").hexdigest(), "replaces": "final_eval_seeds.json", "demotes": []}}))
    assert any("replaces" in p for p in verify_patches(s)) and effective_path(s, "final_eval_seeds.json") == s / "final_eval_seeds.json"   # the seeds are never repaired


def test_check_proposed_module_import_and_attribute_rules(tmp_path):
    good = tmp_path / "good.py"; good.write_text("from sim.mechanisms.base import Mechanism\nimport numpy as np\nimport math\n\ndef make(params):\n    return None\n")
    assert check_proposed_module(good, ROOT) == []
    bad = tmp_path / "bad.py"; bad.write_text("from sim.market import run_episode\nimport sim.search\n\ndef make(params):\n    return None\n")
    probs = check_proposed_module(bad, ROOT)
    assert any("sim.market" in p for p in probs) and any("sim.search" in p for p in probs)
    mut = tmp_path / "mut.py"; mut.write_text("import sim.policies.honest as h\nh.HonestMax.name = 'hacked'\n\ndef make(params):\n    return None\n")
    probs = check_proposed_module(mut, ROOT)
    assert any("sim.policies.honest" in p for p in probs)
    import sim.policies.honest as hm
    assert hm.HonestMax.name != "hacked"                                                  # the check restores what it can and reports
    code = tmp_path / "code.py"; code.write_text("from sim.mechanisms.base import Mechanism\n\ndef _nop(self, *a, **k):\n    return {}\n\nMechanism.allocate.__code__ = _nop.__code__\n\ndef make(params):\n    return None\n")
    assert any("Mechanism.allocate" in p for p in check_proposed_module(code, ROOT))      # function code counts as an attribute
    late = tmp_path / "late.py"; late.write_text("from sim.mechanisms.base import Mechanism\nM = Mechanism\n\ndef make(params):\n    M.late_flag = 1\n    return None\n")
    assert check_proposed_module(late, ROOT) == [] and any("Mechanism.late_flag" in p for p in check_proposed_module(late, ROOT, params={}))   # mutation at factory time through an unflagged alias
    direct = tmp_path / "direct.py"; direct.write_text("import sim.mechanisms.base as b\n\ndef make(params):\n    b.LATE = 1\n    return None\n")
    assert any("monkeypatching" in p for p in check_proposed_module(direct, ROOT))                       # an attribute assignment on an imported name is refused at the source
    dund = tmp_path / "dund.py"; dund.write_text("from sim.mechanisms.base import Offer\nOffer.__init__.__defaults__ = (9.9,)\n\ndef make(params):\n    return None\n")
    assert any("Offer.__init__" in p for p in check_proposed_module(dund, ROOT))                                        # constructor defaults count
    rel = tmp_path / "rel.py"; rel.write_text("from .base import Mechanism\n\ndef make(params):\n    return None\n")
    assert any("relative" in p.lower() or "not allowed" in p for p in check_proposed_module(rel, ROOT))
    dyn = tmp_path / "dyn.py"; dyn.write_text("m = __import__('sim.metrics')\n\ndef make(params):\n    return None\n")
    assert any("dynamic import" in p for p in check_proposed_module(dyn, ROOT))
    for src in ("exec('import sim.metrics as m')\n", "m = eval('__imp' + 'ort__(\"sim.metrics\")')\n", "m = getattr(__builtins__, '__import__')('sim.metrics')\n",
                "x = ().__class__.__base__.__subclasses__()\n", "name = '__imp' + 'ort__'\nm = getattr(object, name)\n"):
        f = tmp_path / "ref.py"; f.write_text(src + "\ndef make(params):\n    return None\n")
        assert check_proposed_module(f, ROOT) != []                                                  # exec, eval, dunder getattr, __builtins__, and dunder attribute chains are refused
    benign = tmp_path / "benign.py"; benign.write_text("from sim.mechanisms.base import Mechanism\n\nclass R:\n    def f(self):\n        return getattr(self, 'x', 0)\n\ndef make(params):\n    return None\n")
    assert check_proposed_module(benign, ROOT) == []                                                   # getattr with an ordinary literal name is fine


def test_check_claim_cli_synthetic_and_verify_only(tmp_path):
    good_h2().to_csv(tmp_path / "h2.csv", index=False); good_h1().to_csv(tmp_path / "h1.csv", index=False)
    (tmp_path / "cov.json").write_text(json.dumps(coverage())); (tmp_path / "s.json").write_text(json.dumps(summary()))
    cmd = [sys.executable, str(ROOT / "scripts" / "check_claim.py")]
    r = subprocess.run(cmd + ["--synthetic", "--h2-rows", str(tmp_path / "h2.csv"), "--h1-rows", str(tmp_path / "h1.csv"), "--h1-summary", str(tmp_path / "s.json"),
                              "--coverage-report", str(tmp_path / "cov.json"), "--proposed", "R", "--out", str(tmp_path / "verdict.json")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    assert json.loads((tmp_path / "verdict.json").read_text())["claim"] == "PASS" and "SYNTHETIC" in r.stdout
    r2 = subprocess.run(cmd + ["--h2-rows", str(tmp_path / "h2.csv"), "--coverage-report", str(tmp_path / "cov.json"), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r2.returncode == 2 and "synthetic" in (r2.stderr + r2.stdout).lower()           # CSV inputs without --synthetic are refused
    r3 = subprocess.run(cmd + ["--sweep-out", str(tmp_path), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r3.returncode == 2 and "verify-lock" in (r3.stderr + r3.stdout)                 # confirmatory mode needs both tags, the calibrations, the tuned dir, and the description
    repo = make_repo(tmp_path)
    r4 = subprocess.run(cmd + ["--verify-only", "--verify-lock", "lock-test", "--repo", str(repo), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r4.returncode == 0, r4.stderr
    (repo / "sim" / "market.py").write_text("frozen = 2\n")
    r5 = subprocess.run(cmd + ["--verify-only", "--verify-lock", "lock-test", "--repo", str(repo), "--proposed", "R"], capture_output=True, text=True, cwd=ROOT)
    assert r5.returncode == 2 and "sim/market.py" in r5.stderr


def test_module_check_catches_numpy_monkeypatching_and_runs_isolated(tmp_path):
    """Final review F2: a proposed module that patches numpy or scipy, or assigns an attribute of any imported module,
    is refused, and the check runs in a subprocess so the verdict process never imports the module."""
    import numpy as np
    from sim.claimcheck import check_proposed_module_isolated
    evil = tmp_path / "evil.py"
    evil.write_text("import numpy as np\n_q = np.quantile\nnp.quantile = lambda a, q, *k, **kw: _q(a, q, *k, **kw) - 10\n\ndef make(params):\n    return None\n")
    probs = check_proposed_module_isolated(evil, ROOT)
    assert probs and any("numpy" in p or "attribute" in p for p in probs)
    assert np.quantile(np.arange(5), 0.5) == 2.0                                          # this process is untouched
    sneaky = tmp_path / "sneaky.py"
    sneaky.write_text("import scipy.stats as st\n\ndef make(params):\n    st.t.ppf = lambda *a, **k: 0.0\n    return None\n")
    assert check_proposed_module_isolated(sneaky, ROOT, params={}) != []                 # factory-time patching of scipy
    good = tmp_path / "good.py"; good.write_text("from sim.mechanisms.base import Mechanism\nimport numpy as np\n\ndef make(params):\n    return np.sum([1])\n")
    assert check_proposed_module_isolated(good, ROOT, params={}) == []


def test_describe_record_file_must_match_the_rule_and_the_vocabulary():
    """Final review F5: the frozen proposed_describe.yaml is checked against the vocabulary and against the record of
    the rule the actor actually saw."""
    from sim.claimcheck import verify_describe_record
    from sim.mechanisms.posted_audit import PostedRandomAudit
    rule = PostedRandomAudit(0.2, 0.35, 0.5, tol=0.12, L=3)
    rec = rule.describe()
    assert verify_describe_record(dict(rec), rule) == []
    assert verify_describe_record(dict(rec, payment="the bid"), rule) != []                 # differs from the rule's record
    assert verify_describe_record(dict(rec, payment="we think about it"), rule) != []       # off-vocabulary
    assert verify_describe_record(dict(rec, note="x"), rule) != []                          # a key outside the fields


# ---- amendment 1: the H3 comparative clause -----------------------------------------------------------------------------

from sim.amendment import LIMITATION  # noqa: E402
from sim.claimcheck import evaluate_amendment, verify_amendment_report, verify_h3_records  # noqa: E402

LK = load_locked()
AMEND_FIXTURE = {"clause": {"family": "D2+H3", "position": "median", "beta": 0.05, "eff_min": 0.90, "gain_max": 0.30, "gain_reduction_min": 0.10,
                            "level_rule": 0.95, "level_comparative": 0.9875, "baselines": ["B2", "B3"], "n": 40, "requires_h2_rule_clause": True}}
REGISTERED_NAMES = [c["name"] for c in json.loads((ROOT / "experiments" / "coverage_cells.json").read_text())]


def ext_cov(admitted=True):
    m = "studentized" if admitted else None
    return {"admitted_sides": {"gain_diff|lower|0.9875|40": m, "gain_diff|upper|0.9875|40": m}, "consequences": {"h3_comparative": "confirmatory" if admitted else "exploratory"}}


def good_h3(gain_r=0.05, gain_b2=0.6, gain_b3=0.4, n=40, eff_r=0.97):
    return pd.concat([frame("R", "D2+H3", gain_r, eff_r, 0.98, 1.0, budget=2.0, n=n), frame("B2", "D2+H3", gain_b2, 0.87, 0.97, 1.0, budget=2.0, n=n),
                      frame("B3", "D2+H3", gain_b3, 0.97, 0.99, 1.0, budget=2.0, n=n)], ignore_index=True)


def test_amendment_decision_rule_and_h2_gate():
    cov = coverage(method20=None, par="studentized_n40", n_final=40, method40="studentized"); am = AMEND_FIXTURE
    r = evaluate_amendment(good_h3(), cov, ext_cov(), LK, am, "R", PASS)
    assert r["amended"] == PASS and r["comparative"]["status"] == PASS and r["absolute"]["status"] == PASS and r["note"] == LIMITATION and r["admitted"] is True
    assert r["comparative"]["B2"].status == PASS and r["comparative"]["B3"].status == PASS and r["absolute"]["audit"] == PASS and r["n"] == 40
    assert evaluate_amendment(good_h3(), cov, ext_cov(), LK, am, "R", FAIL)["amended"] == FAIL                      # the H2 clause failed: no amended PASS
    assert evaluate_amendment(good_h3(), cov, ext_cov(), LK, am, "R", INCONCLUSIVE)["amended"] == INCONCLUSIVE
    assert evaluate_amendment(good_h3(gain_r=0.55), cov, ext_cov(), LK, am, "R", PASS)["comparative"]["B2"].status == FAIL     # 0.6 - 0.55: the upper bound misses 0.10
    assert evaluate_amendment(good_h3(gain_r=0.45), cov, ext_cov(), LK, am, "R", PASS)["comparative"]["status"] == FAIL      # B2 - R = 0.15 passes, B3 - R = -0.05 fails
    assert evaluate_amendment(good_h3(eff_r=0.80), cov, ext_cov(), LK, am, "R", PASS)["absolute"]["eff"].status == FAIL
    r = evaluate_amendment(good_h3(), cov, ext_cov(admitted=False), LK, am, "R", PASS); assert r["amended"] == INCONCLUSIVE and "not admitted" in r["reason"] and r["admitted"] is False
    dup = pd.concat([good_h3(), good_h3().query("rule == 'R' and seed == 0")], ignore_index=True)
    assert "rows" in evaluate_amendment(dup, cov, ext_cov(), LK, am, "R", PASS)["reason"]
    assert "rows" in evaluate_amendment(good_h3().query("rule != 'R'"), cov, ext_cov(), LK, am, "R", PASS)["reason"]
    short = good_h3(); short.loc[(short.rule == "B3") & (short.seed == 39), "seed"] = 99
    assert "pairing" in evaluate_amendment(short, cov, ext_cov(), LK, am, "R", PASS)["reason"]
    assert evaluate_amendment(None, cov, None, LK, am, "R", PASS)["amended"] == INCONCLUSIVE
    assert evaluate_amendment(good_h3(), cov, ext_cov(), LK, am, "R", PASS, demoted=frozenset({"R|D2+H3"}))["amended"] == INCONCLUSIVE


def test_verify_h3_records_and_amendment_report(tmp_path):
    lk = dict(LK, identity_salt_sha256="ab" * 32, coverage_consequences={"final_eval_n": 3, "h1": "exploratory", "parametrized": "studentized_n40"})
    def job(rule):
        return {"spec": {"name": f"c_{rule}", "rule": rule, "family": "D2+H3", "beta": 0.05, "position": "median"}, "params": {"tol": 0.1}, "cfg": {"T": 200, "budget": 0.5},
                "settings_hash": settings_hash(lk), "budget": [1, 2, 3, 4], "smoke": False, "salt_hash": "ab" * 32, "eval_namespace": "final_eval"}
    def rec(rule, seeds=(7, 8, 9)):
        j = job(rule); meta = {"rule": rule, "family": "D2+H3", "beta": 0.05, "position": "median", "budget": 0.5}
        return {**{k: j[k] for k in ("spec", "params", "cfg", "settings_hash", "budget", "smoke", "salt_hash")}, "eval_namespace": "final_eval", "rows": [dict(meta, seed=s) for s in seeds]}
    jobs = {f"c_{r}": job(r) for r in ("B2", "B3", "R")}; recs = [rec("B2"), rec("B3"), rec("R")]; seeds = [7, 8, 9, 10]
    assert verify_h3_records(recs, lk, jobs, seeds, "R") == []
    assert any("duplicate seed" in p for p in verify_h3_records([rec("B2", (7, 7, 9)), rec("B3"), rec("R")], lk, jobs, seeds, "R"))
    assert any("missing rule" in p for p in verify_h3_records(recs[:2], lk, jobs, seeds, "R"))
    assert any("namespace" in p for p in verify_h3_records([dict(rec("B2"), eval_namespace="dev_val"), rec("B3"), rec("R")], lk, jobs, seeds, "R"))
    from sim.amendment import amendment_hash
    am = {"clause": {"n": 40}, "coverage_report_amendment_sha256": None, "coverage_consequences": {"h3_comparative": "confirmatory"}}
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{"name": n} for n in REGISTERED_NAMES], "consequences": {"h3_comparative": "confirmatory"}, "limitation": LIMITATION,
           "amendment_sha256": amendment_hash(am)}
    p = tmp_path / "r.json"; p.write_text(json.dumps(rep)); h = hashlib.sha256(p.read_bytes()).hexdigest()
    am = {**am, "coverage_report_amendment_sha256": h}
    assert verify_amendment_report(p, am) == []
    assert verify_amendment_report(p, dict(am, coverage_report_amendment_sha256="0" * 32 + "1" * 32))
    assert verify_amendment_report(p, dict(am, coverage_consequences={"h3_comparative": "exploratory"}))
    for bad in (dict(rep, smoke=True), dict(rep, admission_basis="smoke (not an admission)"), dict(rep, selection=rep["selection"][:5]), dict(rep, limitation="x"),
                dict(rep, selection=[{"name": "zz"}] + rep["selection"][1:])):
        q = tmp_path / "bad.json"; q.write_text(json.dumps(bad))
        assert verify_amendment_report(q, dict(am, coverage_report_amendment_sha256=hashlib.sha256(q.read_bytes()).hexdigest()))


def write_amendment(path, registered: bool, report_hash=None, consequences=None):
    import yaml
    doc = {"amendment": {"id": 1}, **AMEND_FIXTURE, "seeds_ext": {"start": 6_600_000, "block": 400_000, "pool": 35_000, "replications": {"40": 4000}},
           "coverage_report_amendment_sha256": report_hash if registered else None, "coverage_consequences": consequences if registered else None}
    Path(path).write_text(yaml.safe_dump(doc)); return path


def test_check_claim_cli_reports_the_amendment_and_stays_silent_without_it(tmp_path):
    h2_40 = pd.concat([frame("R", "H2", 0.05, 0.97, 0.98, 0.5, n=40), frame("B2", "H2", 1.5, 0.80, 0.95, 0.5, n=40), frame("B3", "H2", 0.2, 0.85, 0.97, 0.5, n=40)], ignore_index=True)
    h2_40.to_csv(tmp_path / "h2.csv", index=False); good_h1().to_csv(tmp_path / "h1.csv", index=False); good_h3().to_csv(tmp_path / "h3.csv", index=False)
    (tmp_path / "cov.json").write_text(json.dumps(coverage(method20=None, par="studentized_n40", n_final=40, method40="studentized", h1="exploratory")))
    (tmp_path / "ext.json").write_text(json.dumps(ext_cov())); (tmp_path / "s.json").write_text(json.dumps(summary()))
    am = write_amendment(tmp_path / "am.yaml", registered=True, report_hash="ab" * 32, consequences={"h3_comparative": "confirmatory"})
    cmd = [sys.executable, str(ROOT / "scripts" / "check_claim.py"), "--synthetic", "--h2-rows", str(tmp_path / "h2.csv"), "--h1-rows", str(tmp_path / "h1.csv"),
           "--h1-summary", str(tmp_path / "s.json"), "--coverage-report", str(tmp_path / "cov.json"), "--proposed", "R"]
    r = subprocess.run(cmd + ["--h3-rows", str(tmp_path / "h3.csv"), "--coverage-ext", str(tmp_path / "ext.json"), "--amendment", str(am), "--out", str(tmp_path / "v.json")],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    v = json.loads((tmp_path / "v.json").read_text()); assert v["amendment"]["amended"] == PASS and v["claim"] == PASS
    assert "amended claim: PASS" in r.stdout and LIMITATION in r.stdout and "stress test" in r.stdout and "held out" not in r.stdout.lower()
    r2 = subprocess.run(cmd + ["--out", str(tmp_path / "v2.json"), "--amendment", str(tmp_path / "absent.yaml")], capture_output=True, text=True, cwd=ROOT)
    assert r2.returncode == 0 and "amendment" not in json.loads((tmp_path / "v2.json").read_text()) and "amended" not in r2.stdout


def test_check_claim_refuses_a_draft_or_bad_amendment_before_reading_any_sweep(tmp_path):
    repo = make_repo(tmp_path); git(repo, "tag", "freeze-test")
    cmd = [sys.executable, str(ROOT / "scripts" / "check_claim.py"), "--repo", str(repo), "--proposed", "R", "--verify-lock", "lock-test"]
    draft = write_amendment(tmp_path / "draft.yaml", registered=False)
    r = subprocess.run(cmd + ["--verify-only", "--amendment", str(draft)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "unregistered (draft)" in r.stdout
    conf = cmd + ["--verify-freeze", "freeze-test", "--sweep-out", str(tmp_path), "--calibration", str(tmp_path / "cal.json"), "--tuned-dir", str(tmp_path), "--proposed-describe", str(tmp_path / "d.yaml")]
    r = subprocess.run(conf + ["--amendment", str(draft)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 2 and "not registered" in r.stderr
    import yaml
    from sim.amendment import amendment_hash
    base_doc = yaml.safe_load(write_amendment(tmp_path / "probe.yaml", registered=False).read_text())
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{"name": n} for n in REGISTERED_NAMES], "consequences": {"h3_comparative": "confirmatory"}, "limitation": LIMITATION,
           "amendment_sha256": amendment_hash(base_doc)}
    ext = tmp_path / "ext.json"; ext.write_text(json.dumps(rep)); h = hashlib.sha256(ext.read_bytes()).hexdigest()
    ok = write_amendment(tmp_path / "ok.yaml", registered=True, report_hash=h, consequences={"h3_comparative": "confirmatory"})
    r = subprocess.run(cmd + ["--verify-only", "--amendment", str(ok), "--coverage-ext", str(ext)], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0 and "amendment report verified" in r.stdout
    for bad_am, bad_rep in ((write_amendment(tmp_path / "b1.yaml", True, "00" * 32, rep["consequences"]), rep),
                            (ok, dict(rep, smoke=True)), (ok, dict(rep, consequences={"h3_comparative": "exploratory"})), (ok, dict(rep, selection=rep["selection"][::-1]))):
        bad = tmp_path / "bad_ext.json"; bad.write_text(json.dumps(bad_rep))
        for mode in (["--verify-only"], ["--verify-freeze", "freeze-test", "--sweep-out", str(tmp_path), "--calibration", str(tmp_path / "cal.json"), "--tuned-dir", str(tmp_path), "--proposed-describe", str(tmp_path / "d.yaml")]):
            r = subprocess.run(cmd + mode + ["--amendment", str(bad_am), "--coverage-ext", str(bad)], capture_output=True, text=True, cwd=ROOT)
            assert r.returncode == 2 and "amendment report" in r.stderr


def test_check_claim_refuses_the_locked_file_override(tmp_path):
    import os
    repo = make_repo(tmp_path)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_claim.py"), "--verify-only", "--verify-lock", "lock-test", "--repo", str(repo), "--proposed", "R"],
                       capture_output=True, text=True, cwd=ROOT, env={**os.environ, "TOUCHSTONE_LOCKED": str(tmp_path / "other.yaml")})
    assert r.returncode == 2 and "TOUCHSTONE_LOCKED" in r.stderr


def test_amendment_keeps_known_failures_and_binds_the_amendment_hash(tmp_path):
    cov = coverage(method20=None, par="studentized_n40", n_final=40, method40="studentized"); am = AMEND_FIXTURE
    r = evaluate_amendment(good_h3(), cov, ext_cov(admitted=False), LK, am, "R", FAIL)
    assert r["amended"] == FAIL and r["comparative"]["status"] == INCONCLUSIVE and r["absolute"]["status"] == PASS      # an H2 FAIL survives an unadmitted extension
    r = evaluate_amendment(good_h3(eff_r=0.80), cov, ext_cov(admitted=False), LK, am, "R", PASS)
    assert r["amended"] == FAIL and r["absolute"]["eff"].status == FAIL                                                   # an admitted absolute FAIL survives too
    assert evaluate_amendment(None, cov, None, LK, am, "R", FAIL)["amended"] == FAIL                                      # no rows at all: the H2 FAIL still decides
    assert evaluate_amendment(good_h3().query("rule != 'R'"), cov, ext_cov(), LK, am, "R", FAIL)["amended"] == FAIL
    from sim.amendment import amendment_hash
    doc = {"clause": dict(am["clause"]), "coverage_report_amendment_sha256": None, "coverage_consequences": None}
    rep = {"admission_basis": "registered", "smoke": False, "selection": [{"name": n} for n in REGISTERED_NAMES], "consequences": {"h3_comparative": "confirmatory"},
           "limitation": LIMITATION, "amendment_sha256": amendment_hash(doc)}
    p = tmp_path / "r.json"; p.write_text(json.dumps(rep)); h = hashlib.sha256(p.read_bytes()).hexdigest()
    reg = {**doc, "coverage_report_amendment_sha256": h, "coverage_consequences": rep["consequences"]}
    assert verify_amendment_report(p, reg) == []
    edited = {**reg, "clause": {**reg["clause"], "gain_reduction_min": 0.0}}
    assert any("amendment_sha256" in q for q in verify_amendment_report(p, edited))                                      # an edited amendment copy no longer matches the report
