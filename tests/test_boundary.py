import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.base import Offer
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.policies.base import Action
from sim.policies.honest import HonestMax
from sim.rng import Draws, make_draws


class SameClaimLowEffort:
    name = "same_claim_low_effort"

    def act(self, view):
        p = view.params
        return Action(effort=p.q_max * 0.5, offer=Offer(claim=p.q_max, bid=p.a + p.b * p.q_max))


def cfgb(budget, T=30):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


def rule():
    return PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=0)


def test_hidden_effort_does_not_change_decisions_without_audits():
    cfg = cfgb(budget=0.0)
    d = make_draws(cfg, 0)
    a = run_episode(cfg, rule(), [HonestMax() for _ in range(cfg.N)], 0, draws=d)
    b = run_episode(cfg, rule(), [SameClaimLowEffort() for _ in range(cfg.N)], 0, draws=d)
    for ra, rb in zip(a.history, b.history):
        assert ra.assignment == rb.assignment and ra.payments == rb.payments and ra.audits == rb.audits


def test_audit_selection_does_not_depend_on_hidden_effort_or_noise():
    cfg = cfgb(budget=5.0)
    d = make_draws(cfg, 0)
    a = run_episode(cfg, rule(), [HonestMax() for _ in range(cfg.N)], 0, draws=d)
    b = run_episode(cfg, rule(), [SameClaimLowEffort() for _ in range(cfg.N)], 0, draws=d)
    for ra, rb in zip(a.history, b.history):
        assert [r.job for r in ra.audits] == [r.job for r in rb.audits]


def test_relabeling_identities_relabels_decisions():
    cfg = cfgb(budget=1.0)
    d = make_draws(cfg, 5)
    perm = np.array([3, 0, 9, 1, 7, 2, 8, 5, 4, 6])   # new index -> old index
    cfg_p = MarketConfig(N=cfg.N, J=cfg.J, T=cfg.T, sigma=cfg.sigma, e=cfg.e, v_min=cfg.v_min, v_max=cfg.v_max,
                         providers=tuple(cfg.providers[o] for o in perm), alpha=cfg.alpha, budget=cfg.budget)
    d_p = Draws(values=d.values, noise=d.noise[:, perm, :], tie_key=d.tie_key[:, :, perm], audit_u=d.audit_u,
                audit_key=d.audit_key, policy_seed=d.policy_seed[:, perm])
    r = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    a = run_episode(cfg, r, [HonestMax() for _ in range(cfg.N)], 5, draws=d)
    b = run_episode(cfg_p, r, [HonestMax() for _ in range(cfg.N)], 5, draws=d_p)
    inv = np.argsort(perm)   # old index -> new index
    for ra, rb in zip(a.history, b.history):
        assert {j: int(inv[i]) for j, i in ra.assignment.items()} == rb.assignment
    assert np.allclose(a.profit[perm], b.profit)


def test_enforce_output_type_is_checked():
    class WrongType(PostedRandomAudit):
        def enforce(self, records, view):
            return {"refunds": {}}
    cfg = cfgb(budget=5.0)
    with pytest.raises(TypeError):
        run_episode(cfg, WrongType(0.25, 0.40, 0.55, tol=0.12, L=10), [HonestMax() for _ in range(cfg.N)], 0)
