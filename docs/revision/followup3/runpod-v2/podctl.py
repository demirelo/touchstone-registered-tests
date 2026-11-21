"""Pod safety primitives for the follow-up launchers (internal reviews r8-r16 of reset_pod.sh). Every function fails
closed: a failed listing counts as "pods may still exist", and success needs a successful listing that shows no pod.
Elapsed budgets use the monotonic clock; deadlines (HARD_TS) are wall-clock epoch seconds.

Spend (r16): the record is the account balance difference, NAME.bal0 (written before the first creation request) minus
the balance at least an hour after the watchdog ended. Other usage on the account during that time is included, so the
record can overstate the spend, never understate it. The launcher prints only estimates.

CLI (exit 0 = success):
  podctl.py reconcile NAME [KEEP_ID]          delete every pod named NAME except KEEP_ID; verified by a fresh listing
  podctl.py delete ID SECONDS                 delete one pod and verify it is gone within SECONDS
  podctl.py price ID                          print ID's price (finite, positive); exit 1 when unknown
  podctl.py balance                           print "BALANCE SPEND_PER_HR"; exit 1 when unknown
  podctl.py spend NAME                        print the recorded spend (USD, rounded up to a cent); refused until the
                                              watchdog ended at least WAIT_AFTER_WATCHDOG s ago and no pod is named NAME
  podctl.py watchdog NAME HARD_TS DONE_FILE   after DONE_FILE, or from HARD_TS (also writes NAME.blocked): delete every
                                              pod named NAME; exits only with DONE_FILE and the settle time of empty
                                              listings; then writes NAME.wdend and releases NAME.launchlock
  podctl.py unlock NAME                       release NAME.launchlock (only an empty directory)
  podctl.py may-create NAME HARD_TS           exit 0 only before HARD_TS and while NAME.blocked does not exist
  podctl.py remaining UNTIL_TS                print the seconds left (0 when past)
"""
from __future__ import annotations

import datetime
import json
import math
import os
import subprocess
import sys
import time
from decimal import ROUND_CEILING, Decimal, InvalidOperation

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

SETTLE = 300               # seconds of consecutive empty listings, counted only after DONE, before the watchdog ends
AMBIGUOUS_SETTLE = 1800    # the same while NAME.request is "pending" (an outstanding or ambiguous creation request)
WAIT_AFTER_WATCHDOG = 3600  # assumed bound on the delay before the account balance shows the last charge


