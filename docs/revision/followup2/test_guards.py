"""Shared guards of the follow-up runs (internal review round 1 of both plans)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guards as G  # noqa: E402
from sim.records_v2 import read, write  # noqa: E402


def test_a_locked_settings_override_is_refused(monkeypatch):
    monkeypatch.setenv("TOUCHSTONE_LOCKED", "/tmp/other.yaml")
    with pytest.raises(SystemExit, match="TOUCHSTONE_LOCKED"):
        G.pin_settings()
    monkeypatch.delenv("TOUCHSTONE_LOCKED")
    G.pin_settings()                                     # locked.yaml and the manifest equal protocol-v2


def test_budgets_must_equal_the_frozen_records(tmp_path):
    write(tmp_path / "rec.json", {"provenance": {"budget": [5, 300, 5, 200]}})
    G.check_budget({"id": "x", "budget": [5, 300, 5, 200]}, tmp_path / "rec.json")
    with pytest.raises(SystemExit, match="budget"):
        G.check_budget({"id": "x", "budget": [5, 150, 5, 200]}, tmp_path / "rec.json")


def test_saved_results_are_reused_only_under_the_same_binding(tmp_path):
    b = G.binding(inputs_sha="i", provenance={"id": "x"}, smoke=False, settings={"max_rounds": 3}, driver_sha="d")
    p = tmp_path / "r.json"
    assert G.reusable(p, b) is False                                            # nothing saved
    write(p, {"binding": b, "x": 1}); assert G.reusable(p, b) is True
    for k, v in (("smoke", True), ("settings", {"max_rounds": 2}), ("inputs_sha", "j"), ("driver_sha", "e")):
        with pytest.raises(SystemExit, match="binding"):
            G.reusable(p, {**b, k: v})


def test_the_inventory_names_this_driver_its_helpers_and_the_run(tmp_path):
    (tmp_path / "a.json").write_text("{}")
    inv = G.inventory(tmp_path, deviations=["d1"], files={"driver": Path(G.__file__)}, args=["--x", "1"])
    assert inv["deviations"] == ["d1"] and inv["files"]["driver"] == G.sha_file(Path(G.__file__)) and inv["args"] == ["--x", "1"]
    assert "a.json" in inv["records"] and "inventory.json" not in inv["records"] and "reset_followup_v2.py" in inv["files"]
    assert {"python", "numpy", "scipy", "cma", "blas", "cpu"} <= set(inv["environment"]) and "driver_sha256" not in inv["environment"]


def test_cost_stop_between_stages_never_kills(tmp_path):
    clock = iter([0.0, 3600.0 * 5]).__next__
    c = G.CostStop(cap_usd=3.0, usd_per_hour=0.56, started=0.0, clock=clock)
    assert c.allow("search", 1.0) is True                                      # 0 h spent + 1 h at 0.56
    assert c.allow("doubling", 1.0) is False and c.stopped == "doubling"        # 5 h = 2.80 USD + 0.56 > 3.00
    assert c.report()["stopped_before"] == "doubling"


def test_evidence_files_must_report_a_pass(tmp_path):
    write(tmp_path / "ok.json", {"pass": True}); write(tmp_path / "bad.json", {"pass": False})
    G.check_evidence([tmp_path / "ok.json"])
    with pytest.raises(SystemExit, match="evidence"):
        G.check_evidence([tmp_path / "ok.json", tmp_path / "bad.json"])
    with pytest.raises(SystemExit, match="evidence"):
        G.check_evidence([tmp_path / "missing.json"])


def test_finite_values_are_required():
    assert G.finite([0.1, 2], {"a": 0.3}) and not G.finite([0.1, float("nan")]) and not G.finite({"a": float("inf")})


def test_a_binding_survives_its_json_round_trip(tmp_path):
    b = G.binding(inputs_sha="i", provenance={"seeds": (1, 2)}, smoke=True, settings={"markets": ("fresh0",)}, driver_sha="d")
    write(tmp_path / "r.json", {"binding": b}); assert G.reusable(tmp_path / "r.json", G.binding("i", {"seeds": (1, 2)}, True, {"markets": ("fresh0",)}, "d"))
