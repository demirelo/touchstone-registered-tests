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
    dg = read(d / "diagnostics.json")["fresh0@rho0.2|F111"]
    assert ev["stage"] == "evaluate" and ev["provenance"]["churn"] == 0.05 and len(ev["gain"]) == 2
    assert db["stage"] == "doubling" and "freeze/fresh0@rho0.2" in ev["upstream"] and f"reference/fresh0@rho0.2/F111" in ev["upstream"]
    assert dg["shares"]["honest_replacements_per_episode"] > 0                                  # churn happened in the evaluated episodes
    assert inv["churn"] == 0.05 and "churn_driver_sha256" in inv["environment"]
