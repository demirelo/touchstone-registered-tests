"""Market generator, domain-separated streams, evaluation and coverage seeds (design 7.1, 7.2)."""
import hashlib

import numpy as np
import pytest

from sim.amendment import _registered_ranges
from sim.locked import load_locked


def test_digest_encoding():
    from sim.instances import digest
    assert digest("r", "d", 3) == hashlib.sha256(b"r|touchstone-v2|d|3").digest()


def test_stream_is_index_independent():
    from sim.instances import stream
    a = stream("root", 1).random(5)
    stream("root", 0).random(1000)
    assert np.array_equal(stream("root", 1).random(5), a)
    assert int.from_bytes(hashlib.sha256(b"root|touchstone-v2|instance|1").digest()[:16], "big") > 0


def test_draw_fixed_parameters_and_ranges():
    from sim.instances import draw_instance, stream
    for i in range(10):
        cfg, rej = draw_instance(stream("t", i))
        assert (cfg.N, cfg.J, cfg.T, cfg.sigma, cfg.e, cfg.v_min) == (10, 50, 200, 0.05, 0.0, 0.6)
        q = [p.q_max for p in cfg.providers]
        assert q == sorted(q) and all(0.55 <= v <= 1.0 for v in q)
        assert all(4 <= p.k <= 8 for p in cfg.providers) and 1.2 <= cfg.v_max <= 1.6 and all(0 <= p.a <= 0.05 for p in cfg.providers)
        assert rej >= 0


def test_b_is_decreasing_in_rank_up_to_noise():
    from sim.instances import draw_instance, stream
    cfg, _ = draw_instance(stream("t", 3))
    b = [p.b for p in cfg.providers]
    assert all(b[i + 1] <= b[i] + 0.04 + 1e-12 for i in range(9)) and b[0] > b[-1]


def test_draw_passes_validate():
    from sim.instances import draw_instance, stream
    cfg, _ = draw_instance(stream("t", 5)); cfg.validate()


def test_draw_matches_independent_reimplementation():
    from sim.instances import draw_instance, stream
    cfg, rej = draw_instance(stream("dev-20261022", 0))
    assert rej == 0                                           # the reimplementation below assumes the first attempt is valid
    g = np.random.Generator(np.random.PCG64(int.from_bytes(hashlib.sha256(b"dev-20261022|touchstone-v2|instance|0").digest()[:16], "big")))
    q = np.sort(g.uniform(0.55, 1.0, 10)); blo = g.uniform(0.18, 0.26); bhi = g.uniform(0.34, 0.46); nz = g.uniform(-0.02, 0.02, 10)
    a = g.uniform(0.0, 0.05, 10); k = g.integers(4, 9, size=10); vmax = g.uniform(1.2, 1.6)
    b = [bhi - (bhi - blo) * r / 9 + nz[r] for r in range(10)]
    assert [p.q_max for p in cfg.providers] == pytest.approx(list(q)) and [p.b for p in cfg.providers] == pytest.approx(b)
    assert [p.a for p in cfg.providers] == pytest.approx(list(a)) and [p.k for p in cfg.providers] == list(k) and cfg.v_max == pytest.approx(vmax)


def test_limit_replacement_keeps_label_order(monkeypatch):
    import sim.instances as I
    real = I._draw_stream

    def fake(root, i, limit):
        if i == 0:
            raise I.InstanceLimit("forced")
        return real(root, i, limit)
    monkeypatch.setattr(I, "_draw_stream", fake)
    ms = I.markets("r", 6)
    assert [m["label"] for m in ms] == [f"fresh{i}" for i in range(6)]
    assert [m["stream_index"] for m in ms] == [6, 1, 2, 3, 4, 5]


def test_dev_markets_labels():
    from sim.instances import dev_markets
    ms = dev_markets()
    assert [m["label"] for m in ms] == ["dev0", "dev1"] and [m["stream_index"] for m in ms] == [0, 1]


def test_eval_seeds_range_unique_and_count():
    from sim.instances import digest, eval_seeds
    s = eval_seeds("abc", "fresh0")
    assert len(s) == 200 == len(set(s)) and all(30_000_000 <= v < 40_000_000 for v in s)
    assert s[0] == 30_000_000 + int.from_bytes(digest("abc", "seeds/fresh0", 0)[:8], "big") % 10_000_000
    assert eval_seeds("abc", "headline") != s


def test_identity_salt_hex():
    from sim.instances import identity_salt_hex
    h = identity_salt_hex("abc")
    assert len(h) == 64 and h == hashlib.sha256(b"abc|touchstone-v2|salt|0").hexdigest()


def test_seed_ranges_disjoint():
    from sim.instances import COVERAGE_RANGE, EVAL_RANGE, coverage_pool
    reserved = _registered_ranges(load_locked()) + [("amendment-1", 6_600_000, 9_000_000)]
    for lo, hi in (EVAL_RANGE, COVERAGE_RANGE):
        for _, a, b in reserved:
            assert hi <= a or lo >= b
    assert EVAL_RANGE[1] <= COVERAGE_RANGE[0]
    pool = coverage_pool("dev0", 1000)
    assert len(set(pool)) == 1000 and all(COVERAGE_RANGE[0] <= v < COVERAGE_RANGE[1] for v in pool)


def test_calibrated_sets_budget_and_alpha():
    from sim.instances import calibrated, dev_markets
    cfg = calibrated(dev_markets()[0]["cfg"])
    assert cfg.budget > 0 and cfg.alpha > 0
