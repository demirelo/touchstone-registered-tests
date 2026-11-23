"""Post-analysis extract for the paper (not part of the stamped manifest): R3's audit counts per winner set, rate and
market, exactly as the committed collector (rep_collect.collect) builds them for expectation 5, and the list of cells
that received continued search, read from the run's continuation directory. Usage:
replication_extract.py --out <followup3-rep dir> --manifest <manifest> --draw <draw.json> --write <json>"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def continued_cells(out: Path) -> list:
    """File stems of the continued cells (one record per flagged cell); the gate and diagnostics folders are excluded."""
    return sorted(p.stem for p in (out / "continuation").glob("*.json"))


def parse_cell(stem: str) -> dict:
    """'menu-p0.05__fresh3@rho0.2__F111__D2+H3__profit__churn0.05' -> kind, rate, market index, policy."""
    parts = stem.split("__")
    kind, rate = parts[0].split("-p")
    return {"kind": kind, "rate": rate, "market": "rep" + parts[1].split("@")[0].removeprefix("fresh"), "policy": parts[2]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--manifest", required=True); ap.add_argument("--draw", required=True)
    ap.add_argument("--write", required=True)
    a = ap.parse_args(argv)
    import rep_v2 as V
    import rep_collect as C
    ns = V.main.__globals__["argparse"].Namespace(out=a.out, manifest=a.manifest, draw=a.draw, smoke=False,
                                                  params=str(V.ROOT / "experiments/v2/params.json"))
    V._require(ns)
    c = V._context(ns); jobs = V._jobs_by_dir(c, False)
    col = C.collect(Path(a.out), jobs, gate=V.gate_item(jobs, a.out), smoke=False)
    cells = continued_cells(Path(a.out))
    res = {"audit": {s: {rk: {m: list(v) for m, v in sorted(ms.items())} for rk, ms in sorted(col["audit"][s].items())}
                     for s in ("frozen", "primary")},
           "counts": col["counts"], "continued": [dict(parse_cell(s), stem=s) for s in cells]}
    Path(a.write).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
