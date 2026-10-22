"""Loader of the sealed, independently authored family H4 (design 5.3). The bundle's h4/family.py exports
make_family(T, L) -> Family and BINARY (the binary knob names, clip included); the loader verifies the bundle hash, imports
the module by absolute path, and checks the family at two constant pairs (a Family named H4, clip last, bounds for every
non-binary knob). Any failure excludes H4 and is reported; there is no repair after the lock."""
from __future__ import annotations

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path

from .policies.families import Family

BUNDLE_FILES = ("h4/family.py", "h4/containment.md", "h4/check.json")
CHECK_CONSTANTS = ((200, 10), (100, 20))


def bundle_sha(bundle_dir) -> str:
    h = hashlib.sha256()
    for rel in BUNDLE_FILES:
        h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256((Path(bundle_dir) / rel).read_bytes()).hexdigest().encode()); h.update(b"\n")
    return h.hexdigest()


@dataclass(frozen=True)
class Excluded:
    reason: str


class H4Source:
    def __init__(self, module) -> None:
        self.module = module

    def family(self, T: int, L: int) -> Family:
        return self.module.make_family(int(T), int(L))


def _check(fam, binary) -> str | None:
    if not isinstance(fam, Family):
        return "make_family did not return a Family"
    if fam.name != "H4":
        return f"family name {fam.name!r} is not H4"
    if not fam.knobs or fam.knobs[-1] != "clip" or "clip" in fam.bounds:
        return "clip must be the last, binary knob"
    missing = [k for k in fam.knobs if k not in fam.bounds and k not in binary]
    if missing:
        return f"no bounds for non-binary knob(s) {missing}"
    if any(not (float(lo) < float(hi)) for lo, hi in fam.bounds.values()):
        return "empty knob bounds"
    return None


def load(bundle_dir, expected_sha256: str) -> H4Source | Excluded:
    d = Path(bundle_dir)
    try:
        got = bundle_sha(d)
    except OSError as e:
        return Excluded(f"bundle unreadable: {e}")
    if got != expected_sha256:
        return Excluded(f"bundle hash {got} differs from the protocol's {expected_sha256}")
    try:
        spec = importlib.util.spec_from_file_location("touchstone_sealed_h4", d / "h4/family.py")
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        make, binary = getattr(mod, "make_family"), tuple(getattr(mod, "BINARY"))
        for T, L in CHECK_CONSTANTS:
            problem = _check(make(T, L), binary)
            if problem:
                return Excluded(problem)
    except Exception as e:                       # the family is untrusted code: any failure excludes it
        return Excluded(f"load failed: {type(e).__name__}: {e}")
    return H4Source(mod)
