import numpy as np
import pytest
from sim.cell import SeedCache, Cell, run_focal
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, exact_key
from sim.policies.honest import HonestMax
from sim.reference import (REFERENCE_ORDER, Candidate, twin_search, attack_search, reference_candidates,
                           select_reference, evaluate_gain, seed_rows, ROW_FIELDS)
from sim.search import SearchSettings, Objective


def fixture_cfg(budget=0.0):
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=20, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=budget)


SMALL = SearchSettings(popsize=8, sigma0=0.3, restarts=2, evals_per_restart=40, reeval_every=10, near_corner=0.02, sobol_seed=3)   # two restarts: the near-full-cheat start reaches a cheating attack


def cell_on(prices, seeds=(1, 2), focal=3):
    return Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(*prices), focal=focal, seeds=seeds, name="c")


def test_candidates_come_from_archive_in_registered_order_and_known_values_skip_runs():
    cache = SeedCache()
    cell = cell_on((0.20, 0.35, 0.50))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    assert set(at.incumbent_scores) == {"twin_best", "honest_point"}
    cands = reference_candidates(cell, D1, at, tw, bank_members=[])
    names = [c.name for c in cands]
    assert names[:3] == ["abstain", "honest_max", "twin_search"]          # the attack projection may de-duplicate against the twin
    assert set(names) <= set(REFERENCE_ORDER) | {n for n in names if n.startswith("bank_")}
    assert all(c.knobs is None or c.knobs["clip"] == 1 for c in cands)
    assert len({exact_key(c.knobs) for c in cands if c.knobs}) == len([c for c in cands if c.knobs])
    runs_before = cache.runs
    ref = select_reference(cell, cands, cache)
    assert cache.runs - runs_before == len(cell.seeds)          # only honest_max needed a run
    assert set(ref.scores) == set(names) and ref.candidate.name in names
    assert ref.scores["abstain"] == 0.0


def test_twin_point_as_attacker_reproduces_trajectory():
    cache = SeedCache()
    cell = cell_on((0.20, 0.35, 0.50), seeds=(1,))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    att = Objective(cell, D1, cache)
    for entry in list(tw.archive.values())[:5]:
        # the twin candidate re-run as an attacker with clip = 1 reproduces its value and never inflates (spec 5.2 pre-lock test)
        att.eval_knobs(entry.knobs)
        a = att.archive[exact_key(entry.knobs)]
        assert a.knobs["clip"] == 1 and a.f == entry.f and np.array_equal(a.per_seed_profit, entry.per_seed_profit) and a.inflated is False
    # the clipped-attack run of section 7 is the same policy with the clip knob set: efforts unchanged, claims = min(claim, effort)
    k = {"u": 0.4, "m": 0.9, "s": 0.05, "w": 0.2, "clip": 0}
    raw = run_focal(cell, lambda: D1.make(k), cache).results[0]
    clp = run_focal(cell, lambda: D1.make(D1.project(k)), cache).results[0]
    assert np.array_equal(raw.efforts[:, 3], clp.efforts[:, 3])
    assert np.allclose(clp.claims[:, 3], np.minimum(raw.claims[:, 3], raw.efforts[:, 3]))


def test_honest_attack_against_honest_reference_has_gain_exactly_zero():
    cache = SeedCache()
    cell = cell_on((0.25, 0.40, 0.55))
    ref = select_reference(cell, [Candidate("honest_max", HonestMax, None)], cache)
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    assert np.all(g.gain == 0.0) and np.all(g.inflation_term == 0.0) and np.all(g.selection_term == 0.0)
    assert np.all(g.eff_attack == g.eff_ref) and np.all(g.eff_attack == g.eff_honest)


def test_gain_on_other_seeds_subtracts_reference_on_those_seeds():
    cache = SeedCache()
    train = cell_on((0.25, 0.40, 0.55), seeds=(1, 2))
    ref = select_reference(train, [Candidate("honest_max", HonestMax, None)], cache)
    val = Cell(cfg=train.cfg, rule_factory=train.rule_factory, focal=train.focal, seeds=(3, 4, 5), name="val")
    g = evaluate_gain(val, D1, D1.honest_point(), ref.candidate, cache)
    assert g.gain.shape == (3,) and np.all(g.gain == 0.0)
    assert g.profit_ref.shape == (3,) and np.array_equal(g.profit_ref, g.profit_attack)


def test_full_cheat_has_positive_gain_and_decomposition_adds_up():
    cache = SeedCache()
    cell = cell_on((0.20, 0.35, 0.50))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    attack = {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}
    ref = select_reference(cell, reference_candidates(cell, D1, at, tw, []), cache)
    g = evaluate_gain(cell, D1, attack, ref.candidate, cache)
    assert g.gain.mean() > 0
    assert np.allclose(g.gain, g.inflation_term + g.selection_term)
    assert g.eff_attack.shape == (2,) and np.all(np.isfinite(g.eff_honest)) and np.all(g.audit_spend_attack == 0.0)
    assert np.allclose(g.harm_accounting, g.harm_direct, atol=1e-9)


