"""Tests for stability.compare: decision fields that move are reported; estimates alone do not count."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stability as S  # noqa: E402

BASE = {"q1": {"tests": {"C*-F111|D2+H3": {"category": "equivalent", "reject": True, "efficiency": "met", "better": None, "estimate": 0.02}}},
        "q4": {"k": 3, "passing": ["fresh1"], "failing": ["fresh0"], "undecided": [], "decided": True}}


def test_identical_decisions_with_moved_estimates_report_nothing():
    new = copy.deepcopy(BASE); new["q1"]["tests"]["C*-F111|D2+H3"]["estimate"] = 0.021
    assert S.compare(BASE, new) == []


def test_a_changed_category_or_count_is_reported():
    new = copy.deepcopy(BASE); new["q1"]["tests"]["C*-F111|D2+H3"]["category"] = "materially lower"; new["q4"]["k"] = 4
    got = S.compare(BASE, new)
    assert any("category" in d for d in got) and any(d.startswith("q4 k") for d in got)