def _run(args, timeout=60):
    try:
        r = subprocess.run([PY, os.path.join(HERE, "runpod.py")] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return 124, ""


def list_pods(run=_run, timeout=60):
    """The pods as a list, or None when the listing failed (never an empty list on failure). No command runs without a
    positive budget, and the budget is passed unchanged (r12, r13)."""
    if float(timeout) <= 0:
        return None
    rc, out = run(["list"], timeout=float(timeout))
    if rc != 0:
        return None
    try:
        pods = json.loads(out)
    except ValueError:
        return None
    return pods if isinstance(pods, list) else None


def named(pods, name):
    return [p["id"] for p in pods if p.get("name") == name]


def delete_verified(pid, seconds, run=_run, clock=time.monotonic, sleep=time.sleep):
    """Delete PID until a successful listing no longer shows it, within SECONDS of elapsed time."""
    end = clock() + seconds
    while clock() < end:
        run(["delete", pid], timeout=min(60.0, end - clock()))
        if clock() >= end:
            break
        pods = list_pods(run, min(60, end - clock()))
        if clock() < end + 1e-9 and pods is not None and pid not in [p["id"] for p in pods]:
            return clock() <= end
        sleep(min(15, max(0.0, end - clock())))
    return False


def reconcile(name, keep="", seconds=600, run=_run, clock=time.monotonic, sleep=time.sleep):
    """Delete every pod named NAME except KEEP; True only when a successful listing shows none left."""
    end = clock() + seconds
    while clock() < end:
        pods = list_pods(run, min(60, end - clock()))
        if pods is not None and clock() <= end:
            extra = [i for i in named(pods, name) if i != keep]
            if not extra:
                return True
            for i in extra:
                if clock() >= end:
                    break
                delete_verified(i, end - clock(), run, clock, sleep)
        sleep(min(15, max(0.0, end - clock())))
    return False


def may_create(name, hard_ts, clock=time.time, here=HERE):
    return clock() < hard_ts and not os.path.exists(os.path.join(here, f"{name}.blocked"))


def classify_creation(answer, exc=None):
    """(pod id, ambiguous) for one creation request. Only a clear client refusal (HTTP 4xx other than 408 and 429) is
    unambiguous; a timeout, exception, server or gateway error, or unreadable answer may still create a pod (r11)."""
    if exc is not None:
        return "", True
    if isinstance(answer, dict) and answer.get("id"):
        return str(answer["id"]), False
    if isinstance(answer, dict) and isinstance(answer.get("error"), int):
        code = answer["error"]
        return "", not (400 <= code < 500 and code not in (408, 429))
    return "", True


def _finite(v, minimum):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v >= minimum else None


def price_of(pod):
    """The pod's price in USD/h when it is finite and positive, else None (missing, null, zero or unreadable: r12)."""
    v = _finite((pod or {}).get("costPerHr"), 0)
    return v if v is not None and v > 0 else None


def price(pid, run=_run):
    pods = list_pods(run)
    pod = next((p for p in pods or [] if p.get("id") == pid), None)
    return price_of(pod)


def balance(run=_run):
    """(balance USD, account spend USD/h) from `runpod.py balance`, or None when either is missing or unreadable."""
    rc, out = run(["balance"], timeout=60)
    if rc != 0:
        return None
    try:
        d = json.loads(out)
    except ValueError:
        return None
    if not isinstance(d, dict):
        return None
    b, s = _finite(d.get("balance"), -math.inf), _finite(d.get("spendPerHr"), 0)
    return None if b is None or s is None else (b, s)


def _utc(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def spend(name, run=_run, clock=time.time, here=HERE, mono=time.monotonic):
    """(USD rounded up to a cent, note) or (None, reason); on success also writes NAME.spent. Needs NAME.bal0, NAME.wdend
    at least WAIT_AFTER_WATCHDOG s old by both wall and monotonic time (r17; after a restart the wait cannot be verified
    and spend is refused), a successful listing with no pod named NAME, a readable balance, and a balance that did not
    rise (a rise proves a credit or deposit). The difference is valid only if no deposit or credit was added in the
    window (r16): the author confirms that on the Runpod billing page; the note names the window. It holds
    NAME.launchlock while it works, so it cannot overlap a launch (r17), and publishes NAME.spent atomically."""
    lock = os.path.join(here, f"{name}.launchlock")
    try:
        os.mkdir(lock)
    except OSError:
        return None, "a launch or its watchdog holds NAME.launchlock"
    try:
        return _spend_locked(name, run, clock, here, mono)
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


def _spend_locked(name, run, clock, here, mono):
    f0 = os.path.join(here, f"{name}.bal0")
    try:
        bal0 = Decimal(open(f0).read().split()[0]); t0 = os.path.getmtime(f0)
    except (OSError, IndexError, InvalidOperation):
        return None, "no starting balance (NAME.bal0)"
    try:
        wdend, wdmono = (float(x) for x in open(os.path.join(here, f"{name}.wdend")).read().split()[:2])
    except (OSError, ValueError):
        return None, "the watchdog has not ended"
    if mono() < wdmono:
        return None, "the machine restarted since the watchdog ended, so the wait cannot be verified; take the spend from the Runpod billing page"
    if clock() - wdend < WAIT_AFTER_WATCHDOG or mono() - wdmono < WAIT_AFTER_WATCHDOG:
        return None, f"wait until {WAIT_AFTER_WATCHDOG} s after the watchdog ended"
    pods = list_pods(run)
    if pods is None or named(pods, name):
        return None, "a pod named NAME may still exist"
    b = balance(run)
    if b is None:
        return None, "balance unknown"
    now = Decimal(str(b[0]))
    if now > bal0:
        return None, "the balance rose (a credit or deposit was added); take the spend from the Runpod billing page"
    usd = float((bal0 - now).quantize(Decimal("0.01"), rounding=ROUND_CEILING))
    note = (f"balance difference; valid only if no deposit or credit was added between {_utc(t0)} and {_utc(clock())} "
            f"(check the Runpod billing page)"
            + (f"; the account still bills {b[1]} USD/h elsewhere, so this overstates" if b[1] > 0 else ""))
    final, tmp = os.path.join(here, f"{name}.spent"), os.path.join(here, f"{name}.spent.tmp")
    try:
        with open(tmp, "w") as f:
            f.write(f"{usd} USD {note}\n"); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, final)     # published only when complete (r17)
    except OSError as e:
        return None, f"could not write the spend record ({e})"
    return usd, note


def _request_pending(here, name):
    try:
        return open(os.path.join(here, f"{name}.request")).read().strip() == "pending"
    except OSError:
        return False


def watchdog(name, hard_ts, done_file, run=_run, clock=time.time, sleep=time.sleep, here=HERE, settle=SETTLE,
             mono=time.monotonic):
    """Ends only when DONE_FILE exists and successful listings show no pod named NAME for the settle time, counted from
    DONE onwards (r11); while NAME.request is "pending" (an outstanding or ambiguous creation request) the settle time is
    at least AMBIGUOUS_SETTLE. After DONE (the launcher reconciles first) any pod named NAME is an orphan and is deleted.
    From HARD_TS it also blocks creation and deletes every pod named NAME, with no retry limit. On exit it writes
    NAME.wdend and releases NAME.launchlock (it is the last process of a launch). Wall time (CLOCK) is used only for the
    hard deadline; the settle time and deletion budgets use MONO, so a clock change cannot shorten them (r16)."""
    blocked = False
    empty_since = None
    while True:
        if not blocked and clock() >= hard_ts:
            open(os.path.join(here, f"{name}.blocked"), "w").write(str(int(clock())))
            print(f"{time.strftime('%H:%M')} WATCHDOG: hard deadline; creation blocked; deleting every pod named {name}", flush=True)
            blocked = True
        done = os.path.exists(done_file)
        need = max(settle, AMBIGUOUS_SETTLE) if _request_pending(here, name) else settle
        if done or blocked:
            pods = list_pods(run)
            if pods is None:
                empty_since = None
            else:
                ids = named(pods, name)
                if ids:
                    empty_since = None
                    for i in ids:
                        print(f"{time.strftime('%H:%M')} WATCHDOG: deleting {i}", flush=True)
                        delete_verified(i, 120, run, mono, sleep)
                elif done:
                    empty_since = mono() if empty_since is None else empty_since
                    if mono() - empty_since >= need:
                        open(os.path.join(here, f"{name}.wdend"), "w").write(f"{time.time()} {time.monotonic()}")   # wall, monotonic (r17)
                        try:
                            os.rmdir(os.path.join(here, f"{name}.launchlock"))
                        except OSError:
                            pass
                        print(f"{time.strftime('%H:%M')} WATCHDOG: no pod named {name} for {need}s after the launcher was done; "
                              f"record the spend with `podctl.py spend {name}` from {WAIT_AFTER_WATCHDOG}s after now", flush=True)
                        return 0
                else:
                    empty_since = None
        sleep(30 if blocked else min(30, max(0.0, hard_ts - clock())) or 30)


def main(argv) -> int:
    cmd, a = argv[0], argv[1:]
    if cmd == "reconcile":
        return 0 if reconcile(a[0], a[1] if len(a) > 1 else "") else 1
    if cmd == "delete":
        return 0 if delete_verified(a[0], float(a[1])) else 1
    if cmd == "price":
        p = price(a[0]); print(p if p is not None else "unknown"); return 0 if p is not None else 1
    if cmd == "balance":
        b = balance(); print(f"{b[0]} {b[1]}" if b else "unknown"); return 0 if b else 1
    if cmd == "spend":
        usd, note = spend(a[0]); print(f"{usd} USD ({note})" if usd is not None else f"refused: {note}"); return 0 if usd is not None else 1
    if cmd == "watchdog":
        return watchdog(a[0], float(a[1]), a[2])
    if cmd == "unlock":      # release NAME.launchlock (an empty directory; os.rmdir refuses anything else)
        try:
            os.rmdir(os.path.join(HERE, f"{a[0]}.launchlock")); return 0
        except OSError:
            return 1
    if cmd == "may-create":
        return 0 if may_create(a[0], float(a[1])) else 1
    if cmd == "remaining":
        print(max(0, int(float(a[0]) - time.time()))); return 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