def test_abstention_wins_when_everything_loses_money():
    cache = SeedCache()
    # every tier price is below the fixed cost a = 0.02: any service loses money; a twin that serves nothing ties abstention at 0
    cell = cell_on((0.005, 0.010, 0.015), seeds=(1,))
    tw = twin_search(cell, D1, cache, SMALL, seed=0)
    at = attack_search(cell, D1, cache, SMALL, seed=1, twin=tw)
    ref = select_reference(cell, reference_candidates(cell, D1, at, tw, []), cache)
    assert ref.candidate.name == "abstain" and ref.per_seed_profit[0] == 0.0
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    assert g.gain[0] < 0.0


def test_seed_rows_follow_the_schema():
    cache = SeedCache()
    cell = cell_on((0.25, 0.40, 0.55))
    ref = select_reference(cell, [Candidate("honest_max", HonestMax, None)], cache)
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    rows = seed_rows(cell, g, {"cell": "c", "rule": "B1"})
    assert len(rows) == 2 and list(rows[0]) == ["cell", "rule"] + ROW_FIELDS
    assert rows[0]["seed"] == 1 and rows[0]["sstar"] > 0 and rows[0]["n_identities_attack"] == 4
    for name in ("refunds_attack", "forfeits_attack", "holdback_in_attack", "refunds_focal_attack", "forfeits_focal_attack", "focal_bans_attack",
                 "focal_audited_attack", "focal_banned_rounds_attack", "others_audited_attack", "others_bans_attack", "others_lost_capacity_attack"):
        assert name in ROW_FIELDS and rows[0][name] == 0       # B1 audits nothing


def test_participant_diagnostics_count_audits_bans_and_lost_capacity():
    from sim.mechanisms.posted_audit import PostedRandomAudit
    c = fixture_cfg(budget=5.0)
    cache = SeedCache()
    cell = Cell(cfg=c, rule_factory=lambda: PostedRandomAudit(0.20, 0.35, 0.50, tol=-10.0, L=2), focal=3, seeds=(1,), name="a")   # every audit fails
    ref = select_reference(cell, [Candidate("honest_max", HonestMax, None)], cache)
    g = evaluate_gain(cell, D1, D1.honest_point(), ref.candidate, cache)
    res = run_focal(cell, HonestMax, cache).results[0]                   # the attack run is honest-max here
    total_audits = int(res.audits.sum())
    assert total_audits > 0 and g.focal_audited_attack[0] + g.others_audited_attack[0] == total_audits
    assert g.others_bans_attack[0] > 0 and g.others_lost_capacity_attack[0] > 0
    assert g.refunds_attack[0] > 0 and g.forfeits_attack[0] == 0 and g.holdback_in_attack[0] == 0
    assert g.refunds_focal_attack[0] <= g.refunds_attack[0] and (g.focal_bans_attack[0] > 0) == (g.focal_banned_rounds_attack[0] > 0)


def test_focal_banned_rounds_ignore_retired_identities():
    from sim.mechanisms.posted_audit import PostedRandomAudit
    from sim.policies.identity import h3_family
    from sim.reference import participant_diagnostics
    c = fixture_cfg(budget=5.0)
    cache = SeedCache()
    cell = Cell(cfg=c, rule_factory=lambda: PostedRandomAudit(0.20, 0.35, 0.50, tol=-10.0, L=50), focal=3, seeds=(1,), name="h3")
    h3 = h3_family(D1)
    res = run_focal(cell, lambda: h3.make(dict(D1.honest_point(), x=1)), cache).results[0]      # exits after every failure
    d = participant_diagnostics(res, c, 3)
    assert res.n_identities > 4 and d["focal_banned_rounds"] <= c.T and d["focal_bans"] >= 1
    # a round-zero exit: the initial and the replacement identity share creation round 0; the replacement is current
    from sim.policies.base import Action
    class ExitFirst:
        name = "exit_first"
        def act(self, view):
            a = HonestMax().act(view)
            return Action(effort=a.effort, offer=a.offer, exit=(view.t == 0))
    c_all = fixture_cfg(budget=50.0)                                                         # every served job is audited and fails
    cell_all = Cell(cfg=c_all, rule_factory=lambda: PostedRandomAudit(0.20, 0.35, 0.50, tol=-10.0, L=50), focal=3, seeds=(1,), name="x0")
    res0 = run_focal(cell_all, ExitFirst, cache).results[0]
    d0 = participant_diagnostics(res0, c_all, 3)
    assert res0.n_identities == 5 and res0.served[0, 3] > 0 and d0["focal_banned_rounds"] == c_all.T - 1   # the replacement is current and banned from round 1
