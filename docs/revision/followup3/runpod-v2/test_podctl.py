"""Every test runs under a 30 s alarm (a watchdog loop must never hang the suite).

podctl: fail-closed listing, verified deletion within elapsed time, reconciliation, creation block, sustained watchdog."""
import json
import os
import signal

import pytest


@pytest.fixture(autouse=True)
def _alarm():
    signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError('test exceeded 30 s')))
    signal.alarm(30); yield; signal.alarm(0)

import podctl as C


class Fake:
    """A fake Runpod: pods by id -> name; `fail_list` listings fail; a pod in `stuck` survives `stuck[id]` deletes."""
    def __init__(self, pods=None, fail_list=0, stuck=None, prices=None):
        self.pods = dict(pods or {}); self.fail_list = fail_list; self.stuck = dict(stuck or {}); self.t = 0.0; self.calls = []
        self.prices = dict(prices or {})
    def run(self, args, timeout=60):
        self.calls.append(args[0]); self.t += 1
        if args[0] == "list":
            if self.fail_list > 0:
                self.fail_list -= 1; return 1, ""
            return 0, json.dumps([{"id": i, "name": n, "costPerHr": self.prices.get(i, 0.5)} for i, n in self.pods.items()])
        if args[0] == "delete":
            pid = args[1]
            if self.stuck.get(pid, 0) > 0:
                self.stuck[pid] -= 1
            else:
                self.pods.pop(pid, None)
            return 0, "{}"
        return 0, ""
    def clock(self):
        return self.t
    def sleep(self, s):
        self.t += max(s, 0.01)


def test_a_failed_listing_is_never_an_empty_list():
    f = Fake({"a": "ts-r-x"}, fail_list=1)
    assert C.list_pods(f.run) is None and [p["id"] for p in C.list_pods(f.run)] == ["a"]


def test_delete_is_verified_and_bounded_by_elapsed_time():
    f = Fake({"a": "n"}, stuck={"a": 2})
    assert C.delete_verified("a", 100, f.run, f.clock, f.sleep) and "a" not in f.pods
    g = Fake({"a": "n"}, stuck={"a": 10**6})
    assert not C.delete_verified("a", 50, g.run, g.clock, g.sleep) and g.t < 50 + 20     # stops by elapsed time


def test_reconcile_fails_closed_on_listing_failures_and_survivors():
    f = Fake({"a": "ts-r-x", "keep": "ts-r-x", "other": "else"}, fail_list=3)
    assert C.reconcile("ts-r-x", "keep", 600, f.run, f.clock, f.sleep) and set(f.pods) == {"keep", "other"}
    g = Fake({"a": "ts-r-x"}, fail_list=10**6)                                          # listing never works
    assert not C.reconcile("ts-r-x", "", 100, g.run, g.clock, g.sleep)
    h = Fake({"a": "ts-r-x"}, stuck={"a": 10**6})                                       # deletion never takes effect
    assert not C.reconcile("ts-r-x", "", 100, h.run, h.clock, h.sleep)


def test_creation_is_blocked_after_the_hard_deadline_or_the_block_file(tmp_path):
    assert C.may_create("n", 10, clock=lambda: 5, here=str(tmp_path))
    assert not C.may_create("n", 10, clock=lambda: 11, here=str(tmp_path))
    (tmp_path / "n.blocked").write_text("1")
    assert not C.may_create("n", 10, clock=lambda: 5, here=str(tmp_path))


def test_watchdog_blocks_creation_and_keeps_deleting_until_none_remain(tmp_path):
    f = Fake({"a": "ts-r-x", "b": "ts-r-x"}, fail_list=0, stuck={"a": 30}); f.t = 100; (tmp_path / "done").write_text("")
    assert C.watchdog("ts-r-x", 50, str(tmp_path / "done"), f.run, f.clock, f.sleep, here=str(tmp_path), settle=60, mono=f.clock) == 0
    assert (tmp_path / "ts-r-x.blocked").exists() and not [i for i, n in f.pods.items() if n == "ts-r-x"]


def test_watchdog_waits_for_done_and_an_empty_listing_before_the_deadline(tmp_path):
    f = Fake({"a": "ts-r-x"}); done = tmp_path / "done"; done.write_text("")
    calls = {"n": 0}
    def sleep(s):
        f.t += s; calls["n"] += 1
        if calls["n"] == 3:
            f.pods.clear()                                                              # the launcher deleted its pod
    assert C.watchdog("ts-r-x", 10**6, str(done), f.run, f.clock, sleep, here=str(tmp_path), mono=f.clock) == 0
    assert not (tmp_path / "ts-r-x.blocked").exists()


