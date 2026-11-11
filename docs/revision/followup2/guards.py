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


def binding(inputs_sha: str, provenance: dict, smoke: bool, settings: dict, driver_sha: str, deps: dict | None = None) -> dict:
    """`deps`: hashes of everything else a result depends on (helpers, plan, report, posthoc, registered records)."""
    b = {"inputs_sha": inputs_sha, "provenance": provenance, "smoke": bool(smoke), "settings": settings, "driver_sha": driver_sha, "deps": dict(deps or {})}
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

    def __init__(self, cap_usd: float, usd_per_hour: float, started: float, clock=time.time, prior_usd: float = 0.0,
                 stop_file=None, soft_deadline: float | None = None):
        self.cap, self.rate, self.started, self.clock, self.stopped, self.log = float(cap_usd), float(usd_per_hour), float(started), clock, None, []
        self.prior = float(prior_usd)                                    # earlier attempts and launches of the same run count toward the cap
        self.stop_file, self.soft = (Path(stop_file) if stop_file else None), soft_deadline     # the launcher's STOP file and soft deadline

    def allow(self, stage: str, est_hours: float) -> bool:
        if not (math.isfinite(float(est_hours)) and est_hours >= 0):
            _refuse(f"the step estimate {est_hours} hours must be finite and nonnegative")
        spent = self.prior + (self.clock() - self.started) / 3600 * self.rate; ok = spent + est_hours * self.rate <= self.cap + 1e-9
        if (self.stop_file is not None and self.stop_file.exists()) or (self.soft is not None and self.clock() >= self.soft):
            ok = False
        self.log.append({"stage": stage, "spent_usd": round(spent, 4), "next_usd": round(est_hours * self.rate, 4), "allowed": ok})
        if not ok and self.stopped is None:
            self.stopped = stage
        return ok

    def report(self) -> dict:
        return {"cap_usd": self.cap, "usd_per_hour": self.rate, "prior_usd": self.prior, "stopped_before": self.stopped, "log": self.log,
                "note": "an admission limit checked before each stage or round; a running stage finishes, so billing can exceed the cap by that stage"}


def attempts_spend(path, usd_per_hour: float, started: float | None = None, now: float | None = None) -> dict:
    """The launcher's attempts file (results/pods/reset_pod.sh: one line per event, `<pod> <epoch> start` or
    `<pod> <epoch> deleted`), validated: finite epochs in nondecreasing order, every deletion after its pod's start, and
    exactly one open attempt (the current pod). A closed attempt is billed at `usd_per_hour` (the price ceiling); the open
    one is the caller's, counted from `started`, which must lie between the open start and `now`."""
    p = Path(path) if path else None
    if p is None or not p.exists():
        _refuse(f"no launcher attempts file at {path}")
    starts, closed, last = {}, 0.0, -math.inf
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 3 or parts[2] not in ("start", "deleted"):
            _refuse(f"unreadable line in the attempts file {p}: {line!r}")
        try:
            t = float(parts[1])
        except ValueError:
            t = math.nan
        if not math.isfinite(t) or t < last:
            _refuse(f"a nonfinite or out-of-order epoch in the attempts file {p}: {line!r}")
        last = t; pod, ev = parts[0], parts[2]
        if ev == "start":
            if pod in starts:
                _refuse(f"two starts of {pod} in the attempts file {p}")
            starts[pod] = t
        else:
            if pod not in starts:
                _refuse(f"a deletion of {pod} without an earlier start in the attempts file {p}")
            closed += (t - starts.pop(pod)) / 3600 * usd_per_hour
    if len(starts) != 1:
        _refuse(f"the attempts file {p} must have exactly one open attempt, the current pod; it has {sorted(starts)}")
    (pod, t_open), = starts.items()
    if started is not None:
        now = time.time() if now is None else now
        if not (t_open <= float(started) <= now):
            _refuse(f"the allocation time {started} is not between the open attempt's start {t_open} and now {now}")
    return {"closed_usd": closed, "open": [pod], "open_start": t_open}


