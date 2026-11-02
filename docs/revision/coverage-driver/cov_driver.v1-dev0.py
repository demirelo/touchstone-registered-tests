"""Orchestration driver for coverage pools (operations, 2026-11-02; not repository code). It calls the frozen
`sim.calibration_v2.build_pool` on small seed slices instead of one slice per worker: the frozen `build_market_pool`
keeps every episode record of a worker's slice in memory and exceeds a pod's RAM at 20,000 seeds. Episodes are
deterministic per seed, so the assembled pool equals the frozen one (checked on a small pool before use). The output file
is written exactly as `scripts/coverage_v2.py --pools` writes it."""
import argparse, json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, ".")
import scripts.coverage_v2 as CV          # noqa: E402
from sim import calibration_v2 as C       # noqa: E402
from sim.instances import coverage_pool   # noqa: E402


def part(args):
    mkt, attacks, refs, seeds, cred = args
    return C.build_pool(mkt, attacks, refs, seeds, cred)


def build(label, inputs, branch, M, workers, code_commit, chunk):
    cred = json.loads((Path(inputs) / "comparator.json").read_text())["cred"]
    attacks, refs = CV.fixture_inputs(Path(inputs), label); mkt = CV.RV.market(label, CV.RV.DEV_ROOT, 0.2, dev=True)
    seeds = list(coverage_pool(label, M))
    chunks = [seeds[i:i + chunk] for i in range(0, len(seeds), chunk)]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        parts = list(ex.map(part, [(mkt, attacks, refs, ch, cred) for ch in chunks], chunksize=1))
    pool = {"seeds": [s for p in parts for s in p["seeds"]],
            "normalized": {k: [v for p in parts for v in p["normalized"][k]] for k in parts[0]["normalized"]},
            "eff": {k: [v for p in parts for v in p["eff"][k]] for k in parts[0]["eff"]}}
    head = CV.RV.git_commit()
    if code_commit is not None and not CV.same_code(CV.REPO, code_commit, head):
        raise SystemExit(f"this checkout ({head}) is not the code commit {code_commit} or a data-only descendant: the pools are refused")
    return {**pool, "market": label, "branch": branch, "pool_size": int(M), "inputs_manifest": CV.inputs_manifest(inputs), "commit": head,
            "code_commit": code_commit or head}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", required=True); ap.add_argument("--branch", required=True); ap.add_argument("--inputs", required=True)
    ap.add_argument("--code-commit", dest="code_commit", required=True); ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--pool-size", dest="pool_size", type=int, default=None); ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    M = int(a.pool_size or C.BRANCHES[a.branch][1])
    pool = build(a.market, a.inputs, a.branch, M, a.workers, a.code_commit, a.chunk)
    out = Path(a.out); (out / "pools").mkdir(parents=True, exist_ok=True); (out / "pools" / f"{a.market}.json").write_text(json.dumps(pool))
