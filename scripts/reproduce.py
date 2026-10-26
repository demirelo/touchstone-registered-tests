"""One-command reproduction of the protocol-v2 report (design 10; operations plan Task 10; final review K12): unpack the
release artifact, clone the repository, verify the signed tag protocol-v2 and check it out, run the artifact check
(manifest, required files, frozen records, packed registration inputs equal to the tagged files), check that the
installed packages match the clone's uv.lock, and run the real report's --check (report.json and report.md) on the packed
records. Exit 0 means every table is reproduced; otherwise the problems or differences are printed."""
from __future__ import annotations

import argparse
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP = "touchstone-v2"


def _installed(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


_real_installed = _installed


def environment_problems(lock: Path) -> list[str]:
    """Every locked package that is installed here has the locked version (platform-specific packages that are not
    installed are skipped; the project itself is skipped)."""
    out = []
    for pkg in tomllib.loads(Path(lock).read_text()).get("package", []):
        src = pkg.get("source") or {}
        if "editable" in src or "virtual" in src:
            continue
        got = _installed(pkg["name"])
        if got is not None and got != pkg.get("version"):
            out.append(f"{pkg['name']}: installed {got}, locked {pkg.get('version')}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifact", required=True); ap.add_argument("--repo", default=str(ROOT), help="a clone source: path or URL")
    ap.add_argument("--smoke", action="store_true", help="the report's smoke seeds (tests only)")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT))
    from scripts.artifact_v2 import check
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        with tarfile.open(a.artifact) as tf:
            tf.extractall(tmp / "u", filter="data")
        u = tmp / "u" / TOP; clone = tmp / "clone"
        subprocess.run(["git", "clone", "-q", str(a.repo), str(clone)], check=True)
        if subprocess.run(["git", "-C", str(clone), "tag", "-v", "protocol-v2"], capture_output=True).returncode != 0:
            print("refused: tag protocol-v2 is missing, unsigned, or does not verify"); return 1
        subprocess.run(["git", "-C", str(clone), "checkout", "-q", "protocol-v2"], check=True)
        problems = check(a.artifact, repo=clone) + environment_problems(clone / "uv.lock")
        if problems:
            print("refused:\n" + "\n".join(problems)); return 1
        r = subprocess.run([sys.executable, "scripts/report_v2.py", "--out", str(u / "eval"), "--protocol", str(u / "experiments" / "protocol-v2.yaml"),
                            "--instances", str(u / "draw" / "instances.json"), "--h4", str(u / "draw" / "h4.json"), "--report", str(u / "report"),
                            "--params", str(u / "experiments" / "v2" / "params.json"), "--check"] + (["--smoke"] if a.smoke else []),
                           cwd=clone, capture_output=True, text=True)
        print(r.stdout, end=""); print(r.stderr, end="", file=sys.stderr)
        return r.returncode


if __name__ == "__main__":
    sys.exit(main())
