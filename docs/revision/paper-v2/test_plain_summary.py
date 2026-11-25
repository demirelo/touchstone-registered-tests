"""The plain-language summary may only state numbers the paper's number file holds (lesson 2026-11-25: a summary
number written from memory was wrong)."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARY = HERE.parent / "plain-summary.md"


def _site(name: str) -> str:
    return re.search(r"site@" + name + r"\\endcsname\{([^}]*)\}", (HERE / "numbers.tex").read_text()).group(1)


def test_summary_numbers_match_the_paper():
    s = SUMMARY.read_text()
    fa1, fa5 = (round(float(_site(n)) * 100, 1) for n in ("abs_ch_fa1", "abs_ch_fa5"))
    assert f"from {fa1:g}% to {fa5:g}%" in s
    assert f"on only {_site('abs_q4_k')} of the 6" in s
    assert f"met all {_site('abs_rp_met')} of its expectations" in s


def test_summary_has_no_other_percentages():
    allowed = {f"{round(float(_site(n)) * 100, 1):g}%" for n in ("abs_ch_fa1", "abs_ch_fa5")} | {"1%", "5%"}
    assert set(re.findall(r"\d+(?:\.\d+)?%", SUMMARY.read_text())) <= allowed
