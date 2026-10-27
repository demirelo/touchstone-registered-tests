"""The budget ledger (operations plan Task 4): capped reservations, actual spend, the combined approval limit, the lock."""
import json
import multiprocessing as mp

import pytest


def _new(path, dev=10.0, ev=40.0):
    path.write_text(json.dumps({"caps": {"development": dev, "evaluation": ev}, "reservations": [], "spent": [], "approval": None}))
    return path


def test_reservations_are_aggregate(tmp_path):
    from scripts.budget_v2 import Refused, record, reserve
    p = _new(tmp_path / "l.json")
    assert reserve(p, "development", "a", 3.0) == pytest.approx(3.75) and reserve(p, "development", "b", 3.0) == pytest.approx(3.75)
    assert reserve(p, "development", "c", 2.0) == pytest.approx(2.5)
    with pytest.raises(Refused):
        reserve(p, "development", "d", 0.5)
    record(p, "a", 1.0)
    assert reserve(p, "development", "d", 2.0) == pytest.approx(2.5)            # 2.75 released by the actual spend
    d = json.loads(p.read_text())
    assert [r["tag"] for r in d["reservations"]] == ["b", "c", "d"] and d["spent"] == [{"op": "development", "tag": "a", "usd": 1.0}]


def test_combined_total_needs_approval(tmp_path):
    from scripts.budget_v2 import Refused, approve, reserve
    p = _new(tmp_path / "l.json", dev=12.0)
    d = json.loads(p.read_text()); d["spent"] = [{"op": "development", "tag": "x", "usd": 12.0}, {"op": "evaluation", "tag": "y", "usd": 27.0}]; p.write_text(json.dumps(d))
    with pytest.raises(Refused):
        reserve(p, "evaluation", "z", 3.2)                                        # 4 fits the evaluation cap; 43 passes the 40 USD limit
    approve(p, 45.0, "Approved up to 45 USD for the revision program. (author)")
    assert reserve(p, "evaluation", "z", 3.2) == pytest.approx(4.0)


def test_estimate_above_the_remainder_is_refused(tmp_path):
    from scripts.budget_v2 import Refused, reserve
    p = _new(tmp_path / "l.json", dev=2.0)
    with pytest.raises(Refused):
        reserve(p, "development", "a", 3.0)


def _child(path, tag, barrier, q):
    from scripts.budget_v2 import Refused, reserve
    barrier.wait()
    try:
        q.put((tag, reserve(path, "development", tag, 2.0)))
    except Refused:
        q.put((tag, None))


def test_concurrent_reservations_respect_the_cap(tmp_path):
    p = _new(tmp_path / "l.json"); ctx = mp.get_context("spawn"); barrier = ctx.Barrier(8); q = ctx.Queue()
    procs = [ctx.Process(target=_child, args=(p, f"p{i}", barrier, q)) for i in range(8)]
    [x.start() for x in procs]; [x.join(60) for x in procs]
    got = [q.get(timeout=10) for _ in range(8)]; ok = {t: g for t, g in got if g is not None}
    tags = [r["tag"] for r in json.loads(p.read_text())["reservations"]]
    assert len(ok) <= 4 and sum(ok.values()) <= 10.0 + 1e-9 and sorted(tags) == sorted(ok) and len(tags) == len(set(tags))


def _slow_child(path, tag, q):
    import time
    import scripts.budget_v2 as B
    B._after_read = lambda: time.sleep(1.5)
    q.put((tag, B.reserve(path, "development", tag, 1.0)))


def _fast_child(path, tag, q):
    import scripts.budget_v2 as B
    q.put((tag, B.reserve(path, "development", tag, 1.0)))


def test_lost_update_is_impossible(tmp_path):
    import time
    p = _new(tmp_path / "l.json"); ctx = mp.get_context("spawn"); q = ctx.Queue()
    a = ctx.Process(target=_slow_child, args=(p, "slow", q)); a.start(); time.sleep(0.8)
    b = ctx.Process(target=_fast_child, args=(p, "fast", q)); b.start(); a.join(60); b.join(60)
    assert {r["tag"] for r in json.loads(p.read_text())["reservations"]} == {"slow", "fast"}


def test_cli(tmp_path, capsys):
    from scripts.budget_v2 import main
    p = _new(tmp_path / "l.json")
    assert main(["--ledger", str(p), "--reserve", "development", "bench", "2.4"]) == 0 and "3.0" in capsys.readouterr().out
    assert main(["--ledger", str(p), "--record", "bench", "1.2"]) == 0 and main(["--ledger", str(p), "--show"]) == 0
    assert main(["--ledger", str(p), "--reserve", "development", "big", "50"]) == 1


