"""Tests for addendum_v2.py: the Operation 8 addendum beside the tagged report (labels, claim scope, deviations,
search-flag dependencies traced through reference and bank records, per-market Q1 side fields)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import addendum_v2 as A  # noqa: E402


def _path_of(out: Path, rid: str) -> Path:
    return out / "rec" / (rid.replace("|", "__").replace("/", "~").replace("*", "star") + ".json")


def _put(out, rid, upstream, **fields):
    p = _path_of(out, rid); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"upstream": {u: "0" * 64 for u in upstream}, **fields}))


def _ev(out, rid, upstream, **fields):
    p = out / "evaluate" / (A.safe(rid) + ".json"); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"upstream": {u: "0" * 64 for u in upstream}, **fields}))


@pytest.fixture
def chain(tmp_path):
    # C* X7-SC evaluate -> reference C* -> bank source F111 D2+H3 (flagged); freeze links everything and is skipped.
    _put(tmp_path, "freeze/m0", ["m0|F111|D2+H3|profit", "m0|C*|X7-SC|profit"])
    _put(tmp_path, "m0|F111|D2+H3|profit", [])
    _put(tmp_path, "m0|C*|X7-SC|profit", [])
    _put(tmp_path, "reference/m0/C*", ["m0|C*|X7-SC|profit", "m0|F111|D2+H3|profit"])
    _put(tmp_path, "reference/m0/F000", ["m0|F000|D2+H3|profit"])
    _put(tmp_path, "m0|F000|D2+H3|profit", [])
    _ev(tmp_path, "m0|C*|X7-SC|profit", ["freeze/m0", "m0|C*|X7-SC|profit", "reference/m0/C*"])
    _ev(tmp_path, "m0|F000|D2+H3|profit", ["freeze/m0", "m0|F000|D2+H3|profit", "reference/m0/F000"])
    return tmp_path


def test_dependencies_follow_reference_and_bank_but_not_freeze(chain):
    got = A.flag_dependencies(chain, ["m0|C*|X7-SC|profit", "m0|F000|D2+H3|profit"], {"m0|F111|D2+H3|profit"}, _path_of)
    assert got["m0|C*|X7-SC|profit"] == ["m0|F111|D2+H3|profit"]
    assert got["m0|F000|D2+H3|profit"] == []     # reachable only through freeze, which is not a computational input


def test_a_flagged_cell_depends_on_itself(chain):
    got = A.flag_dependencies(chain, ["m0|F000|D2+H3|profit"], {"m0|F000|D2+H3|profit"}, _path_of)
    assert got["m0|F000|D2+H3|profit"] == ["m0|F000|D2+H3|profit"]


def test_unresolvable_upstream_refuses(chain):
    _ev(chain, "m0|F111|X7-SC|profit", ["reference/m0/GONE"])
    with pytest.raises(SystemExit, match="GONE"):
        A.flag_dependencies(chain, ["m0|F111|X7-SC|profit"], set(), _path_of)


def test_side_fields_are_per_market_means_of_a_minus_b(tmp_path):
    side = {"gross_eff_diff": "eff_attack", "ref_profit_diff": "profit_ref"}
    _ev(tmp_path, "m0@rho0.2|F111|D2+H3|profit", [], eff_attack=[0.9, 0.7], profit_ref=[2.0, 4.0])
    _ev(tmp_path, "m0@rho0.2|C*|D2+H3|profit", [], eff_attack=[0.8, 0.6], profit_ref=[1.0, 1.0])
    got = A.side_fields(tmp_path, ["m0"], ("F111", "C*"), ["D2+H3"], side)
    assert got["m0"]["C*-F111|D2+H3"] == pytest.approx({"gross_eff_diff": 0.1, "ref_profit_diff": 2.0})


def _inputs():
    report = {"q1": {"tests": {"C*-F111|D2+H3": {"category": "equivalent", "search": "flag"},
                               "C*-F111|X7-SC": {"category": "equivalent", "search": None}}},
              "q4": {"markets": {"fresh0": {"search": None}, "fresh1": {"search": "flag"}}}}
    cfg = {"ok": True, "markets": {"fresh0": {"recorded_hash": "a" * 64, "container_hash": "b" * 64, "pod_hashes": ["b" * 64],
                                              "differences": [["p", 1.0, 1.0, 1]], "within_one_ulp": True, "verify_exit": 0, "ok": True}}}
    ledger = {"caps": {"evaluation": 43.0}, "approval": {"text": "Raise caps ... 43 USD, program limit 55 USD"},
              "spent": [{"op": "evaluation", "tag": "x", "usd": 1.5}]}
    deps = {"q1": {"C*-F111|X7-SC": ["fresh0@rho0.2|C*|D2+H3|profit"], "C*-F111|D2+H3": ["fresh0@rho0.2|C*|D2+H3|profit"]}, "q4": {"fresh0": ["fresh0@rho0.2|C*|D2+H3|profit"], "fresh1": []}}
    return report, cfg, ledger, deps


def test_render_states_labels_scope_deviations_and_dependencies():
    report, cfg, ledger, deps = _inputs()
    md = A.render(A.build(report, cfg, "c" * 64, ledger, deps, {"fresh0": {}}))
    for s in ("nominal 95 percent, unadjusted", "nominal one-sided 97.5 percent", "0.05/c", "Bonferroni", "Holm",
              "six sampled markets", "internal replication", "not the complete amended PASS predicate",
              "a" * 64, "b" * 64, "c" * 64, "40", "43", "not verified", "C*-F111|X7-SC", "fresh0@rho0.2|C*|D2+H3|profit"):
        assert s in md, s


def test_build_marks_new_qualifications_only_where_the_report_has_none():
    report, cfg, ledger, deps = _inputs()
    add = A.build(report, cfg, "c" * 64, ledger, deps, {})
    assert add["search_dependencies"]["q1"]["C*-F111|X7-SC"]["new_qualification"] is True
    assert add["search_dependencies"]["q1"]["C*-F111|D2+H3"]["new_qualification"] is False   # already labelled
    assert add["search_dependencies"]["q4"]["fresh0"]["new_qualification"] is True
    assert add["search_dependencies"]["q4"]["fresh1"]["new_qualification"] is False   # already labelled by the report


def test_build_refuses_a_failed_deviation_check():
    report, cfg, ledger, deps = _inputs()
    cfg["ok"] = False
    with pytest.raises(SystemExit, match="deviation check"):
        A.build(report, cfg, "c" * 64, ledger, deps, {})


def test_a_passed_stability_check_replaces_not_verified():
    report, cfg, ledger, deps = _inputs()
    stab = {"decisions_unchanged": True, "decision_diffs": [], "cells": {"a": {"seeds_changed": 5, "mean_old": 0.1, "mean_new": 0.104}}}
    add = A.build(report, cfg, "c" * 64, ledger, deps, {}, stab, "d" * 64)
    md = A.render(add)
    assert add["deviations"]["decision_stability"] == "verified: every Q1 and Q4 decision unchanged"
    assert "not verified" not in md and "d" * 64 in md and "0.004" in md


def test_a_failed_stability_check_lists_the_changed_decisions():
    report, cfg, ledger, deps = _inputs()
    stab = {"decisions_unchanged": False, "decision_diffs": ["q4 k: 3 -> 4"], "cells": {}}
    md = A.render(A.build(report, cfg, "c" * 64, ledger, deps, {}, stab, "d" * 64))
    assert "q4 k: 3 -> 4" in md and "changed" in md


def test_stability_text_does_not_understate_the_largest_mean_change():
    """Round-5 review: 0.00737 printed as 'at most 0.007' understates it; four decimals keep the bound true."""
    dev = {"stability": {"sha256": "x", "diffs": [], "cells": 36, "cells_with_seed_changes": 30, "max_mean_shift": 0.007372580557210351}}
    assert "at most 0.0074" in A._stab_text(dev)