def test_r10_delete_respects_the_budget_even_with_slow_commands():
    class Slow(Fake):
        def run(self, args, timeout=60):
            self.t += 60; return super().run(args, timeout)
    f = Slow({"a": "n"})
    assert not C.delete_verified("a", 1, f.run, f.clock, f.sleep)              # success after the budget is not success


def test_r10_watchdog_after_the_deadline_needs_done_and_a_settled_empty_listing(tmp_path):
    f = Fake({}); f.t = 100; done = tmp_path / "done"
    late = {"n": 0}
    def sleep(s):
        f.t += s; late["n"] += 1
        if late["n"] == 2:
            f.pods["late"] = "ts-r-x"                                             # a delayed creation appears
        if late["n"] == 6:
            done.write_text("")
    assert C.watchdog("ts-r-x", 50, str(done), f.run, f.clock, sleep, here=str(tmp_path), settle=60, mono=f.clock) == 0
    assert "late" not in f.pods and late["n"] >= 6


def test_r11_watchdog_before_the_deadline_settles_so_a_delayed_creation_is_deleted(tmp_path):
    # harness3 scenario 5: an ambiguous creation answer, DONE written, then the pod appears. One empty listing is not proof.
    f = Fake({}); done = tmp_path / "done"; done.write_text("")
    n = {"k": 0}
    def sleep(s):
        f.t += s; n["k"] += 1
        if n["k"] == 2:
            f.pods["late"] = "ts-r-x"
    assert C.watchdog("ts-r-x", 10**6, str(done), f.run, f.clock, sleep, here=str(tmp_path), settle=60, mono=f.clock) == 0
    assert n["k"] >= 2, "the watchdog stopped before the delayed pod appeared"
    assert "late" not in f.pods and "delete" in f.calls and not (tmp_path / "ts-r-x.blocked").exists()


def test_r12_settle_counts_only_after_done(tmp_path):
    # r11 Sol 3: empty time before DONE must not count; DONE appears at t=330, so exit must be at t >= 330 + settle
    f = Fake({}); f.t = 100; done = tmp_path / "done"
    def sleep(s):
        f.t += s
        if f.t >= 330 and not done.exists():
            done.write_text(""); sleep.at = f.t
    sleep.at = None
    assert C.watchdog("ts-r-x", 50, str(done), f.run, f.clock, sleep, here=str(tmp_path), settle=300, mono=f.clock) == 0
    assert sleep.at is not None and f.t >= sleep.at + 300


def test_r12_after_an_ambiguous_answer_the_settle_is_long_enough_for_a_late_pod(tmp_path):
    # r11 Sol 2 / Astra 2: a creation delayed beyond the normal settle (here at t=600 > 300) must still be deleted
    f = Fake({}); done = tmp_path / "done"; done.write_text(""); (tmp_path / "ts-r-x.request").write_text("pending")
    def sleep(s):
        f.t += s
        if f.t >= 600 and "late" not in f.pods and not sleep.added:
            f.pods["late"] = "ts-r-x"; sleep.added = True
    sleep.added = False
    assert C.watchdog("ts-r-x", 10**6, str(done), f.run, f.clock, sleep, here=str(tmp_path), settle=300, mono=f.clock) == 0
    assert sleep.added, "the watchdog stopped before the late pod appeared"
    assert "late" not in f.pods and f.t >= C.AMBIGUOUS_SETTLE


def test_r12_fractional_budget_is_passed_as_a_fractional_timeout():
    seen = []
    def run(args, timeout=60):
        seen.append(timeout); return 0, "[]"
    C.list_pods(run, 0.1)
    assert seen and seen[0] <= 0.1


@pytest.mark.parametrize("answer,exc,ambiguous", [
    ({"id": "p1"}, None, False),
    ({"error": 400, "body": "no capacity"}, None, False),
    ({"error": 404, "body": ""}, None, False),
    ({"error": 408, "body": ""}, None, True),
    ({"error": 429, "body": ""}, None, True),
    ({"error": 500, "body": ""}, None, True),
    ({"error": 504, "body": ""}, None, True),
    (None, None, True),
    ("garbage", None, True),
    (None, TimeoutError(), True),
])
def test_r12_creation_answers_are_ambiguous_unless_clearly_refused(answer, exc, ambiguous):
    pid, amb = C.classify_creation(answer, exc)
    assert amb is ambiguous and (pid == "p1") == (answer == {"id": "p1"})


@pytest.mark.parametrize("value,price", [
    (0.56, 0.56), ("0.56", 0.56), (None, None), (0, None), (-1, None), ("nan", None), ("inf", None), ("", None), ("x", None),
])
def test_r13_only_a_finite_positive_price_counts(value, price):
    # r12 Sol 3 / Astra 2: a missing or null price became 0 and left billing marked resolved
    assert C.price_of({"costPerHr": value}) == price
    assert C.price_of({}) is None


