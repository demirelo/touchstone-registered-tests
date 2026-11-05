"""Tests for posthoc_v2.py (exploratory analyses after the report; external review round 4): the Q1 split into attacked and
reference terms, the episode-mixture welfare frontier, and the per-market Q4 diagnostics."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import posthoc_v2 as P  # noqa: E402


def _rec(out, rid, **f):
    p = out / "evaluate" / (P.safe(rid) + ".json"); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(f))


def test_split_terms_add_up_to_the_gain_difference(tmp_path):
    s = [10.0, 10.0]
    _rec(tmp_path, "m0@rho0.2|C*|D2+H3|profit", profit_attack=[3.0, 5.0], profit_ref=[1.0, 1.0], sstar=s)
    _rec(tmp_path, "m0@rho0.2|F111|D2+H3|profit", profit_attack=[2.0, 2.0], profit_ref=[0.5, 0.5], sstar=s)
    got = P.split(tmp_path, ["m0"], "C*", "F111", "D2+H3", n=10)
    # g_C = (2, 4), g_F = (1.5, 1.5): d mean = 1.5; attacked term = (1, 3) mean 2; reference term = -(0.5, 0.5) mean -0.5
    assert got["pooled"]["estimate"] == pytest.approx(1.5)
    assert got["pooled"]["attacked"] == pytest.approx(2.0) and got["pooled"]["reference"] == pytest.approx(-0.5)


def test_mixture_weight_is_the_largest_with_a_nonnegative_lower_bound():
    rng = np.random.default_rng(0)
    gw0, gp = -0.1 + 0.001 * rng.standard_normal(200), 0.06 + 0.001 * rng.standard_normal(200)
    ew0, ep = np.full(200, 0.84), np.full(200, 1.0)
    m = P.mixture(gw0, ew0, gp, ep)
    assert 0.0 < m["weight"] < 0.375                          # 0.375 is where the mean gain reaches zero
    g = m["weight"] * gw0 + (1 - m["weight"]) * gp
    assert g.mean() - 1.645 * g.std(ddof=1) / np.sqrt(len(g)) >= 0
    assert m["efficiency"] == pytest.approx(m["weight"] * 0.84 + (1 - m["weight"]) * 1.0)


def test_no_mixture_when_the_profitable_policy_is_not_profitable():
    z = np.zeros(200)
    assert P.mixture(z - 0.1, z + 0.84, z - 0.01, z + 1.0)["weight"] == 0.0
