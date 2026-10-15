"""The sealed held-out bundle (spec 6.1): layout, content hash, patch log with demotions, and loader."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path

BUNDLE_FILES = ("README.md", "h1_prompt.txt", "h2/family.py", "h2/containment.md", "final_eval_seeds.json", "identity_salt.hex", "b1_check.json")
REPLACEABLE = ("h1_prompt.txt", "h2/family.py")               # a repair may replace the prompt or the family, never the seeds or the salt
IGNORED_DIRS = ("patches", "__pycache__")
ACCESS_LOG = "access_log.md"                                  # the custodian's running log: outside the hash by design


def _bundle_files(root: Path):
    """Exactly the registered bundle files, in order; nothing else enters the hash."""
    for rel in BUNDLE_FILES:
        p = root / rel
        if p.is_file():
            yield rel, p


def stray_files(root: Path) -> list:
    """Files in the bundle directory that are neither bundle files, patches, import artifacts, dotfiles, nor the access log."""
    out = []
    for p in sorted(q for q in Path(root).rglob("*") if q.is_file()):
        rel = p.relative_to(root); name = rel.as_posix()
        if name in BUNDLE_FILES or name == ACCESS_LOG or any(part in IGNORED_DIRS for part in rel.parts) or p.suffix == ".pyc" or any(part.startswith(".") for part in rel.parts):
            continue
        out.append(name)
    return out


def bundle_hash(sealed_dir) -> str:
    h = hashlib.sha256()
    for rel, p in _bundle_files(Path(sealed_dir)):
        h.update(rel.encode()); h.update(b"\0"); h.update(hashlib.sha256(p.read_bytes()).hexdigest().encode()); h.update(b"\n")
    return h.hexdigest()


def verify_bundle(sealed_dir, locked: dict) -> None:
    want = locked.get("sealed_bundle_sha256")
    if not want:
        raise ValueError("locked.yaml has no sealed_bundle_sha256")
    got = bundle_hash(sealed_dir)
    if got != want:
        raise ValueError(f"sealed bundle hash {got} differs from the lock commitment {want}")
    strays = stray_files(Path(sealed_dir))
    if strays:
        raise ValueError(f"sealed bundle has unexpected files: {strays}")


def patch_log(sealed_dir) -> dict:
    p = Path(sealed_dir) / "patches" / "log.json"
    return json.loads(p.read_text()) if p.exists() else {}


def verify_patches(sealed_dir) -> list:
    d = Path(sealed_dir) / "patches"; log = patch_log(sealed_dir); problems = []
    present = {q.relative_to(d).as_posix(): q for q in d.rglob("*") if q.is_file() and q.name != "log.json"} if d.exists() else {}
    for rel, p in present.items():
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        if rel not in log:
            problems.append(f"sealed/patches/{rel}: not in the patch log")
        elif log[rel].get("sha256") != h:
            problems.append(f"sealed/patches/{rel}: hash {h} differs from the logged {log[rel].get('sha256')}")
        elif log[rel].get("replaces") not in REPLACEABLE:
            problems.append(f"sealed/patches/{rel}: 'replaces' must be one of {REPLACEABLE}, got {log[rel].get('replaces')!r}")
    for rel in log:
        if rel not in present:
            problems.append(f"sealed/patches/{rel}: logged but missing")
    return problems


def effective_path(sealed_dir, rel: str) -> Path:
    """The overlay: the logged, hash-verified patch that replaces `rel`, else the original bundle file. The original is
    never edited, so the bundle hash stays what the lock committed to."""
    root = Path(sealed_dir); log = patch_log(root)
    for prel, entry in log.items():
        p = root / "patches" / prel
        if rel in REPLACEABLE and entry.get("replaces") == rel and p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == entry.get("sha256"):
            return p
    return root / rel


def demoted_cells(sealed_dir) -> set:
    return {c for entry in patch_log(sealed_dir).values() for c in entry.get("demotes", [])}


def final_eval_seeds(sealed_dir) -> list:
    return [int(s) for s in json.loads(effective_path(sealed_dir, "final_eval_seeds.json").read_text())]


@dataclass
class SealedBundle:
    h1_prompt: str
    h2_module: object
    containment: str
    final_eval_seeds: list
    salt_hex: str | None
    b1_check: dict


def load_bundle(sealed_dir, locked: dict) -> SealedBundle:
    root = Path(sealed_dir); verify_bundle(root, locked)
    spec = importlib.util.spec_from_file_location("sealed_h2_family", effective_path(root, "h2/family.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    salt = root / "identity_salt.hex"
    return SealedBundle(h1_prompt=effective_path(root, "h1_prompt.txt").read_text(), h2_module=mod, containment=(root / "h2" / "containment.md").read_text(),
                        final_eval_seeds=final_eval_seeds(root), salt_hex=salt.read_text().strip() if salt.exists() else None,
                        b1_check=json.loads((root / "b1_check.json").read_text()) if (root / "b1_check.json").exists() else {})
