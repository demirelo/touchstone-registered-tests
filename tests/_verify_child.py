"""Runs the runner's verify stage in a fresh spawned process under a write and child-process guard (operations plan Task 8).
Imports happen first; then calibration, episodes, stage bodies, the H4 loader, the salt readers, and the salt installer are
replaced by functions that raise, and an audit hook refuses every filesystem mutation and every child process."""
from __future__ import annotations

import io
import os
import sys


class Guarded(RuntimeError):
    pass


WRITE = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
MUTATE = {"os.mkdir", "os.rename", "os.replace", "os.remove", "os.rmdir", "os.link", "os.symlink", "os.truncate", "os.chmod", "os.chown", "os.utime"}
SPAWN = {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty"}


def _hook(event, args):
    if event == "open":
        mode, flags = (args[1] if len(args) > 1 else None), (args[2] if len(args) > 2 else 0)
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & WRITE):
            raise Guarded(f"write: {args[0]}")
    elif event in MUTATE:
        raise Guarded(f"{event}: {args}")
    elif event in SPAWN:
        raise Guarded(f"{event}: {args}")


def _raiser(name):
    def f(*a, **k):
        raise Guarded(f"forbidden call: {name}")
    return f


def _patch():
    import scripts.revision_v2 as RV
    import sim.calibrate
    import sim.cell
    import sim.h4_loader
    import sim.instances
    import sim.manifest_v2 as MAN
    import sim.rng
    from tests import test_revision_v2 as T
    MAN.required = T._required; MAN.bank_rules = lambda ctx, fam, cuts=0, h4_excluded=False: []
    for mod, name in ((sim.calibrate, "calibrate"), (sim.instances, "calibrate"), (sim.calibrate, "first_best_episode"), (sim.cell, "run_focal"),
                      (sim.h4_loader, "load"), (RV, "load_h4"), (sim.rng, "load_identity_salt"), (RV, "load_identity_salt"), (RV, "install_salt"),
                      (RV, "stage_search"), (RV, "stage_dependent"), (RV, "stage_evaluate"), (RV, "stage_reference"), (RV, "stage_cross"),
                      (RV, "stage_doubling"), (RV, "coalition_prereqs"), (RV, "run_focal")):
        setattr(mod, name, _raiser(f"{mod.__name__}.{name}"))
    return RV


FAULTS = {
    "write outside out": lambda tmp: __import__("pathlib").Path(tmp, "leak.txt").write_text("x"),
    "create a directory": lambda tmp: os.mkdir(os.path.join(tmp, "newdir")),
    "hard link": lambda tmp: os.link(__file__, os.path.join(tmp, "link")),
    "child process": lambda tmp: __import__("subprocess").run(["git", "rev-parse", "HEAD"], capture_output=True),
}


def child(argv, q, fault=None, tmp=None):
    """Put ("ok", stdout) or ("error", repr) on the queue."""
    sys.dont_write_bytecode = True
    try:
        import json  # noqa: F401
        import yaml  # noqa: F401
        RV = _patch()
        if fault:
            RV.verify = lambda *a, **k: FAULTS[fault](tmp)
        buf = io.StringIO(); old = sys.stdout; sys.stdout = buf
        sys.addaudithook(_hook)
        try:
            rc = RV.main(argv)
        finally:
            sys.stdout = old
        q.put(("ok", rc, buf.getvalue()))
    except BaseException as e:                       # the parent inspects the failure
        q.put(("error", None, f"{type(e).__name__}: {e}"))
