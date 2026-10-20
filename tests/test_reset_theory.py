"""Theorem checks (docs/theory/reset-deterrence.md section 8; plan docs/superpowers/plans/2026-10-21-theorem-and-robustness.md Task 2)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from sim.calibrate import cell_config, load_calibration
from sim.locked import load_locked, market_config_from_locked
from sim.market import run_episode
from sim.policies.base import ProviderHistory, ProviderView
from sim.policies.honest import HonestMax
from sim.positions import positions
from sim.registry import make_rule, proposed_params


def cfg_beta(beta=0.05):
    lk = load_locked()
    return cell_config(market_config_from_locked(lk), load_calibration("experiments/calibration.json"), rho=0.2, beta=beta)


def r3_params():
    p = proposed_params(); return dict(p.get("best_params", p))


def r3():
    return make_rule("proposed", r3_params())


def episode(policy, rule, seed=2000, beta=0.05):
    cfg = cfg_beta(beta); f = positions(cfg)["median"]; pols = [HonestMax() for _ in range(cfg.N)]; pols[f] = policy
    return cfg, f, run_episode(cfg, rule, pols, seed)


def test_fixed_shade_honest_while_fresh_and_resets_or_waits():
    from sim.policies.theory_diag import FixedShade
    cfg = cfg_beta(); p = cfg.providers[4]; h = ProviderHistory(); ident = 0
    pol = FixedShade(delta=0.2, reset=True)
    acts = []
    for t in range(25):
        a = pol.act(ProviderView(i=4, params=p, t=t, posted_prices=None, history=h, policy_seed=0, identity=ident))
        acts.append(a); ident += int(a.exit)
        h.append(6, 3.0, 1, int(t == 14), 0.0, 25 if t == 14 else 0)
    assert all(a.effort == p.q_max for a in acts[:10]) and all(abs(a.effort - (p.q_max - 0.2)) < 1e-12 for a in acts[10:15])
    assert all(a.offer.claim == p.q_max and abs(a.offer.bid - (p.a + p.b * p.q_max)) < 1e-12 for a in acts)
    assert acts[15].exit and all(a.effort == p.q_max for a in acts[15:25])              # fresh again for 10 rounds
    w = FixedShade(delta=0.2, reset=False); h2 = ProviderHistory()
    for t in range(20):
        a = w.act(ProviderView(i=4, params=p, t=t, posted_prices=None, history=h2, policy_seed=0, identity=0))
        assert not a.exit
        h2.append(6, 3.0, 1, int(t == 14), 0.0, 25 if t == 14 else 0)


def test_round_table_matches_episode_ledger():
    from scripts.check_reset_theory import round_table
    from sim.policies.theory_diag import FixedShade
    for RN, RP in (("B3", {"tol": 0.16, "L": 10}), ("proposed", r3_params())):
        cfg, f, res = episode(FixedShade(0.24, True), make_rule(RN, RP))
        tab = round_table(res, cfg, RN, RP, f)
        assert len(tab) == cfg.T
        assert sum(r["profit"] for r in tab) == pytest.approx(float(res.profit[f]))
        assert sum(r["S"] for r in tab) == int(res.served[:, f].sum())
        assert sum(r["failures"] for r in tab) == int(res.failures[:, f].sum())
        assert sum(r["refunds"] for r in tab) == pytest.approx(sum(float(res.ledger.refunds[:, i].sum()) for i, e in enumerate(res.entity_of) if e == f))
        assert all(r["audited_payment"] <= r["payment"] + 1e-9 and r["K"] <= r["S"] for r in tab)


def test_hazard_from_K_distribution_not_pooled_rate():
    from scripts.check_reset_theory import hazard_from_K
    d = 0.9
    rows = [{"K": 6}, {"K": 0}]                                    # pooled rate 0.5 of 6 jobs would give 1 - (1 - 0.45)^6
    assert hazard_from_K(rows, d) == pytest.approx(0.5 * (1 - (1 - d) ** 6))
    pooled = 1 - (1 - 0.5 * d) ** 6
    assert abs(hazard_from_K(rows, d) - pooled) > 0.04


def test_recovery_duration_formula():
    from scripts.check_reset_theory import expected_recovery
    rng = np.random.default_rng(0); r, L = 0.8, 4
    sims = []
    for _ in range(20000):
        run = n = 0
        while run < L:
            n += 1; run = run + 1 if rng.random() < r else 0
        sims.append(n)
    assert expected_recovery(r, L) == pytest.approx(np.mean(sims), rel=0.02)
    assert expected_recovery(1.0, 10) == 10


def test_renewal_identity_on_synthetic_cycles():
    from scripts.check_reset_theory import renewal_profit
    # established reward 2 per round with hazard 0.25 (mean spell 4), recovery 10 rounds earning 1 each, no entry charge
    assert renewal_profit(r_E=2.0, q_E=0.25, ER_F=10.0, ED=10.0, e_in=0.0, EN_R=1.0) == pytest.approx((2 / 0.25 + 10) / (4 + 10))
    from scripts.check_reset_theory import surplus_bound
    assert surplus_bound(G_E=1.0, q_E=0.5, eps=0.0, L=10) == pytest.approx(1 / 6)
    assert surplus_bound(G_E=-1.0, q_E=0.5, eps=0.1, L=10) == pytest.approx(0.1)


def test_terminal_impossibility_from_loaded_parameters():
    from scripts.check_reset_theory import terminal_margin
    cfg = cfg_beta()
    m = terminal_margin(cfg, tol=0.16)
    assert m["subtracted_max"] < 0.067 and m["b_min"] >= 0.22 and m["profitable"]
    phi = math.exp(-3.2 ** 2 / 2) / math.sqrt(2 * math.pi)
    assert m["subtracted_max"] == pytest.approx(cfg.v_max * phi / cfg.sigma)


def test_initial_versus_replacement_established_rates_split_by_generation():
    from scripts.check_reset_theory import round_table, established_rates
    from sim.policies.theory_diag import FixedShade
    RN, RP = "proposed", r3_params()
    cfg, f, res = episode(FixedShade(0.24, True), make_rule(RN, RP))
    tab = round_table(res, cfg, RN, RP, f)
    rates = established_rates(tab)
    assert set(rates) == {"initial", "replacement"}
    if rates["replacement"]["rounds"] > 0:
        assert rates["replacement"]["K_per_S"] >= 5 / 6 - 1e-9 or rates["replacement"]["rounds"] < 3   # Lemma 2b at the headline market


def test_round_table_quota_reconstruction():
    """R3's available quota and carry are rebuilt from the configuration and the audit history; the audits performed
    equal min(available, served, audits left) every round, and unused quota carries."""
    from scripts.check_reset_theory import round_table
    from sim.policies.theory_diag import FixedShade
    RN, RP = "proposed", r3_params()
    cfg, f, res = episode(FixedShade(0.24, True), make_rule(RN, RP), beta=0.10)
    tab = round_table(res, cfg, RN, RP, f)
    assert all(r["k_available"] is not None for r in tab)
    assert all(r["audits_round"] == min(r["k_available"], r["served_round"], r["audits_left"]) for r in tab)
    assert any(r["carry"] > 0 for r in tab) or all(r["k_available"] <= r["served_round"] for r in tab)


def test_age_group_quantities_against_selection():
    """H, n, s, k' of the focal age group equal what select_audits does: the focal group receives exactly k' audits."""
    from scripts.check_reset_theory import round_table
    from sim.policies.theory_diag import FixedShade
    RN, RP = "proposed", r3_params()
    cfg, f, res = episode(FixedShade(0.24, True), make_rule(RN, RP), seed=2003)
    tab = round_table(res, cfg, RN, RP, f)
    fresh = [r for r in tab if r["phase"] == "fresh" and r["S"] > 0]
    assert fresh
    for r in fresh:
        assert r["group_audits"] == r["k_prime"] and r["k_prime"] == min(r["n"], max(0, r["k_available_capped"] - r["H"]))


def test_hypergeometric_enumeration_matches_age_group_selection():
    from scripts.check_reset_theory import hypergeom_pmf
    from sim.mechanisms.proposed import select_audits
    rng = np.random.default_rng(1); n, s, kprime, L = 12, 6, 5, 10
    counts = np.zeros(s + 1)
    for _ in range(4000):
        jobs = {0: list(range(s)), 1: list(range(s, n))}
        key = rng.random(n)
        chosen = select_audits(jobs, key, {0: 3, 1: 3}, {}, {0: s, 1: n - s}, "T1", kprime, 5, L)
        counts[sum(1 for j in chosen if j < s)] += 1
    pmf = hypergeom_pmf(n, s, kprime)
    assert np.allclose(counts / counts.sum(), pmf, atol=0.02)


def test_payment_audit_correlation_fixture():
    from scripts.check_reset_theory import surplus_terms
    rows = [{"S": 2, "K": 1, "payment": 2.0, "audited_payment": 1.8, "delta": 0.2, "b": 0.3}]
    w = surplus_terms(rows, tol=0.16, sigma=0.05)
    assert w["payment_weighted"] != pytest.approx(w["unweighted"])


def test_renewal_inapplicable_when_assumptions_fail():
    from scripts.check_reset_theory import apply_renewal
    base = {"reset": True, "delta": 0.24, "s_mode": 6}
    ok_rows = [{"phase": "established", "S": 6, "K": 6, "profit": 1.0, "failures": int(t % 3 == 2), "delta": 0.24, "t": t, "refunds": 0.0} for t in range(30)]
    out = apply_renewal(ok_rows + [{"phase": "fresh", "S": 6, "K": 6, "profit": 1.0, "failures": 0, "delta": 0.0, "t": 30 + t, "refunds": 0.0} for t in range(10)], h=0.5, cfg={**base, "L": 10, "tol": 0.16, "sigma": 0.05, "b": 0.3})
    assert "applicable" in out
    wait = apply_renewal(ok_rows, h=0.5, cfg={**base, "reset": False, "L": 10, "tol": 0.16, "sigma": 0.05, "b": 0.3})
    assert wait["applicable"] is False and "replacement after every failure" in " ".join(wait["failed_assumptions"])
    zero = apply_renewal([{**r, "failures": 0} for r in ok_rows], h=0.5, cfg={**base, "L": 10, "tol": 0.16, "sigma": 0.05, "b": 0.3})
    assert zero["applicable"] is False and "q_E > 0" in " ".join(zero["failed_assumptions"])
    vary = apply_renewal([{**r, "S": 2 + (r["t"] % 5)} for r in ok_rows], h=0.5, cfg={**base, "L": 10, "tol": 0.16, "sigma": 0.05, "b": 0.3})
    assert vary["applicable"] is False and "constant service" in " ".join(vary["failed_assumptions"])
    under = apply_renewal(ok_rows + [{"phase": "fresh", "S": 6, "K": 3, "profit": 1.0, "failures": 0, "delta": 0.0, "t": 40, "refunds": 0.0}], h=0.5, cfg={**base, "L": 10, "tol": 0.16, "sigma": 0.05, "b": 0.3})
    assert under["applicable"] is False and "full fresh auditing" in " ".join(under["failed_assumptions"])


def test_finite_reward_reconciliation_with_censoring():
    from scripts.check_reset_theory import round_table, finite_horizon
    from sim.policies.theory_diag import FixedShade
    RN, RP = "proposed", r3_params()
    cfg, f, res = episode(FixedShade(0.24, True), make_rule(RN, RP))
    tab = round_table(res, cfg, RN, RP, f)
    fh = finite_horizon(tab, L=10)
    assert fh["initial"] + fh["middle"] + fh["terminal"] == pytest.approx(float(res.profit[f]))
    assert fh["per_round"] == pytest.approx(float(res.profit[f]) / cfg.T)


def test_renewal_inapplicable_without_stationarity_or_with_mixed_generations():
    from scripts.check_reset_theory import apply_renewal
    cfgd = {"reset": True, "delta": 0.24, "L": 10, "tol": 0.16, "sigma": 0.05}
    early = [{"phase": "established", "S": 6, "K": 6, "profit": 1.0, "failures": int(t % 2 == 1), "delta": 0.24, "t": t, "refunds": 0.0, "generation": 1} for t in range(40)]
    late = [{"phase": "established", "S": 6, "K": 1, "profit": 3.0, "failures": int(t % 20 == 0), "delta": 0.24, "t": 40 + t, "refunds": 0.0, "generation": 1} for t in range(40)]
    out = apply_renewal(early + late, h=0.5, cfg=cfgd)
    assert out["applicable"] is False and "constant conditional established reward and hazard" in " ".join(out["failed_assumptions"])
    mixed = [{**r, "generation": 0 if r["t"] < 20 else 1, "K": 0 if r["t"] < 20 else 6} for r in early]
    out2 = apply_renewal(mixed, h=0.5, cfg=cfgd)
    assert out2["applicable"] is False and "single identity-generation class" in " ".join(out2["failed_assumptions"])
    one = [{**r, "failures": int(r["t"] == 39)} for r in early]
    out3 = apply_renewal(one, h=0.5, cfg=cfgd)
    assert out3["applicable"] is False and "at least two complete cycles" in " ".join(out3["failed_assumptions"])
