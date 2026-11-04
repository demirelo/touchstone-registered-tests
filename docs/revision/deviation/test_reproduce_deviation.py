"""Tests for reproduce_deviation.substitution_problems: the substituted instance file may differ from the registered one
only in fresh-market calibrated_cfg floats, each by at most one ulp."""
import copy
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reproduce_deviation as D  # noqa: E402

REG = {"salt_sha256": "s", "confirmatory": True,
       "markets": {"fresh0": {"calibrated_cfg": {"providers": [[0.5, 2.0]], "alpha": 1.0}, "seeds": [1, 2]},
                   "headline": {"calibrated_cfg": {"providers": [[0.25]]}}}}


def test_one_ulp_in_a_fresh_config_is_accepted():
    sub = copy.deepcopy(REG); sub["markets"]["fresh0"]["calibrated_cfg"]["providers"][0][0] = math.nextafter(0.5, 1.0)
    assert D.substitution_problems(REG, sub) == []


def test_two_ulps_are_refused():
    sub = copy.deepcopy(REG); x = math.nextafter(math.nextafter(0.5, 1.0), 1.0)
    sub["markets"]["fresh0"]["calibrated_cfg"]["providers"][0][0] = x
    assert D.substitution_problems(REG, sub)


def test_a_change_outside_fresh_configs_is_refused():
    sub = copy.deepcopy(REG); sub["markets"]["fresh0"]["seeds"] = [1, 3]
    assert D.substitution_problems(REG, sub)
    sub = copy.deepcopy(REG); sub["markets"]["headline"]["calibrated_cfg"]["providers"][0][0] = math.nextafter(0.25, 1.0)
    assert D.substitution_problems(REG, sub)
    sub = copy.deepcopy(REG); sub["salt_sha256"] = "t"
    assert D.substitution_problems(REG, sub)
