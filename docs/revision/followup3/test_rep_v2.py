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
                              prior_usd=0, started=None, peak_search=2.5e8)
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


def test_continuation_cost_stop_carries_the_launchers_stop_file_and_soft_deadline(tmp_path):
    # Run B's worker cost stop holds the STOP file and the soft deadline; the replication's must too
    import types
    a = types.SimpleNamespace(smoke=False, stop_usd=30.0, usd_per_hour=0.7, started=1.7e9, prior_usd=1.5,
                              stop_file=str(tmp_path / "STOP"), soft_deadline=1.7e9 + 3600)
    s = D.cost_stop(a)
    assert (s.cap, s.rate, s.started, s.prior, str(s.stop_file), s.soft) == (30.0, 0.7, 1.7e9, 1.5, str(tmp_path / "STOP"), 1.7e9 + 3600)
    (tmp_path / "STOP").write_text("")
    assert not s.allow("round 1", 0.0)
    a.smoke = True
    assert D.cost_stop(a) is None


# ---- review rep-impl-r1 (Sol 1, 2, 3, 12; Astra 1, 2, 3, 7, 12) --------------------------------------------------------

def _manifest(tmp_path, files=None):
    import json
    m = tmp_path / "manifest.json"; m.write_text(json.dumps({"commit": "c0ffee", "files": files or {}})); return m


def test_parameter_files_must_be_listed_in_the_manifest(tmp_path):
    m = _manifest(tmp_path, {"experiments/v2/params.json": "x"})
    D.check_params_listed(m, D.ROOT / "experiments/v2/params.json")
    with pytest.raises(SystemExit):
        D.check_params_listed(m, tmp_path / "my-params.json")


def test_every_provenance_carries_the_manifest_and_draw_hashes(tmp_path, monkeypatch):
    import revision_v2 as R
    monkeypatch.setattr(R, "context_provenance", lambda mkt: {"a": 1})
    m = _manifest(tmp_path); draw = tmp_path / "draw.json"; draw.write_text("{}")
    D.bind_provenance(m, draw); D.bind_provenance(m, draw)          # idempotent
    p = R.context_provenance({})
    assert p == {"a": 1, "manifest_sha256": D.K._sha(m), "draw_sha256": D.K._sha(draw)}
    assert R.aux_provenance({}, rule="F111")["manifest_sha256"] == D.K._sha(m)


def test_instances_and_calibration_are_never_replaced(tmp_path, monkeypatch):
    import json
    import types
    from scripts import draw_v2
    monkeypatch.setattr(draw_v2, "instances", lambda *a, **k: {"root": "r1"})
    (tmp_path / "draw.json").write_text("{}"); (tmp_path / "proof").write_bytes(b"p"); m = _manifest(tmp_path)
    a = types.SimpleNamespace(out=str(tmp_path / "o"), draw=str(tmp_path / "draw.json"), proof=str(tmp_path / "proof"),
                              manifest=str(m), protocol=None, smoke=False, published_height=None)
    D.stage_instances(a); D.stage_instances(a)                     # a resume with the same draw is allowed
    monkeypatch.setattr(draw_v2, "instances", lambda *a, **k: {"root": "r2"})
    with pytest.raises(SystemExit):
        D.stage_instances(a)
    (tmp_path / "o" / "calibration.json").write_text(json.dumps({"cfgs_sha256": "x"}))
    with pytest.raises(SystemExit):
        D.stage_calibrate(types.SimpleNamespace(out=str(tmp_path / "o"), params="p"))


def test_a_reused_calibration_must_come_from_linux_x86(tmp_path):
    D.check_calibration_platform({"system": "Linux", "machine": "x86_64"}, smoke=False)
    D.check_calibration_platform({"system": "Darwin", "machine": "arm64"}, smoke=True)
    with pytest.raises(SystemExit):
        D.check_calibration_platform({"system": "Darwin", "machine": "arm64"}, smoke=False)


