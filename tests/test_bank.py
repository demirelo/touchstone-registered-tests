import pytest
from sim.bank import Bank
from sim.cell import SeedCache, Cell
from sim.config import MarketConfig
from sim.mechanisms.posted import PostedPrices
from sim.policies.families import D1, D2, exact_key


def fixture_cfg():
    c = MarketConfig.default()
    return MarketConfig(N=4, J=30, T=10, sigma=c.sigma, e=0.0, v_min=0.6, v_max=1.4,
                        providers=c.providers[6:10], alpha=c.alpha, budget=0.0)


def test_typed_filter_corners_projection_and_dedupe():
    b = Bank()
    b.add("D1", {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="B1/D1/0.05")
    b.add("D1", {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="same-again")
    b.add("D1", {"u": 0.5 + 1e-12, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}, origin="one-ulp-away")      # a distinct policy, kept
    b.add("D1", {"u": 1.0, "m": 1.0, "s": 0.0, "w": 0.0, "clip": 0}, origin="is-a-corner")                 # equals a D1 corner: one entry, member origin kept
    b.add("D2", {"u0": 0.1, "m0": 0.2, "s": 0.0, "d": 0.5, "r": 0.1, "w": 0.0, "clip": 1}, origin="B2/D2/0.05")
    d1 = b.members_for("D1"); d2 = b.members_for("D2")
    assert len(d1) == 3 + 32 - 1                          # three distinct D1 members plus the 32 D1 corners, one of them already a member
    assert len(d2) == 3 + 1 + 128 - 1                     # three D1 members embedded, the D2 member, 128 D2 corners; the embedded full cheat is a D2 corner
    assert any(m["d"] == 0.0 and m["u0"] == 0.5 for m in d2)
    p1 = b.projected_members_for("D1"); p2 = b.projected_members_for("D2")
    assert len(p1) == 3 + 16 - 1 and all(m["clip"] == 1 for m in p1)
    assert len({exact_key(m) for m in p2}) == len(p2) and all(m["clip"] == 1 for m in p2)
    b2 = Bank.from_json(b.to_json())
    assert len(b2.members_for("D2")) == len(d2)


def test_bank_pass_replaces_incumbent_when_a_member_or_corner_scores_higher():
    b = Bank()
    b.add("D1", {"u": 0.9, "m": 0.9, "s": 0.0, "w": 0.0, "clip": 0}, origin="cheat")
    b.add("D1", {"u": 0.0, "m": 0.0, "s": 0.0, "w": 0.0, "clip": 1}, origin="honest")
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    cache = SeedCache()
    ranked = b.evaluate(cell, D1, cache)
    assert len(ranked) == 1 + 32 and ranked[0][2] == "corner"          # the honest member is itself a corner (de-duplicated, keeps its origin); the full-cheat corner (u = m = 1) wins
    assert sum(1 for _, _, o in ranked if o == "honest") == 1
    runs = cache.runs
    known = {exact_key(m): f for m, f, _ in ranked}
    assert b.evaluate(cell, D1, cache, known=known) == ranked and cache.runs == runs      # known values need no run
    assert ranked[0][1] > ranked[-1][1]
    bp = b.bank_pass(cell, D1, cache, incumbent_f=ranked[-1][1])
    assert bp.improved is True and bp.best_origin == "corner" and bp.best_f == ranked[0][1] and bp.best_knobs["u"] == 1.0
    bp2 = b.bank_pass(cell, D1, cache, incumbent_f=ranked[0][1] + 1.0)
    assert bp2.improved is False
    row = Bank.transfer_rows("c", ranked[-1][1], bp)
    assert row["improved"] is True and row["best_origin"] == "corner"


def test_h3_transfer_through_both_embeddings_with_registered_order_origins_and_projections():
    from sim.policies.families import embed_d2_in_h3, embed_d2_in_h3_exit
    from sim.registry import available_families
    from sim.schedule import N_CORNERS, bank_members
    b = Bank()
    d1 = {"u": 0.5, "m": 0.5, "s": 0.0, "w": 0.0, "clip": 0}; d2 = {"u0": 0.1, "m0": 0.2, "s": 0.0, "d": 0.5, "r": 0.1, "w": 0.0, "clip": 1}
    b.add("D1", d1, origin="B1/D1"); b.add("D2", d2, origin="B2/D2")
    assert embed_d2_in_h3(d2) == {**d2, "x": 0} and embed_d2_in_h3_exit(d2) == {**d2, "x": 1}
    comp = b._compatible("D2+H3")
    members = [m for m, _ in comp]; origins = [o for _, o in comp]
    assert members[0] == {**embed_d1_in_d2_(d1), "x": 0} and origins[0] == "B1/D1|x=0"            # entry order: the embedded D1 member first, x = 0 before x = 1
    assert members[1] == {**embed_d1_in_d2_(d1), "x": 1} and origins[1] == "B1/D1|x=1"
    assert members[2] == {**d2, "x": 0} and origins[2] == "B2/D2|x=0" and members[3] == {**d2, "x": 1} and origins[3] == "B2/D2|x=1"
    corner_keys = {exact_key(c) for c in available_families()["D2+H3"].corners()}
    assert len(members) == 4 + len(corner_keys) - sum(1 for m in members[:4] if exact_key(m) in corner_keys)      # the H3 corners follow, de-duplicated
    assert len({exact_key(m) for m in members}) == len(members)
    proj = b.projected_members_for("D2+H3")
    assert all(m["clip"] == 1 for m in proj) and len({exact_key(m) for m in proj}) == len(proj)
    from sim.schedule import N_PROJECTED_CORNERS
    assert bank_members(24)["D2+H3"] == {"n_unknown": 2 * (24 + 2 * 24), "n_projected": 2 * (24 + 2 * 24) + N_PROJECTED_CORNERS["D2+H3"]}   # both embeddings of the D2-compatible set (D1 embedded + D2) plus H3's projected corners
    # x = 0 is the behaviour-preserving containment: the embedded member reproduces the D2 member's focal trajectory on a seed
    from sim.cell import run_focal
    fam2 = available_families()["D2"]; fam3 = available_families()["D2+H3"]
    cell = Cell(cfg=fixture_cfg(), rule_factory=lambda: PostedPrices(0.20, 0.35, 0.50), focal=3, seeds=(1,), name="c")
    r2 = run_focal(cell, lambda: fam2.make(d2), SeedCache()).results[0]; r3 = run_focal(cell, lambda: fam3.make({**d2, "x": 0}), SeedCache()).results[0]
    assert r2.profit[3] == r3.profit[3] and r2.sstar == r3.sstar
    ranked = b.evaluate(cell, fam3, SeedCache())
    assert len(ranked) == len(members) and ranked[0][1] >= ranked[-1][1]


def embed_d1_in_d2_(k):
    from sim.policies.families import embed_d1_in_d2
    return embed_d1_in_d2(k)
