"""The follow-up budget category of the reset experiment (docs/revision/reset-experiment-plan.md, draft 4, section 7).

scripts/budget_v2.py is frozen (code freeze 627a2de) and has no way to add a category, so this module adds one under the
same lock and validation: the author's written approval sets the program limit and the new `followup` cap together.
Reservations and spend then go through budget_v2.reserve and budget_v2.record unchanged."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts import budget_v2 as BV  # noqa: E402

OP = "followup"
Refused = BV.Refused


def approve(path, new_limit: float, cap: float, text: str) -> None:
    new_limit = BV._amount(new_limit, "approval limit", positive=True); cap = BV._amount(cap, f"cap {OP}", positive=True)
    if not str(text).strip():
        raise Refused("an approval needs the author's written text")
    if not Path(path).exists():
        raise Refused(f"no ledger at {path}")
    with BV._locked(path) as d:
        if OP in d["caps"]:
            raise Refused(f"the {OP} category already has a cap of {d['caps'][OP]} USD")
        if new_limit + 1e-9 < BV._used(d) + cap:
            raise Refused(f"the limit {new_limit} is below the spend and reservations ({BV._used(d):.3f}) plus the new cap {cap}")
        if d.get("approval"):
            d.setdefault("approval_history", []).append(d["approval"])
        d["caps"][OP] = cap
        d["approval"] = {"limit": new_limit, "text": str(text)}


def reserve(path, tag: str, estimate: float) -> float:
    with BV._locked(path) as d:
        if OP not in d["caps"]:
            raise Refused(f"no cap for {OP!r}: record the author's approval first (--approve LIMIT CAP TEXT)")
    return BV.reserve(path, OP, tag, estimate)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--ledger", default=str(BV.DEFAULT))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--approve", nargs=3, metavar=("LIMIT", "CAP", "TEXT")); g.add_argument("--reserve", nargs=2, metavar=("TAG", "ESTIMATE"))
    a = ap.parse_args(argv)
    try:
        if a.approve:
            approve(a.ledger, float(a.approve[0]), float(a.approve[1]), a.approve[2])
        else:
            print(f"{reserve(a.ledger, a.reserve[0], float(a.reserve[1])):.2f}")
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
