"""The honest-churn arm (docs/revision/churn/churn-plan.md): the churning honest policy, its injection into the frozen
cells, the churn jobs, the newcomer audit diagnostic, and a smoke-size run of the whole path."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import churn_v2 as C  # noqa: E402
from sim.config import ProviderParams  # noqa: E402
from sim.policies.base import ProviderHistory, ProviderView  # noqa: E402
from sim.policies.honest import HonestMax  # noqa: E402
from sim.records_v2 import read  # noqa: E402

MAIN = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")
PARAMS = ProviderParams(q_max=0.9, a=0.02, b=0.3, k=6)


def _view(seed, t=5):
    return ProviderView(i=1, params=PARAMS, t=t, posted_prices=None, history=ProviderHistory(), policy_seed=seed, identity=1)


def test_churn_policy_is_honest_and_exits_at_rate_p():
    pol = C.HonestChurn(0.05); honest = HonestMax().act(_view(1))
    acts = [pol.act(_view(s)) for s in range(4000)]
    assert all(a.effort == honest.effort and a.offer == honest.offer for a in acts)          # truthful delivery and offer
    rate = np.mean([a.exit for a in acts])
    assert 0.04 < rate < 0.06                                                                  # 4000 draws: sd about 0.0034
    assert [pol.act(_view(s)).exit for s in range(50)] == [C.HonestChurn(0.05).act(_view(s)).exit for s in range(50)]   # deterministic


def test_churn_zero_is_honest_max():
    assert not any(C.HonestChurn(0.0).act(_view(s)).exit for s in range(500))


def _job(p=0.05, focal=3, n=10):
    from sim.cell import Cell
    cfg = NS(N=n)
    return {"id": "x", "churn": p, "rule": "F111", "spec": {"tol": 0.16, "L": 10}, "_cfg": cfg, "_focal": focal}


def test_install_adds_churning_opponents_to_training_and_evaluation_cells(monkeypatch):
    calls = {}
    def fake_train_cell(job, others=()):
        from sim.cell import Cell
        return Cell(cfg=job["_cfg"], rule_factory=None, focal=job["_focal"], seeds=(1,), name="x", others=others)
    monkeypatch.setattr(C.R, "train_cell", fake_train_cell)
    C.install()
    try:
        cell = C.R.train_cell(_job())
        assert [e for e, _ in cell.others] == [e for e in range(10) if e != 3]
        assert all(f().p == 0.05 for _, f in cell.others)
        assert C.R.train_cell({**_job(), "churn": None}).others == ()
    finally:
        C.uninstall()
    assert C.R.train_cell is fake_train_cell


def test_churn_jobs_have_their_own_ids_and_provenance():
    j = {"id": "fresh0@rho0.2|F111|D2+H3|profit", "context": "fresh0@rho0.2", "rule": "F111", "family": "D2+H3",
         "provenance": {"id": "fresh0@rho0.2|F111|D2+H3|profit", "cfg_sha256": "c"}}
    k = C.churn_job(j, 0.05)
    assert k["id"] == "fresh0@rho0.2|F111|D2+H3|profit|churn0.05" and k["provenance"]["id"] == k["id"] and k["provenance"]["churn"] == 0.05
    assert C.R.path_of(Path("/o"), k["id"]) != C.R.path_of(Path("/o"), j["id"]) and k["churn"] == 0.05 and "churn" not in j


def test_newcomer_audit_shares_by_age():
    rec = lambda assign, audits: NS(assignment=assign, audits=tuple(NS(provider=p) for p in audits))
    # identities 0 (focal entity 0, initial), 1 (honest entity 1, initial), 2 (honest entity 1, replacement born at t=1)
    ep = NS(entity_of=(0, 1, 1), identity_generation=(0, 0, 1), identity_round=(0, 0, 1),
            history=(rec({0: 0, 1: 1}, [1]), rec({0: 0, 1: 2, 2: 2}, [2, 2]), rec({0: 2, 1: 2}, [2])))
    got = C.newcomer_shares([ep], focal=0, edges=(0, 1, 50))
    assert got["honest_replacement"][0] == {"age": [0, 1], "served": 2, "audited": 2, "share": 1.0}
    assert got["honest_replacement"][1] == {"age": [1, 50], "served": 2, "audited": 1, "share": 0.5}
    assert got["honest_initial"][0]["served"] == 1 and got["honest_initial"][0]["share"] == 1.0
    assert got["focal"][0]["served"] == 1 and got["focal"][1]["served"] == 1 and got["focal"][1]["share"] == 0.0
    assert got["honest_replacements_per_episode"] == 1.0


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_smoke_path_for_one_fresh_cell_under_churn(tmp_path):
    out = tmp_path / "churn"
    args = ["--src", str(MAIN / "eval/all"), "--out", str(out), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"),
            "--markets", "fresh0", "--rules", "F111", "--rates", "0.05", "--smoke"]
    assert C.main(args) == 0
    d = out / "p0.05"; rid = "fresh0@rho0.2|F111|D2+H3|profit|churn0.05"
    ev = read(C.R.eval_path(d, rid)); db = read(d / "doubling" / (C.R._safe(rid) + ".json")); inv = read(d / "inventory.json")
    dg = read(d / "diagnostics.json")["cells"]["fresh0@rho0.2|F111"]
    assert ev["stage"] == "evaluate" and ev["provenance"]["churn"] == 0.05 and len(ev["gain"]) == 2
    assert db["stage"] == "doubling" and "freeze/fresh0@rho0.2" in ev["upstream"] and f"reference/fresh0@rho0.2/F111" in ev["upstream"]
    for w in ("base", "doubled"):
        assert dg[w]["shares"]["honest_replacements_per_episode"] > 0 and len(dg[w]["normalized"]) == 2   # churn happened
    g = read(out / "gate-p0" / "gate.json")                                                     # the smoke gate ran the mapped comparison
    assert g["churn"].endswith("|churn0") and set(g) >= {"search", "doubling", "pass"} and (out / "gate-p0" / "inventory.json").exists()
    assert inv["churn"] == 0.05 and "churn_driver_sha256" in inv["environment"]


# ---- internal review round 1 (Sol, Astra: reject) ----

def _full_churn_job(p=0.05, rule="F111", market="fresh0"):
    """A full-size (five training seeds) churn job on the registered configuration, with its inputs copied."""
    M = MAIN
    root = json.loads((M / "draw/draw.json").read_text())["hash"]; salt = json.loads((M / "draw/instances.json").read_text())["salt_sha256"]
    from sim.records import cfg_from_dict
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads((M / "deviation/cfg_linux.json").read_text()).items()}
    params = json.loads((C.F.ROOT / "experiments/v2/params.json").read_text())
    return C.build_jobs(root, cfgs, params, salt, p, (market,), (rule,))[0], root


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_r1_menu_candidates_are_rerun_under_churn_on_five_training_seeds(tmp_path):
    """Blocker 1: the copied menu candidates carry no-churn profits on the five training seeds; under churn they must be
    run again, so every selection score equals a fresh churn evaluation of that candidate."""
    from sim.cell import SeedCache, run_focal
    import sim.reference as REF
    j, root = _full_churn_job(); C.R.install_salt(root, tmp_path); C.install()
    C.F.copy_inputs(MAIN / "eval/all", tmp_path, C.F.inputs(MAIN / "eval/all", [j]))
    cands, _, _ = C.R.menu(j, tmp_path, C.F.CUTS, C.F.H4_EXCLUDED)
    cell = C.R.train_cell(j); assert len(cell.seeds) == 5 and cell.others
    known = [c for c in cands if c.known_normalized is not None and len(c.known_normalized) == 5 and c.name != "abstain"]
    assert known                                                                              # the defect needs cached values to exist
    differ = 0                                                                                # names repeat across families: one candidate at a time
    for c in known:
        want = float(run_focal(cell, c.policy_factory, SeedCache()).normalized.mean())
        assert C.R.select_reference(cell, [c], SeedCache()).scores[c.name] == want
        differ += REF.select_reference(cell, [c], SeedCache()).scores[c.name] != want
    assert differ > 0


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_r1_frozen_reference_score_is_recomputed_under_churn(tmp_path):
    """Blocker 1: reference_change compares two churn scores; the frozen reference's stored no-churn score is replaced by
    its evaluation under churn on the training seeds."""
    from sim.cell import SeedCache, run_focal
    j, root = _full_churn_job(); C.R.install_salt(root, tmp_path); C.install()
    C.F.copy_inputs(MAIN / "eval/all", tmp_path, C.F.inputs(MAIN / "eval/all", [j]))
    cand, rrec, _ = C.R.reference_of(j, tmp_path)
    want = run_focal(C.R.train_cell(j), cand.policy_factory, SeedCache()).normalized
    assert rrec["per_seed_normalized"] == [float(x) for x in want] and rrec["churn_reevaluated"] is True
    stored = read(C.R.path_of(tmp_path, f"reference/{j['context']}/F111"))["per_seed_normalized"]
    assert stored != rrec["per_seed_normalized"]
    nj = {k: v for k, v in j.items() if k != "churn"}
    assert C.R.reference_of(nj, tmp_path)[1]["per_seed_normalized"] == stored                # no-churn jobs unchanged


def _probe(job):
    return len(C.R.train_cell(job).others)


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_r1_injection_reaches_pool_workers():
    from concurrent.futures import ProcessPoolExecutor
    j, _ = _full_churn_job()
    with ProcessPoolExecutor(max_workers=2, initializer=C._init_worker) as ex:
        assert list(ex.map(_probe, [j, j])) == [9, 9]


def test_r1_gate_maps_the_churn_id_and_keeps_every_other_check(tmp_path):
    rid = "fresh0@rho0.2|F111|D2+H3|profit"; cid = rid + "|churn0"
    from sim.records_v2 import write
    prov = {"cfg_sha256": "c", "budget": [5, 300, 5, 200], "runner_sha256": "r", "salt_sha256": "s", "rule_params_sha256": "p", "root": "h",
            "seeds_train": [7], "seeds_val": [8], "seeds_eval": [1, 2], "context": "fresh0@rho0.2", "git_commit": "x"}
    def put(base, i, gain, extra=None):
        write(C.R.path_of(base, i), {"stage": "search", "id": i, "attack": {"best_knobs": {"u0": 0.5, "x": 1, "clip": 0}, "best_f": 0.1, "best_source": "r", "archive": [0]},
                                     "twin": {"archive": [0], "best_f": 0.05}, "runs": 9, "upstream": {}, "provenance": {**prov, "id": i, **(extra or {})}})
        write(C.R.eval_path(base, i), {"stage": "evaluate", "seeds": [1, 2], "gain": gain,
                                       "upstream": {i: "a", "reference/fresh0@rho0.2/F111": "ref", "freeze/fresh0@rho0.2": "f"}})
        write(base / "doubling" / (C.R._safe(i) + ".json"), {"stage": "doubling", "incomplete": False, "attack_change": 0.0, "reference_change": 0.0,
                                                               "heldout": {"knobs": {"u0": 0.5, "x": 1, "clip": 0}, "seeds": [1, 2], "gain": gain}})
    put(tmp_path / "src", rid, [0.1, 0.2]); put(tmp_path / "out", cid, [0.1, 0.2 + 1e-15], {"churn": 0.0})
    g = C.gate_compare(tmp_path / "src", tmp_path / "out", rid, cid)
    assert g["pass"] and g["search"]["pass"] and g["doubling"]["pass"] and read(tmp_path / "out" / "gate.json")["pass"]
    put(tmp_path / "bad", cid, [0.1, 0.3], {"churn": 0.0})
    assert not C.gate_compare(tmp_path / "src", tmp_path / "bad", rid, cid)["pass"]


def test_r1_the_cap_stops_dispatch_between_stages_only():
    """Author, 2026-11-10: no running stage is killed; the next stage is not dispatched if it would pass the 8 USD cap."""
    t0 = 1_000_000.0
    C.check_cap(t0, 3600, now=t0 + 3600)                                                       # 0.56 + 0.56 USD
    with pytest.raises(SystemExit, match="between stages"):
        C.check_cap(t0, 3600 * 3, now=t0 + 3600 * 12)                                          # 6.72 + 1.68 > 8
    C.check_cap(None, 10**9)
    assert C.STOP_USD == 8.0


def test_r1_per_seed_counts_unavailable_bins_and_focal_newest_share():
    rec = lambda assign, audits: NS(assignment=assign, audits=tuple(NS(provider=p) for p in audits))
    # entity 0 focal: identity 0 then 3 (born t=2); entity 1 honest: identity 1 then 2 (born t=1); entity 2 honest: identity 4? no
    ep = NS(entity_of=(0, 1, 1, 0), identity_generation=(0, 0, 1, 1), identity_round=(0, 0, 1, 2),
            history=(rec({0: 0}, []), rec({0: 0}, []), rec({0: 3}, [3]), rec({0: 3}, [])))
    got = C.newcomer_shares([ep], focal=0, edges=(0, 1, 50, 100))
    assert got["per_episode"][0]["focal"] == [[2, 1], [2, 0], [0, 0]]                          # [served, audited] per bin
    assert got["focal"][2]["share"] is None                                                    # empty bin: unavailable
    # rounds 0..3: t0 all age 0 (tie), t1 honest identity 2 newest, t2 and t3 focal identity 3 uniquely newest
    assert got["focal_uniquely_newest"] == [0.5]


def test_r1_market_pooling_is_the_mean_of_market_shares_over_available_markets():
    m = {"fresh0": {"honest_replacement": [{"share": 0.8}, {"share": None}]}, "fresh1": {"honest_replacement": [{"share": 0.4}, {"share": 0.2}]}}
    assert C.pool_markets(m, "honest_replacement") == [{"share": pytest.approx(0.6), "markets": 2}, {"share": 0.2, "markets": 1}]


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_r1_a_failed_gate_stops_dispatch(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(C, "_run_rate", lambda out, jobs, *a, **k: calls.append(jobs[0]["churn"]))
    monkeypatch.setattr(C, "gate_compare", lambda *a, **k: {"pass": False, "search": {}, "doubling": {}})
    monkeypatch.setattr(C, "inventory", lambda *a, **k: None)
    args = ["--src", str(MAIN / "eval/all"), "--out", str(tmp_path / "c"), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--markets", "fresh0", "--rules", "F111"]
    assert C.main(args) == 1 and calls == [0.0]                                              # only the gate ran
