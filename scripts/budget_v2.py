"""The budget ledger of the paid operations (design 8.2; operations plan Task 4). A pod's USD cap is reserved before its
launch: the grant is min(estimate x 1.25, phase cap - spent - outstanding), refused when it is below the estimate or when
the spend plus outstanding reservations of both phases would pass the approval limit (40 USD, or the higher limit of a
written approval). The actual spend replaces the reservation when the pod is pulled. Every update holds an exclusive lock
on <ledger>.lock across its read and write, so concurrent launches cannot oversubscribe a cap."""
from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import sys
from contextlib import contextmanager
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "docs" / "revision" / "budget-ledger.json"
DECISION_H4 = Path(__file__).resolve().parents[1] / "experiments" / "v2" / "benchmark" / "decision-h4.json"
CAPS = {"development": 12.0, "evaluation": 40.0}
APPROVAL_LIMIT = 40.0
HEADROOM = 1.25


class Refused(Exception):
    pass


def _amount(x, what: str, positive: bool = False) -> float:
    """A finite, nonnegative amount (positive when required); anything else would disable the cap comparisons."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise Refused(f"{what} {x!r} is not a number")
    if not math.isfinite(v) or v < 0 or (positive and v <= 0):
        raise Refused(f"{what} {x!r} must be finite and {'positive' if positive else 'nonnegative'}")
    return v


def _valid(d: dict) -> dict:
    for op, cap in d.get("caps", {}).items():
        _amount(cap, f"cap {op}", positive=True)
    for r in d.get("spent", []):
        _amount(r.get("usd"), f"spend {r.get('tag')}")
    for r in d.get("reservations", []):
        _amount(r.get("cap"), f"reservation {r.get('tag')}")
    if d.get("approval"):
        _amount(d["approval"].get("limit"), "approval limit", positive=True)
        if not (isinstance(d["approval"].get("text"), str) and d["approval"]["text"].strip()):
            raise Refused("the saved approval has no written text")
    return d


def _after_read() -> None:
    """Called between the ledger read and write of an update; a test replaces it to widen the race window."""


@contextmanager
def _locked(path: Path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{path}.lock", "a") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        try:
            d = _valid(json.loads(path.read_text()) if path.exists() else {"caps": dict(CAPS), "reservations": [], "spent": [], "approval": None})
            _after_read()
            yield d
            tmp = Path(f"{path}.{os.getpid()}.tmp"); tmp.write_text(json.dumps(d, indent=1)); os.replace(tmp, path)
        finally:
            fcntl.flock(lk, fcntl.LOCK_UN)


def _used(d: dict, op: str | None = None) -> float:
    pick = lambda rows: sum(float(r.get("usd", r.get("cap", 0.0))) for r in rows if op is None or r["op"] == op)
    return pick(d["spent"]) + pick(d["reservations"])


def limit(d: dict) -> float:
    return float((d.get("approval") or {}).get("limit", APPROVAL_LIMIT))


def _gate(d: dict, op: str, decision_h4) -> None:
    """Design draft 7, 5.3 and 8.2: once the decision after the H4 timing exists, no development reservation (any tag)
    while it stops, or while its total needs an approval that the ledger's limit does not cover."""
    p = Path(decision_h4) if decision_h4 is not None else None
    if op != "development" or p is None or not p.exists():
        return
    dec = json.loads(p.read_text())["decision"]
    if dec.get("stop"):
        raise Refused(f"the decision after the H4 timing stops at {dec['stop']!r}: no further development reservation")
    if dec.get("approval_required") and limit(d) + 1e-9 < float(dec.get("total_usd") or 0.0):
        raise Refused(f"the decision after the H4 timing totals {dec.get('total_usd')} USD; record the author's approval with --approve first")


def reserve(path, op: str, tag: str, estimate: float, decision_h4=DECISION_H4) -> float:
    estimate = _amount(estimate, "estimate", positive=True)
    with _locked(path) as d:
        _gate(d, op, decision_h4)
        if any(r["tag"] == tag for r in d["reservations"] + d["spent"]):
            raise Refused(f"tag {tag!r} is already in the ledger")
        grant = min(float(estimate) * HEADROOM, float(d["caps"][op]) - _used(d, op))
        if grant < float(estimate):
            raise Refused(f"{op}: {grant:.2f} USD left under the cap, below the estimate {float(estimate):.2f}")
        if _used(d) + grant > limit(d) + 1e-9:
            raise Refused(f"the combined spend and reservations would reach {_used(d) + grant:.2f} USD, above the approved {limit(d):.2f}")
        d["reservations"].append({"op": op, "tag": tag, "cap": round(grant, 6)})
        return grant


def record(path, tag: str, usd: float) -> None:
    usd = _amount(usd, "spend")
    with _locked(path) as d:
        r = next((r for r in d["reservations"] if r["tag"] == tag), None)
        if r is None:
            raise Refused(f"no reservation {tag!r}")
        d["reservations"].remove(r); d["spent"].append({"op": r["op"], "tag": tag, "usd": float(usd)})


def approve(path, new_limit: float, text: str) -> None:
    new_limit = _amount(new_limit, "approval limit", positive=True)
    if not str(text).strip():
        raise Refused("an approval needs the author's written text")
    with _locked(path) as d:
        d["approval"] = {"limit": float(new_limit), "text": str(text)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=str(DEFAULT))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--reserve", nargs=3, metavar=("OP", "TAG", "ESTIMATE")); g.add_argument("--record", nargs=2, metavar=("TAG", "USD"))
    g.add_argument("--approve", nargs=2, metavar=("LIMIT", "TEXT")); g.add_argument("--show", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.reserve:
            print(f"{reserve(a.ledger, a.reserve[0], a.reserve[1], float(a.reserve[2])):.2f}")
        elif a.record:
            record(a.ledger, a.record[0], float(a.record[1]))
        elif a.approve:
            approve(a.ledger, float(a.approve[0]), a.approve[1])
        else:
            print(Path(a.ledger).read_text())
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
