"""Tests for replication_paper.py: the paper summary and table built from the committed analysis and extract."""
import json
import math
from pathlib import Path

import pytest

import replication_paper as RP

HERE = Path(__file__).resolve().parent


def _analysis():
    mk = lambda v: {f"rep{i}": v + 0.01 * i for i in range(6)}
    pc = lambda mean: {"complete": True, "lower": 5, "markets": mk(mean), "mean": mean, "t95": [mean - 0.1, mean + 0.1]}
    ab = lambda mean: {"complete": True, "markets": {}, "mean": mean, "pooled_ci95": [mean - 0.01, mean + 0.01],
                       "t95": [mean - 0.2, mean + 0.2]}
    terms = {p: {f"rep{i}": {r: {"attack": 0.3, "eff_attack": e, "gain": 0.1, "reference": 0.2}
                             for r, e in (("R3", 0.95 - float(p)), ("C*", 0.99), ("C-thr", 0.98), ("B3", 0.97))}
                 for i in range(6)} for p in ("0", "0.03", "0.05")}
    s = {"paired_changes": {p: {x: pc(-0.1 if p == "0.05" else -0.05) for x in "dqu"} for p in ("0.03", "0.05")},
         "absolute": {p: {x: ab(0.02 - float(p) * 4) for x in "dqu"} for p in ("0", "0.03", "0.05")},
         "criteria": {p: {x: {"material": True, "support": True} for x in "dqu"} for p in ("0.03", "0.05")},
         "expectations": {str(k): {"text": "t", "verdict": "met"} for k in range(1, 6)}, "terms": terms}
    return {"primary": s, "frozen": json.loads(json.dumps(s)), "counts": {"continued": 3, "frozen": 69},
            "gate_ok": True, "problems": [], "unscorable": [], "round1_mismatch": False, "confirmatory": True}


def _extract():
    au = {"0": {f"rep{i}": [80, 100] for i in range(6)}, "0.05": {f"rep{i}": [2 + i, 100] for i in range(6)},
          "0.03": {"rep0": [5, 100]}}
    return {"audit": {"primary": au, "frozen": au}, "counts": {"continued": 3, "frozen": 69},
            "continued": [{"kind": "menu", "rate": "0", "market": "rep2", "policy": "F111", "stem": "a"},
                          {"kind": "menu", "rate": "0.05", "market": "rep1", "policy": "Cstar", "stem": "b"},
                          {"kind": "cthr", "rate": "0.05", "market": "rep3", "policy": "Cstar", "stem": "c"}]}


def test_audit_shares_min_max_and_count_below():
    s = RP.summary(_analysis(), _extract())
    a = s["primary"]["audit"]
    assert a["0"]["focal_audit_min"] == pytest.approx(0.8) and a["0"]["focal_audit_max"] == pytest.approx(0.8)
    assert a["0.05"]["focal_audit_min"] == pytest.approx(0.02) and a["0.05"]["focal_audit_max"] == pytest.approx(0.07)
    assert a["0.05"]["markets"] == 6                      # markets with an audit count at this rate
    assert a["below"]["markets"] == 6                     # 0.05 below 0 on every market
    assert a["0.03"]["markets"] == 1                      # missing counts are not imputed


def test_zero_denominator_counts_as_not_below():
    ex = _extract(); ex["audit"]["primary"]["0.05"]["rep0"] = [0, 0]
    s = RP.summary(_analysis(), ex)
    assert s["primary"]["audit"]["below"]["markets"] == 5


def test_efficiency_means_per_rule():
    s = RP.summary(_analysis(), _extract())
    assert s["primary"]["eff"]["0.05"]["R3"]["eff"] == pytest.approx(0.90)
    assert s["primary"]["eff"]["0"]["C*"]["eff"] == pytest.approx(0.99)
    assert s["primary"]["eff"]["0.05"]["R3"]["eff_min"] == pytest.approx(0.90)


def test_continued_split_by_rate_and_rule():
    s = RP.summary(_analysis(), _extract())
    c = s["continued"]
    assert c["all"]["cells"] == 3 and c["0"]["cells"] == 1 and c["0.05"]["cells"] == 2 and c["0.03"]["cells"] == 0
    assert c["rules"]["R3"]["cells"] == 1 and c["rules"]["C-thr"]["cells"] == 1 and c["rules"]["C*"]["cells"] == 1


def test_counts_must_agree():
    ex = _extract(); ex["counts"] = {"continued": 4, "frozen": 68}
    with pytest.raises(ValueError):
        RP.summary(_analysis(), ex)


def test_refuses_a_failed_analysis():
    an = _analysis(); an["problems"] = ["x"]
    with pytest.raises(ValueError):
        RP.summary(an, _extract())


def test_table_has_both_sets_and_rates_and_no_nan():
    t = RP.table(_analysis())
    assert "primary" in t.lower() and "all-frozen" in t.lower()
    assert t.count("0.03") >= 2 and t.count("0.05") >= 2 and "nan" not in t.lower()
    assert "5/6" in t


def test_check_reports_stale_files(tmp_path):
    an, ex = _analysis(), _extract()
    RP.write(an, ex, tmp_path / "s.json", tmp_path / "t.tex")
    assert RP.check(an, ex, tmp_path / "s.json", tmp_path / "t.tex") == []
    (tmp_path / "t.tex").write_text("stale")
    assert RP.check(an, ex, tmp_path / "s.json", tmp_path / "t.tex")


def test_committed_files_are_current():
    an = json.loads((HERE / "replication-analysis.json").read_text())
    ex = json.loads((HERE / "replication-extract.json").read_text())
    tex = HERE.parent / "paper-v2" / "tables" / "replication.tex"
    assert RP.check(an, ex, HERE / "replication_paper.json", tex) == []
