import json, subprocess, sys
from pathlib import Path
import pytest
from sim.calibrate import calibrate, save_calibration
from sim.locked import load_locked, market_config_from_locked, seeds, settings_hash
from sim.reference import ROW_FIELDS


@pytest.fixture(scope="module")
def cal_path(tmp_path_factory):
    p = tmp_path_factory.mktemp("cal") / "cal.json"
    save_calibration(calibrate(market_config_from_locked(load_locked()), seeds=[4000]), p)
    return p


def run_sweep(cal_path, out, *extra):
    return subprocess.run([sys.executable, "scripts/sweep.py", "--calibration", str(cal_path), "--out", str(out), *extra],
                          capture_output=True, text=True)


def test_sweep_refuses_untuned_run_without_smoke_flag(cal_path, tmp_path):
    r = run_sweep(cal_path, tmp_path / "res", "--stage", "search", "--rules", "B1", "--limit", "1")
    assert r.returncode != 0 and "tuned" in (r.stderr + r.stdout)


def test_sweep_refuses_unbound_tuned_file_and_partial_calibration(cal_path, tmp_path):
    td = tmp_path / "tuned"; td.mkdir()
    lk = load_locked()
    good = {"rule": "B1", "market_key": json.loads(cal_path.read_text())["market_key"], "settings_hash": settings_hash(lk), "quick": False,
            "calibration_seeds": [4000], "best_params": {"P1": 0.25, "P2": 0.40, "P3": 0.55}}
    (td / "tuned_B1.json").write_text(json.dumps(dict(good, rule="B3")))
    r = run_sweep(cal_path, tmp_path / "r1", "--stage", "search", "--rules", "B1", "--limit", "1", "--tuned-dir", str(td))
    assert r.returncode != 0 and "rule" in (r.stderr + r.stdout)
    (td / "tuned_B1.json").write_text(json.dumps(dict(good, calibration_seeds=[4000, 4001])))
    r = run_sweep(cal_path, tmp_path / "r2", "--stage", "search", "--rules", "B1", "--limit", "1", "--tuned-dir", str(td))
    assert r.returncode != 0 and "calibration seeds" in (r.stderr + r.stdout)   # tuned with another calibration
    (td / "tuned_B1.json").write_text(json.dumps(good))
    r = run_sweep(cal_path, tmp_path / "r3", "--stage", "search", "--rules", "B1", "--limit", "1", "--tuned-dir", str(td))
    assert r.returncode != 0 and "calibration namespace" in (r.stderr + r.stdout)     # one calibration seed is not the full namespace


