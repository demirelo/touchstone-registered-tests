"""Tests for check_letter_tables.py: every table number in a letter carries its label, and the number matches the paper."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_letter_tables as C  # noqa: E402

AUX = "\\newlabel{tab:q4}{{8}{14}{x}{table.8}{}}\n\\newlabel{tab:ph-welfare}{{11}{16}{x}{table.11}{}}\n"


def test_labelled_numbers_that_match_pass():
    assert C.problems("See Table 8 (tab:q4) and Table 11 (tab:ph-welfare).", AUX) == []


def test_a_wrong_number_fails():
    assert C.problems("See Table 9 (tab:q4).", AUX)


def test_an_unlabelled_table_number_fails():
    assert C.problems("See Table 8 for details.", AUX)


def test_an_unknown_label_fails():
    assert C.problems("See Table 3 (tab:none).", AUX)
