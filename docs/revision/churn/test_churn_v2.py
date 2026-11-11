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
    root = json.loads((MAIN / "draw/draw.json").read_text())["hash"]; salt = json.loads((MAIN / "draw/instances.json").read_text())["salt_sha256"]
    from sim.records import cfg_from_dict
    cfgs = {k: cfg_from_dict(v) for k, v in json.loads((MAIN / "deviation/cfg_linux.json").read_text()).items()}
    j = C.build_jobs(root, cfgs, json.loads((C.F.ROOT / "experiments/v2/params.json").read_text()), salt, 0.05, ("fresh0",), ("F111",), True)[0]
    with pytest.raises(SystemExit, match="memory evidence"):                                   # r4: an existing record is no measurement
        C.memory_preflight("evaluate", [j], d, 9)
    ep = C.R.eval_path(d, rid); ep.rename(tmp_path / "eval_kept.json")                         # the task is unfinished again
    mp = C.memory_preflight("evaluate", [j], d, 9)                                              # the pod-side preflight, a real child run
    assert mp["measured"] == [rid] and not mp["reused"] and ep.exists()                        # it ran and wrote the production record
    assert mp["task_peak_bytes"] > 0 and mp["parent_bytes"] > 0 and 1 <= mp["workers"] <= 9 and read(d / "memory_preflight_evaluate.json") == mp
    assert read(ep)["gain"] == read(tmp_path / "eval_kept.json")["gain"]
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
    with pytest.raises(SystemExit, match="between stages"):
        C.check_cap(t0, 3600, now=t0 + 3600, prior_usd=7.0)                                    # charges of a failed attempt count
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
    assert got["focal_newest_by_creation"] == [0.5]


