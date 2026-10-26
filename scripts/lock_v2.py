"""Protocol v2: writer and checker (design 2, 7.3, 9.6; operations plan Task 6). --write builds experiments/protocol-v2.yaml
from the promoted inputs: the hashes of the manifest, parameters, promotion record, frozen cost decision, coverage, and
predictions; the decision's branch, markets, and cuts; kappa from kappa_effective (admitted only); the H4 commitment; the
recorded spend; the block, seed, market, and cap rules. --check re-derives every value from its file. --check-commit runs
in the evaluation checkout: a clean tree, a valid signed tag protocol-v2 at HEAD, only data and documents changed since
code_commit, and --check."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = "experiments/protocol-v2.yaml"
TAG = "protocol-v2"
FILES = {"manifest_sha256": "experiments/revision-v2-manifest.yaml", "params_sha256": "experiments/v2/params.json",
         "promotion_sha256": "experiments/v2/promotion.json", "decision_sha256": "experiments/v2/benchmark/decision.json",
         "coverage_sha256": "experiments/v2/coverage.json", "predictions_sha256": "docs/revision/predictions-v2.md"}
LEDGER = "docs/revision/budget-ledger.json"
ALLOWED = ("experiments/v2/", "docs/")
ALLOWED_FILES = (PROTOCOL, PROTOCOL + ".ots")
APPROVAL_LIMIT = 40.0


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _json(p: Path) -> dict:
    return json.loads(Path(p).read_text())


def _spent(repo: Path) -> float:
    p = Path(repo) / LEDGER
    return float(sum(float(r["usd"]) for r in _json(p).get("spent", []))) if p.exists() else 0.0


def _choices(dec: dict, cuts: int, branch: str, markets: list[str], approval: str | None) -> list[str]:
    out = []
    if (int(cuts), branch, list(markets)) != (dec.get("cuts"), dec.get("branch"), list(dec.get("markets") or [])):
        out.append(f"decision: cuts, branch, markets ({cuts}, {branch}, {markets}) differ from the frozen decision "
                   f"({dec.get('cuts')}, {dec.get('branch')}, {dec.get('markets')})")
    if float(dec.get("total_usd") or 0.0) > APPROVAL_LIMIT and not approval:
        out.append(f"approval: the decision's total {dec.get('total_usd')} USD is above {APPROVAL_LIMIT} and needs the author's written approval")
    return out


def build(repo, code_commit: str, cuts: int, h4: dict | None, approval: str | None, branch: str, markets: list) -> dict:
    repo = Path(repo); dec = _json(repo / FILES["decision_sha256"])["decision"]
    problems = _choices(dec, cuts, branch, markets, approval)
    if problems:
        raise SystemExit("; ".join(problems))
    cov = _json(repo / FILES["coverage_sha256"])
    p = {"version": 2, "code_commit": str(code_commit), **{k: _sha(repo / rel) for k, rel in FILES.items()}, "cuts": int(cuts), "branch": branch,
         "development_markets": list(markets), "h4": dict(h4) if h4 else None,
         "kappa": {f: (cov.get(f) or {}).get("kappa_effective") for f in ("Q1", "Q4")},
         "cost": {"development_usd": dec.get("development_usd"), "evaluation_usd": dec.get("evaluation_usd"), "total_usd": dec.get("total_usd"),
                  "spent_usd": _spent(repo)},
         "approval": approval, "block": {"rule": "H = A + 144", "depth": 6, "explorers": ["blockstream.info", "mempool.space"]},
         "seeds": {"eval_range": [30_000_000, 40_000_000], "per_market": 200}, "markets": ["headline"] + [f"fresh{i}" for i in range(6)],
         "caps": {"development": 12, "evaluation": 40}}
    bad = check(repo, p)
    if bad:
        raise SystemExit("; ".join(bad))
    return p


def check(repo, protocol: dict) -> list[str]:
    repo = Path(repo); out = []
    for k, rel in FILES.items():
        f = repo / rel
        if not f.exists() or _sha(f) != protocol.get(k):
            out.append(f"{rel}: missing or its hash differs from the protocol's {k}")
    if out:
        return out
    from scripts.promote_v2 import derive_params, verify_promoted
    v2 = repo / "experiments" / "v2"
    out += verify_promoted(v2)
    try:
        if _json(v2 / "params.json") != derive_params(v2):
            out.append("params.json does not follow from the promoted comparator and tuned files")
    except (OSError, KeyError, ValueError) as e:
        out.append(f"params.json cannot be derived from the promoted files: {e}")
    dec = _json(repo / FILES["decision_sha256"])["decision"]
    out += _choices(dec, protocol.get("cuts"), protocol.get("branch"), protocol.get("development_markets") or [], protocol.get("approval"))
    cov = _json(repo / FILES["coverage_sha256"])
    if protocol.get("kappa") != {f: (cov.get(f) or {}).get("kappa_effective") for f in ("Q1", "Q4")}:
        out.append("coverage: kappa differs from kappa_effective")
    if abs(float((protocol.get("cost") or {}).get("spent_usd", -1)) - _spent(repo)) > 1e-9:
        out.append("ledger: the recorded spend differs from the protocol's spent_usd")
    h4 = protocol.get("h4")
    if h4 is not None and not (re.fullmatch(r"[0-9a-f]{40}", str(h4.get("commit"))) and re.fullmatch(r"[0-9a-f]{64}", str(h4.get("bundle_sha256")))):
        out.append("h4: the commitment needs a 40-hex commit and a 64-hex bundle hash")
    if protocol.get("version") != 2 or not re.fullmatch(r"[0-9a-f]{40}", str(protocol.get("code_commit"))):
        out.append("protocol: version 2 and a 40-hex code_commit are required")
    return out


def _git(repo: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def check_commit(repo) -> None:
    repo = Path(repo)
    if _git(repo, "status", "--porcelain").stdout.strip():
        raise SystemExit("the tree is not clean")
    if _git(repo, "tag", "-v", TAG).returncode != 0:
        raise SystemExit(f"tag {TAG} is missing, unsigned, or its signature does not verify")
    head, tagged = _git(repo, "rev-parse", "HEAD").stdout.strip(), _git(repo, "rev-parse", f"{TAG}^{{commit}}").stdout.strip()
    if head != tagged:
        raise SystemExit(f"HEAD {head} is not the commit of {TAG} ({tagged})")
    protocol = yaml.safe_load((repo / PROTOCOL).read_text()); code = str(protocol["code_commit"])
    if _git(repo, "cat-file", "-e", f"{code}^{{commit}}").returncode != 0:
        raise SystemExit(f"code_commit {code} is not a commit in this checkout (shallow or foreign clone?)")
    if _git(repo, "merge-base", "--is-ancestor", code, "HEAD").returncode != 0:
        raise SystemExit(f"code_commit {code} is not an ancestor of HEAD")
    diff = _git(repo, "diff", "--name-only", code, "HEAD")
    if diff.returncode != 0:
        raise SystemExit(f"git diff {code} HEAD failed: {diff.stderr.strip()}")
    changed = [p for p in diff.stdout.split() if p]
    bad = [p for p in changed if not (p.startswith(ALLOWED) or p in ALLOWED_FILES)]
    if bad:
        raise SystemExit(f"files other than data and documents changed since code_commit: {bad}")
    problems = check(repo, protocol)
    if problems:
        raise SystemExit("; ".join(problems))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true"); g.add_argument("--check", action="store_true"); g.add_argument("--check-commit", dest="check_commit", action="store_true")
    ap.add_argument("--repo", default=str(ROOT)); ap.add_argument("--code-commit", dest="code_commit"); ap.add_argument("--cuts", type=int)
    ap.add_argument("--branch"); ap.add_argument("--markets"); ap.add_argument("--h4-commit", dest="h4_commit"); ap.add_argument("--h4-sha", dest="h4_sha")
    ap.add_argument("--no-h4", dest="no_h4", action="store_true"); ap.add_argument("--approval", default=None)
    a = ap.parse_args(argv); repo = Path(a.repo)
    if a.write:
        if a.no_h4 == bool(a.h4_commit or a.h4_sha):
            raise SystemExit("give --h4-commit and --h4-sha, or --no-h4")
        h4 = None if a.no_h4 else {"commit": a.h4_commit, "bundle_sha256": a.h4_sha}
        p = build(repo, a.code_commit, a.cuts, h4, a.approval, a.branch, a.markets.split(","))
        (repo / PROTOCOL).write_text(yaml.safe_dump(p, sort_keys=False))
        return 0
    if a.check:
        problems = check(repo, yaml.safe_load((repo / PROTOCOL).read_text()))
        print("\n".join(problems) or "ok")
        return 1 if problems else 0
    check_commit(repo)
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
