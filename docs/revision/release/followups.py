"""Follow-up record archives for the public release (separately dated from the second test's artifact
touchstone-v2.tar.gz, which stays as built on 2026-11-05). One gzip tarball per follow-up, each under GitHub's 2 GiB
release-asset limit, each holding MANIFEST.json (sha256 and size of every packed file, plus the source folder's record
digest as replication_extract.records_digest computes it). Packing is deterministic: sorted paths, fixed mtime, uid and
gid 0, no user names. The folder list is explicit (SPEC); the builder never walks results/ itself, so it cannot enter a
folder that is not listed (lesson 2026-11-24: results/pods/mac_diag holds sealed/).

Usage:
  followups.py --build OUTDIR [--only NAME]     write OUTDIR/<name>.tar.gz for every archive in SPEC
  followups.py --check OUTDIR [--only NAME]     verify every archive's manifest against its packed bytes"""
import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from pathlib import Path

RESULTS = Path("/Users/oemer.demirel/Projects/touchstone/results")
REPO = Path(__file__).resolve().parents[3]
MTIME = 1764547200                       # 2025-12-01T00:00:00Z: a fixed timestamp so that rebuilds are byte-identical
LIMIT = 2 * 1024 ** 3                    # GitHub release asset limit
FORBIDDEN = ("sealed", "mac_diag")       # never packed, at any depth

# archive name -> [(source folder, name inside the archive)]
SPEC = {
    "touchstone-followup-paper-inputs": [
        (RESULTS / "v2/paper", "v2/paper"),                              # cells, scoring, eligibility (paper_check.sh)
        (RESULTS / "v2/deviation/stability", "v2/deviation/stability"),  # audit_v2.py --stability-work (inferred; see notes)
    ],
    "touchstone-followup-reset": [
        (RESULTS / "v2/followup-reset-pod", "v2/followup-reset-pod"),            # reset.json (inventory hash matches)
        (RESULTS / "v2/followup-reset-mac-diag", "v2/followup-reset-mac-diag"),  # reset.json diagnostics (hash matches)
    ],
    "touchstone-followup-churn": [
        (RESULTS / "v2/followup-churn", "v2/followup-churn"),                    # churn.json (p = 0.01, 0.05)
    ],
    "touchstone-followup-churn-mid": [
        (RESULTS / "v2/followup-churn-mid", "v2/followup-churn-mid"),            # churn_mid.json (p = 0.02, 0.03)
    ],
    "touchstone-followup-runnerup-convergence": [
        (RESULTS / "v2/followup2-runnerup-mac", "v2/followup2-runnerup-mac"),    # runnerup_analysis.json (identical)
        (RESULTS / "v2/followup2-pod-b2/followup2-conv", "v2/followup2-pod-b2/followup2-conv"),   # convergence_analysis.json
    ],
    "touchstone-replication": [
        (RESULTS / "pods/rep_p3_out/followup3-rep", "followup3-rep"),            # replication run records (digest 51086341)
    ],
}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def files_of(src: Path) -> list:
    """Every regular file under src, sorted by relative path; refuses symlinks and any forbidden path component."""
    out = []
    for q in sorted(src.rglob("*")):
        rel = q.relative_to(src)
        if any(part in FORBIDDEN for part in rel.parts):
            raise ValueError(f"forbidden path in {src}: {rel}")
        if q.is_symlink():
            raise ValueError(f"symlink in {src}: {rel}")
        if q.is_file():
            out.append(q)
    return out


def records_digest(src: Path) -> tuple:
    """As replication_extract.records_digest: sha256 over sorted '<path> <sha256>' lines, analysis.json excluded."""
    lines = sorted(f"{q.relative_to(src).as_posix()} {sha_bytes(q.read_bytes())}" for q in files_of(src) if q != src / "analysis.json")
    return len(lines), sha_bytes("\n".join(lines).encode())


def _info(name: str, size: int) -> tarfile.TarInfo:
    ti = tarfile.TarInfo(name); ti.size = size; ti.mtime = MTIME; ti.mode = 0o644
    ti.uid = ti.gid = 0; ti.uname = ti.gname = ""
    return ti


def build(name: str, parts: list, outdir: Path) -> Path:
    for src, arc in parts:
        if any(part in FORBIDDEN for part in Path(arc).parts) or any(part in FORBIDDEN for part in src.parts):
            raise ValueError(f"forbidden source: {src}")
        if not src.is_dir():
            raise ValueError(f"missing source folder: {src}")
    manifest = {"archive": name, "files": {}, "sources": {}}
    dest = Path(outdir) / f"{name}.tar.gz"
    with open(dest, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=MTIME, filename="") as gz, \
            tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tf:
        for src, arc in parts:
            n, dig = records_digest(src)
            manifest["sources"][arc] = {"files": n, "records_digest": dig}
            for q in files_of(src):
                b = q.read_bytes(); path = f"{name}/{arc}/{q.relative_to(src).as_posix()}"
                manifest["files"][path] = {"sha256": sha_bytes(b), "size": len(b)}
                tf.addfile(_info(path, len(b)), io.BytesIO(b))
        mb = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode()
        tf.addfile(_info(f"{name}/MANIFEST.json", len(mb)), io.BytesIO(mb))
    if dest.stat().st_size >= LIMIT:
        raise ValueError(f"{dest.name} is {dest.stat().st_size} bytes, above the GitHub release limit")
    return dest


def check(path: Path) -> list:
    """Problems with one archive: a missing or extra member, a hash or size mismatch, a forbidden path."""
    probs, seen, manifest = [], {}, None
    with tarfile.open(path, "r:gz") as tf:
        for m in tf:
            if not m.isfile():
                probs.append(f"not a regular file: {m.name}"); continue
            if any(part in FORBIDDEN for part in Path(m.name).parts):
                probs.append(f"forbidden path: {m.name}")
            b = tf.extractfile(m).read()
            if m.name.endswith("/MANIFEST.json") and m.name.count("/") == 1:
                manifest = json.loads(b)
            else:
                seen[m.name] = {"sha256": sha_bytes(b), "size": len(b)}
    if manifest is None:
        return probs + ["no MANIFEST.json"]
    for p, v in manifest["files"].items():
        if seen.get(p) != v:
            probs.append(f"missing or changed: {p}")
    probs += [f"not in the manifest: {p}" for p in seen if p not in manifest["files"]]
    return probs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--build"); g.add_argument("--check")
    ap.add_argument("--only")
    a = ap.parse_args(argv)
    names = [a.only] if a.only else list(SPEC)
    if a.build:
        Path(a.build).mkdir(parents=True, exist_ok=True)
        for n in names:
            d = build(n, SPEC[n], Path(a.build))
            print(f"{d.name} {d.stat().st_size} {sha_bytes(d.read_bytes())}")
        return 0
    bad = 0
    for n in names:
        probs = check(Path(a.check) / f"{n}.tar.gz")
        print(f"{n}: " + ("ok" if not probs else "; ".join(probs[:5])))
        bad += bool(probs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