def test_r1_market_pooling_is_the_mean_of_market_shares_over_available_markets():
    m = {"fresh0": {"honest_replacement": [{"share": 0.8}, {"share": None}]}, "fresh1": {"honest_replacement": [{"share": 0.4}, {"share": 0.2}]}}
    assert C.pool_markets(m, "honest_replacement") == [{"share": pytest.approx(0.6), "markets": 2}, {"share": 0.2, "markets": 1}]


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_r1_a_failed_gate_stops_dispatch(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(C, "_run_rate", lambda out, jobs, *a, **k: calls.append(jobs[0]["churn"]))
    monkeypatch.setattr(C, "gate_compare", lambda *a, **k: {"pass": False, "gate_ok": False, "identical": False, "search": {}, "doubling": {}})
    monkeypatch.setattr(C, "inventory", lambda *a, **k: None)
    args = ["--src", str(MAIN / "eval/all"), "--out", str(tmp_path / "c"), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--markets", "fresh0", "--rules", "F111"]
    import time
    args += ["--started", str(time.time() - 60), "--usd-per-hour", "0.56"]
    assert C.main(args) == 1 and calls == [0.0]                                              # only the gate ran


# ---- internal review round 2 (Sol accept-with-caveat, Astra reject) ----

def test_r2_production_needs_a_valid_allocation_time_and_price():
    import time
    now = time.time()
    C.check_started(now - 60, now)
    for bad in (None, now + 3600, 0.0, float("nan")):
        with pytest.raises(SystemExit, match="started"):
            C.check_started(bad, now)


def test_r2_a_matching_passing_gate_is_required(tmp_path):
    from sim.records_v2 import write
    g = tmp_path / "gate-p0"
    with pytest.raises(SystemExit, match="gate"):
        C.require_gate(tmp_path)
    write(g / "gate.json", {"pass": False, "registered": "fresh0@rho0.2|F111|D2+H3|profit", "churn": "fresh0@rho0.2|F111|D2+H3|profit|churn0"})
    with pytest.raises(SystemExit, match="gate"):
        C.require_gate(tmp_path)
    write(g / "gate.json", {"pass": True, "gate_ok": True, "require_identical": False, "registered": "fresh0@rho0.2|F111|D2+H3|profit", "churn": "fresh0@rho0.2|F111|D2+H3|profit|churn0"})
    write(g / "inventory.json", {"environment": {"churn_driver_sha256": "0" * 64}})
    with pytest.raises(SystemExit, match="driver"):
        C.require_gate(tmp_path)                                                               # a gate run by another driver version
    write(g / "inventory.json", {"environment": {"churn_driver_sha256": sha256_of(C.__file__)}})
    C.require_gate(tmp_path)


def sha256_of(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.mark.skipif(not (MAIN / "eval/all/freeze").is_dir(), reason="needs the registered evaluation records")
def test_r2_production_refuses_gate_skip_and_missing_started(tmp_path):
    base = ["--src", str(MAIN / "eval/all"), "--out", str(tmp_path / "c"), "--draw", str(MAIN / "draw/draw.json"), "--instances", str(MAIN / "draw/instances.json"),
            "--cfgs", str(MAIN / "deviation/cfg_linux.json"), "--addendum", str(MAIN / "report/addendum.json"), "--markets", "fresh0", "--rules", "F111"]
    with pytest.raises(SystemExit, match="started"):
        C.main(base)
    import time
    with pytest.raises(SystemExit, match="gate"):
        C.main(base + ["--started", str(time.time() - 60), "--usd-per-hour", "0.56", "--gate", "skip"])
    with pytest.raises(SystemExit, match="gate"):
        C.main(base + ["--started", str(time.time() - 60), "--usd-per-hour", "0.56", "--stage", "evaluate"])   # a separate stage needs the saved gate


def test_r2_workers_fit_the_memory_limit():
    G = 2 ** 30
    assert C.plan_workers(limit=32 * G, task_peak=int(2.5 * G), parent=1 * G, requested=9) == 9
    assert C.plan_workers(limit=20 * G, task_peak=int(2.5 * G), parent=1 * G, requested=9) == 6     # floor((0.9*20 - 1) / 2.5)
    with pytest.raises(SystemExit, match="memory"):
        C.plan_workers(limit=2 * G, task_peak=int(2.5 * G), parent=1 * G, requested=9)


def test_r2_first_offer_newest_among_identities_with_assigned_jobs():
    rec = lambda offers, assign: NS(offers={i: None for i in offers}, assignment=assign, audits=())
    # identities 0 (focal), 1 (honest, offers first at t0), 2 (honest replacement created t1, first offer t2)
    ep = NS(entity_of=(0, 1, 1), identity_generation=(0, 0, 1), identity_round=(0, 0, 1),
            history=(rec([0, 1], {0: 0, 1: 1}), rec([0], {0: 0}), rec([0, 2], {0: 0, 1: 2}), rec([0, 2], {0: 0})))
    got = C.newcomer_shares([ep], focal=0, edges=(0, 100, 200))
    # t0: 0 and 1 tie at first offer 0 -> no; t1: only the focal has jobs -> yes; t2: identity 2 (first offer 2) newer -> no; t3: focal alone -> yes
    assert got["focal_newest_by_first_offer_assigned"] == [0.5]


# ---- internal review round 3 (Sol, Astra: reject) and the cross-cutting rules ----

def _gate_records(tmp_path, gain_out, knob_out=0.5):
    from sim.records_v2 import write
    rid = "fresh0@rho0.2|F111|D2+H3|profit"; cid = rid + "|churn0"
    prov = {"cfg_sha256": "c", "budget": [5, 300, 5, 200], "runner_sha256": "r", "salt_sha256": "s", "rule_params_sha256": "p", "root": "h",
            "seeds_train": [7], "seeds_val": [8], "seeds_eval": [1, 2], "context": "fresh0@rho0.2", "git_commit": "x"}
    def put(base, i, gain, u0):
        k = {"u0": u0, "x": 1, "clip": 0}
        write(C.R.path_of(base, i), {"stage": "search", "id": i, "attack": {"best_knobs": k, "best_f": 0.1, "best_source": "r", "archive": [0]},
                                     "twin": {"archive": [0], "best_f": 0.05}, "runs": 9, "upstream": {}, "provenance": {**prov, "id": i}})
        write(C.R.eval_path(base, i), {"stage": "evaluate", "seeds": [1, 2], "gain": gain,
                                       "upstream": {i: "a", "reference/fresh0@rho0.2/F111": "ref", "freeze/fresh0@rho0.2": "f"}})
        write(base / "doubling" / (C.R._safe(i) + ".json"), {"stage": "doubling", "incomplete": False, "attack_change": 0.0, "reference_change": 0.0,
                                                               "heldout": {"knobs": k, "seeds": [1, 2], "gain": gain}})
    put(tmp_path / "src", rid, [0.1, 0.2], 0.5); put(tmp_path / "out", cid, gain_out, knob_out)
    return rid, cid


def test_r3_pod_gate_requires_bit_identity_and_the_mac_gate_the_tolerance(tmp_path):
    rid, cid = _gate_records(tmp_path, [0.1, 0.2 + 1e-15])
    tol = C.gate_compare(tmp_path / "src", tmp_path / "out", rid, cid, require_identical=False)
    pod = C.gate_compare(tmp_path / "src", tmp_path / "out", rid, cid, require_identical=True)
    assert tol["pass"] and tol["gate_ok"] and not tol["identical"]
    assert pod["pass"] and not pod["gate_ok"] and pod["require_identical"]
    rid, cid = _gate_records(tmp_path / "same", [0.1, 0.2])
    assert C.gate_compare(tmp_path / "same" / "src", tmp_path / "same" / "out", rid, cid, require_identical=True)["gate_ok"]


def test_r3_a_production_stage_on_the_pod_needs_a_bit_identical_gate(tmp_path):
    from sim.records_v2 import write
    g = tmp_path / "gate-p0"; base = {"pass": True, "registered": "fresh0@rho0.2|F111|D2+H3|profit", "churn": "fresh0@rho0.2|F111|D2+H3|profit|churn0"}
    write(g / "inventory.json", {"environment": {"churn_driver_sha256": sha256_of(C.__file__)}})
    write(g / "gate.json", {**base, "gate_ok": True, "require_identical": False})
    C.require_gate(tmp_path, require_identical=False)
    with pytest.raises(SystemExit, match="bit-identical"):
        C.require_gate(tmp_path, require_identical=True)
    write(g / "gate.json", {**base, "gate_ok": True, "require_identical": True, "identical": True})
    C.require_gate(tmp_path, require_identical=True)


def test_r3_preflight_measures_real_tasks_one_per_rule_and_the_doubling(tmp_path):
    jobs = [{"id": f"m{i}|{r}", "rule": r, "context": f"m{i}"} for i in range(2) for r in ("F111", "C*", "F000")]
    peaks = {"F111": 2.0, "C*": 2.6, "F000": 2.2}; ran = []
    def runner(stage, job, out, catalog):
        ran.append((stage, job["id"])); return {"peak_rss_bytes": int(peaks[job["rule"]] * 2 ** 30), "status": "done"}
    G = 2 ** 30
    ev = C.memory_preflight("evaluate", jobs, tmp_path, 9, runner=runner, limit=32 * G, parent=G)
    assert [j for s, j in ran] == ["m0|F111", "m0|C*", "m0|F000"]                              # one real task per rule
    assert ev["task_peak_bytes"] == int(2.6 * G) and ev["margin"] == 1.25 and ev["workers"] == int((0.9 * 32 * G - G) // int(1.25 * 2.6 * G))
    assert ev["measured"] == ["m0|F111", "m0|C*", "m0|F000"]                                   # their records count as done
    ran.clear(); db = C.memory_preflight("doubling", jobs, tmp_path, 9, runner=runner, limit=32 * G, parent=G)
    assert len(ran) == 1 and db["stage"] == "doubling"


def test_r3_admission_is_rerun_after_the_preflight_and_the_reduced_workers_persist(tmp_path, monkeypatch):
    needs, runs = [], []
    monkeypatch.setattr(C, "check_cap", lambda started, need_s, *a, **k: needs.append(round(need_s)))
    monkeypatch.setattr(C, "memory_preflight", lambda stage, jobs, out, req, **k: {"workers": 2, "measured": [jobs[0]["id"]], "seconds": 100.0})
    monkeypatch.setattr(C, "run_stage", lambda st, jobs, out, w: runs.append((st, w, len(jobs))))
    monkeypatch.setattr(C.F, "accept", lambda *a, **k: None)
    monkeypatch.setattr(C, "diagnostics", lambda out, jobs, w: runs.append(("diagnostics", w, len(jobs))) or {})
    for f in ("check_configs", "check_salt", "check_commit", "check_code", "check_pairing"):
        monkeypatch.setattr(C.F, f, lambda *a, **k: None)
    a = NS(smoke=False, src="s", workers_search=16, workers_eval=9, stop_usd=8.0, usd_per_hour=0.56, prior_usd=0.0)
    jobs = [{"id": f"j{i}", "churn": 0.05, "rule": ("F111", "C*", "F000")[i % 3]} for i in range(18)]
    C._run_rate(tmp_path, jobs, ("evaluate", "doubling", "diagnostics"), a, "salt", {}, 0.05, started=1.0)
    s = C.STAGE_SECONDS; f = 1.33
    assert needs[0] == round(s["evaluate"] * f * (3 + 2))                                      # three serial preflight tasks + 15 jobs at nine workers
    assert needs[1] == round(s["evaluate"] * f * 9)                                            # rerun after the preflight: 17 remaining jobs at two workers
    assert needs[2] == round(s["doubling"] * f * (1 + 9))                                      # doubling: one preflight task + 17 jobs at the kept two workers
    assert needs[3] == round(s["doubling"] * f * 9)
    assert ("evaluate", 2, 17) in runs and ("doubling", 2, 17) in runs and ("diagnostics", 2, 18) in runs   # the limit persists


# ---- internal review round 4 (Sol, Astra: reject) ----

def _rate_env(monkeypatch, tmp_path, workers_by_stage, limit=32 * 2 ** 30):
    """_run_rate with every check stubbed; the preflight returns the given workers per stage."""
    needs, runs, pre = [], [], []
    monkeypatch.setattr(C, "check_cap", lambda started, need_s, *a, **k: needs.append(round(need_s)))
    monkeypatch.setattr(C, "memory_limit", lambda: limit)
    def mp(stage, jobs, out, req, **k):
        pre.append((stage, req)); return {"workers": min(req, workers_by_stage[stage]), "measured": [jobs[0]["id"]], "limit_bytes": limit, "seconds": 1.0}
    monkeypatch.setattr(C, "memory_preflight", mp)
    monkeypatch.setattr(C, "run_stage", lambda st, jobs, out, w: runs.append((st, w, len(jobs))))
    monkeypatch.setattr(C.F, "accept", lambda *a, **k: None)
    monkeypatch.setattr(C, "diagnostics", lambda out, jobs, w: runs.append(("diagnostics", w, len(jobs))) or {})
    for f in ("check_configs", "check_salt", "check_commit", "check_code", "check_pairing"):
        monkeypatch.setattr(C.F, f, lambda *a, **k: None)
    a = NS(smoke=False, src="s", workers_search=16, workers_eval=9, stop_usd=8.0, usd_per_hour=0.56, prior_usd=0.0)
    jobs = [{"id": f"j{i}", "churn": 0.05, "rule": ("F111", "C*", "F000")[i % 3]} for i in range(18)]
    return a, jobs, needs, runs, pre


def test_r4_a_skipped_record_is_never_a_memory_measurement(tmp_path):
    # Review r4: on resume, _run_one returns "skipped" for a valid record, so the child measures no real task.
    jobs = [{"id": f"m{i}|{r}", "rule": r} for i in range(3) for r in ("F111", "C*", "F000")]
    G = 2 ** 30; peaks = {"F111": 2.0, "C*": 2.6, "F000": 2.2}; ran = []
    done_before = {"m0|F111", "m0|C*"}                                                         # records left by a crashed earlier attempt
    def runner(stage, job, out, catalog):
        ran.append(job["id"])
        if job["id"] in done_before:
            return {"peak_rss_bytes": int(0.3 * G), "status": "skipped"}
        return {"peak_rss_bytes": int(peaks[job["rule"]] * G), "status": "done"}
    ev = C.memory_preflight("evaluate", jobs, tmp_path, 9, runner=runner, limit=32 * G, parent=G)
    assert "m0|F111" in ran and "m0|C*" in ran                                                 # the skipped attempts happened
    assert ran == ["m0|F111", "m1|F111", "m0|C*", "m1|C*", "m0|F000"]                          # each was replaced by a real task
    assert ev["task_peak_bytes"] == int(2.6 * G) and ev["measured"] == ["m1|F111", "m1|C*", "m0|F000"]
    assert all(v >= int(2.0 * G) for v in ev["peaks"].values())


def test_r4_a_rule_with_only_skipped_records_and_no_saved_peak_is_refused(tmp_path):
    jobs = [{"id": f"m{i}|F111", "rule": "F111"} for i in range(2)]; called = []
    def runner(stage, job, out, catalog):
        called.append(job["id"]); return {"peak_rss_bytes": 1, "status": "skipped"}
    with pytest.raises(SystemExit, match="memory evidence"):
        C.memory_preflight("evaluate", jobs, tmp_path, 9, runner=runner, limit=32 * 2 ** 30, parent=2 ** 30)
    assert called == ["m0|F111", "m1|F111"]


def test_r4_a_partial_stage_retry_reuses_the_validated_saved_peak(tmp_path):
    jobs = [{"id": f"m{i}|{r}", "rule": r} for i in range(2) for r in ("F111", "C*")]; G = 2 ** 30
    first = C.memory_preflight("evaluate", jobs, tmp_path, 9, runner=lambda s, j, o, c: {"peak_rss_bytes": int(2.6 * G), "status": "done"},
                               limit=32 * G, parent=G)
    assert (tmp_path / "memory_preflight_evaluate.json").exists()                               # the retry finds a saved measurement
    called = []
    def runner(stage, job, out, catalog):
        called.append(job["id"]); return {"peak_rss_bytes": 1, "status": "skipped"}
    again = C.memory_preflight("evaluate", jobs, tmp_path, 9, runner=runner, limit=32 * G, parent=G)
    assert called == [] and again["task_peak_bytes"] == first["task_peak_bytes"] and again["workers"] == first["workers"] and again["reused"]
    with pytest.raises(SystemExit, match="memory evidence"):                                   # a saved peak from another memory limit does not apply
        C.memory_preflight("evaluate", jobs, tmp_path, 9, runner=runner, limit=64 * G, parent=G)


def test_r4_the_worker_limit_persists_across_separate_stage_commands(tmp_path, monkeypatch):
    a, jobs, needs, runs, pre = _rate_env(monkeypatch, tmp_path, {"evaluate": 2, "doubling": 5})
    C._run_rate(tmp_path, jobs, ("evaluate",), a, "salt", {}, 0.05, started=1.0)
    assert ("evaluate", 2, 17) in runs
    C._run_rate(tmp_path, jobs, ("diagnostics",), a, "salt", {}, 0.05, started=1.0)          # a separate command
    assert runs[-1] == ("diagnostics", 2, 18)
    C._run_rate(tmp_path, jobs, ("doubling",), a, "salt", {}, 0.05, started=1.0)
    assert pre[-1] == ("doubling", 2) and runs[-1] == ("doubling", 2, 17)                     # the lowest limit is kept


def test_r4_diagnostics_without_memory_evidence_is_refused(tmp_path, monkeypatch):
    a, jobs, needs, runs, pre = _rate_env(monkeypatch, tmp_path, {"evaluate": 2, "doubling": 2})
    with pytest.raises(SystemExit, match="memory evidence"):
        C._run_rate(tmp_path, jobs, ("diagnostics",), a, "salt", {}, 0.05, started=1.0)
    assert not runs
    C._run_rate(tmp_path, jobs, ("evaluate",), a, "salt", {}, 0.05, started=1.0)
    monkeypatch.setattr(C, "memory_limit", lambda: 64 * 2 ** 30)                              # another pod: the saved limit does not apply
    with pytest.raises(SystemExit, match="memory evidence"):
        C._run_rate(tmp_path, jobs, ("diagnostics",), a, "salt", {}, 0.05, started=1.0)