def ledger_spend(ledger, tag_prefix: str) -> float:
    """Spend recorded in the budget ledger for earlier launches of this run (the launcher truncates its attempts file);
    the ledger must have a `spent` list whose rows carry a tag and a finite, nonnegative amount."""
    d = read(ledger) if ledger else None
    if not isinstance(d, dict) or not isinstance(d.get("spent"), list):
        _refuse(f"no valid budget ledger at {ledger} (a `spent` list is required)")
    tot = 0.0
    for r in d["spent"]:
        usd = r.get("usd") if isinstance(r, dict) else None
        if not isinstance(usd, (int, float)) or isinstance(usd, bool) or not math.isfinite(usd) or usd < 0 or "tag" not in r:
            _refuse(f"a malformed spend row in the ledger {ledger}: {r!r}")
        if str(r["tag"]).startswith(tag_prefix):
            tot += float(usd)
    return tot


def paid_cost_stop(cap_usd: float, usd_per_hour: float, started, attempts, ledger=None, tag: str | None = None, clock=time.time,
                   stop_file=None, soft_deadline=None) -> CostStop:
    """A paid run must state the pod allocation time, a positive rate (the price ceiling), the launcher's attempts file,
    and the ledger with the run's tag: closed attempts of this launch and recorded spend of earlier launches count toward
    the cap (no default of zero)."""
    if started is None:
        _refuse("a paid run needs --started-at (the pod allocation time)")
    if not (math.isfinite(float(usd_per_hour)) and usd_per_hour > 0 and math.isfinite(float(cap_usd)) and cap_usd > 0):
        _refuse("a paid run needs a finite positive rate and cap")
    if attempts is None:
        _refuse("a paid run needs --attempts (the launcher's attempts file)")
    if not tag:
        _refuse("a paid run needs --run-tag and --ledger (spend of earlier launches)")
    att = attempts_spend(attempts, usd_per_hour, started, clock())
    prior = att["closed_usd"] + ledger_spend(ledger, tag)
    return CostStop(cap_usd, usd_per_hour, att["open_start"], clock, prior, stop_file, soft_deadline)   # counted from the recorded open event


ENV_KEYS = ("cpu", "machine", "platform", "python", "numpy", "scipy", "cma", "blas")


def same_environment(a: dict, b: dict) -> bool:
    return all(a.get(k) == b.get(k) for k in ENV_KEYS)


def check_gate_evidence(paths, want: dict) -> None:
    """Run B: for every gate cell, a passing gate record from the Mac and one from this machine (same numerical stack),
    each with exactly the expected binding (full-budget provenance, gate settings, input hashes, driver, dependencies)."""
    recs = [read(p) for p in paths]; here = environment()
    for cell, b in want.items():
        for site in ("mac", "pod"):
            ok = [r for r in recs if r and r.get("stage") == "convergence gate" and r.get("cell") == cell and r.get("site") == site
                  and r.get("pass") is True and r.get("binding") == b and (site == "mac" or same_environment(r.get("environment") or {}, here))]
            if not ok:
                _refuse(f"no valid {site} gate evidence for {cell}")


REPRO_CELL, DBL_CELL = "headline@rho0.2|F111|D2|profit", "fresh0@rho0.2|F111|D2+H3|profit"


def _required_records(d: Path, stage: str, cell: str) -> list:
    if stage == "reproduction gate":
        return ["gate.json", "inputs.json", str(F.R.path_of(d, cell).relative_to(d)), str(F.R.eval_path(d, cell).relative_to(d)),
                f"freeze/{cell.split('|')[0]}.json"]
    return ["gate.json", "inputs.json", str(F.R.path_of(d, cell).relative_to(d)), f"doubling/{F.R._safe(cell)}.json"]


def _deps_ok(d: Path, up: dict, want_ids: set) -> bool:
    return set(up) == set(want_ids) and all(F.R.path_of(d, u).exists() and sha_file(F.R.path_of(d, u)) == h for u, h in up.items())


