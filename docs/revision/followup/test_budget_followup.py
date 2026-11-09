"""The follow-up budget category (reset plan draft 4, section 7) on top of the frozen scripts/budget_v2.py."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import budget_followup as B  # noqa: E402


def _ledger(tmp_path):
    p = tmp_path / "l.json"
    p.write_text(json.dumps({"caps": {"development": 12.0, "evaluation": 43.0}, "reservations": [],
                             "spent": [{"op": "development", "tag": "x", "usd": 11.42}, {"op": "evaluation", "tag": "y", "usd": 39.449}],
                             "approval": {"limit": 55.0, "text": "earlier approval (author)"}}))
    return p


def test_no_followup_reservation_before_the_written_approval(tmp_path):
    p = _ledger(tmp_path)
    with pytest.raises(B.Refused, match="no cap"):
        B.reserve(p, "reset-pod", 2.1)


def test_the_approval_adds_the_category_and_its_limit(tmp_path):
    p = _ledger(tmp_path)
    assert B.main(["--ledger", str(p), "--approve", "61", "10", "Approve the reset experiment. (author)"]) == 0
    d = json.loads(p.read_text()); assert d["caps"]["followup"] == 10.0 and d["approval"]["limit"] == 61.0
    assert B.reserve(p, "reset-pod", 2.1) == pytest.approx(2.625)               # 50.869 + 2.625 within 61
    with pytest.raises(B.Refused):
        B.reserve(p, "reset-pod-2", 7.5)                                         # 10 - 2.625 = 7.375 left, below the estimate


@pytest.mark.parametrize("limit,cap,text", [(61, float("nan"), "ok"), (61, 10, " "), (0, 10, "ok")])
def test_invalid_approvals_are_refused(tmp_path, limit, cap, text):
    p = _ledger(tmp_path)
    with pytest.raises(B.Refused):
        B.approve(p, limit, cap, text)
    assert "followup" not in json.loads(p.read_text())["caps"]


def test_an_existing_category_is_never_changed(tmp_path):
    p = _ledger(tmp_path); B.approve(p, 61, 10, "Approve. (author)")
    with pytest.raises(B.Refused, match="already"):
        B.approve(p, 70, 20, "Raise it. (author)")
    assert json.loads(p.read_text())["caps"]["followup"] == 10.0
