import numpy as np
import pytest
from sim.config import MarketConfig
from sim.market import run_episode
from sim.mechanisms.posted import PostedPrices
from sim.mechanisms.posted_audit import PostedRandomAudit
from sim.mechanisms.base import Consequences
from sim.policies.base import Action, ProviderView, ProviderHistory
from sim.policies.honest import HonestMax
from sim.policies.identity import IdentityReplacement
from sim.ledger import Ledger
from sim.rng import fresh_tie_keys, identity_secret, retired_secret, entrant_rank, replacement_noise, load_identity_salt, DEFAULT_SALT_PATH, make_draws, Draws


def cfgb(budget, e=0.0, T=40, N=None):
    c = MarketConfig.default()
    return MarketConfig(N=c.N, J=c.J, T=T, sigma=c.sigma, e=e, v_min=c.v_min, v_max=c.v_max,
                        providers=c.providers, alpha=c.alpha, budget=budget)


class ExitAt:
    """Exits in round `when` (the fresh identity offers in that round), otherwise honest-max."""
    name = "exit_at"
    def __init__(self, when): self.when = when
    def act(self, view):
        a = HonestMax().act(view)
        return Action(effort=a.effort, offer=a.offer, exit=(view.t == self.when))


class Spy(PostedRandomAudit):
    """Records what a rule can see each round."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.seen = []
    def allocate(self, values_t, offers, view):
        self.seen.append({"t": view.t, "N": view.N, "cap": view.capacity.copy(), "ban": view.banned_until.copy(),
                          "bond": view.bond.copy(), "tie": np.array(view.memory["tie_key"], copy=True),
                          "offers": set(offers), "offer_order": list(offers)})
        return super().allocate(values_t, offers, view)


def test_ledger_grow_keeps_totals():
    led = Ledger(N=2, T=3)
    esc, own = {}, {}
    led.fund(0, 0, 1, 0.5, esc, own); led.settle(0, esc, own, Consequences(), {})
    led.grow(4)
    assert led.funding.shape == (3, 4) and led.bond.shape == (4,)
    assert led.funding.sum() == pytest.approx(0.5)
    led.check_conservation(0.0)


def test_fresh_tie_keys_depend_only_on_the_secret():
    salt = bytes(range(32))
    s1, s2, s3 = identity_secret(salt, 7, 3, 11, 1), identity_secret(salt, 7, 3, 22, 1), identity_secret(salt, 7, 3, 11, 2)
    assert len({s1, s2, s3, retired_secret(salt, 7, 3, 10), identity_secret(salt, 7, 4, 11, 1)}) == 5     # entity, generation, round, retirement all matter
    assert identity_secret(bytes(32), 7, 3, 11, 1) != s1          # without the salt, knowing seed, round, fresh_seed and generation gives nothing
    assert entrant_rank(salt, 7, 3, 11) != entrant_rank(bytes(32), 7, 3, 11) and entrant_rank(salt, 7, 3, 11) != s1
    assert len(load_identity_salt()) == 32
    a = fresh_tie_keys([s1, s2], 50); b = fresh_tie_keys([s2, s1, s3], 50)
    assert a.shape == (50, 2) and np.array_equal(a[:, 0], b[:, 1]) and np.array_equal(a[:, 1], b[:, 0])
    assert not np.array_equal(b[:, 2], a[:, 0])
    assert not a.flags.writeable and a.min() >= 0.0 and a.max() < 1.0 and len(np.unique(a[:, 0])) == 50
    d = make_draws(MarketConfig.default(), 3)
    assert d.fresh_seed.shape == (200, 10) and d.fresh_seed.dtype == np.int64


def test_identity_salt_can_be_loaded_from_an_untracked_path(tmp_path, monkeypatch):
    other = tmp_path / "final_salt.hex"; other.write_text("ab" * 32 + "\n")
    monkeypatch.setenv("TOUCHSTONE_IDENTITY_SALT", str(other))
    assert load_identity_salt() == bytes([0xAB] * 32) and load_identity_salt() != load_identity_salt(DEFAULT_SALT_PATH)
    bad = tmp_path / "short.hex"; bad.write_text("abcd\n")
    with pytest.raises(ValueError):
        load_identity_salt(bad)


def test_same_round_entrant_order_is_not_a_function_of_the_seed_alone():
    """A rule that recovers the episode seed must not be able to map same-round entrants to their predecessors,
    neither through the ids nor through the order of the offers it receives."""
    cfg = cfgb(budget=0.0, T=5)
    orders = {}
    for salt in (bytes(range(32)), bytes(range(1, 33))):
        pols = [ExitAt(when=2) for _ in range(cfg.N)]                       # every entity exits in round 2
        spy = Spy(0.25, 0.40, 0.55, tol=0.12, L=10)
        res = run_episode(cfg, spy, pols, 0, identity_salt=salt)
        orders[salt] = tuple(res.entity_of[cfg.N:])                          # entity of identity N, N + 1, ... in creation order
        assert all(rec["offer_order"] == sorted(rec["offer_order"]) for rec in spy.seen)   # offers arrive in id order, never in entity order
        assert all(list(h.offers) == sorted(h.offers) for h in res.history)
    assert len(set(orders.values())) == 2                                   # the order depends on the salt, not on the seed alone
    public = tuple(int(x) for x in np.random.default_rng(np.random.SeedSequence([0, 2, 2])).permutation(cfg.N))
    assert all(o != public for o in orders.values())


def test_replacement_identities_deliver_with_salted_noise():
    """An audited delivery of a replacement identity never matches the entity's public noise stream."""
    cfg = cfgb(budget=50.0, T=6)                                            # every served job is audited
    d = make_draws(cfg, 0); salt = bytes(range(32))
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=1)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0, draws=d, identity_salt=salt)
    audits = [(rec.t, r) for rec in res.history for r in rec.audits if r.provider == cfg.N]
    assert audits
    q = cfg.providers[2].q_max
    for t, r in audits:
        public = q + d.noise[t, 2, :]                                         # what a seed-recovering rule predicts from the entity's stream
        salted = q + replacement_noise(salt, 0, t, int(d.fresh_seed[t, 2]), 1, cfg.kmax, cfg.sigma)
        assert not np.any(np.isclose(r.delivered, public)) and np.any(np.isclose(r.delivered, salted))