def _supporting_problems(d: Path, stage: str, cell: str, inp: dict, srch, src) -> list:
    """The supporting records' stages, provenance, dependency sets, dependency hashes, and the freeze contents."""
    out, ctx = [], cell.split("|")[0]
    reg = read(F.R.path_of(src, cell)) if src is not None else None
    if reg is not None and srch is not None and any((srch.get("provenance") or {}).get(k) != reg["provenance"].get(k) for k in F.EXACT_PROV):
        out.append("search provenance differs from the registered record")
    if stage == "reproduction gate":
        fr, ev = read(d / "freeze" / f"{ctx}.json"), read(F.R.eval_path(d, cell))
        want = {r: h for r, h in inp.items() if r.startswith(ctx) or f"/{ctx}/" in r}
        want[cell] = sha_file(F.R.path_of(d, cell)) if F.R.path_of(d, cell).exists() else None
        if fr is None or fr.get("stage") != "freeze" or fr.get("followup") is not True or fr.get("cuts") != F.CUTS or fr.get("h4_excluded") != F.H4_EXCLUDED \
                or not fr.get("records") or fr["records"] != want or not _deps_ok(d, fr["records"], set(want)):
            out.append("freeze empty, incomplete, or stale")
        if ev is None or ev.get("stage") != "evaluate" or ev.get("id") != cell or ev.get("provenance") != (srch or {}).get("provenance") \
                or not _deps_ok(d, ev.get("upstream") or {}, {cell, f"reference/{ctx}/{cell.split('|')[1]}", f"freeze/{ctx}"}):
            out.append("evaluation record: stage, provenance, or dependencies wrong")
    else:
        db = read(d / "doubling" / (F.R._safe(cell) + ".json"))
        if db is None or db.get("stage") != "doubling" or db.get("id") != cell or not _deps_ok(d, db.get("upstream") or {}, set(inp)) \
                or (reg is not None and any((db.get("provenance") or {}).get(k) != reg["provenance"].get(k) for k in F.EXACT_PROV)):
            out.append("doubling record: stage, provenance, or dependencies wrong")
    return out


def _verified_dir(d, stage: str, cell: str, inputs: dict, budget, site: str, src=None) -> dict:
    """A reset-driver evidence directory: the gate record names this stage and cell and passed; the inventory lists every
    required record and every listed hash equals its file; the reset driver is the current one; the inputs equal those
    recomputed from the original records; the search record has the full budget; and, with `src`, the comparison is
    recomputed against the registered records and passes."""
    d = Path(d); g, inv, inp = read(d / "gate.json"), read(d / "inventory.json"), read(d / "inputs.json")
    srch = read(F.R.path_of(d, cell)); drv = sha_file(HERE.parent / "followup" / "reset_followup_v2.py")
    recs = (inv or {}).get("records") or {}; env = (inv or {}).get("environment") or {}
    problems = []
    if g is None or g.get("stage") != stage or g.get("cell") != cell or g.get("pass") is not True:
        problems.append("gate record missing, unrelated, or failed")
    if missing := [r for r in _required_records(d, stage, cell) if r not in recs or not (d / r).exists()]:
        problems.append(f"required records missing or unlisted: {missing}")
    if bad := [r for r, h in recs.items() if not (d / r).exists() or sha_file(d / r) != h]:
        problems.append(f"inventory hashes differ from the files: {bad[:3]}")
    if env.get("driver_sha256") != drv:
        problems.append("made by another reset driver")
    if inp != inputs:
        problems.append("inputs differ from the current original records")
    if srch is None or list((srch.get("provenance") or {}).get("budget") or []) != list(budget):
        problems.append("not the registered full budget")
    if srch is None or srch.get("stage") != "search" or srch.get("id") != cell or (srch.get("provenance") or {}).get("id") != cell:
        problems.append("search record: stage or identity wrong")
    for r, h in (inp or {}).items():                              # every copied input present with its recorded hash
        q = F.R.path_of(d, r)
        if not q.exists() or sha_file(q) != h:
            problems.append(f"copied input {r} missing or changed"); break
    problems += _supporting_problems(d, stage, cell, inp or {}, srch, src)
    rep = None
    if not problems and src is not None:
        rep = F.compare(src, d) if stage == "reproduction gate" else F.compare_doubling(src, d, cell)
        if not rep.get("pass"):
            problems.append(f"the recomputed comparison fails: {rep.get('problems')}")
    if problems:
        _refuse(f"{site} evidence in {d}: {problems}")
    return {"gate": g, "environment": env, "recomputed": rep}