def test_every_stage_checks_the_output_belongs_to_this_manifest_and_draw(tmp_path):
    import json
    m = _manifest(tmp_path); draw = tmp_path / "draw.json"; draw.write_text("{}")
    out = tmp_path / "o"; out.mkdir()
    D.write_binding(out, m, draw)
    D.check_binding(out, m, draw)
    draw2 = tmp_path / "draw2.json"; draw2.write_text('{"other": 1}')
    with pytest.raises(SystemExit):
        D.check_binding(out, m, draw2)
    (out / "binding.json").write_text(json.dumps({"manifest_sha256": "0" * 64, "draw_sha256": D.K._sha(draw)}))
    with pytest.raises(SystemExit):
        D.check_binding(out, m, draw)


def test_churn_rates_need_a_passed_churn_zero_gate(monkeypatch, tmp_path):
    import json
    import types
    calls = []
    fake = types.SimpleNamespace(install=lambda: None, _run_rate=lambda out, jobs, steps, a, s, c, p, st: calls.append(Path(out).name))
    monkeypatch.setitem(sys.modules, "churn_v2", fake)
    monkeypatch.setattr(D, "_context", lambda a: types.SimpleNamespace(root="r", salt="s", container={}))
    monkeypatch.setattr(D, "rate_jobs", lambda c, k, p, s: [])
    monkeypatch.setattr(D, "_memory_limit", lambda: None)
    import revision_v2 as R
    monkeypatch.setattr(R, "install_salt", lambda root, out: None)
    a = types.SimpleNamespace(out=str(tmp_path), smoke=False, rates="churn", workers_search=16, workers_eval=9, stop_usd=1,
                              usd_per_hour=1, prior_usd=0, started=0.0, peak_search=2.5e8)
    with pytest.raises(SystemExit):
        D.stage_rates(a)
    (tmp_path / "gate0").mkdir(); (tmp_path / "gate0" / "gate.json").write_text(json.dumps({"gate_ok": False}))
    with pytest.raises(SystemExit):
        D.stage_rates(a)
    (tmp_path / "gate0" / "gate.json").write_text(json.dumps({"gate_ok": True}))
    D.stage_rates(a)
    assert calls == ["menu-p0.03", "menu-p0.05", "cthr-p0.03", "cthr-p0.05"]


def test_churn_search_workers_are_admitted_and_kept_across_restarts(tmp_path):
    gb = 1e9
    assert D.rate_search_workers(tmp_path, 16, 6 * gb, 0.8 * gb) == 4          # (6 - 2) / (0.8 * 1.25) = 4
    assert D.rate_search_workers(tmp_path, 16, 64 * gb, 0.8 * gb) == 4         # a restart keeps the lower count
    assert D.rate_search_workers(tmp_path / "s", 16, None, 0.8 * gb) == 16     # smoke: no limit


def test_the_continuation_gate_is_the_first_p005_cell():
    jobs = {("menu", 0.05): [{"id": "fresh1@rho0.2|F111|D2+H3|profit|churn0.05", "mkt": {"label": "fresh1"}, "rule": "F111"},
                             {"id": "fresh0@rho0.2|C*|D2+H3|profit|churn0.05", "mkt": {"label": "fresh0"}, "rule": "C*"},
                             {"id": "fresh0@rho0.2|F111|D2+H3|profit|churn0.05", "mkt": {"label": "fresh0"}, "rule": "F111"}],
            ("menu", 0.0): [{"id": "fresh0@rho0.2|F111|D2+H3|profit", "mkt": {"label": "fresh0"}, "rule": "F111"}]}
    g = D.gate_item(jobs, Path("/b"))
    assert g["job"]["id"] == "fresh0@rho0.2|F111|D2+H3|profit|churn0.05" and g["dir"] == "/b/menu-p0.05"
    assert g["id"] == "menu-p0.05|fresh0@rho0.2|F111|D2+H3|profit|churn0.05"