def test_r13_no_command_gets_more_time_than_the_budget_left():
    # r12 Sol 5 / Astra 4: a 0.001 s budget became a 0.01 s timeout
    seen = []
    def run(args, timeout=60):
        seen.append((args[0], timeout)); return 0, "[]"
    C.list_pods(run, 0.001)
    assert seen == [("list", 0.001)]
    seen.clear()
    assert C.list_pods(run, 0) is None and C.list_pods(run, -1) is None and seen == []
    t = {"now": 0.0}
    def slow(args, timeout=60):
        seen.append((args[0], timeout)); t["now"] += 0.0004; return 0, "[]"
    C.delete_verified("p", 0.001, slow, clock=lambda: t["now"], sleep=lambda s: None)
    start = 0.0
    assert seen and all(0 < to <= 0.001 for _, to in seen)


# r16: spend comes from the account balance; a pending request marker exists before every creation request; a launch
# lock; the watchdog records its end time and releases the lock.

@pytest.mark.parametrize("out,rc,expect", [
    ('{"balance": 10.5, "spendPerHr": 0}', 0, (10.5, 0.0)),
    ('{"balance": 10.5, "spendPerHr": 0.56}', 0, (10.5, 0.56)),
    ('{"balance": 10.5}', 0, None), ('{"balance": "nan", "spendPerHr": 0}', 0, None),
    ('{"balance": 10.5, "spendPerHr": -1}', 0, None), ("garbage", 0, None), ('{"balance": 1, "spendPerHr": 0}', 1, None),
])
def test_r16_balance_parses_or_fails_closed(out, rc, expect):
    assert C.balance(lambda args, timeout=60: (rc, out)) == expect


def _spend_setup(tmp_path, wd_ago, pods=None, bal_now=9.123, rate_now=0.0):
    (tmp_path / "n.bal0").write_text("10.0 0.0")
    if wd_ago is not None:
        import time as _t   # wall and monotonic end times (r17: both must show the hour)
        (tmp_path / "n.wdend").write_text(f"{1_000_000 - wd_ago} {_t.monotonic() - wd_ago}")
    f = Fake(pods or {})
    def run(args, timeout=60):
        if args[0] == "balance":
            return 0, json.dumps({"balance": bal_now, "spendPerHr": rate_now})
        return f.run(args, timeout)
    return run


def test_r16_spend_is_refused_until_the_watchdog_ended_an_hour_ago_and_no_pod_is_named(tmp_path):
    clock = lambda: 1_000_000
    assert C.spend("n", _spend_setup(tmp_path, None), clock, here=str(tmp_path))[0] is None          # watchdog not ended
    assert C.spend("n", _spend_setup(tmp_path, 3599), clock, here=str(tmp_path))[0] is None          # less than an hour
    assert C.spend("n", _spend_setup(tmp_path, 4000, {"x": "n"}), clock, here=str(tmp_path))[0] is None  # a pod named n


def test_r16_spend_is_the_balance_difference_rounded_up_to_a_cent(tmp_path):
    usd, note = C.spend("n", _spend_setup(tmp_path, 4000), lambda: 1_000_000, here=str(tmp_path))
    assert usd == 0.88 and "overstates" not in note
    usd, note = C.spend("n", _spend_setup(tmp_path, 4000, rate_now=0.3), lambda: 1_000_000, here=str(tmp_path))
    assert usd == 0.88 and "overstates" in note        # other usage on the account: the difference includes it


def test_r16_watchdog_writes_its_end_time_and_releases_the_launch_lock(tmp_path):
    f = Fake({}); done = tmp_path / "done"; done.write_text(""); (tmp_path / "ts-r-x.launchlock").mkdir()
    assert C.watchdog("ts-r-x", 10**6, str(done), f.run, f.clock, f.sleep, here=str(tmp_path), settle=60, mono=f.clock) == 0
    assert not (tmp_path / "ts-r-x.launchlock").exists() and all(float(x) > 0 for x in (tmp_path / "ts-r-x.wdend").read_text().split()) and len((tmp_path / "ts-r-x.wdend").read_text().split()) == 2


def test_r16_a_cleared_request_needs_only_the_normal_settle(tmp_path):
    f = Fake({}); done = tmp_path / "done"; done.write_text(""); (tmp_path / "ts-r-x.request").write_text("clear")
    assert C.watchdog("ts-r-x", 10**6, str(done), f.run, f.clock, f.sleep, here=str(tmp_path), settle=60, mono=f.clock) == 0
    assert f.t < C.AMBIGUOUS_SETTLE