def check_reset_evidence(mac_dir, pod_dir, dbl_dir, want: dict) -> None:
    """Run A: the reset driver's reproduction gate for headline F111 D2 passed on the Mac and bit-identically on this
    machine (same numerical stack), and its doubling gate for fresh0 F111 D2+H3 passed; each directory verified by
    `_verified_dir`, with the comparisons recomputed against the registered records (`want["src"]`)."""
    src = want.get("src")
    _verified_dir(mac_dir, "reproduction gate", REPRO_CELL, want["repro_inputs"], want["budget"], "mac", src)
    pod = _verified_dir(pod_dir, "reproduction gate", REPRO_CELL, want["repro_inputs"], want["budget"], "pod", src)
    if pod["gate"].get("identical") is not True or (pod["recomputed"] or {}).get("identical") is False or not same_environment(pod["environment"], environment()):
        _refuse(f"pod evidence in {pod_dir}: not bit-identical on this machine's numerical stack")
    _verified_dir(dbl_dir, "doubling gate", DBL_CELL, want["dbl_inputs"], want["budget"], "doubling", src)


def check_evidence(paths) -> None:
    for p in paths:
        rec = read(p)
        if rec is None or rec.get("pass") is not True:
            _refuse(f"reproduction evidence {p} is missing or did not pass")


def sha_json(obj) -> str:
    import hashlib
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=float).encode()).hexdigest()


def check_grant(grant: float, cap_usd: float) -> None:
    """The ledger may grant less than asked when the category is nearly full; the run's cap must be granted in full."""
    if abs(float(grant) - float(cap_usd)) > 1e-6:
        _refuse(f"the reservation grant {grant} USD is not the stop cap {cap_usd} USD")


def reservation_input(cap_usd: float) -> float:
    """The estimate to pass to `budget_followup.py reserve` so that the grant (estimate x HEADROOM) equals the stop cap."""
    from scripts import budget_v2 as BV
    return round(float(cap_usd) / BV.HEADROOM, 6)


def main(argv=None) -> int:
    """`guards.py admit ...`: the spend admission check a launcher runs before any paid step (including the reset gate);
    exit 0 when the step may start, 3 when it may not."""
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=("admit",))
    ap.add_argument("--cap-usd", dest="cap", type=float, required=True); ap.add_argument("--usd-per-hour", dest="rate", type=float, required=True)
    ap.add_argument("--started-at", dest="started", type=float, required=True); ap.add_argument("--attempts", required=True)
    ap.add_argument("--ledger", required=True); ap.add_argument("--run-tag", dest="tag", required=True); ap.add_argument("--hours", type=float, required=True)
    ap.add_argument("--stop-file", dest="stop_file", default=None); ap.add_argument("--soft-deadline", dest="soft", type=float, default=None)
    ap.add_argument("--now", type=float, default=None, help="for tests")
    a = ap.parse_args(argv)
    clock = (lambda: a.now) if a.now is not None else time.time
    c = paid_cost_stop(a.cap, a.rate, a.started, a.attempts, a.ledger, a.tag, clock=clock, stop_file=a.stop_file, soft_deadline=a.soft)
    ok = c.allow("next step", a.hours); print(json.dumps(c.report()))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
