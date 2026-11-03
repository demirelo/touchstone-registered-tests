"""Per-cell means from the evaluation records, for the paper's descriptive statements that the frozen report does not
list per cell (single-family gains behind Q3-a, Q3-b, Q3-c; the X8-DB beneficiary behind Q3-e). Run only after
`report_v2.py --check` has passed on the same records (the report's verify stage refuses stale or foreign records);
each entry carries the record file's SHA-256. Means and nominal intervals use the report's own helpers."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def safe(rid: str) -> str:
    return rid.replace("|", "__").replace("/", "~").replace("*", "star")      # revision_v2._safe


def extract(out) -> dict:
    import numpy as np
    from scripts.report_v2 import _est, _interval
    cells = {}
    for f in sorted((Path(out) / "evaluate").glob("*.json")):
        rec = json.loads(f.read_text()); rid = rec.get("id")
        if not rid:
            continue
        e = {"sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
        if "gain" in rec:
            g = np.asarray(rec["gain"], dtype=float); e.update(gain=_est(g), gain_interval=_interval(g))
        if "eff_attack" in rec:
            e["eff_attack"] = _est(np.asarray(rec["eff_attack"], dtype=float))
        if "member_gain" in rec:
            e["member_gain"] = [float(np.mean(m)) for m in rec["member_gain"]]
        cells[rid] = e
    return cells


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--write", required=True)
    a = ap.parse_args(argv)
    Path(a.write).write_text(json.dumps(extract(a.out), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