def test_smoke_sweep_runs_every_stage_with_counted_runs(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development,h3,all_deviators", "--rules", "B1",
                  "--select", "beta0.05_rho0.2_median", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    assert (out / "SMOKE").exists()
    search = {p.stem: json.loads(p.read_text()) for p in (out / "search").glob("*.json")}
    assert {rec["spec"]["family"] for rec in search.values()} == {"D1", "D2", "D2+H3"}
    for stage in ("search", "bank", "reference", "evaluate", "checks"):
        for p in (out / stage).glob("*.json"):
            rec = json.loads(p.read_text())
            assert rec["runs"] == rec["scheduled"] if stage in ("search", "evaluate") else rec["runs"] <= rec["scheduled"]
    checks = json.loads((out / "checks.json").read_text())
    assert len(checks) == 3 and {c["spec"]["family"] for c in checks} == {"D1", "D2", "D2+H3"}      # D1, D2, and (amendment 2) the H3 doubling control at beta_headline, median
    h3c = next(c for c in checks if c["spec"]["family"] == "D2+H3"); assert "delta_gain" in json.dumps(h3c) and h3c["runs"] <= h3c["scheduled"]
    headline = json.loads((out / "headline.json").read_text())
    assert set(headline) == {"B1/D1", "B1/D2"} and all(h["headline"] == "median" for h in headline.values())
    rows = (out / "development.csv").read_text().splitlines()
    assert rows[0] == "cell,section,rule,family,beta,rho,position,smoke,reference,budget," + ",".join(ROW_FIELDS)
    assert len(rows) == 1 + 2 * 2 and (out / "h3.csv").exists()
    ad = json.loads((out / "all_deviators.json").read_text())
    assert len(ad) == 1 and ad[0]["runs"] == ad[0]["scheduled"] and len(ad[0]["gain_dev_val"]) == 10
    assert set(ad[0]) >= {"attack", "twin", "gain_dev_val"}
    # provenance: a changed source record stops the bank stage; a changed bank stops the reference stage
    src = next((out / "search").glob("*D1*.json"))
    rec = json.loads(src.read_text()); rec["params"]["P3"] = 0.99; src.write_text(json.dumps(rec))
    r = run_sweep(cal_path, out, "--stage", "bank", "--rules", "B1", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "differs" in (r.stderr + r.stdout)
    r = run_sweep(cal_path, out, "--stage", "reference", "--rules", "B1", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "bank source" in (r.stderr + r.stdout)
    r = run_sweep(cal_path, out, "--stage", "evaluate", "--rules", "B1", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "bank" in (r.stderr + r.stdout)           # the evaluate stage checks the bank too


def test_reference_records_carry_per_seed_values_and_foreign_rules_are_refused(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development", "--rules", "B1",
                  "--select", "B1_D1_beta0.05_rho0.2_median", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    rec = json.loads(next((out / "reference").glob("*.json")).read_text())
    assert len(rec["attack_per_seed_normalized"]) == 1 and len(rec["reference_per_seed_normalized"]) == 1
    assert rec["gain_train"] == pytest.approx(rec["attack_per_seed_normalized"][0] - rec["reference_per_seed_normalized"][0])
    r = run_sweep(cal_path, out, "--stage", "reference", "--rules", "B2", "--smoke", "--workers", "1")
    assert r.returncode != 0 and "B1" in (r.stderr + r.stdout)
    r = run_sweep(cal_path, out, "--stage", "evaluate", "--rules", "B1", "--smoke", "--workers", "1", "--eval-namespace", "final_eval")
    from scripts.sweep import train_val
    from sim.schedule import Budget, stage_runs
    lk = load_locked()
    job = {"budget": [1, 16, 1, 2], "locked": dict(lk, coverage_consequences={"final_eval_n": 3}, seeds=dict(lk["seeds"], final_eval=[9, 8, 7, 6])), "eval_namespace": "final_eval"}
    _, val, b = train_val(job)
    assert val == (9, 8, 7) and b == Budget(1, 16, 1, 3) and stage_runs("D1", "evaluate", b) == 12      # the evaluate count follows final_eval_n
    assert r.returncode != 0 and "final_eval" in (r.stderr + r.stdout)


def test_search_shards_cover_the_unsharded_record_set(cal_path, tmp_path):
    whole = tmp_path / "whole"; parts = tmp_path / "parts"
    common = ["--stage", "search", "--sections", "development", "--rules", "B1", "--select", "B1_D1_beta0.05", "--smoke", "--workers", "1"]
    r = run_sweep(cal_path, whole, *common); assert r.returncode == 0, r.stderr
    for shard in ("0/2", "1/2"):
        r = run_sweep(cal_path, parts, *common, "--shard", shard); assert r.returncode == 0, r.stderr
    names = lambda d: sorted(p.name for p in (d / "search").glob("*.json"))
    assert names(whole) == names(parts) and len(names(whole)) == 3                    # three positions at the headline beta, split 2 + 1


def test_limit_without_shard_keeps_the_manifest_order(cal_path, tmp_path):
    """Final review F13: --limit picks the manifest's first cells unless --shard asks for the sorted order."""
    from sim.manifest import enumerate_manifest
    from sim.schedule import SMOKE_BUDGET
    lk = load_locked()
    first = next(c.name for c in enumerate_manifest(lk, ["B1"], budget=SMOKE_BUDGET) if c.section == "development" and c.kind == "full_cell" and "beta0.05" in c.name)
    out = tmp_path / "lim"
    r = run_sweep(cal_path, out, "--stage", "search", "--sections", "development", "--rules", "B1", "--select", "beta0.05", "--smoke", "--workers", "1", "--limit", "1")
    assert r.returncode == 0, r.stderr
    assert [p.stem for p in (out / "search").glob("*.json")] == [first]


def test_checks_scope_follows_the_selected_sections_and_refuses_a_missing_in_scope_record(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development,h3", "--rules", "B1", "--select", "beta0.05_rho0.2_median", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    assert {c["spec"]["family"] for c in json.loads((out / "checks.json").read_text())} == {"D1", "D2", "D2+H3"}
    r2 = run_sweep(cal_path, out, "--stage", "checks", "--sections", "development", "--rules", "B1", "--smoke", "--workers", "1")
    assert r2.returncode == 0 and {c["spec"]["family"] for c in json.loads((out / "checks.json").read_text())} == {"D1", "D2"}      # H3 control out of scope: not visited
    next((out / "search").glob("*D2+H3*.json")).unlink()
    r3 = run_sweep(cal_path, out, "--stage", "checks", "--sections", "h3", "--rules", "B1", "--smoke", "--workers", "1")
    assert r3.returncode != 0 and "control" in (r3.stderr + r3.stdout)                                                                 # in scope and missing: refused


def test_h3_cells_take_the_bank_and_a_tampered_embeddings_entry_is_refused(cal_path, tmp_path):
    out = tmp_path / "res"
    r = run_sweep(cal_path, out, "--stage", "all", "--sections", "development,h3", "--rules", "B1", "--select", "beta0.05_rho0.2_median", "--smoke", "--workers", "1")
    assert r.returncode == 0, r.stderr
    bank_doc = json.loads((out / "bank.json").read_text())
    assert bank_doc["embeddings"] == {"D2+H3": ["embed_d2_in_h3", "embed_d2_in_h3_exit"]}
    h3 = json.loads(next((out / "bank").glob("*D2+H3*.json")).read_text())
    assert h3["bank_hash"] == bank_doc["bank_hash"] and any(o.endswith("|x=1") for o in [t[2] for t in h3["ranked_top"]] + [h3["transfer"].get("best_origin") or ""])
    ref = json.loads(next((out / "reference").glob("*D2+H3*.json")).read_text()); assert ref["bank_hash"] == bank_doc["bank_hash"]
    bank_doc["embeddings"] = {"D2+H3": ["embed_d2_in_h3"]}; (out / "bank.json").write_text(json.dumps(bank_doc))
    r2 = run_sweep(cal_path, out, "--stage", "reference", "--rules", "B1", "--smoke", "--workers", "1")
    assert r2.returncode != 0 and "embeddings" in (r2.stderr + r2.stdout)
