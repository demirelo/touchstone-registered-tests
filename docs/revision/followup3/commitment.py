"""Commitment manifest and run-time freeze check of the churn replication (replication-plan.md, section 5).
build(): deterministic manifest bytes (sorted JSON) with the frozen code's git commit and the SHA-256 of every listed
file; these bytes are what is stamped and what block_draw.py and the instance wrapper read as --protocol.
frozen_problems(): sim/, scripts/ and the frozen configuration inputs equal the commit (no change, no untracked file)
  and no outside override is set.
verify() / require(): every required file is listed and every listed file still matches its hash; require() stops the
  run on any problem. build() refuses a file list without a required file or without a file of the drivers' import
  closure (imports inside functions included, review rep-impl-r1).
Usage: commitment.py build <out> <commit> <file>...   |   commitment.py check <manifest>"""
import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

FROZEN = ("sim", "scripts")
# Files outside sim/ and scripts/ that the frozen code reads (plan section 5: "the frozen configuration inputs").
FROZEN_INPUTS = ("experiments/locked.yaml", "experiments/revision-v2-manifest.yaml", "experiments/calibration.json",
                 "experiments/v2/params.json", "experiments/v2/benchmark/timings.json")
F3, CH, F2, F1 = "docs/revision/followup3", "docs/revision/churn", "docs/revision/followup2", "docs/revision/followup"
# Plan section 5: this plan, the analysis and its tests, the drivers and adapters, every imported helper outside sim/
# and scripts/ (test_the_real_required_set_covers_the_drivers_import_closure keeps this complete), the parameter files
# and uv.lock; also the launcher and its harness, the cost schedule and the frozen configuration inputs.
REQUIRED = tuple(sorted({
    f"{F3}/replication-plan.md", f"{F3}/replication_analysis.py", f"{F3}/test_replication_analysis.py",
    f"{F3}/commitment.py", f"{F3}/test_commitment.py", f"{F3}/continuation.py", f"{F3}/test_continuation.py",
    f"{F3}/rep_v2.py", f"{F3}/test_rep_v2.py", f"{F3}/rep_collect.py", f"{F3}/test_rep_collect.py",
    f"{F3}/rep_pod.sh", f"{F3}/test_rep_pod_harness.sh", f"{F3}/cost_estimate.py",
    f"{CH}/churn_v2.py", f"{F1}/reset_followup_v2.py", f"{F2}/common.py", f"{F2}/convergence_v2.py", f"{F2}/guards.py",
    f"{F2}/runnerup_v2.py", "uv.lock", *FROZEN_INPUTS,
    # Review rep-impl-r2: the preflight task that churn_v2 runs as a subprocess, and the runner-up recheck record that
    # runnerup_v2.runner_up_cred reads (the C-thr(12) parameters).
    f"{CH}/churn_memory.py",
    'experiments/v2/log/Cstar__{"L":10,"cred":{"K":12,"M":null,"variant":"thr"},"tol":0.16}__recheck.json'}))
# Environment variables the frozen code reads; the driver sets TOUCHSTONE_IDENTITY_SALT itself (checked against the draw).
OVERRIDES = ("TOUCHSTONE_LOCKED", "TOUCHSTONE_PROPOSED_MODULE", "TOUCHSTONE_PROPOSED_PARAMS", "TOUCHSTONE_SEALED_DIR",
             "TOUCHSTONE_GIT_COMMIT")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def search_dirs(root) -> list:
    """The drivers' import path outside the standard library (rep_v2.py, rep_collect.py): their own folders and the repo."""
    root = Path(root)
    return [root / F3, root / CH, root / F2, root / F1, root, root / "scripts"]


def _imports(path: Path) -> set:
    """Module names imported by the file, plus the stems of scripts it names as string literals ending in .py (a script
    run as a subprocess, review rep-impl-r2)."""
    names = set()
    for n in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value.endswith(".py") and "/" not in n.value \
                and n.value[:-3].isidentifier():
            names.add(n.value[:-3])
        elif isinstance(n, ast.Import):
            names |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            names.add(n.module.split(".")[0])
    return names


