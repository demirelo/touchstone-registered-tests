"""Run B (docs/revision/followup2/convergence-plan.md): further doublings of the flagged profit cells until the doubling
check passes or the cap is reached."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import convergence_v2 as B  # noqa: E402
from sim.records_v2 import read, write  # noqa: E402

MAIN = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")


def test_flagged_cells_split_into_profit_and_coalition():
    rep = {"doubling": {"a|F111|D2+H3|profit": {"kind": "profit", "incomplete": True}, "b|C*|X6-SE/v2|total|c2_s": {"kind": "coalition", "incomplete": True},
                        "c|F000|D2+H3|profit": {"kind": "profit", "incomplete": False}}}
    assert B.flagged(rep) == {"profit": ["a|F111|D2+H3|profit"], "coalition": ["b|C*|X6-SE/v2|total|c2_s"]}


@pytest.mark.skipif(not (MAIN / "report/report.json").is_file(), reason="needs the report")
def test_the_registered_report_has_14_flagged_profit_cells_and_7_coalition_cells():
    f = B.flagged(json.loads((MAIN / "report/report.json").read_text()))
    assert len(f["profit"]) == 14 and len(f["coalition"]) == 7


def test_round_seeds_never_repeat_a_cma_seed():
    R5 = 5
    used = set(range(2, R5 + 2))                                            # the registered search: cma_search(seed 1)
    for k in (1, 2, 3):
        s = B.cma_seeds(k, R5)
        assert len(s) == R5 and not (s & used); used |= s
    assert B.cma_seeds(1, R5) == set(range(R5 + 2, 2 * R5 + 2))             # round 1 = the registered doubling (seed 1)


@pytest.mark.parametrize("changes,stop", [([(0.01, 0.0), (0.004, 0.0)], 2), ([(0.001, 0.001)], 1), ([(0.01, 0.0), (0.006, 0.0), (0.02, 0.0)], None),
                                          ([(0.01, 0.0), (0.001, 0.005)], None)])
def test_stopping_rule_is_the_registered_doubling_threshold(changes, stop):
    rounds = [{"round": i + 1, "attack_change": a, "reference_change": r} for i, (a, r) in enumerate(changes)]
    assert B.passed_round(rounds) == stop


def test_round_one_is_checked_against_the_registered_doubling():
    reg = {"attack_change": 0.0175, "reference_change": 0.0}
    assert B.round1_agrees({"attack_change": 0.0175 + 1e-12, "reference_change": 0.0}, reg)
    assert not B.round1_agrees({"attack_change": 0.02, "reference_change": 0.0}, reg)


def test_recompute_substitutes_only_the_converged_cells(tmp_path):
    src, conv = tmp_path / "src", tmp_path / "conv"
    for m, gc, gr in (("fresh0", [0.2, 0.2], [0.1, 0.1]), ("fresh1", [0.3, 0.3], [0.1, 0.1])):
        write(B.R.eval_path(src, f"{m}@rho0.2|C*|D2+H3|profit"), {"seeds": [1, 2], "gain": gc})
        write(B.R.eval_path(src, f"{m}@rho0.2|F111|D2+H3|profit"), {"seeds": [1, 2], "gain": gr})
        write(B.R.eval_path(src, f"{m}@rho0.2|F000|D2+H3|profit"), {"seeds": [1, 2], "gain": [0.5, 0.5]})
    write(conv / "convergence" / (B.R._safe("fresh1@rho0.2|C*|D2+H3|profit") + ".json"),
          {"id": "fresh1@rho0.2|C*|D2+H3|profit", "heldout": {"seeds": [1, 2], "gain": [0.4, 0.4]}})
    got = B.recompute(src, conv, ("fresh0", "fresh1"), resamples=99)
    assert got["q1"]["frozen"]["estimate"] == pytest.approx(0.15) and got["q1"]["converged"]["estimate"] == pytest.approx(0.2)
    assert got["q4"]["converged"]["markets"]["fresh0"] == pytest.approx(0.4) and got["substituted"] == ["fresh1@rho0.2|C*|D2+H3|profit"]


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_smoke_path_for_one_flagged_fresh_cell(tmp_path):
    out = tmp_path / "conv"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--report", str(MAIN / "report/report.json"), "--draw", str(MAIN / "draw/draw.json"),
            "--instances", str(MAIN / "draw/instances.json"), "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"),
            "--cells", "fresh1@rho0.2|F111|D2+H3|profit", "--max-rounds", "2", "--smoke"]
    assert B.main(args) == 0
    rec = read(out / "convergence" / (B.R._safe("fresh1@rho0.2|F111|D2+H3|profit") + ".json"))
    assert 1 <= len(rec["rounds"]) <= 2 and rec["status"] in ("passed", "not passed at the cap") and len(rec["heldout"]["gain"]) == 2
    assert rec["rounds"][0]["restarts_total"] == 2 * rec["restarts"] and (out / "inventory.json").exists()
