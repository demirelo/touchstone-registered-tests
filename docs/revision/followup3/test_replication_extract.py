"""Tests for replication_extract.py: the allocation, the cell parser, the extract builder and the committed binding."""
import hashlib
import json
from pathlib import Path

import pytest

import replication_extract as RE

HERE = Path(__file__).resolve().parent


def _shares():
    # two episodes, two age bins; [served, audited]
    e = {"honest_replacement": [[10, 4], [20, 1]], "honest_initial": [[5, 1], [15, 3]], "focal": [[4, 2], [6, 0]]}
    return {"per_episode": [e, e]}


def test_allocation_matches_hand_count():
    a = RE.allocation(_shares())
    served, audits = 2 * (10 + 20 + 5 + 15 + 4 + 6), 2 * (4 + 1 + 1 + 3 + 2 + 0)
    assert a["young_honest_job_share"] == pytest.approx(2 * 15 / served)
    assert a["young_honest_audit_share"] == pytest.approx(2 * 5 / audits)
    assert a["established_honest_audit_rate"] == pytest.approx(4 / 35)
    assert a["focal_job_share"] == pytest.approx(20 / served)
    assert a["focal_audit_rate"] == pytest.approx(4 / 20)


def test_allocation_zero_denominator_is_none():
    e = {"honest_replacement": [[0, 0], [0, 0]], "honest_initial": [[0, 0], [0, 0]], "focal": [[0, 0], [0, 0]]}
    a = RE.allocation({"per_episode": [e]})
    assert all(v is None for v in a.values())


def test_parse_cell_accepts_the_run_shapes():
    assert RE.parse_cell("menu-p0.05__fresh3@rho0.2__F111__D2+H3__profit__churn0.05") == \
        {"kind": "menu", "rate": "0.05", "market": "rep3", "policy": "F111"}
    assert RE.parse_cell("cthr-p0__fresh0@rho0.2__Cstar__D2+H3__profit")["rate"] == "0"


@pytest.mark.parametrize("stem", ["menu-p0.05__fresh3@rho0.2__F111__D2+H3__profit__churn0.03",   # suffix disagrees
                                  "menu-p0__fresh3@rho0.2__F111__D2+H3__profit__churn0.05",      # churn at p = 0
                                  "menu-p0.05__fresh3@rho0.2__F111__D2+H3__profit",              # suffix missing
                                  "menu-p0.05__fresh6@rho0.2__F111__D2+H3__profit__churn0.05",   # no such market
                                  "menu-p0.05__fresh3@rho0.2__F222__D2+H3__profit__churn0.05",   # no such policy
                                  "menu-p0.02__fresh3@rho0.2__F111__D2+H3__profit__churn0.02",   # no such rate
                                  "cthr-p0__fresh1@rho0.2__F111__D2+H3__profit"])                # cthr on another policy
def test_parse_cell_refuses_other_shapes(stem):
    with pytest.raises(ValueError):
        RE.parse_cell(stem)


def _col(continued=2):
    c0, c1 = RE.Counts((5, 10)), RE.Counts((1, 10))
    c0.alloc, c1.alloc = {"focal_audit_rate": 0.5}, {"focal_audit_rate": 0.1}
    return {"audit": {"frozen": {"0": {"rep0": c0}, "0.05": {"rep0": c1}}, "primary": {"0": {"rep0": c0}}},
            "counts": {"continued": continued, "frozen": 1, "unresolved": 0}, "problems": [], "unscorable": [],
            "round1_mismatch": False, "gate_ok": True}


SAFE = lambda k: k.replace("|", "__")
WIN = {"menu-p0.05|fresh3@rho0.2__F111__D2+H3__profit__churn0.05": "continued",
       "cthr-p0|fresh0@rho0.2__Cstar__D2+H3__profit": "continued",
       "menu-p0|fresh1@rho0.2__F111__D2+H3__profit": "frozen"}


def test_build_keeps_counts_alloc_status_and_only_winning_continuations():
    r = RE.build(_col(), WIN, SAFE, {"analysis": "a"})
    assert r["audit"]["frozen"]["0.05"]["rep0"] == [1, 10]
    assert r["alloc"]["frozen"]["0"]["rep0"] == {"focal_audit_rate": 0.5}
    assert [c["market"] for c in r["continued"]] == ["rep0", "rep3"]          # the "frozen" outcome is not listed
    assert r["status"] == {"problems": [], "unscorable": [], "round1_mismatch": False, "gate_ok": True}
    assert r["binding"] == {"analysis": "a"}


def test_build_refuses_a_count_mismatch():
    with pytest.raises(ValueError):
        RE.build(_col(continued=3), WIN, SAFE, {})


def test_build_refuses_a_duplicate_identity():
    with pytest.raises(ValueError):
        RE.build(_col(), {"a|x": "continued", "a__x": "continued"}, lambda k: "menu-p0__fresh1@rho0.2__F111__D2+H3__profit", {})


def test_committed_extract_is_bound_to_the_committed_analysis():
    ex = json.loads((HERE / "replication-extract.json").read_text())
    assert ex["binding"]["analysis"] == hashlib.sha256((HERE / "replication-analysis.json").read_bytes()).hexdigest()
    assert ex["status"] == {"problems": [], "unscorable": [], "round1_mismatch": False, "gate_ok": True}


def test_recompute_matches_the_analyse_stage_layout():
    col = {"counts": {"continued": 0}, "round1_mismatch": False, "gate_ok": True, "problems": [], "unscorable": [],
           "primary": None, "frozen": {"g": 1}, "audit": {"frozen": {"0": {"rep0": RE.Counts((1, 2))}}, "primary": {}}}
    seen = {}
    out = json.loads(RE.recompute(col, True, lambda g, au: seen.update(au=au) or {"ok": g}))
    assert out["confirmatory"] is True and out["frozen"] == {"ok": {"g": 1}} and out["primary"].startswith("not available")
    assert seen["au"] == {"0": {"rep0": (1, 2)}}


# Rebuild with `replication_extract.py --out <analysed clone> ... --check replication-extract.json` before changing this.
EXTRACT_SHA256 = "36e7c69be53db5c606c2a0ff365c4cae380efe4db081da35fba0eec8a9750cae"


def test_committed_extract_is_pinned():
    """Values that exist only in the extract (allocation, x, counts) are authenticated by this pin: the committed file was
    rebuilt from the run records with --check (byte-identical) on 2026-11-24; any later edit fails here."""
    assert hashlib.sha256((HERE / "replication-extract.json").read_bytes()).hexdigest() == EXTRACT_SHA256


def test_refuses_an_out_dir_without_analysis(tmp_path):
    with pytest.raises(SystemExit):
        RE.main(["--out", str(tmp_path), "--manifest", "m", "--draw", "d", "--check", "x"])
    assert list(tmp_path.iterdir()) == []                 # nothing written before the refusal


def test_records_digest_ignores_analysis_and_sees_any_record_change(tmp_path):
    (tmp_path / "a").mkdir(); (tmp_path / "a" / "r.json").write_text("1"); (tmp_path / "analysis.json").write_text("x")
    n, d = RE.records_digest(tmp_path)
    (tmp_path / "analysis.json").write_text("y")
    assert RE.records_digest(tmp_path) == (n, d) and n == 1
    (tmp_path / "a" / "r.json").write_text("2")
    assert RE.records_digest(tmp_path)[1] != d
