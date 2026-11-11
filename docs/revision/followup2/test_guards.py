"""Shared guards of the follow-up runs (internal review round 1 of both plans)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guards as G  # noqa: E402
from sim.records_v2 import read, write  # noqa: E402


def test_a_locked_settings_override_is_refused(monkeypatch):
    monkeypatch.setenv("TOUCHSTONE_LOCKED", "/tmp/other.yaml")
    with pytest.raises(SystemExit, match="TOUCHSTONE_LOCKED"):
        G.pin_settings()
    monkeypatch.delenv("TOUCHSTONE_LOCKED")
    G.pin_settings()                                     # locked.yaml and the manifest equal protocol-v2


def test_budgets_must_equal_the_frozen_records(tmp_path):
    write(tmp_path / "rec.json", {"provenance": {"budget": [5, 300, 5, 200]}})
    G.check_budget({"id": "x", "budget": [5, 300, 5, 200]}, tmp_path / "rec.json")
    with pytest.raises(SystemExit, match="budget"):
        G.check_budget({"id": "x", "budget": [5, 150, 5, 200]}, tmp_path / "rec.json")


def test_saved_results_are_reused_only_under_the_same_binding(tmp_path):
    b = G.binding(inputs_sha="i", provenance={"id": "x"}, smoke=False, settings={"max_rounds": 3}, driver_sha="d")
    p = tmp_path / "r.json"
    assert G.reusable(p, b) is False                                            # nothing saved
    write(p, {"binding": b, "x": 1}); assert G.reusable(p, b) is True
    for k, v in (("smoke", True), ("settings", {"max_rounds": 2}), ("inputs_sha", "j"), ("driver_sha", "e")):
        with pytest.raises(SystemExit, match="binding"):
            G.reusable(p, {**b, k: v})


def test_the_inventory_names_this_driver_its_helpers_and_the_run(tmp_path):
    (tmp_path / "a.json").write_text("{}")
    inv = G.inventory(tmp_path, deviations=["d1"], files={"driver": Path(G.__file__)}, args=["--x", "1"])
    assert inv["deviations"] == ["d1"] and inv["files"]["driver"] == G.sha_file(Path(G.__file__)) and inv["args"] == ["--x", "1"]
    assert "a.json" in inv["records"] and "inventory.json" not in inv["records"] and "reset_followup_v2.py" in inv["files"]
    assert {"python", "numpy", "scipy", "cma", "blas", "cpu"} <= set(inv["environment"]) and "driver_sha256" not in inv["environment"]


def test_cost_stop_between_stages_never_kills(tmp_path):
    clock = iter([0.0, 3600.0 * 5]).__next__
    c = G.CostStop(cap_usd=3.0, usd_per_hour=0.56, started=0.0, clock=clock)
    assert c.allow("search", 1.0) is True                                      # 0 h spent + 1 h at 0.56
    assert c.allow("doubling", 1.0) is False and c.stopped == "doubling"        # 5 h = 2.80 USD + 0.56 > 3.00
    assert c.report()["stopped_before"] == "doubling"


def test_evidence_files_must_report_a_pass(tmp_path):
    write(tmp_path / "ok.json", {"pass": True}); write(tmp_path / "bad.json", {"pass": False})
    G.check_evidence([tmp_path / "ok.json"])
    with pytest.raises(SystemExit, match="evidence"):
        G.check_evidence([tmp_path / "ok.json", tmp_path / "bad.json"])
    with pytest.raises(SystemExit, match="evidence"):
        G.check_evidence([tmp_path / "missing.json"])


def test_finite_values_are_required():
    assert G.finite([0.1, 2], {"a": 0.3}) and not G.finite([0.1, float("nan")]) and not G.finite({"a": float("inf")})


def test_a_binding_survives_its_json_round_trip(tmp_path):
    b = G.binding(inputs_sha="i", provenance={"seeds": (1, 2)}, smoke=True, settings={"markets": ("fresh0",)}, driver_sha="d")
    write(tmp_path / "r.json", {"binding": b}); assert G.reusable(tmp_path / "r.json", G.binding("i", {"seeds": (1, 2)}, True, {"markets": ("fresh0",)}, "d"))


# ---- round 3: complete environment, full bindings, verified evidence, prior spend from the attempts file ----

def test_environment_comparison_covers_the_numerical_stack():
    e = G.environment()
    for k in ("scipy", "cma", "blas"):
        assert k in G.ENV_KEYS
        assert not G.same_environment(e, {**e, k: "other"})
    assert G.same_environment(e, dict(e))


def test_a_binding_carries_the_dependency_hashes():
    b = G.binding("i", {"budget": [5, 300, 5, 200]}, False, {"max_rounds": 3}, "d", deps={"report": "r1", "registered_doubling": "x"})
    assert b["deps"] == {"report": "r1", "registered_doubling": "x"}
    assert b != G.binding("i", {"budget": [5, 300, 5, 200]}, False, {"max_rounds": 3}, "d", deps={"report": "r2", "registered_doubling": "x"})


def _gate(path, cell, site, env, binding, ok=True):
    write(path, {"stage": "convergence gate", "cell": cell, "pass": ok, "site": site, "environment": env, "binding": binding})


def test_gate_evidence_matches_the_complete_binding_and_environment(tmp_path):
    here = G.environment(); mac = {**here, "cpu": "Apple M3"}
    want = {c: G.binding("i", {"budget": [5, 300, 5, 200], "id": c}, False, {"max_rounds": 1}, "d", deps={"report": "r"}) for c in ("a", "b")}
    ps = []
    for c in want:
        for site, env in (("mac", mac), ("pod", here)):
            p = tmp_path / f"{c}-{site}.json"; _gate(p, c, site, env, want[c]); ps.append(p)
    G.check_gate_evidence(ps, want)
    for drop in ps:
        with pytest.raises(SystemExit, match="evidence"):
            G.check_gate_evidence([p for p in ps if p != drop], want)
    write(tmp_path / "x.json", {"pass": True})
    with pytest.raises(SystemExit, match="evidence"):
        G.check_gate_evidence([tmp_path / "x.json"] + ps[1:], want)
    bad_bindings = [{**want["a"], "provenance": {"budget": [5, 150, 5, 200], "id": "a"}}, {**want["a"], "settings": {"max_rounds": 3}},
                    {**want["a"], "deps": {"report": "stale"}}, {**want["a"], "smoke": True}]
    for bb in bad_bindings:
        q = tmp_path / "a-pod.json"; _gate(q, "a", "pod", here, bb)
        with pytest.raises(SystemExit, match="evidence"):
            G.check_gate_evidence(ps, want)
    _gate(tmp_path / "a-pod.json", "a", "pod", {**here, "scipy": "0.0"}, want["a"])                  # another numerical stack
    with pytest.raises(SystemExit, match="evidence"):
        G.check_gate_evidence(ps, want)


R1, D1 = "headline@rho0.2|F111|D2|profit", "fresh0@rho0.2|F111|D2+H3|profit"
INPUT_ID = "reference/headline@rho0.2/F111"


def _reset_dir(d, stage, cell, ok=True, ident=True, env=None, inputs=None, budget=(5, 300, 5, 200), drop=None, tamper=None, output=True):
    """A reset-driver evidence directory as reproduce / reproduce_doubling write it, with its inventory."""
    d.mkdir(parents=True, exist_ok=True)
    write(d / "gate.json", {"stage": stage, "cell": cell, "pass": ok, "identical": ident})
    write(G.F.R.path_of(d, INPUT_ID), {"stage": "reference"})
    write(d / "inputs.json", inputs if inputs is not None else {INPUT_ID: G.sha_file(G.F.R.path_of(d, INPUT_ID))})
    write(G.F.R.path_of(d, cell), {"stage": "search", "id": cell, "provenance": {"budget": list(budget), "id": cell}})
    if output and stage == "reproduction gate":
        write(G.F.R.eval_path(d, cell), {"stage": "evaluate", "gain": [0.1]}); write(d / "freeze" / "headline@rho0.2.json", {"stage": "freeze"})
    elif output:
        write(d / "doubling" / (G.F.R._safe(cell) + ".json"), {"stage": "doubling"})
    recs = {str(p.relative_to(d)): G.sha_file(p) for p in sorted(d.rglob("*.json")) if p.name != "inventory.json"}
    if drop:
        recs.pop(drop)
    drv = G.sha_file(G.HERE.parent / "followup" / "reset_followup_v2.py")
    write(d / "inventory.json", {"environment": {**(env or G.environment()), "driver_sha256": drv}, "records": recs})
    if tamper:
        write(d / tamper, {"edited": True})
    return d


@pytest.fixture
def recompute_ok(monkeypatch):
    calls = []
    monkeypatch.setattr(G.F, "compare", lambda src, out, rid=None: calls.append(("compare", out)) or {"pass": True, "identical": True})
    monkeypatch.setattr(G.F, "compare_doubling", lambda src, out, rid: calls.append(("doubling", out)) or {"pass": True})
    return calls


def test_reset_evidence_requires_the_named_checks_their_records_and_a_recomputed_pass(tmp_path, recompute_ok, monkeypatch):
    monkeypatch.setattr(G, "_supporting_problems", lambda *a: [])     # supporting records: test_real_evidence_with_changed_supporting_records_is_refused
    write(tmp_path / "ref.json", {"stage": "reference"}); h = G.sha_file(tmp_path / "ref.json")
    want = {"repro_inputs": {INPUT_ID: h}, "dbl_inputs": {INPUT_ID: h}, "budget": [5, 300, 5, 200], "src": tmp_path / "src"}
    mac = _reset_dir(tmp_path / "mac", "reproduction gate", R1, ident=False, env={**G.environment(), "cpu": "Apple"})
    pod = _reset_dir(tmp_path / "pod", "reproduction gate", R1)
    dbl = _reset_dir(tmp_path / "dbl", "doubling gate", D1, ident=False, env={**G.environment(), "cpu": "Apple"})
    G.check_reset_evidence(mac, pod, dbl, want)
    assert ("compare", pod) in recompute_ok and ("doubling", dbl) in recompute_ok
    ev = G.F.R._safe(R1)
    bad = {"unrelated stage": dict(stage="doubling gate", cell=R1), "wrong cell": dict(stage="reproduction gate", cell="fresh0@rho0.2|F111|D2|profit"),
           "not identical": dict(stage="reproduction gate", cell=R1, ident=False), "half budget": dict(stage="reproduction gate", cell=R1, budget=(5, 150, 5, 200)),
           "stale inputs": dict(stage="reproduction gate", cell=R1, inputs={INPUT_ID: "2" * 64}), "unlisted gate": dict(stage="reproduction gate", cell=R1, drop="gate.json"),
           "unlisted evaluation": dict(stage="reproduction gate", cell=R1, drop=f"evaluate/{ev}.json"),
           "no evaluation": dict(stage="reproduction gate", cell=R1, output=False),
           "changed search output": dict(stage="reproduction gate", cell=R1, tamper=f"search/{ev}.json"),
           "other numerical stack": dict(stage="reproduction gate", cell=R1, env={**G.environment(), "cma": "0"})}
    for name, kw in bad.items():
        with pytest.raises(SystemExit, match="evidence"):
            G.check_reset_evidence(mac, _reset_dir(tmp_path / name.replace(" ", "_"), **kw), dbl, want)
    with pytest.raises(SystemExit, match="evidence"):
        G.check_reset_evidence(mac, pod, _reset_dir(tmp_path / "nodbl", "doubling gate", D1, ident=False, output=False), want)
    monkeypatch.setattr(G.F, "compare_doubling", lambda src, out, rid: {"pass": False})          # the recomputed comparison fails
    with pytest.raises(SystemExit, match="evidence"):
        G.check_reset_evidence(mac, pod, dbl, want)


def _launcher_events(path, lines):
    """Lines exactly as results/pods/reset_pod.sh writes them: echo "$id $(date +%s) start" / "... deleted"."""
    path.write_text("".join(f"{l}\n" for l in lines)); return path


def test_prior_spend_reads_the_launchers_event_lines(tmp_path):
    f = _launcher_events(tmp_path / "ts-r-x.attempts", ["p1 1000 start", "p1 4600 deleted", "p2 5000 start", "p2 5060 deleted", "p3 6000 start"])
    got = G.attempts_spend(f, usd_per_hour=0.56)
    assert got["closed_usd"] == pytest.approx((3600 + 60) / 3600 * 0.56) and got["open"] == ["p3"]          # p3 is the current pod
    for bad in (["p1 1000 start", "p1 900 deleted"], ["garbled"], ["p1 1000 deleted"], ["p1 1000 start", "p1 2000 start"]):
        with pytest.raises(SystemExit, match="attempts"):
            G.attempts_spend(_launcher_events(tmp_path / "bad.attempts", bad), 0.56)
    with pytest.raises(SystemExit, match="attempts"):
        G.attempts_spend(tmp_path / "missing.attempts", 0.56)


def test_earlier_launches_come_from_the_ledger(tmp_path):
    led = tmp_path / "ledger.json"
    write(led, {"caps": {"followup": 22.0}, "reservations": [], "spent": [{"op": "followup", "tag": "runner-up-1", "usd": 1.2},
                                                                        {"op": "followup", "tag": "runner-up-2", "usd": 0.3}, {"op": "followup", "tag": "reset-1", "usd": 2.0}]})
    assert G.ledger_spend(led, "runner-up") == pytest.approx(1.5)
    with pytest.raises(SystemExit, match="ledger"):
        G.ledger_spend(tmp_path / "none.json", "runner-up")


def test_paid_runs_need_the_allocation_time_the_attempts_and_the_ledger(tmp_path):
    f = _launcher_events(tmp_path / "a.attempts", ["p1 0 start", "p1 3600 deleted", "p2 4000 start"]); led = tmp_path / "l.json"
    write(led, {"spent": [{"op": "followup", "tag": "run-1", "usd": 0.5}]})
    with pytest.raises(SystemExit, match="allocation"):
        G.paid_cost_stop(3.0, 0.56, started=None, attempts=f, ledger=led, tag="run")
    with pytest.raises(SystemExit, match="attempts"):
        G.paid_cost_stop(3.0, 0.56, started=0.0, attempts=None, ledger=led, tag="run")
    c = G.paid_cost_stop(3.0, 0.56, started=4000.0, attempts=f, ledger=led, tag="run", clock=lambda: 4000.0)
    assert c.prior == pytest.approx(0.5 + 0.56) and c.allow("x", 1.0) is True and c.allow("y", 4.0) is False   # 1.06 + 2.24 = 3.30 > 3.00


def test_the_launchers_stop_file_and_soft_deadline_block_the_next_stage(tmp_path):
    stop = tmp_path / "STOP"
    c = G.CostStop(10.0, 0.56, 0.0, clock=lambda: 50.0, stop_file=stop, soft_deadline=100.0)
    assert c.allow("a", 0.0) is True
    stop.write_text(""); assert c.allow("b", 0.0) is False and c.report()["stopped_before"] == "b"
    c2 = G.CostStop(10.0, 0.56, 0.0, clock=lambda: 150.0, soft_deadline=100.0); assert c2.allow("a", 0.0) is False


# ---- round 5: strict attempts, spend admission CLI, evidence with the real comparison functions ----

def test_attempts_need_ordered_finite_events_and_exactly_one_open_attempt(tmp_path):
    ok = _launcher_events(tmp_path / "ok.attempts", ["p1 1000 start", "p1 4600 deleted", "p2 5000 start"])
    assert G.attempts_spend(ok, 0.56, started=5000.0, now=6000.0)["open"] == ["p2"]
    bad = {"empty": [], "reverse order": ["p1 1000 start", "p1 4600 deleted", "p2 4000 start"], "two open": ["p1 1000 start", "p2 2000 start"],
           "nan time": ["p1 nan start"], "none open": ["p1 1000 start", "p1 2000 deleted"]}
    for name, lines in bad.items():
        with pytest.raises(SystemExit, match="attempts"):
            G.attempts_spend(_launcher_events(tmp_path / f"{name.replace(' ', '_')}.attempts", lines), 0.56, started=5000.0, now=6000.0)
    for started in (4000.0, 7000.0):                                                       # before the open start; in the future
        with pytest.raises(SystemExit, match="allocation"):
            G.attempts_spend(ok, 0.56, started=started, now=6000.0)


def test_the_admission_command_counts_attempts_and_earlier_launches(tmp_path):
    f = _launcher_events(tmp_path / "a.attempts", ["p1 0 start", "p1 3600 deleted", "p2 4000 start"]); led = tmp_path / "l.json"
    write(led, {"spent": [{"op": "followup", "tag": "runner-up-1", "usd": 2.0}]})
    base = ["admit", "--cap-usd", "3.00", "--usd-per-hour", "0.56", "--started-at", "4000", "--attempts", str(f), "--ledger", str(led),
            "--run-tag", "runner-up", "--now", "4000"]
    assert G.main(base + ["--hours", "0.6"]) == 0                                          # 2.00 + 0.56 + 0.336 = 2.90
    assert G.main(base + ["--hours", "0.9"]) == 3                                          # 2.00 + 0.56 + 0.504 = 3.06 > 3.00
    assert G.main(base[:-2] + ["--now", "4000", "--hours", "0.6", "--stop-file", str(f)]) == 3   # the STOP file exists


def test_reservation_inputs_grant_exactly_the_stop_caps():
    assert G.reservation_input(3.00) == pytest.approx(2.40) and G.reservation_input(4.25) == pytest.approx(3.40)


EVID = Path("/Users/oemer.demirel/Projects/touchstone/results/v2")


def _real_want():
    import json as _j
    sys.path.insert(0, str(Path(__file__).resolve().parent)); import runnerup_v2 as A
    from sim.records import cfg_from_dict
    root = _j.loads((EVID / "draw/draw.json").read_text())["hash"]; salt = _j.loads((EVID / "draw/instances.json").read_text())["salt_sha256"]
    cfgs = {k: cfg_from_dict(v) for k, v in _j.loads((EVID / "deviation/cfg_linux.json").read_text()).items()}
    return A.evidence_want(EVID / "eval/all", root, cfgs, _j.loads((A.ROOT / "experiments/v2/params.json").read_text()), salt)


def _resign(d):
    inv = read(d / "inventory.json")
    inv["records"] = {str(p.relative_to(d)): G.sha_file(p) for p in sorted(d.rglob("*")) if p.is_file() and p.name != "inventory.json"}
    write(d / "inventory.json", inv)


@pytest.mark.skipif(not (EVID / "followup2-a-gate-repro/gate.json").exists(), reason="needs the saved Run A Mac evidence")
def test_real_evidence_with_changed_supporting_records_is_refused(tmp_path):
    import shutil
    want = _real_want(); R1 = G.REPRO_CELL; D1 = G.DBL_CELL
    G._verified_dir(EVID / "followup2-a-gate-repro", "reproduction gate", R1, want["repro_inputs"], want["budget"], "mac", want["src"])
    def mutated(src_dir, name, fn):
        d = tmp_path / name; shutil.copytree(src_dir, d); fn(d); _resign(d); return d
    ev = lambda d: G.F.R.eval_path(d, R1)
    cases = {
        "evaluation provenance": (EVID / "followup2-a-gate-repro", lambda d: write(ev(d), {**read(ev(d)), "provenance": {**read(ev(d))["provenance"], "root": "x"}})),
        "evaluation dependency hash": (EVID / "followup2-a-gate-repro", lambda d: write(ev(d), {**read(ev(d)), "upstream": {k: "0" * 64 for k in read(ev(d))["upstream"]}})),
        "empty freeze": (EVID / "followup2-a-gate-repro", lambda d: write(d / "freeze" / "headline@rho0.2.json", {**read(d / "freeze" / "headline@rho0.2.json"), "records": {}})),
        "missing copied input": (EVID / "followup2-a-gate-repro", lambda d: shutil.move(str(G.F.R.path_of(d, f"reference/headline@rho0.2/F111")), str(tmp_path / "moved.json"))),
    }
    for name, (base, fn) in cases.items():
        with pytest.raises(SystemExit, match="evidence"):
            G._verified_dir(mutated(base, name.replace(" ", "_"), fn), "reproduction gate", R1, want["repro_inputs"], want["budget"], "mac", want["src"])
    dbl = lambda d: d / "doubling" / (G.F.R._safe(D1) + ".json")
    for name, fn in {"doubling provenance": lambda d: write(dbl(d), {**read(dbl(d)), "provenance": {**read(dbl(d))["provenance"], "root": "x"}}),
                     "doubling dependencies": lambda d: write(dbl(d), {**read(dbl(d)), "upstream": {}})}.items():
        with pytest.raises(SystemExit, match="evidence"):
            G._verified_dir(mutated(EVID / "followup2-a-gate-dbl", name.replace(" ", "_"), fn), "doubling gate", D1, want["dbl_inputs"], want["budget"], "doubling", want["src"])


# ---- round 6: conservative accounting start, ledger and amount validation, search identity, grant check ----

def test_accounting_starts_at_the_recorded_open_event(tmp_path):
    f = _launcher_events(tmp_path / "a.attempts", ["p1 0 start"]); led = tmp_path / "l.json"; write(led, {"spent": [{"op": "followup", "tag": "r-1", "usd": 2.5}]})
    c = G.paid_cost_stop(3.0, 0.56, started=3600.0, attempts=f, ledger=led, tag="r", clock=lambda: 3600.0)    # --started-at = now, one hour after the event
    assert c.started == 0.0 and c.allow("gate", 0.61) is False                                                 # 2.50 + 0.56 + 0.34 > 3.00


@pytest.mark.parametrize("ledger", [{}, {"spent": "x"}, {"spent": [{"op": "followup", "tag": "r-1", "usd": -4.0}]},
                                    {"spent": [{"op": "followup", "tag": "r-1", "usd": float("nan")}]}, {"spent": [{"op": "followup", "tag": "r-1"}]}])
def test_a_malformed_ledger_is_refused(tmp_path, ledger):
    write(tmp_path / "l.json", ledger)
    with pytest.raises(SystemExit, match="ledger"):
        G.ledger_spend(tmp_path / "l.json", "r")


@pytest.mark.parametrize("cap,rate,hours", [(float("inf"), 0.56, 0.5), (3.0, float("nan"), 0.5), (3.0, 0.56, -10.0), (3.0, 0.56, float("inf"))])
def test_admission_amounts_must_be_finite_and_valid(tmp_path, cap, rate, hours):
    f = _launcher_events(tmp_path / "a.attempts", ["p1 0 start"]); led = tmp_path / "l.json"; write(led, {"spent": []})
    with pytest.raises(SystemExit):
        G.main(["admit", "--cap-usd", str(cap), "--usd-per-hour", str(rate), "--started-at", "0", "--attempts", str(f), "--ledger", str(led),
                "--run-tag", "r", "--hours", str(hours), "--now", "0"])


def test_the_reservation_grant_must_equal_the_stop_cap():
    G.check_grant(3.00, 3.00)
    with pytest.raises(SystemExit, match="grant"):
        G.check_grant(2.75, 3.00)


@pytest.mark.skipif(not (EVID / "followup2-a-gate-repro/gate.json").exists(), reason="needs the saved Run A Mac evidence")
def test_real_evidence_with_a_changed_search_identity_is_refused(tmp_path):
    import shutil
    want = _real_want(); R1 = G.REPRO_CELL
    for name, change in (("search stage", lambda r: {**r, "stage": "reference"}), ("search id", lambda r: {**r, "id": "headline@rho0.2|F000|D2|profit"}),
                         ("provenance id", lambda r: {**r, "provenance": {**r["provenance"], "id": "headline@rho0.2|F000|D2|profit"}})):
        d = tmp_path / name.replace(" ", "_"); shutil.copytree(EVID / "followup2-a-gate-repro", d)
        p = G.F.R.path_of(d, R1); write(p, change(read(p)))
        fr = read(d / "freeze" / "headline@rho0.2.json"); fr["records"][R1] = G.sha_file(p); write(d / "freeze" / "headline@rho0.2.json", fr)
        ev = read(G.F.R.eval_path(d, R1)); ev["upstream"][R1] = G.sha_file(p); ev["upstream"]["freeze/headline@rho0.2"] = G.sha_file(d / "freeze" / "headline@rho0.2.json")
        write(G.F.R.eval_path(d, R1), ev); _resign(d)
        with pytest.raises(SystemExit, match="evidence"):
            G._verified_dir(d, "reproduction gate", R1, want["repro_inputs"], want["budget"], "mac", want["src"])