# ---- final review K6: invalid amounts never disable the caps ----------------------------------------------------------------

@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0, 0.0])
def test_k6_invalid_estimates_are_refused(tmp_path, bad):
    from scripts.budget_v2 import Refused, reserve
    p = _new(tmp_path / "l.json")
    with pytest.raises(Refused):
        reserve(p, "development", "x", bad)
    assert json.loads(p.read_text())["reservations"] == []


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.5])
def test_k6_invalid_spend_is_refused(tmp_path, bad):
    from scripts.budget_v2 import Refused, record, reserve
    p = _new(tmp_path / "l.json"); reserve(p, "development", "a", 1.0)
    with pytest.raises(Refused):
        record(p, "a", bad)


def test_k6_a_corrupt_ledger_is_refused(tmp_path):
    from scripts.budget_v2 import Refused, reserve
    p = _new(tmp_path / "l.json"); d = json.loads(p.read_text()); d["spent"] = [{"op": "development", "tag": "x", "usd": float("nan")}]
    p.write_text(json.dumps(d))
    with pytest.raises(Refused):
        reserve(p, "development", "big", 1000.0)                         # a NaN must not make 1,250 USD look affordable


@pytest.mark.parametrize("limit,text", [(float("nan"), "ok"), (-5.0, "ok"), (45.0, "")])
def test_k6_invalid_approval_is_refused(tmp_path, limit, text):
    from scripts.budget_v2 import Refused, approve
    p = _new(tmp_path / "l.json")
    with pytest.raises(Refused):
        approve(p, limit, text)


@pytest.mark.parametrize("approval", [{"limit": 100.0, "text": ""}, {"limit": 100.0}, {"limit": 100.0, "text": "   "}])
def test_l1_a_saved_approval_needs_its_written_text(tmp_path, approval):
    from scripts.budget_v2 import Refused, reserve
    p = _new(tmp_path / "l.json", dev=12.0); d = json.loads(p.read_text())
    d["spent"] = [{"op": "development", "tag": "x", "usd": 12.0}]; d["approval"] = approval; p.write_text(json.dumps(d))
    with pytest.raises(Refused):
        reserve(p, "evaluation", "big", 32.0)


# ---- design draft 7 (Part A2 Task 10): the gate after the H4 decision ---------------------------------------------------------

def _decision_h4(tmp_path, **kw):
    p = tmp_path / "decision-h4.json"; p.write_text(json.dumps({"decision": {"stop": None, "approval_required": False, "total_usd": 38.0, **kw}}))
    return p


def test_reservation_gate_after_h4(tmp_path):
    from scripts.budget_v2 import Refused, approve, reserve
    p = _new(tmp_path / "l.json", dev=12.0)
    for dec, ok in ((_decision_h4(tmp_path, stop="evaluation"), False), (_decision_h4(tmp_path, approval_required=True, total_usd=45.0), False)):
        for tag in ("coverage-headline", "coverage-dev0"):
            with pytest.raises(Refused):
                reserve(p, "development", tag, 1.0, decision_h4=dec)
    dec = _decision_h4(tmp_path, approval_required=True, total_usd=45.0)
    approve(p, 45.0, "Approved up to 45 USD after the H4 timing. (author)")
    assert reserve(p, "development", "coverage-headline", 1.0, decision_h4=dec) > 0 and reserve(p, "development", "coverage-dev0", 1.0, decision_h4=dec) > 0
    assert reserve(p, "evaluation", "pod-fresh0", 1.0, decision_h4=_decision_h4(tmp_path, stop="development")) > 0    # the gate is for development only


def test_approved_limit_reaches_evaluation(tmp_path):
    from scripts.budget_v2 import Refused, approve, reserve
    p = _new(tmp_path / "l.json", dev=12.0)
    d = json.loads(p.read_text()); d["spent"] = [{"op": "development", "tag": "x", "usd": 11.0}, {"op": "evaluation", "tag": "y", "usd": 28.0}]; p.write_text(json.dumps(d))
    with pytest.raises(Refused):
        reserve(p, "evaluation", "z", 2.0)                                       # 39 + 2.5 passes 40
    approve(p, 45.0, "Approved up to 45 USD after the H4 timing. (author)")
    assert reserve(p, "evaluation", "z", 2.0) == pytest.approx(2.5)              # combined 41.5 within 45; evaluation 30.5 within its 40 cap
    with pytest.raises(Refused):
        reserve(p, "evaluation", "w", 4.0)                                       # combined 46.5 passes 45

