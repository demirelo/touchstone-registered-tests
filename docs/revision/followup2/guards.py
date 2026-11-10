"""Shared guards of the follow-up runs in docs/revision/followup2 (internal review round 1 of both plans): pinned search
settings, budgets checked against the frozen records, saved results reused only under the same binding, a
driver-specific inventory, a cost stop between stages (never a kill), and saved reproduction evidence."""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE.parent / "followup"))

import reset_followup_v2 as F  # noqa: E402
from sim.records_v2 import read, sha_file, write  # noqa: E402

PINNED = ("experiments/locked.yaml", "experiments/revision-v2-manifest.yaml")


def _refuse(msg: str):
    raise SystemExit(f"follow-up refused: {msg}")


def pin_settings() -> None:
    """The locked search settings and the manifest are those of protocol-v2, with no TOUCHSTONE_LOCKED override."""
    if os.environ.get("TOUCHSTONE_LOCKED"):
        _refuse("TOUCHSTONE_LOCKED is set; the locked settings must be the registered file")
    r = subprocess.run(["git", "diff", "--quiet", "protocol-v2", "--", *PINNED], cwd=ROOT)
    if r.returncode != 0:
        _refuse(f"{PINNED} differ from protocol-v2 (or the tag is missing)")


def check_budget(job: dict, frozen_record) -> None:
    rec = read(frozen_record)
    if rec is None or list(rec["provenance"]["budget"]) != list(job["budget"]):
        _refuse(f"{job['id']}: search budget {job['budget']} is not the frozen record's {None if rec is None else rec['provenance']['budget']}")


def binding(inputs_sha: str, provenance: dict, smoke: bool, settings: dict, driver_sha: str) -> dict:
    b = {"inputs_sha": inputs_sha, "provenance": provenance, "smoke": bool(smoke), "settings": settings, "driver_sha": driver_sha}
    return json.loads(json.dumps(b, default=float))              # the form it has when read back (tuples become lists)


def reusable(path, b: dict) -> bool:
    """False if nothing is saved; True if the saved result has this exact binding; refused otherwise (never overwritten)."""
    rec = read(path)
    if rec is None:
        return False
    if rec.get("binding") != b:
        _refuse(f"{path}: a saved result with another binding exists")
    return True


def finite(*xs) -> bool:
    def vals(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from vals(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                yield from vals(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            yield x
    return all(math.isfinite(v) for x in xs for v in vals(x))


def environment() -> dict:
    env = dict(F.environment()); env.pop("driver_sha256", None)          # the helper hashes the reset driver, not this one
    return env


def inventory(out, deviations, files: dict, args) -> dict:
    """Every output file with its hash; this run's deviations; hashes of this driver, the shared modules, the imported
    helpers, the plan and the report; the run arguments and the environment."""
    out = Path(out)
    fixed = {"common.py": HERE / "common.py", "guards.py": HERE / "guards.py", "reset_followup_v2.py": HERE.parent / "followup" / "reset_followup_v2.py",
             "revision_v2.py": ROOT / "scripts" / "revision_v2.py"}
    hashes = {k: sha_file(Path(p)) for k, p in {**fixed, **files}.items() if Path(p).exists()}
    recs = {str(p.relative_to(out)): sha_file(p) for p in sorted(out.rglob("*"))
            if p.is_file() and p.name != "inventory.json" and not p.name.endswith((".lock", ".tmp"))}
    inv = {"stage": "inventory", "deviations": list(deviations), "files": hashes, "args": list(args), "environment": environment(), "records": recs}
    write(out / "inventory.json", inv)
    return inv


class CostStop:
    """Checked between stages: a stage starts only if the billed time so far plus its estimate stays within the cap.
    A running stage is never interrupted (the author: do not kill jobs); the run stops and reports instead."""

    def __init__(self, cap_usd: float, usd_per_hour: float, started: float, clock=time.time):
        self.cap, self.rate, self.started, self.clock, self.stopped, self.log = float(cap_usd), float(usd_per_hour), float(started), clock, None, []

    def allow(self, stage: str, est_hours: float) -> bool:
        spent = (self.clock() - self.started) / 3600 * self.rate; ok = spent + est_hours * self.rate <= self.cap + 1e-9
        self.log.append({"stage": stage, "spent_usd": round(spent, 4), "next_usd": round(est_hours * self.rate, 4), "allowed": ok})
        if not ok and self.stopped is None:
            self.stopped = stage
        return ok

    def report(self) -> dict:
        return {"cap_usd": self.cap, "usd_per_hour": self.rate, "stopped_before": self.stopped, "log": self.log}


def check_evidence(paths) -> None:
    for p in paths:
        rec = read(p)
        if rec is None or rec.get("pass") is not True:
            _refuse(f"reproduction evidence {p} is missing or did not pass")


def sha_json(obj) -> str:
    import hashlib
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=float).encode()).hexdigest()
