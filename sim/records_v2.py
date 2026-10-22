"""Stage records of the v2 runner: atomic JSON writes, tolerant reads (a missing or truncated file is absent), and
validation of a record's stage, provenance, and upstream hashes against the current files."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def write(path, rec: dict) -> None:
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(rec, f, default=float); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)


def read(path) -> dict | None:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def sha_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(job: dict, stage: str, rec: dict, upstream: dict) -> None:
    """`upstream` maps each upstream record id to its current path; raises ValueError on any mismatch."""
    if rec.get("stage") != stage:
        raise ValueError(f"record stage {rec.get('stage')!r} is not {stage!r}")
    if rec.get("provenance") != job.get("provenance"):
        raise ValueError("record provenance differs from the job's")
    for rid, sha in (rec.get("upstream") or {}).items():
        p = upstream.get(rid)
        if p is None or not Path(p).exists() or sha_file(p) != sha:
            raise ValueError(f"upstream {rid} changed or is missing")
