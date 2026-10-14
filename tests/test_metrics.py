import hashlib, subprocess, sys
import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.metrics import summarize, gain, harm
from sim.policies.honest import HonestMax
from sim.policies.fixed_cheat import FixedCheat
from sim.policies.twin import Twin
from sim.rng import make_draws


def cfgb(budget, T=60):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def honest(n):
    return [HonestMax() for _ in range(n)]


def test_summary_definitions():
    cfg = cfgb(1.0)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), honest(cfg.N), 0)
    s = summarize(res)
    assert s["gross_eff"] == pytest.approx((res.W + res.audit_cost) / res.sstar)
    assert s["net_eff"] == pytest.approx(res.W / res.sstar)
    assert s["audit_spend"] == pytest.approx(res.audit_cost / res.sstar)
    assert s["audited_fraction"] == pytest.approx(res.audits.sum() / res.served.sum())
    assert "profit_0" in s and "profit_9" in s


def test_full_cheat_on_b1_fixture_has_positive_gain():
    c = MarketConfig.default()
    cfg = MarketConfig(N=c.N, J=c.J, T=60, sigma=c.sigma, e=c.e, v_min=0.6, v_max=1.4,
                       providers=c.providers, alpha=c.alpha, budget=0.0)
    rule = PostedPrices(0.20, 0.35, 0.50)
    d = make_draws(cfg, 1); focal = 9
    att = honest(cfg.N); att[focal] = FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0)
    ref = honest(cfg.N); ref[focal] = Twin(FixedCheat(u=1.0, m=1.0, s=0.0, w=0.0, clip=0))
    a, b = run_episode(cfg, rule, att, 1, draws=d), run_episode(cfg, rule, ref, 1, draws=d)
    assert gain(a, b, focal) > 0.0


def test_harm_identity_holds():
    cfg = cfgb(1.0)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    d = make_draws(cfg, 2); focal = 7
    att = honest(cfg.N); att[focal] = FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0)
    ref = honest(cfg.N); ref[focal] = Twin(FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0))
    a, b = run_episode(cfg, rule, att, 2, draws=d), run_episode(cfg, rule, ref, 2, draws=d)
    acc, direct = harm(a, b, focal)
    assert acc == pytest.approx(direct, abs=1e-9)


def test_run_script_byte_identical(tmp_path):
    outs = [tmp_path / "a.csv", tmp_path / "b.csv"]
    for out in outs:
        subprocess.run([sys.executable, "scripts/run.py", "--rule", "B2", "--seed", "4", "--budget", "1.0",
                        "--T", "40", "--out", str(out)], check=True)
    assert hashlib.sha256(outs[0].read_bytes()).hexdigest() == hashlib.sha256(outs[1].read_bytes()).hexdigest()


class BondRule(PostedRandomAudit):
    """Test-only rule in the admissible class: holds back 20% of each round's
    release and forfeits bond on failure, so the harm identity meets bonds."""
    def enforce(self, records, view):
        from sim.mechanisms.base import Consequences
        cons = super().enforce(records, view)
        released = {}
        for j, amt in view.escrow.items():
            i = view.memory["owner"][j]
            released[i] = released.get(i, 0.0) + amt - cons.refunds.get(j, 0.0)
        failed = {r.provider for r in records if r.failed}
        for i, rel in released.items():
            if i in failed and view.bond[i] > 0:
                fail_escrow = sum(view.escrow[r.job] for r in records if r.failed and r.provider == i)
                cons.forfeits[i] = min(float(view.bond[i]), fail_escrow)
            hb = 0.2 * rel
            cons.holdbacks[i] = hb
        return cons

    def allocate(self, values_t, offers, view):
        out = super().allocate(values_t, offers, view)
        view.memory["owner"] = dict(out)
        return out


def test_harm_identity_and_conservation_hold_with_bonds():
    cfg = cfgb(5.0)   # 100 audits over 60 rounds so the cheater is audited and forfeits
    rule = BondRule(0.25, 0.40, 0.55, tol=0.12, L=10)
    d = make_draws(cfg, 2); focal = 7
    att = honest(cfg.N); att[focal] = FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0)
    ref = honest(cfg.N); ref[focal] = Twin(FixedCheat(u=0.5, m=0.5, s=0.0, w=0.0, clip=0))
    a, b = run_episode(cfg, rule, att, 2, draws=d), run_episode(cfg, rule, ref, 2, draws=d)
    assert a.ledger.holdback_in.sum() > 0 and a.ledger.forfeits.sum() > 0
    acc, direct = harm(a, b, focal)
    assert acc == pytest.approx(direct, abs=1e-9)
