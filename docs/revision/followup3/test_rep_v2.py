"""Tests for the replication driver's pure rules (plan sections 4 and 5)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rep_v2 as D  # noqa: E402


def _c(rate, market, rule):
    return {"rate": rate, "market": market, "rule": rule, "id": f"{rate}|{market}|{rule}"}


def test_queue_order_rate_then_market_then_rule():
    cells = [_c(0.0, "fresh0", "F111"), _c(0.05, "fresh2", "F000"), _c(0.05, "fresh2", "F111"), _c(0.03, "fresh0", "Cthr"),
             _c(0.05, "fresh0", "Cthr"), _c(0.05, "fresh0", "C*")]
    q = [c["id"] for c in D.continuation_queue(cells)]
    assert q == ["0.05|fresh0|C*", "0.05|fresh0|Cthr", "0.05|fresh2|F111", "0.05|fresh2|F000", "0.03|fresh0|Cthr", "0.0|fresh0|F111"]


def test_queue_refuses_unknown_cells():
    with pytest.raises(SystemExit):
        D.continuation_queue([_c(0.02, "fresh0", "F111")])


def test_resume_continues_from_the_first_cell_without_a_pass():
    q = D.continuation_queue([_c(0.05, "fresh0", "F111"), _c(0.05, "fresh1", "F111"), _c(0.03, "fresh0", "F111")])
    assert D.resume_point(q, {"0.05|fresh0|F111"}) == 1
    assert D.resume_point(q, {c["id"] for c in q}) == 3


def test_memory_admission_lowers_workers_and_refuses_when_one_task_does_not_fit():
    gb = 1e9
    assert D.admit_workers(16, None, 1.2 * gb) == 16
    assert D.admit_workers(9, 28 * gb, 2.8 * gb) == 7          # (28 - 2) / (2.8 * 1.25) = 7.4
    assert D.admit_workers(5, 28 * gb, 3.54 * gb) == 5
    with pytest.raises(SystemExit):
        D.admit_workers(5, 4 * gb, 3.54 * gb)


def test_cfg_reuse_requires_the_calibration_hash(tmp_path):
    p = tmp_path / "cfgs.json"; p.write_text('{"fresh0": {}}\n')
    D.check_cfg_reuse(p, {"cfgs_sha256": D.K._sha(p)})
    with pytest.raises(SystemExit):
        D.check_cfg_reuse(p, {"cfgs_sha256": "0" * 64})


def test_jobs_carry_the_manifest_commit_not_the_current_head(tmp_path, monkeypatch):
    # smoke run 2026-11-19: a commit between stages changed the provenance and broke the p = 0 freeze
    import json
    import revision_v2 as R
    monkeypatch.setattr(R, "git_commit", lambda: "head-now")
    m = tmp_path / "manifest.json"; m.write_text(json.dumps({"commit": "c0ffee", "files": {}}))
    D.pin_commit(m)
    assert R.git_commit() == "c0ffee"



def test_salt_is_installed_and_checked(tmp_path, monkeypatch):
    # smoke run 2026-11-19: the continuation stage never installed the salt, so churn cells (new identities) differed
    import hashlib
    import os
    from sim import instances as INST
    root = "00" * 32
    monkeypatch.delenv("TOUCHSTONE_IDENTITY_SALT", raising=False)
    want = hashlib.sha256(bytes.fromhex(INST.identity_salt_hex(root))).hexdigest()
    D.install_checked_salt(root, tmp_path, want)
    assert os.environ["TOUCHSTONE_IDENTITY_SALT"] == str(tmp_path / "salt.hex")
    with pytest.raises(SystemExit):
        D.install_checked_salt(root, tmp_path, "0" * 64)


def test_rates_split_runs_p0_before_the_gate_and_churn_after(monkeypatch, tmp_path):
    # plan section 5: the churn-zero gate runs after the p = 0 branch and before any churn spend
    calls = []
    import types
    fake = types.SimpleNamespace(install=lambda: None, _run_rate=lambda out, jobs, steps, a, s, c, p, st: calls.append((Path(out).name, steps[1])))
    monkeypatch.setitem(sys.modules, "churn_v2", fake)
    monkeypatch.setattr(D, "_context", lambda a: types.SimpleNamespace(root="r", salt="s", container={}))
    monkeypatch.setattr(D, "rate_jobs", lambda c, k, p, s: [])
    import revision_v2 as R
    monkeypatch.setattr(R, "install_salt", lambda root, out: None)
    a = types.SimpleNamespace(out=str(tmp_path), smoke=True, rates="p0", workers_search=1, workers_eval=1, stop_usd=1, usd_per_hour=1,
                              prior_usd=0, started=None)
    D.stage_rates(a)
    assert [n for n, _ in calls] == ["menu-p0", "cthr-p0"]
    calls.clear(); a.rates = "churn"; D.stage_rates(a)
    assert [n for n, _ in calls] == ["menu-p0.03", "menu-p0.05", "cthr-p0.03", "cthr-p0.05"]


def test_root_inventory_lists_every_file_but_itself(tmp_path):
    import json
    (tmp_path / "menu" / "search").mkdir(parents=True); (tmp_path / "menu" / "search" / "a.json").write_text("{}")
    (tmp_path / "menu-p0").mkdir(); (tmp_path / "menu-p0" / "inventory.json").write_text("{}"); (tmp_path / "x.lock").write_text("")
    (tmp_path / "cfgs.json").write_text("{}")
    D.root_inventory(tmp_path)
    recs = json.loads((tmp_path / "inventory.json").read_text())["records"]
    assert set(recs) == {"menu/search/a.json", "cfgs.json"}


def test_main_returns_the_stage_exit_code(monkeypatch):
    monkeypatch.setattr(D, "_require", lambda a: None)
    monkeypatch.setitem(D.STAGES, "continue", lambda a: 5)
    assert D.main(["--stage", "continue", "--out", "o", "--manifest", "m", "--smoke"]) == 5
