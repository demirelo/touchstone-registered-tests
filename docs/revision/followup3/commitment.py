"""Commitment manifest and run-time freeze check of the churn replication (replication-plan.md, section 5).
build(): deterministic manifest bytes (sorted JSON) with the frozen code's git commit and the SHA-256 of every listed
file; these bytes are what is stamped and what block_draw.py and the instance wrapper read as --protocol.
frozen_problems(): sim/ and scripts/ equal the commit (no change, no untracked file) and no outside override is set.
verify() / require(): every listed file still matches its hash; require() stops the run on any problem.
Usage: commitment.py build <out> <commit> <file>...   |   commitment.py check <manifest>"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

FROZEN = ("sim", "scripts")
# Environment variables the frozen code reads; the driver sets TOUCHSTONE_IDENTITY_SALT itself (checked against the draw).
OVERRIDES = ("TOUCHSTONE_LOCKED", "TOUCHSTONE_PROPOSED_MODULE", "TOUCHSTONE_PROPOSED_PARAMS", "TOUCHSTONE_SEALED_DIR",
             "TOUCHSTONE_GIT_COMMIT")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(root, files, commit: str) -> bytes:
    root = Path(root)
    body = {"commit": commit, "files": {f: _sha(root / f) for f in sorted(set(files))},
            "note": "churn replication commitment; docs/revision/followup3/replication-plan.md"}
    return (json.dumps(body, indent=1, sort_keys=True) + "\n").encode()


def verify(root, manifest) -> list:
    root = Path(root); m = json.loads(Path(manifest).read_text())
    out = []
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
    out = []
    if _git(root, "diff", "--quiet", commit, "--", *FROZEN).returncode != 0:
        out.append(f"{', '.join(FROZEN)} differ from commit {commit}")
    untracked = _git(root, "ls-files", "--others", "--exclude-standard", "--", *FROZEN).stdout.split()
    if untracked:
        out.append(f"untracked files under {', '.join(FROZEN)}: {', '.join(untracked[:5])}")
    out += [f"environment override set: {v}" for v in OVERRIDES if os.environ.get(v)]
    return out


def require(root, manifest) -> None:
    m = json.loads(Path(manifest).read_text())
    bad = frozen_problems(root, m["commit"]) + verify(root, manifest)
    if bad:
        raise SystemExit("commitment check failed:\n" + "\n".join(bad))


def main(argv) -> int:
    root = Path(_git(".", "rev-parse", "--show-toplevel").stdout.strip())
    if argv[0] == "build":
        Path(argv[1]).write_bytes(build(root, argv[3:], argv[2])); print("manifest written"); return 0
    require(root, argv[1]); print("commitment ok"); return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
