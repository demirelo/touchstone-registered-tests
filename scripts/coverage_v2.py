"""Coverage check and calibration of protocol v2 (design 9.5). --pools builds the aligned 14-profile pools on each
coverage market from the tuning outputs (frozen development attacks at the fixed pair and development references);
--select chooses kappa per confirmatory family on selection replications; --validate admits it on independent
replications. Everything is written under --out (pools/<market>.json, coverage.json). --pools --market M --workers N
builds one market's pool on N processes (seed chunks, concatenated in seed order; each pool records its branch, size, and
the manifest of the tuning inputs it was built from). --select and --validate read every pool of --branch, refuse a pool
of another branch or with other inputs, and record what they read; kappa_effective is the selected kappa only when
validation admitted it (operations plan Task 3)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import revision_v2 as RV  # noqa: E402
from sim import calibration_v2 as C  # noqa: E402
from sim.instances import coverage_pool  # noqa: E402

FIXED = {"tol": 0.16, "L": 10}
REGISTERED = {"selection": 10_000, "validation": 20_000, "resamples": 9999}
SOURCE = {"F000": "B3-t", "F111": "R3-t"}


def fixture_inputs(inputs: Path, label: str) -> tuple[dict, dict]:
    """Attacks and references of the three fixture rules (F000, F111, C*) on one market, from the tuning logs (inner searches
    at the fixed pair) and the comparator selection (design draft 7, 9.5)."""
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
    missing = sorted((set(SOURCE) | {"C*"}) - set(refs))
    if missing:
        raise SystemExit(f"{label}: no tuning log for {missing}")
    return attacks, refs


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs_manifest(inputs: Path) -> dict:
    """SHA-256 of the tuning files a pool is built from, keyed by their path under --inputs."""
    d = Path(inputs); files = [d / "comparator.json", *sorted((d / "log").glob("*.json"))]
    return {f.relative_to(d).as_posix(): _sha(f) for f in files if f.exists()}


def _map(fn, items: list[tuple], workers: int) -> list:
    if workers <= 1 or len(items) <= 1:
        return [fn(*it) for it in items]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, *zip(*items)))


def build_market_pool(label: str, inputs: Path, branch: str, M: int, workers: int) -> dict:
    cred = json.loads((Path(inputs) / "comparator.json").read_text())["cred"]
    attacks, refs = fixture_inputs(Path(inputs), label); mkt = RV.market(label, RV.DEV_ROOT, 0.2, dev=True)
    seeds = list(coverage_pool(label, M)); k = max(1, min(int(workers), len(seeds)))
    chunks = [seeds[i * len(seeds) // k:(i + 1) * len(seeds) // k] for i in range(k)]
    parts = _map(C.build_pool, [(mkt, attacks, refs, ch, cred) for ch in chunks if ch], k)
    pool = {"seeds": [s for p in parts for s in p["seeds"]],
            "normalized": {key: [v for p in parts for v in p["normalized"][key]] for key in parts[0]["normalized"]},
            "eff": {key: [v for p in parts for v in p["eff"][key]] for key in parts[0]["eff"]}}
    return {**pool, "market": label, "branch": branch, "pool_size": int(M), "inputs_manifest": inputs_manifest(inputs), "commit": RV.git_commit()}


def read_pools(out: Path, branch: str, commit: str | None = None) -> dict:
    """Every pool of the branch, built by this code (`commit`), for its own market and branch, from the same tuning inputs."""
    markets = C.BRANCHES[branch][0]; pools = {}; commit = commit or RV.git_commit()
    for m in markets:
        p = Path(out) / "pools" / f"{m}.json"
        if not p.exists():
            raise SystemExit(f"branch {branch} needs the pool of {m}")
        pools[m] = json.loads(p.read_text())
        if pools[m].get("branch") != branch:
            raise SystemExit(f"pool {m} was built for branch {pools[m].get('branch')!r}, not {branch!r}")
        if pools[m].get("market") not in (None, m) or pools[m].get("commit") != commit:
            raise SystemExit(f"pool {m} was built by commit {pools[m].get('commit')!r} for market {pools[m].get('market')!r}, not by {commit!r}")
    if len({json.dumps(pl.get("inputs_manifest"), sort_keys=True) for pl in pools.values()}) != 1:
        raise SystemExit("the pools were built from different tuning inputs")
    return pools


def fixtures(out: Path, branch: str, M: int | None, pools: dict | None = None) -> dict:
    markets = C.BRANCHES[branch][0]
    pools = pools or {m: json.loads((Path(out) / "pools" / f"{m}.json").read_text()) for m in markets}
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
    ap.add_argument("--inputs", default=None); ap.add_argument("--workers", type=int, default=1); ap.add_argument("--market", default=None)
    ap.add_argument("--replications", type=int, default=None); ap.add_argument("--resamples", type=int, default=9999)
    ap.add_argument("--pool-size", dest="pool_size", type=int, default=None); ap.add_argument("--seed", type=int, default=20261022)
    a = ap.parse_args(argv)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); cov_path = out / "coverage.json"
    if a.pools:
        if not a.inputs:
            raise SystemExit("--pools needs --inputs (the promoted tuning outputs)")
        markets, M, _ = C.BRANCHES[a.branch]; M = a.pool_size or M
        for m in ([a.market] if a.market else markets):
            if m not in markets:
                raise SystemExit(f"{m} is not a market of branch {a.branch}")
            pool = build_market_pool(m, Path(a.inputs), a.branch, M, a.workers)
            (out / "pools").mkdir(exist_ok=True); (out / "pools" / f"{m}.json").write_text(json.dumps(pool))
        return 0
    pools = read_pools(out, a.branch); sizes = {pl.get("pool_size") for pl in pools.values()}
    if len(sizes) != 1 or (a.pool_size and a.pool_size not in sizes):
        raise SystemExit(f"pool sizes {sorted(sizes)} disagree with each other or with --pool-size")
    M = sizes.pop()
    fx = fixtures(out, a.branch, M, pools)
    cov = json.loads(cov_path.read_text()) if cov_path.exists() else {}
    if cov.get("branch") not in (None, a.branch):
        raise SystemExit(f"coverage.json is for branch {cov.get('branch')!r}")
    shas = {m: _sha(out / "pools" / f"{m}.json") for m in pools}
    if a.select:
        cov["selected_pools"] = shas
    elif cov.get("selected_pools") != shas:
        raise SystemExit("the pools differ from the pools selected on: validate reads the same pool bytes as select")
    for fam in ("Q1", "Q4"):
        if a.select:
            reps = a.replications or REGISTERED["selection"]
            kp = C.select_kappa(fam, fx[fam], a.branch, a.seed, reps, a.resamples)
            cov[fam] = {"kappa": kp, "branch": a.branch, "selection_replications": reps, "resamples": a.resamples, "kappa_effective": None}
        else:
            reps = a.replications or REGISTERED["validation"]; kp = cov.get(fam, {}).get("kappa")
            cov.setdefault(fam, {})["validation"] = None if kp is None else C.validate(fam, kp, fx[fam], a.branch, a.seed, reps, a.resamples)
            cov[fam]["admitted"] = bool(cov[fam]["validation"] and cov[fam]["validation"]["admitted"])
            cov[fam].update(validation_replications=reps, resamples=a.resamples, kappa_effective=kp if cov[fam]["admitted"] else None)
    reg = C.BRANCHES[a.branch][1]
    cov.update(branch=a.branch, markets=list(C.BRANCHES[a.branch][0]), pool_size=int(M), commit=RV.git_commit(),
               inputs_manifest=next(iter(pools.values())).get("inputs_manifest"),
               pools={m: {"sha256": _sha(out / "pools" / f"{m}.json"), "seeds": len(pl["seeds"]),
                          "profile_lengths": sorted({len(v) for v in pl["normalized"].values()} | {len(v) for v in pl["eff"].values()})}
                      for m, pl in pools.items()})
    small = any(cov.get(f, {}).get("selection_replications", REGISTERED["selection"]) < REGISTERED["selection"]
                or cov.get(f, {}).get("validation_replications", REGISTERED["validation"]) < REGISTERED["validation"]
                or cov.get(f, {}).get("resamples", REGISTERED["resamples"]) < REGISTERED["resamples"] for f in ("Q1", "Q4"))
    cov["smoke"] = bool(small or int(M) != int(reg))
    cov_path.write_text(json.dumps(cov, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
