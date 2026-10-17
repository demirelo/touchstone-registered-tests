"""Amendment 2 (task A4): write the proposed rule's describe() record from its allow-listed module and parameter file,
print the rendered prose, and refuse a record that is not the registered one (audit_selection must be
`not expressible` for this rule, every other field in the locked vocabulary)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", default=str(ROOT / "experiments" / "proposed.yaml"))
    ap.add_argument("--out", default=str(ROOT / "experiments" / "proposed_describe.yaml"))
    a = ap.parse_args()
    os.environ["TOUCHSTONE_PROPOSED_PARAMS"] = str(Path(a.params).resolve())
    from sim.claimcheck import verify_describe_record
    from sim.describe import NOT_EXPRESSIBLE, describe_record, load_vocabulary, render
    from sim.registry import make_rule, proposed_params
    doc = proposed_params()
    if doc.get("rule") != "proposed" or "best_params" not in doc:
        raise SystemExit(f"{a.params}: not a tuning result of the proposed rule")
    rec = describe_record(make_rule("proposed", doc["best_params"]))
    if rec.get("audit_selection") != NOT_EXPRESSIBLE:
        raise SystemExit(f"the registered ruling requires audit_selection = {NOT_EXPRESSIBLE!r} for the proposed rule; the module reports {rec.get('audit_selection')!r}")
    problems = verify_describe_record(rec, make_rule("proposed", doc["best_params"]))
    if problems:
        raise SystemExit("describe record refused: " + "; ".join(map(str, problems)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(yaml.safe_dump(rec, sort_keys=False))
    sys.stdout.write(render(rec, load_vocabulary()))


if __name__ == "__main__":
    main()
