"""Shared analysis of the follow-up runs (docs/revision/followup2): paired seed bootstrap and the descriptive Q1 category."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def test_pooled_difference_is_the_mean_of_market_means():
    a = {"m0": np.array([0.3, 0.5]), "m1": np.array([0.1, 0.1, 0.1])}
    b = {"m0": np.array([0.1, 0.1]), "m1": np.array([0.0, 0.0, 0.0])}
    got = C.pooled_paired(a, b, resamples=999, seed=0)
    assert got["markets"] == {"m0": pytest.approx(0.3), "m1": pytest.approx(0.1)} and got["estimate"] == pytest.approx(0.2)
    lo, hi = got["interval"]; assert lo <= 0.2 <= hi


def test_bootstrap_is_reproducible_and_pairs_seeds():
    rng = np.random.default_rng(1); x = rng.normal(size=50); y = x + 0.01
    a, b = {"m": y}, {"m": x}
    g1, g2 = C.pooled_paired(a, b, 999, 0), C.pooled_paired(a, b, 999, 0)
    assert g1 == g2 and g1["interval"][0] == pytest.approx(0.01) and g1["interval"][1] == pytest.approx(0.01)   # paired: no spread


@pytest.mark.parametrize("iv,cat", [((0.06, 0.08), "materially lower (R3 lower)"), ((-0.09, -0.06), "materially lower (comparator lower)"),
                                    ((0.01, 0.03), "equivalent, direction R3 lower"), ((-0.03, 0.03), "equivalent"),
                                    ((0.02, 0.07), "ordered, size not established"), ((-0.02, 0.07), "inconclusive")])
def test_descriptive_q1_category_uses_the_registered_margin(iv, cat):
    assert C.q1_category(iv) == cat


def test_unequal_seeds_are_refused():
    with pytest.raises(ValueError):
        C.pooled_paired({"m": np.zeros(2)}, {"m": np.zeros(3)}, 99, 0)
