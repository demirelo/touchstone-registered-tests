"""Tests for cfg_ulp.py, the check behind the 2026-11-04 deviation: the pods recalibrated the fresh-market configs on
Linux x86 and a few values differ from instances.json (computed on the Mac) by one unit in the last place."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cfg_ulp as U  # noqa: E402

REC = {"providers": [[0.9, 1.0, 0.4461948910398329], [0.95, 1.0, 0.25]], "beta": 0.05, "n": 10}


def _bump(x, k):
    for _ in range(k):
        x = math.nextafter(x, math.inf)
    return x


def test_identical_configs_have_no_differences():
    assert U.diffs(REC, REC) == []


def test_one_ulp_difference_is_found_and_counted():
    lin = {**REC, "providers": [[0.9, 1.0, _bump(REC["providers"][0][2], 1)], [0.95, 1.0, 0.25]]}
    d = U.diffs(REC, lin)
    assert [(p, u) for p, _, _, u in d] == [(".providers[0][2]", 1)]
    assert U.within(d, 1)


def test_two_ulp_difference_fails_the_one_ulp_bound():
    lin = {**REC, "providers": [[0.9, 1.0, _bump(REC["providers"][0][2], 2)], [0.95, 1.0, 0.25]]}
    assert not U.within(U.diffs(REC, lin), 1)


def test_structural_or_nonfloat_difference_fails():
    assert not U.within(U.diffs(REC, {**REC, "n": 11}), 1)
    assert not U.within(U.diffs(REC, {k: v for k, v in REC.items() if k != "beta"}), 1)
    assert not U.within(U.diffs(REC, {**REC, "providers": REC["providers"][:1]}), 1)


def test_pod_hash_must_be_unique_and_equal_to_the_container_hash():
    assert U.pod_hash_ok({"a", }, "a")
    assert not U.pod_hash_ok({"a", "b"}, "a")
    assert not U.pod_hash_ok({"b"}, "a")
    assert not U.pod_hash_ok(set(), "a")