def test_exit_creates_fresh_identity_and_charges_entry_cost_in_that_round():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=3)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N + 1 and res.entity_of[-1] == 2 and res.identity_round[-1] == 3 and res.identity_generation[-1] == 1
    assert res.ledger.entry.sum() == pytest.approx(0.3) and res.ledger.entry[3, cfg.N] == pytest.approx(0.3)
    assert all(2 not in rec.assignment.values() for rec in res.history[3:])     # old identity never offers again
    assert any(cfg.N in rec.assignment.values() for rec in res.history[3:])     # fresh one serves
    assert cfg.N in res.history[3].offers and 2 not in res.history[3].offers    # offer of round 3 is under the fresh identity
    assert res.profit.shape == (cfg.N,)
    assert res.profit[2] == pytest.approx(res.identity_profit[2] + res.identity_profit[cfg.N])


def test_exit_in_last_round_creates_identity_and_releases_its_bond_at_terminal_settlement():
    cfg = cfgb(budget=0.0, e=0.3, T=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=9)
    res = run_episode(cfg, PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    assert res.n_identities == cfg.N + 1 and res.ledger.entry[9, cfg.N] == pytest.approx(0.3)
    assert res.ledger.bond.sum() == 0.0


def test_banned_identity_can_still_exit_and_fresh_identity_is_not_banned():
    cfg = cfgb(budget=50.0, e=0.0, T=12)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=50)   # every audit fails, long bans
    pols = [HonestMax() for _ in range(cfg.N)]; pols[0] = IdentityReplacement(HonestMax())
    res = run_episode(cfg, rule, pols, 0)
    assert res.n_identities > cfg.N
    # after a failure in round t the entity serves again in round t + 1 under a fresh identity
    fails = np.flatnonzero(res.failures[:, 0] > 0)
    assert len(fails) >= 1 and res.served[fails[0] + 1, 0] > 0


def test_identity_replacement_exits_in_the_round_after_failure():
    cfg = cfgb(budget=50.0, T=6)
    rule = PostedRandomAudit(0.25, 0.40, 0.55, tol=-10.0, L=2)
    pols = [IdentityReplacement(HonestMax()) for _ in range(cfg.N)]
    res = run_episode(cfg, rule, pols, 0)
    first_fail = int(np.argmax(res.failures[:, 0] > 0))
    assert res.failures[first_fail, 0] > 0
    created = [r for r, e in zip(res.identity_round, res.entity_of) if e == 0 and r > 0]
    assert created[0] == first_fail + 1
    assert res.identity_profit.shape == (res.n_identities,)
    assert res.profit[0] == pytest.approx(sum(res.identity_profit[k] for k, e in enumerate(res.entity_of) if e == 0))


def test_rule_view_does_not_reveal_exit_or_successor():
    cfg = cfgb(budget=5.0, T=8)
    rule = Spy(0.25, 0.40, 0.55, tol=0.12, L=10)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[2] = ExitAt(when=3)
    run_episode(cfg, rule, pols, 0)
    before, after = rule.seen[2], rule.seen[3]
    assert after["N"] == before["N"] + 1
    assert after["cap"][2] == before["cap"][2] and after["ban"][2] == before["ban"][2]    # old identity not marked
    assert after["cap"][cfg.N] == cfg.providers[2].k and after["ban"][cfg.N] == 0
    assert not np.array_equal(after["tie"][:, 2], after["tie"][:, cfg.N])                  # no shared randomness
    assert 2 not in after["offers"] and cfg.N in after["offers"]


