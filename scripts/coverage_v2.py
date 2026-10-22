"""Coverage check and calibration of protocol v2 (design 9.5). --pools builds the aligned 14-profile pools on each
coverage market from the tuning outputs (frozen development attacks at the fixed pair and development references);
--select chooses kappa per confirmatory family on selection replications; --validate admits it on independent
replications. Everything is written under --out (pools/<market>.json, coverage.json)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from sim import calibration_v2 as C  # noqa: E402
from sim.instances import coverage_pool  # noqa: E402

FIXED = {"tol": 0.16, "L": 10}
SOURCE = {"F000": "B3-t", "F111": "R3-t", "R4": "R4-t"}


def fixture_inputs(inputs: Path, label: str) -> tuple[dict, dict]:
    """Attacks and references of the five fixture rules on one market, from the tuning logs (inner searches at the fixed
    pair), the comparator selection, and the C*/S2 fixture searches."""
    inputs = Path(inputs); cred = json.loads((inputs / "comparator.json").read_text())["cred"]
    want = {**{rule: (src, dict(FIXED)) for rule, src in SOURCE.items()}, "C*": ("C*", {**FIXED, "cred": cred})}
    attacks, refs = {}, {}
    for f in sorted((inputs / "log").glob("*.json")):
        d = json.loads(f.read_text())
        if d.get("recheck") or label not in d.get("detail", {}):
            continue
        for rule, (src, spec) in want.items():
            if d["rule"] == src and d["spec"] == spec and rule not in refs:
                det = d["detail"][label]; refs[rule] = det["reference"]
                for fam in (("D2+H3",) if rule == "F000" else ("D2+H3", "X7-SC")):
                    attacks[(rule, fam)] = det[fam]["attack"]
    fx = json.loads((inputs / "fixture_cstar_s2.json").read_text())["markets"][label]
    refs["C*/S2"] = fx["reference"]
    for fam in ("D2+H3", "X7-SC"):
        attacks[("C*/S2", fam)] = fx["attacks"][fam]
    missing = sorted((set(SOURCE) | {"C*"}) - set(refs))
    if missing:
        raise SystemExit(f"{label}: no tuning log for {missing}")
    return attacks, refs


def fixtures(out: Path, branch: str, M: int | None) -> dict:
    markets = C.BRANCHES[branch][0]
    pools = {m: json.loads((Path(out) / "pools" / f"{m}.json").read_text()) for m in markets}
    idx = {m: list(range(len(pools[m]["seeds"]))) for m in markets}
    blocks = C.strata(idx, branch, M)
    per_market_blocks = len(blocks) // len(markets)
    q1 = [{s: v[np.asarray(blk)] for s, v in C.q1_stats(pools[markets[b // per_market_blocks]]).items()} for b, blk in enumerate(blocks)]
    M = int(M or C.BRANCHES[branch][1])
    q4 = {m: {s: v[:M] for s, v in C.q4_stats(pools[m]).items()} for m in markets}
    return {"Q1": {"pooled": q1}, "Q4": q4}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pools", action="store_true"); g.add_argument("--select", action="store_true"); g.add_argument("--validate", action="store_true")
    ap.add_argument("--branch", default="three20k", choices=sorted(C.BRANCHES)); ap.add_argument("--out", required=True)
    ap.add_argument("--inputs", default=None); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--replications", type=int, default=None); ap.add_argument("--resamples", type=int, default=9999)
    ap.add_argument("--pool-size", dest="pool_size", type=int, default=None); ap.add_argument("--seed", type=int, default=20261022)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); cov_path = out / "coverage.json"
    if a.pools:
        if not a.inputs:
            raise SystemExit("--pools needs --inputs (the promoted tuning outputs)")
        cred = json.loads((Path(a.inputs) / "comparator.json").read_text())["cred"]
        markets, M, _ = C.BRANCHES[a.branch]; M = a.pool_size or M
        for m in markets:
            attacks, refs = fixture_inputs(Path(a.inputs), m)
            mkt = RV.market(m, RV.DEV_ROOT, 0.2, dev=True)
            pool = C.build_pool(mkt, attacks, refs, coverage_pool(m, M), cred)
            (out / "pools").mkdir(exist_ok=True); (out / "pools" / f"{m}.json").write_text(json.dumps(pool))
        return 0
    fx = fixtures(out, a.branch, a.pool_size)
    cov = json.loads(cov_path.read_text()) if cov_path.exists() else {}
    for fam in ("Q1", "Q4"):
        if a.select:
            kp = C.select_kappa(fam, fx[fam], a.branch, a.seed, a.replications or 10_000, a.resamples)
            cov[fam] = {"kappa": kp, "branch": a.branch, "selection_replications": a.replications or 10_000}
        else:
            kp = cov.get(fam, {}).get("kappa")
            cov.setdefault(fam, {})["validation"] = None if kp is None else C.validate(fam, kp, fx[fam], a.branch, a.seed, a.replications or 20_000, a.resamples)
            cov[fam]["admitted"] = bool(cov[fam]["validation"] and cov[fam]["validation"]["admitted"])
    cov_path.write_text(json.dumps(cov, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