def test_r16_elapsed_budgets_use_the_monotonic_clock():
    import inspect, time
    for fn in (C.delete_verified, C.reconcile):
        assert inspect.signature(fn).parameters["clock"].default is time.monotonic



# r17

def test_r17_a_wall_clock_jump_does_not_shorten_the_settle(tmp_path):
    # r16 Sol 2 / Astra 2: wall time +3600 s after 30 s of elapsed time ended the 1800 s settle
    f = Fake({}); done = tmp_path / "done"; done.write_text(""); (tmp_path / "ts-r-x.request").write_text("pending")
    mono = {"t": 0.0}; wall = {"t": 1000.0}
    def sleep(s):
        mono["t"] += s; wall["t"] += s
        if mono["t"] >= 30 and not sleep.jumped:
            wall["t"] += 3600; sleep.jumped = True
    sleep.jumped = False
    assert C.watchdog("ts-r-x", 10**9, str(done), f.run, lambda: wall["t"], sleep, here=str(tmp_path), settle=300,
                      mono=lambda: mono["t"]) == 0
    assert mono["t"] >= C.AMBIGUOUS_SETTLE


def test_r17_spend_rounds_up_exactly(tmp_path):
    # r16 Sol 5 / Astra 7: rounding to 6 places before ceil gave 0.01 for 0.010000001
    usd, _ = C.spend("n", _spend_setup(tmp_path, 4000, bal_now=9.989999999), lambda: 1_000_000, here=str(tmp_path))
    assert usd == 0.02


def test_r17_spend_refuses_a_balance_that_rose_and_states_the_credit_condition(tmp_path):
    # r16 Sol 1 / Astra 1: a credit or deposit raises the balance; the difference is valid only without one
    usd, why = C.spend("n", _spend_setup(tmp_path, 4000, bal_now=10.5), lambda: 1_000_000, here=str(tmp_path))
    assert usd is None and "credit" in why
    usd, note = C.spend("n", _spend_setup(tmp_path, 4000), lambda: 1_000_000, here=str(tmp_path))
    assert "valid only if no deposit or credit" in note


def test_r17_spend_writes_its_record(tmp_path):
    usd, note = C.spend("n", _spend_setup(tmp_path, 4000), lambda: 1_000_000, here=str(tmp_path))
    rec = (tmp_path / "n.spent").read_text()
    assert str(usd) in rec and "valid only if" in rec


# r18

def test_r18_a_wall_clock_jump_does_not_shorten_the_billing_wait(tmp_path):
    # r17 Sol 1: wall time jumped 4000 s while only 30 s elapsed; spend accepted the balance
    import time as _t
    run = _spend_setup(tmp_path, 4000)
    (tmp_path / "n.wdend").write_text(f"{1_000_000 - 4000} {_t.monotonic() - 30}")
    usd, why = C.spend("n", run, lambda: 1_000_000, here=str(tmp_path))
    assert usd is None and not (tmp_path / "n.spent").exists()


def test_r18_after_a_restart_the_wait_cannot_be_verified_and_spend_is_refused(tmp_path):
    import time as _t
    run = _spend_setup(tmp_path, 4000)
    (tmp_path / "n.wdend").write_text(f"{1_000_000 - 4000} {_t.monotonic() + 10**6}")   # monotonic went backwards
    usd, why = C.spend("n", run, lambda: 1_000_000, here=str(tmp_path))
    assert usd is None and "billing page" in why


def test_r18_spend_holds_the_launch_lock_and_refuses_while_it_is_held(tmp_path):
    # r17 Astra 1: a spend check overlapping a new launch wrote the old spend into the new launch's record
    run = _spend_setup(tmp_path, 4000)
    (tmp_path / "n.launchlock").mkdir()
    assert C.spend("n", run, lambda: 1_000_000, here=str(tmp_path))[0] is None and not (tmp_path / "n.spent").exists()
    (tmp_path / "n.launchlock").rmdir()
    seen = []
    def run2(args, timeout=60):
        seen.append((tmp_path / "n.launchlock").is_dir()); return run(args, timeout)
    assert C.spend("n", run2, lambda: 1_000_000, here=str(tmp_path))[0] == 0.88
    assert seen and all(seen) and not (tmp_path / "n.launchlock").exists()


def test_r18_a_failed_record_write_publishes_no_record(tmp_path, monkeypatch):
    # r17 Astra 2: a failed write left an empty .spent that the launcher accepted
    run = _spend_setup(tmp_path, 4000)
    def boom(*a, **k):
        raise OSError("disk full")
    monkeypatch.setattr(C.os, "replace", boom)
    usd, why = C.spend("n", run, lambda: 1_000_000, here=str(tmp_path))
    assert usd is None and not (tmp_path / "n.spent").exists() and not (tmp_path / "n.launchlock").exists()