class ExitAtRounds:
    """Exits in each round of `when`, otherwise honest-max."""
    name = "exit_at_rounds"
    def __init__(self, when): self.when = set(when)
    def act(self, view):
        a = HonestMax().act(view)
        return Action(effort=a.effort, offer=a.offer, exit=(view.t in self.when))


@pytest.mark.parametrize("perm,exits", [
    (np.array([3, 0, 9, 1, 7, 5, 8, 2, 4, 6]), {2: (3,), 5: (3,)}),        # simultaneous exits whose creation order reverses under the permutation
    (np.array([3, 0, 9, 1, 7, 2, 8, 5, 4, 6]), {2: (3, 6), 5: (3,)}),     # unequal replacement histories
])
def test_relabeling_with_reentry_relabels_decisions(perm, exits):
    c = cfgb(budget=1.0, T=12)
    cfg_p = MarketConfig(N=c.N, J=c.J, T=c.T, sigma=c.sigma, e=c.e, v_min=c.v_min, v_max=c.v_max,
                         providers=tuple(c.providers[o] for o in perm), alpha=c.alpha, budget=c.budget)
    d = make_draws(c, 5)
    d_p = Draws(values=d.values, noise=d.noise[:, perm, :], tie_key=d.tie_key[:, :, perm], audit_u=d.audit_u,
                audit_key=d.audit_key, policy_seed=d.policy_seed[:, perm], fresh_seed=d.fresh_seed[:, perm])
    inv = np.argsort(perm)
    pols = [HonestMax() for _ in range(c.N)]
    for e, when in exits.items():
        pols[e] = ExitAtRounds(when)
    pols_p = [pols[o] for o in perm]
    r = PostedRandomAudit(0.25, 0.40, 0.55, tol=0.12, L=10)
    a = run_episode(c, r, pols, 5, draws=d); b = run_episode(cfg_p, r, pols_p, 5, draws=d_p)
    # key an identity by (entity, generation) so fresh identities compare across runs whatever their creation order
    ka = {i: (int(inv[e]), g) for i, (e, g) in enumerate(zip(a.entity_of, a.identity_generation))}
    kb = {i: (int(e), g) for i, (e, g) in enumerate(zip(b.entity_of, b.identity_generation))}
    for ra, rb in zip(a.history, b.history):
        assert {j: ka[i] for j, i in ra.assignment.items()} == {j: kb[i] for j, i in rb.assignment.items()}
    assert np.allclose(a.profit[perm], b.profit)


def _hold_rule_factory(exit_round):
    class HoldAndExit(HonestMax):
        name = "hold_and_exit"
        def act(self, view):
            a = super().act(view)
            return Action(effort=a.effort, offer=a.offer, exit=(view.t == exit_round))
    class HoldRule(PostedRandomAudit):
        """Holds back 10% of each release and releases every bond one round later."""
        def enforce(self, records, view):
            cons = super().enforce(records, view)
            for j, amt in view.escrow.items():
                i = view.memory["owner"][j]
                cons.holdbacks[i] = cons.holdbacks.get(i, 0.0) + 0.1 * amt
            for i in range(view.N):
                if view.bond[i] > 0:
                    cons.releases[i] = float(view.bond[i])
            return cons
        def allocate(self, values_t, offers, view):
            out = super().allocate(values_t, offers, view)
            view.memory["owner"] = dict(out)
            return out
    return HoldAndExit, HoldRule


def test_exit_does_not_change_ban_or_bond_schedule():
    cfg = cfgb(budget=0.0, T=8)
    HoldAndExit, HoldRule = _hold_rule_factory(exit_round=3)
    pols = [HonestMax() for _ in range(cfg.N)]; pols[5] = HoldAndExit()
    with_exit = run_episode(cfg, HoldRule(0.25, 0.40, 0.55, tol=0.12, L=10), pols, 0)
    pols2 = [HonestMax() for _ in range(cfg.N)]; pols2[5] = HonestMax()
    no_exit = run_episode(cfg, HoldRule(0.25, 0.40, 0.55, tol=0.12, L=10), pols2, 0)
    # the bond held back in round 2 is released in round 3 in both runs, to identity 5
    assert with_exit.ledger.holdback_in[2, 5] > 0
    assert with_exit.ledger.holdback_out[3, 5] == pytest.approx(no_exit.ledger.holdback_out[3, 5])
    assert with_exit.ledger.holdback_out[3, 5] == pytest.approx(with_exit.ledger.holdback_in[2, 5])
    assert with_exit.ledger.bond.sum() == pytest.approx(0.0)
    assert with_exit.ledger.holdback_out[:, 5].sum() == pytest.approx(with_exit.ledger.holdback_in[:, 5].sum())
    with_exit.ledger.check_conservation(0.0)
