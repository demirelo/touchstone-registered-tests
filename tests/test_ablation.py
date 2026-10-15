import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.ablation import EnforcementAblation, exclusion_by_allocation
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.honest import HonestMax


def cfgb(budget, T=20):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=0.0, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


class HoldAndLongBan(PostedRandomAudit):
    """A rule with hold-backs and 40-round bans; the ablation must strip both to B2's enforcement."""
    def enforce(self, records, view):
        cons = super().enforce(records, view)
        for j, amt in view.escrow.items():
            i = view.memory["owner"][j]
            cons.holdbacks[i] = cons.holdbacks.get(i, 0.0) + 0.2 * amt
        for i in list(cons.bans):
            cons.bans[i] = 40
        return cons
    def allocate(self, values_t, offers, view):
        out = super().allocate(values_t, offers, view)
        view.memory["owner"] = dict(out)
        return out


class Shunner(PostedRandomAudit):
    """Never allocates to an identity after it failed an audit; no bans."""
    def allocate(self, values_t, offers, view):
        shunned = view.memory.setdefault("shunned", set())
        out = super().allocate(values_t, {i: o for i, o in offers.items() if i not in shunned}, view)
        return out
    def enforce(self, records, view):
        cons = super().enforce(records, view)
        cons.bans.clear()
        for r in records:
            if r.failed:
                view.memory.setdefault("shunned", set()).add(r.provider)
        return cons


def test_ablation_uses_enforcer_consequences_and_rule_allocation():
    cfg = cfgb(budget=5.0)
    rule = HoldAndLongBan(0.25, 0.40, 0.55, tol=-10.0, L=40)        # every audit fails
    enforcer = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=3)
    abl = EnforcementAblation(rule, enforcer)
    assert abl.tol == rule.tol and abl.name.startswith("ablation(")
    res = run_episode(cfg, abl, [HonestMax() for _ in range(cfg.N)], 0)
    assert res.ledger.holdback_in.sum() == 0.0 and res.ledger.bond.sum() == 0.0
    bans = [c for rec in res.history for c in rec.consequences.bans.values()]
    assert bans and set(bans) == {3}
    res.ledger.check_conservation(0.0)
    d = abl.describe()
    assert d["ban_length"] == "3" and d["holdback"] == "none" and d["pricing"] == rule.describe()["pricing"]


def test_ablation_keeps_the_rules_enforce_time_memory():
    cfg = cfgb(budget=5.0, T=12)
    abl = EnforcementAblation(Shunner(0.25, 0.40, 0.55, tol=-10.0, L=10), PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=3))
    res = run_episode(cfg, abl, [HonestMax() for _ in range(cfg.N)], 0)
    assert any(v > 0 for v in exclusion_by_allocation(res).values())        # the shun list, written in enforce, still drives allocation
    bans = [c for rec in res.history for c in rec.consequences.bans.values()]
    assert bans and set(bans) == {3}                                        # consequences come from the enforcer


def test_exclusion_by_allocation_counts_shunned_rounds():
    cfg = cfgb(budget=5.0, T=12)
    res = run_episode(cfg, Shunner(0.25, 0.40, 0.55, tol=-10.0, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    ex = exclusion_by_allocation(res)
    assert any(v > 0 for v in ex.values())
    assert all(not rec.consequences.bans for rec in res.history)
    res2 = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
    ex2 = exclusion_by_allocation(res2)
    assert set(ex2) == set(range(res2.n_identities)) and all(v >= 0 for v in ex2.values())
    base = exclusion_by_allocation(res, after_failure=False)
    assert all(base[i] >= ex[i] for i in ex)            # the competition baseline counts at least the post-failure rounds