def import_closure(root, start, search) -> set:
    """Every repo file outside sim/, scripts/ and the virtual environment reachable by imports (at any depth, inside
    functions too) from the start files, resolved along `search` as the drivers' sys.path does; paths relative to root."""
    root = Path(root).resolve(); seen, todo = set(), [root / f for f in start]
    while todo:
        p = todo.pop().resolve(); rel = str(p.relative_to(root))
        if rel in seen:
            continue
        seen.add(rel)
        for name in _imports(p):
            for d in [p.parent, *map(Path, search)]:
                q = (Path(d) / f"{name}.py").resolve()
                if q.is_file():
                    r = q.relative_to(root).parts
                    if r[0] not in (*FROZEN, ".venv"):
                        todo.append(q)
                    break
    return seen


def build(root, files, commit: str, required=None, search=None) -> bytes:
    root = Path(root); files = sorted(set(files))
    need = set(REQUIRED if required is None else required)
    py = [f for f in files if f.endswith(".py")]
    need |= import_closure(root, py, search_dirs(root) if search is None else search)
    if missing := sorted(need - set(files)):
        raise SystemExit(f"manifest refused: required or imported files not listed: {missing}")
    body = {"commit": commit, "files": {f: _sha(root / f) for f in sorted(set(files))},
            "note": "churn replication commitment; docs/revision/followup3/replication-plan.md"}
    return (json.dumps(body, indent=1, sort_keys=True) + "\n").encode()


def verify(root, manifest, required=None) -> list:
    root = Path(root); m = json.loads(Path(manifest).read_text())
    out = [f"{f}: required but not listed" for f in (REQUIRED if required is None else required) if f not in m["files"]]
    for f, h in m["files"].items():
        p = root / f
        if not p.exists():
            out.append(f"{f}: missing")
        elif _sha(p) != h:
            out.append(f"{f}: hash differs from the manifest")
    return out


def _git(root, *a) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True)


def frozen_problems(root, commit: str) -> list:
    """A git error (an unknown commit included) is a problem, never an empty difference (review rep-impl-r2)."""
    if _git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
        return [f"git: commit {commit} not found"]
    out = []
    paths = [*FROZEN, *[f for f in FROZEN_INPUTS if (Path(root) / f).exists() or _git(root, "cat-file", "-e", f"{commit}:{f}").returncode == 0]]
    d = _git(root, "diff", "--name-only", commit, "--", *paths)
    if d.returncode != 0:
        return [f"git diff failed: {d.stderr.strip()[:200]}"]
    changed = d.stdout.split()
    if changed:
        out.append(f"differ from commit {commit}: {', '.join(changed[:5])}")
    u = _git(root, "ls-files", "--others", "--exclude-standard", "--", *paths)
    if u.returncode != 0:
        return [f"git ls-files failed: {u.stderr.strip()[:200]}"]
    untracked = u.stdout.split()
    if untracked:
        out.append(f"untracked files under {', '.join(FROZEN)}: {', '.join(untracked[:5])}")
    out += [f"environment override set: {v}" for v in OVERRIDES if os.environ.get(v)]
    return out


def require(root, manifest, required=None) -> None:
    m = json.loads(Path(manifest).read_text())
    bad = frozen_problems(root, m["commit"]) + verify(root, manifest, required)
    if bad:
        raise SystemExit("commitment check failed:\n" + "\n".join(bad))


def main(argv) -> int:
    root = Path(_git(".", "rev-parse", "--show-toplevel").stdout.strip())
    if argv[0] == "build":
        Path(argv[1]).write_bytes(build(root, argv[3:], argv[2])); print("manifest written"); return 0
    require(root, argv[1]); print("commitment ok"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
